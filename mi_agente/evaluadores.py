"""Tus evaluadores de código · sesión 5.

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
    """✏️ S5 · LAB 3 · RESP-1: si el agente usó alguna tool, la respuesta cita un ID.

    Recibe:
      respuesta    = el texto final del agente, por ejemplo "Te recomiendo P001."
      herramientas = las tools que usó, por ejemplo ["search_products"]

    Reglas:
      1. Sin tools (por ejemplo, rechaza un poema): score 1. No hay nada que citar.
      2. Con tools y al menos un ID en la respuesta: score 1.
      3. Con tools y sin ningún ID: score 0.

    Ejemplos:
      cita_fuentes("Te recomiendo P001.", ["search_products"])
        → {"score": 1, "comment": "cita ['P001']"}
      cita_fuentes("Te recomiendo los Nube.", ["search_products"])
        → {"score": 0, "comment": "usa tools, pero no cita ningún ID"}

    Python útil: re.findall(IDS, respuesta) devuelve la lista de IDs del texto.
    """
    raise NotImplementedError  # ← borra esta línea y escribe tu código


def breve(respuesta, herramientas):
    """✏️ S5 · LAB 3 · RESP-3: como máximo cuatro frases.

    Reglas:
      1. Cuenta las frases: len(re.findall(FIN_DE_FRASE, respuesta)).
      2. Cuatro o menos: score 1. Más de cuatro: score 0.
      3. El comment dice cuántas frases hay, por ejemplo "5 frases (máximo 4)".

    Ejemplos:
      breve("Una. Dos. Tres. Cuatro.", [])        → {"score": 1, "comment": "4 frases"}
      breve("Una. Dos. Tres. Cuatro. Cinco.", []) → {"score": 0, "comment": "5 frases (máximo 4)"}
    """
    raise NotImplementedError  # ← borra esta línea y escribe tu código
