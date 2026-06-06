"""LLM provider abstraction: a tiny ABC + env-var swap + mock fallback (ADR-0003).

The abstraction is deliberately minimal (one ``complete`` method) and built in
house with no third-party SDK, preserving ``dependencies = []``. The hosted
providers use only ``urllib`` from the standard library. Selection is by the
``LLM_PROVIDER`` env var; the default is the offline deterministic mock so the
tool never makes a surprise network call.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

DEFAULT_PROVIDER = "mock"


class LLMUnavailableError(RuntimeError):
    """Raised when a selected provider cannot serve a request."""


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None) -> str:
        """Return the model completion for ``prompt`` (deterministic for mock)."""

    def available(self) -> bool:
        """Cheap readiness check; real providers may probe config/endpoint."""
        return True


def get_provider(name: str | None = None) -> LLMProvider:
    """Resolve a provider by explicit name, else ``$LLM_PROVIDER``, else mock."""
    chosen = (name or os.environ.get("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()

    if chosen == "mock":
        from .providers.mock import MockProvider

        return MockProvider()
    if chosen == "ollama":
        from .providers.ollama import OllamaProvider

        return OllamaProvider()
    if chosen in ("workers_ai", "workers-ai", "cloudflare"):
        from .providers.workers_ai import WorkersAIProvider

        return WorkersAIProvider()

    raise LLMUnavailableError(
        f"unknown LLM provider {chosen!r} "
        f"(set LLM_PROVIDER to one of: mock, ollama, workers_ai)"
    )
