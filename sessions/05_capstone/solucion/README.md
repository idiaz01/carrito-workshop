# 5 · Una posible solución

No es la única correcta. Es la que vimos en clase. Parte de la [solución de S4](../../04_agents_state/solucion/).

| Archivo | Lab | Qué cambia |
|---|---|---|
| [skills/regalos.md](skills/regalos.md) | 1 | Una skill propia: regalos con presupuesto, envoltorio y ticket regalo |
| [casos.jsonl](casos.jsonl) | 1 | M2 y M3, los casos de la skill de regalos |
| [agente.toml](agente.toml) | 1 y C36 | La ruta de búsqueda ya no tiene «regalo» (atrapaba la skill) y no atrapa «¿cuánto costaría…?» |
| [system.md](system.md) | C33 | Sin presupuesto: busca; si encajan varios productos, pregunta el presupuesto |
| [tools.md](tools.md) | C34, C35 | `search_products` busca por nombre y descripción; para buscar por precio, query vacío |
| [evaluadores.py](evaluadores.py) | 3 | `cita_fuentes` y `breve` enteras |
| [juez.md](juez.md) | 4 | Una rúbrica con las reglas de la tienda: 20 de 20 en el ensayo |
| [desde_cero.py](desde_cero.py) | Reto | La plantilla del gimnasio, convertida en el asistente de un restaurante |

## Probarla sin tocar tu agente

```bash
CARRITO_MI_AGENTE=sessions/05_capstone/solucion uv run carrito evals juez
CARRITO_MI_AGENTE=sessions/05_capstone/solucion uv run carrito evals experimento --nombre solucion
CARRITO_MI_AGENTE=sessions/05_capstone/solucion uv run carrito reto
```
