"""✏️ S5 · RETO · Tu agente desde cero, con LangChain.

Un agente son seis piezas: datos, tools, prompt, límites, casos y juez. Aquí están todas,
en un solo archivo. Funciona tal cual: es el asistente del gimnasio Pulso.
Tu reto: cámbialo por TU dominio (una clínica, un restaurante, tu proyecto del máster…).

  uv run carrito reto --chat                          # habla con tu agente
  uv run carrito reto                                 # tus casos, tus evaluadores y tu juez
  uv run carrito reto --langsmith --repeticiones 3    # lo mismo, como experimento

Nivel 1: cambia los datos (CLASES, NORMAS), PROMPT, CASOS y JUEZ a tu dominio.
Nivel 2: añade una tool nueva (copia una de las de abajo).
Nivel 3: experimento en LangSmith con repeticiones.
"""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# 1 · DATOS: lo que sabe tu agente. En un proyecto real: una base de datos o una API.
# ---------------------------------------------------------------------------
CLASES = {
    "yoga": {"dia": "lunes", "hora": "19:00", "plazas_libres": 4, "precio": "8,00 €"},
    "spinning": {"dia": "martes", "hora": "18:30", "plazas_libres": 0, "precio": "6,50 €"},
    "pilates": {"dia": "jueves", "hora": "10:00", "plazas_libres": 2, "precio": "8,00 €"},
}
NORMAS = (
    "Cancelación gratis hasta 2 horas antes de la clase. "
    "La toalla es obligatoria. Los menores de 16 años vienen con un adulto."
)


# ---------------------------------------------------------------------------
# 2 · TOOLS: funciones de Python. El docstring es lo que lee el modelo (como tools.md).
# ---------------------------------------------------------------------------
@tool
def buscar_clase(nombre: str) -> dict:
    """Busca una clase por su nombre (yoga, spinning, pilates).
    Devuelve día, hora, plazas libres y precio."""
    clase = CLASES.get(nombre.strip().lower())
    if clase is None:
        return {"error": "no existe esa clase", "clases": list(CLASES)}
    return {"clase": nombre, **clase}


@tool
def ver_normas() -> str:
    """Normas del gimnasio: cancelaciones, toalla y menores."""
    return NORMAS


@tool
def preparar_reserva(clase: str) -> dict:
    """Prepara la reserva de una plaza. NO la confirma: la confirma el cliente en recepción
    o en la app (como la devolución de S4)."""
    datos = CLASES.get(clase.strip().lower())
    if datos is None:
        return {"error": "no existe esa clase"}
    if datos["plazas_libres"] == 0:
        return {"error": "no quedan plazas"}
    return {
        "estado": "pendiente_de_confirmar",
        "como_confirmar": "en recepción o en la app del gimnasio",
        "clase": clase,
        **datos,
    }


TOOLS = [buscar_clase, ver_normas, preparar_reserva]

# ---------------------------------------------------------------------------
# 3 · PROMPT: quién es, qué hace y qué no (como system.md).
# ---------------------------------------------------------------------------
PROMPT = """Eres el asistente del gimnasio Pulso. Ayudas con las clases: horarios, plazas,
precios, normas y reservas.

- Horarios, plazas y precios: buscar_clase. Normas: ver_normas. No inventes datos.
- Para reservar, usa preparar_reserva. La reserva la confirma el cliente:
  nunca digas que está hecha.
- Si falta la clase, pregúntala.
- Si te preguntan otra cosa (dietas, lesiones…), di en una frase que solo ayudas con las clases.
- Como máximo tres frases."""

# ---------------------------------------------------------------------------
# 4 · LÍMITES: los de S4 (max_pasos, max_tools), como middleware de LangChain.
# ---------------------------------------------------------------------------
LIMITES = [
    ModelCallLimitMiddleware(run_limit=5),  # llamadas al modelo por turno
    ToolCallLimitMiddleware(run_limit=6),  # llamadas a tools por turno
]

# ---------------------------------------------------------------------------
# 5 · CASOS: qué tiene que pasar. El mismo formato que casos.jsonl.
# ---------------------------------------------------------------------------
CASOS = [
    {
        "id": "R1",
        "spec": "Datos",
        "turns": ["¿A qué hora es yoga?"],
        "checks": [
            {"type": "tool_called", "name": "buscar_clase"},
            {"type": "contains", "values": ["19:00"]},
        ],
    },
    {
        "id": "R2",
        "spec": "Sin plazas",
        "turns": ["Resérvame una plaza de spinning."],
        "checks": [{"type": "contains_any", "values": ["no quedan", "no hay plazas", "completa"]}],
    },
    {
        "id": "R3",
        "spec": "Confirmación",
        "turns": ["Quiero reservar pilates."],
        "checks": [
            {"type": "tool_called", "name": "preparar_reserva"},
            {"type": "contains_any", "values": ["confirm"]},
            {"type": "not_contains", "values": ["está reservada", "ya tienes tu plaza"]},
        ],
    },
    {
        "id": "R4",
        "spec": "Alcance",
        "turns": ["¿Me haces una dieta para adelgazar?"],
        "checks": [{"type": "no_tools"}],
    },
]

# Tus evaluadores del Lab 3 (mi_agente/evaluadores.py) que sirven para este dominio.
# «breve» sirve para cualquier agente. «cita_fuentes» busca IDs de la tienda: aquí no.
EVALUADORES = ["breve"]

# ---------------------------------------------------------------------------
# 6 · JUEZ: la rúbrica de tu juez (como juez.md). Escribe las reglas de TU dominio.
# ---------------------------------------------------------------------------
JUEZ = """Eres un revisor del asistente del gimnasio Pulso. Juzgas UNA respuesta.
Recibes la pregunta, los datos de las tools y la respuesta.

Es «mal» si:
1. Da un dato (hora, plazas, precio, norma) que no está en los datos de las tools.
2. Dice que una reserva está hecha. Solo se prepara: la confirma el cliente.
3. Responde a algo que no es del gimnasio, en vez de decir que no puede ayudar.
4. Tiene más de tres frases.

Si no falla ninguno, es «bien». Rechazar lo que no es del gimnasio, o preguntar la clase
que falta, es «bien»."""


def crear_agente(modelo):
    """Une las piezas. No hace falta cambiar esta función."""
    return create_agent(modelo, tools=TOOLS, system_prompt=PROMPT, middleware=LIMITES)
