"""Una posible solución de mi_agente/contexto.py (pasos 3 y 4 de la sesión 2).

Cada función tiene comentarios línea a línea. Léelos con el docstring de tu
mi_agente/contexto.py al lado: el contrato es el mismo.
"""

import json  # convierte listas y diccionarios de Python en texto JSON
import re  # expresiones regulares: buscar patrones dentro de un texto


# ---------------------------------------------------------------------------
# PASO 3 · Qué ve el modelo de cada resultado de una tool
# ---------------------------------------------------------------------------
def format_tool_result(name, result):
    # 1. Un error pasa sin cambios: el modelo tiene que verlo tal cual.
    #    Un error es un diccionario con la clave "error", por ejemplo
    #    {"error": "order_not_found"}.
    if isinstance(result, dict) and "error" in result:
        return json.dumps(result, ensure_ascii=False)

    # 2. Productos: de cada producto, solo 4 campos. El precio ya en euros.
    if name == "search_products":
        products = []
        for p in result:  # result es una lista de diccionarios, uno por producto
            euros = p["price_cents"] / 100  # 6990 -> 69.9
            texto = f"{euros:.2f}"  # 69.9 -> "69.90" (siempre dos decimales)
            precio = texto.replace(".", ",") + " €"  # "69.90" -> "69,90 €"
            products.append(
                {
                    "product_id": p["product_id"],
                    "name": p["name"],
                    "precio": precio,
                    "description": p["description"],
                }
            )
        # El modelo solo recibe texto: json.dumps convierte la lista en texto JSON.
        # ensure_ascii=False deja las tildes y el € como son (y gasta menos tokens).
        return json.dumps(products, ensure_ascii=False)

    # 3. Políticas: como mucho los dos primeros documentos (los más relevantes,
    #    porque la búsqueda ya los ordena). result[:2] = los dos primeros.
    if name == "search_policies":
        documents = []
        for d in result[:2]:
            documents.append({"source_id": d["source_id"], "text": d["text"]})
        return json.dumps(documents, ensure_ascii=False)

    # 4. El resto de tools (get_order, request_return): sin cambios.
    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# PASO 4 · Memoria: escribir el estado y comprimir el historial
# ---------------------------------------------------------------------------
def update_state(state, user_message):
    # Copia del estado anterior: nunca modificamos el que nos llega.
    new = dict(state)

    # Busca un importe: uno o más dígitos, opcionalmente con decimales,
    # seguido de "€" o "euros". Ejemplos: "80 €", "79,90 euros".
    amount = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:€|euros)", user_message)
    if amount:
        numero = amount.group(1)  # el texto entre los primeros paréntesis: "80"
        new["presupuesto_eur"] = float(numero.replace(",", "."))  # "79,90" -> 79.9

    # Busca "me llamo X" o "soy X", con X empezando por mayúscula.
    name = re.search(r"(?:me llamo|soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)", user_message)
    if name:
        new["nombre"] = name.group(1)

    return new


def build_history(turns, state, max_turns=2):
    messages = []

    # 1. Si hay estado, va primero, en un mensaje de sistema.
    #    {"presupuesto_eur": 80.0, "nombre": "Ana"} -> "presupuesto_eur=80.0; nombre=Ana"
    if state:
        partes = [f"{clave}={valor}" for clave, valor in state.items()]
        resumen = "; ".join(partes)
        messages.append({"role": "system", "content": f"Estado de la conversación: {resumen}"})

    # 2. Solo los últimos max_turns turnos. turns[-2:] = los dos últimos.
    #    De cada turno: la pregunta del cliente y la respuesta. Sin resultados de tools.
    for turn in turns[-max_turns:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})

    return messages
