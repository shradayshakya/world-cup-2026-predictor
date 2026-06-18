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
- **Next concrete steps** (per PRD §11 Phase 2 — match model):
  1. Poisson-Elo per-match probability + scoreline model, fed by `elo.json` + `results.json`.
  2. Write `matches.json` with predicted scores for all remaining fixtures.

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
