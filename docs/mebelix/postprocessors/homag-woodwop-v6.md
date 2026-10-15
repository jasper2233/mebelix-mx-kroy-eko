# Homag woodWOP v6.x — `.mpr` postprotsessor formati (namunalardan tiklangan)

> Manba: `post prtsessorlar/PRISADKA APPARAT/Homag Wood WOP v6.x/*.zip` (15 buyurtma, 1009 ta `.mpr`) va shu buyurtmalarning
> korxona `.project` fayllaridagi XNC dasturlari (1014 ta). Faqat chiqish fayllari va korxonaning o'z XML fayllari o'qildi.
> Mijoz ismlari — «mijoz». Holat: **to'liq tushunilgan** (avtomatik solishtirish: 958/958 fayl, 8349/8349 amal mos — §3.6).

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.mpr` (woodWOP 4.0 matn formati; sarlavhada `VERSION="4.0 Alpha"`) |
| Bir fayl = | **bitta XNC operatsiyasi** (bitta detal tomoni). Yuz (лицевая) va orqa tomon — alohida XNC operatsiyalari → alohida fayllar |
| Fayl nomi | `<XNC operatsiya kodi>.mpr`, masalan `316601_01_003.mpr` |
| Takror kod | bir loyihada bir xil kod bir necha marta uchrasa — XML tartibida: `kod.mpr`, `kod (1).mpr`, `kod (2).mpr` … (masalan `316601_13_008 (5).mpr`) |
| Kodlash | kod — XNC operatsiyasining `code` atributi (MebeliX: «Кодирование» natijasi). Korxona shabloni: `BBBBPP_MM_DDD` — `BBBB` buyurtma raqami, `PP` mahsulot raqami (`01`, `02` …), `MM_DDD` — detal kodi (`part.code`, masalan `01_003` = 01-modul, 3-detal). Orqa tomon dasturi — xodim qo'lda yaratgan alohida operatsiya, kodi `…_2` bilan tugaydi (`318001_01_001_2`). Boshqa shablonlar ham uchraydi (`01_041x047x0`) — fayl nomi har doim kodning o'zi |
| Kodirovka | sof ASCII (1009/1009); kiril harfi uchramadi. Material nomlari lotincha. Kiril bo'lsa — ❓ (savol 6) |
| Qator oxiri | CRLF (`\r\n`), oxirgi qator `!` + CRLF |
| O'nlik ajratgich | nuqta `.` |
| Sonlar | 2 xonagacha yaxlitlanadi, keyin eng qisqa ko'rinish (`34.0`→`34`, `590.9996`→`591`, `313.4998`→`313.5`, `-5.7952`→`-5.8`). **Istisno:** qirra teshigi (`<103`) da qarama-qarshi qirra koordinatasi `XA="368.0"` / `YA="500.0"` (dx/dy `.0` bilan) — stanok uchun farqi yo'q, lekin aynan takrorlash uchun shunday yozish mumkin |
| Bo'sh qatorlar | `[H` va `[001` bloklaridan keyin, har bir `<100/<102/<103/<105/<109/]n` va `$E1…` blokidan **oldin** bitta bo'sh qator; `<152`, `!` va `$E0` oldidan bo'sh qator yo'q |
| Zip | `<buyurtma>_<mijoz>.zip`, ichida papkasiz `.mpr` lar |

Sarlavha → `[001` → `<100` → amallar (XNC tartibida) → `<152` grafik izohlar → `!`.

## 2. Sintaksis

### 2.1 `[H` — sarlavha
```
[H
VERSION="4.0 Alpha"     const
MAT="HOMAG"             const
FM="1"                  const
INCH="0"                const (mm)
VIEW="NOMIRROR"         const (orqa tomon ham NOMIRROR — ko'zgulash koordinatalarda qilinadi)
ANZ="1"                 = detal soni (part@count), 958/958 tasdiqlangan
BES="0"                 const
ENT="0"                 const
_BSX=1784               = dx  (qo'shtirnoqsiz)
_BSY=283                = dy
_BSZ=16                 = dz
_FNX=0.000000           const
_FNY=0.000000           const
_RNX=0.000000           const
_RNY=0.000000           const
_RNZ=0.000000           const
_RX=1784                = dx
_RY=283                 = dy
```

### 2.2 `[001` — o'zgaruvchilar va `<100 \WerkStck\` — zagotovka
```
[001
l="1784"        = dx
KM="length"
w="283"         = dy
KM="width"
t="16"          = dz
KM="thickness"

<100 \WerkStck\
LA="l"  BR="w"  DI="t"          (har biri alohida qatorda) — o'lcham o'zgaruvchilardan
FNX="0" FNY="0" AX="0" AY="0"   const (pripusk/siljish yo'q)
```

### 2.3 Koordinata tizimi
* `.mpr` koordinatalari = XNC koordinatalari **o'zgarishsiz** (yuz tomoni). Origin (0,0) — XNC origini, X — dx bo'ylab, Y — dy bo'ylab, mm.
* XNC konventsiyasi (`.project` da saqlangani, qirra teshiklari va kromka ma'lumotidan aniqlangan):
  `y = 0` — **`elt`** («верх») qirrasi (`bt` teshigi `YA=0`, `BM="YP"`); `y = dy` — **`elb`** («низ», `bb` → `YA=dy`, `YM`);
  `x = 0` — **`ell`** (`bl` → `XA=0`, `XP`); `x = dx` — **`elr`** (`br` → `XA=dx`, `XM`). Kromka grafik izohlari ham shu joylarda (§2.9, 958/958).
* Yoy yo'nalishi va radius korreksiyasi raqamlarga **o'zgarishsiz** o'tadi (`dir=false→DS=0`, `c=1→WRKL`). Bu XNC raqamlarini matematik
  (Y yuqoriga) tizimda talqin qilishga mos: freza doim chiqindi tomonda turadi (§2.7). woodWOP ham Y yuqoriga. Demak GibLab ekranida
  (Y pastga) ko'rinadigan rasm stanokda X o'qi atrofida ko'zgulangan ko'rinadi — dastur raqamlari bir xil.
* Z: vertikal teshik chuqurligi `TI` musbat, yuzadan pastga. Qirra teshigi balandligi `ZA` — **XNC `z` ga teskari tomondan** o'lchanadi (§2.5).
* Burilish (`turn`) va ko'zgu (`mirHor/mirVert`) namunalarda doim 0/false — ularning ta'siri ko'rilmagan.

### 2.4 `<102 \BohrVert\` — vertikal (yuza) teshik
```
<102 \BohrVert\
XA="371"     X
YA="50"      Y
BM="LS"      LS — chuqurligi berilgan (keyin TI), LSL — o'tuvchi (TI yo'q)
TI="9"       chuqurlik (faqat LS)
DU="5"       diametr = XNC tool d
```
Kalitlar tartibi: LS — `XA YA BM TI DU`; LSL — `XA YA BM DU`.
O'tuvchi teshik: XNC `dp ≥ dz` (namunalarda har doim `dp=throughBoreDepth`, `var throughBoreDepth = dz+3.00`, asbob `BoreTh8`/`BoreTh7`) →
`BM="LSL"`, chuqurlik yozilmaydi (stanok o'zi o'tkazadi). Raqamli `dp` hech qachon `dz` dan katta bo'lmagan (max 13).
Tool raqami yo'q — stanok diametr bo'yicha shpindel tanlaydi.

### 2.5 `<103 \BohrHoriz\` — gorizontal (qirra) teshik
```
<103 \BohrHoriz\
XA="0"     X  (bl → 0, br → dx (".0" bilan), bt/bb → x)
YA="70"    Y  (bt → 0, bb → dy (".0" bilan), bl/br → y)
ZA="8"     balandlik
TI="34"    chuqurlik (qirradan ichkariga) = dp
BM="XP"    yo'nalish: XP (+X, chap qirradan), XM (−X, o'ng qirradan), YP (+Y, elt qirradan), YM (−Y, elb qirradan)
DU="4.5"   diametr
```
`ZA`: `m=true` («по середине») → `dz/2`; `m=false` → **`dz − z`** (3166 `14_017`: dz=18, z=8 → ZA=10; 28 ta teshik, hammasi mos).

### 2.6 `<109 \Nuten\` — paz (arra)
```
<109 \Nuten\
XA="1784" YA="141.5"   boshi (x1,y1)
XE="0"    YE="141.5"   oxiri (x2,y2)
TI="10.5"              chuqurlik = dp (o'tuvchi: throughCutDepth = dz+3 → TI=19)
NB="10.5"              paz eni = XNC t (arra qalinligidan katta bo'lsa — stanok bir necha o'tish qiladi)
RK="NoWRK"             korreksiya yo'q (XNC c=0; boshqa c namunada yo'q)
TNO="-1"               asbob — stanok tanlaydi (const)
EM="MOD1"              const
```
Arra asbobi (`Cut4`, d=4) faylga yozilmaydi. Paz o'qi = (x1,y1)→(x2,y2) chizig'i, NB shu chiziq atrofida (c=0 → markaz).

### 2.7 Frezalash konturi: `]n` + `$E…` + `<105 \Konturfraesen\`
```
]1                 kontur raqami (fayl ichida 1, 2, … XNC dagi ms tartibida)
$E0                element 0 — boshlang'ich nuqta
KP                 (oxirida bitta bo'shliq: "KP ")
X=0                ms x   (qo'shtirnoqsiz)
Y=-10              ms y
Z=0                const
KO=00              const
                   (bo'sh qator)
$E1
KL                 to'g'ri chiziq ("KL ")  ← ml
X=0
Y=284
                   
$E2
KA                 yoy ("KA", bo'shliqsiz)  ← mac
X=300              oxirgi nuqta
Y=582
DS=0               yo'nalish: XNC dir=false → 0, dir=true → 1
R=298.3            radius = |boshlang'ich nuqta − markaz(cx,cy)|, 2 xona
…
<105 \Konturfraesen\
EA="1:0"           kontur:element boshi
EE="1:3"           kontur:oxirgi element
RK="WRKL"          korreksiya: XNC c=1 → WRKL, c=2 → WRKR (44 / 21 ta, hammasi mos). c=0 → NoWRK (taxmin, namunada yo'q)
MDA="SEN"          kirish — tik (XNC in=0); boshqa in qiymati namunada yo'q
MDE="SEN_AB"       chiqish — tik ko'tarilish (XNC out=1); boshqasi yo'q
EM="0"             const
TNO="-1"           asbob — stanok tanlaydi (Mill8 d=8 yozilmaydi)
ZA="0"             chuqurlik pozitsiyasi: namunalarda doim dp=contMillDepth=dz (o'tuvchi) → 0. Taxmin: ZA = dz − dp ❓
F_="STANDARD"      const
```
Yoylar faqat markaz bilan (`mac`) uchradi; barchasi ≤ 180° (63–90°), shuning uchun `R`+`DS` bir qiymatli. > 180° yoy uchun woodWOP
`KA` da qanday ifoda kerakligi ❓. `ma` (radius bilan), `ma3p`, `MillRect`, `MillEllipse` — namunada yo'q.
Har kontur o'z `]n` bloki bilan, darhol keyin uning `<105` i keladi (kontur ta'rifi va makro birga, XNC tartibidagi o'rnida).

### 2.8 Amallar tartibi
Faylda amallar XNC buyruqlari tartibida (958/958 ketma-ket solishtirildi): `bf→<102`, `bl/br/bt/bb→<103`, `gr→<109`,
`ms…(ml|mac)*→]n…<105`. `tool` va `var` buyruqlari faylga chiqmaydi (faqat qiymat beradi). Massiv `ac>1` namunada yo'q
(hamma joyda `ac=1` yoki yo'q) — MebeliX har teshikni alohida `<102` sifatida yoyishi kerak (taxmin).

### 2.9 `<152 \Grafischer Kommentar\` — kromka va tomon belgilari (faqat ekran uchun, ishlov emas)
**Kromka chizig'i** (`LOCAL="1"`) — detalning har kromkali qirrasi uchun, tartib: `elt, elb, ell, elr`:
```
<152 \Grafischer Kommentar\
LOCAL="1"
XA= YA=        to'rtburchak markazi: elt (dx/2, 0) · elb (dx/2, dy) · ell (0, dy/2) · elr (dx, dy/2)
BR= HE=        eni/bo'yi: elt/elb (dx, 5) · ell/elr (5, dy)
WI="0"
ROT= GRUEN= BLAU=   rang (RGB) = kromka operatsiyasi (EL) id si bo'yicha palitra:
                    #1 (0,0,0) · #2 (210,105,30) · #3 (100,149,237) · #4 (255,127,80) · #5 (95,158,160)   (1593/1593 mos)
WIDTH="3"
KAT="06-19 votan"   kromka materiali nomi (part@el?Mat)
MNM="06-19 votan"   xuddi shu
STARTLOCAL                    ┐
SIZE X100.0000 Y100.0000      │
SPINDLE X0.0000 Y0.0000       │  o'zgarmas «birlik kvadrat» rasm
U                             │  (aynan shu matn, jumladan
X0.0000 Y0.0000               │   "X0.000 Y100.0000" dagi 3 xona)
D                             │
X100.0000 Y0.0000             │
X100.0000 Y100.0000           │
X0.000 Y100.0000              │
X0.000 Y0.0000                │
ENDLOCAL                      ┘
```
**Tomon belgisi** (`LOCAL="2"`) — faqat detalning ham yuz, ham orqa XNC dasturi bo'lsa (37+37 fayl, 74/74):
kalitlar tartibi `LOCAL XA YA ROT GRUEN BLAU BR HE WI WIDTH` + o'sha STARTLOCAL…ENDLOCAL; 20×20 kvadrat:
yuz tomoni — `XA=dx−30, YA=30`, rang (10,200,150); orqa tomoni — `XA=30, YA=30`, rang (200,10,150) (ikkalasi ham detalning bitta fizik burchagi).

### 2.10 Orqa tomon (`side=false` yoki eski loyihada `side="2"`)
`X' = dx − x`, `Y' = y` (detal Y o'qi atrofida ag'dariladi). Tasdiqlangan: `bf` (255 teshik, 37 fayl), `gr` (7 paz), kromka izohlari (`ell`↔`elr` joy almashadi).
Orqa tomonda qirra teshigi va freza namunada yo'q; mantiqan `bl/br` yo'nalishi `XP↔XM`, yoy `DS` 0↔1, `WRKL↔WRKR` almashishi kerak (❓ tasdiqlanmagan).
Yuz tomoni: `side=true` yoki `"1"`.

## 3. MebeliX XNC → `.mpr` moslik jadvali

| MebeliX | GibLab teg | `.mpr` | Qoida |
|---|---|---|---|
| (dastur) dx, dy, dz | `program dx dy dz` | `_BSX/_RX`, `_BSY/_RY`, `_BSZ`; `l/w/t` | 2 xona, qisqa format |
| Operatsiya «Количество» | part@count | `ANZ` | |
| Tool | `tool name d` | — | faqat `DU` uchun diametr |
| Var / Par / Set | `var` | — | ifoda hisoblanadi (dp ga) |
| DrillFront | `bf x y dp` | `<102` XA=X(x) YA=y DU=d; dp<dz → `LS`+TI=dp; dp≥dz → `LSL` | X(x)=x (yuz) / dx−x (orqa) |
| DrillLeft | `bl y z m dp` | `<103` XA=0 YA=y BM=XP | ZA: m → dz/2, aks holda dz−z; TI=dp |
| DrillRight | `br` | `<103` XA=dx YA=y BM=XM | |
| DrillTop | `bt x` | `<103` XA=x YA=0 BM=YP | |
| DrillBottom | `bb x` | `<103` XA=x YA=dy BM=YM | |
| Groove | `gr x1 y1 x2 y2 t dp c` | `<109` XA YA XE YE TI=dp NB=t RK=NoWRK TNO=-1 EM=MOD1 | |
| MillStart | `ms x y dp c in out` | `]n`, `$E0 KP X Y Z=0 KO=00`, `<105` RK/MDA/MDE/ZA | c 1→WRKL, 2→WRKR; in 0→SEN; out 1→SEN_AB |
| MillLine | `ml x y` | `$Ek KL X Y` | |
| MillArcCenter | `mac x y cx cy dir` | `$Ek KA X Y DS R` | DS = dir?1:0; R = |start−c| |
| MillArc (R) | `ma` | `$Ek KA X Y DS R` (taxmin; namunada yo'q) | R<0 / DIR → DS |
| Origin | `xy` | — | koordinatalarga qo'shib yuboriladi (namunada yo'q) |
| Kromka | part@elt/elb/ell/elr | `<152 LOCAL=1` | §2.9 |

### 3.5 Tekshirilgan detallar (yonma-yon)

**A. `316601_01_001`** (1250×500×16, kromka `elb` — EL#1): pastki qirradan 4 ta Ø4.5 + 4 ta o'tuvchi Ø8.
| XNC | `.mpr` |
|---|---|
| `bb x=785.99 dp=32.0 z=8 m=true Bore4.5` | `<103 XA="785.99" YA="500.0" ZA="8" TI="32" BM="YM" DU="4.5"` |
| `bb x=986 dp=34.0` | `<103 XA="986" YA="500.0" ZA="8" TI="34" BM="YM" DU="4.5"` |
| `bf x=8 y=70 dp=throughBoreDepth BoreTh8` | `<102 XA="8" YA="70" BM="LSL" DU="8"` |
| `bf x=1242 y=430 …` | `<102 XA="1242" YA="430" BM="LSL" DU="8"` |
| part `elb=@operation#1`, `elbMat=06-19 votan` | `<152 LOCAL=1 XA=625 YA=500 BR=1250 HE=5 ROT=0 GRUEN=0 BLAU=0 KAT="06-19 votan"` |

**B. `316601_13_008`** (368×582×16, kromka `elb`,`ell` — EL#3; 6 ta bir xil operatsiya → `…008.mpr`, `…008 (1)…(5).mpr`):
| XNC | `.mpr` |
|---|---|
| `bt x=69 dp=34.0 z=8 m=true Bore4.5` | `<103 XA="69" YA="0" ZA="8" TI="34" BM="YP" DU="4.5"` |
| `br y=291 …` | `<103 XA="368.0" YA="291" ZA="8" TI="34" BM="XM" DU="4.5"` |
| `ms x=0 y=-10 dp=contMillDepth(=dz) in=0 out=1 c=1 Mill8` | `]1 / $E0 KP X=0 Y=-10 Z=0 KO=00` … `<105 EA="1:0" EE="1:3" RK="WRKL" MDA="SEN" MDE="SEN_AB" ZA="0"` |
| `ml x=0 y=284` | `$E1 KL X=0 Y=284` |
| `mac x=300 y=582 cx=298.2989 cy=283.7059 dir=false` | `$E2 KA X=300 Y=582 DS=0 R=298.3` (|(0,284)−c| = 298.299) |
| `ml x=378 y=582` | `$E3 KL X=378 Y=582` |
| elb, ell (EL#3) | `<152 XA=184 YA=582 BR=368 HE=5` va `XA=0 YA=291 BR=5 HE=582`, rang (100,149,237) |

**C. `318001_01_001_2`** (orqa tomon, 2200×503×16, `side=false`; juft yuz dasturi `318001_01_001`):
| XNC | `.mpr` |
|---|---|
| `bf x=2192 y=73 dp=11 Bore8` | `<102 XA="8" YA="73" BM="LS" TI="11" DU="8"` (2200−2192) |
| `bf x=108 y=93 dp=11` | `<102 XA="2092" YA="93" …` |
| `bf x=50 y=469 dp=11` | `<102 XA="2150" YA="469" …` |
| `gr x1=2200 y1=0 x2=100 y2=0 t=6 dp=8 c=0 Cut4` | `<109 XA="0" YA="0" XE="2100" YE="0" TI="8" NB="6" RK="NoWRK"` |
| `ell` kromka | `<152 XA="2200" YA="251.5" BR="5" HE="503"` (chapdan o'ngga ko'chdi) |
| juft belgi | `<152 LOCAL="2" XA="30" YA="30" ROT="200" GRUEN="10" BLAU="150"`; yuz faylida `XA="2170"`, (10,200,150) |

**D. `316601_14_017`** (68×1581×18): `bl y=70 z=8 m=false dp=34.0 Bore8` → `<103 XA="0" YA="70" ZA="10" TI="34" BM="XP" DU="8"` (18−8);
`bl y=102 z=9 m=true dp=23.3` → `ZA="9" TI="23.3"`; `br y=493.67 …` → `XA="68.0" YA="493.67" BM="XM"`.

### 3.6 Avtomatik solishtirish natijasi
Skript (scratchpad `tools/hcmp.py`, `hcom.py`): har XNC dasturni yuqoridagi qoidalar bilan `.mpr` ga aylantirib, fayldagi bloklar bilan
**tartibi bo'yicha** solishtiradi (±0.006 mm).
* 3173 dan tashqari 14 buyurtma: **958/958 fayl**, 5795/5795 `<102`, 2434/2434 `<103`, 60/60 `<109`, 60/60 kontur (barcha elementlari,
  DS, R, RK), sarlavha o'lchamlari, `ANZ`, kromka izohlari (geometriya, KAT, rang) va juft belgilar — **hammasi mos**.
* 3173: loyiha eksportdan keyin tahrirlangan (fayl 2026-10-01, zip 2026-09-30): 7 dastur faylsiz, 2 fayl dasturiz, 24 faylda o'lcham/teshiklar
  farq qiladi; eski `3173 mijoz.project` ham mos emas → oraliq versiyadan eksport qilingan. Format xatosi emas.
* 3183: eski loyiha (`side="1"/"2"`, part@l yo'q, kromka material nomi yo'q) — geometriya mos, KAT nomi tekshirilmadi.

## 4. Doimiy maydonlar (stanok sozlamasi bo'lishi mumkin) va ma'lumotdan keladiganlar

| Doimiy (stanok profiliga chiqarish tavsiya etiladi) | Ma'lumotdan |
|---|---|
| `VERSION="4.0 Alpha"`, `MAT="HOMAG"`, `FM`, `INCH=0`, `VIEW=NOMIRROR`, `BES`, `ENT`, `_FN*/_RN*` | `ANZ`, `_BSX/_BSY/_BSZ`, `_RX/_RY`, `l/w/t` |
| `<100`: `LA/BR/DI` nomlari, `FNX/FNY/AX/AY=0` | barcha XA/YA/XE/YE/ZA/TI/DU/NB, BM (tur va qirra) |
| `<109`: `RK=NoWRK`, `TNO=-1`, `EM=MOD1` | kontur X/Y, DS, R, RK, EA/EE |
| `<105`: `MDA=SEN`, `MDE=SEN_AB`, `EM=0`, `TNO=-1`, `ZA=0`, `F_=STANDARD`, `$E0 Z=0 KO=00` | kromka izohlari: joy, KAT/MNM, rang (EL id) |
| `<152`: `HE/BR=5` (kromka qalinligi chizig'i), `WIDTH=3`, `WI=0`, palitra, juft belgi (30 mm, 20×20, ranglar), STARTLOCAL rasm | juft belgi bor/yo'q |
| Through qoidasi `dp≥dz → LSL`, yaxlitlash 2 xona | |

## 5. Minimal namuna (anonim, 600×400×16, yuz tomoni, `elt` kromkasi EL#1)
XNC: `bf x=32 y=50 dp=13 (Bore35 d=35)`, `bf x=300 y=8 dp=dz+3 (BoreTh8)`, `bl y=50 z=8 m=true dp=34 (Bore8)`,
`gr x1=0 y1=380 x2=600 y2=380 t=4 dp=8 c=0`, `ms x=-10 y=100 dp=dz c=2 in=0 out=1` → `ml x=610 y=100`.
```
[H
VERSION="4.0 Alpha"
MAT="HOMAG"
FM="1"
INCH="0"
VIEW="NOMIRROR"
ANZ="1"
BES="0"
ENT="0"
_BSX=600
_BSY=400
_BSZ=16
_FNX=0.000000
_FNY=0.000000
_RNX=0.000000
_RNY=0.000000
_RNZ=0.000000
_RX=600
_RY=400

[001
l="600"
KM="length"
w="400"
KM="width"
t="16"
KM="thickness"

<100 \WerkStck\
LA="l"
BR="w"
DI="t"
FNX="0"
FNY="0"
AX="0"
AY="0"

<102 \BohrVert\
XA="32"
YA="50"
BM="LS"
TI="13"
DU="35"

<102 \BohrVert\
XA="300"
YA="8"
BM="LSL"
DU="8"

<103 \BohrHoriz\
XA="0"
YA="50"
ZA="8"
TI="34"
BM="XP"
DU="8"

<109 \Nuten\
XA="0"
YA="380"
XE="600"
YE="380"
TI="8"
NB="4"
RK="NoWRK"
TNO="-1"
EM="MOD1"

]1
$E0
KP 
X=-10
Y=100
Z=0
KO=00

$E1
KL 
X=610
Y=100

<105 \Konturfraesen\
EA="1:0"
EE="1:1"
RK="WRKR"
MDA="SEN"
MDE="SEN_AB"
EM="0"
TNO="-1"
ZA="0"
F_="STANDARD"
<152 \Grafischer Kommentar\
LOCAL="1"
XA="300"
YA="0"
BR="600"
HE="5"
WI="0"
ROT="0"
GRUEN="0"
BLAU="0"
WIDTH="3"
KAT="kromka-1"
MNM="kromka-1"
STARTLOCAL
SIZE X100.0000 Y100.0000
SPINDLE X0.0000 Y0.0000
U
X0.0000 Y0.0000
D
X100.0000 Y0.0000
X100.0000 Y100.0000
X0.000 Y100.0000
X0.000 Y0.0000
ENDLOCAL
!
```
(Har qator CRLF bilan tugaydi; `KP ` va `KL ` dan keyin bitta bo'shliq.)

## 6. Ochiq savollar (foydalanuvchiga)
1. **`<105 ZA`**: namunalarda freza doim o'tuvchi (`dp=dz`) va `ZA="0"`. Chuqurligi `dz` dan kichik freza (cho'ntak, chuqur bo'lmagan kontur) qanday yoziladi — `ZA = dz − dp` mi yoki `ZA = dp`? Bitta shunday namuna kerak.
2. **Qirra teshigi Z**: `m=false` da `ZA = dz − z` chiqdi. XNC `z` qaysi yuzadan (lits/orqa) o'lchanadi va stanokda `ZA` stol tomonidanmi? (Raqam mos, ma'no tasdig'i kerak.)
3. **Orqa tomonda** qirra teshigi / freza bo'lsa — `XP↔XM`, `DS` 0↔1, `WRKL↔WRKR` almashtirish to'g'rimi? (namunada yo'q)
4. **C korreksiya ma'nosi**: GibLab `c=1` → `WRKL`, `c=2` → `WRKR` chiqdi; `J_XNC_SPEC.md` da «1 o'ng, 2 chap» deb yozilgan — bu ekran (Y pastga) bo'yicha. MebeliX UI dagi nomlanish shunday qolsinmi (raqam bo'yicha o'tkazish to'g'ri)?
5. **Kirish/chiqish** (`in/out`): faqat 0/1 uchradi → `SEN`/`SEN_AB`. Urinma/yoy bo'ylab kirish (`TAN`, `BOG` …) kerakmi va stanokda qaysi nomlar ishlaydi?
6. **Asbob raqami** `TNO="-1"` va `F_="STANDARD"` — stanok o'zi tanlaydi; aniq asbob raqamini yozish kerakmi (Mill8, Cut4)?
7. **Massiv** (`ac>1`), `MillArc` (R bilan), > 180° yoy, `Origin`, burilish/ko'zgu — namunada yo'q; yoyib yozish (har teshik alohida, yoy — ikkiga bo'lib) maqbulmi?
8. **Kirill / maxsus belgilar** material nomida (`KAT`) bo'lsa kodirovka (cp1252? UTF-8?) — namunada faqat ASCII.
9. Kromka rang palitrasi 5 ta (EL#1…#5) uchradi; 6-chi va keyingilari rangi noma'lum (faqat ekran uchun — muhim emas).
