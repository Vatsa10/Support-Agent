from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from core.state import SupportAgentState
from core.graph import support_agent

router = APIRouter()

# In-memory storage (use Redis in production)
conversations = {}

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
    """Handle chat request"""
    
    try:
        # Generate IDs
        thread_id = request.thread_id or str(uuid.uuid4())
        conversation_key = f"{request.user_id}:{thread_id}"
        
        # Load or create conversation history
        if conversation_key not in conversations:
            conversations[conversation_key] = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "user_id": request.user_id
            }
        
        conv = conversations[conversation_key]
        
        # Build messages
        messages = []
        for msg in conv["messages"]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Create state
        state = SupportAgentState(
            user_id=request.user_id,
            thread_id=thread_id,
            session_start=conv["created_at"],
            messages=messages,
            current_query=request.message,
            category="",
            intent="",
            confidence_score=0.0,
            user_sentiment="neutral",
            retrieved_docs=[],
            retrieved_context="",
            retrieval_scores={},
            draft_response="",
            final_response="",
            requires_escalation=False,
            escalation_reason="",
            ticket_id="",
            resolution_status="pending",
            processing_time=0.0,
            model_used=""
        )
        
        # Run agent
        result = support_agent.invoke(state)
        
        # Update conversation history
        conv["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        
        conv["messages"].append({
            "role": "assistant",
            "content": result["final_response"],
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            thread_id=thread_id,
            response=result["final_response"],
            ticket_id=result.get("ticket_id"),
            status=result["resolution_status"],
            metadata={
                "category": result["category"],
                "intent": result["intent"],
                "sentiment": result["user_sentiment"],
                "confidence": result["confidence_score"],
                "escalated": result["requires_escalation"],
                "retrieval_scores": result.get("retrieval_scores", {})
            }
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
