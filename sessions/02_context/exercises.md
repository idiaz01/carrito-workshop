# 2 · Guía de la sesión

Método: cambia **una** pieza → prueba en `carrito agente --debug` → mide con `carrito casos`.

| Paso | Archivo | Qué construyes | Requisitos del SPEC | Test |
|---|---|---|---|---|
| 1 | `mi_agente/system.md` | System prompt por secciones | ALC-1, DAT-1, DAT-2, RESP-1, RESP-2, RESP-3, ACL-1, ESC-1, ESC-2 | `-k paso1` |
| 2 | `mi_agente/tools.md` | Descripciones: qué hace, cuándo sí, cuándo no, unidades, resultado | DAT-1, ACL-1, ESC-1 | `-k paso2` |
| 3 | `mi_agente/contexto.py` | `format_tool_result`: solo los campos útiles, precios en euros | DAT-2, RESP-1, RESP-2, RESP-3 | `-k paso3` |
| 4 | `mi_agente/contexto.py` | `update_state` (escribir) y `build_history` (comprimir) | Caso C8 | `-k paso4` |
| Reto | Cualquiera | Más casos con menos tokens | Todos | `carrito casos` |

## Debes poder explicar

- Qué es context engineering y en qué se diferencia de escribir un prompt.
- Los tipos de contexto de un agente y dónde vive cada uno en `mi_agente/`.
- Las cuatro estrategias: escribir, seleccionar, comprimir y aislar.
- Qué va en el prompt y qué va en el código.
