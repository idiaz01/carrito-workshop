# 4 · Designing Agents + Agentic Workflows
Ahora configuramos el agente real de Carrito: objetivos, capacidades y límites.
El checkpoint de preferencias no es una reanudación automática de ejecución.

Predice el resultado antes de ejecutar y anota tus observaciones.

## Configurar el loop real
Configura un perfil de lectura. Predice tres recorridos: final normal, tool no permitida y límite de pasos. Cada decisión del fixture está preescrita; el host ejecuta controles reales. Cambiar el prompt no concede permisos.

## Estado y recuperación: qué sobrevive
Guardamos preferencias explícitas, destruimos el objeto en memoria y lo recuperamos.
Esto NO conserva un programa en ejecución ni su call stack. Para retomar una acción hay que comprobar estado de negocio, identidad y confirmación de nuevo.

## Recovery + confirmación
Clasifica errores permanentes y transitorios. Completa una operación de lectura que falle una vez y después consulte SQLite. Compárala con pedido ajeno: ese error no debe reintentarse. Después confirma el payload exacto y repite la escritura; debe existir una sola solicitud.

## Traces y decisiones de diseño
Inspecciona un recorrido correcto y el loop detenido. Señala la primera divergencia, el control que la limita y el dato que necesitas para diagnosticarlo. Un timeout y una denegación necesitan respuestas distintas. No confundir latencia de fixture con rendimiento real del LLM.

## Salida de sesión
Entrega límites del perfil, dos decisiones workflow/agent y una traza diagnosticada. S5 usa el mismo runtime para configurar, evaluar y mejorar una aplicación completa.

## Comprobación final

Reinicia el kernel y ejecuta todo. Revisa cada mensaje PENDIENTE sin alterar los checks para que pasen. Anota qué comportamiento has comprobado y qué afirmaciones requieren revisión humana.
