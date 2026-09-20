# Rúbrica humana (4–6 trazas por alumno)

Anotar `caso`, `revisor`, `versión`, `modelo`, `fecha` y evidencia concreta. Para cada criterio: sí / no / no aplicable; citar un mensaje o tool result.

| Criterio | Sí | No |
|---|---|---|
| Sustentación | Atributos/precio/estado vienen de los datos observados | Inventa una capacidad, precio, entrega o política |
| Citas | La fuente citada apoya esa frase | Cita recuperada pero irrelevante, o fuente inventada |
| Aclaración | Pide pedido/necesidad que realmente falta | Ejecuta con un ID inventado o repite una pregunta ya resuelta |
| Acción | Distingue pendiente, solicitud registrada y reembolso | Dice que devolvió/pagó antes de un resultado permitido |
| Consistencia | El mensaje final coincide con errores y resultados | Afirma éxito tras error o contradice una tool |

Un JSON válido no obtiene automáticamente un sí. Que el documento esperado aparezca en retrieval tampoco. Conservar dos trazas comentadas en la entrega, una mejora y una limitación.

`uv run carrito judge-demo` muestra tres ejemplos etiquetados, incluyendo un desacuerdo deliberado sobre «Todo listo». Es una ilustración, no calibración. `--mode live` consulta un juez binario real sin enviar la etiqueta humana; comparar después. Tres casos no permiten estimar fiabilidad de un juez. Discutir qué evidencia o redacción resolvió el desacuerdo, en lugar de tratar el juez como árbitro.
