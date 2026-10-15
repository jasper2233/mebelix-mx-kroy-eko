# T. W16 — (CN) «Нестинговый раскрой» (kontur detallarni listga zich joylash)

Sana: 2026-10-02 · Holat: backend + UI + testlar · Asos: `giblab_inventory/05_import_buyurtma_yangilanishlar.md` (UPD-001…004, 011, 012, WP-I).
**GibLabda CN uchun yordam sahifasi yo'q** (u yerda ham «!ТЕСТ!» beta) — algoritm, parametrlar va xulq-atvor **noldan, bizning qarorimiz**; har bir taxmin bitta
konstanta / parametr orqasida va §8 savollarida. Yangilanish jurnali (UPD-001…004) faqat nimaga e'tibor berishni aytadi: qoldiqlarni hisobga olish (detalsiz
joyda va detal ichki kesimlarida), etiketka o'rnini ishlovsiz joydan topish, kartani qo'lda tahrirlash (yopishtirib ko'chirish, burish), saralash.

## 1. Nima qilindi
| Qatlam | Fayl |
|---|---|
| Model | `models.py`: `CNParams`, `CN_DEFAULTS`, `Operation.cn`; `Placement` (+ `angle`, `outline`, `holes`, `label`), `Offcut.in_part`, `CuttingResult.kind="nest"` + `nest`; `PrintSettings.cn_*` (6 ta) |
| Geometriya | `services/cn_geometry.py` — poligon amallari, yoylar (xato ≤ `arc_tol`), XNC konturidan shakl (`part_shape`), ichki konturlar, burish, **ofset** (`offset_ring`), xavfsiz chegaralar |
| Optimizator | `services/cn_nest.py` — raster «pastki-chap» nesting (numpy; shapely/scipy yo'q), deterministik `fast/normal/max`, vaqt himoyasi, to'xtatish, progress |
| Tekshiruv | `services/cn_validate.py` — **mustaqil** aniq-geometriya tekshiruvchi (`validate_cn`, `check_polys`) |
| Bo'sh joy | `services/cn_free.py` — qoldiq to'rtburchaklar (detal ichki kesimlarida ham), etiketka o'rni |
| Hisob | `services/cn_calc.py` — kroy elementlari, natija yig'ish, qoldiqlar, narx, ombor talabnomasi, MES, eskirish qoidalari |
| Tahrir | `services/cn_editor.py` — CNE: ko'chirish / yopishtirish (chet, nuqta) / burish / o'chirish / qo'yish / qayta joylash, `result_rev` |
| Fon vazifasi | `services/cn_jobs.py` (+ `api_cn.py`: `cn/jobs`) — uzoq hisob UI ni bloklamaydi: progress, to'xtatish, eskirgan natija himoyasi |
| Chop | `services/cn_render.py` (SVG karta + hisobot bo'limi), `cn_labels.py` (ru/uz matnlar), `render.py` ga 3 ta kichik Edit |
| Postprotsessor | `services/cn_post.py` (+ `postprocessors.context_cn`, `run_builtin`): `json / csv / dxf / commands`; stanok formati YO'Q |
| Xabarlar | `services/cn_messages.py` (`i18n.MSG` ga qo'shiladi; umumiy `i18n.py` ga tegilmadi) |
| API | `api_cn.py`: `cn-quantities`, `cn-shapes`, `cn-edit/rev`, `cn-validate`, `cn/jobs` (POST / GET / DELETE) |
| UI | `frontend/src/features/cn/*`: `CnPanel` (4 tab: Параметры · Детали · Листы и остатки · Раскрой), `CnParams` (30 ta `?` yordam, narx / material miqdori, hisoblangan min. masofa), `CnParts` («Форма» ustuni, kichik kontur chizmasi, Excel Ctrl+V), `CnSheets` (L × W tahrirlanadi, qoldiq-listlar, natija qoldiqlari «Д5⊂3»), `CnCut` (**fon vazifasi + progress + «Остановить»**, holat qatori, miniatyuralar, omborga yozish, postprotsessor), `NestMap` (SVG: kontur / ichki kesim / qoldiq / etiketka o'rni, masshtab va siljitish), `CnEditor` (CNE), `cnHooks.ts`, `cnGeom.ts`, `cn.css`; `scripts/i18n_cn.py` (ru / uz); umumiy fayllarda kichik Edit: `types.ts`, `opmeta.tsx`, `ProjectView.tsx`, `OperationsTable.tsx`, `Print.tsx` («(CN)» bo'limi), `hotkeys.ts`, `CsSheets.tsx`, `PartDialogs.tsx` |
| Umumiy fayllarga kichik Edit | `main.py` (tur, `_need_cut`, `_new_operation`, optimize / edit / result / svg tarmoqlari, eskirish), `calc.py` (`recalc_project`, `warehouse_request`, `product_costs`, EL / GR / SP tuplelari), `warehouse.py` (`commit`), `mes.py`, `order_flow.py`, `api_cs_w2.py`, `settings.py` (`cn_defaults`), `render.py`, `postprocessors.py` |
| Testlar | `tests/test_cn_w16_{geometry,nest,validate,editor,calc,api}.py` + `cn_w16_util.py` (mustaqil skalyar tekshiruvchi), `cn_w16_proj.py` |

CN operatsiyasi **CS bilan bir xil tuzilmada**: `parts`, `sheets` (ustuvorlik tartibida; qoldiq-listlar `RemnantPicker` bilan), `result: CuttingResult`. Shuning uchun ИК/Ост hisobi,
ombor (`commit` / `rollback`, «Исп. кол-во»), rezerv, MES, `.mxk.json`, undo/redo umumiy kod bilan ishlaydi.

## 2. Qarorlar jadvali (hammasi parametr / konstanta orqasida)
| № | Qaror | Qayerda | Asos |
|---|---|---|---|
| 1 | Detallar orasidagi talab etilgan masofa `spacing = max(D, 2·ofset) + part_gap` (D — asbob diametri, ofset — asbob markazining konturdan masofasi, standart D/2); tekshiruv va nesting `spacing + arc_tol` ishlatadi | `CNParams.spacing`, `cn_calc.spacing_of` | asbob ikki detal orasidan o'tadi; yoy xatosi zaxirasi |
| 2 | List chetidan masofa `margin` (standart 5 mm): kontur foydali zonada | `CNParams.margin` | qisqich / ishonchlilik; taxmin |
| 3 | Detal shakli = bog'langan XNC dasturining **yopiq, teshib o'tuvchi** konturlari: o'lchamning ≥ 90 % ini egallovchi eng katta kontur — tashqi chegara, uning ichidagilari — ichki kesimlar; tashqi chegara bo'lmasa — to'rtburchak L×W va konturlar uning ichidagi kesimlar; yopiq kontur yo'q — oddiy to'rtburchak | `cn_geometry.OUTLINE_COVER`, `shape_from_contours` | XNC `MillStart…Mill*`, `MillRect`, `MillEllipse` |
| 4 | **Dasturlangan kontur = tayyor detal chegarasi** (freza korreksiyasi C = 0/1/2 e'tiborga olinmaydi) | `cn_geometry` | ❓ §8-1 |
| 5 | Kontur «teshib o'tadi» agar chuqurlik ≥ qalinlik − 0.5 mm va cho'ntak (C = 3) emas; cho'ntaklar va ochiq konturlar shaklga ta'sir qilmaydi (ochiq kontur — ogohlantirish) | `THROUGH_TOL`, `CLOSE_TOL` | |
| 6 | Yoylar siniq chiziqqa **ichki** (inscribed) `arc_tol` (0.25 mm; ≤ 1 mm) xato bilan; xato `spacing` ga qo'shiladi (haqiqiy detallar ham ≥ spacing) | `CNParams.arc_tol` | |
| 7 | Burchak: musbat — ekranda soat mili bo'yicha (Y pastga, XNC «Поворот» kabi). Ruxsat: `rot90` (0/90/180/270) va `rot_step` (erkin qadam, 0 — o'chiq). Ткт ✓ detal (va `use_grain`) — faqat 0°/180°. **Ko'zgu yo'q** | `cn_nest.allowed_angles`, `cn_validate.angle_ok` | |
| 8 | Qoldiq — detalsiz **to'rtburchak** (shu jumladan detal ichki kesimida: `Offcut.in_part = detal uid`); har qoldiq detaldan va boshqa qoldiqdan ≥ spacing; tomonlar ≥ `remnant_min_side1/2`, maydon ≥ `remnant_min_area` — деловой. Xom o'lcham — list chetigacha kengaytirilgan | `cn_free.free_rectangles`, `CNParams.remnant_*` | UPD-001; ❓ §8-3 |
| 9 | Narx: CS bilan bir xil (list / m², yaxlitlash kodlari, 4 asos: **kesim uzunligi = konturlar perimetri** (tashqi + ichki), detal perimetri, detal maydoni, material maydoni; kroygacha `Σ maydon × (2 − p/100)`, standart p = 80 %) | `cn_calc.cn_cost` | |
| 10 | F = detallar **sof** maydoni (teshiklar ayriladi) ÷ (list − деловой qoldiqlar) | `finish_result` | CS dagi qoida |
| 11 | Kroy natijasi saqlanishdan oldin `validate_cn` dan o'tadi; o'tmasa `RuntimeError` (nesting xatosi — foydalanuvchiga noto'g'ri natija ko'rsatilmaydi) | `cn_calc.run_nesting` | |
| 12 | Vaqt byudjeti deterministik (sinovlar soni), vaqt chegarasi (`time_limit_s`; `fast` 3 s / `normal` 10 s / `max` 40 s) faqat himoya: oshsa shu paytgacha eng yaxshi natija + ogohlantirish | `cn_nest.QUALITY` | |
| 13 | Etiketka o'rni: detal ichida kontur chetidan va ishlov (teshik, freza yo'li, paz) dan ≥ 3 mm uzoq eng katta bo'sh to'rtburchak; etiketka (standart 40×20) sig'sa — uning markaziga; sig'masa — `label=null`, `fits=false` | `cn_free.find_label_spot`, `LABEL_CLEAR` | UPD-002 «oddiy variant» |
| 14 | «Сортировка» (UPD-004): `sort_mode = list` — detallar «Детали» jadvali tartibida joylanadi; `auto` — optimizator o'zi tanlaydi | `CNParams.sort_mode` | jadvalni saralash umumiy (`parts/sort`) |
| 15 | Hajm chegarasi: bitta kroyda ≤ 5000 detal nusxasi (`MEBELIX_MAX_NEST_ITEMS`); kontur nuqtalari ≤ 600 (halqa) / ≤ 3000 (detal); ichki kesimlar ≤ 200; juda murakkab kontur — to'rtburchak + ogohlantirish | `cn_calc.MAX_NEST_ITEMS`, `cn_geometry.MAX_*` | |
| 16 | Fon vazifalari jarayon xotirasida (bir jarayonli o'rnatish); tugagan vazifalar 15 daqiqadan keyin tozalanadi; natija loyiha kirishi (`input_rev`) o'zgarmagan bo'lsagina qo'llanadi | `cn_jobs` | UI bloklanmasin |

## 3. Algoritm (`cn_nest.py`) — raster «pastki-chap»
1. **Katak.** Foydali zona (list − `margin`) `c` mm li kataklarga bo'linadi (`c` — maqsadli kataklar soniga qarab 1…16 mm: `fast` ≈ 70 k, `normal` ≈ 220 k, `max` ≈ 600 k; faqat to'rtburchaklar bo'lsa ×2; mayda detallar bo'lsa ×2).
2. **Niqob.** Har detal-burilish uchun *konservativ* niqob: detal bilan kesishgan har bir katak (juft-toq qoidasi bilan ichki kesimlar bo'sh; chegara kataklari ham kiradi). To'rtburchak 90° karrali burilishda — aniq blok.
3. **Masofa.** Joylangan detal niqobi `spacing` masofali **kvadratlar-masofasi yadrosi** bilan kengaytirilib band xaritaga qo'shiladi (`dilate`). Ikki niqob yadro bo'yicha kesishmasa — haqiqiy konturlar orasidagi masofa ≥ spacing (isbot: `cn_nest.py` modul izohida). **Shuning uchun to'g'rilik raster aniqligiga bog'liq emas** — faqat zichlik.
4. **Joylash.** Detal (katta → kichik) har ruxsat etilgan burchakda sinab ko'riladi; mumkin bo'lgan **barcha** o'rinlar xaritasi hisoblanadi (to'rtburchak niqob — integral tasvir, umumiy shakl — FFT korrelyatsiyasi `numpy.fft`, keyin aniq tekshiruv); eng «chap-yuqori» o'rin tanlanadi (kalit: o'rovchi to'rtburchak oxiri, so'ng ikkinchi koordinata). Kichik detallar ichki bo'shliqlarga o'zi tushadi (ular eng chapdagi mumkin o'rin).
5. **Sinovlar.** Tartib (maydon / uzun tomon / bbox / perimetr / ro'yxat), to'ldirish o'qi (uzun / qisqa tomon), burilish afzalligi (avto / yotiq / tik), urug'li tasodifiy o'zgarishlar. `fast` — 3 sinov, `normal` — 8, `max` — 20; eng yaxshisi `(sig'magan, list maydoni, oxirgi list band qismi)` bo'yicha. Listlar soni quyi chegaraga (⌈Σ sof maydon / foydali maydon⌉) yetsa to'xtaydi.
6. **Bir xil listlar.** Ketma-ket bir xil sxemali listlar `copies` bilan bitta kartaga birlashtiriladi (avtomatik hisobga teng, vaqt tejaydi).
7. **Ro'yxat tartibi / qoldiq-listlar.** `op.sheets` tartibi = ustuvorlik (CS dagi qoida): har list turi `qty` gacha ishlatiladi; hech narsa sig'maganini keyingi turga o'tadi.

Natijalar (shu mashinada, 16 mantiqiy yadro; `tools/bench` ga kiritilmagan — CS optimizatoriga TEGILMAGAN):
| Misol | Sifat | Vaqt | Izoh |
|---|---|---|---|
| 50 xil to'rtburchak (93 ta, 2750×1830) | fast / normal / max | 0.4 / 2.4 / 22 s | 4 list (CS optimizatori ham 4); birinchi 3 listning to'ldirilishi ≈ 89–90 % (CS: 91–96 %) |
| 120 xil to'rtburchak (~420 ta) | fast / normal | 2.0 / 8.6 s | 11 list (F 81 %) / 10 list (F 89.6 %) |
| 40 / 60 aralash kontur (doira, L, teshikli, yumaloq teshikli) | normal | 2.8 / 7.5 s | to'g'rilik 100 % (mustaqil tekshiruv); skript: 	ools/bench/cn_bench.py |
| 15 xil kontur, erkin burchak 30° (12 yo'nalish) | normal | 5.5 s | |

**Ochiq cheklovlar.** (a) Raster: zichlik katak o'lchamiga bog'liq (odatda ≤ 1–2 % maydon yo'qotish; kichik detallar ko'p bo'lsa ko'proq); (b) NFP / «sirpanish» yo'q — detal faqat panjara nuqtalarida; (c) umumiy chiziq bo'ylab kesish (common-line) yo'q; (d) ko'prikchalar (перемычки), kirish / chiqish yoyi va kesish tartibi hisobga olinmaydi (postprotsessor sohasi); (e) erkin burchak ko'p vaqt oladi (`rot_step` × detal turlari); (f) fon vazifalari bir jarayonda (GIL: hisob davomida boshqa so'rovlar sekinlashadi); (g) qoldiqlar faqat **to'rtburchak**; (h) 3000 nuqtadan murakkab kontur to'rtburchak bo'ladi; (i) «Исп. кол-во» kaliti faqat o'lcham bo'yicha (umumiy `warehouse.rem_key`): bir xil o'lchamli «detal ichidagi» va oddiy qoldiq jadvalda bitta qatorga yig'iladi; (j) fon vazifasining birinchi sinovi `4 × vaqt chegarasi` gacha cho'zilishi mumkin (keyingilari — chegarada to'xtaydi); (k) `CnParts` da Excel import oynasi (`ExcelImportDialog`) va ustunlar sozlamasi (Ctrl+P) yo'q — faqat Ctrl+V.

## 4. Shakl (`cn_geometry.py`)
- `Shape(outer, holes, kind, marks, warns)`: tashqi kontur musbat, ichki manfiy imzo; bbox burchagi (0,0); `area` (sof), `perimeter`, `bbox_size`.
- XNC: `xnc.machine_program` (burilish 0 ga majburlangan — shakl detalning o'z holatida) amallaridan `mill_start / mill_line / mill_arc` ketma-ketligi, `rect`, `ellipse` yig'iladi; yopiq (`CLOSE_TOL` 0.1 mm), teshib o'tuvchi konturlar tanlanadi.
- `offset_ring(ring, d, tol)`: konturni materialdan tashqariga `d` ga siljitadi (yumaloq burchak, o'zaro kesishuvlar olib tashlanadi; ichki kontur — teshik ichiga). Formula bilan tekshirilgan (to'rtburchak `A + P·d + πd²`, L-shakl, doira, teshikning yopilishi). Asbob yo'li ma'lumoti uchun (`tool_path`), nesting masofalari unga bog'liq emas.
- Ogohlantirishlar (`cn.w_*`): ochiq kontur, kontur detaldan tashqarida, XNC o'qilmadi, o'lcham farqi, murakkablik.

## 5. API
| Yo'l | Vazifa |
|---|---|
| `POST /projects/{pid}/operations {type:"CN"}` | yangi operatsiya (`cn_defaults` + 2750×1830 list) |
| `PATCH …/operations/{oid} {cn:{…}}` | parametrlar; natijani eskirtiradiganlari (`cn_calc.CN_NON_CUT` dan boshqasi) natijani o'chiradi |
| `POST …/optimize?quality=` | sinxron kroy (API / MES uchun) |
| `POST …/cn/jobs?quality=` · `GET …/cn/jobs/{id}` · `GET …/cn/jobs/current` · `DELETE …/cn/jobs/{id}` | **fon vazifasi** (UI): `{state: running|done|error|cancelled, progress, elapsed_s, error, result}`; 409 — band; natija tugaganda loyihaga yoziladi (bitta undo qadami); `current` — sahifa qayta yuklansa ketayotgan vazifani topish (yo'q — `null`) |
| `GET …/cn-quantities` · `cn-shapes` · `cn-validate` · `cn-edit/rev` | miqdorlar va narx · detal shakllari / etiketka o'rni · saqlangan natijani tekshirish · tahrir izi |
| `POST …/edit {result, action}` · `PUT …/result?base=` | CNE (amallar: `cn_editor.py` boshidagi hujjat); 409 — natija boshqa oynada o'zgargan; mijoz konturlari **ishonilmaydi** (serverda qayta hisoblanadi) |
| `GET …/maps/{i}.svg` · `GET /projects/{pid}/report` | server SVG karta; hisobotda «(CN)» bo'limi (`PrintSettings.cn_*`) |
| `GET …/postprocess?key=json\|csv\|dxf\|commands` yoki `profile_id` (Jinja shablon) | `context_cn` (qarang `cn_post.py`) |
| `…/remnants`, `…/remnants/commit\|rollback`, `…/sheets/from-remnants`, `PUT …/result/taken`, `GET /remnants` | umumiy ombor mexanizmi (CN uchun qoldiq — listli, `linear=false`) |

## 6. Qo'lda tahrir (CNE, UPD-003)
Amallar: ko'chirish (`move dx, dy`), **yopishtirib** ko'chirish — `slide` (4 yo'nalishda qo'shni detal / list chetigacha: «chet bo'yicha») va `snap` (tanlangan detal uchi → nishon uchi, to'siq (masofa qoidasi) uchragan joyda to'xtaydi: «nuqta bo'yicha»), `rotate` (90° qadam yoki erkin burchak; guruh — markaz atrofida), `remove`, `place` (joylanmagan nusxani berilgan joyga), `auto_place` (eng chap-yuqori mumkin o'rinaga), `renest` (karta + joylanmaganlarni qaytadan joylash; yomonlashsa — rad), kartalar (`add_map / delete_map / copies / comment / move_map`). Har amal serverda **to'liq qayta quriladi** va `validate_cn` dan o'tadi: kesishish, masofa, list chetidan masofa, burchak qoidasi (Ткт), soni — buzilsa 422 va qoralama o'zgarmaydi. Undo/redo — mijozda (qoralamalar stack i). Saqlash — `PUT result?base=` (409 himoyasi, W13 `result_rev` namunasi).

## 7. Postprotsessor, eksport, import
- `postprocessors.context_cn` / `cn_post.context_cn`: `project, op, tool{diameter, radius, offset}, maps[{placements[{uid, x, y, angle, length, width, outline, holes, tool_path{outer, holes}, label}], remnants[…]}], parts[…], f, now`. **Stanok G-code formati o'ylab topilmagan** — korxona dasturchilari shablonda yozadi (`machine=None`; stanok sozlamalari `pp_machine_ctx` CN uchun ulanmagan).
- O'rnatilgan formatlar: `json` (to'liq kontekst), `csv`, `dxf` (qatlamlar: SHEET, PARTS, HOLES, TOOLPATH, REMNANT, TEXT), `commands` (operator uchun matn).
- `.project` **eksporti**: CN o'tkazib yuboriladi va ogohlantiriladi (`op_skipped`; formatda CN atributlari tavsiflanmagan). **Importda** CN operatsiyasi (real korpusda yo'q) ogohlantirish bilan o'tkazib yuboriladi. Faqat bizning `.mxk.json` da saqlanadi (natija konturlari bilan; sinab ko'rilgan).
- Eski JSON: `cn` / `nest` / `angle` / `outline` maydonlari yo'q bo'lsa — standart qiymatlar (sinab ko'rilgan).

## 8. Savollar (foydalanuvchiga)
1. **Freza korreksiyasi.** XNC dasturidagi kontur **tayyor detal chegarasi**mi (hozir shunday) yoki asbob markazining yo'limi (C = 0)? Qaysi kontur «tashqi» ekanini 90 % qoidasi bilan topamiz — korxona dasturlarida bu mos keladimi? (Namuna XNC bilan nesting kerak.)
2. **Ko'prikchalar / kesish tartibi / kirish yoyi.** Detal kesib bo'lingach siljib ketmasligi uchun ko'prikchalar (перемычки), ichki konturlarni birinchi kesish, kirish / chiqish yoyi — bularni `context_cn` ga qo'shishmi (hozir faqat toza kontur va asbob yo'li)?
3. **Qoldiq qoidalari.** CN da qoldiq to'rtburchakmi (hozir shunday), standart chegaralar 300 / 150 mm va 0.1 m² (CS da 1000 / 500 / 0.5) to'g'rimi? Detal ichki kesimidagi qoldiq omborga yozilsinmi (hozir деловой bo'lsa yoziladi)?
4. **Masofa qoidalari.** Detallar orasidagi minimal masofa = asbob diametri + qo'shimcha (hozir 6 mm + 0); list chetidan 5 mm — korxona qiymatlari? Umumiy chiziq bo'ylab kesish (ikki detal orasida bitta o'tish) kerakmi?
5. **GibLab CN.** Onlayn GibLabda CN beta — namuna `.project` / skrinshot (parametrlar, karta ko'rinishi, qo'lda tahrir) bersangiz xulqni moslaymiz; hozir hammasi taxmin.
6. **Postprotsessor (UPD-012: KDT GCode nesting uchun).** Qaysi stanok (KDT, Excitech, Biesse …) va namuna fayl — shablon ulash uchun.
7. **Etiketka.** Detal etiketkasi (W4 `LB`) CN detallar uchun chop etilmaydi (W4 modullari tegilmadi): etiketka shabloniga CN kartasidagi detal o'rni (`label`) ni ulashmi?
8. **Hajm.** Bitta kroyda ≤ 5000 nusxa, kontur ≤ 600 nuqta — ish uchun yetarlimi? `fast/normal/max` vaqtlari (3 / 10 / 40 s) mos keladimi?

## 9. Boshqa paketlarga ta'siri
- **W2 / W13 (CS):** `api_cs_w2._cut` (qoldiq «Исп. кол-во» CN da ham), `warehouse.commit` (CN qalinligi). CS kodi o'zgarmagan; `optimizer.py` / `colpack.py` ga TEGILMAGAN.
- **W6 / W12 (EL, GR, SP):** CN detallari ham kromka / paz / sirt ishlovi hisobiga kiradi (`calc.py` dagi `(CS, CL)` tuplelariga `CN` qo'shildi, `product_costs` ham).
- **W1 / W8 (XNC):** `calc.sync_xnc` CN qalinligini (`cn.thickness`) ishlatadi; `main.add_xnc_for_part` ham. XNC modulining o'zi o'zgarmagan (`machine_program` chaqiriladi).
- **W10 / W9:** `.project` eksporti CN ni o'tkazib yuboradi (avvalgidek); importda ogohlantirish (avvalgidek).
- **W4 (etiketka):** CN ulanmagan (§8-7). **W14:** `order_flow.warnings_for` CN ni ham hisobga oladi. **MES:** `mes.export` CN bo'limi.
- `render.T` ga `CN_T` qo'shildi (ru / uz). Umumiy `i18n.py` ga tegilmadi (`cn_messages.py` ro'yxatdan o'tkazadi).
