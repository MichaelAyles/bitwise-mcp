"""Ingest documentation tool."""

import asyncio
import hashlib
from pathlib import Path
from typing import Optional
from ..config import Config
from ..ingestion.pdf_parser import PDFParser
from ..ingestion.table_detector import TableDetector
from ..ingestion.table_extractor import TableExtractor
from ..ingestion.chunker import SemanticChunker
from ..indexing.embedder import LocalEmbedder
from ..indexing.vector_store import VectorStore
from ..indexing.metadata_store import MetadataStore


async def ingest_docs(doc_path: str, title: Optional[str] = None, version: Optional[str] = None,
                      config: Optional[Config] = None) -> str:
    """Ingest a documentation file into the index.

    Currently supports PDF files. Future support planned for other formats.

    Args:
        doc_path: Path to documentation file
        title: Optional document title
        version: Optional document version
        config: Configuration object

    Returns:
        Status message as markdown
    """
    if config is None:
        config = Config.load()

    doc_path_obj = Path(doc_path)

    if not doc_path_obj.exists():
        return f"❌ Error: Documentation file not found: {doc_path}"

    if not doc_path_obj.suffix.lower() == '.pdf':
        return f"❌ Error: Currently only PDF files are supported. Got: {doc_path_obj.suffix}"

    try:
        # Generate document ID from filename
        doc_id = hashlib.md5(doc_path_obj.name.encode()).hexdigest()[:16]

        lines = [f"# Ingesting: {doc_path_obj.name}", ""]

        # Parse PDF
        lines.append("## 1️⃣ Parsing PDF...")
        with PDFParser(doc_path_obj) as parser:
            pages = parser.extract_text_with_layout()
            toc = parser.extract_toc()
            sections = parser.detect_sections(pages, toc)

        lines.append(f"✓ Extracted {len(pages)} pages, {len(sections)} sections")
        lines.append("")

        # Detect and extract tables
        lines.append("## 2️⃣ Detecting register tables...")
        extractor = TableExtractor(str(doc_path_obj))

        all_tables = []
        with TableDetector(str(doc_path_obj)) as detector:
            for page in pages:
                table_regions = detector.detect_register_tables(page)

                for region in table_regions:
                    context = detector.detect_table_context(page, region)
                    table = extractor.extract_register_table(region, context)
                    if table:
                        all_tables.append(table)

        lines.append(f"✓ Found {len(all_tables)} register tables")
        lines.append("")

        # Create chunks
        lines.append("## 3️⃣ Creating semantic chunks...")
        chunker = SemanticChunker(
            target_size=config.chunking.target_size,
            overlap=config.chunking.overlap,
            preserve_tables=config.chunking.preserve_tables
        )

        chunks = chunker.chunk_document(doc_id, sections, all_tables)
        lines.append(f"✓ Created {len(chunks)} chunks")
        lines.append("")

        # Initialize indexing components
        lines.append("## 4️⃣ Creating embeddings and indexing...")
        embedder = LocalEmbedder(
            model_name=config.embeddings.model,
            device=config.embeddings.device
        )

        vector_store = VectorStore(dimension=embedder.dimension)
        metadata_store = MetadataStore(config.index.directory / config.index.metadata_db)

        # Add document metadata
        metadata_store.add_document(
            doc_id=doc_id,
            filename=doc_path_obj.name,
            title=title,
            version=version
        )

        # Process chunks
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.id for chunk in chunks]

        # Create embeddings
        embeddings = embedder.embed_batch(chunk_texts, show_progress=False)

        # Add to vector store
        vector_store.add_vectors(embeddings, chunk_ids)

        # Add to metadata store
        for chunk in chunks:
            metadata_store.add_chunk(
                chunk_id=chunk.id,
                doc_id=chunk.doc_id,
                chunk_type=chunk.chunk_type,
                text=chunk.text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                structured_data=chunk.structured_data,
                metadata=chunk.metadata
            )

        # Save vector store
        config.index.directory.mkdir(parents=True, exist_ok=True)
        vector_store.save(config.index.directory / config.index.vector_file)

        metadata_store.close()

        lines.append(f"✓ Completed indexing")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"✅ **Successfully indexed {doc_path_obj.name}**")
        lines.append("")
        lines.append(f"- **Document ID:** `{doc_id}`")
        lines.append(f"- **Total chunks:** {len(chunks)}")
        lines.append(f"- **Register tables:** {len(all_tables)}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ **Error during ingestion:** {str(e)}"