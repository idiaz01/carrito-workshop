"""S5 · Reto: tu agente desde cero (mi_agente/desde_cero.py), con LangChain.

Ejecuta tus CASOS con tus evaluadores y tu juez, en la terminal o como experimento
en LangSmith. Cada caso empieza una conversación nueva.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor

from carrito.cases import check_case
from carrito.model import load_settings
from carrito.student import load_student_module

TEMPLATE = "desde_cero"


def load():
    module = load_student_module(TEMPLATE)
    if module is None:
        raise SystemExit("Falta mi_agente/desde_cero.py. Ejecuta: git pull")
    for name in ("crear_agente", "CASOS"):
        if not hasattr(module, name):
            raise SystemExit(f"mi_agente/desde_cero.py: falta {name}.")
    return module


def default_model():
    from langchain_openai import ChatOpenAI

    load_settings()
    return ChatOpenAI(model=os.environ["OPENAI_MODEL"], use_responses_api=True)


def new_agent(module, model=None):
    return module.crear_agente(model or default_model())


def ask(agent, messages, text):
    """One turn. `messages` is the conversation so far; it grows with this turn."""
    before = len(messages)
    result = agent.invoke({"messages": [*messages, {"role": "user", "content": text}]})
    messages[:] = result["messages"]
    new = messages[before:]
    tools, evidence, tokens = [], [], 0
    for message in new:
        if message.type == "ai":
            usage = message.usage_metadata or {}
            tokens += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            tools += [call["name"] for call in message.tool_calls]
        elif message.type == "tool":
            evidence.append(f"{message.name}: {_text(message.content)[:400]}")
    answer = next((_text(m.content) for m in reversed(new) if m.type == "ai"), "")
    return {"answer": answer, "tools": tools, "evidence": evidence, "tokens": tokens}


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # Responses API: a list of blocks
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return json.dumps(content, ensure_ascii=False)


def run_case(module, turns, model=None):
    """A fresh conversation with the agent for the turns of one case."""
    agent = new_agent(module, model)
    messages, tools, evidence, tokens, answer = [], [], [], 0, ""
    for text in turns:
        turn = ask(agent, messages, text)
        answer = turn["answer"]
        tools += turn["tools"]
        evidence += turn["evidence"]
        tokens += turn["tokens"]
    return {"respuesta": answer, "tools": tools, "datos": "\n".join(evidence), "tokens": tokens}


def evaluators(module, with_judge=True, model=None):
    """checks + tokens + the Lab 3 evaluators named in EVALUADORES + the judge (JUEZ)."""
    found = [_checks, _tokens]
    lab3 = load_student_module("evaluadores")
    for name in getattr(module, "EVALUADORES", []):
        function = getattr(lab3, name, None) if lab3 else None
        if function is None or not _works(function):
            continue

        def wrapped(inputs, outputs, reference_outputs, function=function, name=name):
            return {"key": name, **function(outputs["respuesta"], outputs["tools"])}

        found.append(wrapped)
    rubric = getattr(module, "JUEZ", "").strip()
    if with_judge and rubric:

        def judge(inputs, outputs, reference_outputs):
            from carrito.experimentos import judge as llm_judge

            verdict = llm_judge(
                " / ".join(inputs["turns"]),
                outputs["respuesta"],
                outputs.get("datos", ""),
                model=model,
                rubric=rubric,
            )
            return {
                "key": "juez",
                "score": int(verdict.veredicto == "bien"),
                "comment": verdict.motivo,
            }

        found.append(judge)
    return found


def _works(function):
    try:
        function("Una frase.", [])
        return True
    except Exception:  # noqa: BLE001 - NotImplementedError or a bug: not used
        return False


def _checks(inputs, outputs, reference_outputs):
    failures = check_case(
        {"checks": reference_outputs["checks"]}, outputs["respuesta"], outputs["tools"]
    )
    return {"key": "checks", "score": int(not failures), "comment": "; ".join(failures) or "ok"}


def _tokens(inputs, outputs, reference_outputs):
    return {"key": "tokens", "score": outputs["tokens"]}


def local(module, only=None, with_judge=True, model=None):
    """Every case of CASOS, four at a time. Returns one row per case."""
    cases = [c for c in module.CASOS if not only or c["id"] in only]
    active = evaluators(module, with_judge, model)

    def one(case):
        outputs = run_case(module, case["turns"], model)
        reference = {"checks": case["checks"]}
        scores = [e({"turns": case["turns"]}, outputs, reference) for e in active]
        return {"id": case["id"], "respuesta": outputs["respuesta"], "scores": scores}

    if model is not None:  # a fixture model answers in order
        return [one(case) for case in cases]
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(one, cases))


def render(rows):
    keys = [s["key"] for s in rows[0]["scores"]] if rows else []
    lines = ["Caso  " + "  ".join(f"{k:>12}" for k in keys)]
    notes = []
    for row in rows:
        cells = [f"{s['score']:>12}" for s in row["scores"]]
        lines.append(f"{row['id']:<5} " + "  ".join(cells))
        for s in row["scores"]:
            if s["key"] != "tokens" and not s["score"]:
                notes.append(f"  {row['id']} · {s['key']}: {s.get('comment', '')}")
    if notes:
        lines += ["", "Por qué fallan:"] + notes
    totals = []
    for key in keys:
        if key != "tokens":
            values = [s["score"] for r in rows for s in r["scores"] if s["key"] == key]
            totals.append(f"{key} {sum(values)}/{len(values)}")
    lines.append("\nTOTAL: " + " · ".join(totals))
    return "\n".join(lines)


def experiment(module, name="reto", repetitions=1, with_judge=True):
    """The same evaluation, as an experiment in LangSmith (dataset reto-<your project>)."""
    from langsmith import evaluate

    from carrito.experimentos import upload_cases

    load_settings()
    dataset = f"reto-{os.getenv('LANGSMITH_PROJECT', 'carrito')}"
    print(upload_cases(dataset, module.CASOS, "Reto S5: tu agente desde cero"))

    def target(inputs):
        return run_case(module, inputs["turns"])

    return evaluate(
        target,
        data=dataset,
        evaluators=evaluators(module, with_judge),
        experiment_prefix=name,
        num_repetitions=repetitions,
        max_concurrency=4,
    )


def chat(module):
    """Talk to your agent in the terminal. Each turn shows the tools it used."""
    agent = new_agent(module)
    messages = []
    print("Tu agente desde cero. Escribe /salir para terminar.")
    while True:
        try:
            text = input("Tú> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text in {"/salir", "salir", "exit"}:
            break
        if not text:
            continue
        turn = ask(agent, messages, text)
        for name in turn["tools"]:
            print(f"  → {name}")
        print(f"Agente> {turn['answer']}  ({turn['tokens']} tokens)\n")
