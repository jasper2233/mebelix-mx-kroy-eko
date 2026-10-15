# WEB tadqiqot: hali ochiq manbasi topilmagan stanok formatlari

> Sana: 2026-10-04. Usul: WebSearch / WebFetch (EN, RU, IT, DE, ZH, TR so'rovlari), ochiq PDF qo'llanmalar matni,
> GitHub ochiq kodi (kod qidiruvi va `raw` fayllar). Login qilinmadi, bajariluvchi fayl yuklanmadi.
> Avvalgi uchta hujjatda (`WEB_asia_formats.md`, `WEB_homag_holzma_schelling.md`, `WEB_biesse_scm_felder_tpa.md`)
> bor narsalar bu yerda takrorlanmaydi — faqat havola beriladi.
>
> **Ishonch darajasi:** **yuqori** = ishlab chiquvchi hujjati yoki ishlaydigan ochiq kod/namuna fayl o'qildi;
> **o'rta** = uchinchi tomon (boshqa CAM, forum) matni o'qildi; **past** = faqat qidiruv parchasi yoki mantiqiy xulosa.
> Parchalar — ochiq manbalardan, manbasi ko'rsatilgan; hech bir sintaksis o'ylab topilmagan.
>
> **Ochilmagan saytlar** (bot-tekshiruv / 403 / ulanish uzildi — aylanib o'tilmadi): wooddesigner.org (OptiCut va PolyBoard
> yordam sahifalari), cncarena / cnczone / industryarena, forums.autodesk.com, scribd.com, mecsoft.com, technodocbox.com, CSDN.
> Ularning ro'yxati oxirida — foydalanuvchi brauzerda o'zi ko'rishi mumkin.

## Yig'ma jadval

| # | Format | Natija | Eng foydali manba |
|---|---|---|---|
| 1 | KDT PreSize `.qk` / `.lbd`, versiyalar | **topilmadi** (faqat atrof-faktlar) | Promob Cut Pro «Giben‑KDT Presizing» (PTX) |
| 2 | FastPanel `.ocm` 2.1.4 / 2.1.5 | **topilmadi** | — |
| 3 | Scheer («Pa») | **topilmadi** | — |
| 4 | Holzma CADmatic 3 `.SPL`, CADmatic 4 `.LC4` | **topilmadi** (ichki format); `.saw` yo'li — qisman | Magi‑Cut Interface Guide (CADlink) |
| 5a | Giben G‑Drive `.DAX` / `.CPX` | **topilmadi**; muqobil `.AC` formati — **yaxshi topildi** | GibenAmerica «AC File Format» |
| 5b | Biesse Selco NC300 (`dist` / `tagli`) | **qisman** (ochiq namuna + kodlar) | tecnocom forum mavzusi |
| 6 | Felder F4Classic `PR_*` kalitlari | **topilmadi** | — |
| 7 | Masterwood MW310 | **qisman–yaxshi** (ISO dastur sarlavhasi, G‑kodlar ro'yxati, kengaytmalar) | FreeCAD muhokamasi #25829, BAZIS‑ЧПУ |
| 8 | IMA ImaWop `.fmc` | **qisman** (2.6 versiya bloklari; teshik makrosi yo'q) | GitHub `Raynover/Frustify` |
| 9 | Holz‑Her NC‑HOPS `.hop` | **yaxshi topildi** | GitHub `saschpe/vscode-nc-hops`, `apers0/nc-hops` |
| 10 | AES Sirius G‑kod | **topilmadi** (faqat dasturiy ta'minot haqida faktlar) | diler sahifalari, BAZIS‑ЧПУ |
| 11 | Vitap Bridge / Point `.tcn` | **qisman** (TpaCAD formati ma'lum + ochiq `.tcn` namunasi; Vitap makroslari yo'q) | GitHub `.tcn` namunalar, BAZIS‑ЧПУ |
| 12 | Xitoy 6 tomonli stanoklarining «G CODE»i | **topilmadi** | — |

---

## 1. KDT «KDT‑PreSize»: `.qk` / `.lbd`, XML import, versiyalar

**Natija: topilmadi (format va versiya farqlari bo'yicha ochiq hujjat yo'q).**

Topilgan faktlar:

* PreSize uchun tashqi optimizatorlar ishlatadigan rasmiy almashinuv yo'li — **PTX**. Promob Cut Pro'ning
  «Giben / KDT Presizing» plagini `.ptx` yozadi; sozlamalarida «fayl versiyasi», fayl nomining maksimal uzunligi
  (minimum 5 belgi; `0` — cheklovsiz), «ruxsat etilgan fazalar» va «stanokning maksimal fazalari» bor (o'rta).
  Manba: https://suporte.promob.com/hc/en-us/articles/31117683705745
* Demak daraja (faza) chegarasi format konstantasi emas — stanok/dastur versiyasiga qarab **sozlanadi** (o'rta, xulosa).
* BAZIS‑Раскрой'da KDT uchun uch postprotsessor («KDT пильный центр (txt)», «KDT ФРС (XML)», «KDT пильный центр (XML)»)
  va alohida «ZD Presize» bor; qo'llanmada faqat papka/etiketka sozlamalari, fayl tuzilishi yo'q (o'rta).
  Manba: https://cdn.bazissoft.ru/documentation/ru/Cutting.pdf (10.36–10.38, 10.42)
* Dasturiy ta'minot kataloglarida PreSize versiyalari 1.2 / 1.6 / 1.7 / 1.8 / 2.9 deb ko'rsatilgan; `V1.4.0P`, `V3.3.0P`,
  `V4.x`, `V6.3.2P` belgilari hech bir ochiq manbada uchramadi (past).
  Manba: https://kdt-presize.software.informer.com/versions/
* `.qk`, `.lbd` kengaytmalari va ularning versiyalararo farqi (2 720 032 / 2 920 032 baytli massiv) — **hech qayerda yo'q**.

Sinab ko'rilgan so'rovlar: `KDT Presize 开料锯 导入 文件格式 qk lbd`; `KDT 极东 电子锯 PreSize 软件 版本 V6.3 …`;
`"KDT-PreSize" "V6.3" OR "V4.0" OR "V3.3.0P" OR "V1.4.0P"`; `KDT PreSize версия … импорт карт раскроя`;
GitHub kod qidiruvi `KDT presize qk`.

**Generator uchun:** `.qk/.lbd` — faqat namunaga mos holda qoladi; versiya tanlovi (eski/yangi massiv hajmi) foydalanuvchi
sozlamasi bo'lsin. Hujjatlangan zaxira yo'l — PTX (bizda generator bor).

---

## 2. FastPanel `.ocm` (ManualPattern XML): 2.1.4 va 2.1.5, daraja chegarasi

**Natija: topilmadi.** «FastPanel» so'zi qidiruvda faqat xosting boshqaruv paneliga olib boradi; `ManualPattern`, `TrimSize`,
`.ocm` bo'yicha na hujjat, na forum, na ochiq kod bor (GitHub kod qidiruvi ham bo'sh).

So'rovlar: `"ManualPattern" "TrimSize" xml panel saw ocm`; `"FastPanel" пильный центр постпроцессор раскрой .ocm`;
`"Fast Panel" beam saw software ocm import`; GitHub: `ManualPattern TrimSize`, `ManualPattern ocm`.

**Generator uchun:** 2.1.4 / 2.1.5 farqi va «3 burilish» chegarasi faqat stanokdagi dasturning o'zidan aniqlanadi
(stanokda qo'lda 4 darajali karta chizib saqlash — eng tez sinov). Hozirgi cheklov (≤ 3) saqlansin.

---

## 3. Scheer («Pa») import fayli

**Natija: topilmadi.**

* Scheer arralari 1990‑yillar o'rtasidan «PA» seriyasi nomi bilan chiqqan; firma 2010‑yilda bankrot bo'lgan, seriyani
  boshqa firma davom ettirgan (o'rta). Manba: https://wtp.hoechsmann.com/en/lexikon/33361/scheer_pa
* Ikkilamchi bozor e'lonlarida optimizatsiya dasturi «ASCII import» opsiyasi bilan tilga olinadi (past, qidiruv parchasi) —
  format tavsifi yo'q.
* Magi‑Cut, Promob Cut Pro, Microvellum, BAZIS‑Раскрой postprotsessor ro'yxatlarida Scheer **yo'q**.

So'rovlar: `Scheer panel saw … import file format "Pa" OR "PA 6000"`; `Scheer Plattensäge Schnittplanübernahme Dateiformat`.

**Generator uchun:** namuna faylsiz hech narsa qilib bo'lmaydi (README'da ham «namuna yo'q»). Stanok bo'lsa — undagi
dasturdan bitta eksport/namuna fayl kerak.

---

## 4. Holzma / Homag CADmatic 3 `.SPL` va CADmatic 4 `.LC4`

**Natija: ichki tuzilish topilmadi; rasmiy tashqi yo'l (PTX → `.saw`) bo'yicha qo'shimcha cheklovlar topildi.**
(Asosiy faktlar `WEB_homag_holzma_schelling.md` 2‑savolda; quyida faqat yangilari.)

Manba: Magi‑Cut «Version 8 Interface Guide rev 1.18», Cadlink bo'limi —
https://www.magi-cut.co.uk/files/v82%20interface%20guide.pdf (yuqori)

* Cadlink PTX dagi har bir `JOBS` yozuvidan bittadan `.saw` fayl yaratadi; **fayl nomi = ish (job) nomi**.
* Cadlink xato kodlari cheklovlar borligini ko'rsatadi: «juda ko'p ish / detal turi / list turi / karta / kesim»
  (3–8‑kodlar) — aniq sonlar berilmagan.
* Kirish PTX fayli nomi ≤ 50 belgi, to'liq yo'l ≤ 150 belgi; UNC yo'llar ruxsat etilmaydi.
* `.saw` ga detal ma'lumoti «information box» lar sifatida o'tadi: sukut bo'yicha 60 ta `PARTS_UDI` + 28 ta `PARTS_INF`
  maydoni (jami 88), tartibi `/INF`, `/UDI` kalitlari bilan boshqariladi.
* Qo'shimcha optimizatsiya / arra / material / shtabel parametrlari `.prm`, `.spm`, `.mpm`, `mdestack.ctl` fayllaridan olinadi.
* Magi‑Cut arra modellari ro'yxatida 21‑model bitta: «CADmatic 1/2/3/4/5 / Giben‑Optilink / Selco‑CRLINK» — ya'ni bu uch
  oila bir xil pattern uzatish mantig'i bilan xizmat ko'rsatiladi (yuqori).
  Manba: https://www.magi-cut.co.uk/files/html/V12webhelp/sawno.htm
* BAZIS‑Раскрой'da «Holzma» va «Holzma CadLink3» postprotsessorlari **PTX** yozadi (CADLink versiyasi, kodlash,
  `PARTS_UDI` opsiyasi, fayl nomida qat'iy belgi soni sozlamalari) — `.SPL`/`.LC4` ni to'g'ridan‑to'g'ri yozmaydi (o'rta).
  Manba: https://cdn.bazissoft.ru/documentation/ru/Cutting.pdf (10.32–10.33)
* `.SPL`, `.LC4` bo'yicha: hech bir ochiq tavsif, namuna yoki kod yo'q (GitHub kod qidiruvi ham bo'sh). Daraja chegarasi (4)
  tasdiqlanmadi.

So'rovlar: `Holzma CADmatic 3 ".saw" file format PTN3 PTNR`; `"CADmatic" ".spl" OR ".lc4" OR ".saw" Holzma импорт раскроя`;
GitHub: `extension:spl holzma`, `extension:lc4`.

**Generator uchun:** o'zgarishsiz. Yangi validatsiya g'oyasi: PTX fayl nomi ≤ 50 belgi (Cadlink talabi).

---

## 5a. Giben G‑Drive `.DAX` / `.CPX`

**Natija: `.DAX`/`.CPX` topilmadi. Lekin Giben'ning hujjatlangan import formati — `.AC` (+ `.AD`) — topildi.**

### 5a.1 Giben `.AC` (yuqori — Giben America hujjati)

Manba: https://www.woodweb.com/images_forums_public/cnc/AC_File_Format.pdf ;
muhokama: https://woodweb.com/cgi-bin/forums/cnc.pl?printfriendly=&rev=804597

`.AC` — bitta material uchun kesish kartalari; ASCII, ajratuvchisiz, **qat'iy pozitsiyali**. Birinchi ikki maydon
(material, qalinlik) barcha qatorlarda bir xil bo'lishi shart.

Sarlavha qatori (HEADLINE, kalit `1`):

| Pozitsiya | Maydon |
|---|---|
| 1–15 | material turi (ixtiyoriy) |
| 16–18 | qalinlik (1/10 mm) |
| 19–20 | karta raqami |
| 21 | yozuv kaliti = `1` |
| 22–26 | listlar soni |
| 27–31 | list uzunligi (1/10 mm) |
| 32–36 | list eni (1/10 mm) |
| 37 | bosh kesim trimi: `0` yo'q / `1` ha |

Kesim qatori:

| Pozitsiya | Maydon |
|---|---|
| 1–15, 16–18, 19–20 | material, qalinlik, karta raqami (sarlavhadagidek) |
| 21 | kalit: `2` bosh kesim, `3` rip (bo'ylama), `4` ko'ndalang, `5` z‑kesim |
| 22–23 | detal raqami |
| 24–28 | kesim o'lchami (1/10 mm) |
| 29–30 | kesim soni |

Hujjatdagi namunadan uch qator (material `PARTICLE BOARD`, 19.2 mm, 1‑karta):

```
PARTICLE BOARD 1920110050024832125440
PARTICLE BOARD 192012002483201
PARTICLE BOARD 192013000614402
```

Cheklovlar (formatdan kelib chiqadi): **daraja kodlari faqat 2…5 → maksimal 4 daraja** (bosh, rip, ko'ndalang, z);
karta raqami 2 xonali (≤ 99), detal raqami 2 xonali (≤ 99), kesim soni ≤ 99, o'lcham ≤ 9999.9 mm.

* Yangi G57 uchun qator 37 emas, 100+ belgidan iborat «yangi» `.AC` talab qilinadi — uning tavsifi ochiq emas (o'rta;
  o'sha WoodWeb mavzusi).
* `.AD` — partiya uchun detal/list (inventar) fayli; «optional» detal (kalit 3) va «rest» list (kalit 5) yozuvlari bor;
  sarlavhasida optimizatsiya va arra parametr fayllari nomi turadi (yuqori).
  Manba: https://www.magi-cut.co.uk/files/html/V12webhelp/mct1066.htm
* Arra parametrlari `.AC`/`.AD` ichida yo'q; Magi‑Cut ularni alohida satrda oladi: arra qalinligi / old rip trim / orqa rip
  trim / old ko'ndalang trim / orqa ko'ndalang trim / bosh kesimdan keyingi retrim, `/` bilan, 0.1 mm da, har biri ≤ 999 (yuqori).
* Promob Cut Pro: G57 «faqat `*.AC`» bilan ishlaydi; GVision / GDriveRT / GDriveQ / GVisionXP uchun `*.FST`, `*.FDT2AD`,
  `*.AD`, `*.bmp` (etiketka ma'lumoti); fayl nomi uzunligi: Optisave — **6**, GVision — **60** belgi; GVision etiketka
  maydoni ≤ 489 belgi (o'rta). Manba: https://suporte.promob.com/hc/en-us/articles/31120880969617
* Microvellum: Giben uchun CPOUT yoziladi, uni arra formatiga Giben'ning «Optilink» dasturi o'giradi; yangi «GDrive»li
  arralarda `.AC` o'rniga `.AD` talab qilingani haqida foydalanuvchi shikoyati bor, format berilmagan (o'rta).
  Manbalar: https://community.microvellum.com/portal/en/kb/articles/microvellum-saw-connections-reference ,
  https://community.microvellum.com/portal/en/community/topic/giben-ad-file

### 5a.2 `.DAX` / `.CPX`

Hech bir manbada uchramadi (EN / IT / RU so'rovlar, GitHub kodi). `0xFC` ekranlash, 8 belgili nom va 3 darajali cheklov
tasdiqlanmadi. Yagona bilvosita ishora: eski Optisave oilasida nom 6 belgigacha — ya'ni Giben kontrollerlarida qisqa nom
cheklovi odatiy hol (past, xulosa).

So'rovlar: `Giben G-Drive import cutting patterns file format`; `Giben ".AC" file format panel saw`;
`magi-cut "Giben" saw transfer "Optisave" OR "G-Drive"`.

**Generator uchun:** (1) `.DAX/.CPX` — o'zgarishsiz; (2) **yangi generator nomzodi — Giben `.AC` (eski 37 belgili)**:
to'liq hujjatlangan, sodda; G57 / Optisave oilasi uchun muqobil. Cheklovlar: ≤ 4 daraja, ≤ 99 karta, ≤ 99 detal turi —
oshsa xabar. Yangi (100+ belgili) `.AC` uchun stanokdan namuna kerak.

---

## 5b. Biesse Selco NC300 (`dist` / `tagli`)

**Natija: qisman — ochiq namuna va kesim kodlari topildi; teglarning rasmiy tavsifi yo'q.**

Manba (o'rta — foydalanuvchi forumi, OptiPlanning eksporti namunasi):
https://forum.tecnocom-ug.ru/viewtopic.php?t=3589 (sayt sertifikati muddati o'tgan)

OptiPlanning'ning «NC300/NC500» eksporti — o'qiladigan matn. Forumdagi namunadan (qisqartirilgan):

```
B_SCH
B_DAT
	NM="4.001"
	MAT="MDF-16                 "
	X=250000
	Y=200000
	Z=1600
	HP=9000
	VL=0
	VT=0
E_DAT
B_CUT
	CUT=1
		COD="1"
		DIM=15000
		QTA=2
	CUT=2
		COD="2"
		DIM=40000
		QTA=4
E_CUT
E_SCH
```

Bundan ko'rinadiganlar:

* Birlik — 1/100 mm (`X=250000` = 2500 mm, `Z=1600` = 16 mm); bizning tavsifimiz bilan mos.
* `B_DAT` da `NM` (karta nomi `<raqam>.<NNN>`), `CMM`, `MAT` (bo'shliq bilan to'ldirilgan), `DAY`, `OPZ`, `X`, `Y`, `Z`,
  `HP`, `VL`, `VT`; `B_CUT` da `CUT=n` → `COD`, `DIM`, `QTA`.
* `HP=9000` (90.00 mm) — paket balandligi bo'lishi ehtimoli katta (past, xulosa; rasmiy izoh yo'q).
* Bu namunada **`B_REF` va `B_LABEL` bloklari yo'q** — ya'ni OptiPlanning'ning o'zi ularsiz ham fayl chiqaradi. Bu
  «`B_LABEL` majburiymi?» savoliga bilvosita «yo'q» javobi (o'rta).
* `COD` qiymatlari: `1`, `2` (bosh kesimli karta) va `4`, `5` (bosh kesimsiz) — OSI kodlari bilan bir xil; forumda `Z1` ham
  tilga olinadi. Kod ma'nolari — `WEB_biesse_scm_felder_tpa.md` 1.3‑band.
* Forum muallifi qayd etgan ikki xususiyat (OptiPlanning eksporti yoki format xulqi): kartada avval 4/5, keyin 1/2 kesimlar
  kelsa — eksportda tartib almashib qoladi; oldingi `4` kesimlar uchun bir xil bo'lgan `5` kesimlar **takrorlanmaydi**
  (tashlab ketiladi). Ikkinchisi bizning generator uchun muhim: bir xil ko'ndalang kesimli qo'shni polosalar qanday
  yozilishini namunalar bilan solishtirish kerak (o'rta).
* OptiPlanning'da uzatish turi «NC500 yoki NC300» deb tanlanadi (past, qidiruv parchasi) — ikkalasi bir oila.

Topilmadi: fayl nomi 8.3 cheklovi (bizdagi «NOME = 8 belgi» kuzatuvi tasdiqlanmadi ham, rad etilmadi ham), `B_REF` teglari,
`VL`/`VT`, daraja chegarasi (kodlar ro'yxatidan: 1, 2, Z1, Z2 yoki 4, 5, Z1, Z2 → **4 daraja**, OSI qo'llanmasidagi kabi — o'rta, xulosa).

So'rovlar: `Selco "NC300" … file "dist" "tagli"`; `форум Selco NC300 импорт раскроя`; `magi-cut "Selco" "NC300"`; GitHub:
`B_CUT B_LABEL B_REF`, `Selco NC300 tagli`.

**Generator uchun:** `B_LABEL` ni ixtiyoriy opsiya qilish mumkin (OptiPlanning namunasi ularsiz); stanokda bitta sinov bilan
tasdiqlansin. Darajani 4 bilan cheklash (Z2 dan chuqur kod yo'q).

---

## 6. Felder F4Classic `.txt` (`PR_VERSIONE`, `PR_NOME`, `PR_DIMX`, `PR_TIPO`, `PR_NPCAR`, `PR_TAGLI`)

**Natija: topilmadi.** Kalit nomlari qo'shtirnoqda hech bir manbada chiqmadi (veb va GitHub kod qidiruvi). Qaysi
kontroller/dastur ekanini aniqlab bo'lmadi; `PR_TIPO`, `PR_NPCAR` ma'nosi va `R<n>` takror belgisi qoidasi ochiq qoldi.

Atrof‑faktlar:

* BAZIS‑Раскрой'da aynan shu nomli alohida postprotsessor bor — «Felder F4 Clasic» (PC7000, «Felder пильный центр (May)»
  va «Felder (ФРС)» dan alohida); sozlamalari faqat papka va «detal etiketkasini bosish» — format tavsifi yo'q (o'rta).
  Manba: https://cdn.bazissoft.ru/documentation/ru/Cutting.pdf (10.21)
* Promob Cut Pro'da Felder uchun ikki plagin: «PC7000» va «PC5100/PC6200»; PC7000 da ajratuvchi `§§`, 10 ta matn ustuni
  (TEXT 1…10 ↔ 20–29‑ustunlar), «ruxsat etilgan fazalar» sozlamasi (o'rta) — bizning `felder-pc7.md` bilan mos.
  Manba: https://suporte.promob.com/hc/en-us/articles/31118460011793
* Felder sahifasiga ko'ra «kappa automatic classic» Ardis optimizatori va «ASCII export / import» bilan keladi (o'rta).
* Kalitlarning italyancha ekani (versione, nome, tagli) — dastur italyan ishlab chiquvchiniki ekaniga ishora; `NPCAR` —
  «numero pannelli caricati/da caricare» (yuklanadigan listlar soni) bo'lishi mumkin — **lingvistik taxmin, manbasiz** (past).

So'rovlar: `"PR_VERSIONE" "PR_NOME" "PR_DIMX"`; `"PR_NPCAR" OR "PR_VERSIONE" OR "PR_DIMX" OR "PR_TAGLI" txt`;
`"PR_TAGLI" OR "PR_NPCAR" OR "PR_TIPO" sezionatrice programma taglio`; GitHub: `PR_NPCAR`, `PR_TAGLI`, `PR_VERSIONE`,
`PR_NOME PR_DIMX`.

**Generator uchun:** namunadagi qiymatlar aynan ko'chirilsin; `R<n>` faqat namunada uchragan o'rinlarda (barg qatorlarida)
ishlatilsin — barg bo'lmagan qatorda takror kerak bo'lsa, qatorni `n` marta yozish xavfsizroq.

---

## 7. Masterwood MW310 (MasterWork)

**Natija: qisman–yaxshi. `.mw` kengaytmasi tasdiqlanmadi; haqiqiy formatlar — `.TLF` (loyiha), kengaytirilgan `.DXF`
va ISO dastur (`.PRG`).**

### 7.1 Qaysi fayllar

* MasterWork MW310 — Masterwood stanoklarining grafik dasturi: CAD + CAM + postprotsessor. Loyiha `.TLF` da saqlanadi;
  ISO postprotsessor uni stanok ISO tiliga o'giradi. Texnologik ma'lumotli («kengaytirilgan») DXF ham import qilinadi (o'rta).
  Manbalar: https://www.masterwood.com/en/masterwork.html ,
  https://wtp.hoechsmann.com/en/lexikon/18232/masterwood_masterwork_mw310
* BAZIS‑ЧПУ'da ikkita chiqish: «MW310 (\*.dxf)» va «MW310 (\*.tlf)» (alohida «MW208» ham bor) (yuqori — CAM qo'llanmasi).
  Manba: https://cdn.bazissoft.ru/documentation/ru/CNC.pdf (10.29)
* DXF importida ishlov **qatlam (layer) nomlari** orqali beriladi; kodlash Masterwood qo'llanmasining «4.9 DXF format»
  bo'limida. Ochiq manbada faqat bitta misol: vertikal teshik uchun qatlam `TOP`, diametr va chuqurlik chizmadan olinadi
  (past — qidiruv parchasi, sahifa ochilmadi).

### 7.2 ISO dastur (stanok o'qiydigan matn) — (o'rta: foydalanuvchi stanok dasturidan olgan namuna)

Manba: https://github.com/FreeCAD/FreeCAD/discussions/25829 (Masterwood Project 300 uchun; o'sha joyda RhinoCAM va Vectric
postprotsessorlari matni ham keltirilgan)

```
%
|1 
|2 0
|3 1
|4 2450
|5 45
|6 713
|7 0 0 0 0
...
|44 0
:1
G120 K1
#910=DX
#911=DY
M61 K1 D1
#902=#911-(65)
G172 X1460 Y=#902 Z3 S18 E2 T41/2
G101 X1460 Y=#902 Z3 F3
%
```

* `%` — dastur boshi va oxiri; `|N qiymat` — sarlavha qatorlari. RhinoCAM postprotsessori bo'yicha `|4` = zagotovka X
  uzunligi, `|5` = Z (qalinlik), `|6` = Y (namunada 2450 / 45 / 713). Vectric postprotsessorida (Masterwood 319‑323, `.PRG`)
  sarlavha boshqacha: `1 <fayl nomi>`, `2 <X> <Y> <Z>`, `3 1` … — ya'ni **sarlavha model/versiyaga bog'liq**.
* `#NNN=` — o'zgaruvchilar (`DX`, `DY` — detal o'lchamlari); koordinatada `Y=#902` ko'rinishida ifoda ishlatiladi.
* Asbob: `T41/2` (asbob / pozitsiya), o'zgaruvchi bilan `T=#1/#2`.
* G‑kodlar ro'yxati (foydalanuvchining stanok qo'llanmasidan qilgan xulosasi):

| Kod | Ma'nosi |
|---|---|
| `G120` | ishlov yuzasini tanlash (`G120 K1`) |
| `G172` | istalgan yuzada ishlash — freza yo'lining boshlang'ich qatori |
| `G101` | to'g'ri chiziq; `G102` / `G103` — yoy; `G105` / `G106` — aylana |
| `G40` / `G41` / `G42` | radius korreksiyasi: o'chiq / yoqilgan (ikki yo'nalish) |
| `G180` / `G181` | arra bilan kesim: X bo'ylab / Y bo'ylab |
| `G100` | vertikal parmalash; `G187` — oddiy teshik; `G186` — furnitura (qator) teshiklari |
| `G188` | gorizontal ishlov; `G178` — ishchi yuzani belgilash |
| `G150`–`G153` | ko'zgu: bekor / X / Y / XY |
| `G90` / `G91` / `G92` | absolyut / nisbiy / nolni o'zgartirish |
| `M16` | asbob almashtirish; `M111` / `M112` — parma kirishida sekinlashish; `M200`–`M209` — vakuum va tayanchlar |

Topilmadi: `G187` / `G100` / `G188` parametr harflari (diametr, chuqurlik, yuz), `.TLF` ichki tuzilishi, qatlam nomlari
jadvali, `|7`…`|44` sarlavha qatorlari ma'nosi.

So'rovlar: `Masterwood MW310 MasterWork program file format postprocessor`; `Masterwood Project 310 ISO program G187 G172 G180`;
`Masterwood DXF layer coding "4.9 DXF format"`; GitHub: `G172 G187 masterwood`.

**Generator uchun:** MW310 uchun eng realistik chiqish — **qatlam nomlari bilan kengaytirilgan DXF** (MasterWork o'zi
`.TLF` ga aylantiradi) — lekin qatlam jadvali uchun Masterwood qo'llanmasining 4.9‑bo'limi yoki stanokdan namuna DXF kerak.
ISO `.PRG` ni to'g'ridan‑to'g'ri yozish — parametrlar noma'lumligi sababli hozircha mumkin emas.

---

## 8. IMA ImaWop `.fmc`

**Natija: qisman — fayl tuzilishi (INI‑ga o'xshash bloklar) ochiq kodda bor (ImaWop 2.6), lekin teshik (parmalash)
makrosi topilmadi; versiyalar bir‑biriga mos emas.**

### 8.1 Versiyalar

* FMC — COBUS «NCAD» dasturining formati; ImaWop / ImaWinCad NCAD asosida, lekin o'z ichki FMC varianti bilan.
  2.x dan 12.x gacha **har versiyaning o'z FMC formati** bor; yangi versiya fayli eski dasturda o'qilmaydi (masalan 3.x
  4.x–6.x fayllarini o'qimaydi) (yuqori — formatni ishlab chiqishda qatnashgan firma).
  Manbalar: https://www.camsol.de/programme/fmcconvert ,
  http://xperteam.de/camsol_bis_2012/pdf/cnc_programme_im_austausch_en.pdf
* BAZIS‑ЧПУ'da postprotsessor «ImaWop 4.0 (\*.fmc)»: asboblar `Tom Id.dat` faylidan (ImaWop o'rnatilgan papka) yuklanadi,
  «dastur versiyasi» ro'yxati, «uzoq ish stoli (panel eni … dan katta bo'lsa)», asbobning yakuniy pozitsiyasi, izohlar tili
  sozlamalari bor (yuqori). Manba: https://cdn.bazissoft.ru/documentation/ru/CNC.pdf (10.23.1)

### 8.2 Tuzilish (ImaWop 2.6) — (yuqori: ishlab chiqarishda ishlatilgan ochiq kod shablonlari)

Manba: https://github.com/Raynover/Frustify (`fmc_structure/*.txt`, `fmc_export.py`)

Fayl — oddiy matn; `[BLOK_NOMI]` + `KALIT=QIYMAT` qatorlari, bloklar bo'sh qator bilan ajratiladi; qiymat ifoda bo'lishi
mumkin. Fayl boshi (qisqartirilgan):

```
[VARDEFAU]
INH=6.6
VAR=@VERSION

[HAUPTPRG]
BEZB=TESTATA DEL PROGRAMMA
FTB=900
FTD=9
FTL=1600
RTB=B+(2*AY)
RTL=L+(2*AX)
VERSION=2.6.04
```

| Blok | Vazifasi | Asosiy kalitlar |
|---|---|---|
| `[VARDEFAU]` | o'zgaruvchi e'loni | `VAR=` nom (`@VERSION`, `@SUBVERSION`, `@MASSTAB`), `INH=` qiymat |
| `[HAUPTPRG]` | dastur sarlavhasi | `FTL` / `FTB` / `FTD` — tayyor detal uzunligi / eni / qalinligi; `RTL` / `RTB` — zagotovka (ifoda `L+(2*AX)`); `AXV`, `AYV`, `BEZB` (izoh), `KOM1`, `KOM2`, `VERSION` |
| `[CAD_F_S]` | freza chaqiruvi + kontur boshi | `TNR` (asbob raqami), `SPX` / `SPY` / `SPZ` (boshlang'ich nuqta), `F`, `FAN` (podacha), `TRKOR` (radius korreksiyasi), `TYPAN` / `TYPAB` (kirish / chiqish turi), `LGEAN` / `LGEAB` |
| `[N'G1-XYZ]` | to'g'ri chiziq | `EPX`, `EPY`, `EPZ` (oxirgi nuqta), `F` |
| `[N'G2R-XY]`, `[N'G3R-XY]` | yoy (soat mili bo'yicha / teskari), radius bilan | `EPX`, `EPY`, `R`, `MPX`, `MPY` |
| `[KO'AB_N2]` | konturdan chiqish | — |
| `[ZY'SNW_N]` | arra pazi (sikl) | `SPX`, `SPY`, `EPX`, `EPY`, `NB` (paz eni), `TI` (chuqurlik), `TNR`, `TRKOR`, `S`, `F` |

* Har ishlov blokida `AFB=1` va `BEZB=<matn>` (ko'rinadigan izoh) bor.
* Kalitlar blok ichida **alifbo tartibida** yozilgan (namunalardagi kuzatuv).
* Kodlash va qator oxiri: shablonlar LF bilan saqlangan; stanok CRLF/ANSI kutishi haqida ma'lumot yo'q.

Topilmadi: **vertikal / gorizontal teshik makrosi nomi va kalitlari**, qator teshiklari, 4.0 va undan yuqori versiyalarda
blok nomlari o'zgarishi, koordinata boshi. (NCAD ekran rasmida «Bohrung X= Y=», «Lochreihe vertikal SPX= SPY= EPX=» qatorlari
ko'rinadi — ya'ni teshik va qator‑teshik alohida makroslar, lekin fayldagi nomlari yo'q.)

So'rovlar: `ImaWop .fmc file format`; `IMAWOP fmc "[HAUPTPRG]" OR "[VARDEFAU]"`; `IMAWOP 4.0 fmc Datei Beispiel "BEZB=" "TNR="`;
GitHub: `HAUPTPRG VARDEFAU`, `extension:fmc BEZB`.

**Generator uchun:** umumiy karkas (`[VARDEFAU]` + `[HAUPTPRG]` + ishlov bloklari) ma'lum, lekin prisadka uchun asosiy narsa —
teshik bloki — yo'q, va format versiyaga qattiq bog'liq. Stanokdagi ImaWop versiyasida 3 ta teshik (yuza, qirra, o'tuvchi) va
bitta paz chizib saqlangan `.fmc` namunasi shart.

---

## 9. Holz‑Her NC‑HOPS (`.hop`)

**Natija: yaxshi topildi** — ikki ochiq loyiha (MIT), haqiqiy namuna fayllar va buyruqlar ro'yxati.

Manbalar:
* https://github.com/saschpe/vscode-nc-hops — sintaksis kengaytmasi + `samples/*.hop` (jumladan `Hops-Befehle.hop` —
  deyarli barcha buyruqlar namunasi, Hops 7.0) (yuqori).
* https://github.com/apers0/nc-hops — `.hop` o'qish/yozish Python kutubxonasi, Hops 7.8, Holz‑Her stanoki (yuqori).
* «Hop Interface» (Hops5) rasmiy hujjati mavjud, lekin ochilmadi: https://www.scribd.com/document/622919786/13144-Hop-Interface-en
  (faqat qidiruv parchasi — past).

### 9.1 Fayl tuzilishi

Matn fayl (namunalar cp1252 da; kutubxona kodlashni avtomatik aniqlaydi). Uch qism: `;KALIT=qiymat` sarlavha qatorlari →
`VARS` → `START` va buyruqlar. `apers0/nc-hops` yozadigan sarlavha:

```
;MAKROTYP=0
;INSTVERSION=
;EXEVERSION=7.8.0.2[Hops.exe]
;BILD=
;INFO=
;WZGV=HOLZHER
;WZGVCONFIG=
;MASCHINE=HOLZHER
;NCNAME=
;KOMMENTAR=
;DX=600
;DY=400
;DZ=19
;DIALOGDLL=Dialoge.Dll
;DIALOGPROC=StandardFormAnzeigen
;DIALOGKIND=0
;AUTOSCRIPTSTART=1
;BUTTONBILD=
;DIMENSION_UNIT=0
VARS
   DX := 600;*VAR*
   DY := 400;*VAR*
   DZ := 19;*VAR*
START
Fertigteil (DX,DY,DZ,0,0,0,0,0,'',0,0,0)
```

* `;WZGV` — asboblar jadvali nomi, `;MASCHINE` — stanok/postprotsessor nomi (boshqa namunada `WZGV=37871`,
  `MASCHINE=B_MC_V7`) — **stanokka bog'liq qiymatlar**.
* `VARS`: `nom := qiymat;*VAR*<izoh>` (namunada `*VAR**REF*Laenge in X` ham bor). O'zgaruvchilar keyin ifodalarda ishlatiladi.
* `Fertigteil (X, Y, Z, burilish, …, 'izoh', …)` — detal o'lchami; 4‑parametr burilish: 0 = 0°, 1 = 90°, 2 = 180°, 3 = 270°
  (kutubxona izohi). Parametrlar soni versiyaga qarab 12 yoki 13.
* Izoh qatori `;` bilan; `;$F$<matn>` — ishlovlar guruhining sarlavhasi; `//` izoh ham uchraydi.
* Boshqaruv: `IF … ELSE … END`, `FOR a := 1 TO 10 STEP 1 … END`, `WHILE … END`, o'zlashtirish `a := 1`.
* Tizim o'zgaruvchilari: `_VE`, `_V`, `_VA`, `_SD`, `_ANF` (podacha / aylanish / kirish uchun standart qiymatlar),
  `_RX`, `_RY`, `_RZ` (detal o'lchamlari).

### 9.2 Asbob chaqiruvi

```
WZB (501,_VE,_V,_VA,_SD,_ANF,'501')
WZF (14,_VE,_V,_VA,_SD,_ANF,'1')
WZS (2,_VE,_V,_VA,_SD,_ANF,'1')
```

`WZB` — parma (B = Bohren), `WZF` — freza, `WZS` — arra. 1‑parametr — asbob ID; **`501` — parmalash kallagi** (barcha
parmalar uchun odatiy ID; parma diametr bo'yicha tanlanadi). Oxirgi satr parametri namunalarda `'501'`, `'51'`, `'1'` —
ma'nosi hujjatlanmagan.

### 9.3 Parmalash

```
Bohrung (x,y,d mm,t,sikl,0,0,0,0,0,0,0)
HorzB (500,50,9.5,8,-30,0,0,180)
HorzB (0,0,0,8,-25,0,0,0,0,1,0,0)
CALL _Bohgx_V5 ( VAL SPY:=10,BIX:=64,BIIX:=64+37,BIIIX:=0,BIIIIX:=0,SPIEGELN:=0,T:=-13,D:=8mm,TLF:=10,INKREMENT:=0,ESXY:=1,ESD:=0,USE2:=1,USE3:=0,USE4:=0)
```

* `Bohrung` (vertikal teshik): X, Y, diametr (`8mm` ko'rinishida — birlik qo'shimchasi bilan), chuqurlik, sikl/bayroq,
  keyin nollar. Kutubxona izohi bo'yicha sikl: **10 = shkant teshigi, 20 = o'tuvchi, 30 = diametri > 10 mm** (petlya,
  ekssentrik). Rasmiy imzo (qidiruv parchasi): `DRILLING(X,Y,D,T,Flag,es,esz)` — es / esz = «easy snap» XY / Z.
* `HorzB` (qirra teshigi): X, Y, Z, diametr, chuqurlik, bayroq, og'ish burchagi, **burilish burchagi (0 / 90 / 180 / 270;
  0 = +X yo'nalishi)**, easysnap XY, easysnap Z, 0, 0. Forum izohi shu tartibni tasdiqlaydi
  (https://www.woodworker.de/forum/threads/nc-hops-v-4-aufbau-eines-bohrprogramms.108466/ ; Hops 7.6, Biesse Rover).
* Chuqurlik **manfiy** yoziladi (`T:=-13`, `HorzB … -30`).
* `CALL _Bohgx_V5` / `_Bohgy_V5` — X / Y bo'ylab teshiklar guruhi: `SPY` (yoki `SPX`) — qator chiziqqacha masofa,
  `BIX … BIIIIX` — 4 tagacha teshik pozitsiyasi (ifoda mumkin: `64+37`), `USE2…USE4` — 2–4‑teshik yoqilganmi, `T` chuqurlik,
  `D` diametr, `TLF`, `SPIEGELN` (ko'zgu), `INKREMENT`, `ESXY` / `ESD` (easysnap).
* Boshqa parmalash makroslari (namunada): `_Rbohx_einpass_V5` / `_Rbohy_einpass_V5` (qadamli qator: `RASTER:=32mm`),
  `_Rbohr_winkel_V5`, `_AufBogenBohren_V5`, `_Topf_V5` (petlya chashkasi), gorizontal: `_BoGr_HX_V5` / `_BoGr_HY_V5`,
  `_RBohX_einpass_Horz_V6`. Holz‑Her'ga xos: `HH_DowelGr_HY` (shkant teshish + qo'yish).
* Makros chaqiruvi sintaksisi: `CALL <nom> ( VAL P1:=…,P2:=… )`; natija qaytaradigan — `( REF RESULT:=var VAL … )`.
  Nom oxiridagi `_V5` / `_V6` / `_V7` — makros versiyasi (Hops versiyasiga bog'liq).

### 9.4 Frezalash va arra

```
WZF (14,_VE,_V,_VA,_SD,_ANF,'1')
SP (x,y,z,0,1,_ANF,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
G01 (x,y,z,0,0,2)
G03R (x,y,z,radius,0,0,0)
EP (0,_ANF,0)
```

* `SP` — boshlang'ich nuqta (23 parametr), `G01` — chiziq, `G02M` / `G03M` — yoy (markaz bilan), `G02R` / `G03R` — yoy
  (radius bilan), `EP` — kontur oxiri. Nomli konturlar: `KSP`, `KB`, `KG01`, `KG02M`, `KonturFraesen`.
* Paz: `CALL _Nuten_X_V5 ( VAL NB:=5,NT:=-5,EBENE:=1,ARAND:=5,… )`, `_Nuten_Y_V5`, `_nuten_frei_V5` (X1, Y1, X2, Y2, `NB` eni,
  `TIEFE`); arra: `_saege_x_V7`, `_saege_y_V7`, `_saege_frei_V7`.
* Cho'ntak: `_RechteckTasche_V5`, `_ExecutePocket_V5`; to'rtburchak aylanib o'tish: `_Rechteck_V7`.
* To'xtash joyi: `CALL Park_V7 ( VAL MODE:=3,POSX:=0,POSY:=0)`.

Topilmadi / tasdiqlanmagan: easysnap kodlari jadvali (`ESXY:=1`, `9` va h.k. — baza burchagi/markazi), `Bohrung` ning oxirgi
7 parametri, `HorzB` da Z bazasi (yuqoridan / pastdan), kodlash talabi.

**Generator uchun:** `.hop` generatorini yozish mumkin: sarlavha + `VARS` + `Fertigteil` + `WZB (501,…)` + `Bohrung` /
`HorzB` + paz makrosi. Sozlamaga chiqariladiganlar: `WZGV`, `MASCHINE`, `EXEVERSION`, parma kallagi ID (501), sikl kodlari
(10 / 20 / 30), makros versiya qo'shimchasi. Massivlarni alohida `Bohrung` qatorlari bilan yozish — eng xavfsiz. Bitta sinov
detali bilan baza burchagi (easysnap) va `HorzB` Z bazasi tekshirilsin.

---

## 10. AES Sirius G‑kod dialekti

**Natija: topilmadi (dialekt tavsifi yo'q).**

* Diler sahifalariga ko'ra AES Sirius 950 «Alphacam Essential 2D / AES WOP» yoki **NC‑Hops** interfeysi bilan keladi; DXF
  importi bor; stanok `ANC`, `TXT` yoki `NC` fayllarni o'qishi tilga olinadi (past — qidiruv parchalari).
  Manbalar: https://www.dbs-machines.be/en/machines/compact-cnc-working-center/machine/sirius-950-8447/ ,
  https://www.resellcnc.com/products/boring-mills-vtls-misc-cnc-equipment/01tVS00000CxwaXYAR/aes_sirius_950-m/
* PolyBoard forumidagi mavzu sarlavhasi/parchasi: stanok «to'g'ridan‑to'g'ri G‑kod» ishlatadi, shuning uchun CAM kerak
  (past; sahifa ochilmadi) — https://wooddesigner.org/forum/polyboard/aes-cnc-machine/
* BAZIS‑ЧПУ'da AES uchun uch postprotsessor: «AES Raptor», «AES Drill Macro», «AES Sirius». Sirius sozlamalari: operatsiyalar,
  asboblar bazasi, umumiy, teshik (o'tuvchi teshik uchun qo'shimcha chuqurlik), bo'ylama paz (asbob turi) — **frezalash
  bo'limi yo'q**; G‑kodlar tavsiflanmagan (yuqori — borligi; format yo'q).
  Manba: https://cdn.bazissoft.ru/documentation/ru/CNC.pdf (10.3.3)

So'rovlar: `AES Sirius CNC delik makinesi G kodu post processor program formatı`; `AES Sirius 950 … yazılım program dosyası formatı`;
`AES Sirius "NC-Hops" OR "AES WOP" OR "ANC" file`.

**Generator uchun:** agar korxonadagi Sirius NC‑Hops bilan kelgan bo'lsa — 9‑bo'limdagi `.hop` yo'li ishlaydi (`MASCHINE` /
`WZGV` AES ga mos qiymat bilan). Sof G‑kod uchun stanokdan namuna dastur shart.

---

## 11. Vitap Bridge / Vitap Point (`.tcn`, TpaCAD)

**Natija: qisman.** Format — TpaCAD `.tcn`; uning umumiy tavsifi `WEB_biesse_scm_felder_tpa.md` 8‑bo'limda (rasmiy TPA
qo'llanmalari). Yangi topilganlar:

* PolyBoard Vitap, Brema va ayrim Felder stanoklari uchun «native TpaCAD `.tcn`» chiqaradi (o'rta — qidiruv parchasi; sahifa
  ochilmadi). https://wooddesigner.org/help-centre/felder-vitap-brema-integration-polyboard/
* BAZIS‑ЧПУ'da **uchta alohida** Vitap postprotsessori: «Vitap TPA», «Vitap Bridge ICE112», «Vitap Point» (yuqori).
  Manba: https://cdn.bazissoft.ru/documentation/ru/CNC.pdf (10.40)
  * Bridge va Point: baza burchagini tanlash; «yuzadagi teshiklar uchun optimal baza» (har teshikka alohida); bir chiziqdagi
    teng qadamli teshiklarni **guruhlash**; o'tuvchi teshik uchun qo'shimcha chuqurlik.
  * Point qo'shimcha: diametr chegarasidan katta bo'lsa «chashka» parma turi; **«stanok boshqaruv tizimi» tanlovi** (ya'ni
    Point'ning bir nechta kontroller avlodi bor); diametr → parma turi jadvali; to'g'ri chiziqli paz (Y koordinatasi qaysi
    chiziqdan o'lchanishi sozlanadi).
* Ochiq `.tcn` namunalari (TpaCAD 2.x, Format4 / Felder makroslari bilan) — sarlavha va bloklar tartibini ko'rsatadi (yuqori —
  haqiqiy fayl). Manba: https://github.com/Lecreole74/Codes-divers/tree/HEAD/models (qisqartirilgan):

```
TPA\ALBATROS\EDICAD\02.00:1665:r0w0s6
::SIDE=0;1;4;6;
::ATTR=hide;varv
::UNm DL=#width# DH=#heigth# DS=#depth#
'tcn version=2.9.20
'code=ansi
EXE{ … }EXE
OFFS{ … }OFFS
VARV{ … }VARV
VAR{ … }VAR
SPEC{ }SPEC  INFO{ }INFO  OPTI{ … }OPTI  LINK{ }LINK
SIDE#1{
$=Up
W#1050{ ::WT2 WS=3  #8098=..\custom\mcr\lame.tmcr #6=1 … #8503=r\rl … #8516=2001 #8517=l #8525=2 … }W
}SIDE
```

  Bu yerda `#8503` (kesim eni) haqiqiy faylda ishlatilgan — avvalgi tadqiqotdagi TPA tavsiyasini (paz eni `#8503` orqali)
  qo'llab‑quvvatlaydi; `::UNm` — millimetr; `DL` / `DH` / `DS` — uzunlik / balandlik / qalinlik; `'code=ansi` — kodlash.
* Sarlavhaning birinchi qatori dastur avlodini bildiradi: `EDICAD\00.00` (eski EdiCad) va `EDICAD\02.00:<build>:r0w0s<n>`
  (TpaCAD) — ikkalasi ham ochiq fayllarda uchraydi.

Topilmadi: Vitap'ning o'z makros kodlari (teshik `W#81` dan boshqacha bo'lsa), Bridge ICE112 kontrollerining xususiyatlari,
Point avlodlari orasidagi farq, qo'llaniladigan TpaCAD versiyasi.

So'rovlar: `Vitap Point K2 Bridge .tcn file TpaCAD format example`; `Vitap Point K2 TOP program import "tcn"`; GitHub:
`TPA\ALBATROS\EDICAD`, `vitap tcn`.

**Generator uchun:** mavjud TPA generatorimiz asos bo'ladi; Vitap uchun sozlamalar: baza burchagi, teshiklarni guruhlash
(o'chiq bo'lsin — alohida teshiklar xavfsiz), kontroller avlodi. Stanokdagi TpaCAD'da saqlangan bitta `.tcn` namunasi kerak
(sarlavha qatori va makros kodlarini solishtirish uchun).

---

## 12. Xitoy 6 tomonli parmalash stanoklarining umumiy «G CODE»i

**Natija: topilmadi.** Ochiq manbalarda bu stanoklar uchun G‑kod konvensiyasi tavsiflanmagan; aksincha, manbalar ularning
G‑kod emas, **detal tavsifi fayllari** bilan ishlashini ko'rsatadi.

* Xitoy 6 tomonli stanoklarining CAM dasturlari kirish sifatida MPR, BAN, XML, MCS, DXF, BPP, CIX va h.k. qabul qiladi; BAN —
  «barcha mahalliy brendlarga mos» umumiy format deb ta'riflanadi; stanok dasturi G‑kodni o'zi hosil qiladi (o'rta).
  Manbalar: https://gitcode.com/open-source-toolkit/17696 (BanCAD: HUAHUA, ZHENGTAI, NANXING, JIDONG),
  http://www.sudiaozn.com/show-11-408.html , https://blog.csdn.net/m0_72645744/article/details/125777555
* Asbob raqamlari, yuz belgilari, M‑kodlar (qisqich, silindrlar) har ishlab chiquvchining CAM sozlamalarida — stanokka xos
  (CSDN «六面钻调试» turkumi shu haqda, sahifalar ochilmadi: https://blog.csdn.net/weixin_42584545/article/details/131070702).

So'rovlar: `六面钻 G代码 格式 NC 文件 侧孔 正面孔`; `六面钻 NC 程序 G代码 示例 "G81" 侧面孔`; `六面钻 加工程序 "G00" "G01" "M03" 钻包 新代 OR 维宏 OR LNC`;
`六面钻 对接 拆单软件 输出 "XML" "MPR" "BAN"`.

**Generator uchun:** «G CODE» nomli umumiy format yo'q — har stanok uchun namuna kerak. Namuna bo'lmagan Xitoy stanoklari
uchun eng ishonchli yo'l — bizda allaqachon bor **BAN** (MicroDraw, rasmiy spetsifikatsiyali) yoki MPR / XML chiqishi.

---

## Tavsiyalar (qisqa)

1. **Yangi generator nomzodlari (hujjatlangan):** Holz‑Her / AES **NC‑HOPS `.hop`** (9‑bo'lim); **Giben `.AC`** (5a.1).
2. **Namuna fayl kerak (internetda yo'q):** Scheer; FastPanel 2.1.5; KDT `.qk` boshqa versiyalari; Giben `.DAX/.CPX` chegara
   holatlari; Felder F4Classic chuqur daraja; ImaWop teshik bloki; Masterwood DXF qatlam jadvali; Vitap `.tcn`; AES Sirius sof G‑kod.
3. **Selco NC300:** `B_LABEL` / `B_REF` ni ixtiyoriy opsiya qilish va stanokda sinash; ≤ 4 daraja.
4. **Daraja chegaralari** ko'p joyda format emas, sozlama (Promob: «allowed phases» / «maximum machine phases») — bizda ham
   stanok profilida `max_levels` sozlanadigan bo'lsin, standart qiymat namunadan.
5. **Masterwood:** generator kaliti/nomi `.mw` emas — `.dxf` (qatlamli) yoki `.tlf`.

## JAVOB TOPILMADI (yig'ma)

1. KDT `.qk` / `.lbd` tuzilishi va V1.4.0P / V3.3.0P / V4.x / V6.3.2P farqlari.
2. FastPanel `.ocm`: ishlab chiquvchi, 2.1.4 ↔ 2.1.5 farqi, maksimal daraja.
3. Scheer import formati.
4. Holzma `.SPL` / `.LC4` ichki tuzilishi va aniq daraja chegarasi.
5. Giben `.DAX` / `.CPX`; yangi (100+ belgili) `.AC`; `.AD` maydonlari.
6. Selco NC300: `B_REF`, `VL`, `VT`, `HP` rasmiy ma'nosi; fayl nomi cheklovi.
7. Felder F4Classic: barcha `PR_*` kalitlari, `R<n>` qoidasi, dastur ishlab chiquvchisi.
8. Masterwood: `G187` / `G100` / `G188` parametrlari, `.TLF` tuzilishi, DXF qatlam kodlari.
9. ImaWop: teshik makroslari; 4.0+ versiya farqlari.
10. NC‑HOPS: easysnap kodlari, `Bohrung` ning qo'shimcha parametrlari, `HorzB` Z bazasi.
11. AES Sirius G‑kod dialekti; Vitap makros kodlari; Xitoy 6 tomonli stanoklari G‑kodi.

### Ochilmagan, lekin foydali bo'lishi mumkin bo'lgan manbalar (brauzerda ko'rish uchun)

* Hops5 «Hop Interface» (rasmiy buyruqlar tavsifi) — https://www.scribd.com/document/622919786/13144-Hop-Interface-en ,
  https://www.scribd.com/document/327706636/Hop-Interface-En
* IMAWOP 9.0 dasturlash qo'llanmasi — https://www.scribd.com/document/980362644/IMAWOP-9-KE-en
* Masterwood MW310 foydalanuvchi qo'llanmasi (4.9 «DXF format») — https://www.scribd.com/document/662961495/LB003570-MasterAT-v1-4-Clienti-ING
* RhinoCAM Masterwood postprotsessori — https://mecsoft.com/PostProcessors/MILL/MasterWood.spm
* Masterwood dastur namunalari — https://en.cncarena.com/forum/thread/342117-masterwood-parametric-programming/ ,
  https://www.cnczone.com/forums/cnc-machining-centers/68599-mastercam.html
* OptiCut postprotsessorlar ro'yxati (Scheer, Selco NC300 / NC500, Giben …) — https://wooddesigner.org/help-centre/opticut-integration-cnc-saw/ ,
  https://wooddesigner.org/help-centre/opticut-biesse-selco-saw/
* PolyBoard: AES, NC‑Hops, Vitap — https://wooddesigner.org/forum/polyboard/aes-cnc-machine/ ,
  https://wooddesigner.org/forum/polyboard/direkt-nc-hops-post-processor/ ,
  https://wooddesigner.org/help-centre/felder-vitap-brema-integration-polyboard/
* OptiPlanning qo'llanmasi — https://www.scribd.com/document/377141707/Optiplaning-Eng
* CADmatic mavzulari — https://www.cnczone.com/forums/cnc-machining-centers/115260-software.html ,
  https://www.cnczone.com/forums/uncategorised-cam-discussion/190176-pnc-ptx-cadmatic-3-a.html
* NC300 mavzusidagi Dropbox havolalari (WinCut format tavsifi, OSI kesim turlari) — o'chirilgan.
