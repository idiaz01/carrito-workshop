"""Tests never call the API, even when a session key is in .env."""

import pytest


@pytest.fixture(autouse=True)
def offline_api(monkeypatch):
    monkeypatch.setenv("CARRITO_OFFLINE_CHECK", "1")
