from config import config
from core.state import SupportAgentState
from vector_db.retrieval import retriever
import time

def retrieve_context_node(state: SupportAgentState) -> dict:
    """Retrieve relevant context using hybrid search"""
    
    start_time = time.time()
    
    # Build search query with context
    search_query = f"""
    Category: {state["category"]}
    Intent: {state["intent"]}
    Query: {state["current_query"]}
    """
    
    # Perform hybrid search
    documents, scores = retriever.hybrid_search(
        query=search_query,
        top_k=config.TOP_K
    )
    
    # Format context
    context_parts = []
    for doc in documents:
        source = doc["metadata"].get("source", "Knowledge Base")
        section = doc["metadata"].get("section", "")
        
        context_parts.append(
            f"**Source:** {source} | **Section:** {section}\n\n{doc['text']}"
        )
    
    combined_context = "\n\n---\n\n".join(context_parts)
    
    processing_time = time.time() - start_time
    
    return {
        "retrieved_docs": documents,
        "retrieved_context": combined_context,
        "retrieval_scores": {
            "dense": scores["dense_score"],
            "sparse": scores["sparse_score"],
            "hybrid": scores["hybrid_score"]
        },
        "processing_time": processing_time
    }
