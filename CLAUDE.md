# World Cup 2026 Predictor

Daily-updated tournament-prediction web app for the 2026 FIFA World Cup (USA/Canada/Mexico, 48 teams, already underway as of 2026-06-11).

**`PRD.md` is the source of truth.** Read it first — every architectural decision, model choice, and view spec lives there. This file is the short-form orientation; the PRD is the full design.

---

## Current state

- **Phase 0 (scaffolding): done.**
- Next.js 15 + Tailwind app scaffolded, static export verified (`make build`), "Hello WC26" page live.
- `.venv` + `requirements.txt` (requests, beautifulsoup4, numpy, pandas) set up.
- `Makefile` (`dev`, `build`, `venv`, `update`) and `scripts/update.py` heartbeat stub in place.
- launchd plist drafted at `launchd/com.shradayshakya.wc26predictor.update.plist` — **not yet installed/loaded** (deferred until there's a real pipeline to run daily).
- Cloudflare hosting connected via the Workers Git-integration flow (`wrangler.jsonc`, static assets from `out/`) — **not classic Pages**; production URL is `*.workers.dev`, not `*.pages.dev` (see Locked decisions below). Live at https://world-cup-2026-predictor.shradayshakya.workers.dev, auto-deploy on push to `main` confirmed.
- **Phase 1 (data pipeline): done.**
- `scripts/scrapers/elo.py` scrapes eloratings.net's `World.tsv` + `en.teams.tsv` → `public/data/elo.json` (244 teams, rank/code/name/rating).
- `scripts/scrapers/wikipedia.py` scrapes the single `en.wikipedia.org/wiki/2026_FIFA_World_Cup` page (one fetch, per scraping discipline) → `public/data/groups.json` (12 group standings) and `public/data/results.json` (all 104 matches, group + knockout, played and upcoming).
- `scripts/update.py` orchestrates all three scrapers plus the heartbeat write; `make update` runs it and commits/pushes all four `public/data/*.json` files.
- Knockout-stage matches not yet determined carry placeholder team names scraped verbatim from Wikipedia (e.g. `"Runner-up Group A"`, `"3rd Group A/B/C/D/F"`) — Phase 3's bracket logic will need to resolve these against actual standings.
- **Phase 2 (match model): done.**
- `scripts/model/poisson.py` — Poisson-Elo + Dixon-Coles match model. **No historical results dataset was available to fit this**, so the Elo-to-goals mapping (`ELO_RATIO_SCALE = 500` — see 2026-06-18 entries below for two rounds of recalibration; `AVERAGE_GOALS_PER_MATCH = 2.6`, `HOME_ADVANTAGE_ELO = 100`, `DIXON_COLES_RHO = -0.13`) is a documented heuristic, not a regression fit to match outcomes — revisit via the PRD §10 Brier-score calibration check once enough real matches have been played.
- `scripts/model/matches.py` joins `elo.json` + `groups.json` (for host-nation flags) + `results.json` (for fixtures) into `public/data/matches.json`: predicted scoreline, W/D/L probabilities, and a full 8×8 score-probability grid per match.
- Team-name mismatches between eloratings.net and Wikipedia are bridged via a small `TEAM_ALIASES` dict (currently just `"Czech Republic" → "Czechia"`) — add to it if future scrapes log new unresolved-team warnings that turn out to be naming drift rather than genuine TBD knockout slots.
- Fixed a real bug along the way: `scripts/scrapers/http.py` now forces UTF-8 decoding — `requests` was silently mojibake-ing eloratings.net's unlabeled-charset TSV responses (e.g. "Curaçao" → "CuraÃ§ao").
- Knockout-stage fixtures are skipped in `matches.json` until Wikipedia resolves their placeholder team names (currently all 32); only the 48 not-yet-played group-stage matches get predictions today.
- **Phase 3 (tournament model): done.**
- `scripts/model/bracket.py` hardcodes the 48-team bracket topology (which Round-of-32 slot is "Winner Group X" / "Runner-up Group X" / one of 5 candidate groups' 3rd-place team, and which earlier-round results feed R16→QF→SF→Final/3rd-place) — captured once from Wikipedia's placeholder text rather than re-parsed each scrape, since that text disappears once a slot resolves to a real team name.
- `scripts/model/simulate.py` runs the N=50,000 Monte Carlo: samples remaining group matches from Phase 2's grids, ranks each group (points → goal difference → goals for → head-to-head for a 2-way tie → random for 3+-way ties, standing in for "drawing of lots"), picks the best 8 third-placed teams, resolves the 8 candidate-list bracket slots via a small bipartite matching (a group's 3rd-place team is a candidate for several slots but can only fill one), then simulates R32→Final with extra-time (λ × 1/3) and a lightly Elo-weighted penalty-shootout coin-flip for draws (PRD §6.2). Runs in ~34s.
- Output `public/data/probabilities.json`: per-team probabilities for every stage (group position, `advanced_to_r32`, `reached_r16`/`qf`/`sf`/`final`, `won_tournament`, `won_third_place_match`). Sanity-checked: probabilities sum to 1.0 across teams for `won_tournament`, and each team's group-position probabilities sum to 1.0.
- The third-place bracket-slot matching is a documented simplification: it finds *some* valid assignment of qualifying 3rd-place teams to candidate slots, not necessarily FIFA's exact official table (which also avoids rematches/geography) — fine for prediction purposes, flagged here in case it ever needs tightening.
- **Added two more eloratings.net feeds** (beyond Phase 1's `World.tsv`): `latest.tsv` (global results log → `public/data/form.json`, last-10 results per WC26 team, feeds PRD §5.4's "recent form") and `fixtures.tsv` (their own published win-expectancy → `matches.json`'s `elo_win_expectancy` field, an "according to Elo" comparison alongside our own `prediction`). Both work with our own descriptive UA, no browser-spoofing headers needed.
- **`elo_win_expectancy` is NOT a 3-way split** — it's eloratings.net's classic Elo "expected score" (win=1, draw=0.5, loss=0), not directly comparable to our `prediction`'s separate home/draw/away probabilities. Comparable single-number proxy from our side: `home_win_probability + 0.5 * draw_probability`.
- Both new eloratings.net outputs reference WC26 teams by eloratings.net's own naming (e.g. "Czechia"), so `scripts/scrapers/elo.py` normalizes back to Wikipedia naming via `model/teams.to_wikipedia_name()` before returning — without this, `form.json` keys and `opponent` fields, and `matches.json`'s `elo_win_expectancy` lookups, silently broke for any team with a `TEAM_ALIASES` entry. If you add to `TEAM_ALIASES`, this normalization covers it automatically.
- **Phase 4 (UI): done.**
- All 5 PRD §5 views built: Home (`/`), Bracket (`/bracket`), Groups (`/groups`, all 12 as anchored sections), Team detail (`/teams/[slug]`, 48 static pages), Match detail (`/matches/[slug]`, 104 static pages). Every page is a Server Component with zero client-side JS — hover tooltips use native `title` attributes, not `'use client'`. Home page first-load JS is ~106 KB (PRD §10 budget: <200 KB).
- `scripts/model/simulate.py` extended with per-knockout-slot occupancy tracking (`Counter`s at the same 6 points in the existing loop where matchups were already computed) → new `public/data/bracket.json`, needed because the Bracket view's "most likely 2 teams per node" spec isn't derivable from `probabilities.json`'s per-team aggregates alone. `simulate_tournament()` now returns `{probabilities, bracket}`; `update.py` writes both files.
- Bracket nodes auto-transition from "predicted" to "confirmed": the page checks whether `results.json`'s corresponding match (same round, same array-index as `bracket.json` — both derived from the same topology order) has resolved to a real team name (i.e. one of the 48 in `groups.json`); if so it shows the real matchup, otherwise it falls back to `bracket.json`'s probabilistic occupant. No code changes needed as the tournament progresses.
- `src/lib/data.ts` loads all `public/data/*.json` via static ES imports (not `fs.readFileSync` — simpler, and Next.js/webpack handles JSON imports natively for static export).
- Deferred (per PRD's own phasing, not cut arbitrarily): probability-change arrows + "biggest movers" (§5.1/§5.1a, explicitly Phase 6 — no day-over-day snapshot mechanism exists yet, today is the app's first day of real data), LLM blurbs/badges (§6.4, Phase 5b), squad/injury data (Phase 5), and Team detail's "predicted path to the final" (would need a third `simulate.py` extension — per-team conditional-opponent tracking — beyond the per-slot occupancy already added; cut from v1, Team detail shows full stage probabilities instead).
- No charting library installed — PRD allows Recharts/visx, but neither fit the stacked tournament-winner bar (≤48 unlabeled segments) or the score-distribution heatmap (8×8 grid) well. Both are hand-rolled with Tailwind flex/grid instead.
- Caught and fixed a real bug during browser verification: `MatchCard` and `BracketNode` were nesting a `<Link>` (team name) inside another `<Link>` (the whole card/node) — invalid HTML, caused React hydration errors. Fixed by making team names inside those two components plain text; team pages are still reachable via Groups/Team-detail links elsewhere.
- **Match page UX fix (2026-06-18, user-reported):** the "Predicted result" headline showed the modal exact scoreline (e.g. "1–1") even when the W/D/L breakdown clearly favored one side (e.g. Germany 47% / Draw 28.6% / Ivory Coast 24.3%) — a real Poisson-model property (a win's probability splits across many scorelines while draws concentrate into fewer, so a draw can be the single most likely *exact* result without being the most likely *outcome*), but a confusing headline regardless. Fixed by restructuring, not just disclaiming: the bold headline now states who's favored (`leadingOutcomeLabel()` in `matches/[slug]/page.tsx`), with the modal scoreline demoted to a small secondary line, plus a new `TopScorelines` component listing the top 6 scorelines with their outcomes so the "why" is visible without asking.
- **Recalibration round 1 (2026-06-18): `GOAL_SUPREMACY_PER_400_ELO` 1.0 → 2.5.** User reported predictions felt off (41/48 matches predicted exactly 1-1). At 1.0 the model disagreed with eloratings.net's own win expectancy by ~12.6pp on average; grid-searching against that (free, already-scraped ground truth) found 2.5 cuts it to ~1.5pp. Fixed *decisiveness* but barely moved *variety* (still only {2-0, 1-1, 0-2}, 3 distinct scorelines) — see round 2.
- **Recalibration round 2 (2026-06-18): replaced the additive Elo-to-goals formula with a multiplicative one.** User correctly pushed back that round 1 "doesn't change much" — real investigation found a structural bug, not a tuning issue: the additive formula (`lambda_home = avg + supremacy/2`, `lambda_away = avg - supremacy/2`) holds `lambda_home + lambda_away` constant at `AVERAGE_GOALS_PER_MATCH` regardless of Elo gap, which caps the favorite's expected goals at `2.6 - MIN_EXPECTED_GOALS = 2.45` -- since a Poisson mode is `floor(lambda)`, **no Elo gap, however large, could ever produce a 3-0 or 4-0 prediction**. Replaced with `ratio = 10**(elo_diff / ELO_RATIO_SCALE)`, `lambda_home = avg*sqrt(ratio)`, `lambda_away = avg/sqrt(ratio)` (a multiplicative split, `MAX_EXPECTED_GOALS = 6.0` safety cap added). Grid-searched `ELO_RATIO_SCALE`: 500 fits eloratings.net even better than round 1 (0.74pp avg error) *and* unlocks blowout scorelines (Spain vs Saudi Arabia -> 4-0 at 96%, England vs Ghana -> 4-0 at 94%) while leaving close matches untouched (Switzerland vs Canada stays 1-1 at 35/30/35). 6 distinct scorelines now: {4-0, 3-0, 2-0, 1-1, 0-2, 0-3}. Considered and rejected switching to LLM-based scoring instead (logged in PRD.md §12) -- the actual problem was a fixable structural bug in the existing model, not a case for a fundamentally different approach.
- Re-derive `matches.json`/`probabilities.json`/`bracket.json` from existing `elo.json`/`groups.json`/`results.json` after touching anything in `poisson.py` -- no need to re-scrape (`build_matches()` + `simulate_tournament()` are pure functions of the JSON already on disk).
- **Next concrete steps** (per PRD §11 Phase 5 — LLM injury layer):
  1. Scrape squad pages (Wikipedia) + injury/suspension news (BBC/Guardian/ESPN RSS).
  2. Local Ollama (`gemma4:e4b-mlx`) extraction → injury Elo penalty, applied in `scripts/model/poisson.py`'s `expected_goals()`.
  3. One-time bake-off vs `qwen2.5:14b` on 20 sample headlines before locking in the model.

When you finish a phase, update this section to reflect the new "next".

---

## Architecture in one paragraph

Owner's Mac runs a launchd job daily at 06:00 local. The job scrapes data (eloratings.net, Wikipedia, news RSS), enriches with a local Ollama LLM (`gemma4:e4b-mlx`) for injuries and editorial blurbs, runs a Poisson-per-match + Monte Carlo tournament simulation (50k runs), writes JSON to `public/data/`, and `git push`es. Cloudflare (Workers static assets, Git-connected) auto-deploys a static Next.js site that reads the JSON. **No backend, no database, no cloud compute, no inbound API.**

---

## Locked decisions — do not re-litigate without explicit user request

These were resolved across multiple PRD revisions. The PRD §12 "Resolved" block has the rationale.

| Area | Decision |
|---|---|
| Frontend | Next.js 15 (static export) + Tailwind + Recharts/visx |
| Compute | Python 3.12, `requests` + `beautifulsoup4` + `numpy` + `pandas` |
| LLM | local Ollama `gemma4:e4b-mlx` (bake-off vs `qwen2.5:14b` planned pre-launch) |
| Storage | JSON files in `public/data/`, versioned in git. No database. |
| Hosting | Cloudflare Workers static assets, Git-connected (free permanent tier), `*.workers.dev` subdomain |
| Scheduler | macOS launchd, 06:00 local daily |
| Cost ceiling | $0 — no paid APIs, no AWS, no paid hosting |
| Scope | Read-only viewer. No accounts, no pools, no what-if simulator |

**Explicitly rejected** (PRD §8 has the reasoning — don't re-propose without cause):
- GitHub Actions cron / any cloud compute (would force a second LLM-less code path)
- Cloudflare Tunnel / ngrok / any inbound trigger API
- AWS (12-month free tier expires; Cloudflare is permanent)
- Database of any kind
- Paid sports data APIs (API-Football, Sportmonks, etc.)

---

## Conventions for code we'll write

- **PRD changes**: edit `PRD.md` and bump its `Status: Draft vX.Y` frontmatter. Move resolved questions to the "Resolved" sub-section in §12 — don't delete them; the rationale matters.
- **CLAUDE.md changes**: keep this file tight (loaded into every conversation). Detail belongs in the PRD.
- **Frontend**: TypeScript strict mode, server components where the static export allows, Tailwind utility classes (no CSS modules).
- **Python**: standard library + the four packages above. Avoid frameworks.
- **Data files**: `public/data/*.json`. Never gitignored. Schema drift means a PRD/version bump.
- **Scrapers**: identify with a UA, respect `robots.txt`, hit each source at most once per `make update` run.
- **Monte Carlo**: N=50k unless calibrated otherwise. Seed for reproducibility in tests, not in production runs.
- **LLM output that reaches users**: must show "AI summary" badge and cite source headlines (PRD §6.4a).

---

## Commands (planned — none implemented yet)

| Command | What it does | When it lands |
|---|---|---|
| `make update` | Full daily pipeline (scrape → LLM → simulate → write JSON → commit → push) | Phase 0 (stub) → fleshed out across Phases 1–5 |
| `make dev` | Next.js dev server | Phase 0 |
| `make build` | Static export to `out/` | Phase 0 |
| `make bake-off` | One-time LLM bake-off (gemma4 vs qwen2.5 on 20 sample headlines) | Phase 5 |

---

## Continuing from another machine

This repo is the only thing you need. Steps:

1. `git clone <remote>`
2. Read `PRD.md` (full design) and this file (current state + conventions).
3. Install once:
   ```bash
   # Node + Python toolchains as you prefer (asdf, mise, brew)
   ollama pull gemma4:e4b-mlx
   ```
4. Check the "Current state" section above to see which Phase pointer to pick up.
5. When you finish a Phase, update the "Current state" pointer here and commit.

---

## Things Claude should NOT do without asking

- Initialize a git remote, push, or create a GitHub repo on the user's behalf.
- Introduce any paid service, even with a free tier.
- Add a second compute environment (Lambda, Actions, etc.) "just in case".
- Add a database, ORM, or backend service.
- Suggest model upgrades to GPT-/Claude-/Gemini-hosted APIs for the LLM layer — local Ollama is a deliberate choice.
