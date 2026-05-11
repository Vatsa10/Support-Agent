from datetime import datetime, timezone

from db.pool import tenant_conn


class BudgetExceeded(RuntimeError):
    def __init__(self, used: int, cap: int):
        super().__init__(f"Token budget exceeded: {used}/{cap}")
        self.used = used
        self.cap = cap


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
    return used, cap
