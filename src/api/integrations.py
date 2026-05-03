"""Admin endpoints for connectors, policies, JWT, approvals, billing."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import get_or_create_jwt_secret, require_admin
from billing.meter import monthly_summary
from connectors.base import KIND_TO_CLASS
from db.pool import sys_conn, tenant_conn
from security.crypto import decrypt_json, encrypt_json
from tools import actions as actions_mod
from tools.idempotency import finalize as idem_finalize
from tools.registry import invalidate_kinds_cache

import connectors.stripe_connector  # noqa: F401
import connectors.shopify_connector  # noqa: F401
import connectors.zendesk_connector  # noqa: F401
import connectors.webhook_connector  # noqa: F401

router = APIRouter()


# --------- helpers ----------------------------------------------------------

async def _ensure_tenant_exists(tenant_id: str) -> None:
    async with sys_conn() as conn:
        row = await conn.fetchrow("SELECT id FROM tenants WHERE id = $1", tenant_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")


# --------- integrations -----------------------------------------------------

class IntegrationCreate(BaseModel):
    kind: str = Field(..., description="stripe | shopify | zendesk | generic_webhook")
    label: str = "default"
    creds: dict
    config: dict = {}
    enabled: bool = True


class IntegrationOut(BaseModel):
    id: str
    kind: str
    label: str
    enabled: bool
    config: dict


@router.post("/tenants/{tenant_id}/integrations", response_model=IntegrationOut)
async def create_integration(
    tenant_id: str,
    body: IntegrationCreate,
    _admin: bool = Depends(require_admin),
):
    await _ensure_tenant_exists(tenant_id)
    if body.kind not in KIND_TO_CLASS:
        raise HTTPException(status_code=400, detail=f"Unknown connector kind: {body.kind}")

    enc = encrypt_json(body.creds)

    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tenant_integrations
                (tenant_id, kind, label, encrypted_creds, config, enabled)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2, $3, $4, $5)
            ON CONFLICT (tenant_id, kind, label) DO UPDATE
                SET encrypted_creds = EXCLUDED.encrypted_creds,
                    config = EXCLUDED.config,
                    enabled = EXCLUDED.enabled
            RETURNING id, kind, label, enabled, config
            """,
            body.kind, body.label, enc, json.dumps(body.config), body.enabled,
        )
    await invalidate_kinds_cache(tenant_id)
    return IntegrationOut(
        id=str(row["id"]),
        kind=row["kind"],
        label=row["label"],
        enabled=row["enabled"],
        config=dict(row["config"] or {}),
    )


@router.get("/tenants/{tenant_id}/integrations", response_model=list[IntegrationOut])
async def list_integrations(tenant_id: str, _admin: bool = Depends(require_admin)):
    await _ensure_tenant_exists(tenant_id)
    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(
            "SELECT id, kind, label, enabled, config FROM tenant_integrations ORDER BY created_at"
        )
    return [
        IntegrationOut(
            id=str(r["id"]),
            kind=r["kind"],
            label=r["label"],
            enabled=r["enabled"],
            config=dict(r["config"] or {}),
        )
        for r in rows
    ]


@router.delete("/tenants/{tenant_id}/integrations/{integration_id}")
async def delete_integration(
    tenant_id: str, integration_id: str, _admin: bool = Depends(require_admin)
):
    await _ensure_tenant_exists(tenant_id)
    async with tenant_conn(tenant_id) as conn:
        result = await conn.execute(
            "DELETE FROM tenant_integrations WHERE id = $1", integration_id
        )
    await invalidate_kinds_cache(tenant_id)
    return {"deleted": result.endswith("1")}


# --------- policies ---------------------------------------------------------

class PolicyUpsert(BaseModel):
    tool_name: str
    allow: bool = False
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    requires_approval_above: Optional[float] = None
    frequency_per_user_per_day: Optional[int] = None
    blocked_categories: Optional[list[str]] = None
    extra: dict = {}


@router.post("/tenants/{tenant_id}/policies")
async def upsert_policy(
    tenant_id: str, body: PolicyUpsert, _admin: bool = Depends(require_admin)
):
    await _ensure_tenant_exists(tenant_id)
    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO action_policies
                (tenant_id, tool_name, allow, max_amount, currency,
                 requires_approval_above, frequency_per_user_per_day,
                 blocked_categories, extra)
            VALUES (current_setting('app.tenant_id')::uuid,
                    $1, $2, $3, $4, $5, $6, $7, $8::jsonb)
            ON CONFLICT (tenant_id, tool_name) DO UPDATE
                SET allow = EXCLUDED.allow,
                    max_amount = EXCLUDED.max_amount,
                    currency = EXCLUDED.currency,
                    requires_approval_above = EXCLUDED.requires_approval_above,
                    frequency_per_user_per_day = EXCLUDED.frequency_per_user_per_day,
                    blocked_categories = EXCLUDED.blocked_categories,
                    extra = EXCLUDED.extra,
                    updated_at = now()
            RETURNING id
            """,
            body.tool_name, body.allow, body.max_amount, body.currency,
            body.requires_approval_above, body.frequency_per_user_per_day,
            body.blocked_categories, json.dumps(body.extra),
        )
    return {"policy_id": str(row["id"]), "tool_name": body.tool_name}


@router.get("/tenants/{tenant_id}/policies")
async def list_policies(tenant_id: str, _admin: bool = Depends(require_admin)):
    await _ensure_tenant_exists(tenant_id)
    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(
            "SELECT * FROM action_policies ORDER BY tool_name"
        )
    return [
        {
            "id": str(r["id"]),
            "tool_name": r["tool_name"],
            "allow": r["allow"],
            "max_amount": float(r["max_amount"]) if r["max_amount"] is not None else None,
            "currency": r["currency"],
            "requires_approval_above": float(r["requires_approval_above"])
                if r["requires_approval_above"] is not None else None,
            "frequency_per_user_per_day": r["frequency_per_user_per_day"],
            "blocked_categories": list(r["blocked_categories"] or []),
            "extra": dict(r["extra"] or {}),
        }
        for r in rows
    ]


# --------- JWT secret -------------------------------------------------------

class JwtSecretOut(BaseModel):
    tenant_id: str
    secret: str
    alg: str = "HS256"
    note: str = "Store this securely. Rotate via ?rotate=true."


@router.post("/tenants/{tenant_id}/jwt-secret", response_model=JwtSecretOut)
async def issue_jwt_secret(
    tenant_id: str, rotate: bool = False, _admin: bool = Depends(require_admin)
):
    await _ensure_tenant_exists(tenant_id)
    secret = await get_or_create_jwt_secret(tenant_id, rotate=rotate)
    return JwtSecretOut(tenant_id=tenant_id, secret=secret)


# --------- approvals --------------------------------------------------------

class ApprovalDecisionBody(BaseModel):
    decision: str  # "approve" | "reject"
    reason: Optional[str] = None
    decided_by: Optional[str] = None


@router.get("/tenants/{tenant_id}/approvals")
async def list_pending_approvals(
    tenant_id: str, _admin: bool = Depends(require_admin)
):
    await _ensure_tenant_exists(tenant_id)
    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(
            """
            SELECT a.id, a.action_run_id, a.status, a.reason, a.created_at,
                   r.tool_name, r.args, r.user_id, r.end_user_id, r.thread_id
            FROM approvals a
            JOIN action_runs r ON r.id = a.action_run_id
            WHERE a.status = 'pending'
            ORDER BY a.created_at DESC
            """,
        )
    return [
        {
            "id": str(r["id"]),
            "action_run_id": str(r["action_run_id"]),
            "status": r["status"],
            "reason": r["reason"],
            "created_at": r["created_at"].isoformat(),
            "tool_name": r["tool_name"],
            "args": dict(r["args"] or {}),
            "user_id": r["user_id"],
            "end_user_id": r["end_user_id"],
            "thread_id": r["thread_id"],
        }
        for r in rows
    ]


@router.post("/approvals/{approval_id}/decision")
async def decide_approval(
    approval_id: str,
    body: ApprovalDecisionBody,
    _admin: bool = Depends(require_admin),
):
    if body.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be approve|reject")

    # Approvals row stores tenant_id; resolve before opening tenant_conn
    async with sys_conn() as conn:
        ap = await conn.fetchrow(
            """
            SELECT a.tenant_id, a.action_run_id, a.status,
                   r.tool_name, r.args, r.user_id, r.end_user_id, r.thread_id, r.idempotency_key
            FROM approvals a
            JOIN action_runs r ON r.id = a.action_run_id
            WHERE a.id = $1
            """,
            approval_id,
        )
    if not ap:
        raise HTTPException(status_code=404, detail="Approval not found")
    if ap["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Approval already {ap['status']}")

    tenant_id = str(ap["tenant_id"])

    if body.decision == "reject":
        async with tenant_conn(tenant_id) as conn:
            await conn.execute(
                """
                UPDATE approvals
                   SET status='rejected', decision='reject', reason=$1,
                       decided_by=$2, decided_at=now()
                 WHERE id=$3
                """,
                body.reason, body.decided_by, approval_id,
            )
            await conn.execute(
                "UPDATE action_runs SET status='denied', error=$1 WHERE id=$2",
                body.reason or "rejected by reviewer", ap["action_run_id"],
            )
        await idem_finalize(tenant_id, ap["idempotency_key"], "failed",
                            {"rejected": True, "reason": body.reason})
        return {"approval_id": approval_id, "status": "rejected"}

    # approve: re-run action with skip_policy + same idempotency key (force replay path)
    args = dict(ap["args"] or {})
    # Reset the prior idempotency row so we can finalize freshly
    async with tenant_conn(tenant_id) as conn:
        await conn.execute(
            "UPDATE idempotency_keys SET status='running', result=NULL WHERE key=$1",
            ap["idempotency_key"],
        )
        await conn.execute(
            "UPDATE action_runs SET status='approved' WHERE id=$1",
            ap["action_run_id"],
        )

    result = await actions_mod.run_action(
        tenant_id=tenant_id,
        user_id=ap["user_id"],
        end_user_id=ap["end_user_id"],
        thread_id=ap["thread_id"] or "",
        tool_name=ap["tool_name"],
        args=args,
        skip_policy=True,
        idempotency_key=ap["idempotency_key"] + ":approved",
    )

    async with tenant_conn(tenant_id) as conn:
        await conn.execute(
            """
            UPDATE approvals
               SET status='approved', decision='approve', reason=$1,
                   decided_by=$2, decided_at=now()
             WHERE id=$3
            """,
            body.reason, body.decided_by, approval_id,
        )

    return {"approval_id": approval_id, "status": "approved", "result": result}


# --------- billing ----------------------------------------------------------

@router.get("/tenants/{tenant_id}/billing")
async def get_billing(tenant_id: str, _admin: bool = Depends(require_admin)):
    await _ensure_tenant_exists(tenant_id)
    return await monthly_summary(tenant_id)
