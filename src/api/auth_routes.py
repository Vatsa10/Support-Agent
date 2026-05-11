"""Self-serve signup + signin.

Issues a tenant-scoped API key on signup and returns it once. Sign-in re-issues
the same active key (or returns 401 if pw mismatch). Frontend stores api_key
in an httpOnly cookie and uses it as X-API-Key for /tenant/* and /api/* routes.
"""
import base64
import hashlib
import json
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from api.auth import Tenant, generate_api_key, hash_api_key, require_tenant
from cache.valkey import incr_with_ttl
from db.pool import sys_conn, tenant_conn

router = APIRouter()

PBKDF2_ITERS = 120_000


def _hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, PBKDF2_ITERS)
    return f"pbkdf2${PBKDF2_ITERS}${base64.b64encode(salt).decode()}${base64.b64encode(h).decode()}"


def _verify_password(pw: str, stored: str) -> bool:
    try:
        scheme, iters_s, salt_b64, hash_b64 = stored.split("$", 3)
        if scheme != "pbkdf2":
            return False
        iters = int(iters_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        h = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, iters)
        return secrets.compare_digest(h, expected)
    except Exception:
        return False


class SignupBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    company: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=10, max_length=200)


class SigninBody(BaseModel):
    email: EmailStr
    password: str


class AuthOut(BaseModel):
    tenant_id: str
    tenant_name: str
    user_id: str
    email: str
    name: Optional[str]
    api_key: str


async def _rate_limit_signup(remote_key: str) -> None:
    count = await incr_with_ttl(f"rl:signup:{remote_key}", ttl_seconds=3600)
    if count > 10:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many signups; try again later")


@router.post("/signup", response_model=AuthOut)
async def signup(body: SignupBody):
    await _rate_limit_signup(body.email.split("@")[1])

    async with sys_conn() as conn:
        # Block duplicate emails
        existing = await conn.fetchval("SELECT 1 FROM users WHERE email = $1", body.email)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)

        async with conn.transaction():
            tenant_row = await conn.fetchrow(
                """
                INSERT INTO tenants (name, api_key_hash, plan)
                VALUES ($1, $2, 'free')
                RETURNING id, name
                """,
                body.company, key_hash,
            )
            tenant_id = tenant_row["id"]

            await conn.execute(
                """
                INSERT INTO tenant_settings (tenant_id, rate_limit_per_min)
                VALUES ($1, 60)
                ON CONFLICT (tenant_id) DO NOTHING
                """,
                tenant_id,
            )

            await conn.execute(
                """
                INSERT INTO api_keys (tenant_id, api_key_hash, label, status)
                VALUES ($1, $2, 'default', 'active')
                """,
                tenant_id, key_hash,
            )

            user_row = await conn.fetchrow(
                """
                INSERT INTO users (tenant_id, email, password_hash, name, role)
                VALUES ($1, $2, $3, $4, 'admin')
                RETURNING id, email, name
                """,
                tenant_id, body.email, _hash_password(body.password), body.name,
            )

    return AuthOut(
        tenant_id=str(tenant_id),
        tenant_name=tenant_row["name"],
        user_id=str(user_row["id"]),
        email=user_row["email"],
        name=user_row["name"],
        api_key=api_key,
    )


@router.post("/signin", response_model=AuthOut)
async def signin(body: SigninBody):
    async with sys_conn() as conn:
        row = await conn.fetchrow(
            """
            SELECT u.id AS user_id, u.email, u.name, u.password_hash,
                   u.tenant_id, t.name AS tenant_name, t.api_key_hash
            FROM users u
            JOIN tenants t ON t.id = u.tenant_id
            WHERE u.email = $1
            """,
            body.email,
        )

    if not row or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    # We can't return the original API key (only hash stored). Issue a new one
    # and replace the hash on the tenant + insert in api_keys.
    api_key = generate_api_key()
    new_hash = hash_api_key(api_key)
    async with sys_conn() as conn:
        await conn.execute("UPDATE tenants SET api_key_hash = $1 WHERE id = $2", new_hash, row["tenant_id"])
        await conn.execute(
            """
            INSERT INTO api_keys (tenant_id, api_key_hash, label, status)
            VALUES ($1, $2, 'session', 'active')
            """,
            row["tenant_id"], new_hash,
        )
        await conn.execute("UPDATE users SET last_login_at = now() WHERE id = $1", row["user_id"])

    return AuthOut(
        tenant_id=str(row["tenant_id"]),
        tenant_name=row["tenant_name"],
        user_id=str(row["user_id"]),
        email=row["email"],
        name=row["name"],
        api_key=api_key,
    )


@router.get("/me")
async def me(tenant: Tenant = Depends(require_tenant)):
    async with sys_conn() as conn:
        u = await conn.fetchrow(
            "SELECT id, email, name, role, last_login_at FROM users WHERE tenant_id = $1 ORDER BY created_at ASC LIMIT 1",
            tenant.id,
        )
    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "plan": tenant.plan,
        "status": tenant.status,
        "user": dict(u) if u else None,
    }


@router.post("/logout")
async def logout(tenant: Tenant = Depends(require_tenant)):
    # Cookie clearing happens client-side; backend has nothing to do beyond ack.
    return {"ok": True, "tenant_id": tenant.id}
