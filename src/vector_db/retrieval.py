from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, SparseVector
from config import config
from embeddings import embedding_manager
from typing import List, Tuple
import numpy as np

class HybridRetriever:
    """Hybrid search combining dense and sparse vectors"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=config.QDRANT_URL,
            api_key=config.QDRANT_API_KEY or None
        )
        self.dense_collection = config.DENSE_COLLECTION
        self.sparse_collection = config.SPARSE_COLLECTION
        self._init_collections()
    
    def _init_collections(self):
        """Initialize Qdrant collections"""
        
        try:
            # Check if dense collection exists
            self.client.get_collection(self.dense_collection)
        except:
            # Create dense collection
            self.client.create_collection(
                collection_name=self.dense_collection,
                vectors_config=VectorParams(
                    size=config.DENSE_DIM,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Created dense collection: {self.dense_collection}")
        
        try:
            # Check if sparse collection exists
            self.client.get_collection(self.sparse_collection)
        except:
            # Create sparse collection (uses sparse vectors)
            self.client.create_collection(
                collection_name=self.sparse_collection,
                vectors_config=VectorParams(
                    size=10000,  # Vocabulary size
                    distance=Distance.DOT
                ),
                sparse_vectors_config={
                    "sparse": VectorParams(
                        size=10000,
                        distance=Distance.DOT
                    )
                }
            )
            print(f"✅ Created sparse collection: {self.sparse_collection}")
    
    def index_documents(self, chunks: List[dict]):
        """Index chunks into both dense and sparse collections"""
        
        points_dense = []
        points_sparse = []
        
        for idx, chunk in enumerate(chunks):
            # Dense embedding
            dense_vector = embedding_manager.get_dense_embedding(chunk["text"])
            dense_vector = embedding_manager.normalize_vector(dense_vector)
            
            points_dense.append(
                PointStruct(
                    id=idx,
                    vector=dense_vector,
                    payload={
                        "text": chunk["text"],
                        "metadata": chunk["metadata"]
                    }
                )
            )
            
            # Sparse embedding
            sparse_vector = embedding_manager.get_sparse_embedding(chunk["text"])
            
            points_sparse.append(
                PointStruct(
                    id=idx,
                    vector=sparse_vector,
                    payload={
                        "text": chunk["text"],
                        "metadata": chunk["metadata"]
                    }
                )
            )
        
        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.dense_collection,
            points=points_dense
        )
        print(f"✅ Indexed {len(points_dense)} documents (dense)")
        
        # For sparse, we'll use the main vectors for now
        # (Qdrant sparse vectors are in beta)
        self.client.upsert(
            collection_name=self.sparse_collection,
            points=points_sparse
        )
        print(f"✅ Indexed {len(points_sparse)} documents (sparse)")
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3
    ) -> Tuple[List[dict], dict]:
        """Perform hybrid search with weighted combination"""
        
        # Dense search
        query_dense = embedding_manager.get_query_embedding(query)
        query_dense = embedding_manager.normalize_vector(query_dense)
        
        dense_results = self.client.search(
            collection_name=self.dense_collection,
            query_vector=query_dense,
            limit=top_k * 2  # Get more results for re-ranking
        )
        
        # Sparse search
        query_sparse = embedding_manager.get_sparse_embedding(query)
        
        sparse_results = self.client.search(
            collection_name=self.sparse_collection,
            query_vector=list(query_sparse.values()),
            limit=top_k * 2
        )
        
        # Combine and re-rank results
        combined_results = self._combine_results(
            dense_results,
            sparse_results,
            dense_weight,
            sparse_weight,
            top_k
        )
        
        # Extract documents and scores
        documents = [
            {
                "text": result.payload["text"],
                "metadata": result.payload["metadata"],
                "score": result.score
            }
            for result in combined_results
        ]
        
        scores = {
            "dense_score": combined_results.score if dense_results else 0,
            "sparse_score": combined_results.score if sparse_results else 0,
            "hybrid_score": combined_results.score if combined_results else 0
        }
        
        return documents, scores
    
    def _combine_results(self, dense_results, sparse_results, dense_weight, sparse_weight, top_k):
        """Combine and re-rank dense + sparse results"""
        
        # Create score map
        scores = {}
        
        for result in dense_results:
            scores[result.id] = scores.get(result.id, 0) + (result.score * dense_weight)
        
        for result in sparse_results:
            scores[result.id] = scores.get(result.id, 0) + (result.score * sparse_weight)
        
        # Sort by combined score
        sorted_ids = sorted(scores.items(), key=lambda x: x, reverse=True)
        
        # Get top_k and fetch full results
        all_results = dense_results + sparse_results
        result_map = {r.id: r for r in all_results}
        
        combined = []
        for doc_id, score in sorted_ids[:top_k]:
            if doc_id in result_map:
                result = result_map[doc_id]
                result.score = score  # Update with combined score
                combined.append(result)
        
        return combined


retriever = HybridRetriever()
