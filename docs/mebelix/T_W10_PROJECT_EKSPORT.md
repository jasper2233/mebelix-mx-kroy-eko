# T_W10. `.project` eksporti, CS «Максимальное количество вращений» 1…6, «Минимальный размер детали» sozlamasi

Holat: 2026-10-02. Paket W10. Kod: `backend/app/services/project_export.py` (+ `project_export_xnc.py`, `project_schema.py`),
`backend/app/api_export.py`; UI: `frontend/src/features/project/ExportDialog.tsx`, `features/settings/MinPartSetting.tsx`.

## 1. Ruxsat va chegara
Foydalanuvchi (2026-10-02): `.project` eksporti ruxsat etilgan — tizim ommabop bo'lishi kerak, mijoz ixtiyori muhim; «Biz GibLab tizimini
buzmayapmiz, sertifikatiga tegmaymiz». `CLAUDE.md` 4-qoidaga istisno sifatida yozilgan. Eksport **faqat ochiq tavsiflangan format**
(yordam sahifasi «Формат файлов проектов») va foydalanuvchining o'z fayllaridagi teg/atribut **nomlariga** asoslanadi; GibLab dasturi,
kaliti, litsenziyasi, ikkilik fayllari (`.gibcut`) ishlatilmagan; GibLab ishga tushirilmadi, eksport qilingan fayl GibLabda ochilmadi.
Yordamning matni, rasmi, namuna faylini (`Example1.project`) kodga/testga ko'chirmadik — sxema jadvali o'zimiz yozgan.

## 2. Nima yoziladi (importerning teskarisi)
| MebeliX | `.project` |
|---|---|
| Loyiha | `<project name currency version="1" date orderDate description project.uuid>` |
| Mahsulot | `good typeId="product"` (`code name count phone1 phone2 description product.order product.<nom>` va importdagi `program` matni); ichida `part` lar |
| Detal | `part id name code count minusCount txt` + o'lchamlar **hammasi birdan**: `l w` (zagotovka), `dl dw` (detal), `jl jw` (prifugovkadan keyin), `cl cw` (pilniy) — loyiha rejimidagi juft aynan model qiymati; `allowanceT/B/L/R`, `groupInBlock/MC/MaxC`, `part.designation` (= tavsif), kromka `elt elb ell elr="@operation#N"`, paz `grt grb grl grr` (+ `grts…="false"` — orqa tomon) |
| CS | `good tool.cutting` (`swSawthick swSawthickDiv swPackageHeight swMaxturns swComplexBand swTrimIncludeSaw swSort swSortInBand swMinSizeBand swMaxSizeBand swMaxLengthBand swMinPruning`), `good sheet` (nom, kod, `t`, `cost`; ichida listlar/qoldiq qatorlari `part id count l w [cTrimL cTrimW cTrimEL cTrimEW description]`), `operation CS` (`cSizeMode cTrimL/W/EL/EW csDirectCut csTexture cFillRep cCPF cAllowanceWorkpiece cCostType cCostCut cCostByItem cCostByItemRound cMinDimRegWaste1/2 cBusinessWaste cTrimWaste cMinDimDetail cSaveDrawCut cCombiningParts cMaxPartsOnPattern cPrefLargePacket printable startNewPage description`) + `<material>` + `<part>` havolalari (mahsulot detallari, keyin list qatorlari) |
| EL | `good tool.edgeline` (`elCost elRestSide elMinSize elWidthPreJoint`), `good band` (`w t cost code name`), `operation EL` (`elCalcMat w t elRoundMat elRoundLength elWastePRC elSymbol elColor elLineMark elMinDimDetail`) + shu kromkali detallar |
| GR | `operation GR` (`grWidth grDepth grOffset grOffsetIncl grSawthick grCost typeName`) + pazli detallar |
| XNC | `operation XNC` (`typeName code program count side turn mirHor mirVert bySizeDetail priceBore priceMill priceCut price`) + `<part>`; `program` — §3 |
| O | `good simple` (kod, nom, birlik, `count`, `cost`) har qator uchun + `operation O` (`typeName costOperation owner`) + `<material id count>` |
| LB | `operation LB` (`printMode columns rows gap margin source printParts partEach partONZ partSelected printWastes wasteEach productEach productONZ`, `fields` = `BASE64:<fields>`, `program` = importdagi eski shablon matni yoki `LB_PROGRAM_EXPORTERS` (W9 shu ro'yxatga eksport funksiyasini qo'shadi); `program` yo'q bo'lsa — ogohlantirish) |
| SP (W12) | `operation SP` (`spCalcMat spWastePRC spRestSide spSizeMode spCost`) + shu SP li detallar (tomon formatda yo'q ❓ — §6) |

**Yozilmaydi:** kroy natijasi (`data`, `draw`, `cFilling cMaterialCount cTrimLength …`, `usedCount`), narx jami (`cost costMaterial costOperation costTotal`,
`countBore …`) — qabul qiluvchi dastur qayta hisoblaydi; formatda joyi yo'q maydonlar (buyurtmachi, holat, MES havolasi, XNC koordinata boshi
burchagi, O/GR/LB operatsiya kodi, mahsulot tayyorlik sanasi matni, SP material narxi, mahsulot «Программа» buyruqlari) — ogohlantirishlarda
sanaladi. CN (nesting) operatsiyasi o'tkazib yuboriladi (ogohlantirish); CL (pogonaj) — W11 `services/cl_export.py` (`project_export` chaqiradi).

**Qoidalar:** hamma `id` — bitta hisoblagichdan, butun loyiha bo'ylab noyob (real fayllarda tur ichida noyob; superset xavfsiz).
`version="1"`: tavsif «По умолчанию: 1», namunada ham `1`; real fayllardagi 21052101 / 23051701 — GibLab build sanalari (onlayn / lokal),
o'ylab topmadik. Konstanta `FORMAT_VERSION` (agar GibLab shu bilan ochmasa — bitta joyda o'zgaradi). `project.uuid` — har eksportda yangi UUID4.
Sana (`date`, `orderDate`) — epoch ms, mahalliy 12:00 (UTC+5). Listlar tartibi (kroy ustuvorligi) va operatsiyalar tartibi saqlanadi.
Tartib real fayllardagidek: avval hamma `good`, so'ng `operation` lar. UTF-8, BOM yo'q; XML da ruxsat etilmagan boshqaruv belgilari olib tashlanadi.
Real fayllarda `cTrimWaste` (hujjatda `cTrimWaster`) — real nom yoziladi.

## 3. XNC `program` (tool var bf bl br bt bb ms ml ma mac gr xy)
* Oddiy dastur: har buyruq o'z tegiga (`enable="false"`, `comment`, `ac/as/av`, `m`, `ver`, `ms`: `sdp sxy c in out`, `gr`: `c p`). `Par` — `var`
  (kiritilgan / standart qiymat bilan, izoh = yorliq); `Com` yozilmaydi.
* Formatda teg nomi tavsiflanmagan buyruqlar (If/Else/While/…/Sub/Call, Set, Msg, Err, MillRect, MillEllipse, MillArc3P, MillFillet, X/Y/L yozuvli paz)
  bo'lsa — dastur **«yoyilgan»** yoziladi: `evaluate()` natijasi (kiritilgan Par qiymatlari, detaldan hisoblangan o'zgaruvchilar bilan) tayyor
  koordinatali teglarga aylantiriladi (parametrika yo'qoladi, geometriya va statistika saqlanadi; 7 ta kutubxona shabloni teshik soni va freza/paz
  metri bo'yicha aynan teng). Ogohlantirish beriladi.

## 4. API va UI
* `GET /api/projects/{pid}/export/project` — `Content-Disposition: attachment` (`filename*=UTF-8''…`), `application/xml; charset=utf-8`;
  `GET …/export/project/report` — `{filename, bytes, counts, warnings[{level: warn|info, code, text}], format_version}`;
  `POST /api/projects/export/project-zip {ids}` — ko'p loyiha (ZIP, takroriy nomlar «(2)»). Eski `GET …/export` (`.mxk.json`) o'zgarmagan.
  Eksport o'z sxemamizdan o'tmasa (`validate_project_xml`, strict) — 500 (`exp_invalid`), buzuq fayl berilmaydi.
* «Проект → Экспортировать»: tanlov oynasi (`.project` / `.mxk.json`); `.project` da avval hisobot (fayl, hajm, tarkib, **nima kirmadi** ro'yxati),
  keyin «Скачать». Loyihalar ro'yxati menyusi: «Экспорт .project» (bitta — fayl, ko'p tanlov — ZIP).

## 5. Tekshiruv
* Sxema: XSD yo'q, `lxml` o'rnatilmagan → `services/project_schema.py` (teg/atribut lug'ati = hujjat ∪ real fayllar nomlari, atribut turlari, id
  noyobligi, havolalar, XNC `program` ichki XML). Real fayllar ham shu lug'atga mos (`vocabulary` / `unknown_vocabulary`).
* Testlar (yangi, 60 ta + `test_rules_v2.py` da 2 ta): `test_export_w10_roundtrip.py` (47: sintetik loyiha 3 o'lcham rejimida, hamma operatsiya turlari, XNC yoyish,
  ogohlantirishlar, sxema tekshiruvchisi), `test_export_w10_corpus.py` (5: real korpus; `GP_DIR` yo'q bo'lsa skip), `test_export_w10_api.py` (8); yordamchi: `tests/w10_helpers.py`.
* Real korpus (1248 fayl, GibLab saqlagan 945 + Bazis 303): **import → eksport → import: 1248/1248 fayl** — detallar soni va maydoni, kromka metri
  (`calc.edge_usage`), XNC `xnc-stats` (teshik, freza, paz) aynan teng; butun mazmun (id lar o'rniga tartib raqamlari) ham 1248/1248 teng. Testdagi tasodifiy
  60 ta (`GP_DIR`, `GP_N`, `GP_SEED`): 60/60. Eksport element/atribut to'plami (254 juft) real to'plam (324 juft) ning qismi; farq — faqat hujjatda bor
  atributlar (`operation[CS]/description`, `operation[LB]/typeName`). Importer kichik kengaytirildi: `date` → tayyorlik sanasi, mahsulot `phone1/2/description`,
  operatsiya `description` (CS/EL/XNC/LB), list qatori `description`.
* Importer/eksport birgalikda yo'qotadigan joylar: `ELParams.symbol` 1 belgigacha, `marker_lines` 0 → 1, `est_fill_percent` / `fill_packet` < 50 (importer
  «chiqindi ulushi» deb o'qiydi — ogohlantirish), ombor qoldig'i list qatori sifatida (`is_remnant` yo'qoladi — ogohlantirish), bitta XNC bir nechta detalga
  bog'langan bo'lsa faqat birinchisi (ogohlantirish).

## 6. Savollar / eslatmalar
1. `version="1"` GibLab (lokal/onlayn) da ochiladimi? Ochilmasa — `FORMAT_VERSION` ni build raqamiga almashtirish (bitta konstanta). Fayl **hali GibLabda ochilib ko'rilmagan**
   (ruxsat berilmagan; haqiqiy loyihalar avtosaqlanadi) — foydalanuvchi nusxada sinab ko'rsin.
2. SP tomoni (lits/orqa), mahsulot `program` teg nomlari, LB `program` tanasi — formatda tavsiflanmagan: SP — faqat «detal shu operatsiyada»; mahsulot dasturi — faqat importdagi
   matn qaytariladi; LB — faqat importdagi matn yoki W9 `LB_PROGRAM_EXPORTERS`. W9: `from app.services.project_export import LB_PROGRAM_EXPORTERS; LB_PROGRAM_EXPORTERS.append(fn)`,
   `fn(lbp: LBParams) -> str | None`.
3. Yangi operatsiya turlari: `project_export.SUPPORTED` ga tur va `_Exporter.build()` ga tarmoq qo'shiladi (W11 CL ni shunday ulagan); CN hozir ogohlantirish bilan o'tkazib yuboriladi.
4. Bir xil detal bir nechta CS da bo'lsa (importer nusxalaydi) — har nusxa alohida detal bo'ladi.

## 7. CS «Максимальное количество вращений» 1…6
`CSCutParams.max_rotations` `ge=1` (eski `ge=2`), legacy migratsiya `_fix_range(…, 1, 6)`, importer `max(1, min(6, swMaxturns))`, UI ro'yxati 1–6, yordam matni (`phelp.max_rot`).
Optimizator/validator/muharrir: `max(2, …)` → `max(1, …)`; `_make_child`: `level > max_level` bo'lsa konteyner (ichki kesim) yaratilmaydi; 1 da «ustunli» va «3 bosqichli» oilalar o'tkazib yuboriladi
(ularning daraxti baribir chuqurroq, `_depth_ok` rad etardi). 1 da faqat polosalar: detal polosani (listning foydali eni/uzunligi bo'yicha) to'liq egallashi shart, aks holda joylashmaydi (kutilgan xulq).
Benchmark (R ≥ 2 yo'li kod bo'yicha o'zgarmagan: `max(1, R) = R`, qo'shilgan shartlar R ≥ 2 da hech qachon ishlamaydi): `compare.py normal` — 1186 (avvalgi) ↔ yuklangan kompyuterda 1190
(4 kroy — #60, 93, 301, 305 — boshqa jarayonlar CPU ni band qilgani uchun vaqt byudjeti yetmadi; yolg'iz qayta yuritilganda 10, 6, 2, 2 — avvalgi bilan aynan bir xil → 1186), tekshiruv xatosi 0.
Katta korpus (`BENCH_CORPUS=corpus_big.json … big`): cheksiz listli kroylar 5584 (avvalgi) ↔ 5597 yuklangan holatda (+0.23 %, ≤ 0.3 %), xato 0; o'zgargan 17 kroy qayta yuritilganda jami 104 ↔ 104.
Testlar: `test_rules_v2.py::test_cut_levels_never_exceed_max_rotations` (1,2,3,4) va `test_one_rotation_places_only_strip_exact_parts`; `test_qa_fix_calc.py` chegaralar (0 — 422, 1 — 200).

## 8. «Минимальный размер детали»
Sozlanadi: `cs_defaults` profilida (`material.min_part_size`, standart 30 mm): CS «Параметры» da «сохранить по умолчанию» bilan, endi **«Настройки → Общие»** da ham (`MinPartSetting`:
`cs_defaults` ni o'qib-yozadi; yangi CS operatsiyalar shu qiymat bilan yaratiladi — tekshirildi). Xulq o'zgarmagan: o'lchami kichik detal kroyga kirmaydi va ogohlantirish beriladi (`calc._items_for` / `_small_warning`).
