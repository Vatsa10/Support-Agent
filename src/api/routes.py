from datetime import datetime, timezone
from typing import Optional, TypedDict, Annotated, Sequence
import operator
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from agents.react import run_react_agent
from api.auth import Tenant, require_tenant, verify_end_user_jwt
from cache.valkey import incr_with_ttl, tenant_key
from config import config
from memory.buffer import agent_memory

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    thread_id: str
    response: str
    ticket_id: Optional[str] = None
    status: str
    metadata: dict


async def _enforce_rate_limit(tenant: Tenant, key_suffix: str) -> None:
    minute = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = tenant_key(tenant.id, "rl", key_suffix, minute)
    count = await incr_with_ttl(key, ttl_seconds=70)
    if count > config.RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tenant: Tenant = Depends(require_tenant),
    x_end_user_jwt: str = Header(default=None, alias="X-End-User-JWT"),
):
    end_user_id: str | None = None
    if x_end_user_jwt:
        end_user_id = await verify_end_user_jwt(x_end_user_jwt, tenant.id)

    await _enforce_rate_limit(tenant, end_user_id or request.user_id)

    thread_id = request.thread_id or str(uuid.uuid4())

    state = {
        "tenant_id": tenant.id,
        "user_id": request.user_id,
        "end_user_id": end_user_id,
        "thread_id": thread_id,
        "session_start": datetime.now(timezone.utc).isoformat(),
        "messages": [HumanMessage(content=request.message)],
        "current_query": request.message,
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

    try:
        result = await run_react_agent(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    final_response = result.get("final_answer", result.get("response", ""))

    return ChatResponse(
        thread_id=thread_id,
        response=final_response,
        ticket_id=result.get("ticket_id"),
        status=result.get("resolution_status", "pending"),
        metadata={
            "category": result.get("classification", {}).get("category", "unknown"),
            "intent": result.get("classification", {}).get("intent", "unknown"),
            "sentiment": result.get("classification", {}).get("sentiment", "neutral"),
            "confidence": result.get("classification", {}).get("confidence_score", 0.0),
            "escalated": result.get("requires_escalation", False),
            "retrieval_scores": result.get("retrieval_scores", {}),
            "steps": result.get("steps", []),
        },
    )


@router.get("/chat/history/{user_id}/{thread_id}")
async def get_history(
    user_id: str,
    thread_id: str,
    tenant: Tenant = Depends(require_tenant),
):
    history = await agent_memory.get_conversation_history(
        tenant.id, user_id, thread_id, limit=200
    )
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"user_id": user_id, "thread_id": thread_id, "messages": history}


@router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
