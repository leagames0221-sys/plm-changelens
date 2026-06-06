"""Deterministic, offline mock provider (the default).

Produces stable, content-derived text so the LLM-layer code paths are fully
testable without a network, account, or card. It is intentionally obvious that
the output is a placeholder, never a real model judgement.
"""

from __future__ import annotations

from ..provider import LLMProvider


class MockProvider(LLMProvider):
    name = "mock"

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        # Deterministic: echo a compact, labelled digest of the prompt so tests
        # can assert linkage without depending on a real model.
        first_line = prompt.strip().splitlines()[0] if prompt.strip() else ""
        return f"[mock-llm] {first_line}".strip()
