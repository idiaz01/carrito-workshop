# 2 · Context Engineering and Working with LLMs

Hoy construyes el contexto de tu propio agente: system prompt, descripciones de tools, formato de los resultados y memoria de la conversación.

## Antes de empezar

1. Actualiza el repo: `git fetch origin` y `git reset --hard origin/main`.
2. Pega la clave de hoy en `OPENAI_API_KEY` dentro de `.env`.
3. Ejecuta `uv run carrito doctor`. Debe mostrar `"api": "OK"`.
4. Abre la carpeta del repo en VS Code. Abre [starter.ipynb](starter.ipynb) con el kernel de `.venv`.

Si algo falla, consulta la tabla de [setup](../../docs/setup.md#si-algo-falla).

## Cómo trabajas hoy

Tu agente vive en [`mi_agente/`](../../mi_agente/). Sus requisitos están en [`SPEC.md`](../../SPEC.md).
El docente explica cada paso y lo hace en pantalla. Después, lo haces tú (en el aula, por parejas).

```bash
uv run carrito agente --debug                        # habla con tu agente y mira lo que ve el modelo
uv run carrito casos                                 # marcador: 8 casos del SPEC
uv run pytest tests/test_mi_agente.py --runxfail -q  # tus pasos: FAILED → PASSED
```

Si un paso no está terminado, el agente funciona igual: usa un comportamiento por defecto.
Las respuestas del modelo pueden variar entre equipos: es normal.

La [guía de la sesión](exercises.md) resume cada paso.

## Fuera de alcance

Memoria persistente entre sesiones y subagentes (S4). Trazas en LangSmith (S3).
