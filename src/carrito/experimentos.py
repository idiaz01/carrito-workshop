"""S5 · Evals de tu agente: dataset y experimentos en LangSmith, evaluadores y un juez LLM.

- Dataset: los casos de S2, S3 y S4, más los tuyos (mi_agente/casos.jsonl).
- Evaluadores: los checks de cada caso, los tokens, tus evaluadores de código
  (mi_agente/evaluadores.py) y, si quieres, un juez LLM con tu rúbrica (mi_agente/juez.md).
- `local` hace lo mismo sin LangSmith y lo enseña en la terminal.
"""

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from carrito import diseno
from carrito.cases import SESSIONS, check_case, load_cases
from carrito.model import OpenAIModel, load_settings
from carrito.store import ROOT
from carrito.student import FOLDER, StudentAgent, _read, load_student_module

CALIBRATION = ROOT / "evals" / "s5_juez.jsonl"
DEFAULT_RUBRIC = "Di si la respuesta es buena."


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
def dataset_cases():
    cases = [c for s in (2, 3, 4, 5) for path in SESSIONS[s] for c in load_cases(path)]
    own = FOLDER / "casos.jsonl"
    if own.exists():
        cases += load_cases(own)
    return cases


def dataset_name():
    load_settings()
    return f"carrito-{os.getenv('LANGSMITH_PROJECT', 'carrito')}"


def upload():
    """Create (or update) the dataset in LangSmith.

    New cases are added. A case you changed (for example, M2 in casos.jsonl) is updated.
    A case you deleted is deleted. So the dataset is always the same as your files.
    """
    return upload_cases(dataset_name(), dataset_cases(), "Casos de Carrito (S2-S5)")


def upload_cases(name, cases, description=""):
    """The dataset `name` in LangSmith, the same as `cases`: add, update and delete."""
    from langsmith import Client

    client = Client()
    if client.has_dataset(dataset_name=name):
        dataset = client.read_dataset(dataset_name=name)
        known = {
            (e.metadata or {}).get("id"): e for e in client.list_examples(dataset_id=dataset.id)
        }
    else:
        dataset = client.create_dataset(name, description=description)
        known = {}
    new, changed = [], 0
    for case in cases:
        inputs = {"turns": case["turns"]}
        outputs = {"checks": case["checks"], "spec": case.get("spec", "")}
        example = known.get(case["id"])
        if example is None:
            new.append({"inputs": inputs, "outputs": outputs, "metadata": {"id": case["id"]}})
        elif example.inputs != inputs or example.outputs != outputs:
            client.update_example(example.id, inputs=inputs, outputs=outputs)
            changed += 1
    if new:
        client.create_examples(dataset_id=dataset.id, examples=new)
    ids = {c["id"] for c in cases}
    gone = [e.id for case_id, e in known.items() if case_id not in ids]
    for example_id in gone:
        client.delete_example(example_id)
    return {
        "dataset": name,
        "nuevos": len(new),
        "cambiados": changed,
        "borrados": len(gone),
        "total": len(cases),
    }


# ---------------------------------------------------------------------------
# Target: one fresh conversation per example
# ---------------------------------------------------------------------------
def run_case(inputs, model=None):
    agent = StudentAgent(model=model, warn=lambda m: None)
    answer, tools, tokens, status, salida = "", [], 0, "completed", None
    evidence = []  # what the tools gave the model: the judge needs it to check DAT-1
    try:
        for text in inputs["turns"]:
            result = agent.ask(text)
            report = result["report"]
            answer, status = result["answer"], result["status"]
            tools += [c["name"] for c in report["calls"]]
            evidence += [f"{c['name']}: {c['model_sees']}" for c in report["calls"]]
            tokens += report["input_tokens"] + report["output_tokens"]
            salida = report.get("salida")
    finally:
        agent.close()
    return {
        "respuesta": answer,
        "tools": tools,
        "tokens": tokens,
        "estado": status,
        "salida": salida,
        "datos": "\n".join(evidence),
    }


# ---------------------------------------------------------------------------
# Evaluators. LangSmith calls them with (inputs, outputs, reference_outputs).
# ---------------------------------------------------------------------------
def checks(inputs, outputs, reference_outputs):
    failures = check_case(
        {"checks": reference_outputs["checks"]},
        outputs["respuesta"],
        outputs["tools"],
        {"tokens": outputs["tokens"], "salida": outputs.get("salida")},
    )
    return {"key": "checks", "score": int(not failures), "comment": "; ".join(failures) or "ok"}


def tokens(inputs, outputs, reference_outputs):
    return {"key": "tokens", "score": outputs["tokens"]}


def student_evaluators():
    """Each function of mi_agente/evaluadores.py that is written (no NotImplementedError)."""
    module = load_student_module("evaluadores")
    found = []
    for name in getattr(module, "EVALUADORES", []):
        function = getattr(module, name, None)
        try:
            function("Te recomiendo P001.", ["search_products"])
        except NotImplementedError:
            continue
        except Exception:  # noqa: BLE001 - a broken evaluator is skipped, not fatal
            continue

        def wrapped(inputs, outputs, reference_outputs, function=function, name=name):
            result = function(outputs["respuesta"], outputs["tools"])
            return {"key": name, **result}

        wrapped.__name__ = name
        found.append(wrapped)
    return found


class Veredicto(BaseModel):
    veredicto: Literal["bien", "mal"]
    motivo: str


def judge(question, answer, evidence="", model=None, rubric=None):
    """LLM-as-judge with your rubric (mi_agente/juez.md). Structured output: bien / mal.

    rubric: another rubric, for example the JUEZ of mi_agente/desde_cero.py (reto)."""
    rubric = rubric or _read("juez.md") or DEFAULT_RUBRIC
    model = model or OpenAIModel()
    messages = [
        {"role": "system", "content": rubric},
        {
            "role": "user",
            "content": f"Pregunta del cliente:\n{question}\n\nDatos de las tools:\n"
            f"{evidence or '(ninguno)'}\n\nRespuesta del agente:\n{answer}",
        },
    ]
    turn = model.respond(messages, [], text_format=diseno.strict_schema(Veredicto))
    try:
        return Veredicto.model_validate_json(turn.text)
    except Exception:  # noqa: BLE001
        return Veredicto(veredicto="mal", motivo=f"El juez no siguió el formato: {turn.text[:80]}")


def judge_evaluator(inputs, outputs, reference_outputs):
    verdict = judge(" / ".join(inputs["turns"]), outputs["respuesta"], outputs.get("datos", ""))
    return {"key": "juez", "score": int(verdict.veredicto == "bien"), "comment": verdict.motivo}


def calibrate(model=None, path=CALIBRATION):
    """Compare the judge with human labels: a judge is a system that needs evaluating too.

    The judge reads the answers four at a time (about 15 seconds for 20 answers).
    """
    from concurrent.futures import ThreadPoolExecutor

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    items = [json.loads(line) for line in lines if line.strip()]

    def one(item):
        verdict = judge(item["pregunta"], item["respuesta"], item.get("datos", ""), model)
        return {
            **item,
            "juez": verdict.veredicto,
            "motivo_juez": verdict.motivo,
            "acuerdo": verdict.veredicto == item["humano"],
        }

    if model is None:  # a real model: in parallel
        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(one, items))
    else:  # a fixture model answers in order
        rows = [one(item) for item in items]
    agree = sum(r["acuerdo"] for r in rows)
    return {"acuerdo": agree, "total": len(rows), "filas": rows}


def render_calibration(report):
    lines = [f"{'Caso':<4} {'Humano':<7} {'Juez':<6}  Motivo del juez"]
    for r in report["filas"]:
        mark = "✅" if r["acuerdo"] else "❌"
        lines.append(f"{r['id']:<4} {r['humano']:<7} {r['juez']:<6} {mark} {r['motivo_juez'][:90]}")
        if not r["acuerdo"]:
            lines.append(f"{'':<20}humano: {r['razon']}")
    lines.append(f"\nACUERDO JUEZ-HUMANO: {report['acuerdo']}/{report['total']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------
def evaluators(with_judge=False):
    found = [checks, tokens, *student_evaluators()]
    return found + ([judge_evaluator] if with_judge else [])


def experiment(name, repetitions=1, with_judge=False):
    from langsmith import evaluate

    print(upload())
    return evaluate(
        run_case,
        data=dataset_name(),
        evaluators=evaluators(with_judge),
        experiment_prefix=name,
        num_repetitions=repetitions,
        max_concurrency=4,
        metadata={"carpeta": str(FOLDER)},
    )


def summarize(results):
    """{case id: {evaluator: [scores]}} from the results of langsmith.evaluate."""
    table = {}
    for item in results:
        example = item["example"]
        case_id = (getattr(example, "metadata", None) or {}).get("id", "?")
        row = table.setdefault(case_id, {})
        for result in item["evaluation_results"]["results"]:
            if result.score is not None:
                row.setdefault(result.key, []).append(result.score)
    return table


def render_summary(table):
    """The experiment in the terminal: the cases that fail, and the total of each evaluator."""
    keys = sorted({k for row in table.values() for k in row if k != "tokens"})
    lines = []
    for case_id, row in sorted(table.items(), key=lambda kv: _order(kv[0])):
        bad = {k: v for k, v in row.items() if k != "tokens" and sum(v) < len(v)}
        if bad:
            cells = "  ".join(f"{k} {sum(v):g}/{len(v)}" for k, v in sorted(bad.items()))
            lines.append(f"  {case_id:<5} {cells}")
    head = ["Casos con algún fallo:"] if lines else ["Ningún caso falla."]
    totals = []
    for key in keys:
        values = [x for row in table.values() for x in row.get(key, [])]
        totals.append(f"{key} {sum(values):g}/{len(values)}")
    tokens = [x for row in table.values() for x in row.get("tokens", [])]
    if tokens:
        totals.append(f"tokens {round(sum(tokens) / len(tokens))} de media")
    return "\n".join(head + lines + ["TOTAL: " + " · ".join(totals)])


def _order(case_id):
    letter, number = case_id[:1], case_id[1:]
    return (letter, int(number) if number.isdigit() else 0)


def local(model_factory=None, only=None, with_judge=False):
    """The same evaluation without LangSmith, printed in the terminal."""
    rows = []
    active = evaluators(with_judge)
    for case in dataset_cases():
        if only and case["id"] not in only:
            continue
        outputs = run_case(
            {"turns": case["turns"]}, model=model_factory() if model_factory else None
        )
        reference = {"checks": case["checks"], "spec": case["spec"]}
        scores = [e({"turns": case["turns"]}, outputs, reference) for e in active]
        rows.append({"id": case["id"], "scores": scores})
    return rows


def render_local(rows):
    keys = [s["key"] for s in rows[0]["scores"]] if rows else []
    lines = ["Caso  " + "  ".join(f"{k:>12}" for k in keys)]
    for row in rows:
        cells = [f"{s['score']:>12}" for s in row["scores"]]
        lines.append(f"{row['id']:<5} " + "  ".join(cells))
    for key in keys:
        if key == "tokens":
            continue
        values = [s["score"] for r in rows for s in r["scores"] if s["key"] == key]
        lines.append(f"{key}: {sum(values)}/{len(values)}")
    return "\n".join(lines)
