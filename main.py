import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import config
from vector_db.ingestion import load_knowledge_base
from vector_db.retrieval import retriever
from core.graph import support_agent
from langchain_core.messages import HumanMessage
from core.state import SupportAgentState
import uuid
from datetime import datetime

def main():
    """Interactive CLI for testing support agent"""
    
    print("🚀 Initializing 24x7 Support Agent...")
    print(f"📚 Loading knowledge base from: {config.KB_PATH}")
    
    # Load and index knowledge base
    chunks = load_knowledge_base(config.KB_PATH)
    print(f"✅ Loaded {len(chunks)} chunks")
    
    # Index documents
    print("🔍 Indexing documents...")
    retriever.index_documents(chunks)
    print("✅ Documents indexed\n")
    
    # Start interactive session
    user_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    messages = []
    
    print("=" * 60)
    print("24x7 AI SUPPORT AGENT")
    print("=" * 60)
    print("Type 'exit' to quit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'exit':
            print("👋 Thank you for using Support Agent!")
            break
        
        if not user_input:
            continue
        
        # Add to messages
        messages.append(HumanMessage(content=user_input))
        
        # Create state
        state = SupportAgentState(
            user_id=user_id,
            thread_id=thread_id,
            session_start=datetime.now().isoformat(),
            messages=messages,
            current_query=user_input,
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
        print("\n⏳ Processing...")
        result = support_agent.invoke(state)
        
        # Display response
        print(f"\n🤖 Agent: {result['final_response']}\n")
        
        # Display metadata
        print(f"📊 Metadata:")
        print(f"   Category: {result['category']}")
        print(f"   Intent: {result['intent']}")
        print(f"   Sentiment: {result['user_sentiment']}")
        print(f"   Confidence: {result['confidence_score']:.2%}")
        print(f"   Retrieval Scores: Dense={result.get('retrieval_scores', {}).get('dense', 0):.2f}, Sparse={result.get('retrieval_scores', {}).get('sparse', 0):.2f}")
        print(f"   Status: {result['resolution_status']}")
        
        if result.get('ticket_id'):
            print(f"   Ticket: {result['ticket_id']}")
        
        print()

if __name__ == "__main__":
    main()
