from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class SupportAgentState(TypedDict):
    """Complete state for support agent conversation"""
    
    # Session info
    user_id: str
    thread_id: str
    session_start: str
    
    # Conversation
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_query: str
    
    # Classification
    category: str
    intent: str
    confidence_score: float
    user_sentiment: str  # positive, neutral, negative, frustrated
    
    # Retrieved context
    retrieved_docs: list
    retrieved_context: str
    retrieval_scores: dict  # {"dense": 0.85, "sparse": 0.78, "hybrid": 0.82}
    
    # Response
    draft_response: str
    final_response: str
    
    # Resolution
    requires_escalation: bool
    escalation_reason: str
    ticket_id: str
    resolution_status: str  # pending, resolved, escalated
    
    # Metadata
    processing_time: float
    model_used: str
