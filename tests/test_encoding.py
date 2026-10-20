"""The same checks on Windows, macOS and Linux."""

import ast
from pathlib import Path

from carrito.cases import check_case
from carrito.texto import normalize

ROOT = Path(__file__).resolve().parents[1]


def calls_without_encoding(path):
    """open(), read_text() and write_text() without encoding= use cp1252 on Windows."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in ("open", "read_text", "write_text"):
            continue
        if any(k.arg == "encoding" for k in node.keywords):
            continue
        modes = [a.value for a in node.args if isinstance(a, ast.Constant)]
        if name == "open" and any(isinstance(m, str) and "b" in m for m in modes):
            continue
        found.append(f"{path.relative_to(ROOT)}:{node.lineno} {name}()")
    return found


def test_every_text_file_is_read_as_utf8():
    files = sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "scripts").glob("*.py"))
    found = [hit for path in files for hit in calls_without_encoding(path)]
    assert found == [], 'Falta encoding="utf-8" en: ' + ", ".join(found)


def test_cases_survive_a_cp1252_read():
    """What Windows did before the fix: «número» became «nÃºmero»."""
    raw = (ROOT / "evals" / "s2_casos.jsonl").read_bytes()
    assert "número" in raw.decode("utf-8")
    assert "número" not in raw.decode("cp1252", errors="replace")


def test_normalize_special_spaces_dashes_and_quotes():
    assert normalize("69,85\u202f€") == normalize("69,85 €")
    assert normalize("12\u00a0de octubre") == "12 de octubre"
    assert normalize("2026\u201110\u201112") == "2026-10-12"
    assert normalize("«Tramitada»") == normalize('"tramitada"')
    assert normalize("Nu\u0301mero") == "número"  # a + accent, as macOS writes it
    assert normalize("Garantía") != "garantia"  # accents stay


def test_check_case_uses_the_same_text_for_everybody():
    case = {"checks": [{"type": "contains", "values": ["69,85 €", "2026-10-12"]}]}
    assert check_case(case, "Total: 69,85\u202f€. Hasta el 2026\u201110\u201112.", []) == []
    case = {"checks": [{"type": "not_contains", "values": ["tramitada"]}]}
    assert check_case(case, "Devolución TRAMITADA.", []) == ["dice tramitada"]
