# Carrito

Workshop de **Generative AI y AI Agents** del Máster en Data Science & AI de Nuclio.

Construye un asistente de tienda online que consulta un catálogo, recupera políticas, usa herramientas y registra solicitudes de devolución con confirmación. A lo largo de cinco sesiones evolucionarás desde una llamada a un LLM hasta un agente que puedes observar, evaluar y mejorar.

**Iván Díaz Garnacho** · AI Solutions Architect — Siemens Energy · Co-Founder — Iwana Labs
[LinkedIn](https://linkedin.com/in/ivandiazgarnacho) · [Iwana Labs](https://iwanalabs.com)

## Empezar

Necesitas Python 3.13, Git y [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/idiaz01/carrito-workshop.git
cd carrito-workshop
uv sync --locked
uv run carrito doctor
uv run carrito demo --mode fixture
uv run jupyter lab
```

Abre [el notebook de la primera sesión](sessions/01_models/starter.ipynb) y selecciona el kernel de `.venv`. Sigue el [setup completo](docs/setup.md) si necesitas configurar una API o resolver un problema de instalación.

El modo `fixture` utiliza respuestas preescritas del modelo y ejecuta código y herramientas reales. Funciona sin API y permite inspeccionar los mecanismos de la aplicación. El modo `live` llama al modelo configurado en `.env` y consume API. Las credenciales se guardan únicamente en local.

## One project. Five sessions.

| Sesión | Qué construyes |
|---|---|
| [1 · Fundamentals of GenAI and LLMs](sessions/01_models/) | Una primera petición con evidencia, después de explorar tokens y generación |
| [2 · Context Engineering and Working with LLMs](sessions/02_context/) | Contexto seleccionado, estado explícito y salidas con contrato |
| [3 · Building with LangChain, RAG, and Tools](sessions/03_retrieval_tools/) | Retrieval medido, tools e integración MCP |
| [4 · Designing Agents + Agentic Workflows](sessions/04_agents_state/) | Un agente con límites, confirmación y recuperación de errores |
| [5 · Building a Custom Agent](sessions/05_capstone/) | Una configuración propia y una mejora comprobada con casos y trazas |

Trabaja individualmente o sigue la ejecución guiada en clase. Cada notebook arranca desde un checkpoint funcional: puedes continuar aunque no hayas terminado la sesión anterior. Completa las celdas `TODO`, revisa los checks `PENDIENTE` y conserva tus observaciones. Los [ejercicios de cada sesión](sessions/) explican qué comprobar y entregar.

## Estructura

```text
sessions/       notebooks y ejercicios
src/carrito/    aplicación, contexto, retrieval, tools y agent loop
data/           catálogo, pedidos, políticas y consultas de prueba
evals/          casos de desarrollo y criterios de evaluación
examples/       API, LangChain, MCP, Skills, traces y multimodalidad
tests/          pruebas automatizadas del código
docs/           setup, arquitectura y documentación técnica
scripts/        comprobación del repositorio y notebooks
```

La tienda usa 20 productos, 10 pedidos y seis políticas ficticias. Sus cuatro tools son `search_products`, `get_order`, `search_policies` y `request_return`. La última registra una solicitud local tras confirmación del host; no realiza compras, pagos ni reembolsos.

Consulta la [arquitectura](docs/architecture.md), los [ejemplos ejecutables](examples/README.md), la [guía de evaluación](evals/README.md) y las [fuentes técnicas](docs/references.md).

## Comprobar tu entorno y tus cambios

```bash
uv run ruff check .
uv run pytest -q
uv run carrito eval --split dev --mode fixture
uv run carrito mcp-smoke
uv run python scripts/check_notebooks.py
uv run python scripts/check_student_repo.py
```

La integración opcional con LangChain se instala con `uv sync --locked --extra langchain`. Sigue la [comparación de APIs](examples/langchain-comparison.md).

Los checks offline verifican mecanismos y contratos de aplicación. No miden la calidad de un LLM. Revisa las respuestas y sus fuentes, separa datos de desarrollo de nuevas comprobaciones y registra el contexto de cada experimento.

## Procedencia

Código y datos propios. El entorno de comercio electrónico con tools y evals se inspira en [Cartwheel](https://github.com/ai-evals-course/cartwheel-homeworks). Consulta [las atribuciones](THIRD_PARTY_NOTICES.md).
