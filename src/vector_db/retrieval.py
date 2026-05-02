from typing import List, Tuple, Dict

from db.pool import tenant_conn
from vector_db.embeddings import embedding_manager


class HybridRetriever:
    """Hybrid search: pgvector (dense cosine) + tsvector (lexical BM25-ish), merged via RRF."""

    RRF_K = 60

    async def index_documents(self, tenant_id: str, chunks: List[dict]) -> int:
        rows = []
        for chunk in chunks:
            emb = embedding_manager.get_dense_embedding(chunk["text"])
            md = chunk.get("metadata", {})
            rows.append((
                chunk["text"],
                md.get("source"),
                md.get("section"),
                md.get("category"),
                md.get("key_phrases") or [],
                emb,
            ))

        async with tenant_conn(tenant_id) as conn:
            await conn.execute("DELETE FROM kb_documents")
            await conn.executemany(
                """
                INSERT INTO kb_documents
                    (tenant_id, source, section, category, key_phrases, chunk_text, embedding, tsv)
                VALUES
                    (current_setting('app.tenant_id')::uuid, $2, $3, $4, $5, $1, $6,
                     to_tsvector('english', $1))
                """,
                rows,
            )
        return len(rows)

    async def hybrid_search(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 5,
    ) -> Tuple[List[dict], dict]:
        query_vec = embedding_manager.get_query_embedding(query)
        fetch_n = max(top_k * 2, 10)

        async with tenant_conn(tenant_id) as conn:
            dense_rows = await conn.fetch(
                """
                SELECT id, chunk_text, source, section, category, key_phrases,
                       1 - (embedding <=> $1) AS sim
                FROM kb_documents
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1
                LIMIT $2
                """,
                query_vec,
                fetch_n,
            )
            lexical_rows = await conn.fetch(
                """
                SELECT id, chunk_text, source, section, category, key_phrases,
                       ts_rank_cd(tsv, plainto_tsquery('english', $1)) AS rank
                FROM kb_documents
                WHERE tsv @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT $2
                """,
                query,
                fetch_n,
            )

        rrf: Dict[str, float] = {}
        meta: Dict[str, dict] = {}
        for rank, row in enumerate(dense_rows):
            rid = str(row["id"])
            rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (self.RRF_K + rank + 1)
            meta[rid] = dict(row)
        for rank, row in enumerate(lexical_rows):
            rid = str(row["id"])
            rrf[rid] = rrf.get(rid, 0.0) + 1.0 / (self.RRF_K + rank + 1)
            meta.setdefault(rid, dict(row))

        ranked = sorted(rrf.items(), key=lambda kv: kv[1], reverse=True)[:top_k]

        documents = []
        for rid, score in ranked:
            r = meta[rid]
            documents.append({
                "text": r["chunk_text"],
                "metadata": {
                    "source": r.get("source"),
                    "section": r.get("section"),
                    "category": r.get("category"),
                    "key_phrases": r.get("key_phrases") or [],
                },
                "score": score,
            })

        scores = {
            "dense_top": float(dense_rows[0]["sim"]) if dense_rows else 0.0,
            "lexical_top": float(lexical_rows[0]["rank"]) if lexical_rows else 0.0,
            "hybrid_top": ranked[0][1] if ranked else 0.0,
        }
        return documents, scores


retriever = HybridRetriever()
