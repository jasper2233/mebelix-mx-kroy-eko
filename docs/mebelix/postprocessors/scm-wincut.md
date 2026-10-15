# SCM WinCut — postprotsessor formati (namunalardan teskari hujjatlash)

> Manba: `post prtsessorlar/PILNIY APPARAT/SCM WinCut/*.zip` (7 ta buyurtma: 3151, 3153, 3155, 3156, 3157, 3159, 3161),
> mos `giblab project/3 Eldor/<raqam> <mijoz>/<raqam>_<mijoz>.project` bilan solishtirildi. Mijoz ismlari — «mijoz».
> Bir xil buyurtmalar **SCM MaestroCut** formatida ham bor — [scm-maestrocut.md](scm-maestrocut.md). Ikkala format
> **aynan bir xil kesish daraxtini** saqlaydi (30/30 fayl, har bir kesim, o'lcham, Rip va etiketka havolasi mos);
> farq faqat yozilish sintaksisida. Etiketka maydonlarining to'liq ma'nosi MaestroCut hujjatida (bu yerda havola qilinadi).

**Tushunish darajasi: to'liq (kesish va `*`-qatorlar qoidasi 30/30 faylda qayta generatsiya bilan tasdiqlangan); blob — qisman.**

---

## 1. Qanday fayllar chiqadi

| Xususiyat | Qiymat |
|---|---|
| Konteyner | Har bir *buyurtma × material* uchun bitta `.zip`, nomi `<loyiha>_<material>.zip` (bo'shliqlar `_`, ketma-ket bo'shliqlar bittaga) |
| Zip ichi | **Bitta papka**: `<buyurtma nomi>/` — bu `product.order` qiymati, ya'ni «`<raqam> <mijoz>`» (bo'shliq bilan, masalan `3161 mijoz/`). Papka yozuvi alohida emas — faqat fayl yo'li ichida |
| Fayllar | `<buyurtma nomi>/<loyiha>_<material>.001`, `.002`, … — **har bir karta (pattern) uchun bitta fayl**, kengaytma = 3 xonali raqam |
| Partiya fayli | **Yo'q** (MaestroCut'dagi `.XMix` ga o'xshash narsa yo'q); bir karta bo'yicha listlar soni faqat `AltPacco` orqali bilinadi |
| Kodlash | ASCII (barcha 30 fayl); Kirill uchun noma'lum (Q4) |
| Qator oxiri | CRLF, fayl **oxirida ham** CRLF bor |
| Format | INI uslubi: `[Bo'lim]` va `kalit=qiymat`; bo'sh qatorlar yo'q; ro'yxat elementlari vergul bilan |
| O'nlik ajratgich | Nuqta `.`; kesim o'lchamlari butun son, «bo'sh» sonlar `0.0000` |
| Zip | Deflate, flag 0x808 |

---

## 2. Fayl tuzilishi

```
[Intestazione]
Descrizione=<list nomi>
TipoMateriale=<list kodi yoki bo'sh>
Lunghezza=<mm>
Larghezza=<mm>
Spessore=<mm>
AltPacco=<mm>
VelRotaz=3000
VelAvanz=30
[Dati]
NumeroDati=<m>
1=<etiketka 1>
...
m=<etiketka m>
[Righe]
1=<kesim 1>
...
n=<kesim n>
NumeroRighe=<n>
[Riferimenti]
1=<kesim 1 etiketkalari>
...
n=<kesim n etiketkalari>
```
E'tibor: `[Dati]` da son **boshida** (`NumeroDati`), `[Righe]` da **oxirida** (`NumeroRighe`); `[Riferimenti]` da son qatori yo'q, qatorlar soni = `NumeroRighe`.

### 2.1 `[Intestazione]`

| Kalit | Ma'no | Manba | Kuzatilgan |
|---|---|---|---|
| `Descrizione` | List nomi (aynan) | `sheet@name` | `LDSP  PIKARD` |
| `TipoMateriale` | List kodi | `sheet@code` | faqat 3161 da `110052`, qolganida bo'sh |
| `Lunghezza` | Y-kesim chizig'i bo'ylab o'lcham (MaestroCut `P`) — karta orientatsiyasi | 2750 yoki 1830 | ikkalasi |
| `Larghezza` | Y-polosalar o'lchanadigan o'q | | 1830 yoki 2750 |
| `Spessore` | Qalinlik | `sheet@t` | 16 |
| `AltPacco` | **Paket balandligi = Rep × qalinlik** (shu karta bo'yicha birga kesiladigan listlar) | | 16 (1 list), 32 (2 list) |
| `VelRotaz` | Arra aylanish tezligi (doimiy sozlama) | — | 3000 |
| `VelAvanz` | Surish tezligi (doimiy sozlama) | — | 30 |

`AltPacco=32` bo'lgan fayllar (3156.001, 3157.001, 3157.002) MaestroCut `XMix` da `Rep=2`/`Quantita=2` ga to'liq mos. Arra qalinligi (kerf) faylda **yozilmaydi** — trim qiymatida yashirin (`RY = trim + kerf`; 3159 da `8`, qolganida `5`).

### 2.2 `[Dati]` — etiketkalar (31 vergul bilan ajratilgan maydon)

`<Id>=f1,f2,f3,...,f31` — kalit = etiketka `Id` (MaestroCut `Etichetta@Id` bilan bir xil raqamlash va tartib: detallar CS-operatsiyadagi o'rni bo'yicha, qoldiqlar oxirida).

| # | Ma'no | Manba (tasdiqlangan 223/223) | Kuzatilgan |
|---|---|---|---|
| 1, 2 | bo'sh | — | `""` |
| 3 | **Shu kartadagi** bu etiketkali bo'laklar soni (barcha Rip va paket qatlamlari bilan, `[Riferimenti]` dagi id'lar soni) | hisoblanadi | 1…7 |
| 4 | doimiy matn | — | `jobName` |
| 5 | doimiy matn | — | `jobDesc` |
| 6 | Project part id (MaestroCut `Campo3`) | `part@id` | — |
| 7 | Uzunlik, butun mm | `part@cl` (= `l`) | — |
| 8 | En, butun mm | `part@cw` | — |
| 9 | Qalinlik | `sheet@t` | 16 |
| 10 | bo'sh | — | |
| 11 | doimiy | — | `0` |
| 12 | Loyihadagi umumiy soni (`Richiesti`) | `part@count` (qoldiqda 1) | 1…12 |
| 13–28 | bo'sh (16 ta) | — | |
| 29 | Tur | — | `PART` / `REST` |
| 30 | Detalning CS-operatsiya ro'yxatidagi o'rni (MaestroCut `Campo40`); qoldiqda `1` | | |
| 31 | Etiketka blobi `base64(zlib(...))` — MaestroCut `<GibLabLabel><part data>` bilan **bayt-bayt bir xil** | | |

Detal nomi, kromkalar, mahsulot va boshqa etiketka ma'lumotlari faqat 31-maydondagi blob ichida (format tavsifi — MaestroCut hujjati §3.7).

### 2.3 `[Righe]` — kesimlar

`<k>=<T>,<Dim>,<Rip>,0.0000,0.0000,0.0000,0.0000`

| `T` | Ma'no |
|---|---|
| `RY` | 1-daraja trim (bir marta, birinchi qator) — `Dim` = trim+kerf |
| `Y` | 1-daraja polosa, `Larghezza` o'qi bo'ylab |
| `RX` | 2-daraja trim, har `Y` dan keyin |
| `X` | 2-daraja, `Lunghezza` o'qi bo'ylab |
| `U` | 3-daraja, `Larghezza` o'qi bo'ylab |
| `V` | 4-daraja, `Lunghezza` o'qi bo'ylab |
| `U*`, `V*` | Daraja belgisi qatori: `U*,0.0000,0,0.0000,0.0000,0.0000,0.0000` (pastdagi qoida) |

* MaestroCut'dagi `P` (karta boshi) va `F` (tugallash) qatorlari WinCut'da **yo'q**; ularning o'rniga `*`-qatorlar.
* `Dim` — butun mm; `Rip` — takror soni (1…7). Oxirgi 4 ta maydon namunalarda doim `0.0000` (Q12).
* Tartib — daraxtni pre-order aylanish (MaestroCut bilan bir xil).

**`*`-qator qoidasi (30/30 faylda, 61 ta belgi, aynan qayta hosil qilindi):**
`X` (yoki `U`) darajasidagi bir ota ichidagi aka-uka kesimlar orasida, **birinchi bo'lmagan** va **o'z bolalari bor** birinchi kesimdan oldin bir marta `<keyingi daraja>*` qatori qo'yiladi:
* Y-polosa ichida: 2-, 3-, … `X` lardan birinchisi `U`-bolalarga ega bo'lsa, uning oldiga `U*`.
* X-bo'lak ichida: 2-, 3-, … `U` lardan birinchisi `V`-bolalarga ega bo'lsa, uning oldiga `V*`.
* Har bir ota uchun ko'pi bilan bitta; eng birinchi aka-uka (indeks 0) hech qachon belgilanmaydi (bolasi bo'lsa ham); `Y` darajasida (`X*`) hech qachon uchramadi.

Misollar: `X597# X597# U* X597 U1160#…` (3157.001); `X1000 U244 V995# V* U1974 V496x2#` (3151.001 — birinchi U ham V'li, lekin belgi 2-sida); `X420 U498x2# V* U868 V346# U346 V300#` (3161 — ikkinchi V'li U belgilanmaydi).
Ma'nosi (taxmin): WinCut'ga «shu joydan boshlab bo'laklar keyingi darajada ham kesiladi» degan ishora — Q13.

### 2.4 `[Riferimenti]` — kesim → etiketka

`<k>=<etiketkalar>` — `[Righe]` dagi k-qator bilan bir xil raqam. Format MaestroCut `EtiID` bilan aynan: `(Id)` har bir tayyor bo'lak uchun; Rip>1 bo'lsa takrorlanadi (`(9)(9)(9)`); paket 2 list bo'lsa `(4,4)` (qatlamlar vergul bilan). Etiketkasiz kesim — bo'sh (`3=`), `*` qatorlari ham bo'sh. Qoldiq etiketkasi (`REST`) oxirgi `Y` qatoriga yoziladi (masalan `5=(5)` qatori `Y,600`).

---

## 3. Kesish rejasi qanday kodlanadi

* **Karta** = bitta fayl; bir nechta bir xil list — `AltPacco` (= list soni × qalinlik) va etiketkadagi `(a,a)` qatlamlar.
* **Orientatsiya** — `Lunghezza`/`Larghezza` almashishi bilan (30 dan 12 tasida `Lunghezza=2750`).
* **Darajalar** `Y→X→U→V`; har darajada bo'lak `Dim + kerf` joy egallaydi; trimlar `RY` (1×) va `RX` (har Y'da).
* **Tekstura** — `txt=true` detallar hech qachon burilmagan (uzun o'q bo'ylab = `l`), faqat `txt=false` lar burilgan.
* **Qoldiq** — `REST` etiketka, oxirgi `Y` ga; o'lchami trim bilan (masalan 3157.005: `2740×1543`).
* **Soni tekshiruvi** — `[Riferimenti]` dagi detal id'lari (PART) barcha fayllar bo'yicha yig'indisi = CS bo'yicha Σ`part@count`: 61, 70, 33, 73, 36, 20, 18 — 7/7 buyurtmada aniq mos; 3-maydon 223/223 to'g'ri.

---

## 4. Project → fayl moslik misollari

| Buyurtma | Project | WinCut |
|---|---|---|
| 3161 | `part id=9 "01_008 bok" 300×346 count=6`; `sheet code=110052` | `9=,,6,jobName,jobDesc,9,300,346,16,,0,6,…,PART,9,<blob>`; `TipoMateriale=110052`; `32=X,300,3,…` → `33=U,346,1,…` / `33=(9)(9)(9)` |
| 3159 | `swSawthick=6`, `cTrimW=2`; part 8 `01_005 ustun 2360×100 count=2`; 3 list | `.003`: `1=RY,8,…`, `3=RX,8,…`; `1=,,2,…,8,2360,100,16,,0,2,…,PART,8,…`; qoldiq `2=,,1,…,12,2734,1597,16,,0,1,…,REST,1,…` va `2=(2)` (`Y,211` qatori) |
| 3157 | 7 list; `.001` va `.002` kartalari 2 tadan list | `AltPacco=32`, `[Riferimenti]` `(2,2)`, `(1,1)`; 3-maydon `2` (bitta joylashuv × 2 qatlam) |
| 3156 | `02_017 nosh 100×1530` to'rtta part yozuvi (id 53–56), har biri count=1 | Turli fayllarda alohida `Dati` qatorlari, 6-maydon 53…56 |

---

## 5. Minimal namunaviy fayl (anonim; MaestroCut namunasidagi xuddi shu karta)

List 2750×1830×16, kerf 3, trim 2; detallar 800×400 ×2, 1000×300, 500×600, 480×290; qoldiq 2740×814.
Zip: `1001_mijoz_LDSP_NAMUNA.zip` → `1001 mijoz/1001_mijoz_LDSP_NAMUNA.001`

```ini
[Intestazione]
Descrizione=LDSP NAMUNA
TipoMateriale=
Lunghezza=2750
Larghezza=1830
Spessore=16
AltPacco=16
VelRotaz=3000
VelAvanz=30
[Dati]
NumeroDati=5
1=,,2,jobName,jobDesc,1,800,400,16,,0,2,,,,,,,,,,,,,,,,,PART,1,<blob>
2=,,1,jobName,jobDesc,2,1000,300,16,,0,1,,,,,,,,,,,,,,,,,PART,2,<blob>
3=,,1,jobName,jobDesc,3,500,600,16,,0,1,,,,,,,,,,,,,,,,,PART,3,<blob>
4=,,1,jobName,jobDesc,4,480,290,16,,0,1,,,,,,,,,,,,,,,,,PART,4,<blob>
5=,,1,jobName,jobDesc,5,2740,814,16,,0,1,,,,,,,,,,,,,,,,,REST,1,<blob>
[Righe]
1=RY,5,1,0.0000,0.0000,0.0000,0.0000
2=Y,400,1,0.0000,0.0000,0.0000,0.0000
3=RX,5,1,0.0000,0.0000,0.0000,0.0000
4=X,800,2,0.0000,0.0000,0.0000,0.0000
5=Y,600,1,0.0000,0.0000,0.0000,0.0000
6=RX,5,1,0.0000,0.0000,0.0000,0.0000
7=X,500,1,0.0000,0.0000,0.0000,0.0000
8=U*,0.0000,0,0.0000,0.0000,0.0000,0.0000
9=X,1000,1,0.0000,0.0000,0.0000,0.0000
10=U,300,1,0.0000,0.0000,0.0000,0.0000
11=V*,0.0000,0,0.0000,0.0000,0.0000,0.0000
12=U,290,1,0.0000,0.0000,0.0000,0.0000
13=V,480,1,0.0000,0.0000,0.0000,0.0000
NumeroRighe=13
[Riferimenti]
1=
2=
3=
4=(1)(1)
5=(5)
6=
7=(3)
8=
9=
10=(2)
11=
12=
13=(4)
```
(`<blob>` — base64(zlib) etiketka ma'lumoti; MebeliX uni qanday to'ldirishi Q8 ga bog'liq.)

### Generatsiya algoritmi
1. MaestroCut bilan umumiy karta daraxtini quring (`Y→X→U→V`, trimlar).
2. Pre-order yozing; `P`/`F` yozmang; 2.3-bo'limdagi qoida bo'yicha `U*`/`V*` qo'shing.
3. `[Riferimenti]` — har qator uchun bo'laklar etiketkalari; `[Dati]` 3-maydoni — shu id'lar soni.
4. `AltPacco = Rep × Spessore`.

---

## 6. Ochiq savollar

1. **Q1–Q4, Q8, Q9** — MaestroCut hujjatidagi bilan bir xil (kesish vs detal o'lchami, kasr o'lchamlar formati, RY/RX trim manbasi, kirill kodlash, blob majburiyligi, `Rep` > 2 holati — `AltPacco=48` bo'ladimi?).
2. **Q12** `[Righe]` dagi oxirgi 4 ta `0.0000` maydon nima (masalan, tezlik/bosim/kesim chuqurligi)? Qachon nol bo'lmaydi?
3. **Q13** `U*`/`V*` qatorlarining WinCut'dagi aniq ma'nosi? (Qoida aniqlangan, lekin ma'no taxminiy — stanok operatori yoki WinCut qo'llanmasidan tasdiqlash kerak.) `X*` (Y darajasida) umuman bo'lmaydimi?
4. **Q14** `VelRotaz=3000`, `VelAvanz=30` — material/qalinlikka qarab o'zgaradimi yoki doimiymi?
5. **Q15** Zip ichidagi papka nomi (`<raqam> <mijoz>`) majburiymi? MebeliX'da buyurtma kodi bilan almashtirish mumkinmi?
6. **Q16** `jobName`/`jobDesc` — doimiy matnmi yoki shablon o'zgaruvchisi to'ldirilmay qolganmi (ehtimol buyurtma nomi bo'lishi kerak edi)?
