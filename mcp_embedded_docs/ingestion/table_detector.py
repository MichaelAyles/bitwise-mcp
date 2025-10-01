"""Table detection for register definitions."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Set, Tuple, Optional
import re

import pdfplumber

from .pdf_parser import Page, TextBlock


class TableType(Enum):
    """Types of tables we can detect."""
    REGISTER_MAP = "register_map"
    BITFIELD_DEFINITION = "bitfield_definition"
    MEMORY_MAP = "memory_map"
    OTHER = "other"


@dataclass
class TableRegion:
    """A detected table region."""
    page_num: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    table_type: TableType
    header_keywords: Set[str]
    table_index: int = 0  # Index of table on the page (for pdfplumber)


class TableDetector:
    """Detects register tables in PDF pages."""

    # Common header keywords for different table types
    REGISTER_MAP_HEADERS = {
        "address", "offset", "register", "name", "width", "reset", "access", "description"
    }

    BITFIELD_HEADERS = {
        "field", "bit", "bits", "range", "type", "access", "reset", "description"
    }

    MEMORY_MAP_HEADERS = {
        "peripheral", "base", "address", "size", "description"
    }

    # Keywords that indicate proximity to register tables
    TABLE_CONTEXT_KEYWORDS = {
        "memory map", "register map", "register definition", "register description",
        "bit field", "bitfield", "field description"
    }

    def __init__(self, pdf_path: str, min_columns: int = 3):
        """Initialize table detector.

        Args:
            pdf_path: Path to the PDF file
            min_columns: Minimum number of columns to consider something a table
        """
        self.pdf_path = pdf_path
        self.min_columns = min_columns
        self._pdf = None

    def __enter__(self):
        """Context manager entry."""
        self._pdf = pdfplumber.open(self.pdf_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._pdf:
            self._pdf.close()

    def detect_register_tables(self, page: Page) -> List[TableRegion]:
        """Detect register tables on a page using pdfplumber.

        Args:
            page: Page to analyze

        Returns:
            List of detected table regions
        """
        tables = []

        # Use cached PDF if available, otherwise open temporarily
        if self._pdf:
            pdf = self._pdf
            should_close = False
        else:
            pdf = pdfplumber.open(self.pdf_path)
            should_close = True

        try:
            pdf_page = pdf.pages[page.page_num]

            # Extract all tables from the page
            extracted_tables = pdf_page.extract_tables()

            for table_idx, table_data in enumerate(extracted_tables):
                if not table_data or len(table_data) < 2:
                    continue

                # Get first 2 rows to analyze headers
                header_rows = table_data[:2]
                header_text = ' '.join(
                    str(cell) for row in header_rows for cell in row if cell
                ).lower()

                # Extract keywords from header
                header_keywords = self._extract_keywords_from_text(header_text)

                # Check if this is a register-related table
                if self._is_likely_table_header(header_keywords):
                    table_type = self._classify_table_type(header_keywords)

                    # Create a table region with the table index
                    tables.append(TableRegion(
                        page_num=page.page_num,
                        bbox=(0, 0, pdf_page.width, pdf_page.height),
                        table_type=table_type,
                        header_keywords=header_keywords,
                        table_index=table_idx
                    ))
        finally:
            if should_close:
                pdf.close()

        return tables

    def _group_blocks_into_rows(self, blocks: List[TextBlock], tolerance: float = 5.0) -> List[List[TextBlock]]:
        """Group text blocks into rows based on y-coordinate."""
        if not blocks:
            return []

        # Sort blocks by y-coordinate
        sorted_blocks = sorted(blocks, key=lambda b: b.bbox[1])

        rows = []
        current_row = [sorted_blocks[0]]
        current_y = sorted_blocks[0].bbox[1]

        for block in sorted_blocks[1:]:
            if abs(block.bbox[1] - current_y) <= tolerance:
                # Same row
                current_row.append(block)
            else:
                # New row
                rows.append(sorted(current_row, key=lambda b: b.bbox[0]))  # Sort by x
                current_row = [block]
                current_y = block.bbox[1]

        if current_row:
            rows.append(sorted(current_row, key=lambda b: b.bbox[0]))

        return rows

    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract keywords from text."""
        keywords = set()

        # Normalize text
        text = text.lower().strip()
        # Remove common punctuation
        text = re.sub(r'[^\w\s]', '', text)

        # Split into words and extract meaningful keywords
        words = text.split()
        for word in words:
            if len(word) > 2:  # Skip very short words
                keywords.add(word)

        return keywords

    def _extract_header_keywords(self, row: List[TextBlock]) -> Set[str]:
        """Extract keywords from a potential header row."""
        keywords = set()

        for block in row:
            text = block.text.lower().strip()
            # Remove common punctuation
            text = re.sub(r'[^\w\s]', '', text)
            keywords.add(text)

        return keywords

    def _is_likely_table_header(self, keywords: Set[str]) -> bool:
        """Determine if keywords suggest this is a table header."""
        # Check for register map headers
        register_match = len(keywords & self.REGISTER_MAP_HEADERS)
        if register_match >= 3:
            return True

        # Check for bitfield headers
        bitfield_match = len(keywords & self.BITFIELD_HEADERS)
        if bitfield_match >= 3:
            return True

        # Check for memory map headers
        memory_match = len(keywords & self.MEMORY_MAP_HEADERS)
        if memory_match >= 2:
            return True

        return False

    def _extract_table_region(self, page: Page, rows: List[List[TextBlock]], header_row_idx: int) -> Optional[TableRegion]:
        """Extract the bounding box of a table starting from header row."""
        if header_row_idx >= len(rows):
            return None

        header_row = rows[header_row_idx]
        header_keywords = self._extract_header_keywords(header_row)

        # Determine table type
        table_type = self._classify_table_type(header_keywords)

        # Find table boundaries
        x0 = min(block.bbox[0] for block in header_row)
        x1 = max(block.bbox[2] for block in header_row)
        y0 = min(block.bbox[1] for block in header_row)

        # Find where table ends (look for rows with similar column structure)
        num_cols = len(header_row)
        y1 = y0

        for i in range(header_row_idx + 1, len(rows)):
            row = rows[i]

            # Check if row has similar structure
            if len(row) < max(2, num_cols - 2):  # Allow some variation
                break

            # Check if row is within similar x boundaries
            row_x0 = min(block.bbox[0] for block in row)
            row_x1 = max(block.bbox[2] for block in row)

            if abs(row_x0 - x0) > 50 or abs(row_x1 - x1) > 50:
                break

            # Update bottom boundary
            y1 = max(block.bbox[3] for block in row)

        # Only return if we found at least a few rows
        if y1 - y0 < 20:  # Minimum table height
            return None

        return TableRegion(
            page_num=page.page_num,
            bbox=(x0, y0, x1, y1),
            table_type=table_type,
            header_keywords=header_keywords
        )

    def _classify_table_type(self, keywords: Set[str]) -> TableType:
        """Classify table type based on header keywords."""
        register_score = len(keywords & self.REGISTER_MAP_HEADERS)
        bitfield_score = len(keywords & self.BITFIELD_HEADERS)
        memory_score = len(keywords & self.MEMORY_MAP_HEADERS)

        max_score = max(register_score, bitfield_score, memory_score)

        if max_score == 0:
            return TableType.OTHER

        if register_score == max_score:
            return TableType.REGISTER_MAP
        elif bitfield_score == max_score:
            return TableType.BITFIELD_DEFINITION
        else:
            return TableType.MEMORY_MAP

    def detect_table_context(self, page: Page, table_region: TableRegion, context_lines: int = 5) -> str:
        """Extract context text around a table (useful for understanding what peripheral/register it describes)."""
        context_blocks = []

        # Get text above the table
        for block in page.blocks:
            # Check if block is above the table
            if block.bbox[3] < table_region.bbox[1]:
                # Check if it's close enough
                distance = table_region.bbox[1] - block.bbox[3]
                if distance < 100:  # Within 100 units above
                    context_blocks.append(block)

        # Sort by position (top to bottom)
        context_blocks.sort(key=lambda b: b.bbox[1])

        # Take last N blocks (closest to table)
        context_blocks = context_blocks[-context_lines:]

        return " ".join(block.text for block in context_blocks)