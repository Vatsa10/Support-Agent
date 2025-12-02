import google.generativeai as genai
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from config import config
from typing import List, Tuple
import numpy as np
from bm25_simple import BM25

genai.configure(api_key=config.GOOGLE_API_KEY)

class HybridEmbeddingManager:
    """Manages both dense (Google) and sparse (BM25) embeddings"""
    
    def __init__(self):
        self.dense_model = config.DENSE_MODEL
        self.bm25 = None
        self.vocabulary = set()
    
    def get_dense_embedding(self, text: str) -> List[float]:
        """Get dense vector from Google Gemini"""
        response = genai.embed_content(
            model=self.dense_model,
            content=text,
            task_type="retrieval_document"
        )
        return response['embedding']
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Get dense vector for query (different task type)"""
        response = genai.embed_content(
            model=self.dense_model,
            content=query,
            task_type="retrieval_query"
        )
        return response['embedding']
    
    def build_bm25_index(self, documents: List[str]):
        """Build sparse BM25 index from documents"""
        self.bm25 = BM25(documents)
        # Build vocabulary
        for doc in documents:
            tokens = doc.lower().split()
            self.vocabulary.update(tokens)
    
    def get_sparse_embedding(self, text: str) -> dict:
        """Convert text to sparse BM25 vector representation"""
        if not self.bm25:
            raise ValueError("BM25 index not initialized")
        
        tokens = text.lower().split()
        sparse_vector = {}
        
        for token in tokens:
            if token in self.vocabulary:
                # Create sparse vector with token indices
                token_idx = hash(token) % 10000  # Simple hash-based indexing
                sparse_vector[token_idx] = sparse_vector.get(token_idx, 0) + 1
        
        return sparse_vector
    
    def normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize dense vector to unit length"""
        magnitude = np.sqrt(sum(x**2 for x in vector))
        if magnitude == 0:
            return vector
        return [x / magnitude for x in vector]


embedding_manager = HybridEmbeddingManager()
