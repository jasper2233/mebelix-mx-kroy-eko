# S. Parallel ishlovchilar uchun qoidalar (v2.2)

Bu fayl `R_GIBLAB_FEATURE_MATRIX.md` dagi to'lqin paketlarini bajaruvchi agentlar uchun. Avval o'qing: `CLAUDE.md` (doimiy qoidalar),
`docs/suhbat/01_KONTEKST.md`, o'z paketingizga tegishli `docs/mebelix/giblab_inventory/0N_*.md`.

## Mualliflik va litsenziya (buzilmaydi)
- `C:\GibLabLocal` dagi dastur, kalit, `.exe/.dll/.jar/.cache.html/.rpc`, HASP/litsenziya fayllariga **tegmang, ochmang**; GibLab oynasini
  ishga tushirmang va boshqarmang. Yordam sahifalari (`C:\GibLabLocal\pages\...`) faqat funksional ma'noni tushunish uchun o'qiladi
  (`scratchpad\h2t.py` matnga o'giradi). Yordam matni, rasm, ikonka nusxalanmaydi; interfeysda «GibLab» so'zi yo'q (nom — «MebeliX Kroy»).
- Korxona fayllari (`tools/bench/projects/`) mijoz ismlarini o'z ichiga oladi: hujjat/test/commitga ism yozmang, faqat umumiy hisoblar.
- Taxmin qilmang: yordam javob bermagan joyni **savol** sifatida hisobotingizga yozing (qaror foydalanuvchida), xulq-atvor noaniq
  bo'lsa — bitta konstanta/parametr orqasida standartni tanlang va hujjatda belgilang.

## Umumiy fayllar bo'yicha protokol (bir nechta agent bir daraxtda ishlaydi)
- Faqat **o'z paketingizning fayllarini** o'zgartiring; yangi kod uchun yangi modullar yarating (`services/<nom>.py`, `api_<nom>.py`,
  `features/<nom>/…`, `tests/test_<nom>.py`).
- Umumiy fayllar (`main.py`, `models.py`, `api/types.ts`, `api/hooks.ts`, `styles.css`, `app/Layout.tsx`, `project/ProjectView.tsx`,
  `project/opmeta.tsx`, `i18n.py`, `legacy_project.py`) — **kichik, aniq `Edit`** bilan, tahrirdan oldin shu joyni qayta o'qing
  (boshqa agent o'zgartirgan bo'lishi mumkin); butun faylni qayta yozmang; tahrir rad etilsa — qayta o'qib qaytadan urining.
- Router: yangi endpointlar `backend/app/api_<nom>.py` da `router = APIRouter(...)`; `main.py` da `api.include_router(...)` qatori
  `api.include_router(extra_router)` yonida bitta qator bilan ro'yxatdan o'tadi.
- i18n (frontend): `frontend/scripts/i18n_<nom>.py` yarating (ichida `a("kalit", "ru", "uz")` chaqiruvlari; `i18n_src.py` o'zi yuklaydi),
  so'ng `python frontend/scripts/i18n_src.py` — `ru.json/uz.json` qayta quriladi. Rus yorliqlari — xodimlar odatlangan atamalar;
  uz — to'liq o'zbekcha (lotin). Backend xabarlari — `app/i18n.py` (`"kalit": (ru, uz)` qatorini mos joyga qo'shing).
- Eski JSON/loyiha fayllari ochilishi shart: model maydonlari yangi bo'lsa — standart qiymat bilan (backend «buzma — kengaytir» qoidasi).

## Tekshirish
- Backend: `cd backend; <venv python> -m pytest tests/test_<nom>.py -q` (o'z testlaringiz) + tegilgan hududning mavjud testlari.
  To'liq to'plamni (`pytest -q`, ~3 daqiqa) hisobot oldidan bir marta yuriting. Venv: `D:\cloude giblab jasur\MebeliX_Kroy\.venv\Scripts\python.exe`.
- Frontend turlari: `cd frontend; <node>\npx.cmd tsc --noEmit -p .` (portativ Node: `D:\cloude giblab jasur\MebeliX_Kroy\tools\node`, PATH ga qo'shing).
- **`npm run build` va `npx playwright test` (e2e) ni yurgizmang** — umumiy `dist` va e2e bazasi bilan to'qnashadi; yetakchi yuritadi.
  UI ni ko'rib tekshirish kerak bo'lsa — alohida nusxada: `npx vite build --outDir dist_<nom> --emptyOutDir`, backend ni alohida portda
  (`MEBELIX_WEB_DIR=<...>\frontend\dist_<nom>`, `MEBELIX_DB_URL=sqlite:///./<nom>.db`, `python -m uvicorn app.main:app --port <8801+>`) ishga
  tushiring, Playwright (tizim Chrome: `C:\Program Files\Google\Chrome\Application\chrome.exe`, namuna skript:
  `scratchpad\mes_shots.cjs`) bilan skrinshot oling. Ish tugagach o'z jarayonlaringiz, `dist_<nom>` va `<nom>.db` ni o'chiring
  (`Move-Item` bilan chetga oling yoki Write/Edit; PowerShell himoyasi `Remove-Item` ni bo'sh joyli yo'lda to'sishi mumkin).
- Optimizator (`optimizer.py`, `colpack.py`) ga tegilsa: `tools/bench` benchmarklari (CLAUDE.md qoida 7, 13).

## Hisobot (oxirida, qisqa, o'zbekcha)
1. Nima qilindi (fayllar ro'yxati), nima qilinmadi va nega. 2. Testlar: nechta qo'shildi / hammasi o'tdimi (haqiqiy natija).
3. Foydalanuvchiga savollar (noaniq xulq-atvorlar). 4. Boshqa paketlarga ta'siri/ular uchun eslatmalar.
`docs/mebelix/R_GIBLAB_FEATURE_MATRIX.md` ga tegmang — yetakchi yangilaydi; paket hujjati kerak bo'lsa `docs/mebelix/T_<nom>.md` yarating.
