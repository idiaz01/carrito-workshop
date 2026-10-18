"""S3 · Lab 4 · Tu agente, con LangChain.

Usa las mismas piezas de mi_agente/: system.md, tools.md, contexto.py, rag.toml y
herramientas.py. Las tools y los permisos son los mismos. Cambia quién hace el loop:
aquí lo hace LangChain (create_agent) y no nuestro run_agent.

Pruébalo:  uv run carrito agente --motor langchain
Después, compara las dos trazas en LangSmith.
"""

import json
import os
import threading

from carrito.model import load_settings
from carrito.student import (
    StudentAgent,
    load_student_module,
    load_system_prompt,
    load_tool_descriptions,
)
from carrito.tools import ARGUMENTS, EXTRA_ARGUMENTS


def build_tools(helper, descriptions):
    """Una StructuredTool de LangChain por cada tool de tu agente."""
    from langchain_core.tools import StructuredTool

    module = load_student_module()  # tu contexto.py (format_tool_result)
    extra = helper._configure_tools(descriptions)
    schemas = {**ARGUMENTS, **{name: EXTRA_ARGUMENTS[name] for name in extra}}
    lock = threading.Lock()  # LangChain puede ejecutar dos tools a la vez, en otros hilos

    def make_tool(name, schema):
        def run(**arguments):
            with lock:
                result = helper.tools.dispatch(name, arguments)  # misma tool, mismos permisos
            try:
                return module.format_tool_result(name, result)  # lo que ve el modelo
            except Exception:  # noqa: BLE001 - sin tu función, el resultado completo
                return json.dumps(result, ensure_ascii=False)

        return StructuredTool.from_function(
            run, name=name, description=descriptions[name], args_schema=schema
        )

    return [make_tool(name, schema) for name, schema in schemas.items()]


def build_agent(user_id="user1", model=None):
    """Devuelve (agente de LangChain, helper con las tools de la tienda)."""
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import InMemorySaver

    load_settings()
    helper = StudentAgent(model=object(), user_id=user_id)  # solo usamos sus tools
    helper._configure_rag()  # tu rag.toml
    descriptions = load_tool_descriptions()  # tu tools.md
    tools = build_tools(helper, descriptions)
    system, _ = load_system_prompt()  # tu system.md
    if model is None:
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model=os.environ["OPENAI_MODEL"], use_responses_api=True)
    # InMemorySaver guarda la conversación: LangChain reenvía TODO el historial.
    agent = create_agent(model, tools, system_prompt=system, checkpointer=InMemorySaver())
    return agent, helper


def ask(agent, helper, text):
    config = {
        "configurable": {"thread_id": helper.thread_id},
        "metadata": {"session_id": helper.thread_id, "motor": "langchain"},
        "run_name": "Carrito · LangChain",
    }
    before = (
        len(agent.get_state(config).values.get("messages", [])) if _has_state(agent, config) else 0
    )
    result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
    new = result["messages"][before:]
    calls, model_calls, tokens_in, tokens_out = [], 0, 0, 0
    for message in new:
        if message.type == "ai":
            model_calls += 1
            usage = message.usage_metadata or {}
            tokens_in += usage.get("input_tokens", 0)
            tokens_out += usage.get("output_tokens", 0)
            calls += [(c["name"], c["args"]) for c in message.tool_calls]
    return {
        "answer": result["messages"][-1].text,
        "calls": calls,
        "model_calls": model_calls,
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
    }


def _has_state(agent, config):
    try:
        return bool(agent.get_state(config).values)
    except Exception:  # noqa: BLE001
        return False
