# 2 · Una posible solución

No es la única correcta. Es la que vimos en clase.

| Archivo | Paso | Qué hace |
|---|---|---|
| [system.md](system.md) | 1 | System prompt por secciones, con los IDs del SPEC |
| [tools.md](tools.md) | 2 | Descripciones: qué hace, cuándo sí, cuándo no, unidades, resultado |
| [contexto.py](contexto.py) | 3 y 4 | `format_tool_result`, `update_state` y `build_history`, con comentarios línea a línea |
| [reto/](reto/) | Reto | Cambian `system.md` y `tools.md` para C9–C12. `contexto.py` es igual |

## Probarla sin tocar tu agente

```bash
CARRITO_MI_AGENTE=sessions/02_context/solucion uv run carrito casos
CARRITO_MI_AGENTE=sessions/02_context/solucion/reto uv run carrito casos --reto
```

La variable solo vale para ese comando. Tu `mi_agente/` no cambia.

## Usarla como tu agente

Primero guarda una copia del tuyo. Después copia la solución:

```bash
cp -r mi_agente mi_agente_mio
cp sessions/02_context/solucion/system.md sessions/02_context/solucion/tools.md sessions/02_context/solucion/contexto.py mi_agente/
uv run pytest tests/test_mi_agente.py --runxfail -q
```

Los seis tests deben pasar. El modelo no responde igual cada vez: un caso puede fallar alguna vez.
