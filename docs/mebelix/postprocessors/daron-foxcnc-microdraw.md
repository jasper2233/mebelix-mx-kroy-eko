# Daron FoxCNC (MicroDraw) — `.ban` (MicroDrawBan_XML 3.0) postprotsessori

> Manba: korxonaning o'z namunalari — `post prtsessorlar/PRISADKA APPARAT/Daron FoxCNC, MicroDraw/<NNNN>_<mijoz>.zip`
> (15 buyurtma, **1009 fayl**) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` dagi XNC
> operatsiyalari (3183 — `<NNNN> <mijoz>.project`). Faqat chiqish fayllari va loyiha XML o'qildi. Mijoz ismlari — «mijoz».
>
> **Holat: to'liq tushunilgan (teshik, paz, kromka, orqa tomon — bayt-ma-bayt), frezalash — geometrik jihatdan tushunilgan.**
> Prototip writer (scratchpad `gen.py::daron`) bilan solishtiruv (3173 dan tashqari, u loyiha eksportdan keyin o'zgargan):
> * frezalashsiz detallar — **900/900 fayl bayt-ma-bayt bir xil** (3183 da `Grain` loyiha faylidagi `txt` dan farq qiladi — §6 Q4);
> * frezalashli detallar (58 fayl) — `<Outline>` va freza `SlotL/SlotA` qatorlaridan tashqari hammasi bayt-ma-bayt;
>   freza trayektoriyasi (asbob markazi, d/2 siljitilgan) 47/53 faylda ±0.002 mm aniqlikda qayta hisoblandi, qolgan 6 tasi
>   bitta detal (`316601_13_008`, noto'g'ri tutashgan yoy) — §2.6.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Arxiv | bitta buyurtma = `<buyurtma>_<mijoz>.zip`, ichida papkasiz tekis ro'yxat |
| Fayl | **bitta XNC operatsiyasi = bitta `.ban`** (detalning bitta tomoni). XNC si yo'q detal uchun fayl yo'q |
| Nom | `<XNC operatsiya kodi>.ban` — `operation@code` o'zgarishsiz (`316701_01_001.ban`). Kod «Кодирование» shablonidan: odatda `<buyurtma 4><mahsulot 2>_<modul>_<detal>`, ba'zan standart shablon `01_041x047x0` |
| Takror kod | bir xil kodli 2-, 3-… XNC (loyiha XML tartibida) — `<kod> (1).ban`, `<kod> (2).ban` (80 juft tarkibi turlicha bo'lgan guruhda tasdiqlandi) |
| Orqa tomon | alohida XNC (`side="false"`), kodi `…_2` bilan tugaydi: `316701_01_018_2.ban` |
| Format | XML ko'rinishidagi matn, **XML deklaratsiyasisiz** (`<?xml …?>` yo'q), indentatsiyasiz, har element alohida qatorda |
| Kodlash | namunalarda faqat ASCII; kirill nom/material uchun kodlash noma'lum (❓ Q6) |
| Qator oxiri | `CRLF`, oxirgi `</MicroDrawBan_XML>` dan keyin ham `CRLF` |
| Sonlar | nuqta `.`; 5 kasrgacha yaxlitlanadi, ortiqcha nollar va nuqta tashlanadi (`-1505`, `-54.3541`, `-67.97719`); istisno: `HoleV@Start` dagi Z har doim `0.00` |
| Birlik | mm |

---

## 2. Sintaksis

### 2.1 Tuzilma

```
<MicroDrawBan_XML Version="3.0" Time="YYYY/MM/DD HH:MM:SS" Source="" SourceType="BAN">
<Plane Name="…" Code="…" Material="…" PlaneNo=" " Width="L" Hight="W" Thickness="T" Grain="DIR_NONE|DIR_HOR" EdgeFBLR="f ,b ,l ,r" PlaneSize="1" MachineBase="-1">
<Outline>
<Point Value="X Y 0"/>                 ← detal konturi (yopiq, birinchi nuqta oxirida takrorlanadi)
</Outline>
<HoleV …/>  …                          ← 1) vertikal teshiklar (bf) — dastur tartibida
<SlotL …/> <SlotA …/> …                ← 2) paz (gr) va frezalash (ms/ml/mac) — dastur tartibida
<HoleH Face="L" …/> …                  ← 3) chap qirra (bl)
<HoleH Face="R" …/> …                  ← 4) o'ng qirra (br)
<HoleH Face="D" …/> …                  ← 5) y=0 qirra (bt)
<HoleH Face="U" …/> …                  ← 6) y=W qirra (bb)
</Plane>
</MicroDrawBan_XML>
```

Guruhlar tartibi qat'iy (1009/1009), guruh ichida — XNC dasturidagi tartib (958/958 tekshirildi).

| Atribut | Ma'no / manba |
|---|---|
| `Version="3.0"`, `Source=""`, `SourceType="BAN"` | doimiy |
| `Time` | eksport vaqti (`2026/09/30 09:40:42`) — ma'lumotga bog'liq emas |
| `Plane@Name` | `operation@typeName` (= detal nomi, masalan `01_001 bok`) |
| `Plane@Code` | XNC kodi (fayl nomi, ` (n)` qo'shimchasiz) |
| `Material` | detal joylashgan CS operatsiyasining materiali (`good typeId="sheet"@name`) |
| `PlaneNo=" "` | doimiy (bitta probel) |
| `Width`, `Hight` (sic!), `Thickness` | L = `dx`, W = `dy`, T = `dz` (XNC dastur o'lchami) |
| `Grain` | `DIR_HOR` — detal `txt="true"` (tekstura), aks holda `DIR_NONE` (932/932; 3183 — ❓ Q4) |
| `EdgeFBLR` | 4 ta 0/1, ajratuvchi `" ,"` (probel+vergul): **F = `elb`, B = `elt`, L = `ell`, R = `elr`**; orqa tomonda L va R almashadi (`F=elb, B=elt, L=elr, R=ell`) — 958/958 (3173 dan tashqari) |
| `PlaneSize="1"`, `MachineBase="-1"` | doimiy |

### 2.2 Koordinata tizimi

* GibLab XNC xom koordinatasi (= MebeliX `machine_program()` natijasi, origin `LT`, burishsiz): `x` o'ngga, `y` **pastga**
  (yuqori qirradan), `bt` qirrasi `y=0`, `bb` qirrasi `y=W`. Qirra teshigi balandligi `z` — **pastki (orqa) yuzadan**
  (`m="true"` bo'lsa `z = T/2`, `z` atributi e'tiborsiz).
* Daron: **X = x − L** (koordinata boshi o'ng qirrada, X manfiy), **Y = y** (o'zgarmaydi), **Z = 0 — yuqori (ishlov)
  yuza, pastga manfiy**. Qirra teshigi Z = −(T − z).
* Orqa tomon (`side=false`): avval `x → L − x` (detal tik o'q atrofida ag'dariladi), so'ng yuqoridagi formula → **X = −x**.

### 2.3 Vertikal teshik (`bf`, MebeliX `DrillFront`)

```
<HoleV Name="" Face="A" Start="X Y 0.00" End="X Y -DP" Diameter="D" IsCuted="0"/>
```
`Face="A"` — doimiy (orqa tomonda ham `A`; orqa tomon alohida faylda). `DP` — XNC chuqurligi o'zgarishsiz (o'tuvchi
teshik `dz+3` = `19` → `End … -19`).

### 2.4 Gorizontal (qirra) teshik (`bl/br/bt/bb`)

```
<HoleH Name="" Face="L|R|D|U" Start="Xs Ys Z" End="Xe Ye Z" Diameter="D" IsCuted="0"/>
```
`Start` — qirradagi kirish nuqtasi, `End` — teshik tubi; Z = −(T − z).

| XNC | Face | Start | End |
|---|---|---|---|
| `bl` (x=0) | `L` | `(−L, y)` | `(−L + DP, y)` |
| `br` (x=L) | `R` | `(0, y)` | `(−DP, y)` |
| `bt` (y=0) | `D` | `(x − L, 0)` | `(x − L, DP)` |
| `bb` (y=W) | `U` | `(x − L, W)` | `(x − L, W − DP)` |

### 2.5 Paz (`gr`, MebeliX `Groove`)

```
<SlotL Start="X1 Y1 -DP" End="X2 Y2 -DP" Face="A" Width="T_en" IsCuted="0" />
```
(`" />"` — oldida probel). X = x − L (orqada −x), Y = y, Z = −DP, `Width` = paz eni `t`. Asbob (`Cut4`) va `c`
yozilmaydi (namunada hamma pazlarda `c=0`). 44/44 paz faylida mos.

### 2.6 Frezalash (`ms` + `ml`/`mac`, MebeliX `MillStart/MillLine/MillArcCenter`)

Daron **korreksiya bayrog'ini olmaydi** — GibLab o'zi **asbob markazi trayektoriyasini** hisoblab yozadi:

```
<SlotL Start="Xs Ys -DP" End="Xe Ye -DP" Face="A" Width="D_asbob" IsCuted="0" />
<SlotA Start="Xs Ys -DP" End="Xe Ye -DP" Center="Xc Yc -DP" Face="A" Width="D_asbob" IsCuted="0" />
```
* Har kontur segmenti `d/2` ga korreksiya tomoniga siljitiladi: `c=1` — harakat yo'nalishiga nisbatan **o'ng** (ekranda,
  Y pastga), `c=2` — chap. Chiziq normal vektori (o'ng): `(−dy, dx)/|…|·d/2`.
* Ichki burchakda qo'shni siljigan chiziqlar **kesishish nuqtasida** tutashadi; yoy radiusi `r ∓ d/2` (markaz o'zgarmaydi).
* `SlotA` yo'nalish atributisiz: **Start→End doim soat miliga teskari** (X=x−L, Y=y koordinatada matematik CCW).
  XNC `dir="true"` (MebeliX `clockwise`, ekranda soat bo'yicha) — tartib saqlanadi; `dir="false"` — Start/End almashtiriladi.
* Yoy kontur bilan urinma tutashmagan joyda (namunada 1 detal) GibLab cho'qqi atrofida `r = d/2` li qo'shimcha yoy qo'yadi.
* `Width` = asbob diametri (`Mill8` → `8`), Z = −DP. `in/out` (kirish/chiqish) chiqmaydi — kontur XNC dagi kabi detal
  tashqarisidan boshlanadi.

### 2.7 `<Outline>`

* Frezalashsiz detal: to'rtburchak, 5 nuqta: `(−L,W) (−L,0) (0,0) (0,W) (−L,W)`, Z=0. Orqa tomonda xuddi shu formula
  `x → L − x` bilan: `(0,W) (0,0) (−L,0) (−L,W) (0,W)`.
* O'tuvchi frezalashli detal (shu detalning **istalgan** XNC dasturidagi, orqa tomon fayllarida ham): kesilgandan keyingi
  haqiqiy kontur, yoylar vatarlarga bo'lingan (r=6 → 5 bo'lak, r=10 → 7 bo'lak). Bu GibLab geometriya yadrosi natijasi;
  namunada noto'g'ri yoyli detalda kontur buzilgan holda chiqqan — stanok undan foydalanmasa kerak (❓ Q2).

---

## 3. MebeliX XNC → Daron xaritasi

MebeliX'da `services/xnc.py::machine_program(op, project)` natijasini olamiz (ifodalar hisoblangan, burish/ko'zgu/origin
qo'llangan; koordinata chap-yuqori burchakdan, Y pastga — GibLab xom koordinatasi bilan bir xil). `L = size.length`,
`W = size.width`, `T = blank.thickness`, `back = face_back`.

| MebeliX amal | Daron | Formula |
|---|---|---|
| `drill face=front` (`DrillFront`) | `HoleV` | X = (back ? −x : x − L), Y = y, Z: `0.00` → `−depth`, `Diameter = d` |
| `drill face=left` (`DrillLeft`) | `HoleH Face=L` (orqada `R`) | §2.4; z_b = middle ? T/2 : z |
| `drill face=right` (`DrillRight`) | `HoleH Face=R` (orqada `L`) | §2.4 |
| `drill face=top` (`DrillTop`, y=0) | `HoleH Face=D` | §2.4 |
| `drill face=bottom` (`DrillBottom`, y=W) | `HoleH Face=U` | §2.4 |
| `groove` (`Groove`) | `SlotL` | §2.5, Width = `width` |
| `mill_start` + `mill_line`/`mill_arc` | `SlotL`/`SlotA` | §2.6 — markaz trayektoriyasi offset bilan |
| `rect`, `ellipse` (`MillRect`, `MillEllipse`) | `SlotL`/`SlotA` | `path` ni chiziq/yoy segmentlariga yoyib, §2.6 (namunada yo'q) |
| `count>1` / `AC>1` massiv | bir nechta `HoleV` | massivni alohida teshiklarga yoyish (namunada `ac=1` hammasi) |
| `Tool`, `Var`, `Par`, `Com`… | — | chiqmaydi (faqat hisoblangan natija) |

### 3.1 Tekshirilgan misollar (koordinatalar qo'lda solishtirildi)

**A. `316701_01_001` (2098×597×16, yuz tomon, `elb`)** — XNC: `bf x=593 y=70 dp=dz+3`, `bf x=880.5 y=50 dp=9 Bore5`,
`br y=70 z=8 m=true dp=34`, `bl y=70 …`:
```
<Plane … Width="2098" Hight="597" Thickness="16" Grain="DIR_NONE" EdgeFBLR="1 ,0 ,0 ,0" …>
<HoleV Name="" Face="A" Start="-1505 70 0.00" End="-1505 70 -19" Diameter="8" IsCuted="0"/>     ← 593−2098, dp=16+3
<HoleV Name="" Face="A" Start="-1217.5 50 0.00" End="-1217.5 50 -9" Diameter="5" IsCuted="0"/>  ← 880.5−2098
<HoleH Name="" Face="L" Start="-2098 70 -8" End="-2064 70 -8" Diameter="4.5" IsCuted="0"/>   ← bl: −L … −L+34
<HoleH Name="" Face="R" Start="0 70 -8" End="-34 70 -8" Diameter="4.5" IsCuted="0"/>         ← br
```
**B. `316601_14_017` (68×1581×18, `m=false`)** — `bl y=70 z=8 m=false dp=34` → `Face="L" Start="-68 70 -10" End="-34 70 -10"`
(Z = −(18−8)); `bl y=102 z=9 m=true dp=23.3` → `Start="-68 102 -9" End="-44.7 102 -9"`; `bf x=34 y=70 dp=12.5 Bore15`
→ `Start="-34 70 0.00" End="-34 70 -12.5" Diameter="15"`.

**C. `316601_03_005` (160×520, `bt`/`bb`)** — `bt x=80` → `Face="D" Start="-80 0 -8" End="-80 34 -8"`;
`bb x=80` → `Face="U" Start="-80 520 -8" End="-80 486 -8"`. `elr` → `EdgeFBLR="0 ,0 ,0 ,1"`.

**D. `317001_01_005_2` (696×776, orqa tomon)** — XNC `bf x=243 y=698 dp=1.5 d=3` → `Start="-243 698 0.00" End="-243 698 -1.5"`
(X = −x); `bf x=662 y=86 Bore15` → `X=-662` (yuz faylidagi `br y=86` minifiks teshigi bilan bir qirrada).

**E. `317701_01_002` (704×500, frezalash `c=1 Mill8`)** — XNC `ms (645.5,510) → ml (645.5,480) → mac (651.5,474) c(651.5,480) dir=true → ml (714,474)`:
```
<SlotL Start="-54.5 510 -16" End="-54.5 480 -16" Face="A" Width="8" IsCuted="0" />          ← x+4 (o'ngga), −704
<SlotA Start="-54.5 480 -16" End="-52.5 478 -16" Center="-52.5 480 -16" Face="A" Width="8" IsCuted="0" />  ← r=6−4
<SlotL Start="-52.5 478 -16" End="10 478 -16" Face="A" Width="8" IsCuted="0" />
```
**F. `316801_02_008_2` (990×600, orqa tomon paz)** — `gr x1=990 y1=0 x2=0 y2=0 t=6 dp=8` → `<SlotL Start="-990 0 -8" End="0 0 -8" … Width="6" … />`.

---

## 4. Doimiy va ma'lumotga bog'liq maydonlar

| Doimiy (1009/1009) — stanok sozlamasi deb taxmin | Ma'lumotga bog'liq |
|---|---|
| `Version="3.0"`, `Source=""`, `SourceType="BAN"`, `PlaneNo=" "`, `PlaneSize="1"`, `MachineBase="-1"`, `Face="A"` (vertikal/paz/freza), `Name=""` (teshik), `IsCuted="0"` | `Time`, `Plane@Name/Code/Material`, `Width/Hight/Thickness`, `Grain`, `EdgeFBLR`, `Outline`, barcha koordinata/diametr/chuqurlik, `Face` (L/R/U/D) |

---

## 5. Minimal anonim misol

Detal 600×400×16, `elb`, yuz tomon: `bf (100,50) d=5 dp=12`, `bl y=40 m=true d=8 dp=30`, `gr (0,350)→(600,350) t=4 dp=8`.
```
<MicroDrawBan_XML Version="3.0" Time="2026/01/01 12:00:00" Source="" SourceType="BAN">
<Plane Name="01_001 detal" Code="900101_01_001" Material="LDSP 16" PlaneNo=" " Width="600" Hight="400" Thickness="16" Grain="DIR_NONE" EdgeFBLR="1 ,0 ,0 ,0" PlaneSize="1" MachineBase="-1">
<Outline>
<Point Value="-600 400 0"/>
<Point Value="-600 0 0"/>
<Point Value="0 0 0"/>
<Point Value="0 400 0"/>
<Point Value="-600 400 0"/>
</Outline>
<HoleV Name="" Face="A" Start="-500 50 0.00" End="-500 50 -12" Diameter="5" IsCuted="0"/>
<SlotL Start="-600 350 -8" End="0 350 -8" Face="A" Width="4" IsCuted="0" />
<HoleH Name="" Face="L" Start="-600 40 -8" End="-570 40 -8" Diameter="8" IsCuted="0"/>
</Plane>
</MicroDrawBan_XML>
```
(Har qator `CRLF` bilan.)

---

## 6. Noma'lumlar — foydalanuvchiga savollar

1. **Q1. Koordinata boshi stanokda.** X manfiy (o'ng qirradan), Y — XNC dagi kabi. Stanok stolida detal qaysi burchak
   bilan bazalanadi (o'ng-old?) va «U/D/F/B» qaysi fizik tomon? Namunadagi formulani o'zgarishsiz takrorlash kifoya,
   lekin sinov detali bilan tasdiqlash kerak.
2. **Q2. `<Outline>` stanokda ishlatiladimi?** (faqat ko'rinish/simulyatsiya uchunmi?) Frezalashli detalda GibLab
   kontur hisobini takrorlash qiyin; to'rtburchak yetadimi?
3. **Q3. Freza korreksiyasi:** Daron faqat asbob markazi yo'lini oladi. Tashqi (qavariq) burchaklarda yoy qo'yish qoidasi
   faqat bitta namunada ko'rindi; `c=0` (markaz bo'yicha) va `C=3` (cho'ntak) namunada yo'q — qanday chiqarish kerak?
4. **Q4. `Grain`:** 3183 da loyiha faylida hamma detal `txt="true"`, faylda `DIR_NONE`. Loyiha keyin o'zgarganmi yoki qoida
   boshqacha (materialga bog'liq)? `DIR_VER` qachon chiqadi (namunada yo'q)?
5. **Q5. Burish/ko'zgu:** namunadagi 1014 XNC ning hammasida `turn=0`, `mirHor=mirVert=false`. Ular bo'lsa GibLab
   koordinatalarni burib yozadimi (MebeliX `machine_program` shunday qiladi) — tasdiqlash kerak.
6. **Q6. Kirill yoki maxsus belgili nom/material** qaysi kodlashda yoziladi (XML deklaratsiyasi yo'q)? `"`/`&` belgisi
   ekranlanadimi?
7. **Q7.** Orqa tomonda qirra teshigi/freza namunada yo'q — L↔R almashtirish va yoy yo'nalishi teskari bo'lishi taxmin.
8. **Q8.** Massiv teshiklar (`ac>1`) namunada yo'q — alohida `HoleV` larga yoyish to'g'rimi?
