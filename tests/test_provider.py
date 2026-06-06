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
