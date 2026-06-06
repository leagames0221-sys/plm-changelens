"""Local Ollama provider (stdlib urllib only; no third-party SDK).

Talks to a local Ollama server (default http://localhost:11434). Free,
card-free, fully local (K-2/K-3). Configurable via env:
    OLLAMA_HOST   (default http://localhost:11434)
    OLLAMA_MODEL  (default llama3.1)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ..provider import LLMProvider, LLMUnavailableError


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self) -> None:
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3.1")

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LLMUnavailableError(
                f"ollama request failed ({self.host}, model={self.model}): {exc}"
            ) from exc
        return (body.get("response") or "").strip()
