# 4 · Una posible solución

No es la única correcta. Es la que vimos en clase. Parte de la [solución de S3](../../03_retrieval_tools/solucion/).

| Archivo | Lab | Qué cambia |
|---|---|---|
| [agente.toml](agente.toml) | 1, 2 y 4 | Límites (8 pasos, 10 tools), una ruta fija, una ruta de búsqueda y el subagente apagado |
| [salida.py](salida.py) | 3 | `revisar()` con los tres huecos rellenos |
| [subagente.md](subagente.md) | 4 | El prompt del subagente de documentos |
| [tools.md](tools.md) | Reto | Nueva sección `mis_pedidos` |
| [system.md](system.md) | Reto | Usar `mis_pedidos` y pedir los plazos a la vez |

Los demás archivos son los de S3.

## Probarla sin tocar tu agente

```bash
CARRITO_MI_AGENTE=sessions/04_agents_state/solucion uv run carrito casos --sesion 4
```

## Usarla como tu agente

`uv run carrito empezar s5` guarda tu agente en `mi_agente_s4/` y copia esta solución en `mi_agente/`.
