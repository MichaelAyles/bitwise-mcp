"""Format search results compactly."""

from typing import List
from . import SearchResult


class ResultFormatter:
    """Format search results for minimal token usage."""

    @staticmethod
    def format_results(results: List[SearchResult], max_results: int = 5) -> str:
        """Format search results as compact markdown.

        Args:
            results: List of search results
            max_results: Maximum number of results to format

        Returns:
            Formatted markdown string
        """
        if not results:
            return "No results found."

        lines = []

        for i, result in enumerate(results[:max_results], 1):
            lines.append(f"## Result {i}")
            lines.append("")

            # Show structured data if available (register definitions)
            if result.structured_data:
                formatted = ResultFormatter._format_structured_data(result.structured_data)
                lines.append(formatted)
            else:
                # Show text excerpt
                excerpt = ResultFormatter._create_excerpt(result.text, max_length=500)
                lines.append(excerpt)

            # Add metadata
            lines.append("")
            lines.append(f"**Source:** Pages {result.page_start}-{result.page_end}")

            if result.metadata.get("section_title"):
                lines.append(f"**Section:** {result.metadata['section_title']}")

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_structured_data(data: dict) -> str:
        """Format structured register data compactly."""
        lines = []

        peripheral = data.get("peripheral", "Unknown")
        table_type = data.get("table_type", "").replace("_", " ").title()

        lines.append(f"**{peripheral}** - {table_type}")
        lines.append("")

        for register in data.get("registers", []):
            # Register header
            reg_name = register["name"]
            address = register.get("address", "")
            offset = register.get("offset", "")

            header_parts = [f"### {reg_name}"]
            if address:
                header_parts.append(f"({address})")
            elif offset:
                header_parts.append(f"(Offset: {offset})")

            lines.append(" ".join(header_parts))

            # Register details
            details = []
            details.append(f"**Width:** {register.get('width', 32)}-bit")

            if register.get("reset_value"):
                details.append(f"**Reset:** {register['reset_value']}")

            details.append(f"**Access:** {register.get('access', 'RW')}")

            lines.append(" | ".join(details))

            if register.get("description"):
                lines.append(f"\n{register['description']}")

            # Bit fields
            if register.get("fields"):
                lines.append("\n**Fields:**")
                for field in register["fields"]:
                    field_line = f"- **{field['name']}** [{field['bits']}]: {field['description']} ({field['access']})"
                    lines.append(field_line)

            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _create_excerpt(text: str, max_length: int = 500) -> str:
        """Create an excerpt from text."""
        if len(text) <= max_length:
            return text

        # Try to cut at a sentence boundary
        excerpt = text[:max_length]
        last_period = excerpt.rfind('.')
        last_newline = excerpt.rfind('\n')

        cut_point = max(last_period, last_newline)
        if cut_point > max_length * 0.7:  # Only use if not too short
            excerpt = excerpt[:cut_point + 1]

        return excerpt + "..."

    @staticmethod
    def format_register(result: SearchResult) -> str:
        """Format a single register result.

        Args:
            result: Search result containing register data

        Returns:
            Formatted markdown string
        """
        if not result.structured_data:
            return result.text

        return ResultFormatter._format_structured_data(result.structured_data)