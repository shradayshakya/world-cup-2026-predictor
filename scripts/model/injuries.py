"""LLM injury/availability extraction from news headlines (PRD.md S6.3).

The LLM is asked only to identify players and their status -- never their
team. Team and "key player" importance are resolved deterministically
against the scraped roster (squads.json) afterward, since those are facts
we already have with certainty; the LLM doesn't need to guess at them, and
narrowing its job shrinks what it can hallucinate (PRD.md S6.4a's
guardrail spirit applied to this layer too, even though S6.4a itself talks
about the editorial layer specifically).

"Until" text is captured for display but not used for date-ranged penalty
logic -- see CLAUDE.md for why (the daily re-scrape makes it self-correcting
without date math).
"""

import unicodedata

from .ollama_client import generate_json
from .teams import TEAM_ALIASES

# Locked in via scripts/bakeoff.py's 20-headline comparison (2026-06-18): gemma4:e4b-mlx
# found all 12 expected entries (0 false negatives, 0 false positives, 1 status mismatch)
# vs qwen2.5:14b missing one entirely in addition to the same kind of status mismatch.
INJURY_EXTRACTION_MODEL = "gemma4:e4b-mlx"

CHUNK_SIZE = 20

KEY_PLAYER_COUNT = 11  # top-N by caps within a 26-player squad -- a "starting XI by seniority" proxy
PENALTY_OUT = -15
PENALTY_SUSPENDED = -15
PENALTY_DOUBT = -7.5
TEAM_PENALTY_CAP = -60
STATUS_PENALTY = {"out": PENALTY_OUT, "suspended": PENALTY_SUSPENDED, "doubt": PENALTY_DOUBT}

EXTRACTION_PROMPT_TEMPLATE = """You will be given football news headlines, each with an index, for the 2026 FIFA World Cup.

For each headline+description, identify any named football players reported as currently UNAVAILABLE for an upcoming match -- injured, ill, suspended, or otherwise barred (e.g. visa/disciplinary issues). For each such player, give their status and any explicitly stated return timeframe.

Rules:
- Only include a player if the text says they ARE currently out, doubtful, or suspended right now.
- Do NOT include a player described as recovered, fit, available, or simply playing well.
- Do NOT include a player only at risk of a FUTURE suspension (e.g. "one booking away") -- they are not unavailable yet.
- Do NOT include team staff (coaches, managers) -- players only.
- If a headline mentions no qualifying player, skip it.

Respond with ONLY a JSON object of this exact shape:
{{"injuries": [{{"headline_index": <int>, "player": "<full name as written>", "status": "out"|"doubt"|"suspended", "until": "<text mentioned, or null>"}}]}}
If none found across all headlines, respond {{"injuries": []}}.

Headlines:
{headlines_block}
"""


def _format_headlines_block(headlines: list) -> str:
    blocks = []
    for i, h in enumerate(headlines):
        blocks.append(f"[{i}] Title: {h['title']}\nDescription: {h['description']}")
    return "\n\n".join(blocks)


def build_prompt(headlines: list) -> str:
    return EXTRACTION_PROMPT_TEMPLATE.format(headlines_block=_format_headlines_block(headlines))


def _chunk(items: list, size: int) -> list:
    return [items[i : i + size] for i in range(0, len(items), size)]


def extract_injuries(headlines: list, model: str) -> list:
    """Returns a flat list of {headline, player, status, until} across all headlines."""
    results = []
    for chunk in _chunk(headlines, CHUNK_SIZE):
        prompt = build_prompt(chunk)
        parsed = generate_json(model, prompt)
        if not parsed or "injuries" not in parsed:
            continue
        for entry in parsed["injuries"]:
            idx = entry.get("headline_index")
            if idx is None or not (0 <= idx < len(chunk)):
                continue
            results.append(
                {
                    "headline": chunk[idx],
                    "player": entry.get("player", "").strip(),
                    "status": entry.get("status"),
                    "until": entry.get("until"),
                }
            )
    return results


def _normalize_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFD", name)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.lower().strip()


def _tokens(name: str) -> list:
    """'Junior'/'Jr'/'Jnr' all normalize to 'jr' so nicknames like 'Vini Jr' line up
    with a roster's full 'Vinicius Junior'."""
    words = _normalize_name(name).replace(".", "").split()
    return ["jr" if w in ("jr", "jnr", "junior") else w for w in words]


def _fuzzy_name_match(extracted_tokens: list, roster_tokens: list) -> bool:
    if len(extracted_tokens) > len(roster_tokens):
        return False
    return all(et == rt or rt.startswith(et) for et, rt in zip(extracted_tokens, roster_tokens))


def _key_player_names(squad: list) -> set:
    ranked = sorted(squad, key=lambda p: -p["caps"])
    return {_normalize_name(p["name"]) for p in ranked[:KEY_PLAYER_COUNT]}


STATUS_SEVERITY = {"out": 2, "suspended": 2, "doubt": 1}


def resolve_and_score(extracted: list, squads: dict) -> dict:
    """Matches each LLM-extracted player against the roster (exact name first, then a
    prefix-based fuzzy fallback for nicknames -- accepted only if it resolves to exactly
    one candidate across all squads, since a wrong match would misattribute a real
    player's status to the wrong team).

    The same real injury is often reported by multiple outlets (and so appears as
    multiple separate extracted entries) -- grouped by player below and reduced to the
    single most severe status, so a duplicated report doesn't stack the Elo penalty."""
    roster = [(team, player) for team, players in squads.items() for player in players]
    exact_lookup = {_normalize_name(player["name"]): (team, player) for team, player in roster}
    key_names_by_team = {team: _key_player_names(players) for team, players in squads.items()}

    matches = []
    for entry in extracted:
        if entry["status"] not in STATUS_PENALTY:
            continue
        norm = _normalize_name(entry["player"])
        match = exact_lookup.get(norm)
        if match is None:
            extracted_tokens = _tokens(entry["player"])
            candidates = [tp for tp in roster if _fuzzy_name_match(extracted_tokens, _tokens(tp[1]["name"]))]
            match = candidates[0] if len(candidates) == 1 else None
        if match is not None:
            matches.append((*match, entry))

    most_severe_by_player = {}
    for team, player, entry in matches:
        key = (team, _normalize_name(player["name"]))
        existing = most_severe_by_player.get(key)
        if existing is None or STATUS_SEVERITY[entry["status"]] > STATUS_SEVERITY[existing[2]["status"]]:
            most_severe_by_player[key] = (team, player, entry)

    result = {}
    for team, player, entry in most_severe_by_player.values():
        team_result = result.setdefault(team, {"elo_penalty": 0.0, "absences": []})
        is_key = _normalize_name(player["name"]) in key_names_by_team[team]
        team_result["absences"].append(
            {
                "player": player["name"],
                "status": entry["status"],
                "until": entry["until"],
                "key_player": is_key,
                "source_title": entry["headline"]["title"],
                "source_link": entry["headline"]["link"],
            }
        )
        if is_key:
            penalty = STATUS_PENALTY[entry["status"]]
            team_result["elo_penalty"] = max(team_result["elo_penalty"] + penalty, TEAM_PENALTY_CAP)

    return result


def apply_to_elo(elo: dict, injuries: dict) -> dict:
    """Returns a copy of the elo.json-shaped dict with injury penalties applied to ratings.
    elo.json itself stays the raw eloratings.net scrape -- this adjustment is only ever
    used as the model's internal input, fed to build_matches()/simulate_tournament()."""
    adjusted_teams = [dict(t) for t in elo["teams"]]
    by_name = {t["name"]: t for t in adjusted_teams}
    for wikipedia_team, data in injuries.items():
        elo_name = TEAM_ALIASES.get(wikipedia_team, wikipedia_team)
        if elo_name in by_name:
            by_name[elo_name]["rating"] += data["elo_penalty"]
    return {**elo, "teams": adjusted_teams}
