# 5 · Guía de la sesión

Qué observar en cada sección del [notebook](starter.ipynb). Ciclo: Build → Observe → Evaluate → Diagnose → Improve.

| Sección | Qué observar |
|---|---|
| Skills: procedimiento y contexto | Activar la Skill no habilita tools ni confirma escrituras |
| Dataset y criterio de éxito | Definimos el comportamiento esperado antes de cambiar el sistema |
| Leer una traza | Request, respuesta del modelo, resultado de tool y `response_contract` |
| Baseline y diagnóstico | Un catálogo vacío es válido. El fallo es `recommend` sin IDs |
| Cambiar una pieza del sistema | `improved_response` distingue `recommend` y `no_match`. Compara antes y después |
| Human review y judge | Etiqueta primero. Después compara con el juez. Tres ejemplos no calibran un juez |
| Regression run y observabilidad | Backend (16 casos) y contrato se informan por separado |

## Debes poder explicar

- El perfil, el criterio de éxito y el resultado antes/después.
- Dos trazas comentadas y una limitación.
- Qué monitorizarías en producción y cuándo pararías un despliegue.

Los checks `OK` comprueban el código. No miden la calidad del modelo.
