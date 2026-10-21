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
    (tmp_path / "skills" / "regalos.md").write_text(SKILL, encoding="utf-8")
    (tmp_path / "skills" / "rota.md").write_text("sin cabecera", encoding="utf-8")
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
    (tmp_path / "evaluadores.py").write_text(SOLVED, encoding="utf-8")
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
        + "\n",
        encoding="utf-8",
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


def test_s5_cases_are_in_the_dataset():
    ids = [c["id"] for c in experimentos.dataset_cases()]
    assert ["C33", "C34", "C35", "C36"] == [i for i in ids if i in {"C33", "C34", "C35", "C36"}]


def test_calibration_set_has_good_and_bad_answers():
    rows = [
        json.loads(line)
        for line in experimentos.CALIBRATION.read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 20
    assert {r["humano"] for r in rows} == {"bien", "mal"}


class FakeExample:
    def __init__(self, case_id, inputs, outputs):
        self.id, self.metadata, self.inputs, self.outputs = (
            case_id,
            {"id": case_id},
            inputs,
            outputs,
        )


class FakeClient:
    def __init__(self, examples):
        self.examples = examples
        self.created, self.updated, self.deleted = [], [], []

    def has_dataset(self, dataset_name):
        return True

    def read_dataset(self, dataset_name):
        return type("D", (), {"id": "d1"})()

    def list_examples(self, dataset_id):
        return self.examples

    def create_examples(self, dataset_id, examples):
        self.created += examples

    def update_example(self, example_id, inputs, outputs):
        self.updated.append(example_id)

    def delete_example(self, example_id):
        self.deleted.append(example_id)


def test_upload_adds_updates_and_deletes(monkeypatch):
    import langsmith

    same = FakeExample("A1", {"turns": ["hola"]}, {"checks": [], "spec": "x"})
    changed = FakeExample("A2", {"turns": ["antes"]}, {"checks": [], "spec": "x"})
    gone = FakeExample("A9", {"turns": ["borrado"]}, {"checks": [], "spec": "x"})
    client = FakeClient([same, changed, gone])
    monkeypatch.setattr(langsmith, "Client", lambda: client)
    cases = [
        {"id": "A1", "spec": "x", "turns": ["hola"], "checks": []},
        {"id": "A2", "spec": "x", "turns": ["después"], "checks": []},
        {"id": "A3", "turns": ["nuevo"], "checks": []},
    ]
    report = experimentos.upload_cases("d", cases)
    assert report == {"dataset": "d", "nuevos": 1, "cambiados": 1, "borrados": 1, "total": 3}
    assert client.updated == ["A2"] and client.deleted == ["A9"]


def test_experiment_summary_shows_the_failing_cases():
    def result(key, score):
        return type("R", (), {"key": key, "score": score})()

    items = [
        {
            "example": FakeExample("C2", {}, {}),
            "evaluation_results": {"results": [result("checks", 1), result("tokens", 900)]},
        },
        {
            "example": FakeExample("C10", {}, {}),
            "evaluation_results": {"results": [result("checks", 0), result("tokens", 1100)]},
        },
        {
            "example": FakeExample("C10", {}, {}),
            "evaluation_results": {"results": [result("checks", 1), result("tokens", 1000)]},
        },
    ]
    text = experimentos.render_summary(experimentos.summarize(items))
    assert "C10   checks 1/2" in text
    assert "C2 " not in text
    assert "TOTAL: checks 2/3 · tokens 1000 de media" in text
