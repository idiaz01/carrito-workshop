"""Checks for the in-class labs (✏️ Tu turno).

A check never raises. It prints OK or PENDIENTE and returns a bool.
The checks test behavior with example inputs. They do not contain the solutions.
"""

import hashlib
import json
import re

from carrito.context import ConversationState, validate_recommendation

LAB = {}


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def report(name, passed, detail=""):
    LAB[name] = bool(passed)
    mark = "✅ OK" if passed else "✏️ PENDIENTE"
    print(f"{mark}: {name}" + (f" · {detail}" if detail and not passed else ""))
    return bool(passed)


def run(name, check, *args):
    """Run one lab check. An incomplete cell gives PENDIENTE, not an error."""
    try:
        passed, detail = check(*args)
    except Exception as exc:  # noqa: BLE001 - students see the reason, the notebook continues
        passed, detail = False, f"{type(exc).__name__}: {exc}"
    return report(name, passed, detail)


# ---------- S2 · Lab 1 · origen y autoridad ----------
LAB1_PIECES = [
    "instrucciones developer",
    "pregunta del cliente",
    "ficha del catálogo",
    "anuncio de un proveedor",
    "user_id del cliente",
]
LAB1_OPTIONS = ("aplicación", "usuario", "externo")
# SHA-256 of "piece=answer": the answers are not stored in clear text.
_LAB1_EXPECTED = {
    "instrucciones developer": "207544e2424b336d",
    "pregunta del cliente": "b2a59d4218a50f33",
    "ficha del catálogo": "f6ccd43e7c262670",
    "anuncio de un proveedor": "aa6049e312d794a2",
    "user_id del cliente": "2179fda9e39a7253",
}
_LAB1_AUTHORITY = "8cab192c7b88d34e"


def lab1_origin(origin):
    missing = [p for p in LAB1_PIECES if origin.get(p) not in LAB1_OPTIONS]
    if missing:
        return False, "falta una respuesta válida en: " + ", ".join(missing)
    wrong = [p for p in LAB1_PIECES if _digest(f"{p}={origin[p]}") != _LAB1_EXPECTED[p]]
    if wrong:
        return False, f"{len(wrong)} respuesta(s) para revisar"
    return True, ""


def lab1_authority(can_grant_access):
    if not isinstance(can_grant_access, (set, list, tuple)) or ... in can_grant_access:
        return False, "escribe un conjunto con los orígenes"
    chosen = {str(x) for x in can_grant_access}
    if not chosen <= set(LAB1_OPTIONS):
        return False, "usa solo: " + ", ".join(LAB1_OPTIONS)
    ok = _digest("acceso=" + ",".join(sorted(chosen))) == _LAB1_AUTHORITY
    return ok, "" if ok else "revisa quién puede dar permisos"


# ---------- S2 · Lab 2 · elegir evidencia con presupuesto ----------
# SHA-256 of "id=fuera": candidates that must stay out of the request.
_LAB2_OUT = {
    "21b0d9764867f646",
    "3afaa9b7e16b4691",
    "acea40e93bf1983c",
    "e8ad6fb37df11a65",
}


def lab2_selection(selected, candidates, budget_chars):
    by_id = {c["source_id"]: c for c in candidates}
    if not isinstance(selected, (list, tuple)) or not selected or ... in selected:
        return False, "escribe una lista de source_id"
    unknown = [s for s in selected if s not in by_id]
    if unknown:
        return False, "IDs desconocidos: " + ", ".join(map(str, unknown))
    used = sum(len(json.dumps(by_id[s], ensure_ascii=False)) for s in selected)
    if used > budget_chars:
        return False, f"{used} caracteres: supera el presupuesto de {budget_chars}"
    if "P001" not in selected:
        return False, "falta la evidencia que responde a la pregunta"
    if any(_digest(f"{s}=fuera") in _LAB2_OUT for s in selected):
        return False, "hay evidencia que no debe entrar"
    return True, ""


# ---------- S2 · Lab 3 · reglas de negocio ----------
_LAB3_CASES = [
    ("válido", ["P001"], 80, {"known_ids": True, "within_budget": True}),
    ("fuera de presupuesto", ["P001"], 50, {"known_ids": True, "within_budget": False}),
    ("ID inventado", ["P999"], 80, {"known_ids": False, "within_budget": False}),
    ("dos productos", ["P001", "P003"], 50, {"known_ids": True, "within_budget": False}),
    ("sin productos", [], 80, {"known_ids": True, "within_budget": True}),
]


def lab3_rules(rules, prices):
    for name, ids, budget, expected in _LAB3_CASES:
        got = rules({"product_ids": ids}, budget, prices)
        if not isinstance(got, dict):
            return False, "la función debe devolver un diccionario"
        for key, value in expected.items():
            if got.get(key) is not value:
                return False, f"caso «{name}»: {key} debe ser {value}"
    return True, ""


def lab3_trick(payload, products, budget):
    result = validate_recommendation(payload, products, budget)
    if not result["passed"]:
        return False, "el validador lo rechaza: " + json.dumps(result["checks"])
    text = str(payload.get("explanation", "")).lower()
    by_id = {p["product_id"]: p for p in products}
    real = {
        f"{by_id[i]['price_cents'] / 100:.2f}".replace(".", ",") for i in payload["product_ids"]
    }
    numbers = set(re.findall(r"\d+,\d{2}", text))
    claims = ("agua", "impermeable", "sumergible", "gratis", "garantía", "regalo")
    if (numbers - real) or any(word in text for word in claims):
        return True, ""
    return False, "pasa el validador, pero ¿la explicación dice algo falso?"


# ---------- S2 · Lab 4 · actualizar el estado ----------
def lab4_update(update_state):
    base = ConversationState(category="auriculares", budget_eur=80, preferences=["inalámbricos"])
    new = update_state(base, budget_eur=60)
    if not isinstance(new, ConversationState):
        return False, "la función debe devolver un ConversationState"
    if base.budget_eur != 80:
        return False, "no cambies el estado anterior: crea uno nuevo"
    if new.budget_eur != 60:
        return False, "el presupuesto nuevo no se aplica"
    if new.category != "auriculares" or "inalámbricos" not in new.preferences:
        return False, "se pierde la categoría o la preferencia"
    extra = update_state(base, preference="micrófono")
    if not isinstance(extra, ConversationState):
        return False, "la función debe devolver un ConversationState"
    if extra.budget_eur != 80 or set(extra.preferences) != {"inalámbricos", "micrófono"}:
        return False, "añadir una preferencia no debe borrar las anteriores"
    return True, ""


# ---------- S2 · Lab 5 · reto final ----------
def lab5_state(state):
    if not isinstance(state, ConversationState):
        return False, "crea un ConversationState"
    if not state.category or state.budget_eur != 50:
        return False, "revisa categoría y presupuesto (50 €)"
    return True, ""


def lab5_evidence(evidence):
    if not isinstance(evidence, list) or not evidence or ... in evidence:
        return False, "escribe una lista de evidencias"
    ids = {e.get("source_id") for e in evidence if isinstance(e, dict)}
    if "P003" not in ids:
        return False, "falta la ficha del altavoz"
    if len(ids) > 3:
        return False, "demasiada evidencia: selecciona"
    return True, ""
