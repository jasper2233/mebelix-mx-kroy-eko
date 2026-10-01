@echo off
REM MebeliX Kroy — ishlab chiquvchi rejimi (Windows): backend (avtoqayta yuklash) :8000 + Vite :5173 (/api proksi)
REM Talab: Python 3.11+, Node.js 20+
cd /d %~dp0
if not exist .venv\Scripts\python.exe python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt
if not exist frontend\node_modules (
  pushd frontend
  call npm ci --no-audit --no-fund
  popd
)
start "MebeliX backend :8000" /D "%~dp0backend" cmd /k python -m uvicorn app.main:app --reload --port 8000
cd frontend
echo Frontend: http://localhost:5173   Backend: http://localhost:8000/docs
call npx vite
