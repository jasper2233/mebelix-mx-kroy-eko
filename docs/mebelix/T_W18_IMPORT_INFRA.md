# T. W18 — «Импорт из других программ» infratuzilmasi (WP-C), Excel bo'shliqlari va mayda bandlar (2026-10-02)

Manba: `giblab_inventory/05` (IMP-001, 004–006; XLS-005, 009, 012, 013, 017; OL-007), `T_W3_IMPORT_KATALOG.md` §5 («Qilinmadi»), `T_O_KOMPLEKTATSIYA.md` §7,
`T_W12_SP_PROGRAMMA.md` §1, `T_W7_PP_SXEMA.md`. GibLab yordami faqat funksional ma'noni tushunish uchun o'qilgan; kod, matn, ikonka bizniki.
Shu paketning boshqa bloklari: `T_W18_XNC.md` (XNC), `T_W18_CL.md` (CL).

## 1. «Импорт из других программ» (IMP-001/004/005/006)

### 1.1 Modullar
| Nima | Fayl |
|---|---|
| Format katalogi, parametrlar sxemasi, profil modeli, JSON/XML fayl, `option()` | `backend/app/services/import_formats.py` |
| Plagin reestri (`key`, `exts`, `by_ext`, `by_key()`) | `backend/app/plugins/__init__.py` |
| API (`/api/import/*`) | `backend/app/api_import_w18.py` (`main.py` da bitta `include_router`) |
| Profil doirasi `import_profile`, umumiy sozlama `import_settings` | `services/settings.py`, `services/import_settings.py` |
| `.project` importeri: parametrlarni o'qiydi | `plugins/legacy_project.py` (kichik Edit), `services/cl_import.py` (1 qator) |
| UI | `frontend/src/features/importer/{ImportDialog.tsx, importApi.ts, importIcons.ts, importer.css}`; `ProjectMenu.tsx` (eski `ImportOther` o'rniga) |
| i18n | `frontend/scripts/i18n_w18_import.py` (`importx.*`), `backend/app/i18n.py` (`imp_*`) |
| Testlar | `backend/tests/test_w18_import.py` (21) |

### 1.2 API
| So'rov | Vazifa |
|---|---|
| `GET /import/catalog` | `[{key, name{ru,uz}, exts[], icon, status: ready \| no_module, reason, n_params}]` — katalog + plagin reestri |
| `GET /import/formats/{key}/schema[?profile_id=]` | ParamGrid sxemasi (W7 bilan bir xil shakl: `groups[{key,ru,uz,params[]}]`, `values`, `defaults`, `modified`) + `help{ru,uz}`; parametrda `help` |
| `POST /import/run` | multipart: `file`, `format`, `profile_id?`, `params?` (JSON), `folder_id?` → `{project, warnings, format, options}`. Standart ← profil ← `params` (tur qat'iy: `"false"` matni bool emas) |
| `GET /import/profiles[?format=]` | `[{id, name, format, params, is_default}]` |
| `GET /import/profiles/export?as=json\|xml[&format=][&ids=1,2]` | profillar fayli (hamma parametr qiymati **aniq** yoziladi) |
| `POST /import/profiles/import` | multipart `file` (JSON yoki XML — mazmundan), `on_conflict=replace\|rename\|skip` → `{created, replaced, renamed, skipped, invalid[], total}` |
| `POST/PUT/DELETE /settings/import_profile[/{id}]` | profil yaratish/o'zgartirish/o'chirish (umumiy sozlamalar API si); `data = {format, params}` |

Xavfsizlik: faylni diskka yozmaydi; `/import/run` ≤ 64 MB (413), profillar fayli ≤ 1 MB va ≤ 200 profil; XML — `defusedxml` (XXE / «billion laughs» rad);
parametrlar `pp_machine_schema.coerce` bilan qat'iy tekshiriladi, xato → 400 va hech narsa saqlanmaydi.

### 1.3 Format holati va dinamik ro'yxat
Dialog ro'yxati — **plagin reestridan**: `services/import_formats.CATALOG` (nom, kengaytma, ikonka, parametrlar, «Справка») + `plugins.BY_KEY` (importer bor-yo'qligi).
Importeri yo'q format — `no_module`: ro'yxatda xira, parametrsiz, «Нет модуля импорта — предоставьте образец файла», `/import/run` → 400. **Importerlar o'ylab topilmaydi**
(CLAUDE.md 4–5): hozir faqat `.project` ishlaydi; PRO100 (`.sto`), Imos (`.fxm`), Базис-Мебельщик (`.xml`, `.obl` — eski yo'l ham shu yerda), BCAD (`.xml`),
Woody2 (`.xml`, `.wes`), WoodWop (`.mpr`), iLENIA (`.pd4`) — namuna fayl kelguncha `no_module`. Katalogda yo'q, lekin plagin ro'yxatdan o'tgan format ham ro'yxatga
chiqadi (umumiy yozuv sifatida). Ikonkalar — o'zimizning umumiy belgilarimiz (dastur logotiplari ishlatilmaydi).

### 1.4 Yangi importer qo'shish yo'li (qo'llanma)
1. **Namuna fayl** (mijoz ma'lumotisiz) va fayldan loyihada nima chiqishi kerakligi tavsifi — usiz importer yozilmaydi.
2. `backend/app/plugins/<nom>.py`: `@register(".fxm", "Imos (fxm)", key="imos")` bilan `(bytes, filename) -> (Project, list[str])` funksiyasi. `key` — `CATALOG` dagi kalit.
   Bir xil kengaytma bir necha formatda bo'lsa (`.xml`): `@register("", "BCAD (xml)", key="bcad", exts=(".xml",), by_ext=False)` — kengaytma bo'yicha avtomatik tanlanmaydi,
   faqat dialog (`format`) orqali. Xato — `ValueError` (400); chegaralar (hajm, qatorlar) importerning o'zida.
3. `plugins/__init__.py` oxirida `from . import <nom>` (ro'yxatga olish).
4. Parametrlar: `CATALOG["imos"]` ni `declare(ImportFormat(..., groups=(…), params=(IParam(…), …), help_ru=…, help_uz=…))` bilan to'ldiring
   (`IParam` = `Param` + `help_ru/help_uz`; turlar: `bool int mm float string path choice template`). Plagin ichida: `import_formats.option("kalit", standart)` —
   dialogdan tashqarida (eski `/projects/import-file`) standart qaytadi, shuning uchun eski xulq buzilmaydi.
5. Testlar: `tests/test_import_<nom>.py` — namuna (sintetik) fayl bilan; `test_w18_import.py` dagi `fake_plugin` namunasi reestr/dialog yo'lini ko'rsatadi.
6. `docs/mebelix/` da format hujjati (qaysi maydon qayerga tushadi; taxminlar konstanta orqasida + savollar).

### 1.5 Profillar (IMP-004) va fayl (IMP-006)
Profil = nom + format + **standartdan farqli** parametrlar (siyrak; IMP-004: «belgi qo'yilgan parametr standartni bekor qiladi»). «Восстановить стандартные» —
hamma qiymat standartga (profil o'zgarmaydi, «Сохранить» bosilguncha). Shu nomli profil bor bo'lsa — almashtirish so'raladi (dublikat yo'q).
Fayl: JSON `{app, kind:"import_profiles", version:1, profiles:[{name, format, params}]}` yoki XML `<importProfiles><profile name format><param key type value/></profile></importProfiles>`;
yuklashda xato profil `invalid` ga yoziladi (qolganlari yuklanadi); nom to'qnashuvi — `replace` (standart) | `rename` («nom (2)») | `skip`.

### 1.6 `.project` parametrlari (hozirgi yagona real importer)
| Kalit | Tur / standart | Ma'nosi |
|---|---|---|
| `import_xnc`, `import_o`, `import_sp`, `import_cl`, `import_lb` | bool / `true` | shu turdagi operatsiyalar import qilinadi; o'chirilsa — o'tkazib yuboriladi, har tur uchun bitta ogohlantirish («… по параметрам импорта: N») |
| `cl_negative_length` | `uncomputed` \| `abs` / `uncomputed` | CL detalida manfiy `l`: `length = 0` + ogohlantirish (standart) yoki `|l|` (**taxmin**, `T_W11_CL.md` §4) — `cl_import.CL_NEGATIVE_LENGTH_MODE` ni parametrga ulaydi |
Boshqa import konstantalari (`BUSINESS_M_THRESHOLD`, SP tomoni va h.k.) parametr qilinmadi — hujjatda yo'q ma'noni «sozlama» qilib ko'rsatmaslik uchun.

## 2. UI (IMP-005)
`Проект → Импорт из других программ`: chapda formatlar (ikonka, nom, kengaytma, `модуль есть` / `нет модуля`), o'ngda tanlangan format: sarlavha, «Справка» (format va har parametr tavsifi),
profil paneli (tanlash, saqlash, yangi, nomini o'zgartirish, o'chirish, «Восстановить стандартные», eksport JSON/XML, profillarni import), `ParamGrid` (W7 komponenti, o'zgarganlari belgilanadi, har biri alohida qaytariladi),
«Выбрать файл и импортировать». Modulsiz formatda jadval o'rniga sariq ogohlantirish (`data-testid="imx-nomodule"`).
`data-testid`: `import-other`, `imx-list`, `imx-fmt-<kalit>` (`data-status`), `imx-pane`, `imx-help-btn`, `imx-profile`, `imx-profile-save|new|rename|delete`, `imx-reset-all`, `imx-export(-json|-xml)`, `imx-import-profiles`, `imx-grid`, `imx-run`.

## 3. Excel import: W3 «Qilinmadi» bandlari (`services/import_v2_w18.py`, `import_v2.py` — kichik Edit)

Konfiguratsiya (`ExcelImportConfig`) ga qo'shildi: `simple`, `materials`; `parts` ga `linear_no_width`, `target_cl`, qo'shimcha ustunlar. Yangi tablar yoqilgan va `parts` berilmagan bo'lsa — «Детали» o'chiq (`model_validator`).
Tartib: «Изделия» → «Материалы» → «Детали» → «Простые операции» (Материалы detallardan oldin: «Материал» ustuni shu operatsiyalarni topadi).

| Band | Qoida |
|---|---|
| **«Простые операции»** (XLS-013/017) | `simple.map`: `code name unit qty price` + ixtiyoriy `operation` (qiymat bo'yicha alohida O), `product` (egasi; topilmasa — ogohlantirish, egasi = loyiha). Qatorlar `o_ops.parse_rows` ga (buferdan qo'yish bilan bir xil qoidalar: «2 шт», «1 200,5», sarlavha qatori, ≤ 5000 qator, yaroqsiz qator `skipped` da `tab="simple"`). `op_name` (standart «Комплектация»); `target_op` — mavjud O ga qo'shish |
| **«Материалы»** (XLS-012) | `materials.map`: `code name kind thickness length width price`. Katalogdan (kod, so'ng nom — aniq, harf farqsiz) topiladi → turi katalogdan: `sheet→CS`, `edge→EL`, `surface→SP`, `linear→CL`; parametrlar `main._new_operation` orqali (katalog narxi, qalinlik, list o'lchami). Katalogda yo'q: `create_missing` (standart ✓) — qator ustunlari bilan, turi `kind` ustunidan yoki `default_kind`; ogohlantirish. Allaqachon bor operatsiya (kod/nom) qayta yaratilmaydi (`materials_existing`). Tur tanilmasa / son noto'g'ri — qator `skipped` (`tab="materials"`) |
| **(SP)** | `sp_front`, `sp_back` ustunlari: matn = SP kodi/nomi → `sp_ops.find_or_create` + `sp_ops.attach` (lits / orqa). Yangi SP — ogohlantirish |
| **(GR)** | `gr_top gr_bottom gr_left gr_right`: matn = GR kodi/nomi (mavjud yoki `gr_defaults` bilan yangisi) → `groove_<tomon>` (tomoni lits). «-» / «нет» — yo'q |
| **(XNC)** | `xnc1`, `xnc2`: matn = shablon kodi: `lib:<kalit>`, `u:<id>`, foydalanuvchi shablon nomi, o'rnatilgan shablon kaliti/nomi (ru/uz). Topilsa — **detalga yangi XNC operatsiyasi** (shablon dasturi + `par_values`, `xnc_part_id`, `Part.xnc_op_ids`), kodi `<mahsulot kodi>_<detal kodi>` (ikkinchisiga `-2`; loyihada noyob: `-2`, `-3`…); o'lchamlar `sync_xnc` dan. Topilmasa — **bir marta** ogohlantirish (qator raqami bilan) |
| **погонаж** (XLS-005) | `parts.linear_no_width` (standart ✗ — eski xulq: eni bo'sh qator tashlanadi): eni bo'sh qator CL operatsiyasiga: «Материал» ustuni bo'yicha (nom/kod, katalog `linear`), bo'sh bo'lsa `target_cl` → birinchi CL → yangi «Погонаж». Eni = 0 (polosa eni), kromka ustunlari ishlaydi, o'lcham rejimi o'tkazilmaydi, (SP)/(GR)/(XNC) ustunlari e'tiborsiz |
| Profil (`excel_import`) | yangi `simple`, `materials`, `parts.linear_no_width`; «CL uchun ustun profili» = shu profil (CL xaritasi: Длина, Кол, Ов… + `linear_no_width`); `target_*` profilga yozilmaydi (loyihaga xos) |

Chegaralar: yangi operatsiyalar `MAX_NEW_OPS` (100) ga kiradi; SP/GR — 100, XNC — `MAX_NEW_XNC` (5000); aks holda `ImportConfigError` (400). Hisobotda: `created_o`, `simple_rows`, `materials_added/existing`, `linear_imported`, `linked{sp,gr,xnc,xnc_new}`.
`importers.assign_edge_style` — `_new_edge` dan ajratildi («Материалы» tabi ham foydalanadi).

### 3.1 Ildiz kategoriyalar serverda (CAT-002)
`import_settings.catalog_roots = {sheet, linear, edge, surface}` — `PUT /settings/import_settings/default`. «Товары → Импорт» dialogi ochilganda serverdagini yuklaydi (yo'q bo'lsa — brauzerdagi eski qiymat),
muvaffaqiyatli importdan keyin serverga yozadi; `POST /catalog/import` da `roots` berilmasa — serverdagi ishlatiladi (berilsa, so'rovdagisi ustun, `{}` — ildizsiz).

## 4. Mayda bandlar
- **Loyihalar ro'yxatida «№»** (OL-007): ko'rinadigan qator raqami (`colId: "n"`; saralashdan keyin qayta hisoblanadi); «ID» — buyurtma raqami.
- **Stanok sozlamalari: etiketka shabloni havolasi** (W7, F4Classic va KDT XML «Открыть»): `pp_machine_schema` da yangi tur `template` (`""` | `builtin:<kalit>` | `profile:<id>` — faqat havola, server shablonni o'qimaydi);
  F4Classic va KDT XML «Этикетки» guruhida `label_template`. UI: `LabelTemplateField` — W4 kutubxonasidan tanlash (`GET /label-templates`, `LabelsPanel` dagi ro'yxat) + «Открыть» — namuna ma'lumotda ko'rinish
  (`POST /label-templates/preview`); shablon o'chirilgan bo'lsa — ogohlantirish. W15 vizual redaktori bilan bog'lanish keyin (bu yerda faqat tanlovchi + ko'rinish). Shablon konteksti: `machine.params.label_template`.
- **«Что нового»**: `i18n_w6.py::_WN` ga v2.3 yozuvi (W7–W14 + W18: 13 band, ru/uz).

## 5. Qarorlar (bitta joyda o'zgaradi)
| Qaror | Joy |
|---|---|
| Profil siyrak (faqat farqlar); faylda hamma qiymat | `import_formats.sparse`, `export_json` |
| Profil nomi to'qnashuvi: faylda `replace`, UI da tasdiq bilan almashtirish | `api_import_w18.profiles_import`, `ImportDialog.saveNew` |
| `.project` parametrlari faqat haqiqatan ishlatiladiganlar | `import_formats.CATALOG["project"]` |
| Excel `linear_no_width` standarti ✗ (eski xulq buzilmasin) | `import_v2.PartsTab` |
| Materials: katalogda yo'q → yaratish (standart ✓) | `MaterialsTab.create_missing` |
| XNC shablon qidiruv tartibi: `lib:`/`u:` → foydalanuvchi nomi → o'rnatilgan kalit/nom | `import_v2_w18.resolve_template` |
| `template` turi faqat havola | `pp_machine_schema._TPL_REF` |

## 6. Qilinmadi
- **Haqiqiy CAD importerlari** (PRO100, Imos, Базис xml/obl, BCAD, Woody2, WoodWop, iLENIA): namuna fayl yo'q — ro'yxatda `no_module` (talab shu edi).
- «Материалы» tabi ustun tarkibi GibLab yordamida yo'q (XLS-012 «❓») — katalog bo'yicha qidiruv + qator qiymatlari (yuqoridagi taxmin).
- (SP)/(GR) uchun orqa tomon/«Лицевая» belgisini ustun qiymatidan o'qish (GR tomoni har doim lits), mavjud XNC operatsiyasini kod bo'yicha bog'lash (faqat shablondan yangisi).
- Katalogda rasm zip-yuklash, katalogni qo'lda tahrirlash (W3 ro'yxatida qolgan).
- Format-spetsifik «Справка» parametrlari modulsiz formatlar uchun (parametrlar modul bilan keladi).

## 7. Foydalanuvchiga savollar
1. Namuna fayllar (PRO100/Imos/BM xml-obl/BCAD/Woody2/WoodWop/iLENIA) — qaysi biri birinchi? Usiz importer yozilmaydi.
2. Excel «Простые операции»/«Материалы» namunasi (GibLabda ustun tarkibi hujjatsiz) — mijoz fayli bilan tekshirish kerak; hozirgi ustunlar tasdiqlansinmi?
3. Excel: «Ширина» bo'sh qator GibLabda **doim** CL ga tushadi — bizda `linear_no_width` o'chiq (eski xulq). Standart ✓ qilinsinmi?
4. XNC ustunidagi kod GibLabda aynan nimani bildiradi (shablon kodi / mavjud XNC operatsiyasi kodi)? Hozir — shablon.
5. `.project` importida CL manfiy uzunlik `abs` varianti qoldirilsinmi (hozir parametr, standart `uncomputed`)?
6. Etiketka shabloni havolasi stanok postprotsessorida qanday ishlatiladi (shablon konteksti `machine.params.label_template` yetarlimi, yoki shablon ichidagi maydonlar ham kerakmi)?
