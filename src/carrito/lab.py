"""One configurable application for S2–S5; fixtures exercise mechanisms only."""

import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from carrito.agent import SYSTEM_PROMPT, run_agent
from carrito.context import ConversationState, compose_context
from carrito.model import FixtureModel, OpenAIModel
from carrito.store import create_store
from carrito.tools import StoreTools


@dataclass(frozen=True)
class AgentProfile:
    name: str = "shopping-assistant"
    instructions: str = "Ayuda a comparar productos según necesidades y presupuesto."
    allowed_tools: tuple[str, ...] = ("search_products", "search_policies", "get_order")
    max_steps: int = 4
    max_tool_calls: int = 6
    enable_skills: bool = False


def catalog_response(products, improved=True):
    """A deterministic contract, not a claim about LLM writing quality."""
    if improved and not products:
        return {
            "status": "no_match",
            "product_ids": [],
            "explanation": "No hay coincidencias. ¿Quieres cambiar presupuesto o categoría?",
            "missing_information": ["alternative_preference"],
        }
    return {
        "status": "recommend",
        "product_ids": [p["product_id"] for p in products],
        "explanation": "Productos encontrados en el catálogo.",
        "missing_information": [],
    }


def trace_metrics(result, input_eur_per_million=None, output_eur_per_million=None):
    responses = [event for event in result["events"] if event["type"] == "model_response"]
    tool_events = [event for event in result["events"] if event["type"] == "tool_result"]
    inputs = sum(e["usage"].get("input_tokens", 0) for e in responses)
    outputs = sum(e["usage"].get("output_tokens", 0) for e in responses)
    cost = None
    if (
        result.get("mode") == "live"
        and input_eur_per_million is not None
        and output_eur_per_million is not None
    ):
        cost = (inputs * input_eur_per_million + outputs * output_eur_per_million) / 1e6
    return {
        "model_calls": len(responses),
        "tool_calls": len(tool_events),
        "tool_latency_ms": round(sum(e.get("latency_ms", 0) for e in tool_events), 3),
        "tool_errors": sum(
            isinstance(e["result"], dict) and "error" in e["result"] for e in tool_events
        ),
        "input_tokens": inputs,
        "output_tokens": outputs,
        "model_latency_ms": round(sum(e["latency_ms"] for e in responses), 3),
        "estimated_cost_eur": cost,
        "cost_note": (
            "Unknown unless LIVE usage and explicit dated prices supplied. "
            "Cached/reasoning pricing may require a richer calculation."
        ),
    }


def run_profile(
    question, tools, model, profile=None, state=None, evidence=None, response_builder=None
):
    profile = profile or AgentProfile()
    state = state or ConversationState()
    pack = compose_context(question, state, evidence or [])
    messages = pack["messages"]
    messages[0]["content"] = (
        SYSTEM_PROMPT + "\n" + profile.instructions + "\n" + messages[0]["content"]
    )
    started = perf_counter()
    result = run_agent(
        messages[1]["content"],
        tools,
        model,
        history=messages[:1],
        allowed_tools=profile.allowed_tools,
        max_steps=profile.max_steps,
        max_tool_calls=profile.max_tool_calls,
        enable_skills=profile.enable_skills,
    )
    result["profile"] = profile.name
    result["model_answer"] = result["answer"]
    result["context"] = {k: v for k, v in pack.items() if k != "messages"}
    searches = [
        e["result"]
        for e in result["events"]
        if e["type"] == "tool_result"
        and e["name"] == "search_products"
        and isinstance(e["result"], list)
    ]
    if response_builder is not None and searches and result["status"] == "completed":
        result["contract"] = response_builder(searches[-1])
        result["answer"] = result["contract"]["explanation"]
        result["events"].append({"type": "response_contract", "result": result["contract"]})
    result["metrics"] = trace_metrics(result)
    result["metrics"]["run_latency_ms"] = round((perf_counter() - started) * 1000, 3)
    return result


def compare_contracts(builder=None, profile=None, cases=None, mode="fixture"):
    if mode not in {"fixture", "live"}:
        raise ValueError("mode must be fixture or live")
    from carrito.context import validate_recommendation

    before, after = [], []
    cases = cases or [("auriculares", 80), ("telescopio", 80), ("teclado", 60), ("monitor", 20)]
    for rows, improved in [(before, False), (after, True)]:
        for query, budget in cases:
            tools = StoreTools(create_store())
            call = {
                "type": "function_call",
                "call_id": "catalog",
                "name": "search_products",
                "arguments": json.dumps({"query": query, "max_price_eur": budget}),
            }
            model = (
                OpenAIModel()
                if mode == "live"
                else FixtureModel([[call], []], "[FIXTURE] Inspecciona evidencia.")
            )
            response_builder = (
                builder
                if improved and builder
                else lambda products, fixed=improved: catalog_response(products, fixed)
            )
            result = run_profile(
                f"{query} por menos de {budget}",
                tools,
                model,
                profile,
                ConversationState(category=query, budget_eur=budget),
                response_builder=response_builder,
            )
            products = tools.search_products(query, budget)
            check = validate_recommendation(result.get("contract", {}), products, budget)
            rows.append(
                {
                    "query": query,
                    "passed": check["passed"],
                    "checks": check["checks"],
                    "trace": result,
                }
            )
            tools.db.close()
    return {
        "before": before,
        "after": after,
        "before_passed": sum(r["passed"] for r in before),
        "after_passed": sum(r["passed"] for r in after),
        "total": len(cases),
        "model_quality_measured": False,
        "scope": "Observed catalog + application contract; final response requires human review",
        "model_calls_live": mode == "live",
    }


def save_state(path, state):
    Path(path).write_text(state.model_dump_json(indent=2))


def load_state(path):
    return ConversationState.model_validate_json(Path(path).read_text())


def recover_read(operation, attempts=2):
    """Retry only an explicitly transient read. Never use for blind write retries."""
    if attempts < 1 or attempts > 3:
        raise ValueError("Use 1 to 3 bounded attempts")
    observations = []
    for _ in range(attempts):
        result = operation()
        observations.append(result)
        if not isinstance(result, dict) or result.get("error") != "temporary_unavailable":
            break
    return {"result": result, "attempts": observations}
