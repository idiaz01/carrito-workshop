"""Read-only catalog over real MCP stdio; no identity or return endpoint."""

from mcp.server.mcpserver import MCPServer

from carrito.store import create_store
from carrito.tools import StoreTools

server = MCPServer("carrito-catalog", log_level="WARNING")


@server.tool()
def search_products(query: str, max_price_eur: float | None = None) -> list[dict]:
    """Search original catalog; prices are integer cents."""
    db = create_store()
    try:
        return StoreTools(db).search_products(query, max_price_eur)
    finally:
        db.close()


if __name__ == "__main__":
    server.run(transport="stdio")
