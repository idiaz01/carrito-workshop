"""Una posible solución de mi_agente/evaluadores.py (sesión 5, lab 3).

Un evaluador recibe la respuesta final del agente y la lista de tools que usó.
Devuelve {"score": 1 o 0, "comment": "por qué"}. LangSmith guarda el score de cada caso.

Comprueba tu código: uv run pytest tests/test_mi_agente.py --runxfail -q -k s5
"""

import re

# Los evaluadores que se usan en los experimentos (por nombre).
EVALUADORES = ["cita_fuentes", "breve"]

# Un ID de la tienda: P001, POL-DEV, AYU-ENV o un número de pedido de 3 cifras (104).
IDS = r"P\d{3}|POL-[A-Z]{3}|AYU-[A-Z]{3}|\b\d{3}\b"

# El final de una frase: . ? o ! seguido de un espacio o del final del texto.
FIN_DE_FRASE = r"[.!?](\s|$)"


def cita_fuentes(respuesta, herramientas):
    """RESP-1: si el agente usó alguna tool, la respuesta cita un ID."""
    if not herramientas:  # regla 1: sin tools, no hay nada que citar
        return {"score": 1, "comment": "sin tools: no hay nada que citar"}
    ids = re.findall(IDS, respuesta)
    if ids:  # regla 2: al menos un ID
        return {"score": 1, "comment": f"cita {ids}"}
    return {"score": 0, "comment": "usa tools, pero no cita ningún ID"}  # regla 3


def breve(respuesta, herramientas):
    """RESP-3: como máximo cuatro frases."""
    frases = len(re.findall(FIN_DE_FRASE, respuesta))
    if frases <= 4:
        return {"score": 1, "comment": f"{frases} frases"}
    return {"score": 0, "comment": f"{frases} frases (máximo 4)"}
