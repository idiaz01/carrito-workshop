"""S4 · agente.toml (limits, routes, subagent), structured output and mis_pedidos."""

import json

import pytest

import carrito.student as student
from carrito import diseno
from carrito.model import FixtureModel

SOLVED_REVIEW = """
from pydantic import BaseModel, Field

class Respuesta(BaseModel):
    texto: str = Field(description="texto")
    fuentes: list[str] = Field(description="ids")
    pide_confirmacion: bool = Field(description="confirmar")

def revisar(respuesta, vistos):
    return [f"inventada {f}" for f in respuesta.fuentes if f not in vistos]
"""


def call(name, args, cid="c1"):
    return {"type": "function_call", "name": name, "arguments": json.dumps(args), "call_id": cid}


def write_design(folder, body):
    (folder / "agente.toml").write_text(body)


def test_design_validation(tmp_path):
    assert diseno.load(tmp_path / "nada.toml") is None
    path = tmp_path / "agente.toml"
    path.write_text("[limites]\nmax_pasos = 8\n")
    design = diseno.load(path)
    assert design["limites"] == {"max_pasos": 8, "max_tools": 12, "max_tokens": 16000}
    assert design["rutas"] == [] and design["subagente"] == {"activo": False}
    path.write_text("[limites]\nmax_pasos = 0\n")
    with pytest.raises(diseno.ConfigError, match="max_pasos"):
        diseno.load(path)
    path.write_text('[[rutas]]\ntipo = "fija"\npalabras = ["poema"]\n')
    with pytest.raises(diseno.ConfigError, match="respuesta"):
        diseno.load(path)


def test_routes_match_words_without_accents():
    routes = [
        {"tipo": "fija", "palabras": ["poema", "chiste"], "respuesta": "Solo tienda."},
        {"tipo": "buscar", "palabras": ["envío", "garantía"]},
    ]
    assert diseno.choose_route("Escríbeme un CHISTE", routes)["tipo"] == "fija"
    assert diseno.choose_route("¿Cuánto cuesta el envio?", routes)["tipo"] == "buscar"
    assert diseno.choose_route("¿Dónde está mi pedido 104?", routes) is None


def test_fixed_route_costs_no_model_call(tmp_path, monkeypatch):
    write_design(
        tmp_path,
        '[[rutas]]\ntipo = "fija"\npalabras = ["chiste"]\n'
        'respuesta = "Solo puedo ayudarte con la tienda."\n',
    )
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    agent = student.StudentAgent(model=FixtureModel([]), warn=print)
    result = agent.ask("Cuéntame un chiste")
    assert result["answer"] == "Solo puedo ayudarte con la tienda."
    assert result["report"]["ruta"] == "fija" and result["report"]["model_calls"] == 0
    agent.close()


def test_search_route_is_one_call_without_tools(tmp_path, monkeypatch):
    write_design(tmp_path, '[[rutas]]\ntipo = "buscar"\npalabras = ["envío"]\n')
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    agent = student.StudentAgent(model=FixtureModel([], final_text="Envío: 3 a 5 días (POL-ENV)."))
    result = agent.ask("¿Cuánto tarda el envío?")
    report = result["report"]
    assert report["ruta"] == "buscar" and report["model_calls"] == 1
    assert [c["name"] for c in report["calls"]] == ["search_policies"]
    agent.close()


def test_limits_stop_the_loop_and_mis_pedidos_is_offered(tmp_path, monkeypatch):
    write_design(tmp_path, "[limites]\nmax_pasos = 2\n")
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    turns = [
        [call("mis_pedidos", {}, "a")],
        [call("plazo_devolucion", {"order_id": "101"}, "b")],
        [call("plazo_devolucion", {"order_id": "104"}, "c")],
        [],
    ]
    agent = student.StudentAgent(model=FixtureModel(turns), warn=print)
    result = agent.ask("¿Qué pedidos puedo devolver?")
    assert result["status"] == "step_limit"
    start = next(e for e in result["events"] if e["type"] == "start")
    assert "mis_pedidos" in [t["name"] for t in start["tools"]]
    first = next(e for e in result["events"] if e["type"] == "tool_result")
    assert {o["order_id"] for o in first["result"]} >= {"101", "104"}
    agent.close()


def test_structured_answer_is_reviewed_and_fixed_once(tmp_path, monkeypatch):
    write_design(tmp_path, "[limites]\nmax_pasos = 4\n")
    (tmp_path / "salida.py").write_text(SOLVED_REVIEW)
    monkeypatch.setattr(student, "FOLDER", tmp_path)

    class Scripted(FixtureModel):
        def respond(self, messages, tools, text_format=None):
            assert text_format and text_format["strict"] is True
            return super().respond(messages, tools)

    first = json.dumps(
        {"texto": "P001 o P002", "fuentes": ["P001", "P002"], "pide_confirmacion": False}
    )
    fixed = json.dumps(
        {"texto": "Te recomiendo P001.", "fuentes": ["P001"], "pide_confirmacion": False}
    )
    model = Scripted(
        [[call("search_products", {"query": "auriculares", "max_price_eur": 80})], []],
        final_text=first,
    )
    agent = student.StudentAgent(model=model, warn=print)
    model.turns.append([])  # the correction call
    original = model.respond

    def respond(messages, tools, text_format=None):
        turn = original(messages, tools, text_format)
        if any("Corrige" in str(m.get("content", "")) for m in messages if isinstance(m, dict)):
            turn.text = fixed
        return turn

    model.respond = respond
    result = agent.ask("Auriculares por menos de 80 €")
    out = result["report"]["salida"]
    assert out["problemas"] == ["inventada P002"] and out["corregida"] is True
    assert result["answer"] == "Te recomiendo P001." and out["fuentes"] == ["P001"]
    agent.close()


def test_subagent_answers_search_policies_with_a_summary(tmp_path, monkeypatch):
    write_design(tmp_path, "[subagente]\nactivo = true\n")
    (tmp_path / "subagente.md").write_text("Resume en una frase y cita el ID.")
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    turns = [
        [call("search_policies", {"query": "garantía"}, "main")],  # main agent
        [call("search_policies", {"query": "garantía batería"}, "sub")],  # subagent
        [],  # subagent answers
        [],
    ]  # main agent answers
    agent = student.StudentAgent(model=FixtureModel(turns, final_text="Resumen (POL-GAR)."))
    result = agent.ask("¿Qué garantía tiene la batería?")
    seen = result["report"]["calls"][0]["model_sees"]
    assert "resumen" in seen and "POL-GAR" in seen
    assert result["report"]["subagente"]["llamadas"] == 2
    agent.close()


def test_strict_schema_has_all_fields_required():
    from pydantic import BaseModel

    class Demo(BaseModel):
        texto: str
        fuentes: list[str] = []

    schema = diseno.strict_schema(Demo)["schema"]
    assert schema["required"] == ["texto", "fuentes"]
    assert schema["additionalProperties"] is False
    assert "default" not in schema["properties"]["fuentes"]
