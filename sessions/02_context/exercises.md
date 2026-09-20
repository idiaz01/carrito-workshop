# 2 · Context Engineering and Working with LLMs
Carrito evoluciona mediante `carrito.context`, compartido con el agente final.
Predice → ejecuta → compara → explica. Los experimentos offline miden composición y contratos, no calidad del modelo.

Predice el resultado antes de ejecutar y anota tus observaciones.

## Anatomía y autoridad
Identifica instrucciones, petición, estado y evidencia en el request. Un campo `source_id` permite citar; no concede autoridad. El límite de caracteres de esta práctica no es un contador de tokens.

## Experimento controlado: qué cambia y qué permanece
Varía únicamente el presupuesto de evidencia (50/200/2000 caracteres). Después marca el anuncio como relevante y observa que puede entrar: seleccionar contexto NO neutraliza prompt injection. Decide qué condición debe aplicar el host fuera del prompt.

## Contrato de respuesta
Antes de programar, predice cada caso. JSON válido no comprueba precio ni pertinencia.
Completa `accept_recommendation` usando el validador compartido con el agente final. Añade dos casos: ID inventado y producto existente fuera del presupuesto. Explica por qué ninguna validación comprueba la veracidad de todo el texto.

## Structured Outputs: ejecutar el mismo contrato
El request real usa `text_format`; un rechazo o salida incompleta debe manejarse aparte. Sin API, inspecciona el schema y valida los casos anteriores. No se atribuye ningún resultado offline a un LLM.

## Selección y conversación
El usuario corrige «80» por «60». Conserva categoría y preferencia, cambia presupuesto y selecciona evidencia relevante. No copies todo el historial como memoria. Prueba la misma pregunta con estado viejo, actualizado y perdido; explica qué información recibe el modelo.

## Salida de sesión
Explica history vs state vs memory, schema vs verdad y autoridad vs contenido. Conserva dos contraejemplos. S3 resolverá cómo obtener evidencia actual sin pegar manualmente todo el catálogo.

## Comprobación final

Reinicia el kernel y ejecuta todo. Revisa cada mensaje PENDIENTE sin alterar los checks para que pasen. Anota qué comportamiento has comprobado y qué afirmaciones requieren revisión humana.
