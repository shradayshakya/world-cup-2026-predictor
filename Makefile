.PHONY: dev build update venv bake-off

PYTHON := .venv/bin/python3

dev:
	npm run dev

build:
	npm run build

venv:
	python3 -m venv .venv
	.venv/bin/pip install -q --upgrade pip
	.venv/bin/pip install -q -r requirements.txt

bake-off:
	$(PYTHON) scripts/bakeoff.py

update:
	$(PYTHON) scripts/update.py
	git add public/data/*.json
	git commit -m "Daily update $$(date -u +%Y-%m-%dT%H:%M:%SZ)"
	git push origin main
