"""Cloudflare Workers AI provider (stdlib urllib only; opt-in, free tier).

Hosted free-tier inference. Requires (env), supplied by the user:
    CF_ACCOUNT_ID       Cloudflare account id
    CF_API_TOKEN        API token with Workers AI access
    WORKERS_AI_MODEL    model id (default @cf/meta/llama-3.1-8b-instruct)

This is opt-in: it only sends data to an external endpoint when the user
explicitly selects LLM_PROVIDER=workers_ai and provides credentials (R8.1).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from ..provider import LLMProvider, LLMUnavailableError

DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct"


class WorkersAIProvider(LLMProvider):
    name = "workers_ai"

    def __init__(self) -> None:
        self.account_id = os.environ.get("CF_ACCOUNT_ID", "")
        self.token = os.environ.get("CF_API_TOKEN", "")
        self.model = os.environ.get("WORKERS_AI_MODEL", DEFAULT_MODEL)

    def available(self) -> bool:
        return bool(self.account_id and self.token)

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        if not self.available():
            raise LLMUnavailableError(
                "workers_ai requires CF_ACCOUNT_ID and CF_API_TOKEN env vars"
            )
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/ai/run/{self.model}"
        )
        data = json.dumps({"messages": messages}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise LLMUnavailableError(f"workers_ai request failed: {exc}") from exc
        result = body.get("result") or {}
        return (result.get("response") or "").strip()
