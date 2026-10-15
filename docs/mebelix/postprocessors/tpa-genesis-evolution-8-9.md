# TPA Genesis Evolution 8.9 — `.CNC` (EDICAD / Albatros) postprotsessori

Holat: **to'liq (sverlovka, paz, frezalash — yuz tomon)**. 15 buyurtmadagi barcha fayllar prototip generatorimiz bilan solishtirildi: 3173 dan tashqari **958/958 fayl bayt-ma-bayt bir xil** (3173 da yana 25 fayl bir xil; qolgan 24 tasi — eksportdan keyin o'zgargan loyiha). Ochiq joylar: paz eni faylga yozilmaydi, orqa tomondagi qirra teshigi va frezalash namunada yo'q.

Manba namunalar: `post prtsessorlar/PRISADKA APPARAT/TPA Genesis Evolution 8.9/<NNNN>_<mijoz>.zip` (15 ta, jami 1009 fayl).
Mos loyihalar: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` (3183 — `<NNNN> <mijoz>.project`, `side="1"/"2"`).

> 3173: loyiha eksportdan keyin (2026-10-01) o'zgartirilgan: 7 XNC ning fayli yo'q, 2 fayl loyihada yo'q, 1-mahsulot dasturlari o'zgargan. Format xatosi emas.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.CNC` (oddiy matn, EDICAD formati) |
| Bitta fayl | **bitta XNC operatsiyasi** (detalning bitta tomoni) = bitta fayl |
| Fayl nomi | `<XNC kodi>.CNC` (`316601_01_003.CNC`); bir xil kodli XNC lar XML tartibida: `kod.CNC`, `kod (1).CNC`, `kod (2).CNC` … (3166 `13_008` — 6 ta). Orqa tomon — alohida XNC, kodi Bazisdan `_2` bilan (`317001_01_005_2.CNC`) |
| Kodlash | ASCII (namunada ASCII dan tashqari bayt yo'q; kirill nom bo'lsa — cp1251 deb taxmin qilinadi, tekshirilmagan) |
| Qator oxiri | `CRLF`, oxirgi `}SIDE` ham `CRLF` bilan tugaydi |
| Sonlar | nuqta `.`; koordinata/chuqurlik — 4 kasrgacha yaxlitlab, ortiqcha nollarsiz (`371`, `785.99`, `-11.67`, `298.2989`); diametr — har doim kasr bilan (`5.0`, `4.5`, `35.0`) |
| Birlik | mm (`::UNm`) |

XNC kodi tuzilishi (barcha stanoklarda umumiy): `<buyurtma 4 xona><mahsulot 2 xona>_<shkaf>_<detal>[_2]`, masalan `316601_01_003` = buyurtma 3166, mahsulot 01 (`good code`), Bazis pozitsiyasi `01_003`.

---

## 2. Sintaksis

### 2.1 Fayl tuzilishi

```
TPA\ALBATROS\EDICAD\01.00:86:r0w0h0      ← o'zgarmas imzo
$=<detal nomi>                           ← operation@typeName, masalan "01_003 pb-bok"
::SIDE=1                                 ← o'zgarmas (1009/1009)
::UNm DL=<dx> DH=<dy> DS=<dz>            ← zagotovka: uzunlik, en, qalinlik
OFFS{ #0=0|0 … #7=0.0|0 }OFFS            ← o'zgarmas blok (har biri alohida qatorda, pastga qarang)
VARV{ }VARV  VAR{ }VAR  SPEC{ }SPEC  OPTI{ }OPTI  LINK{ }LINK  PREV{ }PREV   ← hammasi bo'sh
SIDE#1{ … }SIDE                          ← yuz (vertikal teshik, paz, frezalash)
SIDE#2{ }SIDE                            ← namunada doim bo'sh
SIDE#3{ … }SIDE                          ← yuqori qirra (XNC bt, y=0)
SIDE#4{ … }SIDE                          ← o'ng qirra  (XNC br, x=dx)
SIDE#5{ … }SIDE                          ← pastki qirra (XNC bb, y=dy)
SIDE#6{ … }SIDE                          ← chap qirra  (XNC bl, x=0)
```

5–23-qatorlar 1009 faylda bayt-ma-bayt bir xil:

```
OFFS{
#0=0|0
#1=0|0
#2=0|0
#3=0.0|0
#4=0.0|0
#5=0.0|0
#6=0.0|0
#7=0.0|0
}OFFS
VARV{
}VARV
VAR{
}VAR
SPEC{
}SPEC
OPTI{
}OPTI
LINK{
}LINK
PREV{
}PREV
```

Har `SIDE#k{` … `}SIDE` bloki ichida amallar `W#<makro>{ ::<tur> #<param>=<qiymat> … }W` ko'rinishida, XNC dagi tartibda. Bo'sh tomon ham yoziladi (`SIDE#2{` / `}SIDE`).

### 2.2 Makrolar

| Makro | Tur | Ma'nosi | Soni (namunada) |
|---|---|---|---|
| `W#81` | `::WTp` | teshik (point) | 8737 |
| `W#1050` | `::WT2` | paz X o'qi bo'ylab | 42 |
| `W#1051` | `::WT2` | paz Y o'qi bo'ylab | 18 |
| `W#89` | `::WTs` | frezalash boshlanishi (setup) | 65 |
| `W#2201` | `::WTl` | frezalash — to'g'ri chiziq | 128 |
| `W#2101` | `::WTa` | frezalash — markazli yoy | 51 |

#### `W#81` — teshik

```
W#81{ ::WTp #1=<a> #2=<b> #3=<-chuqurlik> #1002=<diametr> #1001=<o'tuvchi> }W
```

| Param | Ma'nosi |
|---|---|
| `#1`, `#2` | tomonning lokal koordinatalari (2.3-jadval) |
| `#3` | chuqurlik, **manfiy** (`dp=9` → `#3=-9`; o'tuvchi `dz+3` → `-19`) |
| `#1002` | asbob diametri (XNC `tool@d`), Java-double ko'rinishida (`8.0`, `4.5`) |
| `#1001` | `1` — o'tuvchi teshik: faqat **yuz** teshigi (`SIDE#1`) va `dp > dz`; qirra teshiklarida doim `0` (1623 ta `1`) |

Asbob nomi/raqami yozilmaydi — stanok diametr va tomon bo'yicha tanlaydi.

#### `W#1050` / `W#1051` — paz (arra)

```
W#1050{ ::WT2 #6=1 #8509=0 #8517=<x2> #8510=<x1> #8511=<y1> #8512=<-dp> #8514=1 #8515=1 #8525=0 #8526=0 #8527=0 }W
W#1051{ ::WT2 #6=1 #8509=1  #8518=<y2> #8510=<x1> #8511=<y1> #8512=<-dp> #8514=1 #8515=1 #8525=0 #8526=0 #8527=0 }W
```

(`W#1051` da `#8509=1` dan keyin **ikkita bo'sh joy**.)

| Param | Ma'nosi |
|---|---|
| `#8510`, `#8511` | boshlanish nuqtasi (x1, y1) |
| `#8517` | (1050) oxirgi X — paz `y = y1` chizig'ida x1 → x2 |
| `#8518` | (1051) oxirgi Y — paz `x = x1` chizig'ida y1 → y2 |
| `#8509` | o'q: 0 — X bo'ylab, 1 — Y bo'ylab |
| `#8512` | chuqurlik, manfiy |
| `#6=1`, `#8514=1`, `#8515=1`, `#8525..#8527=0` | o'zgarmas (60/60) |

**Paz eni (`gr@t`) va korreksiya (`gr@c`) faylga yozilmaydi.** `t=4`, `6`, `10.5` li pazlar bir xil chiqadi — stanok arraning o'z qalinligi bilan bitta o'tish qiladi deb ko'rinadi (Startech esa enni bir necha o'tishga bo'ladi). Bu — 1-ochiq savol. Qiya (o'qqa parallel bo'lmagan) paz namunada yo'q.

#### `W#89` / `W#2201` / `W#2101` — frezalash konturi (SIDE#1 ichida)

```
W#89{ ::WTs #1=<x> #2=<y> #3=<-dp> #40=<c> #36=<r> }W
W#2201{ ::WTl  #1=<x>  #2=<y> }W                                (#1 va #2 oldidan 2 ta bo'sh joy)
W#2101{ ::WTa  #1=<x>  #2=<y> #34=<dir> #31=<cx-x0> #32=<cy-y0> }W
```

| Param | Ma'nosi |
|---|---|
| `W#89 #1 #2` | freza kirish nuqtasi (XNC `ms x y`) |
| `W#89 #3` | chuqurlik, manfiy (`contMillDepth = dz` → `-16`) |
| `W#89 #40` | asbob radius korreksiyasi = XNC `ms@c` (namunada 1 — 44 ta, 2 — 21 ta). Qaysi tomon chap/o'ng — 3-savol |
| `W#89 #36` | `4` = freza diametri/2 (`Mill8` → 4) — **faraz**: namunada bitta freza bor, `in=0, out=1` ham o'zgarmas, shuning uchun `#36` kirish turi bo'lishi ham mumkin |
| `W#2201 #1 #2` | chiziq oxiri (XNC `ml`) |
| `W#2101 #1 #2` | yoy oxiri (XNC `mac x y`) |
| `W#2101 #34` | yo'nalish = XNC `mac@dir`: `true` → `1`, `false` → `0` |
| `W#2101 #31 #32` | yoy markazi **yoy boshlanish nuqtasiga nisbatan**: `cx − x0`, `cy − y0` (x0,y0 — oldingi nuqta) |

`ms@in/out` (kirish/chiqish turi) yozilmaydi. Frezalash qadamlari (SDP), tezliklar yozilmaydi.

### 2.3 Koordinatalar tizimi

**XNC (loyiha) koordinatalari:** boshlanish **chap-yuqori** burchak, X o'ngga, **Y pastga** — `y=0` = `elt` (yuqori qirra), `y=dy` = `elb`, `x=0` = `ell`, `x=dx` = `elr`. Dalil: «PAZ XDF» (orqa devor pazi) `elb` kromkali detallarda `y=0` da, `elt` kromkali detallarda `y=dy` da (masalan 3168 `02_001` / `02_002`); `services/xnc.py` ham shunday.

**TPA:** XNC koordinatalari **o'zgarishsiz** yoziladi (Y teskari qilinmaydi — Startech dan farqli). Tomonlar va lokal o'qlar:

| XNC | TPA tomon | `#1` | `#2` | `#3` |
|---|---|---|---|---|
| `bf x y dp` | `SIDE#1` | `x` | `y` | `-dp` |
| `bt x z dp` (yuqori qirra, y=0) | `SIDE#3` | `x` | `dz − z` | `-dp` |
| `br y z dp` (o'ng qirra, x=dx) | `SIDE#4` | `y` | `dz − z` | `-dp` |
| `bb x z dp` (pastki qirra, y=dy) | `SIDE#5` | `x` | `dz − z` | `-dp` |
| `bl y z dp` (chap qirra, x=0) | `SIDE#6` | `y` | `dz − z` | `-dp` |

`#2 = dz − z`: `m=true` da `z = dz/2` bo'lgani uchun farq ko'rinmaydi; `m=false, z=8, dz=18` (3166 `14_017…14_024`, 24 teshik) → `#2=10`. Homag ham `dz − z` yozadi, Startech esa `z` (8) — 2-savol.

Ma'lum bo'lishicha TPA tomon raqamlari: 1 — yuqori yuz, 3 — XNC y=0 qirrasi, 4 — x=dx, 5 — y=dy, 6 — x=0 (TPA da 3 odatda «old» qirra deb ataladi; demak TPA stolida XNC y=0 qirrasi operator tomonda — tasdiqlash kerak).

### 2.4 Orqa tomon (`side="false"` / `"2"`)

Alohida fayl (`…_2.CNC`), baribir `::SIDE=1` va `SIDE#1` ichida; detal **X bo'yicha ag'dariladi**: `#1 = dx − x`, `#2 = y` (o'zgarmaydi).

* `bf`: 255 ta — hammasi tasdiqlandi (3170 `01_005_2`: `x=243 y=698` → `#1=453 #2=698`, dx=696).
* `gr`: 7 ta — tasdiqlandi (3168 `02_008_2`: `(990,0)→(0,0)` → `#8510=0 #8511=0 #8517=990`).
* Qirra teshiklari, frezalash: orqa tomonda namunada **yo'q**. Faraz: `bl ↔ br` (SIDE#6 ↔ SIDE#4), `bt/bb` da `#1 = dx − x`; yoyda `x, cx` ag'dariladi va `#34` teskari bo'ladi.

---

## 3. MebeliX XNC → TPA moslik jadvali

| MebeliX `cmd` | TPA | Izoh |
|---|---|---|
| `DrillFront` | `SIDE#1 W#81 #1=X #2=Y #3=-DP #1002=D #1001=(DP>dz)` | orqa: `#1=dx−X` |
| `DrillTop` | `SIDE#3 W#81 #1=X #2=dz−Z` | `M=true` → Z=dz/2 |
| `DrillRight` | `SIDE#4 W#81 #1=Y #2=dz−Z` | |
| `DrillBottom` | `SIDE#5 W#81 #1=X #2=dz−Z` | |
| `DrillLeft` | `SIDE#6 W#81 #1=Y #2=dz−Z` | |
| `Groove` (gorizontal) | `SIDE#1 W#1050` | W (en) va C yo'qoladi! |
| `Groove` (vertikal) | `SIDE#1 W#1051` | |
| `MillStart` | `SIDE#1 W#89 #40=C #36=D/2` | IN/OUT/SDP yozilmaydi |
| `MillLine` | `W#2201` | |
| `MillArcCenter` | `W#2101 #34=DIR #31/#32 nisbiy markaz` | |
| `MillArc` (R bilan), `MillArc3P`, `MillFillet`, `MillRect`, `MillEllipse` | — | namunada yo'q: generator ularni avval markazli yoy / chiziqlarga aylantirishi kerak (`xnc.evaluate()` + `mill_arc()` geometriyasi) |
| `Origin`, `Var`, `Par`, `If`… | — | `evaluate()` bilan hisoblanib, faqat sonlar yoziladi |

Prototip generator (Python, namunalar bilan bayt-ma-bayt tekshirilgan):

```python
def n(v):                       # 4 kasr, ortiqcha nolsiz
    v = round(v, 4); return str(int(v)) if v == int(v) else repr(v)
SIDE = {"DrillFront": 1, "DrillTop": 3, "DrillRight": 4, "DrillBottom": 5, "DrillLeft": 6}
def cnc(name, dx, dy, dz, back, ops):
    sides = {k: [] for k in range(1, 7)}; cur = None
    for o in ops:                                   # evaluate() natijasi
        k = o.kind
        if k in SIDE:
            s = SIDE[k]
            a, b = {"DrillFront": (o.X, o.Y), "DrillTop": (o.X, dz-o.Z), "DrillBottom": (o.X, dz-o.Z),
                    "DrillLeft": (o.Y, dz-o.Z), "DrillRight": (o.Y, dz-o.Z)}[k]
            if back:
                if s in (1, 3, 5): a = dx - a
                else: s = 10 - s                    # 4<->6 (faraz)
            thr = 1 if k == "DrillFront" and o.DP > dz else 0
            sides[s].append(f"W#81{{ ::WTp #1={n(a)} #2={n(b)} #3={n(-o.DP)} #1002={float(o.D)!r} #1001={thr} }}W")
        elif k == "MillStart":
            x = dx - o.X if back else o.X; cur = (x, o.Y)
            sides[1].append(f"W#89{{ ::WTs #1={n(x)} #2={n(o.Y)} #3={n(-o.DP)} #40={o.C} #36={n(o.D/2)} }}W")
        elif k == "MillLine":
            x = dx - o.X if back else o.X; cur = (x, o.Y)
            sides[1].append(f"W#2201{{ ::WTl  #1={n(x)}  #2={n(o.Y)} }}W")
        elif k == "MillArcCenter":
            x, cx, d = o.X, o.CX, 1 if o.DIR == "true" else 0
            if back: x, cx, d = dx - x, dx - cx, 1 - d          # faraz
            sides[1].append(f"W#2101{{ ::WTa  #1={n(x)}  #2={n(o.Y)} #34={d} #31={n(cx-cur[0])} #32={n(o.CY-cur[1])} }}W")
            cur = (x, o.Y)
        elif k == "Groove":
            x1, x2 = (dx - o.X1, dx - o.X2) if back else (o.X1, o.X2)
            if abs(o.Y1 - o.Y2) < 1e-9:
                sides[1].append(f"W#1050{{ ::WT2 #6=1 #8509=0 #8517={n(x2)} #8510={n(x1)} #8511={n(o.Y1)} "
                                f"#8512={n(-o.DP)} #8514=1 #8515=1 #8525=0 #8526=0 #8527=0 }}W")
            else:
                sides[1].append(f"W#1051{{ ::WT2 #6=1 #8509=1  #8518={n(o.Y2)} #8510={n(x1)} #8511={n(o.Y1)} "
                                f"#8512={n(-o.DP)} #8514=1 #8515=1 #8525=0 #8526=0 #8527=0 }}W")
    L = [r"TPA\ALBATROS\EDICAD\01.00:86:r0w0h0", f"$={name}", "::SIDE=1",
         f"::UNm DL={n(dx)} DH={n(dy)} DS={n(dz)}", *HEADER_19_LINES]
    for s in range(1, 7):
        L += [f"SIDE#{s}{{", *sides[s], "}SIDE"]
    return "\r\n".join(L) + "\r\n"
```

---

## 4. Tekshiruv

### 4.1 Avtomatik (15 buyurtma, 1014 XNC)

| | Soni |
|---|---|
| Fayllar bayt-ma-bayt bir xil (3173 dan tashqari) | **958 / 958** |
| 3173: bir xil / farqli / fayli yo'q | 25 / 24 / 7 (loyiha o'zgargan) |
| `W#81` tomonlar bo'yicha | SIDE#1 6132, #3 259, #4 966, #5 286, #6 1094 |
| Paz / freza makrolari | 60 / 65 + 128 + 51 |

Birinchi gipotezadagi xatolar va tuzatish: (1) `#1001` faqat yuz teshigida (qirra teshigida `dp=34 > dz` bo'lsa ham 0); (2) qirra `#2 = dz − z` (12 faylda `z=8, dz=18` → 10).

### 4.2 Qo'lda tekshirilgan detallar

**A. 3166 `01_003` «pb-bok»** (694×500×16):

| XNC | TPA |
|---|---|
| `bf x=371 y=50 dp=9 Bore5` | `SIDE#1: W#81{ ::WTp #1=371 #2=50 #3=-9 #1002=5.0 #1001=0 }W` |
| `bf x=644 y=8 dp=throughBoreDepth (19) BoreTh8` | `SIDE#1: #1=644 #2=8 #3=-19 #1002=8.0 #1001=1` |
| `bl y=70 z=8 dp=34 Bore4.5` | `SIDE#6: #1=70 #2=8 #3=-34 #1002=4.5 #1001=0` |

**B. 3166 `13_008` «nostandart polka»** (368×582×16) — qirra + frezalash:

| XNC | TPA |
|---|---|
| `bt x=69 z=8 dp=34` | `SIDE#3: #1=69 #2=8 #3=-34` |
| `br y=50 z=8 dp=34` | `SIDE#4: #1=50 #2=8 #3=-34` |
| `ms x=0 y=-10 dp=contMillDepth(16) c=1 Mill8` | `W#89{ ::WTs #1=0 #2=-10 #3=-16 #40=1 #36=4 }W` |
| `ml x=0 y=284` | `W#2201{ ::WTl  #1=0  #2=284 }W` |
| `mac x=300 y=582 cx=298.2989 cy=283.7059 dir=false` | `W#2101{ ::WTa  #1=300  #2=582 #34=0 #31=298.2989 #32=-0.2941 }W` (298.2989−0, 283.7059−284) |
| `ml x=378 y=582` | `W#2201{ ::WTl  #1=378  #2=582 }W` |

**C. 3166 `00_010` «pol»** (283×1300) — vertikal paz `gr (141.5,0)→(141.5,1300) t=10.5 dp=10.5` → `W#1051{ ::WT2 #6=1 #8509=1  #8518=1300 #8510=141.5 #8511=0 #8512=-10.5 … }W`. `00_009` (gorizontal, 1784→0) → `W#1050 … #8517=0 #8510=1784 #8511=141.5 #8512=-10.5`.

**D. 3166 `14_017` «qosh»** (68×1581×18): `bl y=70 z=8 m=false dp=34 Bore8` → `SIDE#6: #1=70 #2=10 #3=-34 #1002=8.0`; `br y=50 z=9 m=true` → `SIDE#4: #1=50 #2=9`.

**E. 3170 `01_005_2`** (orqa, 696×776×16): `bf x=662 y=86 dp=12.5 Bore15` → `SIDE#1: #1=34 #2=86 #3=-12.5 #1002=15.0`.

---

## 5. O'zgarmas va ma'lumotga bog'liq maydonlar

| O'zgarmas (stanok/postprotsessor sozlamasi) | Ma'lumotdan |
|---|---|
| 1-qator imzosi, `::SIDE=1`, OFFS…PREV bloklari | `$=` nom, `::UNm DL DH DS` |
| `SIDE#2` (bo'sh) | har tomon amallari, tartib = XNC tartibi |
| `#6=1 #8514=1 #8515=1 #8525..27=0` (paz) | `#1 #2 #3 #1002 #1001` (teshik) |
| `#36=4` (freza; ehtimol D/2) | `#40` (= c), yoy `#34/#31/#32` |

---

## 6. Minimal namuna (anonim)

600×400×16 yon devor: yuzda Ø5 teshik, chap qirrada Ø8, o'tuvchi Ø8, gorizontal paz.

```
TPA\ALBATROS\EDICAD\01.00:86:r0w0h0
$=01_001 bok
::SIDE=1
::UNm DL=600 DH=400 DS=16
OFFS{
#0=0|0
#1=0|0
#2=0|0
#3=0.0|0
#4=0.0|0
#5=0.0|0
#6=0.0|0
#7=0.0|0
}OFFS
VARV{
}VARV
VAR{
}VAR
SPEC{
}SPEC
OPTI{
}OPTI
LINK{
}LINK
PREV{
}PREV
SIDE#1{
W#81{ ::WTp #1=37 #2=32 #3=-13 #1002=5.0 #1001=0 }W
W#81{ ::WTp #1=8 #2=200 #3=-19 #1002=8.0 #1001=1 }W
W#1050{ ::WT2 #6=1 #8509=0 #8517=600 #8510=0 #8511=380 #8512=-8 #8514=1 #8515=1 #8525=0 #8526=0 #8527=0 }W
}SIDE
SIDE#2{
}SIDE
SIDE#3{
}SIDE
SIDE#4{
}SIDE
SIDE#5{
}SIDE
SIDE#6{
W#81{ ::WTp #1=50 #2=8 #3=-34 #1002=8.0 #1001=0 }W
}SIDE
```

---

## 7. Ochiq savollar (foydalanuvchiga)

1. **Paz eni yozilmaydi** (`t=4/6/10.5` bir xil chiqadi). Stanok 10.5 mm LED pazini qanday kesadi — arra bitta o'tish qiladimi (unda paz 4 mm bo'lib qoladi)? `#8514`, `#8515`, `#6`, `#8525–#8527` qaysi biri en/o'tishlar soni/korreksiya? (TPA EDICAD qo'llanmasi yoki stanokdagi W#1050 parametrlar oynasi skrini kerak.)
2. **Qirra teshigi `#2 = dz − z`** (TPA, Homag), Startech esa `z`. XNC `z` qaysi yuzadan o'lchanadi, stanokda teshik qaysi balandlikda tushadi? (18 mm detal, `m=false` — 3166 `14_017`.)
3. **Freza korreksiyasi `#40`:** XNC `c=1` → `#40=1`, `c=2` → `#40=2`. TPA da 1 — chap yoki o'ng? (Homag fork `c=1 → WRKL` (chap) topdi; `J_XNC_SPEC.md` da «1 — o'ng» yozilgan — ziddiyat.)
4. **`#36=4`** — freza radiusimi (Ø8/2) yoki kirish/chiqish turi? Boshqa freza (Ø6, Ø10) yoki `in/out` boshqa qiymatli namuna kerak.
5. Orqa tomonda qirra teshigi va frezalash bo'lsa (namunada yo'q) — SIDE#4↔#6 almashadimi, yoy yo'nalishi `#34` teskari bo'ladimi? `SIDE#2` (pastki yuz) qachon ishlatiladi — ikki tomonlama stanokmi?
6. Detal stolga qanday qo'yiladi (TPA SIDE#3 = XNC y=0 qirrasi = `elt`)? Stanok bazasi qaysi burchak?
7. Qiya paz, teshik massivi (`ac>1`), R bilan berilgan yoy, `MillRect/Ellipse` uchun namuna yo'q — kerak bo'lsa test detali bilan GibLab/stanokdan namunalar.
