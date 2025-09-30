"""List documents tool."""

from typing import Optional
from ..retrieval.hybrid_search import HybridSearch
from ..config import Config


async def list_docs(config: Optional[Config] = None) -> str:
    """List all indexed documents.

    Args:
        config: Configuration object

    Returns:
        Formatted list of documents as markdown
    """
    if config is None:
        config = Config.load()

    search = HybridSearch(config)

    try:
        docs = search.list_documents()

        if not docs:
            return "No documents indexed yet."

        lines = ["# Indexed Documents", ""]

        for doc in docs:
            lines.append(f"## {doc['filename']}")
            if doc['title']:
                lines.append(f"**Title:** {doc['title']}")
            if doc['version']:
                lines.append(f"**Version:** {doc['version']}")
            lines.append(f"**ID:** {doc['id']}")
            lines.append(f"**Indexed:** {doc['index_date']}")
            lines.append("")

        return "\n".join(lines)
    finally:
        search.close()