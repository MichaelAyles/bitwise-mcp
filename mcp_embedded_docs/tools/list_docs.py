"""List documents tool."""

import logging
from pathlib import Path
from typing import Optional

from ..indexing.metadata_store import MetadataStore
from ..config import Config

logger = logging.getLogger(__name__)


async def list_docs(config: Optional[Config] = None) -> str:
    """List all PDF files in doc directories and their index status.

    Args:
        config: Configuration object

    Returns:
        Formatted list of documents as markdown
    """
    if config is None:
        config = Config.load()

    # Lightweight DB check for indexed status
    db_path = config.index.directory / config.index.metadata_db
    indexed_filenames: dict = {}
    if db_path.exists():
        store = MetadataStore(db_path)
        try:
            for doc in store.list_documents():
                indexed_filenames[doc['filename']] = doc
        finally:
            store.close()

    # Scan doc directories for PDF files
    all_pdfs = []
    for doc_dir in config.doc_dirs:
        if not doc_dir.exists():
            continue
        for pdf_path in doc_dir.glob("**/*.pdf"):
            all_pdfs.append({
                'path': pdf_path,
                'name': pdf_path.name,
                'size_mb': pdf_path.stat().st_size / (1024 * 1024),
                'indexed': pdf_path.name in indexed_filenames,
            })

    if not all_pdfs:
        return f"No PDF files found in: {', '.join(str(d) for d in config.doc_dirs)}"

    all_pdfs.sort(key=lambda x: (not x['indexed'], x['name']))

    lines = ["# Documentation", ""]
    indexed_count = sum(1 for p in all_pdfs if p['indexed'])
    lines.append(f"**{len(all_pdfs)}** PDFs found ({indexed_count} indexed)")
    lines.append("")

    for pdf in all_pdfs:
        status = "indexed" if pdf['indexed'] else "not indexed"
        lines.append(f"- **{pdf['name']}** ({pdf['size_mb']:.1f} MB) — {status}")
        if pdf['indexed']:
            doc = indexed_filenames[pdf['name']]
            lines.append(f"  - ID: `{doc['id']}`")

    return "\n".join(lines)