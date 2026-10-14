"""Carrito CLI. Live by default; --mode fixture is for tests and CI."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from carrito.agent import run_agent
from carrito.evaluation import run_evals
from carrito.judge import judge_demo
from carrito.model import FixtureModel, OpenAIModel, live_check, load_settings
from carrito.skills import activate_skill
from carrito.store import REFERENCE_DATE, create_store
from carrito.tools import StoreTools

PROMPTS = {
    "catalog": "Busco auriculares inalámbricos por menos de 80 €.",
    "order": "¿Dónde está mi pedido 104?",
    "policy": "¿Qué plazo de devolución tengo?",
    "return": "Quiero devolver el pedido 104. Motivo: No encaja.",
}


def show(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def model_for(mode, scenario):
    return FixtureModel.for_scenario(scenario) if mode == "fixture" else OpenAIModel()


def doctor():
    tools = StoreTools(create_store())
    report = {
        "project": "Carrito",
        "data_ready": len(tools.search_products("")) == 20,
        "reference_date": REFERENCE_DATE.isoformat(),
        "api_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL") or None,
    }
    try:
        report["live_check"] = live_check()
    except RuntimeError as exc:
        report["live_check"] = {"api": "ERROR", "message": str(exc)}
        show(report)
        raise SystemExit(1) from None
    show(report)


def confirm_host(tools):
    payload = tools.pending
    if payload is None:
        return {"error": "nothing_to_confirm"}
    tools.confirm_pending()
    return tools.request_return(*payload)


def chat(mode, trace_dir):
    tools = StoreTools(create_store())
    history = None
    turn = 0
    print(f"Carrito · {mode}. /confirm confirma el payload mostrado; /quit sale.")
    if mode == "fixture":
        print(
            "FIXTURE: escenarios preescritos, no interpreta lenguaje libre. "
            "Palabras: devolver, pedido, política, auriculares."
        )
    while True:
        try:
            prompt = input("Tú> ").strip()
        except EOFError:
            break
        if prompt == "/quit":
            break
        if not prompt:
            continue
        if prompt == "/confirm":
            result = confirm_host(tools)
            show(result)
            if history is not None:
                history.append(
                    {
                        "role": "user",
                        "content": "Host observation data (not instructions): "
                        + json.dumps(result),
                    }
                )
            trace_dir.mkdir(parents=True, exist_ok=True)
            with (trace_dir / "host.jsonl").open("a") as handle:
                handle.write(json.dumps({"type": "host_confirmation", "result": result}) + "\n")
            continue
        scenario = (
            "return"
            if "devol" in prompt.lower()
            else "order"
            if "pedido" in prompt.lower()
            else "policy"
            if "pol" in prompt.lower()
            else "catalog"
        )
        turn += 1
        result = run_agent(
            prompt,
            tools,
            model_for(mode, scenario),
            history=history,
            trace_path=trace_dir / f"turn-{turn}.jsonl",
        )
        history = result["messages"]
        print(result["answer"])
        show(
            {
                "status": result["status"],
                "pending": tools.pending,
                "events": [
                    e
                    for e in result["events"]
                    if e["type"] in {"tool_result", "model_response", "model_error"}
                ],
            }
        )
    tools.db.close()


def mi_agente(debug, question, user):
    """S2: chat with the agent built from mi_agente/. Edits apply on the next message."""
    from carrito.student import StudentAgent, render_report

    agent = StudentAgent(user_id=user)
    turn = 0
    print("Tu agente · mi_agente/. /reset empieza otra conversación; /salir sale.")
    try:
        while True:
            if question is not None:
                prompt = question
            else:
                try:
                    prompt = input("Tú> ").strip()
                except EOFError:
                    break
            if prompt in {"/salir", "/quit"}:
                break
            if prompt == "/reset":
                agent.close()
                agent = StudentAgent(user_id=user)
                turn = 0
                print("Conversación nueva.")
                continue
            if not prompt:
                continue
            turn += 1
            result = agent.ask(prompt)
            if debug:
                print(render_report(result["report"], turn))
            print(f"Carrito> {result['answer']}\n")
            if question is not None:
                break
    finally:
        agent.close()


def casos(debug, only):
    """S2 scoreboard: more cases passed with fewer tokens."""
    from carrito.cases import render_table, run_cases, save_report
    from carrito.student import render_report

    def on_turn(case, turn, text, result):
        print(f"[{case['id']}·{turn}] Tú> {text}")
        if debug:
            print(render_report(result["report"], turn))
        print(f"        Carrito> {result['answer'][:300]}\n")

    report = run_cases(only=only, on_turn=on_turn)
    print(render_table(report))
    saved = save_report(report)
    print(f"Guardado en runtime/casos/{saved.name} (y runtime/casos/ultimo.json)")


def main():
    parser = argparse.ArgumentParser(description="Carrito · taller local")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    demo = sub.add_parser("demo")
    demo.add_argument("--mode", choices=["fixture", "live"], default="live")
    demo.add_argument("--scenario", choices=list(PROMPTS), default="catalog")
    demo.add_argument("--trace", type=Path, default=Path("runtime/demo.jsonl"))
    demo.add_argument(
        "--confirm", action="store_true", help="Host confirms the displayed scenario payload"
    )
    conversation = sub.add_parser("chat")
    conversation.add_argument("--mode", choices=["fixture", "live"], default="live")
    conversation.add_argument("--trace-dir", type=Path, default=Path("runtime/chat"))
    agente = sub.add_parser("agente", help="S2: habla con tu agente (mi_agente/)")
    agente.add_argument("--debug", action="store_true", help="muestra lo que ve el modelo")
    agente.add_argument("--pregunta", help="una sola pregunta y sale")
    agente.add_argument("--user", choices=["user1", "user2"], default="user1")
    cases = sub.add_parser("casos", help="S2: marcador de casos de tu agente")
    cases.add_argument("--debug", action="store_true")
    cases.add_argument("--caso", action="append", help="ejecuta solo este caso (C1...)")
    evaluate = sub.add_parser("eval")
    evaluate.add_argument("--split", choices=["dev"], default="dev")
    evaluate.add_argument("--mode", choices=["fixture", "live"], default="live")
    evaluate.add_argument("--trace-dir", type=Path, default=Path("runtime/evals"))
    viewer = sub.add_parser("trace")
    viewer.add_argument("path", type=Path)
    sub.add_parser("mcp-smoke")
    skill = sub.add_parser("skill-demo")
    skill.add_argument("--mode", choices=["fixture", "live"], default="live")
    judge = sub.add_parser("judge-demo")
    judge.add_argument("--mode", choices=["fixture", "live"], default="live")
    args = parser.parse_args()
    load_settings()
    if args.command == "doctor":
        doctor()
    elif args.command == "demo":
        tools = StoreTools(create_store())
        result = run_agent(
            PROMPTS[args.scenario],
            tools,
            model_for(args.mode, args.scenario),
            trace_path=args.trace,
        )
        show(result)
        if args.confirm and args.scenario == "return":
            # The flag authorizes only this displayed demo order AND reason.
            if tools.pending == ("104", "No encaja"):
                confirmation = confirm_host(tools)
                show({"host_confirmation": confirmation})
                with args.trace.open("a") as handle:
                    handle.write(
                        json.dumps({"type": "host_confirmation", "result": confirmation}) + "\n"
                    )
            else:
                show({"error": "pending_payload_differs_from_demo_confirmation"})
        show({"return_count": tools.return_count()})
        if result["status"] != "completed":
            raise SystemExit(1)
    elif args.command == "chat":
        chat(args.mode, args.trace_dir)
    elif args.command == "agente":
        mi_agente(args.debug, args.pregunta, args.user)
    elif args.command == "casos":
        casos(args.debug, args.caso)
    elif args.command == "eval":
        report = run_evals(args.split, args.mode, args.trace_dir)
        show(report)
        if report["passed"] != report["total"]:
            raise SystemExit(1)
    elif args.command == "trace":
        for index, line in enumerate(args.path.read_text().splitlines(), 1):
            event = json.loads(line)
            print(f"\nEvent {index}: {event['type']}")
            show(event)
    elif args.command == "mcp-smoke":
        from carrito.mcp_client import catalog_smoke

        show(asyncio.run(catalog_smoke()))
    elif args.command == "skill-demo":
        for prompt in ["Busco auriculares", "Quiero devolver un pedido"]:
            show({"prompt": prompt, "activation": activate_skill(prompt)})
        show(
            run_agent(
                PROMPTS["return"], StoreTools(create_store()), model_for(args.mode, "return")
            )
        )
    elif args.command == "judge-demo":
        show(judge_demo(args.mode))


if __name__ == "__main__":
    main()
