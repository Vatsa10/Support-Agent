import numpy as np
from typing import List

from llm.gemini import embed


class GoogleEmbeddings:
    """Dense embeddings via Google Gemini (new `google.genai` SDK).
    Sparse/lexical handled by Postgres tsvector.
    """

    def get_dense_embedding(self, text: str) -> List[float]:
        return embed(text, task_type="RETRIEVAL_DOCUMENT")

    def get_query_embedding(self, query: str) -> List[float]:
        return embed(query, task_type="RETRIEVAL_QUERY")

    def normalize_vector(self, vector: List[float]) -> List[float]:
        magnitude = float(np.sqrt(sum(x * x for x in vector)))
        if magnitude == 0:
            return vector
        return [x / magnitude for x in vector]


embedding_manager = GoogleEmbeddings()
