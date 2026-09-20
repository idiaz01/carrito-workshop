"""Optional integration tests: install with uv sync --extra langchain."""

import json

import pytest

pytest.importorskip("langchain_openai")
from langchain_core.messages import AIMessage, ToolMessage

from carrito.langchain_demo import run_comparison
from carrito.store import create_store
from carrito.tools import StoreTools


class ScriptedModel:
    def __init__(self, name="search_products", arguments=None):
        self.name = name
        self.arguments = arguments or {"query": "auriculares", "max_price_eur": 80}
        self.messages = []

    def bind_tools(self, tools):
        self.tools = tools
        return self

    def invoke(self, messages):
        self.messages.append(list(messages))
        if len(self.messages) == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {"name": self.name, "args": self.arguments, "id": "lc_1", "type": "tool_call"}
                ],
            )
        return AIMessage(content="Fixture: consulta el resultado del catálogo.")


def test_langchain_tool_round_trip_uses_real_catalog():
    model = ScriptedModel()
    result = run_comparison(model=model)
    assert result["mode"] == "fixture"
    assert result["tool_results"][0]["result"][0]["product_id"] == "P001"
    assert result["tool_results"][0]["result"][0]["price_cents"] == 6990
    output = next(m for m in model.messages[1] if isinstance(m, ToolMessage))
    assert output.tool_call_id == "lc_1"
    assert json.loads(output.content)[0]["product_id"] == "P001"
    assert model.tools[0].name == "search_products"


def test_langchain_demo_cannot_execute_writes():
    shop = StoreTools(create_store())
    shop.request_return("104", "No encaja")
    shop.confirm_pending()
    result = run_comparison(
        model=ScriptedModel("request_return", {"order_id": "104", "reason": "No encaja"}),
        tools=shop,
    )
    assert result["tool_results"][0]["result"]["error"] == "read_only_demo"
    assert shop.return_count() == 0


def test_langchain_bad_arguments_are_observable():
    result = run_comparison(
        model=ScriptedModel(arguments={"query": "auriculares", "max_price_eur": -1})
    )
    assert result["tool_results"][0]["result"]["error"] == "invalid_arguments"


def test_langchain_default_fixture_is_offline(monkeypatch):
    import langchain_openai

    def fail(**kwargs):
        raise AssertionError("must not construct a live model")

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", fail)
    assert run_comparison()["mode"] == "fixture"


def test_actual_chatopenai_adapter_serializes_responses_without_network():
    import httpx
    from langchain_openai import ChatOpenAI

    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        if len(requests) == 1:
            assert body["include"] == ["reasoning.encrypted_content"]
            assert body["tools"][0]["name"] == "search_products"
            output = [
                {
                    "type": "reasoning",
                    "id": "rs_lc",
                    "summary": [],
                    "encrypted_content": "opaque-lc",
                },
                {
                    "type": "function_call",
                    "id": "fc_lc",
                    "call_id": "call_lc",
                    "name": "search_products",
                    "arguments": '{"query":"auriculares","max_price_eur":80}',
                    "status": "completed",
                },
            ]
        else:
            tool_result = next(
                item for item in body["input"] if item.get("type") == "function_call_output"
            )
            assert tool_result["call_id"] == "call_lc"
            assert json.loads(tool_result["output"])[0]["product_id"] == "P001"
            output = [
                {
                    "type": "message",
                    "id": "msg_lc",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {"type": "output_text", "text": "P001 cuesta 69,90 €.", "annotations": []}
                    ],
                }
            ]
        return httpx.Response(
            200,
            json={
                "id": f"resp_lc_{len(requests)}",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": "test-model",
                "output": output,
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        model = ChatOpenAI(
            model="test-model",
            api_key="offline-test-placeholder",
            http_client=client,
            use_responses_api=True,
            include=["reasoning.encrypted_content"],
            store=False,
            max_retries=0,
        )
        result = run_comparison(model=model)
    assert len(requests) == 2
    assert result["tool_results"][0]["result"][0]["product_id"] == "P001"
