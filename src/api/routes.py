from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from typing import TypedDict, Annotated, Sequence
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
import operator
from agents.react import run_react_agent

router = APIRouter()

conversations = {}


class ReActAgentState(TypedDict):
    user_id: str
    thread_id: str
    session_start: str
    messages: Annotated[Sequence[HumanMessage], operator.add]
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

    steps: list
    final_answer: str


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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat request using ReACT agent"""

    try:
        thread_id = request.thread_id or str(uuid.uuid4())
        conversation_key = f"{request.user_id}:{thread_id}"

        if conversation_key not in conversations:
            conversations[conversation_key] = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "user_id": request.user_id,
            }

        conv = conversations[conversation_key]

        messages = []
        for msg in conv["messages"]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=request.message))

        state = ReActAgentState(
            user_id=request.user_id,
            thread_id=thread_id,
            session_start=conv["created_at"],
            messages=messages,
            current_query=request.message,
            thought="",
            action="",
            action_input={},
            observation="",
            classification={},
            retrieved_context="",
            retrieval_scores={},
            response="",
            requires_escalation=False,
            ticket_id=None,
            resolution_status="pending",
            steps=[],
            final_answer="",
        )

        result = run_react_agent(state)

        conv["messages"].append(
            {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        conv["messages"].append(
            {
                "role": "assistant",
                "content": result.get("final_answer", result.get("response", "")),
                "timestamp": datetime.now().isoformat(),
            }
        )

        final_response = result.get("final_answer", result.get("response", ""))

        return ChatResponse(
            thread_id=thread_id,
            response=final_response,
            ticket_id=result.get("ticket_id"),
            status=result.get("resolution_status", "pending"),
            metadata={
                "category": result.get("classification", {}).get("category", "unknown"),
                "intent": result.get("classification", {}).get("intent", "unknown"),
                "sentiment": result.get("classification", {}).get(
                    "sentiment", "neutral"
                ),
                "confidence": result.get("classification", {}).get(
                    "confidence_score", 0.0
                ),
                "escalated": result.get("requires_escalation", False),
                "retrieval_scores": result.get("retrieval_scores", {}),
                "steps": result.get("steps", []),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{user_id}/{thread_id}")
async def get_history(user_id: str, thread_id: str):
    """Get conversation history"""

    conversation_key = f"{user_id}:{thread_id}"

    if conversation_key not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversations[conversation_key]


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
