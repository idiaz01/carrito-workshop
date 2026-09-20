# Carrito: cinco sesiones, un runtime observable

Los notebooks permiten modificar contexto, contrato y configuración que utilizan los mismos módulos de `src/carrito`. Los notebooks parten de checkpoints independientes para recuperar el ritmo, pero no definen un segundo agent loop. Código en inglés, explicaciones en español.

`uv run python examples/learning_labs.py --output runtime/learning-evidence.json` ejecuta los experimentos deterministas. La captura distribuida está en `examples/traces/learning-evidence.json`: proviene de Python y SQLite ejecutados, con decisiones del modelo preescritas. No representa calidad ni rendimiento de un LLM.

## Contexto: contrato exacto

```python
from carrito.context import ConversationState, compose_context, RecommendationContract
state = ConversationState(category="auriculares", budget_eur=80)
pack = compose_context("Recomienda", state, [
    {"source_id": "P001", "text": "Auriculares Nube:69,90 EUR", "relevant": True}
], max_evidence_chars=200)
messages = pack["messages"]
```

El presupuesto transparente se expresa en **caracteres serializados de evidencia**, no en tokens ni contexto total del proveedor. Cambiar `relevant` es una decisión del caller, no un detector de injection. La autoridad se explica mediante developer/user y se refuerza con controles del host; el prompt solo no es una frontera de seguridad.

`RecommendationContract`: `status` (`recommend`, `clarify`, `no_match`), `product_ids`, `explanation`, `missing_information`. El checker valida schema, IDs, relación status/IDs y presupuesto. La veracidad completa de `explanation` requiere revisión adicional.

## Un perfil utilizado por el agente

```python
from carrito.lab import AgentProfile, run_profile
from carrito.model import FixtureModel
from carrito.store import create_store
from carrito.tools import StoreTools
profile = AgentProfile(name="shopping", allowed_tools=("search_products", "search_policies"), max_steps=4)
result = run_profile("Auriculares por menos de80 euros", StoreTools(create_store()),
                     FixtureModel.for_scenario("catalog"), profile, state=state)
```

`run_profile` compone el contexto, añade instrucciones del perfil y llama a `run_agent`; el host filtra schemas **y** ejecución. `response_builder` permite aplicar el contrato a productos realmente observados. Se conservan `model_answer`, `answer`, eventos y métricas. `enable_skills` es independiente de permisos. Para live se sustituye `FixtureModel` por `OpenAIModel`, con `.env` configurado; genera coste y exige revisar outputs.

## Retrieval y representación

Cada política es ya una unidad corta coherente; `load_chunks` conserva el documento y añade `chunk_id`, `source_id` y metadata. No se promete un pipeline de ingestion de producción. `retrieve` utiliza palabras normalizadas y una expansión de sinónimos visible. No son embeddings. En documentos largos, comprueba si una división arbitraria separa regla y excepción antes de decidir el tamaño.

Datos medidos sobre6consultas originales, insuficientes para generalizar:

| top-k | Expansión | Mean recall | Mean precision |
|---|---|---:|---:|
|1|No|0,4167|0,5000|
|1|Sí|0,7500|0,8333|
|2|No|0,6667|0,5000|
|2|Sí|1,0000|0,6667|

La comparación factorial separa efectos. Una fuente recuperada puede no respaldar la afirmación. Dense retrieval, hybrid y reranking se explican con sus ventajas y límites; no se atribuyen a este buscador léxico.

## Recuperación y límites

`save_state`/`load_state` conservan preferencias tipadas. La demo S4 también registra una solicitud en SQLite con archivo, cierra la conexión y la reabre: permanece una sola fila y la misma request_id, mientras `pending` vuelve a `None`. No conservan ejecución de agente, permisos, confirmación pendiente ni call stack. `recover_read` reintenta solo `temporary_unavailable`, hasta3intentos; no debe envolver escrituras a ciegas. El límite de tokens del loop se comprueba después de recibir una respuesta: impide continuar, no limita exactamente la factura de la llamada ya enviada.

## Evaluación del mismo cambio

`compare_contracts(builder=improved_response, profile=profile, cases=[("bicicleta",100),("altavoz",60)])` aplica la función del alumno a productos observados en el mismo runtime. Cada caso recibe SQLite nueva. El contrato y las invariantes de backend se reportan por separado. Los 16 casos de `evals/dev.jsonl` son datos de desarrollo. Añade consultas nuevas para comprobar si el cambio generaliza.

Formula una hipótesis, localiza el primer fallo y comprueba regresiones con casos nuevos.

Métricas: model/tool calls, errores, tokens y latencia de modelo/run. Los tokens fixture son0; el coste se deja `null`. Solo estimar coste live con precios explícitos, fechados y sus unidades; cached/reasoning pricing puede necesitar cálculo específico. El JSON de evidencia excluye latencias por no ser una medición útil del rendimiento del modelo.

En S2 el bloque live compara tres requests con el mismo modelo, pregunta y schema: evidencia seleccionada, preferencias ausentes y contexto ruidoso. Son tres llamadas de pago; sirven para inspeccionar mecanismos y formular hipótesis, no para estimar una tasa de mejora. En S3, la estrategia elegida se inyecta con `StoreTools(..., policy_retriever=partial(retrieve, chunks=chunks, top_k=2, expand=True))` y el agente ejecuta `search_policies` con ella.
