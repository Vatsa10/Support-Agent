import google.generativeai as genai
import numpy as np
from typing import List

from config import config

genai.configure(api_key=config.GOOGLE_API_KEY)


class GoogleEmbeddings:
    """Dense embeddings via Google Gemini. Sparse/lexical handled by Postgres tsvector."""

    def __init__(self):
        self.model = config.DENSE_MODEL

    def get_dense_embedding(self, text: str) -> List[float]:
        response = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )
        return response["embedding"]

    def get_query_embedding(self, query: str) -> List[float]:
        response = genai.embed_content(
            model=self.model,
            content=query,
            task_type="retrieval_query",
        )
        return response["embedding"]

    def normalize_vector(self, vector: List[float]) -> List[float]:
        magnitude = float(np.sqrt(sum(x * x for x in vector)))
        if magnitude == 0:
            return vector
        return [x / magnitude for x in vector]


embedding_manager = GoogleEmbeddings()
