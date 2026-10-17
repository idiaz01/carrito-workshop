"""Tests never call the API and never send traces, even when a session key is in .env."""

import pytest


@pytest.fixture(autouse=True)
def offline_api(monkeypatch, tmp_path):
    from carrito import model

    monkeypatch.setenv("CARRITO_OFFLINE_CHECK", "1")
    # Do not read the real .env: with LANGSMITH_TRACING=true every test would be a trace.
    monkeypatch.setattr(model, "ENV_FILE", tmp_path / "no.env")
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
