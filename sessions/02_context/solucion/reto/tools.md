## search_products
Busca productos del catálogo por palabras clave. Para productos, precios o características. max_price_eur: presupuesto máximo en euros (null si no lo hay). Lista vacía = ningún producto cumple.

## get_order
Lee un pedido del cliente activo por su número (order_id, por ejemplo "104"). Úsala siempre que el cliente dé un número de pedido, también si pregunta si puede devolverlo. Devuelve estado y fecha de entrega. {"error": "order_not_found"}: no existe o no es de este cliente; no des más detalles.

## search_policies
Busca en las políticas de la tienda: devoluciones, envíos, garantías, cancelaciones y privacidad. Devuelve documentos con source_id (por ejemplo POL-DEV): cítalo.

## request_return
Prepara una solicitud de devolución. Solo cuando el cliente pide devolver un pedido; NO si solo pregunta si puede. Devuelve confirmation_required: pide al cliente que confirme y para. No es una devolución completada.
