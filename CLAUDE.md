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

   **Istisno (foydalanuvchi ruxsati, 2026-10-02):** foydalanuvchining o'z tayyor fayllarini import/eksport qilish (`.project` eksporti — GibLabning
   ochiq tavsiflangan formati; etiketka shablonlari/`program` importi va eksporti). GibLabning o'z namuna shablonlari, rasmlari, matnlari
   va ikkilik fayllari (`.gibcut`) bizning kod/test/repoga kiritilmaydi; GibLab dasturi, kaliti va litsenziyasiga baribir tegilmaydi.
   Maqsad — tizim ommabop bo'lishi (mijoz ixtiyori).

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
12. Jonli GibLab oynasida «Раскроить», «Удаление раскроя», list tartibini o'zgartirish kabi amallar loyihani **avtomatik
    diskka saqlaydi** — haqiqiy `.project` fayllarida (Yandex.Disk papkasi) tajriba o'tkazmang; avval nusxa oling,
    keyin faqat ko'rish dialoglarini oching (batafsil: `docs/suhbat/01_KONTEKST.md` «Texnik eslatmalar»).
13. Optimizatorda list tartibi muhim: `Operation.sheets` = kroy ustuvorligi (soni bo'yicha o'sish; `10000` — cheksiz);
    ko'p-listli o'zgarishdan keyin `cd tools/bench && python compare_stock.py normal` ham ishlating.

14. Ifodalar (XNC parametrlari, etiketka maydonlari, hisoblanadigan ustunlar) — faqat `backend/app/services/expr.py` da hisoblanadi;
    ikkinchi dvigatel (JS yoki Python `eval/ast`) yozilmaydi. MES integratsiyasi va stanok formatlari (postprotsessor mantig'i) — korxona
    dasturchilariniki: bizda faqat toza ma'lumot konteksti, stanok nomlari ro'yxati va shablon ulash.
    **Yangilanish (foydalanuvchi qarori, 2026-10-04):** stanok formatlari korxonaning o'z namuna fayllaridan
    (`post prtsessorlar/` — o'z stanoklari uchun chiqarilgan fayllar) o'rganilib, **o'rnatilgan generatorlar** sifatida qo'shiladi:
    `backend/app/services/ppfmt/` (tavsiflar — `docs/mebelix/postprocessors/`). Shablon biriktirilgan bo'lsa — shablon ustun.
    GibLab'ning o'z ichki ma'lumotlari (`GibLabData.xml`, etiketka bloblari, `GibLabPart` va h.k.) nusxalanmaydi; fayllarda
    «GibLab» so'zi yozilmaydi.
15. Parallel agentlar uchun qoidalar: `docs/mebelix/S_ISH_QOIDALARI.md` (umumiy fayllarga kichik aniq Edit, i18n `scripts/i18n_<nom>.py`).
16. MCP serveri — `mcp/` (TypeScript, `npm run build` → `dist/`, `.mcp.json`): `mx_*` REST vositalari, `compare_project` (fayl bilan),
    `giblab_*` (onlayn tizim brauzer orqali — faqat o'qish; yozuvchi amallar `GIBLAB_ALLOW_WRITE=1` + `GIBLAB_WORK_FOLDER="test uchun"` bilan,
    haqiqiy loyihalarda hech qachon). Onlayn solishtiruv va ko'p-kroyli audit natijalari — `docs/mebelix/X_1015_ONLAYN_AUDIT_MCP.md`.

## Ochiq savollar (foydalanuvchidan so'raladi, taxmin qilinmaydi)
- Kromka qalinligi (PVC 1 mm) korxona loyihalarida 0 — shunday qolsinmi?
- Arra stanogi modeli va postprotsessor formati (namuna fayl) — format foydalanuvchidan keladi.
- MES API manzillari, autentifikatsiya, webhook formati.
- Etiketka printeri va o'lchami.
