"""Scraper for football news RSS feeds (PRD.md S7), source for the injury layer."""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from .http import fetch

FEEDS = {
    "BBC Sport": "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "The Guardian": "https://www.theguardian.com/football/rss",
    "ESPN": "https://www.espn.com/espn/rss/soccer/news",
}

LOOKBACK_HOURS = 24


def _strip_html(text: str) -> str:
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)


def _parse_feed(xml_text: str, source: str, cutoff: datetime) -> list:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        pub_date_text = item.findtext("pubDate")
        if not pub_date_text:
            continue
        published_at = parsedate_to_datetime(pub_date_text)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        if published_at < cutoff:
            continue
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "description": _strip_html(item.findtext("description") or ""),
                "link": (item.findtext("link") or "").strip(),
                "source": source,
                "published_at": published_at.astimezone(timezone.utc).isoformat(),
            }
        )
    return items


def scrape_headlines() -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    headlines = []
    for source, url in FEEDS.items():
        headlines.extend(_parse_feed(fetch(url), source, cutoff))
    return headlines
