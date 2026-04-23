#!/usr/bin/env bash
set -euo pipefail
set -m
cd "$(dirname "$0")/.."
cleanup() {
	for j in $(jobs -p); do
		kill "$j" 2>/dev/null || true
	done
}
trap cleanup INT TERM EXIT
npm run dev &
uv run python manage.py runserver &
wait
