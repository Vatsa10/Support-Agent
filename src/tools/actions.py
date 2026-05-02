"""Side-effecting action tools wired to per-tenant connectors.

Each action follows: idempotency.reserve -> policy.evaluate -> connector.execute
                  -> action_runs row -> idempotency.finalize.
"""
import json
from typing import Callable, Optional

from connectors.base import Connector, ToolSpec
from connectors.base import load_connector as _load
from db.pool import tenant_conn
from policy.engine import evaluate as policy_evaluate
from security.crypto import decrypt_json
from tools.idempotency import derive_key, finalize, reserve


# tool_name -> connector kind that owns it
TOOL_TO_KIND = {
    "issue_refund": "stripe",
    "cancel_subscription": "stripe",
    "cancel_order": "shopify",
    "replace_order": "shopify",
    "close_zendesk_ticket": "zendesk",
    "comment_zendesk_ticket": "zendesk",
    "generic_webhook_call": "generic_webhook",
}


async def _load_connector_for(tenant_id: str, kind: str) -> Optional[Connector]:
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """
            SELECT encrypted_creds, config
            FROM tenant_integrations
            WHERE kind = $1 AND enabled = true
            ORDER BY created_at ASC
            LIMIT 1
            """,
            kind,
        )
    if not row:
        return None
    creds = decrypt_json(row["encrypted_creds"])
    config = dict(row["config"] or {})
    return _load(kind, creds, config)


async def _record_run(
    tenant_id: str,
    user_id: str,
    end_user_id: Optional[str],
    thread_id: str,
    tool_name: str,
    args: dict,
    status: str,
    result: dict | None,
    error: Optional[str],
    idempotency_key: str,
) -> str:
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO action_runs
                (tenant_id, user_id, end_user_id, thread_id, tool_name,
                 args, status, result, error, idempotency_key)
            VALUES (current_setting('app.tenant_id')::uuid,
                    $1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            user_id,
            end_user_id,
            thread_id,
            tool_name,
            json.dumps(args, default=str),
            status,
            json.dumps(result, default=str) if result is not None else None,
            error,
            idempotency_key,
        )
    return str(row["id"])


async def _create_approval(tenant_id: str, action_run_id: str, reason: str) -> str:
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO approvals (tenant_id, action_run_id, reason)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2)
            RETURNING id
            """,
            action_run_id,
            reason,
        )
    return str(row["id"])


async def run_action(
    *,
    tenant_id: str,
    user_id: str,
    end_user_id: Optional[str],
    thread_id: str,
    tool_name: str,
    args: dict,
    sentiment: Optional[str] = None,
    skip_policy: bool = False,
    idempotency_key: Optional[str] = None,
) -> dict:
    """Generic action runner. Action tools are thin wrappers over this."""
    kind = TOOL_TO_KIND.get(tool_name)
    if kind is None:
        return {"ok": False, "error": f"unknown action tool {tool_name}"}

    key = idempotency_key or derive_key(tenant_id, thread_id, tool_name, args)

    fresh, cached = await reserve(tenant_id, key, tool_name)
    if cached is not None:
        return {"ok": True, "replay": True, "result": cached, "idempotency_key": key}
    if not fresh:
        return {
            "ok": False,
            "error": "action already in flight",
            "idempotency_key": key,
        }

    if not skip_policy:
        decision = await policy_evaluate(
            tenant_id=tenant_id,
            tool_name=tool_name,
            args=args,
            end_user_id=end_user_id,
            sentiment=sentiment,
        )
        if decision.decision == "deny":
            run_id = await _record_run(
                tenant_id, user_id, end_user_id, thread_id, tool_name, args,
                "denied", {"reason": decision.reason}, decision.reason, key,
            )
            await finalize(tenant_id, key, "failed", {"denied": True, "reason": decision.reason})
            return {
                "ok": False,
                "denied": True,
                "reason": decision.reason,
                "action_run_id": run_id,
                "response": (
                    "I can't take that action automatically due to policy. "
                    "Please contact support; a human agent will follow up."
                ),
            }
        if decision.decision == "approval":
            run_id = await _record_run(
                tenant_id, user_id, end_user_id, thread_id, tool_name, args,
                "pending_approval", {"reason": decision.reason}, None, key,
            )
            approval_id = await _create_approval(tenant_id, run_id, decision.reason)
            await finalize(
                tenant_id, key, "pending_approval",
                {"approval_id": approval_id, "reason": decision.reason},
            )
            return {
                "ok": True,
                "pending_approval": True,
                "action_run_id": run_id,
                "approval_id": approval_id,
                "reason": decision.reason,
                "response": (
                    "I've queued this action for human approval. You'll be notified once a reviewer decides."
                ),
            }

    connector = await _load_connector_for(tenant_id, kind)
    if connector is None:
        msg = f"No enabled '{kind}' integration for tenant"
        run_id = await _record_run(
            tenant_id, user_id, end_user_id, thread_id, tool_name, args,
            "failed", None, msg, key,
        )
        await finalize(tenant_id, key, "failed", {"error": msg})
        return {"ok": False, "error": msg, "action_run_id": run_id}

    try:
        result = await connector.execute(tool_name, args)
    except Exception as e:
        run_id = await _record_run(
            tenant_id, user_id, end_user_id, thread_id, tool_name, args,
            "failed", None, str(e), key,
        )
        await finalize(tenant_id, key, "failed", {"error": str(e)})
        return {"ok": False, "error": str(e), "action_run_id": run_id}

    status = "succeeded" if result.get("ok") else "failed"
    run_id = await _record_run(
        tenant_id, user_id, end_user_id, thread_id, tool_name, args,
        status, result, result.get("error"), key,
    )
    await finalize(tenant_id, key, status, result)

    summary = (
        f"Action {tool_name} completed (external_id={result.get('external_id')})."
        if result.get("ok")
        else f"Action {tool_name} failed: {result.get('error') or result.get('data')}"
    )
    return {
        "ok": result.get("ok", False),
        "result": result,
        "action_run_id": run_id,
        "idempotency_key": key,
        "response": summary,
    }
