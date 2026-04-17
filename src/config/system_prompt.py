import os
from pathlib import Path


def load_system_prompt() -> str:
    """Load base system prompt from file."""

    prompt_path = Path(__file__).parent.parent / "prompt.md"

    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return """You are a helpful, empathetic customer support agent.

Guidelines:
- Keep responses concise and helpful
- Use warm, professional tone
- Use conversation history to maintain context
- Acknowledge customer sentiment
- If unsure, offer to escalate"""


def get_system_prompt(state: dict = None, conversation_history: str = "") -> str:
    """Generate system prompt with context and conversation history.

    Args:
        state: Optional dict with classification, retrieved_context, etc.
        conversation_history: Formatted string of previous messages

    Returns:
        Complete system prompt string
    """

    system_prompt = load_system_prompt()

    if conversation_history:
        system_prompt += f"""

## Current Conversation History

{conversation_history}

Use the conversation history above to maintain context and provide personalized responses.
Remember any details the user has shared in previous messages."""

    if state:
        category = state.get("classification", {}).get("category", "general")
        sentiment = state.get("classification", {}).get("sentiment", "neutral")
        confidence = state.get("classification", {}).get("confidence_score", 0.0)
        context = state.get("retrieved_context", "")

        system_prompt += f"""

## Current Query Context

Category: {category}
Customer Sentiment: {sentiment}
Confidence Score: {confidence:.2%}

Retrieved Knowledge Base Context:
{context}

Important: If confidence is below threshold or you don't have clear answer, suggest escalation."""

    return system_prompt
