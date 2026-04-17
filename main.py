import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import config
from vector_db.ingestion import load_knowledge_base
from vector_db.retrieval import retriever
from agents.react import run_react_agent
from langchain_core.messages import HumanMessage
import uuid
from datetime import datetime


class ReActAgentState(dict):
    pass


def main():
    print("🚀 Initializing 24x7 Support Agent (ReACT)...")
    print(f"📚 Loading knowledge base from: {config.KB_PATH}")

    chunks = load_knowledge_base(config.KB_PATH)
    print(f"✅ Loaded {len(chunks)} chunks")

    print("🔍 Indexing documents...")
    retriever.index_documents(chunks)
    print("✅ Documents indexed\n")

    user_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    session_start = datetime.now().isoformat()
    messages = []

    print("=" * 60)
    print("24x7 AI SUPPORT AGENT (ReACT)")
    print("=" * 60)
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("👋 Thank you for using Support Agent!")
            break

        if not user_input:
            continue

        messages.append(HumanMessage(content=user_input))

        state = {
            "user_id": user_id,
            "thread_id": thread_id,
            "session_start": session_start,
            "messages": messages,
            "current_query": user_input,
            "thought": "",
            "action": "",
            "action_input": {},
            "observation": "",
            "classification": {},
            "retrieved_context": "",
            "retrieval_scores": {},
            "response": "",
            "requires_escalation": False,
            "ticket_id": None,
            "resolution_status": "pending",
            "steps": [],
            "final_answer": "",
        }

        print("\n⏳ Processing...")
        result = run_react_agent(state)

        print(f"\n🤖 Agent: {result.get('final_answer', result.get('response', ''))}\n")

        print(f"📊 Metadata:")
        classification = result.get("classification", {})
        print(f"   Category: {classification.get('category', 'unknown')}")
        print(f"   Intent: {classification.get('intent', 'unknown')}")
        print(f"   Sentiment: {classification.get('sentiment', 'neutral')}")
        print(f"   Confidence: {classification.get('confidence_score', 0):.2%}")

        retrieval_scores = result.get("retrieval_scores", {})
        print(
            f"   Retrieval Scores: Dense={retrieval_scores.get('dense', 0):.2f}, Sparse={retrieval_scores.get('sparse', 0):.2f}"
        )

        print(f"   Status: {result.get('resolution_status', 'pending')}")

        if result.get("ticket_id"):
            print(f"   Ticket: {result['ticket_id']}")

        print(f"\n🔄 ReACT Steps:")
        for i, step in enumerate(result.get("steps", []), 1):
            print(f"   {i}. {step[:100]}...")

        print()


if __name__ == "__main__":
    main()
