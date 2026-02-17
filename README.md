# bitwise-mcp

MCP server for embedded developers. Ingests PDF reference manuals (1000+ pages), extracts register definitions, and provides fast semantic search. Built with [FastMCP](https://github.com/jlowin/fastmcp) and available as a Claude Code plugin.

## Features

- **PDF Ingestion** - Parses large reference manuals preserving structure
- **Register Table Extraction** - Detects and converts register definitions to structured JSON
- **Hybrid Search** - Combines keyword matching (SQLite FTS5) with semantic similarity (FAISS)
- **Context-Aware Chunking** - Chunks include section hierarchy prefixes (e.g. `[Manual > FlexCAN > MCR Register]`) for better retrieval
- **Sentence-Aware Splitting** - Text splits on sentence boundaries with 1-2 sentence overlap, never mid-word
- **Compact Output** - Formats responses to minimize token usage

## Installation

### Option 1: Claude Code Plugin (Recommended)

Install directly from the Claude Code plugin marketplace:

```bash
claude plugin add bitwise-embedded-docs
```

This registers the MCP server and adds `/ingest-docs` and `/search-docs` slash commands.

### Option 2: Global Install

Install once, use across all projects:

```bash
# From this repository directory
pip install -e .

# Then in ANY project directory where you want to use it
claude mcp add --scope project embedded-docs python -m mcp_embedded_docs
```

Each project maintains its own isolated documentation index. When you run the server in a project, it only indexes and searches PDFs in that project's `docs/` directory.

### Option 3: Poetry Install (Development)

```bash
poetry install

# Add to Claude Code
claude mcp add embedded-docs --command poetry --args "run" "mcp-embedded-docs" "serve" --cwd "<path-to-this-repo>"
```

Restart Claude Code after adding the server.

## Usage

Place PDFs in a `docs/` directory, then in Claude Code:

```
What PDFs are available?
Ingest any files that haven't been ingested yet
What's the base address for FlexCAN0?
```

### Example: Checking Available PDFs

![Listing available PDFs](images/Screenshot%20(10).PNG)

### Example: Searching Documentation

The MCP server automatically queries the indexed documentation when you ask questions:

![Documentation search in action](images/Screenshot%20(11).PNG)

### CLI Usage

```bash
poetry run mcp-embedded-docs ingest docs/manual.pdf --title "MCU Manual"
poetry run mcp-embedded-docs list  # View indexed documents
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_docs` | Search documentation with hybrid keyword + semantic retrieval |
| `find_register` | Find specific register definitions by name |
| `list_docs` | List all documentation files with status (indexed + available) |
| `ingest_docs` | Ingest PDF documentation files into the search index |
| `remove_docs` | Remove documents from the search index by ID |

## Architecture

Built on [FastMCP](https://github.com/jlowin/fastmcp) for the MCP server layer. The ingestion pipeline:

1. **PDF Parsing** (PyMuPDF) - Extracts text with layout, TOC, and section hierarchy
2. **Table Detection** (pdfplumber) - Identifies register maps, bitfield definitions, memory maps
3. **Semantic Chunking** - Leaf-only section chunking with contextual hierarchy prefixes, sentence-aware splitting, and content-based deduplication
4. **Embedding** (sentence-transformers, bge-small-en-v1.5) - Local embeddings, no API calls
5. **Indexing** (FAISS + SQLite FTS5) - Hybrid vector + keyword search

## Tech Stack

Python 3.10+ | FastMCP | PyMuPDF | pdfplumber | sentence-transformers | FAISS | SQLite FTS5

## Performance

**Tested:** S32K144 Reference Manual (2,179 pages, 14MB)
**Results:** 3min indexing, <500ms search, ~500MB memory

## License

[MIT](LICENSE)
