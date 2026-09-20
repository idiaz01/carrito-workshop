# 1 · Fundamentos de LLMs: de tokens a una primera aplicación

Fundamentos explicables, una función de mensajes, tres contrastes y cinco notas (tres propias y dos guiadas).

## Empezar

Desde la raíz del repositorio, ejecuta `uv sync --locked`, `uv run carrito doctor` y `uv run jupyter lab`. Abre [starter.ipynb](starter.ipynb) con el kernel de `.venv`.

El notebook carga un checkpoint funcional con datos de práctica. No depende de entregas anteriores. `RUN_LIVE = False` permite ejecutar los mecanismos sin API; activar llamadas reales requiere configurar `.env` y puede generar coste.

## Ejercicios y resultados

Sigue [exercises.md](exercises.md). Completa las celdas `TODO`, vuelve a ejecutar los checks y registra qué cambió. `PENDIENTE` indica una parte que todavía no has completado.

Reinicia el kernel y ejecuta todo antes de entregar. Los checks automáticos verifican comportamientos concretos; acompáñalos con tus observaciones y revisión de las respuestas.

## Alcance

Implementación de agent loops, frameworks de evals y pipelines multimodales.

Las fixtures son respuestas preescritas. Sus resultados verifican mecanismos de aplicación y no miden calidad del LLM.
