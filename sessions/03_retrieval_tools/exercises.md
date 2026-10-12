# 3 · Guía de la sesión

Qué observar en cada sección del [notebook](starter.ipynb). Método: predice → ejecuta → compara → explica.

| Sección | Qué observar |
|---|---|
| Documentos → unidades recuperables | Una división sin criterio puede separar una regla de su excepción |
| Calidad de retrieval | Cuatro condiciones: top-k 1 o 2, con o sin expansión. Más recall puede dar menos precision |
| Tool calling nativo | En la traza: `call_id`, nombre, `arguments` y resultado. El host rechaza escrituras fuera del perfil |
| MCP: integración ejecutable | Host → cliente → servidor. El server solo expone el catálogo |
| LangChain: qué abstrae | El código de negocio no cambia. Cambian mensajes, schemas e invocación |

## Debes poder explicar

- Cuándo usar retrieval, una tool, contexto largo o nada.
- Una consulta fallida, una cita no sustentada y una denegación correcta.

Los checks `OK` comprueban el código. No miden la calidad del modelo.
