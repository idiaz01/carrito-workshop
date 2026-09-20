"""Real SDK serialization with an in-process HTTP transport; no network or API key."""

import json

import httpx
import pytest
from openai import OpenAI

from carrito.agent import run_agent
from carrito.model import OpenAIModel, native_call, recommend_structured
from carrito.store import create_store
from carrito.tools import StoreTools


def response_payload(output, status="completed"):
    return {
        "id": "resp_test",
        "object": "response",
        "created_at": 1,
        "model": "test-model",
        "status": status,
        "output": output,
        "usage": {"input_tokens": 12, "output_tokens": 5, "total_tokens": 17},
    }


def message(text):
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "status": "completed",
        "content": [{"type": "output_text", "text": text, "annotations": []}],
    }


def client_for(handler):
    return OpenAI(
        api_key="offline-test-placeholder",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_real_sdk_native_call_records_usage_and_input():
    def handler(request):
        body = json.loads(request.content)
        assert request.url.path == "/v1/responses"
        assert body["input"] == [{"role": "user", "content": "Hola"}]
        assert body["store"] is False
        assert "tools" not in body
        return httpx.Response(200, json=response_payload([message("Hola")]))

    with client_for(handler) as client:
        result = native_call(
            [{"role": "user", "content": "Hola"}], client=client, model="test-model"
        )
    assert result["output_text"] == "Hola"
    assert result["usage"]["total_tokens"] == 17


def test_real_sdk_preserves_tool_round_trip():
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        if len(requests) == 1:
            assert body["include"] == ["reasoning.encrypted_content"]
            assert {tool["name"] for tool in body["tools"]} == {
                "search_products",
                "get_order",
                "search_policies",
                "request_return",
            }
            return httpx.Response(
                200,
                json=response_payload(
                    [
                        {
                            "type": "reasoning",
                            "id": "rs_test",
                            "summary": [],
                            "encrypted_content": "opaque-test-data",
                        },
                        {
                            "type": "function_call",
                            "id": "fc_test",
                            "call_id": "call_test",
                            "name": "get_order",
                            "arguments": '{"order_id":"104"}',
                            "status": "completed",
                        },
                    ]
                ),
            )
        reasoning = next(item for item in body["input"] if item.get("id") == "rs_test")
        assert reasoning["encrypted_content"] == "opaque-test-data"
        tool_result = next(
            item for item in body["input"] if item.get("type") == "function_call_output"
        )
        assert tool_result["call_id"] == "call_test"
        assert json.loads(tool_result["output"])["order_id"] == "104"
        return httpx.Response(200, json=response_payload([message("Pedido 104 entregado.")]))

    with client_for(handler) as client:
        result = run_agent(
            "Pedido 104", StoreTools(create_store()), OpenAIModel(client=client, model="test-model")
        )
    assert result["status"] == "completed" and len(requests) == 2


@pytest.mark.parametrize("product_id,valid", [("P001", True), ("INVENTED", False)])
def test_real_sdk_structured_parse_and_business_validation(product_id, valid):
    def handler(request):
        body = json.loads(request.content)
        assert body["text"]["format"]["type"] == "json_schema"
        assert body["text"]["format"]["strict"] is True
        recommendation = {
            "product_ids": [product_id],
            "explanation": "Prueba offline",
            "needs_clarification": False,
            "mode": "live",
        }
        return httpx.Response(200, json=response_payload([message(json.dumps(recommendation))]))

    products = StoreTools(create_store()).search_products("auriculares", 80)
    with client_for(handler) as client:
        if valid:
            result = recommend_structured(
                products, "auriculares", live=True, client=client, model="test-model"
            )
            assert result.product_ids == ["P001"]
        else:
            with pytest.raises(ValueError, match="invented"):
                recommend_structured(
                    products, "auriculares", live=True, client=client, model="test-model"
                )
