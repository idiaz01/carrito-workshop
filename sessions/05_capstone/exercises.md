# 5 · Building a Custom Agent
Build → Observe → Evaluate → Diagnose → Improve.
Configura nombre, objetivo, capacidades y límites del perfil; justifica qué decisión delegas y qué comprueba Python.
El perfil se utiliza en el mismo runtime de S3/S4. La mejora verificable afecta al contrato de aplicación; no se atribuye al modelo una mejora sintética.

Predice el resultado antes de ejecutar y anota tus observaciones.

## Skills: procedimiento y contexto
Inspecciona metadata y procedimiento de `examples/skills/return-help/SKILL.md`.
Compara prompt, Skill, tool, MCP server y host. Aquí la activación por palabras es deliberadamente simple. Activar la Skill no habilita tools ni confirma escrituras.

## Dataset y criterio de éxito
Antes de ejecutar: define expected behavior para resultado vacío, producto fuera de presupuesto, ID desconocido y tool denegada. Separa calidad de respuesta y invariantes del host. Escribe dos casos propios antes de modificar el sistema.

## Leer una traza
Localiza request, model response, tool result y response_contract. Distingue respuesta original del modelo de respuesta final de aplicación. Cuenta llamadas y fallos antes de proponer un cambio.

## Baseline y diagnóstico
Ejecuta los cuatro casos, clasifica primera causa y contrasta con la tool. El catálogo vacío es un resultado válido; el contrato `recommend` sin IDs es el fallo. Añade un caso donde hay datos pero una explicación textual miente: el checker básico no lo detecta.

## Cambiar una pieza del sistema
Completa un constructor de respuesta sobre productos observados. Preserva IDs, distingue `recommend`/`no_match` y solicita una preferencia alternativa cuando no hay resultados. Pásalo a `compare_contracts`: el mismo runtime ejecuta ambas versiones. Tu mejora no puede copiar outputs esperados ni tocar fixtures.

## Human review y judge
Etiqueta los ejemplos sin mirar la etiqueta del juez. Después inspecciona desacuerdo y evidencia. Tres ejemplos no calibran un judge. Los jueces también fallan; una rúbrica acotada y un humano permiten diagnosticar por qué.

## Regression run y observabilidad
Ejecuta los casos dev del backend, compara tus cuatro recorridos y revisa dos respuestas finales. Define dos casos propios ejecutables. Registra perfil, cambio, casos, límites y alcance de la evidencia. Un pase de tools/estado no garantiza que la respuesta sea correcta.

## Entrega
Perfil propio, criterio de éxito, dos casos propios, resultado antes/después, dos trazas comentadas y una limitación. Define qué monitorizarías online y cuándo pararías un despliegue. El trabajo termina cuando puedes explicar si funciona y mejorarlo con evidencia.

## Comprobación final

Reinicia el kernel y ejecuta todo. Revisa cada mensaje PENDIENTE sin alterar los checks para que pasen. Anota qué comportamiento has comprobado y qué afirmaciones requieren revisión humana.
