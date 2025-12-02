import uuid
from core.state import SupportAgentState
import time

def escalate_to_human_node(state: SupportAgentState) -> dict:
    """Create ticket and escalate to human"""
    
    start_time = time.time()
    
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    escalation_response = f"""Thank you for reaching out. Your inquiry requires specialist attention.

I've created support ticket **{ticket_id}** and a member of our team will assist you shortly.

**Ticket Details:**
- Ticket ID: {ticket_id}
- Category: {state["category"]}
- Priority: {'High' if state['user_sentiment'] == 'frustrated' else 'Normal'}
- Expected Response: Within 1 hour

You'll receive updates via email. We appreciate your patience!"""
    
    processing_time = time.time() - start_time
    
    return {
        "final_response": escalation_response,
        "ticket_id": ticket_id,
        "resolution_status": "escalated",
        "processing_time": processing_time
    }
    