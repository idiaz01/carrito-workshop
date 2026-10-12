# 1 · Guía de la sesión

Qué observar en cada sección del [notebook](starter.ipynb). Método: predice → ejecuta → compara → explica.

| Sección | Qué observar |
|---|---|
| Preparación | La celda comprueba la clave. Debe mostrar `'api': 'OK'` |
| Experimento 1 · Misma pregunta, tres respuestas | El modelo sortea tokens: las respuestas cambian. `usage` da los tokens y el coste |
| Experimento 2 · Sin datos y con datos | Sin datos, inventa o reconoce que no sabe. Con datos, responde 69,90 € |
| Experimento 3 · El modelo no tiene memoria | Cada llamada empieza de cero. Reenviando el historial, «recuerda» |
| Contexto contrafactual | Con 89,90 €, ¿el modelo cambia la conclusión? |
| Capacidades, límites y entrada multimodal | ¿Qué se ve en la imagen y qué hay que consultar? |
| Modelo, aplicación, workflow y agente | ¿Quién debe comprobar un precio? |
| Primera aplicación | `build_messages`: dos roles, cinco fichas, una regla para datos ausentes |
| Primera evaluación: cinco casos | Aplica el criterio de la tabla a cada respuesta real |

## Debes poder explicar

- Qué hace un LLM: predecir el siguiente token y sortear.
- Por qué la misma pregunta da respuestas distintas.
- Por qué sin datos puede inventar, y con datos responde bien.
- Por qué el modelo no recuerda nada entre llamadas.
- Qué caso de la evaluación falló y por qué.

Los checks `OK` comprueban el código. No miden la calidad del modelo.
