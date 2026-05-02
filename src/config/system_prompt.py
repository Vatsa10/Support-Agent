from pathlib import Path
from typing import Optional

from cache.valkey import cache_get, cache_set, tenant_key
from db.pool import tenant_conn

_DEFAULT_PROMPT = """You are a helpful, empathetic customer support agent.

Guidelines:
- Keep responses concise and helpful
- Use warm, professional tone
- Use conversation history to maintain context
- Acknowledge customer sentiment
- If unsure, offer to escalate"""


def _load_base_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return _DEFAULT_PROMPT


async def _tenant_override(tenant_id: str) -> Optional[str]:
    cache_k = tenant_key(tenant_id, "prompt_override")
    cached = await cache_get(cache_k)
    if cached is not None:
        return cached or None  # empty string means no override

    async with tenant_conn(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT system_prompt_override FROM tenant_settings WHERE tenant_id = current_setting('app.tenant_id')::uuid"
        )
    override = (row["system_prompt_override"] if row else None) or ""
    await cache_set(cache_k, override, ttl_seconds=300)
    return override or None


async def get_system_prompt(state: dict = None, conversation_history: str = "") -> str:
    base = _load_base_prompt()

    if state and state.get("tenant_id"):
        override = await _tenant_override(state["tenant_id"])
        if override:
            base = override

    if conversation_history:
        base += f"""

## Current Conversation History

{conversation_history}

Use the conversation history above to maintain context and provide personalized responses."""

    if state:
        category = state.get("classification", {}).get("category", "general")
        sentiment = state.get("classification", {}).get("sentiment", "neutral")
        confidence = state.get("classification", {}).get("confidence_score", 0.0)
        context = state.get("retrieved_context", "")

        base += f"""

## Current Query Context

Category: {category}
Customer Sentiment: {sentiment}
Confidence Score: {confidence:.2%}

Retrieved Knowledge Base Context:
{context}

Important: If confidence is below threshold or you don't have clear answer, suggest escalation."""

    return base
