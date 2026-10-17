# 5 · Una posible solución

No es la única correcta. Es la que vimos en clase. Parte de la [solución de S4](../../04_agents_state/solucion/).

| Archivo | Lab | Qué cambia |
|---|---|---|
| [skills/regalos.md](skills/regalos.md) | 1 | Una skill propia: regalos con presupuesto, envoltorio y ticket regalo |
| [casos.jsonl](casos.jsonl) | 1 | M2 y M3, los casos de la skill de regalos |
| [agente.toml](agente.toml) | 1 | La ruta de búsqueda ya no tiene «regalo»: atrapaba las preguntas de la skill |
| [evaluadores.py](evaluadores.py) | 3 | `cita_fuentes` y `breve`, con los huecos rellenos |
| [juez.md](juez.md) | 4 | Una rúbrica con los criterios del SPEC |
| [system.md](system.md) | Reto | «El pedido más reciente es el de fecha de entrega más tardía» (C26) |

## Probarla sin tocar tu agente

```bash
CARRITO_MI_AGENTE=sessions/05_capstone/solucion uv run carrito evals juez
CARRITO_MI_AGENTE=sessions/05_capstone/solucion uv run carrito evals experimento --nombre solucion
```
