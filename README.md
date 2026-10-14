# Carrito

Workshop de **Generative AI y AI Agents** del Máster en Data Science & AI de Nuclio.

Construimos un asistente de tienda online. El asistente consulta un catálogo, recupera políticas, usa tools y registra solicitudes de devolución con confirmación. En cinco sesiones pasamos de una llamada a un LLM a un agente que podemos observar, evaluar y mejorar.

**Iván Díaz Garnacho** · AI Solutions Architect — Siemens Energy · Co-Founder — Iwana Labs
[LinkedIn](https://linkedin.com/in/ivandiazgarnacho) · [Iwana Labs](https://iwanalabs.com)

## Cómo funciona la clase

El docente comparte pantalla y ejecuta cada paso. Tú lo ejecutas en tu equipo, al mismo tiempo.
Desde la sesión 2 construyes tu propio agente en [`mi_agente/`](mi_agente/), paso a paso, a partir de su [`SPEC.md`](SPEC.md). No hay entregas.

Cada sesión usa una clave de API nueva. El docente la comparte al inicio de la sesión.

## Empezar (una vez, antes de la primera sesión)

Necesitas Python 3.13, Git y [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/idiaz01/carrito-workshop.git
cd carrito-workshop
uv sync --locked --extra langchain
```

Después, en cada sesión:

1. Copia `.env.example` como `.env` (solo la primera vez).
2. Pega la clave de la sesión en `OPENAI_API_KEY`.
3. Comprueba la clave: `uv run carrito doctor`. Debe mostrar `"api": "OK"`.
4. Abre Jupyter: `uv run jupyter lab`. Selecciona el kernel de `.venv`.

Más detalle y solución de problemas: [setup](docs/setup.md).

## Cinco sesiones, un proyecto

| Sesión                                                                      | Qué construimos                                                             |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| [1 · Fundamentals of GenAI and LLMs](sessions/01_models/)                   | Una primera petición con evidencia, después de explorar tokens y generación |
| [2 · Context Engineering and Working with LLMs](sessions/02_context/)       | El contexto de tu agente: system prompt, tools, resultados y memoria        |
| [3 · Building with LangChain, RAG, and Tools](sessions/03_retrieval_tools/) | Retrieval medido, tools e integración MCP                                   |
| [4 · Designing Agents + Agentic Workflows](sessions/04_agents_state/)       | Un agente con límites, confirmación y recuperación de errores               |
| [5 · Building a Custom Agent](sessions/05_capstone/)                        | Un perfil propio y una mejora comprobada con casos y trazas                 |

Cada notebook empieza desde datos preparados. No necesitas la sesión anterior.

## La tienda

20 productos, 10 pedidos y seis políticas. Todos son ficticios.
Cuatro tools: `search_products`, `get_order`, `search_policies` y `request_return`.
`request_return` registra una solicitud local después de la confirmación del host. No hace compras, pagos ni reembolsos.

```text
SPEC.md         requisitos del asistente, con IDs
mi_agente/      tu agente: lo construyes a partir de la sesión 2
sessions/       notebooks y guía de cada sesión
src/carrito/    aplicación, contexto, retrieval, tools y agent loop
data/           catálogo, pedidos, políticas y consultas de prueba
evals/          casos de desarrollo y rúbrica
examples/       LangChain, MCP, Skills, trazas y multimodalidad
tests/          pruebas automáticas del código
docs/           setup, arquitectura y fuentes
scripts/        comprobación del repositorio y de los notebooks
```

Más información: [arquitectura](docs/architecture.md), [ejemplos](examples/README.md), [evaluación](evals/README.md) y [fuentes](docs/references.md).

## Mantenimiento

Estos checks no llaman a la API y no necesitan clave:

```bash
uv run ruff check .
uv run pytest -q
uv run python scripts/check_notebooks.py
uv run python scripts/check_student_repo.py
```

Los tests y los notebooks usan un cliente falso (`CARRITO_OFFLINE_CHECK=1`). Comprueban el código, no las respuestas del modelo. No uses esa variable en clase.
