# Evaluación pequeña y observable

`uv run carrito eval` ejecuta 16 casos con el modelo de la sesión. Cada caso usa una SQLite nueva.

El checker lee dos cosas: las tools que se ejecutaron y el estado de SQLite. No lee la calidad del texto final. Para eso usamos la [rúbrica humana](rubrics.md).

Si el modelo pide una aclaración donde el caso esperaba una tool, el check puede fallar. Lee la traza antes de decidir si es un fallo real.

## Casos de desarrollo

`dev.jsonl` tiene 16 escenarios públicos. Cada línea tiene pregunta, expectativas y `fixture_calls`.
El modelo no recibe las expectativas ni las `fixture_calls`. Las `fixture_calls` solo sirven para los tests sin API.

En los casos de escritura, el host simula el clic de confirmación. El check comprueba tres cosas: no hay escritura antes de confirmar, el payload guardado es el exacto y solo existe una solicitud.

## Qué comprueba cada tipo de caso

- **Catálogo:** IDs existentes, precio exacto, presupuesto y candidato esperado.
- **Pedidos:** el pedido es del usuario del host. Un pedido ajeno y uno inexistente dan el mismo error.
- **Retrieval:** la fuente esperada aparece. Esto no prueba que la respuesta use bien la fuente.
- **Devolución:** reglas de plazo, estado y excepciones; confirmación del host; una sola solicitud.
- **Aclaración:** sin tools si faltan datos, y respuesta no vacía.

Las trazas se guardan en `runtime/evals`. Usa `--trace-dir` para comparar dos versiones.
Para comparar, mantén iguales: modelo, casos, usuario, fecha de referencia y estado inicial.

## S5: contrato de respuesta

`compare_contracts(builder=improved_response, profile=profile, mode="live")` ejecuta cuatro casos con el agente real, antes y después de la mejora. Mide el contrato de la aplicación, no la calidad del lenguaje.
`cases=[("bicicleta", 100), ("altavoz", 60)]` añade casos nuevos.

El backend (16 casos) y el contrato (casos de S5) se informan por separado.
