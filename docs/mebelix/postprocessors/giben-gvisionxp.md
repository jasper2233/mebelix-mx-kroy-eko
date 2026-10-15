# Giben GVisionXP — `.fdt` («soddalashtirilgan» FDT/FDS INI-matn) postprotsessori

Holat: **to'liq** (fayl tuzilmasi). 7/7 namuna loyiha + kesish daraxtidan **bayt-ma-bayt qayta yasaldi**. Ammo bu variantda ba'zi qiymatlar (qalinlik 18, ikkinchi list formati 2750×2100) loyihadan emas — shablondagi doimiylar; ular stanokda qanday ishlatilishi noma'lum (6-bo'lim).

Manba: `post prtsessorlar/PILNIY APPARAT/Giben GVisionXP/*.fdt` (7 fayl: 3151, 3153, 3155, 3156, 3157, 3159, 3161).
Mos loyiha: `giblab project/3 Eldor/<NNNN> <mijoz>/<NNNN>_<mijoz>.project` (pastki chiziqli variant).

Bu format **Giben G57** (`giben-g57.md`) bilan bir xil sintaksisli (`[StartXxx]/[EndXxx]`, `KALIT = QIYMAT`, mm×1000, LF), lekin **detallar ro'yxati va joylashuv yo'q** — faqat kartalar va kesimlar ketma-ketligi (`Tagli_Ed`) bor. Quyida faqat G57 dan farqlar va to'liq tuzilma berilgan.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma / nomlash | `.fdt`, `<loyiha nomi>_<material, bo'shliqlar→_>.fdt` (G57 bilan aynan bir xil nom), masalan `3161_mijoz_LDSP_PIKARD.fdt` |
| Soni | buyurtmaga 1 fayl — faqat **birinchi CS operatsiyasi** (birinchi material) |
| Kodlash | ASCII; qator oxiri `LF`; fayl `\n` bilan tugaydi |
| Birlik | mm × 1000, butun son; mantiqiy `-1/0` |
| Hajm | G57 dan ~2,5 marta kichik (3161: 673 qator, G57 da 1443) |

## 2. Tuzilma (G57 ga nisbatan farqlar)

Bo'limlar tartibi G57 bilan bir xil. Farqlar (7/7 faylda bir xil):

| Joy | G57 | GVisionXP |
|---|---|---|
| `[StartOtt1]` `MATERIALE` | material nomi | **bo'sh** (`MATERIALE = `) |
| `[StartOtt1]` va `ParametriPannelli` `SPESSORE` | haqiqiy qalinlik (16000) | **doim `18000`** (loyihada 16 mm bo'lsa ham) |
| `CODMAT`, `CODMATERIALE` | material nomi | material nomi (o'zgarmagan) |
| `ParametriPannelli` `MATERIALE` | `␠` + nom | **bo'sh** |
| `VELMATERIALE` | 150000 | **20000** |
| `DESCRPRODUZIONE` | `MATERIALE|COLORE|1` | **bo'sh** |
| `TIPOSTRISCE`, `LIVELLITAGLIO`, `XORDINADIR` | 1, 4, 1 | **0, 0, 0** |
| `SPESSORELAMA` | arra qalinligi | **qator umuman yo'q** (kerf faylda yozilmaydi!) |
| `PannelliFDT` | 1 ta list (loyihadagi list id, `QTA` = jami listlar) | **2 ta doimiy list**: `IDL=1` 2750×1830 va `IDL=3` 2750×2100, ikkalasida `QTAINIZ=QTA=1`, `NUMEROPANNINIZ=NUMEROPANN=2` |
| `ElementiFDT` | detallar ro'yxati | **bo'sh** (`[StartElementiFDT]` darhol `[EndElementiFDT]`) |
| `AREATOTALEPANN/ELEM/ELEMREC` | m²×1000 | doim `10807500000 / 0 / 0` (10807500000 = (2750·1830 + 2750·2100) mm² × 1000 — ikki doimiy listning yig'indisi) |
| karta `IDL` | loyiha list id | **doim `1`** |
| `ElementiFDS` | joylashuvlar | **bo'sh** |
| `Tagli` (`Taglio1`) | 1 ta yozuv | **bo'sh** (`[StartTagli]` `[EndTagli]`) |
| `Tagli_Ed` | kesimlar | **G57 bilan aynan bir xil** (7/7 faylda har karta uchun ketma-ketlik bir xil) |
| fayl oxiri | `[EndPannelloFDS{n}]` → `[EndPannelliFDS]` | oxirgi kartadan keyin **ortiqcha `[StartTagli_Ed]`** qatori, keyin `[EndPannelliFDS]` (yopilmagan teg — aynan shunday yozish kerak) |

`PannelliFDT` bloki (aynan):
```
[StartPannelliFDT]
[StartDatiPannelloFDT1]
NUMEROPANNINIZ = 2
NUMEROPANN = 2
[StartDatiPannelloFDT1]
NUOVO = -1
SFRIDO = 0
FAMIGLIA = 
RIGA = -1
IDL = 1
DES = 
BARCODE = 
XBA = 2750000
YAL = 1830000
QTAINIZ = 1
QTA = 1
COS = 0
PRT = 0
COD = 1
MINTRONC = 0
… (G57 2.3 dagi qolgan doimiy qatorlar)
[EndDatiPannelloFDT1]
[EndPannelloFDT1]
[StartDatiPannelloFDT2]
NUMEROPANNINIZ = 2
NUMEROPANN = 2
[StartDatiPannelloFDT2]
… IDL = 3, XBA = 2750000, YAL = 2100000, QTAINIZ = 1, QTA = 1, COD = 3 …
[EndDatiPannelloFDT2]
[EndPannelloFDT2]
[EndPannelliFDT]
[StartElementiFDT]
[EndElementiFDT]
```

Har bir karta (`PannelloFDS{k}`):
```
[StartPannelloFDS{k}]
[StartDatiPannelloFDS{k}]
NUMELEMENTI = 0
RIPETIZIONI = {listlar soni}
IDL = 1
DIMX = {×1000}
DIMY = {×1000}
… (G57 2.6 dagi qatorlar; MINIMOSFRIDOX/Y = 30000, FOGLIPACCO = RIPETIZIONI, RIFILO3 = RIFILO4 = 2000)
[EndDatiPannelloFDS{k}]
[StartElementiFDS]
[EndElementiFDS]
[StartTagli]
[EndTagli]
[StartTagli_Ed]
[StartTg_Ed1] … (G57 2.8 shabloni: QUOTATG, TIPOTG, QTARIP)
[EndTagli_Ed]
[StartSIDP_PezziProd]
[EndSIDP_PezziProd]
[EndPannelloFDS{k}]
```
Oxiri:
```
[EndPannelloFDS{n}]
[StartTagli_Ed]
[EndPannelliFDS]
[EndOttimizzazione1]
[EndOttimizzazioni]
```

## 3. Kesish rejasi

* Kesish rejasi **faqat** `Tagli_Ed` daraxtida (G57 3.2 bilan bir xil semantika: `TIPOTG` 3→Y, 4→X, 5→Y, 6→X; `QUOTATG` — bo'lak o'lchami; `QTARIP` — takror, pastki daraxt har nusxaga).
* Karta orientatsiyasi `DIMX/DIMY` (1830/2750 yoki 2750/1830) va listlar soni `RIPETIZIONI = FOGLIPACCO` — G57 dagidek.
* Detal identifikatori, o'lchami, soni, joylashuv koordinatalari **yo'q**: stanok faqat «qayerdan qancha kesish» ni biladi. Qaysi bo'lak qaysi detal ekanini bu fayldan aniqlab bo'lmaydi.
* Arra qalinligi yozilmaydi — kesim o'lchamlari (`QUOTATG`) loyihadagi kerf bilan hisoblangan (3159 da kerf 6, faylda buni ko'rsatuvchi hech narsa yo'q, faqat `QUOTATG` qiymatlari kerf 6 bilan mos).
* Trim: `RIFILO3/RIFILO4 = cTrimL/cTrimW ×1000` (2000).

## 4. Loyiha → fayl moslashuvi (tekshirilgan)

| Loyiha | Fayl | Misol |
|---|---|---|
| `sheet/@name` | `CODMAT`, `CODMATERIALE` | 3161: `LDSP  PIKARD` (2 bo'shliq saqlanadi) |
| kartalar soni | `TOTALESCHEMI` | 3151: 6, 3156: 7 |
| sxema bo'yicha listlar | `RIPETIZIONI`, `FOGLIPACCO` | 3156 1-karta: 2; 3157 1- va 2-karta: 2 |
| CS kesim daraxti | `Tagli_Ed` | 3161: `T3 2254 → T4 420 → T5 498 ×2 …` — G57 bilan bir xil 28 yozuv |
| `@cTrimL/W` | `RIFILO3/4` | 2 → 2000 |
| `@cMinDimDetail` | `MINIMOSFRIDOX/Y` | 30 → 30000 |
| list o'lchami, qalinlik, kerf, detallar | **yozilmaydi** (doimiylar) | |

Tekshiruv: G57 generatori `gvision=True` rejimida 7/7 faylni bayt-ma-bayt takrorladi; 7/7 faylda kartalar soni, `DIMX/DIMY`, `RIPETIZIONI` va `Tagli_Ed` ketma-ketligi G57 fayli bilan aynan bir xil.

## 5. Minimal misol

Sintetik buyurtma (G57 hujjatidagi bilan bir xil: list `LDSP OQ`, detallar 1000×500 ×2 va 600×400 ×1, bitta karta `DIMX=1830`):

```
[StartGenerale]
VERSIONE = 6
[EndGenerale]
[StartProduzione]
NUMOTTIMIZZAZIONI = 1
[StartOtt1]
MATERIALE = 
SPESSORE = 18000
SCARICATA = 0
RIGA = 23
APPLICAZIONE = 
VERSIONEOTT = 
COLORE = Colore
CODTIPO = 
DESCR = 
CODMAT = LDSP OQ
CODCOL = COL
PEZZINONPOS = 0
TAGLIABILE = -1
[EndOtt1]
[EndProduzione]
… Parametri (G57 2.2, farqlar jadvali bo'yicha; SPESSORELAMA qatori yo'q) …
… PannelliFDT (2 doimiy list, yuqoridagi blok) …
[StartMacro]
[EndMacro]
[StartParametriFDS]
TEMPODICALCOLO = 
TOTALESCHEMI = 1
AREATOTALEPANN = 10807500000
AREATOTALEELEM = 0
AREATOTALEELEMREC = 0
[EndParametriFDS]
[StartPannelliFDS]
[StartPannelloFDS1]
[StartDatiPannelloFDS1]
NUMELEMENTI = 0
RIPETIZIONI = 1
IDL = 1
DIMX = 1830000
DIMY = 2750000
… (doimiy qatorlar, FOGLIPACCO = 1) …
[EndDatiPannelloFDS1]
[StartElementiFDS]
[EndElementiFDS]
[StartTagli]
[EndTagli]
[StartTagli_Ed]
[StartTg_Ed1] … QUOTATG = 1000000, TIPOTG = 3, QTARIP = 1 … [EndTg_Ed1]
[StartTg_Ed2] … QUOTATG = 500000,  TIPOTG = 4, QTARIP = 2 … [EndTg_Ed2]
[StartTg_Ed3] … QUOTATG = 400000,  TIPOTG = 4, QTARIP = 1 … [EndTg_Ed3]
[StartTg_Ed4] … QUOTATG = 600000,  TIPOTG = 5, QTARIP = 1 … [EndTg_Ed4]
[EndTagli_Ed]
[StartSIDP_PezziProd]
[EndSIDP_PezziProd]
[EndPannelloFDS1]
[StartTagli_Ed]
[EndPannelliFDS]
[EndOttimizzazione1]
[EndOttimizzazioni]
```
(To'liq shablon bilan 313 qator.)

## 6. Noaniq joylar va savollar

1. `SPESSORE = 18000` (18 mm) — barcha namunalarda, material 16 mm bo'lsa ham. Bu stanok sozlamasimi yoki postprotsessor xatosi? Bizning generator ham 18000 yozsinmi yoki haqiqiy qalinlikni?
2. Ikkita doimiy list (`IDL=1` 2750×1830, `IDL=3` 2750×2100) — bu stanokdagi «standart formatlar» ro'yxatimi? Agar list boshqa o'lchamda (masalan 2800×2070) bo'lsa, `IDL=1` o'lchami o'zgaradimi? (Namunalarda hamma list 2750×1830 — aniqlab bo'lmadi.)
3. Arra qalinligi (`SPESSORELAMA`) yozilmaydi — stanok o'z sozlamasidan oladimi? Kerf 6 mm bilan kesilgan 3159 fayli stanokda 3 mm bilan ishlansa o'lchamlar siljiydi.
4. Detallar (`ElementiFDT/FDS`) yo'qligi sababli etiketka/detal identifikatsiyasi stanokda bo'lmaydi — bu ataylabmi (GVision faqat kesish rejasini oladi)?
5. Oxiridagi yopilmagan `[StartTagli_Ed]` — stanok dasturi buni talab qiladimi yoki shunchaki e'tiborsiz qoldiradimi (biz aynan nusxa qilamiz)?
6. `VELMATERIALE = 20000`, `TIPOSTRISCE/LIVELLITAGLIO/XORDINADIR = 0` — sozlamalar; o'zgartirish kerak bo'ladimi?
7. Faqat birinchi material eksport qilinadi (G57 kabi) — boshqa materiallar uchun alohida fayl kerakmi?
