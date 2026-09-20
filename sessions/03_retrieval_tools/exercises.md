# 3 · Building with LangChain, RAG, and Tools
La misma aplicación recupera evidencia y ejecuta capacidades autorizadas.
La búsqueda local es léxica; no se presenta como embeddings ni semantic retrieval.

Predice el resultado antes de ejecutar y anota tus observaciones.

## Documentos → unidades recuperables → resultados
Las políticas ya son unidades cortas: dividirlas arbitrariamente puede separar regla y excepción. Inspecciona metadata y decide qué frontera conservarías en un manual más largo.

## Calidad de retrieval
Predice fallos para sinónimos y excepciones. Compara top-k=1/2 con y sin expansión: cuatro condiciones, no dos cambios confundidos. Completa una configuración y conserva el detalle por consulta; mejorar recall puede empeorar precision. La expansión explícita no es comprensión semántica.

## Tool calling nativo
Antes de ejecutar, identifica call_id, nombre, arguments y resultado. Configura solo lectura; una petición de escritura debe rechazarse incluso si el modelo la propone. El mismo `run_profile` continúa en S4 y S5.

## MCP: integración ejecutable
Host → cliente → proceso servidor. Inspecciona `examples/mcp/server.py`: el server expone catálogo, no permisos para devoluciones. Compara el mismo resultado local y remoto; usa el resultado MCP como evidencia para el siguiente request.

## LangChain: qué abstrae
Compara request/response nativos con `StructuredTool`, `AIMessage.tool_calls` y `ToolMessage`. La función y autorización siguen en Python. El ejemplo tiene dos llamadas y una capacidad de lectura; no es otro agente.

## Salida de sesión
Decide para cada necesidad: retrieval, tool, long context o ninguna. Documenta una consulta fallida, una cita no sustentada y una denegación correcta. S4 decide cuándo delegar la secuencia al modelo.

## Comprobación final

Reinicia el kernel y ejecuta todo. Revisa cada mensaje PENDIENTE sin alterar los checks para que pasen. Anota qué comportamiento has comprobado y qué afirmaciones requieren revisión humana.
