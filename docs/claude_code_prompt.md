# Prompt for Claude Code: Build MCP Embedded Documentation Server

## Project Goal
Build a Python-based MCP server that ingests large PDF reference manuals (specifically the S32K144 2200-page manual) and component datasheets, creating a searchable index for efficient retrieval by code assistants. The system must handle arbitrary PDF formats without relying on CMSIS-SVD files.

## Technical Requirements

### Core Functionality
1. **PDF Ingestion:** Parse PDFs preserving structure (chapters, sections, tables)
2. **Table Extraction:** Detect and parse register tables into structured JSON
3. **Semantic Indexing:** Create vector embeddings for fast retrieval
4. **MCP Server:** Expose tools for querying documentation
5. **Compact Output:** Format responses to minimize token usage
6. **LLM Fallback:** Optional OpenRouter integration for complex table parsing

### Technology Stack
- **Python 3.10+** for all components
- **pymupdf (fitz)** - Fast PDF text extraction with layout
- **pdfplumber** - Table detection and extraction
- **sentence-transformers** - Local embeddings (BAAI/bge-small-en-v1.5)
- **FAISS** - Vector similarity search
- **SQLite** - Metadata storage with FTS5 for keyword search
- **MCP SDK** - Server implementation
- **openai + httpx** - OpenRouter API client (optional)

## Project Structure to Create

```
mcp-embedded-docs/
├── pyproject.toml
├── README.md
├── config.yaml
├── mcp_embedded_docs/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── config.py            # Configuration loader
│   ├── server.py            # MCP server
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py       # PyMuPDF + pdfplumber
│   │   ├── table_detector.py   # Heuristic table detection
│   │   ├── table_extractor.py  # Convert tables to structured data
│   │   ├── llm_fallback.py     # OpenRouter integration
│   │   └── chunker.py          # Semantic chunking logic
│   ├── indexing/
│   │   ├── __init__.py
│   │   ├── embedder.py         # sentence-transformers wrapper
│   │   ├── vector_store.py     # FAISS index management
│   │   └── metadata_store.py   # SQLite database
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── hybrid_search.py    # Keyword + semantic search
│   │   ├── ranker.py           # Result scoring/ranking
│   │   └── formatter.py        # Format results compactly
│   └── tools/
│       ├── __init__.py
│       ├── search_docs.py
│       ├── find_register.py
│       ├── get_section.py
│       └── list_docs.py
├── docs/                     # User PDF directory (gitignored)
├── index/                    # Generated indexes (gitignored)
│   ├── vectors.faiss
│   ├── metadata.db
│   └── documents.json
└── tests/
    ├── test_pdf_parser.py
    ├── test_table_extractor.py
    └── test_search.py
```

## Implementation Steps

### Step 1: Project Setup
Create pyproject.toml with dependencies:
```toml
[tool.poetry]
name = "mcp-embedded-docs"
version = "0.1.0"
description = "MCP server for embedded systems documentation"

[tool.poetry.dependencies]
python = "^3.10"
pymupdf = "^1.23.0"
pdfplumber = "^0.10.0"
sentence-transformers = "^2.2.0"
faiss-cpu = "^1.7.4"
sqlalchemy = "^2.0.0"
mcp = "^0.9.0"
pydantic = "^2.5.0"
openai = "^1.6.0"
httpx = "^0.25.0"
pyyaml = "^6.0"
click = "^8.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
black = "^23.12.0"
```

### Step 2: PDF Parser (`ingestion/pdf_parser.py`)

Key functions to implement:
```python
def extract_text_with_layout(pdf_path: Path) -> List[Page]:
    """
    Extract text preserving layout structure using PyMuPDF.
    Return pages with blocks, lines, and bounding boxes.
    """

def extract_toc(pdf_path: Path) -> List[TOCEntry]:
    """
    Extract table of contents from PDF.
    Returns hierarchical structure of sections.
    """

def detect_sections(pages: List[Page]) -> List[Section]:
    """
    Identify section boundaries using:
    - Font size changes (headers are larger)
    - TOC references
    - Common patterns like "Chapter 45.3.2"
    """
```

### Step 3: Table Detector (`ingestion/table_detector.py`)

Implement heuristics for S32K144-style register tables:
```python
def detect_register_tables(page: Page) -> List[TableRegion]:
    """
    Detect register tables using:
    1. Column headers: "Address", "Offset", "Width", "Field", "Description", "Type"
    2. Grid patterns (horizontal/vertical lines)
    3. Proximity to keywords: "Memory Map", "Register Definition"
    4. Consistent cell structure
    
    Return bounding boxes of detected tables.
    """

def classify_table_type(table: TableRegion) -> TableType:
    """
    Classify as:
    - REGISTER_MAP (base addresses, offsets)
    - BITFIELD_DEFINITION (field names, bit ranges)
    - MEMORY_MAP (peripheral addresses)
    - OTHER
    """
```

### Step 4: Table Extractor (`ingestion/table_extractor.py`)

Parse detected tables into structured data:
```python
def extract_register_table(table_region: TableRegion, page: Page) -> RegisterTable:
    """
    Use pdfplumber to extract table cells.
    Parse into structured format:
    {
        "peripheral": "FlexCAN0",
        "registers": [
            {
                "name": "MCR",
                "offset": "0x00",
                "address": "0x40024000",
                "width": 32,
                "reset_value": "0xD890000F",
                "access": "RW",
                "fields": [
                    {
                        "name": "MDIS",
                        "bits": "31",
                        "bit_range": [31, 31],
                        "access": "RW",
                        "description": "Module Disable"
                    }
                ]
            }
        ]
    }
    """

def handle_merged_cells(table_data: List[List[str]]) -> List[List[str]]:
    """Handle common PDF table issues like merged cells."""

def parse_bit_notation(bit_string: str) -> Tuple[int, int]:
    """Parse "[31:24]", "[23]", "31:24" into (msb, lsb) tuples."""
```

### Step 5: LLM Fallback (`ingestion/llm_fallback.py`)

For complex tables that heuristics fail:
```python
async def parse_table_with_llm(
    table_image: bytes,
    table_text: str,
    openrouter_config: dict
) -> Optional[dict]:
    """
    Send table to OpenRouter API with prompt:
    
    'Parse this register table into JSON format. Extract:
    - Register names, addresses/offsets, widths
    - Field names, bit ranges, access types
    - Reset values and descriptions
    
    Format: {...}
    
    Be precise with bit ranges. If unsure, mark field as "unclear".'
    
    Use Claude Haiku or GPT-4o-mini for cost efficiency.
    Cache responses to avoid re-parsing same table.
    """
```

### Step 6: Semantic Chunker (`ingestion/chunker.py`)

```python
def chunk_document(
    sections: List[Section],
    tables: List[RegisterTable],
    target_size: int = 1000,
    overlap: int = 100
) -> List[Chunk]:
    """
    Create chunks that:
    1. Keep register tables intact (never split)
    2. Split long sections at paragraph boundaries
    3. Preserve context: peripheral name, chapter title in metadata
    4. Add overlap between adjacent chunks for continuity
    
    Each chunk should be 500-1500 tokens, but prefer semantic boundaries.
    """

def create_chunk_metadata(chunk: Chunk, document: Document) -> dict:
    """
    Generate rich metadata:
    - Document ID and name
    - Section hierarchy
    - Page numbers
    - Peripheral/register names (if applicable)
    - Chunk type (text, register_definition, memory_map, etc.)
    """
```

### Step 7: Embedder (`indexing/embedder.py`)

```python
class LocalEmbedder:
    """
    Wrapper for sentence-transformers.
    Use 'BAAI/bge-small-en-v1.5' - good quality, small size.
    """
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed texts in batches for efficiency."""
        return self.model.encode(texts, show_progress_bar=True)
```

### Step 8: Vector Store (`indexing/vector_store.py`)

```python
class VectorStore:
    """FAISS-based vector storage."""
    
    def __init__(self, dimension: int = 384):
        # Use FAISS IVF for speed with large datasets
        self.index = faiss.IndexFlatL2(dimension)
    
    def add_vectors(self, vectors: np.ndarray, ids: List[str]):
        """Add embeddings with corresponding chunk IDs."""
    
    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """Return (chunk_id, distance) pairs."""
```

### Step 9: Metadata Store (`indexing/metadata_store.py`)

SQLite schema:
```python
def create_schema(conn: sqlite3.Connection):
    """
    chunks table:
    - id (PRIMARY KEY)
    - doc_id
    - chunk_type (text, register_definition, etc.)
    - section_hierarchy (e.g., "Chapter 45 > 45.3 > 45.3.2")
    - page_start, page_end
    - text (FTS5 full-text indexed)
    - structured_data (JSON blob for register tables)
    
    registers table:
    - name
    - peripheral
    - address
    - chunk_id (FOREIGN KEY)
    
    documents table:
    - id (PRIMARY KEY)
    - filename
    - title
    - version
    - index_date
    
    Create indexes on frequently queried fields.
    """
```

### Step 10: Hybrid Search (`retrieval/hybrid_search.py`)

```python
async def search(
    query: str,
    top_k: int = 5,
    doc_filter: Optional[str] = None
) -> List[SearchResult]:
    """
    1. Keyword search using SQLite FTS5 on chunk text
    2. Semantic search using FAISS on query embedding
    3. Combine scores: 0.4 * keyword + 0.6 * semantic
    4. Boost exact matches for register names
    5. Filter by document if specified
    6. Return top_k results with metadata and snippets
    """
```

### Step 11: MCP Tools (`tools/*.py`)

Implement these MCP tools:

**search_docs:**
```python
@mcp.tool()
async def search_docs(
    query: str,
    top_k: int = 5,
    doc_filter: Optional[str] = None
) -> str:
    """
    Search documentation. Returns markdown-formatted results.
    Include register definitions in compact format when found.
    Always include citations (doc name, section, page).
    """
```

**find_register:**
```python
@mcp.tool()
async def find_register(
    name: str,
    peripheral: Optional[str] = None
) -> str:
    """
    Find specific register by name.
    Format output as compact register definition:
    
    ## FlexCAN0 MCR (0x40024000)
    **Offset:** 0x00 | **Width:** 32-bit | **Reset:** 0xD890000F
    
    ### Fields:
    - MDIS [31]: Module Disable (RW)
    - FRZ [30]: Freeze Enable (RW)
    ...
    
    **Source:** S32K144_RM, Section 45.3.2, Page 1547
    """
```

### Step 12: CLI (`__main__.py`)

```python
@click.group()
def cli():
    """MCP Embedded Docs CLI"""

@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--use-llm', is_flag=True)
def ingest(pdf_path: str, use_llm: bool):
    """Index a PDF document."""
    # Run full ingestion pipeline

@cli.command()
def serve():
    """Start MCP server."""
    # Start MCP server listening on stdio

@cli.command()
def list():
    """List indexed documents."""
```

## Testing Approach

1. **Start with sample pages:** Extract 10-20 pages from S32K144 with known register tables
2. **Test table extraction:** Verify accuracy of parsed register definitions
3. **Test chunking:** Ensure register tables aren't split
4. **Test search:** Query "FlexCAN MCR register" should return correct info
5. **Measure performance:** Time full 2200-page ingestion
6. **Token efficiency:** Verify responses are <1000 tokens

## Success Criteria

- [ ] Parse S32K144 manual without errors
- [ ] Extract 80%+ of register tables correctly
- [ ] Search returns relevant results in <500ms
- [ ] Output format uses <1000 tokens per response
- [ ] Works without LLM fallback (graceful degradation)
- [ ] Can index multiple documents simultaneously

## Key Challenges & Solutions

**Challenge:** Tables in PDFs are notoriously difficult to parse
**Solution:** Use pdfplumber's table detection + custom heuristics for register table patterns + optional LLM fallback

**Challenge:** 2200 pages = huge token cost if done naively
**Solution:** Semantic chunking + structured extraction + compact output format

**Challenge:** No CMSIS-SVD means no guaranteed structure
**Solution:** Flexible parsing with pattern matching, not hardcoded assumptions

**Challenge:** Need local operation
**Solution:** sentence-transformers for embeddings, FAISS for search, SQLite for metadata

## Configuration Example

`config.yaml`:
```yaml
doc_dirs:
  - ./docs

embeddings:
  model: "BAAI/bge-small-en-v1.5"
  device: "cpu"
  batch_size: 32

llm_fallback:
  enabled: false
  provider: "openrouter"
  api_key_env: "OPENROUTER_API_KEY"
  model: "anthropic/claude-3-haiku"
  cache_results: true

chunking:
  target_size: 1000
  overlap: 100
  preserve_tables: true

search:
  keyword_weight: 0.4
  semantic_weight: 0.6
  top_k_default: 5
```

## Start Implementation

Begin with these files in order:
1. `pyproject.toml` - Set up project
2. `config.py` - Configuration loading
3. `ingestion/pdf_parser.py` - Basic PDF extraction
4. `ingestion/table_detector.py` - Table detection heuristics
5. Test on sample S32K144 pages before continuing

Focus on getting robust table extraction working first - that's the most critical component for embedded docs.
