import google.generativeai as genai
from config import config
from core.state import SupportAgentState
import time

genai.configure(api_key=config.GOOGLE_API_KEY)

def generate_response_node(state: SupportAgentState) -> dict:
    """Generate response using retrieved context"""
    
    start_time = time.time()
    
    model = genai.GenerativeModel(config.LLM_MODEL)
    
    system_prompt = f"""You are a helpful, empathetic customer support agent.

Guidelines:
- Use the provided knowledge base context for accurate information
- Be concise but helpful (keep responses under 200 words)
- If unsure, offer to escalate to a specialist
- Be professional and friendly
- Acknowledge the customer's sentiment and emotion

Category: {state["category"]}
Customer Sentiment: {state["user_sentiment"]}
Confidence in retrieved context: {state["retrieval_scores"]["hybrid"]:.2%}

Knowledge Base Context:
{state["retrieved_context"]}

Important: If confidence is below {config.CONFIDENCE_THRESHOLD} or you don't have clear answer, suggest escalation."""
    
    # Build conversation history
    conversation_messages = []
    for msg in state["messages"][-5:]:
        role = "user" if msg.type == "human" else "model"
        conversation_messages.append({
            "role": role,
            "parts": [{"text": msg.content}]
        })
    
    # Current query
    conversation_messages.append({
        "role": "user",
        "parts": [{"text": state["current_query"]}]
    })
    
    # Generate response
    response = model.generate_content(
        contents=conversation_messages,
        system_instruction=system_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=config.LLM_TEMPERATURE,
            max_output_tokens=500
        )
    )
    
    response_text = response.text
    
    # Check if escalation needed
    needs_escalation = (
        state["confidence_score"] < config.CONFIDENCE_THRESHOLD or
        state["user_sentiment"] == "frustrated" or
        any(phrase in response_text.lower() for phrase in [
            "escalate", "specialist", "supervisor", "unable to help"
        ])
    )
    
    processing_time = time.time() - start_time
    
    return {
        "draft_response": response_text,
        "final_response": response_text,
        "requires_escalation": needs_escalation,
        "escalation_reason": "Low confidence or customer frustration" if needs_escalation else None,
        "processing_time": processing_time
    }
