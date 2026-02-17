# bitwise-mcp

MCP server for embedded developers. Ingests PDF reference manuals (1000+ pages), extracts register definitions, and provides fast semantic search.

## Features

- **PDF Ingestion** - Parses large reference manuals preserving structure
- **Register Table Extraction** - Detects and converts register definitions to structured JSON
- **Hybrid Search** - Combines keyword matching (SQLite FTS5) with semantic similarity (FAISS)
- **Compact Output** - Formats responses to minimize token usage

## Installation

### Option 1: Global Install (Recommended for Multi-Project Use)

Install once, use across all projects:

```bash
# From this repository directory
pip install -e .

# Then in ANY project directory where you want to use it
claude mcp add --scope project embedded-docs python -m mcp_embedded_docs
```

**How it works:** The global install makes the MCP server code available system-wide, but each project maintains its own isolated documentation index. When you run the server in a project, it only indexes and searches PDFs in that project's `docs/` directory. Projects don't share documentation data.

**Example:**
- Project A with `docs/` folder → indexes only Project A's PDFs
- Project B with `docs/` folder → indexes only Project B's PDFs
- Both use the same MCP server code, but completely separate data

### Option 2: Poetry Install (For Development)

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

Or use CLI directly:

```bash
poetry run mcp-embedded-docs ingest docs/manual.pdf --title "MCU Manual"
poetry run mcp-embedded-docs list  # View indexed documents
```

## MCP Tools

- **search_docs** - Search documentation with hybrid retrieval
- **find_register** - Find specific register definitions
- **list_docs** - List all documentation files with status (indexed + available)
- **ingest_docs** - Ingest documentation files into the search index
- **remove_docs** - Remove documents from the search index by ID

## Tech Stack

Python 3.10+ • PyMuPDF • pdfplumber • sentence-transformers • FAISS • SQLite FTS5

## Performance

**Tested:** S32K144 Reference Manual (2,179 pages, 14MB)
**Results:** 3min indexing, <500ms search, ~500MB memory

## License

[MIT](LICENSE)
