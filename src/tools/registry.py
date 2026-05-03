"""Per-tenant tool registry.

Resolves the set of tools available to the agent for a given tenant:
- always-on read-only tools (knowledge_search, classify_intent, generate_response, create_ticket)
- action tools whose connector kind has at least one enabled tenant_integrations row

Returns name -> async callable map plus ToolSpec list for the LLM prompt.
"""
import json
from typing import Awaitable, Callable

from cache.valkey import cache_get, cache_set, tenant_key
from connectors.base import ToolSpec, KIND_TO_CLASS
from db.pool import tenant_conn
from tools import actions
from tools.definitions import (
    classify_intent_tool,
    create_ticket_tool,
    generate_response_tool,
    knowledge_search_tool,
)

import connectors.stripe_connector  # noqa: F401  -- side effect: register
import connectors.shopify_connector  # noqa: F401
import connectors.zendesk_connector  # noqa: F401
import connectors.webhook_connector  # noqa: F401


# Read-only tool specs (advertised to LLM regardless of integrations)
READ_ONLY_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="knowledge_search",
        description="Search the knowledge base for relevant information.",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"},
                "top_k": {"type": "integer"},
            },
            "required": ["query"],
        },
    ),
    ToolSpec(
        name="classify_intent",
        description="Classify the user's query (category, intent, sentiment).",
        parameters_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
    ToolSpec(
        name="generate_response",
        description="Generate a final response using retrieved knowledge.",
        parameters_schema={"type": "object"},
    ),
    ToolSpec(
        name="create_ticket",
        description="Escalate to a human by creating a support ticket.",
        parameters_schema={
            "type": "object",
            "properties": {"reason": {"type": "string"}},
        },
    ),
]


async def _read_only_callables(state) -> dict[str, Callable[..., Awaitable[dict]]]:
    tenant_id = state["tenant_id"]
    user_id = state["user_id"]
    thread_id = state["thread_id"]

    async def _knowledge(args: dict) -> dict:
        return await knowledge_search_tool.run(
            tenant_id=tenant_id,
            query=args.get("query", state.get("current_query", "")),
            category=args.get("category"),
            top_k=args.get("top_k"),
        )

    async def _classify(args: dict) -> dict:
        history = state.get("_conversation_history") or []
        return classify_intent_tool.run(
            tenant_id=tenant_id,
            query=args.get("query", state.get("current_query", "")),
            conversation_history=history,
        )

    async def _generate(args: dict) -> dict:
        cls = state.get("classification", {})
        return generate_response_tool.run(
            tenant_id=tenant_id,
            query=args.get("query", state.get("current_query", "")),
            context=state.get("retrieved_context", ""),
            category=cls.get("category", "general"),
            sentiment=cls.get("sentiment", "neutral"),
            confidence=cls.get("confidence_score", 0.5),
            conversation_history=state.get("_conversation_history") or [],
        )

    async def _ticket(args: dict) -> dict:
        cls = state.get("classification", {})
        return await create_ticket_tool.run(
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
            user_query=state.get("current_query", ""),
            category=cls.get("category", "general"),
            sentiment=cls.get("sentiment", "neutral"),
            intent=cls.get("intent"),
            reason=args.get("reason"),
        )

    return {
        "knowledge_search": _knowledge,
        "classify_intent": _classify,
        "generate_response": _generate,
        "create_ticket": _ticket,
    }


def _action_callable(tool_name: str):
    async def _call(state, args: dict) -> dict:
        cls = state.get("classification", {})
        return await actions.run_action(
            tenant_id=state["tenant_id"],
            user_id=state["user_id"],
            end_user_id=state.get("end_user_id"),
            thread_id=state["thread_id"],
            tool_name=tool_name,
            args=args,
            sentiment=cls.get("sentiment"),
            idempotency_key=args.get("idempotency_key"),
        )

    return _call


async def _enabled_kinds(tenant_id: str) -> list[str]:
    cache_k = tenant_key(tenant_id, "enabled_kinds")
    cached = await cache_get(cache_k)
    if cached is not None:
        return json.loads(cached)

    async with tenant_conn(tenant_id) as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT kind FROM tenant_integrations WHERE enabled = true"
        )
    kinds = [r["kind"] for r in rows]
    await cache_set(cache_k, json.dumps(kinds), ttl_seconds=60)
    return kinds


async def invalidate_kinds_cache(tenant_id: str) -> None:
    from cache.valkey import cache_delete
    await cache_delete(tenant_key(tenant_id, "enabled_kinds"))


async def resolve_for(state) -> tuple[dict, list[ToolSpec]]:
    """Return (callables, specs) for tenant in `state`."""
    tenant_id = state["tenant_id"]
    callables = await _read_only_callables(state)
    specs = list(READ_ONLY_SPECS)

    kinds = await _enabled_kinds(tenant_id)
    seen: set[str] = set()
    for kind in kinds:
        cls = KIND_TO_CLASS.get(kind)
        if not cls:
            continue
        # Build dummy connector to read tool_specs (config-driven for webhook)
        config = {}
        if kind == "generic_webhook":
            # Need actual config to render correct action enum
            async with tenant_conn(tenant_id) as conn:
                row = await conn.fetchrow(
                    "SELECT config FROM tenant_integrations WHERE kind = $1 AND enabled = true ORDER BY created_at LIMIT 1",
                    kind,
                )
            config = dict(row["config"] or {}) if row else {}
        try:
            stub = cls({}, config)
            for spec in stub.tool_specs():
                if spec.name in seen:
                    continue
                seen.add(spec.name)
                spec.kind = kind
                specs.append(spec)
                callables[spec.name] = _make_action_wrapper(spec.name)
        except Exception:
            continue

    return callables, specs


def _make_action_wrapper(tool_name: str):
    fn = _action_callable(tool_name)

    async def _wrapper(args: dict, state) -> dict:
        return await fn(state, args)

    return _wrapper


def render_tool_block(specs: list[ToolSpec]) -> str:
    """Format ToolSpecs for inclusion in the LLM prompt."""
    lines = []
    for s in specs:
        params = json.dumps(s.parameters_schema, separators=(",", ":")) if s.parameters_schema else "{}"
        lines.append(f"- {s.name}: {s.description}  args_schema={params}")
    return "\n".join(lines)
