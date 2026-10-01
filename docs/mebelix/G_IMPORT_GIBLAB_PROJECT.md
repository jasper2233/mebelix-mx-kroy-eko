# G. GibLab «.project» faylini import qilish (migratsiya + Bazis-Mebelshik)

**Nima uchun muhim:** xodimlar loyihalari GibLab'da; mahsulot xossasida `product.import = bm.1.86`
ko'rindi — ya'ni detallar **Bazis-Mebelshik** dan «GibLabExport» skripti (v1.86) orqali keladi.
Bu skript GibLab XML formatini yaratadi. Demak **shu XML ni o'qish** = (1) eski loyihalarni ko'chirish
va (2) Bazis-Mebelshik bilan hozirgi ish oqimini saqlab qolish.

Reference: `backend/app/services/giblab_project.py`, endpoint `POST /api/projects/import-giblab`, test
`test_import_giblab_project`. **Muhim:** xodimdan haqiqiy `.project` faylni olib (GibLab → Проект →
Експортировать) `backend/tests/fixtures/` ga qo'ying va test yozing — format tavsifi hujjatdan olingan.

## G1. Tuzilma (qisqa)

```
<project version currency date(ms) description costOperation costMaterial cost>
  <good id typeId=... code name ...>        ← tovarlar: mahsulot, materiallar, stanoklar
     <part id .../>                          ← mahsulot ichida — detallar; material ichida — list/qoldiqlar
  </good>
  <operation id typeId=CS|CL|EL|SP|GR|XNC|LB|O typeName description printable startNewPage tool1 ...>
     <material id=<good id> used="base"/>    ← asosiy material
     <part id=<part id>/>                    ← operatsiyaga kiruvchi detallar va listlar (havola)
  </operation>
</project>
```
Sana — epoch millisekund. O'lcham — mm. Mantiqiy — "true"/"false". Manfiy torsovka (−1) — «operatsiya qiymati».

## G2. `good` turlari → MebeliX

| typeId | Ma'nosi | MebeliX |
|---|---|---|
| `product` | mahsulot: count, costMaterial, costOperation, cost, description, orderDate, date, phone1, phone2, program(xml); ichida `part` — detallar | `Product` |
| `simple` | oddiy material: unit, count, cost | O operatsiyasi `OMaterial` |
| `band` | pogonaj material / kromka lentasi: w, t, count, cost (cCostByItem ga ko'ra metr yoki dona) | EL: width/thickness/price; CL: polosa |
| `sheet` | listli material: l, w, t, count, cost (m² yoki list); ichida `part` — list/qoldiqlar | CS nomi/kodi/qalinligi/narxi + `sheets[]` |
| `tool.cutting` | arra stanogi: swSawthick, swPackageHeight, swMaxturns, swSort, swSortInBand, swComplexBand, swMinSizeBand, swMaxSizeBand, swMaxLengthBand, swMinPruning | `CSCutParams`: kerf, pack_height, max_rotations, strip_sort, in_strip_sort, complex_strips, min/max_strip_width, max_strip_length, min_trim_cut |
| `tool.edgeline` | kromka stanogi: elCost, elRestSide, elMinSize, elWidthPreJoint | `ELParams`: op_price, overhang, min_glue_length, jointing_width |

## G3. `part` atributlari → `Part` / `StockSheet`

| Atribut | Ma'nosi | MebeliX |
|---|---|---|
| id | ID | `uid` |
| l, w | заготовка o'lchami (cSizeMode=0 da majburiy) | length/width (rejim blank) |
| dl, dw | detal o'lchami (rejim 1) | length/width (rejim detail) |
| jl, jw | prifugovkadan keyin (rejim 2) | length/width (rejim jointed) |
| cl, cw | pilniy o'lcham (ixtiyoriy) | tekshiruv uchun |
| allowanceT/B/L/R | pripusklar | allow_top/bottom/left/right |
| count, usedCount | soni, ishlatilgani | qty, used_qty |
| name, description | nom; tavsif (`#KOD` lits, `##KOD` orqa XNC kodlari) | name, description |
| txt | tekstura | grain |
| waste, business | qoldiq belgisi, delovoy | StockSheet.kind |
| sheetId | qoldiq qaysi listda | source (ixtiyoriy) |
| elt, elb, ell, elr | kromka operatsiyasi havolasi (yuqori/past/chap/o'ng) | edge_top/bottom/left/right |
| grt, grb, grl, grr (+ grts…: tomon, true=lits) | paz operatsiyasi | groove_* (front) |
| groupInBlock (0/1/2), groupInBlockMC, groupInBlockMaxC | guruhlash | group_by none/length/width, group_min/max |
| cTrimL, cTrimW, cTrimEL, cTrimEW | list uchun torsovka/otstup (−1 = operatsiyadan) | StockSheet.trim_*, end_offset_* |
| dbId | ombor ID si | StockSheet.db_id |

## G4. Operatsiya atributlari

**CS**: tool1 (arra stanogi), cTrimL, cTrimW, cTrimEL, cTrimEW (−1 = mos torsovka), csDirectCut (0..4),
csTexture, cFillRep, cAllowanceWorkpiece, cCostType (0 kesish, 1 perimetr, 2 material maydoni, 3 detal maydoni),
cCostCut, cCostByItem, cCostByItemRound (11..34), cCPF (taxminiy: to'ldirish % = (1−cCPF)×100),
cMinDimRegWaste1/2, cBusinessWaste (m²), cTrimWaster, cMinDimDetail, cSizeMode (0/1/2),
statistika (cFilling, cCountPackets, cBusinessWasteAmount, cTrimLength, cTrimCount, cPartCount,
cPartAmount, cWasteCount, cWasteAmount, cMaterialCount, cMaterialAmount — va «P» bilan tugaydigan taxminiylari),
data (base64 kartalar), cSaveDrawCut, draw (xml: `p` karta [l,w,c,cm,sheetId,tl,tw], `c` kesim, `d` detal, `r` qoldiq — x,y,l,w,id).
> Import: kartalarni (`draw`) ko'chirish ixtiyoriy — odatda qayta kroy qilinadi. Agar `draw` bo'lsa,
> `CutMap` larni tiklash mumkin (p → map, d → placement, r → offcut).

**CL**: tool1, cTrimW (torsovka), cTrimEW, cFillRep, cCostType (0 kesish torsovka bilan, 1 torsovkasiz,
2 material uzunligi, 3 detal uzunligi), cCostCut, cCostByItem, cCostByItemRound (11, 32, 33, 34), cCPF,
cMinDimRegWaste1 (min qoldiq), cBusinessWaste (delovoy uzunlik, m), cTrimWaster, cMinDimDetail.

**EL**: tool1 (kromka stanogi), elCalcMat, elLength, elRoundMat, elRoundLength, elWastePRC, elSymbol, elColor, elLineMark.

**SP**: spCalcMat, spWastePRC, spRestSide, spSizeMode (−1 pilniy, 0 zagotovka), spCost (m²).

**GR**: grWidth (4), grDepth (8), grOffset (10), grOffsetIncl (true), grSawthick (4), grCuttingLength, grCost.

**LB**: columns, rows, gap, margin, border, source (0 foydalanuvchi, 1 mahsulotlar, 2 detal/qoldiqlar),
printParts, printWastes, partEach, partONZ, partSelected, wasteEach, productEach, productONZ, fields, data, program.

**XNC**: program (xml), count, side, turn (0..3 = 0/90/180/270°), mirHor, mirVert, bySizeDetail, code,
priceBore/countBore/costBore, priceMill/countMill/costMill, priceCut/countCut/costCut, price, cost.
Dastur XML: ildiz `program` (dx, dy, dz); teglar `tool`, `bf` (frontal), `bl`, `br`, `bt`, `bb` (yon parmalash),
`ms` (freza kirish nuqtasi), `ml` (to'g'ri), `ma` (yoy), `mac` (markazli yoy), `gr` (paz), `xy` (koordinata boshi) —
batafsil `J_XNC_SPEC.md`.

**O**: standart atributlar + `material` havolalari (count).

## G5. Import algoritmi (reference)

1. `good` larni id bo'yicha indekslash; har `part` qaysi `good` ichida ekanini eslab qolish.
2. `product` → `Product` (bo'lmasa bitta «Mahsulot1»).
3. Operatsiyalarni yaratish (id xaritasi), asosiy material va stanok parametrlarini ko'chirish;
   loyiha `size_mode` — birinchi CS dagi `cSizeMode`.
4. Operatsiyadagi `part` havolalari: `sheet/band` ichidagilar → `sheets[]` (waste/business → kind),
   `product` ichidagilar → `parts[]` (o'lcham rejimga mos atributdan), kromka/paz havolalari → EL/GR id.
5. `_save()` → recalc. Natijani xodim tekshiradi (detallar soni, kromkalar).

## G6. Excel import va bufer

* Excel oynasi: tablar «Детали», «Материалы», «Изделия», «Простые операции»; har biri: list (sheet),
  boshlang'ich qator, ustun xaritasi; profil sifatida saqlash (`settings_profiles.scope = excel_import`).
* Bufer (Ctrl+V) ustun tartibi: CS `Д-на, Ш-на, Кол, Ткт, ОВ, ОН, ОЛ, ОП, Наименование`;
  CL `Д-на, Кол, ОВ, ОН, ОЛ, ОП, Наименование`; O `Код, Наименование, Ед.И, Кол, Цена`.
  Noma'lum kromka nomi → yangi EL (keyingi bo'sh belgi bilan).
