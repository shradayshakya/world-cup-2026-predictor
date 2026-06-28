"""Shared HTTP fetch helper (CLAUDE.md scraping discipline: identify with a UA, respect robots.txt)."""

import requests

USER_AGENT = "WC26Predictor/0.1 (+https://github.com/shradayshakya/world-cup-2026-predictor)"


HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch(url: str, timeout: int = 30) -> str:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    # Some sources (e.g. eloratings.net) don't declare a charset, so requests
    # falls back to ISO-8859-1 per HTTP spec default and mangles UTF-8 bytes.
    response.encoding = "utf-8"
    return response.text
