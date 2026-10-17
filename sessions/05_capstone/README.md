# 5 · Building a Custom Agent

Hoy tu agente gana una capacidad tuya (una skill) y lo evalúas como se hace en producción: dataset, evaluadores, un juez LLM y experimentos en LangSmith.

## Antes de empezar

1. Actualiza el repo: `git pull`.
2. Pega la clave de hoy en `OPENAI_API_KEY` dentro de `.env`. Deja las líneas de LangSmith.
3. Ejecuta `uv run carrito doctor`. Debe mostrar `"api": "OK"` y `"langsmith": "OK"`.
4. Ejecuta `uv run carrito empezar s5`. Tu agente parte de la solución de S4. El tuyo se guarda en `mi_agente_s4/`.

## Cómo trabajas hoy

| Lab | Archivo | Qué haces | Compruebas con |
|---|---|---|---|
| 1 | `mi_agente/skills/` y `mi_agente/casos.jsonl` | Una skill tuya y dos casos para ella | `uv run carrito casos --caso M2 --debug` |
| 2 | Ninguno | Tu dataset y tu primer experimento en LangSmith | `uv run carrito evals experimento --nombre base` |
| 3 | `mi_agente/evaluadores.py` | Dos evaluadores de código | `uv run pytest tests/test_mi_agente.py --runxfail -q -k s5` |
| 4 | `mi_agente/juez.md` | La rúbrica de un juez LLM, comparada con personas | `uv run carrito evals juez` |
| Reto | Cualquiera | Una mejora demostrada: experimento antes y después | LangSmith · Compare |

```bash
uv run carrito evals subir                         # sube tu dataset a LangSmith
uv run carrito evals experimento --nombre base     # un experimento con todos los casos
uv run carrito evals experimento --nombre v2 --repeticiones 3 --juez
uv run carrito evals local --caso M2               # lo mismo, en la terminal y sin LangSmith
uv run carrito pista s5-1
```

La [guía de la sesión](exercises.md) resume cada lab.
[starter.ipynb](starter.ipynb) es material opcional para repasar en casa.

## Fuera de alcance

Despliegue y monitorización en producción (se explican, no se construyen).
