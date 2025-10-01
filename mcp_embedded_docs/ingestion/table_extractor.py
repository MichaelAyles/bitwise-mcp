"""Extract structured data from detected tables."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import re

import pdfplumber

from .table_detector import TableRegion, TableType


@dataclass
class BitField:
    """A bit field within a register."""
    name: str
    bits: str  # e.g., "31:24" or "15"
    bit_range: Tuple[int, int]  # (msb, lsb)
    access: str  # RW, RO, WO, etc.
    description: str
    reset_value: Optional[str] = None


@dataclass
class Register:
    """A register definition."""
    name: str
    offset: Optional[str] = None
    address: Optional[str] = None
    width: int = 32
    reset_value: Optional[str] = None
    access: str = "RW"
    description: str = ""
    fields: List[BitField] = field(default_factory=list)


@dataclass
class RegisterTable:
    """A table of register definitions."""
    peripheral: str
    table_type: TableType
    registers: List[Register]
    context: str = ""


class TableExtractor:
    """Extract structured register data from PDF tables."""

    def __init__(self, pdf_path: str):
        """Initialize extractor with PDF path."""
        self.pdf_path = pdf_path

    def extract_register_table(self, table_region: TableRegion, context: str = "") -> Optional[RegisterTable]:
        """Extract structured data from a table region.

        Args:
            table_region: Detected table region
            context: Context text around the table

        Returns:
            Structured register table or None if extraction fails
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[table_region.page_num]

            # Extract all tables and get the specific one we want
            tables = page.extract_tables()

            if not tables or table_region.table_index >= len(tables):
                return None

            # Get the specific table by index
            table_data = tables[table_region.table_index]

            if not table_data or len(table_data) < 2:  # Need header + at least one row
                return None

            # Parse based on table type
            if table_region.table_type == TableType.REGISTER_MAP:
                return self._parse_register_map(table_data, context)
            elif table_region.table_type == TableType.BITFIELD_DEFINITION:
                return self._parse_bitfield_table(table_data, context)
            elif table_region.table_type == TableType.MEMORY_MAP:
                return self._parse_memory_map(table_data, context)

        return None

    def _parse_register_map(self, table_data: List[List[str]], context: str) -> RegisterTable:
        """Parse a register map table."""
        # Find the actual header row (might not be row 0 if there's a title row)
        header_row_idx = 0
        header = None

        for i in range(min(3, len(table_data))):  # Check first 3 rows for header
            test_header = [self._normalize_header(h) for h in table_data[i]]

            # Check if this looks like a header (has keywords like name, offset, etc.)
            if any(keyword in ' '.join(test_header) for keyword in ['name', 'register', 'offset', 'address', 'bit']):
                header_row_idx = i
                header = test_header
                break

        if not header:
            # Fallback to first row
            header = [self._normalize_header(h) for h in table_data[0]]

        # Find column indices
        name_col = self._find_column(header, ["name", "register"])
        offset_col = self._find_column(header, ["offset"])
        address_col = self._find_column(header, ["address", "addr"])
        width_col = self._find_column(header, ["width", "size"])
        reset_col = self._find_column(header, ["reset", "default"])
        access_col = self._find_column(header, ["access", "type", "r/w"])
        desc_col = self._find_column(header, ["description", "desc"])

        registers = []

        # Start from row after header
        for row in table_data[header_row_idx + 1:]:
            if not row or not any(row):  # Skip empty rows
                continue

            # Clean up cells
            row = [self._clean_cell(cell) for cell in row]

            name = row[name_col] if name_col is not None and name_col < len(row) else ""
            if not name:
                continue

            register = Register(
                name=name,
                offset=row[offset_col] if offset_col is not None and offset_col < len(row) else None,
                address=row[address_col] if address_col is not None and address_col < len(row) else None,
                width=self._parse_width(row[width_col] if width_col is not None and width_col < len(row) else "32"),
                reset_value=row[reset_col] if reset_col is not None and reset_col < len(row) else None,
                access=row[access_col] if access_col is not None and access_col < len(row) else "RW",
                description=row[desc_col] if desc_col is not None and desc_col < len(row) else "",
            )

            registers.append(register)

        # Extract peripheral name from context
        peripheral = self._extract_peripheral_name(context)

        return RegisterTable(
            peripheral=peripheral,
            table_type=TableType.REGISTER_MAP,
            registers=registers,
            context=context
        )

    def _parse_bitfield_table(self, table_data: List[List[str]], context: str) -> RegisterTable:
        """Parse a bitfield definition table."""
        header = [self._normalize_header(h) for h in table_data[0]]

        # Find column indices
        field_col = self._find_column(header, ["field", "name"])
        bits_col = self._find_column(header, ["bit", "bits", "range"])
        access_col = self._find_column(header, ["access", "type", "r/w"])
        reset_col = self._find_column(header, ["reset", "default"])
        desc_col = self._find_column(header, ["description", "desc"])

        # Create a single register with multiple fields
        fields = []

        for row in table_data[1:]:
            if not row or not any(row):
                continue

            row = [self._clean_cell(cell) for cell in row]

            field_name = row[field_col] if field_col is not None else ""
            if not field_name:
                continue

            bits_str = row[bits_col] if bits_col is not None and bits_col < len(row) else ""
            bit_range = self._parse_bit_notation(bits_str)

            if bit_range is None:
                continue

            field = BitField(
                name=field_name,
                bits=bits_str,
                bit_range=bit_range,
                access=row[access_col] if access_col is not None and access_col < len(row) else "RW",
                description=row[desc_col] if desc_col is not None and desc_col < len(row) else "",
                reset_value=row[reset_col] if reset_col is not None and reset_col < len(row) else None
            )

            fields.append(field)

        # Extract register name from context
        register_name = self._extract_register_name(context)
        peripheral = self._extract_peripheral_name(context)

        register = Register(
            name=register_name,
            fields=fields,
            description=context
        )

        return RegisterTable(
            peripheral=peripheral,
            table_type=TableType.BITFIELD_DEFINITION,
            registers=[register],
            context=context
        )

    def _parse_memory_map(self, table_data: List[List[str]], context: str) -> RegisterTable:
        """Parse a memory map table."""
        # Similar to register map but for peripherals
        return self._parse_register_map(table_data, context)

    def _normalize_header(self, header: Optional[str]) -> str:
        """Normalize header text."""
        if not header:
            return ""
        return header.lower().strip()

    def _clean_cell(self, cell: Optional[str]) -> str:
        """Clean cell text."""
        if not cell:
            return ""
        return " ".join(cell.split())  # Normalize whitespace

    def _find_column(self, header: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by matching keywords."""
        for i, h in enumerate(header):
            for keyword in keywords:
                if keyword in h:
                    return i
        return None

    def _parse_width(self, width_str: str) -> int:
        """Parse width string to integer."""
        if not width_str:
            return 32

        # Extract number from string like "32-bit" or "32"
        match = re.search(r'(\d+)', width_str)
        if match:
            return int(match.group(1))

        return 32

    def _parse_bit_notation(self, bit_string: str) -> Optional[Tuple[int, int]]:
        """Parse bit notation like '[31:24]', '[23]', '31:24' into (msb, lsb) tuple."""
        if not bit_string:
            return None

        # Remove brackets and whitespace
        cleaned = re.sub(r'[\[\]\s]', '', bit_string)

        # Try range notation (31:24)
        match = re.match(r'(\d+):(\d+)', cleaned)
        if match:
            msb = int(match.group(1))
            lsb = int(match.group(2))
            return (msb, lsb)

        # Try single bit notation (23)
        match = re.match(r'(\d+)$', cleaned)
        if match:
            bit = int(match.group(1))
            return (bit, bit)

        return None

    def _extract_peripheral_name(self, context: str) -> str:
        """Extract peripheral name from context."""
        if not context:
            return "Unknown"

        # Look for common patterns like "FlexCAN", "UART0", etc.
        # Typically capitalized words or words with numbers
        words = context.split()
        for word in words:
            # Look for mixed case or words with numbers
            if re.match(r'^[A-Z][A-Za-z0-9_]*\d*$', word):
                return word

        return "Unknown"

    def _extract_register_name(self, context: str) -> str:
        """Extract register name from context."""
        if not context:
            return "Unknown"

        # Look for register names (usually uppercase abbreviations)
        words = context.split()
        for word in words:
            # Look for uppercase words (3-10 chars)
            if re.match(r'^[A-Z_]{2,10}$', word):
                return word

        return "Unknown"