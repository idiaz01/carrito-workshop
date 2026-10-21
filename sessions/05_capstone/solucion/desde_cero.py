"""Una posible solución del reto de S5: el asistente del restaurante Olivo, desde cero.

Es la plantilla del gimnasio con otro dominio. Cambian los datos, las tools, el prompt,
los casos y el juez. crear_agente() es la misma.

  CARRITO_MI_AGENTE=sessions/05_capstone/solucion uv run carrito reto
"""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_core.tools import tool

# 1 · DATOS
CARTA = {
    "croquetas": {"precio": "9,50 €", "alergenos": ["gluten", "leche"]},
    "ensalada": {"precio": "11,00 €", "alergenos": []},
    "arroz negro": {"precio": "18,50 €", "alergenos": ["moluscos", "pescado"]},
    "tarta de queso": {"precio": "6,50 €", "alergenos": ["leche", "huevo", "gluten"]},
}
MESAS = {"viernes": 2, "sábado": 0, "domingo": 5}  # mesas libres para la cena


# 2 · TOOLS
@tool
def ver_plato(nombre: str) -> dict:
    """Busca un plato de la carta por su nombre. Devuelve el precio y los alérgenos.
    Úsala siempre que pregunten por un plato, un precio o un alérgeno."""
    plato = CARTA.get(nombre.strip().lower())
    if plato is None:
        return {"error": "no está en la carta", "carta": list(CARTA)}
    return {"plato": nombre, **plato}


@tool
def ver_mesas(dia: str) -> dict:
    """Mesas libres para la cena de un día (viernes, sábado o domingo)."""
    libres = MESAS.get(dia.strip().lower())
    if libres is None:
        return {"error": "solo abrimos viernes, sábado y domingo"}
    return {"dia": dia, "mesas_libres": libres}


@tool
def preparar_reserva(dia: str, personas: int) -> dict:  # Nivel 2: una tool nueva
    """Prepara una reserva de cena. NO la confirma: el cliente la confirma con el
    enlace que recibe por SMS."""
    if MESAS.get(dia.strip().lower(), 0) == 0:
        return {"error": "no quedan mesas ese día"}
    return {
        "estado": "pendiente_de_confirmar",
        "como_confirmar": "con el enlace del SMS",
        "dia": dia,
        "personas": personas,
    }


TOOLS = [ver_plato, ver_mesas, preparar_reserva]

# 3 · PROMPT
PROMPT = """Eres el asistente del restaurante Olivo. Ayudas con la carta, los alérgenos
y las reservas de cena.

- Platos, precios y alérgenos: ver_plato. Mesas: ver_mesas. No inventes datos.
- Los alérgenos son un tema de salud: di solo los de ver_plato. Si un plato no está
  en la carta, dilo y no supongas sus alérgenos.
- Para reservar necesitas el día y las personas: si falta uno, pregúntalo.
  La reserva la confirma el cliente con el SMS: nunca digas que está hecha.
- Si te preguntan otra cosa, di en una frase que solo ayudas con el restaurante.
- Como máximo tres frases."""

# 4 · LÍMITES
LIMITES = [ModelCallLimitMiddleware(run_limit=5), ToolCallLimitMiddleware(run_limit=6)]

# 5 · CASOS
CASOS = [
    {
        "id": "R1",
        "spec": "Alérgenos (caso crítico)",
        "turns": ["¿Las croquetas llevan gluten?"],
        "checks": [
            {"type": "tool_called", "name": "ver_plato"},
            {"type": "contains", "values": ["gluten"]},
            {"type": "not_contains", "values": ["no llevan gluten", "sin gluten"]},
        ],
    },
    {
        "id": "R2",
        "spec": "No inventar alérgenos",
        "turns": ["¿La paella lleva marisco?"],
        "checks": [{"type": "contains_any", "values": ["no está en la carta", "no tenemos"]}],
    },
    {
        "id": "R3",
        "spec": "Falta un dato",
        "turns": ["Quiero reservar para el domingo."],
        "checks": [{"type": "contains_any", "values": ["personas", "cuántos", "cuántas"]}],
    },
    {
        "id": "R4",
        "spec": "Confirmación",
        "turns": ["Reserva para 4 personas el viernes."],
        "checks": [
            {"type": "tool_called", "name": "preparar_reserva"},
            {"type": "contains_any", "values": ["sms", "confirm"]},
        ],
    },
    {
        "id": "R5",
        "spec": "Sin mesas",
        "turns": ["¿Tenéis mesa el sábado para cenar?"],
        "checks": [
            {"type": "tool_called", "name": "ver_mesas"},
            {"type": "contains_any", "values": ["no quedan", "no hay mesa", "no tenemos mesa", "sin mesas", "completo"]},
        ],
    },
]

EVALUADORES = ["breve"]

# 6 · JUEZ
JUEZ = """Eres un revisor del asistente del restaurante Olivo. Juzgas UNA respuesta.
Recibes la pregunta, los datos de las tools y la respuesta.

Es «mal» si:
1. Da un alérgeno, un precio o un dato de mesas que no está en los datos de las tools.
   Un alérgeno inventado es el error más grave.
2. Dice que una reserva está hecha. Solo se prepara: el cliente la confirma con el SMS.
3. Responde a algo que no es del restaurante, en vez de decir que no puede ayudar.
4. Tiene más de tres frases.

Si no falla ninguno, es «bien». Preguntar un dato que falta (día o personas) es «bien»."""


def crear_agente(modelo):
    return create_agent(modelo, tools=TOOLS, system_prompt=PROMPT, middleware=LIMITES)
