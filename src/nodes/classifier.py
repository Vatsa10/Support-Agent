import google.generativeai as genai
from config import config
from core.state import SupportAgentState
import json
import time

genai.configure(api_key=config.GOOGLE_API_KEY)

def classify_intent_node(state: SupportAgentState) -> dict:
    """Use Gemini to classify intent and sentiment"""
    
    start_time = time.time()
    
    model = genai.GenerativeModel(config.LLM_MODEL)
    
    # Build conversation context
    conversation_text = ""
    if state["messages"]:
        for msg in state["messages"][-5:]:
            role = "User" if msg.type == "human" else "Assistant"
            conversation_text += f"{role}: {msg.content}\n"
    
    conversation_text += f"User: {state['current_query']}"
    
    # Classification prompt
    prompt = f"""Analyze this customer support query and classify it.

Conversation:
{conversation_text}

Provide analysis in JSON format:
{{
    "category": "billing|technical|shipping|returns|general|account",
    "intent": "get_info|troubleshoot|report_issue|request_action|complaint",
    "sentiment": "positive|neutral|negative|frustrated",
    "confidence_score": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Return only valid JSON, no markdown formatting."""
    
    response = model.generate_content(prompt)
    
    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        result = {
            "category": "general",
            "intent": "get_info",
            "sentiment": "neutral",
            "confidence_score": 0.5,
            "reasoning": "Default classification due to parsing error"
        }
    
    processing_time = time.time() - start_time
    
    return {
        "category": result["category"],
        "intent": result["intent"],
        "user_sentiment": result["sentiment"],
        "confidence_score": result["confidence_score"],
        "processing_time": processing_time,
        "model_used": config.LLM_MODEL
    }
