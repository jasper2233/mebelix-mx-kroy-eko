# T. (O) Комплектация и другие действия — W5 paketi (2026-10-02)

Manba: `giblab_inventory/03_EL_GR_O_LB_ifodalar.md` §3 (spetsifikatsiya), K2, B10/B11/B13, G (import). GibLab yordami faqat funksional
ma'noni tushunish uchun o'qilgan, matn/rasm nusxalanmagan. Bu hujjat — amalga oshirilgan holat, taxminlar va bog'lanish nuqtalari.

## 1. Nima bu
Murakkab hisobsiz operatsiya: furnitura/qadoq materiallari sarfi, transport / o'rnatish / qadoqlash ish narxi, izoh.
Egasi — butun loyiha yoki bitta mahsulot (mahsulot bo'lsa har pozitsiya soni va ish narxi shu mahsulot soniga ko'paytiriladi).

## 2. Model (`backend/app/models.py`)
`OMaterial` (`id, code ≤100, name ≤300, unit ≤20 = «шт», qty 0..1e9 = 1, price 0..1e9 = 0`) · `OParams` (`owner_product_id`, `materials`
≤ 5000 (`O_MAX_ROWS`), `work_cost`, hisoblangan: `multiplier`, `messages`) · `Operation.o: OParams | None` · `PrintSettings.o_params / o_materials`.
Eski JSON: `o` yo'q → `None` (xato emas; `recalc_project` bo'sh `OParams` yaratadi). Eski saqlangan qiymat chegaradan chiqsa — qisqartiriladi
(`_legacy` konteksti: qty/price/work_cost, matn uzunligi, qatorlar 5000 gacha).

## 3. Hisob (`services/o_ops.py`, `calc.recalc_project` ichida)
```
mult = mahsulot.qty (egasi mahsulot)  |  1 (egasi — loyiha)
cost_material  = round(Σ(qty × price) × mult, 2)         cost_operation = round(work_cost × mult, 2)
omborga qty    = qty × mult   (mult = 0 yoki qty = 0 → qator chiqmaydi)
```
Namuna (testda): mahsulot «Shkaf» 3 dona; Ruchka 4 × 15 000 + Plyonka 2,5 × 8 000, ish 50 000 → **390 000** (240 000 + 150 000),
talabnoma 12 va 7,5; egasi — loyiha → **130 000**, talabnoma 4 va 2,5.
* Mahsulot o'chirilsa (yoki MES yangilashida yo'qolsa) — `owner_product_id = None`, `messages = ["owner_lost"]` (UI ogohlantiradi, «×» bilan yopiladi).
* Mahsulot narxi (Изделия): egasi mahsulot → butun narx shu mahsulotga (1 dona = jami / soni). Egasi loyiha → **taqsimlanmaydi** (standart).
  O'zgartirish: `o_ops.SPREAD_PROJECT_OWNED = True` (mahsulotlarga soniga proporsional taqsimlanadi) — test bor.
* Qator «Стоимость» = `qty × price` ko'paytirgichsiz (1 mahsulot uchun); ko'paytirgichli jami — jadval tagida va «Параметры» da.

## 4. API (`backend/app/api_o.py`, `main.py` da bitta `include_router`)
| So'rov | Vazifa |
|---|---|
| `POST /api/projects/{pid}/operations {type:"O"}` | yaratish (`o_defaults` bo'yicha ish narxi) |
| `PATCH …/operations/{oid} {o:{owner_product_id, work_cost, messages}, description}` | parametrlar; yo'q mahsulot egasi → 422 |
| `PUT …/operations/{oid}/o/materials [OMaterial…]` | butun jadvalni almashtirish (1 undo qadami); > 5000 qator, chegara buzilishi → 422 |
| `POST …/o/materials/paste {text, mode: append\|replace}` | Excel/TSV dan; javob: loyiha + `added`, `skipped:[{row, reason}]`, `warnings`; hech narsa qo'shilmasa tarixga yozilmaydi |
| `PUT /api/settings/o_defaults/default {work_cost, unit}` | yangi O ish narxi va yangi qatorlar birligi |
Talabnoma (`GET …/warehouse`, hisobot, `mes-export.warehouse`) da O qatorlari: Тип `O`, Код = material kodi, Наименование = `operatsiya — material`,
o'z birligi, Кол = qty × mult. `mes-export.operations[]` da O: `owner_product_id, multiplier, work_cost, materials[{…, qty_total}]`.

## 5. Interfeys (`frontend/src/features/o/OPanel.tsx`, `OCatalogPicker.tsx`)
«Параметры» (Владелец, Стоимость материала — o'qish, Стоимость операции, Стоимость, Описание) va «Материалы» (jadval `№ Код Наименование Ед.И Кол Цена Стоимость`).
Yorliqlar (materiallar jadvali): Ctrl+PgDn — oxiriga qo'shish, Ctrl+PgUp/Insert — joriydan oldin, Del — o'chirish, Ctrl+K — nusxa, Ctrl+↑/↓ — ko'chirish,
**Ctrl+V** — Excel dan (Код, Наименование, Ед.И, Кол, Цена), Enter/Tab — keyingi katak (Excel kabi). Katak tahrirlari yig'iladi va hech bir katak tahrirda
bo'lmay qolganda (350 ms) bitta so'rov bilan yuboriladi (tez yozishda tahrir uzilmasin). «Каталог» — katalogdan bir nechta tovarni qator qilib qo'shadi
(`OCatalogPicker`: umumiy `CatalogPicker` faqat list/kromkani operatsiyaga aylantiradi, shuning uchun alohida oyna; W3 daraxt oynasini tugatgach almashtirish mumkin).
«Печать отчета» → «(O) Комплектация» bo'limi (`o_params`, `o_materials`). Qilinmadi: jadval ustunlarini sozlash (Ctrl+P) — ustunlar 6 ta, qat'iy.

## 6. `.project` importi (`plugins/legacy_project.py` → `o_ops.from_project_xml`)
`<operation typeId="O">`: `typeName/description/code/printable/startNewPage`, `costOperation` → `work_cost`, `<material id count/>` → `OMaterial`
(`<good typeId="simple">`: `code, name, unit, count, cost`; Кол — `material.count`, bo'lmasa `good.count`). `owner` mahsulot good id si bo'lsa — shu mahsulot,
aks holda loyiha (`0`, `-1`, noma'lum id — loyiha). **Taxminlar (real korpusda O yo'q, 205 faylda 0 ta):**
1. `owner` mahsulot good id si deb olindi (format «изделие или проект» deydi, qiymat shakli yozilmagan);
2. egasi mahsulot (soni q > 1) va `costMaterial` ≈ Σ(Кол × Цена) × q bo'lsa — fayldagi summalar barcha mahsulot uchun yozilgan deb, ish narxi q ga bo'linadi
   (ogohlantirish bilan); `costMaterial` Σ(Кол × Цена) ga teng bo'lsa — o'zgarishsiz.
Yo'q material havolasi / yo'q egasi — ogohlantirish. CL/SP/LB/CN lar avvalgidek o'tkazib yuboriladi va aytiladi. `.project` **eksport** yo'q (CLAUDE.md 4-qoida).

## 7. Excel importi bilan bog'lanish nuqtasi (W3 uchun; W3 fayllariga tegilmadi)
* Matn (TSV) → `o_ops.parse_paste(text, room, default_unit)`; **katak qatorlari** (Excel varag'i) → `o_ops.parse_rows(((qator_raqami, [Код, Наименование, Ед.И, Кол, Цена, …]), …), room, default_unit)`.
  Ikkalasi `PasteResult(rows: list[OMaterial], skipped: [{row, reason}], warnings)` qaytaradi — `ExcelImport` dagi `skipped/warnings` bilan bir xil shakl.
* «Простые операции» tabi: yangi O operatsiyasini `Operation(type=OpType.O, name=…, o=o_ops.new_params(settings.get_default("o_defaults")))` bilan yarating, `o.materials = res.rows`
  (jami ≤ 5000 — `room` ni shunga moslang), keyin `store.editing` ichida `project.operations.append(op)`; hisob `recalc_project` da avtomatik.
* «Материалы» tabi (katalogga) — `importers.import_catalog` ga tegishli; O jadvaliga qo'yish `parse_rows` orqali.
* Son o'qish `importers.parse_number` ga tayanadi (nomi/imzosi o'zgarmasin yoki `o_ops.parse_rows` dagi importni moslang).

## 8. Ochiq savollar (foydalanuvchiga)
1. Egasi «Проект» bo'lsa, O narxi mahsulotlarga taqsimlansinmi? (hozir yo'q; `SPREAD_PROJECT_OWNED`).
2. `.project` da O `owner` qiymati va `costOperation` (ko'paytirilganmi, 1 dona uchunmi) — bitta real O fayli kerak (hozir taxmin, §6).
3. O jadvalidagi qator «Стоимость» mahsulot soniga ko'paytirilgan holda ko'rinsinmi (hozir yo'q — 1 dona uchun; jami pastda ko'paytirgich bilan)?
4. Mahsulot nusxalanganda (Ctrl+K) unga tegishli O operatsiyalari ham nusxalansinmi (hozir yo'q — asl mahsulotda qoladi)?
5. Tayyor shablonlar (transport / o'rnatish / qadoqlash, O-016) kerakmi?

## 9. Testlar — `backend/tests/test_o_operation.py` (29 ta)
Spetsifikatsiya namunasi (390 000 / 130 000, talabnoma 12 / 7,5 va 4 / 2,5, mahsulot narxi), soni 3 → 5 → 0, mahsulot o'chirilishi, egasi 422, taqsimlash
konstantasi, paste (sonlar, bo'sh qator, 5001-qator, sarlavha, uzun matn, `o_defaults` birligi), chegaralar (422), eski JSON va `legacy` qisqartirish, eksport/import,
klon + undo, hisobot (ru/uz, escape, bo'limlar), MES eksport, `.project` importi (egasi mahsulot/loyiha, ogohlantirishlar, narx taxminiy bo'lish, API orqali).
