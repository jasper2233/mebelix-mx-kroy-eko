# Suhbat arxivi va VS Code + Claude Code'da davom ettirish

| Fayl | Mazmuni |
|---|---|
| `01_KONTEKST.md` | Loyiha konteksti: maqsad, qat'iy cheklovlar, tarix, holat, buyruqlar, tuzoqlar, keyingi ishlar. `CLAUDE.md` orqali **har sessiyada avtomatik** yuklanadi |
| `02_SUHBAT_TARIXI.md` | Suhbat xronologiyasi: foydalanuvchi xabarlari aynan, javoblar (saqlangani aynan, qolgani qisqa) |
| `03_TEXNIK_XULOSA_EN.md` | 2026-10-01 dagi batafsil texnik xulosa (inglizcha): qoidalar, formulalar, fayllar, xatolar va yechimlar |
| `04_ISH_TARIXI.md` | Git commitlari bo'yicha ish tarixi (har bosqichda nima qilingan) |
| `ilovalar/` | Suhbatga yuborilgan fayllar (v1/v2 paketlar, eski HTML prototiplar) — arxiv |

## VS Code'da Claude Code bilan ishlash

1. Kerak: VS Code 1.94+, Python 3.11+, Node.js 20+, Git. Windows'da birinchi ishga tushirish — `run.bat`
   (virtual muhit `.venv` va kutubxonalar o'rnatiladi, dastur http://localhost:8000 da ochiladi).
2. Claude Code kengaytmasi: VS Code'da `Ctrl+Shift+X` → «Claude Code» (Anthropic) → **Install**; birinchi ochishda
   Claude hisobingiz bilan kiring (Pro, Max, Team yoki Enterprise obunasi). Rasmiy qo'llanma:
   https://code.claude.com/docs/en/vs-code
3. `File → Open Folder…` → `MebeliX_Kroy` papkasi. Tavsiya etilgan kengaytmalar (`.vscode/extensions.json`) taklif qilinadi.
4. Claude Code panelini oching (muharrir o'ng yuqorisidagi Spark belgisi yoki `Ctrl+Esc`). Loyiha ildizidagi `CLAUDE.md`
   va u ulagan `docs/suhbat/01_KONTEKST.md` avtomatik o'qiladi — tekshirish: `/context` → «Memory files».
5. Birinchi so'rov uchun namuna:
   «`docs/suhbat/02_SUHBAT_TARIXI.md` ni o'qib chiq, backend testlarini ishga tushir va holatni qisqa ayt. Keyin
   ochiq savollar bo'yicha davom etamiz.»

Ishga tushirish va tekshirish (VS Code ichida): `Run and Debug` → «Backend (FastAPI)», «Frontend (Vite)» yoki
«Full stack»; `Terminal → Run Task…` → «pytest: backend», «frontend: build», «e2e: Playwright», «bench: compare normal»,
«i18n: generate».
