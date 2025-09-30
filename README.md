# bitwise-mcp

MCP documentation server for embedded developers. Ingests PDF reference manuals (1000+ pages), extracts register definitions, and provides fast semantic search with minimal token usage.

## Overview

This project builds an MCP (Model Context Protocol) server that makes large embedded systems documentation accessible to code assistants. It parses PDF reference manuals like the S32K144 (2200 pages), extracts register definitions from complex tables, and enables efficient semantic search without requiring CMSIS-SVD files.

## Key Features

- **PDF Ingestion** - Parses large reference manuals preserving structure (chapters, sections, tables)
- **Register Table Extraction** - Detects and converts register definitions to structured JSON
- **Semantic Search** - Local embeddings + FAISS for fast retrieval
- **Hybrid Search** - Combines keyword matching (SQLite FTS5) with semantic similarity
- **Compact Output** - Formats responses to minimize token usage (<1000 tokens)
- **Optional LLM Fallback** - OpenRouter integration for complex table parsing

## Architecture

```
Ingestion Pipeline → Indexing Layer → Retrieval System → MCP Server
     ↓                    ↓                ↓              ↓
 PDF Parser         Embeddings        Hybrid Search   MCP Tools
 Table Detector     FAISS Store       Result Ranking  (search_docs,
 Table Extractor    SQLite/FTS5       Formatting      find_register)
 Chunking
```

## Technology Stack

- **Python 3.10+**
- **pymupdf** - PDF text extraction with layout preservation
- **pdfplumber** - Table detection and extraction
- **sentence-transformers** - Local embeddings (BAAI/bge-small-en-v1.5)
- **FAISS** - Vector similarity search
- **SQLite** with FTS5 - Keyword search and metadata
- **MCP SDK** - Server implementation

## Project Status

Early development. See `claude_code_prompt.md` for detailed implementation specification and `CLAUDE.md` for development guidance.

## Planned Usage

```bash
# Index a PDF document
python -m mcp_embedded_docs ingest S32K-RM.pdf

# Start MCP server
python -m mcp_embedded_docs serve

# List indexed documents
python -m mcp_embedded_docs list
```

## MCP Tools (Planned)

- `search_docs(query, top_k, doc_filter)` - Search documentation with hybrid retrieval
- `find_register(name, peripheral)` - Find specific register definitions
- `get_section(doc_id, section)` - Retrieve specific sections
- `list_docs()` - List all indexed documents

## Development Priorities

1. PDF parsing and table detection
2. Register table extraction (most critical component)
3. Test on S32K144 sample pages
4. Semantic chunking and indexing
5. Retrieval system
6. MCP server implementation

## License

MIT
