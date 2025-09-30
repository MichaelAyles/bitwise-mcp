"""PDF parsing with layout preservation."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re

import fitz  # PyMuPDF


@dataclass
class TextBlock:
    """A block of text with position information."""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_size: float
    font_name: str
    page_num: int


@dataclass
class Page:
    """A PDF page with extracted content."""
    page_num: int
    width: float
    height: float
    blocks: List[TextBlock]
    raw_text: str


@dataclass
class TOCEntry:
    """Table of contents entry."""
    level: int
    title: str
    page_num: int


@dataclass
class Section:
    """A document section."""
    title: str
    level: int
    start_page: int
    end_page: int
    content: str
    subsections: List["Section"]


class PDFParser:
    """PDF parser using PyMuPDF."""

    def __init__(self, pdf_path: Path):
        """Initialize parser with PDF path."""
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()

    def extract_text_with_layout(self) -> List[Page]:
        """Extract text preserving layout structure."""
        pages = []

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            blocks = []

            # Extract text blocks with formatting
            text_dict = page.get_text("dict")

            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                blocks.append(TextBlock(
                                    text=text,
                                    bbox=tuple(span.get("bbox", [0, 0, 0, 0])),
                                    font_size=span.get("size", 0),
                                    font_name=span.get("font", ""),
                                    page_num=page_num
                                ))

            raw_text = page.get_text()

            pages.append(Page(
                page_num=page_num,
                width=page.rect.width,
                height=page.rect.height,
                blocks=blocks,
                raw_text=raw_text
            ))

        return pages

    def extract_toc(self) -> List[TOCEntry]:
        """Extract table of contents from PDF."""
        toc_entries = []
        toc = self.doc.get_toc()

        for entry in toc:
            level, title, page_num = entry
            toc_entries.append(TOCEntry(
                level=level,
                title=title,
                page_num=page_num - 1  # Convert to 0-indexed
            ))

        return toc_entries

    def detect_sections(self, pages: List[Page], toc: List[TOCEntry]) -> List[Section]:
        """Identify section boundaries using font sizes and TOC."""
        sections = []

        # If we have TOC, use it to define sections
        if toc:
            for i, entry in enumerate(toc):
                # Determine end page
                if i + 1 < len(toc):
                    end_page = toc[i + 1].page_num - 1
                else:
                    end_page = len(pages) - 1

                # Extract content for this section
                content = ""
                for page_num in range(entry.page_num, min(end_page + 1, len(pages))):
                    if page_num < len(pages):
                        content += pages[page_num].raw_text + "\n"

                sections.append(Section(
                    title=entry.title,
                    level=entry.level,
                    start_page=entry.page_num,
                    end_page=end_page,
                    content=content,
                    subsections=[]
                ))
        else:
            # Fallback: detect sections using font size and patterns
            sections = self._detect_sections_heuristic(pages)

        # Build hierarchy
        return self._build_section_hierarchy(sections)

    def _detect_sections_heuristic(self, pages: List[Page]) -> List[Section]:
        """Detect sections using heuristics when no TOC available."""
        sections = []
        current_section = None
        section_pattern = re.compile(r'^(\d+\.)+\d*\s+[A-Z]')  # Match "45.3.2 Title"

        for page in pages:
            for block in page.blocks:
                # Look for large font sizes or section number patterns
                if block.font_size > 12 or section_pattern.match(block.text):
                    # Start new section
                    if current_section:
                        current_section.end_page = page.page_num - 1
                        sections.append(current_section)

                    # Determine level from numbering
                    level = block.text.count('.') + 1 if '.' in block.text else 1

                    current_section = Section(
                        title=block.text,
                        level=level,
                        start_page=page.page_num,
                        end_page=page.page_num,
                        content="",
                        subsections=[]
                    )

            if current_section:
                current_section.content += page.raw_text + "\n"

        # Add last section
        if current_section:
            current_section.end_page = len(pages) - 1
            sections.append(current_section)

        return sections

    def _build_section_hierarchy(self, sections: List[Section]) -> List[Section]:
        """Build hierarchical structure from flat section list."""
        if not sections:
            return []

        root_sections = []
        stack = []

        for section in sections:
            # Pop sections from stack that are not parents
            while stack and stack[-1].level >= section.level:
                stack.pop()

            if stack:
                # Add as subsection to parent
                stack[-1].subsections.append(section)
            else:
                # Add as root section
                root_sections.append(section)

            stack.append(section)

        return root_sections

    def extract_page_range(self, start_page: int, end_page: int) -> List[Page]:
        """Extract a specific range of pages."""
        all_pages = self.extract_text_with_layout()
        return all_pages[start_page:end_page + 1]