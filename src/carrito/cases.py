"""S2 scoreboard: run the cases of evals/s2_casos.jsonl against the student's agent."""

import json
from datetime import datetime
from pathlib import Path

from carrito.student import ROOT, StudentAgent

CASES = ROOT / "evals" / "s2_casos.jsonl"
RETO = ROOT / "evals" / "s2_reto.jsonl"
# The scoreboard of each session. S2 also has its reto (C9-C12).
SESSIONS = {
    2: [CASES],
    3: [ROOT / "evals" / "s3_casos.jsonl"],
    4: [ROOT / "evals" / "s4_casos.jsonl"],
}
RESULTS = ROOT / "runtime" / "casos"


def load_cases(path=CASES):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def check_case(case, answer, tools_called, info=None):
    """info (S4): {"tokens": tokens of the case, "salida": the Salida line of --debug}."""
    info = info or {}
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
        elif kind == "presupuesto" and info.get("tokens", 0) > check["value"]:
            failures.append(f"gastó {info['tokens']} tokens (máx. {check['value']})")
        elif kind == "salida":
            out = info.get("salida")
            if not out:
                failures.append("sin salida estructurada (salida.py)")
            elif out["problemas"] and not out["corregida"]:
                failures.append("revisar() encontró problemas sin corregir")
    return failures


def all_case_files():
    return [CASES, RETO] + [f for s, files in SESSIONS.items() if s != 2 for f in files]


def run_cases(model_factory=None, only=None, on_turn=None, reto=False, sesion=2, todos=False):
    """Each case starts a fresh conversation and a fresh store.

    sesion picks the scoreboard (2, 3...). reto=True adds the S2 challenge (C9-C12).
    todos=True runs every case of every session. --caso finds a case in any file.
    """
    if only or todos:
        files = all_case_files()
    else:
        files = list(SESSIONS[sesion]) + ([RETO] if reto and sesion == 2 else [])
    cases = [case for path in files if path.exists() for case in load_cases(path)]
    rows = []
    for case in cases:
        if only and case["id"] not in only:
            continue
        agent = StudentAgent(model=model_factory() if model_factory else None, warn=lambda m: None)
        answer, tools_called, tokens, estimated, salida = "", [], 0, 0, None
        try:
            for turn, text in enumerate(case["turns"], 1):
                result = agent.ask(text)
                answer = result["answer"]
                report = result["report"]
                tools_called += [c["name"] for c in report["calls"]]
                tokens += report["input_tokens"] + report["output_tokens"]
                estimated += sum(report["blocks"].values())
                salida = report.get("salida")
                if on_turn:
                    on_turn(case, turn, text, result)
        finally:
            agent.close()
        failures = check_case(
            case, answer, tools_called, {"tokens": tokens or estimated, "salida": salida}
        )
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


def last_two_reports(results=RESULTS):
    """The two most recent scoreboards saved in runtime/casos/ (oldest first)."""
    files = sorted(Path(results).glob("2*.json"))
    if len(files) < 2:
        return None
    return [(f.name, json.loads(f.read_text())) for f in files[-2:]]


def render_comparison(before, after):
    """Before/after view of two scoreboards: score, tokens and the cases that changed."""
    (name_a, a), (name_b, b) = before, after
    lines = [
        f"Antes:   {a['passed']}/{a['total']} casos · {a['tokens']} tokens  ({name_a})",
        f"Después: {b['passed']}/{b['total']} casos · {b['tokens']} tokens  ({name_b})",
    ]
    old = {row["id"]: row for row in a["cases"]}
    changes = []
    for row in b["cases"]:
        prev = old.get(row["id"])
        if prev is None or prev["passed"] == row["passed"]:
            continue
        arrow = "❌ → ✅" if row["passed"] else "✅ → ❌"
        changes.append(f"  {row['id']:<4} {arrow}  {row['spec']}")
    lines.append("Casos que cambian:" if changes else "Ningún caso cambia de resultado.")
    lines.extend(changes)
    return "\n".join(lines)
