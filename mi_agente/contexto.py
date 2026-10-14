"""Tu agente · contexto. Pasos 3 y 4 de la sesión 2.

Completa las funciones marcadas con ✏️.
Mientras una función lanza NotImplementedError, la aplicación usa un comportamiento por
defecto (el resultado completo de la tool o todo el historial) y el agente sigue funcionando.

Comprueba tu código: uv run pytest tests/test_mi_agente.py --runxfail -q
"""


def format_tool_result(name, result):
    """✏️ PASO 3 · Lo que devuelve una tool también es contexto.

    Recibe el nombre de la tool y su resultado completo (un dict o una lista de dicts).
    Devuelve el texto que verá el modelo (un str).

    Contrato:
    - Un error (un dict con la clave "error") pasa sin cambios.
    - search_products: para cada producto, solo product_id, name, el precio en euros con
      coma decimal ("69,90 €") y description. Nada de price_cents, category ni returnable.
    - search_policies: como mucho los 2 primeros documentos, con source_id y text.
    - Las demás tools: el resultado sin cambios.

    Ejemplo de resultado de search_products:
        [{"product_id": "P001", "name": "Auriculares Nube", "category": "audio",
          "price_cents": 6990, "description": "auriculares inalámbricos ...", "returnable": 1}]
    """
    ### TU CÓDIGO AQUÍ (S2 · Paso 3)
    raise NotImplementedError


def update_state(state, user_message):
    """✏️ PASO 4a · Escribir: guarda fuera del historial lo que decide la respuesta.

    Recibe el estado anterior (un dict) y el mensaje nuevo del cliente (un str).
    Devuelve un estado NUEVO (un dict). No modifiques `state`.

    Contrato:
    - Si el mensaje dice un importe en euros ("80 €", "80 euros"), guarda
      state["presupuesto_eur"] = 80 (un número).
    - Si el mensaje dice "me llamo X" o "soy X", guarda state["nombre"] = "X".
    - Lo que ya estaba en el estado se conserva.

    Pista: el módulo `re` de Python. r"(\\d+(?:[.,]\\d+)?)\\s*(?:€|euros)" encuentra "80 €".
    """
    ### TU CÓDIGO AQUÍ (S2 · Paso 4a)
    raise NotImplementedError


def build_history(turns, state, max_turns=2):
    """✏️ PASO 4b · Comprimir: decide qué parte de la conversación vuelve a entrar.

    turns: los turnos anteriores, del más antiguo al más reciente. Cada turno es
        {"user": "texto del cliente", "assistant": "respuesta", "tools": [...]}
    state: el diccionario de update_state.

    Devuelve una lista de mensajes {"role": ..., "content": ...}:
    - Si el estado no está vacío: primero un mensaje "system" con el estado,
      por ejemplo "Estado de la conversación: presupuesto_eur=80; nombre=Ana".
    - Después, solo los últimos `max_turns` turnos: un mensaje "user" y un mensaje
      "assistant" por turno. Sin los resultados de las tools.
    """
    ### TU CÓDIGO AQUÍ (S2 · Paso 4b)
    raise NotImplementedError
