# T. W14 — «Заказать» oqimi, loyiha ro'yxati ustunlari, «Общие действия»

Chegara: MES integratsiyasi (REST klientlari, mijoz buyurtma portali, ID+PIN, GibSaw) — korxona MES jamoasiniki. Bu paket faqat **ichki**
ish oqimi: holatlar, o'tish qoidalari, «Заказать» oynasi, tayyorlik sanasi va holat o'zgarganda mavjud MES webhooki.
Manba: GibLab buyurtma yordami (`order/help_ru`) — faqat funksional ma'no, o'z so'zlarimiz bilan. Yordam aytmagan hamma joy
**konstanta** orqasida standart tanlangan (pastda «Savollar»).

## 1. Holatlar va o'tish qoidalari (`services/order_flow.py`)

| Holat | Ma'nosi (yordamdan) |
|---|---|
| 0 Не заказан | buyurtma to'ldirilmoqda |
| 1 Заказан | buyurtma tekshiruv va baho uchun ijrochiga yuborilgan («Заказать» tugmasi shuni qiladi) |
| 2 Утвержден | qabul qilindi, ishga tushdi, **tayyorlik sanasi** qo'yildi (ORD-006) |
| 3 Готов | tayyor mahsulot ombordan olinadi |

Yordamda yo'q (bizning qarorlar, konstantalar `order_flow.py` boshida):

| Qoida | Standart | Konstanta |
|---|---|---|
| oldinga 0→1, 1→2, 2→3 | yozish huquqi bor hamma rol | — |
| oldinga o'tkazib 0→2, 0→3, 1→3 | **ruxsat** (avvalgi PATCH xulqi; ichki buyurtma) | `ALLOW_SKIP_FORWARD` |
| orqaga (har qanday kamayish) | faqat `admin`, `texnolog` (`texnolog`/`technologist`), rolsiz token va lokal rejim — kroychi **yo'q** | `BACK_ROLES` |
| «ko'ruvchi» (read_only) | hech qanday o'zgartirish yo'q (403) | — |
| «Утвержден» ga o'tishda sana | **majburiy** (`POST .../order`): so'rovda `ready_date` yoki oldin qo'yilgan sana (> buyurtma sanasi). Sana «qo'yilmagan» = tayyorlik sanasi ≤ buyurtma sanasi (yangi loyihada ikkalasi bugun) | `ready_is_set` |
| undo/redo | holatni pasaytiruvchi qadam ham «orqaga qaytarish» qoidasiga bo'ysunadi (Ctrl+Z bilan aylanib o'tib bo'lmaydi) | `check_step` |
| tahrir bloklanishi | **o'chiq** (yordamda bloklash haqida gap yo'q): faqat ogohlantirish. Yoqish: `MEBELIX_ORDER_LOCK_FROM=2` (Утвержден dan) yoki `3` (Готов dan) | `LOCK_ENV` |

Bloklash yoqilganda 409 beradi: `operations/*`, `products/*`, `actions/*`, `import/*` (Excel) so'rovlari. Ochiq qoladi: o'qish,
sarlavha (PATCH), holat (`/order`), saqlash, undo/redo, nusxa, hisobot/ko'rish, eksport va sex «bajarildi» (`/mes/scan`).
MES buyurtmasini qayta yuborish ≥ «Утвержден» da 409 — avvalgidek (alohida mexanizm, o'zgarmagan).

**Ogohlantirishlar (hech narsani bloklamaydi):** «Заказан»: detallar yo'q; «Готов»: CS operatsiyasi kroysiz; kartalar sexda
«bajarildi» deb belgilanmagan. Loyiha sarlavhasida ≥ «Утвержден» da «Правки после утверждения» belgisi (bloklash yoqilsa — qizil
«Редактирование заблокировано»).

## 2. API

| So'rov | Vazifa |
|---|---|
| `GET /api/projects/{id}/order` | joriy holat, har maqsad bo'yicha `allowed/reason/needs_ready_date/warnings` (rolga ko'ra), tarix (yangisi birinchi), `lock`, `edit_warning` |
| `POST /api/projects/{id}/order` | `{status (standart 1), ready_date?, executor?, comment?}` → loyiha. Xato: 403 (rol / orqaga), 409 (o'sha holat / o'tkazib), 422 (sana kerak / noto'g'ri holat), 400 (sana noto'g'ri) |
| `PATCH /api/projects/{id}` `{status}` | eski yo'l saqlangan (sanasiz «Утвержден» ham ishlaydi); rol/orqaga qoidalari va tarix amal qiladi |
| `POST /api/projects/{id}/actions/clear` | «Очистить проект» (pastda) |
| `GET /api/projects` | endi `updated_at` UTC belgisi («Z») bilan; `?status=` filtri (avvaldan) |

**Tarix:** `Project.order_log` (yangi maydon; eski JSON da yo'q — bo'sh): `at` (UTC), `user`, `from_status`, `to_status`, `executor`, `comment`,
`ready_date`, `via` (order | patch); oxirgi 100 ta. Loyiha JSON ida — undo/redo holat bilan birga yuradi; nusxada tozalanadi.
**Ijrochi/izoh — faqat ichki matn:** webhookka ham, MES eksportiga ham kirmaydi.
**MES webhook:** holat o'zgarsa mavjud `mes.send_webhook("project.status", {project_id, number, mes_order_ref, status, old_status})`
(fon vazifasi) — yuklama PATCH dagi bilan aynan bir xil, `services/mes.py` o'zgartirilmagan.

## 3. Interfeys (`frontend/src/features/order/`)
- Chap «Проект» menyusidagi blok (`OrderPanel`): holat belgisi, tayyorlik sanasi, navbatdagi qadam tugmasi («Заказать» → «Утвердить» →
  «Отметить готовым»), «Состояние заказа…», narxlar. Eski holat tanlagich (select) olib tashlandi.
- «Заказать» / «Состояние заказа» oynasi (`OrderDialog`): maqsad holat (ruxsat etilmaganlari sababi bilan xira), tayyorlik sanasi («Утвержден»
  da majburiy), ijrochi, izoh (ichki), ogohlantirishlar, holatlar tarixi.
- Loyiha sarlavhasi: holat belgisi + ≥ «Утвержден» da ogohlantirish belgisi. Ro'yxat: «Состояние» belgisi, **«Изменено»** ustuni (OL-007;
  `updated_at` UTC → mahalliy vaqt), holat bo'yicha filtr (saralash — ustun sarlavhasi).
- «Общие действия»: onlayndagi 3 amal (`merge-same`, `split-edges`, `optimize-ops`) + avvalgi «Перекодировать XNC» + **«Очистить проект»**.

## 4. «Общие действия»
- **Onlayn 3 amal bizda ishlaydi** (testlar: `test_order_w14_actions.py`): birlashtirish (CS/CL/EL: bir xil tur+kod+nom; kromka qalinligi boshqa EL
  birlashmaydi; kromka havolalari qayta bog'lanadi; tegilmagan CS natijasi saqlanadi), kromkani materiallar bo'yicha ajratish (har CS o'z kromka
  nusxasi «nom (CS nomi)»; takror chaqiruv yangisini yaratmaydi), operatsiyalarni optimallashtirish (bo'sh CS, ishlatilmagan EL va avto-XNC
  o'chadi, bir xillari birlashadi, tartib CS→EL→GR→XNC; qo'lda qo'shilgan XNC/GR qoladi). Har biri — bitta undo qadami.
- **«Очистить проект» — TAXMINIY, xavfsiz talqin** (GibLab yordamida ma'nosi yo'q): kroy natijalari va ulardan hisoblangan sanoqlar
  (`result`: kartalar, qoldiqlar, sex «bajarildi» belgilari; detalda «Раскроено/Осталось»; listda «Использовано») tozalanadi; omborga yozilgan
  qoldiqlar bekor qilinadi (qayta kroydagidek; undo ularni qayta yozmaydi). **Detallar, mahsulotlar, operatsiyalar va parametrlari, listlar ro'yxati,
  kromka/XNC/etiketka ma'lumotlari saqlanadi.** Tasdiq oynasi (nechta operatsiya/karta, ombor va holat ogohlantirishi), bitta undo qadami;
  tozalanadigan narsa bo'lmasa bo'sh qadam yozilmaydi. Holatga qarab bloklanmaydi (bloklash yoqilgan bo'lsa — 409).
- **«KDT Sort line» — qilinmadi** (ma'nosi noma'lum); «Пересчитать параметричность» — W12 (tegilmadi).

## 5. Testlar (`backend/tests/test_order_w14_*.py`)
`flow` (o'tish matritsasi 16×6 rol, jadval, rollar, sana, tarix, webhook (mock va httpx), undo qoidasi, PATCH moslik, eski JSON, nusxa),
`lock` (sozlama, standart «bloklanmaydi», yoqilgan holat, ogohlantirishlar), `actions` (3 amal, «Очистить проект» + undo + ombor),
`list` (ustunlar, «Изменено» UTC, holat filtri, «Владелец»: yaratish/nusxa/MES/import/JWT).

## 6. Savollar (qaror foydalanuvchida)
1. Kim «Утвержден» va «Готов» qo'ya oladi? Hozir yozish huquqi bor hamma rol (kroychi ham). Faqat texnolog/admin bo'lsinmi?
2. Holatni o'tkazib yuborish (0→2, 0→3, 1→3) ruxsatmi? (Hozir ha — eski PATCH xulqi.)
3. Orqaga qaytarish faqat admin/texnolog. «Заказан → Не заказан» (buyurtmani qaytarib olish) kroychiga ham ruxsat bo'lsinmi?
4. Tahrir bloklash kerakmi (qaysi holatdan va nima)? Hozir faqat ogohlantirish; `MEBELIX_ORDER_LOCK_FROM=2|3` bilan yoqiladi.
5. MES webhook: hozir faqat `project.status` (+ `old_status`). Hujjatlardagi `project.ordered` (ijrochi bilan) yo'q; `ready_date` yuklamada yo'q.
   MES jamoasi tayyorlik sanasini webhookda xohlaydimi (qo'shimcha kalit — orqaga mos)?
6. «Утвержден» da sana majburiyligi hozir faqat «Заказать» oynasi / `POST /order` da; eski `PATCH {status}` sanasiz ishlayveradi.
   PATCH ni ham yopaylikmi (MES/boshqa mijozlar `POST /order` ga o'tadi)?
7. «Готов» uchun qat'iy shart kerakmi (masalan, hamma kartalar sexda «bajarildi»)? Hozir faqat ogohlantirish.
8. «Очистить проект» ma'nosi to'g'rimi (faqat kroy natijalari)? Yoki GibLabda detal/operatsiyalarni ham o'chiradimi? «KDT Sort line» nima qiladi?
9. «Владелец»: `.mxk.json` importida fayldagi ega saqlanadi (bo'sh bo'lsa import qilgan foydalanuvchi). Onlayn GibLabda import qiluvchi egasi bo'ladimi?
   Ustunda «Мой/boshqa» ko'rinishi kerakmi?
10. `merge-same`: birlashayotgan CS operatsiyalarining list zaxiralari (`sheets`, qoldiq bog'lanishlari) birlashtirilmaydi — birinchisiniki qoladi,
    qolganlariniki tushib qoladi. GibLabda ham shundaymi (yoki zaxiralar yig'ilishi kerakmi)?
11. Onlayndagi «№» (qator raqami) ustuni qo'shilmadi (ID ustuni bor) — kerakmi?

## 7. Boshqa paketlarga ta'sir
- `models.py`: `OrderLogEntry` + `Project.order_log` (eski JSON da standart bo'sh). `.project` importi/eksporti (W10) bu maydonni bilmaydi — normal.
- `main.py`: `api = APIRouter(..., dependencies=[current_user, order_flow.edit_guard])`; `update_project_header` va `undo/redo/_step` ga `user`;
  `copy_project` tarixni tozalaydi; `list_projects.updated_at` — «Z» bilan. `api_order.py` routeri `extra_router` dan keyin ulangan.
- `auth.py`: `canonical_roles(roles)` qo'shildi (`is_read_only` shuni ishlatadi, xulq o'zgarmagan).
- `ProjectMenu.tsx`: `CommonActions` ga `project` prop; yangi amallar (W12 «Пересчитать параметричность») `action-list` oxiriga qo'shiladi.
  Eski `order-status` selecti o'rniga `OrderPanel` (testid: `order-btn`, `order-manage`, `order-status-badge`, `order-dialog`, `order-confirm`).
- `app/i18n.py`: `order_*` kalitlari; frontend: `scripts/i18n_w14.py`.
- MES jamoasi: webhook yuklamasi o'zgarmagan; yangi `GET/POST /projects/{id}/order` ixtiyoriy ishlatiladi.
