# SCM Xilog v3 — `.pgm` (ikkilik konteyner + Xilog matni)

> Manba: korxonaning o'z namunalari — `post prtsessorlar/PRISADKA APPARAT/SCM Xilog v3/*.zip` (15 buyurtma, **1009 fayl**)
> va ularning `.project` XML fayllaridagi XNC operatsiyalari (1014 dastur). Faqat chiqish fayllari va loyiha XML o'qildi,
> hech qanday dastur ikkiligi ochilmadi. Mijoz ismlari — «mijoz».
>
> **Holat: to'liq tushunilgan (generatsiyaga tayyor).** Tekshiruv natijasi (§3.5):
> * yozuvchi (writer) parsing natijasidan **1009/1009** faylni bayt-ma-bayt qayta yasadi;
> * XNC → `.pgm` to'liq zanjir (sarlavha izohi, R, barcha buyruqlar): loyiha fayli eksportdan keyin o'zgarmagan
>   13 buyurtmada **881/881 fayl bayt-ma-bayt bir xil**;
> * buyruq qatorlari (sarlavhadan tashqari) — 3173 dan tashqari barcha **958/958** dastur aynan mos.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Arxiv | bitta buyurtma = bitta zip `<buyurtma>_<mijoz>.zip`, ichida papkasiz tekis ro'yxat |
| Fayl | **bitta XNC operatsiyasi = bitta `.pgm`** (bir detal tomoni uchun bitta dastur) |
| Nom | `<XNC operatsiya kodi>.pgm` — kod o'zgarishsiz (`operation@code`), masalan `316601_01_003.pgm` |
| Takror kod | bir xil kodli ikkinchi, uchinchi… operatsiya — `<kod> (1).pgm`, `<kod> (2).pgm` (XML tartibida; 82 ta turli tarkibli takror guruhda tasdiqlangan) |
| Orqa tomon | alohida XNC operatsiyasi (`side="false"` yoki eski formatda `side="2"`), kodi odatda `…_2` bilan tugaydi: `316601_13_005_2.pgm` |
| Format | **ikkilik** konteyner (`Xilog3-7.0`), ichida ASCII Xilog matn qatorlari |
| Kodlash | namunalarda faqat ASCII (0x80+ bayt yo'q); kirill uchun kodlash noma'lum (❓ Q5) |
| Qator oxiri | yo'q — har qator alohida yozuv (uzunlik maydoni + NUL) |
| Kasr ajratuvchi | nuqta `.`; son **2 xonagacha yaxlitlanadi**, oxirgi nollar va `.` olib tashlanadi (`298.2989→298.3`, `283.7059→283.71`, `568.00→568`, `-10`) |
| Birlik | mm (`*MM`) |

**Kod tuzilishi.** Odatda `kod = <mahsulot kodi>_<detal kodi>[_2]`: mahsulot (`good@code`) = buyurtma raqami (4) + mahsulot
tartib raqami (2), masalan `3166`+`01`; detal kodi `part@code` = `<modul>_<pozitsiya>` (`01_003`). 933/1014 dastur shu qoidaga
mos; qolganlari — «Кодирование» shabloni bilan berilgan kod (`01_041x047x0`) yoki eski loyiha. **Postprotsessor kodni o'zi
hosil qilmaydi — XNC operatsiyasining kodini fayl nomiga qo'yadi.**

## 2. Konteyner tuzilishi (hex)

Barcha sonlar little-endian. 1009 faylning hammasida quyidagi bloklar tekshirildi (`tools/xl_parse.py` assert'lari).

### 2.1. Sarlavha 0x000–0x108 (doimiy, 2 ta o'lcham maydonidan tashqari)

| Ofset | Uzunlik | Tarkib | Ma'no |
|---|---|---|---|
| 0x000 | 0x42 | `42 4D 42 00 … FF FF FF 00 00 00 00 00` | 1×1 piksel, 1-bit BMP (oq) — eskiz (thumbnail). 1009 faylda bir xil |
| 0x042 | 12 | `Xilog3-7.0 ` + `00` | versiya satri |
| 0x04E | 4×3 | `05 00 00 00` `02 00 00 00` `01 00 00 00` | doimiy (ma'nosi noma'lum) |
| 0x05A | 2 | `00 00` | doimiy |
| 0x05C | 4 | `4` | doimiy |
| 0x060 | 4 | `0` | doimiy |
| 0x064 | 4 | `0x42` | ofset: versiya satri boshi |
| 0x068 | 4 | `0x42` | ofset (xuddi shu) |
| 0x06C | 4 | `0x46` | doimiy (ofset deb taxmin) |
| 0x070 | 4 | `0x88` | ofset: o'zgaruvchilar jadvali boshi |
| **0x074** | 4 | **`fayl_hajmi − 0x8A`** | tana uzunligi (0x8A dan oxirigacha) |
| 0x078 | 4 | `4` | doimiy |
| 0x07C | 4 | `0` | doimiy |
| **0x080** | 4 | **`fayl_hajmi`** | to'liq fayl uzunligi |
| 0x084 | 4 | `0` | doimiy |
| 0x088 | 0x81 | o'zgaruvchilar jadvali (doimiy) | 4 yozuv: `DZ` (`V` b), `FLD` (`V` c, tur bayti 0x21), `DX` (`V` \`), `DY` (`V` a). Yozuv: `00 00 00 10 2x` + 16×`00` + `07 61 <len> <nom> 56 <indeks> 00 69 00 00`. Qiymatlar bu yerda saqlanmaydi |

### 2.2. `H` bloki (0x109 dan)

| Nisbiy ofset | Tarkib |
|---|---|
| +0 | `01 03 01 00` (doimiy) |
| +4 | `u16 L` = `M + 3 + len(H_matn)` (blok uzunligi, oxirgi NUL siz) |
| +6 | `u16 M` = `81 + len(izoh)` (= `S` tokenining nisbiy ofseti) |
| +8 | 12 × `00` |
| +20 | `7F FF` |
| +22 | `51 <f32 DX>` `51 <f32 DY>` `51 <f32 DZ>` — `Q` + float32 |
| +37 | tokenlar (37 bayt, faqat `R` o'zgaradi): `69 41 42` (i "AB" — maydon), `69 00 00` (C=0), `6C 00 00 00 00` (l 0), `69 <i16 R>` (R), `69 02 00` (*MM), `61 03 64 65 66` (a "def" — asboblar jadvali), `69 00 00`, `69 01 00`, `69 00 00` ×3 |
| +74 | `51 00 00 00 00` (Q 0.0) |
| +79 | `3B <u8 izoh_uzunligi> <izoh>` |
| +M | `53 <u16 len> <H_matn> 00` — to'liq `H …` qatori matn sifatida |

Token turlari: `i`(0x69)+int16, `l`(0x6C)+int32, `Q`(0x51)+float32, `a`(0x61)+u8 uzunlik+satr, `S`(0x53)+u16 uzunlik+satr.
Faqat `H` qatori tokenlangan; qolgan qatorlar faqat matn.

### 2.3. Buyruq yozuvlari (`0x109 + L + 1` dan)

```
02 37 10 | u16 RL | 08 00 | 53 | u16 TL | <TL bayt ASCII matn> | 00        RL = TL + 11 (02 baytidan NUL gacha)
...
02 37 10 <fayl oxiri>   ← yakunlovchi marker (uzunliksiz)
```
Oxirgi matnli yozuv har doim `;END`. Yozish algoritmi: doimiy 0x109 baytlik prefiks → `H` bloki → yozuvlar → `02 37 10`
→ 0x74 va 0x80 dagi o'lchamlarni to'g'irlash. Shu algoritm 1009/1009 faylni bayt-ma-bayt qayta yasadi.

## 3. Sintaksis va XNC → Xilog moslik

### 3.1. Koordinata tizimi

* **XNC (`.project`) konventsiyasi** (data bilan isbotlangan): boshlanish — **chap-yuqori burchak**, X o'ngga (L bo'ylab),
  Y «pastga» (W bo'ylab): `y=0` — `elt` (yuqori qirra), `y=dy` — `elb` (pastki), `x=0` — `ell`, `x=dx` — `elr`.
  Dalil: minifiks juftliklari — `bb` (DrillBottom) qirra teshigi 66 holatda `y=dy` dan chiqib Bore15 kosasiga yetadi, 0 holatda
  `y=0` dan; `bt` — 22 holatda `y=0` dan, 0 holatda `y=dy` dan. Bu `xnc.py` dagi «LT, Y pastga» bilan mos.
* **Xilog:** yuz tomon (`side=true`) uchun **X = x, Y = y — hech qanday o'zgartirishsiz** (aylantirish, Y teskari qilish yo'q).
  Ya'ni Xilog'ning (0,0) nuqtasi = detalning `elt`×`ell` burchagi. Xilog o'qlari XNC chizmasiga nisbatan oynali (qo'l yo'nalishi
  teskari) — shuning uchun yoy yo'nalishi va korreksiya tomoni raqam bo'yicha «teskari» ko'rinadi (§3.4).
* **Orqa tomon** (`side=false`/`2`): **X → dx − x**, Y o'zgarmaydi (35 ta bf va 7 ta gr dasturida tasdiqlangan; masalan
  paz `x1=733→x2=3` → `XG0 X=3 … G1 X=733`).
* Z: teshik/freza chuqurligi musbat son, yuzadan pastga (`Z=dp`).

### 3.2. `H` — detal sarlavhasi (har faylda birinchi)

```
H DX=<dx> DY=<dy> DZ=<dz> -AB C=0 R=<soni> *MM /"def.tlg" ;<izoh>
```
| Maydon | Manba | Holat |
|---|---|---|
| DX, DY, DZ | XNC `program@dx/dy/dz` (= detal L, W, qalinlik) | data |
| `-AB` | ishchi maydon AB | doimiy (stanok sozlamasi) |
| `C=0` | — | doimiy |
| `R` | XNC **operatsiya** `count` (detal soni, 1…10) | data |
| `*MM` | birlik mm | doimiy |
| `/"def.tlg"` | asboblar jadvali fayli | doimiy (stanok sozlamasi) |
| izoh | kromkalar + operatsiya nomi (`typeName`) | data |

**Izoh:** har kromkalangan qirra uchun `<strelka>:(<elSymbol>) <t>mm` + **2 bo'sh joy**, tartib `elt, elb, ell, elr`, oxirida
operatsiya nomi (`00_009 pol`). `elSymbol` va `t` — qirraga bog'langan EL operatsiyasidan (`@operation#N` → `elSymbol="A"`,
`t="1"` → `(A) 1mm`). Strelka — qirradan ichkariga normal (XNC Y-pastga chizmasida):

| Qirra | yuz tomon | orqa tomon |
|---|---|---|
| elt | `V` | `V` |
| elb | `^` | `^` |
| ell | `>` | `<` |
| elr | `<` | `>` |

Misol: `V:(A) 1mm  ^:(A) 1mm  <:(A) 1mm  01_002 pol`. Kromkasiz detal: faqat nom.

### 3.3. Teshiklar — `XBO`

```
XBO X=<x> Y=<y> Z=<chuqurlik> D=<diametr> N=<P|L> F=<yuz>
```
| XNC (MebeliX) | F | X | Y | Z | N |
|---|---|---|---|---|---|
| `bf` DrillFront | 1 | x | y | dp | `L` agar dp ≥ dz (o'tuvchi), aks holda `P` |
| `br` DrillRight (x=dx qirra) | **2** | dz − z | y | dp | P |
| `bl` DrillLeft (x=0 qirra) | **3** | dz − z | y | dp | P |
| `bb` DrillBottom (y=dy qirra) | **4** | x | dz − z | dp | P |
| `bt` DrillTop (y=0 qirra) | **5** | x | dz − z | dp | P |

* `D` — XNC `tool@d` (asbob nomi `Bore4.5`, `BoreTh8` chiqmaydi; stanok asbobni D va N bo'yicha tanlaydi).
* `m="true"` (o'rtada) → balandlik = dz/2. `m="false"` → **dz − z** (masalan dz=18, z=8 → `X=10`; 24 holatda tasdiqlangan).
  Qirra yuzlarida tekislikdagi 2 koordinatadan biri (qirra bo'ylab) — panel koordinatasi, ikkinchisi — balandlik.
* O'tuvchi teshik: `var throughBoreDepth = dz+3.00` hisoblanadi → `Z=19` (dz=16), `N=L` (lancia — o'tuvchi parma).
  Namunalarda `N=L` faqat `BoreTh*` asbobli frontal teshiklarda (= dp ≥ dz) — qaysi qoida asl ekanini ajratib bo'lmaydi (❓ Q3).
* `ac/as/av` massivlari: namunalarda hammasi `ac=1` — massivni alohida `XBO` qatorlariga yoyish taklif qilinadi (tekshirilmagan).
* Tartib — XNC buyruqlari tartibida, guruhlash/saralash yo'q.
* Orqa tomon: X → dx − x; qirra teshiklari uchun `bl↔br` (F=3↔F=2) almashinuvi **faraz** (namunada orqa tomonda qirra teshigi yo'q).

### 3.4. Paz (arra) va frezalash

**Paz (`gr` / Groove):**
```
XG0 X=<x1> Y=<y1> Z=<dp> T=-1 F=1 C=<c>
G1 X=<x2> Y=<y2>
```
* Paz eni `t` (4 / 6 / 10.5) va asbob `Cut4` **chiqmaydi**; har paz — bitta o'tish (60/60). Eni stanokda qanday ta'minlanishi — ❓ Q1.
* `throughCutDepth = dz+3` → `Z=19`. `gr@comment` chiqmaydi. Namunalarda faqat `c=0`.

**Frezalash (`ms`/`ml`/`mac`):**
```
XGIN Q=0 G=2 C=<c>                       ← kirish (lead-in) parametrlari
XG0 X=<x> Y=<y> Z=<dp> T=-1 F=1 C=<c>    ← MillStart
XL2P X=<x> Y=<y>                         ← MillLine
G2|G3 X=<x> Y=<y> I=<cx> J=<cy>          ← MillArcCenter (I, J — markaz, absolyut)
```
* `c` raqami o'zgarishsiz (`c=1`→`C=1` 44 ta, `c=2`→`C=2` 21 ta). XNC'da 1 — o'ng, 2 — chap; Xilog oynali o'qlarda buni o'zi to'g'ri talqin qiladi.
* `dir="true"` → **G2**, `dir="false"` → **G3** (51/51). (Raqamlar bir xil, lekin Xilog o'qlari oynali — shuning uchun «teskari».)
* `in=0 out=1` (namunalarda yagona kombinatsiya) → `XGIN Q=0 G=2`; `XGOUT` chiqmaydi. Boshqa `in/out` kodlari — ❓ Q2.
* Asbob (`Mill8`, D=8) chiqmaydi: `T=-1` (❓ Q1). `contMillDepth = dz` → `Z=16`. Kontur panel tashqarisidan boshlanishi mumkin (`Y=-10`, `X=-10`).
* `MillArc` (R bilan), `MillArc3P`, `MillFillet`, `MillRect`, `MillEllipse` — Xilog'da namunasi yo'q: eksportdan oldin
  `xnc.evaluate()` / `mill_arc()` bilan `MillLine` + `MillArcCenter` ga yoyish kerak (ellips — siniq chiziq `XL2P`).
* Orqa tomonda frezalash namunasi yo'q: X → dx − x bilan birga **G2↔G3 va C 1↔2 almashinuvi kerak** (faraz).

### 3.5. Tekshiruv (avtomatik komparator)

Skriptlar (scratchpad, repoga kirmaydi): `xl_parse.py` (o'quvchi), `xl_write.py` (yozuvchi), `xl_cmp.py` (XNC → kutilgan qatorlar).

| O'lchov | Natija |
|---|---|
| Fayllar parse qilindi (barcha assert'lar) | 1009 / 1009 |
| Yozuvchi bayt-ma-bayt qayta yasadi | 1009 / 1009 |
| Buyruq qatorlari aynan mos (3173 siz) | 958 / 958 dastur, 9980 / 10135 qator jami |
| XNC → `.pgm` to'liq bayt-ma-bayt (3173, 3183 siz) | 881 / 881 |
| Qamrov (to'g'ri chiqqan dasturlar) | bf 768 (+35 orqa), bl 381, br 360, bt 92, bb 83, gr 37 (+7 orqa), ms 53, ml 53, mac 38 |

Mos kelmaslik sinflari (hammasi manba bilan bog'liq, format bilan emas):
1. **3173** — `.project` eksportdan keyin tahrirlangan (01-oktyabr, zip 30-sentyabr): 56 op vs 51 fayl, 24 faylda boshqa o'lcham/teshiklar.
   Tarkib bo'yicha qidirilganda 42/51 fayl biror XNC dasturiga aynan mos.
2. **3183** — faqat eski `3183 mijoz.project` bor (`side="1"/"2"`, op'da `count` yo'q, detallarda kromka yo'q): buyruqlar 77/77 mos,
   lekin `R=` va izohdagi kromkalarni tiklab bo'lmaydi.

### 3.6. Uchta detal — yonma-yon

**A) `316601_01_001` (1250×500×16, elb=A).** XNC → Xilog:
```
bb x=785.99 z=8 m=true dp=32 Bore4.5     → XBO X=785.99 Y=8 Z=32 D=4.5 N=P F=4
bb x=1180   z=8 m=true dp=34             → XBO X=1180 Y=8 Z=34 D=4.5 N=P F=4
bf x=8 y=70 dp=throughBoreDepth BoreTh8  → XBO X=8 Y=70 Z=19 D=8 N=L F=1
bf x=1242 y=430 (o'sha)                  → XBO X=1242 Y=430 Z=19 D=8 N=L F=1
sarlavha                                 → H DX=1250 DY=500 DZ=16 -AB C=0 R=1 *MM /"def.tlg" ;^:(A) 1mm  01_001 pb-pol
```
**B) `317001_01_002` (1165×626×16, elt+elb+elr) — freza c=2, dir=true:**
```
bt x=901 z=8 dp=34       → XBO X=901 Y=8 Z=34 D=4.5 N=P F=5
bb x=102 z=8 dp=23.3     → XBO X=102 Y=8 Z=23.3 D=8 N=P F=4
bl y=70 / br y=220       → XBO X=8 Y=70 … F=3 / XBO X=8 Y=220 … F=2
bf x=70 y=592 dp=12.5    → XBO X=70 Y=592 Z=12.5 D=15 N=P F=1   (Bore15 — y=dy qirra yonida, bb bilan juft)
ms x=-10 y=0 dp=contMillDepth in=0 out=1 c=2 → XGIN Q=0 G=2 C=2 / XG0 X=-10 Y=0 Z=16 T=-1 F=1 C=2
ml x=1015 y=0            → XL2P X=1015 Y=0
mac x=1165 y=150 cx=1015 cy=150 dir=true → G2 X=1165 Y=150 I=1015 J=150
ml x=1165 y=636          → XL2P X=1165 Y=636
izoh: V:(A) 1mm  ^:(A) 1mm  <:(A) 1mm  01_002 pol
```
**C) `316601_13_008` (368×582×16, elb+ell=C), 6 nusxa `(1)…(5)`, c=1, dir=false:**
```
bt x=69 z=8 dp=34        → XBO X=69 Y=8 Z=34 D=4.5 N=P F=5
br y=532 z=8 dp=34       → XBO X=8 Y=532 Z=34 D=4.5 N=P F=2
ms x=0 y=-10 c=1         → XGIN Q=0 G=2 C=1 / XG0 X=0 Y=-10 Z=16 T=-1 F=1 C=1
mac x=300 y=582 cx=298.2989 cy=283.7059 dir=false → G3 X=300 Y=582 I=298.3 J=283.71
```
**D) Orqa tomon `317902_05_006_2` (1648×350, side=false):** `gr x1=0 y1=175 → x2=1648 y2=175 dp=10.5` →
`XG0 X=1648 Y=175 Z=10.5 T=-1 F=1 C=0` / `G1 X=0 Y=175`. `316601_13_005_2`: `bf x=34 y=70` → `XBO X=564 Y=70` (dx=598).
**E) Balandlik `m=false`:** `316601_14_024` (dz=18): `bl y=174.75 z=8 m=false` → `XBO X=10 Y=174.75 Z=34 D=8 N=P F=3`.

## 4. Doimiy va ma'lumotga bog'liq maydonlar

* **Doimiy (stanok/postprotsessor sozlamasi):** BMP eskiz, `Xilog3-7.0`, sarlavha jadvali, o'zgaruvchilar jadvali (`DZ, FLD, DX, DY`),
  `-AB`, `C=0`, `*MM`, `/"def.tlg"`, `T=-1`, `F=1` (frezada), `XGIN Q=0 G=2`, `N=P/L` qoidasi, F raqamlari (2/3/4/5), 2 xonali yaxlitlash.
  MebeliX sozlamasiga chiqariladigan: maydon (`AB`), asbob jadvali nomi (`def`), `T` qiymati, `XGIN` parametrlari.
* **Ma'lumot:** fayl nomi (op kodi), DX/DY/DZ, R (op soni), izoh (kromka belgisi/qalinligi + nom), har buyruq koordinatalari,
  chuqurlik, diametr, korreksiya, yoy yo'nalishi; 0x074/0x080 o'lcham maydonlari va H blokidagi L, M, float'lar, R tokeni.

## 5. Minimal anonim misol

Matn ko'rinishi (600×400×16, elb kromka A 1 mm; chap qirra teshigi, o'tuvchi teshik, paz):
```
H DX=600 DY=400 DZ=16 -AB C=0 R=1 *MM /"def.tlg" ;^:(A) 1mm  01_001 polka
XBO X=8 Y=70 Z=34 D=4.5 N=P F=3
XBO X=34 Y=70 Z=19 D=8 N=L F=1
XG0 X=600 Y=200 Z=8 T=-1 F=1 C=0
G1 X=0 Y=200
;END
```
Ikkilik fayl (613 bayt; `xl_write.build()` bilan yasalgan, `xl_parse` qayta o'qiydi):
```
00000000: 424d 4200 0000 0000 0000 3e00 0000 2800  BMB.......>...(.     BMP 1x1
00000010: 0000 0100 0000 0100 0000 0100 0100 0000  ................
00000020: 0000 0400 0000 ce0e 0000 c40e 0000 0000  ................
00000030: 0000 0000 0000 0000 0000 ffff ff00 0000  ................
00000040: 0000 5869 6c6f 6733 2d37 2e30 2000 0500  ..Xilog3-7.0 ...     versiya
00000050: 0000 0200 0000 0100 0000 0000 0400 0000  ................
00000060: 0000 0000 4200 0000 4200 0000 4600 0000  ....B...B...F...
00000070: 8800 0000 db01 0000 0400 0000 0000 0000  ................     0x74: 0x1DB = 613-0x8A
00000080: 6502 0000 0000 0000 0000 0010 2000 0000  e........... ...     0x80: 0x265 = 613
00000090..00000108: o'zgaruvchilar jadvali (DZ, FLD, DX, DY) — doimiy
00000100: 0244 5956 6100 6900 0001 0301 00b4 0068  .DYVa.i........h     0x109: 01 03 01 00, L=0xB4, M=0x68
00000110: 0000 0000 0000 0000 0000 0000 007f ff51  ...............Q
00000120: 0000 1644 5100 00c8 4351 0000 8041 6941  ...DQ...CQ...AiA     600.0f, 400.0f, 16.0f
00000130: 4269 0000 6c00 0000 0069 0100 6902 0061  Bi..l....i..i..a     R=1
00000140: 0364 6566 6900 0069 0100 6900 0069 0000  .defi..i..i..i..
00000150: 6900 0051 0000 0000 3b17 5e3a 2841 2920  i..Q....;.^:(A)      izoh (23 bayt)
00000160: 316d 6d20 2030 315f 3030 3120 706f 6c6b  1mm  01_001 polk
00000170: 6153 4900 4820 4458 3d36 3030 2044 593d  aSI.H DX=600 DY=     'S' + 0x49 + H matni
...
000001b0: 2030 315f 3030 3120 706f 6c6b 6100 0237   01_001 polka..7
000001c0: 102a 0008 0053 1f00 5842 4f20 583d 3820  .*...S..XBO X=8      02 37 10 | RL=0x2A | 08 00 | 53 | TL=0x1F
...
00000250: 3030 0002 3710 0f00 0800 5304 003b 454e  00..7.....S..;EN
00000260: 4400 0237 10                             D..7.                 ;END + yakuniy 02 37 10
```

## 6. MebeliX uchun eksport algoritmi (qisqa)

1. `xnc.evaluate(program, dx, dy, dz, program_vars(x))` — ifodalar, Var/Par, Origin, sikllar, fillet hisoblanadi.
2. `face_side=False` → X → dx − x (yoy markazi ham), `DrillLeft↔DrillRight`, yoy yo'nalishi va C 1↔2 teskari.
   `rotation/mirror_x/mirror_y/origin` — namunalarda hammasi 0/yo'q/LT; boshqa qiymatlarda geometrik o'zgartirish
   eksportdan oldin qo'llanishi kerak (tekshirilmagan).
3. Har amal → §3.3–3.4 jadvali bo'yicha qator; sonlar `round(v,2)` + oxirgi nollarsiz.
4. `H` qatori va izoh → §3.2; fayl → §2 (doimiy prefiks + H bloki + yozuvlar + `02 37 10` + o'lcham maydonlari).
5. Nom: `<op kodi>.pgm`, takror kod `(n)`; buyurtma bo'yicha zip.

## 7. Ochiq savollar (foydalanuvchiga)

* **Q1.** Freza va arra uchun `T=-1` chiqadi, paz eni (4/6/10.5 mm) va freza diametri yozilmaydi. Stanokda (Xilog `def.tlg`)
  asbob qanday tanlanadi? Keng pazlar (6, 10.5 mm, arra 4 mm) operator tomonidan qo'lda bir necha o'tishga bo'linadimi?
* **Q2.** `XGIN Q=0 G=2` (kirish turi) faqat `in=0` uchun ko'rildi; boshqa kirish/chiqish kodlari (`in`=1/2/3, `out`) va
  `XGOUT` kerakmi? Namuna (masalan tangensial kirishli kontur) kerak.
* **Q3.** `N=L` (o'tuvchi parma) qoidasi: «DP ≥ qalinlik» mi yoki «asbob nomi BoreTh*» mi? Masalan 16 mm detalda 17 mm chuqurlikdagi
  Bore5 teshigi qaysi parma bilan teshilishi kerak?
* **Q4.** Orqa tomonda qirra teshigi / frezalash bo'lsa (namunada yo'q) F=2↔3 almashinuvi va G2↔G3 / C 1↔2 teskari bo'lishi to'g'rimi?
  Bitta shunday namuna fayli tasdiqlash uchun kerak.
* **Q5.** Detal nomida kirill yoki o'zbek maxsus harflari bo'lsa (namunalarda yo'q) qaysi kodlash (cp1251 / cp1252) ishlatiladi?
  Izoh uzunligi 255 baytdan oshmasligi kerak (u8 maydon).
* **Q6.** Sarlavhadagi doimiy maydonlar (`05/02/01`, `0x46`, o'zgaruvchi `FLD`, BMP eskiz) — boshqa SCM stanok/Xilog
  versiyasida o'zgaradimi? Generatsiya hozir ularni namunadan aynan ko'chiradi; stanokda yasalgan faylni ochib sinash kerak.
* **Q7.** `R=` (detal soni) stanokda takrorlash sifatida ishlatiladimi yoki faqat ma'lumotmi?
