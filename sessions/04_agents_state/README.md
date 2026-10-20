# 4 · Designing Agents + Agentic Workflows

Hoy abres el loop de tu agente: límites, workflows antes del agente, salida estructurada con un guardrail y un subagente.

## Antes de empezar

1. Actualiza el repo: `git pull`.
2. Pega la clave de hoy en `OPENAI_API_KEY` dentro de `.env`. Deja las líneas de LangSmith.
3. Ejecuta `uv run carrito doctor`. Debe mostrar `"api": "OK"` y `"langsmith": "OK"`.
4. Ejecuta `uv run carrito empezar s4`. Tu agente parte de la solución de S3. El tuyo se guarda en `mi_agente_s3/`.

## Cómo trabajas hoy

| Lab | Archivo | Qué haces | Compruebas con |
|---|---|---|---|
| 1 | `mi_agente/agente.toml` · `[limites]` | Pasos, tools y tokens por turno | `uv run carrito casos --caso C28 --debug` |
| 2 | `mi_agente/agente.toml` · `[[rutas]]` | Workflows fijos antes del agente | `uv run carrito casos --sesion 4` |
| 3 | `mi_agente/salida.py` | Un guardrail para la salida estructurada | `uv run pytest tests/test_mi_agente.py --runxfail -q -k s4` |
| 4 | `mi_agente/subagente.md` y `[subagente]` | Un subagente para los documentos | LangSmith |
| Reto | Cualquiera | Marcador de la sesión 4 | `uv run carrito casos --sesion 4` |

```bash
uv run carrito agente --debug        # /confirmar confirma una devolución pendiente
uv run carrito casos --todos         # los casos de S2, S3 y S4: ¿has roto algo?
uv run carrito pista s4-2            # la siguiente pista del lab 2
```

La [guía de la sesión](exercises.md) resume cada lab.
[starter.ipynb](starter.ipynb) es material opcional para repasar en casa.

## Fuera de alcance

LangGraph en código, despliegue y agentes que se coordinan entre sí. Evals en LangSmith (S5).
