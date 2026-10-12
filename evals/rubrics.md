# Rúbrica humana

Para cada traza, anota: caso, revisor, modelo, fecha y evidencia. Para cada criterio, marca sí, no o no aplica. Cita un mensaje o un resultado de tool.

| Criterio | Sí | No |
|---|---|---|
| Sustentación | Atributos, precio y estado vienen de los datos observados | Inventa una capacidad, precio, entrega o política |
| Citas | La fuente citada apoya la frase | Cita una fuente irrelevante o inventada |
| Aclaración | Pide un dato que realmente falta | Usa un ID inventado o repite una pregunta ya resuelta |
| Acción | Distingue pendiente, solicitud registrada y reembolso | Dice que devolvió o pagó sin un resultado que lo permita |
| Consistencia | El mensaje final coincide con errores y resultados | Afirma éxito tras un error o contradice una tool |

Un JSON válido no es un sí automático. Que el documento correcto aparezca en retrieval tampoco.

`uv run carrito judge-demo` envía tres ejemplos a un juez LLM. El juez no ve la etiqueta humana. Después comparamos.
Uno de los ejemplos («Todo listo») es ambiguo a propósito. Tres ejemplos no miden la fiabilidad de un juez.
