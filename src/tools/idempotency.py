import hashlib
import json
from typing import Optional, Tuple

from cache.valkey import setnx_idempotency, tenant_key
from db.pool import tenant_conn


def derive_key(tenant_id: str, thread_id: str, tool_name: str, args: dict) -> str:
    raw = json.dumps(
        {"thread": thread_id, "tool": tool_name, "args": args},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(f"{tenant_id}:{raw}".encode("utf-8")).hexdigest()


async def reserve(
    tenant_id: str, key: str, tool_name: str, ttl: int = 3600
) -> Tuple[bool, Optional[dict]]:
    """Returns (newly_reserved, cached_result_or_None).

    If newly_reserved=False and cached_result is not None: replay; return cached.
    If newly_reserved=False and cached_result is None: another worker holds it.
    """
    valkey_k = tenant_key(tenant_id, "idem", tool_name, key)
    fresh = await setnx_idempotency(valkey_k, ttl)

    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT status, result FROM idempotency_keys WHERE key = $1",
            key,
        )
        if row and row["status"] == "succeeded":
            return False, dict(row["result"]) if row["result"] else {}

        if fresh:
            await conn.execute(
                """
                INSERT INTO idempotency_keys (tenant_id, key, tool_name, status)
                VALUES (current_setting('app.tenant_id')::uuid, $1, $2, 'running')
                ON CONFLICT (tenant_id, key) DO UPDATE SET tool_name = EXCLUDED.tool_name
                """,
                key,
                tool_name,
            )
            return True, None

    return False, None


async def finalize(tenant_id: str, key: str, status: str, result: dict) -> None:
    async with tenant_conn(tenant_id) as conn:
        await conn.execute(
            """
            UPDATE idempotency_keys
               SET status = $1, result = $2
             WHERE key = $3
            """,
            status,
            json.dumps(result, default=str),
            key,
        )
