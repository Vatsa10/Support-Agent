import os
from datetime import datetime, timezone

from cache.valkey import cache_get, cache_set, tenant_key
from db.pool import sys_conn, tenant_conn


class BudgetExceeded(RuntimeError):
    def __init__(self, used: int, cap: int):
        super().__init__(f"Token budget exceeded: {used}/{cap}")
        self.used = used
        self.cap = cap


async def _maybe_alert_threshold(tenant_id: str, used: int, cap: int, notify_pct: int) -> None:
    """Send budget threshold email once per period when crossing notify_pct."""
    if not cap or notify_pct <= 0:
        return
    pct = int((used / cap) * 100)
    if pct < notify_pct:
        return
    ym = datetime.now(timezone.utc).strftime("%Y%m")
    cache_k = tenant_key(tenant_id, "budget_alert", ym)
    if await cache_get(cache_k):
        return
    try:
        from notify import send_email
        from notify.templates import budget_threshold

        async with sys_conn() as conn:
            users = await conn.fetch(
                "SELECT email, name FROM users WHERE tenant_id = $1 AND role = 'admin'", tenant_id
            )
        app_url = os.getenv("APP_URL", "http://localhost:3000")
        link = f"{app_url}/billing"
        for u in users:
            subject, html = budget_threshold(u["name"] or "", used, cap, pct, link)
            await send_email(u["email"], subject, html, tag="budget_threshold")
        await cache_set(cache_k, "1", ttl_seconds=60 * 60 * 24 * 31)
    except Exception:
        pass


async def check_budget(tenant_id: str) -> tuple[int, int | None]:
    """Returns (used_this_month, cap_or_None). Raises BudgetExceeded if hard cap reached."""
    async with tenant_conn(tenant_id) as conn:
        cap_row = await conn.fetchrow(
            "SELECT monthly_token_cap, hard_cap FROM token_budgets WHERE tenant_id = current_setting('app.tenant_id')::uuid"
        )
        if not cap_row or not cap_row["monthly_token_cap"]:
            return 0, None
        cap = int(cap_row["monthly_token_cap"])
        hard = bool(cap_row["hard_cap"])

        used_row = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(units),0)::bigint AS used
            FROM billing_events
            WHERE event_type IN ('llm_input_tokens','llm_output_tokens')
              AND created_at >= date_trunc('month', now())
            """
        )
    used = int(used_row["used"]) if used_row else 0
    if hard and used >= cap:
        raise BudgetExceeded(used, cap)

    # Notify-once threshold email (default 80%)
    notify_pct = int(os.getenv("BUDGET_NOTIFY_PCT", "80"))
    await _maybe_alert_threshold(tenant_id, used, cap, notify_pct)

    return used, cap
