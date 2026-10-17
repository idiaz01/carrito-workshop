"""S2 · Tu agente. Each test checks one step of mi_agente/.

While a step is not done, its test is marked xfail and the suite stays green.
To see your progress: uv run pytest tests/test_mi_agente.py --runxfail -q
"""

import json

import pytest

from carrito.student import (
    load_rag_config,
    load_student_module,
    system_prompt_status,
    tool_descriptions_status,
)

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
    assert "POL-0" in text and "POL-1" in text
    # S2: at most two documents. From S3 on, rag.toml (top_k) decides how many arrive.
    if load_rag_config() is None:
        assert "POL-2" not in text
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


# ---------------------------------------------------------------------------
# S3 · Paso 3 · mi_agente/herramientas.py
# ---------------------------------------------------------------------------
def _deadline(order_id, delivered_at, status="delivered", returnable=1):
    from datetime import date

    from carrito.student import load_student_module

    module = load_student_module("herramientas")
    if module is None:
        raise NotImplementedError("Falta mi_agente/herramientas.py")
    pedido = {"order_id": order_id, "status": status, "delivered_at": delivered_at}
    producto = {"product_id": "P001", "returnable": returnable}
    return module.plazo_devolucion(pedido, producto, date(2026, 9, 20))


@TODO
def test_s3_paso3_deadline_in_time():
    result = _deadline("104", "2026-09-12")
    assert result["se_puede_devolver"] is True
    assert result["fecha_limite"] == "2026-10-12"
    assert result["dias_restantes"] == 22
    assert result["motivo"] == "POL-DEV"


@TODO
def test_s3_paso3_deadline_rules():
    assert _deadline("103", None, status="shipped")["motivo"] == "no_entregado"
    personal = _deadline("106", "2026-09-15", returnable=0)
    assert personal["se_puede_devolver"] is False and personal["motivo"] == "POL-EXC"
    late = _deadline("102", "2026-08-01")
    assert late["se_puede_devolver"] is False and late["motivo"] == "plazo_vencido"
    assert late["fecha_limite"] == "2026-08-31"
