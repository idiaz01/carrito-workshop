# S3 · La misma aplicación con LangChain

La comparación usa el mismo catálogo y las mismas políticas de Carrito. Solo cambia la capa de mensajes y tools.

```bash
uv run python examples/langchain_comparison.py
```

La demo usa `StructuredTool`, `AIMessage` y `ToolMessage`. Recupera políticas con `StoreTools.search_policies` y ejecuta `search_products` sobre la misma SQLite.
Hace como máximo dos llamadas al modelo y solo lee. No es un segundo agent loop.

| Concepto | API nativa (S1–S4) | LangChain |
|---|---|---|
| Petición al modelo | `client.responses.create` | `ChatOpenAI.invoke` |
| Registrar schema | `tools=[...]` | `bind_tools([catalog])` |
| Petición de función | `function_call` | `AIMessage.tool_calls` |
| Ejecutar Python | `StoreTools.dispatch` | `StructuredTool.invoke` sobre la misma función |
| Devolver resultado | `function_call_output` y `call_id` | `ToolMessage` y `tool_call_id` |
| Recuperación | `search_policies` local | La misma recuperación antes de llamar al modelo |

`bind_tools` declara capacidades. No ejecuta funciones. Python sigue validando los argumentos.
La demo usa `use_responses_api=True`. No necesita LangGraph, vector store ni cuenta de LangSmith.

**Pregunta:** ¿qué código de negocio cambia? Ninguno. Cambian la representación de mensajes, el registro del schema y la interfaz de invocación.

Versión bloqueada: `langchain-openai==1.6.2` (con `langchain-core==1.6.3`). Fuentes: [PyPI](https://pypi.org/project/langchain-openai/), [ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai) y [tool calling](https://docs.langchain.com/oss/python/langchain/models#tool-calling).
