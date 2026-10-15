# Biesse Selco NC300 — postprotsessor formati (teskari hujjatlash)

> Manba: `post prtsessorlar/PILNIY APPARAT/Biesse Selco NC300/*.zip` (12 ta buyurtma: 3168, 3169, 3170, 3171, 3173, 3174, 3175, 3177, 3178, 3179, 3180, 3182) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` fayllari.
> Mijoz ismlari hujjatda «mijoz» bilan almashtirilgan. Dasturiy binar fayllar o'qilmagan — faqat namuna chiqish fayllari va kompaniya `.project` XML fayllari tahlil qilingan.
> Xuddi shu buyurtmalar uchun **Biesse Selco OSI** (`.xml`) namunalari ham bor — ular bilan kesish dasturlari solishtirildi (qarang: `biesse-selco-osi.md`).

**Tushunish darajasi: to'liq (kesish qismi) / deyarli to'liq (etiketka qismi).**
Barcha 76 fayl (12 `dist` + 64 `tagli`) shu hujjatdagi qoidalar bo'yicha **bayt-baayt aynan qayta generatsiya qilindi** (`B_LABEL` ichidagi base64/zlib bloklari ham). Ochiq qolgan narsa — ayrim doimiy maydonlarning mashinadagi ma'nosi (pastda savollar).

---

## 1. Chiqadigan fayllar

| Xususiyat | Qiymat |
|---|---|
| Konteyner | bitta `.zip` har bir buyurtma × material uchun (namunalarda har zipda faqat **bitta material**) |
| Zip nomi | `<NOME>.zip`, `NOME` = loyiha nomining **birinchi 8 belgisi** (masalan `3171_<mijoz>` → `3171_Mij` tipidagi 8 belgili nom; DOS 8.3 cheklovi) |
| Zip ichidagi papkalar | `dist/<NOME>` (kengaytmasiz, 1 dona) va `tagli/<NOME>.001`, `tagli/<NOME>.002`, … (har bir kesish kartasi/pattern uchun bittadan, 3 xonali nol bilan to'ldirilgan raqam) |
| Zip siqish | Deflate (compress_type=8) |
| Kodlash | Namunalarda faqat ASCII (`MAT`/`COMM` lotin). Kirill uchun cp1251 deb taxmin qilinadi — **tasdiqlanmagan** (savol 1) |
| Qator oxiri | `CRLF` (`\r\n`), fayl oxirida ham `CRLF` bor |
| Chekinish | TAB (`\t`); `dist` da ichki darajalar 2 ta TAB |
| O'nlik ajratgich | ishlatilmaydi — barcha o'lchamlar **butun son, 1/100 mm** (`DIM=140000` = 1400.00 mm) |
| Soni | `dist` 1 ta + `tagli` = patternlar soni (namunalarda 2…10) |

`dist` ning birinchi qatori — `DIS` yozuvlari soni (= `tagli` fayllari soni).

Bitta loyihada bir nechta material (masalan LDSP + XDF orqa devor) bo'lsa ham namunadagi zip faqat bitta materialni o'z ichiga oladi; `NOME` 8 belgiga qisqargani uchun boshqa material zipi **aynan shu nomni** oladi (savol 2).

---

## 2. Fayl tuzilmasi

### 2.1 `dist/<NOME>` — buyurtma ro'yxati ("distinta")

```
<N>                       ← DIS yozuvlari soni
B_FDIS
	DAT
		NOME="<NOME>"         ← 8 belgi (loyiha nomi qisqartmasi)
		PROX=""               ← doim bo'sh
		CPI=0                 ← doim 0
		COMM="<product.order>"← masalan "3171 mijoz" (loyiha/buyurtma nomi, to'liq)
B_DIS
	DIS                     ← har bir tagli uchun takrorlanadi
		NM=<i>              ← 1..N
		NPG="<NOME>.<iii>"  ← tagli fayl nomi
		QTA=<q>             ← shu patterndan nechta list kesiladi (= tagli DAT.QTA)
		ESE=0               ← bajarilgan soni (doim 0)
		OPZ=""              ← doim bo'sh
		COM="<L>x<W>x<T>: <material>"  ← mm, butun; 40 belgigacha QIRQILADI
E_DIS
E_FDIS
```

`COM` 40 belgidan uzun bo'lsa kesiladi: `"2750x1830x16: LDSP METALIK SHAGREN 5.03 "` (asli `... 5.03 kv`). Tagli ichidagi `MAT` esa to'liq yoziladi.

### 2.2 `tagli/<NOME>.<iii>` — bitta kesish kartasi (pattern)

Bo'limlar ketma-ketligi qat'iy: `B_SCH` → `B_DAT…E_DAT` → `B_REF…E_REF` → `B_CUT…E_CUT` → `E_SCH` → `B_LABEL…E_LABEL`.

#### B_DAT

| Maydon | Tur | Namuna qiymatlari | Ma'no | Doimiy/ma'lumot |
|---|---|---|---|---|
| `NM` | "str" | `"3171_Mij.001"` | fayl nomi | ma'lumot |
| `CMM` | "str" | `""` | izoh | doim bo'sh |
| `MAT` | "str" | `"LDSP DUB VATAN TEKSTURA"` | material nomi (CS operatsiyasidagi sheet `good@name`) | ma'lumot |
| `DAY` | "str" | `""` | sana? | doim bo'sh |
| `OPZ` | "str" | `""` | opsiyalar | doim bo'sh |
| `X` | int, 1/100 mm | `275000` | list uzunligi (L) | ma'lumot (64/64 = 2750) |
| `Y` | int, 1/100 mm | `183000`, `45000` | list eni (W) | ma'lumot (bitta 2750×450 qoldiq list) |
| `Z` | int, 1/100 mm | `1600` | qalinlik | ma'lumot |
| `HP` | int, 1/100 mm | `4000` | paket (kitob) balandligi = 40 mm. Loyihadagi `tool.cutting@swPackageHeight="40"` ga mos | doimiy (sozlama) |
| `VL` | int | `0` | noma'lum (tolalik? tezlik?) | doim 0 |
| `VT` | int | `0` | noma'lum | doim 0 |
| `QTA` | int | `1`, `2` | shu patterndan kesiladigan listlar soni | ma'lumot |

#### B_REF (trim/refilo parametrlari) — hammasi doimiy

| Maydon | Qiymat | Taxminiy ma'no |
|---|---|---|
| `FORZ` | `0` | majburiy rejim (forzatura)? |
| `ROL` | `500` | uzunlik bo'yicha trim = 5.00 mm |
| `RMADL` | `500` | uzunlik bo'yicha "ona" (asosiy) trim? |
| `RMIDL` | `500` | uzunlik bo'yicha oraliq trim? |
| `ROT` | `500` | en bo'yicha trim = 5.00 mm |
| `RMADT` | `500` | en bo'yicha asosiy trim? |
| `RMIDT` | `500` | en bo'yicha oraliq trim? |
| `RMIP` | `500` | minimal bo'lak trim? |

5.00 mm qiymati optimizator natijasi bilan mos: list chetlaridan har tomondan 5 mm olinadi (loyihada `cTrimL=cTrimW=2` + `swSawthick=3`, `swTrimIncludeSaw=false` → 2+3 = 5 mm). Qoldiq (`rest`) etiketkalari ham `2740×…`, `…×1820` (= 2750−10, 1830−10).

#### B_CUT — kesish ketma-ketligi

```
	CUT=<n>          ← 1..K tartib raqami
		COD="<kod>"  ← kesish darajasi/yo'nalishi
		DIM=<1/100 mm>
		QTA=<takror>
```

Kodlar (namunada: `1` 98, `2` 236, `4` 80, `5` 197, `Z1` 374, `Z2` 109 ta; `Z3/Z4` faqat OSI dagi 6-burilishli loyihalarda uchradi):

| Kod | Daraja | O'lcham qaysi o'q bo'yicha |
|---|---|---|
| `1` | 1 (bosh/strip kesish) | X (list uzunligi, 2750) bo'ylab |
| `2` | 2 (`1` ichida) | Y bo'ylab |
| `4` | 1 (bosh kesish, **burilgan**) | Y (list eni, 1830) bo'ylab |
| `5` | 2 (`4` ichida) | X bo'ylab |
| `Z1` | 3 | 1-daraja bilan bir xil o'q |
| `Z2` | 4 | 2-daraja bilan bir xil o'q |
| `Z3`, `Z4`, … | 5, 6, … | navbatma-navbat almashadi |

Bitta patternda 1-daraja kodi faqat `1` yoki faqat `4` (64 tadan 35 ta `1`, 29 ta `4`; aralash yo'q). Ya'ni `1/2` = "avval uzunlik bo'ylab tasma", `4/5` = "avval en bo'ylab tasma".

**Daraxt qoidasi (tekshirilgan):** ro'yxat — kesish daraxtining *preorder* yurishi. Har bir yozuvning ota-onasi — undan oldingi, darajasi bittaga kichik bo'lgan oxirgi yozuv. `QTA=q` — butun **pastki daraxt** bilan birga q marta takrorlash (`Z1:65 QTA=2` ostidagi `Z2:1920` har ikkala 65 lik tasmaga tegishli). Farzandi yo'q yozuv — tayyor detal; uning ikkinchi o'lchami ota-onasining o'lchamiga teng. Ota-ona ichida farzandlar to'ldirmagan qism — chiqindi (yoki oxirgi patternda — biznes-qoldiq).

NC300 **ketma-ket kelgan bir xil pastki daraxtlarni har doim birlashtiradi** (QTA ga yig'adi) — 64 faylda birorta ham birlashtirilmagan ketma-ket bir xil qo'shni yo'q. OSI esa faqat bir xil detal bo'lsa birlashtiradi (OSI hujjatiga qarang). Ikkala format QTA/Rep yoyilgandan keyin **64/64 patternda aynan bir xil**.

Arra/trim (optimizator xulqi, format emas): 1–2-darajada `ota_o'lcham ≥ 10 + Σ(o'lcham×q) + 3×(n−1)` (ikki chetdan 5 mm, orada arra 3 mm), chuqurroq darajalarda odatda `≥ 5 + Σ + 3×(n−1)` (bitta istisno — chiqindisiz ichki kesishda faqat 3 mm). Format faqat **sof detal o'lchamini** yozadi; trim va arra qalinligini mashina o'zi qo'llaydi.

#### B_LABEL — etiketkalar bloki

Har qatori `\t` + 80 belgili base64 bo'lagi (oxirgisi qisqa). Barcha qatorlar **bitta uzluksiz base64 oqim** (faqat oxirida `=` padding). Dekod qilingan ikkilik tuzilma (big-endian):

```
int32  R                      ← "rest" (biznes-qoldiq) etiketkalar soni (0 yoki 1)
R × { REC ; int32 restQty }   ← restQty namunada doim 1
int32  N                      ← detal etiketkalari soni
N × REC
int32  G (= N)                ← joylashuv guruhlari soni
G × { int32 c ; c × { int32 X_1/100mm ; int32 Y_1/100mm ; int32 labelIndex } }
```

`REC` = `byte 0x01` + `int32 baytUzunligi` + matn. Matn — vergul bilan ajratilgan 31 maydon (CSV, qo'shtirnoqsiz), **"overlong" kodlangan**: 0x50…0x7F oralig'idagi har bir bayt `0xC1, 0x80|(b&0x3F)` juftligi bilan yoziladi (P–Z, `_`, kichik harflar va h.k.), 0x50 dan kichik baytlar (raqamlar, A–O, bo'shliq, `.`, `,`, `-`, `/`) o'zgarmaydi. 942 641 ta belgi bo'yicha istisnosiz tasdiqlangan.

Detal etiketkasi (`detail.fme`) CSV maydonlari:

| # | Ma'no | Manba (loyiha) | Misol |
|---|---|---|---|
| 0 | shablon | doim `detail.fme` | `detail.fme` |
| 1 | — | doim bo'sh | |
| 2 | detalning umumiy soni | `part@count` | `8` |
| 3 | detalning CS operatsiyadagi tartib raqami | `indexInOperation` (= OSI `Part@Code`) | `15` |
| 4 | — | doim `1` | `1` |
| 5 | buyurtma | `good(product)@product.order` | `3168 mijoz` |
| 6 | uzunlik | `part@l` | `852` |
| 7 | en | `part@w` | `287` |
| 8 | detal nomi | `part@name` | `01_012 polka` |
| 9 | soni (= #2) | `part@count` | `8` |
| 10 | chap kromka belgisi | `ell` → EL operatsiya `elSymbol` | `A` yoki bo'sh |
| 11 | o'ng kromka | `elr` | |
| 12 | yuqori kromka | `elt` | |
| 13 | pastki kromka | `elb` | |
| 14 | tolalik (tekstura) | `part@txt` (`true/false`) | `false` |
| 15–29 | — | doim bo'sh | |
| 30 | to'liq o'zgaruvchilar xaritasi | zlib(level 6) → base64 | `eJyt…` |

Qoldiq etiketkasi (`rest.fme`): `rest.fme,,1,1,<L>,<W>,<maydon m², 3–4 xona>,<buyurtma>,,,…` + #30 xarita (`waste=true`, `business=true`, `part.id` = shu operatsiyadagi qoldiq `part` id si). Faqat buyurtmaning **oxirgi** tagli faylida uchraydi (5 ta namunada).

**#30 xarita** (zlib ichida) — tartiblangan yozuvlar ketma-ketligi:
`byte tur` + `KEY` + `QIYMAT`; `KEY`/string = `byte notNull(0/1)` + `int32 len` + overlong bayt; tur: `0`=string, `1`=int32 (`notNull`+4 bayt), `2`=double (`notNull`+8 bayt IEEE), `3`=bool (`notNull`+1 bayt). Oxirida `0x0A` + `int32 len` + **SVG** (Batik bilan chizilgan detal eskizi, kromka chiziqlari bilan), so'ng `0xFF`. 147 ta kalit (2 xil tartib variant): `project.name, project.date, project.description, project.currency, project.crc16, project.crc32, project.uuid, products.count, products.rows, …, material.name, material.code, product.index, product.name, product.code, product.count, …, operation.name, operation.parts.count, …, part.id, part.code, good, name, description, index, indexInOperation, fullName, length, width, detail.length/width (= dl/dw), afterPreMilling.length/width (= jl/jw), workpiece.length/width, cutting.length/width (= cl/cw), allowanceT/B/L/R, thick, waste, business, txt, count, totalCount, usedCount, et{c,n,s,t,w,j} / eb… / el… / er… (kromka kodi, nomi, belgisi, qalinligi, eni, prejoint), gr{t,b,l,r}{c,n,w,d,o,oi,s} (paz), surfFront, surfBack, groove, drill, mill, XNC1..5 + xncSide/xncBSD, part.position, part.designation, part.code, project.uuid, product.import, product.order`.

Joylashuv guruhlari: har bir guruh bitta etiketkaga tegishli (`labelIndex` — shu fayldagi N ta yozuvdan biri, 0 dan), guruh ichidagi elementlar soni = shu listdagi nusxa soni (bitta list uchun; `QTA` ga ko'paytirilmaydi). `(X, Y)` — detalning **listdagi** o'lchami (X list uzunligi bo'ylab), ya'ni burilgan bo'lsa `(287, 852)` kabi teskari. Guruhlar tartibi kesish tartibiga mos emas (qoidasi noma'lum — savol 6).

Tekshiruv: 64 faylning har birida kesish daraxtidan chiqqan detallar multiset'i joylashuv guruhlari multiset'iga **aynan teng** (64/64).

---

## 3. Kesish rejasi qanday kodlangan

- **Material/list:** `DAT.MAT`, `X/Y/Z`. Bir zip = bir material. Qoldiq list (masalan 2750×450) ham oddiy `X/Y` bilan beriladi.
- **Pattern:** bitta `tagli` fayli = bitta kesish kartasi; `QTA` = shu kartadan kesiladigan listlar soni (`dist` dagi `QTA` bilan bir xil). Loyihadagi `cMaterialCount` = Σ`QTA` (12/12 buyurtmada mos).
- **Paket (kitob):** `HP=4000` (40 mm) — mashinaga paket balandligi chegarasi; alohida "kitob" yozuvi yo'q. Namunada `QTA` ≤ 2 (16 mm × 2 = 32 ≤ 40).
- **Strip/burilish:** 1-darajadagi kod (`1` yoki `4`) birinchi kesish yo'nalishini belgilaydi; keyingi darajalar o'qni almashtiradi (`2/5`, `Z1`, `Z2`…). Loyihadagi `swMaxturns=4` → namunalarda eng chuqur `Z2` (4-daraja).
- **Bosh kesish/trim:** faylda yozilmaydi, `B_REF` (5 mm) orqali mashina bajaradi.
- **Qoldiq:** faqat etiketka (`rest.fme`) shaklida; kesish ro'yxatida qoldiq alohida belgilanmaydi.
- **Detal joylashuvi:** `B_CUT` daraxti + `B_LABEL` joylashuv guruhlari (qaysi o'lchamdagi bo'lak qaysi etiketkaga).

Hisob-kitob tekshiruvi (har buyurtma):

| Buyurtma | Material | tagli | ΣQTA | loyiha cMaterialCount | daraxtdan detal ×QTA | loyiha cPartCount | CUT yozuvlari | detal etiketkalari | rest |
|---|---|---|---|---|---|---|---|---|---|
| 3168 | LDSP KASHMIR SHAGREN | 8 | 9 | 9 | 90 | 90 | 113 | 70 | 1 |
| 3169 | LDSP METALIK SHAGREN 5.03 kv | 4 | 4 | 4 | 104 | 104 | 122 | 90 | 0 |
| 3170 | LDSP KASHMIR SHAGREN | 2 | 2 | 2 | 40 | 40 | 62 | 33 | 0 |
| 3171 | LDSP DUB VATAN TEKSTURA | 2 | 4 | 4 | 28 | 28 | 17 | 8 | 0 |
| 3173 | LDSP KASHMIR SHAGREN | 9 | 10 | 10 | 77 | 83* | 105 | 59 | 1 |
| 3174 | LDSP KASHMIR SHAGREN | 10 | 11 | 11 | 112 | 112 | 141 | 81 | 0 |
| 3175 | LDSP KASHMIR SHAGREN | 3 | 4 | 4 | 32 | 32 | 23 | 15 | 1 |
| 3177 | LDSP KAPUCHINO | 4 | 4 | 4 | 87 | 87 | 119 | 80 | 1 |
| 3178 | LDSP LIZA BEJIVIY | 3 | 3 | 3 | 30 | 30 | 28 | 16 | 0 |
| 3179 | LMDF OQ GLYANETS | 6 | 6 | 6 | 104 | 104 | 122 | 89 | 1 |
| 3180 | LDSP DUB VATAN TEKSTURA | 5 | 5 | 5 | 69 | 69 | 113 | 58 | 0 |
| 3182 | LDSP KASHMIR SHAGREN | 8 | 9 | 9 | 117 | 117 | 129 | 93 | 0 |

\* 3173: `.project` fayli eksportdan keyin o'zgartirilgan (detal nomlari/o'lchamlari siljigan, 5 ta detal qo'shilgan) — fayl ichidagi 77 ta detal OSI bilan to'liq mos.

Etiketka soni (70) detal turlari sonidan (67) ko'p bo'lishi mumkin — bitta detal turi bir nechta patternga bo'linsa, har bir patternda o'z etiketka yozuvi bo'ladi.

---

## 4. Loyiha → fayl maydonlari xaritasi

| Loyiha (`.project`) | NC300 maydoni |
|---|---|
| `project@name` (birinchi 8 belgi) | zip nomi, `dist/NOME`, `tagli/NOME.iii`, `NM`, `NPG` |
| `good(product)@product.order` | `dist.COMM`, etiketka #5 |
| CS `operation` → `material` → `good(sheet)@name` | `DAT.MAT`, `dist.COM` (≤40) |
| sheet `l / w / t` (yoki ishlatilgan qoldiq list o'lchami) | `X / Y / Z` (×100) |
| `tool.cutting@swPackageHeight` (40) | `HP` (×100) — namunada doimiy |
| `cTrimL/cTrimW` + `swSawthick` (2+3) | `B_REF` 500 lar (5 mm) — namunada doimiy |
| `part@cl / cw` (kesish o'lchami; namunada `l=cl=dl`) | `CUT.DIM` (barg tugunlar), joylashuv `(X,Y)` |
| `part@txt="true"` | burilmaydi: X bo'ylab har doim `cl` (81/81 tolali detal); etiketka #14 |
| `part@count` | etiketka #2, #9 ; Σ(guruh elementlari × `QTA`) bo'yicha barcha patternlarda = `count` |
| `part@name` | etiketka #8 |
| `elt/elb/ell/elr` → EL op `elSymbol` | etiketka #12/#13/#10/#11 |
| kromka `band@name/code/t/w`, `elWidthPreJoint` | xarita `et*/eb*/el*/er*` |
| `jl/jw` | xarita `afterPreMilling.*` |

### Tekshirilgan misollar (≥3)

**A. 3171, `01_001 oldi bok`** — loyiha: `l=1400 w=1750 count=2 txt=true`, 4 tomon kromka `A` (1-19, t=1).
`tagli/…001`: `QTA=2`; `CUT=1 COD="1" DIM=140000` → `CUT=2 COD="2" DIM=175000` (barg) ⇒ bo'lak X=1400, Y=1750 (tolali — burilmagan). Etiketka: `detail.fme,,2,1,1,3171 mijoz,1400,1750,01_001 oldi bok,2,A,A,A,A,true,…`; joylashuv `[(140000,175000,0)]` → 1 dona/list × QTA 2 = 2 = `count` ✓.

**B. 3168, `01_012 polka`** — loyiha: `l=852 w=287 count=8 txt=false`, faqat `elb` (A).
`…001` (`QTA=2`): `4:852` tasma ichida `5:287 QTA=2` barg ⇒ bo'lak (X=287, Y=852) — burilgan; joylashuv `[(28700,85200,8)×2]` → 2×2=4.
`…003` (`QTA=1`): `4:1202 → 5:852 → Z1:287 QTA=4` ⇒ (X=852, Y=287) ×4.
Jami 4+4 = 8 = `count` ✓. Etiketka: `…,8,15,1,3168 mijoz,852,287,01_012 polka,8,,,,A,false` — #13 (pastki) = `A` ✓.

**C. 3178, `01_008 Fasad`** — loyiha: `l=2354 w=546 count=1 txt=true`, 4 tomon `A`.
`…003`: `1:2354 → 2:497 QTA=2 → Z1:2328` (2 ta 2328×497) ; `2:546` (barg) ⇒ (2354, 546) ✓. Etiketka `…,1,1,1,3178 mijoz,2354,546,01_008 Fasad,1,A,A,A,A,true`, joylashuv `[(235400,54600,1)]` ✓. Xuddi shu faylda `1:321 → 2:1750 → Z1:170` (barg, 170×1750) va `Z1:70 QTA=2 → Z2:1730` (2 ta 70×1730, pastki daraxt bilan takror).

**D. 3168 qoldiq:** `…008` dagi `rest.fme,,1,1,2740,562,1.54,3168 mijoz` — `4:491` + `4:761` = 1252; 1830 − 5 − 1252 − 2×3 − 5 = 562 ✓ (2740 = 2750 − 10).

---

## 5. Minimal qayta tiklangan namuna (anonim)

`9001_Mij.zip`:

`dist/9001_Mij`
```
1
B_FDIS
	DAT
		NOME="9001_Mij"
		PROX=""
		CPI=0
		COMM="9001 mijoz"
B_DIS
	DIS
		NM=1
		NPG="9001_Mij.001"
		QTA=2
		ESE=0
		OPZ=""
		COM="2750x1830x16: LDSP DUB VATAN TEKSTURA"
E_DIS
E_FDIS
```

`tagli/9001_Mij.001` (3171.001 tuzilmasi asosida; detallar: 1400×1750 ×1, 1718×584 ×1, 583×548 ×2, 583×590 ×1 — har listda):
```
B_SCH
B_DAT
	NM="9001_Mij.001"
	CMM=""
	MAT="LDSP DUB VATAN TEKSTURA"
	DAY=""
	OPZ=""
	X=275000
	Y=183000
	Z=1600
	HP=4000
	VL=0
	VT=0
	QTA=2
E_DAT
B_REF
	FORZ=0
	ROL=500
	RMADL=500
	RMIDL=500
	ROT=500
	RMADT=500
	RMIDT=500
	RMIP=500
E_REF
B_CUT
	CUT=1
		COD="1"
		DIM=140000
		QTA=1
	CUT=2
		COD="2"
		DIM=175000
		QTA=1
	CUT=3
		COD="1"
		DIM=117500
		QTA=1
	CUT=4
		COD="2"
		DIM=171800
		QTA=1
	CUT=5
		COD="Z1"
		DIM=58400
		QTA=1
	CUT=6
		COD="Z1"
		DIM=58300
		QTA=1
	CUT=7
		COD="Z2"
		DIM=54800
		QTA=2
	CUT=8
		COD="Z2"
		DIM=59000
		QTA=1
E_CUT
E_SCH
B_LABEL
	<base64, 80 belgidan, quyidagi algoritm bilan>
E_LABEL
```
(barcha qatorlar `CRLF` bilan, oxirgi `E_LABEL` dan keyin ham `CRLF`.)

`B_LABEL` generatori (Python, namunalarda bayt-baayt tasdiqlangan):

```python
import struct, zlib, base64
def over(b):                      # 0x50..0x7F -> overlong C1 xx
    o = bytearray()
    for x in b:
        o += bytes([0xC1, 0x80 | (x & 0x3F)]) if 0x50 <= x <= 0x7F else bytes([x])
    return bytes(o)
def s(v):                         # nullable string
    if v is None: return b'\x00'
    b = over(v.encode('utf-8')); return b'\x01' + struct.pack('>I', len(b)) + b
def enc_map(entries, svg):        # entries: [(type, key, value)], type 0=str 1=int 2=double 3=bool
    o = bytearray()
    for t, k, v in entries:
        o += bytes([t]) + s(k)
        if t == 0: o += s(v)
        elif t == 1: o += b'\x00' if v is None else b'\x01' + struct.pack('>i', v)
        elif t == 2: o += b'\x00' if v is None else b'\x01' + struct.pack('>d', v)
        elif t == 3: o += b'\x00' if v is None else b'\x01' + bytes([1 if v else 0])
    sv = svg.encode('utf-8'); o += b'\x0a' + struct.pack('>I', len(sv)) + sv + b'\xff'
    return base64.b64encode(zlib.compress(bytes(o), 6)).decode()
def rec(fields):                  # 31 ta maydon, oxirgisi enc_map natijasi
    b = over(','.join(fields).encode('utf-8')); return b'\x01' + struct.pack('>I', len(b)) + b
def label_block(rests, details, groups):
    o = bytearray(struct.pack('>I', len(rests)))
    for f in rests: o += rec(f) + struct.pack('>I', 1)
    o += struct.pack('>I', len(details))
    for f in details: o += rec(f)
    o += struct.pack('>I', len(groups))
    for g in groups:              # g = [(x_1/100, y_1/100, labelIndex), ...] bitta list uchun
        o += struct.pack('>I', len(g))
        for x, y, i in g: o += struct.pack('>III', x, y, i)
    b64 = base64.b64encode(bytes(o)).decode()
    return ['\t' + b64[i:i+80] for i in range(0, len(b64), 80)]
```

---

## 6. Noma'lum / noaniq joylar — foydalanuvchiga savollar

1. **Kodlash:** material/buyurtma nomida kirill harflari bo'lsa fayl cp1251 da yozilishi kerakmi (namunalarda faqat ASCII)? Etiketka ichidagi 0x80+ baytlar (UTF-8 kirill) qanday "overlong" qilinadi — namunasi yo'q.
2. **Bir nechta material:** bitta buyurtmadagi 2-material (masalan XDF orqa devor) uchun zip/`NOME` qanday nomlanadi (8 belgi bir xil chiqadi)? Ular NC300 ga umuman yuboriladimi?
3. **`B_REF` maydonlari** (`FORZ, ROL, RMADL, RMIDL, ROT, RMADT, RMIDT, RMIP`) ning aniq ma'nosi va ular har doim 500 (5 mm) bo'lishi kerakmi yoki loyiha `cTrimL/cTrimW/swSawthick` dan hisoblanadimi?
4. **`HP`, `VL`, `VT`, `CPI`, `PROX`, `ESE`, `DAY`, `OPZ`** — doimiy deb yozsak bo'ladimi? `VL/VT` tolalik (venatura) bayrog'i emasmi (tolali materialda ham 0)?
5. **`B_LABEL` majburiymi?** Mashina etiketka printerisiz ishlasa, blokni bo'sh (`R=0, N=0, G=0`) qoldirish mumkinmi? Agar majburiy bo'lsa, SVG eskiz va 147 kalitli xarita to'liq kerakmi yoki faqat CSV maydonlari (#0–#14) yetarlimi? `project.crc16/crc32` qanday hisoblanadi (noma'lum, mashina tekshiradimi)?
6. **Joylashuv guruhlarining tartibi** qanday qoida bo'yicha (kesish tartibiga mos emas)? Mashina uchun ahamiyati bormi?
7. **`rest.fme` maydonlari:** 3-maydon (`1`) va yozuvdan keyingi `int32` (`1`) — qoldiqlar soni/indeksimi? Bir patternda bir nechta qoldiq bo'lsa qanday yoziladi (namunada har doim 1)?
8. **Kod `4/5`** — mashinada "list 90° burilgan holda yuklanadi" degani(mi) yoki faqat birinchi kesish yo'nalishimi? Operator uchun alohida ko'rsatma bormi?
9. **Fraksion o'lchamlar:** namunadagi barcha `DIM` lar butun mm (×100). 0.5 mm li o'lcham `DIM=58350` ko'rinishida yozilishini tasdiqlang. `COM` dagi qalinlik (masalan 5.5 mm) qanday yoziladi?

---

## 7. 2026-10-04 onlayn namunasi bilan tekshiruv (bitta loyiha, 3 karta, haqiqiy geometriya ma'lum)

Avvalgi namunalarda kesish daraxti faqat `tagli` ning o'zidan o'qilgan edi, shuning uchun ro'yxat tartibining listdagi haqiqiy
joylashuvga nisbati tekshirilmagan. Yangi namunada shu kroyning koordinatali tavsifi ham bor; natija
(`tools/bench/pp_online_check_saw.py nc300` — `dist` va 3 ta `tagli` bayt-ma-bayt, etiketka yozuvining 30-maydonisiz):

* **B_CUT tartibi:** list **Y o'qi** bo'ylab ketma-ket bo'laklar (kod `4`, `2`, burilgan kartada `Z1`, burilmaganda `Z2`…)
  **teskari** tartibda yoziladi (stanok Y o'qi ko'zguli); X o'qi bo'ylab — o'z tartibida. Generator: `biesse_nc300.flip_y`.
* **`dist` → `COMM`** — buyurtma nomi lotinga o'giriladi (`Без имени` → `Bez imeni`); `NOME` / fayl nomlari ham lotin
  (`Bez_imen`). Etiketka yozuvidagi buyurtma nomi (5-maydon) o'girilmaydi.
* **B_LABEL detal yozuvlari tartibi** — detal raqami bo'yicha xesh-jadval tartibi (savat = raqam & (sig'im − 1), sig'im 16 dan,
  to'ldirilganda ikki barobar; savat ichida listdagi birinchi uchrash tartibi). Onlayn tizimda kalit — loyiha faylidagi detal
  `id`, bizda — detal uid (`biesse_nc300.hash_order`).
* **Joylashuv guruhlari** — listdagi (geometrik, B_CUT tartibidan mustaqil) preorder tartibda; guruh — ketma-ket kelgan bir xil
  detal bo'laklari (o'lchami bir xil, lekin boshqa detal aralashsa — alohida guruhlar: `A, B, A` → 3 guruh). Avvalgi 64 namunada
  guruhlar mosligi 52 → 55.
