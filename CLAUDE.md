# MebeliX Kroy — doimiy qoidalar (Claude Code uchun)

Loyiha konteksti (maqsad, tarix, holat, keyingi ishlar) — har sessiyada yuklanadi:
@docs/suhbat/01_KONTEKST.md

Foydalanuvchi bilan **o'zbekcha (lotin)** yozing; qisqa va aniq. Savol bo'lsa — so'rang, taxmin qilmang.
Suhbat tarixi: `docs/suhbat/02_SUHBAT_TARIXI.md`; batafsil texnik xulosa: `docs/suhbat/03_TEXNIK_XULOSA_EN.md`.

## Manbalar
1. Biznes qoidalari — `docs/mebelix/B_DOMAIN_RULES.md`; optimizator — `docs/mebelix/C_CS_OPTIMIZER_SPEC.md`;
   UI — `docs/mebelix/D_UI_SPEC_v2.md` (+ v1 `UI_SPEC.md`); yorliqlar — `docs/mebelix/E_HOTKEYS.md`;
   atamalar — `docs/mebelix/A_GLOSSARY.md`; ish oqimi — `docs/mebelix/O_WORKFLOW_QUICKSTART.md`.
2. Formulani o'zgartirishdan oldin `docs/mebelix/L_ACCEPTANCE_TESTS.md` dagi raqamlarni va
   `backend/tests/test_rules_v2.py` ni tekshiring — ular korxona loyihalaridagi saqlangan natijalar bilan solishtirilgan.
3. UI yorliqlari (rus) va xodimlar ustun nomlari (o'zbek) — `A_GLOSSARY.md` dagi kabi; faqat i18n orqali:
   frontend — `frontend/scripts/i18n_src.py` (bitta manba → `src/i18n/ru.json`, `uz.json`), backend — `app/i18n.py`.

## Mualliflik huquqi (qat'iy)
4. Boshqa dasturlarning (GibLab, SketchCut va h.k.) kodi, JS/CSS, ikonkalari, logosi, nomi, yordam matnlari, fayl
   formatlari nusxalanmaydi — hammasi noldan yoziladi. Interfeysda «GibLab» so'zi ishlatilmaydi; nom — «MebeliX Kroy».
5. GibLab litsenziyasi / USB himoya kaliti (HASP/Sentinel) va dastur fayllariga tegilmaydi, dekompilyatsiya qilinmaydi.
   Yordam sahifalari faqat funksional ma'noni tushunish uchun o'qiladi; `.project` importi — korxonaning o'z fayllari
   uchun (ichki ikkilik kroy natijasi o'qilmaydi, loyiha qayta kroy qilinadi).

## Kod
6. Backend: buzmang — kengaytiring (API mos qolsin; eski JSON `model_validator` migratsiyalari bilan o'qiladi).
7. Optimizator (`backend/app/services/optimizer.py`, `colpack.py`) o'zgarsa:
   `cd backend && pytest -q` va `cd tools/bench && python compare.py normal` — listlar soni ko'paymasin,
   tekshiruv xatosi 0 bo'lsin (oxirgi natijalar `docs/mebelix/P_TAQQOSLASH.md` da).
8. Kesish daraxti qoidalari: kesim darajasi = burilish raqami (≤ «Макс. количество вращений»), kesimlar orasida propil,
   ichki qirindi 0 yoki ≥ «Минимальная обрезка» (list chetida emas), har natija `services/validate.py` dan o'tadi.
9. Testlar: `cd backend && pytest -q` (SQLite; PostgreSQL: `MEBELIX_TEST_DB_URL=postgresql+psycopg://...`),
   `cd frontend && npm run e2e` (birinchi marta `npx playwright install chromium`; boshqa Chrome: `PW_CHROMIUM=...`).
   Frontend o'zgarsa `npm run build` (backend `frontend/dist` ni xizmat qiladi).
10. Korxona fayllari (`tools/bench/projects/`, `docs/suhbat/ilovalar/`) git'ga va ommaviy joylarga chiqmasin.
11. Har katta bosqichdan keyin `docs/suhbat/01_KONTEKST.md` dagi «Holat» va «Keyingi ishlar» ni yangilang.

## Ochiq savollar (foydalanuvchidan so'raladi, taxmin qilinmaydi)
- Kromka qalinligi (PVC 1 mm) korxona loyihalarida 0 — shunday qolsinmi?
- Arra stanogi modeli va postprotsessor formati (namuna fayl) — format foydalanuvchidan keladi.
- MES API manzillari, autentifikatsiya, webhook formati.
- Etiketka printeri va o'lchami.
