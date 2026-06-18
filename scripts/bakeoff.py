#!/usr/bin/env python3
"""One-time model bake-off: gemma4:e4b-mlx vs qwen2.5:14b on injury extraction (PRD.md S6.3).

Run once, not part of the daily pipeline. Mix of real headlines pulled from
today's RSS feeds and hand-crafted edge cases (multi-player, recovery
false-positive traps, coach-not-player, future-risk-not-current-suspension,
nickname variants, irrelevant control cases). Each has a hand-labeled
expected extraction to score against.

Usage: .venv/bin/python3 scripts/bakeoff.py
"""

from model.injuries import build_prompt, extract_injuries
from model.ollama_client import generate_json

MODELS = ["gemma4:e4b-mlx", "qwen2.5:14b"]

# (headline, expected) -- expected is the ground-truth list of {player, status} dicts
# (until isn't scored: free text, no canonical form to compare against).
HEADLINES = [
    # --- real, pulled from today's feeds ---
    (
        {
            "title": "Pulisic training solo in race to be fit vs. Australia",
            "description": "United States national team attacker Christian Pulisic continued to train apart from the main group at Wednesday's training session, as he looks to recover from a calf injury he first sustained last week, and aggravated in last Friday's 4-1 over Paraguay.",
        },
        [{"player": "Christian Pulisic", "status": "doubt"}],
    ),
    (
        {
            "title": "Canada's Davies fit to face Qatar in World Cup",
            "description": "Canada captain Alphonso Davies will be available to play on Thursday against Qatar after he missed his team's World Cup opener while recovering from a hamstring injury.",
        },
        [],
    ),
    (
        {
            "title": "Ivory Coast's Wahi denied entry to Canada",
            "description": "The Ivory Coast football federation have announced their forward Elye Wahi has been denied entry to Canada for their next World Cup game.",
        },
        [{"player": "Elye Wahi", "status": "out"}],
    ),
    (
        {
            "title": "Australia superpower v USA pentagon: how each team can win their World Cup clash",
            "description": "The Socceroos and United States both made a fast start to their campaign. Back Nestory Irankunda: the 20-year-old was expected to be an impact player at this World Cup, coming on as a substitute to affect matches against tiring opposition. A player of the match performance when starting against Turkey showed how Irankunda has become one of the Socceroos' most important players.",
        },
        [],
    ),
    (
        {
            "title": "Tactical analysis: England look exciting but how can they tighten up?",
            "description": "England impressed in attack in their opener but defensive lapses will need addressing against tougher opposition.",
        },
        [],
    ),
    (
        {
            "title": "Konate to join Real Madrid on four-year deal",
            "description": "Liverpool defender Ibrahima Konate has signed a four-year deal with Real Madrid, the Spanish club have announced.",
        },
        [],
    ),
    # --- synthetic edge cases ---
    (
        {
            "title": "France without Tchouameni and Konate for crucial qualifier",
            "description": "France will be missing midfielder Aurelien Tchouameni (hamstring) and defender Jules Kounde (suspended after a second yellow card) for Friday's must-win match.",
        },
        [
            {"player": "Aurelien Tchouameni", "status": "out"},
            {"player": "Jules Kounde", "status": "suspended"},
        ],
    ),
    (
        {
            "title": "Walker faces late fitness test ahead of Brazil clash",
            "description": "England defender Kyle Walker will undergo a fitness test on Thursday morning to determine whether he can face Brazil, after picking up a knock in training.",
        },
        [{"player": "Kyle Walker", "status": "doubt"}],
    ),
    (
        {
            "title": "Modric ruled out for rest of the tournament with knee injury",
            "description": "Croatia captain Luka Modric will play no further part in the World Cup after sustaining a serious knee injury in training, the federation confirmed on Tuesday.",
        },
        [{"player": "Luka Modric", "status": "out"}],
    ),
    (
        {
            "title": "Senegal boss Cisse banned for one match after touchline outburst",
            "description": "Senegal head coach Aliou Cisse has been suspended for his side's next match by FIFA's disciplinary committee following his sending-off during Tuesday's game.",
        },
        [],
    ),
    (
        {
            "title": "Salah back in training after illness scare",
            "description": "Egypt forward Mohamed Salah returned to full training on Wednesday having recovered from a stomach virus that kept him out of Monday's session.",
        },
        [],
    ),
    (
        {
            "title": "Vini Jr a doubt for Brazil's next match",
            "description": "Brazil winger Vinicius Jr is a doubt for Saturday's game against Scotland after limping off with what is feared to be a hamstring strain.",
        },
        [{"player": "Vinicius Jr", "status": "doubt"}],
    ),
    (
        {
            "title": "Warner Bros sign new streaming deal",
            "description": "Entertainment giant Warner Bros has announced a new multi-year streaming partnership.",
        },
        [],
    ),
    (
        {
            "title": "Two-goal hero De Bruyne expected to start again",
            "description": "Kevin De Bruyne, who scored twice in Belgium's opening win, is expected to keep his place in the starting line-up for the next match.",
        },
        [],
    ),
    (
        {
            "title": "Argentina sweat on Otamendi suspension risk",
            "description": "Defender Nicolas Otamendi is one booking away from a suspension that would rule him out of Argentina's final group game if he is shown a yellow card on Thursday.",
        },
        [],
    ),
    (
        {
            "title": "Mexico's Lozano suspended for one match following red card",
            "description": "Hirving Lozano will serve a one-match suspension after being sent off in Mexico's win over South Korea, ruling him out of the team's next group game.",
        },
        [{"player": "Hirving Lozano", "status": "suspended"}],
    ),
    (
        {
            "title": "Spain monitor Pedri after midweek complaint of tightness",
            "description": "Spain midfielder Pedri trained alone on Thursday after complaining of tightness in his hamstring, with the medical staff continuing to assess him ahead of the weekend.",
        },
        [{"player": "Pedri", "status": "doubt"}],
    ),
    (
        {
            "title": "Portugal's Ronaldo: 'World Cup far from over'",
            "description": "Cristiano Ronaldo says Portugal's World Cup campaign is far from over despite a difficult start to the tournament.",
        },
        [],
    ),
    (
        {
            "title": "Norway's Haaland a late addition to squad after recovering from illness",
            "description": "Erling Haaland trained with the squad on Wednesday and is available for selection after recovering from a minor illness earlier in the week.",
        },
        [],
    ),
    (
        {
            "title": "Three Netherlands players doubtful for crunch clash",
            "description": "Netherlands could be without up to three first-choice players for their decisive group game, with Memphis Depay (hamstring), Virgil van Dijk (back spasm), and Frenkie de Jong (illness) all listed as doubtful in Wednesday's update.",
        },
        [
            {"player": "Memphis Depay", "status": "doubt"},
            {"player": "Virgil van Dijk", "status": "doubt"},
            {"player": "Frenkie de Jong", "status": "doubt"},
        ],
    ),
]


def _name_matches(extracted: str, expected: str) -> bool:
    e1, e2 = extracted.lower(), expected.lower()
    return e1 == e2 or e2 in e1 or e1 in e2 or e2.split()[-1] in e1


def score_model(model: str) -> dict:
    headlines = [h for h, _ in HEADLINES]
    prompt = build_prompt(headlines)
    parsed = generate_json(model, prompt)

    json_valid = parsed is not None and "injuries" in parsed
    extractions_by_index = {}
    if json_valid:
        for entry in parsed["injuries"]:
            idx = entry.get("headline_index")
            if isinstance(idx, int) and 0 <= idx < len(headlines):
                extractions_by_index.setdefault(idx, []).append(entry)

    true_positives = false_positives = false_negatives = wrong_status = 0
    for i, (_, expected) in enumerate(HEADLINES):
        extracted = extractions_by_index.get(i, [])
        matched_expected = set()
        for entry in extracted:
            match = next(
                (j for j, exp in enumerate(expected) if j not in matched_expected and _name_matches(entry.get("player", ""), exp["player"])),
                None,
            )
            if match is None:
                false_positives += 1
            else:
                matched_expected.add(match)
                if entry.get("status") == expected[match]["status"]:
                    true_positives += 1
                else:
                    wrong_status += 1
        false_negatives += len(expected) - len(matched_expected)

    return {
        "model": model,
        "json_valid": json_valid,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "wrong_status": wrong_status,
        "score": true_positives - false_positives - false_negatives - wrong_status,
    }


def main() -> None:
    results = [score_model(model) for model in MODELS]  # one model fully processed before the next -- avoid reload thrashing
    print(f"{'Model':<18} {'JSON OK':<8} {'TP':<4} {'FP':<4} {'FN':<4} {'Wrong status':<13} {'Score'}")
    for r in results:
        print(f"{r['model']:<18} {str(r['json_valid']):<8} {r['true_positives']:<4} {r['false_positives']:<4} {r['false_negatives']:<4} {r['wrong_status']:<13} {r['score']}")
    winner = max(results, key=lambda r: r["score"])
    print(f"\nWinner: {winner['model']}")


if __name__ == "__main__":
    main()
