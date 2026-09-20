# Evaluación pequeña y observable

`uv run carrito eval --split dev --mode fixture` ejecuta 16 casos con SQLite nuevo por caso. Las tools y las comprobaciones se ejecutan de verdad; las llamadas del modelo son preescritas. Pasar esto comprueba mecanismos, **no calidad del modelo**. Una prueba de regresión inyecta IDs/precios erróneos y solicitudes para otro pedido: el checker falla.

`--mode live` usa el modelo de `OPENAI_MODEL`, ejecuta la pregunta y evalúa los resultados observados. Consume API. Los checks de tools/estado no comprueban por sí solos la respuesta final. El informe deja la revisión humana pendiente y las trazas contienen mensajes, outputs, usage, latencia y errores. Si un modelo pide aclaración en un caso que esperaba una tool, el check puede fallar: inspeccionar la traza antes de etiquetar el fallo.

Los casos de escritura positiva simulan el clic del host después de obtener un payload pendiente. Ese seguimiento de host es determinista en ambos modos; no mide una segunda decisión autónoma del LLM. Comprueba ausencia de escritura antes de confirmar, payload exacto persistido e idempotencia. No hay ninguna tool de confirmación.

## Casos de desarrollo

`dev.jsonl` contiene 16 escenarios públicos. Úsalos para diagnosticar el sistema y añade casos propios que comprueben comportamientos distintos. Mantén esas nuevas comprobaciones separadas durante el ajuste.

Cada línea contiene pregunta, llamadas fixture preescritas y expectativas declaradas. En modo live no se entregan las llamadas ni expectativas al modelo. El checker lee salidas capturadas y estado SQLite. Nunca sustituye una respuesta real por el oráculo.

## Qué revisar

- Catálogo: IDs existentes, precios exactos en datos, presupuesto y candidato esperado.
- Pedidos: propiedad del usuario fijado por el host; un pedido ajeno y uno ausente se ocultan igual.
- Retrieval: presencia de fuente esperada; esto no demuestra grounding de la respuesta final.
- Devolución: reglas de plazo/estado/excepciones, ausencia de escritura, confirmación del host, payload exacto y una sola solicitud.
- Aclaración: check mínimo de no llamar tools sin datos y respuesta no vacía; la pertinencia se juzga con la rúbrica humana.

Resultados por defecto en stdout; guardar con `> runtime/report.json`. Trazas en `runtime/evals`; `--trace-dir` permite comparar dos versiones sin sobrescribir. Misma fecha, usuario, modelo, casos y estado inicial en toda comparación. Registrar versión del prompt y modelo manualmente en la entrega.

## Capstone: contrato del mismo runtime

El notebook S5 usa `carrito.lab.compare_contracts(builder=improved_response, profile=profile)`: cuatro casos independientes ejecutan el agente real con llamadas preescritas, tools SQLite reales y el constructor del alumno. La comparación mide el contrato de aplicación, no calidad de lenguaje. `cases=[("bicicleta",100),("altavoz",60)]` permite comprobar consultas nuevas tras congelar el cambio.

`mode="live"` sustituye las decisiones preescritas por `OpenAIModel`; requiere API y consume coste. El checker conserva el mismo alcance y marca fallo si no se observa un contrato válido. Comparar el texto final y las decisiones exige revisión humana; la variabilidad del modelo puede introducir diferencias adicionales.

Los 16 casos de desarrollo validan invariantes generales de backend y se reportan separados de los casos del contrato modificado. [Experimentos y límites](../examples/learning-labs.md).
