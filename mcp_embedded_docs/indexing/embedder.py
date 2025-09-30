"""Text embedding using sentence-transformers."""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class LocalEmbedder:
    """Wrapper for sentence-transformers embeddings."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu"):
        """Initialize embedder.

        Args:
            model_name: Name of the sentence-transformers model
            device: Device to run on ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_batch(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """Embed a batch of texts.

        Args:
            texts: List of texts to embed
            show_progress: Show progress bar

        Returns:
            Array of embeddings with shape (len(texts), dimension)
        """
        return self.model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return self.embed_batch([text])[0]

    def embed_query(self, query: str) -> np.ndarray:
        """Embed a query (same as text embedding for this model).

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        return self.embed_single(query)