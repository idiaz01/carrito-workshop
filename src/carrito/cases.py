"""S2 scoreboard: run the cases of evals/s2_casos.jsonl against the student's agent."""

import json
from datetime import datetime
from pathlib import Path

from carrito.student import ROOT, StudentAgent

CASES = ROOT / "evals" / "s2_casos.jsonl"
RESULTS = ROOT / "runtime" / "casos"


def load_cases(path=CASES):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def check_case(case, answer, tools_called):
    text = answer.lower()
    failures = []
    for check in case["checks"]:
        kind = check["type"]
        values = [v.lower() for v in check.get("values", [])]
        if kind == "tool_called" and check["name"] not in tools_called:
            failures.append(f"no llamó a {check['name']}")
        elif kind == "tool_not_called" and check["name"] in tools_called:
            failures.append(f"llamó a {check['name']}")
        elif kind == "no_tools" and tools_called:
            failures.append("usó tools: " + ", ".join(tools_called))
        elif kind == "contains":
            missing = [v for v in check["values"] if v.lower() not in text]
            if missing:
                failures.append("falta " + ", ".join(missing))
        elif kind == "contains_any" and not any(v in text for v in values):
            failures.append("no dice: " + " / ".join(check["values"][:3]) + "…")
        elif kind == "not_contains":
            found = [v for v in check["values"] if v.lower() in text]
            if found:
                failures.append("dice " + ", ".join(found))
        elif kind == "max_chars" and len(answer) > check["value"]:
            failures.append(f"{len(answer)} caracteres (máx. {check['value']})")
    return failures


def run_cases(model_factory=None, only=None, on_turn=None):
    """Each case starts a fresh conversation and a fresh store."""
    rows = []
    for case in load_cases():
        if only and case["id"] not in only:
            continue
        agent = StudentAgent(model=model_factory() if model_factory else None, warn=lambda m: None)
        answer, tools_called, tokens, estimated = "", [], 0, 0
        try:
            for turn, text in enumerate(case["turns"], 1):
                result = agent.ask(text)
                answer = result["answer"]
                report = result["report"]
                tools_called += [c["name"] for c in report["calls"]]
                tokens += report["input_tokens"] + report["output_tokens"]
                estimated += sum(report["blocks"].values())
                if on_turn:
                    on_turn(case, turn, text, result)
        finally:
            agent.close()
        failures = check_case(case, answer, tools_called)
        rows.append(
            {
                "id": case["id"],
                "spec": case["spec"],
                "passed": not failures,
                "failures": failures,
                "tokens": tokens or estimated,
                "answer": answer,
                "tools": tools_called,
            }
        )
    return {
        "passed": sum(r["passed"] for r in rows),
        "total": len(rows),
        "tokens": sum(r["tokens"] for r in rows),
        "cases": rows,
    }


def save_report(report):
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for name in (f"{stamp}.json", "ultimo.json"):
        (RESULTS / name).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return RESULTS / f"{stamp}.json"


def render_table(report):
    lines = [f"{'Caso':<5} {'Spec':<20} {'':<3} {'Tokens':>7}  Motivo"]
    for row in report["cases"]:
        mark = "✅" if row["passed"] else "❌"
        reason = "; ".join(row["failures"])
        lines.append(f"{row['id']:<5} {row['spec']:<20} {mark:<3} {row['tokens']:>7}  {reason}")
    lines.append(
        f"\nMARCADOR: {report['passed']}/{report['total']} casos · {report['tokens']} tokens"
    )
    return "\n".join(lines)
