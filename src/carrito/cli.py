"""Prepared host controls: the model cannot execute /confirm."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from carrito.agent import run_agent
from carrito.evaluation import run_evals
from carrito.judge import judge_demo
from carrito.model import FixtureModel, OpenAIModel
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


def main():
    parser = argparse.ArgumentParser(description="Carrito · taller local")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    demo = sub.add_parser("demo")
    demo.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    demo.add_argument("--scenario", choices=list(PROMPTS), default="catalog")
    demo.add_argument("--trace", type=Path, default=Path("runtime/demo.jsonl"))
    demo.add_argument(
        "--confirm", action="store_true", help="Host confirms the displayed scenario payload"
    )
    conversation = sub.add_parser("chat")
    conversation.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    conversation.add_argument("--trace-dir", type=Path, default=Path("runtime/chat"))
    evaluate = sub.add_parser("eval")
    evaluate.add_argument("--split", choices=["dev"], default="dev")
    evaluate.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    evaluate.add_argument("--trace-dir", type=Path, default=Path("runtime/evals"))
    viewer = sub.add_parser("trace")
    viewer.add_argument("path", type=Path)
    sub.add_parser("mcp-smoke")
    sub.add_parser("skill-demo")
    judge = sub.add_parser("judge-demo")
    judge.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    args = parser.parse_args()
    load_dotenv()
    if args.command == "doctor":
        tools = StoreTools(create_store())
        show(
            {
                "project": "Carrito",
                "offline_ready": len(tools.search_products("")) == 20,
                "reference_date": REFERENCE_DATE.isoformat(),
                "api_key_present": bool(os.getenv("OPENAI_API_KEY")),
                "model_configured": bool(os.getenv("OPENAI_MODEL")),
                "live_call_made": False,
            }
        )
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
                PROMPTS["return"], StoreTools(create_store()), FixtureModel.for_scenario("return")
            )
        )
    elif args.command == "judge-demo":
        show(judge_demo(args.mode))


if __name__ == "__main__":
    main()
