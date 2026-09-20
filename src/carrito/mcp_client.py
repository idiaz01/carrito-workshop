"""Prepared real MCP client; invokes a child process, not an in-process mock."""

import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from carrito.store import ROOT


async def catalog_smoke():
    params = StdioServerParameters(
        command=sys.executable, args=[str(ROOT / "examples" / "mcp" / "server.py")], cwd=str(ROOT)
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listing = await session.list_tools()
            assert [t.name for t in listing.tools] == ["search_products"]
            result = await session.call_tool(
                "search_products", {"query": "auriculares", "max_price_eur": 80}
            )
            assert not result.is_error
            texts = [c.text for c in result.content if c.type == "text"]
            assert "P001" in json.dumps(texts)
            return {
                "transport": "stdio",
                "tools": [t.name for t in listing.tools],
                "content": texts,
                "read_only": True,
            }
