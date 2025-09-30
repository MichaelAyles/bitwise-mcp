# bitwise-mcp

MCP server for embedded developers. Ingests PDF reference manuals (1000+ pages), extracts register definitions, and provides fast semantic search.

## Features

- **PDF Ingestion** - Parses large reference manuals preserving structure
- **Register Table Extraction** - Detects and converts register definitions to structured JSON
- **Hybrid Search** - Combines keyword matching (SQLite FTS5) with semantic similarity (FAISS)
- **Compact Output** - Formats responses to minimize token usage

## Installation

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

Or use CLI directly:

```bash
poetry run mcp-embedded-docs ingest docs/manual.pdf --title "MCU Manual"
```

## MCP Tools

- **search_docs** - Search documentation with hybrid retrieval
- **find_register** - Find specific register definitions
- **list_docs** - List all indexed documents
- **list_pdfs** - List available PDFs with ingestion status
- **ingest_pdf** - Ingest a PDF into the search index

## Tech Stack

Python 3.10+ • PyMuPDF • pdfplumber • sentence-transformers • FAISS • SQLite FTS5

## Performance

**Tested:** S32K144 Reference Manual (2,179 pages, 14MB)
**Results:** 3min indexing, <500ms search, ~500MB memory

## License

MIT
