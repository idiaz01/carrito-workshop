# 3 · Building with LangChain, RAG, and Tools

Hoy tu agente encuentra respuestas en documentos (RAG), gana una tool nueva y lo ves todo en LangSmith.

## Antes de empezar

1. Actualiza el repo: `git pull`. Tus cambios en `mi_agente/` se conservan.
2. Pega la clave de hoy en `OPENAI_API_KEY` dentro de `.env`.
3. Añade tu clave de LangSmith a `.env` ([setup](../../docs/setup.md#3-langsmith-desde-la-sesión-3)).
4. Ejecuta `uv run carrito doctor`. Debe mostrar `"api": "OK"` y `"langsmith": "OK"`.
5. Ejecuta `uv run carrito empezar s3`. Tu agente parte de la solución de S2. El tuyo se guarda en `mi_agente_s2/`.

## Cómo trabajas hoy

Igual que en S2: el docente explica cada paso y lo hace en pantalla. Después, lo haces tú.

| Lab | Archivo | Qué haces | Compruebas con |
|---|---|---|---|
| 1 | `.env` | Activas las trazas y lees tu primera traza | LangSmith |
| 2 | `mi_agente/rag.toml` | Eliges fuentes, troceado, método y `top_k` | `uv run carrito rag --evaluar` |
| 3 | `mi_agente/herramientas.py` y `tools.md` | Una tool nueva: `plazo_devolucion` | `uv run pytest tests/test_mi_agente.py --runxfail -q -k s3` |
| 4 | Ninguno | Tu agente con LangChain. Comparas las dos trazas | `uv run carrito agente --motor langchain` |
| Reto | Cualquiera | Marcador de la sesión 3 | `uv run carrito casos --sesion 3` |

```bash
uv run carrito agente --debug                 # habla con tu agente
uv run carrito rag --buscar "pregunta"        # qué piezas encuentra la búsqueda
uv run carrito pista s3-2                     # la siguiente pista del lab 2
```

La [guía de la sesión](exercises.md) resume cada lab.
[starter.ipynb](starter.ipynb) es material opcional para repasar en casa.

## Fuera de alcance

Bases de datos vectoriales y despliegue. Loop, estado y workflows (S4). Evals en LangSmith (S5).
