# 3 · Guía de la sesión

Método: cambia **una** pieza → mira la traza en LangSmith → mide con `carrito rag --evaluar` o `carrito casos --sesion 3`.

## Lab 1 · Trazas

1. Añade a `.env`: `LANGSMITH_TRACING=true`, tu `LANGSMITH_API_KEY` y `LANGSMITH_PROJECT=carrito`.
2. `uv run carrito doctor` → `"langsmith": "OK"`.
3. `uv run carrito agente` y pregunta: «¿Cuánto cuesta el envío a Canarias?».
4. En LangSmith, abre el proyecto `carrito` y la traza. Responde: ¿cuántas llamadas al modelo hay? ¿Qué tool usó? ¿Cuántos tokens?

## Lab 2 · RAG con `mi_agente/rag.toml`

| Valor | Opciones | Qué cambia |
|---|---|---|
| `fuentes` | `politicas`, `ayuda` | Qué documentos se pueden encontrar |
| `trocear` | `documento`, `seccion`, `frase` | El tamaño de cada pieza |
| `metodo` | `lexico`, `embeddings`, `hibrido` | Cómo se ordenan las piezas |
| `top_k` | 1 a 10 | Cuántas piezas recibe el modelo |

Objetivo: más aciertos con menos tokens. Cambia un valor y ejecuta `uv run carrito rag --evaluar`.

## Lab 3 · Una tool nueva

1. En `mi_agente/herramientas.py`, borra `raise NotImplementedError` y rellena los `___`.
2. Comprueba: `uv run pytest tests/test_mi_agente.py --runxfail -q -k s3`.
3. En `mi_agente/tools.md`, añade la sección `## plazo_devolucion` con su descripción. Sin descripción, el modelo no ve la tool.
4. Pregunta: «¿Hasta qué día puedo devolver el pedido 104?».

## Lab 4 · LangChain

1. `uv run carrito agente --motor langchain --debug` con la misma pregunta del lab 3.
2. En LangSmith, compara las dos trazas: pasos, tools, tokens y lo que ve el modelo.
3. Abre `src/carrito/langchain_agente.py`. Encuentra las tres piezas: el modelo, las tools y el system prompt.

## Reto

`uv run carrito casos --sesion 3`: 8 casos nuevos (C13–C20). Gana quien pase más casos con menos tokens.
Para cada caso que falla, busca en LangSmith el paso donde se rompe.

## Debes poder explicar

- Cuándo usar RAG, una tool o nada.
- Qué cambia al trocear por documento, por sección o por frase.
- Por qué la fecha límite la calcula el código y no el modelo.
- Qué hace LangChain por ti y qué sigue siendo trabajo tuyo.
