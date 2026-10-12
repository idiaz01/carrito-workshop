# Carrito: cinco sesiones, un runtime

Los notebooks usan los mismos módulos de `src/carrito`. No hay un segundo agent loop.
Código en inglés, explicaciones en español.

`uv run python examples/learning_labs.py --output runtime/learning-evidence.json` repite los experimentos sin API, con decisiones del modelo escritas de antemano. La captura está en `examples/traces/learning-evidence.json`.

## Contexto y contrato (S2)

```python
from carrito.context import ConversationState, compose_context
state = ConversationState(category="auriculares", budget_eur=80)
pack = compose_context("Recomienda", state, [
    {"source_id": "P001", "text": "Auriculares Nube: 69,90 EUR", "relevant": True}
], max_evidence_chars=200)
```

- El presupuesto de evidencia cuenta caracteres serializados, no tokens.
- `relevant` es una decisión del caller. No detecta prompt injection.
- `RecommendationContract` tiene `status` (`recommend`, `clarify`, `no_match`), `product_ids`, `explanation` y `missing_information`.
- El checker valida schema, IDs, coherencia entre status e IDs, y presupuesto. No valida la verdad de `explanation`.

## Un perfil para el agente (S3–S5)

```python
from carrito.lab import AgentProfile, run_profile
from carrito.model import OpenAIModel
from carrito.store import create_store
from carrito.tools import StoreTools
profile = AgentProfile(name="shopping", allowed_tools=("search_products", "search_policies"), max_steps=4)
result = run_profile("Auriculares por menos de 80 euros", StoreTools(create_store()),
                     OpenAIModel(), profile, state=state)
```

`run_profile` compone el contexto, añade las instrucciones del perfil y llama a `run_agent`.
El host filtra los schemas y también la ejecución. `enable_skills` no da permisos.
`response_builder` aplica el contrato a los productos observados. El resultado conserva `model_answer`, `answer`, eventos y métricas.

## Retrieval (S3)

Cada política ya es una unidad corta. `retrieve` usa palabras normalizadas y una expansión de sinónimos visible. No usa embeddings.

Resultados medidos sobre 6 consultas (pocas para generalizar):

| top-k | Expansión | Mean recall | Mean precision |
|---|---|---:|---:|
| 1 | No | 0,4167 | 0,5000 |
| 1 | Sí | 0,7500 | 0,8333 |
| 2 | No | 0,6667 | 0,5000 |
| 2 | Sí | 1,0000 | 0,6667 |

Una fuente recuperada puede no apoyar la afirmación.

## Estado y recuperación (S4)

- `save_state` / `load_state` guardan preferencias. No guardan la ejecución, los permisos ni la confirmación pendiente.
- `recover_read` repite solo `temporary_unavailable`, hasta 3 intentos. No lo uses con escrituras.
- El límite de tokens se comprueba después de cada respuesta. Para el loop, pero no limita la llamada ya enviada.

## Métricas (S5)

`trace_metrics` cuenta llamadas al modelo y a tools, errores, tokens y latencia.
El coste solo se calcula si pasas precios explícitos y fechados.
