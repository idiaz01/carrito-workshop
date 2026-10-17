"""Tus evaluadores de código · sesión 5.

Un evaluador recibe la respuesta final del agente y la lista de tools que usó.
Devuelve {"score": 1 o 0, "comment": "por qué"}. LangSmith guarda el score de cada caso.

Comprueba tu código: uv run pytest tests/test_mi_agente.py --runxfail -q -k s5
"""

import re

# Los evaluadores que se usan en los experimentos (por nombre).
EVALUADORES = ["cita_fuentes", "breve"]


def cita_fuentes(respuesta, herramientas):
    """✏️ S5 · LAB 3 · RESP-1: si el agente usó alguna tool, la respuesta cita un ID.

    IDs válidos: P001, POL-DEV, AYU-ENV o un número de pedido de 3 cifras (104).
    Si no usó ninguna tool (por ejemplo, rechaza un poema), pasa: no hay nada que citar.

    Cómo hacerlo: borra la línea `raise NotImplementedError` y rellena los ___.
    """
    raise NotImplementedError  # ← borra esta línea

    if not herramientas:
        return {"score": ___, "comment": "sin tools: no hay nada que citar"}

    ids = re.findall(r"P\d{3}|POL-[A-Z]{3}|AYU-[A-Z]{3}|\b\d{3}\b", respuesta)
    if len(ids) > ___:
        return {"score": 1, "comment": f"cita {ids}"}
    return {"score": 0, "comment": "usa tools, pero no cita ningún ID"}


def breve(respuesta, herramientas):
    """✏️ S5 · LAB 3 · RESP-3: como máximo cuatro frases.

    Una frase termina en . ? o ! seguido de un espacio o del final del texto.

    Cómo hacerlo: borra la línea `raise NotImplementedError` y rellena los ___.
    """
    raise NotImplementedError  # ← borra esta línea

    frases = len(re.findall(r"[.!?](\s|$)", respuesta))
    if frases <= ___:
        return {"score": 1, "comment": f"{frases} frases"}
    return {"score": ___, "comment": f"{frases} frases (máximo 4)"}
