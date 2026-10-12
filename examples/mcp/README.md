# Catálogo mediante MCP stdio

Ejecuta `uv run carrito mcp-smoke`. El cliente inicia el proceso servidor, hace `initialize`, lista las tools y llama a `search_products`.
El servidor solo expone el catálogo, en modo lectura. No necesita Docker, puertos ni cuentas externas.

También puedes ejecutar `uv run python examples/mcp/client.py`.
`server.py` no es un chat: stdout está reservado para el protocolo JSON-RPC.

MCP transporta y descubre tools. No decide cuándo llamar al modelo.
Una Skill añade instrucciones. No es un protocolo de transporte.
