"""Search documentation tool."""

from typing import Optional
from ..retrieval.hybrid_search import HybridSearch
from ..retrieval.formatter import ResultFormatter
from ..config import Config


async def search_docs(
    query: str,
    top_k: int = 5,
    doc_filter: Optional[str] = None,
    config: Optional[Config] = None
) -> str:
    """Search documentation using hybrid search.

    Args:
        query: Search query
        top_k: Number of results to return (default: 5)
        doc_filter: Optional document ID to filter results
        config: Configuration object

    Returns:
        Formatted search results as markdown
    """
    if config is None:
        config = Config.load()

    search = HybridSearch(config)

    try:
        results = search.search(query, top_k, doc_filter)
        formatted = ResultFormatter.format_results(results, top_k)
        return formatted
    finally:
        search.close()