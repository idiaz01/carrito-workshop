# Datos del taller

Una tienda ficticia: 20 productos, 10 pedidos y seis políticas cortas. Escribimos los datos para este curso.
Fecha de referencia: **2026-09-20**. Los precios son enteros en céntimos. Cada pedido tiene un producto.

`create_store()` crea una SQLite en memoria. Cada demo y cada caso de evaluación empiezan con una base nueva.
`create_store("runtime/store.sqlite")` guarda la base en un archivo. Para reiniciarla, cierra la conexión y borra el archivo.

| Usuario | Pedidos | Notas |
|---|---|---|
| user1 | 101–107 | 104 admite devolución. 102 fuera de plazo, 103 no entregado, 106 personalizado, 107 digital |
| user2 | 108–110 | Pedidos ajenos para user1 |

El host fija la identidad. El modelo nunca elige el usuario ni confirma.
