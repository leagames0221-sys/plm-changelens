"""R7.1-R7.3: provider ABC, env-var swap, deterministic offline mock."""

from __future__ import annotations

import pytest

from plm_changelens.llm.provider import (
    DEFAULT_PROVIDER,
    LLMUnavailableError,
    get_provider,
)
from plm_changelens.llm.providers.mock import MockProvider


def test_default_is_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    p = get_provider()
    assert p.name == "mock"
    assert DEFAULT_PROVIDER == "mock"


def test_env_var_swap(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    assert get_provider().name == "ollama"
    monkeypatch.setenv("LLM_PROVIDER", "workers_ai")
    assert get_provider().name == "workers_ai"


def test_explicit_name_overrides_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    assert get_provider("mock").name == "mock"


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with pytest.raises(LLMUnavailableError, match="unknown LLM provider"):
        get_provider("nope")


def test_mock_is_deterministic_and_offline():
    p = MockProvider()
    a = p.complete("hello world\nsecond line")
    b = p.complete("hello world\nsecond line")
    assert a == b
    assert a.startswith("[mock-llm]")


# ── hosted providers: exercise request build + response parse with no network ──

class _FakeResp:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_ollama_parses_response(monkeypatch):
    import json

    from plm_changelens.llm.providers import ollama as om

    captured = {}

    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode())
        return _FakeResp(json.dumps({"response": "  hello from ollama  "}).encode())

    monkeypatch.setattr(om.urllib.request, "urlopen", fake_urlopen)
    out = om.OllamaProvider().complete("a prompt", system="sys")
    assert out == "hello from ollama"
    assert captured["url"].endswith("/api/generate")
    assert captured["body"]["prompt"] == "a prompt"
    assert captured["body"]["system"] == "sys"
    assert captured["body"]["stream"] is False


def test_workers_ai_requires_credentials(monkeypatch):
    from plm_changelens.llm.provider import LLMUnavailableError
    from plm_changelens.llm.providers.workers_ai import WorkersAIProvider

    monkeypatch.delenv("CF_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("CF_API_TOKEN", raising=False)
    p = WorkersAIProvider()
    assert p.available() is False
    with pytest.raises(LLMUnavailableError, match="CF_ACCOUNT_ID"):
        p.complete("x")


def test_workers_ai_parses_result(monkeypatch):
    import json

    from plm_changelens.llm.providers import workers_ai as wm

    monkeypatch.setenv("CF_ACCOUNT_ID", "acc")
    monkeypatch.setenv("CF_API_TOKEN", "tok")

    def fake_urlopen(req, timeout=0):
        assert req.headers["Authorization"] == "Bearer tok"
        return _FakeResp(json.dumps({"result": {"response": "hi"}}).encode())

    monkeypatch.setattr(wm.urllib.request, "urlopen", fake_urlopen)
    assert wm.WorkersAIProvider().complete("p") == "hi"
