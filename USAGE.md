# MCP Embedded Docs - Usage Guide

This guide shows how to use the MCP embedded documentation server.

## Installation

```bash
# Install dependencies
poetry install

# Or using pip in a virtual environment
pip install -e .
```

## Quick Start

### 1. Index a PDF Document

```bash
# Basic indexing
poetry run mcp-embedded-docs ingest path/to/manual.pdf

# With metadata
poetry run mcp-embedded-docs ingest \
    "sample-data/S32K-RM (2).pdf" \
    --title "S32K144 Reference Manual" \
    --version "Rev. 13"
```

This will:
- Parse the PDF (text + tables)
- Detect register definitions
- Create semantic chunks
- Generate embeddings
- Store in local index (./index/)

### 2. List Indexed Documents

```bash
poetry run mcp-embedded-docs list
```

### 3. Start MCP Server

```bash
poetry run mcp-embedded-docs serve
```

The server runs on stdio and provides three tools:
- `search_docs` - Search documentation
- `find_register` - Find specific registers
- `list_docs` - List indexed documents

## Using from Python

### Search Documentation

```python
import asyncio
from mcp_embedded_docs.config import Config
from mcp_embedded_docs.tools.search_docs import search_docs

async def main():
    config = Config.load()

    # Search for FlexCAN information
    result = await search_docs("FlexCAN initialization", top_k=5, config=config)
    print(result)

asyncio.run(main())
```

### Find a Register

```python
import asyncio
from mcp_embedded_docs.config import Config
from mcp_embedded_docs.tools.find_register import find_register

async def main():
    config = Config.load()

    # Find MCR register in FlexCAN
    result = await find_register("MCR", peripheral="FlexCAN", config=config)
    print(result)

asyncio.run(main())
```

### List Documents

```python
import asyncio
from mcp_embedded_docs.config import Config
from mcp_embedded_docs.tools.list_docs import list_docs

async def main():
    config = Config.load()
    result = await list_docs(config)
    print(result)

asyncio.run(main())
```

## Configuration

Create a `config.yaml` file (see `config.yaml.example`):

```yaml
doc_dirs:
  - ./docs

embeddings:
  model: "BAAI/bge-small-en-v1.5"
  device: "cpu"
  batch_size: 32

chunking:
  target_size: 1000
  overlap: 100
  preserve_tables: true

search:
  keyword_weight: 0.4
  semantic_weight: 0.6
  top_k_default: 5

index:
  directory: "./index"
  vector_file: "vectors.faiss"
  metadata_db: "metadata.db"
```

## MCP Client Configuration

To use with Claude Desktop or other MCP clients, add to your MCP settings:

```json
{
  "mcpServers": {
    "embedded-docs": {
      "command": "poetry",
      "args": [
        "run",
        "mcp-embedded-docs",
        "serve"
      ],
      "cwd": "/path/to/bitwise-mcp"
    }
  }
}
```

Then in Claude, you can:

```
Search the S32K144 documentation for GPIO configuration examples
```

```
Find the FlexCAN MCR register definition
```

## Testing

Run the included test scripts:

```bash
# Test search functionality
poetry run python test_search.py

# Test MCP server startup
poetry run python test_mcp_server.py
```

## Architecture

The system uses a multi-stage pipeline:

1. **Ingestion** - Parse PDF, detect tables, chunk content
2. **Indexing** - Create embeddings, build vector index
3. **Retrieval** - Hybrid search (keyword + semantic)
4. **Formatting** - Compact markdown output

### Data Flow

```
PDF → Parser → Table Detector → Extractor → Chunker
                                              ↓
                                          Embedder
                                              ↓
                                    Vector Store + Metadata Store
                                              ↓
                                       Hybrid Search
                                              ↓
                                         Formatter
                                              ↓
                                        MCP Tools
```

## Performance

Tested on S32K144 Reference Manual (2179 pages, 14MB):
- **Indexing time**: ~3 minutes
- **Search time**: <500ms
- **Storage**: ~100MB (embeddings + metadata)
- **Memory**: ~1GB during indexing, ~500MB during search

## Troubleshooting

### Import Errors

If you see import errors, make sure you're running from the poetry environment:

```bash
poetry shell
python test_search.py
```

### No Search Results

Check that documents are indexed:

```bash
poetry run mcp-embedded-docs list
```

Verify the index directory exists:

```bash
ls -lh index/
```

### Slow Search

First search is slower due to model loading. Subsequent searches are fast (<500ms).

## Next Steps

See `CLAUDE.md` for development guidance and architecture details.