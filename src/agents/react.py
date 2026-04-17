from typing import TypedDict, List, Optional, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import json
import google.generativeai as genai
from config import config
from config.system_prompt import get_system_prompt
from memory.buffer import agent_memory
from tools.definitions import (
    knowledge_search_tool,
    classify_intent_tool,
    create_ticket_tool,
    generate_response_tool,
)


class ReActAgentState(TypedDict):
    user_id: str
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
    resolution_status: str

    steps: List[str]
    final_answer: str


class ReActAgent:
    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self.model = genai.GenerativeModel(config.LLM_MODEL)

    def think(self, state: ReActAgentState) -> dict:
        session_id = state.get("thread_id", "default")
        conversation_history = agent_memory.get_formatted_history(session_id, last_n=3)

        thought_prompt = f"""You are a helpful, empathetic customer support agent. Be warm, professional, and concise.

## Current Conversation
{conversation_history}

Current Query: {state["current_query"]}

Previous Steps:
{chr(10).join(state.get("steps", []))}

## Available Actions
- knowledge_search: Search the knowledge base for relevant information
- classify_intent: Classify the user's query intent, category, and sentiment  
- create_ticket: Create a support ticket for human escalation
- generate_response: Generate a final response to the user

## Guidelines
- Keep responses under 200 words
- Use natural prose, not bullet points
- Acknowledge the customer's sentiment
- If unsure, offer to escalate
- Always prioritize accurate information from the knowledge base

Choose ONE action and respond in JSON:
{{
    "thought": "Your reasoning about what to do next",
    "action": "action_name",
    "action_input": {{"key": "value"}}
}}"""

        response = self.model.generate_content(thought_prompt)

        try:
            result = json.loads(response.text)
        except:
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

    def act(self, action: str, action_input: dict, state: ReActAgentState) -> dict:
        session_id = state.get("thread_id", "default")
        conversation_history = agent_memory.get_conversation_history(session_id)

        if action == "knowledge_search":
            result = knowledge_search_tool.run(
                query=action_input.get("query", state["current_query"]),
                category=action_input.get("category"),
                top_k=action_input.get("top_k"),
            )
            return {
                "observation": f"Found {len(result['results'])} relevant documents. Context: {result['context'][:500]}...",
                "retrieved_context": result["context"],
                "retrieval_scores": result["scores"],
            }

        elif action == "classify_intent":
            result = classify_intent_tool.run(
                query=action_input.get("query", state["current_query"]),
                conversation_history=conversation_history,
            )
            return {
                "observation": f"Classified as {result['category']} intent: {result['intent']}, sentiment: {result['sentiment']}",
                "classification": result,
            }

        elif action == "create_ticket":
            result = create_ticket_tool.run(
                user_query=state["current_query"],
                category=state.get("classification", {}).get("category", "general"),
                sentiment=state.get("classification", {}).get("sentiment", "neutral"),
                reason=action_input.get("reason"),
            )
            return {
                "observation": f"Created ticket {result['ticket_id']}",
                "ticket_id": result["ticket_id"],
                "response": result["response"],
                "requires_escalation": True,
            }

        elif action == "generate_response":
            classification = state.get("classification", {})
            result = generate_response_tool.run(
                query=state["current_query"],
                context=state.get("retrieved_context", ""),
                category=classification.get("category", "general"),
                sentiment=classification.get("sentiment", "neutral"),
                confidence=classification.get("confidence_score", 0.5),
                conversation_history=conversation_history,
            )
            return {
                "observation": f"Generated response: {result['response'][:100]}...",
                "response": result["response"],
                "requires_escalation": result["needs_escalation"],
            }

        elif action == "END":
            return {
                "observation": "Task completed",
                "response": state.get(
                    "response",
                    "I'm here to help. Can you please clarify your question?",
                ),
            }

        return {"observation": "Unknown action"}

    def run(self, state: ReActAgentState) -> dict:
        session_id = state.get("thread_id", "default")

        agent_memory.add_user_message(session_id, state["current_query"])

        iteration = 0

        while iteration < self.max_iterations:
            thought_result = self.think(state)
            state["thought"] = thought_result["thought"]
            state["action"] = thought_result["action"]
            state["action_input"] = thought_result["action_input"]

            action = state["action"]
            action_input = state["action_input"]

            step = f"Thought: {state['thought']}\nAction: {action}\nAction Input: {action_input}"
            state["steps"].append(step)

            if action == "END" or (
                action == "generate_response" and not state.get("requires_escalation")
            ):
                break

            act_result = self.act(action, action_input, state)
            state["observation"] = act_result.get("observation", "")

            if "classification" in act_result:
                state["classification"] = act_result["classification"]
            if "retrieved_context" in act_result:
                state["retrieved_context"] = act_result["retrieved_context"]
            if "retrieval_scores" in act_result:
                state["retrieval_scores"] = act_result["retrieval_scores"]
            if "response" in act_result:
                state["response"] = act_result["response"]
            if "requires_escalation" in act_result:
                state["requires_escalation"] = act_result["requires_escalation"]
            if "ticket_id" in act_result:
                state["ticket_id"] = act_result["ticket_id"]

            iteration += 1

        if state.get("requires_escalation") and not state.get("ticket_id"):
            ticket_result = create_ticket_tool.run(
                user_query=state["current_query"],
                category=state.get("classification", {}).get("category", "general"),
                sentiment=state.get("classification", {}).get("sentiment", "neutral"),
            )
            state["ticket_id"] = ticket_result["ticket_id"]
            state["response"] = ticket_result["response"]
            state["resolution_status"] = "escalated"
        elif state.get("response"):
            state["resolution_status"] = "resolved"
        else:
            state["response"] = state.get(
                "observation", "I'm here to help. Can you please clarify your question?"
            )
            state["resolution_status"] = "resolved"

        state["final_answer"] = state.get("response", state.get("observation", ""))

        agent_memory.add_ai_message(session_id, state["final_answer"])

        return state


react_agent = ReActAgent()


def run_react_agent(state: ReActAgentState) -> dict:
    return react_agent.run(state)
