"""Public-key surface: /public/chat + /tenant/publishable-keys CRUD.

Publishable keys are browser-safe (prefix `rsv_pub_`). They resolve to a tenant
but cannot manage integrations / policies / KB. /public/chat is CORS-open and
rate-limited per (pub_key, end_user_id). Use this for the embed widget and
hosted chat surfaces — never expose `X-API-Key` in the browser.
"""
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import uuid

from api.auth import Tenant, require_tenant, verify_end_user_jwt
from agents.react import run_react_agent
from cache.valkey import incr_with_ttl, tenant_key
from config import config
from db.pool import sys_conn, tenant_conn


router = APIRouter()


def _make_pub_key() -> str:
    return "rsv_pub_" + secrets.token_urlsafe(24)


# ============================================================
# Tenant-scoped CRUD (/tenant/publishable-keys)
# ============================================================

tenant_router = APIRouter()


class PubKeyCreate(BaseModel):
    label: str = "default"
    allowed_origins: Optional[list[str]] = None


class PubKeyOut(BaseModel):
    id: str
    pub_key: str
    label: str
    status: str
    allowed_origins: Optional[list[str]] = None
    created_at: str
    last_used_at: Optional[str] = None


@tenant_router.post("/publishable-keys", response_model=PubKeyOut)
async def create_pub_key(body: PubKeyCreate, tenant: Tenant = Depends(require_tenant)):
    pk = _make_pub_key()
    async with tenant_conn(tenant.id) as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO publishable_keys (tenant_id, pub_key, label, allowed_origins)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2, $3)
            RETURNING id, pub_key, label, status, allowed_origins, created_at, last_used_at
            """,
            pk, body.label, body.allowed_origins,
        )
    return PubKeyOut(
        id=str(row["id"]),
        pub_key=row["pub_key"],
        label=row["label"],
        status=row["status"],
        allowed_origins=list(row["allowed_origins"] or []) or None,
        created_at=row["created_at"].isoformat(),
        last_used_at=row["last_used_at"].isoformat() if row["last_used_at"] else None,
    )


@tenant_router.get("/publishable-keys", response_model=list[PubKeyOut])
async def list_pub_keys(tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        rows = await conn.fetch(
            "SELECT id, pub_key, label, status, allowed_origins, created_at, last_used_at FROM publishable_keys ORDER BY created_at DESC"
        )
    return [
        PubKeyOut(
            id=str(r["id"]),
            pub_key=r["pub_key"],
            label=r["label"],
            status=r["status"],
            allowed_origins=list(r["allowed_origins"] or []) or None,
            created_at=r["created_at"].isoformat(),
            last_used_at=r["last_used_at"].isoformat() if r["last_used_at"] else None,
        )
        for r in rows
    ]


@tenant_router.delete("/publishable-keys/{pk_id}")
async def revoke_pub_key(pk_id: str, tenant: Tenant = Depends(require_tenant)):
    async with tenant_conn(tenant.id) as conn:
        result = await conn.execute(
            "UPDATE publishable_keys SET status = 'revoked' WHERE id = $1",
            pk_id,
        )
    return {"revoked": result.endswith("1")}


# ============================================================
# /public/chat — CORS-open, pub-key auth, rate-limited
# ============================================================


async def _resolve_pub_key(pk: str, origin: Optional[str]) -> str:
    """Returns tenant_id for a valid pub key, raises 401 otherwise."""
    async with sys_conn() as conn:
        row = await conn.fetchrow(
            "SELECT tenant_id, status, allowed_origins FROM publishable_keys WHERE pub_key = $1",
            pk,
        )
    if not row or row["status"] != "active":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid publishable key")
    allowed = row["allowed_origins"] or []
    if allowed and origin and origin not in allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Origin {origin} not allowed for this key")
    # Best-effort touch
    try:
        async with sys_conn() as conn:
            await conn.execute("UPDATE publishable_keys SET last_used_at = now() WHERE pub_key = $1", pk)
    except Exception:
        pass
    return str(row["tenant_id"])


async def _enforce_public_rate_limit(tenant_id: str, who: str) -> None:
    minute = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = tenant_key(tenant_id, "rl_pub", who, minute)
    count = await incr_with_ttl(key, ttl_seconds=70)
    if count > config.RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


class PublicChatBody(BaseModel):
    message: str
    publishable_key: str
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    end_user_jwt: Optional[str] = None
    context: Optional[dict] = None


@router.post("/chat")
async def public_chat(body: PublicChatBody, request: Request):
    origin = request.headers.get("origin")
    tenant_id = await _resolve_pub_key(body.publishable_key, origin)

    end_user_id = None
    if body.end_user_jwt:
        end_user_id = await verify_end_user_jwt(body.end_user_jwt, tenant_id)

    user_id = end_user_id or body.user_id or f"anon_{secrets.token_hex(6)}"
    thread_id = body.thread_id or str(uuid.uuid4())

    await _enforce_public_rate_limit(tenant_id, end_user_id or request.client.host or "anon")

    state = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "end_user_id": end_user_id,
        "thread_id": thread_id,
        "session_start": datetime.now(timezone.utc).isoformat(),
        "messages": [HumanMessage(content=body.message)],
        "current_query": body.message,
        "thought": "",
        "action": "",
        "action_input": {},
        "observation": "",
        "classification": {},
        "retrieved_context": "",
        "retrieval_scores": {},
        "response": "",
        "requires_escalation": False,
        "ticket_id": None,
        "resolution_status": "pending",
        "steps": [],
        "final_answer": "",
    }
    if body.context:
        state["classification"] = {"context": body.context}

    try:
        result = await run_react_agent(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    cls = result.get("classification", {}) or {}
    return {
        "thread_id": thread_id,
        "user_id": user_id,
        "response": result.get("final_answer", result.get("response", "")),
        "ticket_id": result.get("ticket_id"),
        "status": result.get("resolution_status", "pending"),
        "action_run_id": result.get("action_run_id"),
        "pending_approval_id": result.get("pending_approval_id"),
        "metadata": {
            "category": cls.get("category", "unknown"),
            "intent": cls.get("intent", "unknown"),
            "sentiment": cls.get("sentiment", "neutral"),
            "escalated": result.get("requires_escalation", False),
        },
    }
