# 5 · Guía de la sesión

Ciclo: construir → observar → evaluar → diagnosticar → mejorar. Una pieza cada vez, con evidencia.

## Lab 1 · Tu skill

1. Lee `mi_agente/skills/comparar.md`: una cabecera (`nombre`, `descripcion`) y los pasos.
2. Crea `mi_agente/skills/<tu_skill>.md` con una capacidad nueva para la tienda (regalos, viajes, reclamaciones…).
3. Añade dos casos para tu skill en `mi_agente/casos.jsonl` (M2, M3), copiando el formato de M1.
4. Prueba: `uv run carrito casos --caso M2 --debug`. ¿Llama a `cargar_skill`?

El modelo solo ve el nombre y la descripción de cada skill. Las instrucciones se cargan cuando las pide.

## Lab 2 · Dataset y experimento

1. `uv run carrito evals subir`: sube los casos de S2–S5 y los tuyos. Si cambias un caso, `subir` lo actualiza.
2. `uv run carrito evals experimento --nombre base`. Al terminar, la terminal enseña los casos que fallan.
3. En LangSmith, abre «Datasets & Experiments», tu dataset y el experimento. Abre un caso que falla (C33–C36) y su traza.

## Lab 3 · Evaluadores de código

En `mi_agente/evaluadores.py`, escribe las dos funciones enteras: `cita_fuentes` (RESP-1) y `breve` (RESP-3). El docstring de cada una tiene las reglas y dos ejemplos.
Comprueba: `uv run pytest tests/test_mi_agente.py --runxfail -q -k s5`.

## Lab 4 · Un juez LLM

1. `uv run carrito evals juez`: el juez valora 20 respuestas que una persona ya ha etiquetado.
2. Mejora `mi_agente/juez.md` hasta que el acuerdo sea alto. Usa los requisitos de `SPEC.md`.
3. Un juez también es un sistema que hay que evaluar.

## Reto · Tu agente desde cero

`mi_agente/desde_cero.py`: un agente completo con LangChain en un archivo. Funciona tal cual: el asistente de un gimnasio. Tiene las seis piezas del curso: datos, tools, prompt, límites, casos y juez.

1. **Nivel 1:** cámbialo por tu dominio: datos, prompt, casos y juez.
2. **Nivel 2:** añade una tool nueva.
3. **Nivel 3:** un experimento en LangSmith con repeticiones.

```bash
uv run carrito reto --chat                         # habla con tu agente
uv run carrito reto                                # tus casos, tus evaluadores y tu juez
uv run carrito reto --langsmith --repeticiones 3   # el experimento
uv run carrito pista s5-reto
```

## Debes poder explicar

- Qué es una skill y por qué solo se carga cuando hace falta.
- Dataset, evaluador, experimento: qué es cada uno.
- Cuándo usar un evaluador de código, un juez LLM o una persona.
- Por qué se repite un experimento.
- Qué vigilarías de tu agente en producción.
- Qué piezas tiene un agente que construyes desde cero, y dónde estaba cada una en Carrito.
