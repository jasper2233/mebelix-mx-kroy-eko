# WEB tadqiqot: HOMAG / HOLZMA / Schelling fayl formatlari bo'yicha ochiq savollar

Sana: 2026-10-04. Usul: ochiq internet manbalari (ishlab chiqaruvchi qo'llanmalari, PDF spetsifikatsiyalar, yordam sahifalari, forum/GitHub).
Hech qayerga login qilinmadi, bajariluvchi fayl yuklanmadi.

Ishonch darajasi: **yuqori** = rasmiy spetsifikatsiya matni o'qildi; **o'rta** = rasmiy bo'lmagan, lekin ishonchli manba yoki bilvosita dalil;
**past** = faqat qidiruv natijasidagi parcha / taxmin.

## Asosiy manbalar

| Qisqa nom | Manba | Nima bor |
|---|---|---|
| **[IG10]** | Magi-Cut / Cut Rite "Version 10 Interface Guide, rev 1.07", 3-bo'lim "Pattern Exchange File – Specification – V1.14" — https://www.magi-cut.co.uk/files/v10%20interface%20guide.pdf | PTX ning **rasmiy** to'liq spetsifikatsiyasi (110–155-betlar) |
| **[MC-34]** | Magi-Cut V12 yordam: "Homag Sawtech – saw model number 34 – setup" — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1028.htm | NPS400 V3 (CHF320/CHF41/CHF51) funksiya kodlari, `#TRIMS` tartibi |
| **[MC-33]** | "Homag Sawtech – saw model number 33" — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1017.htm | NPS400 V2, trim versiyalari, fayllar ro'yxati |
| **[MC-LBL]** | "Restrictions on label data – Homag Sawtech" — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1072.htm | `#CUT` dagi detal raqami, `#LABEL` yozuvi, DIST/PEZZI/NPSPRG |
| **[MC-2ND]** | "Second cut after laminating – Homag Sawtech" — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1355.htm | NPS dastur faylining **haqiqiy misoli** (`#REMARK/#DIMENSION/#TRIMS/#CUT/#LABEL`) |
| **[MC-ILE]** | "Homag Sawtech – Ilenia controller" — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1303.htm | Ilenia: `.NPS`, `.DST`, `.PCS` fayllari |
| **[MC-CAD]** | "Transfer to CADmatic saws – setup" — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1269.htm | CADmatic rejimlari, `.SAW`, PTN3/PTNR, recut cheklovi |
| **[MC-CL]** | "CADlink" — https://www.magi-cut.co.uk/files/html/V12webhelp/Cadlink.htm | PTX → `.saw` konvertori, xato kodlari (nom ≤ 8, kod ≤ 25) |
| **[MC-BK]** | "Rules for combiTec recuts" (book height misoli) — https://www.magi-cut.co.uk/files/html/V12webhelp/mct2409.htm | Kitob balandligi qoidasi misoli |
| **[CAD3-RU]** | HOLZMA "Руководство по эксплуатации CADmatic V3.0" (9-482-42-3055) — https://stankoteam.ru/upload/iblock/63b/63b1df490bd0bf4c3e95109c229ecfdc.PDF | Kesish darajalari 1…15, paket/Total, etiketka — opsiya |
| **[MCS412]** | IMA Schelling "NC data format 4.12 for standard import" — https://www.imaschelling.com/fileadmin/Downloads/MCS_NC_4.12_data_format_import_EN.pdf | `F 01`, `F 80`, `B 01`, `K 01`, `L 01` yozuvlari, birliklar, etiketka qoidasi |
| **[MPR4]** | HOMAG "woodWOP MPR4x Format" (Beschreibung woodWOP-Variantendatei) nusxasi — https://idoc.pub/documents/woodwop-mpr4x-format-34wmxewgy8l7 | `<103`, `<105`, koordinata tizimlari, RK |
| **[STILES]** | Stiles "Assigning WoodWOP Layer Names to DXF Geometry" — https://www.stilesmachinery.com/articles/assigning-woodwop-layer-names-to-dxf-geometry (PDF: https://www.woodweb.com/images_forums_public/cad/WoodWOP_Layer_Names_to_DXF_Geometry.pdf) | woodWOP da frezaning Z qiymati qayerdan o'lchanadi |
| **[MC-C4]** | "Schelling – Commander 4 – setup" — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1070.htm | Eski Schelling `.NC` formati (MCS emas) — faqat taqqoslash uchun |

---

## 1-savol. Cut Rite PTX (Pattern Exchange) formati

**JAVOB (ishonch: yuqori).** Rasmiy spetsifikatsiya topildi: [IG10] 3-bo'lim, "Pattern Exchange File – Specification – V1.14". Quyida bizning hujjatdagi (`holzma-ptx.md`) taxminlar bilan solishtirilgan to'liq maydon ro'yxati.

### 1.1 Umumiy qoidalar
- Fayl — oddiy CSV; matn ichida vergul bo'lsa qo'shtirnoq majburiy. Dalil: *"Text fields containing commas must be enclosed in quotes."* [IG10]
- Oxirgi vergullar shart emas, boshidagi bo'shliqlar e'tiborga olinmaydi. Dalil: *"Trailing commas (separators) are not necessary."* [IG10]
- Kodlash: "ASCII/Unicode comma-separated file" — aniq kod sahifa ko'rsatilmagan. [IG10]
- Kasr sonlar nuqta bilan: misolda `1272.6`, `5.2`, `130.4`. [IG10, 18-misol]
- Minimal talab — `PARTS_REQ` va `MATERIALS`. Dalil: *"The minimum requirement of lines in a PTX file is PARTS_REQ and MATERIALS."* — https://www.magi-cut.co.uk/files/html/V12webhelp/mct1404.htm
- Cheklovlar arraga bog'liq. Dalil: *"some controllers will, for example, only accept 5 digits for the job number."* [IG10]

### 1.2 `HEADER` — VERSION, TITLE, UNITS, ORIGIN, TRIM_TYPE
| Maydon | Rasmiy ma'no |
|---|---|
| UNITS | `0` = metrik, `1` = o'nlik dyuym |
| ORIGIN | **faqat `VECTORS` chizma yozuvlari uchun** koordinata boshi: 0 = yuqoridan pastga, chapdan o'ngga; 1 = yuqoridan pastga, o'ngdan chapga; 2 = pastdan yuqoriga, chapdan o'ngga; 3 = pastdan yuqoriga, o'ngdan chapga. `CUTS` uchun doim 0 (yuqori-chap) |
| TRIM_TYPE | `0` = avval chiqindi bo'lak kesiladi; `1` = **avval qat'iy trim** (oldingi chekka) |

Dalil: *"0 = trim waste piece first / 1 = trim fixed trim first"* [IG10].
**Generator uchun:** `0,0,1` — to'g'ri, **saqlansin** (mm, yuqori-chap, avval trim — bizning 90/91/92 trim ketma-ketligimizga mos).

### 1.3 `JOBS` — JOB_INDEX, NAME, DESC, ORD_DATE, CUT_DATE, CUSTOMER, STATUS, OPT_PARAM, SAW_PARAM, CUT_TIME, WASTE_PCNT
- STATUS: `0` optimallashtirilmagan, `1` optimallashtirilgan, `2` xato. Sana formati spetsifikatsiyada `DD/MM/YYYY` (GibLab `dd.mm.yyyy` yozadi).
- **Generator uchun:** `STATUS=1` saqlansin. Sana ajratuvchisi — namunalardagidek qoldirilsin (ishlayotgan namuna ustun), lekin sozlamada `DD/MM/YYYY` varianti bo'lsin.
- CADmatic 3 uchun ish nomi cheklovi: *"Job name not valid (contains spaces or > 8 chrs)"* [MC-CL] — CADlink orqali konvertatsiyada JOBS.NAME bo'shliqsiz va ≤ 8 belgi bo'lishi kerak (xato 18). Kodlar ≤ 25 belgi (xato 19) — bu bizdagi "TITLE 25 belgiga kesiladi" kuzatuvini tushuntiradi.

### 1.4 `PARTS_REQ` — JOB_INDEX, PART_INDEX, CODE, MAT_INDEX, LENGTH, WIDTH, QTY_REQ, QTY_OVER, QTY_UNDER, GRAIN, QTY_PROD, UNDER_PROD_ERROR, UNDER_PROD_ALLOWED, UNDER_PROD_PLUSPART
- LENGTH/WIDTH — **kesish o'lchami**. Dalil: *"LENGTH - Cut length of part shown in appropriate measurement unit"* [IG10].
- GRAIN: `0` = tekstura yo'q/aylantirish mumkin; `1` = uzunlik bo'ylab, aylantirib bo'lmaydi; **`2` = eni bo'ylab, albatta aylantirilishi shart**. Dalil: *"2 = grain along the width of the board/part must be rotated"* [IG10].
- 12–14-maydonlar: xato sabab ishlab chiqarilmagan / ruxsat etilgan kam / plus-detal sonlari — `0,0,0` to'g'ri.
- **Generator uchun:** `holzma-ptx.md` 6-bo'lim 3-savoliga javob: PARTS_REQ ga **`cl/cw` (arra o'lchami)** yozilsin; tayyor o'lcham `PARTS_INF.FIN_LENGTH/FIN_WIDTH` ga. 8-savol: `GRAIN=2` mavjud — kerak bo'lsa ishlatsa bo'ladi.

### 1.5 `PARTS_INF` — to'liq ro'yxat (bizning 31 maydonimizga moslab)
Spetsifikatsiya sarlavhasida `PALLET` yo'q, lekin tavsifda va misolda bor (`...,MDF18,2X1,BU-SIDE-CNC,BU4DW,...`), shuning uchun haqiqiy tartib:

| # | Rasmiy nom | Ma'no | GibLab namunasida |
|---|---|---|---|
| 1,2 | JOB_INDEX, PART_INDEX | | |
| 3 | DESC | ikkinchi tavsif | bo'sh |
| 4 | **LABEL_QTY** | etiketka nusxalari; `0` = etiketka yo'q; standart 1 | `1` |
| 5,6 | **FIN_LENGTH, FIN_WIDTH** | kromka va frezerdan keyingi **tayyor** o'lcham | L, W |
| 7 | ORDER | buyurtma | `3161 mijoz` |
| 8–11 | EDGE1..4 | kromka: **pastki, yuqori (uzun), chap, o'ng (qisqa)** | to'g'ri aniqlangan |
| 12–15 | EDG_PG1..4 | kromka dasturi/operatsiya kodi (shu tartibda) | `A`,`B`… |
| 16,17 | FACE_LAM, BACK_LAM | yuz/orqa laminat | bo'sh |
| 18 | CORE | asos material | material nomi |
| 19 | PALLET | taglik sxemasi | bo'sh |
| 20 | DRAWING | chizma / CNC dastur fayli nomi | bo'sh |
| 21 | PRODUCT | buyum kodi | `01 shkaf` |
| 22 | PROD_INFO | buyum tavsifi | bo'sh |
| 23 | PROD_WIDTH | buyum tashqi o'lchami | **GibLab bu yerga buyum kodini (`316101`) yozadi** |
| 24,25 | PROD_HGT, PROD_DEPTH | | bo'sh |
| 26 | **PROD_NUM** | xonadagi buyum raqami | `1` |
| 27 | **ROOM** | xona/guruh raqami | `1` |
| 28 | **BARCODE1** | 1-shtrix-kod matni | 1-XNC kodi |
| 29 | **BARCODE2** | 2-shtrix-kod matni | 2-XNC kodi |
| 30 | COLOUR | kengaytirilgan rang nomi | `(CS) material` |
| 31,32 | SECOND_CUT_LENGTH/WIDTH | ikkinchi kesishdan oldingi o'lcham | yo'q |

Dalil: *"EDGE1 - Code or description of edging for bottom (length) edge"*; *"LABEL_QTY - Number of copies of the label for this part."* [IG10].
**Generator uchun:** tuzilma **saqlansin**. O'zgartirish: 5,6-maydonga `dl/dw` (tayyor o'lcham) yozilsin, agar `cl/cw` dan farq qilsa. 4, 26, 27-maydonlar (`1`) — konstant emas, ma'nosi ma'lum: LABEL_QTY, PROD_NUM, ROOM.

### 1.6 `BOARDS` — JOB_INDEX, BRD_INDEX, CODE, MAT_INDEX, LENGTH, WIDTH, QTY_STOCK, QTY_USED, COST, STK_FLAG, INFORMATION, MAT_PARAM, GRAIN, TYPE, BIN, SUPPLIER
- **INFORMATION** — erkin matn, 50 belgigacha. Dalil: *"INFORMATION - Extra descriptive details about the sheet"* [IG10]. Misollarda u `Bin 1`, `Spec. Order` kabi izoh.
- Demak `2750 x 2750` — **arra uchun ahamiyatsiz izoh**; GibLab'da shunchaki `L x L` yozadigan xato. Arra geometriyani 5,6-maydon (LENGTH, WIDTH) dan oladi.
- 12-maydon — **MAT_PARAM** (material parametrlari fayli nomi; GibLab material nomini yozadi), 13 — GRAIN (0/1/2), 14 — **TYPE**: `0` oddiy list, `1` qoldiq (offcut), `2` avtomatik qoldiq; 15 — BIN; 16 — SUPPLIER.
- QTY_STOCK standart 99999 (0 = yo'q); STK_FLAG — zaxira yetmaganda harakat bayrog'i.
- **Generator uchun:** INFORMATION ga `"<L> x <W>"` (to'g'ri o'lcham) yoki bo'sh yozish **xavfsiz — o'zgartirilsin**. Qoldiq listdan kesilganda `TYPE=1` yozish tavsiya etiladi (14-maydon qo'shiladi).

### 1.7 `MATERIALS` — JOB_INDEX, MAT_INDEX, CODE, DESC, THICK, BOOK, KERF_RIP, KERF_XCT, TRIM_FRIP, TRIM_VRIP, TRIM_FXCT, TRIM_VXCT, TRIM_HEAD, TRIM_FRCT, TRIM_VRCT, RULE1..4, MAT_PARAM, GRAIN, PICTURE, DENSITY
- **Trim arra eni bilan birga yoziladi.** Dalil: *"TRIM_FRIP - Fixed rip trim - includes saw kerf"* va *"TRIM_VRIP - Minimum waste rip trim ... including saw kerf"* [IG10]. Xuddi shunday FXCT, VXCT, HEAD, FRCT, VRCT.
- Qo'shimcha dalil (VECTORS bo'limi): *"a 10 mm trim would result in a vector at x=10 ... waste removed is 5.5"* (kerf 4.5 da) [IG10].
- BOOK. Dalil: *"BOOK - Max sheets per book, reflects cutting height of saw"* [IG10].
- 13–15: TRIM_HEAD (ichki bosh kesim trimi), TRIM_FRCT (recut qat'iy trimi), TRIM_VRCT (recut min. chiqindi).
- 16–19: RULE1 = kesish chuqurligi chegarasi 1…9 (*"3 = allow third phase recuts"*), RULE2 = bosh kesimga ruxsat (0/1), RULE3 = listni burish (0/1), RULE4 = takroriy detallar uchun alohida kartalar (0/1).
- 20 MAT_PARAM, 21 GRAIN, 22 PICTURE (`RGB(255:0:0)` yoki rasm fayli), 23 DENSITY.
- **Generator uchun:** `5 = cTrim 2 + kerf 3` gipotezasi **tasdiqlandi — saqlansin** (`swTrimIncludeSaw=true` bo'lsa kerf qo'shilmaydi). RULE1 hozir `1` — bu faqat optimallashtiruvchi uchun; mantiqan kartadagi maksimal daraja (masalan 5) yozilsa to'g'riroq, lekin ishlayotgan namuna `1` — **o'zgartirish ixtiyoriy**. TRIM_HEAD/FRCT/VRCT = 0 qoladi, chunki biz 3+ darajada trim yozmaymiz.

### 1.8 `PATTERNS` — JOB_INDEX, PTN_INDEX, BRD_INDEX, TYPE, QTY_RUN, QTY_CYCLES, MAX_BOOK, PICTURE, CYCLE_TIME, TOTAL_TIME
- TYPE: `0` avval uzunasiga rip (bosh kesimsiz); `1` rip oldidan listni burish; `2` bosh kesim eni bo'ylab; `3` bosh kesim uzunligi bo'ylab; `4` faqat ko'ndalang; `5–8` shablon kartalari.
- QTY_RUN. Dalil: *"QTY_RUN - Run quantity - number of sheets to be cut to this pattern"*.
- QTY_CYCLES. Dalil: *"QTY_CYCLES - Number of cycles or books"*.
- MAX_BOOK. Dalil: *"MAX_BOOK - Maximum number of sheets per book (cutting height)"*.
- Hisob misoli. Dalil: *"run quantity 20, and cut 6 sheets at a time, then there will be 4 cycles"* [IG10] → `QTY_CYCLES = ceil(QTY_RUN / MAX_BOOK)`. Sikllarni arra o'zi sanaydi: *"The saw takes care of counting the cycles."*
- **Generator uchun (O'ZGARTIRISH):** hozir `QTY_CYCLES` doim `1`. `QTY_RUN > BOOK` bo'lganda `QTY_CYCLES = ceil(QTY_RUN / BOOK)`, `MAX_BOOK = min(QTY_RUN, BOOK)` yozilsin (namunalarda QTY_RUN ≤ 2 bo'lgani uchun farq ko'rinmagan). `TYPE=1` (listni burish) va `TYPE=3` ham mavjud — hozircha 0 va 2 yetarli.

### 1.9 `CUTS` — JOB_INDEX, PTN_INDEX, CUT_INDEX, SEQUENCE, FUNCTION, DIMENSION, QTY_RPT, PART_INDEX, QTY_PARTS, COMMENT
- FUNCTION: `0` bosh kesim, `1` rip, `2` ko'ndalang, `3` 3-faza recut, `4` 4-faza … **maksimal faza = 9**. Dalil: *"Maximum phase = 9"* [IG10].
- `90,91,92,93…` — tegishli fazaning trim/chiqindi kesimi (jadvalda diapazon `0-9, 90-99`). Dalil: *"trim / waste cut corresponding to phase of cut"* [IG10]. Ya'ni 90 = bosh kesim trimi, 91 = rip trimi, 92 = ko'ndalang trimi, 93 = recut trimi, 94 = 4-faza trimi.
- Rasmiy misolda trim ikki xil yoziladi: `…,91,5.2,1,0,0` (QTY_RPT=1 — **haqiqiy trim kesimi**) va `…,92,130.4,0,0,0` (QTY_RPT=0 — **tushadigan chiqindi**, kesim emas).
- SEQUENCE ixtiyoriy. Dalil: *"if not given then the cutting sequence should be determined by the saw"* [IG10] → `0` yozish to'g'ri.
- PART_INDEX: `0` yoki detal indeksi yoki `X<OFC_INDEX>` (qoldiq). Dalil: *"points to the PARTS_REQ records of relevant part or 'X' + OFC_INDEX"* [IG10].
- QTY_PARTS — **shu kartaning barcha sikllari bo'yicha** jami. Dalil: *"Quantity of this part produced by this cut for all cycles of this pattern."*
- Bir kesimdan bir nechta turli detal chiqsa — o'lchami 0, soni 0 bo'lgan "dummy" CUTS qatorlari.
- Rasmiy misolda har karta `CUTS,…,0,0,<list uzunligi>,0,0,0,MAIN` qatori bilan boshlanadi (bosh kesimsiz kartada ham).
- **Generator uchun:**
  1. FUNCTION kodlari bo'yicha taxminimiz **to'g'ri — saqlansin**; 6…9 darajalar ham ruxsat etilgan (lekin arra/CADlink cheklashi mumkin, 2-savolga qarang).
  2. **Farq:** GibLab trim qatorlarida `QTY_RPT=0` yozadi, spetsifikatsiya misolida haqiqiy trim uchun `1`. Ishlayotgan namunalar `0` bilan — **hozircha saqlansin**, lekin sozlama (`trimQtyRpt = 0|1`) qo'shish tavsiya etiladi; arrada trim kesilmayotgani kuzatilsa `1` ga o'tkaziladi.
  3. **QTY_PARTS (TEKSHIRILSIN):** spetsifikatsiya bo'yicha bu barcha sikllar jami (`× QTY_RUN`). GibLab'da `QTY_PARTS = QTY_RPT` (bir list uchun). `QTY_RUN > 1` kartalarda etiketka soni kam chiqishi mumkin — ehtimoliy xato, amalda sinash kerak.
  4. Qoldiq uchun `PART_INDEX = X1` li CUTS qatori qo'shish etiketka chiqarish uchun to'g'ri usul (hozir yozilmaydi).

### 1.10 `OFFCUTS` — JOB_INDEX, OFC_INDEX, CODE, MAT_INDEX, LENGTH, WIDTH, OFC_QTY, GRAIN
- Dalil: *"can occur once for each different off-cut size per material created by the cutting patterns"* [IG10] — ya'ni **faqat oxirgi karta emas**, har bir turli o'lcham uchun bittadan yozuv; `OFC_QTY` — shu o'lchamdan nechta hosil bo'lgani.
- **Generator uchun (O'ZGARTIRISH):** har qanday kartadagi delovoy qoldiq uchun OFFCUTS yozilsin, `OFC_INDEX` 1 dan ketma-ket, bir xil o'lchamlar `OFC_QTY` ga yig'ilsin (karta `QTY_RUN` ga ko'paytirib), 8-maydon GRAIN qo'shilsin.

---

## 2-savol. Holzma CADmatic 3/4 import formatlari (`.SPL`, `.LC4`, `.SAW`)

**JAVOB (ishonch: `.SAW`/PTX yo'li — yuqori; `.SPL`/`.LC4` ichki tuzilishi — topilmadi).**

- Rasmiy tashqi yo'l: **PTX → (CADlink/HolzLink) → `.SAW`**. Dalil: *"Stand alone program for direct conversion from Pattern Exchange to CADmatic III/IV/V (recursive)"* [MC-CL].
- Cut Rite CADmatic 3/4/5 uchun har run ga bitta fayl yaratadi. Dalil: *"The file is named: run_number.saw, for example: 00032.SAW."* [MC-CAD].
- `.LC4` — CADmatic 4 ning **ichki ish formati**: qidiruv natijasidagi forum parchasi bo'yicha CADmatic 4 `.saw` ni o'zi `.LC4` va `.prv` ga aylantiradi (PROMEBELclub, https://promebelclub.ru/forum/showthread.php?t=756&page=5 — sahifa 403 berdi, matn faqat qidiruv parchasidan; **ishonch: past**).
- `.SPL` va `.LC4` ning ochiq tavsifi **topilmadi** (ingliz, nemis, rus qidiruvlari). Bular hujjatlashtirilmagan ichki formatlar.

**Maksimal kesish darajalari:**
- CADmatic V3 boshqaruvining o'zi 15 darajagacha qabul qiladi. Dalil: *"Для уровней 4...15 действителен тот же порядок действий!"* [CAD3-RU]. Darajalar: 1 = bosh kesim, 2 = bo'ylama, 3 = ko'ndalang, 4 = bir xil uzunlikdagi dokroy, 5 = turli uzunlikdagi dokroy.
- Lekin uzatish formati cheklaydi: standart **PTN3 (rekursiv emas)** da murakkab recut tashlab yuboriladi. Dalil: *"The recuts which are too complex are omitted from the pattern."* [MC-CAD]. Cheksiz recut faqat **PTNR (rekursiv)** formatida: *"some CADmatic 3 (and later) controllers accept the recursive pattern description format"*.
- CADlink xatosi 21: *"CADmatic 3 - Illegal recuts"*; xato 20: shablon kartalar taqiqlangan [MC-CL].
- **Xulosa:** `holzma3-spl.md` dagi "SPL maksimal 4 daraja" kuzatuvi rekursiv bo'lmagan format cheklovi bilan mos keladi (bosh + rip + ko'ndalang + 1–2 recut), lekin aniq son (4) internetda **tasdiqlanmadi**.

**Etiketka ma'lumoti majburiymi:**
- Yo'q, etiketkalash — opsiya. Dalil: *"Имеет значение только при опции Этикетирование"* [CAD3-RU]. PTX da ham `PARTS_INF` — *"This optional record"* [IG10].
- `.LC4` ichidagi base64-zlib blob (GibLab etiketkasi) bo'sh bo'lsa nima bo'lishi — **topilmadi**.

**Generator uchun:**
- Asosiy/tavsiya etilgan chiqish — **PTX** (rasmiy, hujjatlashtirilgan). `.SPL`/`.LC4` generatorlari faqat namunalar asosida — "eksperimental" deb belgilansin, **o'zgartirilmasin**.
- Holzma 3 (SPL) uchun optimizator chuqurligi cheklovi (≤ 4 daraja) **saqlansin**.
- CADmatic 3 uchun fayl/ish nomi ≤ 8 belgi, bo'shliqsiz; kodlar ≤ 25 belgi — generatorga validatsiya qo'shilsin.

---

## 3-savol. HOMAG CHF / NPS400 `pattern.NNN` (`#REMARK/#DIMENSION/#SPEEDS/#TRIMS/#CUT`)

**JAVOB (ishonch: daraja kodlari va `#TRIMS` tartibi — o'rta-yuqori; `#SPEEDS` va `#CUT` 6–14-maydonlari — topilmadi).**
Bu — HOMAG Sawtech (Homag España) **NPS400 dastur fayli** (Cut Rite uni `NPSPRG\<run><pattern>` yoki Ilenia uchun `.NPS` nomi bilan yaratadi). Dalil: *"Program files (pattern) ASCII c:\nps400\npsprg\"* [MC-33], Ilenia: *"c:\cn\autgen\npsprg\ runnumber .NPS"* [MC-ILE].

### 3.1 Daraja (funksiya) kodlari — NPS400 V3 (CHF320/CHF41/CHF51, saw model 34)
| Amal | "Main" blokda | "Head" blokda |
|---|---|---|
| Bosh kesim (head cut) | **1** | |
| Rip (bo'ylama) | 4 | **2** |
| Ko'ndalang (crosscut) | 5 | **3** |
| Recut (3-faza) | 6 | **7** |
| Notekis recut (4-faza) | 8 | **9** |

Dalil: *"6 - Recut in main (3rd phase) / 7 - Recut in head (3rd phase)"* va *"8 - Uneven recut in main (4th phase) / 9 - Uneven recut in head"* [MC-34].
- Shuning uchun fayllarimizda `1,2,3,7,9` uchraydi: GibLab **barcha bloklarni "head" sifatida** yozadi (1 → 2 → 3 → 7 → 9). Bu controller mantiqiga mos: *"Head patterns are cut as though all blocks are heads"* [MC-34].
- `4,5,6,8` — xuddi shu amallar, lekin bosh kesimsiz "main" blok uchun (rasmiy misolda `#CUT,4,384,1,0` rip, `#CUT,5,584,1,-1` ko'ndalang [MC-2ND]).
- **Maksimal chuqurlik:** *"If a pattern contains higher phases than multiple 4th phase an error is produced"* [MC-34] → jami **5 daraja** (bosh, rip, ko'ndalang, recut, notekis recut). 6-daraja kodi yo'q.
- Eski NPS400 V2 (model 33) kuchsizroq: *"Recut: Maximum setting is Multiple equal"*, bosh kesim va recut birga bo'lmaydi [MC-33].

**Generator uchun:** kodlar `1,2,3,7,9` **saqlansin**. `homag-chf-nps400.md`/`homag-zip.md` da ma'no to'g'rilansin: `1` = bosh kesim bloki, `2` = rip, `3` = ko'ndalang, `7` = recut, `9` = notekis recut (geometriya o'zgarmaydi). Optimizator HOMAG profillari uchun **maksimal 5 daraja** bilan cheklansin (`swMaxturns=6` kodlanmaydi).

### 3.2 `#TRIMS` qiymatlar tartibi
Dalil [MC-34]: bosh kesimsiz karta — *"#TRIMS,0,Lr,Xr,Z,1"*; bosh kesimli karta — *"#TRIMS,Xcni,Lr,Rt,Z,1"*, bu yerda:

| Poz. (tokendan keyin) | Ma'no |
|---|---|
| 1 | bosh kesim paytidagi trim (`Xcni` = orqa ko'ndalang trim − head retrim); bosh kesimsiz kartada `0` |
| 2 | `Lr` — **orqa rip (bo'ylama) trimi** |
| 3 | `Xr` — orqa ko'ndalang trimi / `Rt` — head retrim |
| 4 | `Z` — orqa recut trimi |
| 5 | bayroq (Cut Rite `1` yozadi; GibLab `0`) — ma'nosi ochiq manbada yo'q |

- Rasmiy misol: *"#TRIMS,10.0,10.0,5.0,0.0,1 (10mm core trims)"* [MC-2ND].
- Trim versiyaga bog'liq: *"NPS400 V2138 and previous versions use only one general trim"*; V3012+ da bosh/rip/ko'ndalang/recut uchun alohida [MC-33].
- Cut Rite da bu trimlar arra eni bilan birga beriladi (parametr nomi: *"Minimum crosscut trim (inc. saw blade thickness)"* [MC-34]); fayl ichidagi qiymat kerf bilanmi — to'g'ridan-to'g'ri yozilmagan (ishonch: o'rta).
- **Kerf maydoni `pattern` faylida yo'q** — manbalar faqat DIMENSION, TRIMS, CUT, LABEL, REMARK yozuvlarini ko'rsatadi; arra eni controller sozlamasi.

**Generator uchun:** GibLab'ning `2.0,2.0,0.0,0.0,0` qiymati = "bosh kesim trimi 2, rip trimi 2, ko'ndalang retrim 0, recut 0". Ishlayotgan namuna — **saqlansin**, lekin `cTrimL/cTrimW` moslashuvi endi ma'lum: 1-poz. — bosh kesim o'qi (X, 1-daraja), 2-poz. — rip o'qi (Y, 2-daraja). 3-poz. (ko'ndalang retrim) va 4-poz. (recut trimi) sozlama sifatida chiqarilsin.

### 3.3 `#CUT`, `#LABEL`, `#DIMENSION`, `#REMARK`
- `#CUT,<kod>,<o'lcham>,<takror>,<detal raqami>,…` — 4-qiymat (bizning hujjatda pos 5) = **detal (item) raqami**: `0` = detal yo'q; `-1` = bir nechta detal, tafsilot `#LABEL` da. Dalil: *"If the part number in the main #CUT record is -1 ... listed in the corresponding #LABEL record"* [MC-LBL].
- `#LABEL` — 5 juft (detal raqami, soni). Dalil: *"#LABEL which contains 5 x part number and quantity"* [MC-LBL]; misol: `#LABEL,15,1,0,0,0,0,0,0,0,0,` [MC-2ND].
- `#DIMENSION,620.0,420.0,18.0,0,` — X, Y, qalinlik, 0; kasr `620.0` ko'rinishida yoziladi [MC-2ND]. 4-qiymat (`0`) ma'nosi berilmagan.
- `#REMARK,DOOR - SECOND CUT,MDF18MM` — *(Part name, core material code)* [MC-2ND]: 1-maydon erkin izoh, 2-maydon material kodi.
- **Listlar soni va kitob balandligi `pattern` faylida emas**, alohida ish ro'yxatida. Dalil: *"list of program files for the run together with pattern run quantities and book heights"* (`DIST\<run>.dbf`) [MC-LBL].
- Etiketka uchun `PEZZI\<run>.dbf` (detallar bazasi) kerak; usiz arra faqat kesadi.
- Model 34 da: *"The order in which crosscut dimensions appear has been reversed (right-to-left)"* [MC-34].

**Generator uchun:**
- `homag-zip.md` 1-savol (listlar soni) javobi: faqat `pattern.NNN` berilganda son va kitob balandligini **operator qo'lda kiritadi**; avtomatik uchun `DIST` DBF kerak (biz yozmaymiz) — hujjatga shunday yozilsin, kod **o'zgarmaydi**.
- `#CUT` pos 5 = detal raqami: `0` yozish = "etiketkasiz" — **saqlansin**. Kelajakda `PEZZI` bazasi bilan birga detal raqamini yozish mumkin.
- Kasr o'lcham: nuqta bilan (`346.5`) — rasmiy misoldagi `620.0`, `10.0` ga mos (ishonch: o'rta; `#CUT` da kasr misoli yo'q).

---

## 4-savol. Schelling MCS `.ncl` / `.ncp`

**JAVOB (ishonch: `F 01`, `F 80`, `B 01`, birliklar, etiketka — yuqori; `P 0x`, `C`, `S 01`, `P 09` — topilmadi).**
Rasmiy hujjat [MCS412] faqat "standart import" yozuvlarini (L, F, K, B, W, U, X) tasvirlaydi; **kesish kartasi yozuvlari (`P 01/02/03/98`, `C`, `S 01`, `S 46`) va `P 09` unda yo'q.** `.ncl` — "schedule" fayli ekani tasdiqlandi: *"unique within the schedule file *.ncl"* [MCS412].

### 4.1 Umumiy
- Birlik: mikron. Dalil: *"eight-digit, integer type and in 1/1000 mm ... 1390mm corresponds to 01390000"* [MCS412].
- Qator oxiri CR LF; maydonlar qat'iy pozitsiyada, bo'shliq bilan ajratilgan; matn chapga, son o'ngga nollar bilan. Dalil: *"Each data record (each line) is terminated with CR LF"*.
- Nomlar 20 belgi. Dalil: *"For names 20 alphanumeric characters are designated."* Taqqoslash registrga bog'liq emas.
- Tekstura doim **A tomonga parallel**: *"A structure on a format or on a raw board runs always parallel to the A-edge."*

### 4.2 `F 01` (Format-base-line) — bizning ustunlarga moslab
| Bizning ustun | Rasmiy maydon |
|---|---|
| 6–9 | Sequential number |
| 11–14 | **Combined number** (birlashtirilgan format raqami; kartalarda aynan shu ishlatiladi) |
| 16 | **Category**: 0 oddiy, 1 qoldiq (remainder), 2 bo'ylama polosa, 3 oraliq format |
| 18–23 / 25–30 | **Quantity order / Quantity optimize** (buyurtma soni / optimizator rejalashtirgan son) |
| 32–51, 53–60 | Board type, Board thickness |
| 62–69, 71–78 | **Cutting dimension A / B** (arra o'lchami) |
| 80–87, 89–96 | **Finished dimension A / B** (tayyor o'lcham) |
| 98–117 | Description |
| 119 | **Format is rotatable**: 0 yo'q, 1 ha, 2 = list teksturali bo'lsa yo'q (standart 2) |
| 121 | Priority (standart **9** = majburiy pozitsiya; 0–8 = to'ldiruvchi) |
| 123 | Quality (standart **9**) |
| 125 | Format only turned use (0) |
| 127–128 | Identifier group of formats (00) |
| 130–135, 137–139 | Over-delivery dona / foiz |
| 141–146, 148–150 | Under-delivery dona / foiz |
| 152 | **Format optimize** (1 = optimallashtirilsin; qoldiqda 0) — "etiketka" emas |
| 154 | Format is sub-part (0) |
| 156–175 | Position number from external program (GibLab: 1-XNC kodi) |
| 177–196 | Line number from external program (GibLab: 2-XNC kodi) |
| 198–237 | Processing note (40 belgi) |
| 239 | **Label print** (1 = etiketka chiqarilsin) |
| 241 | Packing tags print (0) |
| 243–262 | Source assembly (GibLab: GibLabID) |
| 264–283 | Source part list (GibLab: buyum nomi) |
| 285–293 | Format number part list (1…999999999; qoldiqda 0) |
| 295–304 | Delivery date |
| 306, 308 | Orientation in the longitudinal strip (0 erkin, 1, 2); Status (0 optimizator, 1 qo'lda) |

Dalillar: *"quantity of formats orders: The order quantity is the desired quantity"*; *"finished dimension A / B: Those are the final format dimensions."*; *"9= obligatory position: The format must be planned with the given quantity."* [MCS412].

### 4.3 `F 80` (Format-post-processing-line)
| Bizning ustun | Rasmiy maydon |
|---|---|
| 6–40 | Minus/Plus tolerance cutting dimension A, B (4 × 8N, standart 0) |
| 42–45 | Format cutting pattern (`.ncf` fayl raqami, 0 = yo'q) |
| 47, 68, 89, 110 (20A) | **Edge identifier**: A down (bo'ylama old), A above (bo'ylama orqa), B left, B right |
| 131–141 | Corner logo ×4 (2N, `00` = yo'q) |
| 143–150, 152–159 | Intermediate dimension A / B |

- Dalil: *"That is a reference on a schedule-referred data record with an edge definition."* — ya'ni `(A) 1` — **kromka identifikatori (nom)**, qalinlik maydoni emas. Kromka qalinligi alohida `K 01` yozuvida (Base/Finished dimension edge, `.kan` fayli).
- `F 80` ixtiyoriy: *"It is optional."*

### 4.4 `B 01` (Board-base-line)
| Bizning ustun | Rasmiy maydon |
|---|---|
| 6–9 | Sequential position number |
| 11 | **Category**: 0 oddiy list, **1 qoldiq (remainder)**, 2 polosa, 4 XL qoldiq |
| 13–32, 34–41 | Board type, thickness |
| 43–50, 52–59 | Board dimension A, B |
| 61 | **Structure**: 0 tekstura yo'q, 1 bor (A ga parallel) |
| 63–82 | Description |
| 84, 86 | Quality (standart 9), Priority |
| 88–97 | **Cost per unit** (standart 1 → `0000000001`) |
| 99 | Unit for price calculation (0 = m²) |

Dalil: *"13... cost per unit: Default value = 1."* [MCS412]. Keyingi maydonlar (aylantirish, trim A/B ×4 …) bizning 99 belgili qatorda yo'q — eski/qisqa versiya.

### 4.5 Qo'shimcha XML etiketka fayli kerakmi
- **Kerak emas.** Dalil: *"If this line is missing, the standard label of the machine control system is used."* (`F 01` 29-maydon "label print", `F 06` yo'q bo'lsa) [MCS412]. MCS etiketkani `F 01` + `F 06`/`F 60-79` yozuvlaridan oladi; `GibLabData.*.xml` Schelling formatiga kirmaydi — bu GibLab'ning o'z etiketka moduli fayli.

**Generator uchun:**
- `F 01` ikkita son va ikkita o'lcham juftligi: **1-juft = `cl/cw` (kesish), 2-juft = `dl/dw` (tayyor)** yozilsin — o'zgartirish (hozir ikkalasi teng yoziladi; farq bo'lsa to'g'ri bo'ladi).
- `9 9 0 00 …`, `0000000001` va h.k. — konstant emas, standart qiymatlar; **saqlansin**.
- `B 01` 11-ustun: qoldiq-listdan kesilganda `1` yozish rasmiy to'g'ri (GibLab doim 0) — ixtiyoriy yaxshilash. 61-ustun: teksturali materialda `1` mantiqan to'g'ri, lekin aylanish `F 01` 119-ustun orqali allaqachon boshqariladi — **saqlansin**.
- `GibLabData.*.xml` — **yozilmasin** (yoki ixtiyoriy opsiya); stanok talab qilmaydi.
- `F 80` kromka matni 20 belgili identifikator sifatida qoldirilsin.

---

## 5-savol. woodWOP MPR

### 5.1 `<103 \BohrHoriz\` — ZA yuqoridanmi, pastdanmi
**JAVOB (ishonch: o'rta): ZA — tanlangan koordinata tizimidagi absolyut Z koordinata; standart tizimda Z=0 detalning PASTKI yuzasi (stol tomoni), ya'ni pastdan o'lchanadi.**
- Rasmiy format hujjati faqat shunday deydi: *"ZA : Bohrkoordinate in Z"* [MPR4]; BM: *"XP =0: X-Plus, d.h. in positive X-Richtung"*, XM, YP, YM, C.
- Standart koordinata tizimi: *"00: Koordsys XY-Ebene X=0 Y=0 Z=0 Drehwinkel 0 X-Achse positiv"* [MPR4].
- Z noli pastki yuza ekaniga dalil (freza uchun, o'sha koordinata tizimi): *"(-3 mm below the panel bottom edge)"* [STILES].
- Bizning namunalardagi `ZA = dz − z` (z — yuzadan) shu bilan to'liq mos.
- Diqqat: ba'zi CAD'lar (VectorWOP) o'z dialogida Z ni yuqoridan so'raydi (*"Abstand in z bezüglich Oberkante Werkstück"* — https://vectorworks-hilfe.computerworks.eu/2022/Vectorworks-Hilfe/interiorcad/VectorWOP_Klassisch.htm) — bu CAD interfeysi, MPR maydoni emas.

**Generator uchun:** `ZA = dz − z` **saqlansin**.

### 5.2 `<105 \Konturfraesen\` — ZA ma'nosi
**JAVOB (ishonch: o'rta): ZA — frezaning uchi turadigan absolyut Z (pastki yuzadan), "chuqurlik" emas, balki "qolgan qalinlik".**
- Dalil: *"ZA : Startkoordinate in Z"* [MPR4]; *"position the end of the router tooling ... (-3 mm below the panel bottom edge)"* [STILES].
- Demak: o'tuvchi freza `ZA="0"` (yoki stolga kirish uchun manfiy, masalan `-2`); chuqurligi `dp` bo'lgan o'tmaydigan freza **`ZA = dz − dp`**.
- `ZA="@0"` — Z kontur nuqtalarining o'zidan (`$E` dagi `Z=`) olinadi (ochiq kodli postprotsessorda shunday ishlatilgan: https://github.com/FunkJetDie/Autodesk_to_WoodWop5_PostProcessor/blob/master/WW5_PP).

**Generator uchun:** `homag-woodwop-v6.md` 1-savol javobi: **`ZA = dz − dp`** (formula sifatida `"_BSZ-<dp>"` ham yozish mumkin — parser ifodalarni hisoblaydi: *"Mathematische Ausdrücke werden von einem Parser berechnet."* [MPR4]). Bitta haqiqiy namunada tekshirish tavsiya etiladi.

### 5.3 RK: WRKL / WRKR
**JAVOB (ishonch: yuqori).** Dalil: *"WRKL =1: links von der programmierten Linie"*, *"WRKR =2: rechts von der programmierten Linie"*, *"NOWRK =0: auf der programmierten Linie"* [MPR4]. Chap/o'ng — dasturlangan chiziqqa nisbatan, ya'ni **harakat yo'nalishi bo'yicha**.
**Generator uchun:** `c=1 → WRKL`, `c=2 → WRKR` raqamli moslik **saqlansin** (raqamlar ham mos: WRKL=1, WRKR=2).

### 5.4 Kirish/chiqish rejimlari (qo'shimcha)
Dalil: *"MDA : Anfahrmodus TAN =0: tangential"*, *"SEI =1: seitlich"*, *"SEN =2: senkrecht"* [MPR4]. Hozirgi `SEN` / `SEN_AB` to'g'ri; urinma kirish uchun `TAN`.

### 5.5 Kirill uchun kodlash
**JAVOB TOPILMADI.** Rasmiy hujjatda belgilar to'plami haqida gap yo'q. Ochiq kodli generatorlar ASCII yozadi (`setCodePage("ascii")`, yuqoridagi GitHub manba; boshqa loyiha ham kodlashni "ochiq savol" deb qoldirgan: https://github.com/tiagofur/muebleria/pull/1029).
**Generator uchun:** `KAT`, izoh (`KM`) va nomlarda **faqat ASCII** (kirill → lotin transliteratsiya) — xavfsiz yo'l, **shunday qilinsin**.

### 5.6 Kasr qiymatlar
**JAVOB (ishonch: o'rta).** Qiymatlar qo'shtirnoqdagi satr, parser ifodalarni hisoblaydi; misollarda o'nlik nuqta (`TI="35.0"`, `.Z=0.0000`). Dalil: *"Der Eingabestring wird in Doppelhochkommas angegeben."* [MPR4]. Kontur bloki (`$E`) da qo'shtirnoqsiz.
**Generator uchun:** kasrlar nuqta bilan, ortiqcha nollarsiz — **saqlansin**.

---

## 6-savol. Kitob (stopka) balandligi qoidasi

**JAVOB (ishonch: o'rta-yuqori): ha, `listlar soni = floor(maksimal stopka balandligi / qalinlik)`.**
- Dalil: *"maximum stack height = 200mm, material thickness = 12mm, maximum book height = 192mm"* [MC-BK] → 16 list × 12 = 192 = floor(200/12) × 12.
- PTX: *"BOOK - Max sheets per book, reflects cutting height of saw"* [IG10]. Cut Rite'da bu material/list kutubxonasidagi parametr ("Maximum book height", BDX importida 4 xonali maydon), ya'ni foydalanuvchi qo'lda kamaytirishi mumkin (misollar: 18 mm → Book 5, 12 mm → Book 8, 4 mm → Book 8).
- Sikllar: `QTY_CYCLES = ceil(QTY_RUN / BOOK)`; oxirgi kitob to'liq bo'lmasligi mumkin. CADmatic misoli: paket = 2, Total = 5 → 2 + 2 + 1 [CAD3-RU].

**Generator uchun:** `BOOK = max(1, floor(swPackageHeight / t))` **saqlansin**; material darajasida qo'lda cheklash (override) imkoni qo'shilsin. Masalan 40 mm da: 16 mm → 2, 8 mm → 5, 25 mm → 1.

---

## Generatorlar bo'yicha yig'ma tavsiyalar

| Generator | Saqlansin | O'zgartirilsin |
|---|---|---|
| **holzma-ptx** | HEADER `0,0,1`; trim = cTrim + kerf; FUNCTION 0–5/90–92; SEQUENCE 0; BOOK = floor(H/t) | `BOARDS.INFORMATION` → to'g'ri `L x W` yoki bo'sh; `QTY_CYCLES = ceil(QTY_RUN/BOOK)`; PARTS_REQ = `cl/cw`, PARTS_INF 5,6 = `dl/dw`; OFFCUTS — barcha kartalar uchun, `OFC_QTY` bilan; vergulli matn qo'shtirnoqda; `QTY_PARTS × QTY_RUN` va trim `QTY_RPT=1` — sozlama sifatida, arrada sinab ko'rilsin |
| **holzma2-lc4 / holzma3-spl** | hammasi (hujjatsiz ichki format) | faqat validatsiya: nom ≤ 8 belgi, kodlar ≤ 25; chuqurlik cheklovi qolsin; "eksperimental" belgisi |
| **homag-zip / homag-chf-nps400** | kodlar 1,2,3,7,9; `#TRIMS` qiymatlari; `#CUT` pos5 = 0 | hujjatdagi ma'nolar yangilansin (1 = bosh kesim, 2 = rip, 3 = ko'ndalang, 7 = recut, 9 = notekis recut); optimizator ≤ 5 daraja; `#TRIMS` 3- va 4-qiymat sozlamaga chiqarilsin |
| **shelling-zip / shelling-mcs-zip** | qat'iy pozitsiyalar, mikron, CR LF, konstantalar | `F 01` 2-o'lcham juftligi = tayyor o'lcham; qoldiq-list uchun `B 01` kategoriya 1 (ixtiyoriy); `GibLabData.xml` yozilmasin / opsiya |
| **homag-woodwop-v6** | `<103` `ZA = dz − z`; WRKL/WRKR mosligi; nuqtali kasrlar | o'tmaydigan freza: `ZA = dz − dp`; matnlar faqat ASCII (transliteratsiya) |

---

## JAVOB TOPILMADI

1. **`.SPL` va `.LC4` ichki tuzilishi** — ochiq tavsif yo'q. Jumladan: SPL dagi `f[16]/f[28]`, `e` yozuvi (460 bayt), `d[32]`, `d[76..77]` ma'nolari; LC4 dagi `AddInfo_006/007/011`, `Anschnitt*` parametrlari, `ENUM 0x10`, etiketka blobi majburiyligi va `crc16/crc32` hisobi.
2. **Holzma 3 (SPL) uchun aniq maksimal daraja = 4 ekani** — tasdiqlanmadi (faqat "rekursiv bo'lmagan formatda murakkab recut tashlanadi" degan umumiy dalil).
3. **NPS400 `#SPEEDS`** to'rt qiymatining ma'nosi va nol yuborish xavfsizligi.
4. **NPS400 `#CUT` ning 6–14-maydonlari** (4 ta int, `0.00000`, 4 ta int) va **`#DIMENSION` 4-qiymati**; `#TRIMS` 5-qiymati (0/1 bayroq).
5. **`#TRIMS` qiymatlari kerf bilanmi yoki kerfsizmi** — to'g'ridan-to'g'ri dalil yo'q (Cut Rite parametrlari "inc. saw blade thickness").
6. **NPS400 da fayl nomi `pattern.NNN`** (Cut Rite `<run><pattern>` yoki `.NPS` ishlatadi) va 1000 dan ortiq karta nomlanishi.
7. **Schelling `P 01/02/03/98`, `C` (K01/L01, T, X/a/b/c/d, R), `S 01`, `S 46`, `P 09`** — rasmiy tavsif topilmadi; `P 02` 14–17 (kitobdagi list soni?), `P 03` ikkinchi juftlik, `C` qatoridagi `0`, `T 00005000` ning kelib chiqishi ochiq qoldi.
8. **Schelling ichki `.l.zip`** (bir nechta material) ni MCS qanday o'qishi.
9. **Kirill harflari uchun kodlash** — PTX (faqat "ASCII/Unicode" deyilgan), NPS400, Schelling (faqat "ASCII"), woodWOP MPR — hech birida kod sahifa ko'rsatilmagan. Amaliy tavsiya: transliteratsiya.
10. **woodWOP `<103` ZA ning pastdan o'lchanishi** — bilvosita dalil bilan (o'rta ishonch); rasmiy matnda "von unten/oben" so'zlari yo'q. Orqa tomondagi qirra teshigi/freza uchun `XP↔XM`, `WRKL↔WRKR` almashtirish — topilmadi.
11. **PTX: Holzma/CADlink trim qatorida `QTY_RPT=0` ni qanday talqin qilishi** va `QTY_PARTS` ni sikllarga ko'paytirish shartligi — spetsifikatsiya bor, lekin GibLab namunasi undan farq qiladi; faqat arrada sinov bilan aniqlanadi.
