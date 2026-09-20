"""Inspect observed results and store state, never substitute expected outputs."""

import json

from carrito.agent import run_agent
from carrito.model import FixtureModel, OpenAIModel
from carrito.store import ROOT, create_store
from carrito.tools import StoreTools


def load_cases(split="dev"):
    if split != "dev":
        raise ValueError(f"Unknown dataset: {split}")
    lines = (ROOT / "evals/dev.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines if line]


def check_case(case, result, tools):
    events = [e for e in result["events"] if e["type"] == "tool_result"]
    outputs = [e["result"] for e in events]
    checks = {"completed": result["status"] == "completed"}
    kind = case["check"]
    if kind == "catalog":
        rows = [
            row
            for e in events
            if e["name"] == "search_products" and isinstance(e["result"], list)
            for row in e["result"]
        ]
        known = {r[0] for r in tools.db.execute("SELECT product_id FROM products")}
        prices = dict(tools.db.execute("SELECT product_id,price_cents FROM products"))
        checks["correct_prices"] = bool(rows) and all(
            r.get("price_cents") == prices.get(r.get("product_id")) for r in rows
        )
        checks["existing_ids"] = bool(rows) and all(r.get("product_id") in known for r in rows)
        checks["budget"] = bool(rows) and all(
            r.get("price_cents", 10**9) <= case["budget"] * 100 for r in rows
        )
        checks["expected_candidate"] = case["required_id"] in [r.get("product_id") for r in rows]
    elif kind == "empty_catalog":
        checks["empty_retrieval"] = any(
            e["name"] == "search_products" and e["result"] == [] for e in events
        )
    elif kind == "order":
        checks["authorized_order"] = any(
            isinstance(o, dict)
            and o.get("order_id") == case["order_id"]
            and o.get("user_id") == tools.user_id
            for o in outputs
        )
    elif kind == "error":
        checks["expected_error_observed"] = any(
            isinstance(o, dict) and o.get("error") == case["error"] for o in outputs
        )
        authorized_ids = {
            row[0]
            for row in tools.db.execute(
                "SELECT order_id FROM orders WHERE user_id=?", (tools.user_id,)
            )
        }
        # A legitimate preflight read may precede a rejected return. Reject only
        # foreign identity or order data, even if user_id was omitted from a leak.
        checks["no_disclosed_order"] = not any(
            isinstance(o, dict)
            and (
                ("user_id" in o and o["user_id"] != tools.user_id)
                or ("order_id" in o and "error" not in o and o["order_id"] not in authorized_ids)
            )
            for o in outputs
        )
    elif kind == "policy":
        checks["source_retrieved"] = any(
            isinstance(o, list) and any(r.get("source_id") == case["source_id"] for r in o)
            for o in outputs
        )
    elif kind == "pending":
        checks["confirmation_requested"] = any(
            isinstance(o, dict) and o.get("status") == "confirmation_required" for o in outputs
        )
    elif kind in {"requested", "idempotent"}:
        expected = case["fixture_calls"][0]["arguments"]
        persisted = tools.db.execute(
            "SELECT order_id, reason, user_id FROM return_requests"
        ).fetchall()
        checks["exact_persisted_payload"] = len(persisted) == 1 and tuple(persisted[0]) == (
            expected["order_id"],
            expected["reason"],
            tools.user_id,
        )
        checks["one_persisted_request"] = tools.return_count() == 1
        checks["observed_requested"] = any(
            isinstance(o, dict) and o.get("status") == "requested" for o in outputs
        )
        checks["no_write_before_host_confirmation"] = result.get("count_before_confirmation") == 0
        if kind == "idempotent":
            ids = [
                o["request_id"]
                for o in outputs
                if isinstance(o, dict) and o.get("status") == "requested"
            ]
            checks["same_request_id"] = len(ids) >= 2 and len(set(ids)) == 1
    elif kind == "clarification":
        checks["no_unjustified_tools"] = not events
        checks["nonempty_answer"] = bool(result.get("answer", "").strip())
    if kind not in {"requested", "idempotent"}:
        checks["no_write"] = tools.return_count() == 0
    return {
        "id": case["id"],
        "passed": all(checks.values()),
        "checks": checks,
        "human_review": "pending: grounding, clarification, answer vs tool result",
    }


def run_evals(split="dev", mode="fixture", trace_dir=None):
    reports = []
    for case in load_cases(split):
        tools = StoreTools(create_store())
        if mode == "fixture":
            calls = [
                {
                    "type": "function_call",
                    "call_id": f"fixture_{i}",
                    "name": c["name"],
                    "arguments": json.dumps(c["arguments"]),
                }
                for i, c in enumerate(case["fixture_calls"])
            ]
            text = (
                "[FIXTURE] ¿Qué número de pedido quieres consultar?"
                if not calls
                else "[FIXTURE] Revisa el resultado observado de las tools."
            )
            model = FixtureModel([calls, []], text)
        else:
            model = OpenAIModel()
        trace = str(trace_dir / f"{case['id']}.jsonl") if trace_dir else None
        result = run_agent(case["prompt"], tools, model, trace_path=trace)
        result["count_before_confirmation"] = tools.return_count()
        if case.get("confirm") and tools.pending:
            # Test host simulates an explicit click on the displayed concrete payload.
            payload = tools.pending
            host_event = tools.confirm_pending()
            result["events"].append({"type": "host_confirmation", "result": host_event})
            for _ in range(2 if case.get("repeat") else 1):
                output = tools.request_return(*payload)
                result["events"].append(
                    {"type": "tool_result", "name": "request_return", "result": output}
                )
            if trace:
                with open(trace, "a") as handle:
                    handle.write(
                        json.dumps(
                            {"type": "eval_host_followup", "events": result["events"][-3:]},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
        reports.append(check_case(case, result, tools))
        tools.db.close()
    return {
        "mode": mode,
        "split": split,
        "total": len(reports),
        "passed": sum(r["passed"] for r in reports),
        "model_quality_measured": mode == "live",
        "scope": (
            "Tool/state checks only; final response quality requires human review. "
            "Host confirmations scripted."
        ),
        "cases": reports,
    }
