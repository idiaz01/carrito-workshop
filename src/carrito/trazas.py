"""S3 · Trazas en LangSmith. Off unless .env has LANGSMITH_TRACING=true and a key.

Each student uses their own free LangSmith account. Nothing is sent when tracing is off.
"""

import os
from contextlib import nullcontext

from carrito.model import load_settings


def enabled():
    load_settings()
    return os.getenv("LANGSMITH_TRACING", "").strip().lower() == "true" and bool(
        os.getenv("LANGSMITH_API_KEY")
    )


def wrap_client(client):
    """Trace every OpenAI call (prompt, tools, tokens) when tracing is on."""
    if not enabled():
        return client
    from langsmith.wrappers import wrap_openai

    return wrap_openai(client)


def traceable(**options):
    """langsmith.traceable when tracing is on; otherwise the function runs unchanged."""

    def decorate(function):
        def run(*args, **kwargs):
            if not enabled():
                return function(*args, **kwargs)
            from langsmith import traceable as ls_traceable

            return ls_traceable(**options)(function)(*args, **kwargs)

        run.__name__ = function.__name__
        run.__doc__ = function.__doc__
        return run

    return decorate


def tracing_context(**metadata):
    """Group the runs of one conversation (a LangSmith thread) and tag them."""
    if not enabled():
        return nullcontext()
    from langsmith import tracing_context as ls_context

    return ls_context(metadata=metadata)


def as_documents(results):
    """Retriever output in the shape LangSmith shows as documents."""
    return {
        "documents": [
            {
                "page_content": r["text"],
                "type": "Document",
                "metadata": {k: v for k, v in r.items() if k != "text"},
            }
            for r in results
        ]
    }


def check():
    """For carrito doctor: is tracing on, and does the key work?"""
    load_settings()
    if os.getenv("LANGSMITH_TRACING", "").strip().lower() != "true":
        return {"langsmith": "apagado", "message": "Pon LANGSMITH_TRACING=true en .env (S3)."}
    if not os.getenv("LANGSMITH_API_KEY"):
        return {"langsmith": "ERROR", "message": "Falta LANGSMITH_API_KEY en .env."}
    try:
        from langsmith import Client

        next(iter(Client().list_projects(limit=1)), None)
    except Exception as exc:  # noqa: BLE001 - short message for students, never the key
        return {
            "langsmith": "ERROR",
            "message": f"La clave de LangSmith falla ({type(exc).__name__}).",
        }
    return {"langsmith": "OK", "project": os.getenv("LANGSMITH_PROJECT", "default")}
