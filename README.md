# bitwise-mcp

**✅ Production-Ready** MCP documentation server for embedded developers. Ingests PDF reference manuals (1000+ pages), extracts register definitions, and provides fast semantic search with minimal token usage.

## What This Does

Makes your MCU documentation instantly searchable by Claude Code in VSCode. Drop your PDF reference manuals in a folder, run two commands, and Claude Code can answer questions about your hardware - **completely automatic, no manual searching needed**.

**Example:** Ask "What's the FlexCAN base address?" and Claude Code searches your 2000-page manual and gives you the answer.

## Overview

Fully implemented MCP (Model Context Protocol) server that makes large embedded systems documentation accessible to code assistants. Successfully tested with the S32K144 reference manual (2,179 pages, 14MB). Parses PDFs, extracts register definitions, and enables semantic search without requiring CMSIS-SVD files.

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

## 🚀 Quick Start

### For VSCode Users (Windows)

**5-minute setup:**

```powershell
git clone https://github.com/MichaelAyles/bitwise-mcp.git .mcp-docs
cd .mcp-docs
.\setup-mcp.ps1        # Auto-configure for Claude Code
.\index-docs.ps1       # Index your docs
# Restart VSCode - Done!
```

See [QUICKSTART.md](QUICKSTART.md) for details.

### Manual Installation

```bash
poetry install

# Index your documentation
poetry run mcp-embedded-docs ingest docs/manual.pdf --title "MCU Manual"

# Start MCP server (for Claude Code/Claude Desktop)
poetry run mcp-embedded-docs serve
```

See [USAGE.md](USAGE.md) for detailed guide.

## MCP Tools

- `search_docs(query, top_k, doc_filter)` - Search documentation with hybrid retrieval
- `find_register(name, peripheral)` - Find specific register definitions
- `list_docs()` - List all indexed documents

## Usage Example

Once configured with Claude Code in VSCode, just ask:

```
What's the base address for FlexCAN0?
```

```
How do I configure GPIO pins?
```

```
Show me the clock configuration registers
```

Claude Code automatically searches your documentation and provides answers!

## Implementation Status

| Component | Status | Details |
|-----------|--------|---------|
| PDF Parser | ✅ Complete | PyMuPDF-based, preserves layout |
| Table Detection | ✅ Complete | Heuristic detection + extraction |
| Semantic Chunking | ✅ Complete | 4,271 chunks from 2,179 pages |
| Vector Search | ✅ Complete | FAISS + sentence-transformers |
| Keyword Search | ✅ Complete | SQLite FTS5 |
| Hybrid Search | ✅ Complete | <500ms query time |
| MCP Server | ✅ Complete | 3 tools, stdio protocol |
| CLI Interface | ✅ Complete | ingest, serve, list |
| Windows Setup | ✅ Complete | PowerShell automation |
| VSCode Integration | ✅ Complete | Auto-configuration |

**Tested:** S32K144 Reference Manual (2,179 pages, 14MB)
**Performance:** 3min indexing, <500ms search, ~500MB memory

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for complete implementation details.

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[INSTALL_VSCODE.md](INSTALL_VSCODE.md)** - Detailed VSCode/Windows setup
- **[USAGE.md](USAGE.md)** - Complete usage guide and API
- **[CLAUDE.md](CLAUDE.md)** - Development guide for contributors
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Full implementation details

## License

MIT
