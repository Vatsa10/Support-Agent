from typing import TypedDict, List, Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator
import json
import google.generativeai as genai

from billing.meter import record_tokens
from config import config
from config.system_prompt import get_system_prompt
from db.pool import tenant_conn
from memory.buffer import agent_memory
from tools import registry


class ReActAgentState(TypedDict, total=False):
    tenant_id: str
    user_id: str
    end_user_id: Optional[str]
    thread_id: str
    session_start: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_query: str

    thought: str
    action: str
    action_input: dict
    observation: str

    classification: dict
    retrieved_context: str
    retrieval_scores: dict

    response: str
    requires_escalation: bool
    ticket_id: Optional[str]
    action_run_id: Optional[str]
    pending_approval_id: Optional[str]
    resolution_status: str

    steps: List[str]
    final_answer: str

    # internal
    _tool_callables: dict
    _tool_specs: list
    _conversation_history: list


def _usage(response) -> tuple[int, int]:
    um = getattr(response, "usage_metadata", None)
    if not um:
        return 0, 0
    return int(getattr(um, "prompt_token_count", 0) or 0), int(getattr(um, "candidates_token_count", 0) or 0)


class ReActAgent:
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.model = genai.GenerativeModel(config.LLM_MODEL)

    async def think(self, state: ReActAgentState) -> dict:
        tenant_id = state["tenant_id"]
        user_id = state["user_id"]
        thread_id = state["thread_id"]

        conversation_history = await agent_memory.get_formatted_history(
            tenant_id, user_id, thread_id, last_n=3
        )
        system_prompt = await get_system_prompt(state, conversation_history)

        tool_block = registry.render_tool_block(state.get("_tool_specs") or [])

        thought_prompt = f"""{system_prompt}

## Current Query
{state['current_query']}

## Previous Reasoning Steps
{chr(10).join(state.get('steps', []))}

## Available Actions
{tool_block}

Decide what to do next. Choose ONE action and respond in JSON format.
{{
    "thought": "Your reasoning about what to do next",
    "action": "action_name",
    "action_input": {{"key": "value"}}
}}"""

        response = self.model.generate_content(thought_prompt)
        in_tok, out_tok = _usage(response)
        await record_tokens(tenant_id, user_id, thread_id, in_tok, out_tok, model=config.LLM_MODEL)

        try:
            result = json.loads(response.text)
        except Exception:
            result = {
                "thought": "I need to classify the intent first",
                "action": "classify_intent",
                "action_input": {"query": state["current_query"]},
            }

        return {
            "thought": result.get("thought", ""),
            "action": result.get("action", "classify_intent"),
            "action_input": result.get(
                "action_input", {"query": state["current_query"]}
            ),
        }

    async def _audit(
        self, state: ReActAgentState, tool_name: str, inp: dict, out: dict
    ) -> None:
        try:
            async with tenant_conn(state["tenant_id"]) as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_log
                        (tenant_id, user_id, thread_id, tool_name, input, output, reasoning)
                    VALUES (current_setting('app.tenant_id')::uuid, $1, $2, $3, $4, $5, $6)
                    """,
                    state["user_id"],
                    state["thread_id"],
                    tool_name,
                    json.dumps(inp, default=str),
                    json.dumps({k: v for k, v in out.items() if k not in ("response",)}, default=str),
                    state.get("thought", ""),
                )
        except Exception as e:
            print(f"audit write failed: {e}")

    async def act(
        self, action: str, action_input: dict, state: ReActAgentState
    ) -> dict:
        callables: dict = state.get("_tool_callables") or {}
        if action == "END":
            out = {
                "observation": "Task completed",
                "response": state.get(
                    "response",
                    "I'm here to help. Can you please clarify your question?",
                ),
            }
            await self._audit(state, action, action_input, out)
            return out

        fn = callables.get(action)
        if fn is None:
            out = {"observation": f"Unknown or disabled action: {action}"}
            await self._audit(state, action, action_input, out)
            return out

        try:
            # Read-only callables take (args). Action wrappers take (args, state).
            if _wants_state(fn):
                result = await fn(action_input or {}, state)
            else:
                result = await fn(action_input or {})
        except Exception as e:
            out = {"observation": f"Tool {action} errored: {e}"}
            await self._audit(state, action, action_input, out)
            return out

        out = _normalize_tool_output(action, result, state)
        await self._audit(state, action, action_input, out)
        return out

    async def run(self, state: ReActAgentState) -> dict:
        tenant_id = state["tenant_id"]
        user_id = state["user_id"]
        thread_id = state["thread_id"]

        await agent_memory.add_user_message(
            tenant_id, user_id, thread_id, state["current_query"]
        )

        # Pre-load tool registry + history for this run
        callables, specs = await registry.resolve_for(state)
        state["_tool_callables"] = callables
        state["_tool_specs"] = specs
        state["_conversation_history"] = await agent_memory.get_conversation_history(
            tenant_id, user_id, thread_id
        )

        iteration = 0
        while iteration < self.max_iterations:
            thought = await self.think(state)
            state["thought"] = thought["thought"]
            state["action"] = thought["action"]
            state["action_input"] = thought["action_input"]

            step = (
                f"Thought: {state['thought']}\n"
                f"Action: {state['action']}\n"
                f"Action Input: {state['action_input']}"
            )
            state["steps"].append(step)

            terminal = state["action"] == "END" or (
                state["action"] == "generate_response"
                and not state.get("requires_escalation")
            )

            act_result = await self.act(state["action"], state["action_input"], state)
            _merge(state, act_result)

            if state.get("pending_approval_id"):
                state["resolution_status"] = "pending_approval"
                state["response"] = act_result.get("response") or state.get("response", "")
                break

            if terminal:
                break

            iteration += 1

        if state.get("requires_escalation") and not state.get("ticket_id"):
            ticket_fn = callables.get("create_ticket")
            if ticket_fn is not None:
                ticket_result = await ticket_fn({"reason": state.get("observation", "")})
                state["ticket_id"] = ticket_result.get("ticket_id")
                state["response"] = ticket_result.get("response", state.get("response", ""))
                state["resolution_status"] = "escalated"
        elif state.get("response"):
            state.setdefault("resolution_status", "resolved")
        else:
            state["response"] = state.get(
                "observation", "I'm here to help. Can you please clarify your question?"
            )
            state.setdefault("resolution_status", "resolved")

        state["final_answer"] = state.get("response", state.get("observation", ""))
        await agent_memory.add_ai_message(
            tenant_id, user_id, thread_id, state["final_answer"]
        )

        # Strip internal-only keys before returning
        for k in ("_tool_callables", "_tool_specs", "_conversation_history"):
            state.pop(k, None)
        return state


def _wants_state(fn) -> bool:
    """Heuristic: action wrappers accept (args, state)."""
    code = getattr(fn, "__code__", None)
    if not code:
        return False
    return code.co_argcount >= 2


def _normalize_tool_output(action: str, result: dict, state: ReActAgentState) -> dict:
    """Convert per-tool result dicts into the keys ReACT.run expects on `state`."""
    if action == "knowledge_search":
        return {
            "observation": f"Found {len(result.get('results', []))} relevant docs.",
            "retrieved_context": result.get("context", ""),
            "retrieval_scores": result.get("scores", {}),
        }
    if action == "classify_intent":
        return {
            "observation": (
                f"Classified as {result.get('category')}/{result.get('intent')}, "
                f"sentiment={result.get('sentiment')}"
            ),
            "classification": result,
        }
    if action == "generate_response":
        return {
            "observation": f"Generated response: {result.get('response', '')[:80]}...",
            "response": result.get("response", ""),
            "requires_escalation": bool(result.get("needs_escalation")),
        }
    if action == "create_ticket":
        return {
            "observation": f"Created ticket {result.get('ticket_id')}",
            "ticket_id": result.get("ticket_id"),
            "response": result.get("response", ""),
            "requires_escalation": True,
        }

    # Action-tool result (refund/replace/cancel/close/etc.)
    obs_bits = []
    if result.get("ok"):
        obs_bits.append(f"Action {action} succeeded")
    else:
        obs_bits.append(f"Action {action} did not complete")
    if result.get("denied"):
        obs_bits.append("(policy denied)")
    if result.get("pending_approval"):
        obs_bits.append("(pending human approval)")
    out = {
        "observation": " ".join(obs_bits),
        "response": result.get("response", ""),
        "action_run_id": result.get("action_run_id"),
    }
    if result.get("pending_approval"):
        out["pending_approval_id"] = result.get("approval_id")
    return out


def _merge(state: ReActAgentState, act_result: dict) -> None:
    for k in (
        "observation",
        "classification",
        "retrieved_context",
        "retrieval_scores",
        "response",
        "requires_escalation",
        "ticket_id",
        "action_run_id",
        "pending_approval_id",
    ):
        if k in act_result and act_result[k] is not None:
            state[k] = act_result[k]


react_agent = ReActAgent()


async def run_react_agent(state: ReActAgentState) -> dict:
    return await react_agent.run(state)
