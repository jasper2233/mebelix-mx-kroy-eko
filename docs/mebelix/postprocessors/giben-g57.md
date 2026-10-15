# Giben G57 — `.fdt` (Giben Prisma «FDT/FDS» INI-matn) postprotsessori

Holat: **to'liq**. 7/7 namuna fayl loyiha (`.project`) + kesish daraxtidan **bayt-ma-bayt qayta yasaldi** (1-bo'limdagi qoidalar va 2-bo'limdagi shablonlar bilan). Bir nechta o'zgarmas maydonlarning ma'nosi taxminiy (6-bo'lim).

Manba namunalar: `post prtsessorlar/PILNIY APPARAT/GIben G57/*.fdt` (7 ta fayl: 3151, 3153, 3155, 3156, 3157, 3159, 3161).
Mos loyiha: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` (**pastki chiziqli** variant; bo'sh joyli `NNNN mijoz.project` — eski import, CS natijasi yo'q).

Format Giben/Prisma optimallashtiruvchisining ichki fayli: italyancha kalit so'zlar (`PANNELLO`=list, `ELEMENTO`=detal, `TAGLIO`=kesim, `RIFILO`=torsovka, `SPESSORELAMA`=arra qalinligi, `RIPETIZIONI`=takror). `FDT` qismi — kirish ma'lumotlari (listlar, detallar), `FDS` qismi — optimallash natijasi (kartalar, joylashuv, kesimlar ketma-ketligi).

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.fdt` (bitta oddiy matn fayl, arxiv emas) |
| Nomlash | `<loyiha nomi>_<material nomi>.fdt`; materialdagi bo'shliqlar `_` ga, ketma-ket bo'shliqlar bitta `_` ga (`LDSP  PIKARD` → `LDSP_PIKARD`). Masalan `3161_mijoz_LDSP_PIKARD.fdt` |
| Soni | Buyurtmaga **1 fayl** — namunalarda faqat **birinchi CS operatsiyasi** (loyihadagi birinchi `operation typeId="CS"`, ya'ni birinchi material) eksport qilingan. Masalan 3151 da 3 material bor (LMDF…GLYANETS, LDSP…GLYANETS, XDF), faylda faqat birinchisi |
| Kodlash | ASCII (cp1251 deb o'qish xavfsiz); namunalarda ASCII bo'lmagan belgi yo'q (detal nomlari faylga yozilmaydi) |
| Qator oxiri | faqat `LF` (`\n`), `CR` yo'q; oxirgi qator ham `\n` bilan tugaydi |
| Sintaksis | `[StartXxx]` / `[EndXxx]` bo'lim teglari + `KALIT = QIYMAT` qatorlari (`=` atrofida bitta bo'shliq; bo'sh qiymat — `KALIT = ` oxirida bo'shliq bilan) |
| Birlik | **mm × 1000** (mikron), butun son: `2750000` = 2750 mm, `1831500` = 1831,5 mm |
| Mantiqiy | `-1` = rost, `0` = yolg'on (VB uslubi) |
| O'nlik ajratgich | ishlatilmaydi (hamma son butun) |

## 2. To'liq struktura

Fayl qat'iy tartibdagi bo'limlardan iborat. Quyida **aynan shablon** (qator tartibi muhim): `{...}` — ma'lumotdan to'ldiriladigan joy, qolgani doimiy (7/7 namunada bir xil).

### 2.1 Bosh qism (Generale, Produzione)

```
[StartGenerale]
VERSIONE = 6
[EndGenerale]
[StartProduzione]
NUMOTTIMIZZAZIONI = 1
[StartOtt1]
MATERIALE = {material nomi}
SPESSORE = {qalinlik ×1000}
SCARICATA = 0
RIGA = 23
APPLICAZIONE = 
VERSIONEOTT = 
COLORE = Colore
CODTIPO = 
DESCR = 
CODMAT = {material nomi}
CODCOL = COL
PEZZINONPOS = 0
TAGLIABILE = -1
[EndOtt1]
[EndProduzione]
```

### 2.2 Parametrlar

```
[StartOttimizzazioni]
[StartOttimizzazione1]
[StartParametri]
[StartParametriPriorita]
ABILITAPRIORITA = 0
GREZZO = 0
SFRIDO = 0
COIL = 0
SEMILAVORATO = 0
PRODOTTOFINITO = 0
[EndParametriPriorita]
[StartParametriPannelli]
CODGRUPPO = 
PARTENZA = LASTRE
SPESSORE = {qalinlik ×1000}
PROFSCAN = 10000
CODMATERIALE = {material nomi}
MATERIALE =  {material nomi}          ← «= » dan keyin IKKI bo'shliq (nom oldida qo'shimcha bo'shliq)
VELMATERIALE = 150000
CODCOLORE = COL
COLORE = Colore
CODTIPO = 
PESOSPECIFICO = 0
DESCRPRODUZIONE = MATERIALE|COLORE|1
RIFVALORIZ = -1
[EndParametriPannelli]
[StartParametriMacchina]
CODMACCHINA = 0
NOMEMACCHINA = 
OTTSEMPLIFICATA = 0
GESTAUTOSBORDI = 0
ORDPZSTR = 0
TEMPIMEDIOCICLO = 0
ACCORPAPEZZISUMISURE = 0
ACCORPAPEZZISUMISURECODICE = 0
[EndParametriMacchina]
[StartParametriGenerali]
TIPOSTRISCE = 1
LIVELLITAGLIO = 4
ORIGINEASSI = 0
POSIZIONESFRIDI = 0
XORDINAPER = 0
XORDINADIR = 1
YORDINAPER = 0
YORDINADIR = 0
MANTIENILOGICO = 0
SPESSORELAMA = {arra qalinligi ×1000}
DIAMETROLAMA = 390000
```
so'ng quyidagi kalitlarning **har biri `= 0`** (shu tartibda): `LUNGHEZZALAMA, MINIMOX, MINIMOY, MASSIMOX, MASSIMOY, QTFSTGVER, MINSTRISCIAX, MINSTRISCIAY, BATTUTA, PINZEY1, PINZEY2, PRETAGLI, RIFPRETG, RIFPRETAGLIOR, MINIMOPRE, MASSIMOPRE, PRETAGLIORIZ, PRETAGLIOZ`, keyin
```
NOMEPOSTP = 
ALTEZZAPACCO = 90000
```
keyin yana `= 0`: `RIPETIZIONI, TIPOSFRIDO, MAGGIORAZIONE, ECCEDENZAPERC, POSIZIONI, RINUMERAPOS, LIBERAPOS, LUNGMINCOIL, ECCRIP, STIRAMENTO, FORMATOUNICO, MAXNUMSTRISCIE, MAXNUMSTRISCIEPRETG, MAXPROFPRETAGLIO, LIVTGSXPRETG, COSTOTGX, COSTOTGY, COSTOTAGLISUCC, COSTOPRETAGLIO, COSTOSBANCATA, COSTOFISSO, MINIMOSFRIDOX, MINIMOSFRIDOY, MINIMOMIGLIORESFRIDOX, MINIMOMIGLIORESFRIDOY, COL2LIVELLO`, va oxiri:
```
OTTIMIZZA = -1
RIFILOMIN = 0
[EndParametriGenerali]
[EndParametri]
```

### 2.3 `PannelliFDT` — list (format) ta'rifi

```
[StartPannelliFDT]
[StartDatiPannelloFDT1]
NUMEROPANNINIZ = 1
NUMEROPANN = 1
[StartDatiPannelloFDT1]          ← DIQQAT: xuddi shu teg ikkinchi marta (generator xatosi, lekin aynan shunday)
NUOVO = -1
SFRIDO = 0
FAMIGLIA = 
RIGA = -1
IDL = {list id}
DES = 
BARCODE = 
XBA = {list uzunligi l ×1000}
YAL = {list eni w ×1000}
QTAINIZ = {jami list soni}
QTA = {jami list soni}
COS = 0
PRT = 0
COD = {list id}
MINTRONC = 0
CAV = 0
TIPOPANNELLO = 0
RUOT = -1
SBN = 0
SBS = 0
SBE = 0
SBO = 0
MINIMOSFRIDOX = 0
MINIMOSFRIDOY = 0
MINIMOMIGLIORESFRIDOX = 0
MINIMOMIGLIORESFRIDOY = 0
NUMCAV = 0
INSERTMAN = -1
[EndDatiPannelloFDT1]
[EndPannelloFDT1]               ← yopuvchi teg nomi ochuvchidan farq qiladi — aynan shunday yozish kerak
[EndPannelliFDT]
```

| Maydon | Ma'no | Manba |
|---|---|---|
| `IDL`, `COD` | list (format) identifikatori | CS operatsiyasidagi list-part id (`<good typeId="sheet"><part id=…>`; masalan 3161 da `12`, 3151 da `79`) |
| `XBA`, `YAL` | list uzunligi/eni | `sheet/@l`, `sheet/@w` (namunalarda doim 2750×1830) |
| `QTAINIZ`, `QTA` | ishlatiladigan listlar soni | `operation/@cMaterialCount` = Σ `RIPETIZIONI` (6, 5, 3, 8, 7, 3, 1 — hammasi mos) |

### 2.4 `ElementiFDT` — detallar ro'yxati (har bir loyiha detal-qatori uchun 1 ta)

```
[StartDatiElementoFDT{i}]
NUOVO = -1
RIGA = 0
IDP = {detal id}
FAMIGLIA = 
BARCODE = 
DISEGNO = 
PRODUZIONE = 
COMMESSA = 
CLIENTE = 
XBA = {l ×1000}
YAL = {w ×1000}
QTAINIZ = 0
QTA = 0
RUOT = 0
URG = 0
CAV = 0
SBN = 0
SBS = 0
SBE = 0
SBO = 0
IN = 5132488
BN = 
IS = 1242984
BS = 
IE = {i}
BE = 
IO = 0
BO = 
COD = 
ORD = 0
ECCPOS = 0
ECCNEG = 0
MAGGPOSX = 0
MAGGNEGX = 0
MAGGPOSY = 0
MAGGNEGY = 0
NUMLAV = 0
DATA = 
IDL = 0
LCOD = 
LXBA = 0
LYAL = 0
ELSFRIDO = 0
INSERTMAN = -1
DESCRIZIONE = 
TIPORECORD = 0
NUMPEZZIBASEPALLET = 0
NUMPEZZIALTEZZAPALLET = 4203419
ALTEZZAPALLET = 0
DESCRORDINE = 
DATAORDINE = 
SORDINE = 
[EndDatiElementoFDT{i}]
```

| Maydon | Ma'no | Tekshiruv |
|---|---|---|
| `i` (teg raqami) va `IE` | 1..N tartib raqami | N = CS operatsiyasidagi detal-qatorlar soni (29, 55, 23, 42, 22, 11, 10) |
| tartib | **CS operatsiyasidagi `<part id>` tartibi** (loyihadagi `product` tartibi emas) | 7/7 mos (masalan 3151: 42, 44, 43, 46, 45, …) |
| `IDP` | loyiha detal `part/@id` | 192/192 mos |
| `XBA`, `YAL` | detal `l` va `w` (kesish o'lchami) | 192/192 mos. Namunalarda `l=cl=dl`, `w=cw=dw`; fugovka o'lchami `jl/jw` ishlatilmaydi |
| `QTAINIZ`, `QTA` | **0** — miqdor bu yerda yozilmaydi; miqdor FDS joylashuvidan kelib chiqadi | |
| `SBN/SBS/SBE/SBO` | kromka (bordo) — **doim 0**, kromka ma'lumoti chiqmaydi | |
| `IN = 5132488`, `IS = 1242984`, `NUMPEZZIALTEZZAPALLET = 4203419` | doimiy «axlat» qiymatlar (ishga tushirilmagan o'zgaruvchi bo'lishi mumkin) — aynan shunday yozish | 192/192 bir xil |
| `RUOT = 0` | aylantirish taqiqi/ruxsati — doim 0 (amalda detal aylantiriladi, 3-bo'limga qarang) | |

Nom, kod, material, tekstura, kromka — **hech biri** yozilmaydi.

### 2.5 `ParametriFDS` — natija yig'indisi

```
[EndElementiFDT]
[StartMacro]
[EndMacro]
[StartParametriFDS]
TEMPODICALCOLO = 
TOTALESCHEMI = {kartalar soni}
AREATOTALEPANN = {round(cMaterialAmount × 1000)}
AREATOTALEELEM = {round(cPartAmount × 1000)}
AREATOTALEELEMREC = {round(cBusinessWasteAmount × 1000)}
[EndParametriFDS]
```
Maydonlar m² × 1000 (yarimdan yuqoriga yaxlitlash). Tekshiruv: 3151 → `30195/23571/2894` ↔ `cMaterialAmount=30.19499`, `cPartAmount=23.57068`, `cBusinessWasteAmount=2.8938`; 3153 → `25162` (`25.16249`; 5×5,0325=25,1625 dan hisoblansa 25163 chiqadi — shuning uchun loyihadagi saqlangan qiymat yoki float yig'indi ishlatilgan).

### 2.6 `PannelliFDS` — kartalar (har bir raskroy sxemasi uchun 1 blok)

```
[StartPannelliFDS]
[StartPannelloFDS{k}]
[StartDatiPannelloFDS{k}]
NUMELEMENTI = 0
RIPETIZIONI = {shu sxema bo'yicha kesiladigan listlar soni}
IDL = {list id}
DIMX = {karta X o'lchami ×1000}
DIMY = {karta Y o'lchami ×1000}
SBN = 0
SBS = 0
SBE = 0
SBO = 0
RUOT = -1
PRUOTATO = 0
TAGLIABILE = -1
RIFIUTATO = 0
AFFETTATO = 0
VERTOR = 0
ALTOBASSO = 0
DXSX = 0
TIPOTAGLIO = 0
AREAELEM = 0
AREAELEMRECUPER = 0
LUNGTAGLI = 0
NUMTAGLI = 0
MINIMOSFRIDOX = {cMinDimDetail ×1000}     (namunada 30000)
MINIMOSFRIDOY = {cMinDimDetail ×1000}
MINIMOMIGLIORESFRIDOX = 0
MINIMOMIGLIORESFRIDOY = 0
MAGAZZINO = 0
FOGLIPACCO = {RIPETIZIONI bilan bir xil}
RIFILOCODA = 0
RIFILO1 = 0
RIFILO2 = 0
RIFILO3 = {cTrimL ×1000}                   (namunada 2000)
RIFILO4 = {cTrimW ×1000}                   (namunada 2000)
RIFILO5 = 0
NUMCAV = 0
AREAELEMMAX = 0
TOTALEBORDI = 0
[EndDatiPannelloFDS{k}]
[StartElementiFDS]
  … joylashgan detallar (2.7) …
[EndElementiFDS]
[StartTagli]
[StartTaglio1]
XANGINF = {DIMX + kerf/2, ×1000}
YANGINF = 0
XANGSUP = {XANGINF bilan bir xil}
YANGSUP = {DIMY ×1000}
TIPOTG = 0
TGUTENTE = -1
PADRE = 0
FIGLIO = 0
FRATELLO = 0
PEZZOSTACCATO = 0
[EndTaglio1]
[EndTagli]
[StartTagli_Ed]
  … kesimlar (2.8) …
[EndTagli_Ed]
[StartSIDP_PezziProd]
[EndSIDP_PezziProd]
[EndPannelloFDS{k}]
```
va fayl oxiri:
```
[EndPannelliFDS]
[EndOttimizzazione1]
[EndOttimizzazioni]
```

`Taglio1` — har kartada bitta, varaqning o'ng chetidan tashqaridagi vertikal «foydalanuvchi kesimi» (`XANGINF = DIMX + kerf/2`: 1831500 yoki kerf 6 da 1833000; DIMX=2750 bo'lsa 2751500). Ma'lumot tashimaydi, lekin har doim bor.

### 2.7 `ElementiFDS` — kartadagi har bir joylashgan detal (bir nusxa = bitta yozuv)

```
[StartDatiElementoFDS{j}]
IDP = {detal id}
RUOTATO = 0
RUOTABILE = -1
XANGINF = {x0 ×1000}
YANGINF = {y0 ×1000}
XANGSUP = {x1 ×1000}
YANGSUP = {y1 ×1000}
ELSFRIDO = 0
RIFIUTATO = 0
SELEZIONATO = 0
MAGELEMENTO = 0
TIPOSELEZIONE = 5161934
[EndDatiElementoFDS{j}]
```
`RUOTATO` doim 0 (hatto detal aylantirilgan bo'lsa ham — orientatsiyani to'rtburchak o'lchamidan aniqlash kerak). `TIPOSELEZIONE = 5161934` — doimiy «axlat».

### 2.8 `Tagli_Ed` — kesimlar ketma-ketligi (asosiy ma'lumot)

```
[StartTg_Ed{m}]
XSTARTTG = 0
YSTARTTG = 0
XENDTG = 0
YENDTG = 0
QUOTATG = {kesib olinadigan bo'lak o'lchami ×1000}
TIPOTG = {daraja: 3,4,5,6}
LINEATG = 0
TGUTENTE = -1
PEZZISTACCATI = 1
QTARIP = {shu kesim necha marta takrorlanadi}
PADRE = 0
FIGLIO = 0
FRATELLO = 0
[EndTg_Ed{m}]
```

## 3. Kesish rejasi qanday kodlangan

### 3.1 Koordinatalar va karta orientatsiyasi
* Har bir karta o'z koordinata tizimida: `DIMX × DIMY`. Namunalarda ikki variant: `DIMX=1830, DIMY=2750` (18 karta) yoki `DIMX=2750, DIMY=1830` (12 karta). Optimallashtiruvchi har kartada qaysi yo'nalishni tanlaganini bildiradi.
* **Birinchi daraja kesimlari (`TIPOTG=3`) har doim Y o'qi bo'ylab qo'yiladi** (polosalar Y bo'yicha ketma-ket), keyingilari navbatma-navbat: 4 → X, 5 → Y, 6 → X.
* Detalning `XBA` (uzunlik `l`) o'qi list uzunligi (2750) bo'ylab yotadi deb hisoblanadi: `DIMX=2750` kartada `XBA` X bo'ylab, `DIMX=1830` kartada Y bo'ylab. Ammo optimallashtiruvchi detalni 90° aylantira oladi (kvadrat bo'lmagan detallardan 3153 da 19, 3156 da 15, 3161 da 6, 3157 da 4 — jami 44 joylashuv aylantirilgan, masalan 3161 da 300×346 detal 5 marta), bu holda ham `RUOTATO = 0` qoladi.

### 3.2 Kesim daraxti (`Tagli_Ed`)
`Tg_Ed` yozuvlari — gilyotin daraxtining **to'g'ridan-to'g'ri (pre-order) o'tishi**:
* `TIPOTG=3` — butun kartadan polosa kesish (1-daraja), `4` — polosadan bo'lak (2-daraja), `5` — 3-daraja, `6` — 4-daraja. 7/7 faylda 3..6 dan boshqa daraja yo'q (`LIVELLITAGLIO = 4`).
* Yozuv o'zidan keyin keladigan, darajasi kattaroq yozuvlarning «otasi». Yangi `TIPOTG ≤ joriy` bo'lsa — aka-uka (yuqoriga qaytish).
* `QUOTATG` — **bo'lak o'lchami** (pozitsiya emas).
* `QTARIP = n` — shu bo'lak ketma-ket n marta kesiladi; uning ostidagi butun pastki daraxt **har bir nusxaga** qo'llanadi (masalan 3161: `T4 300 ×3` → `T5 346` uchala 300 lik bo'lakdan 346 lik detal chiqaradi).
* Farzandi yo'q bo'lak = tayyor detal (uning o'lchamlari: `QUOTATG` × otasining ko'ndalang o'lchami). Farzandlardan keyin qolgan qism — chiqindi (alohida yozilmaydi).
* Kesimlar soni tekshiruvi: barglar soni (QTARIP bilan ko'paytirib) = `ElementiFDS` yozuvlari soni, 30/30 kartada mos.

### 3.3 Joylashuv geometriyasi (`ElementiFDS` qanday hisoblanadi)
Barcha 289 joylashuv quyidagi qoidaga 100 % mos (kerf = `SPESSORELAMA`, trim = `RIFILO3`):
* Daraja 3 (Y bo'ylab) va daraja 4 (X bo'ylab) — ota bo'lak boshidan **`trim + kerf`** (5 mm; kerf 6 da 8 mm) siljib boshlanadi.
* Daraja 5 (Y) va 6 (X) — ota bo'lak boshidan siljishsiz boshlanadi.
* Har bir keyingi aka-uka: `oldingi boshi + QUOTATG + kerf`.
* Barg to'rtburchagi: kesim o'qi bo'yicha `QUOTATG`, ko'ndalang — otasining to'liq o'lchami.
* Yozuvlar tartibi = barglarning pre-order tartibi (takrorlar ketma-ket).

Misol (3161, karta 1, `DIMX=1830`): `T3 2254` → polosa y=5…2259; uning ichida `T4 420` → x=5…425; `T5 498 ×2` → detal 7 ikki marta: (5,5)-(425,503) va (5,506)-(425,1004). Keyingi polosa `T3 352` y=2262 dan (2254+5+3), ichida detal 3 y=2262…2609 (347 mm; polosadagi 5 mm ortiqcha oxirida qoladi).

### 3.4 Listlar soni, «kitob», qoldiq
* `RIPETIZIONI = FOGLIPACCO` — shu sxema bilan kesiladigan listlar soni (namunalarda 1 yoki 2). Σ = `QTA` (FDT) = `cMaterialCount`.
* Paket balandligi: `ALTEZZAPACCO = 90000` doimiy (loyihadagi `swPackageHeight=40` bilan bog'liq emas).
* Ishbop qoldiq (business waste) faylda **alohida yozilmaydi**: faqat `AREATOTALEELEMREC` (m²×1000) — oxirgi polosadan keyingi bo'sh joy.
* Etiketka, nom, kromka — yo'q.

### 3.5 Miqdor tekshiruvi
Har bir detal uchun Σ(kartadagi joylashuvlar × `RIPETIZIONI`) = loyihadagi `count`: 7/7 faylda 0 xato (61, 70, 33, 73, 36, 20, 18 dona).

## 4. Loyiha → fayl moslashuvi (tekshirilgan misollar)

| Loyiha | Fayl | Misol |
|---|---|---|
| `sheet/@name` | `MATERIALE`, `CODMAT`, `CODMATERIALE`, `MATERIALE =  …` (2 bo'shliq) | `LDSP  PIKARD` (ikki bo'shliq saqlanadi) |
| `sheet/@t` ×1000 | `SPESSORE` (2 joyda) | 16 → `16000` |
| CS `tool.cutting/@swSawthick` ×1000 | `SPESSORELAMA`, `Taglio1` siljishi | 3159 da 6 → `6000`, `XANGINF=1833000`, birinchi detal `8000` dan |
| CS `@cTrimL/@cTrimW` ×1000 | `RIFILO3/RIFILO4` | 2 → `2000` |
| CS `@cMinDimDetail` ×1000 | `MINIMOSFRIDOX/Y` | 30 → `30000` |
| CS list-part id | `IDL`, `COD` | 3161 → `12`, 3155 → `53` |
| `@cMaterialCount` | `QTA`, `QTAINIZ` | 3156 → `8` (karta 1 `RIPETIZIONI=2` + 6×1) |
| detal `@id` | `IDP` | 3161 detal 7 (`01_006 Fasad`, 498×420, 2 dona) → `IDP=7`, `XBA=498000`, `YAL=420000`, `IE=7` |
| detal `@l/@w` | `XBA/YAL` | 3155 detal 41 (612×304) → `XBA=612000 YAL=304000`, FDS da (5,5)-(617,309) `DIMX=2750` kartada |
| detal `@count` | FDS joylashuvlar soni × `RIPETIZIONI` | 3156 detal 58 (100×565, 8 dona): 1-kartada 3 joylashuv × `RIPETIZIONI=2` = 6 + 2-kartada 2 = 8; 3155 detal 37 (777×270, 8 dona) — 1-kartada 5 + 2-kartada 3 = 8 |
| `@cBusinessWasteAmount` | `AREATOTALEELEMREC` | 3159: 4.36619 → `4366` |
| kromka, nom, kod, tekstura | **yozilmaydi** | |

## 5. Minimal qayta tiklangan misol

Sintetik buyurtma (anonim): list `LDSP OQ` 2750×1830×16, list id 50; kerf 3, trim 2; detallar: id 1 `1000×500` 2 dona, id 2 `600×400` 1 dona. Bitta karta, `DIMX=1830 DIMY=2750`: polosa 1000 → ikkita 500 lik detal + 400 lik bo'lakdan 600 lik detal.

Fayl `9001_mijoz_LDSP_OQ.fdt` = 2.1–2.2 shablonlar (`MATERIALE = LDSP OQ`, `SPESSORE = 16000`, `SPESSORELAMA = 3000`) + quyidagilar:

```
[StartPannelliFDT]
[StartDatiPannelloFDT1]
NUMEROPANNINIZ = 1
NUMEROPANN = 1
[StartDatiPannelloFDT1]
… (2.3 shablon: IDL = 50, XBA = 2750000, YAL = 1830000, QTAINIZ = 1, QTA = 1, COD = 50)
[EndDatiPannelloFDT1]
[EndPannelloFDT1]
[EndPannelliFDT]
[StartElementiFDT]
[StartDatiElementoFDT1]
… (2.4 shablon: IDP = 1, XBA = 1000000, YAL = 500000, IE = 1)
[EndDatiElementoFDT1]
[StartDatiElementoFDT2]
… (2.4 shablon: IDP = 2, XBA = 600000, YAL = 400000, IE = 2)
[EndDatiElementoFDT2]
[EndElementiFDT]
[StartMacro]
[EndMacro]
[StartParametriFDS]
TEMPODICALCOLO = 
TOTALESCHEMI = 1
AREATOTALEPANN = 5033
AREATOTALEELEM = 1240
AREATOTALEELEMREC = 3161
[EndParametriFDS]
[StartPannelliFDS]
[StartPannelloFDS1]
[StartDatiPannelloFDS1]
NUMELEMENTI = 0
RIPETIZIONI = 1
IDL = 50
DIMX = 1830000
DIMY = 2750000
… (2.6 shablon: FOGLIPACCO = 1, RIFILO3 = 2000, RIFILO4 = 2000)
[EndDatiPannelloFDS1]
[StartElementiFDS]
[StartDatiElementoFDS1]
IDP = 1
RUOTATO = 0
RUOTABILE = -1
XANGINF = 5000
YANGINF = 5000
XANGSUP = 505000
YANGSUP = 1005000
ELSFRIDO = 0
RIFIUTATO = 0
SELEZIONATO = 0
MAGELEMENTO = 0
TIPOSELEZIONE = 5161934
[EndDatiElementoFDS1]
[StartDatiElementoFDS2]
IDP = 1
… XANGINF = 508000, YANGINF = 5000, XANGSUP = 1008000, YANGSUP = 1005000
[EndDatiElementoFDS2]
[StartDatiElementoFDS3]
IDP = 2
… XANGINF = 1011000, YANGINF = 5000, XANGSUP = 1411000, YANGSUP = 605000
[EndDatiElementoFDS3]
[EndElementiFDS]
[StartTagli]
[StartTaglio1]
XANGINF = 1831500
YANGINF = 0
XANGSUP = 1831500
YANGSUP = 2750000
TIPOTG = 0
TGUTENTE = -1
PADRE = 0
FIGLIO = 0
FRATELLO = 0
PEZZOSTACCATO = 0
[EndTaglio1]
[EndTagli]
[StartTagli_Ed]
[StartTg_Ed1]            QUOTATG = 1000000  TIPOTG = 3  QTARIP = 1
[StartTg_Ed2]            QUOTATG = 500000   TIPOTG = 4  QTARIP = 2
[StartTg_Ed3]            QUOTATG = 400000   TIPOTG = 4  QTARIP = 1
[StartTg_Ed4]            QUOTATG = 600000   TIPOTG = 5  QTARIP = 1
   (har biri 2.8 shablonining to'liq 13 qatori bilan)
[EndTagli_Ed]
[StartSIDP_PezziProd]
[EndSIDP_PezziProd]
[EndPannelloFDS1]
[EndPannelliFDS]
[EndOttimizzazione1]
[EndOttimizzazioni]
```
(Shablonlar to'liq qo'llanganda fayl 441 qator; xuddi shu generator 7/7 haqiqiy namunani bayt-ma-bayt takrorladi.)

### Generator algoritmi (qisqa)
```
for part i in CS.parts (operation tartibida): ElementoFDT(i, IDP=id, XBA=l, YAL=w, IE=i)
for karta k:
    pos-qoidasi (3.3) bo'yicha barglarni pre-order chiqarish → ElementoFDS
    daraxtni pre-order: (TIPOTG=daraja, QUOTATG=o'lcham, QTARIP=n) → Tg_Ed
```

## 6. Noaniq maydonlar va savollar

1. **Faqat birinchi material** eksport qilinadi (3151 da 3 material, faylda 1). Stanokka har material uchun alohida `.fdt` kerakmi yoki postprotsessor ataylab faqat birinchisini chiqaradimi?
2. `IN=5132488`, `IS=1242984`, `NUMPEZZIALTEZZAPALLET=4203419`, `TIPOSELEZIONE=5161934` — barcha namunalarda bir xil «axlat» sonlar. Stanok ularni o'qiydimi? 0 yozsak bo'ladimi (xavfsizroq — aynan nusxa ko'chirish)?
3. `[StartDatiPannelloFDT1]` ikki marta va `[EndPannelloFDT1]` — Prisma importi shu xato tuzilmani kutadimi yoki to'g'ri (`[StartPannelloFDT1]`) teg ham qabul qilinadimi?
4. `RUOTATO = 0` hatto aylantirilgan detalda ham. Stanok/Prisma detal orientatsiyasini faqat `Tg_Ed` dan oladimi (biz shunday deb hisobladik)?
5. Kromka (`SBN/SBS/SBE/SBO`, `BN/BS/BE/BO`) va detal nomi/kodi (`COD`, `DESCRIZIONE`, `BARCODE`) bo'sh — etiketka bosish kerak bo'lsa, ularni to'ldirish kerakmi?
6. `ALTEZZAPACCO = 90000` (90 mm) doimiy; loyihadagi paket balandligi (40) bilan bog'lanmagan. Stanok sozlamasimi?
7. Fugovka: namunalarda `l = cl = dl` bo'lgani uchun `XBA` aynan qaysi o'lcham (`l`, `cl` yoki `dl`) ekanini ajratib bo'lmadi; `jl/jw` emasligi aniq. `cl ≠ l` bo'lgan namuna kerak.
8. Kasr o'lchamlar (masalan 346,5 mm) — `346500` bo'lishi kutiladi (mm×1000), namunada uchramadi.
9. `MINIMOSFRIDOX/Y = 30000` = `cMinDimDetail` (30) deb taxmin qilindi — barcha namunalarda 30 bo'lgani uchun tasdiqlanmagan.
