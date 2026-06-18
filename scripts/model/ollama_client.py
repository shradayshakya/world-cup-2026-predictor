"""Thin wrapper around the local Ollama HTTP API, shared by the daily injury
extraction and the one-time model bake-off (PRD.md S6.3).

Avoid interleaving calls to different models in a tight loop: Ollama only
keeps one model loaded at a time by default, so switching models forces a
multi-second reload on every call. Process all calls for one model before
moving to the next.
"""

import json
import re

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
REQUEST_TIMEOUT = 600  # a full ~20-headline chunk can take several minutes on a local model

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def generate_json(model: str, prompt: str):
    """Calls Ollama in JSON mode and returns the parsed response, or None on failure."""
    response = requests.post(
        OLLAMA_URL,
        json={"model": model, "prompt": prompt, "format": "json", "stream": False},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    text = response.json()["response"]

    # Some models (e.g. gemma4:e4b-mlx) wrap JSON-mode output in markdown fences anyway.
    cleaned = _CODE_FENCE_RE.sub("", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
