# IMA ImaWop — `.FMC` postprotsessori

> Manba: korxonaning o'z namunalari — `post prtsessorlar/ONLINE_2026-10-04/yangi_formatlar/ima_wop.zip` (**36 fayl**, bitta
> loyihaning 36 XNC operatsiyasi) va o'sha loyiha (`loyiha.project`). Faqat chiqish fayllari va loyiha o'qildi; kod noldan
> yozilgan. Internet tadqiqoti — `WEB_missing_formats.md` 8-bo'lim (u yerdagi 2.6 versiya bloklari bu namunaga mos emas —
> namuna `…60` avlodi bloklaridan iborat).
>
> **Holat:** teshik (yuz, 4 qirra), freza konturi (chiziq + markazli yoy), kromka belgilari, orqa tomon (yuz teshigi) —
> tushunilgan. Generator `backend/app/services/ppfmt/ima_wop.py`; tekshiruv `tools/bench/pp_online_check_ima_hops.py`:
> **«namunadagidek» rejimda 36/36 bayt-ma-bayt**, standart rejimda 32/36 (4 frezali faylda faqat `MPY` — 4-bo'limga qarang).

---

## 1. Fayl

| Xususiyat | Qiymat |
|---|---|
| Fayl | bitta XNC operatsiyasi = bitta `<XNC kodi>.FMC` (kengaytma katta harfda) |
| Takror kod | `<kod> (1).FMC` … (fayl ichidagi `BEZB` — takror belgisisiz kod) |
| Tuzilishi | INI ga o'xshash: `[BLOK]` qatori, keyin `KALIT=qiymat` qatorlari; ichki (bog'liq) bloklar — `[[BLOK]]` |
| Qator oxiri | CRLF, oxirgi qatordan keyin ham; bo'sh qator yo'q |
| Kodlash | namunada faqat ASCII; generator cp1251 yozadi (tekshirilmagan) |
| Sonlar | nuqta, **2 kasrgacha**, ortiqcha nollarsiz (`292.3135 → 292.31`, `130.309 → 130.31`, `12.5`, `336`) |
| Koordinatalar | XNC dagidek: X o'ngga, Y pastga (burish / ko'zgusiz); orqa tomon dasturi — X ag'darilgan (`FTL − x`) |

## 2. Bloklar tartibi

```
[PGKOPF60]      detal sarlavhasi
[PRODUZ60]      mahsulot / soni
[BOHRPO60]      teshiklar guruhini optimallash (doimiy; teshik bo'lmasa ham yoziladi)
… amallar (XNC dasturi tartibida) …
[PRODBLOCK] …   har kromka uchun bittadan (top, bottom, left, right tartibida)
```

### 2.1 Sarlavha

| Blok | Maydon | Qiymat |
|---|---|---|
| `PGKOPF60` | `BEZB` | XNC kodi |
| | `FTL`, `FTB`, `FTD` | uzunlik (X), en (Y), qalinlik |
| | `KOM1` | detal nomi, **bo'sh joylarsiz** (`01_001 tr → 01_001tr`) |
| | `KOM2` | bo'sh |
| `PRODUZ60` | `AFB=1`, `WDA=1`, `KAF=` + bitta bo'sh joy | doimiy |
| | `BEZB`, `KOM` | mahsulot nomi, bo'sh joylarsiz |
| | `JON` | `1` (manbasi noma'lum — ochiq savol) |
| | `STZ` | XNC soni (detal soni) |
| `BOHRPO60` | `BEZB=Hole group optimization`, `GPN=1`, `OPA=2`, `AFB=1` | doimiy |

### 2.2 Teshiklar

Yuz teshigi:

```
[VBDMES60]
BEZB=Vertical drilling
DM=<diametr>
TI=<chuqurlik>
X=…
Y=…
GRP=1
AFB=1
PKTBEZUG_XY=0
```

Qirra teshigi (maydonlar tartibi boshqacha — `BEZB` oxirida):

```
[HBXPLU60]            ← blok nomi qirraga qarab
DM=<diametr>
TI=<chuqurlik>
Y1=<qirra bo'ylab koordinata>     (HBY… da X1)
GRP=1
Z=<balandlik>
BEZB=Horizontal drilling X        (HBY… da «Horizontal drilling Y»)
AFB=1
```

| XNC buyrug'i | Qirra | Blok | Koordinata |
|---|---|---|---|
| DrillLeft | x = 0 | `HBXPLU60` (parma +X yo'nalishida) | `Y1 = y` |
| DrillRight | x = FTL | `HBXMIN60` | `Y1 = y` |
| DrillTop | y = 0 | `HBYPLU60` | `X1 = x` |
| DrillBottom | y = FTB | `HBYMIN60` | `X1 = x` |

Qirradagi `X` / `Y` yozilmaydi (blok nomi qirrani belgilaydi). Asbob ko'rsatilmaydi — stanok diametr (`DM`) bo'yicha tanlaydi.

### 2.3 Freza konturi

Har kontur (MillStart + elementlar) ikki marta yoziladi: avval kontur ta'rifi, keyin frezalash chaqiruvi ichida o'sha elementlar.

```
[KDEFANFC]                       kontur boshi
BEZB=Start path Kontur1
PKTBEZUG_XY=0
X=…  Y=…                         boshlang'ich nuqta
HP_RADIUS=0
JUS=0
KNAME=Kontur1                    Kontur<N> — fayl ichida 1 dan
SICHTBAR=1
TH=-10
TNAM=Courier New
[G1] BEZB=Line | AFB=1 | EB=0 | PKTBEZUG_XY=0 | X | Y | Z=0
[G2]/[G3] BEZB=Arc | AFB=1 | EB=0 | PKTBEZUG_XY=0 | MPX | MPY | RAD | X | Y | Z=0
[KDEFENDE] BEZB=End path
[KTFRAE60]                       frezalash
SWKZID=IMA 601 | KNAME=Kontur1 | KENNUNG=(NULL) | DEFRICHTUNG=1 | Z=0 | EBG=0 | KD=0 | ROFFSET=0 | TRKOR=1 | KTDAT=0 |
LGEAN=0 | LGEAB=0 | EVS=0 | BEZU=Milling | AFBU=1 | SINDEX=1 | SKENNUNG=KENNUNG$ | SOFFSET=0 | SOFFSETTYP=0 | EINDEX=-1 |
EKENNUNG=KENNUNG$ | EOFFSET=0 | EOFFSETTYP=0 | UPCALC=0
[[KAFRAE60]]
SWKZID=IMA 601 | BEZB=Call mill | AFB=1 | X | Y | Z=0 | EBG=0 | KD=0 | TRKOR=1 | PKTBEZUG_XY=0 | EVS=0 | LGEAB=0 | LGEAN=0
[[G1]] / [[G2]] / [[G3]]         o'sha elementlar (maydonlari bir xil)
[[KDEFENDE]] BEZB=End path
```

(yuqorida `|` — qator ko'chirish o'rnida, qisqalik uchun.)

* Yoy: XNC `dir="true"` → `G3`, aks holda `G2`; `MPX` / `MPY` — markaz, `RAD` — radius, `X` / `Y` — oxirgi nuqta.
* `TRKOR` — radius korreksiyasi = XNC `C` (namunada faqat `1`).
* `Z` — namunada `0` (kesim o'tuvchi: chuqurlik = qalinlik). Generator `Z = qalinlik − chuqurlik` yozadi (faraz).

### 2.4 Kromka belgisi

Detalning har kromkasi uchun (tartib: top, bottom, left, right) — detal tashqarisida, chetdan 20 mm narida 5 mm enli
to'rtburchak va kromka nomi yozuvi:

```
[PRODBLOCK]
PRODSTATUS=1
BEZ=EDGEBEND-<kromka nomi>
[[KDEFANFC]]
BEZB=Start path
PKTBEZUG_XY=0
X=…  Y=…                 boshlang'ich nuqta — tomon o'rtasi
HP_RADIUS=0
JUS=<kod>
KNAME=<kromka nomi>       (nom boshidagi bo'sh joy saqlanadi)
SICHTBAR=1
TH=-20
TNAM=Courier New Bold
[[G1]] AFB=1 | EB=0 | PKTBEZUG_XY=0 | X | Y | Z=0      × 5 (BEZB yo'q)
[[KDEFENDE]]
BEZB=End path
```

| Tomon | `JUS` | Boshi | Keyingi 5 nuqta |
|---|---|---|---|
| top (y=0) | 21 | (L/2, −20) | (L, −20), (L, −25), (0, −25), (0, −20), (L/2, −20) |
| bottom (y=W) | 1 | (L/2, W+20) | (L, W+20), (L, W+25), (0, W+25), (0, W+20), (L/2, W+20) |
| left (x=0) | 12 | (−20, W/2) | (−20, W), (−25, W), (−25, 0), (−20, 0), (−20, W/2) |
| right (x=L) | 10 | (L+20, W/2) | (L+20, W), (L+25, W), (L+25, 0), (L+20, 0), (L+20, W/2) |

## 3. Asboblar

* Teshiklar: diametr bo'yicha (`DM`) — namunada «nomdan foydalanish» belgilanmagan edi. Jadvalda parma nomi berilsa fayl
  qanday o'zgarishi noma'lum — generator nomni e'tiborsiz qoldiradi.
* Freza: «Инструменты» jadvalida `mill:front:<d>` uchun nom bo'lishi **shart** (`tooling.need_tool`; bo'lmasa xato —
  namuna dasturi ham bo'sh nom bilan fayl chiqarmaydi). Lekin namunada jadvaldagi nom faylga chiqmagan: `SWKZID=IMA 601`
  (generator konstantasi `MILL_SWKZID`).

## 4. Namunadan farq (ataylab)

Namunaning barcha yoylarida `MPY = MPX` (markaz `(165.5; 282.31)` uchun `MPX=165.5`, `MPY=165.5`) — markazning Y o'rniga X
yozilgan, ya'ni aniq xato. Generator standart holatda **to'g'ri** `MPY` yozadi; `ima_wop.MPY_AS_SAMPLE = True` — namunadagi
kabi (tekshiruv skripti ikkala rejimni ko'rsatadi).

## 5. Ochiq savollar (namunada yo'q)

1. `SWKZID=IMA 601` — doimiymi yoki jadvaldagi asbob nomi shu yerga yozilishi kerakmi (namunada nom boshqa edi, faylda `IMA 601`).
2. `MPY` — stanok yoyni `RAD` bo'yicha quradimi (u holda namunadagi xato sezilmaydi) yoki markaz bo'yichami.
3. Paz (Groove) bloki — namuna yo'q; generator xato beradi (jim o'tkazib yuborilmaydi).
4. O'tuvchi yuz teshigi (chuqurlik ≥ qalinlik) — alohida blok / bayroq bormi (generator oddiy `VBDMES60`, `TI` = chuqurlik).
5. Qirra teshigi `Z` bazasi (yuqoridan / pastdan) — namunada hammasi qalinlik o'rtasida (8 / 16).
6. Chuqurligi qalinlikdan kichik freza: `Z` qiymati (generator: `qalinlik − chuqurlik`), `TRKOR` 0 / 2 kodlari.
7. Bir nechta kontur: ta'rif va chaqiruvlar navbatma-navbatmi (generator shunday) yoki avval hamma ta'riflar.
8. Teshik va freza aralash dasturda tartib (generator: XNC dasturi tartibi; namunada qirra teshiklari doim yuz teshiklaridan oldin).
9. Orqa tomon dasturida chap / o'ng kromka belgisi (generator almashtiradi), qirra teshigi va freza (X ag'darilgan — faraz).
10. `JON` (namunada `1`), `KAF`, `WDA`, `GPN`, `OPA` ma'nosi; mahsulotsiz detalda `BEZB` / `KOM`.
11. Kirill harfli nomlar kodlashi.
