"""Hybrid search combining keyword and semantic search."""

from typing import List, Optional, Dict, Tuple
from pathlib import Path

from ..indexing.embedder import LocalEmbedder
from ..indexing.vector_store import VectorStore
from ..indexing.metadata_store import MetadataStore
from ..config import Config
from . import SearchResult


class HybridSearch:
    """Hybrid search engine combining keyword and semantic search."""

    def __init__(self, config: Config):
        """Initialize hybrid search.

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize components
        self.embedder = LocalEmbedder(
            model_name=config.embeddings.model,
            device=config.embeddings.device
        )

        # Initialize stores (will be loaded if they exist)
        index_dir = config.index.directory
        self.vector_store = VectorStore(dimension=self.embedder.dimension)
        self.metadata_store = MetadataStore(index_dir / config.index.metadata_db)

        # Try to load existing index
        vector_path = index_dir / config.index.vector_file
        if vector_path.exists():
            self.vector_store.load(vector_path)

    def search(
        self,
        query: str,
        top_k: int = 5,
        doc_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """Perform hybrid search.

        Args:
            query: Search query
            top_k: Number of results to return
            doc_filter: Optional document ID to filter results

        Returns:
            List of search results sorted by relevance
        """
        # Get keyword search results
        keyword_results = self._keyword_search(query, top_k * 2, doc_filter)

        # Get semantic search results
        semantic_results = self._semantic_search(query, top_k * 2, doc_filter)

        # Combine and rank results
        combined = self._combine_results(keyword_results, semantic_results)

        # Get full chunk data for top results
        results = []
        for chunk_id, score in combined[:top_k]:
            chunk_data = self.metadata_store.get_chunk(chunk_id)
            if chunk_data:
                results.append(SearchResult(
                    chunk_id=chunk_id,
                    score=score,
                    text=chunk_data["text"],
                    structured_data=chunk_data.get("structured_data"),
                    metadata=chunk_data.get("metadata", {}),
                    doc_id=chunk_data["doc_id"],
                    page_start=chunk_data["page_start"],
                    page_end=chunk_data["page_end"]
                ))

        return results

    def _keyword_search(
        self,
        query: str,
        top_k: int,
        doc_filter: Optional[str]
    ) -> List[Tuple[str, float]]:
        """Perform keyword search using FTS5."""
        try:
            results = self.metadata_store.keyword_search(query, top_k, doc_filter)
            # Normalize scores to 0-1 range (FTS5 scores are negative)
            if results:
                max_score = max(score for _, score in results)
                if max_score > 0:
                    results = [(chunk_id, score / max_score) for chunk_id, score in results]
            return results
        except Exception as e:
            print(f"Keyword search error: {e}")
            return []

    def _semantic_search(
        self,
        query: str,
        top_k: int,
        doc_filter: Optional[str]
    ) -> List[Tuple[str, float]]:
        """Perform semantic search using embeddings."""
        try:
            # Embed query
            query_vector = self.embedder.embed_query(query)

            # Search vector store
            results = self.vector_store.search(query_vector, top_k)

            # Filter by document if requested
            if doc_filter:
                filtered = []
                for chunk_id, distance in results:
                    chunk = self.metadata_store.get_chunk(chunk_id)
                    if chunk and chunk["doc_id"] == doc_filter:
                        filtered.append((chunk_id, distance))
                results = filtered

            # Convert distances to similarity scores (lower distance = higher similarity)
            # For normalized vectors, L2 distance ≈ 2(1 - cosine_similarity)
            # So similarity ≈ 1 - distance/2
            results = [(chunk_id, max(0, 1 - distance / 2)) for chunk_id, distance in results]

            return results
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []

    def _combine_results(
        self,
        keyword_results: List[Tuple[str, float]],
        semantic_results: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """Combine keyword and semantic results with weighted scoring."""
        keyword_weight = self.config.search.keyword_weight
        semantic_weight = self.config.search.semantic_weight

        # Build score dictionaries
        keyword_scores = {chunk_id: score for chunk_id, score in keyword_results}
        semantic_scores = {chunk_id: score for chunk_id, score in semantic_results}

        # Get all unique chunk IDs
        all_chunk_ids = set(keyword_scores.keys()) | set(semantic_scores.keys())

        # Compute combined scores
        combined_scores = []
        for chunk_id in all_chunk_ids:
            keyword_score = keyword_scores.get(chunk_id, 0)
            semantic_score = semantic_scores.get(chunk_id, 0)

            # Weighted combination
            combined_score = (keyword_weight * keyword_score +
                            semantic_weight * semantic_score)

            # Boost score if present in both result sets
            if chunk_id in keyword_scores and chunk_id in semantic_scores:
                combined_score *= 1.2  # 20% boost for appearing in both

            combined_scores.append((chunk_id, combined_score))

        # Sort by score descending
        combined_scores.sort(key=lambda x: x[1], reverse=True)

        return combined_scores

    def find_register(
        self,
        name: str,
        peripheral: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Find a specific register by name.

        Args:
            name: Register name
            peripheral: Optional peripheral name to filter

        Returns:
            Search result containing the register or None
        """
        chunk_data = self.metadata_store.find_register(name, peripheral)

        if not chunk_data:
            return None

        return SearchResult(
            chunk_id=chunk_data["id"],
            score=1.0,  # Exact match
            text=chunk_data["text"],
            structured_data=chunk_data.get("structured_data"),
            metadata=chunk_data.get("metadata", {}),
            doc_id=chunk_data["doc_id"],
            page_start=chunk_data["page_start"],
            page_end=chunk_data["page_end"]
        )

    def list_documents(self) -> List[Dict]:
        """List all indexed documents.

        Returns:
            List of document information
        """
        return self.metadata_store.list_documents()

    def close(self):
        """Close connections."""
        self.metadata_store.close()