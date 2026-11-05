"""Meta Model API client.

Talks to the OpenAI-compatible endpoint at https://api.meta.ai/v1
using only the Python standard library (urllib). The API key is read
from the MODEL_API_KEY environment variable.

When no key is set the client runs in DEMO mode: it returns a canned,
clearly-labelled completion so the whole application can be run and
tested end-to-end without spending anything. Demo mode never pretends
to be a live model call.
"""

from __future__ import annotations

import json
import os
import urllib.request

BASE_URL = os.environ.get("MODEL_API_BASE", "https://api.meta.ai/v1")
# Override with MODEL_ID=... ; resolve_model() checks it against /v1/models.
DEFAULT_MODEL = os.environ.get("MODEL_ID", "muse-spark-1.3")

# Reported launch pricing for Muse Spark 1.3 (USD per 1M tokens).
# Used only for the informational cost tally in burn.py.
PRICE_IN_PER_M = 1.25
PRICE_OUT_PER_M = 4.25

DEMO_REPLY = (
    "DEMO MODE — canned advisor notes (no live model was called). "
    "On these numbers the renewal decision turns on three things: the "
    "gap between the lender's renewal offer and the best comparable "
    "market rate, the prepayment penalty for leaving early, and how "
    "much of the remaining amortization the household wants to keep. "
    "If the penalty is smaller than the interest saved over the new "
    "term, switching or blending usually wins; if the household may "
    "move within two years, a shorter term or a variable rate deserves "
    "a serious look. Confirm the exact penalty figure with the current "
    "lender in writing before signing anything."
)


class MetaClient:
    """Minimal chat-completions client for the Meta Model API."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key if api_key is not None else os.environ.get("MODEL_API_KEY", "")
        self.model = model

    @property
    def demo_mode(self) -> bool:
        return not self.api_key

    def list_models(self) -> list[str]:
        """Return model IDs available to this key (live mode only)."""
        if self.demo_mode:
            return []
        req = urllib.request.Request(
            f"{BASE_URL}/models",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return [m.get("id", "") for m in body.get("data", [])]

    def resolve_model(self) -> str:
        """Verify self.model exists; otherwise fall back to the newest
        muse-spark model the key can see. Returns the model actually used."""
        if self.demo_mode:
            return self.model
        try:
            ids = self.list_models()
        except Exception:
            return self.model
        if self.model in ids or not ids:
            return self.model
        sparks = [i for i in ids if i.startswith("muse-spark")]
        pick = sparks[0] if sparks else ids[0]
        print(f"[meta_client] model '{self.model}' not available; using '{pick}'")
        self.model = pick
        return pick

    def complete(self, system: str, user: str, max_tokens: int = 900) -> dict:
        """Return {"text": str, "usage": {...}, "mode": "live"|"demo"}."""
        if self.demo_mode:
            # Rough token estimates so the tally code path is exercised.
            est_in = max(1, (len(system) + len(user)) // 4)
            return {
                "text": DEMO_REPLY,
                "usage": {"prompt_tokens": est_in, "completion_tokens": 160},
                "mode": "demo",
            }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        req = urllib.request.Request(
            f"{BASE_URL}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        text = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return {
            "text": text,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            "mode": "live",
        }


def estimate_cost_usd(usage: dict) -> float:
    return (
        usage.get("prompt_tokens", 0) / 1_000_000 * PRICE_IN_PER_M
        + usage.get("completion_tokens", 0) / 1_000_000 * PRICE_OUT_PER_M
    )
