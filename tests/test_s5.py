"""S5 · skills, evaluators, the LLM judge and local evaluation (no LangSmith needed)."""

import json

import carrito.student as student
from carrito import experimentos
from carrito.model import FixtureModel

SKILL = """---
nombre: regalos
descripcion: Ayudar a elegir un regalo con presupuesto.
---
1. Pregunta el presupuesto si falta.
2. Busca con search_products.
"""

SOLVED = """
EVALUADORES = ["siempre"]

def siempre(respuesta, herramientas):
    return {"score": 1, "comment": "ok"}
"""


def call(name, args, cid="c1"):
    return {"type": "function_call", "name": name, "arguments": json.dumps(args), "call_id": cid}


def test_skills_are_listed_and_loaded_on_demand(tmp_path, monkeypatch):
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "regalos.md").write_text(SKILL)
    (tmp_path / "skills" / "rota.md").write_text("sin cabecera")
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    assert list(student.load_skills()) == ["regalos"]
    model = FixtureModel([[call("cargar_skill", {"nombre": "regalos"})], []], final_text="ok")
    agent = student.StudentAgent(model=model, warn=print)
    result = agent.ask("Quiero un regalo")
    start = next(e for e in result["events"] if e["type"] == "start")
    assert "cargar_skill" in [t["name"] for t in start["tools"]]
    assert any("Skills disponibles" in str(m.get("content")) for m in start["messages"])
    loaded = result["report"]["calls"][0]["model_sees"]
    assert "Pregunta el presupuesto" in loaded
    assert agent.tools.cargar_skill("otra")["error"] == "skill_not_found"
    agent.close()


def test_checks_and_tokens_evaluators():
    outputs = {"respuesta": "Te recomiendo P001.", "tools": ["search_products"], "tokens": 900}
    reference = {"checks": [{"type": "contains", "values": ["P001"]}]}
    assert experimentos.checks({}, outputs, reference) == {
        "key": "checks",
        "score": 1,
        "comment": "ok",
    }
    assert experimentos.tokens({}, outputs, reference)["score"] == 900


def test_student_evaluators_are_found_when_written(tmp_path, monkeypatch):
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    monkeypatch.setattr(experimentos, "load_student_module", student.load_student_module)
    (tmp_path / "evaluadores.py").write_text(SOLVED)
    found = experimentos.student_evaluators()
    assert [f.__name__ for f in found] == ["siempre"]
    result = found[0]({}, {"respuesta": "x", "tools": []}, {})
    assert result == {"key": "siempre", "score": 1, "comment": "ok"}


def test_local_evaluation_runs_every_case_with_a_fixture():
    rows = experimentos.local(
        model_factory=lambda: FixtureModel([[]], final_text="Hola"), only=["C6", "C22"]
    )
    assert [r["id"] for r in rows] == ["C6", "C22"]
    assert {s["key"] for s in rows[0]["scores"]} >= {"checks", "tokens"}
    assert "checks:" in experimentos.render_local(rows)


def test_judge_calibration_counts_agreement(tmp_path):
    data = tmp_path / "cal.jsonl"
    data.write_text(
        json.dumps({"id": "J1", "pregunta": "p", "respuesta": "r", "humano": "bien", "razon": "x"})
        + "\n"
        + json.dumps({"id": "J2", "pregunta": "p", "respuesta": "r", "humano": "mal", "razon": "y"})
        + "\n"
    )

    class Lenient(FixtureModel):
        def respond(self, messages, tools, text_format=None):
            turn = super().respond(messages, tools)
            turn.text = json.dumps({"veredicto": "bien", "motivo": "parece correcta"})
            return turn

    report = experimentos.calibrate(model=Lenient([]), path=data)
    assert report["acuerdo"] == 1 and report["total"] == 2
    assert "ACUERDO JUEZ-HUMANO: 1/2" in experimentos.render_calibration(report)


def test_judge_evaluator_receives_the_tool_data(monkeypatch):
    from carrito import experimentos

    seen = {}

    def fake_judge(question, answer, evidence="", model=None):
        seen["evidence"] = evidence
        return experimentos.Veredicto(veredicto="bien", motivo="ok")

    monkeypatch.setattr(experimentos, "judge", fake_judge)
    outputs = {"respuesta": "P001", "datos": "search_products: [P001 69,90]"}
    result = experimentos.judge_evaluator({"turns": ["¿Auriculares?"]}, outputs, {})
    assert result["score"] == 1
    assert seen["evidence"] == "search_products: [P001 69,90]"
