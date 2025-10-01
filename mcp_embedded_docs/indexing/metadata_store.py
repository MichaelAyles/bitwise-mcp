"""SQLite metadata store with full-text search."""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class MetadataStore:
    """SQLite database for chunk metadata and keyword search."""

    def __init__(self, db_path: Path):
        """Initialize metadata store.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self._create_schema()

    def _create_schema(self):
        """Create database schema."""
        cursor = self.conn.cursor()

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                title TEXT,
                version TEXT,
                index_date TEXT NOT NULL
            )
        """)

        # Chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                section_hierarchy TEXT,
                page_start INTEGER,
                page_end INTEGER,
                text TEXT NOT NULL,
                structured_data TEXT,
                metadata TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)

        # Registers table for quick lookup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registers (
                name TEXT NOT NULL,
                peripheral TEXT,
                address TEXT,
                offset TEXT,
                chunk_id TEXT NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES chunks(id)
            )
        """)

        # Create FTS5 virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                id UNINDEXED,
                text,
                content='chunks',
                content_rowid='rowid'
            )
        """)

        # Create triggers to keep FTS in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, id, text) VALUES (new.rowid, new.id, new.text);
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                DELETE FROM chunks_fts WHERE rowid = old.rowid;
            END
        """)

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                UPDATE chunks_fts SET text = new.text WHERE rowid = old.rowid;
            END
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_registers_name ON registers(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_registers_peripheral ON registers(peripheral)")

        self.conn.commit()

    def add_document(self, doc_id: str, filename: str, title: Optional[str] = None, version: Optional[str] = None):
        """Add a document to the database.

        Args:
            doc_id: Document identifier
            filename: Document filename
            title: Document title
            version: Document version
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, filename, title, version, index_date)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, filename, title, version, datetime.now().isoformat()))
        self.conn.commit()

    def add_chunk(self, chunk_id: str, doc_id: str, chunk_type: str, text: str,
                  page_start: int, page_end: int,
                  structured_data: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None):
        """Add a chunk to the database.

        Args:
            chunk_id: Chunk identifier
            doc_id: Parent document ID
            chunk_type: Type of chunk
            text: Chunk text content
            page_start: Starting page number
            page_end: Ending page number
            structured_data: Optional structured data (will be JSON serialized)
            metadata: Optional metadata dict
        """
        cursor = self.conn.cursor()

        section_hierarchy = None
        if metadata and "section_title" in metadata:
            section_hierarchy = metadata["section_title"]

        structured_json = json.dumps(structured_data) if structured_data else None
        metadata_json = json.dumps(metadata) if metadata else None

        cursor.execute("""
            INSERT OR REPLACE INTO chunks
            (id, doc_id, chunk_type, section_hierarchy, page_start, page_end, text, structured_data, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (chunk_id, doc_id, chunk_type, section_hierarchy, page_start, page_end,
              text, structured_json, metadata_json))

        # Extract and add registers if this is a register table
        if structured_data and "registers" in structured_data:
            peripheral = structured_data.get("peripheral", "Unknown")
            for register in structured_data["registers"]:
                cursor.execute("""
                    INSERT INTO registers (name, peripheral, address, offset, chunk_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (register["name"], peripheral, register.get("address"),
                      register.get("offset"), chunk_id))

        self.conn.commit()

    def keyword_search(self, query: str, top_k: int = 10, doc_filter: Optional[str] = None) -> List[Tuple[str, float]]:
        """Search using keyword matching (FTS5).

        Args:
            query: Search query
            top_k: Number of results
            doc_filter: Optional document ID to filter by

        Returns:
            List of (chunk_id, score) tuples
        """
        cursor = self.conn.cursor()

        if doc_filter:
            cursor.execute("""
                SELECT chunks_fts.id, rank
                FROM chunks_fts
                JOIN chunks ON chunks_fts.id = chunks.id
                WHERE chunks_fts MATCH ? AND chunks.doc_id = ?
                ORDER BY rank
                LIMIT ?
            """, (query, doc_filter, top_k))
        else:
            cursor.execute("""
                SELECT id, rank
                FROM chunks_fts
                WHERE chunks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, top_k))

        results = []
        for row in cursor.fetchall():
            # Convert rank to a score (FTS5 rank is negative)
            score = abs(float(row['rank']))
            results.append((row['id'], score))

        return results

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get chunk by ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Chunk data as dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "doc_id": row["doc_id"],
            "chunk_type": row["chunk_type"],
            "section_hierarchy": row["section_hierarchy"],
            "page_start": row["page_start"],
            "page_end": row["page_end"],
            "text": row["text"],
            "structured_data": json.loads(row["structured_data"]) if row["structured_data"] else None,
            "metadata": json.loads(row["metadata"]) if row["metadata"] else None
        }

    def find_register(self, name: str, peripheral: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find a register by name.

        Args:
            name: Register name
            peripheral: Optional peripheral name to filter

        Returns:
            Chunk containing the register or None
        """
        cursor = self.conn.cursor()

        if peripheral:
            cursor.execute("""
                SELECT chunk_id FROM registers
                WHERE name = ? AND peripheral = ?
                LIMIT 1
            """, (name, peripheral))
        else:
            cursor.execute("""
                SELECT chunk_id FROM registers
                WHERE name = ?
                LIMIT 1
            """, (name,))

        row = cursor.fetchone()
        if not row:
            return None

        return self.get_chunk(row["chunk_id"])

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents.

        Returns:
            List of document info dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY index_date DESC")

        docs = []
        for row in cursor.fetchall():
            docs.append({
                "id": row["id"],
                "filename": row["filename"],
                "title": row["title"],
                "version": row["version"],
                "index_date": row["index_date"]
            })

        return docs

    def get_document_stats(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Dictionary with chunk count and table count, or None if document not found
        """
        cursor = self.conn.cursor()

        # Get total chunk count
        cursor.execute("SELECT COUNT(*) as count FROM chunks WHERE doc_id = ?", (doc_id,))
        chunk_count = cursor.fetchone()["count"]

        # Get table count (chunks with type 'table')
        cursor.execute("SELECT COUNT(*) as count FROM chunks WHERE doc_id = ? AND chunk_type = 'table'", (doc_id,))
        table_count = cursor.fetchone()["count"]

        return {
            "chunks": chunk_count,
            "tables": table_count
        }

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its chunks.

        Args:
            doc_id: Document identifier to delete

        Returns:
            True if document was deleted, False if not found
        """
        cursor = self.conn.cursor()

        # Check if document exists
        cursor.execute("SELECT id FROM documents WHERE id = ?", (doc_id,))
        if not cursor.fetchone():
            return False

        # Delete registers associated with chunks
        cursor.execute("""
            DELETE FROM registers
            WHERE chunk_id IN (SELECT id FROM chunks WHERE doc_id = ?)
        """, (doc_id,))

        # Delete chunks (triggers will handle FTS cleanup)
        cursor.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))

        # Delete document
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        self.conn.commit()
        return True

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()