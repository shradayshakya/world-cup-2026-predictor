# World Cup 2026 Predictor — PRD

**Status:** Draft v1.0
**Last updated:** 2026-06-18
**Owner:** Shraday Shakya

---

## 1. Overview

A read-only web app that shows, for the 2026 FIFA World Cup, the live probability of each team:

- winning their group / finishing 2nd / 3rd / 4th
- advancing past each knockout round (R32, R16, QF, SF, Final)
- winning the tournament
- winning each individual upcoming match (with predicted scoreline)
- producing the Golden Boot top scorer

Probabilities are recomputed daily from publicly scraped data (Elo, results, injuries) and a Monte Carlo simulation of the remaining tournament.

## 2. Context & constraints

- **Tournament is already underway.** Started 2026-06-11. The product must condition on matches already played, not predict from a clean slate.
- **Format:** 48 teams, 12 groups of 4, top 2 + 8 best 3rd-placed → R32 → R16 → QF → SF → 3rd place → Final. 104 matches total.
- **Hosts:** USA, Canada, Mexico.
- **Zero budget.** Everything must run on free tiers or local compute. No paid APIs.

## 3. Goals / Non-goals

### Goals
- Live, daily-updated tournament probabilities, freely accessible online.
- Transparent: surface *why* a team's probability changed (Elo shift, key injury, group rival result).
- Match-by-match score predictions with confidence.
- Clean, fast, mobile-friendly read-only UI.

### Non-goals
- User accounts, prediction pools, or social features.
- Live in-match probability updates (we update once a day).
- "What-if" simulator where users override match outcomes. *(deferred — too much UX scope for v1)*
- Club / domestic football. National teams only.
- Historical World Cups (2022 and earlier). *(deferred)*

## 4. Users & user stories

**Primary user:** football fan curious about how their team is tracking.

- *As a fan*, I want to see my team's chance of advancing past the group, so I know what they need from the remaining group matches.
- *As a fan*, I want to see the predicted score for tonight's match.
- *As a fan*, I want to see the full bracket with probabilities at each node.
- *As a fan*, I want to see why probabilities moved (an injury, an upset).

## 5. Views (information architecture)

### 5.1 Home / Overview
- **All remaining teams, ranked by tournament-winner probability**, in a single stacked horizontal bar (each segment = one team's % of "winning the tournament" mass). Hovering a segment shows the team and its exact probability. Eliminated teams are excluded from this bar (they're at 0%).
- "Today's matches" strip with predicted scorelines.
- **Biggest movers since yesterday:** top 5 teams by absolute percentage-point change in tournament-winner probability. Green ↑ for gainers, red ↓ for losers. Each mover gets a **1-paragraph LLM-generated explanation** (see §6.4) of *why* the probability moved, drawn from results + injuries the pipeline ingested in the last 24h. Small "AI summary" badge.
- Last-updated timestamp banner.

### 5.1a Probability change display (global pattern)
- Wherever a probability is shown, adjacent small ↑/↓ arrow colored **green** (increase) or **red** (decrease) vs. yesterday's value.
- No arrow if change is < 0.1pp (avoid noise from Monte Carlo jitter).
- Tooltip on the arrow shows the delta (e.g., "+1.4pp since yesterday").

### 5.2 Bracket view
- Full 32-team knockout bracket.
- Each node shows the two most likely teams to occupy it, with %.
- Eliminated teams remain visible in past bracket positions with an "ELIMINATED" badge and greyed styling. Future-round nodes they could no longer reach exclude them from the candidate list.
- Click a node → match detail.

### 5.3 Group tables (×12)
- Current standings (real results so far).
- Remaining fixtures with predicted scores.
- Per-team: P(win group), P(2nd), P(3rd), P(advance), P(eliminated).
- Eliminated teams shown in the group table with an "ELIMINATED" badge; probabilities collapse to definite (0% advance, 100% eliminated).

### 5.4 Team detail page
- Squad list (with current injury/suspension flags from LLM layer).
- Current Elo + recent form (last 10).
- Probabilities at every tournament stage.
- Predicted path to the final (most likely opponent at each round).
- All remaining fixtures with predicted scores.

### 5.5 Match detail page
- Predicted scoreline + win/draw/loss probabilities.
- Score distribution heatmap (0–0 through 5–5).
- Key absences for each team.
- Head-to-head form.
- **Match preview blurb (60–80 words, LLM-generated, see §6.4)** — derived from team Elos, recent form, head-to-head, and key absences. Small "AI summary" badge.

## 6. Prediction model

Layered approach. Each layer is independently swappable.

### 6.1 Match-level model (Poisson-Elo)

1. **Inputs per team:** current Elo (from eloratings.net), home advantage (host nations only), key-player availability adjustment.
2. **Expected goals (xG):** convert Elo difference + average tournament goals into λ_home, λ_away using a Dixon-Coles-style calibration.
3. **Score distribution:** Poisson over the score grid (0–0 to ~7–7), with a small low-score correlation correction.
4. **Predicted scoreline:** modal score from the grid.
5. **W/D/L probabilities:** sum the grid.

### 6.2 Tournament-level model (Monte Carlo)

- Simulate the remainder of the tournament **N = 50,000** times.
- For each remaining match, sample the score from the Poisson grid.
- For knockouts, handle ET + penalties by sampling: if drawn after 90', extend λ by 1/3 for ET; if still drawn, coin-flip on pens weighted lightly by Elo.
- Aggregate: count tournament wins, SF appearances, etc. → divide by N → probabilities.

### 6.3 LLM adjustment layer (qualitative)

- Scrape last 24h of football news (BBC, Guardian, ESPN RSS).
- Feed headlines + team rosters into **local Ollama running `gemma4:e4b-mlx`** (Apple Silicon-optimized, ~3GB, fast on M-series Macs).
- Extract structured `{team, player, status: out|doubt|suspended, until: round|date}` via JSON-mode prompting.
- Convert to a small Elo penalty (e.g., −15 Elo per "out" key player, scaled by player importance, capped at −60).
- **Model bake-off (one-time, pre-launch):** run `gemma4:e4b-mlx` and `qwen2.5:14b` over 20 sample headlines, pick whichever produces cleaner JSON. Lock in the winner; don't churn after that.

### 6.4 Editorial LLM layer (user-facing)

Same Ollama runtime as §6.3, two additional prompt templates:

**Movers commentary** (one per "biggest mover" each day)
- Input: yesterday's vs today's tournament-winner %, list of results in last 24h involving that team or its group rivals, injury deltas from §6.3.
- Output: 1 paragraph (≤60 words) explaining the movement.
- Example: *"Brazil's title odds fell 2.3pp after Cameroon held them 1–1 and an Achilles knock left Vinicius Jr. doubtful for the final group match."*

**Match preview blurbs** (one per upcoming match, refreshed daily)
- Input: team Elos + delta, last-5 form, head-to-head record, key absences, predicted scoreline.
- Output: 60–80 words.
- Example: *"Germany face a Mexico side already through. With Musiala suspended and Mexico likely rotating, the model expects an open game (2.7 xG total) but slightly favours Germany on Elo difference."*

### 6.4a Hallucination guardrails (applies to all user-facing LLM output)
- LLM receives **only structured facts produced by our own pipeline** (numbers, ingested headlines). It does not freelance.
- Every user-visible LLM blurb displays a small **"AI summary"** badge.
- Each blurb links back to the specific source headlines it drew from.
- The match preview model is constrained to ≤80 words and forbidden from inventing specific stats not in its input.

### 6.5 Top scorer model

- Per-team Σ predicted goals across remaining matches × player's historical share of team goals × availability factor.
- Aggregate over Monte Carlo simulations.

## 7. Data sources (all free)

| Source | What we pull | Cadence | Method |
|---|---|---|---|
| `eloratings.net` (`World.tsv`) | Daily Elo per national team | Daily | TSV fetch |
| `eloratings.net` (`latest.tsv`) | Recent results, last 10 per WC26 team ("form") | Daily | TSV fetch |
| `eloratings.net` (`fixtures.tsv`) | Their own published win-expectancy, for an "according to Elo" comparison | Daily | TSV fetch |
| `en.wikipedia.org/wiki/2026_FIFA_World_Cup` | Group tables, fixtures, results | Daily | Scrape + parse |
| Wikipedia per-group + per-match pages | Lineups, goal scorers, attendance | Daily | Scrape |
| `fifa.com/worldcup` | Official fixtures (validation) | Daily | Scrape |
| `football-data.org` (free tier) | Backup match results | Daily | API |
| BBC Sport / Guardian football RSS | Injury & suspension news | Daily | RSS + LLM |
| Wikipedia squad pages | Roster baseline | Once + diff | Scrape |

**Scraping discipline:** identify ourselves with a UA, respect `robots.txt`, cache aggressively, never hit a source more than once per cron run.

**Parser robustness fallback:** when the structured BS4 parsers fail or return suspicious data (e.g., a group table with the wrong row count), fall back to the local Ollama model with the raw HTML/text and a "extract this as JSON" prompt. Internal use only; logged and surfaced on a maintenance page so we can fix the structured parser at leisure.

## 8. Architecture

Single, one-directional pipeline. No inbound API, no cloud compute, no tunnels.

```
┌──────────────────────────────────────────────────────────┐
│  Mac — launchd daily job (06:00 local)                   │
│  ──────────────────────────────────────                  │
│  1. Scrape eloratings.net → elo.json                     │
│  2. Scrape Wikipedia → results.json, fixtures.json       │
│  3. Scrape news RSS → headlines.json                     │
│  4. Ollama (gemma4:e4b-mlx) extract → injuries.json      │
│  5. Run Poisson + Monte Carlo → probabilities.json       │
│  6. git commit && git push origin main                   │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  GitHub repo (data + frontend source)                    │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Cloudflare Workers static assets (auto-deploys on push) │
│  Static Next.js site reads /public/data/*.json           │
└──────────────────────────────────────────────────────────┘
```

### Stack
- **Frontend:** Next.js 15 (static export) + Tailwind. Charts: Recharts or visx.
- **Compute:** Python 3.12 — `requests`, `beautifulsoup4`, `numpy`, `pandas`. Monte Carlo vectorized in numpy.
- **LLM layer:** local Ollama running `gemma4:e4b-mlx`. Called once per daily run.
- **Storage:** JSON files in the repo. No database.
- **Hosting:** Cloudflare Workers static assets, Git-connected deploy (frontend, free permanent tier). Production URL: a free `*.workers.dev` subdomain (final slug TBD at scaffold time, e.g., `world-cup-2026-predictor.<account>.workers.dev`). Custom domain can be added later without code changes. (Classic Cloudflare Pages with `*.pages.dev` is no longer the default Git-integration flow in the dashboard as of scaffold time — Workers static assets is the equivalent free, permanent option.)
- **Scheduler:** macOS launchd at 06:00 local daily. Manual fallback: `make update`.

### What we explicitly chose NOT to use
- **GitHub Actions cron / cloud compute** — would require a second code path without Ollama; the only failure mode it covers (Mac offline >24h during a 30-day tournament you're actively watching) is rare enough not to justify the complexity.
- **Cloudflare Tunnel / ngrok / remote trigger API** — solves a problem we don't have. If a manual refresh is ever needed while away, Tailscale SSH + `make update` is enough.
- **AWS** — free tier expires after 12 months; Cloudflare's static hosting is permanently free.
- **Database** — read-only static site; JSON files in git are simpler and version-controlled for free.

### Why static + JSON
- Zero runtime cost.
- Trivially cacheable; CDN does all the work.
- Data is small (<2 MB total) so the whole tournament fits in the browser.
- Git history gives us a free audit trail of probability changes over time.

## 9. Update cadence

- **Schedule:** launchd job at 06:00 local time daily.
- **Why early morning local:** Americas late-night matches have finished; you'll see the refresh when you wake up.
- **Catch-up behavior:** launchd will fire a missed job when the Mac next wakes from sleep, so cadence holds as long as the laptop is opened daily.
- **Manual trigger:** `make update` from the terminal.
- **No live in-match updates.** A small banner shows "Last updated: X hours ago."

## 10. Quality bar

- **Calibration check:** after each match, compare prediction to actual. Log Brier score and log-loss; surface on an `/about` page so users can audit the model.
- **Monte Carlo stability:** N = 50k chosen so per-team tournament-win probability is stable to ±0.2pp run-to-run.
- **Page weight:** < 200 KB JS for the home page. Aggressive code splitting per route.
- **Lighthouse:** ≥ 95 on mobile.

## 11. Phasing

### Phase 0 — Scaffolding (day 1)
- Repo, Next.js skeleton, Tailwind, deploy "Hello WC26" to Cloudflare (Workers static assets).
- launchd plist + `make update` target that runs a dummy script, commits a `heartbeat.json`, and pushes.
- Verify auto-deploy on Cloudflare picks up the push.

### Phase 1 — Data pipeline (days 2–4)
- Scraper for eloratings.net.
- Scraper for Wikipedia results + group tables.
- Outputs `elo.json`, `results.json`, `groups.json`.

### Phase 2 — Match model (days 5–6)
- Poisson-Elo per-match probability + scoreline.
- `matches.json` with predicted scores for all remaining fixtures.

### Phase 3 — Tournament model (days 7–8)
- Monte Carlo over remainder of tournament.
- `probabilities.json` with per-team per-stage probabilities.

### Phase 4 — UI (days 9–12)
- Home, bracket, group tables, team detail, match detail.

### Phase 5 — LLM injury layer (days 13–14)
- News scrape (BBC/Guardian/ESPN RSS) + Ollama (`gemma4:e4b-mlx`) extraction → injury adjustments.
- One-time bake-off: also test `qwen2.5:14b` on 20 sample headlines; lock in whichever produces cleaner JSON.

### Phase 5b — Editorial LLM layer (day 15)
- Movers commentary prompt + rendering in the home page "biggest movers" panel.
- Match preview blurb prompt + rendering on match detail pages.
- "AI summary" badge component + source-headline linking.
- Reuses the §6.3 Ollama runtime — no new infrastructure.

### Phase 5c — Parser fallback (day 16, defensive)
- Wrap structured parsers with a sanity check (row counts, schema validation).
- On failure, retry with an Ollama extraction prompt and log to a maintenance page.

### Phase 6 — Polish (day 17)
- Calibration page, "biggest movers" diffing, mobile QA.

## 12. Open questions

*None blocking. All Phase-0 decisions resolved — ready to scaffold.*

### Resolved
- ~~**LLM choice for injury layer**~~ — Locked: local Ollama `gemma4:e4b-mlx`. Bake-off run 2026-06-18 (`scripts/bakeoff.py`, `make bake-off`): 20 curated headlines (6 real + 14 hand-crafted edge cases), same extraction prompt, both models scored against hand-labeled expected output. `gemma4:e4b-mlx` found all 12 expected entries (0 false negatives/positives, 1 status mismatch); `qwen2.5:14b` missed one entirely plus the same kind of mismatch. Clear win, no further bake-off needed unless re-evaluating later.
- ~~**LLM job scope for the injury layer**~~ — Locked: the LLM is asked only to extract `{player, status, until}` from headline text — never the player's team. Team attribution and "key player" importance are resolved deterministically against the scraped roster (`squads.json`, caps-ranked) instead, since the LLM doesn't reliably know which country a player represents from headline text alone (verified: real headlines like "Pulisic training solo..." don't name "USA"), and narrowing its job shrinks what it can hallucinate (PRD §6.4a's guardrail spirit, applied here too even though that section is nominally about the editorial layer).
- ~~**"Until" date handling**~~ — Locked: captured as free text for display, not parsed into a structured date or used for per-match penalty windows. The daily re-scrape makes this self-correcting (a resolved injury stops appearing in the next day's headlines and the penalty naturally lapses) without needing date-range logic.
- ~~**Scheduler**~~ — Locked: macOS launchd. No GitHub Actions, no Cloudflare Tunnel, no AWS.
- ~~**Home page tournament-winner display**~~ — Locked: all remaining teams in a single stacked horizontal bar, ranked. Eliminated teams excluded from the bar.
- ~~**Probability change UX**~~ — Locked: green ↑ / red ↓ arrows next to every probability (suppressed below 0.1pp jitter threshold). "Biggest movers" panel on home = top 5 teams by absolute pp change since yesterday.
- ~~**Domain**~~ — Locked: free `*.workers.dev` subdomain on Cloudflare (Workers static assets, Git-connected — the dashboard's classic Pages flow with `*.pages.dev` was unavailable at scaffold time). Custom domain deferred.
- ~~**Eliminated teams**~~ — Locked: kept visible everywhere with an "ELIMINATED" badge and greyed styling; probabilities collapse to 0% advance / 100% eliminated. Excluded from the home stacked bar (which only ranks live contenders).
- ~~**Charting library**~~ — Locked: no Recharts/visx after all. The two charts actually needed (the home stacked bar, the score-distribution heatmap) don't fit either library's standard chart types well; hand-rolled with Tailwind flex/grid instead, keeping every Phase 4 page a zero-JS Server Component.
- ~~**Bracket node probabilities**~~ — Locked: §5.2's "most likely 2 teams per node" is computed by `scripts/model/simulate.py` tracking per-slot home/away occupancy counters during the existing Monte Carlo loop, output to `public/data/bracket.json`. The third-place bracket-slot assignment (within that same simulation) finds *a* valid bipartite matching of qualifying 3rd-place teams to candidate slots, not necessarily FIFA's exact official table — acceptable for prediction purposes.
- ~~**Score-model calibration vs. LLM-based scoring**~~ — Considered and rejected switching the per-match scoreline model to LLM-based estimation (feeding player/tactics/formation data to Ollama) after predictions felt too uniform (41/48 matches predicted exactly 1-1). Rejected because: no player/tactics data source exists, a small local model has no calibration feedback loop the way the Poisson model does (PRD §10's Brier-score audit), and §6.3/6.4 already scope LLM use to injury adjustments and editorial text, not the core numeric model. First recalibrated `GOAL_SUPREMACY_PER_400_ELO` (1.0 → 2.5) against eloratings.net's own win expectancy, which fixed decisiveness (cut disagreement from ~12.6pp to ~1.5pp) but barely moved scoreline variety. Investigated why and found a genuine structural bug, not just a tuning gap: the additive Elo-to-goals formula held total expected goals constant regardless of Elo gap, capping the favorite's expected goals at 2.45 — meaning a Poisson mode (floor of expected goals) could mathematically never reach 3, so no Elo gap, however large, could ever produce a 3-0 prediction. Replaced it with a multiplicative formula (`ratio = 10^(elo_diff/500)` scaling each side's expected goals, rather than redistributing a fixed total) — fits eloratings.net even better (0.74pp avg error) and unlocks blowout scorelines (e.g. Spain vs Saudi Arabia → 4-0 at 96%) while leaving close matches untouched. 6 distinct scorelines now vs. 3 before. The remaining UI-level fix (a "top scorelines" breakdown table on the match page, since even a well-calibrated model's single modal scoreline is a narrow statistic) still stands alongside this. A third round then found the multiplicative formula had the *mirror* problem: it holds `lambda_home * lambda_away` constant instead of the sum, which makes 2-1/1-2-style scorelines (needing both teams' expected goals elevated at once) structurally unreachable. Fixed by letting total expected goals grow with the Elo gap (`TOTAL_GOALS_GROWTH_RATE = 0.7`) instead of staying frozen — 9 distinct scorelines now, trading a bit of eloratings.net fit (2.07pp avg error, still far better than the original 12.6pp) for that variety. 1-0/0-1 still never appear, independent of all three rounds — that's the Dixon-Coles correlation term deliberately favoring 1-1/0-0, a real and intentional effect, not a gap in the Elo-to-goals mapping.

---

*Next step after PRD lock-in: scaffold the repo and stand up Phase 0.*
