"""S3 · RAG configuration, the student's tool, LangChain wiring and session helpers."""

import json

import pytest

import carrito.student as student
from carrito import rag
from carrito.model import FixtureModel

SOLVED_TOOL = """
from datetime import date, timedelta

def plazo_devolucion(pedido, producto, hoy):
    limite = date.fromisoformat(pedido["delivered_at"]) + timedelta(days=30)
    return {"order_id": pedido["order_id"], "fecha_limite": limite.isoformat(),
            "se_puede_devolver": True, "motivo": "POL-DEV", "dias_restantes": (limite - hoy).days}
"""


def test_rag_config_validation(tmp_path):
    assert rag.load_config(tmp_path / "nada.toml") is None
    path = tmp_path / "rag.toml"
    path.write_text(
        '[documentos]\nfuentes = ["politicas", "ayuda"]\ntrocear = "seccion"\n'
        '[busqueda]\nmetodo = "lexico"\ntop_k = 3\n'
    )
    assert rag.load_config(path) == {
        "fuentes": ["politicas", "ayuda"],
        "trocear": "seccion",
        "metodo": "lexico",
        "top_k": 3,
    }
    path.write_text('[documentos]\ntrocear = "capitulo"\n')
    with pytest.raises(rag.ConfigError, match="trocear"):
        rag.load_config(path)


def test_chunking_keeps_source_and_sections():
    docs = rag.chunk_documents(["politicas", "ayuda"], "documento")
    sections = rag.chunk_documents(["politicas", "ayuda"], "seccion")
    sentences = rag.chunk_documents(["politicas", "ayuda"], "frase")
    assert len(docs) == 18 and len(docs) < len(sections) < len(sentences)
    canarias = [c for c in sections if "Canarias, Ceuta y Melilla" in c["sections"]]
    assert canarias[0]["source_id"] == "AYU-ENV" and "14,95" in canarias[0]["text"]
    assert "no enviamos baterías" in canarias[0]["text"]


def test_rag_evaluation_shows_the_tradeoff():
    base = rag.evaluate(dict(rag.DEFAULTS))
    assert base["aciertos"] <= 2  # S2: only the six policies
    docs = rag.evaluate(
        {"fuentes": ["politicas", "ayuda"], "trocear": "documento", "metodo": "lexico", "top_k": 3}
    )
    small = rag.evaluate(
        {"fuentes": ["politicas", "ayuda"], "trocear": "seccion", "metodo": "lexico", "top_k": 3}
    )
    assert docs["aciertos"] >= 9 and small["aciertos"] >= 9
    assert small["tokens_medios"] < docs["tokens_medios"] / 2
    assert "RECUPERACIÓN" in rag.render_evaluation(small)


def test_hybrid_and_embeddings_run_offline():
    config = {"fuentes": ["ayuda"], "trocear": "seccion", "metodo": "hibrido", "top_k": 2}
    results = rag.search("garantía de la batería", config)
    assert len(results) == 2 and all("text" in r for r in results)


def test_agent_uses_rag_and_the_student_tool(tmp_path, monkeypatch):
    (tmp_path / "tools.md").write_text(
        "## search_policies\nBusca en políticas y ayuda.\n\n"
        "## plazo_devolucion\nCalcula hasta qué día se puede devolver un pedido.\n"
    )
    (tmp_path / "rag.toml").write_text(
        '[documentos]\nfuentes = ["politicas", "ayuda"]\ntrocear = "seccion"\n'
        '[busqueda]\nmetodo = "lexico"\ntop_k = 2\n'
    )
    (tmp_path / "herramientas.py").write_text(SOLVED_TOOL)
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    calls = [
        [
            {
                "type": "function_call",
                "name": "search_policies",
                "arguments": json.dumps({"query": "envío Canarias"}),
                "call_id": "c1",
            }
        ],
        [
            {
                "type": "function_call",
                "name": "plazo_devolucion",
                "arguments": json.dumps({"order_id": "104"}),
                "call_id": "c2",
            }
        ],
        [],
    ]
    agent = student.StudentAgent(model=FixtureModel(calls), warn=print)
    result = agent.ask("¿Envíos a Canarias? ¿Y el plazo del 104?")
    seen = {c["name"]: c["model_sees"] for c in result["report"]["calls"]}
    assert "AYU-ENV" in seen["search_policies"]
    assert "2026-10-12" in seen["plazo_devolucion"]
    assert result["report"]["uses"]["plazo_devolucion"] == "tuya"
    assert result["report"]["rag"]["trocear"] == "seccion"
    agent.close()


def test_student_tool_hidden_until_described(tmp_path, monkeypatch):
    (tmp_path / "herramientas.py").write_text(SOLVED_TOOL)
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    agent = student.StudentAgent(model=FixtureModel([[]], final_text="Hola"), warn=print)
    result = agent.ask("Hola")
    assert result["report"]["uses"]["plazo_devolucion"] == "sin describir en tools.md"
    start = next(e for e in result["events"] if e["type"] == "start")
    assert "plazo_devolucion" not in [t["name"] for t in start["tools"]]
    agent.close()


def test_other_users_order_never_reaches_the_student_tool(tmp_path, monkeypatch):
    seen = []
    agent = student.StudentAgent(model=FixtureModel([[]]), warn=print)
    agent.tools.deadline_function = lambda order, product, today: seen.append(order) or {}
    assert agent.tools.plazo_devolucion("108") == {"error": "order_not_found"}  # user2's order
    assert seen == []
    agent.close()


def test_langchain_tools_share_store_and_format(tmp_path, monkeypatch):
    pytest.importorskip("langchain_core")
    from carrito.langchain_agente import build_tools

    (tmp_path / "contexto.py").write_text("def format_tool_result(name, result):\n    return 'X'\n")
    monkeypatch.setattr(student, "FOLDER", tmp_path)
    helper = student.StudentAgent(model=object())
    tools = build_tools(helper, student.load_tool_descriptions())
    names = [t.name for t in tools]
    assert names == ["search_products", "get_order", "search_policies", "request_return"]
    assert tools[1].invoke({"order_id": "104"}) == "X"
    helper.close()


def test_pista_and_empezar(tmp_path, monkeypatch, capsys):
    from carrito import cli

    root = tmp_path
    (root / "mi_agente").mkdir()
    (root / "mi_agente" / "system.md").write_text("mío")
    solution = root / "sessions" / "02_context" / "solucion"
    solution.mkdir(parents=True)
    (solution / "system.md").write_text("solución")
    (solution / "README.md").write_text("no se copia")
    monkeypatch.setattr(cli, "ROOT", root)
    monkeypatch.setattr(cli, "SOLUTIONS", {"s3": ("s2", solution)})
    cli.empezar("s3")
    assert (root / "mi_agente" / "system.md").read_text() == "solución"
    assert (root / "mi_agente_s2" / "system.md").read_text() == "mío"
    assert not (root / "mi_agente" / "README.md").exists()
    hints = root / "sessions" / "03_retrieval_tools"
    hints.mkdir(parents=True)
    (hints / "pistas.json").write_text(json.dumps({"2": ["uno", "dos"]}))
    cli.pista("s3-2")
    cli.pista("s3-2")
    out = capsys.readouterr().out
    assert "Pista 1/2: uno" in out and "Pista 2/2: dos" in out


def test_langchain_agent_runs_the_loop_with_a_fake_model(monkeypatch):
    pytest.importorskip("langchain")
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage

    from carrito.langchain_agente import ask, build_agent

    class Fake(GenericFakeChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    usage = {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12}
    messages = iter(
        [
            AIMessage(
                content="",
                tool_calls=[{"name": "get_order", "args": {"order_id": "104"}, "id": "t1"}],
                usage_metadata=usage,
            ),
            AIMessage(content="El 104 está entregado.", usage_metadata=usage),
        ]
    )
    agent, helper = build_agent(model=Fake(messages=messages))
    result = ask(agent, helper, "¿Y el 104?")
    assert result["answer"] == "El 104 está entregado."
    assert result["calls"] == [("get_order", {"order_id": "104"})]
    assert result["model_calls"] == 2 and result["input_tokens"] == 20
    helper.close()


def test_langchain_tools_work_from_another_thread():
    """LangChain runs tools in a worker thread; the SQLite store must accept that."""
    import threading

    from carrito.student import StudentAgent

    helper = StudentAgent(model=object())
    out = {}
    thread = threading.Thread(
        target=lambda: out.update(r=helper.tools.dispatch("get_order", {"order_id": "104"}))
    )
    thread.start()
    thread.join()
    assert "error" not in out["r"]
