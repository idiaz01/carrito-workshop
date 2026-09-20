# 2 · Context Engineering and Working with LLMs

Contexto seleccionado, estado actualizado, schema y contrato de negocio comprobados.

## Empezar

Desde la raíz del repositorio, ejecuta `uv sync --locked`, `uv run carrito doctor` y `uv run jupyter lab`. Abre [starter.ipynb](starter.ipynb) con el kernel de `.venv`.

El notebook carga un checkpoint funcional con datos de práctica. No depende de entregas anteriores. `RUN_LIVE = False` permite ejecutar los mecanismos sin API; activar llamadas reales requiere configurar `.env` y puede generar coste.

## Ejercicios y resultados

Sigue [exercises.md](exercises.md). Completa las celdas `TODO`, vuelve a ejecutar los checks y registra qué cambió. `PENDIENTE` indica una parte que todavía no has completado.

Reinicia el kernel y ejecuta todo antes de entregar. Los checks automáticos verifican comportamientos concretos; acompáñalos con tus observaciones y revisión de las respuestas.

## Alcance

Memoria persistente y motores de validación complejos.

Las fixtures son respuestas preescritas. Sus resultados verifican mecanismos de aplicación y no miden calidad del LLM.
