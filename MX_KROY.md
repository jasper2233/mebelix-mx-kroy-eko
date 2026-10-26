# MebeliX Kroy (MX) — loyiha haqida to'liq ma'lumot

> Sana: 2026-10-26 · Til: o'zbekcha · Batafsil texnik hujjatlar: `docs/mebelix/`, loyiha tarixi: `docs/suhbat/01_KONTEKST.md`,
> MES ga ulash: [`MES_INTEGRATSIYA.md`](MES_INTEGRATSIYA.md).

## 1. Nima bu

**MebeliX Kroy** — mebel korxonasining o'z listli kroy (raskroy) dasturi. LDSP, MDF, XDF, akril va boshqa listli materiallardan
detallarni kesish kartalarini tuzadi, kromka, CNC (XNC) ishlovi, narx, hisobot, etiketka va stanok fayllarini tayyorlaydi.

- Xodimlar avval onlayn kroy tizimida ishlagan — MX **xuddi shu ish oqimi** bilan (joylashuv, ustunlar, tugmalar, klaviatura)
  quriladi, shuning uchun qayta o'rganish shart emas.
- Kroy natijasi avvalgi tizimdan **yaxshiroq** bo'lishi shart (kam list, ko'proq foydali qoldiq).
- Kod noldan yozilgan; boshqa dasturlarning kodi, ikonkasi, matni yoki litsenziyasiga tegilmaydi.
- Maqsad: MX korxonaning **MES tizimining kroy moduli** bo'ladi (buyurtma, ombor, moliya — MES da; kroy — MX da).

## 2. Asosiy qoidalar (korxona egasining qarorlari)

| Qoida | Ma'nosi |
|---|---|
| Sifat birinchi | Kroy aniq, detallar listga zich joylashadi, arrada (pilniy markazda) kesish qulay va oson bo'ladi |
| Eng kam material | Har doim eng kam list / material; деловой qoldiq — undan keyin. Paket (kratnost) uchun ortiqcha list sarflanmaydi |
| Butun listdan boshlash | Kesish butun listlardan boshlanadi; ombordagi qoldiq faqat materialni tejasa taklif qilinadi |
| Foydalanuvchi tanlovi | Xodim sozlamani o'zgartirsa — bu uning tanlovi, eslab qolinadi (keyingi loyihalarda ham), o'zi o'zgartirmaguncha |
| «По умолчанию» | Tugma operatsiyani MX tavsiya qilgan parametrlarga qaytaradi (sifat, zichlik, qulay kesish) |
| Onlayn tizim bilan bir xil | Har tugma, maydon va amal xodimlar o'rgangan tizimdagidek; har raqam haqiqiy ta'sir qiladi |
| Ma'lumot xavfsizligi | Har o'zgarishdan oldin baza zaxirasi; mijoz ma'lumotlari hech qachon o'chmaydi |

## 3. Imkoniyatlar

### 3.1 Loyiha va operatsiyalar
- Loyihalar papkalarda, raqam (Заказ ID), holat (Не заказан → Заказан → Утвержден → Готов), tarix (Отменить / Вернуть).
- Operatsiyalar:

| Kod | Operatsiya | Asosiy vazifa |
|---|---|---|
| CS | Listli kroy | Detallar, listlar va qoldiqlar, kesish kartalari, kroy tahriri |
| CL | Chiziqli (pogonaj) kroy | Profil / polosalarni kesish |
| CN | Nesting | Egri konturli detallarni joylash (CNC) |
| EL | Kromka | Kromka metri (ish va material), narx, belgi / rang |
| XNC | CNC ishlov | Teshik, freza, arra pazi dasturi, chizma, stanok fayli |
| GR | Pazlash | Paz uzunligi, o'tishlar, narx |
| SP | Sirt ishlovi | Plenka / bo'yoq maydoni |
| O | Komplektatsiya | Furnitura va boshqa materiallar |
| LB | Etiketkalar | Detal va qoldiq etiketkalari (QR), ZPL |

### 3.2 Kroy (optimizator)
- Gilyotina kesish daraxti: kesim darajasi = burilish raqami («Макс. количество вращений»), propil, torsovka, min. obrezka.
- Bir nechta list o'lchami, soni cheklangan listlar va qoldiqlar; ro'yxat tartibi yoki eng tejamkor tartib.
- «Быстро / Стандарт / Максимум» sifat rejimlari, vaqt chegarasi bilan.
- Деловой qoldiq — iloji boricha bitta katta bo'lak, oxirgi listda; oldingi listlar maksimal zich.
- Har natija tekshiriladi (`services/validate.py`): chegaradan chiqish, ustma-ust tushish, propil, daraja, tekstura, soni.
- Kroy tahriri: detal / polosani ko'chirish, o'chirish, aylantirish, «Развернуть резы», «До кроить» (bo'sh joylarga), sichqoncha
  va klaviatura kombinatsiyalari onlayn tizim yordamidagidek.
- Natija (205 real loyiha, 397 kroy): **1191 list, avvalgi tizim 1212**; tekshiruv xatosi 0.

### 3.3 Sozlamalar va ularning ta'siri (2026-10-26 audit)
Har parametr kroyga haqiqatan ta'sir qiladi (MX da va onlayn tizimda jonli tekshirildi):

| Parametr | Ta'siri |
|---|---|
| Торцовка по длине / ширине | List chetidan qirqim; 2 → 10 mm: birinchi detal (5,5) → (13,13) |
| Толщина пилы | Detallar orasidagi propil; 3 → 5: joylashuv o'zgaradi |
| Минимальная обрезка | Ichki tor qirindi ruxsat etilmaydi; kesish uzunligi va joylashuv o'zgaradi |
| Макс. количество вращений | Kesim darajasi; kam bo'lsa arra uchun oddiyroq, lekin zichlik pasayishi mumkin |
| Мин./макс. ширина полосы, макс. длина полосы | Barcha qidiruv yo'llarida qat'iy bajariladi |
| Мин. размер остатка (2 tomon), площадь делового остатка, с учетом торцовки | Qaysi bo'lak деловой qoldiq hisoblanadi |
| Минимальный размер детали | Undan kichik detal bo'lsa kroy **bajarilmaydi**: «Размер детали N… меньше ограничения …» |
| Начальное направление резов (предпочтительно) | To'ldirilishi past kartalarda birinchi kesim yo'nalishi majburiy |
| Высота пакета → Кратность | Paketlar soni; teng variantlar ichidan paketi kami tanlanadi (ortiqcha list yo'q) |
| Расчетный процент заполнения, округление листов, цена | Faqat narx / taxminiy sarf (kroy joylashuviga emas) |
| EL: Длина остатка по краям, мин. оклеиваемая длина, процент отхода, округление | Kromka material metri va narxi |
| EL: мин. размер стороны | Tor detal ogohlantirishi |

Sozlama saqlanishi: qiymat Enter bilan ham, boshqa maydonni bosganda ham saqlanadi. CS va EL da qo'yilgan ish parametrlari korxona
standartiga aylanadi — keyingi import va yangi operatsiyalar shu qiymatlar bilan keladi (qalinlik, list narxi, kromka eni,
tekstura — materialga xos, eslab qolinmaydi).

**«По умолчанию» (MX tavsiyasi):** торцовка 2/2, пила 3, вращений 4, мин. обрезка 5, полосы сложные, сортировка по убыванию,
высота пакета 40, qoldiq 1000 / 500 / 0.5 m², мин. детал 30; EL — qoldiq 30, мин. длина 100, мин. сторона 40.

### 3.4 Qoldiqlar ombori
- Qoldiq omborga qoladimi — **foiz** hal qiladi (qoldiq maydoni / butun list maydoni), material turi yoki aniq material bo'yicha.
  Kichik bo'lak mijozga beriladi.
- Qoldiq list arradan chiqqach (MES signali) «mavjud» bo'ladi; sotish narxi = qoldiq m² / list m² × list narxi.
- «Остатки: расход / приход» varaqlari, «Детали на остаток» (qaysi detallar qoldiqdan kesilishini tanlash, «Авто»),
  ombordan mos qoldiq taklifi (material tejasa).
- Ombor ustasi — MES bazasi (MX lokal ombor bilan ham ishlay oladi).

### 3.5 Kromka, XNC, hisobot, etiketka
- EL: ish va material metri, minimal uzunlik, qo'shimcha, chiqindi foizi, yaxlitlash, tor detal ogohlantirishi.
- XNC: dastur muharriri (teshik, freza, paz, shablonlar, ko'zgu, aylantirish), chizma va «Чертеж» varag'i, cheklovlar (Строго),
  kodlash, asbob bo'yicha ish hisobi (teshik / metr) → MES moliya.
- Hisobot: A4 PDF, kroy kartalari, materiallar, kromka, qoldiqlar.
- Etiketka: vizual redaktor, QR, ZPL.

### 3.6 Import / eksport va stanoklar
- `.project` (Bazis-Mebelshik va avvalgi tizim) importi, Excel importi; `.project` eksporti (kroy kartalari bloki bilan — MES o'qiydi).
- **43+ o'rnatilgan stanok formati** (arra va prisadka / CNC): korxonaning o'z namuna fayllari bilan bayt-ma-bayt tekshirilgan
  (`docs/mebelix/postprocessors/`). Stanok fayli aynan o'sha stanok o'qiydigan bo'lishi shart.
- **KDT (korxona stanoklari):** pilniy markaz `KDT (XML)` va prisadka `KDT (KDTPanelFormat)` — stanokda hozir ishlayotgan
  fayllar bilan solishtirilgan (prisadka 680 dan 629 bayt-ma-bayt, qolgani faqat asbob yo'li tartibi; arra mantiqan bir xil).
  Arra etiketkasidagi QR — detalning prisadka dasturi nomi (stanok shu bilan dasturni ochadi).
  Batafsil: `docs/mebelix/postprocessors/kdt-joriy-versiya.md`.

## 4. Texnik tuzilma

```
Brauzer (React 18 + TypeScript + AG Grid, Vite)            frontend/
   │  REST /api/*  (JSON, JWT)
FastAPI (uvicorn, 4 jarayon)                               backend/app/
   │  hisob navbati (kroy, PDF, nesting)
Hisob ishchilari (6 ta)                                    backend/app/worker.py
   │
PostgreSQL (ish) / SQLite (test)                           backend/app/db.py
   │
MES  ◀── webhook / API ──▶  MX                             services/mes*.py, remnant_store.py
```

| Papka / fayl | Vazifa |
|---|---|
| `backend/app/main.py`, `api_*.py` | REST API |
| `backend/app/models.py` | Ma'lumot modellari |
| `backend/app/services/optimizer.py`, `colpack.py` | Kroy optimizatori |
| `backend/app/services/validate.py` | Natijani tekshirish |
| `backend/app/services/calc.py`, `sizes.py` | Narx, kromka, o'lchamlar |
| `backend/app/services/recommended.py` | «По умолчанию» tavsiya qilingan parametrlar |
| `backend/app/plugins/legacy_project.py` | `.project` importi |
| `backend/app/services/ppfmt/` | Stanok formatlari |
| `frontend/src/features/` | Interfeys bo'limlari (cs, el, xnc, settings …) |
| `mcp/` | AI agentlar uchun MCP serveri |
| `tools/bench/` | Korpus solishtiruvi (korxona fayllari repoga kirmaydi) |

## 5. Ishga tushirish va tekshirish

- Docker: `docker compose up -d --build` → http://localhost:8080; Windows: `run.bat` → http://localhost:8000; API: `/docs`.
- Backend testlari: `cd backend && pytest -q` (~2480 test). Brauzer testlari: `cd frontend && npm run e2e` (~74 test).
- Korpus: `cd tools/bench && python compare.py normal` — listlar soni ko'paymasin, tekshiruv xatosi 0.
- Frontend o'zgarsa: `npm run build`.

## 6. Xavfsizlik va ma'lumot

- Har o'zgarishdan oldin baza zaxirasi (`tools/backup_db.py`), eski zaxiralar saqlanadi.
- Maxfiy qiymatlar (baza paroli, JWT siri) repoda yo'q — faqat server muhitida.
- Repo **yopiq**: korpus va testlarda korxona loyihalaridan nomlar bor; mijoz fayllari git'ga kirmaydi.
- Ko'p korxona: PostgreSQL + RLS (`company_id`), rollar.

## 7. Holat va keyingi ishlar

- **Tayyor:** kroy (avvalgi tizimdan yaxshi), barcha operatsiyalar, qoldiq qoidalari, XNC → MES, stanok formatlari, MES paketi,
  sozlamalar auditi va «По умолчанию».
- **MES tomonida:** paketni qabul qilish, qoldiq ombori API, SSO, `xnc_tools` ni moliyada o'qish ([`MES_INTEGRATSIYA.md`](MES_INTEGRATSIYA.md)).
- **Ochiq:** ba'zi stanoklar uchun namuna fayllar (Vitap, FastPanel, IMA …), 2 ta murakkab kroyda zichroq joylash, etiketka
  redaktori auditi.
