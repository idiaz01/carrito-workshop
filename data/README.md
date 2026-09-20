# Datos originales del taller

Una tienda ficticia, 20 productos, 10 pedidos y seis políticas breves. Datos sintéticos escritos para este curso; no copiados de Cartwheel. Fecha de referencia: **2026-09-20**. Precios enteros en céntimos. Cada pedido contiene un producto para reducir carga conceptual.

`create_store()` prepara SQLite en memoria. Cada demo y caso de evaluación parte de una base nueva. `create_store("runtime/store.sqlite")` permite persistencia local; si ya existe, conserva solicitudes. Para reiniciar una base persistida, cierra la conexión y elimina ese archivo local.

Pedidos user1: 101–107. Pedidos user2: 108–110. 104 admite devolución; 102 está fuera de plazo, 103 no entregado, 106 personalizado y 107 digital. La identidad la fija el host. El modelo nunca elige usuario ni confirmación.
