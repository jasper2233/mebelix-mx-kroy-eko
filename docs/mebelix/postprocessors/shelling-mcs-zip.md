# Shelling (MCS) — `.l.zip` (NCL/NCP) formati

> Manba: `post prtsessorlar/PILNIY APPARAT/Shelling (MCS)/` dagi 10 ta namuna (buyurtmalar 2027–2037) va
> `giblab project/2 shogirt/<buyurtma>/` dagi kompaniya `.project` fayllari.
> Mijoz ismlari hujjatda «mijoz» deb almashtirilgan. Dastur binarlari o'qilmagan — faqat chiqish fayllari tahlil qilingan.
> Holat: **to'liq** (kesish rejasi va detallar xaritasi to'liq tushunilgan; bir nechta konstant maydonlar ma'nosi noma'lum — 6-bo'limga qarang).

## 0. Qisqacha

* Har bir buyurtma uchun bitta tashqi `<buyurtma>_<mijoz>_<MATERIAL>.l.zip`. Ichida: bitta material uchun
  `0000.ncl` (sarlavha + listlar + detallar ro'yxati), `0001.ncp … NNNN.ncp` (har bir kesish kartasi/pattern uchun bittadan),
  `GibLabData.<GibLabID>.xml` (yorliq/etiketka ma'lumotlari) va **boshqa materiallar uchun ichma-ich `.l.zip`** fayllar (xuddi shu tuzilishda).
* Matn: ASCII (amalda cp1251 deb olish xavfsiz), qatorlar `CRLF`, **qat'iy pozitsiyali (fixed-width)** maydonlar.
* O'lchamlar: butun son, **1/1000 mm** birligida, 8 xonali nol bilan to'ldirilgan (`02750000` = 2750.000 mm). O'nlik ajratgich yo'q.
* Kesish rejasi daraxt ko'rinishida: `K01`/`L01` (1-daraja) → `X01..` (2-daraja polosalar) → `a01..` (3) → `b01..` (4); barg = detal (`… 0 NNNN`) yoki qoldiq (`R`).
* Oddiy `Shelling` (`shelling-zip.md`) bilan bayt darajasida bir xil yozuv turlari va kengliklar (312/154/159 belgili F-qatorlar) kuzatildi; asosiy farq — MCS namunalarida **boshqa materiallar ichki `.l.zip` sifatida tashqi zip ichiga joylangan** (oddiy Shelling namunalarida ichki zip yo'q, har material alohida zip).

---

## 1. Hosil qilinadigan fayllar

| Narsa | Qiymat |
|---|---|
| Tashqi fayl nomi | `<project.name, bo'shliq→_>_<sheet.name, bo'shliq→_>.l.zip`. Masalan `2028_mijoz_LDSP_OQ_GLYANETS.l.zip`. Material nomidagi ketma-ket bo'shliqlar bitta `_` ga (`XDF 2800x2070 mm  5.8 kv` → `XDF_2800x2070_mm_5.8_kv`), oxirgi bo'shliq ham `_` bo'ladi (`LDSP UD ` → `LDSP_UD_`). Apostrof saqlanadi. |
| Bir buyurtmada | 1 ta tashqi zip. Tashqi zip «asosiy» materialni (ko'pincha 16 mm LDSP/LMDF) o'z ichida to'g'ridan-to'g'ri saqlaydi; qolgan har bir material (XDF 3 mm, ikkinchi LDSP, AKRIL …) — ichki `<project>_<material>.l.zip`. 10 namunada: 9 tasida 1 ta, 2030 da 2 ta, 2028 da 0 ta ichki zip. |
| Zip ichidagi fayllar (har bir daraja) | `0000.ncl`, `0001.ncp`…`NNNN.ncp` (NNNN = patternlar soni, 4 xonali), `GibLabData.<GibLabID>.xml`, so'ng ichki `.l.zip`lar. Papkalar yo'q (tekis). |
| Siqish | GibLab yozgan fayllar: Deflate (method 8), flag `0x0808` (data descriptor + UTF‑8 nom). Ichki `.l.zip` yozuvlari: Stored (method 0), DOS atribut `0x20`, vaqt belgisi boshqacha (mahalliy vaqt) — ichki zip keyinroq boshqa vosita bilan qo'shilganga o'xshaydi (6-bo'lim, savol 1). |
| Kodlash | Barcha `.ncl/.ncp` 100% ASCII (505 detal qatorida birorta ham >127 bayt yo'q). Kirill uchun cp1251 taxmin qilinadi. `GibLabData.*.xml` — UTF‑8. |
| Qator oxiri | `CRLF`. `0000.ncl` `S$\r\n` bilan, har `.ncp` `P$\r\n` bilan tugaydi. |
| Sonlar | Faqat butun sonlar, nol bilan to'ldirilgan; mm qiymatlar ×1000. |

`GibLabID` (20 belgi) = 4 ta tasodifiy hex + 16 hex xonali **eksport vaqti (Unix ms)**: `d939000001a0e3557453` → `0x1a0e3557453` = 1790520423507 ms = 2026‑09‑27. Har bir material (har bir `0000.ncl`) o'z IDsiga ega; u `S 01` qatorida, har `F 01` detal qatorida va `GibLabData.<ID>.xml` nomida takrorlanadi.

Statistika (barcha 10 namuna, ichki zip'lar bilan): 20 ta `0000.ncl`, 72 ta `.ncp`, 21 ta `B`, 505 ta detal `F 01`, 19 ta qoldiq `F 01`, 1270 ta `C` qator.

---

## 2. Tuzilish

### 2.1 `0000.ncl` — material sarlavhasi va detallar ro'yxati

Qatorlar tartibi:
```
S 01 …                (1 marta)
S 46 …                (1 marta)
B 01 …                (listlar/zagotovkalar, 1..n)
F 01 … (detal)        ┐
P 09 …                │ har detal uchun 3 qator
F 80 … (kromka)       ┘
F 01 … (qoldiq)       (0..n, P09/F80siz)
S$
```

Pozitsiyalar 0 dan sanalgan (Python `l[a:b]`).

#### `S 01` (67 belgi)
| Poz. | Misol | Ma'nosi |
|---|---|---|
| 0–11 | `S 01 001 001` | konstant |
| 13–32 | `2027_mijoz_LDSP_UD` | ish nomi = zip nomi (`.l.zip`siz), **20 belgiga qirqilgan**, bo'shliq bilan to'ldirilgan |
| 34–43 | `2026-09-27` | eksport sanasi `YYYY-MM-DD` |
| 45 | `0` | konstant |
| 47–66 | `d939000001a0e3557453` | GibLabID |

#### `S 46` (75 belgi)
`S 46 ` + to'liq ish nomi, **70 belgi**, bo'shliq bilan to'ldirilgan.

#### `B 01` — list (plita) turi (99 belgi)
| Poz. | Misol | Ma'nosi |
|---|---|---|
| 5–8 | `0001` | list indeksi (1..n) — `P 01` dagi 2‑maydon unga murojaat qiladi |
| 10 | `0` | konstant |
| 12–31 | `LDSP UD             ` | material nomi (`sheet@name`), 20 belgi, qirqilgan |
| 33–40 | `00016000` | qalinlik ×1000 (16 mm) |
| 42–49 | `02750000` | list uzunligi ×1000 |
| 51–58 | `01830000` | list eni ×1000 |
| 60 | `0` | konstant |
| 62–81 | material nomi yana (20) | ehtimol list kodi/nomi (savol) |
| 83, 85 | `0 0` | konstant |
| 87–96 | `0000000001` | konstant (zaxira soni 1000/10000 bo'lsa ham 1) |
| 98 | `0` | konstant |

Bir material bir nechta zagotovka o'lchamiga ega bo'lsa, bir nechta `B` yoziladi. Masalan, 2029 (`Ldsp oq`): `B 0001` = 2750×1160 (loyihada `count=1` qoldiq-zagotovka), `B 0002` = 2750×1830 (standart list, ishlatilmagan). Faqat 1160 li ishlatilgan; uning patterni `P 01 0001 0001 …` (list 1).

#### `F 01` — detal yozuvi (312 belgi)
| Poz. | Misol | Ma'nosi |
|---|---|---|
| 5–8 | `0002` | detal indeksi (1..N ketma-ket; `.ncp` dagi `0 NNNN` shu raqam) |
| 10–13 | `0002` | xuddi shu indeks (barcha 505 holatda teng) |
| 15 | `0` | turi: `0` = detal, `1` = qoldiq |
| 17–22 | `000005` | soni (jami dona, barcha listlar bo'yicha) |
| 24–29 | `000005` | soni yana (doim teng) |
| 31–50 | `LDSP OQ GLYANETS    ` | material nomi, 20 belgi |
| 52–59 | `00016000` | qalinlik ×1000 |
| 61–68 | `02000000` | **uzunlik L** ×1000 (`part@cl` = `dl`) |
| 70–77 | `00350000` | **en W** ×1000 (`part@cw` = `dw`) |
| 79–86, 88–95 | L, W takrori | barcha holatda 61–77 bilan teng (ehtimol «tayyor o'lcham»; savol) |
| 97–116 | `01.001 bok          ` | detal nomi (`part@name`), 20 belgi, qirqilgan |
| 118 | `1` | **tekstura/aylantirish bayrog'i**: `0` = tekstura bor, aylantirish mumkin emas (`txt="true"`); `1` = aylantirish mumkin (`txt="false"`) |
| 120–153 | `9 9 0 00 000000 000 000000 000 1 0` | konstant (151‑pozitsiya: detalda `1`, qoldiqda `0`) |
| 155–174 | `_01.001` | 1‑tomon prisadka (XNC) dastur kodi, 20 belgiga qirqilgan; dasturi bo'lmasa bo'sh |
| 176–195 | `203701_01_005_2` | 2‑tomon XNC dastur kodi (`side="false"` operatsiya), bo'lmasa bo'sh |
| 197–237 | bo'sh | yana 2 ta slot bo'lishi mumkin (hech qachon to'lmagan) |
| 238, 240 | `1 0` | konstant |
| 242–261 | GibLabID | |
| 263–282 | `spalniy matrasli    ` | buyum (product) nomi (`good[@typeId=product]@name`), 20 belgi |
| 284–292 | `000000002` | loyihadagi `part@id`, 9 xona |
| 294–303 | `2026.04.04` | `project@orderDate` (ms) → `YYYY.MM.DD` |
| 305–311 | `0 0 000` | konstant |

#### `F 01` — qoldiq (delovoy otxod) yozuvi (154 belgi)
```
F 01 0001 0001 1 000001 000001 LDSP UD              00016000 02740000 01223000 00000000 00000000 Ostatok              0 9 9 0 00 000000 000 000000 000 0 0
```
Turi `1`; indeks qoldiqlar uchun alohida 1 dan boshlanadi; soni = shu qoldiq necha marta hosil bo'lishi (list soni × takror); L (doim list **uzunligi bo'ylab**), W; takror o'lchamlar `0`; nom doim `Ostatok`; bayroq `0`; 151‑pozitsiya `0`. Qator 153‑pozitsiyada tugaydi (P09/F80 yo'q).

#### `P 09` (45 belgi) — doim `P 09 00000000 00000000 00000000 00000000 XXXX` (505/505).

#### `F 80` — kromka (159 belgi)
| Poz. | Ma'nosi |
|---|---|
| 0–44 | `F 80 00000000 00000000 00000000 00000000 0000` konstant |
| 46–66 | **pastki (b) tomon** kromkasi, 21 belgi |
| 67–87 | **yuqori (t)** |
| 88–108 | **chap (l)** |
| 109–129 | **o'ng (r)** |
| 130–158 | `00 00 00 00 00000000 00000000` konstant |

Slot qiymati: `(<elSymbol>) 1` — `elSymbol` loyihadagi `operation[@typeId=EL]@elSymbol` (A, B, C…), part atributi `elb/elt/ell/elr="@operation#<id>"` orqali. Kromkasiz tomon — 21 bo'shliq. Tomon tartibi **b, t, l, r** (loyihadagi `ell/elr` emas!). Kuzatilgan: `(A) 1` 410, `(B) 1` 269, `(C) 1` 30. Raqam `1` — hamma joyda 1 (barcha kromkalar loyihada `t="1"`); qalinlik ekanligi tasdiqlanmagan (savol).

### 2.2 `NNNN.ncp` — bitta kesish kartasi (pattern)

```
P 01 0002 0001 000002 0 0 0000 0
P 02 01 0001 0002 00000000 001
P 03 00 0 00 00000000 02750000 01830000 02750000 01830000
P 98 0 0 0
C K01 T   00005000 001
C K01 X01 01980000 001
C X01 T   00005000 001
C X01     00780000 001 0 0078
…
P$
```

| Qator | Maydonlar |
|---|---|
| `P 01 pppp bbbb ssssss 0 0 0000 0` | pppp = pattern raqami (fayl nomi bilan bir xil), bbbb = `B` list indeksi, ssssss = **shu pattern bo'yicha kesiladigan listlar soni** |
| `P 02 01 kkkk nnnn 00000000 001` | kkkk = **paketlar (kitoblar) soni**, nnnn = **paketdagi listlar soni**; doim kkkk×nnnn = ssssss (72/72). 16 mm uchun maksimal 2 (= `swPackageHeight=40` / 16). |
| `P 03 00 0 00 00000000 D1 D2 D1 D2` | list o'lchamlari, kesish yo'nalishi bo'yicha tartiblangan: **D1 — 1‑darajali kesishlar ketma-ket joylashadigan o'q** (1‑daraja polosalarining «eni» shu o'q bo'ylab o'lchanadi). 2‑juft doim 1‑juftga teng. |
| `P 98 0 0 0` | konstant |
| `C …` | kesish buyruqlari (pastga qarang) |
| `P$` | tugash |

#### `C` qatori (22 yoki 29 belgi)
| Poz. | Ma'nosi |
|---|---|
| 2–4 | ota element (daraja nomi): `K01`/`L01`, `X01..`, `a01..`, `b01..` |
| 6–8 | bola: `X01`/`a01`/`b01` (yangi polosa), `T  ` (trim — tozalash kesimi), `R  ` (qoldiq), `   ` (bo'sh = detal) |
| 10–17 | o'lcham ×1000 (polosa eni / detal o'lchami / trim qalinligi; `R` da 0) |
| 19–21 | takror soni (polosa yoki detal ketma-ket necha marta); `R` da `000` |
| 23 | `0` (detal/qoldiq qatorida) |
| 25–28 | detal `F 01` indeksi yoki (`R` uchun) qoldiq `F 01` indeksi |

---

## 3. Kesish rejasi qanday kodlangan

**Darajalar va yo'nalish.** Daraja harfi o'q almashinuvini bildiradi (guillotine):

| Daraja | Harf | Kesim o'qi |
|---|---|---|
| 1 | `K` yoki `L` | D1 bo'ylab polosalar (`P 03` dagi birinchi o'lcham) |
| 2 | `X` | D2 bo'ylab |
| 3 | `a` | D1 bo'ylab |
| 4 | `b` | D2 bo'ylab |

`K01` — `P 03` = `02750000 01830000` (D1 = list uzunligi; avval ko'ndalang kesish), `L01` — `P 03` = `01830000 02750000` (D1 = list eni; avval bo'ylama kesish). 72 patterndan: K 36 ta (2750/2800/2440 bo'ylab), L 36 ta. Maksimal chuqurlik 4 (`swMaxturns=4`) — `c` darajasi uchramadi.

**Raqamlash.** `X01, X02…` 1‑daraja ichida ketma-ket; `a01…` har bir `X` ichida qaytadan 1 dan; `b01…` har bir `a` ichida qaytadan. Shuning uchun ota nomi oxirgi ochilgan shu nomdagi polosaga tegishli (daraxtni ketma-ket o'qib qurish kerak).

**Trim.** Har bir 1‑daraja (`K01 T`) va har bir `X` polosa (`X0n T`) boshida `T 00005000` (5 mm). `a`/`b` darajada trim yo'q (0 holat). 5 mm = loyiha `cTrimL/cTrimW=2` + arra qalinligi `swSawthick=3` deb taxmin qilinadi (`swTrimIncludeSaw="false"`) — barcha namunalarda `cTrim=2`, shuning uchun alohida tasdiqlab bo'lmadi (savol 3).

**Arra qalinligi (kerf)** faylda yo'q (stanok sozlamasi). Geometrik tekshiruv: 3 mm kerf bilan har bir ota uchun `trim + Σ(o'lcham+3)×takror − 3 ≤ ota o'lchami` — 494 ota tugunning hammasida bajariladi (ortib ketish 0).

**Detal joylashuvi.** Detal qatori `C <ota> ␣␣␣ s n 0 i` — detal o'lchamlari = (s, ota polosa eni); 1‑daraja ostidagi detal uchun ikkinchi o'lcham D2. 574 joylashuvning hammasida {s, ota} = {F01.L, F01.W}. Qaysi o'lcham list uzunligiga tushishini daraja juft/toqligi bo'yicha aniqlash mumkin.

**Tekstura.** `F 01` 118‑pozitsiya `0` bo'lgan detallar 147 marta joylashgan — hammasida F01.L list uzunligi (B.L, 2750/2800/2440) bo'ylab yotadi; `1` li detallar 189 marta 90° burilgan holda ham uchraydi. Demak: `0` → L doim list uzunligi bo'ylab.

**Soni / paket.** Detal ishlab chiqarish soni = Π(yo'ldagi takrorlar) × `P 01` dagi listlar soni. Barcha 20 `.ncl` da Σ(patternlardan) = F01 soni (505/505). Takror ham polosa darajasida bo'lishi mumkin: `C K01 X06 00080000 002` — X06 polosasi 2 marta, ichidagi har detal ×2.

**Qoldiq (`R`).** `C <ota> R 00000000 000 0 r` — shu ota polosaning qolgan qismi r‑qoldiq. O'lchamlari (20/20 holatda tasdiqlangan):
* bo'ylama: `qolgan = ota_o'lcham − (trim + Σ(o'lcham+3)×takror)`, qoldiq = `qolgan − 5`;
* ko'ndalang: 1‑darajada `D2 − 10` (ikki chet trim), `X`/`a` darajada — ota polosa eni.
* `F 01` qoldiq yozuvida L doim list uzunligi o'qi bo'ylab.
Misol (2027, pattern 0008, L01, list 1830×2750): 5+413+3+178+3 = 602 → 1830−602−5 = **1223**, 2750−10 = **2740** → `Ostatok 2740×1223` ✓. Qoldiqlar loyihadagi CS operatsiyasi materiali ostida `count=1 usedCount=0` zagotovka sifatida paydo bo'ladi (2033 XDF: 1718×549 va 2790×988; 2034 XDF: 538×2060 va 2158×2060; 2036 AKRIL: 618×1210; 2037: 2118×734 — hammasi mos).

**Bir xil patternlar birlashtirilmaydi** har doim ham: 2037 XDF da 0001 va 0002 strukturaviy bir xil, faqat detal indekslari boshqa — har biri 1 listdan. Yig'ish ixtiyoriy.

**Yorliqlar.** `GibLabData.<ID>.xml`: `<GibLab><GibLabLabel GibLabID="…"><part data="…"/>…</GibLabLabel></GibLab>`; `<part>` soni = shu `.ncl` dagi barcha `F 01` (detallar + qoldiqlar) soni (20/20). `data` — base64(zlib(GibLabning yopiq kalit‑qiymat formati: `project.name`, `project.date`, `material.name`, `product.name` …)). Etiketka chop etish uchun; MebeliX uni yaratishi shart emas deb taxmin qilinadi (savol 2).

---

## 4. Loyiha → fayl xaritasi

| Loyiha (`.project`) | Fayl maydoni |
|---|---|
| `project@name` (bo'shliq→`_`) + `sheet@name` | zip nomi, `S 01` (20), `S 46` (70) |
| eksport vaqti | `S 01` sana, GibLabID |
| `good[@typeId=sheet]@name/t/l/w` va uning ichki `<part l w count>` zagotovkalari | `B 01` (har o'lcham uchun bitta) |
| `part@id` | F01 284–292 |
| `part@name` | F01 97–116 (20) |
| `part@cl/@cw` (= `dl/dw` bu loyihalarda; `jl/jw` emas) | F01 L, W (×1000) |
| `part@count` | F01 soni (ikkala maydon) |
| `part@txt` (`true`→`0`, `false`→`1`) | F01 118 |
| `part@elb/elt/ell/elr` → `operation[EL]@elSymbol` | F80 slotlar b, t, l, r: `(A) 1` |
| `operation[XNC]@code` (side=true / side=false), `typeName = part@name` | F01 155–174 / 176–195 (20 belgiga qirqilgan) |
| ota `good[@typeId=product]@name` | F01 263–282 |
| `project@orderDate` | F01 294–303 |
| `operation[CS]@cPartCount` | Σ F01 soni |
| `operation[CS]@cMaterialCount` | Σ `P 01` listlar soni |
| `tool.cutting@swPackageHeight` / list qalinligi | `P 02` paketdagi listlar |
| `tool.cutting@swSawthick` | (faylda yo'q) — geometriyani tekshirishda 3 mm |
| `operation[CS]@cTrimL/cTrimW` (+kerf) | `T 00005000` |

Bir xil nomli, lekin alohida `part` elementlari (masalan ko'zgu juftlar: biri `elt`, biri `elb`) alohida `F 01` yozuvlari bo'ladi (2037 `01_003 bok` id 3 va 4). `F 01` tartibi qat'iy qoidaga bo'ysunmaydi (nom/ID bo'yicha emas) — taxminan CS operatsiyasidagi ro'yxat tartibi; muhimi indeks 1..N va `.ncp` murojaatlari mosligi.

### Tekshirilgan namunalar

| Namuna | F01 detal / Σ soni | Loyiha `cPartCount` | Listlar = `cMaterialCount` | Qoldiqlar | Natija |
|---|---|---|---|---|---|
| 2028 (LDSP OQ GLYANETS) | 5 / 23 | 23 | 3 = 3 | 0 | Barcha maydonlar mos (soni, L/W, txt, kromka, XNC kod `_01.001`, product, id, sana 2026.04.04) |
| 2034 (LDSP KASHMIR) | 61 / 67 | 67 | 5 = 5 | 0 | Hammasi mos |
| 2034 ichki XDF | 4 / 4 | 4 | 2 = 2 | 538×2060, 2158×2060 | loyihadagi qoldiqlar bilan mos |
| 2037 (LDSP OQ GLYANETS) | 29 / 44 | 44 | 5 = 5 | 2118×734 | mos; XNC kodlari faqat saqlangan loyiha versiyasida boshqacha (qayta generatsiya) |
| 2036 ichki AKRIL 2440×1220×18 | 10 / 12 | 12 | 1 = 1 | 618×1210 | mos |
| 2033 (+XDF) | 32/36, 3/3 | 36, 3 | 5, 2 | 2188×532 / 1718×549, 2790×988 | mos |
| 2029 (+Ldsp oq 1160 zagotovka) | 15/16, 16/23 | 16, 23 | 1, 1 | — | mos; ikki `B` |

Aniq misol (2028, loyiha `part id="2"`):
```
<part id="2" name="01.001 bok" cl="2000" cw="350" count="5" elt="@operation#1" txt="false" …/>   EL#1 elSymbol="A"
<operation typeId="XNC" code="_01.001" typeName="01.001 bok" side="true"/>
```
→
```
F 01 0002 0002 0 000005 000005 LDSP OQ GLYANETS     00016000 02000000 00350000 02000000 00350000 01.001 bok           1 9 9 0 00 000000 000 000000 000 1 0 _01.001 … 1 0 b309000001a0e3563512 spalniy matrasli     000000002 2026.04.04 0 0 000
F 80 00000000 00000000 00000000 00000000 0000                      (A) 1                                                          00 00 00 00 00000000 00000000
```
(kromka 2‑slotda = t). Pattern 0002 da: `C K01 X01 02000000 001` → `C X01 00350000 005 0 0002` (5 dona) = soni 5 ✓.

Nomuvofiqliklar faqat loyiha fayli eksportdan keyin o'zgartirilgan/saqlanmagan hollarda: 2027 va 2031 da topilgan `.project` lar natijasiz «xom» versiya (`orderDate` yo'q, `txt` hammasi `true`) — u yerda tekstura bayrog'i va sana tekshirib bo'lmadi; 2030 LMDF va 2032 qisman mos (boshqa loyiha versiyasidan eksport qilingan). 2028 dagi ikkinchi material `LDSP krem` (kichik zagotovkalar) zipga kiritilmagan (savol 4).

---

## 5. Minimal namunaviy fayl (anonim)

List 2750×1830×16, detal A 800×400 ×2 (tekstura, pastki kromka A, XNC dastur bor), detal B 600×300 ×1 (aylantirish mumkin), 1 qoldiq. Ustun kengliklari haqiqiy namuna bilan solishtirib tekshirilgan (F01 312, qoldiq 154, F80 159 belgi).

`0000.ncl`:
```
S 01 001 001 9001_mijoz_LDSP_OQ   2026-10-04 0 1a2b000001a0e3557453
S 46 9001_mijoz_LDSP_OQ                                                    
B 01 0001 0 LDSP OQ              00016000 02750000 01830000 0 LDSP OQ              0 0 0000000001 0
F 01 0001 0001 0 000002 000002 LDSP OQ              00016000 00800000 00400000 00800000 00400000 01_001 polka         0 9 9 0 00 000000 000 000000 000 1 0 900101_01_001                                                                      1 0 1a2b000001a0e3557453 01 shkaf             000000001 2026.10.01 0 0 000
P 09 00000000 00000000 00000000 00000000 XXXX
F 80 00000000 00000000 00000000 00000000 0000 (A) 1                                                                               00 00 00 00 00000000 00000000
F 01 0002 0002 0 000001 000001 LDSP OQ              00016000 00600000 00300000 00600000 00300000 01_002 tom           1 9 9 0 00 000000 000 000000 000 1 0                                                                                    1 0 1a2b000001a0e3557453 01 shkaf             000000002 2026.10.01 0 0 000
P 09 00000000 00000000 00000000 00000000 XXXX
F 80 00000000 00000000 00000000 00000000 0000                                                                                     00 00 00 00 00000000 00000000
F 01 0001 0001 1 000001 000001 LDSP OQ              00016000 01937000 01820000 00000000 00000000 Ostatok              0 9 9 0 00 000000 000 000000 000 0 0
S$
```
`0001.ncp`:
```
P 01 0001 0001 000001 0 0 0000 0
P 02 01 0001 0001 00000000 001
P 03 00 0 00 00000000 02750000 01830000 02750000 01830000
P 98 0 0 0
C K01 T   00005000 001
C K01 X01 00800000 001
C X01 T   00005000 001
C X01     00400000 002 0 0001
C X01 a01 00600000 001
C a01     00300000 001 0 0002
C K01 R   00000000 000 0 0001
P$
```
Tekshiruv: X01 (2750 bo'ylab 800) ichida 1830 bo'ylab 5+2×(400+3)+(600+3)=1414 ≤ 1830; A ning 800 tomoni list uzunligi bo'ylab (tekstura ✓); qoldiq 2750−(5+803)−5 = 1937 × 1830−10 = 1820. Zip: `9001_mijoz_LDSP_OQ.l.zip` = {`0000.ncl`, `0001.ncp`, (ixtiyoriy `GibLabData.<ID>.xml`)}, CRLF.

Generator eskizi (Python): `fx(s,n)=s[:n].ljust(n)`, `mm(v)='%08d'%round(v*1000)`; F01 = `'F 01 %04d %04d 0 %06d %06d %s %s %s %s %s %s %s %s 9 9 0 00 000000 000 000000 000 1 0 %s1 0 %s %s %09d %s 0 0 000'` (idx, idx, qty, qty, fx(mat,20), t, L, W, L, W, fx(name,20), grain, prog1(20)+' '+prog2(20)+' '+41 bo'shliq, gid, fx(product,20), part_id, sana); F80 = prefiks + 4×fx(edge,21) + `00 00 00 00 00000000 00000000`; C = `'C %s %s %s %03d' % (ota, fx(bola,3), mm(o'lcham), n)` + (`' 0 %04d' % ref` detal/qoldiq uchun).

---

## 6. Noma'lum / noaniq — savollar

1. **Ichki `.l.zip`**: boshqa materiallarni tashqi zip ichiga GibLab o'zi joylaydimi yoki operator qo'lda qo'shganmi (ichki yozuvlar Stored, boshqa vaqt belgisi)? Stanok (MCS) ichki zipni o'qiydimi yoki har material alohida yuklanadimi? MebeliX qaysi variantni yaratishi kerak?
2. **`GibLabData.<ID>.xml`** stanok yoki etiketka printeri uchun majburiymi? Agar majburiy bo'lsa, etiketka maydonlari ro'yxatini (yoki shablonni) bera olasizmi — biz o'z formatimizda (shifrlanmagan) yozsak bo'ladimi?
3. `T 00005000` (5 mm) qanday hisoblanadi: `cTrim (2) + kerf (3)` mi yoki stanokdagi qat'iy sozlama? cTrim boshqa bo'lgan namuna bormi?
4. 2028 buyurtmadagi `LDSP krem` (kichik zagotovkalar 1000×610, 780×580 …) nega zipga tushmagan — ataylab (qo'lda kesiladi) yoki eksport sozlamasi?
5. F01 dagi takroriy maydonlar: soni×2 (17–22 / 24–29) va o'lcham×2 (61–77 / 79–95) — biri «buyurtma», biri «rejalashtirilgan / tayyor o'lcham (kromkasiz)»mi? Har doim teng bo'lgani uchun teng yozish xavfsiz.
6. F80 dagi `(A) 1` dagi `1` — kromka qalinligimi, `elLineMark`mi yoki konstant? 2 mm kromkali namuna kerak. F80/P09 dagi nollar (ehtimol kromka ostidagi qo'shimcha/frezerlash qiymatlari) qachon nol bo'lmaydi?
7. F01 120–153 dagi `9 9 0 00 …` va `B` dagi `0000000001`, `S 01 001 001`, `P 02 … 01 … 00000000 001`, `P 98 0 0 0` — stanok uchun ma'nosi (ustuvorlik, aylanish, sort)? Hozircha konstant yozamiz.
8. `B 01` dagi ikkinchi material nomi maydoni (62–81) — list kodi (`sheet@code`) bo'lishi kerakmi? Namunalarda doim nom bilan bir xil (hatto `code` bo'lgan XDF da ham nom yozilgan).
9. 20 belgidan uzun nomlar (detal, material, buyum, XNC kod) shunchaki qirqiladi — stanok/etiketka uchun bu maqbulmi, yoki MebeliX qisqa kod ishlatsinmi (masalan XNC kod 22 belgili bo'lganda oxirgi 2 belgi yo'qoladi va bir nechta detal bir xil kodga ega bo'lib qoladi — 2036)?
10. Kirill harflar qaysi kodlashda yozilishi kerak (cp1251 yoki cp866)? Namunalarda kirill yo'q.
