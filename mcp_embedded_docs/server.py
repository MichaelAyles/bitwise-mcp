"""MCP server for embedded documentation using FastMCP."""

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .config import Config

logger = logging.getLogger(__name__)

# Global config
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create config instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


# Create FastMCP server
mcp = FastMCP("mcp-embedded-docs")


@mcp.tool()
async def search_docs(
    query: str,
    top_k: int = 5,
    doc_filter: str | None = None,
) -> str:
    """Search documentation using hybrid keyword and semantic search.

    Returns relevant sections and register definitions from indexed
    embedded systems documentation.

    Args:
        query: Search query (can be natural language or keywords)
        top_k: Number of results to return
        doc_filter: Optional document ID to filter results
    """
    from .tools.search_docs import search_docs as _search

    config = get_config()
    return await _search(query, top_k, doc_filter, config)


@mcp.tool()
async def find_register(
    name: str,
    peripheral: str | None = None,
) -> str:
    """Find a specific hardware register by name.

    Returns detailed register definition including address, bit fields,
    and descriptions.

    Args:
        name: Register name (e.g. 'MCR', 'CTRL')
        peripheral: Optional peripheral name to filter (e.g. 'FlexCAN0')
    """
    from .tools.find_register import find_register as _find

    config = get_config()
    return await _find(name, peripheral, config)


@mcp.tool()
async def list_docs() -> str:
    """List all documentation files with their status.

    Shows indexed documents with statistics (chunks, tables) and
    available PDF files ready for ingestion (pages, size).
    """
    from .tools.list_docs import list_docs as _list

    config = get_config()
    return await _list(config)


@mcp.tool()
async def ingest_docs(
    doc_path: str,
    title: str | None = None,
    version: str | None = None,
) -> str:
    """Ingest a documentation file into the search index.

    Extracts text, detects register tables, creates embeddings, and makes
    the document searchable. Currently supports PDF files. This operation
    may take several minutes for large documents.

    Args:
        doc_path: Path to the documentation file to ingest
        title: Optional document title
        version: Optional document version
    """
    from .tools.ingest_docs import ingest_docs as _ingest

    config = get_config()
    return await _ingest(doc_path, title, version, config)


@mcp.tool()
async def remove_docs(doc_id: str) -> str:
    """Remove a document from the search index by its document ID.

    Args:
        doc_id: Document ID to remove (use list_docs to find IDs)
    """
    from .tools.remove_docs import remove_docs as _remove

    config = get_config()
    return await _remove(doc_id, config)
