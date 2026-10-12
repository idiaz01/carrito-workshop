# 2 · Guía de la sesión

Qué observar en cada sección del [notebook](starter.ipynb). Método: predice → ejecuta → compara → explica.

| Sección | Qué observar |
|---|---|
| Anatomía y autoridad | Instrucciones, petición, estado y evidencia. `source_id` permite citar, no da autoridad |
| Experimento controlado | Solo cambia el presupuesto de evidencia. El anuncio marcado como relevante entra: seleccionar contexto no neutraliza la prompt injection |
| Contrato de respuesta | Un JSON válido no comprueba precio ni pertinencia. Mira el ID inventado y el producto fuera de presupuesto |
| Structured Outputs | Tres variantes con el mismo modelo y schema. ¿Qué cambia en la respuesta? ¿Qué pasa si `output_parsed` es `None`? |
| Selección y conversación | La corrección 80 → 60 cambia solo el presupuesto. Compara estado anterior, actualizado y perdido |

## Debes poder explicar

- History, state y memory.
- Schema y verdad.
- Autoridad y contenido.

Los checks `OK` comprueban el código. No miden la calidad del modelo.
