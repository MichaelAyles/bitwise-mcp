# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for embedded developers that ingests large PDF reference manuals (1000+ pages), extracts register definitions, and provides fast semantic search with minimal token usage. The primary use case is processing documents like the S32K144 reference manual (2200 pages) to make them accessible to code assistants.

## Project Status

This is an early-stage project. The current repository contains:
- `claude_code_prompt.md` - Detailed implementation specification
- `S32K-RM (2).pdf` - Sample S32K144 reference manual for testing
- No implementation code yet

## Architecture (Planned)

The system follows a pipeline architecture:

1. **Ingestion Pipeline** (`ingestion/`)
   - PDF parsing with PyMuPDF preserving layout structure
   - Table detection using heuristics for register definitions
   - Table extraction into structured JSON format
   - Optional LLM fallback (OpenRouter) for complex tables
   - Semantic chunking that preserves table integrity

2. **Indexing Layer** (`indexing/`)
   - Local embeddings using sentence-transformers (BAAI/bge-small-en-v1.5)
   - FAISS vector store for similarity search
   - SQLite with FTS5 for keyword search and metadata
   - Structured storage for register definitions

3. **Retrieval System** (`retrieval/`)
   - Hybrid search (40% keyword + 60% semantic)
   - Register name boosting for exact matches
   - Result ranking and compact formatting

4. **MCP Server** (`server.py` and `tools/`)
   - `search_docs` - General documentation search
   - `find_register` - Specific register lookup
   - `get_section` - Section retrieval
   - `list_docs` - List indexed documents

## Key Design Decisions

### Table Extraction Strategy
Register tables are the most critical content type. The extraction uses:
- Heuristic detection looking for keywords: "Address", "Offset", "Width", "Field", "Description", "Type"
- Grid pattern analysis for table boundaries
- pdfplumber for cell extraction
- Structured output format capturing register names, addresses, bit fields, reset values
- LLM fallback only when heuristics fail

### Token Efficiency
Output format is designed for minimal token usage:
- Compact register definitions (not verbose prose)
- Structured format with abbreviations
- Always include citations (doc name, section, page)
- Target <1000 tokens per response

### Chunking Rules
- Keep register tables intact (never split across chunks)
- Split long sections at paragraph boundaries
- 500-1500 tokens per chunk
- Include overlap (100 tokens) for continuity
- Preserve context in metadata (peripheral name, chapter hierarchy)

## Technology Stack

- **Python 3.10+** - All code
- **pymupdf (fitz)** - PDF text extraction with layout
- **pdfplumber** - Table detection and extraction
- **sentence-transformers** - Local embeddings (no API calls)
- **FAISS** - Vector similarity search
- **SQLite** with FTS5 - Metadata and keyword search
- **MCP SDK** - Server implementation
- **openai + httpx** - OpenRouter client (optional fallback)

## Development Workflow

### HARD RULES - MUST FOLLOW

1. **Commit after each feature** - Create a git commit immediately after completing each distinct feature or component
2. **Only commit when error-free** - NEVER commit code that has errors, failing tests, or any part of the project in a broken state
3. **Verify before committing** - Always run tests and verify functionality before creating a commit
4. **Use subagents liberally** - Leverage the Task tool with specialized agents as much as needed for complex tasks, parallel work, or deep analysis

### Initial Setup (when implementing)
```bash
poetry install
```

### Indexing a PDF
```bash
python -m mcp_embedded_docs ingest <pdf_path>
python -m mcp_embedded_docs ingest <pdf_path> --use-llm  # Enable LLM fallback
```

### Starting MCP Server
```bash
python -m mcp_embedded_docs serve
```

### Testing
```bash
pytest tests/
```

### Typical Development Cycle
1. Implement a feature/component
2. Test thoroughly (run pytest, verify functionality)
3. Fix any errors or issues
4. Once everything works with no errors, commit
5. Move to next feature

## Implementation Priority

Per `claude_code_prompt.md`, implement in this order:
1. `pyproject.toml` - Project dependencies
2. `config.py` - Configuration loading
3. `ingestion/pdf_parser.py` - Basic text extraction
4. `ingestion/table_detector.py` - Register table detection
5. **Test on sample S32K144 pages before continuing**
6. Table extraction, then chunking, indexing, retrieval, MCP server

Focus on table extraction quality first - this is the most challenging and critical component.

## Testing Strategy

- Start with 10-20 sample pages from S32K144 containing known register tables
- Verify table extraction accuracy (target: 80%+ of tables parsed correctly)
- Ensure chunking doesn't split register definitions
- Test search relevance (e.g., "FlexCAN MCR register" returns correct info)
- Measure full document ingestion time
- Verify token efficiency (<1000 tokens per response)

## Configuration

See `config.yaml` (to be created) for:
- Document directories
- Embedding model settings
- LLM fallback configuration (optional)
- Chunking parameters
- Search weights (keyword vs semantic)

Default search weighting: 40% keyword, 60% semantic