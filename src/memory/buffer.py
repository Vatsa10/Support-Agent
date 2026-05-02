from typing import List
from db.pool import tenant_conn


class SupportAgentMemory:
    """Postgres-backed, tenant-scoped conversation memory.

    All access funneled through tenant_conn -> RLS enforces isolation.
    """

    def __init__(self, max_history: int = 10):
        self.max_history = max_history

    async def _ensure_conversation(
        self, conn, tenant_id: str, user_id: str, thread_id: str
    ) -> str:
        row = await conn.fetchrow(
            """
            INSERT INTO conversations (tenant_id, user_id, thread_id)
            VALUES (current_setting('app.tenant_id')::uuid, $1, $2)
            ON CONFLICT (tenant_id, user_id, thread_id)
                DO UPDATE SET last_at = now()
            RETURNING id
            """,
            user_id,
            thread_id,
        )
        return str(row["id"])

    async def add_user_message(
        self, tenant_id: str, user_id: str, thread_id: str, content: str
    ) -> None:
        async with tenant_conn(tenant_id) as conn:
            conv_id = await self._ensure_conversation(conn, tenant_id, user_id, thread_id)
            await conn.execute(
                """
                INSERT INTO messages (tenant_id, conversation_id, role, content)
                VALUES (current_setting('app.tenant_id')::uuid, $1, 'user', $2)
                """,
                conv_id,
                content,
            )

    async def add_ai_message(
        self, tenant_id: str, user_id: str, thread_id: str, content: str
    ) -> None:
        async with tenant_conn(tenant_id) as conn:
            conv_id = await self._ensure_conversation(conn, tenant_id, user_id, thread_id)
            await conn.execute(
                """
                INSERT INTO messages (tenant_id, conversation_id, role, content)
                VALUES (current_setting('app.tenant_id')::uuid, $1, 'assistant', $2)
                """,
                conv_id,
                content,
            )

    async def get_conversation_history(
        self, tenant_id: str, user_id: str, thread_id: str, limit: int = None
    ) -> List[dict]:
        n = limit or (self.max_history * 2)
        async with tenant_conn(tenant_id) as conn:
            rows = await conn.fetch(
                """
                SELECT m.role, m.content, m.created_at
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.user_id = $1 AND c.thread_id = $2
                ORDER BY m.created_at DESC
                LIMIT $3
                """,
                user_id,
                thread_id,
                n,
            )
        rows = list(reversed(rows))
        return [
            {
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["created_at"].isoformat(),
            }
            for r in rows
        ]

    async def get_formatted_history(
        self, tenant_id: str, user_id: str, thread_id: str, last_n: int = 5
    ) -> str:
        history = await self.get_conversation_history(
            tenant_id, user_id, thread_id, limit=last_n * 2
        )
        if not history:
            return ""
        lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)


agent_memory = SupportAgentMemory()
