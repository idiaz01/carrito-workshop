# Catálogo mediante MCP stdio

Ejecutar `uv run carrito mcp-smoke`. El cliente inicia el proceso servidor, hace initialize, lista tools y llama search_products. El servidor solo expone el catálogo de lectura. La SDK MCP 2.x usa `MCPServer`; no se necesita Docker, puerto ni cuenta externa.

También: `uv run python examples/mcp/client.py`. `server.py` no es un chat interactivo: stdout queda reservado al protocolo JSON-RPC. La identidad y las devoluciones no se exponen aquí.

MCP transporta y descubre herramientas; no define cuándo llamar al modelo. La Skill añade instrucciones; no es un protocolo de transporte.
