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
import uuid
from pathlib import Path

from carrito import diseno, rag, trazas
from carrito.agent import run_agent
from carrito.model import OpenAIModel
from carrito.store import REFERENCE_DATE, create_store
from carrito.tools import (
    ARGUMENTS,
    DESCRIPTIONS,
    EXTRA_ARGUMENTS,
    StoreTools,
    tool_definitions,
)

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
    # S3+: a student tool exists for the model only when tools.md describes it.
    for name in EXTRA_ARGUMENTS:
        text = "\n".join(descriptions.get(name, [])).strip()
        if text:
            result[name] = text
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
    unchanged = [
        n
        for n, d in descriptions.items()
        if n in DEFAULT_TOOLS and d.strip() in {DEFAULT_TOOLS[n], n}
    ]
    if unchanged:
        raise NotImplementedError("Descripciones sin cambiar: " + ", ".join(unchanged))
    return {n: len(d) for n, d in descriptions.items()}


def load_student_module(name="contexto"):
    """Import mi_agente/<name>.py again on every call: edits apply without a restart."""
    path = FOLDER / f"{name}.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"mi_agente_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_design():
    """S4. None while mi_agente/agente.toml does not exist (S3 behaviour)."""
    return diseno.load(FOLDER / "agente.toml")


SAMPLE_ANSWER = {"texto": "Hola", "fuentes": [], "pide_confirmacion": False}


def output_status():
    """S4 · Lab 3. Raises NotImplementedError while revisar() is not written."""
    module = load_student_module("salida")
    if module is None or not hasattr(module, "Respuesta") or not hasattr(module, "revisar"):
        raise NotImplementedError("Falta mi_agente/salida.py con Respuesta y revisar")
    return module.revisar(module.Respuesta(**SAMPLE_ANSWER), set())


def load_rag_config():
    """S3 · Paso 2. None while mi_agente/rag.toml does not exist (S2 behaviour)."""
    return rag.load_config(FOLDER / "rag.toml")


# A sample order for checking mi_agente/herramientas.py without the API.
SAMPLE_ORDER = {
    "order_id": "104",
    "user_id": "user1",
    "product_id": "P001",
    "status": "delivered",
    "delivered_at": "2026-09-12",
}
SAMPLE_PRODUCT = {
    "product_id": "P001",
    "name": "Auriculares Nube",
    "category": "audio",
    "price_cents": 6990,
    "description": "auriculares",
    "returnable": 1,
}


def deadline_status():
    """S3 · Paso 3. Raises NotImplementedError while plazo_devolucion is not written."""
    module = load_student_module("herramientas")
    if module is None or not hasattr(module, "plazo_devolucion"):
        raise NotImplementedError("Falta mi_agente/herramientas.py con plazo_devolucion")
    return module.plazo_devolucion(dict(SAMPLE_ORDER), dict(SAMPLE_PRODUCT), REFERENCE_DATE)


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


class StudentTools(StoreTools):
    """The store tools, with each call traced as a LangSmith "tool" run when tracing is on.

    S4: when a subagent is active, search_policies goes to the subagent (once; the subagent
    itself uses the real search)."""

    subagent = None
    _inside_subagent = False

    def dispatch(self, name, arguments):
        if name == "search_policies" and self.subagent and not self._inside_subagent:
            self._inside_subagent = True
            try:
                return self.subagent(arguments.get("query", ""))
            finally:
                self._inside_subagent = False
        traced = trazas.traceable(run_type="tool", name=name)(super().dispatch)
        return traced(name, arguments)


class StudentAgent:
    """One conversation with the agent built from mi_agente/."""

    def __init__(self, model=None, user_id="user1", warn=print):
        self.tools = StudentTools(create_store(), user_id=user_id)
        self.model = model or OpenAIModel()
        self.turns = []
        self.state = {}
        self.warn = warn
        self.uses = {}
        self.thread_id = str(uuid.uuid4())
        self.rag_config = None

    def _student(self, module, name, fallback, *args, check=None):
        function = getattr(module, name, None) if module is not None else None
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

    # ---- S3 · RAG (rag.toml) and the student's tool (herramientas.py) -------------------
    def _configure_rag(self):
        try:
            config = load_rag_config()
        except rag.ConfigError as exc:
            self.warn(f"⚠️  {exc}. Uso la búsqueda de S2.")
            config = None
        self.rag_config = config
        if config is None:
            self.tools.policy_retriever = None
            return

        @trazas.traceable(run_type="retriever", name="search_policies · RAG")
        def retrieve(query):
            return trazas.as_documents(rag.search(query, config))

        def retriever(query):
            if trazas.enabled():
                documents = retrieve(query)["documents"]
                return [{**d["metadata"], "text": d["page_content"]} for d in documents]
            return rag.search(query, config)

        self.tools.policy_retriever = retriever

    def _configure_tools(self, descriptions):
        """plazo_devolucion is offered only when tools.md describes it and the function works."""
        module = load_student_module("herramientas")
        self.tools.deadline_function = None
        if module is None:
            return ()
        if "plazo_devolucion" not in descriptions:
            self.uses["plazo_devolucion"] = "sin describir en tools.md"
            return ()
        sample = self._student(
            module,
            "plazo_devolucion",
            lambda: None,
            dict(SAMPLE_ORDER),
            dict(SAMPLE_PRODUCT),
            REFERENCE_DATE,
            check=lambda v: isinstance(v, dict),
        )
        if sample is None:
            return ()

        def deadline(order, product, today):
            try:
                value = module.plazo_devolucion(order, product, today)
            except Exception as exc:  # noqa: BLE001
                self.warn(f"⚠️  Error en tu plazo_devolucion: {type(exc).__name__}: {exc}")
                return {"error": "tool_error"}
            return value if isinstance(value, dict) else {"error": "tool_error"}

        self.tools.deadline_function = deadline
        return ("plazo_devolucion",)

    def ask(self, text, max_steps=5):
        with trazas.tracing_context(session_id=self.thread_id):
            traced = trazas.traceable(run_type="chain", name="Carrito · turno")(self._ask)
            return traced(text, max_steps)

    def _configure_design(self, descriptions):
        """S4: limits, routes and subagent from agente.toml. Returns (design, extra tools)."""
        try:
            design = load_design()
        except diseno.ConfigError as exc:
            self.warn(f"⚠️  {exc}. Uso el diseño de S3.")
            design = None
        self.tools.subagent = None
        if design is None:
            return None, ()
        # From S4 on, the application also offers mis_pedidos (the user's orders).
        descriptions.setdefault("mis_pedidos", DESCRIPTIONS["mis_pedidos"])
        if design["subagente"]["activo"]:
            self.tools.subagent = self._make_subagent(descriptions)
        return design, ("mis_pedidos",)

    def _make_subagent(self, descriptions):
        prompt = _read("subagente.md") or "Eres un ayudante."
        formatter = self._formatter(load_student_module())

        @trazas.traceable(run_type="chain", name="subagente · documentos")
        def subagent(query):
            run = run_agent(
                query,
                self.tools,
                self.model,
                max_steps=3,
                history=[{"role": "system", "content": prompt}],
                enable_skills=False,
                tool_descriptions=descriptions,
                format_result=formatter,
                allowed_tools=["search_policies"],
            )
            usage = [e["usage"] for e in run["events"] if e["type"] == "model_response"]
            self._subagent_usage += usage
            sources = sorted(diseno.seen_ids(run["events"]))
            return {"resumen": run["answer"], "fuentes": sources}

        return subagent

    def _formatter(self, module):
        def formatter(name, result):
            return self._student(
                module,
                "format_tool_result",
                lambda: _dumps(result),
                name,
                result,
                check=lambda v: isinstance(v, str),
            )

        return formatter

    def _fixed_route(self, route):
        return {
            "answer": route["respuesta"].strip(),
            "status": "completed",
            "events": [],
            "messages": [],
        }

    def _search_route(self, text, context, formatter):
        """Workflow: always search, then ONE model call without tools."""
        results = self.tools.search_policies(text)
        seen = formatter("search_policies", results)
        events = [
            {
                "type": "tool_result",
                "name": "search_policies",
                "arguments": text,
                "result": results,
                "model_sees": seen,
                "by": "workflow",
            }
        ]
        messages = [
            *context,
            {"role": "system", "content": f"Documentos encontrados:\n{seen}"},
            {"role": "user", "content": text},
        ]
        turn = self.model.respond(messages, [])
        events.append({"type": "model_response", "usage": turn.usage, "text": turn.text})
        return {"answer": turn.text, "status": turn.status, "events": events, "messages": messages}

    def _structured(self, run, schema_module, text_format):
        """S4 · Lab 3: parse the JSON answer, run the student's revisar(), fix once."""
        report = {"fuentes": [], "problemas": [], "corregida": False}
        try:
            answer = schema_module.Respuesta.model_validate_json(run["answer"])
        except Exception:  # noqa: BLE001 - the model did not follow the schema
            report["problemas"] = ["La respuesta no sigue el formato de Respuesta."]
            return run["answer"], report
        problems = self._student(
            schema_module,
            "revisar",
            lambda: [],
            answer,
            diseno.seen_ids(run["events"]),
            check=lambda v: isinstance(v, list),
        )
        if problems:
            report["problemas"] = list(problems)
            fix = [
                *run["messages"],
                {"role": "system", "content": "Corrige tu respuesta: " + " ".join(problems)},
            ]
            turn = self.model.respond(fix, [], text_format=text_format)
            run["events"].append({"type": "model_response", "usage": turn.usage, "text": turn.text})
            try:
                answer = schema_module.Respuesta.model_validate_json(turn.text)
                report["corregida"] = True
            except Exception:  # noqa: BLE001
                pass
        report["fuentes"] = list(answer.fuentes)
        report["pide_confirmacion"] = answer.pide_confirmacion
        return answer.texto, report

    def _ask(self, text, max_steps=5):
        module = load_student_module()
        self.uses = {}
        self._subagent_usage = []
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
        self._configure_rag()
        extra = self._configure_tools(descriptions)
        design, design_extra = self._configure_design(descriptions)
        extra = tuple(extra) + tuple(design_extra)
        formatter = self._formatter(module)
        context = [{"role": "system", "content": system}, *history]

        route = diseno.choose_route(text, design["rutas"]) if design else None
        limits = design["limites"] if design else {"max_pasos": max_steps}
        structured = None
        if route and route["tipo"] == "fija":
            run = self._fixed_route(route)
        elif route and route["tipo"] == "buscar":
            run = self._search_route(text, context, formatter)
        else:
            schema_module, text_format = None, None
            if design is not None:
                try:
                    output_status()
                    schema_module = load_student_module("salida")
                    text_format = diseno.strict_schema(schema_module.Respuesta)
                    self.uses["revisar"] = "tuya"
                except NotImplementedError:
                    self.uses["revisar"] = "por defecto"
                except Exception as exc:  # noqa: BLE001
                    self.uses["revisar"] = "error"
                    self.warn(f"⚠️  Error en tu salida.py: {type(exc).__name__}: {exc}")
            options = {}
            if design is not None:
                options = {
                    "max_tool_calls": limits["max_tools"],
                    "max_total_tokens": limits["max_tokens"],
                }
            run = run_agent(
                text,
                self.tools,
                self.model,
                max_steps=limits["max_pasos"],
                history=context,
                enable_skills=False,
                tool_descriptions=descriptions,
                format_result=formatter,
                extra_tools=extra,
                text_format=text_format,
                **options,
            )
            if text_format and run["status"] == "completed":
                answer, structured = self._structured(run, schema_module, text_format)
                run["answer"] = answer
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
        definitions = tool_definitions(descriptions, extra=extra)
        usage = [e["usage"] for e in run["events"] if e["type"] == "model_response"]
        sub = self._subagent_usage
        report = {
            "prompt_version": version,
            "uses": dict(self.uses),
            "state": state,
            "rag": self.rag_config,
            "status": run["status"],
            "ruta": (route or {}).get("tipo", "agente") if design else None,
            "limites": design["limites"] if design else None,
            "salida": structured,
            "subagente": (
                {
                    "llamadas": len(sub),
                    "tokens": sum(
                        u.get("input_tokens", 0) + u.get("output_tokens", 0) for u in sub
                    ),
                }
                if self.tools.subagent
                else None
            ),
            "blocks": {
                "system": estimate_tokens(system),
                "tools": estimate_tokens(_dumps(definitions)) if not route else 0,
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
            "model_calls": len(usage) + len(sub),
            "input_tokens": sum(u.get("input_tokens", 0) for u in usage + sub),
            "output_tokens": sum(u.get("output_tokens", 0) for u in usage + sub),
        }
        if route and route["tipo"] == "fija":
            # A fixed route never calls the model: nothing was sent, nothing is paid.
            report["blocks"] = dict.fromkeys(report["blocks"], 0)
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
    if report.get("ruta"):
        lim = report["limites"]
        lines.append(
            f"  Ruta: {report['ruta']} · límites: {lim['max_pasos']} pasos, "
            f"{lim['max_tools']} tools, {lim['max_tokens']} tokens · estado: {report['status']}"
        )
    if report.get("salida"):
        out = report["salida"]
        lines.append(
            f"  Salida: fuentes={out['fuentes']} · problemas={out['problemas'] or 'ninguno'}"
            + (" · corregida" if out["corregida"] else "")
        )
    if report.get("subagente"):
        lines.append(
            f"  Subagente: {report['subagente']['llamadas']} llamadas · "
            f"{report['subagente']['tokens']} tokens (incluidos en API)"
        )
    if report.get("rag"):
        c = report["rag"]
        lines.append(
            f"  RAG: fuentes={'+'.join(c['fuentes'])} · trocear={c['trocear']}"
            f" · metodo={c['metodo']} · top_k={c['top_k']}"
        )
    pieces = ", ".join(f"{k}: {v}" for k, v in report["uses"].items())
    lines.append(f"  Tus funciones: {pieces}")
    if report["state"]:
        lines.append(f"  Estado: {report['state']}")
    return "\n".join(lines)
