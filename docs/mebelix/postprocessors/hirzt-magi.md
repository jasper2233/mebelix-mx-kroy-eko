# HIRZT MAGI — `.pd4` (CID3 / Maestro‑uslubidagi parametrik matn) postprotsessori

> Manba: korxonaning o'z namunalari — `post prtsessorlar/PRISADKA APPARAT/HIRZT MAGI/<NNNN>_<mijoz>.zip` (15 buyurtma,
> **1009 fayl**) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` XNC operatsiyalari (1014 dastur).
> Faqat chiqish fayllari va loyiha XML o'qildi. Mijoz ismlari — «mijoz».
>
> **Holat: to'liq tushunilgan (teshik, paz, orqa tomon). Frezalash bu formatga umuman chiqmaydi.**
> Prototip writer (scratchpad `gen.py::hirzt`) 3173 dan tashqari **958/958 faylni bayt-ma-bayt** qayta yasadi
> (3173 — loyiha eksportdan keyin, 2026‑10‑01 da o'zgargan; 27/51 fayl mos, qolgani loyihada boshqacha).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Fayl | **bitta XNC operatsiyasi = bitta `.pd4`**; nomi `<XNC kodi>.pd4` (`316701_01_001.pd4`) |
| Takror kod | `<kod> (1).pd4`, `<kod> (2).pd4` … (loyiha XML tartibida) |
| Orqa tomon | alohida XNC (`side="false"`), kod `…_2`: `316701_01_018_2.pd4` |
| Kodlash | ASCII (namunada boshqa bayt yo'q; kirill — ❓ Q6) |
| Qator oxiri | `CRLF`; oxirgi qator (`END BLOCK` yoki `END PARAMETRIC SECTION`) ham `CRLF` bilan |
| Sonlar | nuqta `.`, 4 kasrgacha yaxlitlab, ortiqcha nollarsiz (`70`, `464.01`, `1239.9999`); qirra teshigi nuqtasining qirraga mahkam koordinatasi `%.1f` (`X=0.0 ,`, `Y=500.0`) |
| Birlik | mm |

---

## 2. Sintaksis

### 2.1 Fayl tuzilishi (to'liq)

```
BEGIN ID CID3
 ''=<detal nomi>                         ← operation@typeName
 REL= 3.10
 AXIS= x+,y-,z-                          ← X o'ngga, Y PASTGA, Z yuqori yuzadan pastga
END ID
BEGIN MAINDATA
 LX= <L>
 LY= <W>
 LZ= <T>
END MAINDATA
BEGIN PARAMETRIC SECTION
[ 0.0 ] PROGETTO  <XNC kodi> (            ← "PROGETTO" dan keyin 2 ta probel
LPX = <L> NOP "Width"
, LPY = <W> NOP "Height"
, LPZ = <T> NOP "Thickness"
) EOS
[ 0.i ] PATH    "" "<makro>" …            ← i = 1..N, har amal uchun bitta qator (§2.3)
----------   LAVORAZIONE BASE DEL PROGETTO   ------------------------------------------------
[  1.0 ] LAYER ON START 1 "WRK" COLORE 3
[  1.1 ] LAYER  EOS
[  2.0 ] LAYER ON START 2 "DOC" COLORE 2
[  2.1 ] LAYER  EOS
[  0.0 ] PUNTO [ 0 , 0 , LPZ ]
[  0.1 ] CREA_SPACE 1096 1096 16         ← doimiy (detal o'lchamiga bog'liq emas)
[ 3j-2.0 ] CREA_LAB <tekislik>             ← har amal j uchun 3 qator (§2.4)
[ 3j-1.0 ] SEGMENTO MATITA PER [<nuqta>] INCLINAZIONE ASSE_X ANGOLO 0 MISURA 1
[ 3j.0 ] INSERISCI FORI <qo'shimcha>#j
[  999.  ] FINE_MACRO
&&& [j,1] #…                              ← har amal j uchun texnologiya qatori (§2.5)
END PARAMETRIC SECTION
BEGIN BLOCK                               ← faqat kamida bitta amal bo'lsa (4 bo'sh faylda yo'q)
NAME=WRK
SIDE=0
COLOR=LIGHT_GREEN
VISIBILITY=YES
 BEGIN CUSTOM … END CUSTOM                ← teshik (§2.6)
BEGIN PLINE … END PLINE                   ← paz (§2.7)
END BLOCK
```
Qatorlardagi bo'shliqlar aynan shunday (masalan `[ 0.10 ]`, `[  999.  ]`, `LAYER  EOS`) — 1009 faylda doimiy.

### 2.2 Koordinata tizimi va amallar tartibi

* Koordinatalar **GibLab XNC xom koordinatasi bilan bir xil** (= MebeliX `machine_program()`, origin `LT`): X = x,
  Y = y (yuqori qirradan pastga, `AXIS y-`). Qirra teshigi balandligi **yuqori yuzadan**: `QY = T − z_b`, bu yerda
  `z_b` — XNC dagi pastki yuzadan balandlik (`m="true"` → `T/2`).
* Orqa tomon (`side=false`): `x → L − x` (faqat X; Y o'zgarmaydi). Faylda boshqa belgi yo'q.
* Amallar tartibi (j raqami): **1) yuz guruhi** — `bf` va `gr` aralash, **XNC dasturidagi tartibda**; 2) `bl`
  (SINISTRA); 3) `br` (DESTRA); 4) `bb` (SOPRA); 5) `bt` (SOTTO); guruh ichida — dastur tartibi. Uchala bo'lim
  (PATH, CREA_LAB, &&&) va BLOCK shu bitta tartibda.

### 2.3 PATH qatorlari

Teshik (barcha tekisliklar uchun bitta makro):
```
[ 0.i ] PATH    "" "Drill\1_Single.pm4" (QX = <qx> "Quota X",QY = <qy> "Quota Y",DIA = <d> "Diametro",PRF = <dp> "Profondita")
```
Paz (makro — **ochuvchi qavssiz**, oxirida `)` bor — aynan shunday):
```
[ 0.i ] PATH    "" "Saw\X1_LPX.pm4" QY = <y1> "Quota Y",LPX = <|x2−x1|> "Larghezza",PRF = <dp> "Profondita",SP = <t> "Spessore lama")
```
`Saw\X1_LPX` — X bo'ylab paz makrosi; vertikal paz (x1=x2) uchun ham shu makro `LPX = 0` bilan yoziladi
(haqiqiy geometriya BLOCK dagi `LINE` da) — ❓ Q2.

| XNC | CREA_LAB | QX | QY |
|---|---|---|---|
| `bf` | `FRONTALE` | x (orqada L−x) | y |
| `bl` | `SINISTRA` | y | T − z_b |
| `br` | `DESTRA` | y | T − z_b |
| `bb` (y=W qirra) | `SOPRA` | **L − x** | T − z_b |
| `bt` (y=0 qirra) | `SOTTO` | x | T − z_b |

### 2.4 CREA_LAB bloki (har amal uchun 3 qator)

| Tekislik | `SEGMENTO MATITA PER [ … ]` | `INSERISCI FORI …#j` |
|---|---|---|
| `FRONTALE` (bf **va** gr) | `[0.0,0.0,LPZ]` | `INSERISCI FORI #j` |
| `SINISTRA` | `[0.0,0.0,0.0]` | `INSERISCI FORI SIMMETRICO ASSE_Y PIANO  #j` (2 probel) |
| `DESTRA` | `[LPX,0.0,0.0]` | `INSERISCI FORI  #j` (2 probel) |
| `SOPRA` | `[LPX,LPY,0.0]` | `INSERISCI FORI  #j` |
| `SOTTO` | `[0.0,0.0,0.0]` | `INSERISCI FORI  #j` |

Qator raqamlari `[ 1.0 ]`, `[ 2.0 ]`, `[ 3.0 ]`, `[ 4.0 ]` … ketma-ket (har amal +3).

### 2.5 `&&&` texnologiya qatorlari

Teshik:
```
&&& [j,1] #NUM_CAT=1,#ID_TOOLNAME=*,#PRIORITY=*,#TYPEDRILL=*,#DWNSPEED=*,#RIFDRILL=*,#TYPE=<1|2|3>,#AZ=270.000000,#AR=0.000000,#WORKSIDE=0,#DIAM=<d>,#ID_DEPTH=<dp>
```
`#TYPE` (parma turi): **2** — o'tuvchi (`dp ≥ T`, namunada `BoreTh7/BoreTh8`); **3** — `d ≥ 15` (`Bore15`, `Bore35` —
eksentrik/petlya); **1** — qolganlari (3, 5, 8, 10 mm va barcha qirra teshiklari). 5 795 frontal + 2 434 qirra
teshigida tekshirildi. `#WORKSIDE=0`, `#AZ=270.000000` qirra teshigida ham shunday (haqiqiy tomon BLOCK da).

Paz:
```
&&& [j,1] #NUM_CAT=1,#AR=*,#STDROT_S=*,#STDWRK_S=*,#DWNSPEED=*,#ROTSENSE=*,#ID_DIRECTION=*,#I_X_MIN=*,#I_X_MAX=*,#I_Y_MIN=*,#I_Y_MAX=*,#I_Z_MIN=*,#I_Z_MAX=*,#I_DEPTH_MIN=*,#I_DEPTH_MAX=*,#PRIORITY=*,#ID_TOOLNAME=*,#WORKSIDE=*,#ID_PARDISTANCE=*,#BLOCK_PRIO=*,#MIRXY=*,#TOOLPROFILENAME=*,#BLADE_CRU=*,#TYPE=1,#AZ=0.0,#DIAM=<t>,#ID_PARDEPTH=<dp>,#ISBLOCK=0,#SAWINSERTMODE=0
```

### 2.6 BLOCK — teshik (`BEGIN CUSTOM`)

```
 BEGIN CUSTOM
  BEGIN TECH
   CAT=1
   TYP=<1|2|3>                 ← &&& dagi #TYPE bilan bir xil
   ANG=270.0,0.0               ← frontal; qirra teshigida ANG=0.0,0.0
   DIAM=<d>
   DEPTH=<dp>,<dp>
   WORKSIDE=<0..4>
  END TECH
  POINT,X=<X>,Y=<Y>,Z=<Z>
 END CUSTOM
```
(oldidagi probellar: 1 / 2 / 3 / 2 / 1.)

| XNC | WORKSIDE | POINT |
|---|---|---|
| `bf` | 0 | `X=x,Y=y,Z=0` (orqada X = L−x) |
| `bl` | 1 | `X=0.0 ,Y=y,Z=T−z_b` |
| `bb` | 2 | `X=L−x ,Y=W(.1f),Z=T−z_b` |
| `br` | 3 | `X=L(.1f) ,Y=y,Z=T−z_b` |
| `bt` | 4 | `X=x ,Y=0.0,Z=T−z_b` |

Qirra teshigida X dan keyin **probel + vergul** (`X=598.0 ,Y=70`), frontalda probelsiz.

### 2.7 BLOCK — paz (`BEGIN PLINE`)

```
BEGIN PLINE
BEGIN TECH
    CAT=1
    TYP=1
    ANG=0.0,0.0
    DIAM=<t>
    WORKSIDE=0
    PARALDEPTH=<dp>
     ISBLOCK=0
     SAWINSERTMODE=0
END TECH
    LINE,XS=<x1>,YS=<y1>,ZS=<dp>,XE=<x2>,YE=<y2>,ZE=<dp>
END PLINE
```
Orqa tomonda XS/XE = L − x. Asbob (`Cut4`) va `c` yozilmaydi (namunada `c=0`). 60/60 paz mos.

### 2.8 Frezalash

`ms/ml/mac` (65 kontur, 44 faylda) **hech qayerda chiqmaydi** — na PATH, na BLOCK da. Faqat frezalashdan iborat
dasturlar (masalan `01_041x047x0`) BLOCK bo'limisiz, bo'sh dastur bo'lib chiqadi. ❓ Q1.

---

## 3. MebeliX XNC → HIRZT xaritasi

`machine_program(op, project)` (origin LT, Y pastga, ifodalar hisoblangan): `L = size.length`, `W = size.width`,
`T = blank.thickness`, `back = face_back`, `fx(x) = back ? L − x : x`, `z_b = middle ? T/2 : z`.

| MebeliX | HIRZT |
|---|---|
| `drill front` | PATH Drill (QX=fx(x), QY=y), FRONTALE, &&& TYPE, CUSTOM WORKSIDE 0 |
| `drill left` | SINISTRA (QX=y, QY=T−z_b), WORKSIDE 1 |
| `drill right` | DESTRA, WORKSIDE 3 |
| `drill bottom` (y=W) | SOPRA (QX=L−fx(x)), WORKSIDE 2 |
| `drill top` (y=0) | SOTTO (QX=fx(x)), WORKSIDE 4 |
| `groove` | PATH Saw + FRONTALE + &&& paz + PLINE |
| `mill_*`, `rect`, `ellipse` | **chiqmaydi** (GibLab xatti-harakati; Q1) |
| `AC>1` massiv | alohida teshiklar (namunada yo'q) |

### 3.1 Tekshirilgan misollar

**A. `316701_01_001` (2098×597×16)** — `bf x=593 y=70 dp=dz+3` → `QX = 593 …,QY = 70 …,DIA = 8 …,PRF = 19`, `#TYPE=2`,
`POINT,X=593,Y=70,Z=0`; `bf x=880.5 y=50 dp=9 Bore5` → `#TYPE=1`; `bl y=70` → `CREA_LAB SINISTRA`, `QX = 70, QY = 8`,
`POINT,X=0.0 ,Y=70,Z=8`, `WORKSIDE=1`; `br y=70` → `DESTRA`, `POINT,X=2098.0 ,Y=70,Z=8`, `WORKSIDE=3`.

**B. `316601_14_017` (68×1581×18)** — `bl y=70 z=8 m=false` → `QY = 10` (= 18−8), `POINT,X=0.0 ,Y=70,Z=10`;
`br y=50 z=9 m=true` → `QY = 9`; `bf Bore15 d=15 dp=12.5` → `#TYPE=3`.

**C. `316601_01_001` (1250×500, `bb`)** — `bb x=785.99 dp=32` → `CREA_LAB SOPRA`, `SEGMENTO … [LPX,LPY,0.0]`,
`QX = 464.01` (=1250−785.99), `POINT,X=464.01 ,Y=500.0,Z=8`, `WORKSIDE=2`.

**D. `316601_13_005` (598×600, paz + qirra)** — `gr x1=598 y1=0 x2=0 y2=0 t=6 dp=13` → birinchi amal:
`PATH "" "Saw\X1_LPX.pm4" QY = 0 …,LPX = 598 …,PRF = 13 …,SP = 6 …)`, `LINE,XS=598,YS=0,ZS=13,XE=0,YE=0,ZE=13`.

**E. `317001_01_005_2` (696×776, orqa tomon)** — `bf x=243 y=698 d=3 dp=1.5` → `QX = 453` (=696−243), `QY = 698`.

**F. `317801_01_007` (vertikal paz)** — `gr (1068,280)→(1068,264) t=4 dp=19` → `QY = 280,LPX = 0` (PATH),
`LINE,XS=1068,YS=280,ZS=19,XE=1068,YE=264,ZE=19` (BLOCK).

---

## 4. Doimiy va ma'lumotga bog'liq maydonlar

| Doimiy (1009/1009) | Ma'lumotga bog'liq |
|---|---|
| `BEGIN ID CID3`, `REL= 3.10`, `AXIS= x+,y-,z-`, `LAYER …` qatorlari, `PUNTO [ 0 , 0 , LPZ ]`, `CREA_SPACE 1096 1096 16`, makro nomlari, `NOP "Width"…`, `#…=*` maydonlari, `#NUM_CAT=1`, `CAT=1`, `NAME=WRK`, `SIDE=0`, `COLOR=LIGHT_GREEN`, `VISIBILITY=YES`, `ISBLOCK=0`, `SAWINSERTMODE=0` | `''=`, `PROGETTO`, LX/LY/LZ/LPX/LPY/LPZ, PATH qiymatlari, CREA_LAB tekisligi, `#TYPE/TYP`, `DIAM`, `DEPTH`, `WORKSIDE`, POINT, LINE |

`CREA_SPACE 1096 1096 16` (ish maydoni?) va `T=16` hamma faylda, hatto 18 mm detalda ham — stanok sozlamasi deb taxmin.

---

## 5. Minimal anonim misol

Detal 600×400×16: `bf (100,50) d=5 dp=12`, `gr (0,350)→(600,350) t=4 dp=8`, `bl y=40 m=true d=8 dp=30`
(+ freza — chiqmaydi). Writer natijasi (`CRLF`):
```
BEGIN ID CID3
 ''=01_001 detal
 REL= 3.10
 AXIS= x+,y-,z-
END ID
BEGIN MAINDATA
 LX= 600
 LY= 400
 LZ= 16
END MAINDATA
BEGIN PARAMETRIC SECTION
[ 0.0 ] PROGETTO  900101_01_001 (
LPX = 600 NOP "Width"
, LPY = 400 NOP "Height"
, LPZ = 16 NOP "Thickness"
) EOS
[ 0.1 ] PATH    "" "Drill\1_Single.pm4" (QX = 100 "Quota X",QY = 50 "Quota Y",DIA = 5 "Diametro",PRF = 12 "Profondita")
[ 0.2 ] PATH    "" "Saw\X1_LPX.pm4" QY = 350 "Quota Y",LPX = 600 "Larghezza",PRF = 8 "Profondita",SP = 4 "Spessore lama")
[ 0.3 ] PATH    "" "Drill\1_Single.pm4" (QX = 40 "Quota X",QY = 8 "Quota Y",DIA = 8 "Diametro",PRF = 30 "Profondita")
----------   LAVORAZIONE BASE DEL PROGETTO   ------------------------------------------------
[  1.0 ] LAYER ON START 1 "WRK" COLORE 3
[  1.1 ] LAYER  EOS
[  2.0 ] LAYER ON START 2 "DOC" COLORE 2
[  2.1 ] LAYER  EOS
[  0.0 ] PUNTO [ 0 , 0 , LPZ ]
[  0.1 ] CREA_SPACE 1096 1096 16
[ 1.0 ] CREA_LAB FRONTALE
[ 2.0 ] SEGMENTO MATITA PER [0.0,0.0,LPZ] INCLINAZIONE ASSE_X ANGOLO 0 MISURA 1
[ 3.0 ] INSERISCI FORI #1
[ 4.0 ] CREA_LAB FRONTALE
[ 5.0 ] SEGMENTO MATITA PER [0.0,0.0,LPZ] INCLINAZIONE ASSE_X ANGOLO 0 MISURA 1
[ 6.0 ] INSERISCI FORI #2
[ 7.0 ] CREA_LAB SINISTRA
[ 8.0 ] SEGMENTO MATITA PER [0.0,0.0,0.0] INCLINAZIONE ASSE_X ANGOLO 0 MISURA 1
[ 9.0 ] INSERISCI FORI SIMMETRICO ASSE_Y PIANO  #3
[  999.  ] FINE_MACRO
&&& [1,1] #NUM_CAT=1,#ID_TOOLNAME=*,#PRIORITY=*,#TYPEDRILL=*,#DWNSPEED=*,#RIFDRILL=*,#TYPE=1,#AZ=270.000000,#AR=0.000000,#WORKSIDE=0,#DIAM=5,#ID_DEPTH=12
&&& [2,1] #NUM_CAT=1,#AR=*,#STDROT_S=*,#STDWRK_S=*,#DWNSPEED=*,#ROTSENSE=*,#ID_DIRECTION=*,#I_X_MIN=*,#I_X_MAX=*,#I_Y_MIN=*,#I_Y_MAX=*,#I_Z_MIN=*,#I_Z_MAX=*,#I_DEPTH_MIN=*,#I_DEPTH_MAX=*,#PRIORITY=*,#ID_TOOLNAME=*,#WORKSIDE=*,#ID_PARDISTANCE=*,#BLOCK_PRIO=*,#MIRXY=*,#TOOLPROFILENAME=*,#BLADE_CRU=*,#TYPE=1,#AZ=0.0,#DIAM=4,#ID_PARDEPTH=8,#ISBLOCK=0,#SAWINSERTMODE=0
&&& [3,1] #NUM_CAT=1,#ID_TOOLNAME=*,#PRIORITY=*,#TYPEDRILL=*,#DWNSPEED=*,#RIFDRILL=*,#TYPE=1,#AZ=270.000000,#AR=0.000000,#WORKSIDE=0,#DIAM=8,#ID_DEPTH=30
END PARAMETRIC SECTION
BEGIN BLOCK
NAME=WRK
SIDE=0
COLOR=LIGHT_GREEN
VISIBILITY=YES
 BEGIN CUSTOM
  BEGIN TECH
   CAT=1
   TYP=1
   ANG=270.0,0.0
   DIAM=5
   DEPTH=12,12
   WORKSIDE=0
  END TECH
  POINT,X=100,Y=50,Z=0
 END CUSTOM
BEGIN PLINE
BEGIN TECH
    CAT=1
    TYP=1
    ANG=0.0,0.0
    DIAM=4
    WORKSIDE=0
    PARALDEPTH=8
     ISBLOCK=0
     SAWINSERTMODE=0
END TECH
    LINE,XS=0,YS=350,ZS=8,XE=600,YE=350,ZE=8
END PLINE
 BEGIN CUSTOM
  BEGIN TECH
   CAT=1
   TYP=1
   ANG=0.0,0.0
   DIAM=8
   DEPTH=30,30
   WORKSIDE=1
  END TECH
  POINT,X=0.0 ,Y=40,Z=8
 END CUSTOM
END BLOCK
```

---

## 6. Noma'lumlar — foydalanuvchiga savollar

1. **Q1. Frezalash:** GibLab bu stanok uchun konturlarni (65 ta, masalan plintus kesimi) umuman chiqarmaydi. Stanokda freza
   bormi? Bo'lsa qaysi makro/sintaksis (masalan `ROUT`/`PLINE` + `ARC`) — namunaviy qo'lda yozilgan fayl kerak.
2. **Q2. Paz:** stanok PARAMETRIC (`Saw\X1_LPX`, faqat QY/LPX) ni o'qiydimi yoki BLOCK `LINE` ni? Vertikal paz (x1=x2)
   parametrik qismda `LPX = 0` bo'lib chiqadi — xato emasmi?
3. **Q3. `#TYPE` qoidasi:** 2 = o'tuvchi, 3 = d ≥ 15 deb aniqlandi; chegara 10 va 15 orasida (12 mm?) noma'lum. Tur asbob
   nomidan (`BoreTh*`) olinadimi yoki chuqurlikdan?
4. **Q4. Orqa tomon:** faylda tomon belgisi yo'q, faqat X akslantirilgan (L−x). Operator detalni tik o'q atrofida
   ag'darishi kerak — shundaymi? Orqa tomonda qirra teshigi/paz namunada yo'q (SINISTRA↔DESTRA almashadi deb taxmin).
5. **Q5. Burish/ko'zgu** (`turn`, `mirHor/mirVert`) namunada ishlatilmagan.
6. **Q6.** Kirill nom/`"` belgisi `''=` va PROGETTO da qanday yoziladi?
7. **Q7.** `CREA_SPACE 1096 1096 16` va `REL= 3.10` — stanok sozlamasimi (o'zgartirish kerakmi)?
