# Ejemplos ejecutables

- `uv run carrito demo --mode fixture`: modelo preescrito, tools reales.
- `uv run carrito chat --mode fixture`: escenarios preescritos con historial. `/confirm` confirma el pedido y motivo mostrados; `/quit` termina. `--mode live` usa OPENAI_MODEL y consume API.
- `uv run --extra langchain python examples/langchain_comparison.py --mode fixture`: comparación de retrieval y tools con LangChain; [guía](langchain-comparison.md).
- `uv run carrito mcp-smoke`: servidor/cliente stdio real, solo catálogo.
- `uv run carrito skill-demo`: compara activación y muestra el procedimiento añadido al contexto.
- `uv run carrito judge-demo`: tres juicios preescritos con un desacuerdo deliberado frente a etiquetas humanas; `--mode live` usa un juez real.
- `uv run python examples/multimodal.py`: inspecciona la forma de una petición con una tarjeta de producto original; no llama API. `--mode live` envía la imagen preparada al modelo. La visión no prueba stock, garantía o batería.

La demo de multimodalidad muestra la estructura de una petición con imagen. El loop base es Python. LangGraph queda como lectura opcional para persistencia/orquestación más compleja; no es dependencia del taller.

- `uv run python examples/learning_labs.py`: experimentos compartidos de contexto, retrieval y contrato del agente. [Guía y API](learning-labs.md).
