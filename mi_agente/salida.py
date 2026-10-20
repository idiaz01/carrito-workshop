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
    Si hay problemas, la aplicación se los manda al modelo y le pide UNA corrección.
    Escribe cada problema para el modelo: qué está mal y qué tiene que hacer.

    Reglas:
      1. Cada fuente citada tiene que estar en vistos. Si no, el agente la ha inventado.
      2. El texto tiene como máximo 600 caracteres (RESP-3: cuatro frases).
      3. Si pide_confirmacion es True, el texto tiene que decir "confirm" (confirma, confirmación…).

    Ejemplo:
      revisar(Respuesta(texto="Te recomiendo P001.", fuentes=["P002"], pide_confirmacion=False),
              {"P001"})
      → ["Citas P002, pero no sale de ninguna tool. No la cites."]

    Cómo hacerlo: borra la línea `raise NotImplementedError` y escribe la función.
    Empieza con una lista vacía, añade un problema por cada regla que no se cumple
    y devuelve la lista. Comprueba: uv run pytest tests/test_mi_agente.py --runxfail -q -k s4
    """
    raise NotImplementedError  # ← borra esta línea y escribe tu código

    problemas = []
    # Tu código aquí: una comprobación por cada regla.
    return problemas
