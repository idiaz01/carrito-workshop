# 5 · Guía de la sesión

Ciclo: construir → observar → evaluar → diagnosticar → mejorar. Una pieza cada vez, con evidencia.

## Lab 1 · Tu skill

1. Lee `mi_agente/skills/comparar.md`: una cabecera (`nombre`, `descripcion`) y los pasos.
2. Crea `mi_agente/skills/<tu_skill>.md` con una capacidad nueva para la tienda (regalos, viajes, reclamaciones…).
3. Añade dos casos para tu skill en `mi_agente/casos.jsonl` (M2, M3), copiando el formato de M1.
4. Prueba: `uv run carrito casos --caso M2 --debug`. ¿Llama a `cargar_skill`?

El modelo solo ve el nombre y la descripción de cada skill. Las instrucciones se cargan cuando las pide.

## Lab 2 · Dataset y experimento

1. `uv run carrito evals subir`: sube los casos de S2–S4 y los tuyos.
2. `uv run carrito evals experimento --nombre base`.
3. En LangSmith, abre «Datasets & Experiments», tu dataset y el experimento. Mira `checks` y `tokens` por caso.

## Lab 3 · Evaluadores de código

En `mi_agente/evaluadores.py`, borra `raise NotImplementedError` en las dos funciones y rellena los `___`.
Comprueba: `uv run pytest tests/test_mi_agente.py --runxfail -q -k s5`.

## Lab 4 · Un juez LLM

1. `uv run carrito evals juez`: el juez valora 8 respuestas que una persona ya ha etiquetado.
2. Mejora `mi_agente/juez.md` hasta que el acuerdo sea alto. Usa los requisitos de `SPEC.md`.
3. Un juez también es un sistema que hay que evaluar.

## Reto · Una mejora demostrada

1. Elige un fallo de tu experimento `base`.
2. Cambia UNA pieza de tu agente.
3. `uv run carrito evals experimento --nombre mejora --repeticiones 3`.
4. En LangSmith, compara `base` y `mejora`. ¿Mejora lo que querías? ¿Empeora algo?

## Debes poder explicar

- Qué es una skill y por qué solo se carga cuando hace falta.
- Dataset, evaluador, experimento: qué es cada uno.
- Cuándo usar un evaluador de código, un juez LLM o una persona.
- Por qué se repite un experimento.
- Qué vigilarías de tu agente en producción.
