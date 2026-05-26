.PHONY: up down logs test lint dev help

# ──────────────────────────────────────────────────────────────────────────────
# Docker Compose
# ──────────────────────────────────────────────────────────────────────────────

## Start the full stack (API + Dashboard) in the background
up:
	docker compose up --build -d

## Stop the stack and remove volumes
down:
	docker compose down -v

## Follow container logs
logs:
	docker compose logs -f

# ──────────────────────────────────────────────────────────────────────────────
# Quality
# ──────────────────────────────────────────────────────────────────────────────

## Run tests with coverage (fails under 75 %)
test:
	pytest tests/ -v --cov=api --cov-fail-under=75 --cov-report=term-missing

## Lint with flake8
lint:
	flake8 api/ dashboard/ tests/ --max-line-length=120

# ──────────────────────────────────────────────────────────────────────────────
# Local development (no Docker)
# ──────────────────────────────────────────────────────────────────────────────

## Start the API locally (port 8000)
dev-api:
	uvicorn api.main:app --reload --port 8000

## Start the dashboard locally (port 8501)
dev-dashboard:
	streamlit run dashboard/app.py --server.port=8501

## Start both services locally (background)
dev:
	$(MAKE) dev-api &
	$(MAKE) dev-dashboard

# ──────────────────────────────────────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  DevOps Monitor — Available targets"
	@echo "  ────────────────────────────────────"
	@echo "  make up            Build & start Docker stack"
	@echo "  make down          Stop stack & remove volumes"
	@echo "  make logs          Follow container logs"
	@echo "  make test          Run pytest with coverage ≥ 75 %"
	@echo "  make lint          Run flake8 linter"
	@echo "  make dev-api       Start API locally (uvicorn --reload)"
	@echo "  make dev-dashboard Start dashboard locally (streamlit)"
	@echo ""
