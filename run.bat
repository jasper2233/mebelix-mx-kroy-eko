@echo off
REM MebeliX Kroy — Windows: run.bat  ->  http://localhost:8000
REM Talab: Python 3.11+ va (birinchi marta) Node.js 20+
cd /d %~dp0
if not exist .venv\Scripts\python.exe python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r backend\requirements.txt
if not exist frontend\dist\index.html (
  pushd frontend
  call npm ci --no-audit --no-fund
  call npm run build
  popd
)
cd backend
echo MebeliX Kroy: http://localhost:8000   (API: /docs)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
