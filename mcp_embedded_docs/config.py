"""Configuration management."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class EmbeddingsConfig(BaseModel):
    """Embeddings configuration."""
    model: str = "BAAI/bge-small-en-v1.5"
    device: str = "cpu"
    batch_size: int = 32


class LLMFallbackConfig(BaseModel):
    """LLM fallback configuration."""
    enabled: bool = False
    provider: str = "openrouter"
    api_key_env: str = "OPENROUTER_API_KEY"
    model: str = "anthropic/claude-3-haiku"
    cache_results: bool = True


class ChunkingConfig(BaseModel):
    """Chunking configuration."""
    target_size: int = 1000
    overlap: int = 100
    preserve_tables: bool = True


class SearchConfig(BaseModel):
    """Search configuration."""
    keyword_weight: float = 0.4
    semantic_weight: float = 0.6
    top_k_default: int = 5


class IndexConfig(BaseModel):
    """Index storage configuration."""
    directory: Path = Path("./index")
    vector_file: str = "vectors.faiss"
    metadata_db: str = "metadata.db"
    documents_file: str = "documents.json"


class Config(BaseModel):
    """Main configuration."""
    doc_dirs: List[Path] = Field(default_factory=lambda: [Path("./docs")])
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    llm_fallback: LLMFallbackConfig = Field(default_factory=LLMFallbackConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    index: IndexConfig = Field(default_factory=IndexConfig)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file or use defaults."""
        if config_path is None:
            config_path = Path("config.yaml")

        if not config_path.exists():
            return cls()

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        if not self.llm_fallback.enabled:
            return None
        return os.getenv(self.llm_fallback.api_key_env)