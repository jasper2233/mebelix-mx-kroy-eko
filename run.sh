#!/usr/bin/env bash
# MebeliX Kroy — Docker'siz bitta buyruq bilan:  ./run.sh   →  http://localhost:8000
# Talab: Python 3.11+, (birinchi marta) Node.js 20+ — frontendni yig'ish uchun.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8000}"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install -q -r backend/requirements.txt
if [ ! -f frontend/dist/index.html ] || [ "${REBUILD:-0}" = "1" ]; then
  (cd frontend && npm ci --no-audit --no-fund && npm run build)
fi
cd backend
echo "MebeliX Kroy: http://localhost:${PORT}  (API hujjati: /docs)"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
