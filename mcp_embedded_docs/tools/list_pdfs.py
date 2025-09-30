"""List available PDFs and their ingestion status."""

from pathlib import Path
from typing import Optional, List, Dict, Any
from ..config import Config
from ..retrieval.hybrid_search import HybridSearch


async def list_pdfs(config: Optional[Config] = None) -> str:
    """List all PDFs in doc directories with ingestion status.

    Args:
        config: Configuration object

    Returns:
        Formatted list of PDFs with status as markdown
    """
    if config is None:
        config = Config.load()

    search = HybridSearch(config)

    try:
        # Get list of indexed documents
        indexed_docs = search.list_documents()
        indexed_filenames = {doc['filename'] for doc in indexed_docs}

        # Scan doc directories for PDF files
        all_pdfs: List[Dict[str, Any]] = []

        for doc_dir in config.doc_dirs:
            if not doc_dir.exists():
                continue

            for pdf_path in doc_dir.glob("**/*.pdf"):
                pdf_name = pdf_path.name
                is_ingested = pdf_name in indexed_filenames

                all_pdfs.append({
                    'path': pdf_path,
                    'name': pdf_name,
                    'size_mb': pdf_path.stat().st_size / (1024 * 1024),
                    'ingested': is_ingested
                })

        if not all_pdfs:
            return f"No PDF files found in configured directories: {', '.join(str(d) for d in config.doc_dirs)}"

        # Sort: ingested first, then by name
        all_pdfs.sort(key=lambda x: (not x['ingested'], x['name']))

        # Format output
        lines = ["# Available PDF Files", ""]

        ingested_count = sum(1 for pdf in all_pdfs if pdf['ingested'])
        not_ingested_count = len(all_pdfs) - ingested_count

        lines.append(f"**Total:** {len(all_pdfs)} PDFs ({ingested_count} ingested, {not_ingested_count} not ingested)")
        lines.append("")

        if ingested_count > 0:
            lines.append("## ✅ Ingested")
            lines.append("")
            for pdf in all_pdfs:
                if pdf['ingested']:
                    lines.append(f"- `{pdf['name']}` ({pdf['size_mb']:.1f} MB)")
            lines.append("")

        if not_ingested_count > 0:
            lines.append("## ⏳ Not Ingested")
            lines.append("")
            for pdf in all_pdfs:
                if not pdf['ingested']:
                    lines.append(f"- `{pdf['name']}` ({pdf['size_mb']:.1f} MB) - Path: `{pdf['path']}`")
            lines.append("")

        return "\n".join(lines)

    finally:
        search.close()