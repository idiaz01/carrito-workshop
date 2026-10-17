# 3 · Una posible solución

No es la única correcta. Es la que vimos en clase. Parte de la [solución de S2](../../02_context/solucion/).

| Archivo | Lab | Qué cambia |
|---|---|---|
| [rag.toml](rag.toml) | 2 | Políticas y centro de ayuda, troceado por sección, búsqueda híbrida, `top_k = 3` |
| [herramientas.py](herramientas.py) | 3 | `plazo_devolucion`, con los cinco huecos rellenos y comentados |
| [tools.md](tools.md) | 3 | `search_policies` habla del centro de ayuda; nueva sección `plazo_devolucion` |
| [system.md](system.md) | Reto | Las excepciones van primero; el plazo de un pedido se pide a `plazo_devolucion` |
| [contexto.py](contexto.py) | Reto | `search_policies` ya no se corta a dos documentos: lo decide `top_k` |

## Probarla sin tocar tu agente

```bash
CARRITO_MI_AGENTE=sessions/03_retrieval_tools/solucion uv run carrito rag --evaluar
CARRITO_MI_AGENTE=sessions/03_retrieval_tools/solucion uv run carrito casos --sesion 3
```

## Usarla como tu agente

`uv run carrito empezar s4` guarda tu agente en `mi_agente_s3/` y copia esta solución en `mi_agente/`.
