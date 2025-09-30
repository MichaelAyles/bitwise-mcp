"""Search and retrieval modules."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class SearchResult:
    """A search result."""
    chunk_id: str
    score: float
    text: str
    structured_data: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    doc_id: str
    page_start: int
    page_end: int