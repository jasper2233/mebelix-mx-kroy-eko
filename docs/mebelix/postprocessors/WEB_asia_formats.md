# WEB tadqiqot: Osiyo / Turkiya / Italiya stanok fayl formatlari bo'yicha ochiq savollar

> Sana: 2026-10-04. Usul: WebSearch + WebFetch (ingliz, xitoy, turk, italyan, rus so'rovlari), ochiq sahifalar va
> GitHub. Login qilinmadi, bajariluvchi fayl yuklanmadi.
> **Umumiy xulosa:** 10 savoldan faqat 3 tasida (Daron `.ban`, KDT burg'ilash XML, HIRZT `.pd4` kelib chiqishi)
> jiddiy manba topildi; 3 tasida qisman/bilvosita dalil; qolgan 4 tasida internetda ochiq hujjat **yo'q**.
> Ishonch darajasi: **yuqori** = ishlab chiquvchining o'z hujjati; **o'rta** = uchinchi tomon hujjati / boshqa
> dastur qo'llanmasi; **past** = bilvosita xulosa yoki faqat qidiruv snippeti (sahifa ochilmadi).
> Iqtiboslar asl tilida, 15 so'zdan qisqa.

---

## 1. Nanxing NXCutSaw `.CUT` (AutoCUT XML ver=500) va `.ncp`

**JAVOB (past–o'rta, asosan topilmadi).**

* `.CUT` ildizidagi `AutoCUT` — Xitoyning «华信智能 / 王石软件 (King-Stone)» firmasining AutoCUT / AutoSAW
  optimizatori nomi; AutoSAW Nanxing va KDT arralarini qo'llab-quvvatlaydi. Ya'ni `.CUT` — Nanxing emas, AutoCUT
  oilasining formati (o'rta).
  * Dalil: «排版优化与锯切设备控制工业软件» — https://king-stone.com/?cat=10
  * Dalil: «为工程下料而生的排样优化系统» — https://king-stone.com/?cat=9
  * Qidiruv snippeti (sahifada tasdiqlanmadi, past): AutoSAW bilan birga «NxCutSaw, NXPareto» nomlari tilga olingan.
* `Sx/Sy`, `Flag`, `CutCount`, `Px/Py`, `Grouped`, `Turn` atributlarining rasmiy ta'rifi **topilmadi**.
* Torsovka (trim) qiymati format konstantasi emas, postprotsessor sozlamasi ekaniga bilvosita dalil: BAZIS-Raskroy
  qo'llanmasida Nanxing postprotsessori uchun alohida parametr bor (o'rta).
  * Dalil: «Поле Величина подреза внутренних полос позволяет задать значение параметра» —
    https://cdn.bazissoft.ru/documentation/ru/Cutting.pdf (10.40-bo'lim, Nanxing)
* Nanxing uchun boshqa formatlar ham mavjud (BAZIS 2023): FinChinaSoft boshqaruvi uchun `*.xml`, NCB boshqaruvi
  uchun `*.nc` (o'rta).
  * Dalil: «Добавлен постпроцессор для Nanxing с системой управления FinChinaSoft» —
    https://www.bazissoft.ru/bazis-news/innovations/1725-20230601-bazis2023
* Paket (kitob) balandligi va `.ncp` dagi Y-first kartalarda +kerf siljishi bo'yicha manba **topilmadi**.
  «Tongde» (同德) Nanxing versiyali optimizatori sahifasi «换向修边» (burilishdagi torsovka) ni eslatadi, lekin
  sahifa ochilmadi (past) — http://www.tomder.com/TDCutterSaw.aspx

**Generator uchun xulosa:** `Sx=Sy=5` ni qattiq yozmasdan sozlamaga chiqarish (standart 5); qolgan atributlar
(`Flag="True"`, `CutCount="0"`, `Grouped`, `Turn`) — namunadagidek ko'chirishda davom etish. Paket balandligi faylga
yozilmaydi deb qoldiriladi. `.ncp` dagi +3 siljish — faqat stanokda sinov bilan tasdiqlanadi.

---

## 2. KDT arra (KS-832/833, PreSize): XML, `.qk`/`.lbd`

**JAVOB (o'rta — qisman).**

* PreSize rasman uch formatni import qiladi: `.xml`, `.saw`, `.ptx` (o'rta; diler sahifasi).
  * Dalil: «Формат файлов: .xml, .saw, .ptx» —
    https://ligamac.ru/oborudovanie/product/formatno-raskroechnyy-tsentr-kdt-ks-832d/
  * `.qk` / `.lbd` hech bir ochiq manbada tilga olinmagan → bu PreSize'ning **ichki** (saqlash) formati bo'lishi
    ehtimoli katta (past, xulosa).
* KDT PreSize va Giben GVisionXP — bir oila («Presizing»): Promob Cut Pro'da bitta plagin ikkalasiga xizmat qiladi va
  u PTX orqali ishlaydi (o'rta).
  * Dalil: «Giben Presizing GVisionXP plugin to Giben-KDT Presizing Manager Cut Plugin» —
    https://suporte.promob.com/hc/en-us/articles/31123069471633-Promob-Cut-Pro-Release-Notes
  * Dalil: «New plugin for integration with PTX cutting manager - Giben» — o'sha sahifa (v1.2.4.25)
* BAZIS-Raskroy'da KDT uchun **uchta** postprotsessor bor: «KDT пильный центр (txt)», «KDT ФРС (XML)»,
  «KDT пильный центр (XML)» — versiyaga qarab tanlanadi; qaysi kontroller versiyasi qaysi birini o'qishi yozilmagan
  (o'rta).
  * Dalil: «для постпроцессоров KDT в формате XML» — https://cdn.bazissoft.ru/documentation/ru/Cutting.pdf (10.36–10.38)
* `trim="2.5"` (3-daraja va undan chuqur): BAZIS'da KDT XML uchun ham «Величина подреза внутренних полос»
  parametri bor → bu qiymat **postprotsessor sozlamasi**, format konstantasi emas (o'rta, xulosa).
* Qoldiqlar va etiketkalar ixtiyoriy: «Добавлять обрезки в управляющую программу», «Печатать бирки на детали /
  на обрезки», «Сохранять 1 бирку для каждого типоразмера панелей» opsiyalari (o'rta) — o'sha PDF, 10.38.
* `panelK`, `no.N`, `part type 1/2/3` semantikasi, etiketka rasmi talablari (464×484, PNG/EMF) — **topilmadi**.

**Generator uchun xulosa:** (a) `trim 2.5` ni sozlamaga chiqarish («ichki polosalar podrezi», standart 2.5);
(b) qoldiq yozish va etiketka — sozlanadigan opsiya; (c) **PTX eksportini** KDT PreSize va Giben GVisionXP uchun
zaxira/asosiy yo'l sifatida qo'shishni ko'rib chiqish — ochiq hujjatlangan format, ikkala stanok dasturi ham o'qiydi;
(d) `.qk/.lbd` ni faqat mavjud stanokda sinovdan o'tgan holda qoldirish.

---

## 3. KDT / Anderson burg'ilash `.xml` (AndersonXMLdata, WDX «trepan»)

**JAVOB (o'rta).** Qardosh dialekt — `KDTPanelFormat` (Promob «Flexdrill 1200» plagini chiqishi) 417 ta ishlab
chiqarish fayli asosida GitHub'da hujjatlangan. Maydon lug'ati bir xil (`TypeNo`, `Quadrant`, `Correction`,
`HoleNo`, `IntervalX/Y/Z`, `PlaneID`), lekin bu **uchinchi tomon teskari muhandisligi** (`NOT_TESTED`), rasmiy hujjat emas.
Manba: https://github.com/tiagofur/muebleria/pull/904 →
https://raw.githubusercontent.com/tiagofur/muebleria/main/docs/machines/kdt-xml-format.md

| Savol | Topilgan javob | Dalil (o'sha fayl) |
|---|---|---|
| `Quadrant` | **Fizik qirra raqami**: 1 = o'ng (X=L), 2 = chap (X=0), 3 = Y=W, 4 = Y=0 | «`1` Derecho / final `X1 = PanelLength`» |
| Baza burchagi | `KDTPanelFormat`da koordinata boshi chap-pastki burchak; baza qirrasi kontur cho'qqisida `AlignmentFace` bilan belgilanadi | «Origen `(0, 0)`: esquina inferior izquierda de la pieza» |
| `Correction` | 0 = markaz, 1 = chap, 2 = o'ng (Path uchun). Diqqat: shu hujjatning Line misolida teskari izoh bor (1 = o'ng, 2 = chap) — manba o'zi ziddiyatli | «`1` Fresa a la izquierda de la dirección de avance» |
| Yopiq kontur / cho'ntak | `TypeNo 7 Path` + `Close` 1/0; `TypeNo 6 Rect` + `Empty`; `TypeNo 5 Circle` (`CenterX/Y`, `Radius`) | «`1` = camino cerrado (recorte); `0` = abierto» |
| `HoleNo` / `Interval*` | «naqshdagi teshiklar soni» va «qadam» deb izohlangan, lekin 417 faylda doim 1/0 — tasdiqlanmagan | «número de agujeros en patrón (siempre 1 en muestra)» |
| Yoy > 180°, `Direction` | topilmadi (`Arc` u namunada umuman uchramagan; `Vertex/Bulge` maydoni bor) | «≠0 = arco (no observado en muestra)» |
| Pazning chetdan chiqishi | manfiy / L dan katta koordinata ruxsat etilgan | «`BeginX < 0` y `EndX > PanelLength` son intencionales» |

* Bizning `AndersonXMLdata` bilan solishtirish: bizda `Quadrant 1 ↔ X1=0`, ularda `Quadrant 1 ↔ X1=L`. Bu zid emas —
  bizning dialektda X o'ng qirradan o'lchanadi (X1 = L − x), ya'ni ikkalasida ham **Quadrant 1 = fizik o'ng qirra**.
  Demak `Quadrant` koordinataga emas, qirraga bog'liq (o'rta, xulosa).
* Bizdagi `TypeNo 4 Arc` Promob namunasida yo'q (ularda «TypeNo 4 kuzatilmadi») — bizning namunalar bu bo'shliqni to'ldiradi.
* KDT olti tomonlama stanoklari XML'dan tashqari boshqa formatlarni ham o'qiydi (past; qidiruv snippeti, diler
  sahifasi 403 berdi): «.xml, .pdx, .mpr, .dxf, .bpp» va «SCX, BAN» —
  https://stancomplect.com/en/kdt-drilling-centers-high-precision-solutions-for-the-furniture-industry

**Generator uchun xulosa:** Quadrant jadvalimiz to'g'ri (fizik qirra). Massiv teshiklarni **alohida yozishda davom
etish** (`HoleNo=1`) — massiv semantikasi hech qayerda tasdiqlanmagan. Orqa tomonda `Correction` 1↔2 almashuvi
bo'yicha manba ziddiyatli → stanokda bitta sinov detali shart. Yopiq kontur/cho'ntak kerak bo'lsa `TypeNo 7 Path
(Close=1)` / `TypeNo 6 Rect` nomzod, lekin `AndersonXMLdata` dialektida ishlashi tasdiqlanmagan.

---

## 4. Giben `.fdt` (G57 / GVisionXP), G-Drive `.DAX/.CPX`

**JAVOB (topilmadi; faqat atrof-muhit faktlari, o'rta).**

* `.fdt`, `.DAX`, `.CPX`, `TIPOTG`, `RUOTATO`, `Tg_Ed`, `ALTEZZAPACCO` — hech bir ochiq manbada (ingliz, italyan, rus)
  uchramadi. `0xFC` ni ekranlash qoidasi **topilmadi**.
* GVision versiyaga bog'liq: Promob plaginida «Gvision Version» tanlovi bor; GVisionXP PTX ni ham qabul qiladi (o'rta).
  * Dalil: «Available the Gvision Version option, where you can inform the manager version» —
    https://suporte.promob.com/hc/en-us/articles/31123069471633-Promob-Cut-Pro-Release-Notes
* Giben «Gplan» integratsiyasida torsovka detal tomonlari bo'yicha sozlanadi, etiketka `.lbl` + `.FST` shablon bilan
  GVision'ga import qilinadi (o'rta).
  * Dalil: «In the Trim fields, define the value of the trims» —
    https://suporte.promob.com/hc/en-us/articles/31122096624657-Plugin-Builder-Gplan-Integration
* GibLab ro'yxatida aynan ikki Giben postprotsessori bor: «Giben (GVisionXP)» va «Giben (G57)» —
  https://service.giblab.com/help/datasheet_ru.html

**Generator uchun xulosa:** `.fdt`/`.DAX`/`.CPX` da bayt-ma-bayt nusxa strategiyasi saqlanadi. `0xFC` uchraydigan 10 ta
o'lcham (589, 720, 851, 1441, 1572, 1703, 1834, 2424, 2555, 2686 mm) uchun generator **ogohlantirish** chiqarsin
(yoki sozlama orqali bloklasin) — stanokda sinovsiz ishonib bo'lmaydi. GVisionXP uchun PTX — muqobil yo'l.

---

## 5. AES Alpha `.ss`

**JAVOB (past — format hujjati topilmadi).**

* Yagona iz: OptiCut'da «BSA (AES Alpha, Mizrak Makine)» nomli postprotsessor bor; BSA — Turkiyadagi «BSA Makine İnş.
  ve Bilgisayar» (OptiCut distribyutori). Ya'ni `.ss` — AES va Mızrak arralari uchun umumiy «BSA» formati (o'rta).
  * Dalil (qidiruv natijasi; sahifa bot-himoyasi ortida): «BSA (AES Alpha, Mizrak Makine)» —
    https://wooddesigner.org/help-centre/opticut-integration-cnc-saw/
  * https://www.globalpiyasa.com/en/product-detail/opticut-program-bsa-makine-ins-ve-bilgisayar/82836
* Yozuv turlari — turkcha qisqartmalar bo'lishi ehtimoli (past, **lingvistik taxmin, manbasiz**): BSL = *Başlık*
  (sarlavha), KON = *Kontrol/Konfigürasyon*, LMT = *Limit*, OZL = *Özellik* (list xususiyati), URN = *Ürün* (detal),
  PRT = *Parti/Parça*, PNL = *Panel* (karta), KES = *Kesim* (kesim).
* `-0.50` (3/4-daraja), OZL1 dagi 4 ta trim, PRT4, matn kodlashi — **topilmadi**. Format turkcha ekanidan kelib chiqib
  ASCII bo'lmagan matn uchun Windows-1254 ehtimoli bor, lekin bu tasdiqlanmagan (past).

**Generator uchun xulosa:** hech narsa o'zgartirilmaydi; nomlarni ASCII ga transliteratsiya qilish xavfsiz yo'l
(BAZIS ham umumiy «Транслитерация национальных символов в управляющих программах» opsiyasini beradi —
https://cdn.bazissoft.ru/documentation/ru/Cutting.pdf, 10.14). Aniq javob uchun BSA Makine yoki AES servisiga
murojaat kerak.

---

## 6. FastPanel `.ocm` (ManualPattern XML)

**JAVOB: topilmadi.** «FastPanel» qidiruvi faqat xosting boshqaruv paneli (FASTPANEL) natijalarini beradi; `.ocm`,
`ManualPattern`, `TrimSize` bo'yicha hech qanday ochiq hujjat yo'q. Yagona tasdiq — GibLab'da «Пильный центр
(FastPanel)» postprotsessori mavjud (https://service.giblab.com/help/datasheet_ru.html).

**Generator uchun xulosa:** `TrimSize` bir tomonlama/ikki tomonlama va maksimal daraja — faqat stanokda sinov;
3 darajadan chuqur kartalarni bu postprotsessorda **ogohlantirish bilan** chiqarish.

---

## 7. Daron FoxCNC / MicroDraw `.ban`

**JAVOB (yuqori — ishlab chiquvchining rasmiy spetsifikatsiyasi topildi).** «BAN格式定义说明 V3.0, MicroDraw Tech,
2015.11.21»: https://www.cnblogs.com/asuo/p/5225938.html (V2.0: https://www.cnblogs.com/asuo/p/5224008.html)

| Savol | Javob | Dalil |
|---|---|---|
| `Grain` | 3 qiymat: yo'q / gorizontal / vertikal. (Spetsifikatsiya matnida `DIR_NODE` deb xato yozilgan, misolda `DIR_NONE`.) | «DIR_NODE没有 DIR_HOR 横纹 DIR_VER竖纹» |
| `Grain` vazifasi | Faqat operatorga ko'rsatma — ishlov berishga ta'sir qilmaydi | «纹路材质封边等信息可以作为参照提示工人如何放板及翻板加工» |
| `<Outline>` | Detal tashqi konturi; shaklli detalda ko'p nuqtali | «如果是异形板件，会有多个坐标信息» |
| O'lchamlar | Kromka bilan birga (tayyor o'lcham) | «板的尺寸包含了封边厚度» |
| Baza / Z | Old yuz (A) = Z 0; vertikal teshik Z 0 dan manfiyga | «板的正面（A面）为基准面，即Z=0» |
| Orqa yuz | Spetsifikatsiyada bitta faylda `Face="B"`, Start Z = −T; ag'darish `-auto` bilan | «反面孔的起点Z为板厚度*-1» |
| Yoy (`SlotA`) | Start→End **doim soat miliga teskari** — bizning xulosamiz tasdiqlandi | «起点到终点必须是逆时针方向» |
| `EdgeFBLR` | Kromka qalinligi: old, orqa, chap, o'ng | «封边厚度，顺序为前后左右» |
| `PlaneSize` | 1 = bir tomonlama, 2 = ikki tomonlama burg'ilash | «单面打孔1 双面打孔2» |
| `IsCuted` | 0 = ishlanmagan, 1 = ishlangan, −1 = taqiqlangan | «没有加工0 加工过1 禁止加工-1» |
| Qirra teshigi | `Face` L/R/U/D; L/R da Y teng, U/D da X teng, Z teng | «水平孔的起点Z和终点Z必须相等» |
| Paz/freza | `SlotL` (chiziq), `SlotA` (yoy), `SlotS` (polilniya, `PtCout`); markaz chizig'i bo'yicha | «以槽的中心线来定义» |
| `Width="0"` | Burchak kesish / chet frezasi (切角) | «如果槽宽度为0；则表示为切角» |
| Yuzlar | A old, B orqa, L chap, R o'ng, U yuqori, D past | «正面A 背面B 左面L 右面R 上面U 下面D» |

* Baza burchagi: spetsifikatsiya misolida koordinatalar **musbat**, boshi (0,0) burchakda, `Face="L"` — X=0,
  `Face="R"` — X=Width, `D` — Y=0, `U` — Y=Hight. Bizning fayllarimizdagi manfiy X (x − L) va `MachineBase="-1"`
  spetsifikatsiyada **yo'q** — bu FoxCNC/GibLab moslamasi (o'rta, xulosa).
* Cho'ntak (pocket) va asbob korreksiyasi spetsifikatsiyada yo'q — faqat markaz chizig'i + `Width`.
* Kodlash haqida hech narsa deyilmagan.

**Generator uchun xulosa:** (1) `Grain` ni tekstura yo'nalishi bo'yicha `DIR_HOR`/`DIR_VER`/`DIR_NONE` yozish mumkin —
faqat ma'lumot uchun, 3183 dagi farq xavfsiz; (2) `<Outline>` rasmiy maydon — shaklli detalda haqiqiy kontur
yozilgani ma'qul, to'rtburchak ham sintaktik to'g'ri; (3) yoylarni har doim CCW yozish qoidasi — rasmiy talab;
(4) manfiy X konvensiyasini o'zgartirmaslik (namunalarga mos), lekin sozlamada «musbat X (spetsifikatsiya bo'yicha)»
varianti foydali bo'lishi mumkin; (5) massiv teshiklarni alohida `HoleV` qilib yoyish to'g'ri — formatda massiv yo'q;
(6) cho'ntakni `SlotS`/`SlotL` yo'llari bilan yoyish kerak.

---

## 8. HIRZT MAGI `.pd4` (CID3)

**JAVOB (o'rta — format kelib chiqishi aniqlandi; kodlar jadvali topilmadi).**

* `.pd4` — HIRZT'ning o'z formati emas, **CNI «iLENIA CAD/4»** (CAD-CAM 4) dasturining loyiha fayli. HIRZT stanoklari
  (masalan LIVRA 4) iLENIA / CNiMusa boshqaruvida ishlaydi. HIRZT 2017 yilda MAGGI tomonidan sotib olingan.
  * Dalil: «HIRZT LIVRA 4 Machine - iLENiA software CNiMusa» —
    https://en.industryarena.com/forum/hirzt-livra-4-machine-ilenia-software-cnimusa-constructor-password--457633.html
  * Dalil: «CNI ILENIA CAD-CAM 4» — https://wtp.hoechsmann.com/en/lexikon/28907/cni_ilenia_cad-cam_4
  * Dalil: «Hirzt Srl was acquired by MAGGI in 2017» — https://wtp.hoechsmann.com/en/lexikon/13772/HIRZT
* CAD/4 frezalash/interpolyatsiyani ham qo'llab-quvvatlaydi (qidiruv snippeti; sahifalar 403, past) — demak formatda
  freza sintaksisi **bor**, shunchaki GibLab uni chiqarmaydi.
  * Qo'llanma mavjud, lekin ochilmadi: «Cad/4 User Manual Version 1.5» — https://www.scribd.com/document/931143025/CAD4
  * DXF import mavzusi: https://en.cncarena.com/forums/uncategorised-cad-discussion/354658-cnc-manufacturing-software.html
* `#TYPE` 1/2/3 kodlari, freza makrosi nomi, paz qaysi bo'limdan o'qilishi (PARAMETRIC `Saw` vs `BLOCK LINE`) —
  **topilmadi**.

**Generator uchun xulosa:** format o'zgarmaydi. `#TYPE` chegarasi va freza sintaksisi uchun eng tez yo'l — stanokdagi
CAD/4 da qo'lda 3 ta teshik (ko'r 12 mm, o'tuvchi, 15 mm) va bitta freza konturi chizib `.pd4` ni saqlash; yoki
Scribd'dagi «Cad/4 User Manual 1.5» ni foydalanuvchi o'zi yuklab olishi. CAD/4 ochganda PARAMETRIC bo'lim qayta
hisoblanadi degan taxmin (BLOCK — hosila) hali tasdiqlanmagan.

---

## 9. XD WoodCam `.wxf`

**JAVOB: topilmadi.** Yagona iz — «筑木» mebel loyihalash tizimining plaginlar do'konida «XDWoodCam (*.wxf)»
postprotsessori mavjudligi (qidiruv snippeti; sayt sertifikati eskirgan, ochilmadi) — http://www.zhumu.pro/store.
Paz (arra) sintaksisi, `Num/Dx/Dy` massivlari, baza burchagi bo'yicha ochiq hujjat yo'q.

**Generator uchun xulosa:** pazni hozircha chiqarmaslik yoki sozlama orqali freza konturi sifatida chiqarish;
massivlarni alohida teshiklarga yoyish. Aniq javob uchun stanokdagi XDWoodCam'da qo'lda paz chizib saqlangan `.wxf`
namunasi kerak.

---

## 10. Syntec SyntecCad `.scx`

**JAVOB: topilmadi.** «SyntecCad» va `.scx` bo'yicha ochiq hujjat yo'q (Syntec materiallari faqat CNC kontroller,
RemoteAPI haqida). Faqat bilvosita fakt: SCX — olti tomonlama stanoklar orasida umumiy almashinuv formatlaridan biri
(KDT stanoklari ham «SCX, BAN» o'qiydi — qidiruv snippeti, past). `Cad` atributi tekshirilishi, `Closed`/`Pocket`,
`ToolOffset` 中/左/右 semantikasi bo'yicha manba yo'q (中 = markaz, 左 = chap, 右 = o'ng — faqat so'zma-so'z tarjima).

**Generator uchun xulosa:** `Cad="MebeliX"` bilan faylni stanokda **bir marta sinash** — yagona yo'l; sinovgacha
atribut qiymatini sozlamada o'zgartiriladigan qilish. `Closed`/`Pocket` ni namunadagidek `0` qoldirish.

---

## Tavsiya etilgan o'zgarishlar (qisqa)

1. **Trim sozlamalari:** Nanxing `Sx/Sy` (5), KDT XML `trim` (2.5), FastPanel `TrimSize` (5) — qattiq konstanta emas,
   postprotsessor sozlamasi (BAZIS'dagi «ichki polosalar podrezi» analogi).
2. **KDT / Giben uchun PTX eksporti** — PreSize (`.xml, .saw, .ptx`) va GVisionXP PTX ni o'qiydi; `.qk/.lbd` va `.fdt`
   ga muqobil.
3. **Daron `.ban`:** `Grain` uch qiymatli (`DIR_VER` qo'shish), yoylar doim CCW, `Outline` — haqiqiy kontur.
4. **KDT burg'ilash XML:** `Quadrant` = fizik qirra (jadvalimiz to'g'ri); massivlar yoyilgan holda qoladi.
5. **Giben G-Drive:** `0xFC` baytli 10 ta o'lchamda ogohlantirish.
6. **Kodlash:** barcha formatlarda ASCII bo'lmagan nomlar uchun transliteratsiya opsiyasi (standart: yoqilgan).

---

## JAVOB TOPILMADI

1. Nanxing `.CUT`: `Sx/Sy` qaysi chet(lar)ga tegishli, `Flag`, `CutCount`, `Px/Py` boshi, `Grouped`, `Turn` ta'rifi.
2. Nanxing: paket balandligi qayerda beriladi; `.ncp` Y-first kartalarda +kerf siljishi to'g'riligi.
3. KDT arra XML: `panelK`, `no.N`, `part type 1/2/3` rasmiy ma'nosi; `id` va `O<n>` raqamlash qoidasi.
4. KDT `.qk` / `.lbd`: format hujjati, qaysi PreSize versiyasi qaysi birini o'qishi; etiketka blobi va rasm talablari.
5. KDT burg'ilash XML: 180° dan katta yoy / to'liq aylana, `Direction` rasmiy ta'rifi, `HoleNo/Interval` ishlashi,
   orqa tomonda `Correction` (manba o'zi ziddiyatli), `Mirror`, `UseSaw`.
6. Giben: `.fdt` / `.DAX` / `.CPX` hujjati, `TIPOTG` darajalari, `RUOTATO`, `0xFC` ekranlash, «axlat» konstantalar.
7. AES Alpha `.ss`: barcha yozuv maydonlari (BSL/KON/LMT/OZL/URN/PRT/PNL/KES), `-0.50`, OZL1 trimlari, PRT4, kodlash.
8. FastPanel `.ocm`: `TrimSize` tomoni, maksimal daraja, kodlash, dastur ishlab chiqaruvchisi.
9. Daron: FoxCNC'ning haqiqiy baza burchagi va `MachineBase="-1"` ma'nosi, kodlash, stanok `Outline`ni ishlatadimi.
10. HIRZT `.pd4`: `#TYPE`/`TYP` kodlar jadvali, freza makrosi sintaksisi, paz o'qiladigan bo'lim, `CREA_SPACE`, `REL`.
11. XD WoodCam `.wxf`: paz sintaksisi, `Num/Dx/Dy`, `Ref`, `ImageX/Y/XY`, baza burchagi.
12. Syntec `.scx`: `Cad` tekshiruvi, `Closed`/`Pocket`, `ToolOffset` tomoni orqa yuzda, `Outline` konvensiyasi.

Ochilmagan, lekin foydali bo'lishi mumkin bo'lgan manbalar (403 / login / bot-himoya): Scribd «Cad/4 User Manual 1.5»;
wooddesigner.org OptiCut postprotsessorlar ro'yxati; zhihu «BanCAD» maqolasi; CSDN «六面钻调试» turkumi
(https://blog.csdn.net/weixin_42584545/article/details/131067189); tomder.com Nanxing versiyasi.
