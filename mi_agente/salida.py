"""Tu salida estructurada · sesión 4.

Con Structured Outputs, la API obliga al modelo a responder con esta forma (un JSON).
Así tu código puede revisar la respuesta ANTES de enseñarla al cliente.

Comprueba tu código: uv run pytest tests/test_mi_agente.py --runxfail -q -k s4
"""

from pydantic import BaseModel, Field


class Respuesta(BaseModel):
    """La forma de la respuesta final de tu agente. El modelo lee las descripciones."""

    texto: str = Field(description="La respuesta para el cliente. Como máximo cuatro frases.")
    fuentes: list[str] = Field(
        description="Los IDs exactos que citas: P001, POL-DEV, AYU-ENV o el número de pedido (104)."
    )
    pide_confirmacion: bool = Field(description="True si pides al cliente que confirme algo.")


def revisar(respuesta, vistos):
    """✏️ S4 · LAB 3 · Guardrail: revisa la respuesta antes de enseñarla.

    Recibe:
      respuesta = Respuesta(texto="...", fuentes=["P001"], pide_confirmacion=False)
      vistos    = los IDs que salieron de las tools en este turno, por ejemplo
                  {"P001", "POL-DEV", "104", "pedido 104"}

    Devuelve una lista de problemas (textos). Lista vacía = la respuesta está bien.
    Si hay problemas, la aplicación pide al modelo UNA corrección.

    Reglas:
      1. Cada fuente citada tiene que estar en vistos. Si no, el agente la ha inventado.
      2. El texto tiene como máximo 600 caracteres (RESP-3).
      3. Si pide_confirmacion es True, el texto tiene que decir "confirm" (confirma, confirmación…).

    Cómo hacerlo: borra la línea `raise NotImplementedError` y rellena los ___ de abajo.
    """
    raise NotImplementedError  # ← borra esta línea

    problemas = []

    # Regla 1
    for fuente in respuesta.fuentes:
        if fuente not in ___:
            problemas.append(f"Citas {fuente}, pero no sale de ninguna tool. No la cites.")

    # Regla 2: len(texto) es el número de caracteres
    if len(respuesta.texto) > ___:
        problemas.append("La respuesta es demasiado larga. Máximo cuatro frases.")

    # Regla 3
    if respuesta.___ and "confirm" not in respuesta.texto.lower():
        problemas.append("Pides confirmación, pero el texto no se lo dice al cliente.")

    return problemas
