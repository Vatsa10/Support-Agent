"""Self-serve tenant API (gated by X-API-Key, no admin key required).

Tenants manage their own integrations / policies / KB / approvals / billing
through these endpoints. Same handlers as /admin/* but tenant-scoped (no
cross-tenant access).
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth import Tenant, get_or_create_jwt_secret, require_tenant
from api.integrations import (
    IntegrationCreate,
    IntegrationOut,
    PolicyUpsert,
)
from billing.meter import monthly_summary
from connectors.base import KIND_TO_CLASS
from db.pool import tenant_conn
from memory.buffer import agent_memory
from security.crypto import encrypt_json
from tools import actions as actions_mod
from tools.idempotency import finalize as idem_finalize
from tools.registry import invalidate_kinds_cache
from vector_db.ingestion import AdvancedChunkingStrategy
from vector_db.retrieval import retriever

import connectors.stripe_connector  # noqa: F401
import connectors.shopify_connector  # noqa: F401
import connectors.zendesk_connector  # noqa: F401
import connectors.webhook_connector  # noqa: F401

router = APIRouter()


# ---- Integrations ---------------------------------------------------------

@router.post("/integrations", response_model=IntegrationOut)
async def create_integration(body: IntegrationCreate, tenant: Tenant = Depends(require_tenant)):
    if body.kind not in KIND_TO_CLASS:
        raise HTTPException(status_code=400, detail=f"Unknown connector kind: {body.kind}")
    enc = encrypt_json(body.creds)
    async with tenant_conn(tenant.id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tenant_integrations (tenant_id, kind, label, encrypted_creds, config, enabled)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2, $3, $4, $5)
            ON CONFLICT (tenant_id, kind, label) DO UPDATE
                SET encrypted_creds = EXCLUDED.encrypted_creds,
                    config = EXCLUDED.config,
                    enabled = EXCLUDED.enabled
            RETURNING id, kind, label, enabled, config
            """,
            body.kind, body.label, enc, json.dumps(body.config), body.enabled,
        )
    await invalidate_kinds_cache(tenant.id)
    return IntegrationOut(
        id=str(row["id"]), kind=row["kind"], label=row["label"],
        enabled=row["enabled"], config=dict(row["config"] or {}),
    )


@router.get("/integrations", response_model=list[IntegrationOut])
async def list_integrations(
    tenant: Tenant = Depends(require_tenant),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    async with tenant_conn(tenant.id) as conn:
        rows = await conn.fetch(
            "SELECT id, kind, label, enabled, config FROM tenant_integrations ORDER BY created_at LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [
        IntegrationOut(
            id=str(r["id"]), kind=r["kind"], label=r["label"],
            enabled=r["enabled"], config=dict(r["config"] or {}),
        )
        for r in rows
    ]


@router.delete("/integrations/{integration_id}")
async def delete_integration(integration_id: str, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        result = await conn.execute("DELETE FROM tenant_integrations WHERE id = $1", integration_id)
    await invalidate_kinds_cache(tenant.id)
    return {"deleted": result.endswith("1")}


# ---- Policies -------------------------------------------------------------

@router.post("/policies")
async def upsert_policy(body: PolicyUpsert, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
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


@router.get("/policies")
async def list_policies(tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        rows = await conn.fetch("SELECT * FROM action_policies ORDER BY tool_name")
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


# ---- KB upload + reindex --------------------------------------------------

class KbUploadBody(BaseModel):
    source: str = Field(..., description="Logical source name; used as metadata + dedupe key")
    text: str = Field(..., min_length=1)
    category: Optional[str] = None
    replace: bool = Field(False, description="If true, delete existing rows for this source first")


@router.post("/kb/upload")
async def kb_upload(body: KbUploadBody, tenant: Tenant = Depends(require_tenant)):
    chunker = AdvancedChunkingStrategy(chunk_size=800, chunk_overlap=200)
    chunks = chunker.chunk_with_metadata(body.text, body.source)
    if body.category:
        for c in chunks:
            c["metadata"]["category"] = body.category

    if body.replace:
        async with tenant_conn(tenant.id) as conn:
            await conn.execute("DELETE FROM kb_documents WHERE source = $1", body.source)

    n = await _index_chunks(tenant.id, chunks)
    return {"source": body.source, "chunks_indexed": n}


async def _index_chunks(tenant_id: str, chunks: list[dict]) -> int:
    """Like retriever.index_documents but does NOT wipe existing rows."""
    from vector_db.embeddings import embedding_manager

    rows = []
    for chunk in chunks:
        emb = embedding_manager.get_dense_embedding(chunk["text"])
        md = chunk.get("metadata", {})
        rows.append((
            chunk["text"],
            md.get("source"),
            md.get("section"),
            md.get("category"),
            md.get("key_phrases") or [],
            emb,
        ))
    async with tenant_conn(tenant_id) as conn:
        await conn.executemany(
            """
            INSERT INTO kb_documents
                (tenant_id, source, section, category, key_phrases, chunk_text, embedding, tsv)
            VALUES
                (current_setting('app.tenant_id')::uuid, $2, $3, $4, $5, $1, $6,
                 to_tsvector('english', $1))
            """,
            rows,
        )
    return len(rows)


@router.get("/kb/sources")
async def list_sources(
    tenant: Tenant = Depends(require_tenant),
    limit: int = Query(100, ge=1, le=500),
):
    async with tenant_conn(tenant.id) as conn:
        rows = await conn.fetch(
            "SELECT source, COUNT(*)::int AS chunks FROM kb_documents GROUP BY source ORDER BY source LIMIT $1",
            limit,
        )
    return [{"source": r["source"], "chunks": r["chunks"]} for r in rows]


@router.delete("/kb/sources/{source}")
async def delete_source(source: str, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        await conn.execute("DELETE FROM kb_documents WHERE source = $1", source)
    return {"source": source, "deleted": True}


# ---- JWT secret + approvals + billing -------------------------------------

@router.post("/jwt-secret")
async def jwt_secret(rotate: bool = False, tenant: Tenant = Depends(require_tenant)):
    secret = await get_or_create_jwt_secret(tenant.id, rotate=rotate)
    return {"tenant_id": tenant.id, "secret": secret, "alg": "HS256"}


@router.get("/approvals")
async def list_approvals(
    tenant: Tenant = Depends(require_tenant),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    async with tenant_conn(tenant.id) as conn:
        rows = await conn.fetch(
            """
            SELECT a.id, a.action_run_id, a.status, a.reason, a.created_at,
                   r.tool_name, r.args
            FROM approvals a
            JOIN action_runs r ON r.id = a.action_run_id
            WHERE a.status = 'pending'
            ORDER BY a.created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit, offset,
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
        }
        for r in rows
    ]


class ApprovalDecisionBody(BaseModel):
    decision: str
    reason: Optional[str] = None
    decided_by: Optional[str] = None


@router.post("/approvals/{approval_id}/decision")
async def decide_approval(
    approval_id: str,
    body: ApprovalDecisionBody,
    tenant: Tenant = Depends(require_tenant),
):
    if body.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be approve|reject")

    async with tenant_conn(tenant.id) as conn:
        ap = await conn.fetchrow(
            """
            SELECT a.action_run_id, a.status,
                   r.tool_name, r.args, r.user_id, r.end_user_id, r.thread_id, r.idempotency_key
            FROM approvals a JOIN action_runs r ON r.id = a.action_run_id
            WHERE a.id = $1
            """,
            approval_id,
        )
    if not ap:
        raise HTTPException(status_code=404, detail="Approval not found")
    if ap["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Approval already {ap['status']}")

    if body.decision == "reject":
        async with tenant_conn(tenant.id) as conn:
            await conn.execute(
                "UPDATE approvals SET status='rejected', decision='reject', reason=$1, decided_by=$2, decided_at=now() WHERE id=$3",
                body.reason, body.decided_by or tenant.name, approval_id,
            )
            await conn.execute(
                "UPDATE action_runs SET status='denied', error=$1 WHERE id=$2",
                body.reason or "rejected by tenant reviewer", ap["action_run_id"],
            )
        await idem_finalize(tenant.id, ap["idempotency_key"], "failed", {"rejected": True})
        return {"approval_id": approval_id, "status": "rejected"}

    result = await actions_mod.run_action(
        tenant_id=tenant.id,
        user_id=ap["user_id"],
        end_user_id=ap["end_user_id"],
        thread_id=ap["thread_id"] or "",
        tool_name=ap["tool_name"],
        args=dict(ap["args"] or {}),
        skip_policy=True,
        idempotency_key=ap["idempotency_key"] + ":approved",
    )
    async with tenant_conn(tenant.id) as conn:
        await conn.execute(
            "UPDATE approvals SET status='approved', decision='approve', reason=$1, decided_by=$2, decided_at=now() WHERE id=$3",
            body.reason, body.decided_by or tenant.name, approval_id,
        )
    return {"approval_id": approval_id, "status": "approved", "result": result}


@router.get("/billing")
async def billing(tenant: Tenant = Depends(require_tenant)):
    return await monthly_summary(tenant.id)


# ---- Dashboard aggregate stats --------------------------------------------

@router.get("/stats")
async def tenant_stats(tenant: Tenant = Depends(require_tenant)):
    """One-shot KPI roll-up for the dashboard home page."""
    async with tenant_conn(tenant.id) as conn:
        # last-30d conversations
        resolutions_30d = await conn.fetchval(
            "SELECT COUNT(*) FROM conversations WHERE started_at >= now() - interval '30 days'"
        )
        pending = await conn.fetchval(
            "SELECT COUNT(*) FROM approvals WHERE status = 'pending'"
        )
        succeeded = await conn.fetchval(
            "SELECT COUNT(*) FROM action_runs WHERE status = 'succeeded' AND created_at >= now() - interval '30 days'"
        )
        attempted = await conn.fetchval(
            "SELECT COUNT(*) FROM action_runs WHERE created_at >= now() - interval '30 days'"
        )
        escalated = await conn.fetchval(
            "SELECT COUNT(*) FROM tickets WHERE created_at >= now() - interval '30 days'"
        )
        spark_rows = await conn.fetch(
            """
            SELECT date_trunc('day', started_at)::date AS d, COUNT(*)::int AS n
            FROM conversations
            WHERE started_at >= now() - interval '15 days'
            GROUP BY d ORDER BY d
            """
        )
        recent = await conn.fetch(
            """
            SELECT c.id, c.thread_id, c.user_id, c.last_at,
                   (SELECT content FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_msg,
                   (SELECT tool_name FROM action_runs r WHERE r.thread_id = c.thread_id ORDER BY r.created_at DESC LIMIT 1) AS last_action
            FROM conversations c
            ORDER BY c.last_at DESC LIMIT 8
            """
        )
        budget_row = await conn.fetchrow(
            "SELECT monthly_token_cap FROM token_budgets WHERE tenant_id = current_setting('app.tenant_id')::uuid"
        )
        used_row = await conn.fetchrow(
            """
            SELECT COALESCE(SUM(units),0)::bigint AS used
            FROM billing_events
            WHERE event_type IN ('llm_input_tokens','llm_output_tokens')
              AND created_at >= date_trunc('month', now())
            """
        )

    resolutions_30d = int(resolutions_30d or 0)
    attempted = int(attempted or 0)
    succeeded = int(succeeded or 0)
    escalated = int(escalated or 0)
    pending = int(pending or 0)
    monthly_tokens = int((used_row or {}).get("used", 0) or 0)
    cap = int(budget_row["monthly_token_cap"]) if budget_row and budget_row["monthly_token_cap"] else 0

    deflection_rate = (1 - (escalated / resolutions_30d)) if resolutions_30d else 0.0
    action_success_rate = (succeeded / attempted) if attempted else 0.0

    return {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "kpis": {
            "resolutions_30d": resolutions_30d,
            "deflection_rate": deflection_rate,
            "action_success_rate": action_success_rate,
            "approvals_pending": pending,
            "monthly_tokens": monthly_tokens,
            "token_cap": cap,
        },
        "sparkline": [int(r["n"]) for r in spark_rows] or [0],
        "recent": [
            {
                "id": str(r["id"]),
                "thread_id": r["thread_id"],
                "user_id": r["user_id"],
                "last_at": r["last_at"].isoformat() if r["last_at"] else None,
                "last_msg": (r["last_msg"] or "")[:120],
                "last_action": r["last_action"] or "",
            }
            for r in recent
        ],
    }


@router.get("/conversations")
async def list_conversations(
    tenant: Tenant = Depends(require_tenant),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    async with tenant_conn(tenant.id) as conn:
        rows = await conn.fetch(
            """
            SELECT c.id, c.thread_id, c.user_id, c.started_at, c.last_at,
                   (SELECT content FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at ASC LIMIT 1) AS first_msg,
                   (SELECT tool_name FROM action_runs r WHERE r.thread_id = c.thread_id ORDER BY r.created_at DESC LIMIT 1) AS last_action
            FROM conversations c
            ORDER BY c.last_at DESC LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )
    return [
        {
            "id": str(r["id"]),
            "thread_id": r["thread_id"],
            "user_id": r["user_id"],
            "started_at": r["started_at"].isoformat() if r["started_at"] else None,
            "last_at": r["last_at"].isoformat() if r["last_at"] else None,
            "subject": (r["first_msg"] or "")[:120],
            "last_action": r["last_action"] or "",
        }
        for r in rows
    ]


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        c = await conn.fetchrow(
            "SELECT id, thread_id, user_id, started_at, last_at FROM conversations WHERE id = $1",
            conv_id,
        )
        if not c:
            raise HTTPException(status_code=404, detail="Conversation not found")
        msgs = await conn.fetch(
            "SELECT role, content, metadata, created_at FROM messages WHERE conversation_id = $1 ORDER BY created_at",
            conv_id,
        )
        runs = await conn.fetch(
            """
            SELECT id, tool_name, args, status, result, created_at
            FROM action_runs WHERE thread_id = $1 ORDER BY created_at
            """,
            c["thread_id"],
        )
    return {
        "id": str(c["id"]),
        "thread_id": c["thread_id"],
        "user_id": c["user_id"],
        "started_at": c["started_at"].isoformat() if c["started_at"] else None,
        "messages": [
            {"role": m["role"], "content": m["content"], "metadata": dict(m["metadata"] or {}),
             "at": m["created_at"].isoformat()}
            for m in msgs
        ],
        "actions": [
            {"id": str(r["id"]), "tool_name": r["tool_name"], "status": r["status"],
             "args": dict(r["args"] or {}), "result": dict(r["result"] or {}),
             "at": r["created_at"].isoformat()}
            for r in runs
        ],
    }


@router.get("/actions")
async def list_actions(
    tenant: Tenant = Depends(require_tenant),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    async with tenant_conn(tenant.id) as conn:
        rows = await conn.fetch(
            """
            SELECT id, tool_name, status, args, result, error, idempotency_key, created_at
            FROM action_runs ORDER BY created_at DESC LIMIT $1 OFFSET $2
            """,
            limit, offset,
        )
    return [
        {
            "id": str(r["id"]),
            "tool_name": r["tool_name"],
            "status": r["status"],
            "args": dict(r["args"] or {}),
            "result": dict(r["result"] or {}),
            "error": r["error"],
            "external_id": (r["result"] or {}).get("external_id"),
            "at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]


# ---- Token budget self-config + GDPR --------------------------------------

class BudgetBody(BaseModel):
    monthly_token_cap: Optional[int] = None
    hard_cap: bool = True
    notify_above_pct: int = 80


@router.post("/budget")
async def set_budget(body: BudgetBody, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        await conn.execute(
            """
            INSERT INTO token_budgets (tenant_id, monthly_token_cap, hard_cap, notify_above_pct)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2, $3)
            ON CONFLICT (tenant_id) DO UPDATE
                SET monthly_token_cap = EXCLUDED.monthly_token_cap,
                    hard_cap = EXCLUDED.hard_cap,
                    notify_above_pct = EXCLUDED.notify_above_pct,
                    updated_at = now()
            """,
            body.monthly_token_cap, body.hard_cap, body.notify_above_pct,
        )
    return body.model_dump()


@router.post("/end-users/{end_user_id}/delete")
async def gdpr_delete_end_user(end_user_id: str, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        # Conversations + messages
        rows = await conn.fetch(
            "SELECT id FROM conversations WHERE user_id = $1", end_user_id,
        )
        for r in rows:
            await conn.execute("DELETE FROM messages WHERE conversation_id = $1", r["id"])
        await conn.execute("DELETE FROM conversations WHERE user_id = $1", end_user_id)
        await conn.execute("DELETE FROM action_runs WHERE end_user_id = $1 OR user_id = $1", end_user_id)
        await conn.execute("DELETE FROM tickets WHERE user_id = $1", end_user_id)
    return {"end_user_id": end_user_id, "deleted": True}


@router.get("/end-users/{end_user_id}/export")
async def gdpr_export_end_user(end_user_id: str, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        convs = await conn.fetch(
            "SELECT id, thread_id, started_at, last_at FROM conversations WHERE user_id = $1",
            end_user_id,
        )
        msgs = []
        for c in convs:
            mrows = await conn.fetch(
                "SELECT role, content, created_at FROM messages WHERE conversation_id = $1 ORDER BY created_at",
                c["id"],
            )
            msgs.extend([
                {"thread_id": c["thread_id"], "role": m["role"], "content": m["content"],
                 "created_at": m["created_at"].isoformat()}
                for m in mrows
            ])
        tickets = await conn.fetch(
            "SELECT id, category, status, created_at FROM tickets WHERE user_id = $1",
            end_user_id,
        )
        actions = await conn.fetch(
            "SELECT id, tool_name, status, created_at FROM action_runs WHERE user_id = $1 OR end_user_id = $1",
            end_user_id,
        )
    return {
        "end_user_id": end_user_id,
        "conversations": [{"thread_id": c["thread_id"], "started_at": c["started_at"].isoformat()} for c in convs],
        "messages": msgs,
        "tickets": [{"id": str(t["id"]), "category": t["category"], "status": t["status"]} for t in tickets],
        "actions": [{"id": str(a["id"]), "tool_name": a["tool_name"], "status": a["status"]} for a in actions],
    }
