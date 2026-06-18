.PHONY: dev build update venv

PYTHON := .venv/bin/python3

dev:
	npm run dev

build:
	npm run build

venv:
	python3 -m venv .venv
	.venv/bin/pip install -q --upgrade pip
	.venv/bin/pip install -q -r requirements.txt

update:
	$(PYTHON) scripts/update.py
	git add public/data/heartbeat.json public/data/elo.json public/data/groups.json public/data/results.json public/data/matches.json public/data/probabilities.json
	git commit -m "Daily update $$(date -u +%Y-%m-%dT%H:%M:%SZ)"
	git push origin main
