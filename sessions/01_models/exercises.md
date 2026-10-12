# 1 · Guía de la sesión

Qué observar en cada sección del [notebook](starter.ipynb). Método: predice → ejecuta → compara → explica.

| Sección | Qué observar |
|---|---|
| Qué vamos a observar | La primera celda comprueba la clave. Debe mostrar `'api': 'OK'` |
| Una historia de representaciones y objetivos | Capacidad aprendida, evidencia en el contexto y acceso a tools son cosas distintas |
| Demo 1: un token no es necesariamente una palabra | Compara palabras y tokens en espacios, cifras y puntuación |
| Demo 2: distribución del siguiente token | El prefijo cambia la distribución. La tabla del toy no cambia |
| Transformer | La máscara causal pone a cero las posiciones posteriores |
| Qué se aprende y qué permanece fijo | En inferencia, los parámetros no cambian. Pegar datos no entrena |
| Inferencia y decoding | T cambia la forma de la distribución, no el orden. T no controla las alucinaciones |
| Contexto contrafactual | Con 89,90 €, ¿el modelo cambia la conclusión? |
| Capacidades, límites y entrada multimodal | ¿Qué se ve en la imagen y qué hay que consultar? |
| Modelo, aplicación, workflow y agente | ¿Quién debe comprobar un precio? |
| Primera aplicación | `build_messages`: dos roles, cinco fichas, una regla para datos ausentes |
| Primera evaluación: cinco casos | Aplica el criterio de la tabla a cada respuesta real |

## Debes poder explicar

- Token frente a palabra.
- Generación paso a paso.
- Parámetros frente a contexto.
- Por qué cambiar T no demuestra que una respuesta sea correcta.
- Qué caso de la evaluación falló y por qué.

Los checks `OK` comprueban el código. No miden la calidad del modelo.
