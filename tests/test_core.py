import json
from types import SimpleNamespace

import pytest

from carrito.agent import run_agent
from carrito.model import FixtureModel, OpenAIModel, recommend_structured
from carrito.store import create_store
from carrito.tools import StoreTools


@pytest.fixture
def shop():
    return StoreTools(create_store(), user_id="user1")


def test_original_data_shape(shop):
    assert shop.db.execute("select count(*) from products").fetchone()[0] == 20
    assert shop.db.execute("select count(*) from orders").fetchone()[0] == 10
    assert len(shop.search_policies("")) == 6


def test_catalog_filters_price_in_cents(shop):
    rows = shop.search_products("auriculares", 80)
    assert rows and all(p["price_cents"] <= 8000 for p in rows)
    assert "P001" in [p["product_id"] for p in rows]


def test_identity_is_host_owned(shop):
    assert shop.get_order("104")["order_id"] == "104"
    assert shop.get_order("109") == shop.get_order("999") == {"error": "order_not_found"}
    result = shop.dispatch("get_order", {"order_id": "109", "user_id": "user2"})
    assert result["error"] == "invalid_arguments"
    assert StoreTools(shop.db, "user2").get_order("109")["order_id"] == "109"


def test_confirmation_binds_exact_payload_and_requires_host(shop):
    assert shop.request_return("104", "No encaja")["status"] == "confirmation_required"
    assert shop.return_count() == 0
    assert (
        shop.dispatch(
            "request_return", {"order_id": "104", "reason": "No encaja", "confirmed": True}
        )["error"]
        == "invalid_arguments"
    )
    shop.confirm_pending()
    assert shop.request_return("104", "Otro motivo")["status"] == "confirmation_required"
    assert shop.return_count() == 0
    shop.confirm_pending()
    first = shop.request_return("104", "Otro motivo")
    second = shop.request_return("104", "Otro motivo")
    assert first["status"] == second["status"] == "requested"
    assert first["request_id"] == second["request_id"]
    assert shop.return_count() == 1


def test_confirming_wrong_order_never_writes(shop):
    shop.request_return("104", "No encaja")
    shop.confirm_pending()
    assert shop.request_return("101", "No encaja")["status"] == "confirmation_required"
    assert shop.return_count() == 0
    assert shop.request_return("104", "No encaja")["status"] == "confirmation_required"


@pytest.mark.parametrize(
    "order,error",
    [
        ("109", "order_not_found"),
        ("102", "return_window_expired"),
        ("103", "not_delivered"),
        ("106", "non_returnable"),
    ],
)
def test_return_rules(shop, order, error):
    assert shop.request_return(order, "No encaja")["error"] == error
    assert shop.return_count() == 0


@pytest.mark.parametrize(
    "name,args",
    [
        ("search_products", {"query": "x", "max_price_eur": -1}),
        ("get_order", {"order_id": 104}),
        ("request_return", {"order_id": "104", "reason": " "}),
        ("unknown", {}),
        ("get_order", []),
    ],
)
def test_bad_arguments_are_observable(shop, name, args):
    assert "error" in shop.dispatch(name, args)


def test_loop_stops_and_trace_exposes_calls(shop, tmp_path):
    model = FixtureModel.for_scenario("catalog")
    path = tmp_path / "trace.jsonl"
    result = run_agent("Auriculares por menos de 80", shop, model, trace_path=path)
    assert result["status"] == "completed"
    assert any(e["type"] == "tool_result" for e in result["events"])
    assert all(json.loads(line) for line in path.read_text().splitlines())
    endless = FixtureModel(
        [
            [
                {
                    "type": "function_call",
                    "name": "get_order",
                    "arguments": '{"order_id":"104"}',
                    "call_id": "x",
                }
            ]
        ]
        * 8
    )
    assert run_agent("pedido", shop, endless, max_steps=2)["status"] == "step_limit"


def test_malformed_json_and_tool_errors_return_to_model(shop):
    model = FixtureModel(
        [
            [
                {
                    "type": "function_call",
                    "name": "get_order",
                    "arguments": "{broken",
                    "call_id": "bad",
                }
            ],
            [],
        ]
    )
    result = run_agent("pedido", shop, model)
    assert any(e.get("result", {}).get("error") == "invalid_json" for e in result["events"])


def test_native_continuation_preserves_reasoning_and_call_ids(shop):
    seen = []
    reasoning = {"type": "reasoning", "id": "rs_1", "summary": []}
    call = {
        "type": "function_call",
        "name": "get_order",
        "arguments": '{"order_id":"104"}',
        "call_id": "call_7",
    }

    class Responses:
        def create(self, **kwargs):
            seen.append(kwargs)
            output = [reasoning, call] if len(seen) == 1 else []
            return SimpleNamespace(
                output=output,
                output_text="Pedido entregado",
                usage=SimpleNamespace(model_dump=lambda: {"input_tokens": 8, "output_tokens": 3}),
            )

    model = OpenAIModel(client=SimpleNamespace(responses=Responses()), model="test-model")
    assert run_agent("pedido", shop, model)["status"] == "completed"
    assert reasoning in seen[1]["input"]
    assert call in seen[1]["input"]
    assert any(
        x.get("call_id") == "call_7" and x["type"] == "function_call_output"
        for x in seen[1]["input"]
    )
    assert seen[0]["model"] == "test-model"


def test_structured_fixture_is_validated(shop):
    output = recommend_structured(
        shop.search_products("auriculares", 80), "auriculares", live=False
    )
    assert output.product_ids == ["P001"]
    assert output.mode == "fixture"


def test_tool_and_token_budgets(shop):
    many = [
        {
            "type": "function_call",
            "name": "get_order",
            "arguments": '{"order_id":"104"}',
            "call_id": str(i),
        }
        for i in range(5)
    ]
    assert run_agent("x", shop, FixtureModel([many]), max_tool_calls=2)["status"] == "tool_limit"
    from carrito.model import ModelTurn

    class LargeUsage:
        mode = "fixture"

        def respond(self, messages, tools):
            return ModelTurn([], "x", {"input_tokens": 100, "output_tokens": 20}, "test")

    assert run_agent("x", shop, LargeUsage(), max_total_tokens=10)["status"] == "token_limit"


def test_model_failure_is_visible(shop):
    class Failure:
        mode = "fixture"

        def respond(self, messages, tools):
            raise ConnectionError("do not log secrets")

    result = run_agent("x", shop, Failure())
    assert result["status"] == "model_error"
    assert "do not log secrets" not in json.dumps(result)


def test_storage_failure_returns_tool_error(shop):
    shop.db.close()
    assert shop.dispatch("get_order", {"order_id": "104"})["error"] == "storage_error"


def test_confirmation_has_no_model_tool(shop):
    from carrito.tools import tool_definitions

    assert {t["name"] for t in tool_definitions()} == {
        "search_products",
        "get_order",
        "search_policies",
        "request_return",
    }
    assert shop.dispatch("confirm_pending", {})["error"] == "unknown_tool"


def test_eval_catches_wrong_catalog_and_denied_access():
    from carrito.evaluation import check_case, load_cases, run_evals

    catalog = next(c for c in load_cases("dev") if c["id"] == "D01")
    wrong = {
        "status": "completed",
        "events": [
            {
                "type": "tool_result",
                "name": "search_products",
                "result": [{"product_id": "MADE_UP", "price_cents": 99999}],
            }
        ],
    }
    assert not check_case(catalog, wrong, StoreTools(create_store()))["passed"]
    report = run_evals("dev", mode="fixture")
    assert report["total"] == 16
    assert report["passed"] == 16
    assert report["model_quality_measured"] is False


def test_native_first_call_exposes_usage_without_tools():
    from carrito.model import native_call

    calls = []

    class Responses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                output_text="Hola",
                output=[],
                model="test-model",
                usage=SimpleNamespace(model_dump=lambda: {"input_tokens": 2, "output_tokens": 1}),
            )

    result = native_call(
        [{"role": "user", "content": "Hola"}],
        client=SimpleNamespace(responses=Responses()),
        model="test-model",
    )
    assert result["output_text"] == "Hola"
    assert result["usage"]["input_tokens"] == 2
    assert "tools" not in calls[0]


def test_conversation_history_survives_next_turn(shop):
    first = run_agent("Primera pregunta", shop, FixtureModel([[]], "Primera respuesta"))
    second = run_agent(
        "Siguiente", shop, FixtureModel([[]], "Segunda respuesta"), history=first["messages"]
    )
    assert {"role": "user", "content": "Primera pregunta"} in second["messages"]
    assert {"role": "assistant", "content": "Primera respuesta"} in second["messages"]


def test_skill_activation_is_visible_and_conditional():
    from carrito.skills import activate_skill

    assert activate_skill("Busco auriculares") is None
    loaded = activate_skill("Quiero devolver un pedido")
    assert loaded["name"] == "return-help"
    assert "confirmación" in loaded["content"]


def test_judge_fixture_compares_human_labels():
    from carrito.judge import judge_demo

    result = judge_demo()
    assert result["mode"] == "fixture"
    assert result["total"] == 3
    assert result["agreement"] < 1


@pytest.mark.parametrize("status", ["incomplete", "failed", "refused"])
def test_noncompleted_model_response_never_succeeds_or_executes(shop, status):
    from carrito.model import ModelTurn

    class Partial:
        mode = "fixture"

        def respond(self, messages, tools):
            return ModelTurn([], "", {}, "test", status=status)

    result = run_agent("x", shop, Partial())
    assert result["status"] == status
    assert shop.return_count() == 0


def test_incomplete_native_response_preserves_status(shop):
    class Responses:
        def create(self, **kwargs):
            return SimpleNamespace(output=[], output_text="", usage=None, status="incomplete")

    result = run_agent(
        "x", shop, OpenAIModel(client=SimpleNamespace(responses=Responses()), model="test")
    )
    assert result["status"] == "incomplete"


def test_native_refusal_is_visible(shop):
    class Responses:
        def create(self, **kwargs):
            return SimpleNamespace(
                output=[
                    {
                        "type": "message",
                        "content": [{"type": "refusal", "refusal": "Cannot comply"}],
                    }
                ],
                output_text="",
                usage=None,
                status="completed",
            )

    result = run_agent(
        "x", shop, OpenAIModel(client=SimpleNamespace(responses=Responses()), model="test")
    )
    assert result["status"] == "refused"


@pytest.mark.parametrize(
    "call",
    [
        {"type": "function_call", "arguments": "{}"},
        {"type": "function_call", "name": "get_order", "arguments": "{}", "call_id": ""},
    ],
)
def test_malformed_native_call_is_bounded(shop, call):
    result = run_agent("x", shop, FixtureModel([[call]]))
    assert result["status"] == "invalid_model_output"
    assert shop.return_count() == 0


def test_empty_completed_response_is_not_success(shop):
    result = run_agent("x", shop, FixtureModel([[]], final_text=""))
    assert result["status"] == "empty_response"


def test_evals_reject_wrong_return_payload_and_invented_prices(shop):
    from carrito.evaluation import check_case, load_cases

    cases = {c["id"]: c for c in load_cases()}
    rows = shop.search_products("auriculares", 80)
    rows[0]["price_cents"] = 1
    result = {
        "status": "completed",
        "events": [{"type": "tool_result", "name": "search_products", "result": rows}],
    }
    assert not check_case(cases["D01"], result, shop)["passed"]
    shop.request_return("101", "Wrong payload")
    shop.confirm_pending()
    requested = shop.request_return("101", "Wrong payload")
    result = {
        "status": "completed",
        "count_before_confirmation": 0,
        "events": [{"type": "tool_result", "name": "request_return", "result": requested}],
    }
    assert not check_case(cases["D09"], result, shop)["passed"]


@pytest.mark.parametrize(
    "split,case_id", [("dev", "D10"), ("dev", "D11"), ("dev", "D12")]
)
def test_error_evals_allow_authorized_preflight_read(shop, split, case_id):
    from carrito.evaluation import check_case, load_cases

    case = next(c for c in load_cases(split) if c["id"] == case_id)
    arguments = case["fixture_calls"][0]["arguments"]
    result = {
        "status": "completed",
        "events": [
            {
                "type": "tool_result",
                "name": "get_order",
                "result": shop.get_order(arguments["order_id"]),
            },
            {
                "type": "tool_result",
                "name": "request_return",
                "result": shop.request_return(**arguments),
            },
        ],
    }
    assert check_case(case, result, shop)["passed"]


@pytest.mark.parametrize(
    "disclosure",
    [
        {"order_id": "109", "user_id": "user2", "status": "delivered"},
        {"order_id": "109", "status": "delivered"},
        {"user_id": "user2"},
    ],
)
def test_error_evals_still_reject_foreign_order_disclosure(shop, disclosure):
    from carrito.evaluation import check_case, load_cases

    case = next(c for c in load_cases() if c["id"] == "D04")
    result = {
        "status": "completed",
        "events": [
            {"type": "tool_result", "name": "get_order", "result": disclosure},
            {"type": "tool_result", "name": "get_order", "result": {"error": "order_not_found"}},
        ],
    }
    assert not check_case(case, result, shop)["passed"]


@pytest.mark.parametrize("limit,executed", [("tool_limit", 1), ("token_limit", 0)])
def test_budget_stop_completes_all_call_ids_before_continuation(shop, limit, executed):
    from carrito.model import ModelTurn

    shop.request_return("104", "No encaja")
    shop.confirm_pending()
    calls = [
        {
            "type": "function_call",
            "call_id": "read_1",
            "name": "get_order",
            "arguments": '{"order_id":"101"}',
        },
        {
            "type": "function_call",
            "call_id": "write_2",
            "name": "request_return",
            "arguments": '{"order_id":"104","reason":"No encaja"}',
        },
        {
            "type": "function_call",
            "call_id": "read_3",
            "name": "get_order",
            "arguments": '{"order_id":"104"}',
        },
    ]

    class Batch:
        mode = "fixture"

        def respond(self, messages, tools):
            return ModelTurn(calls, "", {"input_tokens": 20, "output_tokens": 10}, "test")

    budgets = {"max_tool_calls": 1} if limit == "tool_limit" else {"max_total_tokens": 1}
    result = run_agent("x", shop, Batch(), **budgets)
    assert result["status"] == limit
    assert shop.return_count() == 0
    outputs = [m for m in result["messages"] if m.get("type") == "function_call_output"]
    assert {m["call_id"] for m in outputs} == {c["call_id"] for c in calls}
    assert sum(json.loads(m["output"]).get("error") == limit for m in outputs) == 3 - executed
    assert result["events"][-1]["tool_calls"] == executed

    class Responses:
        def create(self, **kwargs):
            inputs = kwargs["input"]
            call_ids = {m["call_id"] for m in inputs if m.get("type") == "function_call"}
            output_ids = {m["call_id"] for m in inputs if m.get("type") == "function_call_output"}
            assert call_ids == output_ids
            return SimpleNamespace(output=[], output_text="Podemos continuar.", usage=None)

    continued = run_agent(
        "Continúa",
        shop,
        OpenAIModel(client=SimpleNamespace(responses=Responses()), model="test"),
        history=result["messages"],
    )
    assert continued["status"] == "completed"
    assert shop.return_count() == 0


def test_catalog_never_rounds_budget_up_to_a_more_expensive_product(shop):
    assert shop.search_products("auriculares", 69.899) == []
    assert [p["product_id"] for p in shop.search_products("auriculares", 69.90)] == ["P001"]
