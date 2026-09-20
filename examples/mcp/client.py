import asyncio
import json

from carrito.mcp_client import catalog_smoke

if __name__ == "__main__":
    print(json.dumps(asyncio.run(catalog_smoke()), ensure_ascii=False, indent=2))
