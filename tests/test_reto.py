"""S5 · Reto: the from-scratch template works without the network."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from carrito import reto
from carrito.cases import check_case

KINDS = {
    "tool_called",
    "tool_called_any",
    "tool_not_called",
    "no_tools",
    "contains",
    "contains_any",
    "not_contains",
    "max_chars",
}


def test_template_loads_and_its_tools_work():
    module = reto.load()
    assert module.buscar_clase.invoke({"nombre": "Yoga"})["hora"] == "19:00"
    assert module.preparar_reserva.invoke({"clase": "spinning"}) == {"error": "no quedan plazas"}
    assert (
        module.preparar_reserva.invoke({"clase": "pilates"})["estado"] == "pendiente_de_confirmar"
    )
    assert module.JUEZ.strip()


def test_template_cases_use_known_checks():
    module = reto.load()
    ids = [c["id"] for c in module.CASOS]
    assert len(ids) == len(set(ids)) >= 3
    for case in module.CASOS:
        assert case["turns"] and {c["type"] for c in case["checks"]} <= KINDS


class FakeAgent:
    """Answers like create_agent: the whole conversation in result["messages"]."""

    def invoke(self, state):
        call = {"name": "buscar_clase", "args": {"nombre": "yoga"}, "id": "t1"}
        history = [
            HumanMessage(m["content"]) if isinstance(m, dict) else m for m in state["messages"]
        ]
        return {
            "messages": [
                *history,
                AIMessage(content="", tool_calls=[call], usage_metadata=_usage(100)),
                ToolMessage(content='{"hora": "19:00"}', name="buscar_clase", tool_call_id="t1"),
                AIMessage(content="Yoga es el lunes a las 19:00.", usage_metadata=_usage(50)),
            ]
        }


def _usage(n):
    return {"input_tokens": n, "output_tokens": 10, "total_tokens": n + 10}


def test_run_case_collects_answer_tools_data_and_tokens(monkeypatch):
    monkeypatch.setattr(reto, "new_agent", lambda module, model=None: FakeAgent())
    out = reto.run_case(reto.load(), ["¿A qué hora es yoga?"])
    assert out["respuesta"] == "Yoga es el lunes a las 19:00."
    assert out["tools"] == ["buscar_clase"]
    assert "19:00" in out["datos"] and out["tokens"] == 170
    case = reto.load().CASOS[0]
    assert check_case(case, out["respuesta"], out["tools"]) == []


def test_local_runs_and_renders_without_the_judge(monkeypatch):
    monkeypatch.setattr(reto, "new_agent", lambda module, model=None: FakeAgent())
    rows = reto.local(reto.load(), only=["R1"], with_judge=False, model=object())
    text = reto.render(rows)
    assert rows[0]["id"] == "R1" and "TOTAL: checks 1/1" in text
