# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
poetry install                                    # Install dependencies
poetry run mcp-embedded-docs serve                # Start MCP server (stdio)
poetry run mcp-embedded-docs ingest PATH --title "Title"  # Ingest a PDF
poetry run mcp-embedded-docs list                 # List indexed documents
poetry run pytest                                 # Run tests
poetry run pytest tests/test_chunker.py -k "test_name"  # Single test
poetry run black mcp_embedded_docs/               # Format
poetry run mypy mcp_embedded_docs/                # Type check
```

## Architecture

FastMCP server (`server.py`) exposing 5 tools: `search_docs`, `find_register`, `list_docs`, `ingest_docs`, `remove_docs`. Heavy imports are deferred — tool implementations live in `tools/` and only import PDF/ML dependencies when called.

### Ingestion Pipeline

```
PDF → pdf_parser.py (PyMuPDF: text, TOC, section hierarchy)
    → table_detector.py (pdfplumber: find register tables on pages)
    → table_extractor.py (parse tables into Register/BitField structures)
    → chunker.py (semantic chunking with context prefixes)
    → embedder.py (bge-small-en-v1.5, 384-dim, normalized)
    → vector_store.py (FAISS IndexFlatL2) + metadata_store.py (SQLite FTS5)
```

Key chunking rules:
- Only leaf sections are chunked (parents with subsections are skipped to avoid duplication)
- Every chunk gets a hierarchy prefix: `[Doc > Section > Subsection]`
- Text splits on sentence boundaries (`. `, `.\n`, `\n\n`), never mid-word
- Register tables are never split — kept as whole chunks with both text and structured JSON
- Chunk IDs are `{doc_id}_{md5(text)[:12]}` to prevent collisions

### Search Pipeline

```
Query → HybridSearch
        ├─ keyword_search() → SQLite FTS5 (weight: 0.4)
        └─ semantic_search() → FAISS vectors (weight: 0.6)
        → normalize scores 0-1, 1.2× boost for results in both channels
        → ResultFormatter → markdown
```

### Storage

- `index/vectors.faiss` — FAISS flat index (cosine similarity via normalized L2)
- `index/metadata.db` — SQLite with FTS5 virtual table, triggers keep FTS in sync
- `docs/` — PDF input directory (gitignored, per-project)

## Config

`config.yaml` (optional, falls back to defaults). Pydantic models in `config.py`:
- `chunking.target_size`: 2500 chars, `overlap`: 200 chars
- `search.keyword_weight`: 0.4, `semantic_weight`: 0.6
- `embeddings.model`: `BAAI/bge-small-en-v1.5`, `device`: `cpu`

## Plugin

`plugins/bitwise-embedded-docs/` contains the Claude Code plugin with `.mcp.json` entry point and two skills (`/ingest-docs`, `/search-docs`). Bump the version by changing `pyproject.toml` version field.

## Adding a New Tool

1. Create `tools/new_tool.py` with an async function returning a markdown string
2. Register in `server.py` with `@mcp.tool()` decorator (docstring becomes the tool description)
3. Use lazy imports inside the tool function to keep server startup fast
