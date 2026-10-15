# XDWoodCam — `.wxf` (WXF 2.0, INI uslubidagi matn) postprotsessori

> Manba: korxonaning o'z namunalari — `post prtsessorlar/PRISADKA APPARAT/XDWoodCam/<NNNN>_<mijoz>.zip` (15 buyurtma,
> **1009 fayl**) va mos `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` XNC operatsiyalari.
> Faqat chiqish fayllari va loyiha XML o'qildi. Mijoz ismlari — «mijoz».
>
> **Holat: to'liq tushunilgan (teshik, frezalash, kromka, orqa tomon). Paz (`gr`) bu formatga chiqmaydi.**
> Prototip writer (scratchpad `gen.py::xdwood`) 3173 dan tashqari **958/958 faylni bayt-ma-bayt** qayta yasadi
> (frezalashli 58 fayl ham). 3173 — loyiha eksportdan keyin o'zgargan.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Fayl | **bitta XNC operatsiyasi = bitta `.wxf`**; nomi `<XNC kodi>.wxf` |
| Takror kod | `<kod> (1).wxf`, `<kod> (2).wxf` … (loyiha XML tartibida) |
| Orqa tomon | alohida XNC (`side="false"`), kod `…_2` |
| Format | INI uslubi: `[WXF]` sarlavha bo'limi, `[DATA]` amallar bo'limi, `kalit=qiymat` |
| Kodlash | ASCII (namunada boshqa bayt yo'q; `Description` dagi kirill — ❓ Q5) |
| Qator oxiri | `CRLF`, oxirgi qator ham |
| Sonlar | nuqta `.`, 4 kasrgacha (yoy `Angle` — 5 kasrgacha), ortiqcha nollarsiz (`880.5`, `-9.7409`, `-90.27025`) |
| Birlik | mm |

---

## 2. Sintaksis

### 2.1 Tuzilma

```
[WXF]
Version=2.0
Description=<buyurtma satri> <XNC kodi>       ← product@product.order (masalan "9001 mijoz") + probel + kod
Password=00000000000000000000000000000000     ← 32 ta "0"
X_Length=L
Y_Width=W
Z_Thickness=T
Edge=Type:61184 Left:a Front:b Right:c Back:d ← kromka bayroqlari (§2.6)
Contour=                                      ← doim bo'sh
[DATA]
Count=N                                       ← amallar soni (0 bo'lishi mumkin)
1=Type:… Panel:… …                            ← amallar, 1..N
```
Amallar tartibi: **1) vertikal teshiklar; 2) Panel 1 (bl); 3) Panel 2 (br); 4) Panel 3 (bt); 5) Panel 4 (bb);
6) frezalash konturlari** — guruh ichida XNC dastur tartibi (958/958). Har amal — `kalit:qiymat` juftlari, bitta probel bilan.

`Type` kodlari (hex ko'rinishda «yumaloq»): `57856` = 0xE200 vertikal teshik, `59904` = 0xEA00 gorizontal teshik,
`58368` = 0xE400 freza konturi; `Edge@Type:61184` = 0xEF00.

### 2.2 Koordinata tizimi

* GibLab XNC xom koordinatasi (= MebeliX `machine_program()`): x o'ngga, y pastga, `bt` — y=0, `bb` — y=W, qirra
  teshigi `z` — pastki yuzadan.
* XDWoodCam yuzasi: **Xs = x, Ys = W − y** (Y akslangan), chuqurlik musbat (`Zs`).
* Qirra teshigi — har qirraning **o'z mahalliy koordinatasida**: `Xs/Ys` dan biri qirra bo'ylab pozitsiya, ikkinchisi
  — **chuqurlik**; `Zs` — balandlik **yuqori yuzadan** (`T − z_b`).
* Orqa tomon: avval `x → L − x`; qirralar L↔R, kromka Left/Right almashadi.

### 2.3 Vertikal teshik

```
i=Type:57856 Panel:0 Ref:0 Xs:<x> Ys:<W−y> Zs:<dp> Dia:<d> Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 Num:1 Dx:0 Dy:0 Edge:0
```
`Zs` — chuqurlik (o'tuvchi `dz+3` = 19 o'zgarishsiz).

### 2.4 Gorizontal (qirra) teshik

```
i=Type:59904 Panel:<1..4> Ref:0 Xs:<…> Ys:<…> Zs:<T−z_b> Dia:<d> Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 Num:1 Dx:0 Dy:0 Edge:0
```
| XNC | Panel | Xs | Ys |
|---|---|---|---|
| `bl` (x=0) | **1** | dp | **W − y** |
| `br` (x=L) | **2** | dp | **y** |
| `bt` (y=0) | **3** | **x** | dp |
| `bb` (y=W) | **4** | **L − x** | dp |

(Panel 1/3/4 da pozitsiya XDWoodCam yuzasidagi koordinata bilan, Panel 2 da teskari o'lchanadi — «qirra atrofida
aylanib» o'lchash; 2 434 qirra teshigida tasdiqlandi.)

### 2.5 Frezalash konturi (`Type:58368`)

```
i=Type:58368 Panel:0 Ref:0 Xs:<x0> Ys:<W−y0> Zs:<dp> Dia:<D_asbob> Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 RK:<0|1|2> Num:<n> <segmentlar>
  LineTo:(Xe:<x>, Ye:<W−y>, Dep:<dp>)
  ArcTo:(Xc:<cx>, Yc:<W−cy>, Dep:<dp>, Angle:<±burchak>)
```
(segmentlar bir qatorda, probel bilan; ichida `", "` — vergul+probel.)
* `Xs/Ys` — `ms` nuqtasi, `Zs` — chuqurlik, `Num` — segmentlar soni. Hole qatoridagi `Num:1 Dx:0 Dy:0 Edge:0` bu yerda yo'q.
* `ArcTo` — **markaz** va burilish burchagi (yoy oxirgi nuqtasi yozilmaydi); `Angle` ishorasi = XNC `dir`:
  `dir="true"` (MebeliX `clockwise`) → musbat, `false` → manfiy (51/51), qiymat — 5 kasrgacha.
* Koordinatalar — kontur chizig'i; korreksiya: **`RK` = `c=1` → `2`, `c=2` → `1`, `c=0` → `0`** (Y akslangani uchun
  almashadi; 65/65).

### 2.6 Kromka (`Edge=`)

`Left` = `ell`, `Front` = **`elt`** (XNC y=0 tomon → Ys=W), `Right` = `elr`, `Back` = **`elb`** (XNC y=W → Ys=0);
orqa tomonda Left↔Right (958/958, 3173 dan tashqari).

### 2.7 Paz

`gr` (60 ta paz, 44 faylda) **chiqmaydi** — faqat pazdan iborat dastur `Count=0` bo'lib qoladi (masalan `316601_00_009.wxf`). ❓ Q1.

---

## 3. MebeliX XNC → XDWoodCam xaritasi

`machine_program()`: `L = size.length`, `W = size.width`, `T = blank.thickness`, `back = face_back`,
`fx(x) = back ? L − x : x`, `z_b = middle ? T/2 : z`.

| MebeliX | XDWoodCam |
|---|---|
| `drill front` | `Type:57856 Panel:0`, Xs=fx(x), Ys=W−y, Zs=depth |
| `drill left` / `right` | `Type:59904 Panel:1/2` (orqada 2/1), Xs=depth, Ys = W−y / y, Zs = T−z_b |
| `drill top` (y=0) / `bottom` (y=W) | Panel 3 / 4, Xs = fx(x) / L−fx(x), Ys = depth |
| `mill_start` + `mill_line`/`mill_arc` | `Type:58368`, `LineTo` / `ArcTo` (markaz + `±angle`), `RK` (correction 1→2, 2→1) |
| `rect` / `ellipse` | `path` → LineTo/ArcTo |
| `groove` | **chiqmaydi** (Q1) |
| kromka (`edges`) | `Edge=… Left Front(top) Right Back(bottom)` |

### 3.1 Tekshirilgan misollar

**A. `316701_01_001` (2098×597×16, `elb`)** — `Edge=Type:61184 Left:0 Front:0 Right:0 Back:1`; `bf x=593 y=70 dp=19` →
`Xs:593 Ys:527 Zs:19 Dia:8`; `bl y=527` → `Panel:1 Xs:34 Ys:70 Zs:8`; `br y=70` → `Panel:2 Xs:34 Ys:70`.

**B. `316601_14_017` (68×1581×18, `elt`)** — `Front:1`; `bl y=70 z=8 m=false dp=34` → `Panel:1 Xs:34 Ys:1511 Zs:10`;
`bl y=102 dp=23.3 m=true` → `Xs:23.3 Ys:1479 Zs:9`; `br y=50` → `Panel:2 Xs:34 Ys:50 Zs:9`.

**C. `316601_01_001` (1250×500)** — `bb x=785.99 dp=32` → `Panel:4 Xs:464.01 Ys:32 Zs:8`; `316601_03_005` `bt x=80` →
`Panel:3 Xs:80 Ys:34`.

**D. `317701_01_002` (704×500, freza `c=1`)** — `Type:58368 … Xs:645.5 Ys:-10 Zs:16 Dia:8 … RK:2 Num:3 LineTo:(Xe:645.5, Ye:20, Dep:16) ArcTo:(Xc:651.5, Yc:20, Dep:16, Angle:90) LineTo:(Xe:714, Ye:26, Dep:16)`.

**E. `316601_13_008` (`dir=false`)** — `ArcTo:(Xc:298.2989, Yc:298.2941, Dep:16, Angle:-90.27025)`.

**F. `317001_01_005_2` (orqa tomon)** — `bf x=243 y=698 d=3 dp=1.5` → `Xs:453 Ys:78 Zs:1.5 Dia:3`; kromkasiz → `Left:0 Front:0 Right:0 Back:0`.

---

## 4. Doimiy va ma'lumotga bog'liq maydonlar

| Doimiy (1009/1009) | Ma'lumotga bog'liq |
|---|---|
| `Version=2.0`, `Password=0…0`, `Edge=Type:61184`, `Contour=` (bo'sh), `Ref:0`, `Disable:0`, `ImageX/ImageY/ImageXY:0`, `Tool:0`, teshikda `Num:1 Dx:0 Dy:0 Edge:0`, vertikal/freza `Panel:0` | `Description`, o'lchamlar, `Edge` bayroqlari, `Count`, `Type`, `Panel` (qirra), Xs/Ys/Zs, `Dia`, `RK`, `Num` (freza), segmentlar |

`Num/Dx/Dy` — teshik massivi (soni va qadami) bo'lishi ehtimol; GibLab doim `1/0/0` yozadi (❓ Q3).

---

## 5. Minimal anonim misol

Detal 600×400×16, `elb`: `bf (100,50) d=5 dp=12`, `bl y=40 m=true d=8 dp=30`, `gr …` (chiqmaydi),
`ms (550,−10) c=1 Mill8 dp=16 → ml (550,60) → mac (560,70) c(560,60) dir=false → ml (610,70)` (`CRLF`):
```
[WXF]
Version=2.0
Description=9001 mijoz 900101_01_001
Password=00000000000000000000000000000000
X_Length=600
Y_Width=400
Z_Thickness=16
Edge=Type:61184 Left:0 Front:0 Right:0 Back:1
Contour=
[DATA]
Count=3
1=Type:57856 Panel:0 Ref:0 Xs:100 Ys:350 Zs:12 Dia:5 Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 Num:1 Dx:0 Dy:0 Edge:0
2=Type:59904 Panel:1 Ref:0 Xs:30 Ys:360 Zs:8 Dia:8 Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 Num:1 Dx:0 Dy:0 Edge:0
3=Type:58368 Panel:0 Ref:0 Xs:550 Ys:410 Zs:16 Dia:8 Disable:0 ImageX:0 ImageY:0 ImageXY:0 Tool:0 RK:2 Num:3 LineTo:(Xe:550, Ye:340, Dep:16) ArcTo:(Xc:560, Yc:340, Dep:16, Angle:-90) LineTo:(Xe:610, Ye:330, Dep:16)
```

---

## 6. Noma'lumlar — foydalanuvchiga savollar

1. **Q1. Paz:** GibLab pazlarni (60 ta, orqa devor/LED pazlari) bu stanokka chiqarmaydi. XDWoodCam'da paz/arra amali
   bormi (boshqa `Type` kodi)? Bo'lsa — qo'lda yasalgan namuna fayl kerak; yo'q bo'lsa pazni freza konturi sifatida
   chiqarish kerakmi?
2. **Q2. Koordinata boshi:** Ys = W − y (Y akslangan), `Front` = XNC yuqori qirrasi. Stanokda detal qaysi burchak bilan
   bazalanadi? Panel 2 dagi teskari pozitsiya stanok konvensiyasimi — sinov detali bilan tasdiqlash kerak.
3. **Q3. Massiv:** `Num/Dx/Dy` teshik qatori uchunmi? `Ref`, `ImageX/Y/XY`, `Tool`, `Edge` (amal ichida) ma'nosi.
4. **Q4. Orqa tomon:** tomon belgisi yo'q, X akslangan; orqa tomonda qirra teshigi/freza namunada yo'q (Panel 1↔2,
   `RK` 1↔2, `Angle` ishorasi — taxmin).
5. **Q5. `Description`** buyurtma satrini (mijoz ismi bilan) o'z ichiga oladi — MebeliX'da `project.number + customer`
   yozilsinmi? Kirill qaysi kodlashda?
6. **Q6.** Yopiq kontur, cho'ntak (`C=3`), `c=0` freza, burish/ko'zgu namunada yo'q.
