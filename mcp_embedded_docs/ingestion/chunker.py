"""Semantic chunking for documents."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json

from .pdf_parser import Section
from .table_extractor import RegisterTable


@dataclass
class Chunk:
    """A chunk of document content."""
    id: str
    doc_id: str
    chunk_type: str  # "text", "register_definition", "memory_map"
    text: str
    structured_data: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    page_start: int
    page_end: int


class SemanticChunker:
    """Create semantic chunks from parsed documents."""

    def __init__(self, target_size: int = 1000, overlap: int = 100, preserve_tables: bool = True):
        """Initialize chunker.

        Args:
            target_size: Target chunk size in characters
            overlap: Overlap between adjacent text chunks
            preserve_tables: Keep register tables intact (never split)
        """
        self.target_size = target_size
        self.overlap = overlap
        self.preserve_tables = preserve_tables

    def chunk_document(
        self,
        doc_id: str,
        sections: List[Section],
        tables: List[RegisterTable]
    ) -> List[Chunk]:
        """Create chunks from document sections and tables.

        Args:
            doc_id: Document identifier
            sections: Document sections
            tables: Extracted register tables

        Returns:
            List of chunks
        """
        chunks = []

        # First, create chunks for register tables (these are always kept intact)
        table_chunks = self._chunk_tables(doc_id, tables)
        chunks.extend(table_chunks)

        # Then, create chunks for text sections
        text_chunks = self._chunk_sections(doc_id, sections)
        chunks.extend(text_chunks)

        return chunks

    def _chunk_tables(self, doc_id: str, tables: List[RegisterTable]) -> List[Chunk]:
        """Create chunks for register tables."""
        chunks = []

        for i, table in enumerate(tables):
            # Convert table to both text and structured format
            text = self._format_table_as_text(table)
            structured = self._format_table_as_json(table)

            chunk = Chunk(
                id=f"{doc_id}_table_{i}",
                doc_id=doc_id,
                chunk_type=table.table_type.value,
                text=text,
                structured_data=structured,
                metadata={
                    "peripheral": table.peripheral,
                    "table_type": table.table_type.value,
                    "context": table.context,
                    "register_names": [r.name for r in table.registers]
                },
                page_start=0,  # Will be set by ingestion pipeline
                page_end=0
            )

            chunks.append(chunk)

        return chunks

    def _chunk_sections(self, doc_id: str, sections: List[Section]) -> List[Chunk]:
        """Create chunks for text sections."""
        chunks = []

        for section in sections:
            # If section is small enough, create single chunk
            if len(section.content) <= self.target_size:
                chunk = Chunk(
                    id=f"{doc_id}_section_{section.start_page}",
                    doc_id=doc_id,
                    chunk_type="text",
                    text=section.content,
                    structured_data=None,
                    metadata={
                        "section_title": section.title,
                        "section_level": section.level,
                    },
                    page_start=section.start_page,
                    page_end=section.end_page
                )
                chunks.append(chunk)
            else:
                # Split large sections into multiple chunks
                section_chunks = self._split_section(doc_id, section)
                chunks.extend(section_chunks)

            # Process subsections recursively
            if section.subsections:
                subsection_chunks = self._chunk_sections(doc_id, section.subsections)
                chunks.extend(subsection_chunks)

        return chunks

    def _split_section(self, doc_id: str, section: Section) -> List[Chunk]:
        """Split a large section into multiple chunks."""
        chunks = []
        content = section.content

        # Split by paragraphs (double newline)
        paragraphs = content.split('\n\n')

        current_chunk_text = ""
        chunk_num = 0

        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed target size
            if len(current_chunk_text) + len(paragraph) > self.target_size and current_chunk_text:
                # Create chunk
                chunk = Chunk(
                    id=f"{doc_id}_section_{section.start_page}_{chunk_num}",
                    doc_id=doc_id,
                    chunk_type="text",
                    text=current_chunk_text,
                    structured_data=None,
                    metadata={
                        "section_title": section.title,
                        "section_level": section.level,
                    },
                    page_start=section.start_page,
                    page_end=section.end_page
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                if self.overlap > 0:
                    # Take last N characters for overlap
                    overlap_text = current_chunk_text[-self.overlap:]
                    current_chunk_text = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk_text = paragraph

                chunk_num += 1
            else:
                # Add to current chunk
                if current_chunk_text:
                    current_chunk_text += "\n\n" + paragraph
                else:
                    current_chunk_text = paragraph

        # Add remaining text as final chunk
        if current_chunk_text:
            chunk = Chunk(
                id=f"{doc_id}_section_{section.start_page}_{chunk_num}",
                doc_id=doc_id,
                chunk_type="text",
                text=current_chunk_text,
                structured_data=None,
                metadata={
                    "section_title": section.title,
                    "section_level": section.level,
                },
                page_start=section.start_page,
                page_end=section.end_page
            )
            chunks.append(chunk)

        return chunks

    def _format_table_as_text(self, table: RegisterTable) -> str:
        """Format register table as compact text."""
        lines = []

        lines.append(f"# {table.peripheral} - {table.table_type.value.replace('_', ' ').title()}")
        lines.append("")

        if table.context:
            lines.append(f"Context: {table.context}")
            lines.append("")

        for register in table.registers:
            lines.append(f"## {register.name}")

            details = []
            if register.address:
                details.append(f"Address: {register.address}")
            if register.offset:
                details.append(f"Offset: {register.offset}")
            details.append(f"Width: {register.width}-bit")
            if register.reset_value:
                details.append(f"Reset: {register.reset_value}")
            details.append(f"Access: {register.access}")

            lines.append(" | ".join(details))

            if register.description:
                lines.append(f"Description: {register.description}")

            if register.fields:
                lines.append("\nFields:")
                for field in register.fields:
                    lines.append(f"  - {field.name} [{field.bits}]: {field.description} ({field.access})")

            lines.append("")

        return "\n".join(lines)

    def _format_table_as_json(self, table: RegisterTable) -> Dict[str, Any]:
        """Format register table as structured JSON."""
        return {
            "peripheral": table.peripheral,
            "table_type": table.table_type.value,
            "context": table.context,
            "registers": [
                {
                    "name": reg.name,
                    "address": reg.address,
                    "offset": reg.offset,
                    "width": reg.width,
                    "reset_value": reg.reset_value,
                    "access": reg.access,
                    "description": reg.description,
                    "fields": [
                        {
                            "name": field.name,
                            "bits": field.bits,
                            "bit_range": field.bit_range,
                            "access": field.access,
                            "description": field.description,
                            "reset_value": field.reset_value
                        }
                        for field in reg.fields
                    ]
                }
                for reg in table.registers
            ]
        }