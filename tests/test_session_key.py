"""Session-key helpers: clear errors, .env reload and the offline CI client."""

from types import SimpleNamespace

import pytest

from carrito import model as model_module
from carrito.context import RecommendationContract
from carrito.model import OpenAIModel, explain_api_error, live_check, native_call
from carrito.offline import OfflineClient


class AuthenticationError(Exception):
    pass


class BadRequestError(Exception):
    body = {"message": "include is not supported"}


def test_api_errors_are_short_spanish_and_hide_the_key():
    message = explain_api_error(AuthenticationError("sk-proj-secret"))
    assert "clave" in message and "sk-proj" not in message
    assert "include is not supported" in explain_api_error(BadRequestError(), detail=True)
    assert "include" not in explain_api_error(BadRequestError())


def test_live_check_uses_the_agent_path():
    report = live_check()
    assert report["api"] == "OK" and report["model"]


def test_live_check_explains_a_revoked_key(monkeypatch):
    class Responses:
        def create(self, **kwargs):
            raise AuthenticationError("sk-proj-secret")

    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    with pytest.raises(RuntimeError, match="caducó") as error:
        live_check(client=SimpleNamespace(responses=Responses()))
    assert "sk-proj" not in str(error.value)


def test_missing_key_is_explained(monkeypatch):
    monkeypatch.delenv("CARRITO_OFFLINE_CHECK")
    monkeypatch.setattr(model_module, "load_settings", lambda: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAIModel()


def test_env_file_overrides_an_old_shell_key(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=new-session-key\n", encoding="utf-8")
    monkeypatch.setattr(model_module, "ENV_FILE", env)
    monkeypatch.setenv("OPENAI_API_KEY", "old-key")
    model_module.load_settings()
    import os

    assert os.environ["OPENAI_API_KEY"] == "new-session-key"


def test_offline_client_returns_valid_shapes():
    client = OfflineClient()
    parsed = client.responses.parse(text_format=RecommendationContract).output_parsed
    assert parsed.status == "no_match" and parsed.product_ids == []
    assert native_call([{"role": "user", "content": "hola"}])["status"] == "completed"


def test_agent_retries_without_reasoning_include():
    seen = []

    class Responses:
        def create(self, **kwargs):
            seen.append(kwargs)
            if "include" in kwargs:
                raise BadRequestError("include is not supported")
            return OfflineClient().responses.create(**kwargs)

    model = OpenAIModel(client=SimpleNamespace(responses=Responses()), model="test-model")
    assert model.respond([{"role": "user", "content": "hola"}], []).status == "completed"
    assert "include" in seen[0] and "include" not in seen[1] and "tools" not in seen[1]
    model.respond([{"role": "user", "content": "hola"}], [])
    assert len(seen) == 3 and "include" not in seen[2]
