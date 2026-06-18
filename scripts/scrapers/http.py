"""Shared HTTP fetch helper (CLAUDE.md scraping discipline: identify with a UA, respect robots.txt)."""

import requests

USER_AGENT = "WC26Predictor/0.1 (+https://github.com/shradayshakya/world-cup-2026-predictor)"


def fetch(url: str, timeout: int = 30) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text
