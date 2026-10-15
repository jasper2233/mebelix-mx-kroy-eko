# SCM Startech CN V — `.ISO` postprotsessori (sverlovka-prisadka)

Holat: **to'liq (sverlovka + paz)**. 15 buyurtmaning 17 ta `.ISO` faylidan 3173 dan tashqari **16/16 fayl bizning prototip generatorimiz bilan bayt-ma-bayt bir xil** chiqdi (6 tasida faqat `-0.000` ↔ `0.000` farqi — 4.4-bo'lim). Frezalash (`ms/ml/mac`) bu formatga **umuman chiqmaydi** (53 dasturda frezalash bor edi — ISO da hech qanday iz yo'q).

Manba namunalar: `post prtsessorlar/PRISADKA APPARAT/SCM Startech CN V/<NNNN>_<mijoz>.zip` (15 ta).
Mos loyihalar: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` (3183 da faqat `<NNNN> <mijoz>.project` bor). Loyihadagi har `operation typeId="XNC"` → bitta ISO dastur bloki.

> 3173: loyiha fayli eksportdan **keyin** (2026-10-01) o'zgartirilgan — 1-mahsulot qayta loyihalangan, 5 ta yangi XNC qo'shilgan. Shu sabab 3173 da 51 blokdan 27 tasi (2-mahsulot to'liq) mos, 1-mahsulot bloklari mos emas. Bu format xatosi emas.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.ISO` (oddiy matn) |
| Bitta faylda | **bir nechta detal dasturi** (`oN` bloklari), **ko'pi bilan 99 ta** |
| Fayl nomi | `<birinchi>_<oxirgi>.ISO` — buyurtmadagi dasturlarning tartib raqamlari: `1_99.ISO`, `100_122.ISO`; ≤ 99 bo'lsa bitta fayl `1_<N>.ISO` (`1_74.ISO`, `1_12.ISO`) |
| Blok raqami | `o1`, `o2`, … — **har faylda 1 dan qayta boshlanadi** (`100_122.ISO` ichida `o1…o23`) |
| Detal identifikatori | blokning 2-qatori `;<XNC kodi>` (masalan `;316601_01_003`, `;01_041x047x0`) |
| Kodlash | ASCII (namunalarda ASCII dan tashqari bayt yo'q; detal nomi yozilmaydi) |
| Qator oxiri | `CRLF`; har blok `M30` + `CRLF` bilan tugaydi, bloklar orasida bitta bo'sh qator (`CRLF`); fayl oxirida bo'sh qator yo'q |
| Sonlar | nuqta `.` bilan, **har doim 3 kasr** (`X1784.000`, `Q4.500`); K/J/I — butun |
| Birlik | mm |

### 1.1 Dasturlar tartibi (fayl ichida)

1. Avval **yuz tomoni** (`side="true"` yoki `"1"`) XNC operatsiyalari — loyiha XML dagi tartibda;
2. keyin **orqa tomon** (`side="false"` yoki `"2"`) operatsiyalari — yana XML tartibida.

Masalan 3167: `…;316701_03_026` dan keyin `;316701_01_018_2`, `;316701_01_027_2` (XML da ular `01_018` va `01_027` dan keyin turgan edi). Takrorlangan kodlar (bir xil `code` li ikki XNC) ikki alohida blok bo'lib, bir xil `;kod` bilan chiqadi.

Hamma 15 buyurtmada bloklar soni = XNC operatsiyalar soni (3173 dan tashqari): jami 1009 blok.

### 1.2 XNC kodi (barcha 5 stanokda umumiy)

`code` = `<mahsulot kodi>_<detal kodi>`: mahsulot kodi = buyurtma raqami + 2 xonali mahsulot raqami (`3166`+`01` → `316601`; `good code` atributi), detal kodi = Bazis pozitsiyasi `<shkaf>_<detal>` (`01_003`). Orqa tomon dasturlari Bazis tomonidan `_2` qo'shimchasi bilan kodlangan (`316701_01_018_2`). Qo'lda kiritilgan kodlar ham uchraydi (`01_041x047x0`).

---

## 2. Sintaksis

### 2.1 Blok tuzilishi

```
o<n>
;<XNC kodi>
$1 X<dx> Y<dy> Z<dz>
(1.000,1.000,0.000)G200
(1.000)G101
G300 …            ← 0..n ta arra (paz) o'tishi — HAMMA pazlar teshiklardan OLDIN
G81 …             ← 0..n ta teshik — XNC tartibida
G80               ← faqat kamida bitta G81 bo'lsa
M30
```

| Qator | Ma'nosi | Manba |
|---|---|---|
| `o<n>` | dastur raqami (fayl ichida 1 dan) | tartib |
| `;<kod>` | izoh — XNC operatsiya kodi | `operation@code` |
| `$1 X Y Z` | zagotovka o'lchami: X = `dx` (uzunlik), Y = `dy` (en), Z = `dz` (qalinlik) | `program@dx/dy/dz` |
| `(1.000,1.000,0.000)G200` | **o'zgarmas** (1009/1009). Ma'nosi noma'lum (masshtab/ofset?) | konstanta |
| `(1.000)G101` | **o'zgarmas** (1009/1009). Ma'nosi noma'lum (bazalash/maydon tanlash?) | konstanta |
| `G80` | sverlovka siklini bekor qilish; G81 bo'lmagan 11 dasturda yo'q | qoida |
| `M30` | dastur oxiri | konstanta |

### 2.2 `G81` — teshik

```
G81 X<a> Y<b> Z<chuqurlik> K<tomon> J0 I0 Q<diametr>
```

| Param | Ma'nosi |
|---|---|
| `K` | tomon: **1** — yuz (vertikal), **2** — chap qirra, **3** — o'ng qirra, **4** — yuqori qirra (XNC `bt`), **5** — pastki qirra (XNC `bb`) |
| `X`, `Y` | K ga qarab (2.4-jadval) |
| `Z` | chuqurlik, **musbat** son = XNC `dp` (o'tuvchi teshik uchun ham shunchaki `dz+3` = 19) |
| `Q` | asbob diametri (XNC `tool@d` — `Bore8` → `8.000`). Asbob nomi/raqami yozilmaydi: stanok asbobni K + diametr bo'yicha tanlaydi |
| `J0 I0` | o'zgarmas (8737/8737) |

### 2.3 `G300` — arra bilan paz (bitta o'tish)

```
G300 X<x> Y<y> Q<uzunlik> Z<chuqurlik> K0 J2 I0
```

| Param | Ma'nosi |
|---|---|
| `X`, `Y` | o'tishning **boshlanish nuqtasi** (stanok koordinatalarida), arra tanasining bir yon yuzasi (pastga qarang) |
| `Q` | paz uzunligi = \|P2 − P1\| (har doim musbat) |
| `Z` | chuqurlik = XNC `gr@dp` (musbat) |
| `K0 J2 I0` | o'zgarmas (126/126) |

**Muhim:** qatorda yo'nalish (X bo'ylab / Y bo'ylab, + yoki −) **yozilmaydi**. Masalan `X1784.000 Y146.750 Q1784.000` (−X ga) va `X136.250 Y1300.000 Q1300.000` (−Y ga) bir xil K/J/I bilan. Yo'nalishni stanok qanday bilishi — ochiq savol (6-bo'lim, 1-savol). Biz faqat namunani aynan takrorlay olamiz.

**Paz eni → bir necha o'tish.** XNC `gr@t` (paz eni) arra qalinligidan (`tool Cut4 d=4` → s = 4) katta bo'lsa, paz bir necha parallel o'tish bilan kesiladi. Stanok koordinatalarida P1→P2 yo'nalish birlik vektori u = (ux, uy), **o'ng normal** n = (uy, −ux) (Y yuqoriga qaragan tizimda harakatning o'ng tomoni). O'tishlar ofsetlari:

```
o_0 = t/2,  o_k = o_{k-1} − 3.0   (o_k > −t/2 + s bo'lguncha)
oxirgi  = −t/2 + s               (chekkaga "qisilgan" o'tish)
har o'tish:  X = P1x + n_x·o,  Y = P1y + n_y·o
```

Ya'ni o'tish nuqtasi — arraning **o'ng yon yuzasi**, arra tanasi harakatning chap tomoniga s mm cho'ziladi; birinchi o'tish pazning o'ng chekkasida, keyingilari 3 mm qadam bilan chapga, oxirgisi aniq chap chekkaga tegadi. Qadam 3.0 mm (s=4 da = 0.75·s yoki s−1 — ajratib bo'lmaydi; 6-bo'lim).

| t | s | o'tishlar (ofset) | namunadagi misol |
|---|---|---|---|
| 4 | 4 | +2 | 3167 `01_005`: `X84 Y82` (markaz chizig'i x=82) |
| 6 | 4 | +3, +1 | `Y603`, `Y601` (markaz 600) |
| 10.5 | 4 | +5.25, +2.25, −0.75, −1.25 | `Y146.75, 143.75, 140.75, 140.25` (markaz 141.5) |

Pazlar XNC tartibida, har paz o'tishlari ketma-ket; **hamma `G300` lar barcha `G81` lardan oldin** (XNC da `gr` oxirida bo'lsa ham — 3166 `13_001`).

`gr@c` (korreksiya) namunalarda faqat `0`; `c=1/2` uchun formula noma'lum.

### 2.4 Koordinatalar tizimi

**XNC (loyiha) koordinatalari** — barcha stanoklar uchun bir xil xulosa: boshlanish **chap-yuqori** burchak, X o'ngga (0…dx), **Y pastga** (0…dy): `y=0` — detalning **yuqori** qirrasi (`elt`), `y=dy` — **pastki** qirra (`elb`), `x=0` — chap (`ell`), `x=dx` — o'ng (`elr`). Dalil: orqa devor (ДВП) pazi «PAZ XDF» doim kromkasiz qirrada: `elb` kromkali detallarda paz `y=0` da (3166 `13_001`, 3168 `02_001`, 3178 `02_029`…), `elt` kromkali detallarda `y=dy` da (3166 `13_002`, 3168 `02_002`, 3180 `01_008`). Bu `services/xnc.py` dagi «chap-yuqori, Y pastga» qoidasiga mos.

**Startech koordinatalari:** boshlanish **chap-past** burchak (pastki = `elb` qirra), **Y yuqoriga**: `Y_st = dy − y`. X o'zgarmaydi. Z — chuqurlik (musbat).

| XNC buyruq | K | X | Y | Z | Q |
|---|---|---|---|---|---|
| `bf x y dp` (yuz) | 1 | `x` | `dy − y` | `dp` | `d` |
| `bl y z dp` (chap qirra) | 2 | `z` | `dy − y` | `dp` | `d` |
| `br y z dp` (o'ng qirra) | 3 | `z` | `dy − y` | `dp` | `d` |
| `bt x z dp` (yuqori qirra, y=0) | 4 | `x` | `z` | `dp` | `d` |
| `bb x z dp` (pastki qirra, y=dy) | 5 | `x` | `z` | `dp` | `d` |

Qirra teshiklarida qalinlik bo'yicha holat (`z`) **to'g'ridan-to'g'ri** yoziladi (`m=true` bo'lsa ham `z` atributi = dz/2). `m=false, z=8, dz=18` (3166 `14_017…14_024`, 24 teshik) → `X8.000` (TPA esa bu holda `dz−z = 10` yozadi — 6-bo'lim, 2-savol).

### 2.5 Orqa tomon (`side="false"` / `"2"`)

Orqa tomon dasturi alohida blok (fayl oxirida, 1.1). Detal **X bo'yicha ag'darilgan** deb hisoblanadi:

| | Yuz tomon | Orqa tomon |
|---|---|---|
| `bf` | `X=x, Y=dy−y` | `X=dx−x, Y=dy−y` |
| `gr` | P1, P2 → `(x, dy−y)` | P1, P2 → `(dx−x, dy−y)`, keyin oddiy o'tish formulasi |
| `bl/br` | K2/K3 | K3/K2 almashadi (**faraz** — namunalarda orqa tomonda qirra teshigi yo'q) |
| `bt/bb` | `X=x` | `X=dx−x` (**faraz**) |

Tekshirilgan: 37 orqa tomon dasturi (255 `bf`, 7 `gr`) — hammasi mos. Masalan 3170 `01_005_2` (dx=696, dy=776): `bf x=243 y=698` → `G81 X453.000 Y78.000` (696−243=453, 776−698=78).

### 2.6 Frezalash, massiv, boshqalar

* **Frezalash (`ms/ml/mac`) chiqmaydi.** 53 dasturda (65 kontur, `Mill8`) frezalash bor — ISO da G0/G1/G2/G3 yo'q; boshqa amallar odatdagidek chiqadi. Faqat frezalashdan iborat dastur — sarlavha + `M30`.
* `bf ac>1` (massiv) namunalarda uchramadi (hamma `ac=1`) — bizning generator massivni alohida `G81` qatorlarga yoyishi kerak (faraz).
* Ifodalar (`throughBoreDepth = dz+3.00`, `throughCutDepth`) hisoblangan qiymat bilan yoziladi (`Z19.000`).
* Asbob/tezlik/aylanish yozilmaydi.

---

## 3. MebeliX XNC → Startech moslik jadvali

| MebeliX `cmd` | Startech | Izoh |
|---|---|---|
| `DrillFront` | `G81 … K1` | `X=x, Y=dy−y, Z=DP, Q=D`; orqa: `X=dx−x` |
| `DrillLeft` | `G81 … K2` | `X=Z, Y=dy−y`; orqa: K3 (faraz) |
| `DrillRight` | `G81 … K3` | `X=Z, Y=dy−y`; orqa: K2 (faraz) |
| `DrillTop` | `G81 … K4` | `X=x, Y=Z` |
| `DrillBottom` | `G81 … K5` | `X=x, Y=Z` |
| `Groove` | `G300` × o'tishlar | 2.3 formula; arra qalinligi `T` asbob diametridan |
| `MillStart/Line/Arc*` | — | **chiqmaydi** (foydalanuvchini ogohlantirish kerak) |
| `Origin` | — | koordinatalarga qo'shiladi (`evaluate()` natijasi ishlatiladi) |
| `Var/Par/If…` | — | `evaluate()` bilan hisoblanadi; ISO ga faqat sonlar |

Generator (tekshirilgan prototip, Python):

```python
def f3(v): return f"{v:.3f}"
def block(n, code, dx, dy, dz, back, ops):
    saws, holes = [], []
    for o in ops:                      # services/xnc.evaluate() natijasi (mm, origin qo'shilgan)
        if o.kind.startswith("Drill"):
            K, X, Y = {"DrillFront": (1, o.X, dy-o.Y), "DrillLeft": (2, o.Z, dy-o.Y),
                       "DrillRight": (3, o.Z, dy-o.Y), "DrillTop": (4, o.X, o.Z),
                       "DrillBottom": (5, o.X, o.Z)}[o.kind]
            if back:
                if K in (1, 4, 5): X = dx - X
                else: K = 5 - K               # 2<->3
            holes.append(f"G81 X{f3(X)} Y{f3(Y)} Z{f3(o.DP)} K{K} J0 I0 Q{f3(o.D)}")
        elif o.kind == "Groove":
            x1, y1, x2, y2 = o.X1, dy-o.Y1, o.X2, dy-o.Y2
            if back: x1, x2 = dx-x1, dx-x2
            L = hypot(x2-x1, y2-y1); ux, uy = (x2-x1)/L, (y2-y1)/L; nx, ny = uy, -ux
            s, t = o.saw, o.W; offs = []; k = t/2
            while k > -t/2 + s + 1e-9: offs.append(k); k -= 3.0
            offs.append(-t/2 + s)
            saws += [f"G300 X{f3(x1+nx*k)} Y{f3(y1+ny*k)} Q{f3(L)} Z{f3(o.DP)} K0 J2 I0" for k in offs]
    lines = [f"o{n}", f";{code}", f"$1 X{f3(dx)} Y{f3(dy)} Z{f3(dz)}",
             "(1.000,1.000,0.000)G200", "(1.000)G101", *saws, *holes]
    if holes: lines.append("G80")
    return "\r\n".join(lines + ["M30"]) + "\r\n"
# fayl: yuz tomon bloklari, keyin orqa tomon bloklari; 99 tadan bo'linadi; bloklar "\r\n" bilan qo'shiladi
```

---

## 4. Tekshiruv

### 4.1 Avtomatik (barcha 15 buyurtma)

| Natija | Soni |
|---|---|
| Fayllar bayt-ma-bayt bir xil | 10 |
| Bir xil, faqat `-0.000`/`0.000` farqi | 6 |
| Farqli | 0 (3173 dan tashqari) |
| Bloklar (dasturlar) mos | 960/960 (923 yuz + 37 orqa); 3173: 27/51 (loyiha o'zgargan) |
| `G81` qatorlari | 8737 (K1 6132, K2 1094, K3 966, K4 259, K5 286) |
| `G300` qatorlari | 126 (60 ta `gr` dan) |

### 4.2 Qo'lda tekshirilgan detallar

**A. 3166 `01_003` «pb-bok»** — 694×500×16, yuz + chap qirra.

| XNC | Startech |
|---|---|
| `bl y=70 z=8 dp=34 Bore4.5` | `G81 X8.000 Y430.000 Z34.000 K2 J0 I0 Q4.500` (500−70=430) |
| `bl y=430 …` | `G81 X8.000 Y70.000 … K2` |
| `bf x=371 y=50 dp=9 Bore5` | `G81 X371.000 Y450.000 Z9.000 K1 J0 I0 Q5.000` |
| `bf x=644 y=8 dp=throughBoreDepth(=19) BoreTh8` | `G81 X644.000 Y492.000 Z19.000 K1 J0 I0 Q8.000` |

**B. 3166 `01_001` «pb-pol»** — 1250×500×16, pastki qirra (`bb`) + o'tuvchi teshik.

| XNC | Startech |
|---|---|
| `bb x=785.99 z=8 dp=32 Bore4.5` | `G81 X785.990 Y8.000 Z32.000 K5 J0 I0 Q4.500` |
| `bf x=8 y=70 dp=dz+3 BoreTh8` | `G81 X8.000 Y430.000 Z19.000 K1 J0 I0 Q8.000` |

**C. 3166 `00_009` «pol»** — 1784×283×16, LED pazi `gr x1=1784 y1=141.5 → x2=0 y2=141.5, t=10.5, dp=10.5, Cut4`.
Stanokda P1=(1784, 141.5), u=(−1,0), n=(0,+1):

```
G300 X1784.000 Y146.750 Q1784.000 Z10.500 K0 J2 I0   (o=+5.25)
G300 X1784.000 Y143.750 Q1784.000 Z10.500 K0 J2 I0   (o=+2.25)
G300 X1784.000 Y140.750 Q1784.000 Z10.500 K0 J2 I0   (o=−0.75)
G300 X1784.000 Y140.250 Q1784.000 Z10.500 K0 J2 I0   (o=−1.25 = −t/2+s)
```

**D. 3167 `01_005`** — 1518×547, to'rtburchak paz (4 ta `gr`, t=4): XNC `(82,465)→(82,82)` → stanokda (82,82)→(82,465), +Y, n=(+1,0) → `G300 X84.000 Y82.000 Q383.000 Z19.000`; `(82,82)→(1436,82)` → stanokda Y=465, +X, n=(0,−1) → `X82.000 Y463.000 Q1354.000`. Teshiklar keyin keladi.

**E. 3170 `01_005_2`** (orqa tomon, 696×776): `bf x=662 y=86 dp=12.5 Bore15` → `G81 X34.000 Y690.000 Z12.500 K1 J0 I0 Q15.000`; blok fayl oxirida (`o28`).

### 4.3 `-0.000`

Asl dastur paz o'tish nuqtalarini trigonometriya bilan hisoblaydi: nolga juda yaqin manfiy son `-0.000` bo'lib chiqadi (`X-0.000 Y597.000`). Bizning generator `0.000` yozishi mumkin — stanok uchun bir xil (lekin baribir sinab ko'rish tavsiya etiladi).

---

## 5. O'zgarmas va ma'lumotga bog'liq maydonlar

| O'zgarmas (stanok sozlamasi bo'lishi mumkin) | Ma'lumotdan |
|---|---|
| `(1.000,1.000,0.000)G200`, `(1.000)G101` | `o<n>`, `;kod`, `$1 X Y Z` |
| `G81 … J0 I0`, `G300 … K0 J2 I0` | `G81 X Y Z K Q`, `G300 X Y Q Z` |
| `G80`, `M30`, 99 dastur/fayl, 3 kasr | o'tishlar soni (paz eni va arra qalinligidan) |
| paz o'tish qadami 3.0 mm | tartib: yuz → orqa; pazlar → teshiklar |

Postprotsessor sozlamalari sifatida chiqarish tavsiya etiladi: fayldagi maksimal dasturlar (99), paz qadami (3.0), arra qalinligi (asbobdan), G200/G101 qiymatlari, `-0` normalizatsiyasi, edge-Z qoidasi (`z` yoki `dz−z`).

---

## 6. Minimal namuna (anonim)

Buyurtma 9999, mahsulot 01, ikki detal: 600×400×16 yon devor (yuzda 2 ta Ø5, chap qirrada Ø8) va orqa tomoni bor polka (6 mm ДВП pazi y=0 da).

```
o1
;999901_01_001
$1 X600.000 Y400.000 Z16.000
(1.000,1.000,0.000)G200
(1.000)G101
G81 X37.000 Y368.000 Z13.000 K1 J0 I0 Q5.000
G81 X37.000 Y32.000 Z13.000 K1 J0 I0 Q5.000
G81 X8.000 Y350.000 Z34.000 K2 J0 I0 Q8.000
G80
M30

o2
;999901_01_002_2
$1 X500.000 Y300.000 Z16.000
(1.000,1.000,0.000)G200
(1.000)G101
G300 X0.000 Y297.000 Q500.000 Z8.000 K0 J2 I0
G300 X0.000 Y299.000 Q500.000 Z8.000 K0 J2 I0
M30
```

(2-blok: XNC `gr x1=500 y1=0 → x2=0 y2=0, t=6, dp=8`, orqa tomon → X ag'dariladi: P1=(0,300)→P2=(500,300), +X, n=(0,−1) → Y=297, 299.)

---

## 7. Ochiq savollar (foydalanuvchiga)

1. **`G300` da yo'nalish yo'q.** Stanok X bo'ylab yoki Y bo'ylab kesishni qanday biladi (masalan `X136.250 Y1300.000 Q1300.000` — Y bo'ylab, `X1784.000 Y146.750 Q1784.000` — X bo'ylab)? `K0 J2 I0` ning ma'nosi nima? Stanok qo'llanmasidan G300 tavsifi kerak — aks holda pazlarni stanokda sinab ko'rish shart.
2. **Qirra teshigining qalinlik bo'yicha holati:** `m=false, z=8` (18 mm detal) Startech da `X8`, TPA va Homag da `10` (= dz − z). Qaysi biri to'g'ri — z yuz tomondan o'lchanadimi yoki stol tomondan? (3166 `14_017` «qosh», 18 mm — stanokda tekshirib ko'rish.)
3. **Frezalash chiqmaydi** — bu stanokda freza yo'qmi (faqat prisadka), yoki postprotsessor sozlamasida o'chirilganmi? Frezalashli detallar (masalan kesik burchakli polkalar) qaysi stanokda ishlanadi?
4. `(1.000,1.000,0.000)G200` va `(1.000)G101` nimani bildiradi (bazalash / masshtab / stol zonasi)? Detalni stolga qaysi burchak bilan qo'yiladi (chap-past = `elb`+`ell` burchagi)?
5. Paz o'tish qadami 3 mm — stanok sozlamasimi (arra 4 mm, 75 %), yoki postprotsessorda qat'iymi? Boshqa arra qalinligida nima bo'ladi?
6. Orqa tomondagi qirra teshiklari (namunada yo'q): K2↔K3 almashinishi to'g'rimi?
7. Bitta faylda 99 dasturdan ortiq bo'lmasligi — stanok cheklovimi? `o` raqami 1 dan qayta boshlanishi shartmi?
