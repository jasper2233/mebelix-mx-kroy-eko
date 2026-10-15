# Holzma — `.ptx` (Cut Rite PTX 1.13) postprotsessori

Holat: **to'liq** (barcha 10 namunada struktura, miqdorlar va geometriya 100% tekshirildi; bir nechta o'zgarmas maydonlarning ma'nosi taxminiy — 6-bo'limga qarang).

Manba namunalar: `post prtsessorlar/PILNIY APPARAT/Holzma/*.ptx` (10 ta fayl, buyurtmalar 3151–3161).
Mos loyiha fayllari: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` — ya'ni **pastki chiziqli** variant (`NNNN_X.project`). Bo'sh joyli variant (`NNNN X.project`) — eski import fayli (faqat `dl/dw`, CS natijasi yo'q), u PTX bilan mos kelmaydi.

Format Holzma/Weinig **Cut Rite PTX** (versiya `1.13`) standartiga juda yaqin; maydon nomlari quyida shu standart nomlari bilan (taxminiy) berilgan, ammo har bir ma'no namunalar asosida tekshirilgan.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.ptx` (bitta oddiy matn fayl, arxiv emas) |
| Nomlash | `<buyurtma>_<mijoz>_<material nomi>.ptx`, materialdagi bo'shliqlar `_` ga almashtiriladi, ketma-ket bo'shliqlar bittaga qisqaradi (`LDSP  PIKARD` → `LDSP_PIKARD`) |
| Soni | **Har bir material (CS operatsiyasi) uchun bitta fayl**; bitta buyurtmada bir nechta material bo'lsa — bir nechta fayl |
| Kodlash | `cp1251` (Windows-1251). ASCII bo'lmagan matn faqat `OFFCUTS` dagi `Остаток` so'zida uchradi |
| Qator oxiri | `CRLF` (`\r\n`), oxirgi qator ham `CRLF` bilan tugaydi |
| Ajratgich | vergul `,`; qo'shtirnoq ishlatilmaydi (matnda vergul bo'lmasligi kerak) |
| Sonlar | Hamma o'lchamlar butun mm (namunalarda kasr son uchramadi) |
| Birlik | mm |

## 2. Yozuvlar tartibi

```
HEADER                      (1 ta)
JOBS                        (1 ta)
PARTS_REQ × N               (har bir loyiha detali-qatori uchun bittadan, 1..N)
PARTS_INF × N               (xuddi shu tartibda, 1..N)
BOARDS                      (1 ta — list formati)
MATERIALS                   (1 ta)
{ PATTERNS, CUTS × k } × P  (har bir karta (raskroy) — sarlavha + uning kesimlari)
OFFCUTS                     (0 yoki 1 ta — oxirida)
```

Yozuvlar soni (tekshirilgan): `PARTS_REQ` = `PARTS_INF` = loyihadagi shu materialning detal-qatorlari soni (29, 29, 55, 23, 42, 22, 30, 11, 107, 10).

### 2.1 `HEADER`
`HEADER,1.13,3161_mijoz_LDSP_PIKARD,0,0,1`

| # | Maydon | Ma'no | Namunalarda |
|---|---|---|---|
| 1 | VERSION | format versiyasi | doim `1.13` |
| 2 | TITLE | fayl nomi (kengaytmasiz), **25 belgigacha kesiladi** | masalan `3151_mijoz_LMDF_BELI_KAR` |
| 3 | UNITS | 0 = mm (taxmin) | doim `0` |
| 4 | ORIGIN | koordinata boshi (taxmin) | doim `0` |
| 5 | TRIM_TYPE | (taxmin) | doim `1` |

### 2.2 `JOBS`
`JOBS,1,3161 mijoz LDSP PIKARD,,31.08.2026,31.08.2026,,1,,`

| # | Maydon | Ma'no |
|---|---|---|
| 1 | JOB_INDEX | doim `1` (barcha yozuvlarning 1-maydoni ham shu job indeksi) |
| 2 | NAME | fayl nomi, `_` → bo'shliq |
| 3 | DESCRIPTION | bo'sh |
| 4 | ORDER_DATE | `dd.mm.yyyy` — loyiha `project/@date` (ms epoch, mahalliy vaqt) dan |
| 5 | CUT_DATE | 4-maydon bilan bir xil |
| 6 | CUSTOMER | bo'sh |
| 7 | STATUS | doim `1` |
| 8,9 | OPT_PARAM, SAW_PARAM | bo'sh |

### 2.3 `PARTS_REQ` — talab qilinadigan detallar
`PARTS_REQ,1,7,01_006 Fasad,1,498,420,2,0,0,1,2,0,0,0`

| # | Maydon | Ma'no | Manba (loyiha `part`) |
|---|---|---|---|
| 1 | JOB | `1` | — |
| 2 | PART_INDEX | 1..N, CS operatsiyasidagi `<part id>` tartibida | — |
| 3 | CODE | detal nomi | `@name` (masalan `01_006 Fasad`) |
| 4 | MAT_INDEX | doim `1` | — |
| 5 | LENGTH | uzunlik | `@l` |
| 6 | WIDTH | eni | `@w` |
| 7 | QTY_REQ | soni | `@count` |
| 8 | QTY_OVER | doim `0` | — |
| 9 | QTY_UNDER | doim `0` | — |
| 10 | GRAIN | `1` = tekstura bor (aylantirish mumkin emas), `0` = yo'q | `@txt` (`true`→1). 358 qatordan 357 tasida aniq mos; 1 istisno — loyiha keyinroq tahrir qilingan (eski variantda `txt="true"` edi) |
| 11 | QTY_PROD | ishlab chiqarilgan soni | doim = 7-maydon (tekshirildi) |
| 12–14 | — | doim `0` | — |

Muhim: loyihada bir xil kodli detal ikki alohida `<part>` bo'lib kelsa (masalan ikki marta `01_004 polka`, har biri `count=2`), PTX da ham **ikki alohida qator** bo'ladi — birlashtirilmaydi.

### 2.4 `PARTS_INF` — detal haqida qo'shimcha ma'lumot (31 maydon)
`PARTS_INF,1,1,,1,1900,347,3161 mijoz,1-19 Sasna,,1-19 Sasna,1-19 Sasna,A,,A,A,,,LDSP  PIKARD,,,01 shkaf,,316101,,,1,1,316101_01_001,,(CS) LDSP  PIKARD`

| # | Ma'no | Manba |
|---|---|---|
| 1 | JOB = 1 | — |
| 2 | PART_INDEX (PARTS_REQ bilan bir xil) | — |
| 3 | bo'sh | — |
| 4 | doim `1` (ehtimol MAT_INDEX) | — |
| 5,6 | L, W (PARTS_REQ bilan bir xil) | `@l`,`@w` |
| 7 | buyurtma | mahsulot `good/@product.order` (masalan `3161 mijoz`) |
| 8 | kromka nomi — **pastki (bottom)** tomon | `@elbMat` |
| 9 | kromka nomi — **yuqori (top)** | `@eltMat` |
| 10 | kromka nomi — **chap (left)** | `@ellMat` |
| 11 | kromka nomi — **o'ng (right)** | `@elrMat` |
| 12–15 | kromka belgisi (8–11 tartibida) | tegishli `operation typeId="EL"/@elSymbol` (`A`,`B`,`C`) |
| 16,17 | bo'sh | — |
| 18 | material nomi | list `good typeId="sheet"/@name` (ikki bo'shliq saqlanadi) |
| 19,20 | bo'sh | — |
| 21 | mahsulot (izdeliye) nomi | `good typeId="product"/@name` (`01 shkaf`) |
| 22 | bo'sh | — |
| 23 | mahsulot kodi | `good/@code` (`316101`) |
| 24,25 | bo'sh | — |
| 26,27 | doim `1`, `1` | ? |
| 28 | 1-XNC (prisadka) dastur kodi | detalga bog'langan 1-`operation typeId="XNC"/@code` (`316101_01_001`), yo'q bo'lsa bo'sh |
| 29 | 2-XNC dastur kodi | 2-XNC operatsiya (`..._2`), yo'q bo'lsa bo'sh |
| 30 | `(CS) ` + material nomi | — |

Kromka tomonlari: `b`/`t` — detalning uzun (L bo'ylab) qirralari, `l`/`r` — qisqa (W bo'ylab) qirralari (giblab konvensiyasi). Barcha 358 qatorda 8–15, 7, 21, 23, 28, 29-maydonlar loyihaga 100% mos keldi.

### 2.5 `BOARDS`
`BOARDS,1,1,110052,1,2750,1830,10000,1,0,0,2750 x 2750,LDSP  PIKARD,1`

| # | Ma'no | Manba/qiymat |
|---|---|---|
| 1 | JOB | 1 |
| 2 | BRD_INDEX | 1 |
| 3 | list kodi | `sheet/@code` (yo'q bo'lsa bo'sh) |
| 4 | MAT_INDEX | 1 |
| 5,6 | list L, W | `sheet/@l`, `@w` (2750 × 1830) |
| 7 | ombordagi soni | `10000` (CS ichidagi list `<part count="10000">`) |
| 8 | ishlatilgan listlar soni | = Σ `PATTERNS.QTY_RUN` (10/10 tekshirildi) |
| 9,10 | `0`,`0` (narx, stok bayrog'i — taxmin) | |
| 11 | info matni | doim `2750 x 2750` (!) — `L x L`, ehtimol postprotsessordagi xato; 6-bo'lim |
| 12 | material nomi | |
| 13 | GRAIN | doim `1` (CS `csTexture="true"`?) |

### 2.6 `MATERIALS`
`MATERIALS,1,1,110052,LDSP  PIKARD,16,2,3,3,5,5,5,5,0,0,0,1,1,1,1,,1`

| # | Ma'no (taxminiy PTX nomi) | Qiymat va manba |
|---|---|---|
| 3 | CODE | `sheet/@code` |
| 4 | DESC | material nomi |
| 5 | THICK | `sheet/@t` (16) |
| 6 | BOOK (maks. paket) | `2` = ⌊`swPackageHeight`(40) / t(16)⌋ (taxmin; boshqa qalinlik namunasi yo'q) |
| 7 | KERF_RIP | `tool.cutting/@swSawthick` (3; 3159 da 6) |
| 8 | KERF_XCUT | xuddi shu |
| 9–12 | TRIM_FRIP, TRIM_VRIP, TRIM_FXCUT, TRIM_VXCUT | `cTrimL/W` + arra = 2+3 = **5** (3159: 2+6 = **8**), chunki `swTrimIncludeSaw="false"` |
| 13–15 | qo'shimcha trimlar | `0,0,0` |
| 16–19 | qoidalar/bayroqlar | `1,1,1,1` |
| 20 | — | bo'sh |
| 21 | GRAIN | `1` |

### 2.7 `PATTERNS` — karta sarlavhasi
`PATTERNS,1,3,1,0,2,1,2,,0,0`

| # | Ma'no | Qiymatlar |
|---|---|---|
| 2 | PTN_INDEX | 1..P |
| 3 | BRD_INDEX | 1 |
| 4 | TYPE | `0` = oddiy karta (avval bo'ylama/rip), `2` = **head-cut** karta (avval listni uzunligi bo'yicha bo'laklarga bo'lish) |
| 5 | QTY_RUN | shu karta bo'yicha kesiladigan listlar soni |
| 6 | QTY_CYCLES | doim `1` |
| 7 | MAX_BOOK | paketdagi listlar = min(QTY_RUN, BOOK=2) (44/44 karta) |
| 8 | PICTURE | bo'sh |
| 9,10 | vaqtlar | `0,0` |

### 2.8 `CUTS` — kesimlar
`CUTS,1,1,5,0,2,498,2,7,2`

| # | Ma'no | |
|---|---|---|
| 2 | PTN_INDEX | |
| 3 | CUT_INDEX | karta ichida 1..k, uzluksiz |
| 4 | SEQUENCE | doim `0` |
| 5 | FUNCTION (daraja) | `0` head-cut, `1` rip (bo'ylama), `2` crosscut (ko'ndalang), `3`,`4`,`5` — keyingi recut darajalari; `90`/`91`/`92` — 0/1/2-darajadagi **trim** (chekka tozalash) |
| 6 | DIMENSION | bo'lak o'lchami (mm); trim uchun — trim qalinligi (5 yoki 8) |
| 7 | QTY_RPT | shu o'lchamdagi kesim necha marta takrorlanadi (trimda 0) |
| 8 | PART_INDEX | hosil bo'lgan detal (`PARTS_REQ` indeksi), oraliq bo'lak bo'lsa `0` |
| 9 | QTY_PARTS | detallar soni = QTY_RPT (barcha detal kesimlarida tekshirildi) |

## 3. Kesish rejasi qanday kodlanadi

**Daraxt (ierarxiya).** `CUTS` qatorlari karta daraxtini oldindan-tartib (pre-order) ko'rinishida beradi: `FUNCTION = n` bo'lgan qator undan oldingi eng yaqin `FUNCTION = n-1` qatorining farzandi. Har bir farzandlar ro'yxati — ota bo'lak ichida koordinata boshidan boshlab ketma-ket joylashgan bo'laklar.

**O'qlar.** Juft darajalar (0, 2, 4) list **uzunligi** (X, 2750) bo'ylab o'lchanadi, toq darajalar (1, 3, 5) — **eni** (Y, 1830) bo'ylab. Ya'ni:
- `TYPE=2` (head-cut): 0-daraja listni X bo'yicha to'liq enli bo'laklarga bo'ladi → 1-daraja ularni Y bo'yicha polosalarga → 2-daraja X bo'yicha → 3-daraja Y …
- `TYPE=0`: 0-daraja yo'q; 1-daraja (rip) to'liq uzunlikdagi polosalar (Y bo'yicha eni) → 2-daraja X bo'yicha → 3 → 4 → 5.

**Detal o'lchami.** Detal yozilgan kesimda bo'lak = (shu darajadagi DIMENSION) × (otaning boshqa o'qdagi o'lchami). Bo'lak (X,Y) = (L,W) bo'lsa detal aylantirilmagan, (W,L) bo'lsa 90° aylantirilgan. Tekshiruv: 423 ta detal-kesimdan 353 tasi aylantirilmagan, 70 tasi aylantirilgan; `GRAIN=1` detallar **hech qachon** aylantirilmagan. O'lcham mos kelmagan holat — 0.

**Kerf va sig'im.** Har bir farzandlar ro'yxati uchun: `trim + Σ (DIMENSION + kerf) × QTY_RPT ≤ ota o'lchami`. 44 kartaning hech birida oshib ketish yo'q. Qoldiq (oxirgi bo'lakdan keyin) yozilmaydi.

**Trimlar (90/91/92).** Trim faqat **listning asl chekkasidan boshlanadigan** kesimlar seriyasi oldidan qo'yiladi:
- `TYPE=2`: kartaning 1-qatori `90,<trim>` (X chekka); har bir 0-daraja bo'lagidan keyin darhol `91,<trim>` (Y chekka). 2-darajada trim yo'q (X chekkasi allaqachon toza). 24/24 kartada tasdiqlandi.
- `TYPE=0`: 1-qator `91,<trim>`; har bir 1-daraja polosadan keyin darhol `92,<trim>` (polosaning X chekkasi asl chekka). 20/20 kartada tasdiqlandi.
- Ichki darajalarda (3+) trim yo'q. Qarama-qarshi chekka trimi alohida yozilmaydi (qoldiqqa kiradi).

**Miqdorlar va paket.** Detal soni = `QTY_PARTS × Π(ajdodlar QTY_RPT) × PATTERNS.QTY_RUN`. Barcha 358 `PARTS_REQ` uchun bu yig'indi `QTY_REQ` ga aniq teng (masalan 3161: `01_008 bok` — 1+1+1+3×1 = 6). `QTY_RUN>1` bo'lsa `MAX_BOOK=2` (ikki list bir paketda). `BOARDS.QTY_USED = Σ QTY_RUN`.

**Kesimlar tartibi.** Farzandlar fizik joylashuv tartibida (koordinata boshidan); o'lcham bo'yicha saralanmagan. Chiqindi (detalsiz) barg-bo'laklar yozilmaydi — detalsiz qator faqat farzandlari bor oraliq bo'lak uchun bo'ladi (0 ta detalsiz barg).

**Qoldiq (`OFFCUTS`).** `OFFCUTS,1,1,Остаток 2740 x 1100,1,2750,1105,1`
- Faqat **oxirgi karta**ning yuqori darajadagi qoldig'i uchun (namunalarda 7/10 faylda, har doim oxirgi karta). Qoldiq = ota o'lchami − trim − Σ(dim+kerf)×rpt.
- 5,6-maydon — qoldiqning yalpi o'lchami (L, W): TYPE=2 da `(qoldiq, 1830)`, TYPE=0 da `(2750, qoldiq)`.
- 3-maydon matn: `Остаток <A> x <B>` — trim olib tashlangan sof o'lcham: to'liq tomondan `2×trim`, kesilgan tomondan `1×trim` (masalan 2750−10=2740, 1105−5=1100; 3159 da trim 8: 2750−16=2734, 1605−8=1597).
- 2-maydon doim `1`, 4-maydon `1` (MAT_INDEX?), 7-maydon `1` (soni).
- Kichik qoldiqlar (98, 124, 156 mm) yozilmagan; eng kichik yozilgani 561 mm. Chegara ehtimol `cMinDimRegWaste2="500"` (taxmin).

### 3.1 Misol: 3161 (LDSP PIKARD, 1 list, TYPE=2)
```
CUTS 1  90  5            ← X trim
CUTS 2   0  2254         ← head bo'lagi 2254 × 1830
CUTS 3  91  5            ← Y trim
CUTS 4   1  420          ← polosa 2254 × 420
CUTS 5   2  498 ×2 → #7  ← 01_006 Fasad 498×420 (2 dona, aylantirilmagan, GRAIN=1)
CUTS 6   2  868          ← 868 × 420
CUTS 7   3  346    → #4  ← 01_004 polka 868×346
...
CUTS 24  0  352          ← 2-head bo'lagi 352 × 1830
CUTS 28  1  300 ×3       ← 3 polosa 352×300
CUTS 29  2  346    → #9  ← har birida 346×300 = 01_008 bok (300×346, aylantirilgan)
CUTS 30  0  100          ← 3-head bo'lagi 100 × 1830
CUTS 32  1  868    → #10 ← 01_009 sokl 100×868 (0-darajadan to'g'ridan-to'g'ri)
```
X: 5 + (2254+3)+(352+3)+(100+3) = 2720 ≤ 2750 (qoldiq 30 → OFFCUTS yo'q).

## 4. Loyiha → PTX moslik (tekshirilgan)

| Loyiha (`*.project`) | PTX |
|---|---|
| `project/@date` (ms) | `JOBS` 4,5 (`dd.mm.yyyy`) |
| CS `operation` → `material/@id` → `good typeId="sheet"` (`@code,@name,@l,@w,@t`) | `BOARDS` 3,5,6,12; `MATERIALS` 3,4,5 |
| CS `@tool1` → `good typeId="tool.cutting"/@swSawthick` | `MATERIALS` 7,8 (kerf) |
| CS `@cTrimL/@cTrimW` + `swSawthick` (`swTrimIncludeSaw=false`) | `MATERIALS` 9–12, `CUTS` 90/91/92 dimension |
| `swPackageHeight` / `t` | `MATERIALS` 6 (book) |
| CS ichidagi `<part id>` tartibi (mahsulot detallari) | `PARTS_REQ/INF` indeksi |
| `part/@name, @l, @w, @count, @txt` | `PARTS_REQ` 3,5,6,7(=11),10 |
| `part/@elbMat, @eltMat, @ellMat, @elrMat` + EL `@elSymbol` | `PARTS_INF` 8–15 |
| mahsulot `@product.order, @name, @code` | `PARTS_INF` 7, 21, 23 |
| XNC `operation/@code` (detalga bog'langan) | `PARTS_INF` 28, 29 |
| CS `data` (binar natija) | o'qilmadi; reja to'liq `PATTERNS/CUTS` dan olinadi |

Tekshirilgan namunalar (hammasi, 10/10): nomi/L/W/soni bo'yicha 0 nomuvofiqlik; jami soni: 61, 39, 70, 33, 73, 36, 30, 20, 165, 18 dona — loyiha va PTX bir xil.
Aniq misollar:
- **3161**: `01_001 bok` l=1900 w=347 count=1, `elb/ell/elr`=`1-19 Sasna` → `PARTS_REQ,1,1,01_001 bok,1,1900,347,1,0,0,0,1,…` va `PARTS_INF …,1-19 Sasna,,1-19 Sasna,1-19 Sasna,A,,A,A,…`.
- **3155**: `01_019 bok` 2484×303, txt=true, faqat `elt` → `PARTS_REQ,1,1,01_019 bok,1,2484,303,1,0,0,1,1,…`, `PARTS_INF …,,1-19 votan,,,,A,,,…,01 prehojka,,315501,…,315501_01_019,,(CS) LMDF DUB VATAN`.
- **3159**: arra `swSawthick=6` → `MATERIALS …,16,2,6,6,8,8,8,8,…`, trim kesimlar `90,8`/`91,8`/`92,8`; detalda 2 ta XNC → `…,315901_01_001,315901_01_001_2,…`; qoldiq `Остаток 2734 x 1597,1,2750,1605`.

Eslatma: barcha namunalarda `l = cl = dl`, shuning uchun PTX `@l` (yoki `@cl`)ni olishini ajratib bo'lmadi — 6-bo'lim.

## 5. Minimal qayta tiklangan misol (anonim)

2 detal: `01_001 bok` 720×560 ×2 (teksturasiz, chap+o'ng kromka), `01_002 polka` 1200×400 ×1 (teksturali). List 2750×1830, kerf 3, trim 5. TYPE=0 karta.

```
HEADER,1.13,9001_mijoz_LDSP_OQ,0,0,1
JOBS,1,9001 mijoz LDSP OQ,,01.10.2026,01.10.2026,,1,,
PARTS_REQ,1,1,01_001 bok,1,720,560,2,0,0,0,2,0,0,0
PARTS_REQ,1,2,01_002 polka,1,1200,400,1,0,0,1,1,0,0,0
PARTS_INF,1,1,,1,720,560,9001 mijoz,,,1-19 Oq,1-19 Oq,,,A,A,,,LDSP OQ,,,01 shkaf,,900101,,,1,1,,,(CS) LDSP OQ
PARTS_INF,1,2,,1,1200,400,9001 mijoz,1-19 Oq,,,,A,,,,,,LDSP OQ,,,01 shkaf,,900101,,,1,1,,,(CS) LDSP OQ
BOARDS,1,1,,1,2750,1830,10000,1,0,0,2750 x 2750,LDSP OQ,1
MATERIALS,1,1,,LDSP OQ,16,2,3,3,5,5,5,5,0,0,0,1,1,1,1,,1
PATTERNS,1,1,1,0,1,1,1,,0,0
CUTS,1,1,1,0,91,5,0,0,0
CUTS,1,1,2,0,1,560,1,0,0
CUTS,1,1,3,0,92,5,0,0,0
CUTS,1,1,4,0,2,720,2,1,2
CUTS,1,1,5,0,1,400,1,0,0
CUTS,1,1,6,0,92,5,0,0,0
CUTS,1,1,7,0,2,1200,1,2,1
OFFCUTS,1,1,Остаток 2740 x 854,1,2750,859,1
```
Tekshiruv: Y: 5 + 563 + 403 = 971 → qoldiq 1830−971 = 859 (sof 2740 × 854). X: 5 + 2×723 = 1451 ≤ 2750. Fayl `cp1251`, `CRLF`.

Generatsiya algoritmi (qisqa): optimallashtirish natijasidagi har bir guillotine kartani daraxt sifatida chiqarish; juft daraja = X, toq = Y; har bir asl chekkadan boshlanadigan seriya oldiga `9n,trim`; bir xil ketma-ket bo'laklarni `QTY_RPT` ga yig'ish; bir xil kartali listlarni `QTY_RUN` ga yig'ish.

## 6. Noaniq joylar — savollar

1. `BOARDS` 11-maydon doim `2750 x 2750` (`L x W` emas). Bu Holzma uchun ahamiyatsiz izohmi yoki xato? Biz `2750 x 1830` yozsak bo'ladimi?
2. `MATERIALS` 6-maydon (`2`) — maksimal paket (book). Formula `⌊swPackageHeight / qalinlik⌋` to'g'rimi? (barcha namunalar 16 mm; masalan 8 mm yoki 25 mm material uchun qanday?)
3. Detal o'lchami uchun `@l/@w` mi yoki `@cl/@cw` (fugovka/pripusk qo'shilgan arra o'lchami)? Namunalarda farq yo'q edi — fugovkali buyurtmadan PTX namunasi kerak.
4. `OFFCUTS` qachon yoziladi: faqat oxirgi kartadami yoki har qanday kartada ≥ 500 mm (`cMinDimRegWaste2`) qoldiqda? Qoldiq `QTY_RUN>1` kartada bo'lsa 7-maydon (soni) o'zgaradimi?
5. Kasr o'lchamlar (masalan 346.5) qanday yoziladi — nuqta bilanmi? Namunalarda yo'q.
6. `HEADER` 3–5 (`0,0,1`), `MATERIALS` 13–19 (`0,0,0,1,1,1,1`), `PARTS_INF` 4, 26, 27 (`1`) — mashina sozlamasi sifatida o'zgarmas qoldirsak bo'ladimi?
7. TYPE=2 (head-cut) va TYPE=0 kartalardan qaysi birini tanlash — optimallashtiruvchi qarori; Holzma'da `TYPE=1` (yoki boshqa) ham qo'llanadimi? Namunalarda faqat 0 va 2.
8. `GRAIN` faqat 0/1 uchradi. Tekstura eni bo'ylab (`2`) kerak bo'ladimi?
9. Detal nomida vergul yoki kirill harflari bo'lsa (cp1251) — mashina qabul qiladimi, qanday ekranlash kerak?
