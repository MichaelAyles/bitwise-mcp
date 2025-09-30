"""Test script for search functionality."""

import asyncio
from mcp_embedded_docs.config import Config
from mcp_embedded_docs.tools.search_docs import search_docs
from mcp_embedded_docs.tools.list_docs import list_docs


async def main():
    config = Config.load()

    print("=" * 80)
    print("TESTING DOCUMENT LISTING")
    print("=" * 80)
    result = await list_docs(config)
    print(result)
    print()

    print("=" * 80)
    print("TESTING SEARCH: 'FlexCAN'")
    print("=" * 80)
    result = await search_docs("FlexCAN", top_k=3, config=config)
    print(result)
    print()

    print("=" * 80)
    print("TESTING SEARCH: 'GPIO configuration'")
    print("=" * 80)
    result = await search_docs("GPIO configuration", top_k=3, config=config)
    print(result)
    print()

    print("=" * 80)
    print("TESTING SEARCH: 'clock configuration'")
    print("=" * 80)
    result = await search_docs("clock configuration", top_k=3, config=config)
    print(result)
    print()


if __name__ == "__main__":
    asyncio.run(main())