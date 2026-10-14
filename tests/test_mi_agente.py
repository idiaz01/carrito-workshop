"""S2 · Tu agente. Each test checks one step of mi_agente/.

While a step is not done, its test is marked xfail and the suite stays green.
To see your progress: uv run pytest tests/test_mi_agente.py --runxfail -q
"""

import json

import pytest

from carrito.student import load_student_module, system_prompt_status, tool_descriptions_status

TODO = pytest.mark.xfail(raises=NotImplementedError, reason="paso pendiente", strict=False)

PRODUCTS = [
    {
        "product_id": "P001",
        "name": "Auriculares Nube",
        "category": "audio",
        "price_cents": 6990,
        "description": "auriculares inalámbricos bluetooth batería 30 horas",
        "returnable": 1,
    }
]
POLICIES = [{"source_id": f"POL-{i}", "text": "texto " * 50, "score": 3 - i} for i in range(3)]


@TODO
def test_paso1_system_prompt_has_sections_and_spec_ids():
    status = system_prompt_status()
    assert len(status["sections"]) >= 4, f"Secciones encontradas: {status['sections']}"
    assert len(status["spec_ids"]) >= 3, f"IDs del SPEC citados: {status['spec_ids']}"


@TODO
def test_paso2_tool_descriptions_say_when_and_what():
    lengths = tool_descriptions_status()
    short = [name for name, size in lengths.items() if size < 80]
    assert not short, f"Descripciones demasiado cortas: {short}"


@TODO
def test_paso3_products_in_euros_without_internal_fields():
    text = load_student_module().format_tool_result("search_products", PRODUCTS)
    assert isinstance(text, str)
    assert "69,90 €" in text
    for field in ("price_cents", "returnable", "category"):
        assert field not in text, f"{field} no debe llegar al modelo"


@TODO
def test_paso3_policies_keep_two_documents_and_errors_pass():
    module = load_student_module()
    text = module.format_tool_result("search_policies", POLICIES)
    assert "POL-0" in text and "POL-1" in text and "POL-2" not in text
    error = {"error": "order_not_found"}
    assert json.loads(module.format_tool_result("get_order", error)) == error


@TODO
def test_paso4a_update_state_keeps_and_adds():
    module = load_student_module()
    state = {"nombre": "Ana"}
    new = module.update_state(state, "Mi presupuesto máximo es 80 €.")
    assert new["presupuesto_eur"] == 80 and new["nombre"] == "Ana"
    assert state == {"nombre": "Ana"}, "No modifiques el estado anterior"
    assert module.update_state({}, "Hola, me llamo Luis.")["nombre"] == "Luis"


@TODO
def test_paso4b_history_has_state_and_last_turns_only():
    turns = [
        {"user": f"pregunta {i}", "assistant": f"respuesta {i}", "tools": [{"name": "x"}]}
        for i in range(5)
    ]
    messages = load_student_module().build_history(turns, {"presupuesto_eur": 80}, max_turns=2)
    assert messages[0]["role"] == "system" and "80" in messages[0]["content"]
    rest = messages[1:]
    expected = ["pregunta 3", "respuesta 3", "pregunta 4", "respuesta 4"]
    assert [m["content"] for m in rest] == expected
