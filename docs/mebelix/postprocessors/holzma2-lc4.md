# Holzma 2 — `.LC4` (binar kesish rejasi + etiketka ma'lumoti)

> Manba: `post prtsessorlar/PILNIY APPARAT/Holzma 2/` dagi 10 ta namuna (3151…3161) va ularga mos
> `giblab project/3 Eldor/NNNN X/NNNN_X.project` fayllari. Mijoz nomlari bu hujjatda «mijoz» deb almashtirilgan.
> Dastur binarlari o'qilmadi — faqat chiqish fayllari va loyiha XML'lari tahlil qilindi.

**Holat: to'liq (struktura).** Yozilgan parser 10 ta namunaning barchasini oxirgi baytigacha o'qiydi va
qayta yozuvchi (serializer) **10/10 faylni bayt-ma-bayt bir xil** qayta tiklaydi. Ichidagi etiketka blobi ham
365/365 holatda bayt-ma-bayt qayta tiklandi. Ochiq qolganlar — asosan semantik (bir nechta doimiy maydon
nimani anglatishi, mashina tomoni blobni talab qiladimi va h.k.), pastdagi 6-bo'limga qarang.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.LC4` (katta harf) |
| Nom | `<project.name>_<material nomi, bo'shliqlar ketma-ketligi → "_">.LC4`, masalan `3161_mijoz_LDSP_PIKARD.LC4` (material `LDSP  PIKARD` — ikki bo'shliq bitta `_` bo'ldi) |
| Nechta fayl | Bitta material (bitta `CS` operatsiyasi) = bitta fayl. Namunalarda har buyurtmadan faqat bitta material fayli berilgan (masalan 3161 loyihasida XDF uchun ham `CS` bor, lekin fayl yo'q) |
| Turi | **Binar**, tegli (tag-length-value'ga o'xshash) oqim, little-endian. Matn qatorlari yo'q → qator oxiri (CRLF/LF) tushunchasi yo'q |
| Kodirovka | Barcha satrlar **UTF-8** (masalan detal ID `Д1` = `D0 94 31`) |
| Sonlar | O'lchamlar — `int64` fixed-point, **×100 000** (1900 mm → `190000000`). Satr ichidagi sonlar (`"347.0"`, `"2.894"`) — nuqta bilan |
| Hajm | 80 KB … 830 KB. Hajmning **~77 %i** — har bir detal uchun **ikki marta** yozilgan `detail.fme,...` satri, uning oxiridagi base64(zlib(...)) etiketka blobi (ichida SVG chizma) |
| Sarlavha/magic, checksum | Yo'q. Fayl to'g'ridan-to'g'ri ildiz obyekt bilan boshlanadi va parametrlar ro'yxati bilan tugaydi |

---

## 2. Binar kodlash (past daraja)

Har bir qiymat oldidan **2 baytli tip tegi** (`uint16 LE`) keladi:

| Teg | Nomi (biz bergan) | Keyin keladi |
|---|---|---|
| `01 00` | BOOL / "mavjud" | 1 bayt: `01`=true/mavjud, `00`=false/null |
| `05 00` | INT16 | 2 bayt LE (signed) |
| `06 00` | INT32 | 4 bayt LE (signed) |
| `08 00` | INT64 | 8 bayt LE (signed) |
| `0D 00` | STRING | `BOOL(1)` + `0E 00` (BYTES) |
| `0E 00` | BYTES | `INT32` (ya'ni `06 00` + uzunlik) + shuncha UTF-8 bayt |
| `0F 00` | DECIMAL | `INT16(1)` + `INT64(qiymat×100000)`; namunalarda har doim keyin `BOOL(false)` keladi (biz uni DECIMAL'ning bir qismi deb yozamiz) |
| `10 00` … `14 00` | ENUM (5 xil turi) | `INT32` qiymat |

Tayyor bayt shablonlari (generator uchun):

```
OBJ(ver)      = 01 00 01  05 00 <ver:int16>               ; obyekt boshlanishi (versiya bilan)
STRING(s)     = 0D 00 01 00 01 0E 00 06 00 <len:int32> <utf8 bytes>
DECIMAL(mm)   = 0F 00 05 00 01 00 08 00 <round(mm*100000):int64> 01 00 00
INT(v)        = 06 00 <v:int32>
BOOL(b)       = 01 00 <00|01>
ENUM(t,v)     = <t:uint16> 06 00 <v:int32>          ; t ∈ {0x10,0x11,0x12,0x13,0x14}
LIST(items)   = OBJ(1) INT(n) item_1 … item_n
```

Obyektlarning tugash belgisi yo'q — sxema qat'iy, shuning uchun maydonlar tartibi aynan quyidagidek bo'lishi shart.

---

## 3. Yuqori daraja sxema

```
File      := OBJ(1) STRING(job) STRING(order)
             LIST<Item>    parts        ; detallar (+ oxirida biznes-qoldiqlar)
             LIST<Item>    boards       ; har bir raskroy kartasi uchun bitta list (board) yozuvi
             LIST<>        (doim bo'sh, n=0)
             LIST<Root>    patterns     ; boards bilan 1:1, bir xil tartibda

Item      := OBJ(1) INT16(2)
             STRING(id) STRING(fme) STRING(fme)          ; fme ikki marta, aynan bir xil
             DECIMAL(L) DECIMAL(W) DECIMAL(T)
             INT(qty) INT(qty)                           ; ikkalasi doim teng
             ENUM(0x13, grain)  BOOL(false)
             LIST<Pair> map     BOOL(false)
Pair      := OBJ(1) STRING(key) STRING(value)

Node      := OBJ(1) STRING("") STRING("") DECIMAL(size) INT(rep)
             ENUM(0x11, kind) ENUM(0x12, sub) INT16(1)
             INT(hasInfo) [Info agar hasInfo=1]
             LIST<> (doim bo'sh)  LIST<Node> children
Root      := OBJ(1) INT16(1) STRING("0000k") STRING("") DECIMAL(board L) INT(1)
             ENUM(0x11,1) ENUM(0x12,1) INT16(1) INT(1) Info
             LIST<> (bo'sh)  LIST<Node> children
             DECIMAL(board W) INT(sheets) INT(sheets) STRING(material) INT16(1)
             ENUM(0x10,0) BOOL(false) LIST<Param> params
Info      := OBJ(1) INT(a) BOOL(rotated) STRING(label) BOOL(true) ENUM(0x14,e14) INT(ref)
Param     := OBJ(2) STRING(key) STRING(value) BOOL(true)
```

### 3.1 File sarlavhasi

| Maydon | Ma'no | Misol (3161) |
|---|---|---|
| `job` | Fayl nomi kengaytmasiz | `3161_mijoz_LDSP_PIKARD` |
| `order` | Loyihadagi `product.order` | `3161 mijoz` |

### 3.2 `parts` — detal yozuvi (`Item`)

| Maydon | Tur | Ma'no / manba (`.project`) |
|---|---|---|
| `id` | STRING | `Д1`, `Д2`, … — ro'yxatdagi tartib raqami (1 dan, uzluksiz). Qoldiq (rest) yozuvida ham `Д1` |
| `fme` (×2) | STRING | 31 maydonli vergulli satr, pastda 3.3 |
| `L`, `W` | DECIMAL mm | `part@cl`, `part@cw` (kesish o'lchami). Namunalarda `cl=dl=l`, shuning uchun `l`/`dl` dan farqi tekshirilmagan |
| `T` | DECIMAL mm | List qalinligi `sheet@t` (16) |
| `qty`, `qty` | INT | `CS` operatsiyasidagi `<part id count>` (= `part@count`). Qoldiqda `0` |
| `grain` | ENUM 0x13 | `0` — tekstura yo'q, `2` — `part@txt="true"` (365/365 mos). `1` uchraganmi — noma'lum |
| `map` | LIST<Pair> | AddInfo kalitlari, pastdagi jadval |

Detallar tartibi = `CS` operatsiyasidagi `<part>` tartibi (list `sheet` yozuvlari tashlab yuboriladi). Biznes-qoldiqlar
(`sheet` ichidagi `waste="true" business="true"` part) ro'yxat **oxiriga** qo'shiladi.

**`map` kalitlari** (qiymatlar har doim STRING):

| Kalit | Ma'no | Manba |
|---|---|---|
| `AddInfo_001` | Material nomi | `sheet@name` |
| `AddInfo_002` | Material kodi — faqat list `code` ga ega bo'lsa | `sheet@code` (`110052`, `115010`) |
| `AddInfo_003` | Mahsulot nomi | `good[product]@name` (`01 shkaf`) |
| `AddInfo_004` | Mahsulot kodi | `good[product]@code` (`316101`) |
| `AddInfo_006`, `AddInfo_007` | Doim `"1"` | ? (mahsulot soni / indeks bo'lishi mumkin) |
| `AddInfo_008` | Buyurtma | `product.order` |
| `AddInfo_009` | Detal nomi | `part@name` (`01_001 bok`) |
| `AddInfo_010` | Detal kodi | `part@code` (`01_001`) |
| `AddInfo_011` | Loyihadagi detal ID | `part@id` (qoldiqda — ichki raqam, pastda savol) |
| `AddInfo_012` | `"true"` — pazi (groove) bor | blobdagi `groove` (31/31 mos) |
| `AddInfo_013` | `"true"` — frezerlash bor | XNC'da `countMill>0` / blob `mill` |
| `AddInfo_014` | `"true"` — присадка (XNC dasturi) bor | blob `drill` |
| `AddInfo_015` | 1-tomon XNC dastur kodi, faqat 014=true bo'lsa | `<product code>_<part code>` = XNC `operation@code` (`316101_01_001`) |
| `AddInfo_016` | 2-tomon (orqa) XNC dasturi, bo'lsa | `…_2` (`315901_01_001_2`), blobdagi `XNC2` bilan 38/38 mos |
| `PartFinishedLength/Width` | Tayyor o'lcham, `"%.1f"` | `part@dl`, `part@dw` |
| `Edge_MaterialFront/Back/Left/Right` | Kromka bor tomonlar: `"(" + elSymbol + ") " + band nomi` | `elb`→Front, `elt`→Back, `ell`→Left, `elr`→Right; masalan `(A) 1-19 Sasna`, `(B) 1-35  qora` |

Kalitlar tartibi tartiblanmagan, Java `HashMap` tartibiga o'xshaydi; namunalarda doim shu tartib:
`Edge_MaterialBack, Edge_MaterialLeft, AddInfo_010, PartFinishedWidth, AddInfo_006, AddInfo_007, AddInfo_004,
AddInfo_015, AddInfo_016, Edge_MaterialRight, AddInfo_002, AddInfo_013, AddInfo_003, AddInfo_014,
PartFinishedLength, AddInfo_011, AddInfo_001, AddInfo_012, Edge_MaterialFront, AddInfo_008, AddInfo_009`
(yo'q kalitlar tashlab yuboriladi). Mashina tartibga qaraydimi — noma'lum, xavfsizlik uchun shu tartibda yozing.

### 3.3 `fme` satri (etiketka shabloni uchun)

Detal (`detail.fme`), 31 maydon, 0 dan sanaladi:

| # | Ma'no | Misol |
|---|---|---|
| 0 | Etiketka shabloni | `detail.fme` |
| 1 | bo'sh | |
| 2 | Soni | `1` |
| 3 | Tartib raqami (= `id` dagi raqam) | `1` |
| 4 | Doim `1` | |
| 5 | `job` | `3161_mijoz_LDSP_PIKARD` |
| 6, 7 | `L`, `W` (butun bo'lsa nuqtasiz, `%g`) | `1900`, `347` |
| 8 | Detal nomi | `01_001 bok` |
| 9 | Soni (yana) | `1` |
| 10, 11, 12, 13 | Kromka belgisi (elSymbol) **l, r, t, b** tartibida, bo'lmasa bo'sh | `A,A,,A` |
| 14 | Tekstura `true/false` (`part@txt`) | `false` |
| 15–29 | bo'sh | |
| 30 | base64( zlib( etiketka blobi ) ) | `eJzd…` |

Qoldiq (`rest.fme`): `rest.fme,,1,1,<L>,<W>,<maydon m², 3 xona>,<job>,,,…,,<blob>` (masalan `rest.fme,,1,1,1590,1820,2.894,3151_mijoz_…`).

**Etiketka blobi** (zlib, standart daraja 6, `78 9C`). Ichida yozuvlar ketma-ketligi:
`[tip:u8][01][kalit uzunligi:u32 BE][kalit][01|00 mavjud][qiymat]`, tiplar: `0`=satr (u32 BE uzunlik + bayt),
`1`=int32 BE, `2`=double BE, `3`=bool (1 bayt), `0x0A`=SVG (kalitsiz: `0A` + u32 BE uzunlik + UTF-8 XML),
oxirida `FF`. Satrlarda **0x50–0x7F oralig'idagi belgilar ortiqcha uzun (overlong) 2 baytli UTF-8 bilan**
yoziladi (`p` → `C1 B0`), qolganlari oddiy — bu yengil obfuskatsiya (Java'ning `readUTF` uslubidagi o'quvchi buni qabul qiladi).
147 ta kalit: `project.name/date/description/currency/crc16/crc32/uuid`, `products.*`, `material.name/code`,
`product.*`, `operation.*`, `part.id/code`, `name`, `length/width`, `detail.*`, `afterPreMilling.*` (`jl/jw`),
`workpiece.*`, `cutting.*`, `allowanceT/B/L/R`, `thick`, `waste/business/txt`, `count/totalCount/usedCount`,
kromkalar (`ebc/ebn/ebs/ebt/ebw/ebj` va `et*/el*/er*`), paz (`grt*/grb*/grl*/grr*`), `groove/drill/mill`,
`XNC1..5`, `xncSide1..5`, `xncBSD1..5`, `part.designation/code/position`, `product.import/order` va SVG
chizma (присадка ko'rinishi). Bu blob kesish rejasiga ta'sir qilmaydi — faqat etiketka bosish uchun.

### 3.4 `boards` (list yozuvi, `Item` bilan bir xil sinf)

| Maydon | Qiymat |
|---|---|
| `id` | `"1"`, `"2"`, … (raskroy kartasi tartibi) |
| `fme` ×2 | Material nomi (masalan `LDSP  PIKARD`) |
| `L`, `W`, `T` | `sheet@l`, `sheet@w`, `sheet@t` (namunalarda doim 2750 × 1830 × 16) |
| `qty` ×2 | Shu karta bo'yicha kesiladigan listlar soni (= "kitob" balandligi; 1 yoki 2 uchradi; `swPackageHeight=40` / 16 mm → maks. 2) |
| `grain` | Doim `0` (teksturali material bo'lsa ham) |
| `map` | Bo'sh (n=0) |

### 3.5 `patterns` — kesish daraxti

Har karta — guillotine daraxti. Ildiz (`Root`) list hisoblanadi, bolalar — ketma-ket kesimlar orasidagi bo'laklar.

**Tugun turlari** (`kind` = ENUM 0x11, `sub` = ENUM 0x12):

| kind | sub | Ma'no | O'lcham manbasi |
|---|---|---|---|
| 1 | 1 | Ildiz (list) | `size` = list uzunligi L |
| 4 | 4 | Torets kesish (trim, "Anschnitt") | `cTrimL/cTrimW` (2 mm) |
| 2 | 4 | Arra kerfi (kesim izi) | `swSawthick` (3 yoki 6 mm) |
| 0 | 0 | Oraliq polosa/bo'lak (keyin yana kesiladi) | |
| 11 | 0 | Tayyor detal (barg) | Info `label="Part"`, `ref` = `parts` dagi 0-asosli indeks |
| 10 | 0 | Biznes-qoldiq (barg) | Info `label="Rest"`, `rep=0`, `ref` = qoldiq yozuvi indeksi |

**Qoidalar** (barcha 44 kartada tekshirildi):

1. Bolalar ro'yxati har doim juft: `X, kerf, X, kerf, …` — har bir element (trim ham, oxirgisi ham) dan keyin kerf tuguni (386/386).
2. Trim (`kind=4`) faqat **ildizning** va **1-daraja polosalarning** birinchi bolasi (44 + 129 holat); chuqurroq darajalarda trim yo'q.
3. Daraja yo'nalishi almashadi: 1-daraja o'lchamlari X o'qi bo'ylab, 2-daraja — Y, 3-daraja — X, … .
   Ildiz `Info.rotated=false` bo'lsa X = list uzunligi (2750), `true` bo'lsa X = list eni (1830) (list 90° buriladi).
   Ildiz `size` har doim list L ga, ildiz dumidagi DECIMAL — W ga teng.
4. `rep` — element (va undan keyingi kerf) necha marta takrorlanadi. Bolalar yig'indisi
   `Σ rep·(size + kerf)` ota-bo'lak uzunligidan oshmaydi (faqat oxirgi kerf chetdan ≤1 mm chiqishi mumkin — 3159 da 6 mm arra bilan 2 holat).
   Qolgan joy — chiqindi, daraxtda alohida yozilmaydi.
5. Detal bargi doim aniq o'lchamgacha kesilgan: `{barg size, ota size} = {L, W}` (423/423).
6. Detal `Info.rotated` = detal uzunligi **Y** o'qi bo'ylab yotadi (ya'ni X bo'ylab emas). Bu ildiz burilishi bilan
   XOR: `rotated = (karta burilgan) XOR (detal L list enibo'ylab)` — 423/423 mos. Teksturali (`grain=2`) detallar
   hech qachon list L o'qidan burilmagan (228/228).
7. Har bir detalning barcha barglaridagi `Π rep (yo'l bo'ylab) × board qty` yig'indisi = `qty` (10/10 faylda; masalan 3160: 108 qator, 165 dona).
8. Qoldiq tuguni 1-darajada, `size` = qoldiqning xom o'lchami (`rl`), qoldiq yozuvi L/W = trim'dan keyingi o'lcham
   (`l`, `w`): 1595 → 1590×1820 (5 mm = `AnschnittLinks`).

**Info obyekti:** `a` — ildizda 0, detal/qoldiqda 1; `rotated` — yuqoridagi 6-qoida (ildizda — karta burilgani);
`label` — `""`/`Part`/`Rest`; keyingi BOOL doim true; `e14` — ildizda 3, detal/qoldiqda 1; `ref` — ildizda karta indeksi (0 dan),
detal/qoldiqda `parts` indeksi.

**Ildiz dumi:** `DECIMAL(list W)`, `INT(listlar soni)` ×2 (= board qty), `STRING(material)`, `INT16(1)`,
`ENUM(0x10, 0)`, `BOOL(false)`, so'ng 11 ta `Param` (versiya 2):

| Kalit | Qiymat (namunalar) | Taxminiy ma'no |
|---|---|---|
| `AnschnittHintenOptimal` | `0` | |
| `AnschnittKopf` | `0.0` | |
| `AnschnittLinks/Oben/Rechts/Unten` | `5.0` (3159 da `8.0`) | trim + arra = 2+3 (3159: 2+6) — gipoteza |
| `AnschnittNachschnittHinten/Vorne` | `0.0` | |
| `AnschnittNullVorneNichtSchneiden` | `1` | |
| `NutTiefe` | `0` | |
| `SaegeblattStaerke` | `3` (3159 da `6`) | arra qalinligi = `swSawthick` |

Karta nomi `00001`, `00002`, … (5 xonali, tartib bilan). Daraxtdagi kerf soni (rep bilan) loyihaning
`cutCount` "0=" qiymatiga yaqin (±1, ortiqchasi — qoldiq kesimi), ya'ni kesimlar list soniga ko'paytirilmaydi — kitob bir yo'la kesiladi.

---

## 4. Loyiha → LC4 moslik (tekshirilgan misollar)

Korrelyatsiya skripti 10 faylning **358 ta detal qatori va 7 ta qoldig'ini** loyihaga solishtirdi:
soni, `cl/cw`, `dl/dw`, nom, kod, mahsulot, buyurtma, XNC kodi, tekstura, kromka tomonlari, fme maydonlari —
barchasi mos (yagona "farq": `AddInfo_014=false` bo'lsa `AddInfo_015` umuman yozilmaydi — kutilgan xatti-harakat).
Mos `.project` — pastki chiziqli variant (`NNNN_X.project`); uni blobdagi `project.uuid` aniqlaydi
(bo'shliqli variantlarda uuid ham, `CS` natijasi ham yo'q).

**Misol 1 — 3161 (LDSP PIKARD, 1 list, 10 qator, 18 dona).**
Loyiha: `<part id="1" name="01_001 bok" cl="1900" cw="347" dl="1900" dw="347" count="1" txt="false" elb ell elr (A, "1-19 Sasna")>`,
mahsulot `code="316101"`, list `code="110052"`. LC4: `Д1`, `L=1900 W=347 T=16`, `qty=1`, `grain=0`,
`fme = detail.fme,,1,1,1,3161_mijoz_LDSP_PIKARD,1900,347,01_001 bok,1,A,A,,A,false,…`,
map: `AddInfo_002=110052`, `AddInfo_015=316101_01_001`, `Edge_MaterialLeft/Right/Front=(A) 1-19 Sasna`.
Daraxt: 2750 bo'ylab `2(trim) 3 | 2254 3 | 352 3 | 100 3` = 2720, qolgan 30 mm chiqindi; `01_008` (300×346, 6 dona)
4 ta bargda (`rep` 1,1,1,3) → 6 ✓.

**Misol 2 — 3158 (LDSP BELI KARONA, 2 karta, 30 dona + qoldiq).**
`01_001 tom` 1500×450, 4 tomon kromka `(A) 06-19 sasna` → `fme …,A,A,A,A,false`, `AddInfo_012=true` (paz),
`AddInfo_002=115010`. Qoldiq: loyihada `l=2740 w=556 rl=2750 rw=561 waste business` → LC4 oxirgi yozuv
`Д1`, `qty=0`, `rest.fme,,1,1,2740,556,1.523,…`; daraxtda 1-daraja `kind=10 size=561 rep=0`.

**Misol 3 — 3159 (LMDF, arra 6 mm).** Loyiha `swSawthick="6"` → barcha kerf tugunlari 6, `SaegeblattStaerke=6`,
`Anschnitt*=8.0`. `01_001 fasad` `txt="true"` → `grain=2`, `fme …,,,,,true`, frezer bor → `AddInfo_013=true`,
2 tomonlama присадка → `AddInfo_015=315901_01_001`, `AddInfo_016=315901_01_001_2`.

**Misol 4 — 3151, karta `00004` (burilgan).** Ildiz `Info.rotated=true`; 1-daraja bolalar yig'indisi 1810 ≤ 1830 (list eni bo'ylab),
2-darajada 1480 polosa ichida `rover` 1480×496 (×3, `rotated=true` — chunki karta burilgan, detal esa list L bo'ylab).

**Misol 5 — 3152 (ikki xil kromka).** `01_002` 4 tomoni `@operation#2` (`elSymbol="B"`, band `1-35  qora`)
→ `fme …,B,B,B,B,…`, `Edge_Material*=(B) 1-35  qora`.

---

## 5. Minimal qayta tiklangan misol (anonim)

1 list 2750×1830×16, 2 detal: `01_001 bok` 800×400 ×2 (pastki kromka A, присадка bor), `01_002 polka` 600×300 ×1.
Arra 3, trim 2. (Etiketka blobi bo'sh qoldirilgan — 6-bo'limdagi savolga qarang.) Bu fayl generator bilan yaratildi,
parserimiz uni xatosiz o'qidi va qayta yozganda bayt-ma-bayt bir xil chiqdi (4945 bayt).

Mantiqiy ko'rinishi:

```
File job="9001_mijoz_LDSP_OQ" order="9001 mijoz"
 parts[2]:
  Д1  fme="detail.fme,,2,1,1,9001_mijoz_LDSP_OQ,800,400,01_001 bok,2,,,,A,false,,,,,,,,,,,,,,,,"
      L=800 W=400 T=16 qty=2/2 grain=0
      map: AddInfo_001=LDSP OQ, AddInfo_003=01 shkaf, AddInfo_004=900101, AddInfo_006=1, AddInfo_007=1,
           AddInfo_008=9001 mijoz, AddInfo_009=01_001 bok, AddInfo_010=01_001, AddInfo_011=1,
           AddInfo_012=false, AddInfo_013=false, AddInfo_014=true, AddInfo_015=900101_01_001,
           PartFinishedLength=800.0, PartFinishedWidth=400.0, Edge_MaterialFront=(A) 1-19 Sasna
  Д2  … 600×300 qty=1, AddInfo_014=false (AddInfo_015 yo'q)
 boards[1]: id="1" fme="LDSP OQ" 2750×1830×16 qty=1/1 grain=0 map={}
 (bo'sh ro'yxat)
 patterns[1]:
  Root "00001" size=2750 rep=1 kind=1 sub=1 Info(a=0,rot=false,"",true,e14=3,ref=0)
    trim 2 | kerf 3
    strip 800                       ; 1-daraja, list L bo'ylab
      trim 2 | kerf 3
      Part 400 rep=2 Info(a=1,rot=false,"Part",true,e14=1,ref=0) | kerf 3
    kerf 3
    strip 600
      trim 2 | kerf 3
      Part 300 Info(…ref=1) | kerf 3
    kerf 3
  tail: W=1830 sheets=1/1 material="LDSP OQ" INT16(1) ENUM10=0 false
        params: AnschnittHintenOptimal=0, AnschnittKopf=0.0, AnschnittLinks/Oben/Rechts/Unten=5.0,
                AnschnittNachschnittHinten/Vorne=0.0, AnschnittNullVorneNichtSchneiden=1, NutTiefe=0, SaegeblattStaerke=3
```

Faylning birinchi 96 bayti:

```
01 00 01 05 00 01 00                          OBJ v1 (File)
0d 00 01 00 01 0e 00 06 00 12 00 00 00 "9001_mijoz_LDSP_OQ"
0d 00 01 00 01 0e 00 06 00 0a 00 00 00 "9001 mijoz"
01 00 01 05 00 01 00 06 00 02 00 00 00        LIST n=2 (parts)
01 00 01 05 00 01 00 05 00 02 00              Item OBJ v1 + INT16(2)
0d 00 01 00 01 0e 00 06 00 03 00 00 00 d0 94 31   "Д1"
…
```

Generator yadrosi (Python, namunalar ustida bayt-ma-bayt tekshirilgan):

```python
import struct
class W:
    def __init__(s): s.b = bytearray()
    def tag(s, t): s.b += struct.pack('<H', t)
    def boolean(s, v): s.tag(1); s.b.append(1 if v else 0)
    def i16(s, v): s.tag(5); s.b += struct.pack('<h', v)
    def i32(s, v): s.tag(6); s.b += struct.pack('<i', v)
    def i64(s, v): s.tag(8); s.b += struct.pack('<q', v)
    def obj(s, ver=1): s.boolean(True); s.i16(ver)
    def string(s, v):
        e = v.encode('utf-8'); s.tag(0x0d); s.boolean(True); s.tag(0x0e); s.i32(len(e)); s.b += e
    def dec(s, v): s.tag(0x0f); s.i16(1); s.i64(int(round(v * 100000))); s.boolean(False)
    def enum(s, t, v): s.tag(t); s.i32(v)
    def lst(s, items, fn): s.obj(); s.i32(len(items)); [fn(x) for x in items]
    def pair(s, kv): s.obj(); s.string(kv[0]); s.string(kv[1])
    def pair2(s, kvb): s.obj(2); s.string(kvb[0]); s.string(kvb[1]); s.boolean(kvb[2])
    def item(s, r):
        s.obj(); s.i16(2); s.string(r['id']); s.string(r['fme']); s.string(r['fme'])
        s.dec(r['L']); s.dec(r['W']); s.dec(r['T'])
        s.i32(r['qty']); s.i32(r['qty']); s.enum(0x13, r['grain']); s.boolean(False)
        s.lst(list(r['map'].items()), s.pair); s.boolean(False)
    def info(s, i):
        s.obj(); s.i32(i['a']); s.boolean(i['rot']); s.string(i['label']); s.boolean(True)
        s.enum(0x14, i['e14']); s.i32(i['ref'])
    def node(s, n, root=False):
        s.obj()
        if root: s.i16(1)
        s.string(n.get('name', '')); s.string(''); s.dec(n['size']); s.i32(n['rep'])
        s.enum(0x11, n['kind']); s.enum(0x12, n['sub']); s.i16(1)
        s.i32(1 if n.get('info') else 0)
        if n.get('info'): s.info(n['info'])
        s.lst([], None); s.lst(n['kids'], s.node)
        if root:
            s.dec(n['W']); s.i32(n['sheets']); s.i32(n['sheets']); s.string(n['mat']); s.i16(1)
            s.enum(0x10, 0); s.boolean(False); s.lst(n['params'], s.pair2)
    def file(s, job, order, parts, boards, roots):
        s.obj(); s.string(job); s.string(order)
        s.lst(parts, s.item); s.lst(boards, s.item); s.lst([], None)
        s.lst(roots, lambda p: s.node(p, True))
        return bytes(s.b)
```

Etiketka blobini yozish kerak bo'lsa: yozuvlarni 3.3-dagi formatda yig'ish, satrlarda 0x50–0x7F belgilarni
`bytes([0xC0 | (c >> 6), 0x80 | (c & 0x3F)])` bilan kodlash, `zlib.compress(data)` (standart daraja), `base64`.

---

## 6. Noaniq joylar — foydalanuvchiga savollar

1. **Qaysi dastur/mashina `.LC4` ni o'qiydi?** (Holzma CADmatic/Cut Rite moduli yoki boshqa vositachi dastur?) Bu fayl turi
   bo'yicha hujjat bormi?
2. **Etiketka blobi majburiymi?** `fme` satri oxiridagi base64-zlib blob (fayl hajmining ~3/4 qismi) bo'sh bo'lsa mashina
   rejani qabul qiladimi? Blob ichidagi `project.crc16` / `project.crc32` qanday hisoblanadi (tekshiriladimi)?
3. `cl/cw` va `dl/dw` farq qiladigan detal (oldindan frezerlash/pripusk bilan) namunasi yo'q: LC4 dagi `L/W` aniq
   `cl/cw` (kesish o'lchami) ekanini tasdiqlash uchun shunday namuna bera olasizmi?
4. `grain` qiymati `1` (eni bo'ylab tekstura) mavjudmi? List `grain` doim 0 — teksturali materialda ham shundaymi?
5. `Anschnitt*` parametrlari: `5.0 = trim 2 + arra 3` degan gipoteza to'g'rimi yoki bu postprotsessorda qo'lda kiritilgan
   sozlamami? `AnschnittKopf`, `AnschnittNullVorneNichtSchneiden=1`, `NutTiefe` qayerdan olinadi?
6. Trim tugunlari 2 mm: `cTrimL` va `cTrimW` qaysi biri qaysi o'qqa tegishli (namunalarda ikkalasi ham 2)?
7. `AddInfo_006` / `AddInfo_007` (doim `"1"`) nimani bildiradi — mahsulot soni/indeksimi?
8. Qoldiq yozuvidagi `AddInfo_011` (masalan 77, 2, 32) va blobdagi `part.id` — loyihadagi qoldiq `id` bilan
   bir xil emas (76, 3, 31). Bu qayerdan olinadi?
9. Ildizdagi `ENUM 0x10` (doim 0), `Info.e14` (3/1), `Info.a` (0/1), ikkinchi `qty`/`sheets` nusxalari va bo'sh ro'yxatlar —
   boshqa qiymat qabul qiladigan holatlar bormi (masalan, qoldiqdan kesish, bir nechta list o'lchami)?
10. Bir buyurtmada bir nechta material bo'lsa (masalan XDF), har biri uchun alohida `.LC4` chiqadimi? (namunalarda faqat bittadan.)
