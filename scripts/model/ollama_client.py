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

# Matches a leading/trailing markdown code fence even when the model emits a literal
# two-character "\n" instead of a real newline after the fence (observed with longer
# prose generations from gemma4:e4b-mlx) -- (?:\\n|\n|\s)* covers both forms, and no
# MULTILINE flag means ^/$ anchor to the whole string's start/end, not internal lines.
_CODE_FENCE_RE = re.compile(r"^```(?:json)?(?:\\n|\n|\s)*|(?:\\n|\n|\s)*```$")


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
        pass

    # Longer prose generations have also been observed using a literal two-character "\n"
    # as a structural separator between JSON tokens (not just at the fence boundary) --
    # invalid there since JSON requires real whitespace, not an escaped representation.
    # A real newline isn't a safe substitute either (unescaped control characters are
    # invalid inside JSON string values too), so fall back to a plain space, which is
    # valid in both the structural and the string-content case.
    try:
        return json.loads(cleaned.replace("\\n", " "))
    except json.JSONDecodeError:
        pass

    # Occasionally the model over-escapes the whole response as if it were itself the
    # contents of a JSON string (literal \" instead of ", on top of the \n above) --
    # unescape both before retrying.
    try:
        return json.loads(cleaned.replace('\\"', '"').replace("\\n", " "))
    except json.JSONDecodeError:
        return None
