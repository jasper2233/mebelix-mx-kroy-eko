# Nanxing SyntecCad — `.scx` (XML `Root/Project/Panels/Panel`) postprotsessori

> Manba: korxonaning o'z namunalari — `post prtsessorlar/PRISADKA APPARAT/Nanxing SyntecCad/<NNNN>_<mijoz>.zip`
> (15 buyurtma, **1009 fayl**) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` XNC operatsiyalari.
> Faqat chiqish fayllari va loyiha XML o'qildi. Mijoz ismlari — «mijoz».
>
> **Holat: to'liq tushunilgan (teshik, paz, frezalash, kromka konturi, orqa tomon).** Prototip writer (scratchpad
> `gen.py::nanxing`), 3173 dan tashqari: frezalashsiz detallar **900/900 bayt-ma-bayt**; frezalashli detallar 58 ta —
> `<Outline>` (frezalangan kontur) va yoy `Angle` ning oxirgi raqamlaridagi suzuvchi nuqta shovqinidan tashqari hammasi mos
> (2 tasi to'liq bayt-ma-bayt). 3173 — loyiha eksportdan keyin o'zgargan.

> **Yangilanish 2026-10-22 (stanok xatosi):** korxonaning Nanxing **MH2026_Drill 3.1.2.4** stanogi MX fayllarini
> «Cad file read failed. Mill path node not on panel outline» bilan rad etdi. Sabab — quyidagi tavsif onlayn tizimning
> 2021 namunalaridan olingan; stanokda ishlayotgan fayllar esa lokal tizimning yangi (2023-05-17) versiyasidan chiqadi va
> formati boshqacha. Korxona namunasi (`uzgarishlar/0004 Test.zip` + `0004 Test (2).project`, 8 fayl) bo'yicha
> generator qayta yozildi — **8/8 bayt-ma-bayt** (`Root@Cad` dan tashqari), tekshiruv `tools/bench/pp_nanxing_check.py`.
>
> | | Eski (2021, onlayn) — MX avval shuni yozardi | Yangi (stanok qabul qiladi) — MX endi |
> |---|---|---|
> | Qatorlar | butun fayl bitta qatorda | sarlavhadan keyin `
`, har element alohida qatorda `

` |
> | `Panel@ID` | XNC kodi | mahsulot kodi + `_` + detal kodi (`000401_01_004`) |
> | `Name` | o'zgarishsiz | lotinda: kirill transliteratsiya, «–» → «-» (`в„–01_004` → `v„-01_004`) |
> | `<Outline>` | frezalangan kontur (yoylar vatarlarda) + 20/30 mm ramka | doim 4 nuqta: (L,0) (L,W) (0,W) (0,0) |
> | Kromka | ramkadagi 30 mm «bo'rtiq» | `<EdgeGroup><Edge CentralAngle="0" Face Pre_Milling="1.0" Thickness X Y/>` (o'ng 3, yuqori 1, chap 4, past 2; X/Y — tomon boshi) |
> | Freza | detal cheti + `ToolOffset` 左/右 (korreksiyani stanok qiladi) | asbob MARKAZI yo'li (d/2 korreksiya tomoniga, yoy radiusi ± d/2), `ToolOffset="中"` |
> | Yoy `Angle` | to'liq double (`90.0`) | 3 kasrgacha (`90`, `-90`) |
> | `ID` | yo'q | har amalda 1000, 1001 … |
> | `IsGenCode` | yuz teshigi 2, qolganlari 0 | hammasi 2 |
>
> Namunada bo'lmagan holatlar — quyidagi MES qoidalari bo'yicha.
>
> **Korxona MES dasturi bilan solishtiruv (2026-10-22).** MES'dagi Nanxing generatori (`MebeliX-Mes-System`,
> `services/giblab/scx.py`, `docs/10-giblab-reference.md` §7.2) 87 loyiha / 5286 eksport fayli korpusidan o'rganilgan.
> Undan MX ga qo'shilgan qoidalar:
> * **orqa tomon dasturi alohida fayl emas** — amallari `Face="6"` bilan old tomon fayliga (X ag'darilmaydi; qirra
>   teshigi Z = qalinlik − z); fayl nomi — old tomon XNC kodi (faqat orqasi tanlansa ham);
> * har dasturda tartib: qirra teshiklari → yuza teshiklari → pazlar → frezalar; paz doim `ToolOffset="中"`;
> * butun kontur bitta chet bo'ylab va `c=2` — xom yo'l, `ToolOffset="右"`;
> * qo'shqavat detal (dz ≈ 2 × list qalinligi yoki 32): `Thickness` va qirra Z ikki baravar kichik, yuza teshigi
>   chuqurligi bir qatlamga kam, freza chuqurligi ≤ eksport qalinligi;
> * `mirHor` / `mirVert` geometriyaga qo'llanadi; `EdgeGroup` tartibi l, r, t, b, `X="0" Y="0"`, kromka qalinligi 0
>   bo'lsa `1.0`.
>
> Ikkala generator 141 korxona loyihasida (6192 detal fayli) solishtirildi: **6162 aynan bir xil**. Qolgan 30 tasi:
> * 15 — keskin (urinma bo'lmagan) burchakda MX freza markazini r = d/2 yoy bilan aylantiradi, MES qo'shmaydi
>   (MES hujjatida ham cheklov sifatida yozilgan) — MX to'g'ri;
> * 11 — cho'ntak (`c=3`, GibLab yordami: «3 — Карман»): MES uni `c=1` kabi suradi — yo'nalishga qarab konturni
>   TASHQARIGA chiqaradi (masalan Y = −1, detaldan tashqarida) yoki yopilish burchagida 2 mm ortiqcha kesadi. MX konturni
>   ichkariga suradi va boshi/oxirini kesishtiradi (8×4 o'yiq d=4 freza bilan aynan 8×4) — **MES xatosi**;
> * 3 — 0.005 mm yaxlitlash (MES `%g`, MX 3 kasr — namunadagidek);
> * 1 — detal tashqarisidagi teshik (Y < 0): MES yozadi, MX yozmaydi (ogohlantiradi).
>
> Shu solishtiruvda **MX'ning umumiy xatosi** topildi: dasturda `<var>` siz ishlatilgan `throughCutDepth` (korpusda 42
> loyiha) MX'da «aniqlanmagan» hisoblanib, freza / paz **barcha formatlarda va chizmada tashlab yuborilardi**. Endi
> standartlar: `throughBoreDepth` = dz+3, `throughCutDepth` = dz+3, `contMillDepth` = dz (dastur e'lon qilsa — o'shanisi).
>
> Ochiq: cho'ntak uchun stanok `Pocket="1"` ni kutadimi (namuna yo'q); paz `Type 4` va orqa tomon — korxona namunasida
> yo'q (MES qoidasi). Quyidagi bo'limlar — eski ko'rinish tavsifi (tarix uchun).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Fayl | **bitta XNC operatsiyasi = bitta `.scx`**; nomi `<XNC kodi>.scx` |
| Takror kod | `<kod> (1).scx`, `<kod> (2).scx` … (loyiha XML tartibida) |
| Orqa tomon | alohida XNC (`side="false"`), kod `…_2` |
| Format | XML, `<?xml version="1.0" encoding="UTF-8"?>`, **butun fayl bitta qatorda** (qator oxiri yo'q, oxirida ham) |
| Kodlash | UTF‑8 BOM'siz; 102 faylda ASCII dan tashqari belgi — faqat `ToolOffset` qiymatlari (`中`/`左`/`右`) |
| Sonlar | koordinata/o'lcham/chuqurlik — **3 kasrgacha** yaxlitlab, ortiqcha nollarsiz (`141.101`, `-5.795`, `0`); yoy `Angle` — to'liq double (`89.99999999999999`, `90.0`, `-90.27025134531921` — Java `Double.toString` uslubi); chiziqda `Angle="0"` |
| Atributlar | har elementda **alifbo tartibida** (`Depth, Diameter, Face, IsGenCode, Type, X, Y, Z`) |
| Birlik | mm |

---

## 2. Sintaksis

### 2.1 Tuzilma

```xml
<?xml version="1.0" encoding="UTF-8"?><Root Cad="Built in GibLab" version="2.0"><Project><Panels>
<Panel ID="<XNC kodi>" IsProduce="true" Length="L" MachiningPoint="1" Name="<detal nomi>" Thickness="T" Width="W">
<Outline><Point X=".." Y=".."/>…</Outline>
<Machines>
<Machining …/>  …                       ← XNC dasturidagi tartib AYNAN saqlanadi (958/958)
</Machines></Panel></Panels></Project></Root>
```
(ko'rinish uchun qatorlarga bo'lingan; haqiqiy faylda hammasi bitta qator.)

| Atribut | Ma'no |
|---|---|
| `Root@Cad="Built in GibLab"`, `version="2.0"` | doimiy (❓ Q1 — MebeliX faylga «GibLab» yozmaydi) |
| `Panel@ID` | XNC kodi; `Name` — `operation@typeName`; `Length/Width/Thickness` — L, W, T |
| `IsProduce="true"`, `MachiningPoint="1"` | doimiy |

### 2.2 Koordinata tizimi

* GibLab XNC xom koordinatasi (= MebeliX `machine_program()`): x o'ngga, y pastga (yuqori qirradan), `bt` — y=0,
  `bb` — y=W, qirra teshigi `z` — pastki yuzadan.
* Nanxing: **X = x**, **Y = W − y** (Y akslangan: koordinata boshi pastki-chap burchak, Y yuqoriga), qirra teshigida
  **Z = z_b** (pastki yuzadan, `m=true` → T/2) — boshqa stanoklardan farqli, `T − z` emas.
* Akslanish (Y) tufayli freza korreksiyasi tomoni almashadi (`c=1` o'ng → `左` chap).
* Orqa tomon: avval `x → L − x` (X akslanadi), Y formula o'zgarmaydi; qirra tomonlari L↔R (`Face 3↔4`, kontur
  «bo'rtiq»lari) almashadi.

### 2.3 Teshiklar

```xml
<Machining Depth="dp" Diameter="d" Face="5" IsGenCode="2" Type="2" X="x" Y="W−y"/>          ← vertikal (bf)
<Machining Depth="dp" Diameter="d" Face="4" IsGenCode="0" Type="1" X="0" Y="W−y" Z="z_b"/>   ← qirra
```
| XNC | Type | Face | X | Y | Z |
|---|---|---|---|---|---|
| `bf` | 2 | **5** (yuz) | x | W − y | — |
| `bl` (x=0) | 1 | **4** | 0 | W − y | z_b |
| `br` (x=L) | 1 | **3** | L | W − y | z_b |
| `bt` (y=0) | 1 | **1** | x | W | z_b |
| `bb` (y=W) | 1 | **2** | x | 0 | z_b |

`IsGenCode`: vertikal teshikda `2`, qolgan hammasida `0` (6132/2730). O'tuvchi teshik chuqurligi (`dz+3`=19) o'zgarishsiz.

### 2.4 Paz (`Type 4`)

```xml
<Machining Depth="dp" EndX="x2" EndY="W−y2" EndZ="T" Face="5" IsGenCode="0" ToolOffset="中" Type="4" Width="t" X="x1" Y="W−y1" Z="T"/>
```
`Z`/`EndZ` — yuqori yuza balandligi (T), `Depth` — paz chuqurligi, `Width` — paz eni. `ToolOffset`: `c=0` → `中`
(markaz; namunada hamma 60 paz). Asbob nomi chiqmaydi.

### 2.5 Frezalash (`Type 3`)

```xml
<Machining Closed="0" Depth="dp" Diameter="D_asbob" Face="5" IsGenCode="0" Pocket="0" ToolOffset="左" Type="3" X="x0" Y="W−y0">
  <Lines>
    <Line Angle="0" EndX="x1" EndY="W−y1" LineID="0"/>                   ← chiziq
    <Line Angle="89.99999999999999" EndX="x2" EndY="W−y2" LineID="1"/>   ← yoy: Angle = burilish burchagi (°)
  </Lines>
</Machining>
```
* `X/Y` — `ms` nuqtasi; har `ml`/`mac` — bitta `Line`, `LineID` 0 dan.
* Koordinatalar — **kontur chizig'i** (asbob markazi emas); korreksiyani stanok qiladi:
  `ToolOffset`: **`c=1` → `左`, `c=2` → `右`, `c=0` → `中`** (44 + 21 kontur).
* Yoy: `Angle` = markaz atrofidagi burilish burchagi gradusda, **ishora = XNC `dir`**: `dir="true"` (MebeliX
  `clockwise`) → musbat, `false` → manfiy (51/51). Markaz va radius yozilmaydi — boshlang'ich, oxirgi nuqta va burchakdan
  aniqlanadi. Burchak qiymati: `degrees(atan2(oxir−markaz) − atan2(bosh−markaz))`, `dir` ga ko'ra ±360 bilan
  to'g'rilangan; oxirgi 1–2 raqam GibLab hisobidan farq qilishi mumkin (suzuvchi nuqta) — stanok uchun ahamiyatsiz.
* `Closed="0"`, `Pocket="0"` — namunada doim (65/65); yopiq kontur yoki cho'ntak (`C=3`) qanday yozilishi ❓ Q3.
* `Depth` = `ms@dp` (`contMillDepth = dz`), `Diameter` = asbob diametri.

### 2.6 `<Outline>` — detal konturi va kromka belgisi

Frezalashsiz detal uchun **31 nuqta** (frezasiz 951 dasturning 938 tasida qolipga aynan mos; qolgan 13 — 3173 va
yuz tomonida frezasi bor detalning orqa tomon fayllari):
```
(0,0) (L,0) (L,W) (0,W) (0,W) (0,0)                         ← detal (Nanxing koordinatasida)
(0,−20) (L+20,−20) (L+20,W+20) (−20,W+20) (−20,0)           ← 20 mm tashqi ramka
(−oL,0) (−oL,W) (−20,W) (−20,W+20)                          ← chap tomon
(−20,W+20) (0,W+20) (0,W+oT) (L,W+oT) (L,W+20) (L+20,W+20)  ← Y=W tomon (XNC y=0, ya'ni `elt`)
(L+20,W) (L+oR,W) (L+oR,0) (L+20,0) (L+20,−20)              ← o'ng tomon
(L,−20) (L,−oB) (0,−oB) (0,−20) (0,0)                       ← Y=0 tomon (XNC y=W, ya'ni `elb`)
```
bu yerda `o = 30` agar shu tomonda kromka bo'lsa, aks holda `20`. Tomon ↔ kromka: chap = `ell`, o'ng = `elr`,
Y=W = `elt`, Y=0 = `elb`; **orqa tomonda chap/o'ng almashadi** (`ell`↔`elr`).

Detalda (uning istalgan XNC dasturida, orqa tomon faylida ham) o'tuvchi frezalash bo'lsa, birinchi 6 nuqta o'rniga
kesilgandan keyingi haqiqiy kontur yoziladi (yoylar vatarlarga bo'lingan: r=6 → 5 bo'lak, r=10 → 7 bo'lak), ramka qismi
o'zgarmaydi. Bu GibLab geometriya natijasi (❓ Q2).

---

## 3. MebeliX XNC → Nanxing xaritasi

`machine_program()`: `L = size.length`, `W = size.width`, `T = blank.thickness`, `back = face_back`,
`fx(x) = back ? L − x : x`, `fy(y) = W − y`, `z_b = middle ? T/2 : z`.

| MebeliX | Nanxing |
|---|---|
| `drill front` | `Type 2 Face 5 IsGenCode 2`, X=fx(x), Y=fy(y) |
| `drill left/right/top/bottom` | `Type 1`, Face 4/3/1/2 (orqada 4↔3), Z = z_b |
| `groove` | `Type 4`, start/end, `Z=EndZ=T`, Width = `width`, ToolOffset (`correction` 0/1/2 → 中/左/右) |
| `mill_start` + `mill_line`/`mill_arc` | `Type 3` + `Lines`; ToolOffset (orqada 左↔右 — taxmin); yoy `Angle = ±burchak` (clockwise → +; orqada ishora teskari — taxmin) |
| `rect` / `ellipse` | `path` → Line (Angle 0) / yoy segmentlari |
| kromka (`edges`) | `Outline` 31 nuqtali qolip (§2.6) |

### 3.1 Tekshirilgan misollar

**A. `316701_01_001` (2098×597×16, `elb`)** — `bf x=593 y=70 dp=19` → `X="593" Y="527" Depth="19"`; `br y=70` →
`Face="3" X="2098" Y="527" Z="8"`; `bl y=527` → `Face="4" X="0" Y="70"`; Outline: faqat Y=0 tomonida `−30` bo'rtiq.

**B. `316601_14_017` (68×1581×18)** — `bl y=70 z=8 m=false` → `Face="4" X="0" Y="1511" Z="8"` (z o'zgarishsiz);
`br y=50 m=true` → `Face="3" X="68" Y="1531" Z="9"`.

**C. `316601_03_005` (160×520)** — `bt x=80` → `Face="1" X="80" Y="520"`; `bb x=80` → `Face="2" X="80" Y="0"`.

**D. `317701_01_002` (704×500, freza `c=1`)** — `<Machining Closed="0" Depth="16" Diameter="8" … ToolOffset="左" Type="3" X="645.5" Y="-10">`
(510 → 500−510), `Line Angle="0" EndX="645.5" EndY="20"`, `Line Angle="89.99999999999999" EndX="651.5" EndY="26"`
(`dir=true`), `Line Angle="0" EndX="714" EndY="26"`.

**E. `316601_13_008` (`dir=false`)** — `Line Angle="-90.27025134531921" EndX="300" EndY="0"`.

**F. `316601_00_010` (paz)** — `gr (141.5,0)→(141.5,1300) t=10.5 dp=10.5` → `Depth="10.5" EndX="141.5" EndY="0" EndZ="16" … Type="4" Width="10.5" X="141.5" Y="1300" Z="16"`;
orqa tomon `316801_02_008_2`: `(990,0)→(0,0)` → `X="0" Y="600" EndX="990" EndY="600"`.

**G. `317001_01_005_2` (orqa tomon)** — `bf x=243 y=698` → `X="453" Y="78"` (696−243, 776−698).

---

## 4. Doimiy va ma'lumotga bog'liq maydonlar

| Doimiy (1009/1009) | Ma'lumotga bog'liq |
|---|---|
| `Cad="Built in GibLab"`, `version="2.0"`, `IsProduce="true"`, `MachiningPoint="1"`, `Face="5"` (yuz/paz/freza), `IsGenCode` (2/0 turga qarab), `Closed="0"`, `Pocket="0"`, Outline ramkasi ofsetlari 20/30 | ID, Name, o'lchamlar, Outline (kromka va freza), barcha koordinatalar, `Face` (qirra), `Z`, `Depth`, `Diameter`, `Width`, `ToolOffset`, `Angle` |

---

## 5. Minimal anonim misol

Detal 600×400×16, `elb`: `bf (100,50) d=5 dp=12`, `bl y=40 m=true d=8 dp=30`, `gr (0,350)→(600,350) t=4 dp=8`,
`ms (550,−10) c=1 Mill8 dp=16 → ml (550,60) → mac (560,70) c(560,60) dir=false → ml (610,70)`.
Bitta qator (bu yerda o'qish uchun bo'lingan):
```xml
<?xml version="1.0" encoding="UTF-8"?><Root Cad="Built in GibLab" version="2.0"><Project><Panels>
<Panel ID="900101_01_001" IsProduce="true" Length="600" MachiningPoint="1" Name="01_001 detal" Thickness="16" Width="400">
<Outline><Point X="0" Y="0"/><Point X="600" Y="0"/><Point X="600" Y="400"/><Point X="0" Y="400"/><Point X="0" Y="400"/><Point X="0" Y="0"/>
<Point X="0" Y="-20"/><Point X="620" Y="-20"/><Point X="620" Y="420"/><Point X="-20" Y="420"/><Point X="-20" Y="0"/>
<Point X="-20" Y="0"/><Point X="-20" Y="400"/><Point X="-20" Y="400"/><Point X="-20" Y="420"/>
<Point X="-20" Y="420"/><Point X="0" Y="420"/><Point X="0" Y="420"/><Point X="600" Y="420"/><Point X="600" Y="420"/><Point X="620" Y="420"/>
<Point X="620" Y="400"/><Point X="620" Y="400"/><Point X="620" Y="0"/><Point X="620" Y="0"/><Point X="620" Y="-20"/>
<Point X="600" Y="-20"/><Point X="600" Y="-30"/><Point X="0" Y="-30"/><Point X="0" Y="-20"/><Point X="0" Y="0"/></Outline>
<Machines>
<Machining Depth="12" Diameter="5" Face="5" IsGenCode="2" Type="2" X="100" Y="350"/>
<Machining Depth="30" Diameter="8" Face="4" IsGenCode="0" Type="1" X="0" Y="360" Z="8"/>
<Machining Depth="8" EndX="600" EndY="50" EndZ="16" Face="5" IsGenCode="0" ToolOffset="中" Type="4" Width="4" X="0" Y="50" Z="16"/>
<Machining Closed="0" Depth="16" Diameter="8" Face="5" IsGenCode="0" Pocket="0" ToolOffset="左" Type="3" X="550" Y="410"><Lines>
<Line Angle="0" EndX="550" EndY="340" LineID="0"/><Line Angle="-90.0" EndX="560" EndY="330" LineID="1"/><Line Angle="0" EndX="610" EndY="330" LineID="2"/>
</Lines></Machining>
</Machines></Panel></Panels></Project></Root>
```

---

## 6. Noma'lumlar — foydalanuvchiga savollar

1. **Q1. `Cad="Built in GibLab"`** — SyntecCad bu atributni tekshiradimi? MebeliX qoidasi bo'yicha faylga «GibLab» yozilmaydi;
   `Cad="MebeliX"` yoki atributsiz fayl stanokda ochilishini sinab ko'rish kerak.
2. **Q2. `<Outline>`:** 20/30 mm ramka va «bo'rtiq»lar — kromka tomonini ko'rsatishmi (SyntecCad'da shunday konvensiya
   bormi)? Frezalangan konturni (geometriya yadrosi) aynan takrorlash shartmi yoki to'rtburchak yetadimi?
3. **Q3. `Closed`/`Pocket`:** yopiq kontur va cho'ntak (`C=3`) namunada yo'q — `Closed="1"`, `Pocket="1"` qachon?
4. **Q4. Orqa tomon:** faylda tomon belgisi yo'q, X akslangan; qirra teshigi/freza orqa tomonda namunada yo'q
   (Face 3↔4, `左`↔`右`, `Angle` ishorasi teskari — taxmin).
5. **Q5. Koordinata boshi:** Y akslangan (pastki-chap), qirra `Z` pastdan — stanokda bazalash burchagi tasdiqlansin.
6. **Q6.** Burish/ko'zgu, massiv teshiklar, `c≠0` paz namunada yo'q.
