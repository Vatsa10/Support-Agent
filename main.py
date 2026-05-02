import argparse
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_core.messages import HumanMessage

from agents.react import run_react_agent
from cache.valkey import init_cache, close_cache
from db.pool import init_pool, close_pool


async def amain(tenant_id: str) -> None:
    await init_pool()
    await init_cache()
    print("=" * 60)
    print(f"24x7 AI SUPPORT AGENT (tenant={tenant_id})")
    print("=" * 60)
    print("Type 'exit' to quit\n")

    user_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    session_start = datetime.now(timezone.utc).isoformat()

    try:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print("bye")
                break
            if not user_input:
                continue

            state = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "thread_id": thread_id,
                "session_start": session_start,
                "messages": [HumanMessage(content=user_input)],
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

            print("\nProcessing...")
            result = await run_react_agent(state)

            print(f"\nAgent: {result.get('final_answer', '')}\n")
            cls = result.get("classification", {})
            print(f"Category: {cls.get('category', 'unknown')}")
            print(f"Intent: {cls.get('intent', 'unknown')}")
            print(f"Sentiment: {cls.get('sentiment', 'neutral')}")
            print(f"Status: {result.get('resolution_status', 'pending')}")
            if result.get("ticket_id"):
                print(f"Ticket: {result['ticket_id']}")
            print()
    finally:
        await close_cache()
        await close_pool()


def main() -> None:
    parser = argparse.ArgumentParser(description="Support Agent CLI (multi-tenant)")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID")
    args = parser.parse_args()
    asyncio.run(amain(args.tenant_id))


if __name__ == "__main__":
    main()
