"""Native Responses API, session-key helpers and scripted models for tests."""

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

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


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
# CI and tests only: replaces the API with a fake client. Students never set it.
OFFLINE_CHECK = "CARRITO_OFFLINE_CHECK"

API_ERRORS = {
    "AuthenticationError": (
        "La clave no es válida o ya caducó. Copia la clave de hoy en .env y repite la celda."
    ),
    "PermissionDeniedError": "La clave no tiene acceso a este modelo. Avisa al docente.",
    "NotFoundError": "El modelo de OPENAI_MODEL no existe o no está disponible. Revisa .env.",
    "RateLimitError": (
        "Límite de uso alcanzado. Espera un minuto y repite. Si sigue, avisa al docente."
    ),
    "APIConnectionError": "No hay conexión con la API. Revisa la red y repite.",
    "APITimeoutError": "La API tardó demasiado. Repite la celda.",
    "BadRequestError": "La API rechazó la petición. Revisa que OPENAI_MODEL admite esta función.",
}


def load_settings():
    """Read .env on every call: a new session key works without a kernel restart."""
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE, override=True)


def _rejects_reasoning_include(exc: Exception) -> bool:
    if type(exc).__name__ != "BadRequestError":
        return False
    body = getattr(exc, "body", None)
    text = (body.get("message") if isinstance(body, dict) else None) or str(exc)
    return "encrypted_content" in text or "include" in text


def offline_check() -> bool:
    return os.getenv(OFFLINE_CHECK) == "1"


def explain_api_error(exc: Exception, detail: bool = False) -> str:
    """Short Spanish message for students. Never includes the key."""
    name = type(exc).__name__
    message = API_ERRORS.get(name, f"Error de la API ({name}). Repite; si sigue, avisa al docente.")
    if detail and name in {"BadRequestError", "NotFoundError"}:
        body = getattr(exc, "body", None)
        text = body.get("message") if isinstance(body, dict) else None
        if text:
            message += f" Detalle: {text}"
    return message


# The course writes instructions with role "system" (common to most providers).
# OpenAI also calls this level "developer". If a model rejects "system", retry once
# with "developer" and keep using it for the rest of the process.
_ROLE = {"developer": False}


def _rejects_system_role(exc: Exception) -> bool:
    if type(exc).__name__ != "BadRequestError":
        return False
    body = getattr(exc, "body", None)
    text = ((body.get("message") if isinstance(body, dict) else None) or str(exc)).lower()
    return "system" in text and "role" in text


def _as_developer(items):
    if not isinstance(items, list):
        return items
    return [
        {**item, "role": "developer"}
        if isinstance(item, dict) and item.get("role") == "system"
        else item
        for item in items
    ]


class _RoleFallbackResponses:
    def __init__(self, inner):
        self._inner = inner

    def _call(self, method, **request):
        if _ROLE["developer"]:
            request["input"] = _as_developer(request.get("input"))
        try:
            return method(**request)
        except Exception as exc:
            if _ROLE["developer"] or not _rejects_system_role(exc):
                raise
            _ROLE["developer"] = True
            request["input"] = _as_developer(request.get("input"))
            return method(**request)

    def create(self, **request):
        return self._call(self._inner.create, **request)

    def parse(self, **request):
        return self._call(self._inner.parse, **request)


class _RoleFallbackClient:
    def __init__(self, inner):
        self._inner = inner
        self.responses = _RoleFallbackResponses(inner.responses)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def make_client():
    if offline_check():
        from carrito.offline import OfflineClient

        return OfflineClient()
    from openai import OpenAI

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Falta OPENAI_API_KEY en .env. Pega la clave de la sesión y repite.")
    return _RoleFallbackClient(OpenAI())


class OpenAIModel:
    mode = "live"

    def __init__(self, client=None, model: str | None = None):
        load_settings()
        self.model = model or os.environ.get("OPENAI_MODEL")
        if not self.model and offline_check():
            self.model = "offline-check"
        if not self.model:
            raise RuntimeError("Falta OPENAI_MODEL en .env. Copia la línea de .env.example.")
        self.client = client or make_client()

    include_reasoning = True

    def respond(self, messages: list[dict], tools: list[dict]) -> ModelTurn:
        request = {
            "model": self.model,
            "input": messages,
            "max_output_tokens": 1200,
            "store": False,
        }
        if tools:
            request["tools"] = tools
        if self.include_reasoning:
            request["include"] = ["reasoning.encrypted_content"]
        try:
            response = self.client.responses.create(**request)
        except Exception as exc:
            # Non-reasoning models may reject the reasoning include: retry once without it.
            if not (self.include_reasoning and _rejects_reasoning_include(exc)):
                raise
            self.include_reasoning = False
            request.pop("include")
            response = self.client.responses.create(**request)
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
                "role": "system",
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
    """Session 1: one native request, no tools, no loop."""
    adapter = OpenAIModel(client=client, model=model)
    try:
        response = adapter.client.responses.create(
            model=adapter.model,
            input=messages,
            max_output_tokens=800,
            store=False,
        )
    except Exception as exc:
        if type(exc).__module__.startswith("openai"):
            raise RuntimeError(explain_api_error(exc, detail=True)) from None
        raise
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


def live_check(client=None) -> dict:
    """One short call through the same path as the agent. Run it at the start of class."""
    started = perf_counter()
    try:
        model = OpenAIModel(client=client)
        turn = model.respond([{"role": "user", "content": "Responde solo: OK"}], [])
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(explain_api_error(exc, detail=True)) from None
    if turn.status != "completed":
        raise RuntimeError(f"La API respondió con estado {turn.status}. Avisa al docente.")
    return {
        "api": "OK",
        "model": model.model,
        "latency_s": round(perf_counter() - started, 1),
        "answer": turn.text.strip()[:40],
    }
