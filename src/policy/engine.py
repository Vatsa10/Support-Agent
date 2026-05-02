from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Optional

from cache.valkey import incr_with_ttl, tenant_key
from db.pool import tenant_conn


DecisionStr = Literal["allow", "deny", "approval"]


@dataclass
class Decision:
    decision: DecisionStr
    reason: str = ""
    policy_id: Optional[str] = None


SOFT_TOOLS = {"comment_zendesk_ticket"}  # exempt from sentiment gate
DEFAULT_DAILY_FREQ_TTL = 86400


async def evaluate(
    tenant_id: str,
    tool_name: str,
    args: dict,
    end_user_id: Optional[str] = None,
    sentiment: Optional[str] = None,
) -> Decision:
    """Evaluate whether a side-effecting tool may run for this tenant.

    Default-deny for action tools without an action_policies row.
    """
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """
            SELECT id, allow, max_amount, currency, requires_approval_above,
                   frequency_per_user_per_day, blocked_categories, extra
            FROM action_policies
            WHERE tool_name = $1
            """,
            tool_name,
        )

    if not row:
        return Decision("deny", f"No policy for {tool_name}; default-deny")

    if not row["allow"]:
        return Decision("deny", "Policy disables this tool", str(row["id"]))

    blocked = row["blocked_categories"] or []
    cat = (args.get("category") or "").lower()
    if cat and cat in [c.lower() for c in blocked]:
        return Decision("deny", f"Category {cat} blocked", str(row["id"]))

    amount = _extract_amount(args)
    if amount is not None:
        if row["max_amount"] is not None and amount > float(row["max_amount"]):
            return Decision(
                "deny",
                f"Amount {amount} exceeds max {row['max_amount']}",
                str(row["id"]),
            )
        if row["requires_approval_above"] is not None and amount > float(row["requires_approval_above"]):
            return Decision(
                "approval",
                f"Amount {amount} > approval threshold {row['requires_approval_above']}",
                str(row["id"]),
            )

    if row["frequency_per_user_per_day"] and end_user_id:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        k = tenant_key(tenant_id, "freq", end_user_id, tool_name, day)
        count = await incr_with_ttl(k, ttl_seconds=DEFAULT_DAILY_FREQ_TTL)
        if count > int(row["frequency_per_user_per_day"]):
            return Decision(
                "deny",
                f"Daily limit {row['frequency_per_user_per_day']} exceeded for end user",
                str(row["id"]),
            )

    if sentiment == "frustrated" and tool_name not in SOFT_TOOLS:
        return Decision(
            "approval",
            "Customer frustration detected; routing to human approval",
            str(row["id"]),
        )

    return Decision("allow", "Within policy", str(row["id"]))


def _extract_amount(args: dict):
    for key in ("amount", "refund_amount", "value"):
        v = args.get(key)
        if v is None:
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None
