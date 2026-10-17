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
from carrito.store import REFERENCE_DATE, ROOT, create_store
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
    from carrito.trazas import check

    report["trazas"] = check()
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


def mi_agente_langchain(debug, question, user):
    """S3 · Lab 4: the same mi_agente/, with LangChain's loop."""
    from carrito.langchain_agente import ask, build_agent

    agent, helper = build_agent(user)
    print("Tu agente con LangChain · mi_agente/. /salir sale.")
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
        if not prompt:
            continue
        result = ask(agent, helper, prompt)
        if debug:
            print(
                f"  LangChain: {result['model_calls']} llamadas al modelo · "
                f"{result['input_tokens']} tokens de entrada · {result['output_tokens']} de salida"
            )
            for name, arguments in result["calls"]:
                print(f"  → {name} {json.dumps(arguments, ensure_ascii=False)}")
        print(f"Carrito> {result['answer']}\n")
        if question is not None:
            break
    helper.close()


def mi_agente(debug, question, user):
    """S2: chat with the agent built from mi_agente/. Edits apply on the next message."""
    from carrito.student import FOLDER, ROOT, StudentAgent, render_report

    agent = StudentAgent(user_id=user)
    try:
        where = FOLDER.resolve().relative_to(ROOT)
    except ValueError:
        where = FOLDER
    turn = 0
    print(f"Tu agente · {where}/. /reset empieza otra conversación; /salir sale.")
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


def casos(debug, only, compare=False, reto=False, sesion=2, todos=False):
    """S2 scoreboard: more cases passed with fewer tokens."""
    from carrito.cases import (
        last_two_reports,
        render_comparison,
        render_table,
        run_cases,
        save_report,
    )
    from carrito.student import render_report

    if compare:
        pair = last_two_reports()
        if pair is None:
            print("Necesitas al menos dos ejecuciones de `carrito casos` para comparar.")
            return
        print(render_comparison(*pair))
        return

    def on_turn(case, turn, text, result):
        print(f"[{case['id']}·{turn}] Tú> {text}")
        if debug:
            print(render_report(result["report"], turn))
        print(f"        Carrito> {result['answer'][:300]}\n")

    report = run_cases(only=only, on_turn=on_turn, reto=reto, sesion=sesion, todos=todos)
    print(render_table(report))
    saved = save_report(report)
    print(f"Guardado en runtime/casos/{saved.name} (y runtime/casos/ultimo.json)")


def rag_command(evaluar, buscar):
    """S3 · Paso 2: measure and inspect the retrieval configured in mi_agente/rag.toml."""
    from carrito import rag
    from carrito.student import load_rag_config

    try:
        config = load_rag_config() or dict(rag.DEFAULTS)
    except rag.ConfigError as exc:
        print(f"⚠️  {exc}")
        raise SystemExit(1) from None
    if buscar:
        print(rag.render_search(buscar, rag.search(buscar, config)))
    if evaluar or not buscar:
        print(rag.render_evaluation(rag.evaluate(config)))


SOLUTIONS = {
    "s3": ("s2", ROOT / "sessions" / "02_context" / "solucion"),
}


def empezar(sesion):
    """Start a session from the published solution of the previous one. Keeps a backup."""
    import shutil

    previous, source = SOLUTIONS[sesion]
    if not source.exists():
        print("Todavía no tienes la solución de la sesión anterior. Ejecuta antes: git pull")
        raise SystemExit(1)
    target = ROOT / "mi_agente"
    backup = ROOT / f"mi_agente_{previous}"
    n = 2
    while backup.exists():
        backup = ROOT / f"mi_agente_{previous}_{n}"
        n += 1
    shutil.copytree(target, backup)
    copied = []
    for path in sorted(source.iterdir()):
        if path.is_file() and path.name != "README.md":
            shutil.copy2(path, target / path.name)
            copied.append(path.name)
    print(f"Tu versión anterior está guardada en {backup.name}/.")
    print(f"mi_agente/ parte ahora de la solución de {previous.upper()}: {', '.join(copied)}.")
    print("Comprueba: uv run carrito agente --debug")


def pista(codigo):
    """Next hint for a lab, for example `carrito pista s3-2`. Each call shows one more."""
    sesion, _, lab = codigo.partition("-")
    folders = {"s3": "03_retrieval_tools", "s4": "04_agents_state", "s5": "05_capstone"}
    path = ROOT / "sessions" / folders.get(sesion, "?") / "pistas.json"
    if not path.exists() or not lab:
        print("Usa: uv run carrito pista s3-2   (sesión 3, lab 2)")
        return
    hints = json.loads(path.read_text()).get(lab)
    if not hints:
        print(f"No hay pistas para el lab {lab} de {sesion}.")
        return
    state_file = ROOT / "runtime" / "pistas.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    seen = state.get(codigo, 0)
    shown = min(seen + 1, len(hints))
    for k, hint in enumerate(hints[:shown], 1):
        print(f"Pista {k}/{len(hints)}: {hint}")
    state[codigo] = shown
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state))


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
    agente.add_argument(
        "--motor",
        choices=["carrito", "langchain"],
        default="carrito",
        help="S3: quién hace el loop",
    )
    rag_parser = sub.add_parser("rag", help="S3: mide y prueba la búsqueda de mi_agente/rag.toml")
    rag_parser.add_argument(
        "--evaluar", action="store_true", help="aciertos y tokens (12 preguntas)"
    )
    rag_parser.add_argument("--buscar", help="qué piezas encuentra para una pregunta")
    start = sub.add_parser("empezar", help="empieza una sesión desde la solución de la anterior")
    start.add_argument("sesion", choices=sorted(SOLUTIONS))
    hint = sub.add_parser("pista", help="la siguiente pista de un lab: carrito pista s3-2")
    hint.add_argument("codigo")
    cases = sub.add_parser("casos", help="S2: marcador de casos de tu agente")
    cases.add_argument("--debug", action="store_true")
    cases.add_argument("--caso", action="append", help="ejecuta solo este caso (C1...)")
    cases.add_argument(
        "--comparar", action="store_true", help="compara las dos últimas ejecuciones"
    )
    cases.add_argument("--reto", action="store_true", help="S2: añade los casos del reto (C9-C12)")
    cases.add_argument(
        "--sesion", type=int, choices=[2, 3], default=2, help="marcador de la sesión"
    )
    cases.add_argument("--todos", action="store_true", help="todos los casos de todas las sesiones")
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
        if args.motor == "langchain":
            mi_agente_langchain(args.debug, args.pregunta, args.user)
        else:
            mi_agente(args.debug, args.pregunta, args.user)
    elif args.command == "rag":
        rag_command(args.evaluar, args.buscar)
    elif args.command == "empezar":
        empezar(args.sesion)
    elif args.command == "pista":
        pista(args.codigo)
    elif args.command == "casos":
        casos(args.debug, args.caso, args.comparar, args.reto, args.sesion, args.todos)
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
            run_agent(PROMPTS["return"], StoreTools(create_store()), model_for(args.mode, "return"))
        )
    elif args.command == "judge-demo":
        show(judge_demo(args.mode))


if __name__ == "__main__":
    main()
