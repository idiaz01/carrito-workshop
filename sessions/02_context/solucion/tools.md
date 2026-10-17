## search_products
Busca productos del catálogo por palabras clave. Úsala para cualquier pregunta sobre productos, precios o características. max_price_eur es el presupuesto máximo en euros (null si el cliente no lo dice). Devuelve una lista de productos; price_cents está en céntimos (6990 = 69,90 €). Una lista vacía significa que no hay productos que cumplan.

## get_order
Lee un pedido del cliente activo por su número (order_id, por ejemplo "104"). Úsala solo si el cliente da el número; si no lo da, pregúntalo. Devuelve estado y fecha de entrega. {"error": "order_not_found"} significa que no existe o que no es de este cliente: no des más detalles.

## search_policies
Busca en las políticas de la tienda: devoluciones, envíos, garantías, cancelaciones y privacidad. Úsala para plazos y condiciones. Devuelve documentos con source_id (por ejemplo POL-DEV): cítalo.

## request_return
Prepara una solicitud de devolución de un pedido entregado. Úsala solo cuando el cliente pide devolver un pedido de forma explícita y da un motivo; NO la uses si solo pregunta si puede devolver. Devuelve confirmation_required: la aplicación pide la confirmación al cliente. Nunca significa devolución completada.
