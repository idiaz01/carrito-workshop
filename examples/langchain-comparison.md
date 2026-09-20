# S3 · La misma aplicación con LangChain

Esta comparación de APIs mantiene el catálogo y las políticas de Carrito; añade una capa de mensajes y tools para comparar conceptos ya vistos.

Preparación opcional, antes de la sesión:

```bash
uv sync --locked --extra langchain
uv run --extra langchain python examples/langchain_comparison.py --mode fixture
```

La demo usa `StructuredTool`, `AIMessage` y `ToolMessage` reales. Recupera políticas con `StoreTools.search_policies`, las incorpora como evidencia y ejecuta `search_products` sobre la misma SQLite. Solo la decisión y la respuesta del modelo están preescritas en modo fixture. El resultado enseña mensajes, llamadas, IDs, resultado de catálogo, fuentes y usage. `null` en usage significa que la fixture no midió tokens.

| Concepto | API nativa de S1–S4 | Comparación LangChain |
|---|---|---|
| Petición al modelo | `client.responses.create` | `ChatOpenAI.invoke` |
| Registrar schema | `tools=[...]` | `bind_tools([catalog])` |
| Petición de función | `function_call` | `AIMessage.tool_calls` |
| Ejecutar Python | `StoreTools.dispatch` | `StructuredTool.invoke` sobre la misma función |
| Devolver resultado | `function_call_output` y `call_id` | `ToolMessage` y `tool_call_id` |
| Recuperación | `search_policies` local | La misma recuperación antes de llamar al modelo |

`bind_tools` declara capacidades; no ejecuta las funciones. Python sigue validando argumentos. La demo solo permite leer el catálogo y hace como máximo dos llamadas al modelo; no es un segundo agent loop. No requiere LangGraph, vector store ni una cuenta de LangSmith. El paquete de integración instala sus dependencias habituales, pero no activamos tracing externo.

Para observar una ejecución real con un modelo de tu cuenta:

```bash
uv run --extra langchain python examples/langchain_comparison.py --mode live
```

Este comando consume API y necesita `OPENAI_API_KEY` y `OPENAI_MODEL`. La demo establece `use_responses_api=True`; no confunde Chat Completions con Responses. No se ha realizado una llamada de pago durante la verificación del repositorio.

**Pregunta de comparación:** ¿qué código de negocio ha cambiado? Ninguno. Cambian la representación de mensajes, el registro del schema y la interfaz de invocación. La respuesta sigue necesitando comprobación contra hechos y fuentes.

**Verificación de versión, 20 septiembre 2026:** `langchain-openai==1.6.2`, que resuelve `langchain-core==1.6.3` en el lock. Fuente: [distribución oficial](https://pypi.org/project/langchain-openai/), [integración ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai) y [tool calling](https://docs.langchain.com/oss/python/langchain/models#tool-calling). Las pruebas usan inyección de un modelo preescrito y ejecutan las tools reales; no estiman calidad del LLM.
