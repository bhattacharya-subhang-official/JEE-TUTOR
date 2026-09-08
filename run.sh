#!/usr/bin/env bash
# ═══ JEE Tutor — start the server ═══
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
echo "Starting JEE Tutor on http://0.0.0.0:${PORT}"
exec python3 -m uvicorn app:app --host 0.0.0.0 --port "${PORT}"
