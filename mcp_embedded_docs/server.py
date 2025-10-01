"""MCP server for embedded documentation."""

import asyncio
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from .config import Config
from .tools.search_docs import search_docs
from .tools.find_register import find_register
from .tools.list_docs import list_docs
from .tools.ingest_docs import ingest_docs
from .tools.remove_docs import remove_docs


# Global config
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create config instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


# Create MCP server
app = Server("mcp-embedded-docs")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_docs",
            description="Search documentation using hybrid keyword and semantic search. "
                       "Returns relevant sections and register definitions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (can be natural language or keywords)"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    },
                    "doc_filter": {
                        "type": "string",
                        "description": "Optional document ID to filter results",
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="find_register",
            description="Find a specific register by name. Returns detailed register definition "
                       "including address, bit fields, and descriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Register name (e.g., 'MCR', 'CTRL')"
                    },
                    "peripheral": {
                        "type": "string",
                        "description": "Optional peripheral name to filter (e.g., 'FlexCAN0')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="list_docs",
            description="List all documentation files with their status. Shows indexed documents with "
                       "statistics (chunks, tables) and available files ready for ingestion (pages, size).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ingest_docs",
            description="Ingest a documentation file into the search index. Extracts text, detects register tables, "
                       "creates embeddings, and makes the document searchable. Currently supports PDF files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_path": {
                        "type": "string",
                        "description": "Path to the documentation file to ingest"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional document title"
                    },
                    "version": {
                        "type": "string",
                        "description": "Optional document version"
                    }
                },
                "required": ["doc_path"]
            }
        ),
        Tool(
            name="remove_docs",
            description="Remove a document from the search index by its document ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "Document ID to remove"
                    }
                },
                "required": ["doc_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    config = get_config()

    if name == "search_docs":
        query = arguments["query"]
        top_k = arguments.get("top_k", 5)
        doc_filter = arguments.get("doc_filter")

        result = await search_docs(query, top_k, doc_filter, config)

        return [TextContent(type="text", text=result)]

    elif name == "find_register":
        register_name = arguments["name"]
        peripheral = arguments.get("peripheral")

        result = await find_register(register_name, peripheral, config)

        return [TextContent(type="text", text=result)]

    elif name == "list_docs":
        result = await list_docs(config)

        return [TextContent(type="text", text=result)]

    elif name == "ingest_docs":
        doc_path = arguments["doc_path"]
        title = arguments.get("title")
        version = arguments.get("version")

        result = await ingest_docs(doc_path, title, version, config)

        return [TextContent(type="text", text=result)]

    elif name == "remove_docs":
        doc_id = arguments["doc_id"]

        result = await remove_docs(doc_id, config)

        return [TextContent(type="text", text=result)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Main entry point for server."""
    asyncio.run(run_server())