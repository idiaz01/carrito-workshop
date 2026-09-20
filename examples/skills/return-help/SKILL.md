---
name: return-help
description: Procedimiento original para ayudar con una devolución de esta tienda ficticia.
---

1. Si no hay número de pedido, pide aclaración.
2. Consulta `get_order`; si falla, no reveles si pertenece a otra persona.
3. Recupera `POL-DEV` y `POL-EXC` mediante `search_policies`.
4. Explica plazo, excepciones y qué información falta. Pide un motivo concreto.
5. Ejecuta `request_return` para preparar pedido y motivo. Muestra ese payload y pide confirmación al cliente.
6. La confirmación se realiza en el host. Nunca inventes un permiso ni un argumento `confirmed`.
7. Solo tras `requested` puedes decir «solicitud registrada». No digas «reembolso realizado».

Una Skill añade instrucciones al contexto; no ejecuta funciones ni sustituye las comprobaciones Python.
