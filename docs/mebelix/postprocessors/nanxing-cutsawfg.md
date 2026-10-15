# Nanxing (CutSawFG) — `.ncp` binar format (zip ichida)

**Holat: to'liq tushunilgan.** 69 ta `.ncp` (10 ta zip, 18 ta material) parser bilan o'qildi.
Hammasi strukturaviy tekshiruvdan xatosiz o'tdi va mening yozuvchim (`write_ncp`, 5-bo'lim) ularni
**baytma-bayt bir xil** qilib qayta yaratadi (149/149, `Nanxing CutSaw` bilan birga). Shunday qilib
bitta ham noma'lum bayt qolmadi. Faqat bir nechta konstanta (masalan 5 mm torsovka, `"MATERIAL NAME"`)
nima uchun aynan shunday ekanligi bo'yicha savollar bor.

Shu format `Nanxing CutSaw` da ham aynan bir xil — qarang [nanxing-cutsaw.md](nanxing-cutsaw.md).
Shu buyurtmalarning AutoCUT XML varianti — [nanxing-nxcutsaw.md](nanxing-nxcutsaw.md); `.ncp` dagi har
bir karta `.CUT` dagi `Layout` bilan 149/149 mos keldi (pastda).

Manba: `post prtsessorlar/PILNIY APPARAT/Nanxing (CutSawFG)/*.zip` (buyurtmalar 2027–2037, 2035 yo'q).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Tashqi fayl | `<buyurtma>_<mijoz>_<material>.zip`, masalan `2027_mijoz_LDSP_UD_.zip`. Material nomidagi bo'shliq va `()` → `_` (`LDSP UD (110197)_diffuseOriginal` → `LDSP_UD_110197__diffuseOriginal`) |
| Zip ichida | `001.ncp`, `002.ncp`, … — **har bir noyob karta (raskroy) uchun bitta fayl**, `Layout` tartibida, 3 xonali nol bilan. Takrorlanuvchi karta bitta fayl + ichidagi `count` maydoni |
| Ichma-ich zip | Buyurtmada boshqa materiallar ham bo'lsa, ular **xuddi shu zip ichiga** `<buyurtma>_<mijoz>_<material2>.zip` nomli ichki zip sifatida qo'yiladi (ichida yana `001.ncp…`). Masalan `2027_…_LDSP_UD_.zip` ichida `2027_…_XDF_2800x2070_mm_5.8_kv.zip` (2 ta `.ncp`). `2032_…_LMDF_KASHMIR_SHAGREN.zip` ichida 16 ta kartali `…_LMDF_DUB_VATAN_TEKSTURA.zip`. `2036` da ikkita ichki zip (AKRIL, XDF) |
| Zip papkalari | yo'q (barcha yozuvlar ildizda) |
| Zip parametrlari | `.ncp` → Deflate (method 8), flag `0x0808` (UTF‑8 nomlar + data‑descriptor), version 20, kommentariy yo'q. Ichki `.zip` → Stored (method 0), flag 0. Sana-vaqt = generatsiya vaqti |
| Fayl turi | **binar**, little-endian, MSVC strukturalarining to'g'ridan-to'g'ri dampi (bo'sh joylar `0xCC` bilan to'ldirilgan) |
| Matn kodirovkasi | **UTF‑16LE** (`wchar_t`), NUL bilan tugaydi, qolgan joy `0xCC` |
| Qator oxiri / o'nlik ajratgich | qator yo'q; sonlar `double`/`int32`/`float`. Faqat etiketka matnida `.` (2 xona: `691.00`) |
| Fayl hajmi | `0x1C + N·0x208 + 0x68 + M·0x1000` bayt; `N` — tugunlar soni, `M` — barg (detal + qoldiq) soni. Masalan 5 tugun, 2 barg → `28+2600+104+8192 = 10924` |

Har material uchun `.ncp` fayllar soni = `.CUT` dagi `Layout` soni; ∑`count` = ishlatilgan listlar soni
(2027 LDSP: 8 fayl/8 list; 2032 DUB VATAN: 16 fayl/18 list; 2032 KASHMIR: 3 fayl/6 list, chunki `003.ncp` `count=4`).

## 2. To'liq tuzilma

### 2.1. Fayl sarlavhasi (0x00–0x1B)

| Offset | Tur | Ma'nosi | Qiymatlar |
|---|---|---|---|
| 0x00 | 4 bayt | sehrli `00 5A 42 44` (`"\0ZBD"`) | konstanta |
| 0x04 | double | list uzunligi (X) | 2750, 2800, 2440 … (ishlatilgan list/qoldiq) |
| 0x0C | double | list eni (Y) | 1830, 2070, 1220 … |
| 0x14 | double | material qalinligi | 16, 3, 18 |

### 2.2. Ildiz (list) yozuvi — 0x1C dan, 0x208 bayt

Ildiz yozuvi oddiy tugun yozuvi bilan bir xil (2.3), faqat birinchi 0x58 bayti boshqacha ishlatiladi:

| Offset (fayl) | Tur | Ma'nosi | Qiymatlar |
|---|---|---|---|
| 0x1C | double | arra qalinligi (propil) | 3 (barcha namunalarda) = `tool.cutting swSawthick` |
| 0x24 | int32 | shu kartali listlar soni | 1, 2, 4 = `.CUT Layout Count` |
| 0x28 | int32 | yana o'sha son (dublikat) | = 0x24 |
| 0x2C | float32 | to'ldirish koeffitsienti (0..1) | formulasi 3.6 da |
| 0x30 | int32 | tugunlar soni `N` (ildiz bilan) | 4…61 |
| 0x34 | 64 bayt | «nom» maydoni — **har doim** `00 00 00 00 00 00 45 00 00 00` + 54×`CC` | konstanta (bo'sh nom + eski `E` qoldig'i) |
| 0x74 | — | tugun tanasi (2.3 dagi +0x58 dan boshlab) | |

### 2.3. Tugun yozuvi (0x208 = 520 bayt), `k`‑tugun `0x1C + k·0x208` da

| +Offset | Tur | Ma'nosi |
|---|---|---|
| +0x000 | int32 | −1 (`FF FF FF FF`), konstanta |
| +0x004 | 16 bayt | nol |
| +0x014 | 4 bayt | `CC CC CC CC` |
| +0x018 | wchar[32] | nom: oraliq tugun `NONE`, detal `Д<n>`, qoldiq `$<k>`; NUL dan keyin `CC` |
| +0x058 | int32 | ota tugun indeksi (ildiz: −1) |
| +0x05C | int32 | bolalar soni (qoldiq `$` hisobga **kirmaydi**) = ∑`count` (torsovkasiz yozuvlar) |
| +0x060 | double | `L` — X bo'yicha o'lcham |
| +0x068 | double | `W` — Y bo'yicha o'lcham |
| +0x070 | double | `wL` — kesib bo'lingandan keyin qolgan chiqindi bo'lagi, X |
| +0x078 | double | `wW` — chiqindi, Y (barglarda `wL=L`, `wW=W`) |
| +0x080 | double | `tX` — tugun X bo'yicha kesilsa 5, aks holda 0 |
| +0x088 | double | `tY` — tugun Y bo'yicha kesilsa 5, aks holda 0 |
| +0x090 | double | `X` — tugunning absolyut X koordinatasi (list burchagidan) |
| +0x098 | double | `Y` — absolyut Y |
| +0x0A0 | 22 × 16 bayt | kesim yozuvlari `{int32 tur; int32 soni; double o'lcham}`; ishlatilmaganlari nol |
| +0x200 | int32 | kesim yozuvlari soni (0…13 kuzatildi, sig'im 22) |
| +0x204 | 4 bayt | `CC CC CC CC` |

**Kesim yozuvi turi** (`tur`): `0` — X bo'yicha bo'lak (vertikal kesim), `1` — Y bo'yicha bo'lak,
`2` — X bo'yicha torsovka, `3` — Y bo'yicha torsovka. `soni` — ketma-ket bir xil bo'laklar soni,
`o'lcham` — bo'lak eni (propilsiz) yoki torsovka (5).

### 2.4. Dum (tail), 0x68 bayt, oxirgi tugundan keyin

| +Offset | Tur | Qiymat |
|---|---|---|
| +0x00 | int32 | −1 |
| +0x04 | 16 bayt | nol |
| +0x14 | 4 bayt | `CC` |
| +0x18 | double | 5.0 (konstanta; ehtimol torsovka — savol) |
| +0x20 | wchar[32] | `"MATERIAL NAME"` (so'zma-so'z, haqiqiy material nomi emas) + NUL + `CC` |
| +0x60 | int32 | 1 (konstanta) |
| +0x64 | int32 | listlar soni (= 0x24) |

### 2.5. Etiketkalar, har biri 0x1000 bayt (wchar[2048])

Barglar soniga teng slot (`M`). Avval **noyob detallar** (tugun tartibida birinchi uchrashi bo'yicha),
keyin **qoldiqlar** (`$k`, tugun tartibida), qolgan slotlar bo'sh (`00 00` + `CC`). Har slot — UTF‑16LE
CSV qator, 21 maydon (vergul bilan; qo'shtirnoq/ekranlash yo'q):

| # | Detal uchun | Qoldiq uchun | Manba (`.CUT` / loyiha) |
|---|---|---|---|
| 0 | `Д<n>` | `$<k>` | Shape `Name` |
| 1 | loyiha nomi (`2027 mijoz`) | xuddi shu | `Project/@Name` = `.project` `name` |
| 2 | material nomi | xuddi shu | `Data/@TypeName` = `good sheet name` |
| 3 | detal nomi | bo'sh | `F1` = `part name` |
| 4 | bo'sh | bo'sh | (F2) |
| 5 | `n` (raqam) | `k` | — |
| 6 | uzunlik `l`, `%.2f` | qoldiq X | `F4` = `part l` |
| 7 | en `w`, `%.2f` | qoldiq Y | `F5` = `part w` |
| 8 | jami soni | `0` | `F3` = `part count` |
| 9 | `false` | `true` | qoldiq belgisi |
| 10 | yuqori kromka | bo'sh | `F8` = `elt` |
| 11 | pastki kromka | bo'sh | `F9` = `elb` |
| 12 | chap kromka | bo'sh | `F10` = `ell` |
| 13 | o'ng kromka | bo'sh | `F11` = `elr` |
| 14 | paz bormi (`true/false`) | `false` | XNC dasturida `gr` (`.CUT` da yo'q!) |
| 15 | frezer bormi | `false` | `F12` (XNC: `ms/ml/ma/mac`) |
| 16 | parmalash bormi | `false` | `F13` (XNC: `bf/bl/br/bt/bb`) |
| 17 | 1‑XNC kodi (old tomon) | bo'sh | `F6` |
| 18 | 2‑XNC kodi (orqa, `…_2`) | bo'sh | `F7` |
| 19 | material turi (`XDF 5.8`) yoki bo'sh | xuddi shu | `Data/@Type` |
| 20 | mahsulot nomi (`01 shkaf`) | bo'sh | `Order` = `good product name` |

Kromka matni: `"(" + elSymbol + ") " + kromka materiali nomi`, masalan `(B) 1-19 dub votan`
(`elSymbol` — EL operatsiyasidagi harf A/B).

### 2.6. Konstanta va ma'lumotga bog'liq maydonlar

Konstanta (69/69 faylda bir xil): sehrli so'z, 0x34 nom maydoni, har tugunning −1/nol/`CC` prefiksi,
dumdagi 5.0, `"MATERIAL NAME"`, 1, propil 3, torsovka 5 (`tX/tY` va torsovka yozuvlari).
Ma'lumotga bog'liq: list o'lchami, qalinlik, `count`, `util`, tugunlar daraxti, etiketkalar.

## 3. Kesish rejasi qanday kodlangan

**Daraxt.** Ildiz = list. Har ichki tugun bir o'q bo'yicha bo'linadi (barcha yozuvlari bir xil `tur%2`),
bolalari keyingi daraja bo'lib, keyingi darajada o'q almashadi (X→Y→X… yoki Y→X→Y…). Barglar — detallar
(`Д`) va qoldiqlar (`$`). Kuzatilgan maksimal chuqurlik 6 (5 ta kesim darajasi). Birinchi kesim o'qi =
`.CUT Layout/@Cut`: `true` → ildiz X bo'yicha (`tur 2,0`), `false` → Y bo'yicha (`tur 3,1`) — 149/149.

**Torsovka (5 mm).** Faqat 0‑daraja (list) va 1‑daraja (polosa) tugunlarida birinchi yozuv torsovka
(`tur 2/3`, o'lcham 5). 2‑darajadan chuqurroqda torsovka yo'q (ikkala papkadagi 676 ta shunday ichki tugunda istisnosiz;
0/1‑darajadagi 557 tugunning hammasida bor).
`tX`/`tY`=5 — tugunning bo'linish o'qini bildiradi (torsovka bor-yo'qligidan qat'i nazar).

**Bo'laklar.** Torsovkadan keyin yozuvlar kesish tartibida (koordinata o'sishi bo'yicha):
`{tur, soni, o'lcham}`. Ketma-ket bir xil **detal** bir yozuvga birlashadi (`(0,3,250)`), lekin
o'lchami teng bo'lsa ham boshqa detal yangi yozuv (`(0,2,250),(0,1,250)` — Д45×2 va Д46).

**Chiqindi.** `qolgan = o'lcham_o'q − torsovka − Σ soni·(o'lcham + propil)` (oxirgi bo'lakdan keyin
ham propil olinadi). Bo'linish o'qida `wL` (yoki `wW`) = qolgan, boshqa o'qda = tugun o'lchami.
Masalan 761×1830 polosa, `(3,1,5),(1,1,292),(1,1,822),(1,1,354),(1,1,343)` → `1830−5−4·3−1811 = 2` → `wW=2`.

**Koordinatalar.** Bola tugunning bo'linmagan o'qdagi koordinatasi va o'lchami otasiniki bilan bir xil.
Bo'linish o'qida: `start = ota_koord + torsovka`, keyingisi `+ o'lcham + propil`.
**Istisno (70/70 holatda):** agar **ildiz Y bo'yicha** bo'linsa, barcha `Y` koordinatalari `.CUT` dagidan
**+3 (propil)** katta: birinchi polosa `Y=8` (CUT `Py=5`). X bo'yicha ildizda siljish yo'q (birinchi polosa `X=5`).
O'lcham va chiqindi hisobi bu siljishga bog'liq emas.

**Tugunlar tartibi.** To'g'ridan-to'g'ri **pre‑order** (ota, keyin uning bolalari rekursiv), bolalar esa
**teskari kesish tartibida** — eng uzoqdagi (eng katta koordinata) birinchi, ya'ni qoldiq `$` birinchi,
birinchi kesilgan bo'lak oxirgi. 149/149 faylda tekshirildi.

**Qoldiq (delovoy ostatok).** Ota tugunning chiqindisi `max ≥ 1000` va `min ≥ 500` bo'lsa (loyiha
`cMinDimRegWaste1/2` = 1000/500) — u `$k` barg sifatida yoziladi (1233 ichki tugunda 25/25 qoldiq,
0 xato). Qoldiq tugun: koordinata = oxirgi bo'lak+propildan keyin, o'lcham = chiqindi **minus 5**
(oxirgi torsovka) bo'linish o'qida; `wL=L, wW=W`, `nchild=0`, `ents=[]`. Masalan XDF 2800×2070,
`(2,1,5),(0,2,853)` → chiqindi 1083×2070 (`.CUT` `О1 X=1083`), `$1` tugun `1078×2070 @X=1717`.
Etiketkada esa list to'liq o'lchamiga teng tomon yana −10 (ikki torsovka): `1078.00,2060.00`. Bu
loyihadagi `waste business` qismning `l×w` iga teng (3175: `l=1816 w=1820 rl=1821 rw=1830`).
`k` — material bo'yicha qoldiq tartib raqami (`.CUT Spares О<k>`).

**Listlar soni (kitob).** `count` (0x24, 0x28, dum +0x64) = bir xil kartali listlar soni. Paket
balandligi (`swPackageHeight=40`) faylda yo'q.

**To'ldirish `util` (float32).** `Σ(detal L·W) / (list L·W − Σ qoldiq etiketka L·W)`. Qoldiqsiz kartada
oddiy detal maydoni / list maydoni (149/149; masalan XDF `001`: (2099·1999+348·691)/(2800·2070)=0.76542).
2032 `003` (2 qoldiq): 2 033 712 / (5 032 500 − 789·1820 − 1948·773) = 0.97273 ✓.

**Detal yo'nalishi.** Tugun `L,W` = list o'qlaridagi o'lcham; etiketka `l,w` bilan solishtirib burilgan-
burilmagani topiladi (aylantirish bayrog'i yo'q). `Turn=false` (tekstura) bo'lgan 294 detal hammasi
`L=l` (burilmagan); `Turn=true` larning 564 tasi burilgan.

## 4. Loyiha → fayl moslashuvi

| Loyiha (`.project`) | `.ncp` |
|---|---|
| CS operatsiyasidagi `part` havolalarining tartib raqami (1 dan) | nom `Д<n>`, etiketka #0, #5 |
| `part name` | etiketka #3 |
| `part l`, `w` (zagotovka = kesiladigan o'lcham; `cSizeMode=1` da `dl/dw` ga teng) | tugun `L×W` (ehtimol 90° burilgan), etiketka #6/#7 |
| `jl/jw` (prifugovkadan keyin) | **ishlatilmaydi** |
| `count` | etiketka #8; barcha fayllardagi barglar × `count` yig'indisi = Σcount (32/32 material) |
| `elt/elb/ell/elr` + EL `elSymbol` + kromka nomi | etiketka #10–13 (1814/1814 mos) |
| `txt` (`Turn = not txt`) | faqat joylashtirishga ta'sir qiladi |
| CS `material` → `good sheet` `name`, `t` | etiketka #2, sarlavha qalinlik |
| ishlatilgan list/qoldiq `l×w` (CS ichidagi sheet part) | sarlavha L×W (3181 da 600×530, 2440×750 qoldiq listlar) |
| `tool.cutting swSawthick` | propil 0x1C (3) |
| `cMinDimRegWaste1/2` | qoldiq chegarasi 1000/500 |
| `cTrimL/cTrimW` (=2) | **ishlatilmaydi**; faylda 5 (savol) |
| XNC `code` (side true / false) | etiketka #17/#18 |
| XNC dasturida `gr` / frezer / parmalash | #14/#15/#16 (100% mos) |
| `product name` | etiketka #20 |
| loyiha `name` | etiketka #1 |

Loyihaning to'g'ri versiyasi topilganda (26/32 material) `.CUT Objective` dagi `F1/F4/F5/F3` va loyiha
`name/l/w/count` qator-qator 100% mos. Qolgan 6 tasi (2030, 2031, 2032, 3173) — loyiha keyin
o'zgartirilgan/boshqa versiya saqlangan (2031/2032 da faqat `dl/dw` bor).

### Tekshirilgan misollar

**A. 2027 XDF `001.ncp`** (ichki zip). Loyiha CS «XDF 2800x2070 mm 5.8 kv», `swSawthick=3`:
`01.029 XDF ort` l=1999 w=2099 count=1 → `Д1`; `01.030 HDF tr` 691×348 → `Д2`. Fayl: list 2800×2070, t=3,
ildiz `(2,1,5),(0,1,2099),(0,1,348)`, chiqindi `2800−5−2102−351=342` → `wL=342`.
Tugunlar: `#1 NONE 348×2070 @2107` → `#2 Д2 348×691 @(2107,5)`; `#3 NONE 2099×2070 @5` → `#4 Д1 2099×1999 @(5,5)`
(teskari tartib). Polosa 348: `(3,1,5),(1,1,691)` → `wW=2070−5−694=1371`. Etiketka:
`Д2,2027 mijoz,XDF 2800x2070 mm  5.8 kv,01.030 HDF tr,,2,691.00,348.00,1,false,,,,,false,false,false,,,XDF 5.8,01 shkaf`.

**B. 2027 LDSP `001.ncp`** (32 tugun, 20 barg, 4 daraja). `02.003 bok` (loyiha l=343 w=395, `elt+elb`
«kromka … 1-19 dub votan», EL `elSymbol=B`, XNC `202701_02.003` 8 ta parmalash) → `Д34 395×343 @(2316,1482)`,
etiketka `…,02.003 bok,,34,343.00,395.00,1,false,(B) 1-19 dub votan,(B) 1-19 dub votan,,,false,false,true,202701_02.003,,,01 shkaf`.
`04.006 ichki bok` count=6 → bu kartada 3 ta (`(0,3,250)`), etiketka #8 = 6. `01.027 pl utalshonka` (XNC faqat
frezer, `countMill>0`) → #15 `true`, #16 `false`.

**C. 2032 KASHMIR `003.ncp`**, `count=4`. `02.001 kupe eshik` 1948×1044 count=4, to'rt tomon kromka →
listda bitta `Д14`, `count=4` ⇒ 4 dona ✓. Ikki qoldiq: `$3 789×1830 @X=1956` (CUT `О3 794×1830`, etiketka
789×1820) va `$2 1948×773 @(5,1052)` (CUT `О2 1948×778`).

**D. 2033 ASTANA `005.ncp`** (ildiz Y bo'yicha, `.CUT Cut="false"`): `#7 NONE 2750×748 @Y=8` (CUT `Py=5`),
`Д14 @Y=151` (CUT 148) — +3 qoidasi; qoldiq `$1 2188×532 @(557,1294)` (CUT `2193×532`).

## 5. Minimal qayta tiklangan misol

Anonim: list 2750×1830×16, propil 3; bitta polosa 600 mm, unda `01_001 polka` 600×400 ×2.
Ikkala chiqindi ham qoldiq chegarasidan katta → 2 ta `$`.

```
#0 ildiz 2750x1830 @(0,0) waste 2142x1830 t=(5,0) ents=[(2,1,5),(0,1,600)]   nchild=1
  #1 $1   2137x1830 @(608,0)                                                 (2142−5)
  #2 NONE 600x1830  @(5,0)  waste 600x1019 t=(0,5) ents=[(3,1,5),(1,2,400)]  nchild=2
    #3 $2   600x1014 @(5,811)                                                (1019−5)
    #4 Д1   600x400  @(5,408)
    #5 Д1   600x400  @(5,5)
etiketkalar (4 slot = 4 barg):
 Д1,0001 mijoz,LDSP OQ,01_001 polka,,1,600.00,400.00,2,false,(A) 1-19 oq,,,,false,false,true,000101_01_001,,,01 shkaf
 $1,0001 mijoz,LDSP OQ,,,1,2137.00,1820.00,0,true,,,,,false,false,false,,,,
 $2,0001 mijoz,LDSP OQ,,,2,600.00,1014.00,0,true,,,,,false,false,false,,,,
 (bo'sh)
util = 480000 / (5032500 − 2137·1820 − 600·1014) = 0.8976
hajm = 0x1C + 6·0x208 + 0x68 + 4·0x1000 = 19636 bayt
boshi: 00 5A 42 44 | 00..7C A5 40 (2750.0) | 00..98 9C 40 (1830.0) | 00..30 40 (16.0) | 00..08 40 (3.0) | 01 00 00 00 | 01 00 00 00 | 0B C9 65 3F
```

Yozuvchi (149/149 namunani baytma-bayt takrorlaydi):

```python
import struct
CC = b'\xcc'
def wstr(s, n):                       # UTF-16LE + NUL, qolgani 0xCC
    b = s.encode('utf-16le') + b'\0\0'; return b + CC*(n-len(b))
def write_ncp(L, W, t, kerf, count, util, nodes, labels):
    # nodes: pre-order; har biri dict(parent,nchild,L,W,wL,wW,tx,ty,X,Y,ents=[(tur,soni,o'lcham)],name)
    def body(n):
        b = struct.pack('<2i8d', n['parent'], n['nchild'], n['L'], n['W'], n['wL'], n['wW'],
                        n['tx'], n['ty'], n['X'], n['Y'])
        for e in list(n['ents']) + [(0,0,0.0)]*(22-len(n['ents'])): b += struct.pack('<iid', *e)
        return b + struct.pack('<i', len(n['ents'])) + CC*4
    out = b'\x00ZBD' + struct.pack('<3d', L, W, t)
    out += struct.pack('<d2ifi', kerf, count, count, util, len(nodes))
    out += bytes.fromhex('00000000000045000000') + CC*54 + body(nodes[0])
    for n in nodes[1:]:
        out += struct.pack('<i', -1) + b'\0'*16 + CC*4 + wstr(n['name'], 0x40) + body(n)
    out += struct.pack('<i', -1) + b'\0'*16 + CC*4 + struct.pack('<d', 5.0) \
           + wstr('MATERIAL NAME', 0x40) + struct.pack('<2i', 1, count)
    for s in labels: out += wstr(s, 0x1000)
    return out
```

Generatsiya algoritmi (MebeliX natijasidan): har noyob karta → daraxt; 0/1‑darajaga torsovka yozuvi;
bo'laklarni kesish tartibida yozuvlarga guruhlash (bir xil detal ketma-ket → bitta yozuv); chiqindi,
koordinata (Y‑ildizda +propil), qoldiq qoidasi; tugunlarni teskari bola tartibidagi pre‑order bilan
yozish; etiketkalar; `util`; zip (deflate) — boshqa materiallar ichki stored zip sifatida.

## 6. Ochiq savollar

1. **Torsovka 5 mm** qayerdan? Loyihada `cTrimL/W=2`, `swMinPruning=5`. Bu postprotsessor/stanok
   sozlamasimi (`.CUT Sx/Sy=5` ham)? Boshqa qiymat (masalan 10) bo'lsa dumdagi `5.0` ham o'zgaradimi?
2. **Y‑ildizdagi +3 siljish** — stanok uchun to'g'ri koordinatami yoki eksport xatosi? Stanok aynan shu
   qiymatlar bilan to'g'ri kesyaptimi (biz uni ko'chirib takrorlaymiz)?
3. **Ichki zip** qaysi material tashqi bo'lishini kim belgilaydi (2032 da tashqisi KASHMIR, CS tartibida
   DUB VATAN birinchi; 2030 da XDF umuman yo'q)? Stanok dasturi ichki zipni o'qiydimi yoki operator
   qo'lda ochadimi?
4. Qoldiq raqami `$k` qaysi tartibda (listlar bo'yicha, ichida chuqurroq daraja avval?) — stanok uchun
   ahamiyatlimi?
5. Etiketka CSV da vergul/qo'shtirnoqli nom kelsa nima bo'ladi (namunada yo'q)? 2048 belgidan uzun?
6. Maydon #4 (F2) va #18–19 qachon to'ladi; #19 `Data/@Type` (faqat XDF da bor) — MebeliX da qaysi
   maydondan olinadi?
7. `swMaxturns`, `swPackageHeight` (paket balandligi) faylga yozilmaydi — stanokda qo'lda o'rnatiladimi?
8. Aylantirish/ tekstura bayrog'i faylda yo'q — stanok etiketkada `l,w` va tugun `L,W` farqidan foydalanadimi?
