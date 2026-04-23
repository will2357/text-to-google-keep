#!/usr/bin/env bash
set -euo pipefail
set -m
cd "$(dirname "$0")/.."

VITE_PID=""
DJANGO_PID=""

cleanup() {
	set +e
	pkill -f "/home/will/src/text-to-google-keep/node_modules/.bin/vite" 2>/dev/null || true
	pkill -f "manage.py runserver 127.0.0.1:${DJANGO_PORT:-8001}" 2>/dev/null || true
	for pid in "$VITE_PID" "$DJANGO_PID"; do
		[ -n "$pid" ] || continue
		# Kill the whole job process-group so child processes (node/python reloader) exit too.
		kill -TERM "-$pid" 2>/dev/null || true
	done
	sleep 0.2
	for pid in "$VITE_PID" "$DJANGO_PID"; do
		[ -n "$pid" ] || continue
		kill -KILL "-$pid" 2>/dev/null || true
	done
}
trap cleanup INT TERM EXIT
npm run dev &
VITE_PID=$!
DJANGO_PORT="${DJANGO_PORT:-8001}"
uv run python manage.py runserver "127.0.0.1:${DJANGO_PORT}" &
DJANGO_PID=$!
wait
