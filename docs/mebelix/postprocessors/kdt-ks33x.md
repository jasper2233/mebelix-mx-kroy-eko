# KDT KS33X — `.zip` → `NUM=k … .qk` (ikkilik massiv) + `.lbd` (Java DataOutput) postprotsessori

Holat: **qisman** — kesish rejasi **to'liq**: 30/30 `.qk` fayl bayt-ma-bayt qayta yasaldi, 30/30 `.lbd` daraxt qismi aynan mos, `.lbd` fayl sintaksisi 100 % o'qildi va qayta yozildi. Ochiq qolgani — `.lbd` ichidagi **etiketka blobi** (base64(zlib) — etiketka o'zgaruvchilari + SVG chizma) va «kitob» bo'lish qoidasining tasdig'i (6-bo'lim).

Manba: `post prtsessorlar/PILNIY APPARAT/KDT KS33X/*.zip` (7 ta: 3151, 3153, 3155, 3156, 3157, 3159, 3161).
Mos loyiha: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` (pastki chiziqli variant).
Yangi versiya (`KDT Новий версия`) — shu formatning kichik farqli varianti: `kdt-novaya-versiya.md`.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Tashqi fayl | `<loyiha nomi>_<material, bo'shliqlar→_>.zip`, masalan `3161_mijoz_LDSP_PIKARD.zip` |
| Zip ichida (papkasiz) | **har bir karta (raskroy sxemasi) uchun 2 fayl**, shu tartibda: `NUM=<k>   PANELS( <n> x 1 = <n> ).qk` va `… .lbd`; `k` = karta raqami (1..), `n` = shu sxema bo'yicha listlar soni. `NUM=<k>` dan keyin **3 ta bo'shliq**; `PANELS(` dan keyin va `)` dan oldin bitta bo'shliq. Misol: `NUM=1   PANELS( 2 x 1 = 2 ).qk` |
| Zip | deflate, flag `0x0808` |
| Soni | buyurtmaga 1 zip — faqat **birinchi CS operatsiyasi**; zip ichida kartalar soni = `TOTALESCHEMI` (6, 5, 3, 7, 5, 3, 1) |
| `.qk` | **qat'iy 2 720 032 bayt**, little-endian `float32`/`int32` massiv (ko'p qismi nol) |
| `.lbd` | Java `DataOutputStream` formati (big-endian), matnlar `writeUTF` (2 bayt uzunlik + UTF-8) — kirill to'g'ridan-to'g'ri UTF-8 |
| Birlik | mm (float32/double), butun qiymatlar |

## 2. `.qk` tuzilmasi

Fayl — bitta `float32` (arra qalinligi) va undan keyin ikkita jadval: **A (geometriya)** va **B (miqdor)**. Hamma joy nol, faqat quyidagi yozuvlar to'ldiriladi (30/30 faylda bitta ham «tushuntirilmagan» nol bo'lmagan bayt qolmadi).

### 2.1 Indekslash
Kesim daraxtining har bir tuguniga daraja `L` va «rank» beriladi:
* `L=1` (polosa): `r1 = j` (0-dan, polosaning tartibi);
* `L=2`: `r2 = 20·r1 + j`;  `L=3`: `r3 = 20·r2 + j`;  `L=4`: `r4 = 20·r3 + j` (j — ota ichidagi tartib, 0..19).

Ya'ni har tugunda **≤ 20 farzand** joyi ajratilgan.

### 2.2 Jadval A — geometriya (yozuv 12 bayt: `f32 f0, f32 f1, f32 f2`)
Yozuv manzili: `4 + 12·i`.

| `i` | Mazmun |
|---|---|
| 0 | (bo'sh) |
| 1 | karta: `(trim+kerf, l, w)` — l = 1-daraja kesimlar bo'ylab o'lcham (G57 `DIMY`), w — ko'ndalang (`DIMX`) |
| `11 + r1` | 1-daraja: `(trim+kerf, w, cut)` |
| `101 + r2` | 2-daraja: `(0, ota cut, cut)` |
| `1001 + r3` | 3-daraja: `(0, ota cut, cut)` |
| 4-daraja | **A jadvalida yo'q** |

`trim+kerf` = `cTrimL + swSawthick` (5; 3159 da 8). Jadval A `i < 20000` (240 004 baytgacha).

### 2.3 Jadval B — miqdor (yozuv 12 bayt: `f32 cut, i32 0, i32 takror`)
Boshi `B = 4 + 12·20000 = 240004`; yozuv manzili `B + 12·i`.

| `i` | Mazmun |
|---|---|
| 1 | karta: `(f32 l, f32 w, i32 0)` |
| `2 + r1` | 1-daraja |
| `102 + r2` | 2-daraja |
| `1002 + r3` | 3-daraja |
| `10022 + r4` | 4-daraja |

`takror` — shu tugun necha marta ketma-ket kesiladi (2.4 dagi bo'lish qoidasidan keyin).
`kerf` — fayl boshidagi `float32` (offset 0).

### 2.4 Daraxt qanday tayyorlanadi (optimallashtiruvchi daraxtidan)
1. **1-daraja (polosalar) tartibi teskari** (G57/optimizator oxirgi polosasi birinchi bo'ladi). Pastki darajalar tartibi o'zgarmaydi.
2. **Farzandli bo'lak** `n` marta takrorlansa, u `m = max(1, ⌊swPackageHeight / (t · listlar_soni)⌋)` dan oshmaydigan bo'laklarga bo'linadi: 40/(16·1) = 2 → `3 → 2+1`, `4 → 2+2`, `7 → 2+2+2+1`; 2 listli sxemada 40/(16·2)=1 → `3 → 1+1+1`. (G57/GDrive da shu bo'lak `QTARIP=3` bitta yozuv.) Barg (tayyor detal) takrori bo'linmaydi.
   Teskari tartib **avval**, bo'lish keyin qo'llanadi (3151 da `40 ×3` → `40 ×2`, `40 ×1`).
3. Ishbop qoldiq `.qk` ga yozilmaydi (faqat `.lbd` da).

Tekshiruv: 30/30 karta — leaf/bo'lak takrorlari 247 + 201 holatda qoida bilan mos.

## 3. `.lbd` tuzilmasi (Java DataOutputStream, big-endian)

```
int32   N                      — 1-daraja tugunlar soni (qoldiq bilan)
Node × N
int32   M                      — etiketkalar soni
{ int32 kalit; UTF csv } × M
```
`Node`:
```
bool    guruh                  — 1 = bo'lak («Полоса»), 0 = detal/qoldiq
UTF     tur                    — "Полоса" | "Деталь" | "Остаток"
double  cut                    — kesib olinadigan o'lcham, mm
int32   takror
agar guruh:  int32 farzandlar_soni; Node × farzandlar_soni
aks holda:   int32 idx; UTF kod; double l; double w; bool qoldiq
```
| Maydon (detal) | Ma'no | Manba |
|---|---|---|
| `idx` | loyiha detal `@id` | 3156: `idx=34` |
| `kod` | CS operatsiyadagi tartib raqami (matn) | 3156: id 34 → `"15"` (G57 `IE=15`) |
| `l`, `w` | detal `@l`, `@w` (aylantirilgan bo'lsa ham asl yo'nalishda) | 247/247 mos |
| `qoldiq` | 0 | |
| **Qoldiq** («Остаток») | 1-darajaning **oxirgi** elementi; `cut` = qoldiqning kesish yo'nalishidagi o'lchami (trim qilingan), `idx` = qoldiq id (3151: 77, 3155: 2, 3156: 32, 3157: 2, 3159: 12 — qoida noma'lum), `kod = "Д1"`, `l, w` — trim qilingan o'lchamlar (masalan 2740×1100; KDT XML dagi trim qilinmagan 2750×1105 dan har chetdan 5 mm), `qoldiq = 1` | 5/5 qoldiqli faylda |

Daraxt `.qk` dagi bilan **bir xil** (2.4 qoidalari, teskari 1-daraja, bo'lingan takrorlar) — 30/30 mos.

### 3.1 Etiketka yozuvlari
Har bir **shu kartada uchraydigan noyob detal** uchun bitta yozuv (+ qoldiq bo'lsa bitta). `kalit` = loyiha detal `@id`. Tartib — Java `HashMap<Integer>` iteratsiyasi: savat = `id & (sig'im−1)`, sig'im 16 dan boshlab `yozuvlar > 0,75·sig'im` bo'lsa 2 baravar (30/30 faylda shu tartib; masalan 3155 4-karta: 39, 40, 26, 42, 47).

Detal CSV (vergul bilan, 31 maydon):

| # | Maydon | Misol / manba |
|---|---|---|
| 0 | shablon nomi | `detail.fme` |
| 1 | — | bo'sh |
| 2 | miqdor | loyiha `count` (**yangi versiyada** — shu kartadagi bitta listdagi soni) |
| 3 | tartib raqami | CS operatsiyadagi `IE` |
| 4 | — | doim `1` |
| 5 | fayl nomi | zip nomi (kengaytmasiz) |
| 6, 7 | l, w | detal o'lchami |
| 8 | detal nomi | `@name`, kirill o'z holicha |
| 9 | miqdor | loyiha `count` |
| 10–13 | kromka belgilari: **chap, o'ng, yuqori, past** | EL operatsiyasi `elSymbol` (masalan `A`) yoki bo'sh; `ell/elr/elt/elb` bilan 218/218 mos |
| 14 | tekstura | `true/false` = detal `@txt` (217/218; 3161 dagi 1 istisno) |
| 15–29 | — | bo'sh |
| 30 | blob | base64(zlib(…)) — 3.2 |

Qoldiq CSV: `rest.fme,,1,1,<l>,<w>,<maydon m², 3 kasr>,<fayl nomi>,` + 22 bo'sh maydon + blob; maydon = `cBusinessWasteAmount` (3155: `2740,1100,3.014`).

### 3.2 Etiketka blobi (base64 → zlib → ikkilik)
* Kalit-qiymat ro'yxati: har yozuv `u8 tur` (0 matn, 1 int32, 2 double, 3 bool) + `u8 1` + `u32 kalit_uzunligi` + kalit + `u8 bor(0/1)` + qiymat (matn: `u32 uzunlik` + bayt). Matnlarda ayrim lotin harflari «ortiqcha uzun» UTF-8 (`C1 xx`) shaklida yozilgan (masalan `c1 b0` = `p`) — dekoder buni qabul qilishi kerak.
* Kalitlar (~140 ta): `project.name/date/currency/crc16/crc32/uuid`, `material.name/code`, `product.name/code/index`, `operation.*`, `part.id`, `name`, `length/width`, `detail.*`, `afterPreMilling.*`, `cutting.*`, `thick`, `waste/business/txt`, `count/totalCount/usedCount`, kromkalar `et*/eb*/el*/er*` (kod, nom, belgi, qalinlik, en), paz `gr*`, `drill/mill/groove`, `XNC1..5`, `part.position`, `product.order` va h.k. — mijoz ismi ham bor.
* Keyin `0A` + `u32 uzunlik` + **SVG** (detal chizmasi, teshiklar bilan) va oxirida `FF`.
* Bu — loyiha dasturining ichki etiketka ma'lumoti. Loyiha qoidasi (CLAUDE.md, 14-band) bo'yicha **biz uni nusxalamaymiz**; stanok uni talab qilsa, o'z (minimal) blobimizni yasash kerak bo'ladi — 6-bo'lim, savol 1.

## 4. Loyiha → fayl moslashuvi (tekshirilgan misollar, anonim)

| Loyiha | Fayl | Misol |
|---|---|---|
| `swSawthick` | `.qk` offset 0 | 3159: `6.0`; qolganlari `3.0` |
| `cTrimL + swSawthick` | A[1].f0, A[11+r1].f0 | 5.0; 3159: 8.0 |
| karta o'lchami | A[1] = (5, l, w), B[1] = (l, w, 0) | 3161: `(5, 2750, 1830)`; 3156 1-karta: `(5, 1830, 2750)` |
| polosalar (teskari) | A[11..] | 3161: `(5,1830,100)`, `(5,1830,352)`, `(5,1830,2254)` (G57 da 2254, 352, 100) |
| 2-daraja | A[101+20·r1+j] | 3161 2254-polosa (r1=2): A[141..145] = `(0,2254,420)`, `(0,2254,346)`, `(0,2254,346)`, `(0,2254,347)`, `(0,2254,347)` |
| takror | B | 3161 352-polosa: B[122..124] = `868×1`, `300×2`, `300×1` (G57 da `300 ×3`) |
| 4-daraja | B[10022+r4] | 3161: 420-ustun ichidagi 868 lik bo'lakdan 346 (r1=2, r2=40, r3=801, r4=16020 → offset 552508) |
| listlar soni | zip ichidagi nom | 3157: `NUM=1   PANELS( 2 x 1 = 2 ).qk` |
| detal id, tartib, o'lcham | `.lbd` detal tugunlari | 3161: `Деталь 498 ×2 idx=7 kod="7" 498×420` |
| qoldiq | `.lbd` «Остаток» + `rest.fme` | 3159: `cut=1597`, `2734×1597`, `4.366` m² |

## 5. Minimal misol (sintetik, anonim)

List 2750×1830×16, kerf 3, trim 2; detal 1 (id 1) 1000×500 ×2, detal 2 (id 2) 600×400 ×1; bitta karta, 1 list. Daraxt: polosa 1000 → [detal 500 ×2, bo'lak 400 → detal 600].

Zip: `9001_mijoz_LDSP_OQ.zip` → `NUM=1   PANELS( 1 x 1 = 1 ).qk`, `NUM=1   PANELS( 1 x 1 = 1 ).lbd`.

`.qk` (2 720 032 bayt, nol bo'lmagan so'zlar — offset: qiymat):
```
0      : 3.0                     kerf
16..24 : 5.0, 2750.0, 1830.0     A[1] karta
136..144: 5.0, 1830.0, 1000.0    A[11]  polosa 1000
1216..1224: 0, 1000.0, 500.0     A[101] (r2=0)  detal 500
1228..1236: 0, 1000.0, 400.0     A[102] (r2=1)  bo'lak 400
12256..12264: 0, 400.0, 600.0    A[1001+20] (r3=20) detal 600
240016..240024: 2750.0, 1830.0, 0      B[1]
240028..240036: 1000.0, 0, 1           B[2]   polosa ×1
241228..241236: 500.0, 0, 2            B[102] detal 500 ×2
241240..241248: 400.0, 0, 1            B[103] bo'lak 400 ×1
252268..252276: 600.0, 0, 1            B[1022] detal 600 ×1
```
`.lbd` daraxt qismi (hex):
```
00 00 00 01                                   N=1
01 00 0C D0 9F D0 BE D0 BB D0 BE D1 81 D0 B0   guruh, "Полоса"
40 8F 40 00 00 00 00 00  00 00 00 01  00 00 00 02     cut=1000.0, ×1, 2 farzand
00 00 0C D0 94 D0 B5 D1 82 D0 B0 D0 BB D1 8C   detal, "Деталь"
40 7F 40 00 00 00 00 00  00 00 00 02  00 00 00 01  00 01 31     cut=500, ×2, idx=1, kod "1"
40 8F 40 00 00 00 00 00  40 7F 40 00 00 00 00 00  00     l=1000, w=500, qoldiq=0
01 00 0C D0 9F … D0 B0  40 79 00 00 00 00 00 00  00 00 00 01  00 00 00 01   "Полоса" 400 ×1, 1 farzand
00 00 0C D0 94 … D1 8C  40 82 C0 00 00 00 00 00  00 00 00 01  00 00 00 02  00 01 32
40 82 C0 00 00 00 00 00  40 79 00 00 00 00 00 00  00          detal 600, idx=2, kod "2", 600×400
00 00 00 02                                   M=2 etiketka
00 00 00 01  <UTF "detail.fme,,2,1,1,9001_mijoz_LDSP_OQ,1000,500,01_001 bok,2,,,,,false,,,,,,,,,,,,,,,,<blob>">
00 00 00 02  <UTF "detail.fme,,1,2,1,9001_mijoz_LDSP_OQ,600,400,01_002 polka,1,,,,,false,,,,,,,,,,,,,,,,<blob>">
```

## 6. Noaniq joylar va savollar

1. **Etiketka blobi** (`detail.fme`/`rest.fme` CSV ning oxirgi maydoni) stanok/etiketka printeriga kerakmi? Kerak bo'lsa — qaysi kalitlar majburiy? (Biz loyiha dasturining ichki blobini nusxalamaymiz; bo'sh yoki o'zimiz yasagan minimal blob qabul qilinadimi?)
2. Takrorni bo'lish qoidasi `⌊swPackageHeight / (t·listlar)⌋` (40/16=2) faqat 3 xil qiymat bilan tasdiqlangan (t=16, paket 40, listlar 1–2). Boshqa qalinlik/paket balandligida tekshirish kerak.
3. Qoldiq `idx` (77, 2, 32, 2, 12) qayerdan olinadi? Loyihadagi waste part id bilan ham mos emas (3155: loyihada 3, faylda 2). Ixtiyoriy noyob son yetarlimi?
4. Massiv chegaralari: 1-darajada ≤ 90 polosa, har tugunda ≤ 20 farzand, 3-darajadan keyin A jadvalida joy yo'q (4-daraja faqat B da). Chuqurroq (5-daraja) yoki 20 dan ko'p farzandli kesimda stanok qanday ishlaydi?
5. Karta raqami ≥ 10 bo'lsa fayl nomidagi bo'shliqlar soni (`NUM=10  PANELS…` yoki 3 ta) — namunada 7 tagacha.
6. `PANELS( n x 1 = n )` dagi `x 1` nima (kitoblar soni?) — doim 1.
7. Etiketka CSV 14-maydon (`txt`) bir holatda loyiha bilan mos emas (3161 `01_009 sokl`: `txt=false`, faylda `true`) — loyiha eksportdan keyin o'zgarganmi?
8. Faqat birinchi material eksport qilinadi — har material uchun alohida zip kerakmi?
