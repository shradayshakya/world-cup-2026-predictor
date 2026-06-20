# World Cup 2026 Predictor

Daily-updated prediction site for the 2026 FIFA World Cup. Live at https://world-cup-2026-predictor.shradayshakya.workers.dev

For the full design and current project status, see `PRD.md` and `CLAUDE.md`. This file is just the practical "how do I run this" reference.

## One-time setup

```bash
make venv               # creates .venv, installs requirements.txt
npm install              # frontend deps
ollama pull gemma4:e4b-mlx   # local LLM used for injury extraction + editorial blurbs
brew services start ollama   # make sure Ollama is running before `make update`
```

## Running the dev server

```bash
make dev   # npm run dev, http://localhost:3000
```

## Running the daily update manually

```bash
make update
```

This runs the full pipeline (`scripts/update.py`): scrapes eloratings.net/Wikipedia/news RSS, runs the Ollama injury extraction, rebuilds the match model and the 50,000-run Monte Carlo simulation, writes everything to `public/data/*.json`, then commits and pushes to `main` — which triggers Cloudflare's auto-deploy.

Takes roughly 15–25 minutes, mostly the Ollama calls (injury extraction + ~48 match preview blurbs). Safe to re-run any time — re-running with no new real-world changes just produces small Monte Carlo jitter (see PRD §10), not duplicate data.

If you only want to check the output without committing/pushing, run the script directly instead of through `make`:

```bash
.venv/bin/python3 scripts/update.py
```

then inspect `public/data/*.json` and decide whether to commit yourself.

## Automated daily run (launchd)

A launchd job is installed and runs `make update` automatically every day at **12:00 local time** (the Mac's system timezone — Nepal, UTC+5:45 — chosen so the previous evening's North American matches have all finished by then; see PRD §9 for the reasoning).

```bash
# Check it's loaded and see its schedule
launchctl list | grep wc26predictor
launchctl print gui/$(id -u)/com.shradayshakya.wc26predictor.update | grep -A8 calendar

# Logs from the most recent automated run
cat launchd/update.log
cat launchd/update.error.log

# Temporarily stop it (e.g. while away from a stable network)
launchctl unload ~/Library/LaunchAgents/com.shradayshakya.wc26predictor.update.plist

# Re-enable it
launchctl load ~/Library/LaunchAgents/com.shradayshakya.wc26predictor.update.plist
```

The plist source of truth lives in this repo at `launchd/com.shradayshakya.wc26predictor.update.plist`; the installed copy is at `~/Library/LaunchAgents/`. If you ever edit the schedule, re-copy it and reload:

```bash
cp launchd/com.shradayshakya.wc26predictor.update.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.shradayshakya.wc26predictor.update.plist
launchctl load ~/Library/LaunchAgents/com.shradayshakya.wc26predictor.update.plist
```

If the Mac is asleep at 12:00, launchd fires the job the next time it wakes — so daily cadence holds as long as you open the laptop at least once a day.

## Building the static site

```bash
make build   # npm run build, outputs to out/
```

## Other commands

| Command | What it does |
|---|---|
| `make bake-off` | Re-run the injury-extraction model comparison (`gemma4:e4b-mlx` vs `qwen2.5:14b`) — only needed if re-evaluating the LLM choice |

## Troubleshooting

- **`make update` fails partway through**: check `public/data/maintenance.json` first — the scrapers self-validate and log parser issues there (PRD §7/§11 Phase 5c). If it crashed before reaching that write, re-run; everything in `update.py` is safe to retry.
- **Ollama calls hang or time out**: confirm `ollama serve` is running (`brew services list`) and the model is pulled (`ollama list`).
- **Working tree dirty after a run**: `make update`'s `git add public/data/*.json` should catch every generated file — if something's uncommitted, check whether a new `public/data/*.json` file was added without updating that glob (it shouldn't need updating, but worth knowing).
