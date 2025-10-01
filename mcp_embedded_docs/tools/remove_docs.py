"""Remove documents tool."""

from typing import Optional
from ..config import Config
from ..retrieval.hybrid_search import HybridSearch


async def remove_docs(doc_id: str, config: Optional[Config] = None) -> str:
    """Remove a document from the index.

    Args:
        doc_id: Document ID to remove
        config: Configuration object

    Returns:
        Status message as markdown
    """
    if config is None:
        config = Config.load()

    search = HybridSearch(config)

    try:
        # Get document info before deleting
        docs = search.list_documents()
        doc_to_delete = None
        for doc in docs:
            if doc['id'] == doc_id:
                doc_to_delete = doc
                break

        if not doc_to_delete:
            return f"❌ Error: Document not found: {doc_id}"

        # Delete from metadata store
        deleted = search.metadata_store.delete_document(doc_id)

        if deleted:
            filename = doc_to_delete.get('filename', 'Unknown')
            return f"✅ Successfully removed document: {filename} (ID: {doc_id})\n\nNote: Vector embeddings remain in the index. Re-ingest other documents to rebuild the vector store if needed."
        else:
            return f"❌ Error: Failed to delete document: {doc_id}"

    finally:
        search.close()
