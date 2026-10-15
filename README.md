# MebeliX Kroy

Listli materiallarni (LDSP, MDF, XDF) kesish — **kroy** dasturi. Korxona MES tizimiga ulanadi,
xodimlar uchun tanish ish oqimi (joylashuv, ustunlar, tugmalar, klaviatura yorliqlari) bilan.
Kod noldan yozilgan; ikonkalar — Lucide (ochiq litsenziya), jadvallar — AG Grid Community.

## Ishga tushirish

| Usul | Buyruq | Manzil |
|---|---|---|
| Docker (PostgreSQL + api + web) | `docker compose up -d --build` | http://localhost:8080 |
| Windows, Docker'siz | `run.bat` | http://localhost:8000 |
| Linux/macOS, Docker'siz | `./run.sh` | http://localhost:8000 |
| Ishlab chiquvchi | `dev.bat` (Windows) / `./dev.sh` (backend :8000 + Vite :5173) | http://localhost:5173 |

`run.*` birinchi marta virtual muhit yaratadi, kutubxonalarni o'rnatadi va frontendni yig'adi
(Python 3.11+, Node.js 20+ kerak). Ma'lumotlar bazasi — standart SQLite (`backend/mebelix_kroy.db`),
prod uchun PostgreSQL: `MEBELIX_DB_URL=postgresql+psycopg://user:parol@host/mebelix`.
API hujjati (Swagger): `/docs`.

## VS Code va Claude Code

Papkani VS Code'da oching (`File → Open Folder…`), tavsiya etilgan kengaytmalarni o'rnating (Claude Code, Python,
Playwright). Claude Code loyiha ildizidagi `CLAUDE.md` ni va u ulagan `docs/suhbat/01_KONTEKST.md` ni (maqsad, cheklovlar,
holat, keyingi ishlar) avtomatik o'qiydi; suhbat tarixi va ilovalar — `docs/suhbat/`. `Run and Debug`: «Backend (FastAPI)»,
«Frontend (Vite)», «Full stack»; `Run Task…`: testlar, build, e2e, i18n, korpus. Batafsil: `docs/suhbat/README.md`.

## Nima bor

**Loyihalar** — papkalar, qidiruv (nomi, raqami, buyurtmachi, MES raqami), ko'chirish, nusxa, holat
(Не заказан / Заказан / Утвержден / Готов), undo/redo (Ctrl+Z / Ctrl+Y) — server tarixida.

**Operatsiyalar** — (CS) listli kroy, (EL) kromka, (GR) pazlash, (XNC) CNC ishlov; katalogdan qo'shish,
«Общие действия» (bir xillarini birlashtirish, kromkani materiallar bo'yicha ajratish, optimallashtirish).

**Detallar (CS)** — Excel kabi kiritish: yozing → Enter → keyingi katak, pastdagi bo'sh qator — yangi
detal; Excel dan Ctrl+V (fokusdagi katakdan boshlab), kromka ro'yxati (ОВ/ОН — uzunlik, ОЛ/ОП — en),
tekstura, 4 xil o'lcham (tooltip), «Свойства» (Ctrl+Space), «Групповые действия» (Ctrl+B),
ustunlar profillari (Ctrl+P, 46 ustun), o'lcham kiritish rejimi (zagotovka / detal / prifugovkadan keyin),
Excel/CSV import (ustunlar xaritasi bilan).

**Kroy** — ko'p darajali gilyotina optimizatori (propil, torsovka, minimal qirqim, tekstura, «Макс. количество
вращений», murakkab/oddiy polosalar, paket: yuqori to'ldirilgan karta takrorlanadi, paketdagi listlar =
min(Кратность, Высота пакета ÷ qalinlik) — paketlar soni ko'rsatiladi, «Большой пакет» afzalligi).
**Guruhlash (blok)** — «По длине/По ширине» belgilangan detallar k tadan (min/max) blokka birlashtirib kroy
qilinadi va «Толщина пилы для групповых деталей» bilan bo'linadi; «Мин. размер детали» dan kichik detallar va
kromkaga perpendikulyar tomoni cheklovdan kichik detallar ogohlantiriladi. **Qoldiqni yig'ish**: oxirgi (to'liq
bo'lmagan) listda detallar tor polosaga yoki burchakka zich joylanadi — bo'sh joy bitta katta деловой qoldiq bo'ladi;
chiqindisi yetarli boshqa listlarda ham. Korxonaning 205 ta real loyihasida (397 kroy, 12 581 detal; avvalgi dastur
fayl ichida saqlagan natija bilan): **1186 list — avvalgisi 1212** (15 kroyda kam, 1 chegaraviy kroyda vaqtga
qarab +1), teng kroylarda деловой qoldiq +15 %, kesish uzunligi −1.2 %; tekshiruv xatosi 0 (`tools/bench`,
`docs/mebelix/P_TAQQOSLASH.md`). Holat qatori
(№, S, C, Cp, LT, F), kartalar, miniatyuralar, buyruqlar jadvali (T/C/P/W + daraja),
**variantlarni solishtirish** (optimal / 1-kesim uzunlik / eni bo'yicha), **До кроить**,
**qo'lda tahrir** (detal qo'yish/olib tashlash, polosani boshiga/oxiriga, nusxa, kengaytirish,
boshqa yo'nalishda qayta kesish — har amal tekshiriladi: ustma-ust, propil, minimal qirqim, daraja).

**Qoldiqlar ombori** — kroydan keyin деловой qoldiqlar tasdiq bilan omborga yoziladi, keyingi
loyihada «Листы и остатки» ga qo'shiladi va birinchi navbatda kesiladi; kroy o'zgarsa yozuv bekor bo'ladi.

**Hisobot** — profillar, bo'limlar (sarlavha, omborga talabnoma, materiallar, mahsulotlar, CS detallar/
listlar/qoldiqlar/kartalar QR bilan, buyruqlar, EL, XNC chizmalari), ru/uz; brauzerda PDF.
**PDF**: asosiy yo'l — brauzerda «Печать / Chop etish → PDF sifatida saqlash» (hech narsa o'rnatish shart emas).
Serverda PDF (`GET /api/projects/{id}/report.pdf`) faqat `weasyprint` o'rnatilgan bo'lsa ishlaydi; u
`requirements.txt` ga ataylab kiritilmagan (Windows'da GTK kutubxonalarini talab qiladi: `pip install weasyprint` +
GTK3 runtime; Linux/Docker'da `libpango` kerak). O'rnatilmagan bo'lsa endpoint **501** va yo'riqnoma matnini
qaytaradi («brauzerda Chop etish → PDF dan foydalaning»).
**Etiketkalar** — har detal nusxasi uchun QR (arradan chiqish tartibida), A4 yoki termoprinter.

**Postprotsessor** — CSV, buyruqlar (TXT), DXF, MES JSON va **o'z stanogingiz formati**:
«Настройки → Постпроцессоры» da shablon (Jinja2, xavfsiz sandbox) — kod o'zgartirmasdan, jonli
tekshirish bilan. Namunaviy shablon bor; stanok formatini berganingizda shu yerga yoziladi.

**Import** — `.mxk.json` (o'z formatimiz) va korxonaning mavjud `.project` (XML) fayllari: mahsulotlar,
detallar, kromkalar, material/kesish parametrlari, CNC dasturlari (teshik/freza/paz). Faylning ichki
ikkilik kroy natijasi o'qilmaydi — loyiha MebeliX optimizatori bilan qayta kroy qilinadi.

**Sex rejimi** — `#/sex` (planshet + QR skaner): karta QR → karta chizmasi va «Раскроено +1».

## MES integratsiyasi

| So'rov | Vazifa |
|---|---|
| `POST /api/mes/orders` | MES buyurtmasi → loyiha (materiallar, kromkalar, mahsulotlar, detallar); qayta yuborilsa (tasdiqlanmagan bo'lsa) mavjud loyiha yangilanadi: MES ga tegishli maydonlar (detallar — id/uid turg'un, yangilari qo'shiladi, yo'qlari o'chadi) almashadi, lokal ish (holat, o'lcham rejimi, izoh, XNC/GR/EL tahrirlari, id/raqam) saqlanadi; tasdiqlangan (holat ≥ 2) — 409. Detal qatoriga ixtiyoriy `line_id` berilsa, qayta yuborishda shu bo'yicha topiladi |
| `GET /api/mes/orders/{ref}` (ref da `/` bo'lishi mumkin), `GET /api/projects/{id}/mes-export` | Natija: listlar, m², qoldiqlar, kromka m, narxlar, kartalar, omborga talabnoma |
| `POST /api/catalog/sync` | Materiallar va narxlar MES dan (upsert) |
| `GET /api/mes/scan/{qr}`, `POST /api/mes/scan/{qr}/done` | Etiketka/karta QR bo'yicha ma'lumot, karta kesildi (+1) |
| `GET/POST/PATCH/DELETE /api/remnants` | Qoldiqlar ombori |
| `GET /api/projects/{id}/material-check`, `GET /api/queue?statuses=0,1,2` | Material bazasi tekshiruvi (katalog `stock` + qoldiqlar) va buyurtmalar navbati: material to'liq bor birinchi loyiha, yetmaganlar uchun «bazani to'ldiring» |
| Webhook | `MES_WEBHOOK_URL` (+ `MES_WEBHOOK_TOKEN`): `project.status`, `cutting.done`, `map.done`, `project.created/updated`. Xatoda (ulanish, timeout, HTTP 5xx/408/429) fon vazifasida qayta uriniladi: `MES_WEBHOOK_RETRIES` (3), `MES_WEBHOOK_RETRY_DELAY` (1 s), `MES_WEBHOOK_TIMEOUT` (5 s); hammasi logga yoziladi. `POST /api/mes/webhook-test` — `sent` faqat server 2xx/3xx javob bersa `true`, aks holda `status`/`error`/`reason` |
| Avtorizatsiya | `MEBELIX_AUTH_REQUIRED=1` + `MEBELIX_JWT_SECRET` (HS256) yoki `MEBELIX_JWT_PUBLIC_KEY` (RS256); `Authorization: Bearer <jwt>`. Token da `exp` majburiy (muddatsiz — 401). Rollar (`roles`): `kroychi` (tahrir), `texnolog` (sozlamalar), `ko'ruvchi`/`viewer` — faqat o'qish (GET); yozish → 403 |
| CORS | standart — o'chiq (ilova bitta manzildan ochiladi). Boshqa domendagi ERP/MES brauzerdan chaqirsa: `MEBELIX_CORS=https://erp.korxona.uz` |

QR formatlari: detal — `MXK:<loyiha №>:<detal ID>:<nusxa>/<jami>`, karta — `MXK:<loyiha №>:<operatsiya id>:<karta №>`.

## Xavfsizlik va ma'lumotlar yaxlitligi

* Hisobot va etiketkalar: barcha matnlar escape qilinadi, sahifada skript taqiqlangan (CSP), oldindan ko'rish
  sandbox iframe da. Postprotsessor shablonlari — Jinja2 sandbox + alohida jarayon (vaqt 20 s, xotira 1 GB,
  chiqish 20 MB chegarasi; `MEBELIX_TEMPLATE_TIMEOUT`).
* Qoldiqlar ombori: omborga yozish faqat server amallarida; boshqa loyiha ishlatib bo'lgan qoldiq bekor qilishda
  o'chirilmaydi; omborda yetmasa — 409. Undo/redo, nusxa, import, papkani o'chirish, birlashtirish ombor
  va sex hisoblagichlarini buzmaydi. Qoldiqdan kesilgan listlar talabnomada alohida (№ bilan), narxi — maydoni bo'yicha.
* Kroy eskirishi: detal o'lchami/soni, mahsulot soni, kromka qalinligi/prifugovka, propil/torsovka o'zgarsa —
  natija o'chadi; faqat keyingi kroy strategiyasi (sifat, saralash) o'zgarsa — saqlanadi.

## Klaviatura

Ctrl+Z/Y — bekor/qaytarish · Ctrl+K — klon · Del — o'chirish · Ctrl+↑/↓ — ko'chirish ·
Ctrl+Space — xossalar (ro'yxatda — ochish) · Ctrl+PgUp (Alt+PgUp, Insert) — qator qo'yish ·
Ctrl+V — Excel dan (noma'lum kromka nomi — yangi EL) · Space — Ткт / navbatdagi kromka · Shift+Space — 4 tomonga
kromka · Ctrl+PgDn — yangi qator · Ctrl+B — guruhli amallar · Ctrl+D/E — teksturani olish/qo'yish ·
Ctrl+W (Alt+W) — uzunlik↔en · Ctrl+M — boshqa operatsiyaga · Ctrl+P — ustunlar · Ctrl+F — filtr ·
F1 — yordam · Home/↑/↓/End — kartalar · F2 — karta izohi · g'ildirak — masshtab ·
tahrirda Ctrl+R/Ctrl+Q/Ctrl+C/Ctrl+←→.
Brauzer Ctrl+W va Ctrl+PgUp ni o'zi band qiladi — «Проект → Полный экран» rejimida ular ham ishlaydi.

## Testlar

```bash
cd backend && pytest -q                         # 91 test (SQLite); PostgreSQL: MEBELIX_TEST_DB_URL=postgresql+psycopg://...
cd frontend && npm run e2e                      # (birinchi marta: npx playwright install chromium) Playwright: loyiha → CS → 14 detal → kromka → Раскроить → hisobot; yorliqlar, XSS, tahrir, sex, v2 (Space, bufer, otstup, ko'rsatkichlar)
cd tools/bench && python3 compare.py normal     # korxona loyihalari korpusi: listlar / деловой qoldiq / kesish — avvalgi dastur bilan
cd tools/bench && python3 el_check.py && python3 xnc_check.py   # kromka va CNC hisobi — saqlangan qiymatlar bilan
```

## Tuzilma

```
backend/app/   main.py (REST), api_extra.py (ombor, sozlamalar, MES), store.py, db.py, auth.py, i18n.py,
               models.py, plugins/ (.project import), services/ (optimizer, editor, validate, calc, render,
               labels, postprocessors, warehouse, settings, xnc, mes, importers, sizes)
frontend/src/  app/ (Layout), features/ (projects, project, cs, el, xnc, print, settings, help, workshop),
               shared/ (grid, hotkeys, ui, dialogs), api/, store/, i18n/ (ru.json, uz.json)
deploy/        nginx.conf        Dockerfile, docker-compose.yml, run.sh, run.bat, dev.sh
docs/mebelix/  v2 hujjatlari (biznes qoidalari, optimizator, UI, yorliqlar, qabul testlari, taqqoslash natijalari)
docs/suhbat/   suhbat arxivi: kontekst (Claude Code uchun), suhbat tarixi, texnik xulosa, ish tarixi, ilovalar
tools/bench/   korpus va solishtirish: compare.py (listlar/qoldiq/kesish), el_check.py, xnc_check.py, corpus_build.py;
               projects/ — korxonaning 205 ta .project fayli (git'ga kirmaydi)
mcp/           MCP serveri (Node): mx_* (REST), compare_* (fayl / onlayn bilan solishtirish), giblab_* (onlayn tizim brauzer orqali);
               .mcp.json — Claude Code uchun; `cd mcp && npm install && npm run build && npm test` (batafsil mcp/README.md)
.vscode/       VS Code: ishga tushirish, vazifalar, kengaytmalar        CLAUDE.md — doimiy qoidalar
```

Interfeys matnlari `frontend/scripts/i18n_src.py` da (bitta manba → `ru.json`, `uz.json`).
