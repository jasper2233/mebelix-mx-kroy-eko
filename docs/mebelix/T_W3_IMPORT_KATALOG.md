# T. W3 — Excel import v2 va «Товары» (material katalogi) daraxti

Paket: `giblab_inventory/05` WP-A (XLS-001…015, UPD-013) va WP-B (CAT-001…003, 007). GibLab yordami faqat funksional ma'noni
tushunish uchun o'qildi; kod, matn va rasmlar o'zimizniki.

## 1. Excel import v2

**Kirish:** `POST /api/projects/{pid}/import/excel` — `multipart`: `file` (.xlsx / .xls / .csv), `config` (JSON), `dry_run` (ixtiyoriy).
CS operatsiyasi bo'lmagan loyihada ham ishlaydi («Проект → Импорт из Excel» har doim faol). Eski
`POST …/operations/{oid}/parts/import` o'zgarmagan (javob shakli ham).

`config` (`services/import_v2.ExcelImportConfig`):

| Maydon | Ma'nosi |
|---|---|
| `mode` | `full` (standart) · `products_qty` — mavjud loyihada **faqat mahsulot soni** yangilanadi, hech narsa qo'shilmaydi |
| `parts` | «Детали»: `enabled`, `sheet` (0 dan) yoki `sheet_name`, `start_row` (2), `end_row` (0 = oxirigacha), `map`, `size_mode`, `skip_zero_qty`, `target_op` |
| `parts.map` | `length`, `width`, `qty`, `grain`, `name`, `number_in_name`, `description`, `code`, `edge_top/bottom/left/right`, **`material`**, **`product`** — ustun harflari |
| `products` | «Изделия»: `enabled`, varaq/qatorlar, `link` (`code` \| `name`), `map` (`code`, `name`, `qty`, `description`, `phone1`, `phone2`, `date`), `skip_zero_qty`, `add_empty` |

**Guruhlash.** `material` ustuni: har qiymat uchun loyihadagi CS (nom, so'ng kod bo'yicha; katta-kichik harf va ortiqcha bo'sh
joy farqsiz) topiladi, bo'lmasa yaratiladi — katalogda (`kind=sheet`) nom yoki kod bilan **aniq** mos qator bo'lsa, qalinlik/narx/
list o'lchami/kerf/tekstura undan; aks holda «Настройки» dagi standartlar. Material bo'sh qatorlar `target_op` ga (berilmasa —
loyihadagi birinchi CS, u ham yo'q bo'lsa «Материал 1»). `product` ustuni: mahsulot topiladi yoki yaratiladi (soni 1);
«Изделия» tabi yoqilgan bo'lsa — kalit (`link`) bo'yicha shu varaqdagi qator olinadi. Yangi CS lar shu importda yaratilgan
kromkalardan oldin turadi. Hech narsa qo'shilmagan standart «Изделие 1» yangi mahsulotlar kelsa olib tashlanadi.

**O'lcham rejimi.** `size_mode` ≠ `project` bo'lsa fayldagi uzunlik/en shu ma'noda (zagotovka / detal / prifugovkadan keyin)
qabul qilinib, loyiha rejimiga `services/sizes.compute_sizes` bilan o'tkaziladi (kromka qalinligi/prifugovka hisobga olinadi).
Loyiha bo'sh (detali yo'q) bo'lsa — aksincha, **loyiha rejimi** faylnikiga almashadi (raqamlar o'zgarmaydi; javobda
`size_mode_changed`).

**Qoidalar.** `Длина`, `Ширина` majburiy; `Количество` ustuni ko'rsatilgan bo'lsa u ham (bo'sh / son emas — qator tashlanadi
va `skipped` da sababi bilan); ustun ko'rsatilmasa soni 1. Soni 0 qatorlar — `skip_zero_qty` bo'lmasa qo'shiladi. «Изделия»
varag'ida soni bo'sh = 0. 0 sonli (qo'shilmagan) mahsulotning detallari ham tashlanadi.

**Javob:** loyiha (avvalgidek) + `imported`, `skipped` (`[{row, reason, tab}]`), `warnings`, `created_edges`, `created_ops`,
`created_products`, `updated_products`, `zero_skipped`, `size_mode_changed`. `dry_run=true` — loyiha o'zgarmaydi, javobda faqat
hisobot (`dry_run: true`).

**Profillar.** `excel_import` scope (modelsiz dict) kengaytirildi: `{mode, parts: {...}, products: {...}}`; eski `{map, start}` ochiladi
(frontend `applyProfile`). `target_op` profilga yozilmaydi (loyihaga xos).

## 2. Fayl o'qish va xavfsizlik (`services/importers.Book`)

* Tur mazmundan aniqlanadi: `PK…` → .xlsx, OLE2 → .xls, boshqasi → CSV. Kengaytmasi Excel bo'lib mazmuni boshqa (HTML-«xls»,
  shifrlangan) bo'lsa — aniq xabar.
* **`.xls`** — `xlrd>=2.0.1` (`requirements.txt`). O'rnatilmagan bo'lsa: «.xls o'qish uchun xlrd kerak — .xlsx yoki .csv qilib saqlang».
* Chegaralar: fayl ≤ `MAX_FILE_BYTES` (10 MB, 413), .xlsx ochilgach ≤ 150 MB / 2000 qism (zip-bomba), o'qiladigan qator ≤
  `MAX_ROW_NO` (50 000), ustun ≤ 256, bir importda ≤ 20 000 detal va ≤ 100 yangi CS (`MAX_IMPORT_PARTS`, `MAX_NEW_OPS`).
* Formulalar hisoblanmaydi (saqlangan qiymat o'qiladi), makrolar bajarilmaydi (`read_only`, `data_only`, `keep_links=False`;
  XML — `defusedxml`). Mijoz fayli faqat xotirada; diskka yozilmaydi (Starlette >1 MB ni vaqtinchalik faylda ushlaydi va so'rovdan keyin o'chiradi).
* `POST /api/import/preview`: `sheets`, `columns`, `rows`, `sheet`, `format`; `sheet_name` qabul qiladi.

## 3. «Товары» katalogi

* **Model.** `catalog_items` (+ `has_image`), yangi `catalog_images(item_id, data)` — rasm alohida jadvalda (ro'yxatga og'ir matn chiqmasin).
  Papka — `kind="folder"`; material — `sheet | linear | edge | surface`.
* **API** (`api_catalog.py`; `/catalog/sync` yo'li va javobi o'zgarmagan, `image_errors` qo'shildi):
  `GET /catalog` (kind, parent_id, q, limit, **recursive**, **unfiled**, **folders**, **tree=true**) ·
  `GET /catalog/tree` (`{nodes: [{id, parent_id, name, count, children}], total, unfiled}`; kind/q bo'yicha mos bo'lmagan papkalar tushadi) ·
  `GET /catalog/{id}` (+ `image`) · `PUT|DELETE /catalog/{id}/image` · `DELETE /catalog/{id}?recursive=true`.
* **Import** (`POST /catalog/import`): ustunlar `id, parent_id, isfolder, code, name, unit, price, stock, image, params, thickness,
  length, width, kind`; `roots` = `{tur: ildiz papka ID}` (qator turi shu ildiz ostida bo'lishidan olinadi; aniq `kind` ustuni ustun,
  so'ng ildiz, so'ng `kind` standarti); `isfolder` ustuni bo'lmasa — ota bo'lgan qator papka; `id_prefix` (boshqa fayl/MES ID lari
  bilan to'qnashmaslik); `sheet_name`, `end_row`. Sikllar uziladi, takroriy ID — oxirgi qator. Ommaviy yozish (`bulk_*`); ustun
  ko'rsatilmasa mavjud rasm/parametr saqlanadi.
* **`params`** ustuni: JSON obyekt yoki `kalit=qiymat; kalit2=qiymat2` (≤ 50 ta; qiymat son / true-false / matn). `kerf`, `trim_length`,
  `trim_width`, `grain`/`texture`, `price_per_m2` — yangi CS yaratilganda ishlatiladi (`main._new_operation`).
* **Rasm xavfsizligi.** Faqat `data:image/(png|jpeg|gif|webp);base64,…` (≤ 256 KB, tomonlari ≤ 8192 px — sarlavhadan) yoki `http(s)://`
  havola (≤ 500 belgi, login/parolsiz, bo'shliq va `<>"'\` belgisiz). Tur sehrli baytlardan aniqlanadi (mijoz MIME ga ishonilmaydi),
  SVG/HTML rad. Excel «Изображение» ustunidagi fayl yo'llari **o'qilmaydi** (server fayllariga yo'l yo'q) — ogohlantirish. Frontend
  yana tekshiradi (`safeImage`) va `referrerPolicy="no-referrer"` bilan ko'rsatadi.
* **UI.** `features/catalog/*`: `CatalogBrowser` (chapda daraxt, o'ngda rasm + parametrlar, pastda jadval; tur filtri daraxtni
  toraytiradi; qidiruv; papkani tanlash — ichki papkalar bilan), `CatalogPicker` (operatsiya qo'shish), «Настройки → Каталог товаров»
  (`CatalogPage`: import, o'chirish, rasm yuklash/olib tashlash, papkani rekursiv o'chirish), `CatalogImport`. Import sozlamalari
  (ustun xaritasi, ildizlar, prefiks) brauzerda (`localStorage`) eslab qolinadi.

## 4. Qabul qilingan standartlar (bitta joyda o'zgaradi)

| Qaror | Joy |
|---|---|
| «Поместить номер в наименование»: qiymat nomning **oldiga** («3 Полка») | `import_v2.NAME_NUMBER_FMT` |
| Mahsulot «Дата» → `Product.ready_date` (matn, YYYY-MM-DD) | `import_v2._read_products` |
| Mavjud (mos kelgan) mahsulot oddiy rejimda **o'zgarmaydi** (faqat `products_qty` rejimida soni yoziladi) | `_import_parts` |
| «Количество» ustuni ko'rsatilgan-u bo'sh — qator tashlanadi (GibLab kabi); eski `parts/import` da bo'sh = 1 | `import_v2` / `import_parts_ex` |
| Rasm yo'llari (`C:\…`) o'qilmaydi | `catalog.normalize_image` |

## 5. Qilinmadi

«Материалы» va «Простые операции» tablari (mazmuni yordamda yo'q / O operatsiyasi — W5), (SP)/(GR)/(XNC) ustun guruhlari (XLS-009),
ildiz kategoriyalarni **serverda** saqlash (hozir import so'rovida va brauzerda), rasmlarni ommaviy yuklash (zip), katalog tahriri (qo'lda qator qo'shish).

## 6. Testlar

`backend/tests/test_import_w3_excel.py` (guruhlash, o'lcham rejimi, mahsulotlar, `products_qty`, dry-run, xavfsizlik chegaralari, `.xls`),
`test_import_w3_catalog.py` (daraxt, ildiz turlar, rasm xavfsizligi, sync buzilmasligi, rekursiv o'chirish, `.xls`);
fikstura: `backend/tests/fixtures/w3_sample.xls`, `w3_goods.xls` (xlwt bilan yaratilgan, kichik, mijoz ma'lumotisiz).
