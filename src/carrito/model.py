"""Native Responses API and explicitly labelled model-free fixtures."""

import copy
import json
import os
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


@dataclass
class ModelTurn:
    output: list[dict]
    text: str
    usage: dict
    model: str
    status: str = "completed"


def response_status(response, output):
    if any(
        part.get("type") == "refusal"
        for item in output
        for part in item.get("content", [])
        if isinstance(part, dict)
    ):
        return "refused"
    return getattr(response, "status", "completed")


class OpenAIModel:
    mode = "live"

    def __init__(self, client=None, model: str | None = None):
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        self.model = model or os.environ.get("OPENAI_MODEL")
        if not self.model:
            raise ValueError("Set OPENAI_MODEL explicitly before a live call.")
        self.client = client or OpenAI()

    def respond(self, messages: list[dict], tools: list[dict]) -> ModelTurn:
        response = self.client.responses.create(
            model=self.model,
            input=messages,
            tools=tools,
            include=["reasoning.encrypted_content"],
            max_output_tokens=1200,
            store=False,
        )
        output = [
            item if isinstance(item, dict) else item.model_dump(exclude_none=True)
            for item in response.output
        ]
        return ModelTurn(
            output,
            response.output_text,
            response.usage.model_dump() if response.usage else {},
            self.model,
            response_status(response, output),
        )


class FixtureModel:
    """Scripted API-shaped outputs; verifies plumbing, never model quality."""

    mode = "fixture"

    def __init__(
        self, turns: list[list[dict]] | None = None, final_text: str = "Fixture completada."
    ):
        self.turns = copy.deepcopy(turns if turns is not None else self._catalog())
        self.final_text = final_text
        self.index = 0

    @staticmethod
    def _catalog():
        return [
            [
                {
                    "type": "function_call",
                    "name": "search_products",
                    "arguments": json.dumps({"query": "auriculares", "max_price_eur": 80}),
                    "call_id": "fixture_catalog",
                }
            ],
            [],
        ]

    @classmethod
    def for_scenario(cls, scenario: str = "catalog"):
        cases = {
            "catalog": (
                "search_products",
                {"query": "auriculares", "max_price_eur": 80},
                "[FIXTURE] P001 · Auriculares Nube · 69,90 €. Bluetooth, batería 30 horas.",
            ),
            "order": (
                "get_order",
                {"order_id": "104"},
                "[FIXTURE] El pedido 104 consta como entregado el 12 de septiembre.",
            ),
            "policy": (
                "search_policies",
                {"query": "devolución 30 días"},
                "[FIXTURE] POL-DEV: plazo de 30 días desde la entrega.",
            ),
            "return": (
                "request_return",
                {"order_id": "104", "reason": "No encaja"},
                "[FIXTURE] Solicitud preparada para 104, motivo: No encaja. Falta confirmar.",
            ),
        }
        name, args, text = cases[scenario]
        call = {
            "type": "function_call",
            "name": name,
            "arguments": json.dumps(args),
            "call_id": "fixture_1",
        }
        return cls([[call], []], final_text=text)

    def respond(self, messages: list[dict], tools: list[dict]) -> ModelTurn:
        output = self.turns[self.index] if self.index < len(self.turns) else []
        self.index += 1
        return ModelTurn(
            output,
            "" if output else self.final_text,
            {"input_tokens": 0, "output_tokens": 0},
            "scripted-fixture",
        )


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_ids: list[str]
    explanation: str
    needs_clarification: bool
    mode: str


def recommend_structured(
    products: list[dict],
    question: str,
    live: bool = False,
    *,
    client=None,
    model: str | None = None,
) -> Recommendation:
    if not live:
        return Recommendation(
            product_ids=[p["product_id"] for p in products[:1]],
            explanation="Fixture: primer resultado suministrado; no evalúa al LLM.",
            needs_clarification=not bool(products),
            mode="fixture",
        )
    adapter = OpenAIModel(client=client, model=model)
    response = adapter.client.responses.parse(
        model=adapter.model,
        input=[
            {
                "role": "developer",
                "content": "Recommend only supplied product IDs; abstain if absent. Set mode=live.",
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"question": question, "products": products}, ensure_ascii=False
                ),
            },
        ],
        text_format=Recommendation,
        max_output_tokens=800,
        store=False,
    )
    if response.output_parsed is None:
        raise ValueError("No structured answer: inspect refusal or incomplete response.")
    result = response.output_parsed
    allowed = {p["product_id"] for p in products}
    if not set(result.product_ids) <= allowed:
        raise ValueError("Model invented a product ID")
    return result


def native_call(messages: list[dict], client=None, model: str | None = None) -> dict:
    """Session 1: one native request, no tools, no loop. This is a LIVE call."""
    adapter = OpenAIModel(client=client, model=model)
    response = adapter.client.responses.create(
        model=adapter.model,
        input=messages,
        max_output_tokens=800,
        store=False,
    )
    return {
        "output_text": response.output_text,
        "output": [
            item if isinstance(item, dict) else item.model_dump(exclude_none=True)
            for item in response.output
        ],
        "usage": response.usage.model_dump() if response.usage else {},
        "model": response.model,
        "status": getattr(response, "status", "completed"),
    }
