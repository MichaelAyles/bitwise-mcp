"""CLI entry point for MCP Embedded Docs."""

import click
from pathlib import Path
import hashlib

from .config import Config
from .ingestion.pdf_parser import PDFParser
from .ingestion.table_detector import TableDetector
from .ingestion.table_extractor import TableExtractor
from .ingestion.chunker import SemanticChunker
from .indexing.embedder import LocalEmbedder
from .indexing.vector_store import VectorStore
from .indexing.metadata_store import MetadataStore
from .server import main as server_main


@click.group()
def cli():
    """MCP Embedded Documentation Server CLI."""
    pass


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--title', help='Document title')
@click.option('--version', help='Document version')
def ingest(pdf_path: str, title: str = None, version: str = None):
    """Index a PDF document.

    Extracts text, detects and parses register tables, creates embeddings,
    and stores everything in the index for searching.
    """
    pdf_path = Path(pdf_path)
    config = Config.load()

    click.echo(f"Ingesting {pdf_path.name}...")

    # Generate document ID from filename
    doc_id = hashlib.md5(pdf_path.name.encode()).hexdigest()[:16]

    # Parse PDF
    click.echo("Parsing PDF...")
    with PDFParser(pdf_path) as parser:
        pages = parser.extract_text_with_layout()
        toc = parser.extract_toc()
        sections = parser.detect_sections(pages, toc)

    click.echo(f"  Extracted {len(pages)} pages, {len(sections)} sections")

    # Detect and extract tables
    click.echo("Detecting register tables...")
    extractor = TableExtractor(str(pdf_path))

    all_tables = []
    with TableDetector(str(pdf_path)) as detector:
        for page in pages:
            table_regions = detector.detect_register_tables(page)

            for region in table_regions:
                context = detector.detect_table_context(page, region)
                table = extractor.extract_register_table(region, context)
                if table:
                    all_tables.append(table)

    click.echo(f"  Found {len(all_tables)} register tables")

    # Create chunks
    click.echo("Creating semantic chunks...")
    chunker = SemanticChunker(
        target_size=config.chunking.target_size,
        overlap=config.chunking.overlap,
        preserve_tables=config.chunking.preserve_tables
    )

    chunks = chunker.chunk_document(doc_id, sections, all_tables)
    click.echo(f"  Created {len(chunks)} chunks")

    # Initialize indexing components
    click.echo("Indexing...")
    embedder = LocalEmbedder(
        model_name=config.embeddings.model,
        device=config.embeddings.device
    )

    vector_store = VectorStore(dimension=embedder.dimension)
    metadata_store = MetadataStore(config.index.directory / config.index.metadata_db)

    # Add document metadata
    metadata_store.add_document(
        doc_id=doc_id,
        filename=pdf_path.name,
        title=title,
        version=version
    )

    # Process chunks
    chunk_texts = [chunk.text for chunk in chunks]
    chunk_ids = [chunk.id for chunk in chunks]

    # Create embeddings
    click.echo("  Creating embeddings...")
    embeddings = embedder.embed_batch(chunk_texts, show_progress=True)

    # Add to vector store
    vector_store.add_vectors(embeddings, chunk_ids)

    # Add to metadata store
    click.echo("  Storing metadata...")
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

    click.echo(f"✓ Successfully indexed {pdf_path.name}")
    click.echo(f"  Document ID: {doc_id}")
    click.echo(f"  Total chunks: {len(chunks)}")
    click.echo(f"  Register tables: {len(all_tables)}")


@cli.command()
def serve():
    """Start MCP server on stdio."""
    click.echo("Starting MCP server...")
    server_main()


@cli.command()
def list():
    """List indexed documents."""
    config = Config.load()
    metadata_store = MetadataStore(config.index.directory / config.index.metadata_db)

    try:
        docs = metadata_store.list_documents()

        if not docs:
            click.echo("No documents indexed yet.")
            return

        click.echo("Indexed Documents:")
        click.echo("")

        for doc in docs:
            click.echo(f"  {doc['filename']}")
            if doc['title']:
                click.echo(f"    Title: {doc['title']}")
            if doc['version']:
                click.echo(f"    Version: {doc['version']}")
            click.echo(f"    ID: {doc['id']}")
            click.echo(f"    Indexed: {doc['index_date']}")
            click.echo("")
    finally:
        metadata_store.close()


if __name__ == "__main__":
    cli()