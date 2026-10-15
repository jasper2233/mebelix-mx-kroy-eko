# 03 — EL, GR, O, LB, katalog, ifodalar tili va interfeys komponentlari: funksiyalar inventari

> Sana: 2026-10-02 · Holat: birinchi to'liq versiya · Til: o'zbek (lotin), rus atamalari qavsda.
> Maqsad: GibLab yordamidagi **(EL) Кромкооблицовка, (GR) Пазование, (O) Комплектация и другие действия, (LB) Этикетки**,
> «Товары» katalogi, **ifodalar tili (expression)**, xizmat API va interfeys komponentlari bo'yicha funksional inventar
> hamda MebeliX Kroy bilan solishtirish. Bizning kod o'zgartirilmagan.

## 0. Qanday tuzilgan (manba, belgilar, cheklovlar)

**Manba.** Faqat `C:\GibLabLocal\pages\help\` ostidagi yordam sahifalari (EL, GR, O, LB, `labels_ru`, `goods_ru`, `service/*`,
`expression/*`, `development/*`, `formatPattern_ru`) va ularga biriktirilgan rasmlar (`images/labels/*`, `images/goods_ru/*`,
`images/operations/el_params1.png`, `lb_params1.png`, `images/site/groove.png`). GUI ishlatilmadi; dastur, kalit, `.exe/.dll/.jar/.rpc` va `.lbl` fayllariga
tegilmadi. Hamma matn **o'z so'zlarim bilan**; ekrandagi rus nomlari saqlangan; yordamdagi qisqa misol qiymatlari faqat
test-vektor sifatida (funksional ma'no) keltirilgan.

**Muhim ogohlantirish — LB yordami deyarli bo'sh.** LB sahifasida «Раздел заполняется» deb yozilgan: parametr nomlari bor,
tushuntirishlar yo'q (`formatPattern_ru.html` ham bo'sh). Shu sababli LB parametrlarining ma'nosi (a) nomidan, (b) `lb_params1.png`
sxemasidan, (c) `images/labels/*.png` skrinshotlaridan, (d) avvalgi jonli kuzatuvlarimizdan (`G_IMPORT_GIBLAB_PROJECT.md §G4`,
`H_REPORTS_LABELS.md §H5`) olindi. Faqat nomga tayangan joylar **❓** yoki «taxmin» deb belgilangan.

**Belgilar.**

| Belgi | Ma'nosi |
|---|---|
| ✅ | bizda bor va ma'nosi mos |
| 🟡 | qisman: hisob bor lekin UI yo'q / ma'no farq qiladi / soddalashtirilgan |
| ❌ | yo'q |
| ❓ | ma'nosi yordamdan aniq emas yoki bizda holati tekshirilmagan — foydalanuvchi/test kerak |

**Murakkablik**: S ≤ 0.5 kun · M 1–3 kun · L > 3 kun (bitta dasturchi, testlar bilan). **Ustuvorlik**: H — xodimlar kundalik ishiga
yoki boshqa funksiyalarga to'siq; M — kerak, lekin kutishi mumkin; L — qulaylik / kam ishlatiladi.

**Dalil qisqartmalari.** `Y:` — GibLab yordam sahifasi: `Y:el`, `Y:gr`, `Y:o`, `Y:lb` = `operations/{el,gr,o,lb}_ru.html`;
`Y:labels` = `labels_ru.html`; `Y:goods` = `goods_ru.html`; `Y:cat` = `service/catalog_ru.html`; `Y:cont` = `service/content_ru.html`;
`Y:types|expr|math|bool|str` = `expression/{types,expression,mathExpression,boolExpression,stringExpression}.html`;
`Y:fmath|fstr|ffmt|fmisc|fnow|fnum` = `expression/fuctions/{math,string,format,misc,now,numericConversion}…html`;
`Y:grid|btn|bar` = `development/{ParamGrid,button,ToolBar}_ru.html`. `R:` — rasm: `R:lb1`, `R:lb2`, `R:lb3`, `R:lb11`, `R:lb12` = `images/labels/<n>.png`;
`R:lbp` = `images/operations/lb_params1.png`; `R:el1` = `images/operations/el_params1.png`; `R:grv` = `images/site/groove.png`;
`R:cvb`, `R:cvb1` … `R:cvb9` = `images/goods_ru/cvb*.png`. Bizning hujjatlar: `B6`, `K4`, `H5`, `J3`, `D9` va h.k. —
`docs/mebelix/` dagi bo'limlar. Kod yo'llari `backend/app/…`, `frontend/src/…` ga nisbatan.

## 1. Qisqa xulosa

**(EL) Кромкооблицовка.** Yordamda 8 ta material parametri, 7 ta narx maydoni, «Детали» jadvali (8 ustun), chop (2 katak) va 2 ta
amal bor. Hammasi bizda ishlaydi (`ELParams`, `calc.edge_usage`, `ElPanel.tsx`); kromka metri GibLab saqlangan natijalariga 303/303
mos. Yordamda yo'q, lekin jonli GibLab'da kuzatilgan qo'shimchalar ham bor (yaxlitlash kodlari, «Линии маркировки», «Учитывать
материал», min. perpendikulyar tomon). Qolgan kamchiliklar kichik: kontekst yordami («?» har parametr yonida), detal jadvalida
Ctrl+Space / saralash, kromka stanogi parametri (importda bor, yordamda yo'q — ❓).

**(GR) Пазование.** Yordamda: W/D/O sxemasi, arra qalinligi (o'tishlar soni), narx bloki (Цена метра паза, Длина пазования, Стоимость),
«Детали» jadvali (10 ustun).
Hisob (`calc.groove_usage`) va hisobot bloki bor, lekin **UI chala**: panelda arra qalinligi, «Отступ включительно», hisoblangan
uzunlik/narx, «umumiy parametrlarni saqlash» yo'q; «Детали» faqat oddiy ro'yxat; chop sozlamasida GR bo'limi yo'q. Standart
qiymatlar (10/16) v2 spetsifikatsiyasidan (8/10) farq qiladi.

**(O) Комплектация и другие действия.** Bizda **yo'q**: `OpType.O` enumda bor, lekin UI o'chirilgan («tez orada»), modeli, hisobi,
hisobot ta'siri va Bazis/`.project` importi yo'q. Operatsiya soddaligi bilan ajralib turadi: egasi (loyiha/mahsulot) + materiallar
jadvali (Код, Наименование, Ед.И, Кол, Цена) + qo'lda ish narxi + izoh. Hajmi ≈ 2–3 kun; ombor talabnomasi va mahsulot narxiga
ta'sir qiladi. To'liq spetsifikatsiya — §3.

**(LB) Этикетки.** GibLab'da LB — alohida operatsiya: 8 ta sahifa parametri (manba, o'lcham, ustun, qator, oraliq, maydon, chegara,
soni) + detal/qoldiq/mahsulot bayroqlari + foydalanuvchi ma'lumotlari jadvali; «Шаблон» yorlig'ida vektor redaktor (13 chizma
buyrug'i + Com/Par/Var/Set/IF/Else/WD/DW boshqaruvi), **104 ta standart o'zgaruvchi**, ifodali pozitsiya/mazmun, shablon kutubxonasi
(papkalar, miniatyuralar, `.lbl` fayl). Bizda: global `LabelSettings` (o'lcham, ustun, 4 bayroq) va **qat'iy** QR-shablon, faqat CS
detallari. Ya'ni foydalanuvchi shabloni, o'zgaruvchilar, qoldiq/mahsulot etiketkasi, shtrixkod turlari, kutubxona — hammasi
yo'q. Taklif: 3 bosqich (§4) — avval LB operatsiya parametrlari, so'ng JSON shablon + render, so'ng vizual redaktor.

**Ifodalar tili.** GibLab: tipli (integer 32-bit, double, boolean, string, null), Java-uslubidagi semantika (butun bo'lish, `round` yarimni
yuqoriga, `DecimalFormat`/`SimpleDateFormat` naqshlari), **67 ta nomlangan funksiya/konstanta** (30 matematik, 25 satr, 5 aralash,
7 sonli konvertatsiya). Bizda `xnc.py::eval_expr` — faqat float, Python sintaksisi (`a if c else b`, `**`), 10 funksiya, trigonometriya
**gradusda**. Farqlar §5 da; umumiy dvigatel kerak, chunki LB shablonlari, ustun formulalari va XNC bir xil tilga tayanadi.

**«Товары» katalogi.** Excel-fayl (10 ustun, ota-ID orqali daraxt, `isfolder` bayrog'i) + sozlash dialogi (ustun xaritasi, boshlang'ich
qator, ildiz kategoriyalar: list / pogonaj / kromka / sirt) + xizmat API (`catalogGet/Search` — ota papka va operatsiya turi bo'yicha).
Bizda: `catalog_items` jadvali (daraxtni saqlaydi), Excel/CSV import, MES sinxroni, yassi ro'yxat oynasi. Yo'q: daraxt ko'rinishi,
rasm, ildiz kategoriya sozlamasi, `isfolder`/`Изображение`/`Параметры` ustunlari, `.xls`.

**Xizmat API va interfeys komponentlari.** `content*` (7 amal: saqlash/papka/ko'chirish/o'chirish/nomlash/yuklash/ro'yxat, tur:
`project|xnc|label`, miniatyura o'lchami) — GibLab shablonlari va loyihalari uchun umumiy ombor; bizda faqat loyihalar. `ParamGrid`
(deklarativ parametr to'ri: guruhlar, ifodali `visible/suffix/readOnly`, 18 tur), `ToolBar`, `button` (fayl tugmalari) — bizda
qo'lda yozilgan React formalar; LB/XNC redaktori xossalar paneli uchun sxemaga asoslangan forma kerak bo'ladi.

**Hisob (avtomatik sanalgan, §2 jadvallari bo'yicha).**

| Bo'lim | Jami | ✅ | 🟡 | ❌ | ❓ |
|---|---|---|---|---|---|
| (EL) Кромкооблицовка | 27 | 24 | 1 | 1 | 1 |
| (GR) Пазование | 15 | 3 | 9 | 2 | 1 |
| (O) Комплектация | 17 | 0 | 1 | 15 | 1 |
| (LB) Этикетки (parametr, redaktor, o'zgaruvchi, tavsiya) | 76 | 3 | 18 | 53 | 2 |
| «Товары» katalogi va xizmat API | 15 | 3 | 9 | 3 | 0 |
| Ifodalar tili | 74 | 14 | 14 | 44 | 2 |
| Interfeys komponentlari | 26 | 8 | 11 | 6 | 1 |
| **Jami** | **250** | **55** | **63** | **124** | **8** |

Eslatma: «jami» — §2 jadvallaridagi qatorlar soni (bitta qator = bitta funksiya yoki bir xil ma'noli guruh). Ifodalar tilidagi 67 ta nomlangan funksiya/konstanta §2.10 da 43 qatorga guruhlangan (ulardan 7 tasi `format`/`now` naqsh belgilari); LB ning 104 ta standart o'zgaruvchisi §2.6 da 13 qatorga guruhlangan.

## 2. Funksiyalar jadvali

Har bo'lim alohida jadval; ID bo'yicha qidirish oson bo'lishi uchun bitta qator = bitta funksiya (yoki bir xil ma'noli guruh).
«Bizda» ustunida UI va hisob alohida baholangan bo'lsa — izohda yozilgan.

### 2.1 (EL) Кромкооблицовка

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| EL-001 | Ширина (kromka eni) | Kromka lentasi yoki profilining eni. Yordamda faqat o'lcham deb ta'riflangan; hisobga ta'siri aniq aytilmagan (ma'lumot; katalogdan keladi) | mm; bizda 19 | ✅ | Y:el; `models.py::ELParams.width`; `ElPanel.tsx` | S | L |
| EL-002 | Толщина (kromka qalinligi) | Kromka qalinligi; kromkalangan tomonda tayyor detal o'lchamiga qo'shiladi (B2 formulasi) | mm; bizda 0 (korxona loyihalarida shunday — ochiq savol §7) | ✅ | Y:el; B2; `services/sizes.py` | S | M |
| EL-003 | Ширина прифуговки | Kromka yopishtirishdan oldin detal chetini frezalab oladigan qatlam eni; «заготовка» va «после прифуговки» o'lchamlariga ta'sir qiladi | mm; bizda 0 | ✅ | Y:el; B2; `ELParams.jointing_width` | S | M |
| EL-004 | Процент отхода кромки | Yopishtirish paytidagi qo'shimcha sarf: material uzunligi × (1 + %/100) | %; bizda 0 | ✅ | Y:el; B6; `calc.edge_usage` | S | M |
| EL-005 | Длина остатка по краям | Stanok har kromkalangan tomonning har ikki uchidan kesib tashlaydigan uzunlik → tomonga 2 × qiymat qo'shiladi (yordam misoli: 1000 mm tomon, 20 → 1040 mm) | mm; bizda 20 | ✅ | Y:el; B6; `ELParams.overhang` | S | M |
| EL-006 | Мин. оклеиваемая длина | Tomon bundan qisqa bo'lsa, material hisobi shu qiymat bilan olinadi (ish uzunligi — haqiqiy) | mm; bizda 100 | ✅ | Y:el; B6; `ELParams.min_glue_length` | S | M |
| EL-007 | Символ для обозначения | Kromkalangan tomonni kroy kartasi va etiketkada belgilovchi belgi (A, B, …) | 1 belgi; bizda «A», yangisi avto A,B,C… | ✅ | Y:el; D3; `ELParams.symbol` | S | L |
| EL-008 | Цвет для обозначения | Detallar jadvalida kromka nomini shu rang bilan ajratib ko'rsatadi | rang; bizda `#000000` (= standart rang) | ✅ | Y:el; `cs/columns.tsx:81` | S | L |
| EL-009 | Линии маркировки | Kartada/etiketkada kromka chizig'i soni (yordamda yo'q; jonli GUI) | 0..3; bizda 1 | ✅ | D9 / screens_v2/42; `ELParams.marker_lines`; `labels.py::_edge_icon` | S | L |
| EL-010 | Учитывать материал | Belgi o'chiq bo'lsa material narxi hisoblanmaydi, faqat ish (yordamda yo'q; jonli GUI) | bool; bizda ✓ | ✅ | B6; `ELParams.count_material` | S | L |
| EL-011 | Мин. размер стороны ⟂ kromka | Kromkalanadigan tomonga perpendikulyar tomon bundan tor bo'lsa ogohlantirish (yordamda yo'q) | mm; bizda 40 | ✅ | B6; `edge_usage.narrow`; `ElPanel.tsx` | S | L |
| EL-012 | Округление длины материала | Material metrini yaxlitlash: 15 variant (kod = o'nlik xona×10 + rejim: 0 yaqiniga, 1 kattaga, 2 kichikka) (yordamda yo'q) | bizda 20 ([0.00] yaqiniga) | ✅ | D9; `calc.round_code` | S | L |
| EL-013 | Округление длины кромкования | Ish metrini yaxlitlash, xuddi shu kodlar bilan | bizda 20 | ✅ | D9; `ELParams.work_round` | S | L |
| EL-014 | Kromka stanogi (tool1) | `.project` faylida EL operatsiyasi uchun stanok maydoni bor (yordamda yo'q); bizda saqlanmaydi | ? | ❓ | G_IMPORT §G4 (EL: tool1) | S | L |
| EL-015 | Цена материала | 1 m kromka narxi | pul/m; bizda 0 | ✅ | Y:el; `ELParams.price` | S | M |
| EL-016 | Количество материала | Jami kromka sarfi (m): Σ (max(tomon, min. uzunlik) + 2×qoldiq) × soni × (1+chiqindi%) | m; hisoblanadi | ✅ | Y:el; B6; `calc.edge_usage` | S | H |
| EL-017 | Стоимость материала | Sarf × 1 m narxi (yordamda formula xato yozilgan — «Кол-во × Кол-во», aslida × Цена) | pul | ✅ | Y:el; `edge_usage` → `cost_material` | S | M |
| EL-018 | Цена метра оклейки | 1 m kromkalash ishi narxi | pul/m; bizda 0 | ✅ | Y:el; `ELParams.op_price` | S | M |
| EL-019 | Длина оклейки | Kromkalangan tomonlar yig'indisi (chiqindi, qoldiq va min. uzunliksiz) — ish uzunligi | m; hisoblanadi | ✅ | Y:el; B6 (tekshirilgan: 10.4 m) | S | H |
| EL-020 | Стоимость операции | Ish narxi × ish uzunligi | pul | ✅ | Y:el; `edge_usage` → `cost_operation` | S | M |
| EL-021 | Стоимость (jami) | Material + operatsiya | pul | ✅ | Y:el; `ElPanel.tsx` | S | M |
| EL-022 | Сохранить параметры по умолчанию | Joriy parametrlarni yangi EL operatsiyalari uchun standart qilib saqlaydi (belgi/rang saqlanmaydi — avto) | scope `el_defaults` | ✅ | Y:el; `services/settings.py` | S | L |
| EL-023 | Справка (F1) | Panel yordamini ochadi; GibLab'da har parametr yonida ham «?» bor | F1 | 🟡 | Y:el; D0.2; `ElPanel.tsx` (faqat umumiy «Справка») | M | L |
| EL-024 | «Детали» yorlig'i | Shu kromka ishlatilgan detallar ro'yxati (faqat o'qish), CS/CL dan yig'iladi | — | ✅ | Y:el; `ElPanel.tsx`; `edge_usage.rows` | S | M |
| EL-025 | Detallar jadvali ustunlari | Товар (material), Длина, Окл. дл., Ширина, Окл. шр., Кол-во, Д-на кромки, Наименование; qo'shimcha: ОК | 8 ustun | ✅ | Y:el; D9; `ElPanel.tsx` | S | M |
| EL-026 | Jadval boshqaruvi | Ctrl+Space — detal xossalari, Home/↑/↓/End — qatorlar bo'ylab yurish, sarlavha bosilsa saralash | — | ❌ | Y:el; D9; `shared/grid/Grid.tsx` (`sortable:false`, EL da hotkey yo'q) | S | M |
| EL-027 | Chop sozlamalari (EL) | «Печать заголовка» (parametrlar bloki) va «Печать деталей»; jonli GUI'da qo'shimcha: sarlavhada «Длина кромкования (работа)» va «Длина материала» | Да/Да; qo'shimcha Нет | ✅ | Y:el (R:el1); H4; `PrintSettings.el_*`; `Print.tsx` | S | L |

### 2.2 (GR) Пазование

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| GR-001 | Ширина (W) паза | Paz eni; arra o'tishlari sonini belgilaydi | mm; bizda 4 | ✅ | Y:gr; `models.py::GRParams.width`; `GrPanel.tsx` | S | M |
| GR-002 | Глубина (D) | Paz chuqurligi | mm; bizda 10 (v2 spetsifikatsiyasida 8) | 🟡 | Y:gr; F2; `GRParams.depth` | S | M |
| GR-003 | Отступ (O) | Detal chetidan paz boshigacha masofa | mm; bizda 16 (spetsifikatsiyada 10) | 🟡 | Y:gr; F2; `GRParams.offset` | S | M |
| GR-004 | Отступ включительно | Masofa paz eni bilan birga yoki alohida sanalishi (yordamda yo'q; `.project` da `grOffsetIncl`) | bool; bizda ✓ (modelda) | 🟡 | G_IMPORT §G4; `GRParams.offset_inclusive`; **panelda ko'rinmaydi** | S | M |
| GR-005 | Толщина пилы | Arra qalinligi: eni undan katta paz bir necha o'tishda kesiladi (⌈W/arra⌉) | mm; bizda 4 (modelda) | 🟡 | Y:gr; K4; `calc.groove_passes`; **panelda ko'rinmaydi** | S | H |
| GR-006 | Rasm 1 — W/D/O sxemasi | Uch o'lchamli bo'lak kesimi: W — paz eni, D — chuqurligi, O — detal chetidan pazning yaqin chetigacha masofa (O ning aynan qaysi chetgacha sanalishi «Отступ включительно» bilan bog'liq) | — | ❌ | Y:gr; R:grv (`images/site/groove.png`) | S | L |
| GR-007 | Цена метра паза | 1 m paz ishi narxi | pul/m; bizda 0 | ✅ | Y:gr; `GRParams.price` | S | M |
| GR-008 | Длина пазования | Barcha detallar bo'yicha paz uzunligi (m): Σ pazli tomonlar × (ОК − МК); qo'shimcha «Длина пропила» = × o'tishlar | m; hisoblanadi | 🟡 | Y:gr; `calc.groove_usage`; hisobotda bor, **panelda yo'q** | S | M |
| GR-009 | Стоимость | Narx × paz uzunligi | pul | 🟡 | Y:gr; `groove_usage`→`cost_operation`; panelda ko'rsatilmaydi (Операции jadvalida bor) | S | M |
| GR-010 | Сохранить параметры по умолчанию | Yangi GR operatsiyasi uchun standartni saqlash | scope `gr_defaults` | ❌ | Y:gr; `services/settings.py::MODELS` (yo'q) | S | M |
| GR-011 | Справка (F1) | Panel yordami | F1 | 🟡 | Y:gr; `GrPanel.tsx` (yordam tugmasi yo'q) | S | L |
| GR-012 | «Детали» yorlig'i | Pazli detallar jadvali: Товар, Длина, ПВ, ПН, Ширина, ПЛ, ПП, Кол-во, Д-на паза, Наименование (+ Ctrl+Space, Home/↑/↓/End) | 10 ustun | 🟡 | Y:gr; K4; `GrPanel.tsx` (oddiy 4 ustunli ro'yxat; to'liq jadval faqat hisobotda — `render._gr_section`) | M | M |
| GR-013 | Paz tomonlari va yuzasi | Detalda 4 tomon: ПВ/ПН — uzunlik bo'yicha (yuqori/past), ПЛ/ПП — en bo'yicha (chap/o'ng) + lits/orqa tomon. (Yordamda en tomonlari ham «ПВ/ПН» deb xato yozilgan) | `groove_top…right`, `back_side` | ✅ | Y:gr; B7; `models.py::Part.groove_*` | S | M |
| GR-014 | Chop sozlamalari (GR) | Parametrlar bloki va pazli detallar jadvalini chopga qo'shish/o'chirish | `gr_params`, `gr_parts` | 🟡 | `PrintSettings`; `render._gr_section`; `Print.tsx` (**GR bo'limi yo'q**) | S | L |
| GR-015 | Standart qiymatlar | `.project` fayllarida W=4, D=8, O=10; bizning model 4/10/16 | — | ❓ | G_IMPORT §G4; F2; `GRParams` | S | M |

### 2.3 (O) Комплектация и другие действия

Yordam bo'yicha operatsiya murakkab hisob talab qilmaydigan ishlar uchun: material sarfi (komplektatsiya), ish narxi, maxsus
ko'rsatma. Misollar: transport, mahsulot komplektatsiyasi, mebel o'rnatish, qadoqlash.

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| O-001 | Operatsiya turi (O) «Простая» | Murakkab hisobsiz operatsiya; tur tanlash dialogida birinchi qator | `OpType.O` | ❌ | Y:o; R:lb1; `models.py::OpType.O` (faqat enum), `opmeta.tsx::IMPLEMENTED` (yo'q) | M | H |
| O-002 | Владелец | Operatsiya loyihaga yoki bitta mahsulotga tegishli; mahsulotniki bo'lsa har material soni va ish narxi shu mahsulot soniga ko'paytiriladi | Проект / Изделие | ❌ | Y:o; B13 | S | H |
| O-003 | Materiallar jadvali (kiritish) | Ustunlar: Код, Наименование, Ед.И (шт, метр, мм…), Кол, Цена | erkin matn / son | ❌ | Y:o; K2 | M | H |
| O-004 | Стоимость (qator) | Qator narxi = Кол × Цена | hisoblanadi | ❌ | Y:o | S | H |
| O-005 | Стоимость материала | Jadval bo'yicha jami (egasi mahsulot bo'lsa × mahsulot soni) | pul | ❌ | Y:o; B13 | S | H |
| O-006 | Стоимость операции | Ish narxi (qo'lda kiritiladi; mahsulot egasida × soni) | pul | ❌ | Y:o | S | H |
| O-007 | Стоимость (jami) | Материал + операция | pul | ❌ | Y:o | S | H |
| O-008 | Описание | Maxsus ko'rsatma, izoh, ish rejasi (ko'p qatorli matn) | matn | 🟡 | Y:o; `models.py::Operation.description` (maydon bor, O paneli yo'q) | S | M |
| O-009 | Excel/OpenOffice'dan qo'yish | Manba ustunlari tartibi (Код, Наименование, Ед.И, Кол, Цена); katakni bosib Ctrl+V | TSV | ❌ | Y:o; E3; `services/importers.py` (faqat detallar) | S | M |
| O-010 | Jadval amallari | Qator qo'shish/o'chirish/ko'chirish (Ctrl+PgUp, Del, Ctrl+↑/↓), klonlash | E3 | ❌ | E3 (O materiallari jadvallari) | S | M |
| O-011 | Сохранить параметры по умолчанию | Yangi O operatsiyasi uchun standart (egasi, ish narxi) | scope `o_defaults` | ❌ | Y:o | S | L |
| O-012 | Справка (F1) | Panel yordami | F1 | ❌ | Y:o | S | L |
| O-013 | Omborga talabnoma ta'siri | O materiallari «Требование на склад» ga o'z birligi bilan tushadi | B11 | ❌ | B11; `calc.warehouse_request` (O yo'q) | S | H |
| O-014 | Mahsulot narxiga taqsimlash | O narxi egasi bo'lgan mahsulotga yoziladi (Изделия: Ст. м-ла / Ст. оп-и) | B10 | ❌ | B10; `calc.product_costs` (O yo'q) | S | H |
| O-015 | Bazis/`.project` importida O | Komplektlar (`material` havolalari + soni) O operatsiyasiga tushadi; hozir import o'tkazib yuboradi | G4 | ❌ | G_IMPORT §G4; `plugins/legacy_project.py:407` | M | H |
| O-016 | Tayyor shablonlar | Transport / komplektatsiya / o'rnatish / qadoqlash uchun oldindan to'ldirilgan operatsiyalar (yordam faqat misol sifatida aytadi) | — | ❌ | Y:o | S | L |
| O-017 | (DR) Сверление tur | Tur tanlash dialogida «(DR) Сверление» bor; yordamda yo'q, ma'nosi aniq emas | — | ❓ | R:lb1 | S | L |

### 2.4 (LB) Этикетки — operatsiya parametrlari

Ma'nolar asosan parametr nomi, `R:lbp` sxemasi va jonli kuzatuv (G4/H5) dan; yordam matni bo'sh.

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| LB-001 | LB operatsiyasi | Loyiha ichidagi alohida operatsiya (Операции jadvalida qator, П-ть/Н.Стр, nom «Этикетки: …»); sozlamalar va shablon loyiha bilan saqlanadi | tur «(LB) Этикетки» | ❌ | Y:lb; R:lb1; `models.py::OpType.LB` (enum), `opmeta.tsx::IMPLEMENTED` (yo'q) | M | H |
| LB-002 | Источник данных | Etiketka qatorlari manbai: foydalanuvchi ma'lumotlari / mahsulotlar / detallar va qoldiqlar (taxmin: `source` 0/1/2) | 3 qiymat | ❌ | Y:lb; R:lb1; G4; `labels.py` (faqat CS detallari) | M | H |
| LB-003 | Печатать: формат A4 / принтер этикеток | Chop rejimi: A4 varaqda to'r yoki etiketka printerida bittadan (rulon) | 2 rejim | 🟡 | R:lb1; `LabelSettings.columns` (0 = printer, >0 = A4 to'r) | S | M |
| LB-004 | Размер | Bitta etiketka o'lchami | mm; bizda 58×40 | ✅ | Y:lb; `LabelSettings.width_mm/height_mm` | S | M |
| LB-005 | Столбцы | A4 varaqdagi ustunlar soni | son; bizda 3 | ✅ | Y:lb; R:lbp; `LabelSettings.columns` | S | M |
| LB-006 | Строки | A4 varaqdagi qatorlar soni (sahifa to'liqligi/bo'sh joy uchun) | son | ❌ | Y:lb; R:lbp (bizda to'r avto oqadi) | S | M |
| LB-007 | Промежуток | Etiketkalar orasidagi masofa | mm; bizda qat'iy 2 | 🟡 | R:lbp; `labels.py` (`gap: 2mm`) | S | M |
| LB-008 | Поля страницы | Varaq chetidagi bo'sh joy (checkbox bilan yoqiladi) | mm; bizda qat'iy 6 | 🟡 | R:lbp; R:lb1; `labels.py` (`@page margin 6mm`) | S | M |
| LB-009 | Границы | Etiketka atrofidagi chegara chiziqlari (kesish yo'riqnomasi) | bool; bizda qat'iy yoqiq (0.2 mm) | 🟡 | Y:lb; `labels.py` (`.lbl border`) | S | L |
| LB-010 | Количество | Chop etiladigan etiketkalarning jami soni (avto hisoblanadi, ko'rsatiladi) | son (misol: 257 шт) | ❌ | R:lb1 | S | M |
| LB-011 | Печать деталей | Detal etiketkalarini chop etishni yoqish/o'chirish | bool | ❌ | Y:lb | S | M |
| LB-012 | Для каждой детали | Yoqilsa — detalning har bir nusxasiga alohida etiketka; o'chiq bo'lsa — detalga bitta (taxmin) | bool; bizda doim «har nusxa» (i/n) | 🟡 | Y:lb; `labels.py` | S | M |
| LB-013 | Только если количество больше нуля | Soni 0 bo'lgan qatorlar chiqmaydi (`ONZ`) | bool; bizda doim shunday | 🟡 | Y:lb; G4 (`partONZ`); `calc.effective_qty` | S | L |
| LB-014 | Выбранные детали | Faqat jadvalda tanlangan detallar etiketkasi | bool | ❌ | Y:lb; G4 (`partSelected`); bizda faqat `op_id` filtri | M | M |
| LB-015 | Печать отходов | Qoldiq/chiqindi etiketkalarini yoqish | bool | ❌ | Y:lb; G4 (`printWastes`) | M | M |
| LB-016 | Для каждого отхода | Qoldiqning har bir nusxasi uchun etiketka | bool | ❌ | Y:lb; G4 (`wasteEach`) | S | M |
| LB-017 | Изделия: Для каждого изделия | Mahsulotning har bir nusxasi uchun etiketka (mahsulot yorlig'i/qadoq) | bool | ❌ | Y:lb; G4 (`productEach`) | M | M |
| LB-018 | Изделия: Только если количество больше нуля | Soni 0 mahsulotlar o'tkazib yuboriladi | bool | ❌ | Y:lb; G4 (`productONZ`) | S | L |
| LB-019 | Пользовательские данные (jadval) | Manba «foydalanuvchi ma'lumotlari» bo'lsa, qo'lda to'ldiriladigan maydonlar sxemasi: Наименование, Описание, Тип, Ш-на (ustun eni), По умолчанию; har qator — bitta etiketka (taxmin) | jadval | ❌ | Y:lb; G4 (`fields`, `data`) | L | M |
| LB-020 | Jadval amallari | Qator qo'shish (Ctrl+PgUp), o'chirish (Del), ko'chirish (Ctrl+↑/↓) | E3 | ❌ | Y:lb; E3 | S | L |
| LB-021 | Открыть | Shablonni katalogdan ochish (ro'yxatda miniatyura, papka, nom) | — | ❌ | Y:lb; R:lb2 | M | M |
| LB-022 | Сохранить | Shablonni katalogga nom bilan saqlash | — | ❌ | Y:lb; R:lb11 | M | M |
| LB-023 | Сохранить текущие параметры по умолчанию | Yangi LB operatsiyalari uchun standart | — | 🟡 | Y:lb; `PUT /settings/labels/default`; `Print.tsx::saveLabels` (operatsiya emas, chop bo'limi) | S | L |
| LB-024 | Справка (F1) | Panel yordami | F1 | ❌ | Y:lb | S | L |

### 2.5 (LB) Шаблон — redaktor va shablon tizimi

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| LB-030 | «Шаблон» yorlig'i (vektor redaktor) | Etiketka maydoni koordinata o'qlari bilan; chap tomonda chizma/boshqaruv buyruqlari paneli, o'ngda dastur ro'yxati va xossalar | mm koordinatalar | ❌ | Y:lb; R:lb3; R:lb12 | L | M |
| LB-031 | Показать все изображение | Rasmni oynaga sig'dirish (zoom-to-fit) | — | ❌ | Y:lb | S | L |
| LB-032 | Панель служебных команд (F4) | Qo'shimcha buyruqlar panelini ko'rsatish/yashirish | F4 | ❌ | Y:lb; E7 | S | L |
| LB-033 | Состояние (F9) | Joriy holat/o'zgaruvchilar qiymatini ko'rsatish (XNC redaktoridagi kabi; yordamda tushuntirilmagan) | F9 | ❓ | Y:lb; E7 | S | L |
| LB-034 | Добавить параметр | Shablonga foydalanuvchi parametri (`Par`: tur, nom, standart qiymat, izoh) qo'shish | — | ❌ | Y:lb; R:lb3 («Program» paneli: `Par double margin=2`) | M | M |
| LB-035 | Переменные | Shablon o'zgaruvchilar (`Var`) oynasi — standart va o'z o'zgaruvchilar | — | ❌ | Y:lb; R:lb3 | M | M |
| LB-036 | Добавить | Buyruq/element qo'shish tugmasi (menyu) | — | ❌ | Y:lb | S | L |
| LB-037 | Справка (shablon, F1) | Redaktor yordami | F1 | ❌ | Y:lb | S | L |
| LB-038 | Экспортировать | Shablonni lokal diskka fayl qilib yuklab olish (`*.lbl`) | fayl | ❌ | Y:lb; Y:labels; R:lb12 | S | M |
| LB-039 | Импортировать | Lokal diskdan/flesh-xotiradan shablon fayli yuklash (tugma turi `fileText`) | fayl | ❌ | Y:lb; R:lb3; Y:btn | S | M |
| LB-040 | Стартовая точка полилинии | Polilinya boshlanish nuqtasi (keyingi chiziq/yoy/egri shu nuqtadan davom etadi) | X, Y | ❌ | Y:lb | M | M |
| LB-041 | Линия | Polilinyaga to'g'ri chiziq segmenti | X, Y | ❌ | Y:lb | S | M |
| LB-042 | Дуга | Polilinyaga yoy segmenti | X, Y, radius/markaz (taxmin) | ❌ | Y:lb | M | L |
| LB-043 | Кривая безье | Bezye egri segmenti | nazorat nuqtalari | ❌ | Y:lb | M | L |
| LB-044 | Прямоугольник | To'g'ri to'rtburchak (ramka, jadval katagi) | X, Y, eni, bo'yi | ❌ | Y:lb | S | M |
| LB-045 | Эллипс | Ellips/aylana | markaz, yarim o'qlar | ❌ | Y:lb | S | L |
| LB-046 | Текст | Matn bloki; pozitsiya va mazmun — ifoda (satr + o'zgaruvchi + funksiya); shrift/o'lcham | ifoda | ❌ | Y:lb; Y:labels | M | H |
| LB-047 | Штрихкод | Shtrixkod elementi; mazmuni ifoda bilan (misol: loyiha №, detal ID, hisoblagich) | ifoda | ❌ | Y:lb; Y:labels | M | H |
| LB-048 | Изображение | Rasm (logotip, ikonka) joylashtirish | fayl/data | ❌ | Y:lb | M | M |
| LB-049 | Начало координат | Keyingi elementlar uchun koordinata boshini ko'chirish | X, Y | ❌ | Y:lb | S | M |
| LB-050 | Вращение | Keyingi elementlarni berilgan burchakka burish (shtrixkodni vertikal qilish uchun) | gradus | ❌ | Y:lb; Y:labels | S | M |
| LB-051 | Деталь | Detal chizmasi (kontur, o'lchamlari) | — | ❌ | Y:lb | M | M |
| LB-052 | Кромка | Kromka belgilari (tomon, belgi, qalin chiziq) | — | ❌ | Y:lb; `labels.py::_edge_icon` (qat'iy ikonka) | M | M |
| LB-053 | Boshqaruv buyruqlari (Com, Par, Var, Set, IF, Else, WD, DW) | Redaktor chap panelida: izoh, parametr, o'zgaruvchi, qiymat berish, shart (IF/Else), sikllar (WD — while, DW — do-while) | XNC redaktori bilan umumiy | ❌ | R:lb3; R:lb12; J2; E7 | L | M |
| LB-054 | «Программа» paneli | Shablonning buyruqlar ro'yxati (daraxt): `Par`/`Var` e'lonlari izoh bilan (`margin`, `suffix`, `XNC1…5`, `xncSide1…5`), elementlar; ↑↓ ko'chirish, o'chirish | — | ❌ | R:lb3; R:lb12 | L | M |
| LB-055 | Shablon fayl formati | Matn faylli shablon `*.lbl`; ichida elementlar, pozitsiya va mazmun ifodalari | `.lbl` | ❌ | Y:labels; bizda JSON rejasi (H5) | M | M |
| LB-056 | Shablon kutubxonasi | Papkalar daraxti, har shablon miniatyurasi, nom maydoni, yaratish/nomlash/ko'chirish/o'chirish; mijozlar papkasi | `content` API | ❌ | R:lb2; R:lb11; Y:cont | L | M |
| LB-057 | Namuna shablonlar | 58×40, 58×60, 100×40, QR 58×40 (rus/ingliz variantlar) va boshqa tayyor maketlar | 6+ ta | ❌ | R:lb3 (fayl nomlari); R:lb2 | M | M |
| LB-058 | Shablon loyiha ichida | Shablon dasturi LB operatsiyasi maydonida (`program`) saqlanadi — loyiha fayli o'zi bilan olib yuradi | — | ❌ | G4 (`program`) | S | M |
| LB-059 | Ifodali pozitsiya va mazmun | Har elementning o'rni, o'lchami va mazmuni string/matematik ifoda; shart bilan elementni chiqarmaslik | §5 | ❌ | Y:labels | L | H |

### 2.6 (LB) Standart o'zgaruvchilar (104 ta) — yordamdagi jadval

To'liq nomlar ro'yxati — Ilova B. «Bizda» ustuni **shablonda ishlatish** nuqtai nazaridan: ma'lumot bizda bor va qat'iy shablon chop
etadi → 🟡; ma'lumot ham yo'q yoki chiqmaydi → ❌. (`H5` jadvalida bizning snake_case nomlari rejalangan.)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| LB-060 | `project.*` (6) | Loyiha: nomi, sanasi, tavsifi, valyutasi, nomining crc16 va crc32 qiymati (nom o'zgarmasa kod ham o'zgarmaydi → shtrixkod uchun) | string | 🟡 | Y:labels; `labels.py` (faqat № va nom) | S | M |
| LB-061 | `product.*` (8) | Mahsulot: tartib №, nomi, kodi, soni (integer), tavsifi, 2 telefon, sana | string/integer | 🟡 | Y:labels; `labels.py` (faqat nomi) | S | M |
| LB-062 | `material.*` (2) | Material nomi va kodi | string | 🟡 | Y:labels; `labels.py` (faqat nomi; kod yo'q) | S | M |
| LB-063 | `part.id`, `part.code`, `part.counter` | Detalning loyihadagi noyob raqami, kodi, hisoblagich (har etiketka uchun noyob — takror skanerlashdan himoya) | integer/string | 🟡 | Y:labels; `labels.py::qr_text` (uid + nusxa/jami) | S | H |
| LB-064 | `good`, `name`, `description`, `index`, `indexInOperation`, `fullName` (6) | Mahsulot/material, detal nomi, tavsif, tartib raqami, operatsiyadagi raqam, material+mahsulot to'liq nomi | string | 🟡 | Y:labels; `labels.py` | S | M |
| LB-065 | `length`, `width`, `detail.length`, `detail.width`, `thick` (5) | Zagotovka o'lchami (uzunlik/en), tayyor detal o'lchami, qalinlik | double | 🟡 | Y:labels; B2; `labels.py` (kiritilgan o'lchamni chiqaradi — rejimga qarab zagotovka ham detal ham bo'lishi mumkin) | S | H |
| LB-066 | `waste`, `business`, `txt` (3) | Qoldiq belgisi, delovoy qoldiq belgisi, tekstura | boolean | ❌ | Y:labels | S | M |
| LB-067 | `count`, `totalCount`, `usedCount` (3) | Soni; jami (detal × mahsulot); kroyga kirgan soni | integer | 🟡 | Y:labels; `labels.py` (i/n) | S | M |
| LB-068 | Kromka: `et*`, `eb*`, `el*`, `er*` (4 tomon × 5 = 20) | Har tomon uchun: kod (`c`), nom (`n`; yordamda «по длине/ширине» deb yozilgan — taxmin), belgi (`s`), qalinlik (`t`), prifugovka (`j`) | string/double | 🟡 | Y:labels; `labels.py::_edge_icon` (faqat belgi/chiziq) | M | M |
| LB-069 | Paz: `grt*`, `grb*`, `grl*`, `grr*` (4 tomon × 7 = 28) | Har tomon uchun: kod, nom, eni, chuqurlik, otstup, otstup-inklyuziv (bool), tomon (bool) | string/double/boolean | ❌ | Y:labels; GR | M | L |
| LB-070 | `surfFront`, `surfBack` | Lits va orqa sirt (SP operatsiyasi) nomi | string | ❌ | Y:labels; `Part.surface_face_op` (maydon bor, SP yo'q) | S | L |
| LB-071 | `groove`, `drill`, `mill` | Detalda paz / parmalash / frezalash borligi (nomdagi `=`, `%`, `*` belgilari) | boolean | 🟡 | Y:labels; `render.part_marks` | S | M |
| LB-072 | `XNC1…5`, `xncSide1…5`, `xncBSD1…5` (15) | Detalga biriktirilgan 5 tagacha CNC dasturi: kod, tomon (lits/orqa), «по размеру детали»; stanokda dastur ishga tushiruvchi shtrixkod uchun | string/boolean | ❌ | Y:labels; J5; `Part.xnc_op_ids` | M | M |

### 2.7 (LB) Etiketka va shtrixkod bo'yicha tavsiyalar (amaliy qoidalar)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| LB-080 | Shtrixkod turlari | Shablonda tanlanadigan tur (1D/2D); bizda faqat QR | — | 🟡 | Y:lb; H5 (Code128/QR rejasi); `labels.py` (QR, `segno`) | M | M |
| LB-081 | Shtrixkod mazmuni | Ifoda bilan tuziladi: loyiha raqami + detal ID (oxirgi 4 raqam, 0 bilan to'ldirilgan) + hisoblagich (4 raqam) — misol qatori satr funksiyalari bilan | ifoda | 🟡 | Y:labels; `labels.py::qr_text` (`MXK:<№>:<uid>:<i>/<n>`, MES skaneri o'qiydi) | M | M |
| LB-082 | Noyoblik talabi | Har etiketkada takrorlanmas qiymat (hisoblagich) — qayta skanerlashni oldini oladi | — | ✅ | Y:labels; `labels.py::parse_qr` (i/n) | S | H |
| LB-083 | Mazmunni matn ko'rinishida takrorlash | Shtrixkod yonida (ustida/ostida) o'qiladigan matn | — | ❌ | Y:labels | S | M |
| LB-084 | Shtrixkodni vertikal joylash / etiketkani 90° burish | Eski printer polosa tashlab ketishi mumkin — shtrixkod chiziqlari yo'nalishi muhim | — | ❌ | Y:labels; LB-050 | S | M |
| LB-085 | CNC uchun shtrixkodlar | Ishlov markazida dastur ishga tushirish uchun detalning har tomoniga kamida bittadan shtrixkod | 2+ | ❌ | Y:labels; LB-072 | M | M |
| LB-086 | Shtrixkod sig'imi cheklovi | 50 mm kenglikda ishonchli o'qish uchun ≈ 16 raqam yoki 8 lotin harf; faqat raqam afzal | cheklov | ❌ | Y:labels (redaktorda ogohlantirish bo'lishi mumkin) | S | L |
| LB-087 | Shablon joylashuvi (ish joylari) | Mahalliy dasturda papka, saytda baza, arra markazi chop moduli (`print\part.lbl`: Holzma CadMatic 3/4x, SCM WinCut) — bir shablon ham ofisda, ham arra markazida | — | ❓ | Y:labels; D12 (postprotsessor «этикетка ma'lumoti») | M | L |
| LB-088 | Shablon yaratish oqimi | LB operatsiyasi qo'shish → «Открыть» (katalog) yoki «Импорт» (lokal) → tahrir → «Сохранить» (katalog) yoki «Экспорт» (lokal) | — | ❌ | Y:labels; R:lb1…lb12; qarang LB-021/022/038/039 | S | M |

### 2.8 «Товары» katalogi va xizmat API

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CAT-001 | Katalog manbasi — Excel fayl | Namuna katalog Excel faylda (`goods.xls`); foydalanuvchi uni tahrirlashi yoki o'zining list/kromka katalogini tuzishi mumkin | .xls (97–2003) | 🟡 | Y:goods; R:cvb1; `services/importers.py::import_catalog` (.xlsx/.csv; `.xls` yo'q) | S | M |
| CAT-002 | Fayl ustunlari (10) | A ID, B Родительский ID, C Папка (bayroq), D Код, E Наименование, F Единицы измерения, G Цена, H Толщина, I Длина, J Ширина | A–J | 🟡 | Y:goods; R:cvb; `catalog_items`; `CatalogImport` (`isfolder` ustuni yo'q — `kind` orqali) | S | M |
| CAT-003 | Daraxt qoidasi | Ildiz kategoriya ID=0 (ota yo'q, papka=1) → ishlab chiqaruvchi → qalinlik → o'lcham (papkalar) → material qatorlari (papka=0); har qator `Родительский ID` bilan bog'lanadi | `parent_id` | 🟡 | Y:goods; R:cvb7; `db.py::CatalogItemRow.parent_id`; UI daraxt yo'q | M | M |
| CAT-004 | Sozlama: fayl, varaq, boshlang'ich qator | Qaysi fayl, qaysi varaq (1…), ma'lumot qaysi qatordan boshlanadi (2) | — | ✅ | R:cvb6; `import_catalog(sheet, start_row)` | S | L |
| CAT-005 | Sozlama: Сортировка | Katalog ro'yxatini tartiblash bayrog'i | bool | ❌ | R:cvb6 | S | L |
| CAT-006 | Sozlama: Отображать колонки | Jadvalda ko'rsatiladigan ixtiyoriy ustunlar: Единица измерения, Цена, Склад | 3 bayroq | ❌ | R:cvb6 | S | L |
| CAT-007 | Sozlama: Корневая категория | Operatsiya turiga ildiz papka ID si: Листовой / Погонажный / Материал кромок / Материал поверхностей | 4 ID | 🟡 | R:cvb6; `catalog_items.kind` (sheet/linear/edge/surface) | M | M |
| CAT-008 | Sozlama: qo'shimcha ustunlar | Склад (qoldiq), Изображение (rasm yo'li), Параметры (qo'shimcha xossalar) | 3 ustun | 🟡 | R:cvb6; `CatalogItemRow.stock/params`; rasm yo'q | M | L |
| CAT-009 | «Товары» oynasi | Chapda «Категории» daraxti, o'ngda «Изображение», pastda «Материалы» jadvali (№, Код, Наименование, Ед.И, Цена, Т-на, Д-на, Ш-на); Поиск, Обновить, Настройки | — | 🟡 | R:cvb6; R:cvb9; D3; `CatalogPicker.tsx` (yassi ro'yxat + tur filtri + qidiruv) | M | M |
| CAT-010 | Tanlash natijasi | Tanlangan tovar kodi, nomi, narxi, qalinligi, list o'lchami operatsiyaga yoziladi | CS, EL, … | 🟡 | `main.py::_new_operation` (CS, EL ✅; linear/surface ❌) | M | M |
| CAT-011 | Umumiy katalog (bir nechta ish joyi) | Katalog fayli bulutli papkaga qo'yilib bir nechta kompyuter/buyurtma moduli ishlatadi | — | ✅ | Y:goods; bizda markaziy baza + MES sinxroni (`POST /api/catalog/sync`) | S | L |
| CAT-012 | `catalogGet` | Ota papka/kategoriya ID si bo'yicha ichidagilarni oladi (ID berilmasa — ildiz) | `id` | ✅ | Y:cat; `GET /api/catalog?parent_id=` | S | M |
| CAT-013 | `catalogSearch` | Qidiruv; joriy operatsiya turi (`typeId`, masalan CS) bo'yicha ildizni tanlaydi | `id`, `typeId` | 🟡 | Y:cat; `GET /api/catalog?q=&kind=` (turga avto-moslash yo'q) | S | M |
| CAT-014 | `content*` amallari | Saqlash, papka yaratish, ko'chirish, o'chirish, nomlash, yuklash — loyiha/XNC shablon/etiketka shablonlari uchun umumiy ombor | 6 amal | 🟡 | Y:cont; `main.py` (loyiha va papkalar ✅; XNC/etiketka shablonlari ❌) | L | M |
| CAT-015 | `contentList` | Ro'yxat: tur (`project`, `xnc`, `label`), ota ID/papka, oldindan yuklash (`preLoad`), papka/element miniatyurasi eni va bo'yi | 6 parametr | ❌ | Y:cont; R:lb2 (miniatyuralar) | M | M |

### 2.9 Ifodalar tili (expression) — tiplar, operatorlar, sintaksis

Bizdagi taqqos manbasi: `backend/app/services/xnc.py::eval_expr` (Python `ast` ustiga qurilgan xavfsiz hisoblagich; qiymatlar faqat
`float`; XNC dasturlari uchun). To'liq farq jadvali — §5.

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| EXP-001 | Tip `integer` | 32-bitli ishorali butun son | ±2 147 483 647 | 🟡 | Y:types; `eval_expr` (barcha son — float, butun tip yo'q) | M | H |
| EXP-002 | Tip `double` | IEEE 754 ikkilangan aniqlikdagi son, `NaN` mumkin | ≈ ±1.79E+308, ~15 xona | ✅ | Y:types; `eval_expr` (NaN/inf rad etiladi) | S | M |
| EXP-003 | Tip `boolean` | `true` / `false` mantiqiy qiymat | 2 qiymat | 🟡 | Y:types; `eval_expr` (1.0/0.0; kichik harfli `true`/`false` literal tanilmaydi — Python `True`) | S | H |
| EXP-004 | Tip `string` | Matn qiymati — satr ifodalari va etiketka mazmuni uchun asos | satr | ❌ | Y:types; `eval_expr` (satr literali taqiqlangan, natija faqat son) | M | H |
| EXP-005 | `null` | Qiymat yo'q; `ns()` va `empty()` shu bilan ishlaydi | null | ❌ | Y:str; Y:fstr | S | M |
| EXP-006 | Tiplarni aralashtirish qoidasi | Hamma operand butun bo'lsa `+ − * /` natijasi ham butun (bo'lish — butunli); bitta `double` bo'lsa natija `double`; satr + istalgan tip = konkatenatsiya | — | ❌ | Y:math; Y:str; `eval_expr` (har doim float: 7/2 = 3.5) | M | H |
| EXP-007 | Uch xil ifoda | Arifmetik, mantiqiy (shart) va satr ifodalari; natija tipiga qarab ishlatiladi | 3 tur | 🟡 | Y:expr; `eval_expr` (arifmetik + mantiqiy; satr yo'q) | M | H |
| EXP-010 | Arifmetik `+ − * /` | Oddiy to'rt amal; tip qoidasi EXP-006 | — | ✅ | Y:math; `xnc.py::_BIN` | S | M |
| EXP-011 | Unar `+` / `−` | Ishora o'zgartirish | — | ✅ | Y:math; `_UN` | S | L |
| EXP-012 | `%` | Butun bo'lishdan qoldiq (manfiy sonlarda ishora qoidasi yordamda aytilmagan) | — | 🟡 | Y:math; `_BIN` (Python `%`: bo'luvchi ishorasi) | S | M |
| EXP-013 | `^` darajaga ko'tarish | Daraja operatori; ustuvorlik/assotsiativlik aytilmagan | — | 🟡 | Y:math; `xnc.py::_pow` (`**` bor, `^` — Python XOR, rad etiladi) | S | H |
| EXP-014 | Qavslar `( )` | Bajarilish tartibini o'zgartirish | — | ✅ | Y:math | S | L |
| EXP-020 | Taqqoslash `< > <= >=` | To'rt tengsizlik; natija boolean | — | ✅ | Y:bool; `_CMP` | S | M |
| EXP-021 | Tenglik `=` va `==` | Ikkala yozuv ham tenglik | — | 🟡 | Y:bool; `_CMP` (`==` ✅; `=` — sintaksis xatosi) | S | H |
| EXP-022 | Teng emas `<>` va `!=` | Ikkala yozuv ham | — | 🟡 | Y:bool; `_CMP` (`!=` ✅; `<>` ❌) | S | H |
| EXP-023 | Haqiqiy sonlarni tenglashtirish xavfi | Yaxlitlash xatosi sababli `double` larni qat'iy tenglashtirmaslik haqida ogohlantirish | — | ✅ | Y:bool; `_CMP` (abs(a−b) ≤ 1e-9 — bizniki yaxshiroq) | S | L |
| EXP-030 | `not` | Mantiqiy inkor | — | ✅ | Y:bool; `_ev` (`ast.Not`) | S | M |
| EXP-031 | `and`, `or` | Mantiqiy ko'paytirish va qo'shish (haqiqiylik jadvali) | — | 🟡 | Y:bool; `_ev` (`BoolOp`: natija operand qiymati, boolean emas) | S | M |
| EXP-032 | `xor` | Mantiqiy istisno qiluvchi YOKI | — | ❌ | Y:bool | S | M |
| EXP-033 | `if(shart, ha, yo'q)` | Shartli tanlov funksiyasi (ikkala tarmoq tipi mos bo'lishi kerak; qaysi tarmoq hisoblanishi aytilmagan) | — | 🟡 | Y:bool; Y:fmisc; `_ev` (`a if c else b` — Python ko'rinishi) | S | H |
| EXP-040 | Satr literali `'...'` | Bitta qo'shtirnoqdagi matn | — | ❌ | Y:str | S | H |
| EXP-041 | Escape ketma-ketliklari | `\b \f \n \r \t \' \" \\ \uXXXX` | 8 ta | ❌ | Y:str | S | M |
| EXP-042 | Satr konkatenatsiyasi `+` | Matn + son/boolean → matn («x»+1 → «x1»); qavs ichidagi son avval hisoblanadi; boolean `true/false` matni bo'lib qo'shiladi | — | ❌ | Y:str | S | H |
| EXP-043 | Nuqtali o'zgaruvchi nomlari | `project.name`, `part.id`, `detail.length` kabi ierarxik nomlar | — | 🟡 | Y:labels; `_ev` (`a.b`, faqat son; `origin.x` uchun) | S | H |
| EXP-044 | Registr sezgirligi | Funksiya nomlari aralash registrda (`DecToHex`, `UUID`, `now`); o'zgaruvchi nomlari (`XNC1`, `xncSide1`) — sezgirlik qoidasi yordamda yo'q | — | ❓ | Y:fnum; Y:fmisc; Y:labels | S | M |
| EXP-045 | Operator ustuvorligi | Yordamda jadval yo'q; odatiy tartib faraz qilinadi (`^` → unar → `* / %` → `+ −` → taqqoslash → `not` → `and` → `xor` → `or`, R3) va testda tasdiqlanadi | — | ❓ | Y:math; Y:bool | S | M |

### 2.10 Ifodalar tili — funksiyalar kutubxonasi (67 ta nom)

Matematik (30 nom: 28 funksiya + 2 konstanta). Misol qiymatlari — kutilgan natija (test-vektor).

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| EXP-050 | `abs(x)` | Modul | abs(-777) = 777 | ✅ | Y:fmath; `_FUNCS` | S | L |
| EXP-051 | `sign(x)` | Ishora: 1, -1 yoki 0 (yordamdagi misol `sign(0) = -0.0`) | sign(-1.5) = -1.0 | ❌ | Y:fmath | S | L |
| EXP-052 | `sqrt(x)` | Kvadrat ildiz (argument manfiy bo'lmasligi shart) | sqrt(4) = 2.0 | ✅ | Y:fmath; `_FUNCS` | S | L |
| EXP-053 | `exp(x)`, `ln(x)`, `log(x)`, `log2(x)`, `logx(x, asos)` | e darajasi; natural, o'nli, ikkilik va ixtiyoriy asosli logarifm (yordamdagi `log(100.0)=0.5` va `log2(4.0)=0.5` misollari matematikaga zid) | logx(9,3) = 2.0; ln(2) = 0.6931 | ❌ | Y:fmath | S | L |
| EXP-054 | `ceil(x)`, `floor(x)` | Yuqoriga / pastga yaxlitlash; natija `double` (2.0) | ceil(1.5) = 2.0; floor(-1.5) = -2.0 | ✅ | Y:fmath; `_FUNCS` | S | M |
| EXP-055 | `round(x)` | Eng yaqin butunga, yarim — **musbat cheksizlik tomon** (−1.5 → −1, 2.5 → 3); natija butun | round(-1.5) = -1; round(2.2) = 2 | 🟡 | Y:fmath; `xnc.py::_round` (nol dan uzoqqa: −1.5 → −2; ixtiyoriy 2-argument) | S | H |
| EXP-056 | `min(a,b)`, `max(a,b)` | Eng kichik / eng katta | max(9,3) = 9 | ✅ | Y:fmath; `_FUNCS` (bizda 1–50 argument) | S | L |
| EXP-057 | `sin(x)`, `cos(x)`, `tan(x)` | Trigonometriya, burchak **radianda** (misollar shuni ko'rsatadi) | cos(pi) = -1.0 | 🟡 | Y:fmath; J3; `_FUNCS` (**gradusda**) | S | H |
| EXP-058 | `asin(x)`, `acos(x)`, `atan(x)` | Teskari trigonometriya (radian natija) | acos(-1) = 3.14159… | ❌ | Y:fmath | S | L |
| EXP-059 | `sinh(x)`, `cosh(x)`, `tanh(x)` | Giperbolik funksiyalar | cosh(1.0) = 1.5430… | ❌ | Y:fmath | S | L |
| EXP-060 | `sec`, `cot`, `coth`, `acot`, `asec` | Qo'shimcha trigonometrik funksiyalar (yordamdagi `asec(1)=π/2` misoli matematikaga zid — amalda tekshirish kerak) | sec(pi) = -1.0 | ❌ | Y:fmath | S | L |
| EXP-061 | `pi`, `e` | Konstantalar | 3.14159…; 2.71828… | ❌ | Y:fmath; `DEFAULT_VARS` (yo'q) | S | M |
| EXP-062 | `random()` | [0, 1) oralig'ida psevdo-tasodifiy son (takrorlanmas natija — etiketka/CNC uchun ehtiyot bo'lish kerak) | — | ❌ | Y:fmath | S | L |

Satr funksiyalari (25 nom). Indekslar 1 dan boshlanadi; sonlar avtomatik matnga aylanadi (`right(part.id,4)`).

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| EXP-070 | `len(s)` | Belgilar soni | len('abc') = 3 | ❌ | Y:fstr | S | M |
| EXP-071 | `mid(s, boshi, uzunlik)` | Qism satr; boshi 1 dan | mid('abc',1,2) = 'ab' | ❌ | Y:fstr | S | M |
| EXP-072 | `left(s, n)`, `right(s, n)` | Chapdan / o'ngdan n belgi | right('abc',2) = 'bc' | ❌ | Y:fstr; Y:labels (shtrixkod misoli) | S | H |
| EXP-073 | `lspace(s, n, belgi)`, `rspace(s, n, belgi)` | Maydonni to'ldirish: `lspace` — chapga tekislab o'ngdan to'ldiradi, `rspace` — o'ngga tekislab chapdan to'ldiradi (nomlari teskari tuyuladi; qisqartirish qoidasi aytilmagan — ❓) | lspace('abc',5,'X') = 'abcXX'; rspace('abc',5,'X') = 'XXabc' | ❌ | Y:fstr; Y:labels | S | H |
| EXP-074 | `rept(s, n)` | Satrni n marta takrorlash (son ham qabul qilinadi) | rept('abc',2) = 'abcabc' | ❌ | Y:fstr | S | L |
| EXP-075 | `ns(s)`, `empty(s)` | null-xavfsiz satr (null → '') va bo'shlikni tekshirish (null yoki '' → true) | empty(null) = true | ❌ | Y:fstr | S | M |
| EXP-076 | `trim`, `ltrim`, `rtrim` | Ikkala / chap / o'ng bo'shliqlarni olib tashlash | trim(' abc ') = 'abc' | ❌ | Y:fstr; Y:labels | S | M |
| EXP-077 | `ucase(s)`, `lcase(s)` | Katta / kichik harfga | ucase('Abc') = 'ABC' | ❌ | Y:fstr | S | L |
| EXP-078 | `find(s, qidir, boshi)`, `findr(...)` | Qidirish (registrga sezgir), 1 dan boshlab pozitsiya, topilmasa 0; `findr` — teskari yo'nalishda | find('abcd','bc',1) = 2; findr('abcdbc','bc',6) = 5 | ❌ | Y:fstr; Y:labels | S | H |
| EXP-079 | `replace(s, eski, yangi)` | Qism satrni almashtirish (hammasini) | replace('abc','b','xxxx') = 'axxxxc' | ❌ | Y:fstr | S | M |
| EXP-080 | `startswith`, `endswith` | Satr boshi/oxiri tekshiruvi (son ham qabul qilinadi) | startswith(1234123,12) = true | ❌ | Y:fstr | S | L |
| EXP-081 | `double(s)`, `integer(s)`, `boolean(s)` | Satr yoki sondan tipga o'tkazish; `boolean`: 'true', 'True', 'T', '1' → true; '', 'false', 'f' → false | integer('1.0') = 1 | ❌ | Y:fstr | S | M |
| EXP-082 | `translit(s)` | Kirill harflarini lotinga o'tkazish | translit('Пример') = 'Primer' | ❌ | Y:fstr | S | M |
| EXP-083 | `crc16(s)` | 16-bitli nazorat yig'indisi; qiymatga mos variant — **CRC-16/ARC** (poli 0x8005 aks, boshlang'ich 0), natija unsigned | crc16('test') = 63534 | ❌ | Y:fstr; Y:labels (`project.crc16`) | S | M |
| EXP-084 | `crc32(s)` | Standart CRC-32 (IEEE), natija **ishorali int32** | crc32('test') = -662733300 | ❌ | Y:fstr; Y:labels (`project.crc32`) | S | M |

Aralash, formatlash, sana-vaqt, sonli konvertatsiya (12 nom).

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| EXP-090 | `calculate(s)` | Satr ichidagi ifodani hisoblaydi (ichma-ich hisoblash — xavfsizlik chegarasi kerak) | calculate('1+2') = 3 | ❌ | Y:fmisc | S | L |
| EXP-091 | `format(naqsh, son)` | Sonni naqsh bo'yicha matnga aylantiradi | format('0.000',23.2) = '23.200'; format('0000',1) = '0001' | ❌ | Y:ffmt; Y:fmisc | M | H |
| EXP-092 | `format`: raqam belgilari | `0` (majburiy xona), `#` (0 yashiriladi), `.` o'nli ajratgich, `,` guruh ajratgich, `-` manfiy prefiks; lokalga bog'liq (o'nli ajratgich til bo'yicha) | — | ❌ | Y:ffmt | M | H |
| EXP-093 | `format`: maxsus belgilar | `E` (eksponensial), `;` (musbat;manfiy qism naqshlar), `%` (×100), `‰` (×1000), `¤` (valyuta), `'` (matnni qo'shtirnoqlash) | format('%',0.32) = '%32' | ❌ | Y:ffmt | M | M |
| EXP-094 | `now(naqsh)` | Joriy sana-vaqtni naqsh bo'yicha matn qilib beradi | now('yyyy.MM.dd') = '2016.06.26' | ❌ | Y:fnow; Y:fmisc | M | M |
| EXP-095 | `now`: era va yil | `G` era; `y`/`yyyy` yil (4 xona), `yy` yil (2 xona) | 2012 / 12 | ❌ | Y:fnow | S | L |
| EXP-096 | `now`: oy | `M` (1), `MM` (01), `MMM` (qisqa nom), `MMMM` (to'liq nom — tilga qarab) | 2 / 02 / фев / Февраль | ❌ | Y:fnow | S | M |
| EXP-097 | `now`: hafta va kun | `w`/`ww` yildagi hafta, `W`/`WW` oydagi hafta, `D` yildagi kun, `d`/`dd` oy kuni, `F`/`FF` oydagi hafta kuni tartibi, `E`/`EEEE` hafta kuni nomi | — | ❌ | Y:fnow | S | L |
| EXP-098 | `now`: vaqt | `H`/`HH` soat (0–23), `k` (1–24), `K` (0–11), `h`/`hh` (12 soatli), `a` (AM/PM), `m`/`mm` daqiqa, `s`/`ss` soniya, `S` millisekund | 18:32:11 | ❌ | Y:fnow | S | M |
| EXP-099 | `now`: vaqt zonasi | `z` zona nomi, `Z` zona siljishi (RFC 822 ko'rinishi) | EET / +0200 | ❌ | Y:fnow | S | L |
| EXP-100 | `UUID()` | Tasodifiy UUID matni (har chaqiruvda yangi) | 36 belgi | ❌ | Y:fmisc | S | L |
| EXP-101 | `DecToHex`, `HexToDec` | O'nli ↔ o'n oltilik | DecToHex(255) = 'ff' | ❌ | Y:fnum | S | L |
| EXP-102 | `DecToOct`, `OctToDec` | O'nli ↔ sakkizlik | DecToOct(255) = '377' | ❌ | Y:fnum | S | L |
| EXP-103 | `DecToBin`, `BinToDec` | O'nli ↔ ikkilik | DecToBin(255) = '11111111' | ❌ | Y:fnum | S | L |
| EXP-104 | `roman(n)` | Rim raqami (1–3999) | roman(111) = 'CXI' | ❌ | Y:fnum | S | L |

### 2.11 Ifodalar dvigateli — qo'llanish joylari va tizim xossalari

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| EXP-110 | Qo'llanish joylari | Ifoda ishlatiladigan joylar: etiketka elementlari pozitsiyasi va mazmuni; XNC parametrlari; ParamGrid dagi `visible/suffix/readOnly`; dinamik tugma ikonkasi (`$ifoda`); ustun formulalari (D7 «keyin») | 5 joy | 🟡 | Y:labels; Y:grid; Y:btn; J3; `xnc.py` (faqat XNC) | M | H |
| EXP-111 | Qiymat beruvchi (kontekst) | Dvigatelga o'zgaruvchi qiymatlarini beruvchi obyekt: shablon uchun `part/project/...`, interfeys uchun forma maydonlari | nom → qiymat | 🟡 | Y:btn (`IValueProvider`); `eval_expr(env: dict[str,float])` (faqat son) | M | H |
| EXP-112 | Xavfsizlik chegaralari | Uzunlik, qadam, sikl, chuqurlik chegaralari; `eval` ishlatilmaydi | 200 belgi, 1e6 qiymat, 100 000 qadam | ✅ | `xnc.py` (`MAX_EXPR`, `MAX_VALUE`, …) | S | L |
| EXP-113 | Xato bilan ishlash | Ifoda xatosi jim 0 ga aylanmaydi — ogohlantirish va hisoblagich | — | ✅ | `xnc.py::_describe`, `EvalOps.problems` | S | L |
| EXP-114 | O'nli vergulni normallashtirish | `1,5*dx` → `1.5*dx` (funksiya argument vergulidan farqlanadi); GibLab yordamida bunday qoida yo'q — bizning qo'shimcha | — | ✅ | `xnc.py::_fix_commas` | S | L |

### 2.12 Interfeys komponentlari (ParamGrid, ToolBar, button)

GibLab interfeysi deklarativ tavsiflanadi (yordam «development» bo'limida). Bizda har panel qo'lda yozilgan React formasi (`Field`,
`Num`, `Sel`, `Check`, `Area`, `Tabs`, `IconBtn`: `frontend/src/shared/ui.tsx`).

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| DEV-001 | `ParamGrid` — parametrlar to'ri | Nom, yordam sahifasi URL, parametr nomi ustuni eni (standart 100 px), tooltip, eni/bo'yi (CSS) bilan guruhlangan forma | `labelWidth=100` | 🟡 | Y:grid; `ui.tsx::Field`, `.form2` | M | M |
| DEV-002 | `group` — guruh | Nomi, yorlig'i, yordam havolasi yoki `#anchor`, ko'rinish sharti (**ifoda**, standart true) | — | 🟡 | Y:grid; `.form-h` sarlavhalar (shartsiz, yordamsiz) | S | L |
| DEV-003 | `param` — asosiy atributlar | Nom, tur, yorliq | — | 🟡 | Y:grid; `Field label=…` | S | M |
| DEV-004 | `param.visible` | Parametrni ko'rsatish sharti — ifoda | true | ❌ | Y:grid | M | M |
| DEV-005 | `param.suffix` | Qo'shimcha matn/birlik — ifoda (masalan, valyuta yoki mm) | — | 🟡 | Y:grid; `Field unit=` (statik) | S | L |
| DEV-006 | `param.readOnly` | Faqat o'qish — ifoda | false | 🟡 | Y:grid; `ro` span (statik) | S | L |
| DEV-007 | `param.allowedNull` | Bo'sh qiymatga ruxsat | false | ❌ | Y:grid | S | L |
| DEV-008 | `param.multiline` | Ko'p qatorli matn balandligi (manfiy → standart qator) | −1 | ✅ | Y:grid; `ui.tsx::Area` | S | L |
| DEV-010 | Turlar: `string`, `integer`, `double`, `boolean` | Asosiy kiritish turlari | 4 tur | ✅ | Y:grid; `Num`, `Check`, input | S | M |
| DEV-011 | Tur `timestamp` | Sana-vaqt kiritish | — | 🟡 | Y:grid; `project/Header.tsx` (sana) | S | L |
| DEV-012 | Tur `color` | Rang tanlash | — | ✅ | Y:grid; `ElPanel.tsx` (`input type=color`) | S | L |
| DEV-013 | Turlar `stroke`, `fill` | Chiziq (rang/qalinlik/uslub) va to'ldirish xossasi — etiketka/XNC elementlari uchun | — | ❌ | Y:grid | M | M |
| DEV-014 | Tur `image` | Rasm tanlash/ko'rsatish (etiketka logotipi) | — | ❌ | Y:grid | M | M |
| DEV-015 | Tur `expression` | Ifoda kiritish maydoni (sintaksis tekshiruvi, o'zgaruvchi tanlash) | — | ❌ | Y:grid; `XncPanel.tsx` (oddiy matn) | M | H |
| DEV-016 | Turlar `file`, `folder` | Fayl / papka tanlash | — | 🟡 | Y:grid; `<input type=file>` (import oynalarida) | S | L |
| DEV-017 | Turlar `object`, `control`, `widget`, `alphabet`, `numeration` | Murakkab/maxsus kontrollar (ma'nosi yordamda ochilmagan; `numeration` — raqamlash sxemasi, `alphabet` — belgilar to'plami bo'lishi mumkin) | — | ❓ | Y:grid | M | L |
| DEV-018 | Tur `password` | Yashirin matn | — | ❌ | Y:grid | S | L |
| DEV-020 | `ToolBar` | CSS sinfi bilan asboblar paneli; ichida tugma va ajratgich | — | ✅ | Y:bar; `.toolbar`, `IconBtn` | S | L |
| DEV-021 | `separator` | Tugmalar guruhlari orasidagi ajratgich | — | ✅ | Y:bar | S | L |
| DEV-022 | `button.action` | Tugma/menyu bandi ro'yxatdan o'tgan amalga (nom yoki raqam) bog'lanadi | — | ✅ | Y:btn; `onClick` | S | L |
| DEV-023 | `button.label`, `button.title` | Yorliq va tooltip; menyu bandida yorliq bo'sh bo'lsa tooltip matni ishlatiladi | — | ✅ | Y:btn; `IconBtn title=` | S | L |
| DEV-024 | `button.image` | Ro'yxatga olingan rasm nomi yoki URL; `$` bilan boshlansa ifoda hisoblanadi (holatga qarab ikonka almashadi) | — | 🟡 | Y:btn; `lucide-react` (statik ikonkalar) | S | L |
| DEV-025 | `button.key` | Tooltipda yorliqni ko'rsatish (Ctrl+…) | — | 🟡 | Y:btn; `hotkeys.ts` (HOTKEYS jadvali; tooltiplar tizimsiz) | S | M |
| DEV-026 | `button.width`, `button.visible` | Eni (CSS, faqat tugma uchun); ko'rinish `*.visible` parametri bilan boshqariladi | — | ✅ | Y:btn; JSX shartlari | S | L |
| DEV-027 | `button.type = fileText / fileDataUrl / fileArrayBuffer` | Fayl tanlash tugmasi: tarkibni matn / Data URL / ikkilik bufer sifatida qaytaradi (etiketka shabloni, rasm, import uchun) | 3 tur | 🟡 | Y:btn; import oynalari (`FileReader` har joyda alohida) | S | M |
| DEV-028 | `button.extensions`, `button.multiple` | Fayl kengaytmalari ro'yxati; ko'p fayl tanlash | `multiple=false` | 🟡 | Y:btn; `accept=".xlsx,.csv"` | S | L |

## 3. (O) Комплектация и другие действия — to'liq spetsifikatsiya (bizda yo'q)

### 3.1 Maqsad va chegaralar

Murakkab hisobsiz ishlar uchun «oddiy operatsiya»: furnitura va qadoq materiallari sarfi, transport / o'rnatish / qadoqlash ish
narxi, maxsus ko'rsatma. Optimizatsiya, kromka, geometriya — yo'q. Faqat jadval + uchta narx + izoh. Bu operatsiya (a) omborga
talabnomaga furnitura qatorlarini beradi, (b) mahsulot tannarxini to'liqlashtiradi (hozir kroy + kromka + paz + XNC dan iborat),
(c) Bazis-Mebelshik importidagi komplektuyushchielarni saqlab qolish joyini beradi.

### 3.2 Ma'lumot modeli (`backend/app/models.py`, yangi — eski JSON mos qoladi)

```python
class OMaterial(Base):
    id: str = Field(default_factory=_id)
    code: str = Field("", max_length=100)         # Код
    name: str = Field("", max_length=300)         # Наименование
    unit: str = Field("шт", max_length=20)        # Ед.И (шт, м, м², компл. …) — erkin matn
    qty: float = Field(1, ge=0, le=1e9)           # Кол (kasr ruxsat)
    price: float = Field(0, ge=0, le=1e9)         # Цена (1 birlik)
    # Стоимость qatori = qty × price — saqlanmaydi, hisoblanadi (UI va hisobotda)

class OParams(Base):
    owner_product_id: Optional[str] = None        # Владелец: None = butun loyiha; aks holda Product.id
    materials: list[OMaterial] = Field(default_factory=list, max_length=5000)
    work_cost: float = Field(0, ge=0, le=1e9)     # Стоимость операции (ish narxi), qo'lda
# Operation:  o: Optional[OParams] = None   (description — mavjud maydon; «Описание» shu)
```

* `Operation.o` yangi maydon (default `None`) → migratsiya kerak emas; `_new_operation` (`main.py`) `OpType.O` da `o = OParams()` yaratadi.
* `legacy`-kontekstda chegaradan chiqqan qiymatlar qisqartiriladi (mavjud `_fix_range` namunasi).
* Mahsulot o'chirilsa (`owner_product_id` yetim) — `owner_product_id = None` (loyiha egasi) va ogohlantirish (XNC `prune_xnc` kabi).
* Standart qiymatlar: `settings` ga `o_defaults` scope (`OParams` dan owner'siz: `work_cost` va birlik).

### 3.3 Hisob (`services/calc.py::o_cost`, `recalc_project` ichida chaqiriladi)

```
mult           = product.qty        agar owner_product_id berilgan va mahsulot bor
               = 1                  aks holda (loyiha egasi)
cost_material  = round( Σ(qty_i × price_i) × mult , 2 )
cost_operation = round( work_cost × mult , 2 )
cost           = cost_material + cost_operation              (Operation.cost property mavjud)
warehouse qty_i = qty_i × mult                                (talabnomada har qator)
```

* Qator «Стоимость» ustuni (jadvalda) = `qty × price` **ko'paytirgichsiz** (1 mahsulot uchun); ko'paytirgichli jami — pastki
  qatorda va «Параметры» yorlig'ida. (Yordam «soni va narx ko'paytiriladi» deydi; qator ustuni qaysi ko'rinishda ekani aniq
  emas — §7 savol 5.)
* Yaxlitlash: qator narxi saqlanmaydi, jami 2 xonagacha (qolgan operatsiyalar bilan bir xil).
* `mult` = 0 (mahsulot soni 0) → narx 0, talabnomada qator chiqmaydi.

**Namuna (qabul testi).** Mahsulot «Shkaf», soni 3. O operatsiya, egasi = «Shkaf»: «Ruchka» шт 4 × 15 000 = 60 000; «Plyonka» м 2.5 × 8 000 =
20 000; ish narxi 50 000. → `cost_material = 80 000 × 3 = 240 000`, `cost_operation = 50 000 × 3 = 150 000`, jami **390 000**; talabnoma:
Ruchka 12 шт, Plyonka 7.5 м. Egasi = loyiha bo'lsa: 80 000 + 50 000 = **130 000**, talabnoma: 4 шт, 2.5 м.

### 3.4 Ekran (UI) — `frontend/src/features/o/OPanel.tsx` (yangi)

Yorliqlar (GibLab bilan bir xil joylashuv): **«Параметры»** | **«Материалы»**; yuqori o'ngda: «Сохранить текущие параметры для
использования по умолчанию», «?» (F1).

**Параметры**: `Владелец` (select: «Проект» + «№ Mahsulot nomi (N шт)»), `Стоимость материала` (faqat o'qish; × mult
ko'rsatma bilan), `Стоимость операции` (kiritiladi, valyuta birligi), `Стоимость` (faqat o'qish), `Описание` (ko'p qatorli, `Operation.description`).

**Материалы**: AG Grid (`shared/grid/Grid.tsx`), ustunlar `№ | Код | Наименование | Ед.И | Кол | Цена | Стоимость`
(`Стоимость` faqat o'qish). Toolbar: qator qo'shish (Ctrl+PgDn) / joriydan oldin qo'shish (Ctrl+PgUp) / o'chirish (Del) / ↑↓ (Ctrl+↑/↓) /
klonlash (Ctrl+K) / ustunlar (Ctrl+P). Pastki qator: «Всего: N позиций · X». Excel/OpenOffice'dan **Ctrl+V**: ustunlar tartibi
`Код, Наименование, Ед.И, Кол, Цена`; `1 200,5` va `2 шт` kabi qiymatlar `importers.parse_number` bilan; noto'g'ri qatorlar
«o'tkazib yuborildi» xabari bilan (detallardagi `skipped/warnings` namunasi).

Operatsiyalar jadvalida: nom avto «Комплектация N»; `opmeta.tsx::IMPLEMENTED` ga `"O"`; `OperationsTable.defName`; tur
tanlash dialogida endi faol. Undo/redo — mavjud `store.editing` orqali (har tahrir bitta qadam).

### 3.5 API

| Usul va yo'l | Vazifa |
|---|---|
| `POST /api/projects/{pid}/operations` `{type:"O", name?}` | O yaratish (`o = OParams()`), `position` bilan qo'yish |
| `PATCH /api/projects/{pid}/operations/{oid}` `{o:{owner_product_id, work_cost}, description}` | parametrlar |
| `PUT /api/projects/{pid}/operations/{oid}/o/materials` `[OMaterial…]` | butun jadvalni almashtirish (bitta undo qadami) |
| `POST /api/projects/{pid}/operations/{oid}/o/materials/paste` `{text, mode:"append"}` | Excel matnidan (TSV) qo'shish; javob: `{added, skipped:[{row,reason}], warnings}` |
| `PUT /api/settings/o_defaults/default` | standart |

Server tekshiruvlari: qiymat chegaralari (422), qatorlar ≤ 5000, `owner_product_id` mavjud mahsulot, matn uzunliklari.

### 3.6 Hisobot va boshqa hisoblarga ta'siri

| Joy | O ning ishtiroki | Fayl |
|---|---|---|
| «Операции» ro'yxati (hisobot + UI) | `Ст. м-ла`, `Ст. оп-и`, `Ст-ть` ustunlarida | `render.py`, `OperationsTable.tsx` |
| «Требование на склад» | har O material qatori: Тип `O`, Код, Наименование (`op.name — material nomi`), Ед.И, Кол = `qty × mult` | `calc.warehouse_request`, `render.py`, `mes.py` (mes-export) |
| Mahsulot narxi (Изделия: Ст. м-ла / Ст. оп-и, B10) | egasi mahsulot → butun narx shu mahsulotga (1 dona uchun = jami / soni); egasi loyiha → mahsulotlarga **taqsimlanmaydi** (faqat loyiha jamida) — §7 savol 3 | `calc.product_costs` |
| Hisobotdagi alohida bo'lim | yangi sahifa (Н.Стр ✓): sarlavha «(O) …», parametrlar bloki, materiallar jadvali `№ Код Наименование Ед.И Кол Цена Стоимость`, izoh | `render.py::_o_section` (yangi) |
| Chop sozlamalari | `PrintSettings.o_params`, `o_materials` (bizning qo'shimcha; GibLab yordamida O uchun chop bo'limi ko'rinmaydi) | `models.py`, `Print.tsx`, `i18n_src.py` |
| Loyiha jami (Стоимость, С-ть материала, С-ть операций) | O ham yig'iladi | `main.py` (jamilar) |
| MES buyurtmasi | furnitura qatorlari omborga talabnomada | `mes.py` |

### 3.7 Import (Bazis-Mebelshik / `.project`)

`legacy_project.py` hozir `O, CL, SP, LB, CN` ni o'tkazib yuboradi (satr ≈ 407). Qo'shish: `typeId=O` operatsiyasi → `Operation(type=O)`
+ `material` havolalari (kod, nom, soni; narx — `good` yozuvidan, birlik — bo'lsa) → `OMaterial`; `owner` — mahsulotga bog'langan bo'lsa
`owner_product_id`. Qolgan operatsiyalar o'tkazib yuborilishi ogohlantirishi saqlanadi (faqat O chiqarib tashlanadi).

### 3.8 Qabul testlari (`backend/tests/test_o_operation.py`)

1. §3.3 namunasi (mahsulot egasi) — 390 000 va talabnoma 12 / 7.5; loyiha egasi — 130 000.
2. Mahsulot soni o'zgarsa (3 → 5) — narx va talabnoma qayta hisoblanadi.
3. Mahsulot o'chirilsa — operatsiya loyiha egasiga o'tadi, ogohlantirish.
4. Paste: `1 200,5` va `2 шт` qiymatlari, bo'sh qator, 5001-qator → `skipped`.
5. Eski JSON (O siz) ochiladi; `Operation.o = None` operatsiya (migratsiyasiz) xato bermaydi.
6. Hisobot: O bo'limi va talabnoma qatori; mahsulot narxi jadvali.
7. Chegaralar: manfiy qty/price → 422; ulkan matn → 422.
8. Bazis importida O komplektlari qatorlarga aylanadi.

### 3.9 Fayllar va hajm

`models.py` (OMaterial, OParams, Operation.o, PrintSettings), `services/calc.py` (o_cost, recalc, warehouse, product_costs),
`main.py` (_new_operation, patch, materials/paste), `services/importers.py` (paste parser umumlashtirish), `services/render.py`,
`services/mes.py`, `plugins/legacy_project.py`, `services/settings.py` (`o_defaults`), `frontend/src/features/o/OPanel.tsx` (yangi),
`features/project/opmeta.tsx`, `OperationsTable.tsx`, `api/types.ts`, `scripts/i18n_src.py`, `features/print/Print.tsx`, testlar.
Hajm: **M** (≈ 2–3 kun, testlar bilan).

## 4. (LB) Etiketka shablon tizimi — spetsifikatsiya

### 4.1 Hozirgi holat (bizda)

`services/labels.py::labels_html` — **qat'iy shablon**: sarlavha (loyiha № va nomi), detal `uid` + belgilar (`=` `*` `%`) + nomi, o'lcham
`L × W × qalinlik`, material (CS operatsiya nomi), mahsulot nomi (ixtiyoriy), `nusxa/jami · karta №`, kromka sxemasi (4 tomon, belgi,
chiziq soni) va QR (`MXK:<loyiha №>:<detal ID>:<nusxa>/<jami>` — MES skaneri `GET /api/mes/scan/{kod}` bilan o'qiydi).
Sozlamalar — global `LabelSettings` (`width_mm`, `height_mm`, `columns` [0 = termoprinter], `qr`, `show_edges`, `show_product`,
`show_map`), chop bo'limidagi «Этикетки» da; operatsiya sifatida emas. Faqat CS detallari; qoldiq/mahsulot yo'q; matn va
joylashuvni foydalanuvchi o'zgartira olmaydi.

### 4.2 Bosqichlar

| Bosqich | Mazmuni | Hajm | Ochadigan ID lar |
|---|---|---|---|
| **LB-A** — operatsiya va parametrlar | LB ni loyiha operatsiyasi qilish (`Operation.lb`), parametrlar (§4.3), manba: detallar / qoldiqlar / mahsulotlar, A4-to'r va rulon rejimi, jami soni, 3–4 ta **o'rnatilgan** shablon (hozirgi QR etiketka — standart) | M (≈ 3–4 kun) | LB-001…018, LB-023, LB-058 |
| **LB-B** — JSON shablon + ifodalar | Shablon sxemasi (§4.4), o'zgaruvchilar (§4.6), render (SVG), kutubxona + import/eksport, JSON-redaktor + jonli ko'rinish. Umumiy ifoda dvigateli (§5) shu bosqichga **to'siq** | L (≈ 2 hafta) | LB-034…039, 046…052, 053 (qisman), 055…059, 060…072, 080…085 |
| **LB-C** — vizual redaktor | Kanvas (SVG), element palitrasi, xossalar paneli, undo/redo, zoom-to-fit, F4/F9, miniatyurali kutubxona oynasi | L (≈ 2–3 hafta) | LB-030…033, 056, 057 |
| **LB-D** — kengaytmalar | Polilinya/yoy/Bezye/ellips, sikllar (WD/DW), foydalanuvchi ma'lumotlari jadvali (`source=user`), `.lbl` importyori (korxonaning o'z fayllari — ruxsat bilan), to'g'ridan-to'g'ri printer tillari (ZPL/TSPL), arra markazi uchun etiketka eksporti | L | LB-019, 040…045, 087 |

Ustuvorlik: LB-A — M (printer o'lchami aniqlangach, §7 savol 1); LB-B/C — printer va shablon shakli aniqlangach. Hozirgi QR oqimi
(MES + sex rejimi) ishlayotgani uchun shoshilinch emas, lekin LB-A xodimlar ko'radigan eng sezilarli kamchilikni (A4/rulon,
qoldiq etiketkasi, tanlangan detallar) yopadi.

### 4.3 `LBParams` (`Operation.lb`)

```python
class LBParams(Base):
    source: Literal["parts", "products", "user"] = "parts"    # parts = detallar va qoldiqlar (GibLab: 2), products (1), user (0)
    mode: Literal["sheet", "roll"] = "roll"                   # «На формат A4» / «На принтер этикеток»
    width_mm: float = Field(58, gt=0, le=500); height_mm: float = Field(40, gt=0, le=500)
    columns: int = Field(3, ge=1, le=20); rows: int = Field(0, ge=0, le=50)     # rows 0 = avto
    gap_mm: float = Field(2, ge=0, le=50); margin_mm: Optional[float] = 6       # None = «Поля страницы» o'chiq
    border: bool = True
    # detallar va qoldiqlar
    print_parts: bool = True; part_each: bool = True; part_only_nonzero: bool = True
    part_selected: list[int] = []                              # tanlangan detal uid lari (bo'sh = hammasi)
    print_wastes: bool = False; waste_each: bool = True
    # mahsulotlar
    product_each: bool = False; product_only_nonzero: bool = True
    template_id: Optional[str] = None                          # kutubxonadan; None = o'rnatilgan
    template: Optional[dict] = None                            # loyiha ichidagi nusxa (GibLab: program)
    params: dict[str, str | float | bool] = {}                 # shablon parametrlari (Par) qiymatlari
    fields: list[dict] = []; data: list[dict] = []             # source=user: {name,title,type,width,default}; qatorlar
```

`count` (jami soni) — hisoblanadi, saqlanmaydi (`GET .../operations/{id}/lb/count`). `LabelSettings` global profili eskirgan deb
belgilanadi (eski chop bo'limi LB-A dan keyin shu operatsiyani ishlatadi; eski profillar migratsiya bilan `LBParams` ga o'tadi).

### 4.4 Shablon formati (JSON, o'zimizniki)

Koordinatalar mm; boshlang'ich nuqta — chap-yuqori, X o'ngga, Y pastga (XNC va kroy kartalari bilan bir xil). Har geometrik va
mazmun maydoni **ifoda** (§5); oddiy son/matn ham ifoda sifatida yoziladi.

```json
{ "v": 1, "name": "Detal 58x40", "size": {"w": 58, "h": 40},
  "params": [ {"name": "margin", "type": "double", "default": 2, "title": "Maydon"} ],
  "vars":   [ {"name": "code", "expr": "'MXK:'+project.number+':'+part.id"} ],
  "elements": [
    {"t": "rect",    "x": "margin", "y": "margin", "w": "58-2*margin", "h": "40-2*margin", "stroke": {"w": 0.2}},
    {"t": "text",    "x": "3", "y": "5", "text": "left(project.name,24)", "size": 2.6, "bold": true, "maxw": "36"},
    {"t": "barcode", "kind": "qr", "x": "40", "y": "18", "size": "15", "data": "code", "caption": false},
    {"t": "if", "cond": "groove", "then": [ {"t": "text", "x": "3", "y": "30", "text": "'PAZ'"} ]},
    {"t": "group", "rotate": "90", "origin": ["50", "6"], "elements": [ {"t": "barcode", "kind": "code128", "x": "0", "y": "0",
        "w": "30", "h": "8", "data": "rspace(right(part.id,4),4,'0')", "caption": true} ]} ] }
```

### 4.5 Minimal imkoniyatlar to'plami (MVP, LB-B)

| Element / buyruq | Zarur xossalar | GibLab ekvivalenti |
|---|---|---|
| `text` | x, y, matn-ifoda, shrift o'lchami, qalin, tekislash (chap/o'rta/o'ng), maksimal eni (sig'dirish yoki qatorlarga bo'lish), burish | Текст (LB-046) |
| `barcode` | `qr` va `code128`; x, y, o'lcham/balandlik, ma'lumot-ifoda, matn ostida ko'rsatish; burish | Штрихкод (LB-047) |
| `image` | data URL (png/jpeg), x, y, eni, bo'yi | Изображение (LB-048) |
| `line`, `rect` | koordinatalar, chiziq qalinligi, to'ldirish | Линия, Прямоугольник |
| `part` | kontur + o'lchamlar + kromka qalin chiziqlari; x, y, eni, bo'yi | Деталь (LB-051) |
| `edges` | kromka belgilari (4 tomon, belgi, chiziq soni) | Кромка (LB-052) |
| `origin`, `rotate` (guruh) | siljish, burchak (0/90/180/270) | Начало координат, Вращение |
| `if` / `else`, `var`, `par` | shart-ifoda; hisoblangan o'zgaruvchi; foydalanuvchi parametri (nom, tur, standart, sarlavha) | IF/Else, Var, Par |
| (LB-D) `polyline`, `ellipse`, `while` | boshlang'ich nuqta + chiziq/yoy/egri; markaz + yarim o'qlar; sikl | Стартовая точка, Линия, Дуга, Кривая, Эллипс, WD/DW |

### 4.6 O'zgaruvchilar

Har etiketka qatori uchun bitta lug'at: `labels_vars.build(project, op, row)`; `row.kind` — `part | remnant | product | user`.
Nomlash: **H5 jadvalidagi snake_case** asosiy (`part_uid`, `edge_top_symbol` …); xodimlar va eski shablonlar uchun GibLab nomlari
(`part.id`, `ets` …) **alias** sifatida qabul qilinadi (`ALIASES` jadvali, 104 ta — Ilova B). Shtrixkodlar uchun kerak: `project.crc32`,
`part.counter`. `part.counter` ma'nosi ❓ (§7 savol 4). Mavjud emas, lekin yordamda bor: kromka/paz kodi (`etc`, `grtc` …),
`XNC1…5` (CNC dasturi shtrixkodi uchun) — LB-B da qamrab olinadi.

### 4.7 Chop maketi

* `mode=sheet`: A4 (210×297), `columns × rows`, `gap`, `margin`, `border`; to'lganda yangi sahifa; to'ldirish — qator bo'ylab.
* `mode=roll`: `@page size = etiketka`, har etiketka alohida sahifa; `rotate_page` (0/90) — printer yo'nalishi uchun.
* Chiqish — HTML + inline SVG (hozirgi `labels_html` kengaytiriladi; brauzer «Chop etish»). To'g'ridan-to'g'ri printer tillari (ZPL/TSPL/ESC) — printer
  modeli aniq bo'lgach (LB-D).

### 4.8 UI

LB qatori «Операции» da; panel yorliqlari «Параметры» | «Шаблон». **Параметры** — LB-002…019 formasi + «Количество: N шт» + jonli
ko'rinish (birinchi 6 ta etiketka). **Шаблон**: LB-B da JSON-matn muharriri + xatolar ro'yxati + o'zgaruvchilar ro'yxati (bosib qo'yish) +
jonli ko'rinish; LB-C da kanvas: zoom-to-fit, to'r bo'yicha tortish, element palitrasi, xossalar paneli (DEV-015 ifoda maydoni), F4 (xizmat
buyruqlari), F9 (tanlangan namuna qatorida qiymatlar), undo/redo (Ctrl+Z/Y), eksport/import, kutubxona oynasi (papkalar, miniatyura, nom).

### 4.9 API va saqlash

| Usul va yo'l | Vazifa |
|---|---|
| `GET/POST/PATCH/DELETE /api/label-templates`, `/api/label-folders` | kutubxona (jadvallar `label_templates`, `content_folders`) |
| `POST /api/label-templates/preview` `{template, sample}` | saqlamasdan ko'rish (SVG/HTML) |
| `GET /api/label-templates/{id}/export`, `POST /api/label-templates/import` | JSON fayl bilan almashish |
| `GET /api/projects/{pid}/labels?op_id=` (mavjud), `GET .../labels.json` | HTML / hal qilingan qatorlar (tashqi printer, MES) |

### 4.10 Xavfsizlik va chegaralar

Ifodalar xavfsiz dvigatelda (§5): bitta etiketka uchun qadam chegarasi, ifoda ≤ 1000 belgi, shablon ≤ 500 element, ichma-ich ≤ 8,
`calculate` rekursiyasi yopiq. Rasm — faqat data URL (png/jpeg), ≤ 200 KB; SVG rad etiladi. Matn `escape` bilan chiqadi, mavjud CSP
(`render.CSP_META`) saqlanadi. Shtrixkod ma'lumoti uzunligi/alifbosi tekshiriladi (Code128 — ASCII; 50 mm da ≈ 16 raqam ogohlantirishi, LB-086).

### 4.11 Qabul mezonlari

1. Hozirgi etiketka o'rnatilgan shablon sifatida **mazmunan** o'zgarmaydi (QR matni `MXK:…` bir xil — MES skaneri va sex rejimi buzilmaydi).
2. Shablonda `if`, `format`, `rspace`/`right`, `crc32`, satr konkatenatsiyasi ishlaydi; ifoda xatosi — alohida ogohlantirish (jim bo'sh emas).
3. Code128 va QR; shtrixkodni 90° burish.
4. Qoldiq va mahsulot etiketkalari; «tanlangan detallar»; «soni 0 bo'lsa chiqarma».
5. 1000 etiketka ≤ 3 s; 10 000 ≤ 30 s (SVG, oqim bilan).
6. Shablon JSON eksport → import — aynan o'sha natija; kutubxonadan boshqa loyihada ishlatish.

## 5. Ifodalar tili — `xnc.py::eval_expr` bilan farq va umumiy dvigatel talablari

### 5.1 Bizdagi hisoblagich (qisqa)

`eval_expr(expr, env: dict[str, float]) -> float` — Python `ast.parse` ustiga qurilgan; qo'shimchalar: o'nli vergul normalizatsiyasi
(`1,5` → `1.5`), uzunlik ≤ 200, natija |x| ≤ 1e6, `a.b` ko'rinishidagi bir darajali nomlar (`origin.x`). Funksiyalar: `sin cos tan`
(**gradus**), `sqrt abs min max round floor ceil`. XNC dasturi buyruqlari parametrlari uchun yozilgan (J3); LB, ustun formulalari, forma
shartlari uchun yaroqsiz (satr va tip yo'q).

### 5.2 Farq jadvali (GibLab yordami ↔ bizdagi `eval_expr`)

| № | Mavzu | GibLab (yordam) | Bizda | Qaror / ta'sir |
|---|---|---|---|---|
| 1 | Tiplar | integer (32-bit), double, boolean, string, `null` | faqat `float` (boolean = 1.0/0.0) | yangi tipli qiymat modeli (R1) |
| 2 | `/` butunlar uchun | butun ÷ butun = **butun** (7/2 = 3) | har doim float (3.5) | LB shablonlarida muhim; XNC da eski dasturlar float kutadi → profil (R15) |
| 3 | Grammatika | o'z sintaksisi: `'satr'`, `true/false/null`, `if(a,b,c)`, `=`/`<>`, `^`, `xor` | Python: `a if c else b`, `**`, `==`/`!=`; `=`, `<>`, `xor` — xato; `^` = XOR (rad etiladi) | o'z leksemasi/parseri; eski (Python-uslubi) yozuvni ham qabul qilish (R2, R15) |
| 4 | Literal | `'abc'` + escape (`\n \t \uXXXX …`) | satr taqiqlangan | R2 |
| 5 | Trigonometriya | burchak **radianda** (cos(pi) = −1) | **gradusda** (J3: `sin(90) = 1`) | to'qnashuv: XNC uchun `deg` profili, umumiy dvigatelda `rad`; korxona XNC shablonlari qaysi birini kutadi — §7 savol 6 |
| 6 | `round` | yaqin butunga, yarimni **+∞ ga** (−1.5 → −1); natija butun | yarimni nol dan uzoqqa (−1.5 → −2); 2-argument (xona) bor | umumiy dvigatelda Java-qoidasi; XNC profili eskicha |
| 7 | `min`/`max` | 2 argument | 1–50 argument | variadic saqlansin (ustun) |
| 8 | `%` | «butun bo'lishdan qoldiq» | Python `%` (bo'luvchi ishorasi) | manfiy operandlarda farq; Java qoidasi (dividend ishorasi) test bilan tasdiqlansin |
| 9 | `=`/`==`, `<>`/`!=` | ikkala yozuv ham | faqat `==`, `!=`; `abs(a−b) ≤ 1e-9` | ikkala yozuvni qabul qilish; tolerans saqlansin (yaxshi) |
| 10 | `and`/`or` natijasi | boolean | operand qiymati (Python) | boolean qaytarish |
| 11 | Shart | `if(shart, a, b)` funksiya | `a if c else b` | ikkalasi |
| 12 | Funksiyalar | 67 nom | 10 | R6 (jadval §2.10) |
| 13 | Konstantalar | `pi`, `e`, `true`, `false`, `null` | yo'q | R2 |
| 14 | O'zgaruvchi nomlari | nuqtali ierarxiya (`project.name`, `detail.length`), turli tip | `a.b` (1 daraja), faqat son | kontekst provayder (R10) |
| 15 | `format`, `now` | Java `DecimalFormat` / `SimpleDateFormat` naqshlari, lokalga bog'liq | yo'q | R8, R9 |
| 16 | `calculate(s)` | satrdan ifoda hisoblash | yo'q | R13 (xavfsizlik bilan) |
| 17 | Natijani matnga aylantirish | `double` → «2.0», `integer` → «2», boolean → `true/false` | yo'q | R5, R18 |
| 18 | Xatolar | yordamda ta'riflanmagan | xabar + hisoblagich (jim 0 emas) | bizniki saqlansin (R12) |
| 19 | Xavfsizlik chegaralari | yordamda yo'q | uzunlik, qiymat, qadam, sikl chegaralari | saqlansin va kengaytirilsin (R13) |
| 20 | Registr sezgirligi | noma'lum | o'zgaruvchi — sezgir, funksiya — kichik harf | ❓ (EXP-044) |

### 5.3 Umumiy ifoda dvigateli uchun talablar

**Tiplar va grammatika**

* **R1.** Qiymat tiplari: `int32`, `double`, `bool`, `str`, `null`. Aniq tur xatolari (masalan `bool` + `bool`) tushunarli xabar bilan.
* **R2.** O'z tokenizeri va parseri (Pratt/precedence climbing); `ast`/`eval` ishlatilmaydi. Literallar: son (`.` va `,` o'nli), `'satr'`
  (+ `"satr"` — bizning kengaytma), `true`/`false`/`null` (registrsiz), konstantalar `pi`, `e`. Satr escape: `\b \f \n \r \t \' \" \\ \uXXXX`.
* **R3.** Operatorlar: `+ − * / % ^`, unar `+ −`, `< > <= >= = == <> !=`, `not and or xor`, qavs, `if(c,a,b)`. Taklif etilgan ustuvorlik
  (yuqoridan pastga; yordamda berilmagan — testda tasdiqlansin): qavs → funksiya chaqiruvi → `^` (o'ngdan chapga assotsiativ, unar
  minusdan kuchli: `-2^2 = -4`) → unar `+ −` → `* / %` → `+ −` → taqqoslash → `not` → `and` → `xor` → `or` (Python/SQL tartibi — mavjud
  XNC ifodalari bilan mos; `not` ning aniq o'rni ❓).
* **R4.** Tip qoidalari: `int ⊕ int = int` (bo'lish — butunli; nolga bo'lish — xato); aralash → `double`; `int32` toshishi — `double` ga
  ko'tarilish yoki xato (yordamda yo'q — ❓ test); `NaN` natija — xato.
* **R5.** `+` da operandlardan biri satr bo'lsa — konkatenatsiya; son/boolean/`null` avtomatik matnga (`double` → Java `Double.toString`
  uslubi: `2.0`, `1.2246467991473532E-16`; `int` → `2`; `bool` → `true`/`false`; `null` → `''` ❓). Satr funksiyalari son argumentini ham qabul
  qiladi (`right(part.id,4)`, `rept(123,2)`).

**Funksiyalar kutubxonasi**

* **R6.** 67 nomning hammasi (§2.10) ro'yxat-reestrda: `FunctionSpec(name, min_args, max_args, arg_types, returns, impl, doc_ru, doc_uz, example, pure)`.
  Avtotoʻldirish va yordam shu reestrdan olinadi (R17).
* **R7.** Semantika (test-vektorlar §5.5): indekslar **1 dan** (`mid`, `find`); topilmasa `find` = 0; `findr` — teskari qidiruv;
  `lspace` = chapga tekislab o'ngdan to'ldirish, `rspace` = o'ngga tekislab chapdan to'ldirish (uzun satrni qisqartirish — ❓);
  `boolean(s)`: `true/True/T/1` → true, `''/false/f` → false; `integer('1.0') = 1`; `translit` — kirill → lotin jadvali (hujjatlangan);
  **`crc16` = CRC-16/ARC** (poli 0x8005, aks, boshlang'ich 0, `crc16('test')=63534`); **`crc32` = IEEE CRC-32, ishorali int32**
  (`crc32('test') = −662733300`); `ucase/lcase` — Unicode; trigonometriya radianda; `round` — yarim +∞ ga; `%` — dividend ishorasi (taxmin).
* **R8.** `format(naqsh, son)`: Java `DecimalFormat` ning quyi to'plami — `0 # . , - ; % ‰ ¤ ' E`; musbat/manfiy qism naqshlari;
  o'nli/guruh ajratgichlari **lokalga bog'liq** (`ru`: vergul; `uz`: ❓; shtrixkod/fayl nomi uchun `invariant` rejimi kerak).
* **R9.** `now(naqsh)`: Java `SimpleDateFormat` ning quyi to'plami (`G y yy yyyy M MM MMM MMMM w ww W WW D d dd F FF E EEEE a H HH k K h hh m mm s ss S z Z`);
  oy/hafta kuni nomlari ru/uz; vaqt zonasi sozlanadi; testlar uchun soat in'ektsiya qilinadi (`clock`).
* **R10.** Kontekst provayderi: `lookup(name) -> Value | MISSING`; nuqtali nomlar; noma'lum nom — xato (jim 0 emas), xabarda yaqin nom
  taklifi; kontekst turi har joyda (etiketka qatori, XNC detali, forma maydonlari) boshqa.

**Ishonchlilik va xavfsizlik**

* **R11.** Kompilyatsiya bosqichida tekshiruv: noma'lum funksiya, argument soni, ochiq tur mos kelmasligi — chop etishdan oldin muharrirda xato.
* **R12.** Xatolar: `ExprError(kod, xabar_ru/uz, pozitsiya)`; bo'lish nolga, domen xatosi, tur xatosi, chegara — hammasi xato; hisoblagich va
  ogohlantirish ro'yxati (mavjud `EvalOps.problems` namunasi).
* **R13.** Chegaralar: ifoda ≤ 1000 belgi, daraxt chuqurligi ≤ 64, bitta hisoblash ≤ 10 000 qadam, satr uzunligi ≤ 10 000,
  `rept`/`format` natijasi chegaralangan, `calculate` rekursiyasi ≤ 4 va umumiy qadam byudjetini ishlatadi, `random/UUID/now` — `pure=False`
  (keshlanmaydi); atribut/metod/import/fayl/tarmoq yo'q; faqat reestrdagi funksiyalar.
* **R14.** Unumdorlik: kompilyatsiya keshi (LRU); 10 000 etiketka × 30 ifoda ≤ 3 s.

**Moslik va integratsiya**

* **R15.** XNC uchun moslik profili: eski Python-uslubidagi yozuv (`a if c else b`, `**`) va **gradusdagi** trigonometriya, hamda eski `round`
  — mavjud dasturlar o'zgarmasligi uchun. `xnc.py::eval_expr` imzosini saqlagan holda yangi dvigatelga yo'naltiriladigan yupqa o'ram bo'ladi.
  Qabul sharti: 223 backend test + `tools/bench/xnc_check.py` + `el_check.py` o'zgarishsiz o'tadi.
* **R16.** Xabarlar ru/uz (`app/i18n.py`); funksiya hujjatlari ham ikki tilda.
* **R17.** Muharrir uchun API: `GET /api/expr/functions` (nom, imzo, tavsif, misol), `POST /api/expr/check` `{expr, context_kind, sample}` →
  `{ok, type, value, errors[]}`. Ifodani **faqat serverda** hisoblash (JS da ikkinchi dvigatel yozilmaydi — farq xavfi).
* **R18.** Qiymatni matnga aylantirish yagona funksiya (`to_text`), shtrixkod va konkatenatsiya shuni ishlatadi.
* **R19.** Fayl tuzilishi: `backend/app/services/expr/` (`lexer.py`, `parser.py`, `types.py`, `functions_math.py`, `functions_str.py`,
  `format_java.py`, `datefmt.py`, `errors.py`, `registry.py`). Shablon (Jinja2) postprotsessorlari alohida qoladi.
* **R20.** Testlar: yordam misollaridan «oltin» vektorlar (§5.5), fuzz (osilib qolmaslik), Python matematik kutubxonasiga qarshi xossalar testlari.

Hajm: **L** (≈ 8–12 kun: yadro 3 kun, kutubxona 3 kun, `format/now` 2 kun, XNC moslik + testlar 2 kun, API/muharrir 2 kun). Ustuvorlik **H**
(LB-B va ustun formulalariga to'siq), lekin XNC ishlayotgani uchun hozir xavfsiz o'rnatiladigan o'ram bilan boshlanadi.

### 5.4 Yordam misollaridagi nomuvofiqliklar

Yordam misollarida matematikaga zid joylar bor (`log(100.0) = 0.5`, `log2(4.0) = 0.5`, `asec(1) = π/2`, `coth(4.0) = 54.598…`, `sign(0) = -0.0`,
`floor`/`asin` imzolari xato nusxalangan). Test-vektorga olinmadi; haqiqiy xatti-harakat jonli tekshiruvda aniqlanadi (foydalanuvchi bilan, §7).

### 5.5 Test-vektorlar (yordam misollaridan; zid joylar chiqarib tashlangan)

| Guruh | Ifoda → kutilgan qiymat |
|---|---|
| Taqqoslash/mantiq | `1>2` → false; `1!=2` → true; `1<>2` → true; `1-3+2==0` → true; `if(1!=2,1,2)` → 2; `if(true,'Да','Нет')` → 'Да' |
| Satr `+` | `'abc'+'XXX'` → 'abcXXX'; `'abc'+1` → 'abc1'; `'abc'+1+2` → 'abc12'; `'abc'+(1+2)` → 'abc3'; `'result:'+(1=2)` → 'result:false' |
| Matematika | `abs(-1.22)` → 1.22; `ceil(1.5)` → 2.0; `floor(-1.5)` → -2.0; `round(-1.5)` → -1; `round(2.2)` → 2; `round(2.5)` → 3; `max(1,-3.0)` → 1.0; `min(9,3)` → 3; `sqrt(4)` → 2.0; `cos(pi)` → -1.0; `acos(-1)` → 3.141592653589793; `ln(2)` → 0.6931471805599453; `logx(9,3)` → 2.0; `sin(1.5)` → 0.9974949866040544; `sec(pi)` → -1.0 |
| Satr funksiyalari | `len('abc')` → 3; `mid('abc',3,1)` → 'c'; `left('abc',2)` → 'ab'; `right('abc',2)` → 'bc'; `lspace('abc',5,'X')` → 'abcXX'; `rspace('abc',5,'X')` → 'XXabc'; `rept(123,2)` → '123123'; `ns(null)` → ''; `empty('')` → true; `trim(' abc ')` → 'abc'; `ltrim(' abc ')` → 'abc '; `rtrim(' abc ')` → ' abc'; `ucase('Abc')` → 'ABC'; `translit('Пример')` → 'Primer' |
| Qidirish/almashtirish | `find('abcd','bc',1)` → 2; `find(1234,23,1)` → 2; `findr('abcdbc','bc',6)` → 5; `findr(1234123,2,7)` → 6; `replace('1231','1','9')` → '9239'; `startswith(1234123,12)` → true; `endswith('abc','ab')` → false |
| Konvertatsiya | `double('1.0')` → 1.0; `integer('1.0')` → 1; `boolean('T')` → true; `boolean('')` → false; `crc16('test')` → 63534; `crc32('test')` → -662733300 |
| Sonli | `DecToHex(255)` → 'ff'; `HexToDec('ff')` → 255; `DecToOct(255)` → '377'; `DecToBin(255)` → '11111111'; `BinToDec('11111111')` → 255; `roman(111)` → 'CXI' |
| Format/aralash | `format('0.000',23.2)` → '23.200'; `format('0000',1)` → '0001'; `format('%',0.32)` → '%32'; `calculate('1+2')` → 3; `now('yyyy.MM.dd')` → 'YYYY.MM.DD' shaklida |
| Shtrixkod misoli (`labels_ru`) | `left(trim(project.name)+' ', find(trim(project.name)+' ',' ',1)-1) + rspace(right(part.id,4),4,'0') + rspace(right(part.counter,4),4,'0')`; `project.name='1234 Shkaf'`, `part.id=7`, `part.counter=3` → '123400070003' |

## 6. Yetishmayotganlar (❌ va 🟡) — ustuvorlik bo'yicha tartiblangan

Tartib: H (to'siq / kundalik ish) → M → L. Har qatorda: nima qilish (1–3 gap) va tegadigan fayllar.

| № | Ust. | Nima yetishmaydi (ID) | Nima qilish kerak | Tegadigan fayllar |
|---|---|---|---|---|
| 1 | H | **(O) operatsiyasi butunlay** (O-001…O-015) | `OParams`/`OMaterial` modeli, `OPanel` (Параметры + Материалы, Ctrl+V), `o_cost`, talabnoma va mahsulot narxiga ulash, Bazis importi — §3 bo'yicha; testlar bilan ≈ 2–3 kun. | `models.py`, `services/calc.py`, `main.py`, `render.py`, `mes.py`, `plugins/legacy_project.py`, `features/o/OPanel.tsx` (yangi), `opmeta.tsx`, `OperationsTable.tsx`, `i18n_src.py` |
| 2 | H | **Umumiy ifoda dvigateli yadrosi** (EXP-001…013, 021, 022, 031…033, 040…043) | Tipli (int/double/bool/str/null) o'z parseri; satr literallari, `=`/`<>`/`^`/`xor`/`if()`, nuqtali nomlar; `eval_expr` — yupqa o'ram (R1–R5, R15). XNC testlari o'zgarishsiz o'tishi shart. | `services/expr/*` (yangi), `services/xnc.py` |
| 3 | H | **Satr va format funksiyalari** (EXP-070…084, 091…093) | Reestr + 25 satr funksiyasi + `format` (Java `DecimalFormat` quyi to'plami); birinchi navbatda shtrixkod misolidagi `left/right/rspace/find/trim/crc32`. | `services/expr/functions_str.py`, `format_java.py` |
| 4 | H | **Semantik to'qnashuvlar** (EXP-012, 055, 057) | Trigonometriya birligi, `round`, `%` ishorasi — foydalanuvchi bilan (§7) tasdiqlab, XNC moslik profili va umumiy profilni ajratish. | `services/expr/*`, `services/xnc.py`, `docs/mebelix/J_XNC_SPEC.md` |
| 5 | H | **LB operatsiyasi va parametrlari** (LB-001, 002, 003…010, 011…018, 023, 058) | `Operation.lb`/`LBParams`, A4/rulon, qoldiq va mahsulot manbalari, «tanlangan detallar», jami soni; `LabelSettings` profilini migratsiya bilan `LBParams` ga o'tkazish (LB-A). | `models.py`, `services/labels.py`, `main.py`, `features/lb/*` (yangi), `Print.tsx`, `services/settings.py`, `opmeta.tsx` |
| 6 | H | **Shablon JSON + matn/shtrixkod elementlari + o'zgaruvchilar** (LB-046, 047, 055, 059, 060…068, 071, 080…085) | JSON shablon va SVG render; `text` va `barcode` (QR + Code128) elementlari, 104 o'zgaruvchi (H5 nomlari + GibLab alias), o'rnatilgan shablon = hozirgi QR etiketka (LB-B). #2 va #3 ga bog'liq. | `services/labels.py` → `labels_render.py`, `labels_vars.py` (yangi), `db.py`, `api_extra.py` |
| 7 | H | **GR paneli: arra qalinligi va «Отступ включительно»; hisob ko'rsatkichlari** (GR-004, 005, 008, 009, 010) | Panelga ikki maydon, hisoblangan «Длина пазования / Длина пропила / Стоимость» (faqat o'qish) va «Сохранить по умолчанию» (`gr_defaults`) qo'shish. | `features/el/GrPanel.tsx`, `services/settings.py`, `api/types.ts`, `i18n_src.py` |
| 8 | H | **Ifoda kiritish maydoni va tekshiruv API** (DEV-015, EXP-110, 111) | `expression` turidagi maydon: sintaksis tekshiruvi, funksiya/o'zgaruvchi ro'yxati, namuna qiymat; `POST /api/expr/check`, `GET /api/expr/functions`. | `shared/ui.tsx`, `api_extra.py`, `services/expr/*` |
| 9 | M | **GR standart qiymatlari, «Детали» jadvali, chop bo'limi** (GR-002, 003, 012, 014, 015) | Standart 8/10 yoki 10/16 ekanini aniqlab bir xillashtirish; «Детали» yorlig'ida 10 ustunli jadval (`groove_usage.rows`); `Print.tsx` ga GR bo'limi (`gr_params`, `gr_parts`). | `models.py::GRParams`, `GrPanel.tsx`, `Print.tsx` |
| 10 | M | **EL/GR: kontekst yordami va jadval boshqaruvi** (EL-023, EL-026, GR-011) | Har parametr yonida «?» (yordam bo'limi/anchor); detallar jadvalida Ctrl+Space, saralash, Home/↑/↓/End. | `ElPanel.tsx`, `GrPanel.tsx`, `shared/grid/Grid.tsx`, `features/help/Help.tsx`, `hotkeys.ts` |
| 11 | M | **Katalog daraxti va tanlash oynasi** (CAT-003, 007, 009, 010, 013) | «Категории» daraxti + «Материалы» jadvali + rasm; operatsiya turiga qarab ildiz; pogonaj va sirt materiallarini ham operatsiyaga aylantirish (CL/SP uchun tayyor bo'lgach). | `CatalogPicker.tsx`, `main.py` (`/catalog`, `_new_operation`), `db.py` (`image`) |
| 12 | M | **Katalog importi kengaytmasi** (CAT-001, 002, 005, 006, 008) | `.xls` (yoki konvertatsiya yo'riqnomasi), `isfolder`, `image`, `params`, `stock` ustunlari, ildiz kategoriya xaritasi, ro'yxat saralash/ko'rinadigan ustunlar. | `services/importers.py::import_catalog`, `Settings.tsx` |
| 13 | M | **Shablon kutubxonasi / content xizmati** (CAT-014, 015, LB-021, 022, 056, 057) | Etiketka va XNC shablonlari uchun papkali ombor: saqlash, ochish, nomlash, ko'chirish, o'chirish, miniatyura; 3–4 ta o'rnatilgan namuna. | `db.py`, `api_extra.py` (yoki yangi router), `features/lb/Library.tsx`, `features/xnc` |
| 14 | M | **LB: kromka/paz/XNC o'zgaruvchilari va CNC shtrixkodlari** (LB-064, 066, 069, 070, 072, 085) | `edge_*`, `groove_*`, `xnc{1..5}_*`, `surface_*` o'zgaruvchilari; har tomon uchun shtrixkod; shtrixkodni 90° burish. | `labels_vars.py`, `labels_render.py` |
| 15 | M | **LB vizual redaktori** (LB-030…037, 040…054) | SVG kanvas, element palitrasi, xossalar paneli, undo/redo, zoom-to-fit, F4/F9 (LB-C). | `features/lb/Editor.tsx` (yangi) |
| 16 | M | **Deklarativ forma (ParamGrid o'xshashi)** (DEV-001…007, 013, 014) | Sxema bo'yicha forma: guruhlar, `visible/readOnly/suffix` ifodalari, `stroke/fill/image` turlari — LB/XNC xossalar paneli uchun. | `shared/ui.tsx` (`SchemaForm`) |
| 17 | M | **O: tayyor shablonlar va jadval qulayliklari** (O-009, 010, 016) | Ctrl+V parser, qator amallari, transport/o'rnatish/qadoqlash namunalari (1-qadam bilan birga). | `OPanel.tsx`, `importers.py` |
| 18 | M | **Kutubxona: sana-vaqt va qo'shimcha** (EXP-094…099) | `now()` naqshlari ru/uz nomlari, soat in'ektsiyasi (R9). | `services/expr/datefmt.py` |
| 19 | M | **EL: kromka stanogi** (EL-014) | Avval savolga javob (§7); kerak bo'lsa `ELParams.tool` va importda saqlash. | `models.py`, `legacy_project.py` |
| 20 | M | **LB: foydalanuvchi ma'lumotlari jadvali** (LB-019, 020) | `source="user"`: maydonlar sxemasi (nom, tavsif, tur, eni, standart) va qatorlar jadvali, Excel'dan qo'yish. | `features/lb/UserData.tsx`, `LBParams.fields/data` (LB-D) |
| 21 | L | **Matematik va aralash funksiyalar to'ldirish** (EXP-051…054, 058…062, 090, 100…104) | Reestrga qo'shish (har biri ≈ 5 qator); zid misollar jonli tekshiruvga qadar o'tkazib turiladi. | `services/expr/functions_math.py` |
| 22 | L | **Interfeys komponentlari tafsilotlari** (DEV-005, 006, 024, 025, 027, 028) | Fayl o'qish yordamchisi (`text/dataURL/arrayBuffer`), tooltipda yorliq (`HOTKEYS` dan avto), dinamik ikonka. | `shared/ui.tsx`, `hotkeys.ts` |
| 23 | L | **LB mayda tomonlari** (LB-024, 031, 032, 033, 086) | Yordam tugmasi, zoom-to-fit, F4/F9 ma'nosini aniqlash, shtrixkod sig'imi ogohlantirishi. | `features/lb/*` |
| 24 | L | **GR sxema rasmi, (DR) turi, maxsus param turlari** (GR-006, O-017, DEV-017, DEV-018) | Birinchisini o'zimiz chizamiz (W/D/O); qolgani — ma'nosi aniqlangach (§7). | `GrPanel.tsx`, — |

## 7. Aniqlashtirish savollari (foydalanuvchiga)

Har savolning yonida qaysi qaror unga bog'liqligi.

1. **Etiketka printeri va o'lchami** (ochiq savol, CLAUDE.md): termoprinter (qaysi model/til: ZPL, TSPL, ESC/POS yoki oddiy Windows drayveri) yoki A4 listli
   etiketka? Standart o'lcham (58×40, 58×60, 100×40, …)? → LB-A/B ning ustuvorligi, to'g'ridan-to'g'ri printer tili kerakmi.
2. **Hozir xodimlar qaysi etiketka shablonini ishlatadi** va unda qaysi maydonlar bor (skrinshot yoki namuna)? Korxonaning o'z `.lbl`
   fayllarini bizning JSON shablonga o'tkazadigan **importyor** yozishga ruxsat bormi (`.project` importiga o'xshash)? → LB-D.
3. **O operatsiyasi:** egasi «Проект» bo'lsa, narx mahsulotlarga taqsimlanishi kerakmi (hozir taklif: yo'q, faqat loyiha jamida)? Bazis-Mebelshik
   komplektlari O ga import qilinsinmi? Hisobotda O uchun alohida bo'lim (materiallar jadvali) kerakmi?
4. **`part.counter` ma'nosi:** loyiha bo'yicha ketma-ket etiketka raqami mi yoki detal nusxasining tartib raqami (bizda `i/n`) mi? Shtrixkodda
   nechta raqam kerak? → shtrixkod mazmuni (LB-081) va MES skaneri bilan moslik.
5. **O jadvalida qator «Стоимость»** mahsulot soniga ko'paytirilgan holda ko'rinadimi (yordam «ko'paytiriladi» deydi, qaysi ustun ekani noaniq)?
6. **XNC ifodalarida trigonometriya birligi:** korxona XNC shablonlarida `sin/cos` argumenti gradusmi (bizda hozir shunday) yoki radianmi (yordam shunday)?
   `/` butunlar uchun butunli bo'linishmi? Eski XNC dasturlari uchun moslik profili saqlanadi, ammo yangi LB shablonlarida qaysi biri bo'lsin?
7. **GR standart qiymatlari:** chuqurlik 8 / otstup 10 (spetsifikatsiya va `.project`) yoki 10 / 16 (bizning kod)? «Отступ включительно» korxonada nimani
   anglatadi (otstup paz chetigacha mi yoki o'qigacha)?
8. **Katalog:** asosiy manba MES katalogimi yoki Excel faylmi? `.xls` (eski) kerakmi yoki `.xlsx` yetarlimi? Rasm (Изображение) ustuni va
   daraxt oynasi kerakmi? Pogonaj va sirt materiallari qachon kerak (CL/SP bilan birga)?
9. **EL:** kromka stanogi (tool1) hisobotda yoki postprotsessorda kerakmi? Kromka qalinligi 0 qolsinmi (ochiq savol)?
10. **Tillar va formatlar:** shablonda sana/son lokal (ru: «1,5», «Февраль»; uz: ?) yoki doim invariant (nuqta, raqamli oy) bo'lsinmi? `translit` qaysi
    standart bo'yicha (ruscha kirill; o'zbekcha kirill ham)?
11. **`(DR) Сверление`** operatsiya turi (GibLab tur dialogida bor) — korxonada ishlatiladimi? Bizning XNC bilan qoplanadimi?
12. **Etiketka redaktorida Y o'qi yo'nalishi** (GibLab skrinshotida aniq ko'rinmaydi): yuqoridan pastga (XNC kabi) saqlansinmi? Xodimlar
    eski shablonlardan koordinata ko'chirishadimi?
13. **Yordam misollaridagi zid qiymatlar** (`log(100)=0.5`, `asec(1)=π/2`) — GibLab'da haqiqiy qiymat kerakmi (foydalanuvchi ruxsati bilan jonli tekshiruv)
    yoki matematik to'g'ri variant yetarlimi?
14. **Arra markazi etiketka moduli** (Holzma/SCM `print\part.lbl`): korxona stanogida etiketka chop moduli bormi? Bo'lsa — shu shablon formati uchun postprotsessor
    kerakmi (LB-087)?

## Ilova A. Yordam sahifalaridagi nomuvofiqliklar (qoidalarga ta'sir qiladi)

| Joy | Nomuvofiqlik | Ish yuritish |
|---|---|---|
| `el_ru` — «Стоимость материала» | formula «Количество материала × Количество материала» deb yozilgan (ikkala ko'paytuvchi bir xil) | aslida × Цена материала (B6 va hisob shunday) |
| `gr_ru` — «Детали» | en bo'yicha pazlar ham «ПВ/ПН» deb nomlangan | ПЛ/ПП deb qabul qilindi (bizdagi nomlar) |
| `mathFunctions` — misollar | `log(100.0)=0.5`, `log2(4.0)=0.5`, `asec(1)=π/2`, `coth(4.0)=54.598`, `sign(0)=-0.0`; `floor` va `asin` imzolari boshqa funksiyadan nusxalangan | test-vektorga olinmadi; jonli tekshiruv (§7.13) |
| `stringFunctions` — `lspace/rspace` | tavsif «chapdan/o'ngdan belgilar» deydi, misollar esa aksini ko'rsatadi (`lspace` o'ngdan to'ldiradi) | misollarga ishonildi |
| `lb_ru` | barcha parametrlar tavsifsiz («Раздел заполняется») | G4/H5 va skrinshotlardan to'ldirildi, ❓ belgilandi |
| `formatPattern_ru` | bo'sh sahifa | `ffmt` ga qaralsin |
| `labels_ru` — kromka `etn`, `ebn`… | «по длине/по ширине» deb yozilgan, paz uchun esa «Наименование» | `n` = nom deb qabul qilindi (H5 ham shunday) |
| `goods_ru` — rasm va matn | «Изображение» va «Параметры» ustunlari matnda yo'q, sozlash dialogida bor | dialog skrinshoti (R:cvb6) asosida |

## Ilova B. Standart o'zgaruvchilar (104 ta) va bizdagi nom taklifi

Turlar yordamdagidek (`string`, `integer`, `double`, `boolean`). «Taklif» — H5 jadvalidagi nom; H5 da yo'q bo'lganlari uchun yangi nom (`*`).

| Guruh | GibLab nomlari | Tur | Ma'nosi | Taklif (MebeliX) |
|---|---|---|---|---|
| Loyiha | `project.name`, `.date`, `.description`, `.currency`, `.crc16`, `.crc32` | string | nom, sana, tavsif, valyuta, nomning nazorat yig'indilari | `project_name`, `project_date`, `project_description*`, `project_currency*`, `project_crc16*`, `project_crc32` (+ `project_number` — Заказ ID, GibLab'da alohida nom yo'q) |
| Mahsulot | `product.index`, `.name`, `.code`, `.count`, `.description`, `.phone1`, `.phone2`, `.date` | string, `count` — integer | tartib №, nom, kod, soni, tavsif, 2 telefon, sana | `product_index*`, `product_name`, `product_code`, `product_qty`, `product_description*`, `product_phone1/2`, `product_date*` |
| Material | `material.name`, `material.code` | string | material nomi va kodi | `material_name`, `material_code` |
| Detal | `part.id` (integer), `part.code`, `part.counter` (integer) | — | loyihadagi noyob raqam, kod, hisoblagich | `part_uid`, `part_code`, `counter` |
| Umumiy | `good`, `name`, `description`, `index`, `indexInOperation`, `fullName` | string | mahsulot/material, detal nomi, tavsif, tartib №, operatsiyadagi №, to'liq nom | `good*`, `part_name`, `part_description`, `part_index*`, `index_in_operation*`, `full_name*` |
| O'lchamlar | `length`, `width`, `detail.length`, `detail.width`, `thick` | double | zagotovka (uz/en), tayyor detal (uz/en), qalinlik | `length`, `width`, `detail_length`, `detail_width`, `thickness` (+ bizda `saw_length/width`) |
| Bayroqlar | `waste`, `business`, `txt` | boolean | qoldiq, delovoy qoldiq, tekstura | `waste*`, `business`, `grain` |
| Sonlar | `count`, `totalCount`, `usedCount` | integer | soni; jami (detal × mahsulot); kroyga kirgan | `qty`, `total_qty`, `used_qty` |
| Kromka (yuqori) | `etc`, `etn`, `ets`, `ett`, `etj` | string, string, string, double, double | kod, nom, belgi, qalinlik, prifugovka | `edge_top_code`, `edge_top_name`, `edge_top_symbol`, `edge_top_thickness`, `edge_top_jointing*` |
| Kromka (past) | `ebc`, `ebn`, `ebs`, `ebt`, `ebj` | xuddi shu | xuddi shu | `edge_bottom_*` |
| Kromka (chap) | `elc`, `eln`, `els`, `elt`, `elj` | xuddi shu | xuddi shu | `edge_left_*` |
| Kromka (o'ng) | `erc`, `ern`, `ers`, `ert`, `erj` | xuddi shu | xuddi shu | `edge_right_*` |
| Paz (yuqori, uzunlik) | `grtc`, `grtn`, `grtw`, `grtd`, `grto`, `grtoi`, `grts` | string, string, double, double, double, boolean, boolean | kod, nom, eni, chuqurlik, otstup, otstup-inklyuziv, tomon (lits/orqa) | `groove_top_code*`, `_name*`, `_width*`, `_depth*`, `_offset*`, `_offset_incl*`, `_back*` |
| Paz (past, uzunlik) | `grbc`, `grbn`, `grbw`, `grbd`, `grbo`, `grboi`, `grbs` | xuddi shu | xuddi shu | `groove_bottom_*` |
| Paz (chap, en) | `grlc`, `grln`, `grlw`, `grld`, `grlo`, `grloi`, `grls` | xuddi shu | xuddi shu | `groove_left_*` |
| Paz (o'ng, en) | `grrc`, `grrn`, `grrw`, `grrd`, `grro`, `grroi`, `grrs` | xuddi shu | xuddi shu | `groove_right_*` |
| Sirt | `surfFront`, `surfBack` | string | lits va orqa sirt | `surface_front*`, `surface_back*` |
| Ishlov belgilari | `groove`, `drill`, `mill` | boolean | paz, parmalash, frezalash (radiuslar) | `groove`, `drill`, `mill` |
| XNC (5 tagacha) | `XNC1…5`, `xncSide1…5`, `xncBSD1…5` | string, boolean, boolean | CNC dastur kodi, tomon, «по размеру детали» | `xnc1_code*`, `xnc1_side*`, `xnc1_by_size*` … `xnc5_*` |

Jami: 6 + 8 + 2 + 3 + 6 + 5 + 3 + 3 + 20 + 28 + 2 + 3 + 15 = **104**.

## Ilova C. Bu hujjatda qamrab olinmaganlar

`help/format_ru.html`, `xnceditor_ru.html`, `libraryXNC_ru.html`, `remainders_ru.html`, `cs_ru`, `cl_ru`, `cle_ru`, `cse_ru`, `question/`,
`help_ru.html`, `update_ru.html` — topshiriqda yo'q (boshqa inventar fayllariga tegishli). Eslatma: etiketka redaktori XNC redaktori bilan
umumiy ko'rinadi (`R:lb3`: bir xil buyruq palitrasi) — LB-053/054 ni `xnceditor_ru` inventari bilan birga rejalash maqsadga muvofiq.
`.lbl` namuna fayllari va `labels` papkasi ochilmadi.
