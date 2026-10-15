# Biesse Works v3.x — `.bpp` postprotsessor formati (namunalardan tiklangan)

> Manba: korxonaning o'z 15 ta buyurtmasi (3166…3183) uchun chiqarilgan `.bpp` fayllari (1009 fayl) va shu
> buyurtmalarning `.project` fayllaridagi XNC dasturlari (1014 dastur). Mijoz ismlari — «mijoz».
> Dastur binarlari o'qilmagan; faqat chiqish fayllari va loyiha XML'i solishtirilgan.
> Avtomatik solishtiruvchi skript: har bir XNC buyrug'i quyidagi qoidalar bilan o'girilib, `.bpp` dagi makros bilan
> maydonma-maydon tekshirildi (natijalar §3.6).

**Tushunish darajasi: yuqori (≈ 95 %).** Teshik (yuza va 4 qirra), paz (arra), kontur frezalash (chiziq + markazli yoy),
orqa tomon (mirror), kromka belgilari va «FACE MARK» to'liq tasdiqlangan. Noma'lum qolganlar — namunada uchramagan
holatlar (paz `c≠0`, freza `in/out`, massiv `ac>1`, burish/mirror, orqa tomonda qirra teshigi) va doimiy maydonlarning
stanokdagi ma'nosi (§6).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.bpp` (Biesse Works «BPP» matn formati, `TYPE=BPP`, `VER=130`) |
| Bitta fayl | **bitta XNC operatsiyasi = bitta fayl** (detalning bir tomoni). Orqa tomon — alohida fayl (`…_2`) |
| Nomi | `<XNC operatsiya kodi>.bpp`; kod loyihada: `<mahsulot kodi>_<detal kodi>[ _2 ]`, masalan `316601_01_001.bpp` |
| Takror kod | bir xil kodli bir nechta XNC operatsiya → `kod.bpp`, `kod (1).bpp`, `kod (2).bpp` … (loyiha XML tartibida; 1014 dasturda tasdiqlandi) |
| Kodlash | ASCII (namunada 7-bitdan tashqari bayt yo'q; kirill nom uchrashi — ochiq savol §6) |
| Qator oxiri | CRLF (`\r\n`) |
| O'nlik ajratgich | nuqta `.`; ming ajratgich yo'q |
| Raqam formati | eng qisqa ko'rinish: oxirgi nollar olib tashlanadi (`34.0` → `34`, `16.00` → `16`, `11.70` → `11.7`); namunada ≤ 4 kasr (`298.2989`) |
| Fayl oxiri | `[TOOLING]\r\n\r\n` |

**Kod tuzilishi.** `316601_01_001`: `3166` — buyurtma, `01` — mahsulot (loyihadagi `good code="316601"`),
`01_001` — detal kodi (`part.code`: guruh/shkaf `01`, detal `001`). Orqa tomon (`side=false` yoki eski loyihada `side="2"`)
dasturining kodi loyihaning o'zida `_2` bilan tugaydi (`316601_13_005_2`) — postprotsessor qo'shmaydi.
Arxiv nomi: `<buyurtma>_<mijoz>.zip`, ichida papka yo'q.

### Fayl skeleti (bo'limlar tartibi doim bir xil)

```
[HEADER]
TYPE=BPP
VER=130
<bo'sh>
[DESCRIPTION]
|<detal nomi>            ← XNC operatsiyaning typeName (masalan «01_001 bok»)
|
<bo'sh>
[VARIABLES]
PAN=LPX|<dx>||0|         ← detal uzunligi (XNC dx)
PAN=LPY|<dy>||0|         ← detal eni (XNC dy)
PAN=LPZ|<dz>||0|         ← qalinlik (XNC dz)
PAN=ORLST|"1"||0|
PAN=SIMMETRY|1||0|
PAN=TLCHK|0||0|
PAN=TOOLING|""||0|
PAN=CUSTSTR|""||0|
PAN=FCN|1.000000||0|
PAN=XCUT|0||0|
PAN=YCUT|0||0|
PAN=JIGTH|0||0|
PAN=CKOP|0||0|
PAN=UNIQUE|0||0|
PAN=MATERIAL|"ashwhite"||0|
PAN=PUTLST|""||0|
PAN=OPPWKRS|0||0|
PAN=UNICLAMP|0||0|
PAN=CHKCOLL|0||0|
PAN=WTPIANI|0||0|
PAN=COLLTOOL|0||0|
PAN=CALCEDTH|0||0|
PAN=ENABLELABEL|0||0|
PAN=RUNPAV|1||0|
<bo'sh>
[PROGRAM]
<ishlov makroslari — XNC tartibida>
<GEO/GEOTEXT kromka belgilari, FACE MARK>
<bo'sh>
[VBSCRIPT]
<bo'sh>
[MACRODATA]
<bo'sh>
[TDCODES]
<bo'sh>
[PCF]
<bo'sh>
[TOOLING]
<bo'sh>
```

`[VARIABLES]` da faqat `LPX/LPY/LPZ` o'zgaradi; qolgan 21 qator 1009 faylda bir xil (stanok/sozlama konstantalari).
`[VBSCRIPT]`, `[MACRODATA]`, `[TDCODES]`, `[PCF]`, `[TOOLING]` — doim bo'sh. Asbob nomi faylga yozilmaydi (faqat diametr).

---

## 2. Sintaksis

### 2.1. Makros qatori

```
@ NOM, "", "<teg>", <id>, "", 0 : <p0>, <p1>, …
```

* `NOM` — `BG` (teshik), `CUT_G` (arra pazi), `ROUT` (freza konturi), `START_POINT`, `LINE_EP`, `ARC_EPCE`, `ENDPATH`
  (kontur elementlari), `GEO` (grafik chiziq), `GEOTEXT` (grafik matn).
* `<teg>` — faqat `GEO`/`GEOTEXT` da: `ET`, `EB`, `EL`, `ER` (kromka), `FACE MARK`. Ishlov makroslarida `""`.
* `<id>` — ishlov makroslarida **`10 × n + tur kodi`**: `n` — fayldagi ishlov makrosining tartib raqami (1 dan; kontur
  elementlari va `ENDPATH` ham sanaladi), tur kodi: `BG` yuza = 1, `BG` chap/o'ng qirra = 2, `BG` yuqori/past qirra = 3,
  `CUT_G` = 4, `ROUT` = 5, `START_POINT` = 6, `LINE_EP` = 7, `ARC_EPCE` = 8, `ENDPATH` = 9. Masalan
  `ROUT 65 → START_POINT 76 → LINE_EP 87 → ARC_EPCE 98 → LINE_EP 107 → ENDPATH 119`. `GEO*` va ularning chiziqlari — `0`.
  (8958/8958 mos keldi.)
* Parametrlar — vergul bilan, matnlar qo'shtirnoqda; parametrlarda ifoda bo'lishi mumkin (`LPX`, `LPY+10`, `LPX/2`) —
  faqat `GEO*` da ishlatilgan.
* `ROUT` ichidagi kontur elementlari (`START_POINT … ENDPATH`) **2 bo'sh joy** bilan suriladi; `GEO` ichidagilar surilmaydi.
* **`"Pnnnnn"` identifikatori** — har `BG`, `CUT_G`, `ROUT`, `GEO`, `GEOTEXT` da bitta. Buyurtma (eksport) bo'yicha
  **uzluksiz hisoblagich**: `P00001` dan boshlanadi, avval barcha old tomon dasturlari loyiha XML tartibida, keyin barcha
  orqa tomon (`_2`) dasturlari; fayllar orasida davom etadi (15/15 buyurtmada tasdiqlandi). Fayl ichida noyob bo'lishi
  yetarlimi — ochiq savol.

### 2.2. Koordinatalar tizimi

* **Raqamlar XNC bilan aynan bir xil** (old tomon): `X = x`, `Y = y`; burish, siljitish yo'q. Birlik — mm.
* XNC (`.project`) konventsiyasi: boshlanish — detalning **chap-yuqori** burchagi, X o'ngga, **Y pastga**. Isbotlar:
  * `bt` (DrillTop) teshiklari `y=0` qirrada, `bb` (DrillBottom) — `y=dy` qirrada: `316601_13_008` da kontur `(0,582)`
    burchagini kesadi va `bt x=69` teshigi `y=582` da bo'lsa havoga tushardi → `bt` `y=0` da.
  * Kromka chizig'i `GEO "EB"` (part `elb`) doim `Y = LPY+10` da, `GEO "ET"` (`elt`) — `Y = -10` da,
    `EL` — `X = -10`, `ER` — `X = LPX+10` (849/849 old tomon fayli loyihadagi `elt/elb/ell/elr` bilan mos).
  * Freza korreksiyasi va yoy yo'nalishi shu (Y pastga) ko'rinishda mantiqli: `c=1` (o'ng) / `c=2` (chap) har ikkala
    namunada asbobni detal tashqarisida qoldiradi.
* Biesse tomonidagi talqin (tavsiya, stanokda tekshirish kerak): panel boshi — orqa-chap burchak (CRN 1), Y operatorga
  qarab o'sadi; shunda XNC «yuqori» qirra (`y=0`) = Biesse 4-tomon (orqa), «past» qirra (`y=dy`) = 2-tomon (old).
* Z: `BG` va `CUT_G` da Z maydoni doim `0`, chuqurlik musbat son (`DP`), yuzadan pastga.

### 2.3. `BG` — teshik (50 parametr)

```
@ BG, "", "", <id>, "", 0 : <SIDE>, "<CRN>", <X>, <Y>, 0, <DP>, <DIA>, 0, -1, 32, 32, 50, 0, 45, 0, "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, "<Pid>", 0, "", "", <THR>, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, "", "", "BG"
```

| # | Ma'no | Qiymat |
|---|---|---|
| 0 | SIDE — ishlov tomoni | 0 yuza, 1 chap qirra (`x=0`), 2 past qirra (`y=dy`), 3 o'ng qirra (`x=dx`), 4 yuqori qirra (`y=0`) |
| 1 | CRN — tayanch burchak | SIDE 0, 1, 2 → `"1"`; SIDE 3, 4 → `"4"` |
| 2 | X | yuza: `x`; chap/o'ng qirra: `y`; yuqori/past qirra: `x` (qirra bo'ylab koordinata, **o'zgartirilmasdan**) |
| 3 | Y | yuza: `y`; qirra: teshik markazining balandligi `z` (`m=true` → `dz/2`, `m=false` → `z`) |
| 4 | Z | doim 0 |
| 5 | DP — chuqurlik | XNC `dp` hisoblangan qiymati; o'tuvchi teshikda `throughBoreDepth = dz+3` (16 → 19, 18 → 21) |
| 6 | DIA — diametr | XNC `tool d` (`Bore4.5` → 4.5, `BoreTh8` → 8, `Bore35` → 35 …) |
| 36 | THR — o'tuvchi belgisi | `1` agar `dp ≥ dz` (namunada faqat `throughBoreDepth` o'zgaruvchisi), aks holda `0` |
| 32 | Pid | `"Pnnnnn"` |
| boshqalar | konstanta | `0, -1, 32, 32, 50, 0, 45, 0, "", 1, …` (8737 qatorda o'zgarmas; ma'nosi — ochiq savol) |

Massiv (`ac>1`) namunada yo'q — tavsiya: har teshik alohida `BG`.

### 2.4. `CUT_G` — arra pazi (60 parametr)

```
@ CUT_G, "", "", <id>, "", 0 : 0, "1", <X1>, <Y1>, 0, <DP>, 2, 0, 0, <X2>, <Y2>, 0, 0, "", 1, <SAW>, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, <W>, 0, 0, 0, 1, "<Pid>", "", 201, 2, 0, 0, 0, "", 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, "", "", "CUT_G", 0
```

| # | Ma'no | XNC `gr` |
|---|---|---|
| 0, 1 | yuza, CRN `"1"` | — |
| 2, 3 | boshlanish X1, Y1 | `x1, y1` (yo'nalish saqlanadi: `x1=1784 → x2=0` aynan shunday) |
| 5 | chuqurlik | `dp` (`throughCutDepth = dz+3` → 19) |
| 6 | `2` — konstanta (ehtimol korreksiya/«markaz» rejimi) | `c=0` (namunada faqat 0) |
| 9, 10 | oxiri X2, Y2 | `x2, y2` |
| 15 | `4` — arra qalinligi? | `tool Cut4 d=4` (namunada yagona arra — konstanta bilan ajratib bo'lmaydi) |
| 33 | paz eni | `t` (4, 6, 10.5) — bir necha o'tishni stanok o'zi hisoblaydi |
| 38 | Pid | |

### 2.5. `ROUT` + kontur — frezalash

```
@ ROUT, "", "", <id>, "", 0 : "<Pid>", 0, "1", 0, <DP>, "", 1, <DIA>, -1, 0, 0, 0, 0, 50, 0, 45, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0,"", 103, 1, <CRC>, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, 0, 0, 0, 0, "", 5, 0, 20, 80, 60, 0, "", "", "ROUT", 0, 0, 0, 0, 0, 0, 0, 0, 0
  @ START_POINT, "", "", <id>, "", 0 : <X>, <Y>, 0
  @ LINE_EP, "", "", <id>, "", 0 : <X>, <Y>, 0, 0, 0, 0, 0, 0, 0
  @ ARC_EPCE, "", "", <id>, "", 0 : <X>, <Y>, <CX>, <CY>, <DIR>, 0, 0, 0, 0, 0, 0
  @ ENDPATH, "", "", <id>, "", 0 :
```

(diqqat: `0,"", 103` — `""` oldidan bo'sh joy yo'q; namunada shunday.)

| Maydon | XNC | Qoida |
|---|---|---|
| ROUT[4] DP | `ms dp` (`contMillDepth = dz` → 16) | namunada doim `dz` (o'tuvchi) |
| ROUT[7] DIA | `tool Mill8 d=8` | asbob diametri; asbob nomi (`ROUT[5]`) bo'sh |
| ROUT[50] CRC | `ms c` | **`c=1` (o'ng) → 2**, **`c=2` (chap) → 1**; `c=0` → 0 (taxmin, namunada yo'q) |
| START_POINT | `ms x, y` | aynan |
| LINE_EP | `ml x, y` | aynan |
| ARC_EPCE | `mac x, y, cx, cy, dir` | aynan; **`dir=true` → 1, `dir=false` → 2** |
| ENDPATH | kontur oxiri | keyingi `ms`/teshik/paz oldidan yoki dastur oxirida |

`ms in=0 out=1` — namunada yagona qiymat (kirish/chiqish maydonlari konstanta: `…, 5, 0, 20, 80, 60, …`) — ochiq savol.
Kontur detal tashqarisidan boshlanadi (`y=-10` yoki `x=-10`) — bu XNC'ning o'zida shunday (kirish masofasi XNC'da).

### 2.6. Kromka belgilari va «FACE MARK» (faqat grafika, stanok ishlovi emas)

Ishlov makroslaridan keyin, detalning har kromkalangan tomoni uchun `GEO` (chiziq) + `GEOTEXT` (yozuv), tartib:
`ET, EB, EL, ER` (orqa tomonda `EL↔ER` almashadi, tartib manba tomon bo'yicha qoladi).

```
@ GEO, "", "EB", 0, "", 0 : "<Pid>", 0, "1", 0, 1, 0, 0, 0, 0.1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, "GEO", 0
@ START_POINT, "", "", 0, "", 0 : 0, LPY+10, 0
@ LINE_EP, "", "", 0, "", 0 : LPX, LPY+10, 0, 0, 0, 0, 0, 0, 0
@ ENDPATH, "", "", 0, "", 0 :
@ GEOTEXT, "", "EB", 0, "", 0 : "<Pid>", 0, "2", "(A) 1mm", LPX/2, -37, 0, 0, 0, 0, 0, 0, 0, 0, "Arial", 32, 0, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, "GEOTEXT"
```

| Teg | Loyiha | Chiziq (boshi → oxiri) | Matn (X, Y, burchak) |
|---|---|---|---|
| ET | `elt` | `0,-10 → LPX,-10` | `LPX/2, LPY+25, 0` |
| EB | `elb` | `0,LPY+10 → LPX,LPY+10` | `LPX/2, -37, 0` |
| EL | `ell` | `-10,0 → -10,LPY` | `-35, LPY/2, 90` |
| ER | `elr` | `LPX+10,0 → LPX+10,LPY` | `LPX+25, LPY/2, 270` |

* Matn: `"(<elSymbol>) <t>mm"` — kromka operatsiyasining (`<operation typeId="EL" elSymbol="A" t="1">`) belgisi va
  qalinligi; `(A)` = `@operation#1`, `(B)` = `#2` … (15 buyurtmada mos).
* **Diqqat:** `ET`/`EB` matnining Y koordinatasi chiziqqa teskari tomonda (EB chizig'i `LPY+10`, matni `-37`). Bu manba
  postprotsessorning xususiyati (yoki xatosi) — ishlovga ta'sir qilmaydi; biz ham aynan takrorlashimiz yoki tuzatishimiz
  mumkin (savol §6).
* **FACE MARK** — orqa tomon dasturi (`_2`) bor detallarda: old fayl ham, orqa fayl ham oxirida 20×20 kvadrat oladi
  (37 + 37 fayl; boshqalarida yo'q):
  ```
  @ GEO, "", "FACE MARK", 0, "", 0 : "<Pid>", 0, "<1 old | 4 orqa>", 0, 1, 0, 0, 0, 0.1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, "GEO", 0
  @ START_POINT, "", "", 0, "", 0 : -20, -20, 0
  @ LINE_EP, "", "", 0, "", 0 : 0, -20, 0, 0, 0, 0, 0, 0, 0
  @ LINE_EP, "", "", 0, "", 0 : 0, 0, 0, 0, 0, 0, 0, 0, 0
  @ LINE_EP, "", "", 0, "", 0 : -20, 0, 0, 0, 0, 0, 0, 0, 0
  @ LINE_EP, "", "", 0, "", 0 : -20, -20, 0, 0, 0, 0, 0, 0, 0
  @ ENDPATH, "", "", 0, "", 0 :
  ```

### 2.7. Orqa tomon (`side=false` / eski loyihada `side="2"`)

* Yuza teshigi va paz: **`X = dx − x`**, `Y = y` o'zgarmaydi (X bo'yicha ko'zgu; 37/37 orqa fayl mos).
* Buyruqlar tartibi XNC'dagidek qoladi.
* Kromka belgilari: `EL ↔ ER` almashadi, `ET`/`EB` joyida.
* `FACE MARK` 3-parametri `"4"`.
* Orqa tomonda qirra teshigi va frezalash namunada yo'q (ochiq savol).

---

## 3. MebeliX XNC → Biesse `.bpp` mosligi

### 3.1. Jadval

| MebeliX `cmd` (teg) | Biesse | Parametrlar |
|---|---|---|
| Tool (`tool`) | — (faylga yozilmaydi) | `D` → BG[6] / ROUT[7] / CUT_G[15] |
| Var / Par / Set (`var`) | — | ifodalar oldindan hisoblanadi (`services/expr.py`), faylga faqat son |
| DrillFront (`bf`) | `BG` SIDE 0, CRN "1" | X=x (orqada dx−x), Y=y, DP=dp, DIA=D, THR = dp≥dz |
| DrillLeft (`bl`) | `BG` SIDE 1, CRN "1" | X=y, Y=z (M → dz/2), DP, DIA |
| DrillBottom (`bb`, `y=dy`) | `BG` SIDE 2, CRN "1" | X=x, Y=z, DP, DIA |
| DrillRight (`br`) | `BG` SIDE 3, CRN "4" | X=y, Y=z, DP, DIA |
| DrillTop (`bt`, `y=0`) | `BG` SIDE 4, CRN "4" | X=x, Y=z, DP, DIA |
| Groove (`gr`) | `CUT_G` | X1,Y1,X2,Y2 (orqada X ko'zgu), DP, en=T(W), arra=D |
| MillStart (`ms`) | `ROUT` + `START_POINT` | DP, DIA, CRC: C 1→2, 2→1, (0→0) |
| MillLine (`ml`) | `LINE_EP` | X, Y |
| MillArcCenter (`mac`) | `ARC_EPCE` | X, Y, CX, CY, DIR: true→1, false→2 |
| MillArc / MillArc3P / MillFillet / MillRect / MillEllipse | `ARC_EPCE` / `LINE_EP` ga yoyib (namunada yo'q) | `xnc.mill_arc()` markazni beradi; `evaluate()` fillet'ni allaqachon `MillArcCenter` ga aylantiradi; ellips — siniq chiziq |
| Origin (`xy`) | — | `evaluate()` koordinatalarga qo'shadi (namunada yo'q) |
| If/While/Sub… | — | `evaluate()` yoyib beradi |

Generator `services/xnc.py::evaluate()` natijasidan (hisoblangan amallar) ishlashi kerak; `inside=False` teshiklar
chiqarilmasin (taklif — manba fayllarda bunday holat yo'q).

### 3.2. Tekshiruv 1 — `316601_01_001` (1250×500×16; past qirra + o'tuvchi teshiklar)

| XNC | `.bpp` |
|---|---|
| `bb x=785.99 dp=32.0 z=8 m=true name=Bore4.5` | `@ BG, "", "", 13, … : 2, "1", 785.99, 8, 0, 32, 4.5, … THR 0` |
| `bb x=1180 dp=34.0` | `… 43 … : 2, "1", 1180, 8, 0, 34, 4.5 …` |
| `var throughBoreDepth = dz+3.00`; `bf x=8 y=70 dp=throughBoreDepth name=BoreTh8` | `… 51 … : 0, "1", 8, 70, 0, 19, 8, … "P00012", 0, "", "", 1, …` (THR=1) |
| `bf x=1242 y=430` | `… 81 … : 0, "1", 1242, 430, 0, 19, 8 …` |
| part `elb` → EL op #1 (`elSymbol=A`, `t=1`) | `GEO "EB"` chiziq `0,LPY+10 → LPX,LPY+10`; `GEOTEXT "(A) 1mm"` |

`LPX=1250, LPY=500, LPZ=16`, `|01_001 pb-pol`. Id'lar: 4 ta `bb` → 13, 23, 33, 43 (tur 3), 4 ta `bf` → 51…81 (tur 1).

### 3.3. Tekshiruv 2 — `316601_13_008` (368×582×16; yuqori/o'ng qirra + yoyli kontur, `c=1`)

| XNC | `.bpp` |
|---|---|
| `bt x=69 dp=34.0 z=8` | `@ BG, "", "", 13, … : 4, "4", 69, 8, 0, 34, 4.5 …` |
| `bt x=298` | `… 23 … : 4, "4", 298, 8, …` |
| `br y=50` / `291` / `532` | `… 32/42/52 … : 3, "4", 50/291/532, 8, 0, 34, 4.5 …` |
| `ms x=0 y=-10 dp=contMillDepth(=16) c=1 name=Mill8` | `@ ROUT, "", "", 65, … : "P00940", 0, "1", 0, 16, "", 1, 8, … 103, 1, 2, 9 …` (CRC=2) |
| `ml x=0 y=284` | `  @ START_POINT … 76 … : 0, -10, 0` / `  @ LINE_EP … 87 … : 0, 284, 0, …` |
| `mac x=300 y=582 cx=298.2989 cy=283.7059 dir=false` | `  @ ARC_EPCE … 98 … : 300, 582, 298.2989, 283.7059, 2, …` |
| `ml x=378 y=582` | `  @ LINE_EP … 107 … : 378, 582, 0, …` + `  @ ENDPATH … 119` |
| part `elb`, `ell` (EL op #3, `C`) | `GEO "EB"` + `"(C) 1mm"`, `GEO "EL"` (`-10,0 → -10,LPY`) + `"(C) 1mm" -35, LPY/2, 90` |

Shu kodli 6 ta operatsiya → `316601_13_008.bpp`, `… (1).bpp` … `… (5).bpp`, tarkibi bir xil, faqat `Pid` farq qiladi.

### 3.4. Tekshiruv 3 — `318001_01_001_2` (2200×503×16, **orqa tomon**, asimmetrik)

| XNC (`side=false`) | `.bpp` (X = 2200 − x) |
|---|---|
| `bf x=2192 y=73 dp=11 Bore8` | `… 11 … : 0, "1", 8, 73, 0, 11, 8 …` |
| `bf x=1926 y=73 dp=11` | `… 21 … : 0, "1", 274, 73, 0, 11, 8 …` |
| `bf x=108 y=93 dp=11` | `… 31 … : 0, "1", 2092, 93, 0, 11, 8 …` |
| `bf x=50 y=469 dp=11` | `… 131 … : 0, "1", 2150, 469, 0, 11, 8 …` |
| `gr x1=2200 y1=0 x2=100 y2=0 dp=8 t=6 c=0 Cut4` | `@ CUT_G, "", "", 144, … : 0, "1", 0, 0, 0, 8, 2, 0, 0, 2100, 0, …, 4, …, 6, …` |
| part `elb`, `ell` | `GEO "EB"` + `GEO "ER"` (chap → o'ng), `FACE MARK` 3-parametri `"4"` |

Old tomon `318001_01_001.bpp` (`bf x=2192 y=40` → `2192, 40`) — ko'zgusiz, oxirida `FACE MARK "1"`.

### 3.5. Tekshiruv 4 — `317001_01_002` (1165×626×16; 4 qirra + kontur `c=2`, `dir=true`)

`bb x=70 dp=34 Bore8` → `2, "1", 70, 8, 0, 34, 8`; `bl y=70` → `1, "1", 70, 8`; `br y=220` → `3, "4", 220, 8`;
`bt x=901` → `4, "4", 901, 8`; `ms x=-10 y=0 c=2` → `ROUT … 1, 1, 9 …` (CRC=1), `START_POINT -10, 0`;
`ml 1015,0` → `LINE_EP 1015, 0`; `mac 1165,150 c 1015,150 dir=true` → `ARC_EPCE 1165, 150, 1015, 150, 1`;
`ml 1165,635.9996` → `LINE_EP 1165, 635.9996`. Qalinligi 18 mm detallarda (`316601_14_017…021`): `br … z=9 m=true` →
`Y=9`, `bl … z=8 m=false` → `Y=8` (dz/2 emas, aniq `z`) — 24 holatda tasdiqlandi.

### 3.6. Avtomatik solishtirish natijasi (barcha 15 buyurtma)

| Ko'rsatkich | Natija |
|---|---|
| XNC dasturlari / zipdagi fayllar | 1014 / 1009 |
| Fayl nomi (kod + « (n)») | 1007 mos; 7 ta dastur faylsiz — hammasi 3173 da |
| To'liq mos fayl (sarlavha, tavsif, har makros) | **958/958** (3173 dan tashqari) ; 3173 da 25/49 |
| Ishlov makroslari | 8958/9013 mos (BG 8579, CUT_G 60, ROUT 65, START_POINT 65, LINE_EP 128, ARC_EPCE 51, ENDPATH 65); 55 nomos — hammasi 3173 |
| Orqa tomon fayllari | 37/37 |
| `id = 10n + tur` | 100 % (3173 dagi 8 ta nomoslik — tarkib boshqa bo'lgani uchun) |
| Kromka GEO ↔ loyiha `el*` | 881/881 (3173, 3183 dan tashqari; orqa tomonda `EL↔ER` almashuvi bilan) |
| `Pid` ketma-ketligi | 15/15 buyurtmada uzluksiz, «old XML tartibi → orqa XML tartibi» |

Nomosliklar sinflari:
1. **3173** — loyiha eksportdan keyin tahrirlangan (zip 30.09, `.project` 01.10): o'lchamlar (`LPX 2458` vs XNC `1868`),
   nomlar, teshiklar boshqa; 7 ta yangi operatsiya fayli yo'q, 2 ta eski « (1)» fayl ortiqcha. Format qoidasi buzilmagan.
2. **3183** — eski loyiha (`side="1"/"2"`, `dx="780.00"`): ishlov 100 % mos, lekin detal ↔ XNC bog'lanishida kromka
   atributlari yo'q, shuning uchun 72 ta faylda GEO kromka belgilarini loyihadan tekshirib bo'lmadi.

---

## 4. Doimiy va ma'lumotga bog'liq maydonlar

**Ma'lumotdan:** fayl nomi, `[DESCRIPTION]` (detal nomi), `LPX/LPY/LPZ`; BG: SIDE, CRN (SIDE dan), X, Y, DP, DIA, THR;
CUT_G: X1, Y1, X2, Y2, DP, en, (arra qalinligi?); ROUT: DP, DIA, CRC; kontur nuqtalari, yoy markazi va DIR; makros id'lari;
`Pid` hisoblagich; kromka belgilari (qaysi tomon, `elSymbol`, `t`), FACE MARK (orqa dasturi bormi, old/orqa).

**Konstanta (stanok/sozlama — o'zgartirish faqat texnolog bilan):** `TYPE=BPP`, `VER=130`; 21 ta `PAN=` qatori
(`ORLST "1"`, `SIMMETRY 1`, `FCN 1.000000`, `MATERIAL "ashwhite"`, `RUNPAV 1` …); BG dagi `0, -1, 32, 32, 50, 0, 45, 0, "", 1,
… , 1, … , -1` bloki; CUT_G dagi `2`, `1`, `-1`, `201, 2`, `1`; ROUT dagi `"1"`, `1`, `-1`, `50`, `45`, `103, 1`, `9`,
`5, 0, 20, 80, 60`; GEO `0.1` va bayroqlar; GEOTEXT `"Arial", 32`; matn siljishlari (`-10`, `+10`, `-37`, `+25`, `-35`).
Generatorda bular sozlanadigan shablon sifatida saqlansin (stanok profili).

---

## 5. Minimal namunaviy dastur (anonim)

Detal «01_001 bok» 600×400×16, old tomon: yuza teshigi Ø15 (dp 12.5), o'tuvchi teshik Ø8, chap qirra teshigi Ø8,
arra pazi, chap qirrada A kromka (1 mm). Fayl nomi: `999901_01_001.bpp` (CRLF).

```
[HEADER]
TYPE=BPP
VER=130

[DESCRIPTION]
|01_001 bok
|

[VARIABLES]
PAN=LPX|600||0|
PAN=LPY|400||0|
PAN=LPZ|16||0|
PAN=ORLST|"1"||0|
PAN=SIMMETRY|1||0|
PAN=TLCHK|0||0|
PAN=TOOLING|""||0|
PAN=CUSTSTR|""||0|
PAN=FCN|1.000000||0|
PAN=XCUT|0||0|
PAN=YCUT|0||0|
PAN=JIGTH|0||0|
PAN=CKOP|0||0|
PAN=UNIQUE|0||0|
PAN=MATERIAL|"ashwhite"||0|
PAN=PUTLST|""||0|
PAN=OPPWKRS|0||0|
PAN=UNICLAMP|0||0|
PAN=CHKCOLL|0||0|
PAN=WTPIANI|0||0|
PAN=COLLTOOL|0||0|
PAN=CALCEDTH|0||0|
PAN=ENABLELABEL|0||0|
PAN=RUNPAV|1||0|

[PROGRAM]
@ BG, "", "", 11, "", 0 : 0, "1", 34, 70, 0, 12.5, 15, 0, -1, 32, 32, 50, 0, 45, 0, "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, "P00001", 0, "", "", 0, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, "", "", "BG"
@ BG, "", "", 21, "", 0 : 0, "1", 8, 200, 0, 19, 8, 0, -1, 32, 32, 50, 0, 45, 0, "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, "P00002", 0, "", "", 1, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, "", "", "BG"
@ BG, "", "", 32, "", 0 : 1, "1", 70, 8, 0, 34, 8, 0, -1, 32, 32, 50, 0, 45, 0, "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, -1, "P00003", 0, "", "", 0, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, "", "", "BG"
@ CUT_G, "", "", 44, "", 0 : 0, "1", 600, 380, 0, 8, 2, 0, 0, 0, 380, 0, 0, "", 1, 4, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 4, 0, 0, 0, 1, "P00004", "", 201, 2, 0, 0, 0, "", 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, "", "", "CUT_G", 0
@ GEO, "", "EL", 0, "", 0 : "P00005", 0, "1", 0, 1, 0, 0, 0, 0.1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, "GEO", 0
@ START_POINT, "", "", 0, "", 0 : -10, 0, 0
@ LINE_EP, "", "", 0, "", 0 : -10, LPY, 0, 0, 0, 0, 0, 0, 0
@ ENDPATH, "", "", 0, "", 0 :
@ GEOTEXT, "", "EL", 0, "", 0 : "P00006", 0, "2", "(A) 1mm", -35, LPY/2, 0, 90, 0, 0, 0, 0, 0, 0, "Arial", 32, 0, 0, 0, 0, 1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, "GEOTEXT"

[VBSCRIPT]

[MACRODATA]

[TDCODES]

[PCF]

[TOOLING]

```

Mos XNC: `bf x=34 y=70 dp=12.5 (Bore15)`, `bf x=8 y=200 dp=throughBoreDepth (BoreTh8)`, `bl y=70 dp=34 m=true (Bore8)`,
`gr x1=600 y1=380 x2=0 y2=380 dp=8 t=4 c=0 (Cut4)`. Freza bo'lsa: `@ ROUT …` (§2.5) + surilgan kontur qatorlari.

---

## 6. Ochiq savollar (foydalanuvchi / texnologga)

1. **Qirra teshiklarida CRN "4"** (o'ng va yuqori qirra): X qiymati XNC'dan o'zgarishsiz yoziladi. Stanokda 3/4-tomondagi
   asimmetrik teshik (masalan `br y=50` 582 mm detalda) haqiqatan `y=50` da tushadimi yoki `LPY−50` da? Bitta sinov
   detali bilan tekshirish kerak.
2. **Biesse panel boshi va Y yo'nalishi** stanokda qaysi burchak (orqa-chap, Y operatorga)? Raqamlar XNC bilan bir xil,
   shuning uchun detal stanokda GibLab chizmasiga nisbatan qanday yotqizilishini texnolog tasdiqlasin.
3. `ET`/`EB` kromka **matni** chiziqqa teskari tomonda (`-37` / `LPY+25`) — takrorlaymizmi yoki tuzatamizmi?
4. Konstantalar ma'nosi: BG `32, 32, 50, 45`, ROUT `103`, `5, 0, 20, 80, 60` (tezlik/kirish?), `MATERIAL "ashwhite"`,
   CUT_G `201, 2` — stanok profili sifatida saqlansinmi, qaysilari asbobga bog'liq?
5. Namunada yo'q holatlar: paz `c=1/2` (CUT_G[6] qiymati?), freza `in/out` boshqa qiymatlari, freza chuqurligi `dp<dz`,
   teshik massivi `ac>1`, orqa tomonda qirra teshigi/frezalash, `turn≠0` va `mirror`, `Origin`, Ø>35 yoki boshqa arra.
6. `Pid` («P00001…») butun buyurtma bo'yicha uzluksiz bo'lishi shartmi (stanok/optimizator uchun) yoki fayl ichida
   noyoblik yetarlimi? Bitta faylni qayta eksport qilganda raqam qanday bo'lishi kerak?
7. Detal nomida kirill/maxsus belgi bo'lsa — kodlash (CP1251? UTF-8?) va qo'shtirnoq/`|` belgilarini qochirish.
8. Kromka qalinligi `t` kasr bo'lsa (`0.4`) matn formati (`0.4mm`?).
9. Raqamlarni yaxlitlash: 4 kasrdan ko'p bo'lsa nechta xona qoldiriladi?
