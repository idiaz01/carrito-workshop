# 4 · Guía de la sesión

Qué observar en cada sección del [notebook](starter.ipynb). Método: predice → ejecuta → compara → explica.

| Sección | Qué observar |
|---|---|
| Configurar el loop real | Tres recorridos: el modelo real, un loop y una tool no permitida. Los dos fallos usan un modelo guionizado; los controles del host son reales |
| Estado y recuperación | Las preferencias sobreviven. La ejecución y la confirmación pendiente no |
| Recovery + confirmación | Un error transitorio se repite. Un error permanente no. Una escritura confirmada crea una sola solicitud |
| Traces y decisiones de diseño | Primera divergencia, control que la limita y dato para el diagnóstico |

## Debes poder explicar

- Los límites del perfil.
- Dos decisiones workflow frente a agent.
- Una traza diagnosticada.

Los checks `OK` comprueban el código. No miden la calidad del modelo.
