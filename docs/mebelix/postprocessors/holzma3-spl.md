# Holzma 3 — `.SPL` (binar kesish rejasi)

> Manba: `post prtsessorlar/PILNIY APPARAT/Holzma 3/` dagi 7 ta namuna (`3151`, `3153`, `3155`, `3156`, `3157`, `3159`, `3161`) va
> `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` fayllari.
> Mijoz ismlari hujjatda «mijoz» bilan almashtirilgan.
>
> **Holat: format to'liq tushunildi** (strukturaviy darajada). Barcha 7 ta namuna fayli
> quyida tavsiflangan model asosida yozilgan generator bilan **baytma-bayt bir xil** qilib qayta yig'ildi.
> Faqat bir nechta *doimiy* (sozlama) maydonlarning ma'nosi va `f` yozuvidagi 2 ta hisoblagich noaniq qolgan (6-bo'lim).

---

## 1. Qanday fayllar chiqadi

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.SPL` (katta harf bilan) |
| Nomlash | Ish (job) nomining **birinchi 8 belgisi**: `NNNN_` + mijoz ismining 3 harfi, masalan `3161_xxx.SPL`. Material nomi nomga kirmaydi (DOS 8.3 uslubi). |
| Fayl soni | **1 fayl = 1 material (1 ta Giblab `CS` operatsiyasi)**. Namunalarda har bir buyurtmadan faqat asosiy plita materiali bor (Holzma `.ptx` papkasidagi material bilan aynan bir xil). Nom materialni o'z ichiga olmagani uchun bitta buyurtmaning ikkinchi materiali eksport qilinsa, fayl ustidan yoziladi (taxmin). |
| Turi | **Binar**, matn emas. Kodirovka, qator oxiri, o'nlik ajratuvchi tushunchalari yo'q. |
| Bayt tartibi | **Big-endian** (Motorola). |
| Sonlar | `uint32` / `uint16`, o'lchamlar **0.0001 mm** birlikda butun son (masalan 2750 mm → `0x01A39DE0` = 27 500 000). |
| Matn | Faqat bitta qisqa ASCII maydon (pattern nomi `"001"`), nol bilan to'ldirilgan. |
| Hajm | 2–10 KB (1 pattern ≈ 0.6–1.6 KB). |

### Nega 3152, 3158, 3160 buyurtmalari yo'q

Holzma (`.ptx`) namunalaridagi `CUTS` qatorlarining kesish darajalari (6-ustun, `0..5`) solishtirildi:

| Buyurtma | `.ptx` dagi eng chuqur kesish | SPL bormi |
|---|---|---|
| 3151, 3153, 3155, 3156, 3157, 3159, 3161 | burilmagan patternlarda ≤ 3, burilgan (start=1) patternlarda ≤ 4 | **bor** |
| 3152 | pattern 1: `0..4` (burilmagan, 5 ta kesish darajasi) | yo'q |
| 3158 | pattern 2: `1..5` | yo'q |
| 3160 | patternlar 1,4,5,6: `1..5` | yo'q |

SPL formati **eng ko'pi bilan 5 ta tugun darajasini** (L1 = plita + 4 ta kesish darajasi) qo'llaydi (`c` va `f` yozuvlarida doimiy `5`).
Demak, chuqurligi bundan oshgan rejalar Holzma 3 postprotsessori tomonidan eksport qilinmagan (fayllarning yaratilish vaqtidagi bo'shliqlar ham shunga mos: 3151→3153 orasida 86 s). **Xulosa: MebeliX optimizatori Holzma 3 uchun kesish chuqurligini cheklashi kerak** (6-bo'limdagi savolga qarang).

---

## 2. To'liq struktura

### 2.1. Yozuv (record) sarlavhasi — har bir yozuv uchun 12 bayt

| Ofset | Hajm | Ma'nosi |
|---|---|---|
| 0 | u16 | `L` — payload uzunligi (tur baytidan **keyingi** baytlar, quyidagi "link" maydonisiz) |
| 2 | u16 | `level` — faqat `n` yozuvida tugun darajasi (1..5), qolganlarida 0 |
| 4 | u16 | `0x0000` (doimiy) |
| 6 | 2 bayt | `0x30 0x21` (ASCII `"0!"`, doimiy imzo) |
| 8 | 3 bayt | `00 00 00` |
| 11 | 1 bayt | Yozuv turi: `c`, `d`, `e`, `f`, `n`, `x` |
| 12 | `L` bayt | payload |
| 12+L | u32 (ixtiyoriy) | **link** — faqat `c`, `f`, `x` yozuvlarida (pastga qarang) |

### 2.2. Fayl ketma-ketligi

```
c  [link = 1-blok uzunligi]
── blok 1 (pattern "001") ─────────────────────────────
d
e
f  [link = n-yozuvlar + x sarlavhasi uzunligi]
n  (lv=1)  n (lv=2) ...  n            ← kesish daraxti, chuqurlik bo'yicha oldindan (pre-order)
x  [link = keyingi blok uzunligi]     ← oxirgi blokda link YO'Q (fayl shu yerda tugaydi)
── blok 2 (pattern "002") ─────────────────────────────
d e f n... x [link]
...
```

* "Blok uzunligi" = `d` sarlavhasi boshidan `x` ning 12 baytli sarlavhasi oxirigacha (x dagi link kirmaydi).
* `f` link = `41 × (n yozuvlar soni) + 12`. (Masalan 3161: 34 ta `n` → 1406 = `0x057E`.)
* Barcha `n` yozuvlari bir xil: 12 + 29 = **41 bayt**.

### 2.3. `c` — fayl sarlavhasi (L = 52, + 4 bayt link)

| Ofset (payload) | Tur | Qiymat | Ma'nosi |
|---|---|---|---|
| 0 | u32 | `0x02CF28C0` | doimiy (versiya/ID?) |
| 4 | u32 | 104 | doimiy |
| 8 | u32 | 1..7 | **patternlar (bloklar) soni** |
| 12 | u32 | 5 | maksimal daraja soni (doimiy) |
| 16..51 | — | 0 | zaxira |
| 52 | u32 | link | 1-blok uzunligi |

### 2.4. `d` — pattern (karta) sarlavhasi (L = 131)

| Ofset | Tur | Namunalardagi qiymatlar | Ma'nosi |
|---|---|---|---|
| 0 | u32 | `0x02CF28BF` | doimiy |
| 4 | u32 | 104 | doimiy |
| 8 | u32 | 101 | doimiy |
| 12..17 | — | 0 | |
| 18..23 | ASCII | `"001"`, `"002"`, ... | **pattern nomi** — 3 xonali tartib raqami, qolgani `\0` |
| 24 | u32 | 0 / 1 | **burilish (rotation) bayrog'i**: 0 → L1 = plita uzunligi (2750), 1 → L1 = plita eni (1830). 30/30 patternda tasdiqlandi |
| 28 | u32 | 1, 2 | **shu pattern bo'yicha kesiladigan plitalar soni** (takror) |
| 32 | u32 | = [28] | ikkinchi miqdor (barcha namunalarda [28] ga teng; "rejadagi/bajariladigan" bo'lishi mumkin) |
| 36 | u32 | 27 500 000 | plita uzunligi (×0.0001 mm) = `sheet@l` |
| 40 | u32 | 18 300 000 | plita eni = `sheet@w` |
| 44 | u32 | 160 000 | plita qalinligi = `sheet@t` (16 mm) |
| 48..73 | — | 0 | |
| 74 | u16 | = [28] | plitalar soni (yana bir marta, 16-bit) |
| 76 | u16 | 1 | doimiy (paket/kitobdagi plita soni? — savol) |
| 78..130 | — | 0 | |

### 2.5. `e` — mashina/optimizatsiya parametrlari (L = 460)

Barcha 30 patternda **bir xil**, faqat arra qalinligi (kerf) farq qiladi (3159 da 6 mm, loyiha `swSawthick="6"`).
Quyida nol bo'lmagan barcha 4-baytli so'zlar (u32, big-endian):

| Ofset | Qiymat | mm (÷10 000) | Ma'nosi (✔ tasdiqlangan / ? taxmin) |
|---|---|---|---|
| 16, 20 | 43 000 000 | 4300 | ? maksimal plita uzunligi/eni (mashina chegarasi) |
| 24, 28 | 1 000 000 | 100 | ? minimal o'lcham |
| 32, 36, 40, 44 | 20 000 | 2.0 | ? 4 tomon trim (loyiha `cTrimL=2`, `cTrimW=2` bilan mos, lekin namunalarda o'zgarmagan) |
| 60 | 50 000 | 5.0 | ? minimal chiqindi tilim (`swMinPruning=5`); geometriya bilan mos — 2.7 ga qarang |
| 72, 76 | 10 000 000 | 1000 | ? |
| 80 | 1000 | (son) | ? |
| 84, 104, 120, 124, 128, 132, 140 | 1 | (bayroq) | ? |
| 204 | 80 000 | 8 | ? |
| 208 | 100 000 | 10 | ? |
| 212 | 500 000 | 50 | ? |
| 216 | 200 000 | 20 | ? |
| **228** | 30 000 / 60 000 | **3.0 / 6.0** | ✔ **arra qalinligi** (`tool.cutting@swSawthick`) |
| 240 | 4 500 000 | 450 | ? |
| 252 | 1 240 000 | 124 | ? |
| 264 | 1 000 000 | 100 | ? |
| 268 | 50 000 | 5 | ? |
| 284 | 13 000 000 | 1300 | ? |
| **288** | 30 000 / 60 000 | 3.0 / 6.0 | ✔ arra qalinligi (takror) |
| 292, 296, 312 | 1 000 000 | 100 | ? |
| 316, 320 | 10 000 000 | 1000 | ? |
| 328 | 13 000 000 | 1300 | ? |
| 332, 344, 348, 448 | 99 999 000 | 9999.9 | ? "cheksiz" chegara |
| 340 | 100 | (son) | ? |
| **380, 384** | 30 000 / 60 000 | 3.0 / 6.0 | ✔ arra qalinligi (takror) |
| 388 | 5 000 | 0.5 | ? |
| 392 | 50 000 | 5 | ? |
| 452 | 1 500 000 | 150 | ? |
| boshqa barcha so'zlar | 0 | | |

**Generatsiya uchun tavsiya:** namunadagi `e` payloadini shablon sifatida aynan nusxalash va faqat 228, 288, 380, 384 ofsetlarga `kerf×10000` yozish.

### 2.6. `f` — pattern statistikasi (L = 32, + 4 bayt link)

| Ofset | Tur | Qiymatlar | Ma'nosi |
|---|---|---|---|
| 0..11 | — | 0 | |
| 12 | u32 | 5 | maksimal daraja (doimiy) |
| 16 | u32 | 4 (oddiy), 0..3 (faylning **oxirgi** patternida) | ? (6-bo'lim) |
| 20 | u32 | | ✔ **shu patterndan chiqadigan detallar jami** = (bir plitadagi detal-barglar soni) × `d[28]` |
| 24 | u32 | 0 | |
| 28 | u32 | 0 (oddiy), 1..4 (oxirgi pattern) | ? har doim `f[16] + f[28] = 4` |
| 32 | u32 | link | `41·n + 12` |

### 2.7. `n` — kesish daraxti tuguni (L = 29)

Sarlavhadagi `level` (u16) = tugun darajasi 1..5. Payload:

| Ofset | Tur | Qiymat | Ma'nosi |
|---|---|---|---|
| 0 | u16 | `0x0080` | doimiy |
| 2 | u8 | `level − 1` | daraja (0..4), sarlavha bilan takror |
| 3 | 5 bayt (big-endian) | 0 yoki 1..N | **detal indeksi** (0 = detal emas, oraliq bo'lak) |
| 8 | u32 | | **bo'lak o'lchami** shu daraja yo'nalishida (×0.0001 mm) |
| 12 | u8 | 4 | doimiy |
| 13..18 | — | 0 | |
| 19 | u8 | 99 (`0x63`) yoki 0 | 99 ⇔ tugun detal (indeks > 0). 551/551 tugunda mos |
| 20..28 | — | 0 | |

Kuzatilgan qoidalar (551 tugun, 30 pattern):
* Har patternda **aynan bitta L1** tugun bor.
* Detal-tugunlar faqat L3, L4, L5 da uchradi (L2 hech qachon detal emas, lekin format buni taqiqlamaydi).
* Bola tugunisiz va detalsiz (bo'sh) barg **yo'q** — chiqindi/qoldiq hech qachon yozilmaydi, u implisit.
* Detal-tugunning bolasi yo'q.

---

## 3. Kesish rejasi qanday kodlanadi

### 3.1. Daraxt va yo'nalishlar

Tugunlar **chuqurlik bo'yicha oldindan tartibda** (pre-order) yoziladi; ota-onasi — o'zidan oldingi eng yaqin, darajasi kichikroq tugun.
Aka-uka tugunlar tartibi = kesish tartibi (trim tomondan boshlab).

| Daraja | Nima | `size` qaysi yo'nalishda |
|---|---|---|
| L1 | butun plita | `rot=0` → X = plita uzunligi (2750); `rot=1` → X = plita eni (1830) |
| L2 | birinchi kesish polosalari | X bo'yicha (L1 ni bo'ladi) |
| L3 | L2 polosaning ichidagi bo'laklar | Y bo'yicha (plitaning ikkinchi o'lchami) |
| L4 | L3 bo'lak ichidagi bo'laklar | X bo'yicha (ota L2 o'lchami ichida) |
| L5 | L4 bo'lak ichidagi bo'laklar | Y bo'yicha (ota L3 o'lchami ichida) |

* Toq/juft darajalar navbatlashadi: juft (L2, L4) — X, toq (L3, L5) — Y.
* **Detal o'lchami = (barg `size`, ota tugun `size`)**. Masalan `L3 420 → L4 498 P7` ⇒ detal 498×420.
* Bitta bolali tugun (masalan `L3 95 → L4 2360 P9`) — polosaning oxirini kesib tashlash (detal uzunligini chiqarish).

### 3.2. Teksturani (grain) hisobga olish

`txt="true"` detallar (141 barg) **har doim** `cl` o'lchami plitaning uzun (2750) tomoni bo'ylab joylashgan:
`rot=0` da `cl` X yo'nalishda, `rot=1` da `cl` Y yo'nalishda. `txt="false"` detallar ikkala yo'nalishda ham uchraydi (aylantirish ruxsat).
SPL da alohida "burilgan detal" bayrog'i yo'q — burilish faqat qaysi daraja qaysi o'lchamni berishi orqali ifodalanadi.

### 3.3. Trim, kerf va qoldiqlar

* Trim va kerf `e` yozuvida (pattern darajasida), tugunlarga qo'shilmaydi. `size` = toza detal/polosa o'lchami.
* Geometrik tekshiruv (barcha 30 pattern, 263 ta ota tugun):
  * Plita darajasida (L2 polosalar L1 bo'yicha, L3 lar plitaning ikkinchi o'lchami bo'yicha): `ext − Σsize − kerf·m ≥ 7`; eng kichik zahira 7 mm = trim 2 + trim kerfi 3 + qarama-qarshi trim 2. Ya'ni: `2 + 3 + Σ(size_i + 3) + 2 ≤ plita o'lchami`.
  * Ichki darajalarda: `ext − Σsize − kerf·(m−1)` qiymati 0 yoki ≥ 5 (kerf=6 bo'lgan 3159 da ham) → oxirgi bo'lakdan keyin 5 mm dan kichik tilim qoldirilmaydi (`swMinPruning=5` / `e[60]=5.0`).
* **Qoldiq (delovoy ostatok / business waste)** faylda alohida yozilmaydi; u daraxt bilan qoplanmagan joy. (Masalan loyiha bo'yicha 3157 oxirgi patternida 2740×1543 qoldiq bor, SPL da faqat L2 lar yig'indisi 277 mm.)

### 3.4. Miqdorlar

* `d[28]` (= `d[32]` = `d[74..75]`) — shu pattern bilan kesiladigan plitalar soni. Faylda jami plitalar = Σ `d[28]` = loyihadagi `CS@cMaterialCount`.
* Detal soni = har patterndagi barg soni × `d[28]`. Paket (kitob) balandligi alohida berilmaydi — `d[76..77]=1` bo'lishi mumkin (savol).

### 3.5. Detal raqamlash (yorliqlar)

SPL da detal nomi, kodi, kromka, yorliq **yo'q** — faqat 1 dan boshlanadigan **detal indeksi**.
Indeks = Giblab `CS` operatsiyasi ichidagi `<part id="..."/>` ro'yxatidagi tartib raqami (plita-`part`lari hisobga olinmaydi).
Bu Holzma `.ptx` faylidagi `PARTS_REQ,1,<indeks>,...` raqami bilan aynan bir xil (7/7 faylda tekshirildi).
Ya'ni mashina detal ma'lumotini boshqa joydan (ehtimol shu tartibdagi ro'yxatdan) oladi — 6-bo'limdagi savol.

---

## 4. Loyiha ma'lumotlaridan maydonlarga moslik

| Loyiha (`.project`) | SPL maydoni |
|---|---|
| `CS` operatsiyasi (`typeId="CS"`) → bitta material | bitta `.SPL` fayl |
| `good[typeId=sheet]@l / @w / @t` | `d[36] / d[40] / d[44]` ×10 000 |
| `tool.cutting@swSawthick` | `e[228], e[288], e[380], e[384]` ×10 000 |
| `CS@cTrimL / cTrimW` (=2) | ehtimol `e[32..44]` (namunalarda o'zgarmagan) |
| `CS@cMaterialCount` | Σ `d[28]` |
| `CS@cPartCount` | Σ `f[20]` |
| `CS` dagi `<part id>` tartibi (1-asosli) | `n[3..7]` detal indeksi |
| `part@cl`, `part@cw` (kesish o'lchami) | barg `size` va ota `size` (tartib — grain/burilishga qarab) |
| `part@count` | indeks barglari soni × `d[28]` yig'indisi |
| `part@txt` (tekstura) | joylashuv yo'nalishi (3.2) |
| `part@jl / jw` (kromka oldidan qisqartirilgan) | **ishlatilmaydi** — SPL `cl/cw` ni oladi |
| `part@name`, `code`, kromka (`elb/ell/elr/elt`) | **SPL ga tushmaydi** |

**Muhim:** namunalardagi barcha detallarda `cl = l`, `cw = w`, shuning uchun `cl` va `l` ni farqlab bo'lmaydi; `jl/jw` esa aniq ishlatilmagan (masalan 01_001: `l=1900`, `jl=1898`, SPL da 1900).

### 4.1. Tekshiruv natijalari (barcha 7 namuna)

| Fayl | Material (loyiha `CS`) | Patternlar | Plitalar Σd[28] = cMaterialCount | Detallar Σ = cPartCount | Turli indekslar = CS dagi detal qatorlari | Soni/o'lcham xatolari |
|---|---|---|---|---|---|---|
| 3151 | LMDF BELI KARONA GLYANETS | 6 | 6 = 6 | 61 = 61 | 29 = 29 | 0 / 0 |
| 3153 | LDSP ASTANA TEKSTURA | 5 | 5 = 5 | 70 = 70 | 55 = 55 | 0 / 0 |
| 3155 | LMDF DUB VATAN | 3 | 3 = 3 | 33 = 33 | 23 = 23 | 0 / 0 |
| 3156 | LDSP KASHMIR SHAGREN | 7 | 8 = 8 | 73 = 73 | 42 = 42 | 0 / 0 |
| 3157 | LDSP KASHMIR SHAGREN | 5 | 7 = 7 | 36 = 36 | 22 = 22 | 0 / 0 |
| 3159 | LMDF BELI KARONA TEKSTURA (kerf 6) | 3 | 3 = 3 | 20 = 20 | 11 = 11 | 0 / 0 |
| 3161 | LDSP PIKARD | 1 | 1 = 1 | 18 = 18 | 10 = 10 | 0 / 0 |

Mos loyiha fayli — **`NNNN_<mijoz>.project`** (pastki chiziqli, yangi variant): unda `CS` operatsiyasida `cTrimL`, `cPartCount`, `cMaterialCount` va `part@cl/cw` bor. Probelli eski variant (`NNNN <mijoz>.project`) da bu atributlar yo'q, ba'zi buyurtmalarda materiallar ham boshqa (masalan 3155 eski variantida "LDSP UD", yangisida "LMDF DUB VATAN" — SPL yangisiga mos).
Indeks tartibi `CS` dagi ro'yxat tartibi ekanligi 3151 da isbotlanadi: `id` bo'yicha saralansa 2 ta son mos kelmaydi, ro'yxat tartibida — 0.

### 4.2. Misol A — 3161 (1 pattern, burilmagan, kerf 3)

Loyiha (`CS` ro'yxati tartibida): P1=`01_001 bok` 1900×347, P2=`01_002 bok` 1900×347, P3=`01_003 tom` 868×347, P4/P5=`01_004 polka` 868×346 (2+2), P6=`01_005 pol` 868×346, P7=`01_006 Fasad` 498×420 ×2, P8=`01_007 bok` 504×346, P9=`01_008 bok` 300×346 ×6, P10=`01_009 sokl` 100×868.

```
d: name="001" rot=0 qty=1 2750×1830×16
L1 2750
  L2 2254
    L3 420   → L4 498 P7 | L4 498 P7 | L4 868 → L5 346 P4 | L4 346 → L5 300 P9
    L3 346   → L4 868 P4 | L4 868 P5 | L4 504 P8
    L3 346   → L4 300 P9 | L4 868 P5 | L4 868 P6
    L3 347   → L4 1900 P1 | L4 346 → L5 300 P9
    L3 347   → L4 1900 P2
  L2 352
    L3 868 → L4 347 P3
    L3 300 → L4 346 P9   (×3 ta shunday L3)
  L2 100
    L3 868 P10
f: [16]=4 [20]=18 [28]=0
```
P9 (300×346) jami 6 = loyiha `count=6`; P4+P5 = 4; jami 18 = `cPartCount`. L2 yig'indisi: 2+3+(2254+3)+(352+3)+(100+3) = 2720 ≤ 2748.

Baytlarda birinchi `n` yozuvlari (fayl ofseti `0x2DB`):
```
00 1D 00 01 00 00 30 21 00 00 00 6E | 00 80 00 00 00 00 00 00 01 A3 9D E0 04 00 ... 00   ← L1 2750
00 1D 00 02 00 00 30 21 00 00 00 6E | 00 80 01 00 00 00 00 00 01 57 EE E0 04 00 ... 00   ← L2 2254
00 1D 00 04 00 00 30 21 00 00 00 6E | 00 80 03 00 00 00 00 07 00 4B FD 20 04 00 00 00 00 00 00 63 00..  ← L4 498 P7
```

### 4.3. Misol B — 3157 pattern "002" (burilgan, 2 ta plita)

```
d: name="002" rot=1 qty=2 (d[74..75]=2, d[76..77]=1)
L1 1830                       ← rot=1: L1 = plita eni
  L2 1230                     ← 1830 bo'yicha
    L3 2644                   ← 2750 bo'yicha
      L4 577 P5   (01_003 Fasad 2644×577)
      L4 577 P6   (01_003 Fasad 2644×577)
      L4 65 → L5 1785 P22   (01_018 qosh 65×1785)
  L2 587
    L3 1128 P12  (01_008 polka 1128×587)
    L3 400  P14  (01_010 bok 400×587)
    L3 1128 → L4 557 P13 (01_009 polka 1128×557)
f: [20]=12 (= 6 barg × 2 plita)
```
L2: 2+3+(1230+3)+(587+3)=1828 ≤ 1830−2 → aynan 7 mm zahira (namunalardagi eng kichik).

### 4.4. Misol C — 3159 (kerf 6)

Loyiha `swSawthick="6"` → `e[228]=e[288]=e[380]=e[384]=0x0000EA60` (60 000). Boshqa barcha `e` baytlari 3 mm li fayllar bilan bir xil.
Pattern "001": `L2 2400 → L3 533 → L4 564 P5 | L4 1825 P3`: 564+6+1825 = 2395, polosa 2400 dan 5 mm qoladi (min. tilim 5).
`txt="true"` (fasad) detallar `cl` (1825) bilan 2750 yo'nalishida.

---

## 5. Minimal qayta tiklangan misol

Bitta plita 2750×1830×16, kerf 3, bitta polosa 800 mm, ichida 2 ta 800×600 detal (indeks 1, `count=2`).
Daraxt: `L1 2750 → L2 800 → (L3 600 P1, L3 600 P1)`. Fayl hajmi 907 bayt.

```
0000: 00 34 00 00 00 00 30 21 00 00 00 63   02 CF 28 C0 00 00 00 68 00 00 00 01 00 00 00 05  (c: 1 pattern, 5 daraja)
      ... 36 ta nol ...                      00 00 03 47                                     (c link = 839 = blok uzunligi)
0044: 00 83 00 00 00 00 30 21 00 00 00 64   02 CF 28 BF 00 00 00 68 00 00 00 65 00×6
      30 30 31 00 00 00  00 00 00 00  00 00 00 01  00 00 00 01                               (name "001", rot 0, qty 1, qty 1)
      01 A3 9D E0  01 17 3C 60  00 02 71 00  ...  [d+74] 00 01 00 01 ... (131 bayt)
00D3: 00 01 CC 00 00 00 30 21 00 00 00 65   <460 bayt e-shablon, kerf=0x7530 @228/288/380/384>
02AB: 00 20 00 00 00 00 30 21 00 00 00 66   00×12 00 00 00 05 00 00 00 04 00 00 00 02 00×4 00 00 00 00
      00 00 00 B0                                                                             (f: 2 detal; link = 4·41+12 = 176)
02DB: 00 1D 00 01 00 00 30 21 00 00 00 6E   00 80 00 00 00 00 00 00 01 A3 9D E0 04 00×16     (L1 2750)
0304: 00 1D 00 02 00 00 30 21 00 00 00 6E   00 80 01 00 00 00 00 00 00 7A 12 00 04 00×16     (L2 800)
032D: 00 1D 00 03 00 00 30 21 00 00 00 6E   00 80 02 00 00 00 00 01 00 5B 8D 80 04 00×6 63 00×9  (L3 600 P1)
0356: 00 1D 00 03 00 00 30 21 00 00 00 6E   00 80 02 00 00 00 00 01 00 5B 8D 80 04 00×6 63 00×9  (L3 600 P1)
037F: 00 00 00 00 00 00 30 21 00 00 00 78                                                   (x, oxirgi — link yo'q)
```

Generator (Python, namunalar bilan baytma-bayt tekshirilgan):

```python
import struct
be32 = lambda v: struct.pack('>I', v)
um   = lambda mm: int(round(mm * 10000))
def rec(t, payload, lv=0, link=None):
    h = struct.pack('>HHH', len(payload), lv, 0) + b'\x30\x21\x00\x00\x00' + t.encode()
    return h + payload + (be32(link) if link is not None else b'')

def build_spl(patterns, E_template, kerf):
    E = bytearray(E_template)                      # 460 bayt, namunadan
    for o in (228, 288, 380, 384): E[o:o+4] = be32(um(kerf))
    blocks = []
    for p in patterns:                             # p: name, rot, qty, L, W, T, f16, f28, nodes=[(lv, idx, size)]
        d = bytearray(131)
        d[0:4] = be32(0x02CF28BF); d[4:8] = be32(104); d[8:12] = be32(101)
        d[18:18+len(p['name'])] = p['name'].encode('ascii')
        d[24:28] = be32(p['rot']); d[28:32] = be32(p['qty']); d[32:36] = be32(p['qty'])
        d[36:40] = be32(um(p['L'])); d[40:44] = be32(um(p['W'])); d[44:48] = be32(um(p['T']))
        d[74:76] = struct.pack('>H', p['qty']); d[76:78] = struct.pack('>H', 1)
        nb, leaves = b'', 0
        for lv, idx, size in p['nodes']:
            q = bytearray(29); q[0:2] = b'\x00\x80'; q[2] = lv - 1
            q[3:8] = idx.to_bytes(5, 'big'); q[8:12] = be32(um(size)); q[12] = 4
            if idx: q[19] = 99; leaves += 1
            nb += rec('n', bytes(q), lv)
        xh = rec('x', b'')
        f = bytearray(32); f[12:16] = be32(5); f[16:20] = be32(p['f16'])
        f[20:24] = be32(leaves * p['qty']); f[28:32] = be32(p['f28'])
        blocks.append(rec('d', bytes(d)) + rec('e', bytes(E)) + rec('f', bytes(f), link=len(nb)+len(xh)) + nb + xh)
    c = bytearray(52); c[0:4] = be32(0x02CF28C0); c[4:8] = be32(104)
    c[8:12] = be32(len(blocks)); c[12:16] = be32(5)
    out = rec('c', bytes(c), link=len(blocks[0]))
    for i, b in enumerate(blocks):
        out += b + (be32(len(blocks[i+1])) if i + 1 < len(blocks) else b'')
    return out
```

MebeliX tomonidan kerak bo'ladigan cheklovlar:
* Daraxt chuqurligi ≤ 5 (L1 + 4 kesish darajasi); aks holda bu mashinaga eksport qilib bo'lmaydi.
* Har patternda bitta L1; L1 = `rot ? W : L`.
* Detal indekslari — materialning detal ro'yxatidagi 1-asosli tartib (xuddi shu tartib `.ptx` `PARTS_REQ` da ham ishlatiladi).
* Fayl nomi 8 belgi (`NNNN_` + 3 harf) — bir buyurtmaning bir nechta materiali to'qnashadi.

---

## 6. Noaniq maydonlar — foydalanuvchiga savollar

1. **`f[16]` va `f[28]`** — oddiy patternlarda 4/0, faylning oxirgi (qoldiqli) patternida 1/3, 3/1, 2/2, 0/4; yig'indi doim 4. Bu trim qilinadigan tomonlar soni / qoldiq tomonlari bo'lishi mumkin. Mashinada (Holzma CADmatic?) shu qiymatlar nimani bildiradi va noto'g'ri bo'lsa nima bo'ladi? Qoldiqsiz patternlar uchun 4/0 yozish yetarlimi?
2. **`e` yozuvi** (460 bayt): trim (2.0 ×4), 4300, 100, 1000, 1300, 450, 124, 150, 9999.9 qiymatlari mashinaning qaysi sozlamalari? Trim loyihada o'zgarsa (`cTrimL≠2`) qaysi ofsetlar o'zgaradi — buni tekshirish uchun boshqa trim bilan bitta namuna kerak.
3. **`d[32]`** har doim `d[28]` (plitalar soni) ga teng, **`d[76..77]=1`** — bular "paketdagi plita soni" (kitob balandligi, `swPackageHeight=40`)mi? 2+ plitali paket bilan namuna bormi?
4. **Detal ma'lumotlari** (nom, kod, yorliq) SPL da yo'q. Mashina ularni qayerdan oladi — alohida ro'yxat fayli (masalan `.ptx` yoki boshqa) ham ko'chiriladimi, yoki operator faqat indeks bilan ishlaydimi?
5. **3152, 3158, 3160** uchun SPL yo'qligi — eksport xato bergani (kesish darajasi > 4) sababli ekanini tasdiqlaysizmi? Mashina haqiqatan maksimal 4 kesish darajasini qabul qiladimi?
6. **Fayl nomi**: postprotsessor nomni 8 belgiga qisqartiradimi (mashina DOS 8.3 talab qiladimi)? Bir buyurtmaning ikkinchi materiali (masalan XDF yoki ikkinchi LDSP) uchun qanday nom ishlatiladi?
7. `c[0]=0x02CF28C0`, `d[0]=0x02CF28BF`, 104, 101 doimiylari — versiya raqamimi? Boshqa sana/kompyuterda chiqarilgan faylda o'zgaradimi?
8. Plita o'lchamlari faqat 2750×1830×16 bilan ko'rilgan — boshqa format (masalan 2800×2070) uchun namuna bormi (L1 ning burilishi va `e` chegaralari tekshirish uchun)?

---

## 7. 2026-10-04 onlayn namunasi bilan tekshiruv

Bitta loyiha (3 karta, burilishlar 4, 2 ta burilgan karta, 4 kesish darajasi): generator natijasi namuna bilan **bayt-ma-bayt
bir xil** (`tools/bench/pp_online_check_saw.py spl`). Tuzatildi: fayl nomi — loyiha nomi avval **lotinga o'giriladi**, keyin
8 belgi (`Без имени` → `Bez_imen.SPL`; onlayn tizim 8 belgili dastur nomini so'raydi, standart — shu). Lotin nomlarda o'zgarish yo'q.
