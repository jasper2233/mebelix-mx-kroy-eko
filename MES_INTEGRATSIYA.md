# MebeliX Kroy → MES: loyiha haqida va integratsiya yo'riqnomasi

> Sana: 2026-10-25 · Kimga: MES tizimi dasturchilari · Holat: MX tayyor va xodimlar serverida ishlayapti, MES tomoni ulanmagan.
> Batafsil shartnomalar `docs/mebelix/` papkasida. Bu fayl — umumiy kirish nuqtasi.

## 1. MebeliX Kroy (MX) nima

- Korxonaning **o'z listli kroy (raskroy) dasturi**: LDSP, MDF, XDF, akril listlarini kesish kartalarini quradi.
- Xodimlar avval ishlatgan kroy dasturi bilan **bir xil ish oqimi** (joylashuv, ustunlar, tugmalar, klaviatura). Kod noldan yozilgan.
- Kroy natijasi avvalgi dasturdan **yaxshi bo'lishi shart**: 205 ta real loyiha korpusida listlar soni kam yoki teng, деловой qoldiq ko'p
  (natijalar `docs/mebelix/P_TAQQOSLASH.md`).
- **Maqsad:** MX MES tizimining **kroy moduli** bo'ladi. Buyurtma, ombor, moliya, sex postlari — MES da; MX faqat o'z vazifasini
  bajaradi: detallar → kroy → kartalar, stanok fayllari, etiketkalar, qoldiq qoidalari.

### Asosiy imkoniyatlar

| Bo'lim | Nima qiladi |
|---|---|
| Operatsiyalar | CS (listli kroy), CL (chiziqli), EL (kromka), XNC (CNC ishlov), GR (guruh), O, SP, LB (etiketka), CN (nesting) |
| Optimizator | gilyotina kesish daraxti, bir nechta list o'lchami va qoldiqlar, burilishlar soni, propil, obrezka; har natija tekshiriladi (`services/validate.py`) |
| Qoldiqlar | ombordagi qoldiqni taklif qilish, «Детали на остаток», kroydan keyingi qoldiqni foiz qoidasi bilan omborga / mijozga |
| Import / eksport | `.project` (Bazis-Mebelshik va oldingi dastur), Excel; `.project` eksportida kroy kartalari bloki — MES fayl o'quvchisi qabul qiladi |
| Postprotsessorlar | 43+ stanok formati (arra va prisadka/CNC), korxona namunalari bilan bayt-ma-bayt tekshirilgan (`docs/mebelix/postprocessors/`) |
| Hisobot / etiketka | A4 PDF hisobot, kroy kartalari, QR etiketkalar (detal, qoldiq, karta), ZPL |
| XNC | dastur muharriri, chizma, cheklovlar, shablonlar; asbob bo'yicha ish hisobi (teshik / metr) — MES moliyasi uchun |
| Ko'p korxona | PostgreSQL + RLS (`company_id`), JWT, rollar, hisob ishchilari navbati |

## 2. Texnik tuzilma

```
Brauzer (React 18 + TypeScript + AG Grid, Vite)        frontend/
        │  REST /api/*  (JSON, JWT Bearer)
FastAPI (uvicorn, 4 jarayon)                           backend/app/main.py, api_*.py
        │  vazifalar navbati (kroy, PDF, nesting)
Hisob ishchilari (app/worker.py, 6 ta)                 backend/app/worker.py
        │
PostgreSQL (prod) / SQLite (test, dev)                 backend/app/db.py
        │
MES  ◀── webhook (MES_WEBHOOK_URL) / MES API (MES_API_*) ──▶  services/mes_*.py, remnant_store.py, remnant_outbox.py
```

- Python 3.11+ (FastAPI, SQLAlchemy 2, psycopg 3, numpy), Node 20+.
- Ishga tushirish: `README.md` (Docker: `docker compose up -d --build`; Windows: `run.bat`).
- API hujjati (Swagger): `http://<server>:8000/docs`.
- MCP serveri (`mcp/`): MX ni AI agentlar orqali boshqarish uchun (`mx_*` vositalari).

### Muhit o'zgaruvchilari (integratsiyaga oid)

Maxfiy qiymatlar repoda **yo'q** — serverda o'rnatiladi.

| O'zgaruvchi | Ma'nosi |
|---|---|
| `MEBELIX_DB_URL` | baza (`postgresql+psycopg://…`) |
| `MEBELIX_JWT_SECRET` yoki `MEBELIX_JWT_PUBLIC_KEY`, `MEBELIX_JWT_AUDIENCE` | MES SSO tokenini tekshirish (HS yoki RS kalit) |
| `MEBELIX_AUTH_REQUIRED` | `1` — har so'rovda token shart |
| `MES_WEBHOOK_URL`, `MES_WEBHOOK_TOKEN`, `MES_WEBHOOK_RETRIES`, `MES_WEBHOOK_TIMEOUT` | MX → MES voqealari |
| `MES_API_TOKEN`, `MES_API_TIMEOUT` | MX → MES API so'rovlari (qoldiq ombori) |
| `MEBELIX_WORKERS`, `MEBELIX_COMPUTE` | jarayonlar va hisob ishchilari |

## 3. MX ↔ MES ma'lumot oqimlari

### 3.1 Umumiy rasm

```
MES buyurtma ──▶ MX loyiha (mes_order_ref)
                   │ detallar (.project / Excel / qo'lda)
                   ▼
                 kroy (CS, CL, EL, XNC …)
                   │
                   ├─▶ MES paketi v1  (detallar, nusxalar QR, kartalar, qoldiqlar, sarf, XNC, stanok fayllari)
                   ├─▶ xnc_tools      (asbob bo'yicha ish → MES moliya)
                   ├─▶ remnant.move   (qoldiq kirim / chiqim / band → MES ombor)
                   └─▶ project.status (Заказан / Утвержден / Готов)
Sex: karta QR skaneri ──▶ MX  map.done  ──▶ qoldiq «mavjud»
```

### 3.2 Endpointlar (MX tomonida tayyor)

| Yo'nalish | Endpoint | Hujjat |
|---|---|---|
| MES → MX | `POST /api/catalog/sync` — materiallar katalogi (upsert) | `docs/mebelix/I_MES_INTEGRATION.md` §I1 |
| MES → MX | `POST /api/mes/orders`, `GET /api/mes/orders/{ref}` — buyurtmadan loyiha | I §I3 |
| MX → MES | `GET /api/projects/{pid}/mes-package?version=1` — tayyor kroy paketi (yubormaydi, faqat quradi) | `docs/mebelix/MES_PAKET_V1.md` |
| MX → MES | `GET /api/mes-package/schema` — paketning JSON sxemasi | MES_PAKET_V1 §6 |
| MX → MES | `GET /api/projects/{pid}/mes-export` — eski eksport formati | — |
| MX → MES | `GET /api/projects/{pid}/xnc-tools` — XNC ishi asbob bo'yicha (+ `mes` — aynan yuboriladigan ko'rinish) | MES_PAKET_V1 §4.10b |
| MX → MES | `GET /api/xnc-mes/tools` — korxona asboblari ro'yxati va MES kodlari | §4 pastda |
| MES → MX | `GET /api/mes/scan/{kod}`, `POST /api/mes/scan/{kod}/done?count=1` — karta QR skaneri, «list arradan chiqdi» | `docs/mebelix/MES_QOLDIQ_V1.md` |
| MES → MX | `GET /api/mes/remnants?since_id=N`, `POST /api/mes/remnants/resend` — qoldiq jurnali va qayta yuborish | MES_QOLDIQ_V1 |
| MES → MX | `POST /api/projects/{pid}/order`, `PATCH /api/projects/{pid}` `{"status": n}` — buyurtma holati | I §I3 |
| MES → MX | `GET /api/queue`, `GET /api/projects/{pid}/material-check` — navbat, material yetarlimi | — |
| test | `POST /api/mes/webhook-test` — webhook ulanishini sinash | — |

### 3.3 Webhook voqealari (MX → `MES_WEBHOOK_URL`)

| Voqea | Qachon | Tana |
|---|---|---|
| `project.status` | loyiha holati o'zgardi (buyurtma berildi va h.k.) | `{event, company_id, project: {...}}` |
| `remnant.move` | qoldiq harakati: `kutish`, `kirim`, `chiqim`, `qaytish`, `bekor`, `rezerv`, `rezerv_bekor`, `mijozga`, `qolda` | `{event, company_id, move, remnant}` |
| `map.done` | karta (list) arradan chiqdi | karta va loyiha ma'lumoti |
| `test` | sinov | — |

Voqealar navbatda saqlanadi (`services/remnant_outbox.py`) — MES javob bermasa yo'qolmaydi, tartib bilan qayta yuboriladi.

## 4. MES dasturchilari qiladigan ishlar

1. **Kirish (SSO).** MES foydalanuvchisi MX ga MES tokeni bilan kiradi: MX `MEBELIX_JWT_PUBLIC_KEY` (yoki umumiy sir) bilan
   tekshiradi. Kerakli claim'lar: foydalanuvchi, `company_id`, rol (kroychi / texnolog / ko'ruvchi). Taklif —
   `MES_PAKET_V1.md` §7.3.
2. **Joylashtirish.** MX alohida servis (konteyner) — MES reverse-proxy ostida, masalan `/kroy/` → MX `:8000`.
   Baza: alohida PostgreSQL sxemasi yoki baza (MX o'z jadvallarini o'zi yaratadi).
3. **Buyurtma → loyiha.** MES buyurtmasidan MX loyihasini yaratish (`POST /api/mes/orders`), `mes_order_ref` bilan bog'lash;
   MES sahifasidan «Kroy» tugmasi MX dagi loyihani ochadi (`/#/p/{pid}`).
4. **Kroy paketini qabul qilish (ingest).** `POST {MES}/api/v1/orders/{id}/kroy-package` — MX paketini MES tuzilmalariga
   yozish (detal, nusxa QR, karta, qoldiq, sarf, stanok fayllari). Bo'limlar va MES jadvallari mosligi — `MES_PAKET_V1.md` §1.
   MX dagi «MES» tugmasi shu endpoint tayyor bo'lgach yoqiladi.
5. **Qoldiq ombori API.** Ombor ustasi — MES bazasi. MX so'raydigan endpointlar: `/remnants` (qidirish), `/remnants/reservations`
   (band), `/remnants/intake` (kroydan keyingi kirim/chiqim), `/intake/{id}/cancel`. Shartnoma — `MES_QOLDIQ_V1.md`.
   Tayyor bo'lgach MX da: «Настройки → Правила остатков → Источник склада → База MES» va manzil.
6. **XNC ishi → moliya.** Paketdagi `xnc_tools`: har asbob bo'yicha teshiklar soni (parma), metr (freza, o'tishlar bilan), arra
   pazi metri. Narx MES da asbobning **MES kodi** bo'yicha qo'yiladi (kod MX da «Настройки → MES интеграция → XNC → MES»
   jadvalida beriladi). Jadvalda faqat korxona ishlatadigan asboblar (loyihalardan yig'ilgan, 33 ta). `known: false` — ro'yxatda
   yo'q yoki o'chirilgan asbob: narx qo'yilmaydi, texnologga ko'rsatiladi (`warnings[]`).
7. **Sex skanerlari.** Karta QR kodi skanerlanganda `POST /api/mes/scan/{kod}/done` — MX qoldiqni «mavjud» qiladi va `map.done`
   yuboradi.
8. **Katalog.** MES materiallari (kod, o'lcham, qalinlik, narx, tekstura) `POST /api/catalog/sync` bilan MX ga — hali ishlatilmagan.

## 5. Biznes qoidalari (korxona egasining qarorlari)

- Kroy ustuvorligi: **eng kam list / material** birinchi, деловой qoldiq undan keyin.
- Kesish doim butun listlardan boshlanadi; ombordagi qoldiq faqat material kamaysa taklif qilinadi (belgi «Использовать остатки со склада»).
- Qoldiq omborga qoladimi — faqat **foiz** hal qiladi: qoldiq maydoni / butun list maydoni ≥ material turi (yoki aniq material) foizi.
  Kichigi mijozga beriladi.
- Qoldiq faqat list arradan chiqqach (MES signali) mavjud bo'ladi. Qoldiq butunligicha sotiladi:
  narx = qoldiq m² / list m² × list narxi; mijozdan olib qolish narxi — MES da.
- Qoldiq faqat aniq material kodi bo'yicha (kod bo'lmasa — nom; katta-kichik harf va bo'shliqlar e'tiborsiz).
- Stanok fayli aynan o'sha stanok o'qiydigan bo'lishi shart; korxona namunasi onlayn namunadan ustun.
- MES ishlov bosqichi faqat paketda tegishli stanok fayli kelgan bo'lsa ochiladi.

## 6. Hujjatlar xaritasi

| Fayl | Mazmuni |
|---|---|
| `docs/mebelix/MES_PAKET_V1.md` | MES paketi shartnomasi, JSON sxema, sintetik misol, ochiq savollar |
| `docs/mebelix/MES_QOLDIQ_V1.md` | qoldiqlar ombori shartnomasi (MX → MES API, voqealar) |
| `docs/mebelix/I_MES_INTEGRATION.md` | katalog, buyurtma holatlari, auth, chiqish fayllari |
| `docs/mebelix/Y_MASSHTAB_ABONENTLAR.md` | ko'p korxonali tuzilma (PostgreSQL, RLS, ishchilar) |
| `docs/mebelix/B_DOMAIN_RULES.md`, `C_CS_OPTIMIZER_SPEC.md` | biznes qoidalari, optimizator |
| `docs/mebelix/postprocessors/` | stanok formatlari, solishtiruvlar |
| `docs/suhbat/01_KONTEKST.md` | loyiha tarixi va joriy holat |

## 7. Holat va ochiq ishlar

- **Tayyor:** kroy, qoldiq qoidalari va lokal ombor, MES paketi quruvchi, XNC → MES, webhooklar, skaner endpointlari, ko'p korxona.
  Testlar: backend 2475, brauzer (e2e) 71.
- **MES tomonida kerak:** paketni qabul qilish, qoldiq ombori API, SSO tokeni, `xnc_tools` ni moliyada o'qish, katalog sinxroni.
- **Kelishiladigan savollar:** `MES_PAKET_V1.md` §8 (transport, fayllar hajmi, qayta yuborish, rollar).

## 8. Muhim eslatmalar

- Repo **yopiq** saqlansin: `tools/bench/corpus.json` va testlarda korxona loyihalaridan olingan nomlar bor.
- Maxfiy qiymatlar (baza paroli, JWT siri) repoga kiritilmaydi — faqat server muhitida.
- Mijoz fayllari (`tools/bench/projects/`, `docs/suhbat/ilovalar/`) git'ga kirmaydi.
