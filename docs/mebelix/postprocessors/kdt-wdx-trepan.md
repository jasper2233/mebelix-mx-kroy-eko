# KDT WDX (trepan) — `.xml` (`AndersonXMLdata`) postprotsessori

> Manba: korxonaning o'z namunalari — `post prtsessorlar/PRISADKA APPARAT/KDT WDX trepan/<NNNN>_<mijoz>.zip` (15 buyurtma,
> **1009 fayl**) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` XNC operatsiyalari (1014 dastur).
> Faqat chiqish fayllari va loyiha XML o'qildi. Mijoz ismlari — «mijoz».
>
> **Holat: to'liq tushunilgan (teshik, paz, frezalash, orqa tomon).** Prototip writer (scratchpad `gen.py::kdt`)
> 3173 dan tashqari **958/958 faylni bayt-ma-bayt** qayta yasadi (frezalashli 58 fayl ham). 3173 — loyiha eksportdan
> keyin o'zgargan (27/51 mos).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Fayl | **bitta XNC operatsiyasi = bitta `.xml`**; nomi `<XNC kodi>.xml` (`316701_01_001.xml`) |
| Takror kod | `<kod> (1).xml`, `<kod> (2).xml` … (loyiha XML tartibida) |
| Orqa tomon | alohida XNC (`side="false"`), kod `…_2` |
| Format | XML, deklaratsiya `<?xml version="1.0" encoding="UTF-8"?>`, **har element alohida qatorda, indentatsiyasiz** |
| Kodlash | UTF‑8 (namunada faqat ASCII) |
| Qator oxiri | `CRLF`, oxirgi `</AndersonXMLdata>` dan keyin ham |
| Sonlar | nuqta `.`, 4 kasrgacha (yoy `Radius` — 5 kasrgacha), ortiqcha nollarsiz (`1505`, `-9.9996`, `298.29895`) |
| Birlik | mm |

---

## 2. Sintaksis

### 2.1 Tuzilma

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AndersonXMLdata>
<PANEL>
<PanelLength>L</PanelLength>
<PanelWidth>W</PanelWidth>
<PanelThickness>T</PanelThickness>
<PanelName>…</PanelName>            ← operation@typeName (detal nomi)
</PANEL>
<CAD>…</CAD>                         ← amallar, tartib: 1) vertikal teshiklar; 2) frezalash va paz (dastur tartibida);
…                                       3) Quadrant 1 (br); 4) Quadrant 2 (bl); 5) Quadrant 4 (bt); 6) Quadrant 3 (bb)
</AndersonXMLdata>
```
Fayl nomi (kod) faylning ichida yo'q. Material, kromka, tekstura yozilmaydi.

### 2.2 Koordinata tizimi

* GibLab XNC xom koordinatasi (= MebeliX `machine_program()`): x o'ngga, y pastga, `bt` — y=0 qirra, `bb` — y=W qirra,
  qirra teshigi `z` — pastki yuzadan (`m=true` → T/2).
* KDT: **X1 = L − x** (X **o'ng** qirradan o'lchanadi), **Y1 = y** (o'zgarmaydi), qirra teshigi **Z1 = T − z_b**
  (yuqori yuzadan).
* Orqa tomon (`side=false`): avval `x → L − x`, so'ng formula → **X1 = x**. Freza `Correction` va yoy `Direction` ham
  akslanishi kerak (namunada orqa tomonda freza yo'q — taxmin).

### 2.3 Vertikal teshik (`TypeNo 1`)

```xml
<CAD>
<TypeNo>1</TypeNo>
<TypeName>Vertical Hole</TypeName>
<PlaneID>0</PlaneID>
<Quadrant>1</Quadrant>
<X1>L−x</X1>
<Y1>y</Y1>
<Depth>dp</Depth>              ← o'tuvchi teshik dz+3 = 19 o'zgarishsiz
<Diameter>d</Diameter>
<HoleNo>1</HoleNo>
<IntervalX>0</IntervalX>
<IntervalY>0</IntervalY>
<IntervalZ>0</IntervalZ>
<Mirror>0</Mirror>
</CAD>
```

### 2.4 Gorizontal teshik (`TypeNo 2`, `PlaneID 2`)

| XNC | Quadrant | X1 | Y1 | Element tartibi |
|---|---|---|---|---|
| `br` (x=L) | **1** | `0` | y | `PlaneID, X1, Quadrant, Y1, Z1, …` |
| `bl` (x=0) | **2** | `L` | y | `PlaneID, X1, Quadrant, Y1, Z1, …` |
| `bb` (y=W) | **3** | L − x | `W` | `PlaneID, Quadrant, X1, Y1, Z1, …` |
| `bt` (y=0) | **4** | L − x | `0` | `PlaneID, Quadrant, X1, Y1, Z1, …` |

```xml
<CAD>
<TypeNo>2</TypeNo>
<TypeName>Horizontal Hole</TypeName>
<PlaneID>2</PlaneID>
<X1>0</X1>                     ← br/bl da X1 Quadrant'dan OLDIN, bt/bb da KEYIN (aynan shunday, 2605/2605)
<Quadrant>1</Quadrant>
<Y1>70</Y1>
<Z1>8</Z1>                     ← T − z_b
<Depth>34</Depth>
<Diameter>4.5</Diameter>
<HoleNo>1</HoleNo>
<IntervalX>0</IntervalX>
<IntervalY>0</IntervalY>
<IntervalZ>0</IntervalZ>
<Mirror>0</Mirror>
</CAD>
```
`Quadrant` — teshik qirrasiga mos «chorak» (1 = X1=0 qirra, 2 = X1=L, 3 = Y1=W, 4 = Y1=0). Vertikal teshiklarda doim 1.

### 2.5 Paz (`TypeNo 3`, `TypeName Groove`)

```xml
<CAD>
<TypeNo>3</TypeNo>
<TypeName>Groove</TypeName>
<BeginX>L−x1</BeginX>
<BeginY>y1</BeginY>
<EndX>L−x2</EndX>
<EndY>y2</EndY>
<Width>t</Width>               ← paz eni (asbob diametri emas)
<Correction>c</Correction>     ← XNC c (namunada hamma 60 pazda 0)
<UseSaw>1</UseSaw>             ← doimiy
<Depth>dp</Depth>
</CAD>
```

### 2.6 Frezalash: chiziq (`TypeNo 3`, `TypeName Line`) va yoy (`TypeNo 4`, `Arc`)

Kontur (`ms` + `ml`/`mac`) har segmenti alohida `CAD`; boshlang'ich nuqta — oldingi segment oxiri (`ms` nuqtasidan).
Koordinatalar — **kontur (detal chizig'i), asbob markazi emas**; korreksiyani stanok o'zi qiladi.
```xml
<CAD>
<TypeNo>3</TypeNo>
<TypeName>Line</TypeName>
<BeginX>L−x0</BeginX>
<BeginY>y0</BeginY>
<EndX>L−x1</EndX>
<EndY>y1</EndY>
<Width>D_asbob</Width>         ← Mill8 → 8
<Correction>…</Correction>
<Depth>dp</Depth>
</CAD>
<CAD>
<TypeNo>4</TypeNo>
<TypeName>Arc</TypeName>
<StartX>…</StartX>
<StartY>…</StartY>
<EndX>…</EndX>
<EndY>…</EndY>
<Radius>r</Radius>             ← |oxirgi nuqta − markaz|, 5 kasr; markaz yozilmaydi
<Direction>0|1</Direction>
<Correction>…</Correction>
<Width>D_asbob</Width>
<Depth>dp</Depth>
</CAD>
```
* `Correction`: X akslangani uchun tomon almashadi — **XNC `c=1` (o'ng) → `2`, `c=2` (chap) → `1`**, `c=0` → `0`
  (44 + 21 kontur tekshirildi). Orqa tomonda (ikki marta aks) — almashmaydi (taxmin).
* `Direction`: **XNC `dir="true"` (MebeliX `clockwise=True`, ekranda soat bo'yicha) → `0`; `dir="false"` → `1`** (51/51 yoy).
  KDT tekisligida (X akslangan) `0` = matematik ma'noda soat bo'yicha (Y yuqoriga deb qaralganda).
* Yoy yarim aylanadan katta bo'lishi namunada yo'q (eng kattasi ≈ 90.3°) — `Radius` ishorasi bilan katta yoy
  belgilanadimi, noma'lum (❓ Q3).
* `in/out` (kirish/chiqish), `sdp/sxy` chiqmaydi.

---

## 3. MebeliX XNC → KDT xaritasi

`machine_program()` natijasi: `L = size.length`, `W = size.width`, `T = blank.thickness`, `back = face_back`,
`fx(x) = back ? x : L − x`, `z_b = middle ? T/2 : z`.

| MebeliX | KDT |
|---|---|
| `drill front` | `TypeNo 1`, X1=fx(x), Y1=y, Depth=depth, Diameter=d |
| `drill right` / `left` | `TypeNo 2`, Quadrant 1 / 2, X1 = 0 / L, Y1 = y, Z1 = T − z_b |
| `drill top` (y=0) / `bottom` (y=W) | Quadrant 4 / 3, X1 = fx(x), Y1 = 0 / W |
| `groove` | `TypeNo 3 Groove`, Begin/End = (fx, y), Width = `width`, Correction = `correction`, UseSaw 1 |
| `mill_start` + `mill_line` | `TypeNo 3 Line` (har segment) |
| `mill_arc` | `TypeNo 4 Arc`, Radius, Direction = clockwise ? 0 : 1 |
| `rect` / `ellipse` | `path` ni Line/Arc ga yoyish (ellips — ko'p qisqa chiziq) |
| `AC>1` | alohida teshiklar (`HoleNo/Interval*` massiv maydonlari namunada doim 1/0 — ❓ Q4) |

### 3.1 Tekshirilgan misollar

**A. `316701_01_001` (2098×597×16)** — `bf x=593 y=70 dp=19` → `X1 1505, Y1 70, Depth 19, Diameter 8`;
`br y=70` → `X1 0, Quadrant 1, Y1 70, Z1 8, Depth 34`; `bl y=70` → `X1 2098, Quadrant 2`.

**B. `317701_01_002` (704×500, freza `c=1 Mill8`)** — `ms (645.5,510) → ml (645.5,480)` →
`Line Begin (58.5,510) End (58.5,480) Width 8 Correction 2 Depth 16`; `mac → (651.5,474) c(651.5,480) dir=true` →
`Arc Start (58.5,480) End (52.5,474) Radius 6 Direction 0 Correction 2`; `ml (714,474)` → `Line … End (-10,474)`.

**C. `316601_14_017` (68×1581×18)** — `bl y=70 z=8 m=false` → `X1 68, Quadrant 2, Y1 70, Z1 10` (=18−8);
`br y=50 z=9 m=true` → `Z1 9`.

**D. `317001_01_005` (696×776, `bt`)** — `bt x=556` → `Quadrant 4, X1 140, Y1 0`; `316601_01_001` `bb x=785.99` →
`Quadrant 3, X1 464.01, Y1 500`.

**E. `317001_01_005_2` (orqa tomon)** — `bf x=243 y=698 d=3 dp=1.5` → `X1 243` (akslanmagan ko'rinadi, chunki ikki
marta aks); `316801_02_008_2` paz `(990,0)→(0,0)` → `BeginX 990 … EndX 0`.

**F. `316601_13_008` (yoy `dir=false`)** — `Arc … Radius 298.29895 Direction 1 Correction 2`.

---

## 4. Doimiy va ma'lumotga bog'liq maydonlar

| Doimiy (1009/1009) | Ma'lumotga bog'liq |
|---|---|
| XML deklaratsiyasi, `PlaneID` (0 vertikal / 2 gorizontal), vertikalda `Quadrant 1`, `HoleNo 1`, `IntervalX/Y/Z 0`, `Mirror 0`, `UseSaw 1` | `Panel*`, barcha koordinatalar, `Quadrant` (qirra), `Depth`, `Diameter`, `Width`, `Correction`, `Radius`, `Direction` |

---

## 5. Minimal anonim misol

Detal 600×400×16: `bf (100,50) d=5 dp=12`, `gr (0,350)→(600,350) t=4 dp=8`,
`ms (550,−10) c=1 Mill8 dp=16 → ml (550,60) → mac (560,70) c(560,60) dir=false → ml (610,70)`, `bl y=40 m=true d=8 dp=30`.
Writer natijasi (`CRLF`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<AndersonXMLdata>
<PANEL>
<PanelLength>600</PanelLength>
<PanelWidth>400</PanelWidth>
<PanelThickness>16</PanelThickness>
<PanelName>01_001 detal</PanelName>
</PANEL>
<CAD>
<TypeNo>1</TypeNo>
<TypeName>Vertical Hole</TypeName>
<PlaneID>0</PlaneID>
<Quadrant>1</Quadrant>
<X1>500</X1>
<Y1>50</Y1>
<Depth>12</Depth>
<Diameter>5</Diameter>
<HoleNo>1</HoleNo>
<IntervalX>0</IntervalX>
<IntervalY>0</IntervalY>
<IntervalZ>0</IntervalZ>
<Mirror>0</Mirror>
</CAD>
<CAD>
<TypeNo>3</TypeNo>
<TypeName>Groove</TypeName>
<BeginX>600</BeginX>
<BeginY>350</BeginY>
<EndX>0</EndX>
<EndY>350</EndY>
<Width>4</Width>
<Correction>0</Correction>
<UseSaw>1</UseSaw>
<Depth>8</Depth>
</CAD>
<CAD>
<TypeNo>3</TypeNo>
<TypeName>Line</TypeName>
<BeginX>50</BeginX>
<BeginY>-10</BeginY>
<EndX>50</EndX>
<EndY>60</EndY>
<Width>8</Width>
<Correction>2</Correction>
<Depth>16</Depth>
</CAD>
<CAD>
<TypeNo>4</TypeNo>
<TypeName>Arc</TypeName>
<StartX>50</StartX>
<StartY>60</StartY>
<EndX>40</EndX>
<EndY>70</EndY>
<Radius>10</Radius>
<Direction>1</Direction>
<Correction>2</Correction>
<Width>8</Width>
<Depth>16</Depth>
</CAD>
<CAD>
<TypeNo>3</TypeNo>
<TypeName>Line</TypeName>
<BeginX>40</BeginX>
<BeginY>70</BeginY>
<EndX>-10</EndX>
<EndY>70</EndY>
<Width>8</Width>
<Correction>2</Correction>
<Depth>16</Depth>
</CAD>
<CAD>
<TypeNo>2</TypeNo>
<TypeName>Horizontal Hole</TypeName>
<PlaneID>2</PlaneID>
<X1>600</X1>
<Quadrant>2</Quadrant>
<Y1>40</Y1>
<Z1>8</Z1>
<Depth>30</Depth>
<Diameter>8</Diameter>
<HoleNo>1</HoleNo>
<IntervalX>0</IntervalX>
<IntervalY>0</IntervalY>
<IntervalZ>0</IntervalZ>
<Mirror>0</Mirror>
</CAD>
</AndersonXMLdata>
```

---

## 6. Noma'lumlar — foydalanuvchiga savollar

1. **Q1. Bazalash:** X1 o'ng qirradan (L−x), Y1 — XNC dagi kabi (yuqori qirradan). Stanokda detal qaysi burchak bilan
   tirgakka qo'yiladi? `Quadrant` nomi shu bilan bog'liqmi? Sinov detali bilan tasdiqlash kerak.
2. **Q2. Orqa tomon:** faylda tomon belgisi yo'q, faqat X akslangan. Operator detalni tik o'q atrofida ag'daradimi?
   Orqa tomonda qirra teshigi/freza namunada yo'q — Quadrant 1↔2, `Correction` va `Direction` qanday bo'ladi?
3. **Q3. Yoy:** markaz yozilmaydi, faqat `Radius` + `Direction` — 180° dan katta yoy uchun manfiy radius kerakmi?
   To'liq aylana (Start=End) qanday yoziladi?
4. **Q4. Massiv:** `HoleNo`, `IntervalX/Y/Z`, `Mirror` — teshik qatori (masalan 32 mm qadam) uchun ishlatsa bo'ladimi
   yoki har teshik alohida yozilsinmi (GibLab doim alohida yozadi)?
5. **Q5. Paz korreksiyasi** `c≠0` va freza `C=3` (cho'ntak) namunada yo'q.
6. **Q6.** `Width` frezada asbob diametri, pazda paz eni — stanok asbobni diametr bo'yicha o'zi tanlaydimi?
7. **Q7.** Burish/ko'zgu (`turn≠0`, `mirHor`) namunada yo'q.
