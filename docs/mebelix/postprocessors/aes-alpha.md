# AES Alpha — `.ss` kesish fayli (beam saw)

> Manba: `post prtsessorlar/PILNIY APPARAT/AES Alpha/*.ss` (12 fayl, buyurtmalar 3168–3182).
> Xuddi shu format `AESS Alpha (SS)` papkasida ham bor — u alohida hujjatda: [`aess-alpha-ss.md`](aess-alpha-ss.md).
> Ikkala papkadagi 33 ta faylning barcha «sozlama» maydonlari bayt-baytgacha bir xil — demak bu **bitta postprotsessor**.
> Tekshiruv uchun «ground truth»: shu buyurtmalarning Nanxing AutoCUT `.CUT` XML fayllari (`Nanxing NXCutSAW/*.CUT`),
> ularda har bir detalning varaqdagi koordinatasi (Px/Py/X/Y) bor.
> Mijoz ismlari hujjatda «mijoz» bilan almashtirilgan.

Format yozuv nomlari turkcha so'zlardan: `BSL` (başlık — sarlavha), `KON` (konfigürasyon), `LMT` (limit),
`OZL` (özellik — list/material), `URN` (ürün — detal turi), `PRT` (parça — detal ma'lumoti), `PNL` (panel — karta),
`BASLA` (başla — boshlash), `KES` (kes — kesim), `BITIR` (bitir — tugatish).

---

## 1. Ishlab chiqariladigan fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.ss` (kichik harf) |
| Bir fayl = | **bitta buyurtma × bitta material** (GibLab CS operatsiyasi). Zip yo'q, papka ichida tekis. |
| Fayl nomi | `<loyiha nomi, bo'shliq→_>_<material nomi sanitizatsiya>.ss`, masalan `3171_mijoz_LDSP_DUB_VATAN_TEKSTURA.ss`, `3169_mijoz_LDSP_METALIK_SHAGREN_5.03_kv.ss` |
| Material nomini sanitizatsiya | bo'shliq va `(`/`)` ketma-ketligi → bitta `_`; nuqta va apostrof saqlanadi (`5.03_kv`, `mijoz'ism`). Misol: `XDF 2800x2070 mm  5.8 kv` → `XDF_2800x2070_mm_5.8_kv`; `LDSP UD ` → `LDSP_UD_`; `LDSP UD (110197)_diffuseOriginal` → `LDSP_UD_110197__diffuseOriginal` |
| Kodlash | sof ASCII (namunalarda 0x7F dan katta bayt yo'q, BOM yo'q). Kirill matn qanday yozilishi noma'lum (savol Q1). |
| Qator oxiri | `CRLF`, oxirgi qatordan keyin ham `CRLF` bor |
| Ajratuvchi | vergul `,`; maydonlar **qat'iy kenglikda** (o'ngga tekislangan, bo'shliq bilan to'ldirilgan) |
| O'nlik ajratuvchi | nuqta `.`; o'lchamlar `%9.2f` (masalan `  1400.00`) |
| Birlik | mm |

AES Alpha papkasida 12 fayl: 3168, 3169, 3170, 3171, 3173, 3174, 3175, 3177, 3178, 3179, 3180, 3182 — hammasi bitta
material (LDSP/LMDF 16 mm, 2750×1830). **3167 va 3181 buyurtmalari yo'q**, holbuki ular uchun Nanxing `.CUT`
fayllari mavjud (savol Q7). XDF/oyna kabi ikkinchi materiallar uchun bu papkada fayl yo'q.
`BSL2` dagi vaqt hamma faylda `16:48` — bitta seansda eksport qilingan.

---

## 2. To'liq tuzilma

Fayl qat'iy tartibdagi bloklardan iborat:

```
BSL1 BSL2 BSL3                 sarlavha (1 marta)
KON1 KON2 KON3 LMT1 ASP1 ASP2  konfiguratsiya (1 marta)
{OZL1 OZL2 OZL3}×M             list turlari (CS dagi har bir list/qoldiq yozuvi uchun bitta blok)
{URN1 URN2 URN3}×N             detal turlari ro'yxati (CS dagi har bir detal qatori uchun)
{PRT1 PRT2 PRT3 PRT4 PRT5}×N   o'sha detallarning qo'shimcha ma'lumoti (xuddi shu tartibda)
{PNL1..PNL5 BASLA KES1×k}×P    kartalar (raskroy sxemalari)
BITIR                          fayl oxiri
```

Quyida `fN` — yozuv nomidan keyingi N-maydon (vergul bo'yicha). «Kenglik» — namunalarda kuzatilgan aniq belgi soni.
«Doimiy» — 33 ta faylning hammasida bir xil.

### 2.1 Sarlavha

| Yozuv | Maydon | Kenglik/format | Ma'nosi | Namunalar |
|---|---|---|---|---|
| BSL1 | f1 | `001` | doimiy (fayl/ish raqami?) | `001` |
| BSL1 | f2 | erkin | GibLab loyiha nomi (`project/@name`) | `3171 mijoz` |
| BSL2 | f1 | `dd.mm.yyyy` | eksport sanasi | `27.09.2026` |
| BSL2 | f2 | `HH:MM` | eksport vaqti | `16:48` |
| BSL2 | f3 | bo'sh | — (qator `,` bilan tugaydi) | |
| BSL3 | f1..f4 | `From GibLab`,`1.0`,``,`` | doimiy: generator nomi va versiyasi | |

### 2.2 Konfiguratsiya

| Yozuv | Maydon | Format | Ma'nosi (ishonch) | Qiymat |
|---|---|---|---|---|
| KON1 | f1,f2,f3 | 1 belgi | doimiy bayroqlar; ma'nosi noma'lum (M=metric? N=no?) — Q2 | `M`,`M`,`N` |
| KON1 | f4 | `%4d` | doimiy | `   1` |
| KON1 | f5 | 1 belgi | doimiy | `0` |
| KON2 | f1 | `%9.2f` | **arra qalinligi (kerf)** = `tool.cutting/@swSawthick` (yuqori ishonch: 3 mm, geometriya buni tasdiqlaydi) | `     3.00` |
| KON2 | f2 | `%9.2f` | ikkinchi 3.00 — ehtimol kerf takrori / podrezka arrasi / `swSawthickDiv=-1` ning yechilgan qiymati — Q3 | `     3.00` |
| KON2 | f3 | `%5.2f` | doimiy | ` 0.00` |
| KON2 | f4..f6 | `%9.2f` | doimiy | `     0.00` |
| KON3 | f1 | `%9.2f` | doimiy | `     0.00` |
| LMT1 | f1 | `%9.2f` | **material qalinligi** (`sheet/@t`) | `16.00`, XDF da `3.00`, akrilda `18.00` |
| LMT1 | f2 | `%9.2f` | **paket (stopka) maksimal balandligi** = `swPackageHeight` (40) | `    40.00` |
| ASP1 | f1..f3 | 6 bo'shliq | bo'sh (ishlatilmagan) | |
| ASP2 | f1..f3 | 11 bo'shliq | bo'sh | |

### 2.3 List (varaq) bloki — `OZL1/OZL2/OZL3`

CS operatsiyasidagi **har bir list yozuvi** (`good typeId="sheet"` ichidagi `part`, ya'ni standart list yoki qoldiq)
uchun bitta blok, operatsiyadagi tartibda. Kartalar `PNL1 f1` orqali shu bloklarga 1-dan boshlab murojaat qiladi.

| Yozuv | Maydon | Format | Ma'nosi | Misol |
|---|---|---|---|---|
| OZL1 | f1 | `*****` | doimiy (list kodi/ombor ID joyi?) — Q4 | `*****` |
| OZL1 | f2 | `%5d` | **ishlatilgan listlar soni** = shu list yozuvining `usedCount` = shu OZL ga tegishli kartalar `PNL1 f3` yig'indisi. 0 bo'lishi mumkin (list ro'yxatda bor, lekin ishlatilmagan). | `    4` |
| OZL1 | f3 | `%8.3f` | doimiy `9.860` — ma'nosi noma'lum (Q4) | `   9.860` |
| OZL1 | f4 | `%9.2f` | **list eni** (W, `part/@w`) | `  1830.00`, `  2070.00`, qoldiqlarda `450.00`, `1160.00` |
| OZL1 | f5 | `%9.2f` | **list uzunligi** (L, `part/@l`) | `  2750.00`, `2800.00`, `2440.00` |
| OZL1 | f6..f9 | `%9.2f` | 4 ta torsovka (chet kesish) qiymati; loyihada `cTrimL=2`, `cTrimW=2`. Qaysi biri qaysi tomonga — Q5 | `     2.00` ×4 |
| OZL2 | f1 | erkin | material nomi (`good/@name`, o'zgarishsiz, oxiridagi bo'shliq ham saqlanadi: `LDSP UD `) | `LDSP DUB VATAN TEKSTURA` |
| OZL3 | f1 | `%-17s` | doimiy `1` + 16 bo'shliq (Q4) | `1                ` |
| OZL3 | f2,f3 | `%9.2f` | yana 2.00, 2.00 — ehtimol L va W bo'yicha torsovka (cTrimL/cTrimW) | `     2.00` |

Ko'p OZL namunasi (qoldiq + butun list):
```
OZL1,*****,    1,   9.860,   450.00,  2750.00,     2.00,     2.00,     2.00,     2.00   ← qoldiq 2750×450, usedCount=1
OZL1,*****,   10,   9.860,  1830.00,  2750.00,     2.00,     2.00,     2.00,     2.00   ← butun list, 10 ta
```
(3174: kartalar `PNL1,01,...` ×1 va `PNL1,02,...` jami 10.) 2029 da esa `1160×2750` qoldiq `1`, `1830×2750` list `0`.

### 2.4 Detal turlari — `URN1/URN2/URN3`

CS operatsiyasidagi har bir **detal qatori** (`<operation><part id=…>` havolalari, operatsiyadagi aynan shu tartibda)
uchun bitta blok. Bir xil nomli ikki qator bo'lsa — ikkita alohida URN (nom kalit emas, **tartib raqami** kalit).

| Yozuv | Maydon | Format | Ma'nosi |
|---|---|---|---|
| URN1 | f1 | `%5d` | detal soni (`part/@count`) |
| URN1 | f2 | `%5d` | yana soni (33 faylda hamisha f1 ga teng; ehtimol «kesiladigan soni» — Q6) |
| URN1 | f3 | `%9.2f` | **uzunlik** = `part/@l` (kesish/zagotovka o'lchami; `l` yo'q bo'lsa `dl`) |
| URN1 | f4 | `%9.2f` | **en** = `part/@w` (yo'q bo'lsa `dw`) |
| URN1 | f5 | 1 bo'shliq | doimiy bo'sh |
| URN1 | f6 | `N` | doimiy (tekstura/aylantirish bayrog'i joyi? namunalarda tekstura bor/yo'q detallarda ham `N`) — Q8 |
| URN2 | f1 | 8 bo'shliq | bo'sh |
| URN2 | f2,f3 | `%9.2f` | URN1 f3/f4 ning takrori (hamisha teng) |
| URN3 | f1 | ` 1` | doimiy |
| URN3 | f2 | `' %d'` | detalning 1-dan boshlangan tartib raqami (`KES1 f4` shu raqamga murojaat qiladi) |

### 2.5 Detal ma'lumoti — `PRT1..PRT5`

URN bloklari tugagach, xuddi shu tartibda N ta PRT bloki keladi.

| Yozuv | Maydon | Format | Ma'nosi |
|---|---|---|---|
| PRT1 | f1 | `%5d` | soni (= URN1 f1) |
| PRT1 | f2 | `' %d'` | **0-dan** boshlangan tartib raqami (= URN3 f2 − 1) |
| PRT1 | f3,f4 | `%9.2f` | uzunlik, en (= URN1 f3/f4) |
| PRT1 | f5 | ` 1` | doimiy |
| PRT1 | f6 | 24 bo'shliq | bo'sh |
| PRT1 | f7 | bo'sh | — |
| PRT1 | f8 | erkin | **detal nomi** (`part/@name`, masalan `01_002 tom`) — yorliq uchun |
| PRT1 | f9 | bo'sh | — |
| PRT1 | f10 | erkin | **mahsulot kodi** (`good[product]/@code`, masalan `317101`; bo'sh bo'lishi mumkin) |
| PRT1 | f11 | erkin | **mahsulot nomi** (`good[product]/@name`, masalan `01 parta`) |
| PRT1 | f12 | 16 bo'shliq | bo'sh |
| PRT2 | f1 | ` 0` | doimiy |
| PRT2 | f2 | ` ` | doimiy |
| PRT2 | f3 | `%9.2f` | material qalinligi (= LMT1 f1) |
| PRT2 | f4 | bo'sh | qator `,` bilan tugaydi |
| PRT3 | f1 | `0000` | doimiy |
| PRT3 | f2,f4,f5,f7,f8,f10,f11,f13 | 8 bo'shliq | bo'sh to'ldiruvchilar |
| PRT3 | f3 | erkin | **chap** (`ell`) kromka nomi |
| PRT3 | f6 | erkin | **yuqori** (`elt`) kromka nomi |
| PRT3 | f9 | erkin | **o'ng** (`elr`) kromka nomi |
| PRT3 | f12 | erkin | **past** (`elb`) kromka nomi |
| PRT4 | f1..f4 | `%9.2f` | o'sha tomonlarning kromka **qalinligi** (chap, yuqori, o'ng, past); kromkasiz tomon `0.00`. Namunalarda faqat `1.00` (`band/@t=1`, hatto «06-19» lentalar ham t=1) — Q9 |
| PRT4 | f5 | `1` | doimiy |
| PRT4 | f6 | 20 bo'shliq | bo'sh |
| PRT5 | f1..f4 | ` `,`N`,5 bo'shliq,5 bo'shliq | doimiy |

Kromka nomi = kromka operatsiyasi (`EL`) materiali bo'lgan `good[band]/@name` (bosh/oxiridagi bo'shliqlar olib tashlangan),
masalan `1-19 dub votan`, `06-19  SASNA`, `1-35  dub Votan` (ichki qo'sh bo'shliq saqlanadi).
Tomonlar tartibi **chap, yuqori, o'ng, past** (L, T, R, B) — 898 ta tekshirilgan qatorning 886 tasida aniq mos
(qolgani loyihaning boshqa versiyasidan kelgan farqlar).

### 2.6 Kartalar — `PNL1..PNL5`, `BASLA`, `KES1`

Har bir **noyob** karta uchun:

| Yozuv | Maydon | Format | Ma'nosi |
|---|---|---|---|
| PNL1 | f1 | `%02d` | qaysi OZL blokidagi list (1-dan) |
| PNL1 | f2 | `S`/`L` | **birinchi daraja kesimlari yo'nalishi** (pastga qarang) |
| PNL1 | f3 | `%d` | shu kartadan nechta list kesiladi (takrorlanish soni; 1, 2, 4 kuzatilgan) |
| PNL1 | f4 | `0` | doimiy |
| PNL2 | f1..f5 | ` 0.0000`, `%14.4f`×3, `%12.3f` | doimiy `0,0,0,0,1.000` — Q10 |
| PNL3 | f1..f4 | 5 bo'shliq | bo'sh |
| PNL4 | f1..f3 | 11 bo'shliq | bo'sh |
| PNL5 | f1..f4 | 6,6,12,12 bo'shliq | bo'sh |
| BASLA | — | — | kesimlar ro'yxati boshlanishi |
| KES1 | f1 | `%02d` | **kesim darajasi** 01..04 (namunalarda max 04 = `swMaxturns=4`) |
| KES1 | f2 | `%9.2f` | kesib olinadigan bo'lak eni (mm) yoki maxsus `-0.50` |
| KES1 | f3 | `0`/`1` | `1` = bo'lak tayyor **detal**; `0` = oraliq bo'lak (keyingi darajada bo'linadi) yoki `-0.50` |
| KES1 | f4 | `%03d` | detal bo'lsa URN tartib raqami (1-dan), aks holda `000` |

`BITIR` — oxirgi kartadan keyin bir marta.

---

## 3. Kesish rejasi qanday kodlangan

**Guillotine daraxt, oldindan tartib (pre-order) bilan yozilgan.**

* Daraja 01 — listdan polosalar (strip). Daraja 02 — polosadan bo'laklar (kesish yo'nalishi 90° buriladi).
  Daraja 03 — 02-bo'lakdan bo'laklar (yana buriladi), daraja 04 — 03-bo'lakdan.
* Yo'nalish `PNL1 f2` bilan:
  * `S` — 01-darajadagi qiymatlar list **uzunligi** (X, 2750) bo'ylab o'lchanadi; polosa listning to'liq eni (Y, 1830) bo'ylab ketadi
    (AutoCUT da polosa `Y = list Y`). 02-daraja — Y bo'ylab, 03 — X, 04 — Y.
  * `L` — 01-daraja list **eni** (Y) bo'ylab; polosa to'liq uzunlikda. 02 — X, 03 — Y, 04 — X.
* Har bir `KES1` qiymati — kesib olinadigan bo'lak **eni** (kesish yo'nalishi bo'yicha). Bo'lakning ikkinchi o'lchami —
  ota-bo'lakning shu o'qdagi o'lchami. Tekshiruv: 33 faylda 1537 ta detal yozuvining **hammasida** ikkinchi o'lcham
  ota-bo'lak o'lchamiga aniq teng va `KES1 f2` URN o'lchamlaridan biriga teng. Demak detalning burilishi (90°)
  alohida maydon emas — qaysi o'lchami `KES1` da kelganidan aniqlanadi.
* `f3=0` va musbat qiymat — keyingi qatorlarda bolalari bor bo'lak. Hech bir faylda «bolasiz 0-bo'lak» yo'q:
  **chiqindi va qoldiqlar umuman yozilmaydi**, polosa oxiridagi ortiqcha ham yozilmaydi.
* Bir xil polosalar/detal takrorlansa — har biri alohida `KES1` qatori (masalan `KES1,04,548.00,1,006` ikki marta).
  Faqat **butun karta** takrori `PNL1 f3` bilan siqiladi.
* **`-0.50` qatori**: har bir 03- va 04-daraja guruhining **birinchi** yozuvi hamisha `KES1,0n,    -0.50,0,000`
  (465 + 158 holat, istisnosiz); 01/02 darajalarda hech qachon yo'q. Bu stanok uchun «burilgandan keyin bosh (torets) kesimi»
  buyrug'i deb taxmin qilinadi (Q11). Geometriyaga ta'sir qilmaydi (pastga qarang).
* Kesim hisobi (namunalardan chiqarilgan, kerf=3, torsovka=2):
  * 01 va 02 darajada: `Σ qiymat + 3·n ≤ (list o'lchami − 2·2) − 3` — ya'ni har ikki chetda 2 mm torsovka + 3 mm kerf.
    Birinchi bo'lak koordinatasi 5 mm dan boshlanadi (AutoCUT dagi `Px=5`).
  * 03 va 04 darajada: bo'lak ota-bo'lak chetidan (0 dan) boshlanadi, oxirida ≥ 5 mm qoladi
    (`Σ + 3·n ≤ ota − 2`). Bitta istisno (3177): `82 + 3 + 322 = 407` — oxirida joy qolmagan.
* Geometrik tekshiruv: `.ss` dan detal to'rtburchaklarini (x, y, uzunlik, en) yuqoridagi qoidalar bilan hisoblab,
  shu buyurtmalarning AutoCUT `.CUT` faylidagi barg detallar (Px, Py, X, Y × Layout Count) bilan solishtirildi —
  **32/32 fayl to'liq mos** (2032 XDF uchun .CUT yo'q). 01-daraja polosalar ketma-ketligi va `S/L` yo'nalishi ham 32/32 mos.
* Paket (kniga): faylda alohida stopka soni yo'q; `PNL1 f3` (bir xil listlar soni) + `LMT1` (qalinlik, maks. paket
  balandligi 40) beriladi — paketlashni stanok o'zi hisoblaydi deb taxmin (Q12).
* Yorliq ma'lumoti: `PRT1` dagi detal nomi, mahsulot kodi/nomi va `PRT3/PRT4` dagi kromka — boshqa yorliq yozuvi yo'q.

Namuna (3171, 1-karta, `S`, 2 list, list 2750×1830):
```
KES1,01,  1400.00,0,000      polosa X=1400 (to'liq Y)
KES1,02,  1750.00,1,001        → detal #1 1400×1750
KES1,01,  1175.00,0,000      polosa X=1175
KES1,02,  1718.00,0,000        bo'lak Y=1718
KES1,03,    -0.50,0,000          (03-daraja boshi markeri)
KES1,03,   584.00,1,002          → detal #2 1718×584 (X bo'yicha 584)
KES1,03,   583.00,0,000          bo'lak X=583
KES1,04,    -0.50,0,000            (04-daraja boshi)
KES1,04,   590.00,1,005            → detal #5 590×583
KES1,04,   548.00,1,006            → detal #6 548×583
KES1,04,   548.00,1,006            → detal #6 yana
```
Tekshiruv: 1400+3+1175+3 = 2581 ≤ 2743; 584+583+2·3 = 1173 ≤ 1175−2; 590+548+548+3·3 = 1695 ≤ 1718−2.

---

## 4. Loyiha → maydonlar xaritasi (tekshirilgan)

| Loyiha (GibLab `.project`) | `.ss` maydon |
|---|---|
| `project/@name` | BSL1 f2 |
| CS `material` → `good[sheet]/@name` | OZL2; fayl nomi qismi |
| `good[sheet]/@t` | LMT1 f1, PRT2 f3 |
| CS dagi list `part/@w`, `@l`, `@usedCount` | OZL1 f4, f5, f2 |
| CS `cTrimL`, `cTrimW` (2) | OZL1 f6..f9, OZL3 f2..f3 (taxmin) |
| `tool.cutting/@swSawthick` (3) | KON2 f1 |
| `tool.cutting/@swPackageHeight` (40) | LMT1 f2 |
| `tool.cutting/@swMaxturns` (4) | daraja ≤ 04 |
| `part/@l`, `@w` (cSizeMode=1 da `l=dl`, `w=dw`) | URN1 f3, f4; URN2; PRT1 f3, f4 |
| `part/@count` | URN1 f1, f2; PRT1 f1 |
| `part/@name` | PRT1 f8 |
| ota `good[product]/@code`, `@name` | PRT1 f10, f11 |
| `ell`, `elt`, `elr`, `elb` → EL op → `band/@name`, `band/@t` | PRT3 f3/f6/f9/f12, PRT4 f1..f4 |
| `part/@txt` (tekstura) | **eksport qilinmaydi** (faqat kartadagi joylashuvda aks etadi) |
| `jl/jw` (prifugovka) | ishlatilmaydi: o'lcham `l/w` (kromka qalinligi 1 mm ni prifugovka 1 mm qoplaydi — `elWidthPreJoint=1`) |
| `part.code`, `description` | eksport qilinmaydi |

Tekshiruv natijasi (12 AES fayl + 21 AESS fayl birgalikda): 1021 qatorning nomi loyihada topildi, **1021/1021 soni mos**,
1016/1021 o'lcham `l×w` (yoki `dl×dw`) bilan aynan mos (5 tasi 3173 da — loyihaning boshqa versiyasi),
1021/1021 qalinlik mos, 1016/1021 mahsulot kodi mos. Barcha fayllarda `Σ URN soni = Σ (karta detallari × PNL1 f3)`.

Konkret misollar (AES Alpha):

1. **3171 (LDSP DUB VATAN, `3171_mijoz.project`)** — CS da 6 detal qatori, jami 28 dona; `.ss` da 6 URN, Σ=28, 2 noyob karta ×2 = 4 list (OZL1 f2=4, list `usedCount=4`).
   `01_001 oldi bok`: loyiha `dl=1400 dw=1750 count=2`, kromka `t,b,l,r` = `1-19 dub votan` →
   `URN1,    2,    2,  1400.00,  1750.00, ,N`, `PRT3,0000,,1-19 dub votan,,,1-19 dub votan,,,1-19 dub votan,,,1-19 dub votan,` (to'ldiruvchi bo'shliqlar qisqartirildi), `PRT4, 1.00, 1.00, 1.00, 1.00`.
   `01_003 bok` (kromka t,l,r): PRT3 → chap, yuqori, o'ng to'la, past bo'sh; PRT4 `1,1,1,0`.
   `01_002 tom` (faqat t): PRT3 da faqat 2-pozitsiya (yuqori).
2. **3174 (LDSP KASHMIR, qoldiq bilan)** — CS da ikkita list yozuvi: qoldiq `l=2750 w=450 usedCount=1` va list `2750×1830 usedCount=10` →
   ikki OZL bloki (`1`, `10`). Qoldiqdagi karta: `PNL1,01,L,1,0` → `KES1,01,435.00` (polosa: 435 + 3 ≤ 450 − 2·2 − 3),
   ikki detal `KES1,02,1340.00,1,018/019`. 70 qator, Σ=112 dona — loyiha bilan teng.
   Bir xil nomli ikki qator (`01_003 Fasad`, har biri `count=1`) — ikkita alohida URN.
3. **3182 / 3179 / 3168** — URN/PRT tartibi CS `<part>` havolalari tartibiga aynan teng (id bo'yicha tartiblanmagan);
   3179 da kromka nomlari `06-19 oq`, `1-21 mokriy` — `3179_mijoz.project` dagi `band/@name` bilan aynan bir xil
   (loyihaning eski nusxasida `kromka PVC 1-21 mokriy` edi — demak `.ss` yangi nusxadan, nom o'zgartirilmaydi).

---

## 5. Minimal qayta tiklangan namuna

Bitta XDF list (2800×2070, qalinligi 3), 2 noyob karta, 3 detal turi (4 dona), kromkasiz. Real fayldan
(AESS 2027 XDF) anonimlashtirilgan; `CRLF` bilan saqlash kerak:

```
BSL1,001,0001 mijoz
BSL2,27.09.2026,17:40,
BSL3,From GibLab,1.0,,
KON1,M,M,N,   1,0
KON2,     3.00,     3.00, 0.00,     0.00,     0.00,     0.00
KON3,     0.00
LMT1,     3.00,    40.00
ASP1,      ,      ,      
ASP2,           ,           ,           
OZL1,*****,    2,   9.860,  2070.00,  2800.00,     2.00,     2.00,     2.00,     2.00
OZL2,XDF 2800x2070 mm  5.8 kv
OZL3,1                ,     2.00,     2.00
URN1,    1,    1,  1999.00,  2099.00, ,N
URN2,        ,  1999.00,  2099.00
URN3, 1, 1
URN1,    1,    1,   691.00,   348.00, ,N
URN2,        ,   691.00,   348.00
URN3, 1, 2
URN1,    2,    2,  2031.00,   853.00, ,N
URN2,        ,  2031.00,   853.00
URN3, 1, 3
PRT1,    1, 0,  1999.00,  2099.00, 1,                        ,,01.029 XDF ort,,000101,01 shkaf,                
PRT2, 0, ,     3.00,
PRT3,0000,        ,,        ,        ,,        ,        ,,        ,        ,,        
PRT4,     0.00,     0.00,     0.00,     0.00,1,                    
PRT5, ,N,     ,     
PRT1,    1, 1,   691.00,   348.00, 1,                        ,,01.030 HDF tr,,000101,01 shkaf,                
PRT2, 0, ,     3.00,
PRT3,0000,        ,,        ,        ,,        ,        ,,        ,        ,,        
PRT4,     0.00,     0.00,     0.00,     0.00,1,                    
PRT5, ,N,     ,     
PRT1,    2, 2,  2031.00,   853.00, 1,                        ,,04.008 XDF ort,,000101,01 shkaf,                
PRT2, 0, ,     3.00,
PRT3,0000,        ,,        ,        ,,        ,        ,,        ,        ,,        
PRT4,     0.00,     0.00,     0.00,     0.00,1,                    
PRT5, ,N,     ,     
PNL1,01,S,1,0
PNL2, 0.0000,        0.0000,        0.0000,        0.0000,       1.000
PNL3,     ,     ,     ,     
PNL4,           ,           ,           
PNL5,      ,      ,            ,            
BASLA
KES1,01,  2099.00,0,000
KES1,02,  1999.00,1,001
KES1,01,   348.00,0,000
KES1,02,   691.00,1,002
PNL1,01,S,1,0
PNL2, 0.0000,        0.0000,        0.0000,        0.0000,       1.000
PNL3,     ,     ,     ,     
PNL4,           ,           ,           
PNL5,      ,      ,            ,            
BASLA
KES1,01,   853.00,0,000
KES1,02,  2031.00,1,003
KES1,01,   853.00,0,000
KES1,02,  2031.00,1,003
BITIR
```

E'tibor: ikkinchi karta aslida bir xil (2×853 polosa) bo'lsa ham GibLab uni alohida PNL qilib yozgan va `PNL1 f3=1`;
uchinchi detal (`2031×853`, soni 2) ikki polosada. Detal #1 `1999×2099` `KES1,01,2099` + `KES1,02,1999` bilan — ya'ni
burilgan holda joylashgan.

Generatsiya algoritmi (MebeliX uchun psevdokod):
```
yoz BSL1..ASP2 (sozlamalar: kerf, qalinlik, paket balandligi)
har list yozuvi s (operatsiya tartibida): OZL1(usedCount, w, l, trim×4), OZL2(nom), OZL3
har detal qatori i (1..N): URN1(count,count,l,w) URN2 URN3(i)
har detal qatori i: PRT1(count, i-1, l, w, nom, mahsulot kodi, mahsulot nomi) PRT2(t) PRT3(L,T,R,B kromka nomlari) PRT4(L,T,R,B qalinlik) PRT5
har noyob karta: PNL1(list#, S|L, takror), PNL2..PNL5, BASLA,
    daraxtni pre-order: har daraja ≥3 guruhining boshida "-0.50" qatori; detal → f3=1, f4=URN#; oraliq → 0,000
BITIR
```

---

## 6. Noma'lum / noaniq maydonlar — savollar

* **Q1.** Kirill (yoki boshqa ASCII bo'lmagan) detal/material nomlari qaysi kodlashda yozilishi kerak (cp1251? cp866? ASCII ga transliteratsiya?). Namunalarda faqat lotin harflari bor.
* **Q2.** `KON1,M,M,N,   1,0` — har bir bayroqning ma'nosi (o'lchov birligi, kesish rejimi, ...)? O'zgartirish kerak bo'ladimi?
* **Q3.** `KON2` ikkinchi `3.00` — podrezka arrasi eni, kerf takrori yoki boshqa narsami? `KON2` f3..f6, `KON3` nollari nima (minimal polosa, torets...)?
* **Q4.** `OZL1 f1 = *****`, `OZL1 f3 = 9.860`, `OZL3 f1 = 1` — list kodi / zichlik / narx / ustuvorlik? Qoldiq (ombor) listlari uchun ular o'zgaradimi?
* **Q5.** `OZL1` dagi to'rt `2.00` qaysi tomonlarning torsovkasi (old/orqa/chap/o'ng)? `OZL3` dagi ikkita `2.00` bilan farqi? (Loyiha `cTrimL=cTrimW=2`; turli torsovkali namuna kerak.)
* **Q6.** `URN1 f1` va `f2` hamisha teng — biri «buyurtma soni», ikkinchisi «kesiladigan soni» (ortiqcha/kam bo'lganda farqlanadi)mi?
* **Q7.** AES Alpha papkasida 3167 va 3181 buyurtmalari, hamda barcha 31xx buyurtmalarning XDF/qo'shimcha materiallari nega yo'q? Eksport qilinmaganmi yoki xato bermi?
* **Q8.** `URN1 f6 = N`, `PRT5 f2 = N` — tekstura (aylantirish taqiqi) bayrog'imi? Teksturali detallarda ham `N`; `Y` qiymati stanokda nimani o'zgartiradi?
* **Q9.** `PRT4` — kromka qalinligimi yoki «kromka bor» bayrog'imi? 0.4/2 mm kromkali (t≠1) namuna kerak.
* **Q10.** `PNL2, 0.0000 ×4, 1.000` — karta bo'yicha qanday parametrlar (offset, masshtab, ustuvorlik)?
* **Q11.** `KES1, 03/04, -0.50` — stanok buni qanday talqin qiladi (burilgandan keyingi torets kesimi, «avtomatik torsovka» buyrug'i)? Qiymat −0.50 doimiymi yoki sozlamadan (masalan `swMinPruning=5`) bog'liqmi?
* **Q12.** Stopka (kniga) soni faylda yo'q — stanok `PNL1 f3`, qalinlik va `LMT1 f2=40` dan o'zi hisoblaydimi?
* **Q13.** Qoldiqlar (delovoy otxod) faylga yozilmaydi — stanok/operator ularni yorliqlashi kerakmi? Agar kerak bo'lsa, format qaysi yozuvni qo'llab-quvvatlaydi?
* **Q14.** `BSL1 f1 = 001` — fayl/ish raqami har eksportda o'zgarishi kerakmi?
