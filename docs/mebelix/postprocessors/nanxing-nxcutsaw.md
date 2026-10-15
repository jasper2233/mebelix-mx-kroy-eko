# Nanxing (NXCutSaw) — `.CUT` (AutoCUT XML) postprotsessor formati

> Manba: `post prtsessorlar\PILNIY APPARAT\Nanxing (NXCutSaw)\<buyurtma>\*.CUT` (20 fayl).
> Xuddi shu format `Nanxing NXCutSAW` papkasida ham bor — qarang [nanxing-nxcutsaw-flat.md](nanxing-nxcutsaw-flat.md).
> Faqat chiqish fayllari va kompaniyaning `.project` XML fayllari o'qildi; dastur binarlari ochilmadi.
> Mijoz ismlari «mijoz» bilan almashtirilgan.

**Tushunish darajasi: to'liq (≈95%).** Barcha 34 ta `.CUT` fayl (ikkala papka) avtomatik tekshiruvdan
xatosiz o'tdi: geometriya (kerf, torsovka, ichma-ich joylashuv), detal sonlari, qoldiqlar soni,
`Grouped` qoidasi, aylantirish (`Angle`) va `Turn` qoidasi, kromka maydonlari, XNC kodlari.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.CUT` (katta harflar bilan) |
| Format | XML 1.0, `<?xml version="1.0" encoding="UTF-8"?>` |
| Kodirovka | UTF-8, **BOM yo'q** (kirillcha `Д`, `О` harflari UTF-8 da) |
| Qator tugashi | **yo'q** — butun fayl bitta qator, oxirida ham `\n` yo'q |
| O'nlik ajratgich | nuqta (`.`) — faqat `F4`/`F5` da (`1400.00`) |
| Birlik | mm, butun sonlar (namunalarda kasr uchramadi) |
| Fayl soni | **har bir material (CS operatsiyasi) uchun bitta fayl** |
| Papka | `Nanxing (NXCutSaw)\<buyurtma raqami>\` |

**Papka nomlari (2027, 2028 … 2037) — yil emas, buyurtma raqami** (fayl nomi ham shu raqam bilan
boshlanadi: `2027\2027_mijoz_LDSP_UD_.CUT`). 2035 papkasi yo'q (bu buyurtma eksport qilinmagan).

**Fayl nomi:** `<buyurtma>_<mijoz>_<material nomi>.CUT`, bu yerda loyiha nomi (`2027 mijoz`) va
material nomi (`XDF 2800x2070 mm  5.8 kv`) dagi **bo'sh joy va qavslar ketma-ketligi bitta `_` ga**
almashtiriladi (regex `[\s()]+` → `_`). Misollar:

| Material nomi (loyihada) | Fayl nomidagi qism |
|---|---|
| `XDF 2800x2070 mm  5.8 kv` | `XDF_2800x2070_mm_5.8_kv` (ikki bo'sh joy → bitta `_`) |
| `LDSP UD (110197)_diffuseOriginal` | `LDSP_UD_110197__diffuseOriginal` |
| `LDSP UD ` (oxirida bo'sh joy) | `LDSP_UD_` |
| `LDSP METALIK SHAGREN 5.03 kv` | `LDSP_METALIK_SHAGREN_5.03_kv` (nuqta saqlanadi) |

Apostrof (`'`) saqlanadi. Bir buyurtmada 1–3 fayl (LDSP/LMDF/XDF/AKRIL). Namunalardagi fayllar:

| Buyurtma | Fayllar (material) | Kartalar (Layout) | Listlar | Detal turlari | Detal soni | Qoldiq |
|---|---|---|---|---|---|---|
| 2027 | LDSP UD / XDF | 8 / 2 | 8 / 2 | 53 / 3 | 73 / 4 | 1 / 1 |
| 2028 | LDSP OQ GLYANETS | 3 | 3 | 5 | 23 | 0 |
| 2029 | LDSP METALIK SHAGREN / Ldsp oq | 1 / 1 | 1 / 1 | 15 / 16 | 16 / 23 | 0 / 0 |
| 2030 | LDSP / LMDF BELI KARONA GLYANETS | 5 / 3 | 5 / 3 | 20 / 19 | 34 / 35 | 1 / 0 |
| 2031 | LDSP DUB VATAN / XDF | 3 / 1 | 3 / 1 | 27 / 4 | 47 / 8 | 1 / 1 |
| 2032 | LMDF DUB VATAN / LMDF KASHMIR | 16 / 3 | 18 / 6 | 154 / 17 | 249 / 37 | 1 / 3 |
| 2033 | LDSP ASTANA / XDF | 5 / 2 | 5 / 2 | 32 / 3 | 36 / 3 | 1 / 2 |
| 2034 | LDSP KASHMIR / XDF | 5 / 2 | 5 / 2 | 61 / 4 | 67 / 4 | 0 / 2 |
| 2036 | AKRIL KASHMIR / LDSP KASHMIR / XDF | 1 / 2 / 1 | 1 / 2 / 1 | 10 / 27 / 5 | 12 / 35 / 7 | 1 / 1 / 1 |
| 2037 | LDSP OQ GLYANETS / XDF | 5 / 2 | 5 / 2 | 29 / 3 | 44 / 5 | 1 / 1 |

Eslatma: boshqa stanoklar (masalan AESS Alpha, FastPanel) da bo'lgan `2030_…_XDF` va `2032_…_XDF`
fayllari bu papkada yo'q — eksport qilinmagan yoki tanlanmagan (savol 6). Loyihadagi arra bilan
kesilmaydigan materiallar (oyna, mato, «zamena material») uchun fayl yaratilmaydi.

---

## 2. To'liq tuzilma

Element daraxti (atributlar **alfavit tartibida** yoziladi — ASCII bo'yicha: `F1 < F10 < F11 < F12 < F13 < F3 …`;
bo'sh elementlar `<X …/>` ko'rinishida, `/>` dan oldin bo'sh joy yo'q):

```
AutoCUT ver="500"
└─ Project Memo="" Name Update
   └─ Data Ply [Type] TypeName
      ├─ Spares Type="Shape"            ← chiqadigan delovoy qoldiqlar ro'yxati
      │   └─ Shape Count Name Turn="False" X Y   (0..n)
      ├─ Condition Count Type="Shape"    ← kirish listlari (zaxira)
      │   └─ Shape Count Flag="True" Name Sx Sy X Y   (1..n)
      ├─ Solutions SolveGap
      │   └─ Solution
      │       └─ Layouts
      │           └─ Layout Count Cut CutCount="0" ID SheetID SheetName X Y   (1..n)
      │               └─ Part … (rekursiv, 1–6 daraja)
      └─ Objective Count Type="Shape"    ← detallar ro'yxati
          └─ Shape Count F1 [F10] [F11] F12 F13 F3 F4 F5 [F6] [F7] [F8] [F9] Name NestGap Order Turn X Y
```

### 2.1 `AutoCUT`, `Project`, `Data`

| Element.atribut | Ma'nosi | Turi / qiymatlar | Konstanta? |
|---|---|---|---|
| `AutoCUT.ver` | format versiyasi | `500` | ha (34/34) |
| `Project.Memo` | izoh | `""` | ha |
| `Project.Name` | loyiha nomi (`.project` dagi `name`) | `"3171 mijoz"` | ma'lumot |
| `Project.Update` | fayl yaratilgan vaqt `dd.MM.yyyy HH:mm:ss` | `27.09.2026 16:46:45` | ma'lumot (savol 7) |
| `Data.Ply` | material qalinligi `good.t` (mm) | 3, 16, 18 | ma'lumot |
| `Data.Type` | material kodi `good.code`; kod bo'lmasa atribut **yozilmaydi** | `XDF 5.8` (faqat XDF da) | ma'lumot |
| `Data.TypeName` | material nomi `good.name` (o'zgarishsiz, oxirgi bo'sh joy ham) | `LDSP KASHMIR SHAGREN` | ma'lumot |

### 2.2 `Condition` — kirish listlari

`Condition.Count` = ichidagi `Shape` soni. Har `Shape`:

| Atribut | Ma'nosi | Qiymatlar |
|---|---|---|
| `Name` | material nomi (`TypeName` bilan bir xil) | |
| `X`, `Y` | list uzunligi va eni (loyihadagi list `part.l`, `part.w`) | 2750×1830, 2800×2070, 2440×1220, qoldiqlar 2750×450, 2570×1200 … |
| `Count` | mavjud listlar soni (`part.count`); `10000` = cheksiz | 10000, 1000, 11, 10, 1 |
| `Sx`, `Sy` | torsovka (kromkadan kesib tashlanadigan) X va Y bo'yicha, mm | **har doim 5** (savol 1) |
| `Flag` | | **har doim `True`** (bosh harf bilan) |

Bir materialda bir nechta list o'lchami bo'lishi mumkin (asosiy list + ombordagi qoldiqlar),
masalan 3167: `2570×1200 ×1`, `2750×1245 ×1`, `2750×1830 ×11`. Ishlatilmagan list ham ro'yxatda
qoladi (2029 «Ldsp oq»: `2750×1830 Count=1000`, hech bir karta unga tegishli emas). Tartib: namunalarda
ko'pincha yuzasi bo'yicha o'sib boradi, lekin 3181 da bunday emas — tartib muhim emas, chunki
`Layout.SheetID` indeks orqali bog'lanadi.

### 2.3 `Spares` — chiqadigan delovoy qoldiqlar

`Spares` bo'sh bo'lishi mumkin (`<Spares Type="Shape"/>`). Har `Shape`:

| Atribut | Ma'nosi |
|---|---|
| `Name` | `О1`, `О2`, … (**kirillcha «О»**, U+041E) — ketma-ket |
| `X`, `Y` | qoldiqning **xom** o'lchami — list chetigacha (torsovka zonasi ham ichida) |
| `Count` | shu qoldiq kartalarda necha marta paydo bo'ladi (`Layout.Count` hisobga olingan) |
| `Turn` | har doim `False` (bosh harf) |

Loyihadagi tegishli qoldiq yozuvi: `rl`,`rw` = `Spares.X`,`Y`; `l`,`w` = toza o'lcham (list chetiga
tegadigan har tomondan 5 mm torsovka ayrilgan). Masalan 3175: `О1 1821×1830` ↔ loyihada
`l=1816 w=1820 rl=1821 rw=1830 waste="true" business="true"`.
Kuzatilgan qoldiqlarning eng kichik tomoni ≥ 500, eng katta tomoni ≥ 1000 → loyihadagi
`cMinDimRegWaste1=1000`, `cMinDimRegWaste2=500` ga mos.

### 2.4 `Solutions` / `Layout` — kesish kartalari

`Solutions.SolveGap` = arra qalinligi (kerf) mm — **3** (loyihadagi `tool.cutting.swSawthick=3`).
`Solution` va `Layouts` — atributsiz o'ramlar (doim bittadan).

| `Layout` atributi | Ma'nosi | Qiymatlar |
|---|---|---|
| `ID` | karta tartib raqami, 0 dan | 0..15 |
| `Count` | shu kartadagi bir xil listlar soni (takrorlanish) | 1, 2, 4 |
| `Cut` | **birinchi kesim yo'nalishi**: `true` → 1-daraja bo'laklar vertikal polosalar (X bo'yicha bo'linadi, `Py=0`, `Y`=list eni); `false` → gorizontal polosalar (Y bo'yicha, `Px=0`, `X`=list uzunligi) | `true`/`false` (kichik harf) |
| `CutCount` | | **har doim 0** (savol 3) |
| `SheetID` | `Condition` dagi list indeksi (0 dan) | |
| `SheetName`, `X`, `Y` | list nomi va o'lchami (Condition dan nusxa) | |

### 2.5 `Part` — gilyotina daraxti (eng muhim qism)

Har `Part` = bitta to'g'ri to'rtburchak bo'lak. Atributlar: `Px`, `Py` (chap-burchak koordinatasi,
**list boshiga nisbatan absolyut**, mm), `X`, `Y` (o'lcham), ixtiyoriy `UID`, `Angle="90"`,
`Grouped="N"`, `Spare="True"`.

Bo'lak turlari:

| Tur | Belgisi | Ma'nosi |
|---|---|---|
| Konteyner (polosa) | farzandlari bor, `UID` yo'q | kesib olinadigan polosa / bo'lak; ichidagilar unga perpendikulyar kesiladi |
| Detal | farzandi yo'q, `UID` bor, `Spare` yo'q | `UID` = `Objective` dagi `Shape` indeksi (0 dan, `Д1` → 0) |
| Qoldiq | `Spare="True"`, `UID` | `UID` = `Spares` dagi indeks (`О1` → 0) |

Chiqindi (ishlatilmaydigan qism) **yozilmaydi** — u bo'laklar orasidagi bo'sh joy sifatida qoladi.

**Tekshirilgan qoidalar (34 faylda 0 istisno):**

1. **Yo'nalish almashinadi**: `Cut="true"` bo'lsa 1-daraja X bo'yicha, 2-daraja Y bo'yicha,
   3-daraja X bo'yicha … (`Cut="false"` — aksincha). 775 ta ko'p-farzandli tugunda istisno yo'q.
2. **Farzand ota-onaning perpendikulyar o'lchamini to'liq egallaydi**: X bo'yicha bo'linsa
   `child.Y == parent.Y` va `child.Py == parent.Py`; Y bo'yicha bo'linsa `child.X == parent.X`.
   Shuning uchun detal polosani to'liq egallamasa, u alohida konteynerga o'raladi
   (masalan `<Part X="1175" Y="1718"><Part UID="1" X="584" Y="1718"/>…`).
3. **Kerf**: ketma-ket qo'shnilar orasida aniq `SolveGap` (3 mm):
   `next.Px = prev.Px + prev.X + 3` (yoki Y bo'yicha).
4. **Torsovka**: 1-daraja polosalar list bo'ylab to'liq (`Py=0, Y=1830` yoki `Px=0, X=2750`),
   ularning birinchi bo'lagi esa `Sx`/`Sy` = 5 dan boshlanadi. 1-daraja polosalarning o'zi ham
   kesish yo'nalishida 5 dan boshlanadi. Ya'ni ikkala o'q bo'yicha boshlang'ich torsovka 5 mm;
   chuqurroq darajalarda birinchi farzand ota-ona boshidan (offset 0) boshlanadi.
   Qarama-qarshi chetdagi torsovka yozilmaydi (qolgan joy chiqindi).
5. **Konteyner o'lchami ichidagidan katta bo'lishi mumkin** (masalan 3171: `X=1175`, ichidagi
   584+3+583=1170) — farq chiqindi.
6. **`Grouped="N"`** faqat **N ta bir xil ketma-ket qo'shnining oxirgisiga** qo'yiladi
   (bir xil = bir xil UID/o'lcham/ichki tuzilma). Kuzatilgan naqshlar: `(-,2)` 167 marta,
   `(-,-,3)` 25, `(-,-,-,4)` 10, `(-,-,-,-,5)` 3, `(-,-,-,-,-,6)` 1. Bu stanokka «oldingi N ta
   kesim bir xil» degan ishora (takroriy polosa/detal). Konteynerlarga ham qo'yiladi.
7. **`Angle="90"`**: detal 90° aylantirilgan — `leaf.X == Objective.Y` va `leaf.Y == Objective.X`.
   Aylantirilgan detalning `Objective.Turn` har doim `true`.
8. **`Spare="True"`** qoldiq doimo o'z ota-onasidagi **oxirgi** bo'lak va ota-ona (yoki list) chetigacha
   cho'ziladi: 3175 `Px=929 X=1821` (929+1821=2750). 1- yoki 2-darajada uchraydi.
9. Chuqurlik (daraja) ≤ `tool.cutting.swMaxturns` (3167: swMaxturns=6 → 6 daraja; qolganlar 4 → ≤4).
10. Har `UID` bo'yicha `Σ(barg soni × Layout.Count) == Objective.Shape.Count` — barcha fayllarda.

### 2.6 `Objective` — detallar ro'yxati

`Objective.Count` = `Shape` soni (= loyihadagi CS operatsiyasining detal qatorlari soni).
Tartib = loyihadagi CS operatsiyasidagi `<part>` havolalari tartibi (28 faylda 1:1 tasdiqlandi,
qolgan 6 tasida loyiha keyin o'zgartirilgan). Bir xil nomli ikki qator alohida `Shape` bo'lib qoladi.

| Atribut | Ma'nosi | Manba (`.project`) | Misol |
|---|---|---|---|
| `Name` | `Д1`, `Д2`, … (kirillcha «Д», ketma-ket) | indeks+1 | `Д3` |
| `Count` | soni | `part.count` | `4` |
| `F3` | soni (takror) | `part.count` | `4` |
| `X`, `Y` | uzunlik va en (butun mm) | `part.l`, `part.w` (namunalarda `= dl, dw`; `jl/jw` emas) | `1400`, `584` |
| `F4`, `F5` | `X`, `Y` 2 kasr bilan | `l`, `w` | `1400.00` |
| `F1` | detal nomi | `part.name` | `01_003 bok` |
| `Order` | mahsulot (buyum) nomi | detal joylashgan `good typeId=product` ning `name` | `01 parta` |
| `Turn` | aylantirish mumkinmi | `not part.txt` (txt=true → `false`) | `true`/`false` |
| `NestGap` | kerf | `swSawthick` | `3` |
| `F8` | **yuqori** (top) kromka | `part.elt` | `(A) 1-19 dub votan` |
| `F9` | **pastki** (bottom) kromka | `part.elb` | |
| `F10` | **chap** kromka | `part.ell` | |
| `F11` | **o'ng** kromka | `part.elr` | |
| `F6` | 1-XNC dastur kodi (yuz tomoni) | `operation typeId=XNC side="1"/"true"` → `code` | `317501_01_004` |
| `F7` | 2-XNC dastur kodi (orqa tomon) | `XNC side="2"/"false"` → `code` | `317501_01_008_2` |
| `F12` | detalda **frezerovka** bor | XNC dasturida `ms/ml/ma/mac` | `true`/`false` |
| `F13` | detalda **parmalash** bor | XNC dasturida `bf/bl/br/bt/bb` | `true`/`false` |

Kromka qiymati formati: `"(" + EL_operatsiya.elSymbol + ") " + kromka materiali nomi`
(`good typeId=band` ning `name`). Masalan `elSymbol="B"`, band `1-19 kapuchino` →
`(B) 1-19 kapuchino`. Kromka bo'lmasa atribut **umuman yozilmaydi**. Moslik: 1228/1228 (GibLab'da
saqlangan loyiha versiyalarida); `F8..F11 ↔ elt/elb/ell/elr` — barcha fayllarda istisnosiz.

`F6`/`F7` kod odatda `<mahsulot kodi>_<detal kodi>` (`317501_01_004`), lekin bu shunchaki XNC
operatsiyasining `code` atributi; ba'zan uzun raqam (`26041609570221009002115`) yoki `01.018x018x0`.
XNC bo'lmasa `F6`/`F7` yo'q. `F12`/`F13` statistikasi: 197 ta XNC'siz → ikkalasi `false`; faqat paz
(`gr`) bor 2 ta → ikkalasi `false`; 6 ta istisno (`bf`+frezer bor, lekin `F12=false`) — savol 4.
`F2` maydoni hech qachon chiqmaydi.

---

## 3. Kesish rejasi qanday kodlangan

- **List** → `Condition/Shape` (o'lcham, soni, torsovka). **Karta (pattern)** → `Layout`; bir xil
  kartaning listlar soni `Layout.Count` (bu «kitob»/paket balandligi emas — paket balandligi
  `swPackageHeight=40` faylga yozilmaydi; savol 2).
- **Polosalar va kesim ketma-ketligi** → `Part` daraxti; 1-daraja yo'nalishi `Layout.Cut`;
  har chuqurlashganda yo'nalish 90° almashadi (gilyotina, `swMaxturns` gacha daraja).
  Hujjat tartibi = kesish tartibi (chapdan o'ngga / pastdan yuqoriga — koordinata boshi savol 5).
- **Torsovka** → `Sx`, `Sy` (5 mm) + birinchi bo'laklarning 5 dan boshlanishi.
- **Kerf** → `SolveGap` va `NestGap` (3).
- **Detal joylashuvi** → barg `Part` (`UID`, `Px`, `Py`, `X`, `Y`, `Angle`).
- **Takroriy kesimlar** → `Grouped`.
- **Delovoy qoldiq** → `Spares` + barg `Part Spare="True"`; oddiy chiqindi yozilmaydi.
- **Yorliq (etiketka) ma'lumoti** → `Objective` dagi `F1` (nom), `Order` (mahsulot), `F6/F7`
  (XNC kodi — shtrix-kod sifatida ishlatilishi mumkin), kromkalar `F8..F11`.

---

## 4. Loyiha → fayl moslashtirish (namunalarda tekshirilgan)

Asosiy qoida: **GibLab'da saqlangan** versiya (`3171_mijoz.project`, pastki chiziqli nom) ishlatiladi —
Bazis'dan kelgan xom versiyada (`3171 mijoz.project`) `txt` va kromka nomlari boshqacha.
Moslash: `F1 == part.name` va `(X,Y) == (part.dl, part.dw)`.

### 4.1 Buyurtma 2033, material `XDF 2800x2070 mm  5.8 kv` (`2033\2033_mijoz_XDF_….CUT`)

Loyiha: `good typeId=sheet name="XDF 2800x2070 mm  5.8 kv" code="XDF 5.8" t="3"`, list `2800×2070
count=10000` → `Data Ply="3" Type="XDF 5.8"`, `Condition Shape Count="10000" X="2800" Y="2070"`.

| Loyiha detali (`name`, `dl×dw`, `count`, `txt`) | `Objective` |
|---|---|
| `01_008 XDF ort`, 2499×1069, 1, false | `Д1 X=2499 Y=1069 Count=1 Turn=true F12=false F13=false` |
| `02_008 XDF ort`, 2499×1069, 1, false | `Д2 …` |
| `04_005 XDF ort`, 549×1069, 1, false | `Д3 X=549 Y=1069` |

Kartalar (`Cut="false"` — avval gorizontal polosa):
```
Layout ID=0: Part Px=0 Py=5 X=2800 Y=1069 → Part Px=5 Py=5 UID=0 2499×1069
             Part Px=0 Py=1077 X=2800 Y=549 → Part Angle=90 Px=5 UID=2 1069×549 ; Part Px=1077 Spare UID=0 1723×549
Layout ID=1: … UID=1 2499×1069 ; Part Px=0 Py=1077 Spare UID=1 2800×993
```
Tekshiruv: 5+1069+3=1077 ✓; 1077+1723=2800 ✓; 1077+993=2070 ✓; `Д3` aylantirilgan (549×1069 → 1069×549) ✓.
Qoldiqlar `О1 1723×549`, `О2 2800×993` ↔ loyihada `1718×549` va `2790×988` (toza o'lcham, chetlardan 5 mm) ✓.

### 4.2 Buyurtma 2036, material `AKRIL KASHMIR` (2440×1220, t=18)

10 qator, jami 12 dona; joylashtirilgan barglar: UID0×3, qolganlar ×1 → 12 ✓.
`01_009 Fasad` (264×398, count 3, to'rt tomoni `@operation#2` = `elSymbol="B"`, band `21-1 kashmir`)
→ `Д1 Count=3 F8=F9=F10=F11="(B) 21-1 kashmir" Turn=true`.
Joylashuv: `Px=5, 272, 539` (5+264+3=272 ✓), uchinchisida `Grouped="3"` ✓.
`02_007 Fasad` ikki qator (har biri o'z XNC kodi bilan) → `Д3 F6="26041609570221009002115"`,
`Д4 F6="…2216"` — XNC `code` bilan aynan bir xil ✓, `F13=true` (parmalash bor).
Qoldiq `О1 623×1220` (`Px=1817`, 1817+623=2440) ↔ loyihada `l=618 w=1210 rl/rw` ✓.

### 4.3 Buyurtma 2029, material `Ldsp oq` (ombordagi qoldiqdan foydalanish)

Loyiha listlari: `2750×1830 count=1000` va `2750×1160 count=1` → `Condition Count="2"`:
`Shape Count="1" X="2750" Y="1160"` (indeks 0) va `Shape Count="1000" X="2750" Y="1830"` (indeks 1).
Yagona karta `SheetID="0"` — ya'ni hamma 23 detal qoldiq listga joylangan; 2750×1830 ishlatilmagan, lekin
ro'yxatda bor ✓.

### 4.4 Ikki mahsulot bitta faylda (2030, `LMDF BELI KARONA GLYANETS`)

19 ta `Shape`: 9 tasi `Order="01 Shkaf"` (`01 Shkaf.project`), 10 tasi `Order="02 Servant"`
(`02 Servant.project`) — `Order` = mahsulot nomi, bitta material bo'yicha barcha mahsulotlar bitta faylga
yig'iladi ✓.

### 4.5 Umumiy statistika (34 fayl, ikkala papka)

- `Turn == not txt` — GibLab'da saqlangan versiyalarda 100% (2027/2031/2032 da faqat xom versiya bor,
  u yerda `txt` hamma joyda `true`, shuning uchun mos emas).
- Kromka tomonlari `elt,elb,ell,elr ↔ F8,F9,F10,F11` — 100%.
- `X,Y == dl,dw` — 1145 tadan 1140 (qolganlari loyiha keyin tahrirlangan: 3173).
- Detal sonlari yig'indisi = joylangan barglar soni — 34/34 fayl.

---

## 5. Minimal qayta tiklangan misol

List 2750×1830 (16 mm), kerf 3, torsovka 5. Detallar: A 1000×500 ×2 (aylantirsa bo'ladi),
B 700×400 ×1 (tekstura, kromka tepada). Natija: bitta vertikal polosa + delovoy qoldiq.
(Fayl aslida bitta qatorda yoziladi; bu yerda o'qish uchun bo'lingan.)

```xml
<?xml version="1.0" encoding="UTF-8"?><AutoCUT ver="500"><Project Memo="" Name="9999 mijoz" Update="04.10.2026 10:00:00">
<Data Ply="16" TypeName="LDSP OQ">
<Spares Type="Shape"><Shape Count="1" Name="О1" Turn="False" X="1742" Y="1830"/></Spares>
<Condition Count="1" Type="Shape"><Shape Count="10000" Flag="True" Name="LDSP OQ" Sx="5" Sy="5" X="2750" Y="1830"/></Condition>
<Solutions SolveGap="3"><Solution><Layouts>
<Layout Count="1" Cut="true" CutCount="0" ID="0" SheetID="0" SheetName="LDSP OQ" X="2750" Y="1830">
 <Part Px="5" Py="0" X="1000" Y="1830">
  <Part Px="5" Py="5" UID="0" X="1000" Y="500"/>
  <Part Grouped="2" Px="5" Py="508" UID="0" X="1000" Y="500"/>
  <Part Px="5" Py="1011" X="1000" Y="400"><Part Px="5" Py="1011" UID="1" X="700" Y="400"/></Part>
 </Part>
 <Part Px="1008" Py="0" Spare="True" UID="0" X="1742" Y="1830"/>
</Layout>
</Layouts></Solution></Solutions>
<Objective Count="2" Type="Shape">
<Shape Count="2" F1="01_001 bok" F12="false" F13="false" F3="2" F4="1000.00" F5="500.00" Name="Д1" NestGap="3" Order="01 shkaf" Turn="true" X="1000" Y="500"/>
<Shape Count="1" F1="01_002 fasad" F12="false" F13="true" F3="1" F4="700.00" F5="400.00" F6="999901_01_002" F8="(A) 1-19 oq" Name="Д2" NestGap="3" Order="01 shkaf" Turn="false" X="700" Y="400"/>
</Objective></Data></Project></AutoCUT>
```
Tekshiruv: 5+500+3=508, 508+500+3=1011; 5+1000+3=1008, 1008+1742=2750; UID0 2 dona, UID1 1 dona.

**Generator algoritmi (MebeliX `CutMap` → `.CUT`)**:
1. Material bo'yicha guruhlash → har material uchun bitta fayl, nom `[\s()]+→_`.
2. `Objective`: CS detal qatorlari tartibida, `UID` = indeks; kromka, XNC kodlari, `Turn = !grain`.
3. `Condition`: material listlari (+ ombor qoldiqlari) — `Count` (cheksiz = 10000), `Sx=Sy=torsovka`.
4. Bir xil kartalarni birlashtirish (`Layout.Count`), har karta uchun gilyotina daraxtini rekursiv yozish:
   1-daraja yo'nalishi → `Cut`; har daraja farzandlari perpendikulyar to'liq; polosaga sig'magan
   detalni konteynerga o'rash; chiqindini yozmaslik; delovoy qoldiqni oxirgi `Spare` bo'lak qilib
   chetgacha yozish; ketma-ket bir xillarning oxirgisiga `Grouped=N`.
5. `Spares`: delovoy qoldiqlarni xom o'lcham bo'yicha guruhlab `О1..` nomlash, `Count` = jami.
6. Atributlarni alfavit tartibida yozish, bitta qatorda, BOM'siz UTF-8.

---

## 6. Noaniq joylar — foydalanuvchiga savollar

1. **Torsovka `Sx=Sy=5`** barcha fayllarda, loyihadagi `cTrimL=cTrimW=2`. 5 — postprotsessor sozlamasimi
   yoki `tool.cutting.swMinPruning=5` dan olinadimi? Ikkinchi (qarama-qarshi) chetdagi torsovka ham 5 mi?
2. **Paket (kitob) balandligi** (`swPackageHeight=40`) faylga yozilmaydi — stanokda qo'lda beriladimi?
   `Layout.Count` (bir xil listlar soni) bilan stanok o'zi paketlaydimi?
3. **`Layout.CutCount="0"`** va **`Condition/Shape Flag="True"`** — har doim bir xil; ularning ma'nosi va
   boshqa qiymat qachon kerak?
4. **`F12`/`F13`** — frezerovka/parmalash belgilari degan xulosa 1250+ detalda to'g'ri, 6 ta istisno bor
   (parmalash+frezer, lekin `F12=false`). Stanok bu maydonlarni ishlatadimi (yorliqqa chiqaradimi)?
5. **Koordinata boshi**: `Px/Py` listning chap-pastki yoki chap-yuqori burchagidanmi? `X` — list uzunligi
   (2750) ekanligi aniq, lekin `Py=5` qaysi chetdan — stanok ekranidan tasdiqlash kerak.
6. Nima uchun ba'zi buyurtmalarda (`2030`, `2032`) XDF fayli bu stanok uchun yaratilmagan, boshqa
   stanoklarda esa bor?
7. **`Update`** vaqti fayl vaqtidan 3 soat orqada (16:46 ↔ 19:46) — server vaqt zonasi; stanok uchun
   ahamiyati bormi?
8. Kasr o'lchamlar (masalan 583.5) qanday yoziladi — `X="583.5"`, `F4="583.50"`? Namunalarda uchramadi.
9. Maxsus belgilar (`&`, `<`, `"`) nomlarda — XML escaping qilinadimi? Namunalarda uchramadi.
10. Prifugovka (`jl/jw`) yoki kromka qalinligi chegirmasi kerak bo'lganda `X/Y` `l/w` danmi yoki `dl/dw`
    danmi olinadi? Namunalarda hamma joyda `l = dl`.
