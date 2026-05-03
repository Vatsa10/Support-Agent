import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import jwt as pyjwt
from fastapi import Header, HTTPException, status

from cache.valkey import cache_delete, cache_get, cache_set, tenant_key
from config import config
from db.pool import sys_conn, tenant_conn
from security.crypto import decrypt, encrypt


@dataclass
class Tenant:
    id: str
    name: str
    plan: str
    status: str


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return "sk_" + secrets.token_urlsafe(32)


async def _lookup_tenant(api_key_hash: str) -> Optional[Tenant]:
    cache_k = f"apikey:{api_key_hash}"
    cached = await cache_get(cache_k)
    if cached:
        d = json.loads(cached)
        return Tenant(**d)

    async with sys_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, plan, status FROM tenants WHERE api_key_hash = $1",
            api_key_hash,
        )
    if not row:
        return None

    tenant = Tenant(
        id=str(row["id"]), name=row["name"], plan=row["plan"], status=row["status"]
    )
    await cache_set(cache_k, json.dumps(tenant.__dict__), ttl_seconds=60)
    return tenant


async def require_tenant(
    x_api_key: str = Header(default=None, alias="X-API-Key"),
) -> Tenant:
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")
    tenant = await _lookup_tenant(hash_api_key(x_api_key))
    if not tenant:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    if tenant.status != "active":
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Tenant status: {tenant.status}")
    return tenant


async def require_admin(
    x_admin_key: str = Header(default=None, alias="X-Admin-Key"),
) -> bool:
    if not config.ADMIN_API_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Admin disabled")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, config.ADMIN_API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid admin key")
    return True


# ============================================================
# Per-tenant end-user JWT (HS256)
# ============================================================

JWT_SECRET_BYTES = 32


async def get_or_create_jwt_secret(tenant_id: str, rotate: bool = False) -> str:
    """Returns the raw HS256 secret (base64-url) for a tenant. Generates if missing.

    Stored encrypted at rest using Fernet (security/crypto).
    """
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT secret FROM tenant_jwt_secrets WHERE tenant_id = current_setting('app.tenant_id')::uuid"
        )
        if row and not rotate:
            return decrypt(bytes(row["secret"])).decode("ascii")

        secret = secrets.token_urlsafe(JWT_SECRET_BYTES)
        enc = encrypt(secret.encode("ascii"))
        await conn.execute(
            """
            INSERT INTO tenant_jwt_secrets (tenant_id, secret)
            VALUES (current_setting('app.tenant_id')::uuid, $1)
            ON CONFLICT (tenant_id) DO UPDATE
                SET secret = EXCLUDED.secret, updated_at = now()
            """,
            enc,
        )
    await cache_delete(tenant_key(tenant_id, "jwt_secret"))
    return secret


async def _load_jwt_secret(tenant_id: str) -> Optional[str]:
    cache_k = tenant_key(tenant_id, "jwt_secret")
    cached = await cache_get(cache_k)
    if cached:
        return cached if cached != "__none__" else None

    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT secret FROM tenant_jwt_secrets WHERE tenant_id = current_setting('app.tenant_id')::uuid"
        )
    if not row:
        await cache_set(cache_k, "__none__", ttl_seconds=60)
        return None
    secret = decrypt(bytes(row["secret"])).decode("ascii")
    await cache_set(cache_k, secret, ttl_seconds=300)
    return secret


async def verify_end_user_jwt(token: str, tenant_id: str) -> Optional[str]:
    """Returns end_user_id (sub claim) if valid; raises 401 if header present but bad."""
    secret = await _load_jwt_secret(tenant_id)
    if not secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tenant has no JWT secret configured")
    try:
        payload = pyjwt.decode(token, secret, algorithms=["HS256"])
    except pyjwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid JWT: {e}")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "JWT missing sub")
    return str(sub)
