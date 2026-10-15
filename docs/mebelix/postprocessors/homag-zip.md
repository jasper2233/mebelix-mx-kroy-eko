# HOMAG (`.zip`, ichida `pattern.NNN`) — postprotsessor formati

Manba namunalar: `post prtsessorlar/PILNIY APPARAT/HOMAG/*.zip` (10 ta buyurtma: 3151, 3152, 3153, 3155, 3156, 3157, 3158, 3159, 3160, 3161 — jami 44 ta pattern fayl, 765 ta `#CUT` yozuv).
Solishtirish uchun loyihalar: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project`.

> Muhim: har bir buyurtma papkasida ikkita loyiha bor — `NNNN mijoz.project` (probel bilan, hisoblanmagan:
> `part` larda `l/w/cl/cw/jl/jw` yo'q, `CS` operatsiyada natija yo'q) va `NNNN_mijoz.project` (pastki chiziq bilan,
> raskroy hisoblangan: `cl/cw/jl/jw`, `cMaterialCount`, `usedCount`, `data` blob bor). HOMAG fayllari **pastki chiziqli**
> variantga to'liq mos keladi (quyidagi tekshiruvlar shu variant bo'yicha).

Ishonch darajasi: **qisman → deyarli to'liq**. Kesish daraxti (strukturasi, o'lchamlar, takrorlar, yo'nalish) 100% tasdiqlandi;
noma'lumlar — konstant maydonlar (`#SPEEDS`, `#TRIMS` ning 3–5-maydonlari, `#CUT` ning 5–14-maydonlari, `#DIMENSION` 4-maydoni),
daraja kodlari 7/9 ning rasmiy nomi va bir xil raskroyli listlar soni (kitob/stopka) qayerda berilishi.

---

## 1. Hosil bo'ladigan fayllar

| Xususiyat | Qiymat |
|---|---|
| Tashqi fayl | `<buyurtma raqami>_<mijoz>_<material nomi>.zip`, masalan `3161_mijoz_LDSP_PIKARD.zip` |
| Fayl nomi qoidasi | `product.order` (`"3161 mijoz"`) dagi probel → `_`, keyin `_`, keyin list materiali `good[@typeId=sheet]/@name` dagi probellar → `_` (ketma-ket bir nechta probel bitta `_` ga aylanadi: `"LDSP  PIKARD"` → `LDSP_PIKARD`) |
| Bir buyurtmaga | **har bir material (har bir `CS` operatsiya) uchun bitta zip**. Namunalarda faqat asosiy plita materiali bor; loyihadagi boshqa materiallar (`XDF 2800x2070 mm 5.8 kv`, `LDSP ASTATKA`, ikkinchi LDSP/LMDF) uchun zip namunalarda yo'q |
| Zip ichida | papka yo'q, faqat yassi fayllar: `pattern.001`, `pattern.002`, … (3 xonali, 001 dan ketma-ket) |
| Pattern fayllar soni | 1 dan 10 gacha (namunalarda). Bitta fayl = bitta raskroy kartasi (list sxemasi) — batafsil 3.4 bo'limda |
| Zip parametrlari | Deflate (`compress_type=8`), `flag_bits=0x0808` (data descriptor + UTF-8 nom bayrog'i — oqimli yozuvchi, masalan Java `ZipOutputStream`), izoh yo'q, `create_system=0` |
| Kodirovka | Sof ASCII (barcha 44 faylda 0x80+ bayt yo'q). Kirill matn qanday yozilishi noma'lum (savol) |
| Qator oxiri | CRLF (`\r\n`), oxirgi qatordan keyin ham CRLF bor |
| Har qator | `#KALIT,` bilan boshlanadi, maydonlar `,` bilan ajratiladi, **har qator oxirida ortiqcha `,` bor** |
| O'nli ajratkich | nuqta (`0.00`, `2.0`, `0.00000`) |
| Birlik | mm |

Fayldagi qatorlar soni = 4 (sarlavha) + `#CUT` qatorlar soni (barcha 44 faylda tekshirildi).

---

## 2. To'liq struktura

Fayl har doim aynan shu tartibda:

```
#REMARK,<buyurtma>,<material nomi>,
#DIMENSION,<D1>,<D2>,<qalinlik>,0,
#SPEEDS,0.00,0.00,0.00,0.00,
#TRIMS,2.0,2.0,0.0,0.0,0,
#CUT,<daraja kodi>,<o'lcham>,<takror>,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,...
```

### 2.1 `#REMARK`
| # | Ma'no | Tip | Namunalar | Manba |
|---|---|---|---|---|
| 1 | Buyurtma nomi | matn | `3161 mijoz`, `3157 mijoz` | `good[@typeId=product]/@product.order` (probel bilan; loyiha `@name` dagi `_` emas) |
| 2 | Material nomi | matn | `LDSP  PIKARD` (ikki probel saqlangan!), `LMDF BELI KARONA GLYANETS` | `good[@typeId=sheet]/@name` — o'zgarishsiz |
| (oxirgi) | bo'sh (trailing `,`) | | | |

### 2.2 `#DIMENSION`
| # | Ma'no | Tip | Ko'rilgan | Izoh |
|---|---|---|---|---|
| 1 | D1 — **1-daraja kesimlari joylashadigan o'q** bo'yicha list o'lchami | butun | `2750` (24 fayl) yoki `1830` (20 fayl) | List har bir pattern uchun 0° yoki 90° burilgan bo'lishi mumkin |
| 2 | D2 — ikkinchi o'q (2-daraja kesimlari o'qi) | butun | `1830` yoki `2750` | |
| 3 | Qalinlik | butun | `16` | `good[@typeId=sheet]/@t` |
| 4 | noma'lum | butun | har doim `0` | Taxmin: listlar soni / burilish bayrog'i / material kodi — savol |

Sheet o'lchami: `good[@typeId=sheet]/part[@count=10000]/@l,@w` (2750×1830). Yo'nalish: D1=2750 bo'lsa 1-daraja kesimlari
2750 o'qi bo'ylab o'lchanadi (tasma eni ≤ 2750, masalan `2254`), D1=1830 bo'lsa ≤1830 (masalan `211`, `1230`).

### 2.3 `#SPEEDS`
4 ta `0.00` — barcha 44 faylda konstant. Taxmin: arra tezliklari (har daraja uchun) — mashina o'z sozlamasidan oladi. Konstanta sifatida yoziladi.

### 2.4 `#TRIMS`
`2.0,2.0,0.0,0.0,0` — barcha faylda konstant.
- 1 va 2-maydon = loyiha `CS` operatsiyasidagi `cTrimL="2"`, `cTrimW="2"` (list chetidan kromka obrezkasi, mm). Namunalarda ikkalasi ham 2, shuning uchun qaysi biri L, qaysi biri W ekanini ajratib bo'lmadi (taxmin: 1-maydon = D1 o'qi, 2-maydon = D2 o'qi; yoki doim L/W) — savol.
- Tekshiruv: barcha patternlarda 1-daraja kesimlar yig'indisi + kesimlar soni×3 ≤ D1 − 2×2 (minimal zaxira 3 mm, 3157 va 3160 da). Ya'ni trim ikki tomondan ayriladi.
- 3, 4-maydon (`0.0`) va 5-maydon (`0`) noma'lum (taxmin: ichki darajalardagi trim / "trim kesimi arra eni bilan" bayrog'i, `swTrimIncludeSaw="false"`).

### 2.5 `#CUT` (asosiy ma'lumot)
| # | Ma'no | Tip | Ko'rilgan qiymatlar |
|---|---|---|---|
| 1 | Kesim **daraja kodi** | butun | `1` (129), `2` (292), `3` (250), `7` (83), `9` (11) |
| 2 | Bo'lak o'lchami (kesim qadami), mm | butun (namunalarda kasr yo'q) | 40 … 2650 |
| 3 | Takror soni (shu bo'lak o'z ichki daraxti bilan necha marta ketma-ket kesiladi) | butun | 1 (706), 2 (45), 3 (12), 4 (1), 7 (1) |
| 4–8 | noma'lum | butun | doim `0` |
| 9 | noma'lum | kasr, 5 xona | doim `0.00000` |
| 10–13 | noma'lum | butun | doim `0` |

Daraja kodlari → mantiqiy daraja (barcha 765 qator daraxtga xatosiz yig'ildi):

| Kod | Daraja | Ma'no | O'lchanadigan o'q |
|---|---|---|---|
| `1` | 1 | Listni tasmalarga bo'lish (bo'ylama/asosiy kesim) | D1 |
| `2` | 2 | Tasmani ko'ndalang kesish | D2 |
| `3` | 3 | 2-daraja bo'lagini qayta kesish | D1 |
| `7` | 4 | 3-daraja bo'lagini qayta kesish | D2 |
| `9` | 5 | 4-daraja bo'lagini qayta kesish | D1 |

Kodlar raqami ketma-ket emas (1,2,3,7,9) — 4,5,6,8 kodlari namunalarda uchramadi (ehtimol bosh kesim/head-cut yoki
burilish uchun ajratilgan — savol). Loyiha `swMaxturns="4"`/`"6"` — maksimal daraja soni; namunalarda eng chuqur daraja 5.

---

## 3. Raskroy rejasi qanday kodlangan

### 3.1 Daraxt (pre-order)
`#CUT` qatorlari — kesish daraxtining **chuqurlik bo'yicha oldindan tartiblangan (pre-order)** ro'yxati. Har bir qator — bitta
bo'lak (piece); undan keyin kelgan va darajasi kattaroq qatorlar uning bolalari. Darajasi kichik yoki teng qator kelganda
ota darajaga qaytiladi. Daraja hech qachon 1 tadan ortiq sakramaydi (1→2→3→7→9).

```
parse:
  stack = [root(level 0, size=(D1,D2))]
  for each #CUT (code, size, rep):
      lvl = {1:1, 2:2, 3:3, 7:4, 9:5}[code]
      while stack.top.level >= lvl: stack.pop()
      assert stack.top.level == lvl-1
      node = (lvl, size, rep); stack.top.children.append(node); stack.push(node)
```

Bo'lak geometriyasi: ota bo'lak `(a, b)` bo'lsa (a — D1 o'qi, b — D2 o'qi), toq darajadagi (1,3,5) bola `(size, b)`,
juft darajadagi (2,4) bola `(a, size)` bo'ladi.

### 3.2 Detallar = barglar
- **Bolasi yo'q har bir tugun (barg) = bitta tayyor detal**, o'lchami yuqoridagi qoida bo'yicha, soni = yo'ldagi barcha `rep` larning ko'paytmasi.
- Bolalari bor tugunda bolalar yig'indisidan ortgan qism — **chiqindi**; u faylda yozilmaydi.
- 1-daraja tasmalar yig'indisidan ortgan list qismi (shu jumladan loyihadagi `waste="true" business="true"` delovoy qoldiq, masalan `rl=1595 rw=1830`) ham yozilmaydi. Qoldiq alohida belgilanmaydi.
- Detal nomi, kodi, etiketka, kromka, material kodi faylda **yo'q** — mashina faqat o'lchamlar bo'yicha kesadi.
- Arra eni (kerf) faylda yozilmaydi; mashina o'z arrasidan oladi. Optimizator kerf=3 bilan joylagan (`swSawthick="3"`): har bir ota bo'lakda Σ(size·rep) + 3·Σrep ≤ ota o'lchami (barcha 44 faylda bajariladi; ko'p hollarda zaxira aynan 2 mm). 1-darajada: Σ + 3·n ≤ D − 2·trim.

### 3.3 Takror (`rep`)
`rep>1` butun ichki daraxt bilan qo'llanadi: `#CUT,2,300,3` + `#CUT,3,346,1` → 3 ta 300 mm tasma, har birida 346 bo'lak → 3 ta 346×300 detal.
Bir xil o'lchamli qo'shni barglar har doim ham birlashtirilmaydi: 3152 da `#CUT,3,80,2` ketma-ket ikki marta — loyihada ular
ikki alohida `part` yozuvi (`id=25` va `id=26`, ikkalasi `code=01_025`, `count=2`, kromka tomoni turlicha). Ya'ni `rep` bitta
`part` yozuvi doirasida guruhlanadi (generatorda majburiy emas — birlashtirsa ham to'g'ri fayl bo'ladi, taxminan).

### 3.4 Listlar soni / kitob (stopka)
Faylda listlar soni **yo'q** (`#DIMENSION` 4-maydoni doim 0). Solishtirish:

| Buyurtma | Loyihada ishlatilgan list (`usedCount`/`cMaterialCount`) | pattern fayllar | Farq |
|---|---|---|---|
| 3151 | 6 | 6 | 0 |
| 3152 | 2 | 2 | 0 |
| 3153 | 5 | 5 | 0 |
| 3155 | 3 | 3 | 0 |
| 3156 | 8 | 7 | yetishmagan detallar = aynan `pattern.001` barglari (11 dona) |
| 3157 | 7 | 5 | yetishmagan = `pattern.001` + `pattern.002` barglari; `pattern.001` va `pattern.003` baytma-bayt bir xil |
| 3158 | 2 | 2 | 0 |
| 3159 | 3 | 3 | 0 |
| 3160 | 11 | 10 | yetishmagan = `pattern.001` barglari (20 dona) |
| 3161 | 1 | 1 | 0 |

Izoh (eng mos gipoteza): bitta fayl = bitta **kitob (stopka)**. `swPackageHeight="40"`, qalinlik 16 → bir kitobda ko'pi bilan
2 list. 3157 da `pattern.001`-sxema 3 listda (kitob 2 + kitob 1 → `001` va `003` bir xil fayl), `pattern.002` 2 listda (1 kitob).
3156 va 3160 da `pattern.001` 2 listli kitob. Ammo kitobdagi listlar soni faylda ko'rsatilmagan → operator qo'lda kiritadi yoki
generator xatosi (savol #1). Takrorlangan sxemalar har doim birinchi fayllarda (eng katta "paket" birinchi: `cPrefLargePacket="true"`).

### 3.5 Tola yo'nalishi (tekstura)
Alohida maydon yo'q, lekin joylashuvda saqlanadi: `txt="true"` bo'lgan barcha detallarning `cl` o'lchami listning 2750 o'qi
bo'ylab joylashgan (3151: 29/29, 3153: 19/19, 3155: 23/23, 3159: 11/11, 3160: 105/105, 3161: 1/1). `txt="false"` detallar
ikkala yo'nalishda uchraydi. Shuning uchun yo'nalish `#DIMENSION` dagi D1/D2 tartibi va daraja o'qi orqali aniqlanadi.

---

## 4. Loyiha ma'lumotlaridan maydonlarga moslik

| Fayldagi joy | Loyiha manbasi |
|---|---|
| zip nomi | `product.order` + `_` + material nomi (probellar→`_`) |
| `#REMARK` 1 | `good[@typeId=product]/@product.order` |
| `#REMARK` 2 | `good[@typeId=sheet]/@name` (CS operatsiyadagi `material/@id` orqali) |
| `#DIMENSION` 1,2 | `sheet/part[@count=10000]/@l,@w` (yoki `operation[@typeId=CS]/@l,@w`), pattern burilishiga qarab tartib |
| `#DIMENSION` 3 | `sheet/@t` (= `CS/@t`) |
| `#TRIMS` 1,2 | `CS/@cTrimL`, `CS/@cTrimW` |
| barg o'lchamlari | `part/@cl`, `part/@cw` (kesish o'lchami). Kromka qalinligi **ayrilmaydi**: namunalarda `cl=l=dl`, `jl/jw` (kromkasiz o'lcham, masalan `jl=1898 jw=346` 3 tomonli 1 mm kromka uchun) faylga **tushmaydi** |
| barglar soni | Σ `part/@count` (CS operatsiyasiga biriktirilgan `cl` li partlar) |
| kerf | faylda yo'q (`tool.cutting/@swSawthick` faqat joylashuvga ta'sir qiladi) |

### Tekshiruv (barglar multiset'i vs loyiha `(cl,cw)×count`)
Skript: barcha patternlarni daraxtga yig'ib barglarni sanash, loyihadagi shu material `CS` operatsiyasi partlari bilan solishtirish.

| Buyurtma | Barglar | `cPartCount` / Σcount | Natija |
|---|---|---|---|
| 3151 | 61 | 61 | to'liq mos |
| 3152 | 39 | 39 | to'liq mos |
| 3153 | 70 | 70 | to'liq mos |
| 3155 | 33 | 33 | to'liq mos |
| 3156 | 62 | 73 | farq 11 = takrorlangan `pattern.001` (3.4) |
| 3157 | 25 | 36 | farq 11 = `pattern.001` + `pattern.002` |
| 3158 | 30 | 30 | to'liq mos |
| 3159 | 20 | 20 | to'liq mos |
| 3160 | 145 | 165 | farq 20 = `pattern.001` |
| 3161 | 18 | 18 | to'liq mos |

`l/w` va `dl/dw` bilan ham bir xil natija (bu namunalarda ular `cl/cw` ga teng); `jl/jw` bilan mos kelmaydi.

### Aniq misol 1 — 3161 (`pattern.001`, D1=2750)
Loyiha: `01_001 bok` 1900×347 (1), `01_002 bok` 1900×347 (1), `01_003 tom` 868×347 (1), `01_004 polka` 868×346 (2+2),
`01_005 pol` 868×346 (1), `01_006 Fasad` 498×420 (2, `txt=true`), `01_007 bok` 504×346 (1), `01_008 bok` 300×346 (6),
`01_009 sokl` 100×868 (1). Jami 18.

```
#CUT,1,2254,1          tasma 2254 (2750 o'qi bo'ylab)
#CUT,2,420,1             420 li ko'ndalang bo'lak
#CUT,3,498,2               → 498×420 ×2   (01_006 Fasad, tola 2750 bo'ylab)
#CUT,3,868,1                 868×420 bo'lak
#CUT,7,346,1                 → 868×346    (polka; 74 mm chiqindi)
#CUT,3,346,1                 346×420
#CUT,7,300,1                 → 346×300    (01_008)
#CUT,2,346,1             → 300, 868, 868 ... (keyingi qatorlar)
...
#CUT,1,352,1           tasma 352
#CUT,2,868,1  #CUT,3,347,1   → 868×347 (01_003)
#CUT,2,300,3  #CUT,3,346,1   → 300×346 ×3 (01_008)
#CUT,1,100,1  #CUT,2,868,1   → 100×868 (01_009 sokl)
```
1-daraja: 2254+352+100 + 3·3 = 2715 ≤ 2750−4. 01_008 jami: 1+1+1+3 = 6 ✓.

### Aniq misol 2 — 3159 (3 fayl, 3 list, 20 detal)
`pattern.003` da `#DIMENSION,1830,2750` (list burilgan): `#CUT,1,211` (1830 o'qi bo'ylab) → `#CUT,2,2360` → `#CUT,3,100,2` = 2360×100 ×2.
Loyiha: 2360×100 (2), 2360×95 (2), 1825×533 (6), 564×533 (6), 1755×150 (2), 1755×100 (2) — barglar bilan to'liq mos.
Hammasi `txt=true` va uzun tomoni 2750 o'qida. (Bu loyihada `swSawthick="6"`; kerf baribir faylga yozilmagan.)

### Aniq misol 3 — 3157 (takrorlangan list)
`pattern.001`: `#CUT,1,2618` → `#CUT,2,597` ×3 qator, uchinchisi ichida `#CUT,3,1160` ×2 → 2618×597 ×2, 1160×597 ×2; `#CUT,1,100` → `#CUT,2,1805` → 1805×100.
`pattern.003` aynan shu fayl. Loyihada 2618×597 = 6, 1160×597 = 6, 1805×100 = 3 → bu sxema 3 listda kesilgan, fayllarda esa faqat 2 marta.

### Aniq misol 4 — 3152 (5-daraja)
```
#CUT,2,466,1
#CUT,3,120,1            → 120×466 ... (barg)
#CUT,3,534,1              534×466
#CUT,7,400,1            → 534×400
#CUT,7,50,1               534×50
#CUT,9,500,1            → 500×50   (5-daraja, `code=9`)
```
Loyiha: 534×400 (2), 500×50 (`01_026`, 2) ✓.

---

## 5. Minimal qayta tiklangan misol

Bitta list 2750×1830×16, trim 2, kerf 3. Detallar: 1900×347 ×2, 900×560 ×2 (tola bo'ylab), 400×300 ×1.
Zip nomi: `0001_mijoz_LDSP_OQ.zip`, ichida bitta `pattern.001` (ASCII, CRLF):

```
#REMARK,0001 mijoz,LDSP OQ,
#DIMENSION,2750,1830,16,0,
#SPEEDS,0.00,0.00,0.00,0.00,
#TRIMS,2.0,2.0,0.0,0.0,0,
#CUT,1,1900,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,2,347,2,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,2,560,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,3,900,2,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,1,800,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,2,600,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,3,400,1,0,0,0,0,0,0.00000,0,0,0,0,
#CUT,7,300,1,0,0,0,0,0,0.00000,0,0,0,0,
```
Tekshiruv: 1-daraja 1900+800+2·3 = 2706 ≤ 2746; 1900-tasmada 2·347+560+3·3 = 1263 ≤ 1826; 560-bo'lakda 2·900+2·3 = 1806 ≤ 1900;
800-tasmada 600+3 ≤ 1826; 600×800 bo'lakda 400+3 ≤ 800; 400×600 bo'lakda 300+3 ≤ 600. Barglar: 1900×347 ×2, 900×560 ×2, 400×300 ×1.

Generator algoritmi (MebeliX Kroy uchun):
1. Har bir material (list turi) bo'yicha alohida zip.
2. Har bir **noyob list sxemasi** (yoki kitob) uchun `pattern.NNN` — tartib: ko'p takrorlanadigan sxemalar birinchi.
3. Gilotina daraxtini pre-order bilan yozish; daraja→kod: 1→1, 2→2, 3→3, 4→7, 5→9. 5 dan chuqur daraja ishlatmaslik.
4. Bir xil o'lchamli ketma-ket qo'shni bo'laklarni (bir xil ichki daraxt bilan) `rep` ga birlashtirish.
5. O'lchamlar butun mm (kasr o'lcham formati noma'lum — savol #5).
6. Barcha konstantalar namunadagidek; har qator oxirida `,` va CRLF.

---

## 6. Noma'lum / noaniq joylar — savollar

1. **Listlar soni**: bir xil sxema bir necha listda kesilsa, mashina buni qanday biladi? Fayllar soni loyiha listlaridan kam (3156: 7/8, 3157: 5/7, 3160: 10/11). Kitob (stopka, `swPackageHeight=40` → 2 list) operator tomonidan qo'lda kiritiladimi? `#DIMENSION` 4-maydoni (doim `0`) shu son uchunmi?
2. `#DIMENSION` 4-maydoni (`0`) nimani bildiradi (list soni, burilish, material/ombor kodi)?
3. `#TRIMS`: 1 va 2-maydon qaysi tomonlarga tegishli (cTrimL/cTrimW yoki D1/D2 o'qi)? 3–5-maydonlar (`0.0,0.0,0`) nima — ichki darajalar trimi, bosh kesim, flag?
4. `#SPEEDS` 4 ta qiymat (doim `0.00`) — mashina sozlamasidan olinadimi, nol yuborish xavfsizmi?
5. `#CUT` 4–13-maydonlari (5 ta int, `0.00000`, 4 ta int) — doim nol. Ehtimol: detal ID/etiketka, burilish, qo'shimcha trim, chiqindi bayrog'i. Kasr o'lcham (masalan 346.5) qanday yoziladi — `346.5` mi yoki yaxlitlanadimi?
6. Daraja kodlari `7` va `9` (4- va 5-daraja) — nega 4/5 emas? 4, 5, 6, 8 kodlari bormi (bosh kesim / head-cut, plitani burish)? 5 dan chuqur daraja (`swMaxturns=6`) qanday kodlanadi?
7. Delovoy qoldiq (`business waste`) va chiqindi faylda belgilanmaydi — mashina qoldiqqa etiketka chiqarishi kerakmi?
8. Kirill harflari (`#REMARK` dagi buyurtma/material nomida) uchun qaysi kodirovka kutiladi (namunalarda faqat ASCII)?
9. Ikkinchi darajali materiallar (XDF, ASTATKA) uchun ham HOMAG zip yaratiladimi (namunalarda yo'q)?
