import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import Header, HTTPException, status

from config import config
from db.pool import sys_conn
from cache.valkey import cache_get, cache_set


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
