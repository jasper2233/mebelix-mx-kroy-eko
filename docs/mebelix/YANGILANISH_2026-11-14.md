# MX Kroy yangilanishi — 2026-11-14 (server dasturchilari uchun)

**Nima o'zgardi:** backend (hisobot PDF sahifalari, optimizatorda yangi ixtiyoriy rejim), frontend (hisobot asboblar paneli,
CS parametrlari), `Dockerfile` (Chromium), `requirements.txt` (`pypdf`). Baza va migratsiyalar o'zgarmagan — baza qayta tiklanmaydi;
yangi CS maydonlari eski loyihalarda standart qiymat bilan o'qiladi.

| | |
| --- | --- |
| Kod | `MebeliX_Kroy` `master` va `mebelix-mx-kroy-eko` `eko-integratsiya` — shu fayl qo'shilgan commit |
| Yangilash | kodni olish → **konteynerni qayta yig'ish** (`docker compose build api web`, Chromium va `pypdf` o'rnatiladi) → qayta ishga tushirish |
| Docker bo'lmasa | serverga `chromium` (yoki Google Chrome) + kirill shriftlari, `pip install -r backend/requirements.txt`; Chrome yo'li odatiy joyda bo'lmasa `MEBELIX_CHROME` |
| Xodimlarga | **F5 kerak** (yangi tugmalar va sozlama) |

## 1. «Печать отчета»: PDF yuklab olish va sahifalar

Muammo: kroy.mebelix.uz da hisobot oddiy sahifa bo'lib ochilardi, PDF yuklab olish yo'q edi. Sabab — server PDF ni headless Chrome bilan
yasaydi (`services/pdf_render.py`), konteynerda Chrome yo'q edi → `report.pdf` 501 → ekran ko'rinishi. Endi:

* `Dockerfile` api bosqichi: `chromium fonts-dejavu-core fonts-liberation`, `MEBELIX_CHROME=/usr/bin/chromium`.
* Asboblar paneli: «Печать», **«Скачать PDF»**, **«Страницы»** (`1-3, 5, 8-`; bo'sh — hammasi). Yuklab olish va chop faqat tanlangan
  varaqlar — `POST /api/pdf/select-pages?pages=…&name=…` (tana — tayyor PDF, `application/pdf`; javob — yuklab olinadigan PDF,
  `X-Pages`, `X-Pages-Total`). Nginx `client_max_body_size 64m` yetadi.
* Tekshirish: `curl -X POST "…/api/projects/<id>/report.pdf" …` 200 va `application/pdf` qaytarishi kerak (501 bo'lsa — Chromium yo'q).

## 2. CS «Повторяющиеся карты» (ixtiyoriy, standart o'chiq)

CS «Параметры» → qo'shimchalar: «Повторяющиеся карты» va «Допуск листов для повторов» (0…10, standart 0). Yoqilsa kroy bir xil
kartalar guruhlaridan tuziladi (pilniy markazda paket bo'lib ustma-ust kesish, arrachi adashmaydi); listlar soni допуск dan ortiq
ko'paymaydi. O'chiq bo'lsa kroy natijasi avvalgidek.

## Tekshirish

* `cd backend && pytest -q` (yangi `tests/test_pdf_select_pages.py`, `tests/test_cs_repeat_maps.py`).
