"""Find register tool."""

from typing import Optional
from ..retrieval.hybrid_search import HybridSearch
from ..retrieval.formatter import ResultFormatter
from ..config import Config


async def find_register(
    name: str,
    peripheral: Optional[str] = None,
    config: Optional[Config] = None
) -> str:
    """Find a specific register by name.

    Args:
        name: Register name to find
        peripheral: Optional peripheral name to filter results
        config: Configuration object

    Returns:
        Formatted register definition as markdown
    """
    if config is None:
        config = Config.load()

    search = HybridSearch(config)

    try:
        result = search.find_register(name, peripheral)

        if not result:
            return f"Register '{name}' not found."

        return ResultFormatter.format_register(result)
    finally:
        search.close()