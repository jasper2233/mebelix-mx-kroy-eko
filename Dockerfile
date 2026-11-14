# MebeliX Kroy — konteynerlar: web (nginx + frontend), api (FastAPI + optimizator).
# docker compose up -d --build   →   http://localhost:8080

# ── 1) frontendni yig'ish ──
FROM node:22-alpine AS build-web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ── 2) web: nginx (statik fayllar + /api proksi) ──
FROM nginx:1.27-alpine AS web
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-web /web/dist /usr/share/nginx/html

# ── 3) api: FastAPI (frontendni ham o'zi xizmat qila oladi — bitta konteynerli rejim) ──
FROM python:3.12-slim AS api
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MEBELIX_WEB_DIR=/app/frontend/dist MEBELIX_CHROME=/usr/bin/chromium
# «Печать отчета» A4 PDF (va «Скачать PDF») — headless Chromium bilan (services/pdf_render.py); kirill shriftlari bilan.
# Chromium bo'lmasa server PDF yasay olmaydi va hisobot faqat ekran ko'rinishida ochiladi (2026-11-14 xodimlar shikoyati).
RUN apt-get update && apt-get install -y --no-install-recommends chromium fonts-dejavu-core fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=build-web /web/dist /app/frontend/dist
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
