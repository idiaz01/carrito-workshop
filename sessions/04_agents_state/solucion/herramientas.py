"""Una posible solución de mi_agente/herramientas.py (sesión 3, lab 3).

El modelo decide CUÁNDO usar una tool. El código decide QUÉ devuelve.
Las cuentas con fechas las hace el código: el código no se equivoca al sumar días.

Comprueba tu código: uv run pytest tests/test_mi_agente.py --runxfail -q -k s3
"""

from datetime import date, timedelta


def plazo_devolucion(pedido, producto, hoy):
    """✏️ S3 · PASO 3 · ¿Hasta qué día se puede devolver este pedido?

    La aplicación ya ha leído el pedido del cliente activo (los permisos los pone ella).
    Tú recibes:
      pedido   = {"order_id": "104", "status": "delivered", "delivered_at": "2026-09-12", ...}
      producto = {"product_id": "P001", "name": "Auriculares Nube", "returnable": 1, ...}
      hoy      = date(2026, 9, 20)   (la fecha de la tienda en el taller)

    Devuelve un dict con estas claves:
      order_id, se_puede_devolver (True/False), motivo,
      fecha_limite ("2026-10-12" o None), dias_restantes (un número o None)

    Reglas (POL-DEV y POL-EXC):
      1. Si el pedido no está entregado (status distinto de "delivered"): no se puede.
         motivo "no_entregado".
      2. Si el producto no admite devolución (returnable es 0): no se puede. motivo "POL-EXC".
      3. fecha_limite = día de entrega + 30 días.
         Si hoy es después de fecha_limite: no se puede. motivo "plazo_vencido".
      4. Si no: se puede. motivo "POL-DEV".

    """
    respuesta = {
        "order_id": pedido["order_id"],
        "se_puede_devolver": False,
        "fecha_limite": None,
        "dias_restantes": None,
    }

    # Regla 1
    if pedido["status"] != "delivered":  # solo pedidos entregados
        respuesta["motivo"] = "no_entregado"
        return respuesta

    # Regla 2
    if not producto["returnable"]:  # 0 = no admite devolución (POL-EXC)
        respuesta["motivo"] = "POL-EXC"
        return respuesta

    # Regla 3: "2026-09-12" (texto) → date(2026, 9, 12) (fecha)
    entrega = date.fromisoformat(pedido["delivered_at"])
    fecha_limite = entrega + timedelta(days=30)  # POL-DEV: 30 días naturales
    dias_restantes = (fecha_limite - hoy).days

    respuesta["fecha_limite"] = fecha_limite.isoformat()
    respuesta["dias_restantes"] = dias_restantes
    if dias_restantes < 0:  # el día 30 todavía vale (0 días restantes)
        respuesta["motivo"] = "plazo_vencido"
        return respuesta

    # Regla 4
    respuesta["se_puede_devolver"] = True
    respuesta["motivo"] = "POL-DEV"
    return respuesta
