"""FAISS vector store for similarity search."""

from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss
import pickle


class VectorStore:
    """FAISS-based vector storage for semantic search."""

    def __init__(self, dimension: int = 384):
        """Initialize vector store.

        Args:
            dimension: Dimension of embedding vectors
        """
        self.dimension = dimension
        # Use L2 distance (with normalized embeddings, equivalent to cosine similarity)
        self.index = faiss.IndexFlatL2(dimension)
        self.ids: List[str] = []  # Map from FAISS index position to chunk ID

    def add_vectors(self, vectors: np.ndarray, ids: List[str]):
        """Add embedding vectors to the index.

        Args:
            vectors: Array of shape (n, dimension)
            ids: List of chunk IDs corresponding to vectors
        """
        if len(ids) != len(vectors):
            raise ValueError("Number of IDs must match number of vectors")

        # Ensure vectors are float32 and contiguous
        vectors = np.ascontiguousarray(vectors.astype(np.float32))

        # Add to FAISS index
        self.index.add(vectors)

        # Store IDs
        self.ids.extend(ids)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of (chunk_id, distance) tuples, sorted by similarity
        """
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)

        # Ensure query is float32 and contiguous
        query_vector = np.ascontiguousarray(query_vector.astype(np.float32))

        # Search
        distances, indices = self.index.search(query_vector, top_k)

        # Convert to list of (id, distance) tuples
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.ids):  # Valid index
                results.append((self.ids[idx], float(dist)))

        return results

    def save(self, filepath: Path):
        """Save index to disk.

        Args:
            filepath: Path to save the index
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(filepath))

        # Save ID mapping
        id_file = filepath.with_suffix('.ids')
        with open(id_file, 'wb') as f:
            pickle.dump(self.ids, f)

    def load(self, filepath: Path):
        """Load index from disk.

        Args:
            filepath: Path to the saved index
        """
        # Load FAISS index
        self.index = faiss.read_index(str(filepath))

        # Load ID mapping
        id_file = filepath.with_suffix('.ids')
        with open(id_file, 'rb') as f:
            self.ids = pickle.load(f)

    @property
    def size(self) -> int:
        """Get number of vectors in the index."""
        return self.index.ntotal

    def __len__(self) -> int:
        """Get number of vectors in the index."""
        return self.size