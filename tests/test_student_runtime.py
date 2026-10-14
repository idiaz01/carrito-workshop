import json

import carrito.student as student
from carrito.cases import check_case, run_cases
from carrito.model import FixtureModel


def test_agent_runs_with_unfinished_steps_and_uses_defaults():
    agent = student.StudentAgent(model=FixtureModel.for_scenario("catalog"))
    first = agent.ask("Busco auriculares por menos de 80 €")
    report = first["report"]
    assert report["uses"]["format_tool_result"] == "por defecto"
    assert report["calls"][0]["name"] == "search_products"
    assert "price_cents" in report["calls"][0]["model_sees"]  # raw result by default
    agent.model = FixtureModel([[]], final_text="Vale")
    second = agent.ask("¿Y otro?")
    history = second["report"]["blocks"]["historial"]
    assert history > 0 and second["report"]["uses"]["build_history"] == "por defecto"
    agent.close()


def test_student_functions_are_used_and_errors_fall_back(tmp_path, monkeypatch):
    (tmp_path / "system.md").write_text("## Rol\nEres Carrito.")
    (tmp_path / "tools.md").write_text("## search_products\nBusca en el catálogo de la tienda.")
    (tmp_path / "contexto.py").write_text(
        "def format_tool_result(name, result):\n    return 'resumen'\n"
        "def update_state(state, message):\n    return {**state, 'visto': True}\n"
        "def build_history(turns, state, max_turns=2):\n    raise ValueError('ups')\n"
    )
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    warnings = []
    agent = student.StudentAgent(model=FixtureModel.for_scenario("catalog"), warn=warnings.append)
    result = agent.ask("Busco auriculares")
    uses = result["report"]["uses"]
    assert uses == {"update_state": "tuya", "build_history": "error", "format_tool_result": "tuya"}
    assert result["report"]["calls"][0]["model_sees"] == "resumen"
    assert result["report"]["state"] == {"visto": True}
    assert warnings and "build_history" in warnings[0]
    descriptions = student.load_tool_descriptions()
    assert descriptions["search_products"].startswith("Busca en el catálogo")
    assert descriptions["get_order"] == "get_order"
    agent.close()


def test_cases_runner_and_checks():
    case = {"checks": [{"type": "contains", "values": ["P001"]}, {"type": "no_tools"}]}
    assert check_case(case, "Te recomiendo P001", []) == []
    assert check_case(case, "Nada", ["search_products"]) == [
        "falta P001",
        "usó tools: search_products",
    ]
    report = run_cases(model_factory=lambda: FixtureModel([[]], final_text="Hola"), only=["C6"])
    assert report["total"] == 1 and report["passed"] == 1
    json.dumps(report)


def test_system_role_falls_back_to_developer_once():
    from carrito import model

    class BadRequestError(Exception):
        body = {"message": "Unsupported value: 'system' role is not supported with this model."}

    seen = []

    class Inner:
        def create(self, **request):
            seen.append([m["role"] for m in request["input"]])
            if request["input"][0]["role"] == "system":
                raise BadRequestError("bad")
            return "ok"

        parse = create

    model._ROLE["developer"] = False
    client = model._RoleFallbackResponses(Inner())
    request = {"input": [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]}
    assert client.create(**request) == "ok"
    assert client.parse(**request) == "ok"
    assert seen == [["system", "user"], ["developer", "user"], ["developer", "user"]]
    model._ROLE["developer"] = False
