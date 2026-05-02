import json
from datetime import datetime, timezone
from typing import Optional

from cache.valkey import incr_with_ttl, tenant_key
from db.pool import tenant_conn


MONTH_TTL = 60 * 60 * 24 * 35  # ~35 days


def _ym() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m")


async def record_tokens(
    tenant_id: str,
    user_id: str,
    thread_id: str,
    in_tokens: int,
    out_tokens: int,
    model: Optional[str] = None,
) -> None:
    if not (in_tokens or out_tokens):
        return

    md = json.dumps({"model": model} if model else {})
    async with tenant_conn(tenant_id) as conn:
        if in_tokens:
            await conn.execute(
                """
                INSERT INTO billing_events
                    (tenant_id, user_id, thread_id, event_type, units, metadata)
                VALUES (current_setting('app.tenant_id')::uuid,
                        $1, $2, 'llm_input_tokens', $3, $4::jsonb)
                """,
                user_id, thread_id, int(in_tokens), md,
            )
        if out_tokens:
            await conn.execute(
                """
                INSERT INTO billing_events
                    (tenant_id, user_id, thread_id, event_type, units, metadata)
                VALUES (current_setting('app.tenant_id')::uuid,
                        $1, $2, 'llm_output_tokens', $3, $4::jsonb)
                """,
                user_id, thread_id, int(out_tokens), md,
            )

    ym = _ym()
    if in_tokens:
        await incr_with_ttl(tenant_key(tenant_id, "bill", ym, "in"), MONTH_TTL)
    if out_tokens:
        await incr_with_ttl(tenant_key(tenant_id, "bill", ym, "out"), MONTH_TTL)


async def monthly_summary(tenant_id: str) -> dict:
    ym = _ym()
    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(
            """
            SELECT event_type, SUM(units)::bigint AS total
            FROM billing_events
            WHERE created_at >= date_trunc('month', now())
            GROUP BY event_type
            """,
        )
    totals = {r["event_type"]: int(r["total"]) for r in rows}
    return {
        "tenant_id": tenant_id,
        "period": ym,
        "llm_input_tokens": totals.get("llm_input_tokens", 0),
        "llm_output_tokens": totals.get("llm_output_tokens", 0),
        "total_tokens": totals.get("llm_input_tokens", 0) + totals.get("llm_output_tokens", 0),
    }
