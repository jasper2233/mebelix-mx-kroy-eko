# WEB-tadqiqot: BiesseWorks `ROUT` `TIN/AIN` va Selco OSI `Cut@Chk`

> Sana: 2026-10-04. Usul: WebSearch / WebFetch, GitHub ochiq manba kodi, ochiq PDF/forum sahifalari (EN/RU).
> Hech qayerga login qilinmadi, bajariladigan fayl yuklanmadi, kod o'zgartirilmadi.
> Avvalgi tadqiqot (`WEB_biesse_scm_felder_tpa.md` §1.1, §3.4) takrorlanmaydi — bu fayl faqat ikki ochiq savolni yopadi.
>
> **Dalil darajalari:**
> * **[A]** — birlamchi manba matni o'qildi (manba kodi / qo'llanma matni / forum posti so'zma-so'z).
> * **[B]** — faqat qidiruv tizimi xulosasi yoki ikkilamchi hujjat (sahifaning o'zi ochilmadi).
> * **[C]** — manbalardan mantiqiy xulosa, to'g'ridan-to'g'ri yozilmagan.

## 0. Qisqa xulosa

| Savol | Javob | Ishonch |
|---|---|---|
| `TIN`/`TOU` kodlari | 0 None, 1 Curve, 2 Line, 3 TgLineCurve, 5 Helix, 6 Curve3DLine, 7 Corrected3DLine, 8 Corrected3DCurve, 9 CorrectedLine, 14 Profile3D | yuqori (nomlar va raqamlar — BppLib [A]; nomlar ro'yxati Biesse qo'llanmasi bilan mos [A]) |
| `AIN`/`AOU` ma'nosi | kirish/chiqish burchagi, **gradus**; ma'nosi `TIN` turiga bog'liq (Curve uchun — kirish yoyining burchagi/ochilishi) | o'rta-yuqori (ta'rif [A]; Curve uchun aniq geometriya rasmda — rasm ko'rilmadi) |
| `AIN = 88` qayerdan | **TOPILMADI.** Format konstantasi emas; hech bir ochiq manbada 88 uchramadi. Boshqa generatorlar 0, 45 yoki 90 yozadi | — |
| `TIN = 9, AIN = 0` (chiziq bilan boshlanadigan kontur) | 9 = CorrectedLine: havoda korreksiya chizig'i + yuzaga perpendikulyar tushish; bu tur uchun burchak ta'riflanmagan → 0 mantiqan to'g'ri | yuqori (tur), o'rta (burchak = 0) |
| `Cut@Chk` algoritmi | **TOPILMADI** (hech qayerda tavsiflanmagan) | — |
| OSI `Chk` ni tekshiradimi | **Ha, katta ehtimol bilan**: Selco/OSI egasining birinchi qo'l guvohligi — `Chk` siz dastur import bo'ladi, lekin **ishga tushmaydi** | o'rta-yuqori (bitta mustaqil guvohlik [A], rasmiy hujjat yo'q) |

---

## 1. Manbalar

| # | URL | Nima berdi | Ishonchlilik |
|---|---|---|---|
| M1 | https://github.com/viachpaliy/BppLib — `BppLib.Core/Enumerations/LeadInOutType.cs` | `TIN`/`TOU` enum: raqamli kodlar + har bir tur uchun to'liq tavsif (kirish va chiqish) | [A] yuqori — ochiq manba, tavsiflar Biesse qo'llanmasi matniga mos; lekin uchinchi tomon kutubxonasi |
| M2 | https://github.com/viachpaliy/BppLib — `BppLib.Core/Millings/Rout.cs` (`RoutG.cs`, `Pock.cs` ham) | `AIN, CIN, GIN, TBI, TLI, TQI, TOU, AOU, COU, GOU, TBO, TLO, TQO, DIN, DOU, SDS, PRP` ta'riflari, turlari, standart qiymatlari; `.bpp` dagi maydon tartibi | [A] yuqori |
| M3 | https://github.com/viachpaliy/BppLib — `BppLib.UnitTests/BppParser.UnitTests/DefaultValuesTests.cs` | BiesseWorks yozgan haqiqiy `@ ROUT` qatori: `… 103, 1, 2, 1, 45, 0, 0, 0, 0, 0, 1, 45, …` (TIN=1, AIN=45, TOU=1, AOU=45) | [A] yuqori (namuna qator) |
| M4 | https://idoc.pub/documents/biesse-works-12-6nq89jodkqnw — «Biesse Works 1.2» foydalanuvchi qo'llanmasi (BIESSE S.p.A., `a211h012.fm`, 412 bet) | «Lead-in Type», «Lead-in Angle», «Percent Radius» maydonlari va Settings → Milling data standartlari ta'rifi | [A] yuqori — ishlab chiqaruvchi hujjati (eski versiya, 2003; rasmlar ko'rinmaydi) |
| M5 | https://woodweb.com/cgi-bin/forums/cnc.pl?read=802943 — «BiesseWorks lead-in lead-out» | CIX da `TIN/TOU/AIN/AOU` bo'lmasa BiesseWorks o'z standartini oladi; `0 = None` haqiqiy qiymat | [A] o'rta (tajribali foydalanuvchi posti) |
| M6 | https://help.cadmate.com.au/en_AU/optimizer/biesse-cix-post-processor-update — Mozaik «Biesse CIX Post Processor Update» | `AIN` ruxsat etilgan oraliqlari tur bo'yicha; `GIN/GOU/DOU` ma'nosi | [A] o'rta (boshqa CAM ishlab chiqaruvchisi hujjati; WebFetch xulosasi orqali o'qildi) |
| M7 | https://github.com/lasselukkari/furnigen — `src/Cix/types/ROUTG.js`; https://github.com/KiidxAtlas/biesse_drill_test — `cix_generator.py` | Boshqa ochiq CIX generatorlari: `TIN=0, CIN=1, AIN=90, TOU=0, COU=1, AOU=90, PRP=100` | [A] o'rta (amaliy namunalar) |
| M8 | Autodesk Fusion «biesse cix.cps» post (GitHub'dagi nusxa: `PriyaBhoomireddi/Frontend-2-contest-2`, `…/CAM/cache/posts/biesse cix.cps`) | `TIN=0, CIN=NO, AIN=45, GIN=0, TOU=0, AOU=45, PRP=100` | [A] o'rta-yuqori (Autodesk rasmiy posti nusxasi) |
| M9 | https://github.com/SolidSolutionsLtd/SwoodReportPro3Example — `programs/*Milling.bpp` | SWOOD CAM yozgan haqiqiy `.bpp`: `… 103, 1, 1, 0, 90, 1, 0, 0, 0, 0, 0, 90, 1, …` (TIN=0, AIN=90, CIN=1; TOU=0, AOU=90, COU=1) | [A] o'rta (haqiqiy CAM chiqishi) |
| M10 | https://github.com/viachpaliy/rastercarve_for_Biesse_CNC | `.bpp` generator: TIN=0, AIN=0 (hammasi nol) | [A] o'rta |
| M11 | https://forum.tecnocom-ug.ru/viewtopic.php?t=335&start=285 — «Biesseworks для чайников» (39 sahifa ko'rib chiqildi) | «Процент Радиуса» (PRP) ma'nosi; `.bpp` da 100 | [A] past-o'rta (forum) |
| M12 | https://www.cnczone.com/forums/general-woodworking/328146-cnc.html — «CPOUT File format» (2017-02-01; jonli sahifa 403, matn Wayback nusxasidan `web.archive.org/web/20180219204235/…` o'qildi) | **`Chk` haqida yagona ochiq guvohlik**: `Chk` siz dastur OSI ga import bo'ladi, lekin ishga tushmaydi | [A] o'rta-yuqori (stanok egasining o'z tajribasi; bitta manba) |
| M13 | https://suporte.promob.com/hc/en-us/articles/31122654246929-Cut-Pro-Biesse-Cutting-Managers-OSI | OSI XML importi Biesse servisi tomonidan yoqiladi; `Chk` haqida hech narsa yo'q | [A] o'rta |
| M14 | https://cdn.bazissoft.ru/documentation/ru/CNC.pdf — «БАЗИС-ЧПУ», 10.6.1 BiesseWorks (*.bpp) | Kirish/chiqish turi postprotsessor sozlamasi ekani; qiymatlar jadvali yo'q | [A] (savolga javob bermadi) |

**Ochilmagan sahifalar** (403 / bot-tekshiruv / arxiv o'chiq): `pdfcoffee.com` dagi «BiesseWorks Instructions Rev6.4 5804A0107» va «Biesseworks: Instructions for use», `scribd.com/document/564782657/BIESSE-CIX-1`, `cnczone.com/forums/biesse/471040-biesse-selco-eb80-xml-import.html`, `cnczone.com/forums/biesse/465129-biesse-selco-post-processor.html`, `wooddesigner.org` (help-centre va forum), `forums.autodesk.com` CIX mavzusi.

---

## 2. 1-savol: `ROUT` dagi `TIN / AIN / TOU / AOU` va qo'shni maydonlar

### 2.1 `.bpp` qatoridagi o'rinlar (tasdiqlandi)

BppLib `Rout.AsBppCode()` tartibi [A, M2] bizning namunaviy qatorga aynan mos (indeks 0 dan, `:` dan keyin):

```
48 TTP=103 | 49 TCL=1 | 50 CRC | 51 TIN | 52 AIN | 53 CIN | 54 GIN | 55 TBI | 56 TLI | 57 TQI |
58 TOU | 59 AOU | 60 COU | 61 GOU | 62 TBO | 63 TLO | 64 TQO | 65 DIN | 66 DOU | 67 SDS | 68 PRP | 69 BDR | 70 SPI=""
```

Namunadagi `…, 103, 1, <CRC>, 9, 0, 0, 0, 0, 0, 0, 0, 0, …` → `TIN=9, AIN=0, CIN=0, GIN=0, TBI=0, TLI=0, TQI=0, TOU=0, AOU=0, COU=0, …, PRP=0`.

### 2.2 `TIN` / `TOU` kodlari [A, M1]

Enum ta'rifi: «Uses with `Tin` and `Tou` properties of milling classes.»

| Kod | Nom | Kirish (lead-in) — manba matni | Chiqish (lead-out) |
|---|---|---|---|
| 0 | None | «the tool descends perpendicularly and reaches the machining operation start point directly» | «leaves the piece directly at the end of machining point rising perpendicularly to the face» |
| 1 | Curve | «descends travelling along a line perpendicular to the face and enters the piece directly reaching the machining start point performing a short arc shaped course along which it corrects its position. When `Cin = true` the tool corrects its position before descending, thereby generating a short linear course parallel to the face» | qisqa yoy bo'ylab chiqadi (korreksiya shu yoyda), so'ng perpendikulyar ko'tariladi |
| 2 | Line | xuddi shunday, lekin «a short linear course along which it corrects its position» | qisqa to'g'ri chiziq bo'ylab chiqadi |
| 3 | TgLineCurve | «forming a line and a tangential arc along which it corrects its position» | chiziq + urinma yoy |
| 5 | Helix | «generates a line in the air parallel to the face along which it carries out the correction, it descends and moves along a spiral course» | spiral + yuzaga parallel chiziq |
| 6 | Curve3DLine | «descends travelling along an inclined line and enters the piece … performing a short arc along which it corrects its position» | yoy + qiya ko'tarilish |
| 7 | Corrected3DLine | «generates a line in the air parallel to the face along which it carries out the correction, it descends and moves along an inclined line» | qiya ko'tarilish + parallel chiziq |
| 8 | Corrected3DCurve | «… line in the air … it descends and moves along an arc shaped course» | yoy bo'ylab ko'tarilish + parallel chiziq |
| 9 | **CorrectedLine** | «generates a line in the air parallel to the face along which it carries out the correction, it descends and moves along a line perpendicular to the plane and enters the piece directly reaching the machining operation start point» | «rise perpendicular to the face and follows a line parallel to the face, along which it corrects its position» |
| 14 | Profile3D | «descends travelling along an inclined line and enters the piece directly … only allowed with closed profiles» | qiya ko'tarilish |

* 4, 10–13 kodlari BppLib da **yo'q** — ularning mavjudligi/ma'nosi TOPILMADI.
* Biesse qo'llanmasidagi nomlar ro'yxati shu bilan mos [A, M4]: «None; … Line; … Corrected 3DLine; … Corrected Line; used to enter the piece forming a line parallel to the work table and descending perpendicular to the work table, so as to carry out tool compensation. … Curve; used to enter the piece along a curved path. Corrected 3DCurve; … 3DLineCurve; … Tg LineCurve; used to enter the piece along a path formed by a line tangent to a curve. Helix; used to enter the piece along a helicoidal path.» (qo'llanmada raqamli kodlar berilmagan — raqamlar faqat M1 dan).
* `0` haqiqiy qiymat, «bo'sh» emas [A, M5]: «it won't change a 0 value in that field as 0 is valid. 0=None».
* CIX/BPP da bu parametrlar bo'lmasa BiesseWorks o'z standartini qo'yadi [A, M5]: «If the macro (ROUT or ROUTG) does not contain param,name= TIN TOU AIN AOU The default lead (in-out) you set should be picked up when you open or import the cix.» (`.bpp` pozitsion format — u yerda tashlab ketib bo'lmaydi.)
* «avtomatik» degan tur **yo'q** (9 — «avtomatik» emas, «CorrectedLine»).

### 2.3 `AIN` / `AOU` — burchak

* Ta'rif [A, M2]: «Property `Ain` represents the lead-in angle of the tool. The type of angle to be entered will vary according to the type of lead-in selected.» Tur `int`, standart `45`.
* Biesse qo'llanmasi [A, M4]: «Lead-in Angle; lead-in angle of the tool into the piece. The type of angle to be entered varies according to the type of tool selected (see figure 167). Figure 167: lead-in angle (ang) for the type of lead-in Line (ref. A) and for the type of lead-in Curve (ref. B). For lead-in Corrected 3DLine, the angle between the line at an oblique angle to the work table and the work table itself must be taken into consideration. For lead-in Corrected 3DCurve, the angle of aperture of the curve on the three-dimensional plane must be taken into consideration. For lead-in 3DLineCurve, the angle of aperture of the curve must be taken into consideration. For lead-in Helix, the angular width of the helix must be taken into consideration.»
* Settings → Milling data [A, M4]: «Lead-in angle — Used to define the tool lead-in angle with respect to cartesian plane X-Y.»; «Default angle — Used to define the default angle according to the type of lead-in or lead-out selected in the top list.»
* Birlik — **gradus** [C]: barcha namunalarda butun gradus qiymatlari (0, 45, 90), M6 da oraliqlar gradusda.
* Ruxsat etilgan oraliqlar — faqat ikki tur uchun topildi [A, M6 — Mozaik hujjati]: `<None>`: burchak = 0; `<Corrected 3DLine>`: 0 ≤ burchak ≤ 90; `<Corrected 3DCurve>`: 0 < burchak ≤ 45. **Curve (1), Line (2), CorrectedLine (9) uchun oraliq TOPILMADI.**
* Tur bo'yicha ma'no (yig'ma):

| TIN | AIN nimani bildiradi | Manba |
|---|---|---|
| 0 None | ishlatilmaydi (0) | M6; M7–M9 da 45/90 yozilgan, ta'siri yo'q [C] |
| 1 Curve | kirish yoyi burchagi (X-Y tekisligida; 167-rasm «ref. B») — aniq o'lchov nuqtalari rasmda, rasm ko'rilmadi | M4 |
| 2 Line | kirish chizig'ining burchagi (X-Y tekisligida; 167-rasm «ref. A») | M4 |
| 7 Corrected3DLine | qiya tushish chizig'i bilan stol orasidagi burchak | M4, M6 |
| 8 Corrected3DCurve / 6 | yoyning ochilish burchagi | M4 |
| 5 Helix | spiralning burchak kengligi | M4 |
| 9 CorrectedLine, 3 TgLineCurve, 14 | **ta'rif yo'q** (CorrectedLine da tushish perpendikulyar — burchak ma'nosiz [C]) | — |

### 2.4 `AIN = 88` — fiksirlangan standartmi yoki hisoblanadimi?

**JAVOB: TOPILMADI.** Aniq ma'lum bo'lganlar:

1. 88 Biesse formatining standarti **emas**. BiesseWorks o'zi yozgan qatorda `TIN=1, AIN=45` [A, M3]; BppLib standarti ham `Curve / 45` [A, M2].
2. Boshqa generatorlar burchakni **konstanta** sifatida yozadi, geometriyadan hisoblamaydi: Autodesk posti `45` [M8], furnigen va biesse_drill_test `90` [M7], SWOOD `90` [M9], rastercarve `0` [M10]. Geometriyadan `AIN` hisoblaydigan birorta ochiq kod topilmadi.
3. BiesseWorks da burchak standarti **har bir kirish turi uchun alohida sozlanadi** («Default angle … according to the type of lead-in» [A, M4]) — ya'ni qiymat CAM/operator tanlovi.
4. «88» soni hech bir qidiruvda (`AIN=88`, `AIN,VALUE=88`, EN/RU) uchramadi.

Xulosa [C]: 88 — bizning namunalarni yozgan dasturning o'z qiymati; u 90° li yoy uchun «90 dan biroz kichik» konstanta bo'lishi ham, geometriyadan hisoblangan bo'lishi ham mumkin. Buni faqat **turli radius/burchakli yoy bilan boshlanadigan namunalarni solishtirish** hal qiladi (hamma namunada 88 bo'lsa — konstanta). Internetdan aniqlab bo'lmaydi.

### 2.5 Qo'shni maydonlar [A, M2]

| Maydon | Tur / standart | Ma'no (manba matni) |
|---|---|---|
| `CIN` (`COU`) | bool, 0 | «enables correction in air. When the correction in air is enabled, the tool corrects its position before descending, thereby generating a short linear course parallel to the face.» |
| `GIN` (`GOU`) | mm, 0 | «the distance in millimetres from the lead-in point of the machining operation to move the tool sideways in such a way that it makes a slightly inclined descent. … can only be used with lead-ins of the Corrected3DLine type or the Corrected3DCurve type.» Mozaik [M6]: «-1 is a 1mm offset away from the geometry» |
| `TBI` (`TBO`) | bool, 0 | «enables generation a linear translation of the tool inside the lead-in trajectory of the tool into the piece, in order to create a short step, that can be calculated on the depth of the programmed machining operation.» |
| `TLI` (`TLO`) | mm, 0 | «the linear length of the segment for translating the tool (if Tbi = true)» |
| `TQI` (`TQO`) | mm, 0 | «the position (mm) to establish the initial translation point that can be calculated by starting from the Z co-ordinate of the final point of the milling» |
| `DIN` | mm, 0 | «transfer of the machining operation point of origin forwards or back along the same trajectory» (faqat yopiq konturlarda — M4) |
| `DOU` | mm, 0 | kirish va chiqish nuqtalari orasidagi masofa (overlap; yopiq kontur) |
| `SDS` | mm, 0 | geometriya oxiri oldidan sekinlashish masofasi |
| `PRP` | %, 0 | «the percentage value to modify the lead-in and lead-out radius» [M2]; M4: «Percent Radius; percentage value to modify the lead-in and lead-out radius». Forum [M11]: «это расстояние на которое отдалится фреза от детали при определенном типе входе и выходе»; boshqa CAM `.bpp` da 100 yozgan. M7, M8 ham `PRP=100` |

**Diqqat (ochiq savol):** bizning qatorda `PRP = 0` (indeks 68). `TIN=1` (Curve) bilan `PRP=0` qanday yoy radiusini berishi hujjatda yozilmagan; boshqa generatorlar yoyli kirishda emas, `TIN=0` da ham `PRP=100` yozadi. Namunadagi yoy-boshli `ROUT` qatorida PRP qiymatini tekshirish va aynan o'shani takrorlash kerak.

### 2.6 Tasdiqlangan / noma'lum

**Tasdiqlangan:** `TIN/TOU` kodlar jadvali (0,1,2,3,5,6,7,8,9,14) va har birining harakati; `9 = CorrectedLine`; `1 = Curve` (qisqa yoy bilan kirish, korreksiya yoyda); `AIN/AOU` — gradusdagi burchak, ma'nosi turga bog'liq; `CIN/GIN/TBI/TLI/TQI/PRP` ta'riflari; maydon o'rinlari (51–68); BiesseWorks standarti `1 / 45`.

**Noma'lum:** (1) 88 ning kelib chiqishi; (2) Curve uchun `AIN` aniq qaysi burchak (yoy markaziy burchagimi yoki urinma bilan burchakmi — 167-rasm) va ruxsat etilgan oralig'i; (3) `PRP=0` ning Curve dagi ta'siri va yoy radiusi formulasi (asbob radiusi × PRP % — faqat taxmin, hujjatda yo'q); (4) kontur geometriyasida kirish yoyi allaqachon bor bo'lsa (`ARC_EPCE` birinchi element) `TIN=1` qo'shimcha yoy qo'shadimi — BiesseWorks simulyatorida ko'rish kerak; (5) 4, 10–13 kodlari.

---

## 3. 2-savol: Selco OSI `Cut@Chk`

### 3.1 Mashina tekshiradimi

**JAVOB: ha deb hisoblash kerak** (ishonch: o'rta-yuqori, bitta birinchi qo'l manba) [A, M12]. Selco arra egasi, OSI uchun o'z XML eksportini yozgan:

> «I have a Selco Panel Saw running their OSI interface, and I have written a small program that exports a specialized cut list to the xml format that OSI can read into it's optimizer function. … My attempts to write the native OSI xml format has failed because I can't decode the value of an attribute called Chk. **Without this the programs import into OSI but cannot be run.** OSI supports importing CPOUT files…»

Mavzuda javob berilmagan (yagona javob — CPOUT bo'yicha, `Chk` haqida emas). Demak:
* `Chk` — dastur (kesish sxemasi) yaxlitligi/haqiqiyligi belgisi; noto'g'ri yoki yo'q bo'lsa import o'tadi, **bajarish bloklanadi**.
* Xuddi shu muallif ishlaydigan yo'lni ko'rsatgan: **detallar ro'yxatini** (cut list) XML qilib OSI ning o'z **optimizatoriga** berish — unda `Chk` kerak emas (kroyni OSI o'zi qiladi).
* OSI **CPOUT** fayllarini ham import qiladi (muallif so'zi; format tafsiloti topilmadi).

### 3.2 Algoritm

**JAVOB: TOPILMADI.** Qidirilgan joylar: OSI Release 1 qo'llanmasi (avvalgi tadqiqot, S4 — XML tuzilishi tavsiflanmagan); Promob OSI maqolasi [M13] — faqat «it is necessary to contact Biesse support to activate the XML import option», `Chk` yo'q; GitHub kod qidiruvi (`"TechnoParam" "QBoards"`, `Chk QBoards ToWork ExeOrder` — 0 natija, ya'ni bu formatni yozadigan ochiq kod yo'q); WebSearch (EN/RU/DE/IT: «Selco OSI xml Chk», «checksum», «контрольная сумма», «prüfsumme», «somma di controllo») — faqat M12; cnczone «BIESSE SELCO EB80 XML IMPORT» va wooddesigner (OptiCut XML/XML2) sahifalari ochilmadi (403).

Ma'lum bo'lgan yagona narsa (o'z namunalarimizdan, avvalgi hujjat): `Chk` faqat dasturning oxirgi `Cut` elementida, butun son; oddiy yig'indi va CRC16/32 mos kelmagan.

### 3.3 Tasdiqlangan / noma'lum

**Tasdiqlangan:** `Chk` majburiy (dasturni bajarish uchun) — bitta mustaqil guvohlik; XML importning o'zi servis tomonidan yoqiladigan opsiya; `Chk` siz import xatosiz o'tadi.
**Noma'lum:** algoritm; `Chk` qaysi maydonlarni qamrashi (faqat `Cut` larmi yoki `Board`/`TechnoParam` hammi); OSI versiyalari orasida farq; OptiCut XML/XML2 chiqishida `Chk` bormi.

---

## 4. Generator uchun aniq tavsiya

### 4.1 BiesseWorks `ROUT`

| Holat | Yozish | Asos |
|---|---|---|
| Kontur **chiziq** bilan boshlanadi | `TIN = 9`, `AIN = 0`, qolganlari 0 (`CIN, GIN, TBI, TLI, TQI, TOU=0, AOU=0, …`) | namunaga aynan mos; 9 = CorrectedLine (havoda korreksiya, perpendikulyar tushish) — detal tashqarisidan boshlanadigan kontur uchun mantiqiy; bu tur uchun burchak ta'rifi yo'q |
| Kontur **yoy** bilan boshlanadi | `TIN = 1`, `AIN = 88` — **namunadagi qiymatni konstanta sifatida** aynan takrorlash; `PRP` va qolgan maydonlar ham yoy-boshli namunadagi kabi | 1 = Curve tasdiqlandi; 88 ning formulasi topilmadi → hisoblashga urinmaslik |
| Chiqish | `TOU = 0`, `AOU = 0` (None: perpendikulyar ko'tarilish) | namunaga mos; 0 haqiqiy qiymat |

* `TIN/AIN` ni stanok profilida **sozlanadigan** qilish (standart: chiziq → `9/0`, yoy → `1/88`): BiesseWorks da ham bu texnolog sozlamasi.
* Geometriyadan `AIN` hisoblash formulasini **qo'shmaslik** — hech bir manba buni tasdiqlamaydi; faqat boshqa burchak/radiusli yoy-boshli namunalar paydo bo'lsa va ularda qiymat 88 dan farq qilsa qayta ko'rish.
* Stanokda/BiesseWorks simulyatorida bir marta tekshirish: yoy-boshli konturda `TIN=1` qo'shimcha kirish yoyini chizadimi va asbob detalga kirib ketmaydimi.

### 4.2 Selco OSI `Chk`

1. **Soxta `Chk` hisoblamaslik va tasodifiy son yozmaslik.** Algoritm noma'lum; noto'g'ri qiymat ham, yo'q qiymat ham bir xil natija beradi (dastur ishga tushmaydi), lekin soxta son muammoni yashiradi.
2. Atributni **yozmaslik** (yoki profil sozlamasi bilan o'chiq) va OSI formatini UI da «sinovdan o'tmagan: dastur import bo'lishi, lekin bajarilmasligi mumkin» deb belgilash.
3. Ishonchli muqobillar (foydalanuvchi bilan kelishish): (a) shu stanok uchun **NC300** formatidan foydalanish (unda `Chk` yo'q, kesish dasturlari bir xil); (b) OSI optimizatoriga **detallar ro'yxatini** berish (`Chk` talab qilinmaydi, lekin kroyni OSI o'zi qiladi — bizning kroy yo'qoladi); (c) OSI ning CPOUT importi — format namunasi kerak.
4. Stanokda sinov (hal qiluvchi): bitta dasturni uch variantda import qilish — `Chk` siz, `Chk="0"`, asl `Chk` bilan lekin bitta `Cut@L` o'zgartirilgan — va qaysi biri «Run» ga ruxsat berishini yozib olish. Uchinchi variant `Chk` kesish ma'lumotiga bog'liqligini ko'rsatadi.
5. Algoritmni olishning qonuniy yo'li — **Biesse servisi** (XML importni baribir ular yoqadi) yoki OptiPlanning/OSI integratsiya hujjati so'rovi. Himoya kaliti emulyatorlari va shunga o'xshash manbalar ishlatilmaydi.

---

## 5. Hali ham javobsiz (foydalanuvchi / texnolog uchun)

1. `AIN = 88` — konstantami yoki hisoblanganmi (boshqa geometriyali yoy-boshli namuna kerak).
2. Curve kirishida yoy radiusi va `PRP=0` ning ma'nosi; 167-rasm (BiesseWorks qo'llanmasining to'liq PDF'i foydalanuvchida bo'lsa — «Lead-in Angle» bo'limi).
3. `Cut@Chk` algoritmi va qamrovi; OSI versiyasi.
4. Brauzerda qo'lda ko'rish mumkin bo'lgan, avtomatik ochilmagan sahifalar: 1-bo'lim oxiridagi ro'yxat (ayniqsa cnczone «BIESSE SELCO EB80 XML IMPORT» dagi zip namunalar — OptiCut XML da `Chk` bor-yo'qligini ko'rsatadi).
