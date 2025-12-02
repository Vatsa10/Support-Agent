from langgraph.graph import StateGraph, START, END
from core.state import SupportAgentState
from nodes.classifier import classify_intent_node
from nodes.retriever import retrieve_context_node
from nodes.generator import generate_response_node
from nodes.escalator import escalate_to_human_node
import time

def create_support_agent():
    """Create LangGraph workflow for support agent"""
    
    workflow = StateGraph(SupportAgentState)
    
    # Add nodes
    workflow.add_node("classify", classify_intent_node)
    workflow.add_node("retrieve", retrieve_context_node)
    workflow.add_node("generate", generate_response_node)
    workflow.add_node("escalate", escalate_to_human_node)
    
    # Define edges
    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "retrieve")
    workflow.add_edge("retrieve", "generate")
    
    # Conditional routing
    def route_after_generate(state):
        if state["requires_escalation"]:
            return "escalate"
        return END
    
    workflow.add_conditional_edges(
        "generate",
        route_after_generate,
        {
            "escalate": "escalate",
            END: END
        }
    )
    
    workflow.add_edge("escalate", END)
    
    return workflow.compile()


support_agent = create_support_agent()
