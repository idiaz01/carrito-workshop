"""Runtime of the student's agent (S2): reads mi_agente/ and builds the context of each call.

The agent loop, the tools and the permissions are given. The student owns four pieces of
context: the system prompt, the tool descriptions, the tool-result format and the history.
Unfinished pieces fall back to a default, so the agent always runs.
"""

import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

from carrito.agent import run_agent
from carrito.model import OpenAIModel
from carrito.store import create_store
from carrito.tools import ARGUMENTS, StoreTools, tool_definitions

ROOT = Path(__file__).resolve().parents[2]
# CARRITO_MI_AGENTE points to another folder (for example, the teacher's reference version).
FOLDER = Path(os.getenv("CARRITO_MI_AGENTE", ROOT / "mi_agente"))
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
DEFAULT_SYSTEM = "Eres un asistente."
DEFAULT_TOOLS = {
    "search_products": "Busca productos.",
    "get_order": "Busca un pedido.",
    "search_policies": "Busca información.",
    "request_return": "Devuelve un pedido.",
}
SECTIONS = ("rol", "objetivo", "reglas", "tool", "falta", "formato")


def _read(name):
    path = FOLDER / name
    return COMMENT.sub("", path.read_text(encoding="utf-8")).strip() if path.exists() else ""


def load_system_prompt():
    """Return (text, version). The version is a short hash: it changes with every edit."""
    text = _read("system.md") or DEFAULT_SYSTEM
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()[:7]


def load_tool_descriptions():
    descriptions, current = {}, None
    for line in _read("tools.md").splitlines():
        header = re.match(r"^##\s+(\w+)\s*$", line)
        if header:
            current = header.group(1)
            descriptions[current] = []
        elif current:
            descriptions[current].append(line)
    result = {}
    for name in ARGUMENTS:
        text = "\n".join(descriptions.get(name, [])).strip()
        result[name] = text or name
    return result


def system_prompt_status():
    """S2 · Paso 1. Raises NotImplementedError while system.md is the starting text."""
    text, version = load_system_prompt()
    if text.strip() == DEFAULT_SYSTEM:
        raise NotImplementedError("mi_agente/system.md sigue siendo el texto inicial")
    headings = [h.lower() for h in re.findall(r"^#+\s*(.+)$", text, re.MULTILINE)]
    found = [s for s in SECTIONS if any(s in h for h in headings)]
    spec_ids = sorted(set(re.findall(r"\b(?:ALC|DAT|RESP|ACL|PER|ESC)-\d\b", text)))
    return {"version": version, "sections": found, "spec_ids": spec_ids, "chars": len(text)}


def tool_descriptions_status():
    """S2 · Paso 2. Raises NotImplementedError while tools.md keeps a starting description."""
    descriptions = load_tool_descriptions()
    unchanged = [n for n, d in descriptions.items() if d.strip() in {DEFAULT_TOOLS[n], n}]
    if unchanged:
        raise NotImplementedError("Descripciones sin cambiar: " + ", ".join(unchanged))
    return {n: len(d) for n, d in descriptions.items()}


def load_student_module():
    """Import mi_agente/contexto.py again on every call: edits apply without a restart."""
    spec = importlib.util.spec_from_file_location("mi_agente_contexto", FOLDER / "contexto.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _dumps(value):
    return json.dumps(value, ensure_ascii=False)


def default_history(turns):
    """Fallback for Paso 4: every previous turn, with the full tool results."""
    messages = []
    for turn in turns:
        messages.append({"role": "user", "content": turn["user"]})
        for tool in turn.get("tools", []):
            messages.append(
                {
                    "role": "assistant",
                    "content": f"[{tool['name']} {tool['arguments']}] → {_dumps(tool['result'])}",
                }
            )
        messages.append({"role": "assistant", "content": turn["assistant"]})
    return messages


def _valid_messages(value):
    return isinstance(value, list) and all(
        isinstance(m, dict)
        and m.get("role") in {"system", "user", "assistant"}
        and isinstance(m.get("content"), str)
        for m in value
    )


def estimate_tokens(text):
    """Rough estimate for the debug view: about 4 characters per token."""
    return max(0, round(len(text) / 4)) if text else 0


class StudentAgent:
    """One conversation with the agent built from mi_agente/."""

    def __init__(self, model=None, user_id="user1", warn=print):
        self.tools = StoreTools(create_store(), user_id=user_id)
        self.model = model or OpenAIModel()
        self.turns = []
        self.state = {}
        self.warn = warn
        self.uses = {}

    def _student(self, module, name, fallback, *args, check=None):
        function = getattr(module, name, None)
        if function is None:
            self.uses[name] = "falta"
            return fallback()
        try:
            value = function(*args)
        except NotImplementedError:
            self.uses[name] = "por defecto"
            return fallback()
        except Exception as exc:  # noqa: BLE001 - the student sees the error, the agent continues
            self.uses[name] = "error"
            self.warn(
                f"⚠️  Error en tu {name}: {type(exc).__name__}: {exc}. Uso el valor por defecto."
            )
            return fallback()
        if check and not check(value):
            self.uses[name] = "error"
            self.warn(f"⚠️  Tu {name} devolvió un valor no válido. Uso el valor por defecto.")
            return fallback()
        self.uses[name] = "tuya"
        return value

    def ask(self, text, max_steps=5):
        module = load_student_module()
        self.uses = {}
        state = self._student(
            module,
            "update_state",
            lambda: dict(self.state),
            dict(self.state),
            text,
            check=lambda v: isinstance(v, dict),
        )
        history = self._student(
            module,
            "build_history",
            lambda: default_history(self.turns),
            [dict(t) for t in self.turns],
            dict(state),
            check=_valid_messages,
        )
        system, version = load_system_prompt()
        descriptions = load_tool_descriptions()

        def formatter(name, result):
            return self._student(
                module,
                "format_tool_result",
                lambda: _dumps(result),
                name,
                result,
                check=lambda v: isinstance(v, str),
            )

        context = [{"role": "system", "content": system}, *history]
        run = run_agent(
            text,
            self.tools,
            self.model,
            max_steps=max_steps,
            history=context,
            enable_skills=False,
            tool_descriptions=descriptions,
            format_result=formatter,
        )
        tool_events = [e for e in run["events"] if e["type"] == "tool_result"]
        self.turns.append(
            {
                "user": text,
                "assistant": run["answer"],
                "tools": [
                    {"name": e["name"], "arguments": e["arguments"], "result": e["result"]}
                    for e in tool_events
                ],
            }
        )
        self.state = state
        definitions = tool_definitions(descriptions)
        usage = [e["usage"] for e in run["events"] if e["type"] == "model_response"]
        report = {
            "prompt_version": version,
            "uses": dict(self.uses),
            "state": state,
            "blocks": {
                "system": estimate_tokens(system),
                "tools": estimate_tokens(_dumps(definitions)),
                "historial": estimate_tokens(_dumps(history)),
                "pregunta": estimate_tokens(text),
                "resultados": estimate_tokens(
                    "".join(e.get("model_sees", "") for e in tool_events)
                ),
            },
            "calls": [
                {
                    "name": e["name"],
                    "arguments": e["arguments"],
                    "model_sees": e.get("model_sees", ""),
                }
                for e in tool_events
            ],
            "model_calls": len(usage),
            "input_tokens": sum(u.get("input_tokens", 0) for u in usage),
            "output_tokens": sum(u.get("output_tokens", 0) for u in usage),
        }
        return {
            "answer": run["answer"],
            "status": run["status"],
            "report": report,
            "events": run["events"],
        }

    def close(self):
        self.tools.db.close()


def render_report(report, turn):
    """Text view of what the model saw in one turn (used by --debug and the notebook)."""
    lines = [
        f"── Lo que vio el modelo · turno {turn} · prompt v{report['prompt_version']} " + "─" * 20
    ]
    blocks = report["blocks"]
    top = max(blocks.values()) or 1
    for name, tokens in blocks.items():
        bar = "█" * max(1 if tokens else 0, round(24 * tokens / top))
        lines.append(f"  {name:<11} ≈{tokens:>6} tokens  {bar}")
    lines.append(
        f"  API: {report['input_tokens']} tokens de entrada · {report['output_tokens']} de salida"
        f" · {report['model_calls']} llamadas al modelo"
    )
    for call in report["calls"]:
        preview = call["model_sees"].replace("\n", " ")
        try:
            arguments = _dumps(json.loads(call["arguments"]))
        except (TypeError, ValueError):
            arguments = str(call["arguments"])
        lines.append(f"  → {call['name']} {arguments}")
        lines.append(f"    ← el modelo ve {len(call['model_sees'])} caracteres: {preview[:110]}")
    pieces = ", ".join(f"{k}: {v}" for k, v in report["uses"].items())
    lines.append(f"  Tus funciones: {pieces}")
    if report["state"]:
        lines.append(f"  Estado: {report['state']}")
    return "\n".join(lines)
