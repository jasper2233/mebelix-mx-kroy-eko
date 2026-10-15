#!/usr/bin/env bash
# Ishlab chiquvchi rejimi: backend (reload) :8000 + Vite :5173 (/api proksi)
set -euo pipefail
cd "$(dirname "$0")"
(cd backend && python3 -m uvicorn app.main:app --reload --port 8000) &
trap 'kill 0' EXIT
cd frontend && npx vite
