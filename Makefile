UV := uv
NPM := npm
export DJANGO_SECRET_KEY ?= dev-only-change-me

.DEFAULT_GOAL := help

.PHONY: help install init-env bootstrap migrate build typecheck test check \
	dev dev-vite dev-django db-create clean cli-help

help: ## Show targets
	@echo "text-to-google-keep — common tasks"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "} {printf "  %-14s %s\n", $$1, $$2}'
	@echo ""
	@echo "Local web: $(MAKE) dev (Vite + Django) — http://127.0.0.1:8000/"
	@echo "Or split: $(MAKE) dev-vite | $(MAKE) dev-django · README for .env / OAuth."

install: ## uv sync + npm install
	$(UV) sync
	$(NPM) install

init-env: ## Copy .env.example → .env if .env is missing
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env"; else echo ".env already exists"; fi

bootstrap: init-env install build migrate ## First-time setup (edit .env; make db-create for local Postgres)

db-create: ## Postgres role ttgk + DB ttgk_dev (psql -U postgres; use sudo -u postgres if needed)
	psql -U postgres -v ON_ERROR_STOP=1 -f scripts/postgres-local.sql

migrate: ## Django migrate
	$(UV) run python manage.py migrate

build: ## Frontend production build (tsc + vite)
	$(NPM) run build

typecheck: ## TypeScript check only
	$(NPM) run typecheck

test: ## Django tests + npm typecheck
	$(UV) run python manage.py test
	$(NPM) run typecheck

check: test build ## CI-style: tests, typecheck, and frontend build

dev: ## Run Vite + Django (Ctrl+C stops both)
	@./scripts/dev.sh

dev-vite: ## Vite dev server (HMR on :5173)
	$(NPM) run dev

dev-django: ## Django runserver on :8000 (PostgreSQL from .env)
	$(UV) run python manage.py runserver

clean: ## Remove frontend/dist
	rm -rf frontend/dist

cli-help: ## CLI --help
	$(UV) run text-to-google-keep --help
