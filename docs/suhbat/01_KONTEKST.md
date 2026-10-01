# MebeliX Kroy — loyiha konteksti (Claude Code har sessiyada o'qiydi)

> Bu fayl `CLAUDE.md` orqali avtomatik yuklanadi. Katta bosqichdan keyin «Holat» va «Keyingi ishlar» bo'limlarini
> yangilang. To'liq suhbat tarixi — `docs/suhbat/02_SUHBAT_TARIXI.md`, ish tarixi — `git log`.

## Kim, nima, nega
- Buyurtmachi — O'zbekistondagi mebel korxonasi egasi (claude.ai loyihasi «jasur giblab»). Muloqot **o'zbekcha (lotin)**,
  norasmiy; javoblar qisqa va aniq bo'lsin, savol bo'lsa — so'rang (taxmin qilmang).
- Maqsad: korxonaning **o'z** listli kroy (raskroy) dasturi **«MebeliX Kroy»** — xodimlarga tanish ish oqimi
  (hozir ular GibLab ishlatadi), MES/ERP bilan REST orqali ulanadi, **aniqligi GibLab'dan yaxshi bo'lishi shart**.
- Xodimlar detallarni Bazis-Mebelshik → GibLab `.project` (XML) orqali oladi; GibLab Windows'da, USB himoya kaliti bilan.

## Qat'iy cheklovlar (foydalanuvchi so'zlari — o'zgarmaydi)
- «lekin giblabni sertifikatiga tegma yani kalitiga . u aftorning huquqi»
- «qaytaraman hech bir tizimni buzmoqchi emasman . men uzimni tizimimni qurmoqchiman»
- «hech birini aftorlik huquqiga tegma va urganib chiq» (GibLab va SketchCut PRO — faqat o'rganish)
- «yana bir narsa giblabni sertifikatiga tegma . u aftorligi himoyasida . bizga uzimizning dastur qiziq , boshqalarniki emas»
- Dastlabki prompt: «GibLab kodini, JS/CSS fayllarini, ikonkalarini, logosini, nomini, yordam matnlarini, fayl
  formatlarini nusxalama va yuklab olma. Hamma narsa noldan yoziladi.» · Backend: «Uni buzma — kengaytir.»
  · Postprotsessor: «bizning arra stanogimiz formati (formatni men beraman)».
- Amalda: HASP/Sentinel/litsenziya fayllariga tegilmaydi, ikkilik fayllar/GWT kodi dekompilyatsiya qilinmaydi, yordam
  matnlari ko'chirilmaydi (faqat funksional ma'noni tushunish uchun o'qiladi); interfeysda «GibLab» so'zi yo'q.
  GibLab/SketchCut arxivlari bu loyihaga kiritilmagan.

## Tarix (qisqa)
1. **2026-09-30** — v1 paket (`PROMPT_CLAUDE_CODE.md`, `UI_SPEC.md`, `screens/`) bo'yicha noldan: FastAPI backend,
   gilyotina optimizatori (kesish daraxti), React+TS frontend (AG Grid, ru/uz), qoldiqlar ombori, hisobot, QR
   etiketkalar, postprotsessor shablonlari, MES API, `.project` importi, sex rejimi, Docker, e2e; mustaqil tekshiruvlar
   (XSS, ombor yaxlitligi, NaN, guruhlash fuzz). Foydalanuvchi avvalgi HTML prototiplarni («GibLab_Pro.html» va h.k.)
   «xodimlarni chalkashtiradi» deb rad etgan — interfeys xodimlarga tanish joylashuvda qayta qurilgan.
2. **2026-10-01** — v2 yangilanish paketi (`docs/mebelix/`) qo'llandi: N1 biznes qoidalari, UI tafsilotlari, yorliqlar;
   205 ta real `.project` bilan solishtirish; optimizator kuchaytirildi (ustunli joylash, bin completion, SVC,
   qoldiqni yig'ish, qat'iy muddatlar); mustaqil agent ko'rib chiqdi (4 kamchilik tuzatildi).
3. **2026-10-01** — VS Code + Claude Code uchun to'liq zip (shu hujjatlar bilan).

## Holat (2026-10-01)
- Korpus (205 loyiha, 397 kroy, avvalgi dastur saqlagan natija bilan) — `docs/mebelix/P_TAQQOSLASH.md`:
  «Стандарт» **1185 list vs 1212** (15 kroyda kam, 0 da ko'p), деловой qoldiq **753 vs 652 m²**, kesish 22 153 vs 22 457 m;
  «Быстро» 1212 vs 1212 (≤ 2 s). Kromka metri 303/303 mos, CNC 8359–8360/8360 mos. Tekshiruv xatosi 0.
- Testlar: backend **91** (SQLite + PostgreSQL), Playwright e2e **3**, TypeScript toza.
- «Detskiy kravat» benchmarki: 2 list, 1-list 92.83 % (max rejim 93.18 %; GibLab 93.87 %).

## Ishga tushirish va tekshirish
- Windows: `run.bat` → http://localhost:8000 · ishlab chiqish: `dev.bat` (backend :8000 + Vite :5173) yoki VS Code
  «Run and Debug» → «Full stack». Linux/macOS: `./run.sh`, `./dev.sh`. API hujjati: `/docs`.
- Backend testlari: `cd backend && pytest -q` (≈2–3 daqiqa). PostgreSQL: `MEBELIX_TEST_DB_URL=postgresql+psycopg://...`.
- E2E: `cd frontend && npm ci && npx playwright install chromium && npm run e2e` (boshqa Chrome: `PW_CHROMIUM=...`).
- Korpus: `cd tools/bench && python3 compare.py normal` (≈8 daqiqa, 2 yadro), `el_check.py`, `xnc_check.py`;
  korpusni qayta qurish: `corpus_build.py` (`tools/bench/projects/` — korxona fayllari, git'ga kirmaydi).
- i18n: matnlar faqat `frontend/scripts/i18n_src.py` da → `python frontend/scripts/i18n_src.py` → `src/i18n/*.json`;
  backend xabarlari — `backend/app/i18n.py`.
- Frontend o'zgarsa `npm run build` (backend `frontend/dist` ni xizmat qiladi; dist git'ga kirmaydi, zipda yig'ilgan).

## Texnik eslatmalar (tuzoqlar)
- Optimizator vaqt byudjeti bilan ishlaydi → kompyuter yuklamasiga qarab natija ±1 list tebranishi mumkin; testlar aniq
  joylashuvga bog'lanmasin. Har natija `services/validate.py` dan o'tishi shart.
- Kesim darajasi = burilish raqami (≤ «Макс. количество вращений»); qirindi 0 yoki ≥ min. obrezka (list chetida emas).
- `colpack.py` numpy talab qiladi (`requirements.txt` da bor). Yangi detal Ткт = «Учет текстуры» (berilmasa).
- `optimize()` bosqichlari: asosiy qidiruv → 3 bosqichli polosa muqobili → (list kamayishi mumkin bo'lsa) bin completion
  + SVC → oxirgi/boshqa listlarda qoldiqni yig'ish. Vaqtlar: `QUALITY_BUDGET`, `IMPROVE_BUDGET`, `COMPACT_BUDGET`.
- Korxona fayllarida mijoz ismlari bor — `tools/bench/projects/` va `docs/suhbat/ilovalar/` ommaviy repoga chiqmasin.

## Keyingi ishlar (backlog)
- Foydalanuvchidan javob kerak: (1) kromka qalinligi 0 qolsinmi; (2) arra stanogi modeli va postprotsessor formati
  (namuna fayl); (3) MES API manzillari, auth, webhook; (4) etiketka printeri va o'lchami.
- UI (v2 spetsifikatsiyasidan qolgan, past ustuvorlik): «Изделия» xossalari oynasi (Свойства | Программа), umumiy
  «Сортировка» oynasi, Excel import profillari, «Заказать» (MES) oynasi, CL/O/SP/GR hisoblari (205 loyihada uchramaydi),
  katalog oynasi sayqali; Docker compose'ni real muhitda sinash.
- Optimizator g'oyalari: «Быстро» rejimida 23 kroyda +1 list; 74 kroyda деловой qoldiq GibLab'dan kam (u bir nechta
  o'rta bo'lak qoldiradi); kravat 1-listi 92.83 % vs 93.87 %.

## Fayllar xaritasi
- `backend/app/main.py` (REST), `api_extra.py` (ombor, sozlamalar, MES), `models.py` (Pydantic, v1 migratsiyalari),
  `services/optimizer.py` + `colpack.py` (kroy), `validate.py`, `editor.py` (qo'lda tahrir), `calc.py` (narx, kromka,
  sarf), `xnc.py`, `render.py` (hisobot), `labels.py`, `postprocessors.py`, `plugins/legacy_project.py` (.project import).
- `frontend/src/features/cs/*` (detallar, parametrlar, listlar, kroy), `shared/hotkeys.ts`, `store/ui.ts`, `e2e/kroy.spec.ts`.
- `docs/mebelix/` — v2 spetsifikatsiyalar (A–O) va taqqoslash (P); `docs/suhbat/` — suhbat arxivi; `tools/bench/` — korpus.
