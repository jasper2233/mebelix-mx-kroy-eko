# WEB-tadqiqot: Biesse / SCM / Felder / TPA fayl formatlari bo'yicha ochiq savollar

> Sana: 2026-10-04. Usul: WebSearch/WebFetch (EN/IT/DE/RU), ochiq PDF qo'llanmalar, GitHub manbalari.
> Hech qayerga login qilinmadi, bajariladigan fayl yuklanmadi.
>
> **Dalil darajalari** (har javobda ko'rsatilgan):
> * **[A] — birlamchi manba matni o'qildi** (PDF/manba kodi yuklab olinib, matni tekshirildi).
> * **[B] — faqat qidiruv tizimi xulosasi** (sahifaning o'zi 403/Cloudflare sababli ochilmadi; matn so'zma-so'z tekshirilmagan).
> * **[C] — xulosa/taxmin** (manbalardan mantiqiy chiqarilgan, to'g'ridan-to'g'ri yozilmagan).

## Asosiy manbalar

| # | Manba | Nima beradi | Daraja |
|---|---|---|---|
| S1 | TPA «TpaCAD Program Editor» qo'llanmasi (2017), 15.6-bo'lim «TpaCAD Program» — https://cdn.shopify.com/s/files/1/0350/8119/1561/files/TpaCAD_eng.pdf | `.tcn` matn formati, `W#81/89/2201/2101`, tomonlar geometriyasi | A |
| S2 | Format4 «Description of possible interface with tpaCAD 4.0» REV2 14-12-2016 — https://forums.autodesk.com/autodesk/attachments/autodesk/hsm-post-processor-forum-en/18184/1/FORMAT4_TPACAD_4_0_CODE_DEFINITION_REV2_14_12_2016.pdf | `W#1050/1051/1052` arra parametrlari, `#36`, `#40`, tomonlar boshi | A |
| S3 | BppLib (C# kutubxona, `.bpp`/`.cix` generator va parser) — https://github.com/viachpaliy/BppLib | BG / CUT_G / ROUT / LINE_EP / ARC_EPCE parametr nomlari va tartibi | A |
| S4 | Biesse «OSI Release 1 — Instructions for use» (L5804L0020) — https://stankoteam.ru/upload/iblock/e0a/e0a6e69dc0987b62f11a50a4f88adea3.pdf | Selco kesish kodlari, texnologik parametrlar, trim rejimlari | A |
| S5 | SCM «Maestro Cut» taqdimoti (2017) — https://www.scmgroup.com/group/software/pdf/maestro%20cut/presentation_maestro_cut_eng.pdf | P/Y/X/U/V/R/F kodlari, WinCut bilan moslik | A |
| S6 | «БАЗИС-ЧПУ. Руководство пользователя» (2025) — https://cdn.bazissoft.ru/documentation/ru/CNC.pdf | Startech CN / CN V / Xilog / BiesseWorks postprotsessor sozlamalari | A |
| S7 | Makxilia — Startech CN V texnik tavsifi — https://www.makxilia.biz/en/product/woodworking-machinery/boring-machines/cnc-automatic-boring-machines/cnc-universal-boring-machine-scm-group-startech-cn-v/ | Arra yo'nalishi, shpindellar | A (sahifa xulosasi orqali) |
| S8 | «Xilog Plus Training 2014» — https://pdfcoffee.com/xilog-plus-traning-2014-1-2-pdf-free.html (403, ochilmadi) | XBO/XG0/XGIN/C/F ta'riflari | **B** |

---

## 1. Biesse Selco OSI / OptiPlanning XML (`Order/WorkList/Job/Program/Cut`)

### 1.1 `Cut@Chk` — nazorat summasi
**JAVOB: TOPILMADI.** `Chk` atributi, uning algoritmi yoki OSI uni tekshirishi haqida ochiq manbada hech narsa yo'q (OSI qo'llanmasi S4 da XML import tuzilishi umuman tavsiflanmagan; forumlardagi namunaviy XML fayllar zip ichida, ochilmadi).

* Bilvosita ma'lumot [B]: OSI da XML importni Biesse servisi yoqishi kerak — «contact Biesse support to activate the XML import option» — https://suporte.promob.com/hc/en-us/articles/31122654246929-Cut-Pro-Biesse-Cutting-Managers-OSI
* Bilvosita [B]: OptiCut «XML» va «XML2» postprotsessorlari Selco SK3 + OSI da ishlaydi (namunalar forumda) — https://www.cnczone.com/forums/biesse/471040-biesse-selco-eb80-xml-import.html

**Generator uchun:** O'ZGARTIRMASLIK. `Chk` ni hozirgidek qoldirish; mashinada sinov shart (Chk siz / `0` bilan / noto'g'ri qiymat bilan import). OptiCut XML2 namunasi (yuqoridagi forum zip) `Chk` siz ishlasa — bu atribut majburiy emasligini isbotlaydi; uni foydalanuvchi qo'lda yuklab solishtirishi kerak.

### 1.2 `TechnoParam` 320–335
**JAVOB (qisman, ishonch: o'rta) [A+C]:** `TechnoParam` — OSI ning «Technological Parameters» mexanizmi: bu **mashina parametrlari raqamlari** (ID = mashina parametri nomeri), ularning qiymati dastur/material/panel/worklist darajasida qayta belgilanadi. Ya'ni 320–335 format konstantasi emas, balki **konkret mashina konfiguratsiyasidagi parametr nomerlari**. Har bir ID ning aniq nomi ochiq manbada yo'q.

* Dalil: «personalise a series of technological parameters (configurable list) for each pattern» — S4
* Dalil: «text-box Machine Parameter with the number of the associated parameter» — S4
* Dalil (trim bilan bog'liqlik, [C]): F7 Trim Cuts oynasi — «Front Forcing … Rear Forcing … Automatic» — S4. 4 ta `(0, 500, 500, 500)` guruh = 4 kesish darajasi uchun (forsaj rejimi=0, trim qiymatlari 5.00 mm) degan farazga mos, lekin isbotlanmagan.

**Generator uchun:** SAQLASH (namunadagi 16 qiymatni aynan yozish). Boshqa mashinaga chiqarilganda bu ID lar mos kelmasligi mumkin → postprotsessor profilida sozlanadigan qilish tavsiya etiladi.

### 1.3 Kesish kodlari (`Cut@Code`) — qo'shimcha topilma [A]
| Kod | Ma'nosi (S4) |
|---|---|
| 1 | Head cut — panel **eni** bo'ylab kesish; 4, 5, Z1, Z2 dan keyin kelmaydi |
| 2 | Cross cut on head cut portion — faqat 1 dan keyin |
| 4 | Length cut — panel **uzunligi** bo'ylab (rip) |
| 5 | Cross cut — odatda 4 dan keyin |
| Z1 | Uchinchi faza — faqat 2 yoki 5 dan keyin |
| Z2 | To'rtinchi faza — faqat Z1 dan keyin |
| W | Groove (paz) — oldingi qator yo'nalishida |

* Dalil: «Code 4: Length cut … Code 5: Cross cut» — S4.

**Generator uchun:** SAQLASH; hujjatlardagi kod jadvalini shu ta'riflar bilan to'ldirish.

---

## 2. Biesse Selco NC300 (`dist/`, `tagli/`: B_CUT, B_LABEL, B_REF, VL, VT, HP)

**JAVOB: fayl formati bo'yicha TOPILMADI.** `B_SCH/B_DAT/B_REF/B_CUT/B_LABEL`, `VL`, `VT`, `HP`, `CPI`, `PROX`, `ESE`, `OPZ` teglari hech bir ochiq manbada uchramadi (EN/IT/RU qidiruvlar natijasiz).

Qisman (OSI qo'llanmasidan o'xshashlik bo'yicha, ishonch: past-o'rta) [C]:
* **`FORZ`** ≈ trim «forsaj» rejimi: Front Forcing / Rear Forcing / Automatic (S4, F7 Trim Cuts). `FORZ=0` → avtomatik deb taxmin qilinadi.
* **Kod 4/5** (nc300 savol 8): bu «list 90° burilgan» emas, balki **birinchi kesish yo'nalishi** — 4 = uzunlik bo'ylab (rip), 5 = undan keyingi ko'ndalang (S4, yuqoridagi jadval). Ishonch: yuqori (Selco kodlari NC300 va OSI da bir xil nomlanadi).
* **`B_LABEL` majburiymi:** to'g'ridan-to'g'ri javob yo'q. OSI da detal ro'yxati faqat chop etish uchun: «Used for off-line label printing» — S4. Bu etiketka ma'lumoti kesishga ta'sir qilmasligiga ishora, lekin NC300 parseri blokni talab qilish-qilmasligi noma'lum.

**Generator uchun:** O'ZGARTIRMASLIK. `B_LABEL` ni to'liq yozishda davom etish (bo'sh blok bilan sinov faqat mashinada). `VL/VT/HP` — konstanta.

---

## 3. BiesseWorks BPP (`.bpp`)

Asosiy manba — BppLib (S3): `AsBppCode()` dagi maydon tartibi bizning namunadagi tartib bilan **to'liq mos tushdi** (BG 50/50, CUT_G 60/60, LINE_EP 9/9, ARC_EPCE 11/11, START_POINT 3/3; ROUT da 1 maydon siljishi — BiesseWorks versiya farqi). Ishonch: yuqori (nomlar), o'rta (ayrim semantika).

### 3.1 BG (teshik) — maydonlar nomi
```
SIDE, CRN, X, Y, Z, DP, DIA, THR, RTY, DX, DY, R, A, DA, NRP, ISO, OPT, AZ, AR, AP, CKA, XRC, YRC, ARP, LRP,
ER, MD, COW, A21, TOS, VTR, S21, ID, AZS, MAC, TNM, TTP, TCL, RSP, IOS, WSP, SPI, DDS, DSP, BFC, SHP, EA21, CEN, AGG, LAY
```
| Bizdagi qiymat | Haqiqiy parametr | Ma'nosi (S3) |
|---|---|---|
| `0` (5-o'rin, «Z doim 0») | **Z** | «translation position of the plane to be worked»; DP ga qo'shiladi |
| `0` (8-o'rin) | **THR** | o'tuvchi teshik bayrog'i — namunada **doim 0** |
| `-1` | **RTY** | takrorlash turi: −1 yo'q, 0 X, 1 Y, 2 XY, 3 aylana, 5 qiya chiziq |
| `32, 32` | **DX, DY** | takror qadamlari (RTY=−1 da ishlatilmaydi; BiesseWorks standart qiymati) |
| `50` | **R** | aylana takror radiusi (standart) |
| `0, 45` | **A, DA** | boshlang'ich burchak, burchak qadami (standart) |
| `0` | NRP | takrorlar soni |
| `""`, `1` | ISO, OPT | ISO qo'shimcha, optimallashtirish = ha |
| `-1` | S21 | AGGRE21 yuzi (ishlatilmaydi) |
| `"<Pid>"` | ID | ishlov identifikatori |
| **bizdagi «THR» (37-o'rin, indeks 36)** | **TTP — asbob turi** | «tool type from the predefined list of the tool types» |

* Dalil: «Dp represents the depth of the bore or the perforation offset value for through bores» — S3 `Bg.cs`.
* Dalil: README namunasi `BV ... DP=5 DIA=7 THR=YES TTP=1` — S3 (TTP=1 = o'tuvchi/lancia parma turi).

**MUHIM topilma:** hujjatimizdagi «36 | THR — o'tuvchi belgisi» aslida **TTP (parma turi: 0 = oddiy, 1 = o'tuvchi/lancia)**. Haqiqiy THR — 8-o'rindagi doimiy `0`. Shuning uchun `DP = dz+3` to'liq chuqurlik sifatida yozilishi to'g'ri (THR=1 bo'lganda DP «teshib o'tish zaxirasi» ma'nosini olardi).

**Generator uchun:** baytlar O'ZGARMAYDI; hujjat va koddagi nomni `THR` → `TTP` ga TUZATISH. `32/32/50/45` — konstanta (takror standartlari), asbobga bog'liq emas.

### 3.2 SIDE va CRN
**JAVOB (qisman):** S3 da faqat «Side represents the piece side», «Crn represents the piece reference corner» deyilgan; kodlar ro'yxati yo'q.
* [B] BiesseWorks yuz raqamlari: «0=up, 1=left, 2=front, 3=right, 4=back, 5=down» (qidiruv xulosasi, manba sahifasi aniq emas) — bizning jadvalga (1 chap, 2 old `y=dy`, 3 o'ng, 4 orqa `y=0`) mos. Ishonch: o'rta.
* CRN: S3 README da `Crn="1"`, `"2"`, hatto ro'yxat `"1,2,4,3"` uchraydi (bir nechta burchakdan simmetrik takror); dastur sarlavhasida `Origins`. Burchaklar geometriyasi (qaysi raqam qaysi burchak) — TOPILMADI.
* Qirra teshigida Y (balandlik) ustki yoki ostki yuzadan o'lchanishi — **TOPILMADI** (9-savolga qarang).

**Generator uchun:** SAQLASH; CRN "4" li qirra teshigi (hujjatdagi 1-savol) stanokda sinov detali bilan tekshirilsin.

### 3.3 CUT_G (arra pazi) — maydonlar nomi
```
SIDE, CRN, X, Y, Z, DP, TYP, L, ANG, XE, YE, ZE, AZ, ISO, OPT, TH, RTY, DX, DY, R, A, DA, RDL, NRP, CKA, THR, RV,
XRC, YRC, ARP, LRP, ER, COW, TTK, OVM, TOS, VTR, GIP, ID, TNM, TTP, TCL, RSP, IOS, WSP, SPI, BFC, SHP, BRC, BDR,
PRV, NRV, DIN, DOU, CRC, DSP, CEN, AGG, LAY, DVR
```
| Bizdagi | Parametr | Ma'nosi (S3) |
|---|---|---|
| `2` (indeks 6) | **TYP** | kesish turi: 2 = cutXY (boshi+oxiri), 3 = XA, 4 = YA, 5 = LA |
| `<SAW>` (indeks 15) | **TH** | «represents the blade thickness» — **arra qalinligi** |
| `<W>` (indeks 33) | **TTK** | «represents the total cut thickness» — **paz umumiy eni** |
| `201`, `2` (indeks 40, 41) | **TTP, TCL** | asbob turi / klassi (arra) |
| `1` (indeks 37) | GIP | profil boshlanishi detal yuzasida |
| `1` (indeks 50) | PRV | arra yo'nalishini o'zgartirishga ruxsat |
| `0` (indeks **54**) | **CRC** | korreksiya: 0 markaz, 1 o'ng, 2 chap |

**Generator uchun:** SAQLASH. Hujjatdagi 5-savol («paz `c=1/2` → CUT_G[6]?») TUZATILSIN: [6] bu TYP; korreksiya — **[54] CRC**. Paz eni mashinaga `TTK` orqali uzatiladi (ko'p o'tishni BiesseWorks o'zi hisoblaydi), `TH` — arra qalinligi; `201/2` — arra asbob turi/klassi (stanok profili sifatida saqlash).

### 3.4 ROUT / START_POINT / LINE_EP / ARC_EPCE
* ROUT boshi: `ID, SIDE, CRN, Z, DP, ISO, OPT, DIA, RTY, XRC, YRC, DX, DY, R, A, DA, RDL, NRP, AZ, AR, ZS, ZE, CKA, THR, RV, CKT, ARP, LRP, ER, COW, OVM, A21, TOS, VTR, DVR, OTR, SVR, COF, DOF, GIP, LSV, S21, AZS, DSP, RSP, IOS, WSP, TNM, TTP, TCL, CRC, TIN, AIN, CIN, GIN, TBI, TLI, TQI, TOU, AOU, COU, GOU, TBO, TLO, TQO, DIN, DOU, SDS, PRP, BDR, SPI, SC, SWI, BLW, PRS, BFC, SHP, SWP, CSP, UDT, TDT, DDT, SDT, IDT, FDT, RDT, EA21, CEN, AGG, LAY, …`
* `103`, `1` = **TTP, TCL** (freza asbob turi/klassi). `50`, `45` = R, DA (takror standartlari).
* `<CRC>` (indeks 50) = **CRC**; undan keyingi `9` = **TIN** (kirish turi) = `CorrectedLine`: asbob havoda korreksiya qilib, yuzaga perpendikulyar tushadi. Keyingi nollar: AIN, CIN, GIN, …, **TOU = 0** (chiqish turi = None: to'g'ridan-to'g'ri ko'tariladi).
* `5, 0, 20, 80, 60` = **DDT, SDT, IDT, FDT, RDT** — qirindi deflektori parametrlari (UDT=0, ya'ni o'chirilgan; BiesseWorks standart qiymatlari). Kirish/chiqishga aloqasi **yo'q**.
  * Dalil: «Ddt represents the safety distance between the chip deflector and the surface» — S3 `Rout.cs`.
* TIN/TOU kodlari (S3 `LeadInOutType`): 0 None, 1 Curve, 2 Line, 3 TgLineCurve, 5 Helix, 6 Curve3DLine, 7 Corrected3DLine, 8 Corrected3DCurve, 9 CorrectedLine, 14 Profile3D.
* START_POINT: `X, Y, Z`. LINE_EP: `XE, YE, ZS, ZE, SC, FD, SP, SOL, MVT`. ARC_EPCE: `XE, YE, XC, YC, DIR, ZS, ZE, SC, FD, SP, SOL`.
* ARC `DIR`: **1 = soat strelkasi bo'yicha (dirCW), 2 = teskari (dirCCW)** — S3 `CircleDirection`.

**Asbob korreksiyasi tomoni:**
* S3 `ToolCorrection`: **0 = Central, 1 = Right, 2 = Left** («Positions the tool axis to the right of the trajectory» = 1).
* Namunada XNC `c=1` → CRC `2`, `c=2` → CRC `1`. Demak XNC `c=1` Biesse nuqtai nazaridan **CHAP**, `c=2` — O'NG. Bu TPA (`c=1 → #40=1 = left`, 8-bo'lim) va Homag (`c=1 → WRKL`) bilan mos; `J_XNC_SPEC.md` dagi «1 — o'ng» yozuvi, ehtimol, xato.
* **Hal bo'lmagan ziddiyat [C]:** yoy yo'nalishi bo'yicha Biesse (`dir=true → 1 = CW`) va TPA (`dir=true → #34=1 = CCW`) teskari, ya'ni koordinata tizimlari bir-biriga oynali; shunda chap/o'ng ham almashishi kerak edi, lekin ikkalasida ham «chap». Yoki BppLib enumidagi nom, yoki o'qlar talqini noaniq — faqat stanokda/BiesseWorks simulyatorida tekshiriladi.

**Generator uchun:** baytlar O'ZGARMAYDI (namunaga aynan mos). Hujjatda: `5,0,20,80,60` → «deflektor standartlari» deb yozish; `in/out` boshqa qiymatlari uchun TIN (indeks 51) va TOU (indeks 58) maydonlari ishlatilishi kerakligi qayd etilsin (hozir `in=0,out=1` → TIN=9, TOU=0).

---

## 4. SCM Xilog (XXL/PGM)

> Diqqat: bu bo'limdagi ta'riflar **[B]** — «Xilog Plus Training 2014» va forum mavzulari qidiruv xulosasi orqali; hujjat sahifalari 403 berdi, matn so'zma-so'z tekshirilmagan.

### 4.1 XBO
**JAVOB (ishonch: o'rta) [B]:** `X`, `Y` — teshik koordinatalari; `Z` — chuqurlik; `D` — diametr; `N` — parma **turi**: `P` = brad (oddiy/ko'r), `L` = lance (o'tuvchi), `S` = countersink (zenkovka); `L` — zenkovka konusi balandligi (faqat `N=S`); `R` — teshiklar soni; `x`, `y` — qadamlar; `V` — podacha; `G` — bosqichlar soni (pecking).
* Dalil: «Brad=P, Lance=L, Countersink=S» — S8 (qidiruv xulosasi), shuningdek https://www.cnczone.com/forums/postprocessor-for-cam/421928-cnc-new-post.html
* `F` yuzlari: **1 = Top, 2 = Right, 3 = Left, 4 = Front, 5 = Back** — S8. Bizning jadval (`br`→2, `bl`→3, `bb`→4, `bt`→5) bilan mos.
* Qirra teshigida balandlik koordinatasi qaysi yuzadan — **TOPILMADI**.
* `N=L` qoidasi (Q3): `N` — asbob **turi**, chuqurlik mezoni emas. Ya'ni «`BoreTh*` asbob → L» talqini ta'rifga yaqinroq; `dp ≥ dz` — faqat namunadagi tasodifiy moslik. Ishonch: o'rta.

**Generator uchun:** SAQLASH; `N=L` ni **asbob turi** (o'tuvchi parma) bo'yicha qo'yish tavsiya etiladi — 16 mm detalda 17 mm `Bore5` teshigi `N=P` bilan chiqishi kerak (stanokda tasdiqlash).

### 4.2 XG0 / XL2P / XGIN / korreksiya
**JAVOB (ishonch: o'rta) [B]:**
* `XG0` — profil boshlanishi: `X, Y, Z`, `T` — freza asbobi nomeri («must be provided»), `V` — podacha, `S` — aylanish, `D` — xavfsiz Z, `F` — yuz, `C` — korreksiya.
* `C`: **0 = markazda (standart), 1 = traektoriyaning o'ng tomonida, 2 = chap tomonida** — S8.
* `XL2P X Y Z` — oxirgi nuqtadan berilgan nuqtagacha kesma.
* `XGIN`: `G` — kirish turi (**1 = to'g'ri chiziq, 2 = yoy**); `Q` — yaqinlashish (**0 = vertikal, 1 = qiya**); `R` — asbob radiusi ko'paytuvchisi (standart 2).
* Dalil: «C=1 (bit on the right of the path), C=2 (bit on the left)» — S8 (qidiruv xulosasi).
* Sarlavhadagi `T` — asbob emas: «Raise bars enable variable» [B].

**`T=-1` ma'nosi — TOPILMADI.** Forumda asbob makros parametri orqali beriladi (`XG0 ... T=pT`, `T=101`) — https://www.woodworker.de/forum/threads/xilog-plus-makro.8757/post-44181 [A]; `-1` «avtomatik tanlash» ekani hech qayerda yozilmagan.

**Paz eni / arra qanday berilishi (XGS va h.k.) — TOPILMADI.** Xilog Plus da arra uchun alohida instruksiya nomi ochiq manbada uchramadi; namunamizda paz `XG0 ... T=-1` + `G1` bilan chiqadi, ya'ni eni faqat asbob (T) orqali aniqlanadi.

**Kodlash — TOPILMADI.**

**Generator uchun:** SAQLASH (`XGIN Q=0 G=2`: vertikal yaqinlashish, yoy bilan kirish — ta'rifga mos). `C` raqamini o'zgarishsiz yozish: Xilog 1 = o'ng, TPA 1 = chap — bu Xilog o'qlari oynali ekani bilan izohlanadi (hujjatimizdagi faraz bilan mos), o'zgartirish kerak emas. `T=-1` bilan freza/arra stanokda ishlashi operator tomonidan tasdiqlansin; keng pazlar (6, 10.5 mm) bitta o'tishda arra qalinligida qolishi xavfi bor.

---

## 5. SCM Startech CN / CN V (ISO G-kod)

### 5.1 G81 (K, Q), G300 (K/J/I/Q), G200, G101
**JAVOB: TOPILMADI.** Startech CN boshqaruvining G-kod ta'rifi (G300, G200, G101, `K` yuz kodi, `Q` diametr) ochiq manbada yo'q. SCM broshyuralari va Bazis qo'llanmasi faqat sozlamalarni tavsiflaydi.

### 5.2 Stanok imkoniyatlari (frezalash bormi, arra yo'nalishi)
**JAVOB (ishonch: yuqori) [A]:**
* Arra **qo'zg'almas, X yo'nalishida** o'rnatilgan: Ø125 gacha, qalinligi 6 mm gacha (standart 5 mm) — S7. Shuning uchun `G300` da yo'nalish yozilmaydi — arra faqat X bo'ylab kesadi.
* Shpindellar: 7 vertikal + gorizontal 2 (X) + 2 (Y) — S7. **Freza elektroshpindeli standart komplektda yo'q.**
* Bazis-ChPU da «SCM Startech CN» postprotsessorida faqat ikkita sozlama bor: «Ширина пилы» va o'tuvchi teshik uchun «Дополнительная глубина» — S6 (10.37.2). Kontur frezalash sozlamasi yo'q → frezalash qo'llab-quvvatlanmaydi.
* «SCM Startech CN V» da: Операции, База инструментов, Отверстие, Продольный паз bo'limlari — S6 (10.37.3); bu yerda ham kontur frezalash bo'limi yo'q.
* `.ISO` dasturlarini USB orqali import qiladi [B] — https://rustan.ru/stanki/po-derevu/sverlilno-prisadochnye-stanki/scm/scm-startech-cn

**Generator uchun:**
* Frezalashni chiqarmaslik — TO'G'RI, SAQLASH (stanok cheklovi).
* **Tekshirish kerak:** hujjatimizda `G300` «Y bo'ylab» pazlar ham bor (`X136.250 Y1300.000 Q1300.000`). Arra faqat X bo'ylab kesgani uchun, yoki stanok X o'qi detalning boshqa o'lchamiga to'g'ri keladi, yoki Y-pazlar stanokda bajarilmaydi/detal burib qo'yiladi. Bitta sinov detali bilan aniqlash shart.
* Paz o'tish qadami 3 mm (arra 4 mm): Bazis da ham «arra eni» postprotsessor sozlamasi — ya'ni qadam postprotsessorda hisoblanadi, stanokda emas. Arra qalinligini (standart 5 mm, bizda 4 mm) profil parametri qilish tavsiya etiladi.

---

## 6. SCM MaestroCut (.XPrg/.XMix) va WinCut (.NNN)

**JAVOB (qisman, ishonch: o'rta-yuqori) [A]:** fayl formatining rasmiy tavsifi ochiq emas, lekin dastur muharriri kodlari SCM taqdimotida berilgan (S5):

| Kod | Ma'nosi |
|---|---|
| `P` | precut (dastlabki kesish) |
| `Y`, `X`, `U`, `V` | 1-, 2-, 3-, 4-daraja kesishlari, **inkremental** o'lcham |
| `R` (RY, RX, …) | har bir kesish darajasi uchun trim |
| `F` | bog'langan kesishlar: 2 ta X orasida turganda U kesish 2-panelda bajariladi |
| `C, CI, CC` | pazlar (ixtiyoriy) |
| `W, WC, WR, WCR` | teshiklar/slotlar (ixtiyoriy) |

* Dalil: «R = trim for each cut level (RY, RX,.....)» — S5.
* Dalil: «Cut quota from previous one or from panel edge if it is the first» — S5 (o'lcham inkremental).
* Cheklovlar: «Max. number of lines per programme: 100»; Mix ro'yxati ham 100 qatorgacha — S5.
* Moslik: MaestroCut «Maestro Ottimo Cut format» ni import qiladi va «Backward compatibility with Wincut programme» — S5.
* Material «grain» turlari: grainsiz / uzunasiga / ko'ndalangiga — S5.

**TOPILMADI:** `Campo1..Campo64` maydonlari ma'nosi, `AltPacco`, WinCut `[Righe]` dagi oxirgi 4 ta `0.0000`, `U*`/`V*` belgi qatorlari, `VelRotaz/VelAvanz`, kasr o'lcham formati, kodlash. (wooddesigner.org va atelierbois.net dagi «Postprocessor variables wincut» mavzulari bot-tekshiruvi sababli ochilmadi.)

**Generator uchun:** SAQLASH. Qo'shimcha tekshiruv qo'shish: bitta XPrg da 100 dan ortiq kesish qatori va XMix da 100 dan ortiq `RigaMix` bo'lmasligi (oshsa — bo'lish yoki ogohlantirish). `RY/RX` — daraja trimi ekani tasdiqlandi (qaysi biri `cTrimL`/`cTrimW` ga to'g'ri kelishi — hali ham ochiq).

---

## 7. Felder / Format4 kappa automatic (PC6/PC7, `MA000…MA999`)

**JAVOB: TOPILMADI.** `MA000/MA010/MA015/MA050/MA200/MA300/MA400/MA999` yozuvlari ta'rifi hech bir ochiq manbada yo'q (EN/DE/RU qidiruvlar natijasiz).

Faqat umumiy ma'lumot [B]:
* kappa automatic Ardis optimizatori bilan komplektlanadi; «ASCII-Export and Import» bor — https://www.felder-group.com/en-us/products/beamsaw-vertical-saw-c1960/pressure-beam-saw-beam-saw-horizontal-kappa-automatic-p583863
* «PC7000» — FORMAT4 / MAYER arralari uchun yangi boshqaruv; «kappa automatic classic» bundan mustasno — https://www.felder-group.com/en-us/service/downloads (pc6 = eski PC6000, pc7 = PC7000 degan talqinga mos — hujjatdagi pc7 11-savolga qisman javob).

**Generator uchun:** O'ZGARTIRMASLIK; ikkala formatni (PC6, PC7) saqlash — tanlov stanok boshqaruvi avlodiga bog'liq.

---

## 8. TPA EdiCad / TpaCAD (`.tcn` / `.CNC` matn formati)

Ikkita rasmiy hujjat (S1, S2) formatni to'liq tavsiflaydi. Ishonch: **yuqori** [A].

### 8.1 `W#81` — teshik
| Param | Ma'nosi (S1/S2) |
|---|---|
| `#1`, `#2` | qo'llash nuqtasining X, Y koordinatasi (tomon lokal tizimida) |
| `#3` | Z chuqurlik koordinatasi (detal ichida — manfiy) |
| `#1002` | asbob diametri («Tool Diameter») |
| `#1001` | **asbob turi («Tool type»)** — o'tuvchilik bayrog'i emas, parma turi |
| `#201/#203/#205` | mashina / guruh / asbob (asbob berilsa, diametrdan ustun) |
| `#8015` | 0 = absolyut (standart), 1 = nisbiy |
| `#2005, #2002, #9012, #9013` | kirish tezligi, aylanish, sekinlashish nuqtalari |

* Dalil: «#1002= Tool Diameter … #1001= Tool type» — S1.
* `#1001` qiymatlari jadvali (0/1/…) hujjatda yo'q; namunalarda `#1001=1`. Bizdagi «1 = o'tuvchi parma, 0 = oddiy» talqini «asbob turi» ta'rifiga mos, lekin qiymatlar stanok asboblar jadvaliga bog'liq.

### 8.2 `W#89` — freza sozlash (setup)
* `#40` — **korreksiya: 1 = chap, 2 = o'ng, 0 = yo'q**.
  * Dalil: «1 for left compensation, 2 for right compensation, 0 for no required» — S1.
* `#36` — **korreksiya radiusi** (kirish turi EMAS).
  * Dalil: «#36= Compensation radius (if not set: will be used the radius of the tool)» — S2.
* `#1001` setup da 100 bo'lishi kerak, `#205` — asbob (S2, Format4 mashinalari uchun).
* Tomon ta'rifi: «the left side corresponds to the compensation outside the rectangle» (profil yo'nalishi bo'yicha) — S1.

### 8.3 `W#2201` (chiziq) / `W#2101` (yoy)
* `#1, #2, #3` — oxirgi nuqta; `#31, #32` — markaz, **yoy boshlanish nuqtasiga nisbatan**; `#34` — **0 = soat strelkasi bo'yicha (standart), 1 = teskari**.
  * Dalil: «#34= Direction of rotation of the arc: 0 if it's clockwise» — S1.

### 8.4 `W#1050` / `W#1051` — arra pazi (X / Y bo'ylab)
| Param | Ma'nosi (S2) |
|---|---|
| `#8510` | boshlanish X |
| `#8511` | Y pozitsiya |
| `#8517` | (1050) oxirgi X |
| `#8518` | (1051) oxirgi Y |
| `#8512` | Z chuqurlik |
| `#8509` | arra turi (Sawtype) |
| `#6` | yuz tanlash (=1) |
| **`#8503`** | **kesim eni**: 0 = bitta o'tish; arra qalinligidan keng bo'lsa — kerakli en |
| **`#8514`** | **Mashina** (=1) — en emas |
| **`#8515`** | **Guruh** (=1) — o'tishlar soni emas |
| `#8516` | asbob ID (arra) |
| `#8525` | korreksiya: 1 chap, 2 o'ng, 0 yo'q |
| `#8526` | 1 = ikki bosqichda kesish (`#8513` — 2-bosqich chuqurligi) |
| `#8527` | 1 = boshlanish nuqtasi uchun arra xordasini hisobga olish |
| `#8098` | ishlatiladigan makros (`..\custom\mcr\lame.tmcr`) |

* Dalil: «#8503= Width of saw-cut (if only one cut = 0 …)» — S2.
* Dalil: «#8514= Machine (has to be =1) … #8515= Group» — S2.
* Arra qalinligi faylga yozilmaydi — asbob jadvalidan (`#8516`) olinadi.

**MUHIM:** bizning chiqishda `#8503` **yo'q** → stanok har doim arra qalinligida bitta o'tish qiladi; 6 va 10.5 mm pazlar tor chiqadi (TPA hujjatidagi 1-ochiq savolning javobi).

### 8.5 Tomonlar va qirra teshigining Z bazasi
* Tomonlar: 1 ustki, 2 ostki, 3 old, 4 o'ng, 5 orqa, 6 chap — S1/S2.
* Detal absolyut tizimi: bosh — chap-quyi burchak, Y ichkariga, **Z yuqoriga**; 1-tomon boshi `(0;0;s)`, 2-tomon `(0;0;0)`.
* 3/5-tomon: lokal X = detal X, **lokal Y = detal Z**; 3-tomon boshi `(0;0;0)`, 5-tomon `(0;h;0)`.
* 4/6-tomon: lokal X = detal Y, **lokal Y = detal Z**; 4-tomon boshi `(l;0;0)`, 6-tomon `(0;0;0)`.
  * Dalil: «Y axis has same orientation and direction of Z axis of ARS» — S2.
* Demak qirra teshigida `#2` **ostki yuzadan (stol tomondan) yuqoriga** o'lchanadi.
* OEM lokal tizimni o'zgartirishi mumkin: «CAD can be configured to change the local systems of real faces» — S2.
* Sarlavha: `TPA\ALBATROS\EDICAD\xx.xx` (00 EDICAD, 01 TPAEDI32, 02 TPACAD); kodlash belgisi `code=ansi` — S2 → kirill uchun ANSI (cp1251) [C].

**Generator uchun:**
1. `#40`: xarita (`c=1 → 1`, `c=2 → 2`) SAQLANADI; hujjatda «1 = chap, 2 = o'ng» deb yozilsin. `J_XNC_SPEC.md` dagi «XNC c=1 — o'ng» TUZATILSIN (TPA, Biesse, Homag uchalasi «chap» deydi).
2. `#36`: «korreksiya radiusi = freza diametri / 2» deb qat'iylashtirish (faraz tasdiqlandi); boshqa freza uchun `d/2`.
3. **O'ZGARTIRISH (tavsiya, stanokda sinov bilan):** paz eni `t` > arra qalinligi bo'lsa `#8503=<t>` qo'shish; ixtiyoriy ravishda `#8516=<arra ID>`. Diqqat: S2 — Format4 (Felder) mashinalari uchun; «Genesis Evolution» OEM makrosi `#8503` ni qo'llashi stanokda tekshirilsin. Muqobil — Startech kabi bir necha parallel `W#1050` o'tish.
4. Qirra teshigi `#2 = dz − z`: SAQLASH (agar XNC `z` ustki yuzadan o'lchansa — TPA bazasi ostki yuza ekani tasdiqlandi).
5. `#34`: `dir=true → 1` = CCW, `false → 0` = CW — SAQLASH.

---

## 9. Qirra (gorizontal) teshiklarda Z qaysi yuzadan o'lchanadi

| Format | Javob | Ishonch | Dalil |
|---|---|---|---|
| **TPA TpaCAD/EdiCad** | **Ostki yuzadan (stoldan) yuqoriga** — lokal Y = detal Z, bosh `z=0` | yuqori [A] | S1, S2 (8.5-band) |
| BiesseWorks BPP | TOPILMADI | — | S3 da faqat «Z = ishlov tekisligining siljishi» |
| SCM Xilog | TOPILMADI | — | S8 da yuzlar raqami bor, bazasi yo'q |
| SCM Startech CN | TOPILMADI | — | — |

Bilvosita [C]: namunalarimizda TPA va Xilog ikkalasida ham `dz − z` yozilgan (TPA bazasi ostki yuza ekani isbotlangan) → XNC `z` **ustki yuzadan** o'lchanadi va Xilog ham ostki yuzadan hisoblaydi degan xulosa izchil. Shunda Startech (`X8` = `z` o'zgarishsiz) va Biesse (`Y = z` o'zgarishsiz) **ustki yuzadan** o'lchaydi degan faraz kelib chiqadi — lekin bu hujjat bilan tasdiqlanmagan.

**Generator uchun:** O'ZGARTIRMASLIK; 18 mm detalda `z=8` li bitta sinov teshigi (3166 `14_017`) Startech va Biesse da o'lchab tasdiqlansin.

---

## Tavsiya etilgan o'zgarishlar (qisqa ro'yxat)

| # | Fayl | O'zgarish | Turi |
|---|---|---|---|
| 1 | `tpa-genesis-evolution-8-9.md` + generator | `#8503=<paz eni>` qo'shish (eni > arra qalinligi bo'lsa); `#8514/#8515` = mashina/guruh deb tuzatish | **kod (sinov bilan)** |
| 2 | `tpa-…md` | `#40`: 1 = chap, 2 = o'ng; `#36` = korreksiya radiusi; `#1001` = asbob turi; `#34`: 0 CW / 1 CCW | hujjat |
| 3 | `biesse-works-v3.md` + kod nomlari | BG indeks 36 `THR` → **`TTP`** (asbob turi); haqiqiy THR = indeks 7 | hujjat/nom |
| 4 | `biesse-works-v3.md` | CUT_G: `<SAW>` = TH, `<W>` = TTK, `201/2` = TTP/TCL, korreksiya = indeks 54; ROUT: `9` = TIN, `5,0,20,80,60` = deflektor | hujjat |
| 5 | `J_XNC_SPEC.md` | XNC `c=1` — **chap** (o'ng emas) | hujjat |
| 6 | `scm-xilog-v3.md` | `N` = parma turi (P/L/S) — `N=L` ni asbob turidan aniqlash; `XGIN G/Q` ta'riflari | hujjat (+kod qoidasi) |
| 7 | `scm-startech-cn-v.md` | arra faqat X bo'ylab; Y-pazlarni stanokda tekshirish; arra qalinligini profil parametri qilish | sinov / profil |
| 8 | `scm-maestrocut.md`, `scm-wincut.md` | 100 qator cheklovi tekshiruvi; P/Y/X/U/V/R/F ta'riflari | kod (validatsiya) + hujjat |
| 9 | `biesse-selco-*.md` | Kod 1/2/4/5/Z1/Z2/W ta'riflari; `TechnoParam` = mashina parametri nomerlari (profilga chiqarish) | hujjat / profil |

---

## JAVOB TOPILMADI

1. **Selco OSI `Cut@Chk`** — algoritm va OSI tekshirishi.
2. **`TechnoParam` 320–335** — har bir ID ning aniq nomi (faqat mexanizm ma'lum).
3. **Selco NC300** — `B_REF` maydonlari (`ROL, RMADL, RMIDL, ROT, RMADT, RMIDT, RMIP`), `VL`, `VT`, `HP`, `CPI`, `PROX`, `ESE`, `OPZ`; `B_LABEL` majburiyligi; `crc16/crc32`; `rest.fme`.
4. **BiesseWorks** — SIDE kodlarining rasmiy jadvali, CRN "1".."4" burchaklari geometriyasi, qirra teshigida Y bazasi (ustki/ostki), CRC chap/o'ng bilan yoy yo'nalishi orasidagi ziddiyat.
5. **Xilog** — `T=-1` ma'nosi; arra/paz eni qanday berilishi; qirra yuzlarida balandlik bazasi; `XGOUT` parametrlari; sarlavha binar maydonlari; kodlash; `R=` vazifasi. (4-bo'limdagi barcha ta'riflar faqat [B] darajada.)
6. **Startech CN** — `G81 K/J/I/Q`, `G300 K0 J2 I0`, `(…)G200`, `(…)G101` ning rasmiy ta'rifi; 99 dastur cheklovi.
7. **MaestroCut/WinCut** — `Campo1..64`, `AltPacco`, `[Righe]` oxirgi 4 maydon, `U*/V*` qatorlari, `VelRotaz/VelAvanz`, kasr o'lcham formati, kodlash, `GibLabLabel` majburiyligi.
8. **Felder PC6/PC7** — barcha `MA0xx…MA999` yozuvlari ta'rifi.
9. **TPA** — `#1001` qiymatlari jadvali; «Genesis Evolution» OEM makrosida `#8503` qo'llanishi (Format4 hujjatidan olingan).
10. **Kirill kodlashi** — barcha formatlar uchun (TPA dan tashqari: `code=ansi`).

### Ochilmagan, lekin foydali bo'lishi mumkin bo'lgan manbalar (foydalanuvchi brauzerda ko'rishi mumkin)
* Xilog Plus Training 2014 — https://pdfcoffee.com/xilog-plus-traning-2014-1-2-pdf-free.html
* Xilog Plus «Editor» qo'llanmasi (IT) — https://it.scribd.com/document/1044949641/Editor-it
* Routech — Xilog Basic Programming Instructions — https://www.cnczone.com/forums/postprocessor-for-cam/421928-cnc-new-post.html
* Selco XML namunalari (OptiCut XML/XML2, zip) — https://www.cnczone.com/forums/biesse/471040-biesse-selco-eb80-xml-import.html
* Biesse Selco XML interface — https://wooddesigner.org/forum/opticut-optinest/biesse-selco-saw-xml-interface-and-integration-with-opticut/
* WinCut postprotsessor o'zgaruvchilari — https://wooddesigner.org/forum/opticut-optinest/postprocessor-variables-wincut/
* BiesseWorks Instructions for Use — https://pdfcoffee.com/biesseworks-instructions-for-use-pdf-free.html
* Biesse CIX Macro Configuration Guide — https://www.scribd.com/document/564782657/BIESSE-CIX-1
