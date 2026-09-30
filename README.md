# MebeliX Kroy

Listli materiallarni kesish (kroy) optimizatsiyasi — korxona MES tizimiga moslashtirilgan,
xodimlar uchun GibLab ga o'xshash ish oqimi bilan. Kod noldan yozilgan.

| Fayl/papka | Nima |
|---|---|
| `PROMPT_CLAUDE_CODE.md` | Claude Code ga beriladigan asosiy prompt (bosqichlar, qoidalar) |
| `UI_SPEC.md` | Har bir ekran, maydon, ustun, tugma va yorliqlar tavsifi |
| `screens/` | 33 ta ekran rasmi (faqat ma'lumot uchun, ilovaga qo'shilmaydi) |
| `backend/` | FastAPI backend: modellar, kroy algoritmi, narx, kromka, XNC, hisobot, API |

## Backendni ishga tushirish
```bash
cd backend
pip install -r requirements.txt
pytest -q                          # 3 test
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

## Asosiy API
- `GET/POST /api/projects`, `GET/PATCH/DELETE /api/projects/{id}`, `/copy`, `/undo`, `/redo`, `/export`
- `POST /api/projects/{id}/operations` (CS, EL, GR, XNC), `PUT/DELETE .../operations/{op}`, `/move`, `/clone`
- `POST .../operations/{op}/parts`, `/parts/delete`, `/parts/group-update`, `/parts/bulk/{swap|grain-on|grain-off}`, `/parts/move-to/{op2}`, `/parts/import`
- `PUT .../operations/{op}/sheets`
- `POST .../operations/{op}/optimize` → kroy natijasi; `GET .../maps/{n}.svg`; `DELETE .../result`; `PUT .../result` (qo'lda tahrir)
- `GET .../operations/{op}/edge-usage`, `GET .../xnc-stats`
- `GET /api/projects/{id}/report` (HTML hisobot), `/warehouse`
- `GET /api/catalog`, `POST /api/catalog/sync` (MES dan)

MES ga ulash: `MEBELIX_DB_URL` (PostgreSQL), `catalog/sync`, `Project.mes_order_ref`.
