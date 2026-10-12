# Ejemplos ejecutables

Todos usan la clave y el modelo de `.env`.

| Comando | Qué muestra |
|---|---|
| `uv run carrito demo` | Una pregunta al agente con tools reales |
| `uv run carrito chat` | Conversación con historial. `/confirm` confirma el payload mostrado; `/quit` sale |
| `uv run python examples/langchain_comparison.py` | Retrieval y tools con LangChain. [Guía](langchain-comparison.md) |
| `uv run carrito mcp-smoke` | Servidor y cliente MCP por stdio, solo catálogo. [Guía](mcp/README.md) |
| `uv run carrito skill-demo` | Activación de la Skill y procedimiento añadido al contexto |
| `uv run carrito judge-demo` | Juez LLM frente a tres etiquetas humanas |
| `uv run python examples/multimodal.py` | Envía la tarjeta de producto al modelo. Una imagen no prueba stock, garantía ni batería |
| `uv run python examples/foundations.py` | Tokenización medida y toy de probabilidades. Sin API |
| `uv run python examples/learning_labs.py` | Experimentos de contexto, retrieval y contrato. Sin API. [Guía](learning-labs.md) |

El agent loop es Python. LangGraph es una lectura opcional, no una dependencia del taller.
