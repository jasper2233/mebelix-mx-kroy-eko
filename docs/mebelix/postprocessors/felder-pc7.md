# Felder PC7 — `.may` formati (GibLab post-protsessor chiqishi)

> Manba: `post prtsessorlar/PILNIY APPARAT/Felder PC7/*.may` (7 ta fayl: 3151, 3153, 3155, 3156, 3157, 3159, 3161) va mos `<NNNN>_<mijoz>.project`.
> Tekshirish: 7 fayl, 30 karta (MA200), 192 detal + 12 `REST` qatori (MA010), 65 `MA400` + 45 `MA300`, 294 barg yozuvi (289 detal + 5 qoldiq `R1`).
> Bu **Felder PC6** formatining yangi "dialekti": yozuv kodlari (MA000…MA999) va kesish daraxti kodlash qoidasi **bir xil**, lekin maydonlar
> `§§` bilan ajratilgan erkin uzunlikli matn, `MA005/MA015/MA050` va etiketka bloki yo'q, qoldiqlar (`REST`, `R1`) qo'shilgan.
> Shuning uchun fayl ~10 marta kichik. Kesish qismi PC6 bilan 7/7 bir xil — umumiy qoidalar `felder-pc6.md` 3-bo'limida batafsil.
> Ishonch: **yuqori** (detal, kromka, XNC bayroqlari, kesish sxemasi va qoldiq 100% tekshirildi); bir nechta doimiy maydonlar — savol.

---

## 1. Fayllar

| Xususiyat | Qiymat |
|---|---|
| Kengaytma | `.may` |
| Nomlash | `<loyiha nomi>_<material nomi, bo'sh joylar → _>.may` (PC6 bilan bir xil). Fayl nomi `MA000` ichida ham yoziladi |
| Soni | bitta material (CS operatsiyasi) = bitta fayl |
| Kodlash | **UTF-8, BOMsiz** (ajratkich `§` = `C2 A7`); boshqa belgilar namunada ASCII |
| Qator oxiri | CRLF; oxirgi `MA999` ham CRLF bilan |
| Ajratkich | `§§` (ikki dona U+00A7). Qator oxirida ajratkich **yo'q** (istisno — qoldiq polosasi, pastga qarang) |
| Maydonlar | erkin uzunlik, to'ldirish (padding) yo'q, nomlar qisqartirilmaydi |
| Sonlar | butun sonlar kasrsiz (`1900`, `16`, `5`); kasrli o'lchamlar qanday yozilishi noma'lum (savol) |
| Mantiqiy | `True/False` (MA010#8 — Python/.NET uslubi), `true/false` (MA010#24–26) |
| Birlik | mm (`MA000#5 = MM`) |

Tuzilish:

```
MA000                         sarlavha
MA010 × N                     detallar (CS tartibida)
MA010 REST (list zaxirasi)    1 ta: ishlatilgan butun listlar
MA010 REST (qoldiq)           0..n ta: kroydan chiqqan delovoy qoldiq(lar)
{ MA200 ; { MA300|MA400 ; { MA3k0|MA4k0 }* }* }*   kartalar
MA999
```

---

## 2. Yozuvlar va maydonlar (`#` — `§§` bo'yicha indeks, 0 = tur)

### MA000 — sarlavha (8 maydon)

| # | Misol | Ma'nosi |
|---|---|---|
| 1 | `26.09.2026` | eksport sanasi `DD.MM.YYYY` |
| 2 | `GibLab` | dastur nomi (doimiy) |
| 3 | `I` | doimiy — **savol** |
| 4 | `3161_mijoz_LDSP_PIKARD.may` | fayl nomi |
| 5 | `MM` | birlik |
| 6 | `UZS` | valyuta (`project@currency`) |
| 7 | `3161 mijoz` | buyurtma (`product.order`) |

### MA010 — detal (28 maydon)

| # | Misol | Ma'nosi / manba |
|---|---|---|
| 1 | `1` | **`part@id`** (loyihadagi ID; kesish yozuvlari shunga havola qiladi) |
| 2 | `110052` | material kodi `sheet@code`; kod bo'sh bo'lsa — **material nomi** (`LMDF DUB VATAN`) |
| 3 | `16` | qalinlik |
| 4 | `01_001 bok` | `part@name` (to'liq) |
| 5 | `1900` | uzunlik `l` |
| 6 | `347` | eni `w` |
| 7 | `1` | soni `count` |
| 8 | `False`/`True` | tekstura (`txt`): `True` = burish mumkin emas. 192/192 mos* |
| 9 | `(A) 1-19 Sasna` | yuqori kromka `elt` → `(<elSymbol>) <band@name>`; yo'q bo'lsa bo'sh |
| 10 | | pastki kromka `elb` |
| 11 | | chap kromka `ell` |
| 12 | | o'ng kromka `elr` |
| 13, 14 | `1900`,`347` | o'lcham (takror; `cl/cw` deb taxmin) |
| 15, 16 | `1900`,`347` | o'lcham (takror; `dl/dw` yoki `l/w` deb taxmin). **Diqqat:** PC6 dagi `jl/jw` (kromkasiz) bu yerda yo'q — `1900` (PC6: `1898`) |
| 17 | `1` | fayldagi tartib raqami (1..N) |
| 18 | `LDSP  PIKARD` | material nomi |
| 19 | `110052` | material kodi (bo'lmasa bo'sh) |
| 20 | `01 shkaf` | mahsulot (`good[typeId=product]@name`) |
| 21 | `` | doim bo'sh — **savol** |
| 22 | `316101_01_001` | XNC dastur kodi, 1-tomon (`operation[XNC][side=true]@code`) |
| 23 | `315501_01_029_2` | XNC dastur kodi, 2-tomon (`side=false`); yo'q bo'lsa bo'sh |
| 24 | `false` | **mill** — XNC dasturida konturni to'liq qalinlikka frezalash (`dp="contMillDepth"`) bor. Etiketka ma'lumotidagi `mill` bilan bir xil |
| 25 | `true` | **drill** — istalgan tomonda teshik bor (`bf/bl/br/bt/bb`) |
| 26 | `false` | **groove** — paz bor (`gr`, istalgan tomonda) |
| 27 | `#P(1)` | `#P(part@id)` — etiketka havolasi |

\* 3161 dagi `01_009 sokl` loyihada `txt=false`, faylda `True`; PC6 etiketka blokida ham `txt=1` — ya'ni eksport paytida loyihada `true` bo'lgan (loyiha keyin o'zgargan). Qoida o'zgarmaydi.

24–26 bayroqlar 192/192 detalda loyiha XNC dasturlari bilan tekshirildi (1 ta "faqat freza, teshiksiz" detalda `drill=false` — to'g'ri).

### MA010 `REST` — list zaxirasi va qoldiq (26 maydon)

```
MA010§§12§§110052§§16§§REST§§2750§§1830§§1§§True§§2750§§1830§§2750§§1830§§2750§§1830§§1§§LDSP  PIKARD§§110052§§§§§§§§§§false§§false§§false§§#P(12)
```

| # | Ma'nosi |
|---|---|
| 1 | ID: list uchun — CS ichidagi stok qismi `part@id` (loyihada `count=10000`, `l/w` = list); qoldiq uchun — yangi noyob ID (loyihada mavjud ID dan farq qilishi mumkin: 3155 da `2`, 3151 da `77`) |
| 2, 3 | material kodi/nomi, qalinlik |
| 4 | `REST` |
| 5, 6 | o'lcham. List: `2750×1830`. Qoldiq: **sof o'lcham** (trim olingan): masalan `2740×1100` |
| 7 | soni: list qatorida — **ishlatilgan listlar soni** (= Σ MA200#7 = `cMaterialCount`, 7/7 mos); qoldiq qatorida — `0` |
| 8 | doim `True` |
| 9–14 | o'lcham juftligi 3 marta takror |
| 15 | doim `1` |
| 16 | material nomi |
| 17 | material kodi |
| 18–21 | bo'sh |
| 22–24 | `false§§false§§false` |
| 25 | `#P(id)` |

Tartib: avval barcha detallar, keyin list `REST`, keyin qoldiq `REST`(lar).

### MA200 — karta (15 maydon)

`MA200§§110052§§16§§LDSP  PIKARD§§#N(26092617480961705)§§2750§§1830§§1§§1§§1§§5§§5§§5§§5§§3`

| # | Ma'nosi |
|---|---|
| 1 | material kodi (yoki nomi) |
| 2 | qalinlik |
| 3 | material nomi |
| 4 | `#N(YYMMDDHHMMSS+5 raqam)` — partiya ID (fayldagi barcha kartalarda bir xil; PC6 MA005#6 bilan bir xil sxema, lekin vaqt boshqa) |
| 5, 6 | list L × W |
| 7, 8, 9 | shu karta bo'yicha listlar soni (uchala teng) |
| 10–13 | trim = `cTrimL + swSawthick` (5; 3159 da 8) |
| 14 | kerf `swSawthick` (3; 3159 da 6) |

### MA300 / MA400 — polosa

* `MA300§§304` — polosa list uzunligi bo'ylab (o'lchami Y o'qida); `MA400§§2254` — ko'ndalang polosa (o'lchami X o'qida).
* **Qoldiq polosasi** oxirida bo'sh maydon bilan: `MA300§§1105§§` (3 maydon). U kartaning oxirgi polosasi va o'lchami list chetigacha (uzoq trimni o'z ichiga oladi): 3155: `1830 − 5 − (614+3+100+3) = 1105`.

### MA3k0 / MA4k0 — barg (6 maydon)

`MA420§§D7§§498§§420§§7§§1`

| # | Ma'nosi |
|---|---|
| 1 | belgi: `D<part@id>` (detal) yoki `R<n>` (qoldiq, n = fayldagi qoldiq tartib raqami) |
| 2 | list X o'qi bo'yicha o'lcham |
| 3 | list Y o'qi bo'yicha o'lcham |
| 4 | havola: detal uchun `part@id`, qoldiq uchun `REST` qatori ID si |
| 5 | **shu yozuv bo'yicha jami dona = karta listlari soni** (MA200#7). PC6 da bu doim `01` |

k (1…5) ma'nosi PC6 bilan bir xil (`felder-pc6.md` §3): `k = 2L−3`; agar detal yangi ochilgan ota bo'lakdagi birinchi kesim va `L≥3` → `k = 2L−4`.

Qoldiq bargi: `MA310§§R1§§2750§§1105§§2§§1` — o'lchamlar **xom** (list chetlarini qo'shib, `2750` = butun uzunlik), `REST` qatorida esa sof (`2740×1100` = `2750−2·5`, `1105−5`). MA400 holatida (3151): `MA400§§1595§§` + `MA410§§R1§§1595§§1830§§77§§1`, `REST 1590×1820`.

---

## 3. Kesish rejasi

PC6 bilan aynan bir xil (polosalar, darajalar, k-kodlar, yashirin oraliq bo'laklar, trim/kerf, takrorlar). Farqlar:

| | PC6 | PC7 |
|---|---|---|
| Detal havolasi | MA010 tartib raqami (`7`) | `D<part@id>` + `part@id` |
| Barg soni maydoni | doim `01` | karta listlari soni (`2` bo'lishi mumkin) |
| Qoldiq | yo'q | `MA3/400§§<o'lcham>§§` + `R1` bargi + `REST` qatori |
| Partiya ID `#N` | MA005 da 1 marta | har MA200 da |

**Tekshiruv natijalari:**
* 30 karta geometrik qayta tiklandi: detallar list/trim ichida, o'zaro kesishmaydi, 0 xato (faqat `R1` qoldiq bo'laklari ataylab list chetigacha).
* Σ(barg × MA200#7) = `part@count` har bir pozitsiyada; jami = `cPartCount` (61, 70, 33, 73, 36, 20, 18) — 7/7.
* SCM MaestroCut `.XPrg` daraxtidan hisoblangan k-kodlar bilan 30/30 karta to'liq mos.
* `REST` list qatori soni = ishlatilgan listlar (6, 5, 3, 8, 7, 3, 1) = `cMaterialCount` — 7/7. Qoldiq qatorlari soni = `cWasteCount` (3153 va 3161 da 0, qolganlarida 1) — 7/7.
* Tekstura (`True`) detallari hech qachon burilmagan (142/142).

---

## 4. Loyiha → fayl moslik (tekshirilgan misollar, mijoz nomlarisiz)

| Loyiha | PC7 |
|---|---|
| `part@id` | MA010#1, #27 `#P(id)`; barg `D<id>`, #4 |
| `sheet@code` ∨ `sheet@name` | MA010#2, MA200#1 |
| `sheet@name` | MA010#18, MA200#3 |
| `part@name, l, w, count, txt` | MA010#4–8 |
| `elt/elb/ell/elr` + `EL@elSymbol` + `band@name` | MA010#9–12 |
| mahsulot `good@name` | MA010#20 |
| XNC `side=true/false` kodlari | MA010#22/#23 |
| XNC dastur mazmuni (contMill/teshik/paz) | MA010#24/#25/#26 |
| `cTrimL+swSawthick`, `swSawthick` | MA200#10–13, #14 |
| `cMaterialCount`, `cWasteCount` | REST qatorlari |

1. **3161:** `MA010§§2§§110052§§16§§01_002 bok§§1900§§347§§1§§False§§(A) 1-19 Sasna§§§§(A) 1-19 Sasna§§(A) 1-19 Sasna§§…§§316101_01_002§§§§false§§true§§false§§#P(2)` — loyiha: elt, ell, elr; `txt=false`; XNC faqat `bf` (teshik) ✓. Karta: 1 list, `MA400§§2254`, `MA420§§D7§§498§§420§§7§§1` (MaestroCut: `X420 → U498 Rip=2`) ✓.
2. **3155:** material kodi yo'q → `#2 = LMDF DUB VATAN`; `01_029 tom` → `#22=315501_01_029`, `#23=315501_01_029_2`, paz 2-tomonda → `#26=true` ✓; `01_031 polka` XNC yo'q → `§§§§§§false§§false§§false` ✓. 3 list (`REST … §§3§§`), qoldiq `R1 2750×1105` → `REST 2740×1100` ✓.
3. **3157:** 1–2-kartalar `§§2§§2§§2§§`, barglar `…§§14§§2` (2 dona); `REST` list soni 7 = 2+2+1+1+1 ✓; qoldiq `R1 2750×1548` → `REST 2740×1543` ✓.
4. **3151:** freza konturli `01_038 rover` (`contMillDepth`) → `#24=true`; `01_047 rover` faqat freza (teshiksiz) → `false§§false§§false` ✓. `MA400` qoldiq `1595×1830` → `REST 1590×1820` ✓.

---

## 5. Minimal qayta tiklangan misol (anonim)

PC6 misolidagi bilan bir xil buyurtma (`9001 mijoz`, `LDSP OQ`, 2750×1830×16, trim 5, kerf 3), qo'shimcha ravishda qoldiq: polosalardan keyin `1830−5−(560+3+396+3) = 863` → `REST 2740×858`.

```text
MA000§§04.10.2026§§GibLab§§I§§9001_mijoz_LDSP_OQ.may§§MM§§UZS§§9001 mijoz
MA010§§1§§LDSP OQ§§16§§01_001 bok§§720§§560§§2§§False§§(A) 1-19 oq§§(A) 1-19 oq§§§§§§720§§560§§720§§560§§1§§LDSP OQ§§§§01 shkaf§§§§900101_01_001§§§§false§§true§§false§§#P(1)
MA010§§2§§LDSP OQ§§16§§01_002 polka§§564§§300§§2§§False§§(A) 1-19 oq§§§§§§§§564§§300§§564§§300§§2§§LDSP OQ§§§§01 shkaf§§§§§§§§false§§false§§false§§#P(2)
MA010§§3§§LDSP OQ§§16§§01_003 fasad§§716§§396§§1§§True§§(A) 1-19 oq§§(A) 1-19 oq§§(A) 1-19 oq§§(A) 1-19 oq§§716§§396§§716§§396§§3§§LDSP OQ§§§§01 shkaf§§§§900101_01_003§§§§false§§true§§false§§#P(3)
MA010§§10§§LDSP OQ§§16§§REST§§2750§§1830§§1§§True§§2750§§1830§§2750§§1830§§2750§§1830§§1§§LDSP OQ§§§§§§§§§§§§false§§false§§false§§#P(10)
MA010§§11§§LDSP OQ§§16§§REST§§2740§§858§§0§§True§§2740§§858§§2740§§858§§2740§§858§§1§§LDSP OQ§§§§§§§§§§§§false§§false§§false§§#P(11)
MA200§§LDSP OQ§§16§§LDSP OQ§§#N(26100412000012345)§§2750§§1830§§1§§1§§1§§5§§5§§5§§5§§3
MA300§§560
MA310§§D1§§720§§560§§1§§1
MA310§§D1§§720§§560§§1§§1
MA320§§D2§§564§§300§§2§§1
MA320§§D2§§564§§300§§2§§1
MA300§§396
MA310§§D3§§716§§396§§3§§1
MA300§§863§§
MA310§§R1§§2750§§863§§11§§1
MA999
```

(UTF-8 BOMsiz, har qator CRLF.) Generatsiya algoritmi — `felder-pc6.md` §5; qo'shimcha: barg #1 = `D<id>`, #5 = listlar soni; qoldiq bo'lsa oxirgi polosa `§§` bilan tugaydi va `R<n>` bargi + `REST` qatori yoziladi.

---

## 6. Ochiq savollar

1. `MA000#3 = I` nimani bildiradi?
2. `#N(...)` oxirgi 5 raqami qanday hosil qilinadi; mashina uni tekshiradimi?
3. MA010#13–16: aniq qaysi o'lchamlar (`cl/cw`, `dl/dw`, `l/w`)? PC6 da ikkinchi juftlik `jl/jw` (kromkasiz), PC7 da emas — bu farq to'g'rimi yoki PC7 sozlamasimi?
4. MA010#21 (bo'sh) — mahsulot izohi/kodi uchunmi?
5. Kasrli o'lchamlar (masalan 597.5) PC7 da qanday yoziladi — `597.5` yoki `597,5`? Namunada hammasi butun.
6. MA200#7/#8/#9 farqi (PC6 dagi savol bilan bir xil); paket balandligi (`swPackageHeight`) bo'yicha bo'linadimi?
7. Bir kartada bir nechta qoldiq (`R1`, `R2`) yoki qoldiq oxirgi bo'lmagan kartada bo'lishi mumkinmi? `R` raqami fayl bo'yicha yoki karta bo'yicha sanaladimi? (Namunada har faylda ≤1 qoldiq, doim oxirgi kartaning oxirgi polosasida.)
8. Qoldiq polosasi faqat 1-darajali polosa bo'lishi shartmi (namunada shunday), yoki ichki bo'lakdan ham qoldiq chiqarish mumkinmi?
9. Qoldiq `REST` ID si qanday tanlanadi (loyihadagi ID dan ±1 farq bor)? Ixtiyoriy noyob ID yetarlimi?
10. MA010#24 (`mill`) faqat `contMillDepth` (to'liq qalinlikdagi kontur) uchunmi yoki boshqa freza turlari ham hisoblanadimi? (Namunada `throughCutDepth` bilan Mill40 — `false`.)
11. PC6 va PC7 qaysi stanoklarda ishlatiladi va bittasini tanlash kerakmi (bir xil kroy, ikki format)?
