# UNMAPPED Protocol — local development shortcuts
# Requires: Docker + Docker Compose v2 (docker compose, not docker-compose)
# Optional targets for bare-metal dev require: Python 3.11+, Node 20+, npm

.DEFAULT_GOAL := help

# ── Docker targets ──────────────────────────────────────────────────────────

## Launch the full stack (backend + frontend) in Docker.
## First build: ~3-5 min (downloads torch CPU, spaCy model, E5-small embedder, npm deps).
## Subsequent builds: <30 s.
## Access: http://localhost:5173 (SPA) | http://localhost:8000/docs (API docs)
dev:
	docker compose up --build

## Launch in detached mode (background).
up:
	docker compose up --build -d

## Stop and remove containers (keeps volumes).
down:
	docker compose down

## Stop and remove containers + volumes (full clean).
clean:
	docker compose down -v --remove-orphans

## Tail combined logs.
logs:
	docker compose logs -f

## Tail backend logs only.
logs-backend:
	docker compose logs -f backend

## Rebuild just the backend image (e.g. after Python dependency change).
rebuild-backend:
	docker compose build --no-cache backend

## Open an interactive shell inside the running backend container.
shell:
	docker compose exec backend bash

# ── Local (no Docker) ───────────────────────────────────────────────────────

## Install Python deps + spaCy model for bare-metal backend dev.
## Requires Python 3.11+. Creates a venv at .venv/.
install-backend:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/python -m spacy download xx_ent_wiki_sm

## Start the backend API server locally (no Docker).
## Requires install-backend to have been run first.
run-backend:
	@cp -n .env.example .env 2>/dev/null || true
	.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## Install Node deps for bare-metal frontend dev.
install-frontend:
	cd frontend && npm install

## Start the frontend dev server (proxies /parse to localhost:8000).
## Requires run-backend to be running in another terminal.
run-frontend:
	cd frontend && VITE_API_URL=http://localhost:8000 npm run dev

# ── Testing ─────────────────────────────────────────────────────────────────

## Run the full Python test suite (149 tests).
test:
	.venv/bin/pytest tests/ -q

## Run tests with coverage report.
test-cov:
	.venv/bin/pytest tests/ -q --cov=app --cov-report=term-missing

## Run only the multilingual tests.
test-multilingual:
	.venv/bin/pytest tests/test_multilingual.py -v

## Run frontend tests.
test-frontend:
	cd frontend && npm test

# ── Lint / type-check ───────────────────────────────────────────────────────

lint:
	.venv/bin/ruff check app/ tests/
	cd frontend && npm run lint

# ── Help ────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  UNMAPPED Protocol — local dev commands"
	@echo ""
	@echo "  Docker (recommended):"
	@echo "    make dev               Launch full stack (builds if needed)"
	@echo "    make up                Same but detached"
	@echo "    make down              Stop containers"
	@echo "    make clean             Stop + wipe volumes"
	@echo "    make logs              Tail all logs"
	@echo "    make rebuild-backend   Force-rebuild backend image"
	@echo ""
	@echo "  Bare-metal:"
	@echo "    make install-backend   Create venv + install Python deps"
	@echo "    make run-backend       Start uvicorn on :8000"
	@echo "    make install-frontend  npm install"
	@echo "    make run-frontend      Start Vite on :5173"
	@echo ""
	@echo "  Tests:"
	@echo "    make test              Run all 149 pytest tests"
	@echo "    make test-cov          Tests + coverage"
	@echo "    make test-frontend     Vitest"
	@echo ""

.PHONY: dev up down clean logs logs-backend rebuild-backend shell \
        install-backend run-backend install-frontend run-frontend \
        test test-cov test-multilingual test-frontend lint help
