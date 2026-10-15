# SCM MaestroCut — postprotsessor formati (namunalardan teskari hujjatlash)

> Manba: `post prtsessorlar/PILNIY APPARAT/SCM MaestroCut/*.zip` (7 ta buyurtma: 3151, 3153, 3155, 3156, 3157, 3159, 3161),
> mos `giblab project/3 Eldor/<raqam> <mijoz>/<raqam>_<mijoz>.project` fayllari bilan solishtirildi.
> Mijoz ismlari hujjatda «mijoz» bilan almashtirilgan. Dastur binarlari o'qilmagan — faqat chiqish fayllari.
> Shu buyurtmalar uchun **SCM WinCut** ham bor ([scm-wincut.md](scm-wincut.md)) — kesish ketma-ketligi 30/30 faylda **aynan bir xil**.

**Tushunish darajasi: to'liq (kesish sxemasi va etiketka maydonlari), qisman — faqat `<GibLabLabel>` ichidagi blob.**

---

## 1. Qanday fayllar chiqadi

| Xususiyat | Qiymat |
|---|---|
| Konteyner | Har bir *buyurtma × material (list)* uchun bitta `.zip` |
| Zip nomi | `<loyiha nomi>_<material nomi>.zip`, material nomidagi bo'shliqlar `_` ga almashadi, ketma-ket bo'shliqlar bittaga qisqaradi (`LDSP  PIKARD` → `LDSP_PIKARD`) |
| Zip ichi | Papka **yo'q**, fayllar ildizda: `<asos>.001.XPrg`, `<asos>.002.XPrg`, … va bitta `<asos>.XMix` (`<asos>` = zip nomi `.zip` siz) |
| Har bir `.NNN.XPrg` | **Bitta karta (pattern)** — bitta xil kesish sxemasi; shu sxema bo'yicha bir nechta list kesilishi mumkin (`Rep`) |
| `.XMix` | Partiya ro'yxati: qaysi XPrg necha marta (`Rep`) va qaysi list bilan |
| Raqamlash | `001` dan boshlab 3 xonali, uzluksiz |
| Kodlash | Faqat ASCII uchradi (barcha 37 fayl). XML deklaratsiyasi (`<?xml ...?>`) **yo'q**. Kirill/maxsus belgilar uchun kodlash noma'lum (savol Q4) |
| Qator oxiri | `.XPrg` — CRLF (`\r\n`), oxirgi `</SchemaDoc>` dan keyin yangi qator yo'q. `.XMix` — bitta qator, CRLF yo'q |
| O'nlik ajratgich | Nuqta `.` |
| Zip | Deflate (method 8), flag 0x808 (UTF-8 nom + data descriptor), barcha yozuvlar bir xil vaqt belgisi |

Namunalar bo'yicha statistika: 7 zip, 30 XPrg, 7 XMix; 223 `Etichetta` (218 detal + 5 qoldiq), 294 detal-joylashuv.
Kesish yozuvlari: `P`=30, `RY`=30, `Y`=89, `RX`=89, `X`=182, `U`=136, `V`=30, `F`=232.

---

## 2. `.XMix` tuzilishi (partiya fayli)

Bir qatorli XML (atributlar alifbo tartibida):

```xml
<xMix><Header Date="26.09.2026" Descrizione="<asos>" Import="From GibLab"/><Materials><Material Codice="110052" Larghezza="1830" Lunghezza="2750" Quantita="1" Spessore="16" Tipologia=""/>...</Materials><RigheMix><RigaMix CambioMateriale="0" File="C:\MaestroCut\Client\xMix\<asos>.001.XPrg" Pacco="2" Rep="1"/>...</RigheMix></xMix>
```

| Element/atribut | Ma'no | Manba | Kuzatilgan |
|---|---|---|---|
| `Header@Date` | Eksport sanasi `dd.MM.yyyy` | joriy sana | 26.09.2026 |
| `Header@Descrizione` | Zip/fayl asosiy nomi | `<loyiha>_<material>` | — |
| `Header@Import` | Doimiy | — | `From GibLab` |
| `Material` | **Har bir XPrg uchun bitta** (tartib RigaMix bilan bir xil) | | |
| `Material@Codice` | List (sheet good) kodi; kod bo'sh bo'lsa atribut **umuman yozilmaydi** | `good[typeId=sheet]@code` | faqat 3161 da `110052` |
| `Material@Larghezza / Lunghezza` | Listning tabiiy eni/bo'yi (karta orientatsiyasidan qat'i nazar doim 1830/2750) | `sheet@w`, `sheet@l` | 1830 / 2750 |
| `Material@Quantita` | Shu karta bo'yicha listlar soni (= `Rep`) | | 1 yoki 2 |
| `Material@Spessore` | Qalinlik | `sheet@t` | 16 |
| `Material@Tipologia` | Doim bo'sh | — | `""` |
| `RigaMix@CambioMateriale` | Doimiy | — | 0 |
| `RigaMix@File` | Mashinadagi absolyut yo'l, prefiks doimiy `C:\MaestroCut\Client\xMix\` | sozlama | — |
| `RigaMix@Pacco` | Paketdagi maks. listlar (= XPrg `NumFogliPacco`) | `floor(swPackageHeight / t)` = floor(40/16) | 2 |
| `RigaMix@Rep` | Shu karta bo'yicha kesiladigan listlar soni | optimizator | 1, 2 |

Tekshiruv: Σ`Rep` = `CS@cMaterialCount` barcha 7 buyurtmada (6, 5, 3, 8, 7, 3, 1).

---

## 3. `.XPrg` tuzilishi (bitta karta)

```
<SchemaDoc><Header .../>
<Material Tipologia="1" Codice="..."/>
<Pattern>
<Cut .../>          × n
</Pattern>
<DatiEtichetta>
<Etichetta .../>    × m
</DatiEtichetta>
<GibLabLabel>
<part id=".." data=".."/>   × m
</GibLabLabel>
</SchemaDoc>
```
(har bir satr CRLF bilan ajratiladi; birinchi satrda `<SchemaDoc>` va `<Header>` birga.)

### 3.1 `Header` (atributlar tartibi aynan shunday)

| Atribut | Ma'no | Manba / qoida | Kuzatilgan |
|---|---|---|---|
| `GibLabID` | 32 hex belgili tasodifiy ID (UUID tirelarsiz), har bir faylda yangi | generatsiya | — |
| `TipoCave` | doimiy | sozlama | 1 |
| `NumFogliPacco` | paketdagi maks. listlar | floor(`swPackageHeight`/t) | 2 |
| `Descrizione` | List nomi (aynan, ikki bo'shliq saqlanadi) | `sheet@name` | `LDSP  PIKARD` |
| `Spessore` | Qalinlik, mm | `sheet@t` | 16 |
| `Date` | Eksport sanasi `dd/MM/yyyy` | joriy sana | 26/09/2026 |
| `Lunghezza` | **Y-kesimlar chizig'i bo'ylab o'lcham** (= `P` Dim) — karta orientatsiyasiga bog'liq | 2750 yoki 1830 | ikkalasi ham uchraydi |
| `Larghezza` | Y-polosalar (strip) qalinligi o'lchanadigan o'q | qolgan tomoni | 1830 yoki 2750 |
| `SpessoreLama` | Arra qalinligi (kerf), mm | `tool.cutting@swSawthick` | 3 (3159 da **6**) |
| `Swap` | doimiy | — | 0 |
| `Inforesto` | qoldiq ma'lumoti yoqilgan | sozlama | 1 |

### 3.2 `Material`
`<Material Tipologia="1" Codice="<sheet code yoki bo'sh>"/>` — `Tipologia` doim `1`, `Codice` atributi har doim bor (bo'sh bo'lishi mumkin).

### 3.3 `Cut` — kesish yozuvlari

`<Cut ID="k" T="<tur>" Dim="<mm>" Rip="<takror>" EtiID="<etiketkalar>"/>`

* `ID` — 1 dan uzluksiz tartib raqami.
* `Dim` — butun mm (namunalarda kasr yo'q; `F` uchun `0.00`). Kasr o'lcham formati noma'lum (Q2).
* `Rip` — shu o'lchamdagi bir xil kesimlar soni (ketma-ket bir xil polosalar). `F` da `0`. Kuzatilgan 1…7.
* `EtiID` — shu kesimdan chiqadigan *tayyor* bo'laklar etiketkalari: har bir bo'lak `(Id)`; paket (`Rep`=2) bo'lsa har bir qatlam uchun vergul bilan: `(4,4)`. Rip hisobga olinadi: `X Dim=300 Rip=3` ostidagi `U 346` → `(9)(9)(9)`.

| `T` | Ma'no | Daraja |
|---|---|---|
| `P` | Karta boshi (panel). `Dim` = `Header@Lunghezza`. Har faylda birinchi va yagona | — |
| `RY` | 1-daraja chekka kesish (trim). Har faylda bitta, `P` dan keyin | 1 |
| `Y` | 1-daraja polosa (strip) eni; o'lchami `Larghezza` o'qi bo'ylab | 1 |
| `RX` | 2-daraja trim; **har bir `Y` dan keyin** bitta | 2 |
| `X` | 2-daraja: Y-polosa ichidagi bo'lak, `Lunghezza` o'qi bo'ylab | 2 |
| `U` | 3-daraja: X-bo'lak ichida, `Larghezza` o'qi bo'ylab | 3 |
| `V` | 4-daraja: U-bo'lak ichida, `Lunghezza` o'qi bo'ylab | 4 |
| `F` | Tugallash belgisi (pastga qarang). `Dim="0.00" Rip="0" EtiID=""` | — |

`RU`/`RV`, `W`/`Z` darajalari namunalarda uchramadi (`swMaxturns`=4 → maks. 4 daraja).

**Ierarxiya** — ketma-ketlik daraxtni oldindan (pre-order) aylanib yozilgan: har bir `Y` dan keyin uning bolalari (`RX`, `X`…), har bir `X` dan keyin uning `U`lari, har `U` dan keyin uning `V`lari. Bolasi yo'q kesim — tayyor detal (yoki chiqindi, agar `EtiID` bo'sh bo'lsa; namunalarda bolasiz va `EtiID`siz kesim yo'q).

**`F` qoidasi (30/30 faylda qayta generatsiya bilan tasdiqlangan):**
bolasiz (tayyor) kesimdan keyin `F` yoziladi, agar u `Y`/`X`/`U` darajasida bo'lsa — **har biridan keyin**; `V` darajasida esa faqat ota-`U`ning **oxirgi** `V` sidan keyin bitta `F` (`U1974 V496# V496# F`).

### 3.4 Geometriya, kerf va trim

* Har bir polosa/bo'lak o'z darajasida `Dim + SpessoreLama` joy egallaydi (Rip marta). 294 bo'lakning hech biri ota o'lchamidan oshmadi.
* Trim kesimi `Dim` = `cTrim + kerf`: kerf 3 → `RY=RX=5`; 3159 (kerf 6) → `8`. Ya'ni trim (`cTrimL=cTrimW=2`) ga arra qalinligi qo'shiladi (`swTrimIncludeSaw=false`). `cTrimL` va `cTrimW` qaysi biri `RY`/`RX` ga ketishini namunalar ajratmaydi (ikkalasi 2) — Q3.
* Orientatsiya: tayyor bo'lakning listning uzun o'qi (2750) bo'ylab o'lchami = detal `l` (tekstura). `txt=true` detallar **hech qachon** burilmagan; burilgan joylashuvlar faqat `txt=false` detallarda uchraydi.
* Oxirgi `Y` polosadan keyingi qoldiq yozilmaydi (implitsit chiqindi), agar u qoldiq-etiketka bo'lmasa.

### 3.5 Qoldiq (remnant, `Resto="1"`)

Ishbop qoldiq **oxirgi `Y` kesimiga** etiketka sifatida biriktiriladi (`<Cut T="Y" ... EtiID="(5)"/>`) — ma'nosi «shu polosadan keyin qolgan list qismi — qoldiq». Uning o'lchami trim bilan kesilgan holda:
`Uzun tomoni = 2750 − 2×(trim+kerf)`, `Qisqa = Larghezza − RY − Σ(Y+kerf)×Rip − (trim+kerf)`.
Masalan 3157.005: `1830 − 5 − (138+3) − (65+3) − (65+3) − 5 = 1543`, `2750 − 5 − 5 = 2740` → etiketka `2740×1543` ✓. 5 ta qoldiqning hammasi formula bilan mos (2734×1597, 2740×1100, 2740×888, 2740×1543, 1590×1820).
Qoldiq etiketkasida `Lunghezza` = listning uzun o'qi bo'ylab o'lcham. Barcha qoldiqlar ≥1000×≥500 (`cMinDimRegWaste1/2`).

### 3.6 `Etichetta` — etiketka/detal ro'yxati

Har bir faylda shu kartada uchraydigan **har bir alohida detal (project `part` yozuvi) uchun bitta** + qoldiqlar. Tartib: detallar `Campo40` (CS operatsiyadagi o'rni) bo'yicha o'sish tartibida, qoldiqlar oxirida (30/30). `Id` — fayl ichida 1 dan.

Atributlar tartibi: `Id Resto Codice Lunghezza Larghezza Richiesti CodiceBordo1..4 Job Campo1..Campo64`.

| Maydon | Ma'no | Project manbasi (tasdiqlangan) |
|---|---|---|
| `Id` | Fayl ichidagi etiketka raqami (EtiID shunga ishora qiladi) | — |
| `Resto` | 0 = detal, 1 = qoldiq | — |
| `Codice`, `Job`, `Campo1` | Buyurtma nomi «`<raqam> <mijoz>`» | `good[product]@product.order` |
| `Lunghezza`, `Larghezza` | Kesish o'lchami, 2 kasr (`1900.00`) | `part@cl`, `part@cw` (218/218; namunalarda `l=cl`) |
| `Richiesti` | Detalning **loyihadagi umumiy soni** (shu kartadagi emas) | `part@count` |
| `CodiceBordo1..4` | Kromka belgisi: 1=yuqori(`elt`), 2=pastki(`elb`), 3=chap(`ell`), 4=o'ng(`elr`); qiymat = EL operatsiyaning `elSymbol` (`A`, `B`), yo'q bo'lsa bo'sh | 218/218 mos |
| `Campo2` | doim bo'sh | — |
| `Campo3` | Project **part id** | `part@id` (qoldiqda: max part id + 1 kabi yangi id) |
| `Campo4/5` | = Lunghezza/Larghezza (`.00`) | `cl/cw` |
| `Campo6` | Qalinlik `16.00` | `sheet@t` |
| `Campo7` | List kodi | `sheet@code` |
| `Campo8` | Tekstura belgisi 1/0 (217/218 da `part@txt`ga mos; 1 istisno — Q6) | `part@txt` |
| `Campo9` | Soni (= Richiesti; qoldiqda 0) | `part@count` |
| `Campo10`, `Campo37` | Detal nomi | `part@name` |
| `Campo11..14` | Kromka material nomi (t,b,l,r) | `part@el?Mat` |
| `Campo15..18` | Kromka material kodi (t,b,l,r) | band `good@code` |
| `Campo19` | Qoldiq bayrog'i 0/1 | — |
| `Campo20` | doimiy `sheet` | — |
| `Campo21..25, 27, 34, 35, 38, 63` | doim bo'sh | — |
| `Campo26` | Loyiha sanasi `dd.MM.yyyy` | `project@date` (ms epoch) |
| `Campo28` | List nomi | `sheet@name` |
| `Campo29` | List kodi | `sheet@code` |
| `Campo30` | Mahsulot tartib raqami (`1`) | product index |
| `Campo31` | Mahsulot nomi (`01 shkaf`) | `good[product]@name` |
| `Campo32` | Mahsulot kodi (`316101`) | `good[product]@code` |
| `Campo33` | Mahsulot soni | `good[product]@count` |
| `Campo36` | Detal kodi (`01_005`) | `part@code` |
| `Campo39` | Detalning loyiha/mahsulot ichidagi umumiy tartib raqami (`index`) | taxminan — Q7 |
| `Campo40` | Detalning CS operatsiya ro'yxatidagi o'rni (1-dan) | `operation[CS]/part` tartibi (tasdiqlangan) |
| `Campo41/42` | Uzunlik/en, 1 kasr (`2360.0`) — detal (gotoviy) o'lchami | `part@l/w` (namunalarda = cl/cw) |
| `Campo43/44` | Kesish o'lchami, 1 kasr | `part@cl/cw` (taxmin; namunalarda farq yo'q — Q1) |
| `Campo45` | Qalinlik `16.0` | |
| `Campo46` | Qoldiq bayrog'i `true/false` | |
| `Campo47/48/49` | count / totalCount / usedCount (qoldiqda 1/1/0) | `part@count`, `@usedCount` |
| `Campo50,52,54,56` | Kromka nomi (t,b,l,r) | |
| `Campo51,53,55,57` | Kromka qalinligi `1.0` / `0.0` | band `good@t` |
| `Campo58/59/60` | Boolean — ehtimol groove / drill / mill (blobdagi kalitlar tartibi); `Campo59=true` deyarli har doim XNC bo'lganda | Q5 |
| `Campo61` | 1-tomon XNC dastur kodi (`315101_01_032`) | `operation[XNC]@code` |
| `Campo62` | 2-tomon XNC kodi (`..._2`) | |
| `Campo64` | `<Header GibLabID>#<Id>` | |

### 3.7 `<GibLabLabel>` — etiketka blobi

`<part id="<Etichetta Id>" data="<base64>"/>` — har bir `Etichetta` uchun bitta. `data` = **base64(zlib(...))** (`eJ` bilan boshlanadi). Ichida GibLab'ning tipli kalit-qiymat xaritasi: yozuv = `[tur:1][flag:1][u32 kalit uzunligi][kalit]`, so'ng `[mavjud:1][qiymat]`; turlar: 0=satr (u32 uzunlik + baytlar), 1=int32, 2=double, 3=bool; lotin harflari «overlong UTF‑8» (`0xC1 0x80|..`) bilan yozilgan, raqam/punktuatsiya oddiy ASCII. Kalitlar: `project.name/date/uuid/crc16/crc32`, `product.*`, `operation.*`, `part.id/code`, `name`, `length/width`, `detail.*`, `afterPreMilling.*`, `cutting.*`, `allowanceT/B/L/R`, `thick`, `txt`, `count`, kromka `et?/eb?/el?/er?` (c,n,s,t,w,j), paz `gr*`, `XNC1..5` … va oxirida detal chizmasining **SVG** rasmi (Batik generatori).
Bu GibLab etiketka moduli uchun; MaestroCut kesish uchun ishlatadimi — noma'lum (Q8). Aynan shu blob WinCut `[Dati]` ning oxirgi maydonida ham takrorlanadi (223/223 bayt-bayt bir xil).

---

## 4. Kesish rejasi qanday kodlanadi (xulosa)

1. **List/karta** → bitta `.XPrg`; necha list kesilishi — `XMix` dagi `Rep`/`Quantita`; paket balandligi — `Pacco`/`NumFogliPacco`.
2. **Orientatsiya** — `Header@Lunghezza` (= `P`): Y-kesim chizig'i uzunligi. 2750 bo'lsa polosalar 1830 bo'ylab o'lchanadi, 1830 bo'lsa 2750 bo'ylab. Optimizator har karta uchun tanlaydi (30 tadan 12 tasi `Lunghezza=2750`).
3. **Daraja zanjiri** `Y → X → U → V`, toq darajalar (`Y`,`U`) `Larghezza` o'qida, juft (`X`,`V`) `Lunghezza` o'qida.
4. **Trim** — `RY` (bir marta), `RX` (har polosada).
5. **Takror** — `Rip`; **paket** — `EtiID` ichida vergul bilan qatlamlar.
6. **Qoldiq** — oxirgi `Y` ga biriktirilgan `Resto=1` etiketka.
7. **Soni tekshiruvi** — barcha buyurtmalarda Σ(EtiID ichidagi detal id lari) = Σ`part@count` CS operatsiyasi bo'yicha: 61, 70, 33, 73, 36, 20, 18 (= `cPartCount`), xatosiz.

---

## 5. Project → fayl moslik misollari (3 tadan ortiq tekshirilgan)

| Buyurtma | Project | Fayldagi yozuv |
|---|---|---|
| 3161 (1 list, kerf 3) | `part id=7 "01_006 Fasad" l=498 w=420 count=2 txt=true`, kromka t,b,l,r=@op1 (`elSymbol=A`) | `Etichetta Id=7 Lunghezza=498.00 Larghezza=420.00 Richiesti=2 CodiceBordo1..4=A,A,A,A`; kesim `X 420` ichida `U Dim=498 Rip=2 EtiID=(7)(7)` |
| 3161 | `part id=1 "01_001 bok" 1900×347`, kromka b,l,r | `CodiceBordo1="" 2..4=A`; `X 347 → U 1900 (1)`. Header `Lunghezza=1830 Larghezza=2750`, Y-polosalar 2254/352/100: 5+(2254+3)+(352+3)+(100+3)=2720 ≤ 2750 |
| 3159 (kerf 6) | `tool swSawthick=6`, `cTrimW=2` | `SpessoreLama="6"`, `RY Dim=8`, `RX Dim=8`; qoldiq 2734×1597 = (2750−8−8)×(1830−8−211−6−8) |
| 3157 (Rep=2) | 7 list, CS `cMaterialCount=7`; `part 01_001 bok 2618×597` ikkita yozuv (id 12, 13), count 1+1 | `.001.XPrg`: `X 597 EtiID=(2,2)`, `(1,1)`; XMix `Quantita=2 Rep=2`; WinCut `AltPacco=32` |
| 3151 | `01_053 rover 40×1398 count=12` | `.006`: `Y 40 Rip=7 → X 1398 (4)×7` va boshqa kartalarda qolgan 5 ta; jami 12 ✓ |
| 3153 | `txt=false` `01_031 bok 400×148` | 148 uzun o'q bo'ylab — burilgan (ruxsat, chunki tekstura yo'q) |

---

## 6. Minimal namunaviy fayl (anonim, qo'lda tuzilgan, qoidalarga mos)

List 2750×1830×16, kerf 3, trim 2, `Lunghezza=2750` orientatsiya. Detallar: 1) 800×400 ×2, 2) 1000×300, 3) 500×600, 4) 480×290; 5) qoldiq 2740×814.
Tekshiruv: Y: 5+(400+3)+(600+3)=1011 → qoldiq 1830−1011−5=814; X(Y400): 5+2×803=1611≤2750; U(X1000): 303+293=596≤600; V(U290): 483≤1000.

`1001_mijoz_LDSP_NAMUNA.zip`:

`1001_mijoz_LDSP_NAMUNA.XMix`
```xml
<xMix><Header Date="01.10.2026" Descrizione="1001_mijoz_LDSP_NAMUNA" Import="From GibLab"/><Materials><Material Larghezza="1830" Lunghezza="2750" Quantita="1" Spessore="16" Tipologia=""/></Materials><RigheMix><RigaMix CambioMateriale="0" File="C:\MaestroCut\Client\xMix\1001_mijoz_LDSP_NAMUNA.001.XPrg" Pacco="2" Rep="1"/></RigheMix></xMix>
```

`1001_mijoz_LDSP_NAMUNA.001.XPrg` (Etichetta 2–4 qisqartirildi — ular 1-ga o'xshash)
```xml
<SchemaDoc><Header GibLabID="00000000000000000000000000000001" TipoCave="1" NumFogliPacco="2" Descrizione="LDSP NAMUNA" Spessore="16" Date="01/10/2026" Lunghezza="2750" Larghezza="1830" SpessoreLama="3" Swap="0" Inforesto="1"/>
<Material Tipologia="1" Codice=""/>
<Pattern>
<Cut ID="1" T="P" Dim="2750" Rip="1" EtiID=""/>
<Cut ID="2" T="RY" Dim="5" Rip="1" EtiID=""/>
<Cut ID="3" T="Y" Dim="400" Rip="1" EtiID=""/>
<Cut ID="4" T="RX" Dim="5" Rip="1" EtiID=""/>
<Cut ID="5" T="X" Dim="800" Rip="2" EtiID="(1)(1)"/>
<Cut ID="6" T="F" Dim="0.00" Rip="0" EtiID=""/>
<Cut ID="7" T="Y" Dim="600" Rip="1" EtiID="(5)"/>
<Cut ID="8" T="RX" Dim="5" Rip="1" EtiID=""/>
<Cut ID="9" T="X" Dim="500" Rip="1" EtiID="(3)"/>
<Cut ID="10" T="F" Dim="0.00" Rip="0" EtiID=""/>
<Cut ID="11" T="X" Dim="1000" Rip="1" EtiID=""/>
<Cut ID="12" T="U" Dim="300" Rip="1" EtiID="(2)"/>
<Cut ID="13" T="F" Dim="0.00" Rip="0" EtiID=""/>
<Cut ID="14" T="U" Dim="290" Rip="1" EtiID=""/>
<Cut ID="15" T="V" Dim="480" Rip="1" EtiID="(4)"/>
<Cut ID="16" T="F" Dim="0.00" Rip="0" EtiID=""/>
</Pattern>
<DatiEtichetta>
<Etichetta Id="1" Resto="0" Codice="1001 mijoz" Lunghezza="800.00" Larghezza="400.00" Richiesti="2" CodiceBordo1="A" CodiceBordo2="A" CodiceBordo3="A" CodiceBordo4="" Job="1001 mijoz" Campo1="1001 mijoz" Campo2="" Campo3="1" Campo4="800.00" Campo5="400.00" Campo6="16.00" Campo7="" Campo8="1" Campo9="2" Campo10="01_001 bok" Campo11="1-19 Namuna" Campo12="1-19 Namuna" Campo13="1-19 Namuna" Campo14="" Campo15="KP-1/19-N" Campo16="KP-1/19-N" Campo17="KP-1/19-N" Campo18="" Campo19="0" Campo20="sheet" Campo21="" Campo22="" Campo23="" Campo24="" Campo25="" Campo26="01.10.2026" Campo27="" Campo28="LDSP NAMUNA" Campo29="" Campo30="1" Campo31="01 shkaf" Campo32="100101" Campo33="1" Campo34="" Campo35="" Campo36="01_001" Campo37="01_001 bok" Campo38="" Campo39="1" Campo40="1" Campo41="800.0" Campo42="400.0" Campo43="800.0" Campo44="400.0" Campo45="16.0" Campo46="false" Campo47="2" Campo48="2" Campo49="2" Campo50="1-19 Namuna" Campo51="1.0" Campo52="1-19 Namuna" Campo53="1.0" Campo54="1-19 Namuna" Campo55="1.0" Campo56="" Campo57="0.0" Campo58="false" Campo59="false" Campo60="false" Campo61="" Campo62="" Campo63="" Campo64="00000000000000000000000000000001#1"/>
<Etichetta Id="2" .../>
<Etichetta Id="3" .../>
<Etichetta Id="4" .../>
<Etichetta Id="5" Resto="1" Codice="1001 mijoz" Lunghezza="2740.00" Larghezza="814.00" Richiesti="1" CodiceBordo1="" CodiceBordo2="" CodiceBordo3="" CodiceBordo4="" Job="1001 mijoz" Campo1="1001 mijoz" Campo2="" Campo3="5" Campo4="2740.00" Campo5="814.00" Campo6="16.00" Campo7="" Campo8="0" Campo9="0" Campo10="" Campo11="" Campo12="" Campo13="" Campo14="" Campo15="" Campo16="" Campo17="" Campo18="" Campo19="1" Campo20="sheet" Campo21="" Campo22="" Campo23="" Campo24="" Campo25="" Campo26="01.10.2026" Campo27="" Campo28="LDSP NAMUNA" Campo29="" Campo30="" Campo31="" Campo32="" Campo33="" Campo34="" Campo35="" Campo36="" Campo37="" Campo38="" Campo39="1" Campo40="1" Campo41="2740.0" Campo42="814.0" Campo43="2740.0" Campo44="814.0" Campo45="16.0" Campo46="true" Campo47="1" Campo48="1" Campo49="0" Campo50="" Campo51="0.0" Campo52="" Campo53="0.0" Campo54="" Campo55="0.0" Campo56="" Campo57="0.0" Campo58="false" Campo59="false" Campo60="false" Campo61="" Campo62="" Campo63="" Campo64="00000000000000000000000000000001#5"/>
</DatiEtichetta>
<GibLabLabel>
<part id="1" data="<base64(zlib(label-map))>"/>
...
<part id="5" data="..."/>
</GibLabLabel>
</SchemaDoc>
```

### Generatsiya algoritmi (MebeliX uchun)
1. Har bir material (CS) uchun kartalarni guruhlash; bir xil kartalar → bitta XPrg, `Rep` = soni.
2. Karta daraxtini (`Y→X→U→V`) pre-order bilan yozish: `P`, `RY`, so'ng har `Y` uchun `Y`, `RX`, uning bolalari…
3. `F` ni 3.3-bo'limdagi qoida bilan qo'shish.
4. Etiketkalar: kartadagi har bir alohida part + qoldiqlar (oxirida), `Campo40` bo'yicha tartib.
5. XMix: har XPrg uchun `Material` + `RigaMix`.

---

## 7. Ochiq savollar (foydalanuvchiga)

1. **Q1** `Lunghezza/Larghezza` va `Campo4/5`, `Campo43/44` — kesish o'lchami (`cl/cw`, pre-jointing bilan) mi yoki detal o'lchami (`l/w`)? Namunalarda hammasi teng; kromka qalinligi > `elWidthPreJoint` bo'lgan loyiha namunasi kerak.
2. **Q2** Kasr o'lchamlar (masalan 346.5) `Cut@Dim` da qanday yoziladi (`346.5`? `346.50`?) — namuna yo'q.
3. **Q3** `RY` = `cTrimW+kerf`, `RX` = `cTrimL+kerf` mi yoki aksincha? Turli trimli namuna kerak.
4. **Q4** Kirillcha nomlar (detal/material) bo'lsa fayl kodlashi (cp1251? UTF-8?) — namuna yo'q. XML maxsus belgilar (`&`, `"`) qochirilishi ham tekshirilmagan.
5. **Q5** `Campo58/59/60` — paz / parmalash / frezalash bayroqlarimi?
6. **Q6** `Campo8` — `txt` bayrog'imi? 3161 da `01_009 sokl` (`txt=false`) uchun `1` yozilgan (yagona istisno).
7. **Q7** `Campo39` (index) aniq qanday hisoblanadi (mahsulotdagi part tartibi?).
8. **Q8** `<GibLabLabel>` blobi MaestroCut uchun majburiymi (etiketka printeri) yoki uni tashlab yuborish/bo'sh qoldirish mumkinmi? Agar kerak bo'lsa — blob formatini to'liq yozish kerak.
9. **Q9** `Rep` > `NumFogliPacco` (masalan 3 list bir xil karta) bo'lganda qanday yoziladi — `Rep=3` yoki ikkita qator? EtiID qatlamlari `(a,a,a)` bo'ladimi?
10. **Q10** Bir zip ichida turli materiallar (`CambioMateriale=1`) hech qachon bo'lmaydimi? `RigaMix@File` yo'li mashinada doimiy `C:\MaestroCut\Client\xMix\` mi?
11. **Q11** Qoldiq `Y` dan boshqa darajada (masalan X polosasi oxirida) bo'lishi mumkinmi va qanday belgilanadi?
