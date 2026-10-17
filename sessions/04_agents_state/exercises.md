# 4 · Guía de la sesión

Método: cambia **una** pieza → mira la traza en LangSmith → mide con `carrito casos --sesion 4`.

## Lab 1 · Límites del loop

En `mi_agente/agente.toml`, sección `[limites]`:

| Valor | Qué limita |
|---|---|
| `max_pasos` | Llamadas al modelo por turno |
| `max_tools` | Llamadas a tools por turno |
| `max_tokens` | Tokens por turno |

Prueba C28 con los valores por defecto. ¿Termina? Ajusta los límites: suficientes para la tarea, no más.

## Lab 2 · Rutas: workflow antes del agente

Añade bloques `[[rutas]]`:

```toml
[[rutas]]
tipo = "fija"                      # sin modelo: 0 tokens
palabras = ["poema", "chiste"]
respuesta = "Solo puedo ayudarte con la tienda."

[[rutas]]
tipo = "buscar"                    # busca y responde en una llamada, sin tools
palabras = ["envío", "garantía"]
```

Compara tokens con `uv run carrito casos --sesion 4` y `--comparar`. Cuidado con las palabras que atrapan preguntas que no son de esa ruta.

## Lab 3 · Salida estructurada y guardrail

1. Lee la clase `Respuesta` de `mi_agente/salida.py`: es la forma de la respuesta final.
2. En `revisar`, borra `raise NotImplementedError` y rellena los `___`.
3. Comprueba: `uv run pytest tests/test_mi_agente.py --runxfail -q -k s4`.
4. En `--debug`, mira la línea «Salida»: fuentes, problemas y si se corrigió.

## Lab 4 · Un subagente

1. Escribe el prompt del subagente en `mi_agente/subagente.md`.
2. En `agente.toml`, pon `activo = true` en `[subagente]`.
3. Pregunta por la garantía de dos productos. En LangSmith, abre la traza: el subagente es una rama propia.
4. Mide: ¿gasta más o menos tokens en total? ¿Qué ve el agente principal?

## Reto

`uv run carrito casos --sesion 4`: 8 casos (C21–C28). Gana quien pase más casos con menos tokens.

## Debes poder explicar

- Cuándo un workflow fijo es mejor que un agente.
- Para qué sirve cada límite del loop.
- Qué garantiza una salida estructurada y qué no.
- Qué gana y qué cuesta un subagente.
- Quién confirma una acción: la persona, nunca el modelo.
