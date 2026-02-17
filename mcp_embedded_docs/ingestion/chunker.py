"""Semantic chunking for documents."""

import hashlib
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .pdf_parser import Section
from .table_extractor import RegisterTable

# Sentence boundary pattern: period/question/exclamation followed by space or newline,
# or a double newline (paragraph break)
_SENTENCE_BOUNDARY_RE = re.compile(r'(?<=[.!?])\s+|\n\n+')


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

    def __init__(self, target_size: int = 2500, overlap: int = 200, preserve_tables: bool = True):
        """Initialize chunker.

        Args:
            target_size: Target chunk size in characters
            overlap: Overlap between adjacent text chunks (in characters, used as budget for trailing sentences)
            preserve_tables: Keep register tables intact (never split)
        """
        self.target_size = target_size
        self.overlap = overlap
        self.preserve_tables = preserve_tables

    def chunk_document(
        self,
        doc_id: str,
        sections: List[Section],
        tables: List[RegisterTable],
        doc_title: str = "",
        table_pages: Optional[Dict[int, int]] = None,
    ) -> List[Chunk]:
        """Create chunks from document sections and tables.

        Args:
            doc_id: Document identifier
            sections: Document sections
            tables: Extracted register tables
            doc_title: Document title for contextual prefixes
            table_pages: Mapping of table index -> page_num from detection phase

        Returns:
            List of chunks
        """
        chunks = []

        # First, create chunks for register tables (these are always kept intact)
        table_chunks = self._chunk_tables(doc_id, tables, doc_title, table_pages or {})
        chunks.extend(table_chunks)

        # Then, create chunks for text sections (starting with no ancestors)
        text_chunks = self._chunk_sections(doc_id, sections, doc_title, ancestors=[])
        chunks.extend(text_chunks)

        return chunks

    # ------------------------------------------------------------------
    # Contextual prefix
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context_prefix(doc_title: str, section_hierarchy: List[str]) -> str:
        """Build a contextual prefix like [Doc > Section > Subsection].

        Args:
            doc_title: Overall document title
            section_hierarchy: List of ancestor section titles, outermost first

        Returns:
            Prefix string (empty if no context available)
        """
        parts = []
        if doc_title:
            parts.append(doc_title)
        parts.extend(h for h in section_hierarchy if h)
        if not parts:
            return ""
        return "[" + " > ".join(parts) + "]\n"

    # ------------------------------------------------------------------
    # Table chunking
    # ------------------------------------------------------------------

    def _chunk_tables(
        self,
        doc_id: str,
        tables: List[RegisterTable],
        doc_title: str,
        table_pages: Dict[int, int],
    ) -> List[Chunk]:
        """Create chunks for register tables."""
        chunks = []

        for i, table in enumerate(tables):
            # Build hierarchy from peripheral + context
            hierarchy: List[str] = []
            if table.peripheral:
                hierarchy.append(table.peripheral)
            if table.context:
                hierarchy.append(table.context)

            prefix = self._build_context_prefix(doc_title, hierarchy)

            # Convert table to both text and structured format
            text = prefix + self._format_table_as_text(table)
            structured = self._format_table_as_json(table)

            # Content-based chunk ID
            chunk_hash = hashlib.md5(text.encode()).hexdigest()[:12]
            chunk_id = f"{doc_id}_{chunk_hash}"

            page_num = table_pages.get(i, 0)

            chunk = Chunk(
                id=chunk_id,
                doc_id=doc_id,
                chunk_type=table.table_type.value,
                text=text,
                structured_data=structured,
                metadata={
                    "peripheral": table.peripheral,
                    "table_type": table.table_type.value,
                    "context": table.context,
                    "register_names": [r.name for r in table.registers],
                },
                page_start=page_num,
                page_end=page_num,
            )

            chunks.append(chunk)

        return chunks

    # ------------------------------------------------------------------
    # Section chunking
    # ------------------------------------------------------------------

    def _chunk_sections(
        self,
        doc_id: str,
        sections: List[Section],
        doc_title: str,
        ancestors: List[str],
    ) -> List[Chunk]:
        """Create chunks for text sections.

        Only leaf sections (those with no subsections) get their content
        chunked, avoiding duplicate text between parent and child sections.
        """
        chunks = []

        for section in sections:
            current_hierarchy = ancestors + [section.title]

            if section.subsections:
                # Non-leaf: recurse into subsections only — skip own content
                # to avoid duplicating text already covered by children
                sub_chunks = self._chunk_sections(
                    doc_id, section.subsections, doc_title, current_hierarchy
                )
                chunks.extend(sub_chunks)
            else:
                # Leaf section: chunk its content
                prefix = self._build_context_prefix(doc_title, current_hierarchy)
                content = section.content.strip()
                if not content:
                    continue

                if len(prefix) + len(content) <= self.target_size:
                    # Fits in a single chunk
                    chunk_text = prefix + content
                    chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:12]

                    chunk = Chunk(
                        id=f"{doc_id}_{chunk_hash}",
                        doc_id=doc_id,
                        chunk_type="text",
                        text=chunk_text,
                        structured_data=None,
                        metadata={
                            "section_title": section.title,
                            "section_level": section.level,
                        },
                        page_start=section.start_page,
                        page_end=section.end_page,
                    )
                    chunks.append(chunk)
                else:
                    # Large section — split with sentence-aware boundaries
                    split_chunks = self._split_section(
                        doc_id, section, prefix
                    )
                    chunks.extend(split_chunks)

        return chunks

    # ------------------------------------------------------------------
    # Sentence-aware splitting
    # ------------------------------------------------------------------

    @staticmethod
    def _find_sentence_boundaries(text: str) -> List[int]:
        """Return a sorted list of positions right *after* sentence boundaries.

        Each value is the index of the first character of the next sentence.
        """
        boundaries = []
        for m in _SENTENCE_BOUNDARY_RE.finditer(text):
            boundaries.append(m.end())
        return boundaries

    def _split_section(self, doc_id: str, section: Section, prefix: str) -> List[Chunk]:
        """Split a large section into multiple chunks using sentence boundaries."""
        chunks: List[Chunk] = []
        content = section.content.strip()
        boundaries = self._find_sentence_boundaries(content)

        # If no sentence boundaries found, fall back to splitting on double-newlines
        if not boundaries:
            boundaries = [m.end() for m in re.finditer(r'\n\n+', content)]

        start = 0
        budget = self.target_size - len(prefix)  # room for actual text per chunk

        while start < len(content):
            end = start + budget

            if end >= len(content):
                # Remaining text fits
                end = len(content)
            else:
                # Find the last sentence boundary before `end`
                best = None
                for b in boundaries:
                    if b <= start:
                        continue
                    if b <= end:
                        best = b
                    else:
                        break
                if best is not None:
                    end = best
                # else: no boundary found — take the full budget (hard cut at word boundary)
                else:
                    # Try to avoid cutting mid-word: back up to last space
                    space_pos = content.rfind(' ', start, end)
                    if space_pos > start:
                        end = space_pos + 1

            chunk_text = prefix + content[start:end].strip()
            if chunk_text.strip():
                chunk_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:12]
                chunks.append(Chunk(
                    id=f"{doc_id}_{chunk_hash}",
                    doc_id=doc_id,
                    chunk_type="text",
                    text=chunk_text,
                    structured_data=None,
                    metadata={
                        "section_title": section.title,
                        "section_level": section.level,
                    },
                    page_start=section.start_page,
                    page_end=section.end_page,
                ))

            # Compute overlap: grab the last 1-2 sentences from the chunk we just created
            overlap_start = self._compute_overlap_start(content, start, end)
            start = overlap_start if overlap_start < end else end

        return chunks

    def _compute_overlap_start(self, content: str, chunk_start: int, chunk_end: int) -> int:
        """Find where the next chunk should start so that it overlaps the last 1-2 sentences."""
        # Look for sentence boundaries in the region [chunk_end - overlap .. chunk_end]
        region_start = max(chunk_start, chunk_end - self.overlap)
        boundaries_in_region = []
        for m in _SENTENCE_BOUNDARY_RE.finditer(content, region_start, chunk_end):
            boundaries_in_region.append(m.end())

        if boundaries_in_region:
            # Start the next chunk from the beginning of the last sentence in the overlap zone
            # Use the second-to-last boundary if available (gives ~1-2 sentences of overlap)
            if len(boundaries_in_region) >= 2:
                return boundaries_in_region[-2]
            return boundaries_in_region[-1]

        # No sentence boundaries in overlap region — just advance to chunk_end (no overlap)
        return chunk_end

    # ------------------------------------------------------------------
    # Table formatting (unchanged)
    # ------------------------------------------------------------------

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
