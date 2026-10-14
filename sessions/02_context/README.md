# 2 · Context Engineering and Working with LLMs

Qué entra en el modelo (origen, autoridad, selección y estado) y cómo comprobar lo que sale (contrato y reglas).

## Antes de empezar

1. Pega la clave de hoy en `OPENAI_API_KEY` dentro de `.env`.
2. Ejecuta `uv run carrito doctor`. Debe mostrar `"api": "OK"`.
3. Ejecuta `uv run jupyter lab` y abre [starter.ipynb](starter.ipynb) con el kernel de `.venv`.

Si algo falla, consulta la tabla de [setup](../../docs/setup.md#si-algo-falla).

## Cómo seguir la sesión

- 🖥️ **Demo:** el docente ejecuta en pantalla. Tú ejecutas la misma celda. Antes, predice el resultado.
- ✏️ **Tu turno:** completa los `...` de la celda. En el aula, por parejas.
- ✅ **Comprueba:** la celda de check dice `✅ OK` o `✏️ PENDIENTE`, con una pista.

Después de cada lab, el docente enseña una solución. Si no terminas un lab, las celdas siguientes funcionan igual.
Las respuestas del modelo pueden variar entre equipos: es normal.

La [guía de la sesión](exercises.md) resume cada lab.

## Fuera de alcance

Memoria persistente y motores de validación complejos.
