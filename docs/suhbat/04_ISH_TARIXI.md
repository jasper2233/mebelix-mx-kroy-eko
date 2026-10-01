# Ish tarixi (git commitlari bo'yicha)

Vaqtlar — UTC (Toshkent = UTC+5). Har commit — bitta bosqich; batafsil o'zgarishlar: `git show <hash>`.
Bu fayldan keyingi commitlar — `git log`.

### 2026-09-30 16:47 · 86ebd90

Boshlang'ich holat (zip)

### 2026-09-30 18:33 · 8e6460e

Optimizator: ko'p darajali gilyotina daraxti, pilot, kompozit polosa, 3 oila, dum ta'mirlash, validator, testlar


### 2026-09-30 19:07 · 2e96270

Backend: qoldiqlar ombori, sozlamalar profillari, postprotsessor shablonlari, etiketka QR, hisobot profillari, variantlar, qo'lda tahrir (daraxt amallari), .project import plagini, MES (buyurtma/eksport/skaner/webhook), JWT stub, SPA xizmati, 40 test


### 2026-09-30 19:47 · f54086d

Frontend: React 18 + TS + Vite, AG Grid, Zustand, TanStack Query, i18n (ru/uz); loyihalar, operatsiyalar, mahsulotlar, CS (parametrlar, detallar, listlar, kroy, tahrir, variantlar), EL, GR, XNC, hisobot, etiketkalar, sozlamalar, sex rejimi. Backend: xabarlar tarjimasi, avtomatik aylantirish, batch-update, o'lcham rejimi konversiyasi


### 2026-09-30 20:00 · 4277a10

E2E (Playwright), Docker (db+api+web), run.sh/run.bat/dev.sh, README; PostgreSQL mosligi (tarix FK tartibi), ro'yxat muharriri, Excel kabi Enter/Tab


### 2026-09-30 21:01 · 13d1160

Tekshiruv natijalari: hisobotda XSS yo'q (escape, CSP, sandbox), ombor yaxlitligi (undo/redo, import, nusxa, 409), kroy eskirishi (mahsulot soni, kromka), CORS standart o'chiq, loyiha raqami poygasi, shablon jarayonda chegaralar bilan, XNC muharriri, Del ro'yxatda, qoldiq listlar narxi/talabnoma, i18n, yorliqlar (Ctrl+P, ↑↓), 51 test + e2e


### 2026-09-30 21:26 · 3361a90

Optimizator: guruhlash (blok, guruh propili), oddiy polosalar, paketlar (Кратность/Высота пакета), «Большой пакет»; barcha oilalarda chuqurlik tekshiruvi; kichik detal va tor kromka ogohlantirishlari; 52 test, fuzz 320/0


### 2026-09-30 22:15 · 1bcbca8

Mustaqil tekshiruv natijalari: cheksiz/NaN qiymatlar loyihani buzmaydi (422, saqlashda 0, eski yozuv tuzatib ochiladi), soxta guruh tugunlari rad etiladi, qoldiq identifikatsiyasi (material/o'lcham), buzuq so'rovlar 4xx, guruh sig'masa yakka detallarga qaytish, shablon navbati va zip nomlari, paketlar qayta hisobi, EL birlashtirish/tur o'zgarishi, i18n qoldiqlari, postprotsessor «Новый» xatosi; 57 test


### 2026-09-30 22:16 · c21ca17

Frontend: kutubxonalar alohida fayllarda (kesh), 57 test + e2e


### 2026-09-30 22:18 · e28a0e0

README: benchmark oralig'i


### 2026-10-01 13:50 · 848cc1f

v2 backend: biznes qoidalari, optimizator (daraja = burilish, ustunli oila, BC/SVC, qoldiqni yig'ish), XNC, import

- N1 qoidalari: torsovka/«Минимальный отступ в конце», kromka (ish/material, yaxlitlash kodlari), taxminiy sarf,
  narx semantikasi (list / m²), listlarni yaxlitlash, МК (minus_qty), avtomatik kratnost, min. detal ogohlantirishi,
  mahsulot narxi 1 dona uchun; v1 JSON migratsiyalari (model_validator)
- Yangi detal: Ткт berilmasa — «Учет текстуры» (material teksturasi) bo'yicha
- Optimizator: kesim darajasi ≤ «Макс. количество вращений»; ustunli joylash (colpack, numpy ryukzak);
  bin completion + qiymat tuzatish (SVC); oxirgi va boshqa listlarda bo'sh joy bitta katta деловой qoldiqqa
  yig'iladi (polosa / burchak); qat'iy muddatlar; eski algoritmda min. polosa eni xatosi tuzatildi
- XNC: paz o'tishlari, yoy uzunligi, hisoblanmaydigan konturlar; .project importi (o'lcham rejimi, kodlar)
- Korpus (205 loyiha, 397 kroy): 1185 list (avvalgi dastur 1212), yomon 0, tekshiruv xatosi 0; 91 test


### 2026-10-01 13:50 · 6d757ac

v2 frontend: Space/Shift+Space, buferdan kromka, qoldiqlar jadvali, 12 ko'rsatkich, F2, masshtab, chop maydonlari

- Detallar: Space (Ткт / navbatdagi kromka), Shift+Space (perimetr), Ctrl+PgDn, Ctrl+V da noma'lum kromka nomi — yangi EL,
  yangi qatorda Ткт = «Учет текстуры», МК ustuni
- CS parametrlar: «Минимальный отступ в конце» oynasi, avtomatik kratnost, material sarfi
- Раскрой: 12 ko'rsatkich sozlamasi, F2 izoh, g'ildirak bilan masshtab, detalni bosish/ikki marta bosish, ogohlantirishlar
- Листы и остатки: kroydan keyingi qoldiq qatorlari; EL: yaxlitlash kodlari; chop: sahifa chegaralari, EL sarlavhalari
- e2e: v2 ssenariysi; kravat ssenariysida xodimlar odati (teksturani hammasidan olish)


### 2026-10-01 13:50 · ee377f0

Hujjatlar: v2 (docs/mebelix), CLAUDE.md doimiy qoidalari, korpus benchmarki va taqqoslash natijalari


### 2026-10-01 16:33 · 93883ea

VS Code + Claude Code paketi: suhbat arxivi, kontekst, ishga tushirish sozlamalari, korpus skriptlari

- docs/suhbat/: 01_KONTEKST (CLAUDE.md orqali har sessiyada yuklanadi), suhbat tarixi, texnik xulosa, ish tarixi,
  ilovalar (arxiv, git'ga kirmaydi)
- .vscode/: Run and Debug (Backend, Frontend, Full stack, pytest, korpus), vazifalar, tavsiya etilgan kengaytmalar
- dev.bat (Windows), .gitattributes (bat — CRLF, sh — LF); e2e serveri Windows/Linux/macOS'da bir xil ishlaydi
- tools/bench: corpus_build.py (korpusni .project fayllardan qayta qurish — natija aynan bir xil), el_check.py, xnc_check.py;
  projects/ — korxona fayllari (git'ga kirmaydi)


### 2026-10-01 16:33 · 082a794

Docker kontekstiga korxona fayllari va arxiv kirmaydi


### 2026-10-01 17:13 · 9217abe

Optimizator: list tejash qidiruvi yechimga juda yaqin bo'lsa bir marta uzaytiriladi (jami ≤ 17 s); hujjatlarda takroriy o'lchovlar

- SVC: eng yaqin urinish (target − 1 listdan ortgan maydon) kuzatiladi; ≤ 6 % list bo'lsa, keyingi iteratsiya muddatga
  sig'maydigan paytda bir marta uzaytiriladi; muddat bilan uzilgan iteratsiya vaznlarga ta'sir qilmaydi
- TOTAL_CAP: standart rejimda kroy jami ≤ 17 s (spetsifikatsiya 20 s), tez rejimda ≤ 4 s
- Korpus (4 o'lchov): 1185–1189 list (avvalgi 1212), chegaraviy kroylar ±1; test vaqt chegarasi 20 s


### 2026-10-01 17:13 · 0b6d960

Hujjat: yakuniy o'lchov aniqlashtirildi


### 2026-10-01 17:13 · eb17c4e

Hujjat: yakuniy kod natijalari jadvalda
