# 1 · Fundamentos de LLMs: de tokens a una primera aplicación

Qué hace un LLM, comprobado con tres experimentos reales. Después, una aplicación con una llamada al modelo y una primera evaluación de cinco casos.

## Antes de empezar

1. Pega la clave de hoy en `OPENAI_API_KEY` dentro de `.env`.
2. Ejecuta `uv run carrito doctor`. Debe mostrar `"api": "OK"`.
3. Ejecuta `uv run jupyter lab` y abre [starter.ipynb](starter.ipynb) con el kernel de `.venv`.

Si algo falla, consulta la tabla de [setup](../../docs/setup.md#si-algo-falla).

## Cómo seguir la sesión

El docente ejecuta el notebook en pantalla. Ejecuta las mismas celdas en tu equipo.
Antes de cada celda, predice el resultado. Después, compáralo.
El código ya está completo. Las respuestas del modelo pueden variar entre equipos: es normal.

La [guía de la sesión](exercises.md) resume qué observar en cada sección.

## Fuera de alcance

Agent loops, frameworks de evals y pipelines multimodales.
