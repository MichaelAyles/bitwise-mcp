"""List documents tool."""

from pathlib import Path
from typing import Optional, List, Dict, Any
import fitz  # PyMuPDF

from ..retrieval.hybrid_search import HybridSearch
from ..config import Config


async def list_docs(config: Optional[Config] = None) -> str:
    """List all documents (both indexed and available for ingestion).

    Args:
        config: Configuration object

    Returns:
        Formatted list of documents as markdown
    """
    if config is None:
        config = Config.load()

    search = HybridSearch(config)

    try:
        # Get indexed documents with stats
        indexed_docs = search.list_documents()
        indexed_filenames = {doc['filename']: doc for doc in indexed_docs}

        # Scan doc directories for all PDF files
        all_pdfs: List[Dict[str, Any]] = []

        for doc_dir in config.doc_dirs:
            if not doc_dir.exists():
                continue

            for pdf_path in doc_dir.glob("**/*.pdf"):
                pdf_name = pdf_path.name
                is_ingested = pdf_name in indexed_filenames

                if is_ingested:
                    doc_info = indexed_filenames[pdf_name]
                    # Get statistics
                    stats = search.metadata_store.get_document_stats(doc_info['id'])
                    all_pdfs.append({
                        'path': pdf_path,
                        'name': pdf_name,
                        'size_mb': pdf_path.stat().st_size / (1024 * 1024),
                        'ingested': True,
                        'id': doc_info['id'],
                        'title': doc_info.get('title'),
                        'version': doc_info.get('version'),
                        'index_date': doc_info['index_date'],
                        'chunks': stats['chunks'],
                        'tables': stats['tables']
                    })
                else:
                    # Get PDF metadata for non-ingested files
                    try:
                        with fitz.open(pdf_path) as pdf:
                            page_count = len(pdf)
                    except:
                        page_count = None

                    all_pdfs.append({
                        'path': pdf_path,
                        'name': pdf_name,
                        'size_mb': pdf_path.stat().st_size / (1024 * 1024),
                        'ingested': False,
                        'pages': page_count
                    })

        if not all_pdfs:
            return f"No documents found in configured directories: {', '.join(str(d) for d in config.doc_dirs)}"

        # Sort: ingested first, then by name
        all_pdfs.sort(key=lambda x: (not x['ingested'], x['name']))

        # Format output
        lines = ["# Documentation", ""]

        ingested_count = sum(1 for pdf in all_pdfs if pdf['ingested'])
        not_ingested_count = len(all_pdfs) - ingested_count

        lines.append(f"**Total:** {len(all_pdfs)} documents ({ingested_count} indexed, {not_ingested_count} available)")
        lines.append("")

        if ingested_count > 0:
            lines.append("## ✅ Indexed Documents")
            lines.append("")
            for pdf in all_pdfs:
                if pdf['ingested']:
                    lines.append(f"### {pdf['name']}")
                    if pdf.get('title'):
                        lines.append(f"**Title:** {pdf['title']}")
                    if pdf.get('version'):
                        lines.append(f"**Version:** {pdf['version']}")
                    lines.append(f"**ID:** `{pdf['id']}`")
                    lines.append(f"**Size:** {pdf['size_mb']:.1f} MB")
                    lines.append(f"**Chunks:** {pdf['chunks']}")
                    lines.append(f"**Tables:** {pdf['tables']}")
                    lines.append(f"**Indexed:** {pdf['index_date']}")
                    lines.append("")

        if not_ingested_count > 0:
            lines.append("## ⏳ Available for Ingestion")
            lines.append("")
            for pdf in all_pdfs:
                if not pdf['ingested']:
                    lines.append(f"### {pdf['name']}")
                    lines.append(f"**Path:** `{pdf['path']}`")
                    lines.append(f"**Size:** {pdf['size_mb']:.1f} MB")
                    if pdf.get('pages'):
                        lines.append(f"**Pages:** {pdf['pages']}")
                    lines.append("")

        return "\n".join(lines)

    finally:
        search.close()