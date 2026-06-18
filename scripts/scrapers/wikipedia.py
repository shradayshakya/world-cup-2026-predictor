"""Scraper for the Wikipedia 2026 FIFA World Cup page: group standings + all matches (PRD.md S7)."""

import re

from bs4 import BeautifulSoup

from .http import fetch

WIKI_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"

GROUP_LETTERS = list("ABCDEFGHIJKL")
GROUP_IDS = [f"Group_{letter}" for letter in GROUP_LETTERS]

ROUND_LABELS = {
    "Round_of_32": "Round of 32",
    "Round_of_16": "Round of 16",
    "Quarterfinals": "Quarter-finals",
    "Semifinals": "Semi-finals",
    "Match_for_third_place": "Third place play-off",
    "Final": "Final",
}

# Matches a leading "N-N" score, tolerant of trailing extra-time/penalty annotations.
SCORE_RE = re.compile(r"^(\d+)\s*[-–−]\s*(\d+)")
NUMBER_RE = re.compile(r"-?\d+")


def _int(text: str) -> int:
    match = NUMBER_RE.search(text.replace("−", "-").replace(",", ""))
    return int(match.group()) if match else 0


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+([,.)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    return text.strip()


def _parse_table_grid(table) -> list:
    """Flattens a table into a row/column grid, forward-filling rowspan/colspan cells."""
    grid = []
    pending = {}
    for tr in table.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        row = []
        col = 0
        ci = 0
        while ci < len(cells) or col in pending:
            if col in pending:
                remaining, text = pending[col]
                row.append(text)
                pending[col][0] = remaining - 1
                if pending[col][0] <= 0:
                    del pending[col]
                col += 1
                continue
            cell = cells[ci]
            text = cell.get_text(" ", strip=True)
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))
            for k in range(colspan):
                row.append(text)
                if rowspan > 1:
                    pending[col + k] = [rowspan - 1, text]
            col += colspan
            ci += 1
        grid.append(row)
    return grid


def _parse_group_standings(table) -> list:
    grid = _parse_table_grid(table)
    standings = []
    for row in grid[1:]:
        team = row[1]
        host = team.endswith("(H)")
        if host:
            team = team[: -len("(H)")].strip()
        standings.append(
            {
                "position": _int(row[0]),
                "team": team,
                "host": host,
                "played": _int(row[2]),
                "won": _int(row[3]),
                "drawn": _int(row[4]),
                "lost": _int(row[5]),
                "goals_for": _int(row[6]),
                "goals_against": _int(row[7]),
                "goal_difference": _int(row[8]),
                "points": _int(row[9]),
                "qualification_note": row[10] if len(row) > 10 else "",
            }
        )
    return standings


def _parse_match(box, round_label: str, group) -> dict:
    bday = box.find("span", class_="bday")
    date = bday.get_text(strip=True) if bday else None
    home = box.find(["th", "td"], class_="fhome").get_text(" ", strip=True)
    away = box.find(["th", "td"], class_="faway").get_text(" ", strip=True)
    score_text = box.find(["th", "td"], class_="fscore").get_text(" ", strip=True)
    score_match = SCORE_RE.match(score_text)

    venue = attendance = referee = None
    fright = box.find("div", class_="fright")
    if fright:
        text = fright.get_text(" ", strip=True)
        venue_part, _, referee_part = text.partition("Referee:")
        referee = _clean_text(referee_part) or None
        venue_part, _, attendance_part = venue_part.partition("Attendance:")
        if attendance_part:
            attendance = _int(attendance_part)
        venue = _clean_text(venue_part) or None

    return {
        "round": round_label,
        "group": group,
        "date": date,
        "home_team": home,
        "away_team": away,
        "played": bool(score_match),
        "home_score": int(score_match.group(1)) if score_match else None,
        "away_score": int(score_match.group(2)) if score_match else None,
        "venue": venue,
        "attendance": attendance,
        "referee": referee,
    }


def scrape_wikipedia() -> tuple:
    soup = BeautifulSoup(fetch(WIKI_URL), "html.parser")
    root = soup.find(id="mw-content-text")

    groups = {}
    for group_id, letter in zip(GROUP_IDS, GROUP_LETTERS):
        heading = root.find(id=group_id)
        table = heading.find_next("table", class_="wikitable")
        groups[letter] = _parse_group_standings(table)

    matches = []
    current_h2 = current_h3 = None
    for node in root.find_all(["h2", "h3", "div"]):
        if node.name == "h2":
            current_h2, current_h3 = node.get("id"), None
        elif node.name == "h3":
            current_h3 = node.get("id")
        elif "footballbox" in (node.get("class") or []):
            if current_h2 == "Group_stage" and current_h3 in GROUP_IDS:
                matches.append(_parse_match(node, "Group stage", current_h3.split("_")[1]))
            elif current_h2 == "Knockout_stage" and current_h3 in ROUND_LABELS:
                matches.append(_parse_match(node, ROUND_LABELS[current_h3], None))

    return groups, matches
