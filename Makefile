UV := uv
NPM := npm
export DJANGO_SECRET_KEY ?= dev-only-change-me

.DEFAULT_GOAL := help

.PHONY: help install init-env bootstrap migrate build typecheck test check \
	dev dev-vite dev-django clean cli-help

help: ## Show targets
	@echo "text-to-google-keep — common tasks"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "} {printf "  %-14s %s\n", $$1, $$2}'
	@echo ""
	@echo "Local web: two terminals — $(MAKE) dev-vite | $(MAKE) dev-django"
	@echo "Then open http://127.0.0.1:8000/ (see README for .env / OAuth)."

install: ## uv sync + npm install
	$(UV) sync
	$(NPM) install

init-env: ## Copy .env.example → .env if .env is missing
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env"; else echo ".env already exists"; fi

bootstrap: init-env install build migrate ## First-time setup (needs .env edited for DB)

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

dev: ## Hint for running Vite + Django
	@echo "Terminal 1: $(MAKE) dev-vite"
	@echo "Terminal 2: $(MAKE) dev-django"

dev-vite: ## Vite dev server (HMR on :5173)
	$(NPM) run dev

dev-django: ## Django runserver on :8000 (set DJANGO_USE_SQLITE=true if needed)
	$(UV) run python manage.py runserver

clean: ## Remove frontend/dist
	rm -rf frontend/dist

cli-help: ## CLI --help
	$(UV) run text-to-google-keep --help
