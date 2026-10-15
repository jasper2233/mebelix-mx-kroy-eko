# 05. Import, buyurtma moduli, GibSaw, katalog/Dropbox, yangilanishlar va Online ↔ Local farqlari

> Funksiyalar inventari: GibLab (GibLabLocal yordam sahifalari) ↔ MebeliX Kroy. Sana: 2026-10-02. Manba: `C:\GibLabLocal\pages\` yordam HTML sahifalari va ulardagi skrinshotlar (faqat funksional ma'noni tushunish uchun; matn va rasmlar ko'chirilmadi, hammasi o'z so'zlarim bilan). Dastur fayllari, kalit/litsenziya, GUI, internet — ishlatilmadi. Bizning kod o'zgartirilmadi.

**Belgilar.** ✅ bor · 🟡 qisman · ❌ yo'q · ❓ noma'lum/aniqlanmagan · **MES-jamoasiga** — foydalanuvchi MES (va GibSaw sex ekrani) ni o'z dasturchilari yozishini aytgan · n/a — bizning modelga tegishli emas. Murakkablik: S (≤1 kun) / M (2–5 kun) / L (>1 hafta). Ustuvorlik: **H** — xodimlarning kundalik ishiga yoki MES oqimiga tegadi; **M** — foydali, kamroq; **L** — korxonada ishlatilmaydi yoki ma'lumot yetarli emas.

## 1. Qisqa xulosa

- **Jami 167 ta funksiya/o'zgarish** qayd qilindi (114 ta funksiya + 53 ta yangilanish bandi). Bizda: ✅ 33 · 🟡 42 · ❌ 53 · ❓ 11 · MES-jamoasiga 17 · n/a 11.
- **Import.** GibLab «Импорт из других программ» oynasida 9 format bor (PRO100, SketchUp ABF, Ardis, Woody2, WoodWop MPR, iLENIA, Базис .bir va .obl, BCAD) + alohida Excel + `.project` (Bazis skripti va 3D-Constructor shuni hosil qiladi). Bizda ishlaydigan: `.project` (korxonaning haqiqiy oqimi: 205 loyiha, 232 mahsulot `bm.1.86`) va Excel/CSV (faqat detallar). Qolgan CAD importerlari — yo'q; ularga namuna fayl ham, talab ham yo'q.
- **Real ehtiyoj kichik.** Korpusdagi 205 loyihada operatsiyalar faqat CS, EL, XNC (+3 ta LB) — furnitura (O), pogonaj (CL), sirt (SP), paz (GR) importi hozir amalda kerak emas. Shuning uchun asosiy bo'shliq — **Excel import** (GibLab'da 4 tabli, material/mahsulot bo'yicha avtomatik operatsiya yaratadi; bizda bitta tab, bitta CS, `.xls` o'qilmaydi).
- **Buyurtma moduli** — mijozga mo'ljallangan brauzer formasi (ID + 4 xonali PIN email orqali, 4 holat, narx, varaq/pogonaj kroy kiritish). Holatlar bizda aynan bir xil (0..3); mijoz portali, PIN, logotip — MES jamoasiga.
- **GibSaw** — sex sensorli ekrani (`.gibcut` fayl, etiketka chop + detal/karta «bajarildi»). Bizda `Workshop.tsx` (QR-skaner → karta «kesildi») bor; detal darajasidagi progress yo'q — MES jamoasiga.
- **Online ↔ Local.** Online: hozircha bepul, ID/email/balans, serverdagi loyihalar (Владелец/Состояние), Chrome. Local: USB kalit, oflayn, pullik modullar, «Лицензии». Postprotsessorlar saytda 2023-iyundan obuna; professional foydalanishga Local tavsiya. Dropbox, 1C, «Сервисы», buyurtma moduli qaysi versiyaga tegishli ekani yordamdan aniq emas (❓).
- **Yangilanishlar** (2020–2023) asosan: nesting (CN), postprotsessorlar, etiketka dizayni, XNC o'zgaruvchilari (bizda ✅), seriya kroy parametrlari. Yordamning eng yangi yozuvi 2023-05-17; o'rnatilgan GibLab undan yangiroq bo'lishi mumkin (yordam bunga ko'rsatma bermaydi).
- **Ziddiyat/topilma:** 2021-03 yozuvi «Процент заполнения для кратности» olib tashlanganini aytadi, bizning spetsifikatsiyada u hali bor — jonli GibLab versiyasini aniqlash kerak (6-bo'lim, savol 1).

### O'qish doirasi va cheklovlar

- O'qildi: `import\*` (ru), `order\*` (ru), `site\helpGibsaw_ru`, `site\dropbox`, `site\home/tech/partner`, `site\products\*`, `server\*`, `help\update_ru`, `help\service\*`, `help\question\*`, `browser/post/postprocessor_ru`, `error*`. Qo'shimcha (mavzuga yaqin): `help\goods_ru`, `remainders_ru`, `operations\o_ru` (faqat O), `development\*`, `libraryXNC_ru`, partner sahifalari. Skrinshotlar import/order/goods/GibSaw/dropbox/giblab/site bo'limlaridan ko'rildi.
- O'qilmadi: boshqa agentlar bo'limi (`operations\cs/cl/el/gr/xnc/lb/cse/cle`, `labels_ru`, `format_ru`, `expression\*`), `site\tech\*` (aspiratsiya/jihoz — mavzudan tashqari), `.xsd` va `Example1.project` (HTML emas). Order yordami en/pl/tr/ua nusxalari ru bilan bir xil hajmda — alohida o'qilmadi.
- **Sana talqini.** `update_ru` da yozuv formati aralash: dastlabki uch yozuv KK.OO.YY (17.05.23, 12.05.21, 12.03.21), keyingilari YY.OO.KK (20.10.23, 20.08.03, 20.05.25/1, 20.04.25/1, 20.04.14/1) deb talqin qilindi — shunda tartib kamayib boruvchi xronologik bo'ladi (2023-05 → 2021-05 → 2021-03 → 2020-10 → 2020-08 → 2020-05 → 2020-04). Bu xulosa; ❓.
- Hech narsa jonli GibLab oynasida sinalmadi; «Сервисы» jadvali, «Сохранение отчетов», `.bir`-yo'li, Ardis/iLENIA/Imos/PRO100 ning ichki tafsiloti yordamda yo'q.

## 2. Funksiyalar jadvali

### 2.1. Import — umumiy mexanizm (IMP)

Dalil kodlari: **H:** yordam sahifasi (`pages\` ga nisbatan), **S:** o'sha sahifadagi skrinshot (funksional ma'no), **K:** bizning kod/hujjat. «ikkalasi (x)» — yordamda farq ko'rsatilmagan, xulosa.

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| IMP-001 | «Импорт из других программ» oynasi | Loyiha menyusida format ro'yxati: PRO100 (.sto), SketchUp ABF (.dxf), Ardis (.xml/.R41), Woody2 (.wes/.xml), WoodWop (.mpr), iLENIA (.pd4), Базис (.bir), Базис (.obl), BCAD (.xml). Format → fayl tanlash → profil/parametr oynasi → «Ок». Eski versiyalarda menyuda alohida bandlar bo'lgan (PRO100, БМ xml/obl, Woody2, Imos fxm). | ikkalasi | 🟡 (oyna bor, ishlaydigani faqat .project) | H:import/import_ru; S:SketchUp.abf_ru (ro'yxat), S:Bazis (eski menyu); K:ProjectMenu.tsx `ImportOther`, plugins/__init__.py | M | M |
| IMP-002 | «Импортировать» — .project faylni yuklash | GibLab loyiha fayli (.project, XML) tanlanadi; Bazis skripti va 3D-Constructor shu formatni hosil qiladi. Local: fayl `projects` papkasidan; online: avval bo'sh loyiha yaratiladi, keyin unga import qilinadi. | ikkalasi | ✅ (yangi loyiha sifatida) | H:import/Bazis_ru; K:main.py `/projects/import-file`, plugins/legacy_project.py; mavjud loyihaga qo'shib import yo'q | S | H |
| IMP-003 | Importdan keyingi natija | «Операции» da mahsulot, kromka va har detal uchun XNC (teshik/freza) operatsiyalari paydo bo'ladi; «Параметры» da detaldagi hamma teshiklar ko'rinadi. | ikkalasi | ✅ | H:import/SketchUp.abf_ru; K:legacy_project.py (CS/EL/XNC/GR), Q_QA §5 (210 fayl importi, 0 xato) | S | H |
| IMP-004 | Import profillari (Профиль: +, ✎, ✕) | Har import oynasida nomlangan sozlama to'plamlari (masalan, frontal teshik diametri 15 yoki 32 mm — mijoz yoki furnitura ishlab chiqaruvchi bo'yicha). Faqat belgi qo'yilgan parametr standartni bekor qiladi. | ikkalasi | 🟡 (faqat Excel) | H:import/profile_ru, parametr_ru; K:ExcelImport.tsx (scope `excel_import`) | S | M |
| IMP-005 | Parametrlar jadvali (guruhlar, standartga qaytarish, «Справка») | Guruhlangan jadval; o'ng tugma: guruhni yoyish/yig'ish, hammasini yoyish/yig'ish, tanlanganni yoki hammasini boshlang'ich qiymatga qaytarish. | ikkalasi | ❌ | H:import/importDialog_ru; bizda importer parametr jadvali yo'q | M | L |
| IMP-006 | Import sozlamalarini XML ga eksport / import | Kompaniya o'z import sozlamalarini XML fayl qilib chiqaradi, mijozlari shuni yuklab bir xil sozlamadan foydalanadi. | ikkalasi | 🟡 (umumiy zaxira bor) | H:import/importDialog_ru; K:api_extra.py `/backup/settings` | S | L |
| IMP-007 | «Экспортировать» — .project ga eksport | Loyihani GibLab XML fayli (.project) qilib saqlash; sayt formatni ochiq va hujjatlashtirilgan deydi (hisob dasturlari bilan integratsiya uchun, statistik ma'lumot fayl ichida). Online: brauzer Downloads ga yuklaydi. | ikkalasi | ❌ (qasddan) | H:site/products/service_ru; S:Bazis (eksport); K:ProjectMenu.tsx faqat `.mxk.json`; CLAUDE.md 4-qoida: GibLab formatlari nusxalanmaydi | M | L |

### 2.2. Importerlar — har biri nima olib keladi (IMP)

Korpus (205 `.project`, `tools/bench`) faqat CS (635), EL (377), XNC (9698), LB (3) operatsiyalarini o'z ichiga oladi; `product.import = bm.1.86` — 232 mahsulot. Ya'ni korxona amalda faqat Bazis-skript oqimidan foydalanadi.

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| IMP-010 | Bazis-Mebelshik 8–11: skript «GibLabExport» → .project | Bazis ichida skript ishga tushiriladi, eksport parametrlari tanlanadi, «Экспортировать» → .project; fayl GibLab ga yuklanadi. Cheklov: Bazis 11 (2020-aprel) dan skriptlar faqat texnik qo'llab-quvvatli litsenziyada yoki Bazis-Online da ishlaydi. | ikkalasi | ✅ | H:import/Bazis_ru; K:legacy_project.py, M_STAFF_HABITS §M1, tools/bench korpus | S | H |
| IMP-011 | Bazis: gabarit o'lchamlar (tekstura hisobga olingan), pozitsiya/belgilanish/nom/soni | Detal l×w (+dl/dw, jl/jw rejimlari), tekstura bayrog'i, nom, kod, `part.designation`; skript parametri «Использовать обозначение вместо номера позиций» va «Учитывать Лицевая сторона». | ikkalasi | ✅ | H:import/Bazis_ru (v1.792, v1.84, v1.851); K:legacy_project.py (name/code/description/grain/size_mode) | S | H |
| IMP-012 | Bazis: kromkalash | Detalning 4 tomoni kromka operatsiyasiga bog'lanadi; «кромка без подрезки» va egri kontur bo'yicha tuzatishlar skript tomonida. | ikkalasi | ✅ | H:import/Bazis_ru; K:legacy_project.py (elt/elb/ell/elr → EL) | S | H |
| IMP-013 | Bazis: mahsulotlar bo'yicha guruhlash | Detallar изделие lar bo'yicha; skript parametri «Объединить детали в одно изделие» hammasini bitta mahsulotga yig'adi; parametrik bloklardan detallar (v11). | ikkalasi | ✅ | H:import/Bazis_ru; S:Bazis (skript parametrlari); K:legacy_project.py (`good typeId=product`, Product.extra) | S | H |
| IMP-014 | Bazis: vertikal va gorizontal teshiklar (frontal + 4 yon) | Teshiklar XNC dasturiga: frontal va yon (yuqori/past/chap/o'ng); skript parametrlari: min. qalinlik (masalan 6.1), sквозное teshik chiqishi (2 mm), sквозное uchun asbob nomiga «S» qo'shimchasi. | ikkalasi | ✅ (teshiklar); «S» ma'nosi ❓ | H:import/Bazis_ru (v1.77, 1.78); S:Bazis; K:legacy_project.py `program_to_commands` (bf/bl/br/bt/bb) | S | H |
| IMP-015 | Bazis: kontur frezerovka, paz, «выемка» | Ichki kontur frezasi (kirish nuqtasi burchakdan xavfsiz masofaga ko'chirilgan, v1.84), pazlar (v1.76), выемка (v1.84). | ikkalasi | 🟡 (kontur/yoy/paz ✅; «выемка» ❓) | H:import/Bazis_ru; K:legacy_project.py (MillStart/Line/Arc, Groove; noma'lum teg → ogohlantirish) | S | M |
| IMP-016 | Bazis: komplektuyushchie (furnitura, mahkamlagich) | Eksportda «Комплектующие» Да/Нет; GibLab da `simple` tovarlar va O (Комплектация) operatsiyasi sifatida keladi. | ikkalasi | 🟡 (O importda o'tkazib yuboriladi + ogohlantirish) | H:import/Bazis_ru; K:legacy_project.py (else-shoxcha), ProjectView.tsx (O hali yo'q); korpusda O operatsiya yo'q | M | L |
| IMP-017 | Bazis: profillar («Импортировать профили») | Pogonaj profil detallari (CL operatsiyasiga). | ikkalasi | ❌ | S:Bazis (skript parametri, eski dialog); CL operatsiyasi bizda yo'q; korpusda CL yo'q | M | L |
| IMP-018 | Bazis: eski yo'l — spetsifikatsiya XML (.obl/.bir) | Bazis «Создать чертежи и таблицы → Спецификация → XML»; GibLab «Импорт БМ(xml,obl)» dialogi: Объединить детали, прифуговка = qalinlik kromka, komplektuyushchie, profillar, teshiklar, orqa teshik bo'lsa aylantirish+ko'zgu (gorizontal/vertikal), teshik chiqishi. Ogohlantirish: Bazis burilgan detalning teshik koordinatalarini XML da qayta hisoblamaydi. | ikkalasi | ❌ | H:import/Bazis_ru (oxirgi qator); S:Bazis (1–9-rasmlar); skript yo'li shuni almashtirgan | M | L |
| IMP-019 | Woody2: WES fayl | Woody «Экспорт → Спецификация изделия (*.WES)»: detallar, kromka, komplektuyushchie/mahkamlagich. «Импортировать комплектующие» belgisi; «Объединить детали в одно изделие» o'chiq — har bo'lim alohida mahsulot, yoqiq — bitta. Minimal Woody 2.01.124. | ikkalasi | ❌ | H:import/Woody_ru; S:Woody; korxona Woody ishlatmaydi, namuna fayl yo'q | M | L |
| IMP-020 | Woody2: XML fayl | Detallar + ishlov; «Импорт контурной обработки (XNC)» belgisi. Woody 2.0.3.69 da faqat XML kerak (WES shart emas). Dialogda 3 ta mm-maydon bor (nomi skrinshotda aniq emas). | ikkalasi | ❌ | H:import/Woody_ru; S:Woody (XML dialogi) | M | L |
| IMP-021 | BCAD: «Экспорт данных проекта» XML | BCAD → Приложения → Подготовка производства → Экспорт данных проекта. Ma'lumot turlari: ishlatiladigan materiallar, panellar (+panel teshiklari), profil detallar, mahkamlagich va komplektuyushchie (tipovoy/ixtiyoriy/furnitura); obyektlar: hammasi/ko'rinadigan/belgilangan, sborkani ajratish; XML sxema: yo'q/alohida fayl/havola. | ikkalasi | ❌ | H:import/BCAD (faqat skrinshotlar); namuna fayl yo'q | M | L |
| IMP-022 | 3D-Constructor v7 → .project | 3DC: Сервис → Настройка → Вывод в XML: papka, kengaytma (.xml yoki .project), «выдавленные/столешницы/профили раскрой ga». Keyin Экспорт → Вывод в XML. Boshqaruv dasturlari nomlari fayl ga tushishi uchun avval CAM-modulga eksport qilinadi. Yangilanishlar: «Составное наименование детали», orqa teshik bo'lsa aylantirish+ko'zgu, asbob zenkovka bilan/siz ajratish, paz asbob o'lchami tuzatildi. | ikkalasi | 🟡 (.project o'qiladi; 3DC namunasi sinalmagan) | H:import/3DC, update_ru (2020-05, 2020-04, 2020-10); S:3DC | M | L |
| IMP-023 | SketchUp ABF: DXF import | SketchUp da ABF plagin: detallarga metka (layer), присадка (minifix, shkant, konfirmat, yashik yo'naltirgichi), kromka; 3D DXF eksport (Файл → Экспорт → 3D модель) → GibLab «SketchUp ABF (*.dxf)». DXF dan oldin SketchUp faylini tozalash tavsiya (ishlatilmagan metka/material/komponentlar — «Статистика → Убрать неиспользуемые»). | ikkalasi | ❌ | H:import/SketchUp.abf_ru, SketchUp.clear_ru; K:Q §4 (DXF import ochiq) | L | L |
| IMP-024 | ABF: chuqurlik metka (layer) nomidan | Sukut bo'yicha teshik/paz chuqurligi metka nomidagi «DEPTH:» dan keyingi qiymatdan olinadi (profilda bekor qilish mumkin). | ikkalasi | ❌ | H:import/SketchUp.abf_ru | S | L |
| IMP-025 | ABF import parametrlari (kodirovka, operatsiya turi, chiqishlar, kontur freza) | «Кодировка символов» (Windows Cyrillic va b.); «Создавать детали для операции» (нестинговый yoki листовой); sквозное teshik va sквозная frezerovka pastga chiqishi (skol oldini olish); kontur frezasi diametri va asbob nomi. | ikkalasi | ❌ | H:import/parametr_ru, SketchUp.abf_ru; S:profile (dialog) | M | L |
| IMP-026 | ABF: teshik/paz turlari bo'yicha sozlash | Frontal: minifixBolts, minifixPlasticBase, screwInside, hingeCub D≤5 (nadsechka 3–5 mm), hingeCub D>5 (chashka ~35 mm); gorizontal: sideDrillDepth; paz: Intersect. Har biri uchun asbob nomi, diametr (5 → 4.5), chuqurlik; paz uchun arra qalinligi. | ikkalasi | ❌ | H:import/SketchUp.abf_ru; S:profil dialogi | M | L |
| IMP-027 | PRO100 (.sto) | Konstruktor dasturidan spetsifikatsiya (kromka, teshik, freza, komplektuyushchie). Yordam sahifasi yo'q; narxnomada pullik modul. | ikkalasi (local narxnoma) | ❌ | H:site/products/_price_ru (1.4), serial_ru; S:Bazis (eski menyu) | M | L |
| IMP-028 | Ardis (.xml, .R41) · iLENIA (.pd4) · Imos (.fxm) | Formatlar ro'yxatda/eski menyuda bor, yordam va skrinshot yo'q — nima olib kelishi noma'lum. | ikkalasi | ❌ | S:SketchUp.abf_ru (ro'yxat), S:Bazis (Imos); batafsil ❓ | M | L |
| IMP-029 | WoodWop MPR (.mpr) — detal ishlovi | CNC dasturidan detal ishlovini olish; 2020-avg «MPR import kamchiliklari tuzatildi», 2020-may «@ belgili nisbiy koordinatalar to'g'ri ko'chiriladi». | ikkalasi | ❌ | H:help/update_ru; S:SketchUp.abf_ru (ro'yxat) | L | L |
| IMP-030 | Sayt da'volari: AutoCAD DXF va VBA makros orqali import | Sayt «Импорт из …» ro'yxatida MS Excel, OpenOffice (nusxa/qo'yish), 3D-Constructor/PRO100, WOODY2, Базис, AutoCAD DXF, Makros VBA sanalgan; DXF/VBA tafsiloti yo'q. | ❓ | ❌ | S:site/about_ru (rasm); H:products/serial_ru | — | L |
| IMP-031 | GibDraw — AutoCAD uchun XNC tayyorlash moduli | Sayt: CNC dasturlar tayyorlashda ixtisoslashgan AutoCAD moduli. Alohida mahsulot; yordami yo'q. | ❓ | n/a | H:products/serial_ru | — | — |

### 2.3. Excel import (XLS)

GibLab «Импорт из Excel» — alohida tugma (Проект menyusi). Bizda: `ExcelImport.tsx` + `services/importers.py`.

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| XLS-001 | Oyna tuzilmasi: 4 tab (Детали, Простые операции, Материалы, Изделия) | Bir faylda bir necha varaq; har tabda o'z varag'i (nomi bilan), boshlang'ich va oxirgi qator. Hammasi bir bosishda import qilinadi. | ikkalasi (x) | 🟡 (faqat «Детали» ekvivalenti) | H:import/Excel; S:Excel; K:ExcelImport.tsx (bitta varaq, faqat boshlang'ich qator) | M | H |
| XLS-002 | Detallar: «Группировка → По изделиям» | Ustun qiymati bo'yicha mahsulotlar (Изделия) avtomatik yaratiladi (misolda «Описание» ustuni = mahsulot nomi). | ikkalasi (x) | ❌ | S:Excel (4–6-rasmlar) | M | H |
| XLS-003 | Detallar: «Группировка → По материалам» | Ustun (misolda A «Материал») bo'yicha har material uchun alohida CS operatsiya yaratiladi; kromka nomlari bo'yicha EL operatsiyalar avtomatik yaratiladi. | ikkalasi (x) | 🟡 (EL avto ✅; material bo'yicha CS ❌) | S:Excel; K:importers.py `_new_edge` (EL), import tanlangan bitta CS ga qo'shadi | M | H |
| XLS-004 | O'lcham rejimi («По размеру»: заготовки / детали / заготовки после прифуговки) | Fayldagi Длина/Ширина qaysi o'lcham ekani import vaqtida tanlanadi. | ikkalasi (x) | 🟡 (loyiha rejimi ishlatiladi) | S:Excel; K:Project.size_mode, sizes.py | S | M |
| XLS-005 | Majburiy ustun qoidalari | Длина va Количество bo'sh/son emas bo'lsa — detal qo'shilmaydi; Ширина bo'sh/son emas bo'lsa — detal погонажный раскрой (CL) ga tushadi. | ikkalasi (x) | 🟡 (qator tashlanadi + hisobot; CL yo'q) | S:Excel (izohlar); K:importers.py `skipped` | S | L |
| XLS-006 | «Не добавлять деталь, если количество равно нулю» | Belgi: soni 0 qatorlar import qilinmaydi. | ikkalasi (x) | ❌ (soni 0 detal qo'shiladi) | S:Excel; K:importers.py `parse_qty` (0 ruxsat) | S | M |
| XLS-007 | Qo'shimcha ustunlar: Текстура, Наименование, «Поместить номер в наименование», Описание | Tekstura va nom ustuni; qator raqamini nomga qo'yish; tavsif ustuni. | ikkalasi (x) | 🟡 (tekstura/nom ✅; raqam-nomga va tavsif ❌) | S:Excel; K:ExcelImport.tsx FIELDS (description yo'q) | S | M |
| XLS-008 | Kromka ustunlari: Сверху/Снизу (по длине), Слева/Справа (по ширине) | 4 tomon uchun ustun; kromka nomi/belgisi bo'yicha EL ga bog'lanadi. | ikkalasi (x) | ✅ | S:Excel; K:importers.py (edge_top… + noma'lum nom → yangi EL) | S | H |
| XLS-009 | Qo'shimcha guruhlar: (SP) Обработка поверхности, (GR) Пазование, (XNC) Обработка 1/2 | Ustunlar orqali detalga sirt ishlovi, paz va XNC dastur kodlari bog'lanadi (yig'iladigan bloklar). | ikkalasi (x) | ❌ | S:Excel (o'ng panel) | M | L |
| XLS-010 | Excel import profillari | Nomlangan to'plam (+, ✎, ✕): varaq, qatorlar, ustun xaritasi — keyingi importda qayta ishlatiladi. | ikkalasi (x) | ✅ | H:import/Excel; S:Excel (9, 10-rasm); K:ExcelImport.tsx (`/settings/excel_import`) | S | M |
| XLS-011 | «Изделия» tabi | Alohida varaq: bog'lash (по коду / по наименованию), Код, Наименование, Количество, «не добавлять, agar 0», Описание, Телефон 1, Телефон 2, Дата, «Добавлять пустые изделия». | ikkalasi (x) | ❌ (Product maydonlari bor, import yo'q) | S:Excel (7-rasm); K:models.py Product (order_info, ready_date) | M | M |
| XLS-012 | «Материалы» tabi | Materiallar varag'i; ustunlari yordamda ko'rsatilmagan (xulosa: kod, nom, o'lcham, narx). | ikkalasi (x) | ❌ | H:import/Excel (nomi); tarkibi ❓ | M | L |
| XLS-013 | «Простые операции» tabi | (O) Простая / Комплектация operatsiyalarini varaqdan yaratadi (xulosa). | ikkalasi (x) | ❌ (O yo'q) | H:import/Excel; K:ProjectView.tsx (`IMPLEMENTED` = CS/EL/GR/XNC) | M | L |
| XLS-014 | «Faqat mahsulot sonini o'zgartirish» rejimi | Mavjud loyihada Excel dan faqat mahsulotlar sonini yangilash (2021-05). Bir xil buyurtma, boshqa soni uchun qulay. | ikkalasi | ❌ (D2 da rejalashtirilgan, qilinmagan) | H:help/update_ru (2021-05-12); K:D_UI_SPEC §D2 | S | M |
| XLS-015 | Fayl formatlari: .xls (Compatibility mode, goods.xls) | GibLab skrinshotlarida ishlatiladigan fayllar «Режим совместимости» (.xls). Bizda .xlsx/.xlsm/.csv. | ikkalasi (x) | ❌ (.xls o'qilmaydi) | S:Excel (1, 5-rasm); K:importers.py (`openpyxl`), ExcelImport.tsx `accept` | S | H |
| XLS-016 | Ctrl+V: Excel/OpenOffice dan detallar jadvaliga qo'yish | Ustun tartibi Д-на, Ш-на, Кол, Ткт, ОВ, ОН, ОЛ, ОП, Наименование; noma'lum kromka nomi yangi EL operatsiya bo'ladi. | ikkalasi | ✅ | H:order/help_ru; K:CsParts.tsx `onPaste`, D_UI_SPEC §D6 | S | H |
| XLS-017 | Ctrl+V: «Материалы» jadvaliga (O operatsiya) | Ustunlar Код, Наименование, Ед.И, Кол, Цена. | ikkalasi | ❌ (O yo'q) | H:help/operations/o_ru | S | L |

### 2.4. Buyurtma moduli (ORD)

Buyurtma moduli — brauzerdagi mijoz-forma (xizmat ko'rsatuvchi logotipi bilan), mijozlar o'z buyurtmasini kiritadi. Online yoki server rejimida ishlashi xulosa (❓). Foydalanuvchi MES ni o'z dasturchilari yozishini aytgan → mijoz portali MES jamoasiga.

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| ORD-001 | Mijoz: yangi buyurtma formasi | Ro'yxatsiz: F.I.Sh.*, Email*, Telefon 1*, Telefon 2 → «Создать». Email noto'g'ri bo'lsa buyurtma yaratilmaydi; telefon noto'g'ri bo'lsa ijrochi bog'lana olmaydi. | online (xulosa) | MES-jamoasiga (bizda: `POST /mes/orders`) | H:order/help_ru; S:order (newOrder); K:api_extra.py `mes_order`, I_MES §I3 | M | M |
| ORD-002 | ID va 4 xonali PIN-kod | Email ga PIN yuboriladi; PIN kiritilgach buyurtma yaratiladi (ID + PIN yozib qo'yilishi kerak); keyin «Открыть» ID+PIN bilan. | online (xulosa) | MES-jamoasiga | H:order/help_ru; S:order (newOrder1/2, openOrderMenu) | M | M |
| ORD-003 | Buyurtma pastki menyusi (ID, PIN, holat, tayyorlik, narx, tavsif) | Chap panelda: ID/PIN, holat, Дата готовности, «Заказать», narx (Ст. м-ла, Ст. оп-й, Всего), erkin tavsif. | online (xulosa) | 🟡 (holat+ID+narx bor; PIN/tavsif-panel yo'q) | H:order/help_ru; S:order (work1); K:ProjectMenu.tsx `side-order` | S | M |
| ORD-004 | Buyurtma holatlari | Не заказан → Заказан (xizmat ko'rsatuvchiga tekshiruv va baho uchun; menejer bog'lanadi) → Утвержден (qabul qilindi, tayyorlik sanasi qo'yildi) → Готов (tayyor mahsulot omboridan olish mumkin). | ikkalasi | ✅ | H:order/help_ru; K:models.py OrderStatus 0..3, I_MES §I3 (+webhook `project.status`) | S | H |
| ORD-005 | «Заказать» tugmasi | Holatni «Заказан» ga o'tkazadi va buyurtmani ijrochiga yuboradi. | ikkalasi | 🟡 (holat select orqali; ijrochi/tasdiq oynasi yo'q) | H:order/help_ru; K:ProjectMenu.tsx; D_UI_SPEC §D2 (ijrochi modali ochiq) | S | M |
| ORD-006 | Tayyorlik sanasi — «Утвержден» da belgilanadi | Sana ijrochi buyurtmani tasdiqlaganda o'rnatiladi, mijoz ko'radi. | ikkalasi | 🟡 (ready_date qo'lda) | H:order/help_ru; K:models.py Project.ready_date | S | M |
| ORD-007 | Xizmat ko'rsatuvchi logotipi + sayt havolasi (white-label) | Oynada ijrochi logotipi; bosilsa uning saytiga o'tadi. | online (xulosa) | MES-jamoasiga | H:order/help_ru | S | L |
| ORD-008 | Varaq kroy qo'shish — material katalogidan | Bo'sh buyurtmada «Добавить листовой раскрой»; katalogdan bo'lim (tepada) va pozitsiya (pastda) tanlanadi, ikki marta bosish = tanlash. | online (xulosa) | 🟡 (tekis katalog oynasi) | H:order/help_ru; S:order (work2); K:CatalogPicker.tsx | S | M |
| ORD-009 | Pogonaj kroy qo'shish | «Добавить погонажный раскрой» — CL operatsiyasi. | online (xulosa) | ❌ (CL yo'q) | H:order/help_ru | M | L |
| ORD-010 | Kroy sarlavhasi | Material nomi, list formati va qalinligi, material narxi/miqdori, operatsiya narxi; sarlavha bosilsa material almashadi. | online (xulosa) | 🟡 | H:order/help_ru; S:order (work3); K:CsPanel.tsx | S | L |
| ORD-011 | Detallar jadvali va tezkor kiritish | Д-на, Ш-на, Кол, Ткт (Space), ОВ/ОН/ОЛ/ОП (Ctrl+Space — kromkani almashtirish), Наименование; qator qo'shish/o'chirish/ko'chirish yorliqlari; kiritish rejimi (по размеру). | ikkalasi | ✅ | H:order/help_ru; K:CsParts.tsx, E_HOTKEYS.md | S | H |
| ORD-012 | Pastki panel tablari: Кромка · Пазование · Деталь · Раскрой + narx hisobi | Kromka va paz parametrlari, detal xossalari, kroy natijasi; narx: material narxi/miqdori/kromka uzunligi/ish narxi/jami. | online (xulosa) | ✅ | S:order (work3); K:CsPanel.tsx, ElPanel.tsx, GrPanel.tsx, calc.py | S | M |
| ORD-013 | Xizmat turlari va ko'rsatmalar sahifasi | Qabul qilinadigan xizmatlar: varaq va pogonaj kroy (DSP, DVP…), kromkalash, присадка va frezerovka. Havolalar: присадка/frezerovka video-darsi va «памятка по присадке». | online (xulosa) | MES-jamoasiga (kontent) | H:order/welcome | S | L |
| ORD-014 | Buyurtma ↔ ijrochi loyihalar ro'yxati | Ijrochi tomonda buyurtma loyiha sifatida ro'yxatda (ustunlar: Владелец, Состояние, Стоимость); «Заказать» loyiha menyusida. Mijoz buyurtmasi ijrochi loyihasiga qanday tushishi yordamda yo'q (Dropbox papkalari xulosa). | online ❓ | 🟡 (MES buyurtma → loyiha ✅) | S:Bazis (6, 9-rasm); K:api_extra.py `/mes/orders`, Projects.tsx | M | M |
| ORD-015 | Buyurtma yordami va tillar | Buyurtma yordami 5 tilda (ru, ua, en, pl, tr) — tarjima emas, matn bir xil. | online (xulosa) | n/a | H:order/help_*.html (bir xil hajm) | — | — |

### 2.5. GibSaw — sex sensorli ekrani (GSW)

Foydalanuvchi: «GibSaw» (sex ekrani) MES ichida tayyor → hamma qator MES jamoasiga. «Bizda hozir» — `Workshop.tsx` + `/mes/scan` holati.

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| GSW-001 | GibSaw — maqsad va afzalliklar | GibLab davomi: sensorli ekranda kroy kartalari va detal ishlov chizmalari (присадка, freza, paz); etiketkani detal/qoldiq uchun kartadan yoki detallar jadvalidan chop etish. Afzallik: chop vaqtida detal tayyor deb belgilanadi → karta, so'ng butun kroy tayyor; qog'ozsiz ish; konstruktor va sex uchun umumiy ko'rinish. | local/alohida (USB kalit) | MES-jamoasiga (bizda: QR-skaner → detal/karta, «Kesildi») | H:site/helpGibsaw_ru, products/gibsaw_ru; K:Workshop.tsx, api_extra.py `/mes/scan` | — | — |
| GSW-002 | Ma'lumot uzatish: `.gibcut` fayl (flesh yoki lokal tarmoq) | GibLab: kroy operatsiyasi → «Постпроцессоры» → «Пильный центр под управлением GibCut» → `*.gibcut`; fayl GibSaw `data` papkasiga yoki flesh orqali «Импорт». Doimiy papka sozlamada belgilanadi. | local/alohida | MES-jamoasiga (bizda REST/webhook) | H:site/helpGibsaw_ru; S:gibsaw (postprotsessor ro'yxati) | — | — |
| GSW-003 | «Раскрои» paneli: fayl/papka boshqaruvi | O'chirish, boshqa papkaga ko'chirish, papka qo'shish, nomini o'zgartirish, qidiruv; ustunlar: Листы, Исп. Л, Ост. Л; bajarilgan kroy belgisi. | local/alohida | MES-jamoasiga | H:site/helpGibsaw_ru | — | — |
| GSW-004 | «Список карт кроя» va statistik sarlavha | Karta ro'yxati va bajarilganlik belgisi; sarlavha: Проект, Материал, №, Размер, КК (kartalar), КД (detallar), КО (qoldiqlar), ДР (kesim uzunligi), КР (kesimlar), ПЗ (to'ldirish %), ТП (arra qalinligi), ТД/ТШ (torsovka). | local/alohida | MES-jamoasiga (status satri ko'rsatkichlari bizda ✅) | H:site/helpGibsaw_ru; S:gibsaw (scr31); K:MapView.tsx | — | — |
| GSW-005 | «Карта кроя» paneli: bosib/ushlab turib etiketka chop + «bajarildi» | Detal yoki qoldiq tanlanadi → printer tugmasi (yoki bosib turish) → etiketka chop etiladi, element «bajarildi». Hammasi bajarilsa karta, so'ng butun kroy bajarilgan hisoblanadi. | local/alohida | MES-jamoasiga (bizda faqat karta darajasida `done_count`; detal darajasi yo'q) | H:site/helpGibsaw_ru; K:api_extra.py `/mes/scan/{code}/done` | — | — |
| GSW-006 | «Чертеж детали» paneli | Detal uchun GibLab da sozlangan ishlov chizmalari (teshik, freza, paz), masshtab, etiketka ko'rish/chop. | local/alohida | MES-jamoasiga (bizda `xnc.svg` bor) | H:site/helpGibsaw_ru; S:gibsaw (scr4) | — | — |
| GSW-007 | «Список деталей» paneli | Ustunlar: Длина, Ширина, Нач./Вып./Ост. кол., Ткт, Паз, Св., Фр., Наименование; karta yoki butun kroy bo'yicha. | local/alohida | MES-jamoasiga | H:site/helpGibsaw_ru | — | — |
| GSW-008 | «Поля этикетки» paneli | Kroy/karta/detal/qoldiqning barcha etiketka maydonlari (nom, tur: integer/double/boolean/string, qiymat) — etiketka shablonini sozlash va nazorat uchun. | local/alohida | MES-jamoasiga | H:site/helpGibsaw_ru; S:gibsaw (scr81) | — | — |
| GSW-009 | «Настройки» paneli | Parol bilan himoyalangan: til; kalit raqami va litsenziya; etiketka shabloni, o'lchami, yo'nalishi; interfeys (o'ng tugmalar, ikki marta bosish emulyatsiyasi vaqti); ma'lumot papkasi; karta ko'rinishi (mahsulot raqami, detal nomi, kromka belgisi, XNC, shriftlar, ustun soni, polosa o'lchamlari, ranglar). | local/alohida | MES-jamoasiga | H:site/helpGibsaw_ru; S:gibsaw (scr61) | — | — |
| GSW-010 | Jarayonni tiklash («Очистить процесс выполнения») | Kroyning dastlabki holatiga qaytarish: barcha «bajarildi» belgilari o'chadi. | local/alohida | MES-jamoasiga | H:site/helpGibsaw_ru | — | — |
| GSW-011 | Oflayn/portable ish va qurilma talablari | O'rnatishsiz arxiv (diskning ildizida, avtoyuklashga qo'yiladi); sensorli monitor ≥17", 1024×768; kompyuter Core 2 Duo/1 GB; Windows XP/7/8/Linux; etiketka printeri: USB, termo/termotransfer, ekranlangan kabel, yopiq korpus, kuchsiz yelimli etiketka. | local/alohida | MES-jamoasiga (printer savoli ochiq) | H:site/helpGibsaw_ru, products/gibsaw_ru; K:CLAUDE.md ochiq savol 4 | — | — |
| GSW-012 | USB himoya kaliti va demo rejim | Kalitsiz etiketka chop etilmaydi; demo rejimda etiketka printerga emas, ekranga chiqadi. | local/alohida | n/a | H:site/helpGibsaw_ru | — | — |

### 2.6. Katalog, Dropbox, xizmatlar, ombor (CAT)

Korxonada Dropbox katalogi ishlamayapti (token eskirgan, `invalid_access_token`) va xodimlar undan foydalanmaydi (M_STAFF_HABITS §M6).

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| CAT-001 | «Товары» (Каталог товаров) oynasi | Chapda kategoriyalar daraxti, o'ngda rasm, pastda materiallar jadvali (Код, Наименование, Ед., Цена, Склад, Т-на, Д-на, Ш-на), qidiruv, «Обновить», «Настройки». Tanlanganda operatsiyaga kod/nom/narx/qalinlik/list o'lchami yoziladi. Ildiz kategoriyalar: листовой, погонажный, кромка, поверхность. | ikkalasi | 🟡 (tekis jadval + tur filtri; daraxt va rasm yo'q) | H:help/goods_ru; S:goods_ru; K:CatalogPicker.tsx, D_UI_SPEC §D3 (ochiq) | M | H |
| CAT-002 | Katalog manbasi — Excel fayl (goods.xls) | Ustunlar: ID, Родительский ID, Папка (0/1), Код, Наименование, Ед.изм., Цена, Склад, Изображение, Параметры, Толщина, Длина, Ширина. Sozlama: varaq, boshlang'ich qator, saralash, ko'rsatiladigan ustunlar, 4 ta ildiz kategoriya ID si. Fayl `GibLabLocal` papkasida yoki Dropbox da. | local (fayl) / online ❓ | 🟡 (`/catalog/import`: papka belgisi, rasm, parametr, ildiz ID yo'q) | H:help/goods_ru; S:goods_ru (cvb6); K:importers.py `import_catalog`, Settings.tsx `CatalogImport` | S | M |
| CAT-003 | ID / ParentID / IsFolder daraxt modeli | Kategoriya = papka (IsFolder=1), pozitsiya = ID 1001… ParentID bilan; daraxt chuqurligi cheklanmagan (ishlab chiqaruvchi → material → qalinlik → format). | ikkalasi | 🟡 (parent_id, kind=folder bor; UI daraxt yo'q) | H:help/goods_ru; K:db.py CatalogItemRow, main.py `/catalog` | S | M |
| CAT-004 | Katalogni Dropbox da ulashish | goods.xls Dropbox papkasiga qo'yilsa bir necha ish joyida va onlayn buyurtma modulida umumiy tahrirlanadi. | ikkalasi ❓ | MES-jamoasiga (bizda: MES katalogi `POST /catalog/sync`) | H:help/goods_ru; K:I_MES §I1 | — | — |
| CAT-005 | Dropbox ulanishi (access token) | Dropbox da ilova yaratib «Generate» → token «Dropbox access token» maydoniga; Dropbox papkasida loyihalar (misolda papkalar: рабочая, Утвержден) va katalog. | ikkalasi ❓ | ❌ (qasddan: MES SSO/MES katalogi) | H:site/dropbox; S:dropbox, goods_ru; K:D_UI_SPEC §D12 («kerak emas») | M | L |
| CAT-006 | «Сервисы» jadvali (sozlamalar) | Yordamda yo'q. Faqat «service» sahifalari katalog va kontent so'rovlari tuzilmasini beradi → ehtimol tashqi xizmat manzillari jadvali (xulosa). | ❓ | ❓ | H:help/service/*; K:Q_QA §4 (ochiq) | ? | ? |
| CAT-007 | Katalog xizmati: catalogGet / catalogSearch | Parametrlar: id (ota papka; bo'sh = ildiz), typeId (material tanlanayotgan operatsiya turi, masalan CS) — katalog operatsiya turiga qarab filtrlanadi. | ikkalasi ❓ | 🟡 (`GET /catalog?kind&parent_id&q`) | H:help/service/catalog_ru; K:main.py `catalog` | S | M |
| CAT-008 | Kontent xizmati: list / save / load / folder / move / rename / delete | Kontent turlari: project, xnc, label — serverda loyiha, XNC shablon va etiketka shablonlari kutubxonasi papkalar bilan; ro'yxatda oldindan yuklash (preLoad) va ikonka o'lchamlari. | ikkalasi ❓ | 🟡 (loyiha+papka ✅; XNC/etiketka shablon kutubxonasi — sozlama profillari) | H:help/service/content_ru; K:main.py `/folders`, api_extra.py `/settings/{scope}` | M | M |
| CAT-009 | Ombor qoldiqlari — 1C 8 (HTTP): yuklash / hisobot / saqlash | POST so'rovlari: `load` (material kodi bo'yicha qoldiq ro'yxati: id, uzunlik, en, soni, izoh), `report` (tanlangan qoldiqlar haqida hisobot), `save` (yangi qoldiqlar: loyiha ID, 1C ID, list/qoldiq, delovoy, L, W, boshlang'ich/ishlatilgan soni, loyiha nomi va yo'li). Javob 200 = muvaffaqiyat. | local ❓ | MES-jamoasiga (bizda: `/remnants`, `remnants/commit/rollback`, webhook `remnants.saved`) | H:help/remainders_ru; K:I_MES §I2, warehouse.py | — | — |
| CAT-010 | Ombor qoldiqlari — 1C 7 (fayl almashinuv) | GibLab `.request`/`.output` fayl yozadi; 1C `.response` yaratadi/ `.output` ni o'chiradi. | local | n/a (eskirgan; MES REST bilan almashtiriladi) | H:help/remainders_ru | — | — |
| CAT-011 | Qoldiqning ombor ID si loyiha faylida (`dbId`) | Kroyda ishlatiladigan qoldiq ID si XML da `dbId` atributiga yoziladi. | ikkalasi | ✅ | H:help/remainders_ru; K:models.py StockSheet.source_remnant_id, G_IMPORT §G3 | S | H |
| CAT-012 | «Библиотека обработок» (tayyor frezerovka arxivlari) | Yuklab olinadigan arxivlar: tipik frezerovkalar, MDF fasad frezerovkalari, eshik nakladkalari frezerovkalari (XNC shablonlar). | ikkalasi | ❌ | H:help/libraryXNC_ru, help/update_ru (2020-04) | M | L |
| CAT-013 | UI-ta'rif hujjatlari (ParamGrid, ToolBar, button) | Parametr formalari: guruh/parametr, 19 tur (string, integer, double, boolean, timestamp, object, control, password, image, expression, stroke, fill, color, file, folder, alphabet, numeration, widget), visible/readOnly ifodalar; tugmalar fayl o'qish turlari bilan. «Свойства → Программа» parametrik mahsulot formalari uchun. | ikkalasi ❓ | ❌ | H:help/development/*; K:D_UI_SPEC §D4 (3-bosqich) | L | L |

### 2.7. Online, Local, hisob va litsenziya (OL)

Bu bo'lim 4-bo'limdagi taqqoslash jadvaliga asos. «n/a» — bizning model (o'z serveringiz + MES SSO) uchun qo'llanmaydi.

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| OL-001 | Tarqatish modeli | Online — bulutli veb-xizmat (giblab.com, «Облачный офис»); Local — GibLabLocal: internetsiz, USB himoya kaliti, loyihalar lokal diskda. | ikkalasi | ✅ (o'z serveringizda veb-ilova) | H:site/products/_price_ru, products/cloud_ru; S:Bazis | — | — |
| OL-002 | Narx modeli | Online: hozircha bepul. Local: bir ish joyi narxi + qo'shimcha ish joylari; pullik modullar: varaq kroy optimallashtirish, PRO100 import, pila/CNC postprotsessorlar, GibSaw; bepul: pogonaj optimallashtirish, torets kromkalash, Bazis/Woody2/BCAD import, G-CODE. | ikkalasi | n/a | H:site/products/_price_ru | — | — |
| OL-003 | Postprotsessorlar siyosati | Saytdagi postprotsessorlar — demo; 2023-04-15…06-01 oralig'ida dushanba/seshanba/juma o'chirilgan; 2023-iyundan obuna ($50–70 oyiga har biri). Professional foydalanishga Local + o'z stanogi postprotsessorlari tavsiya; Rossiya va Belarusga sotilmaydi. | online ↔ local | n/a | H:post_ru, postprocessor_ru | — | — |
| OL-004 | Hisob: ID, email, balans, «Выйти», «Статистика» | Online yon panelda foydalanuvchi ID, email, balans (grn); chiqish va statistika bandlari. | online | n/a (MES SSO) | S:Bazis (script6/7 — online ekran); K:auth.py | — | — |
| OL-005 | Ro'yxatdan o'tish va foydalanuvchi xatolari | Saytda «легкая регистрация» → sinab ko'rish; foydalanuvchi ko'rsatilmasa/topilmasa xato sahifalari. | online | n/a (MES SSO) | H:site/products/service_ru, errorUser_ru, errorNotUser_ru | — | — |
| OL-006 | «Лицензии» paneli | Chap menyuda kalit raqami va litsenziyalar; Local da bor, online skrinshotda yo'q. | local | n/a | S:Bazis (script5), serial1 | — | — |
| OL-007 | Loyihalar ro'yxati ustunlari | Online: №, ID, Владелец, Состояние, Дата, Стоимость, Наименование; Local: №, Наименование, Стоимость, Дата, Изменено. | online ↔ local | 🟡 (ID, Владелец, Состояние, Дата, Стоимость bor; «Изменено» yo'q) | S:Bazis (6, 8-rasm); K:Projects.tsx | S | L |
| OL-008 | Papka va loyiha amallari | Обновить, Открыть, Добавить, Добавить папку, Переместить, Переименовать, Копировать, Удалить, Справка. | ikkalasi | ✅ | S:Bazis; K:Projects.tsx (D1) | S | H |
| OL-009 | Loyiha egasi va loyihalar almashinuvi («Обмен проектами (заказами)») | Online ro'yxatda «Владелец» (Мой/boshqa); sayt «loyihalar (buyurtmalar) almashinuvi»ni da'vo qiladi — qanday ulashish yordamda yo'q. | online ❓ | 🟡 (owner maydoni bor; ulashish yo'q, MES SSO) | S:Bazis (6-rasm), S:site/about_ru; K:models.py Project.owner | M | L |
| OL-010 | Bazis importi: ish tartibi farqi | Local: skript chiqishini `projects` papkasiga saqlab, ro'yxatni «Обновить» → «Открыть». Online: yangi loyiha yaratib, unga «Импортировать» orqali yuklash. | online ↔ local | ✅ | H:import/Bazis_ru | — | — |
| OL-011 | Brauzer talabi | Online: Chrome tavsiya (IE/Edge qo'llab-quvvatlanmaydi; Firefox/Opera mos). Local oynasi — «GibLabLocal» (brauzermi yoki o'ramami — yordamda yo'q). | online (+ local ❓) | n/a | H:browser_ru; S:Bazis | — | — |
| OL-012 | Interfeys tillari | Yordam ru, ua, en, pl, tr (lt — ro'yxat) tillarida (bayroqlar kutubxonasi 10 ta). | ikkalasi ❓ | 🟡 (ru/uz) | H:help/*_ua/en/pl/tr/lt; K:frontend i18n | S | L |
| OL-013 | «Что нового» (Обновления) sahifasi | Справка da: sana → o'zgarishlar ro'yxati. | ikkalasi | ❌ (ilova ichida yo'q; `docs/`) | H:help/update_ru, help/help_ru; K:Help.tsx | S | L |
| OL-014 | Yangilanishni yetkazish | Online — server tomonida; Local — yangi versiya (ikonkalar orasida «progUpdate» bor; mexanizm yordamda yo'q). | online ↔ local ❓ | ❓ | S:ui ikonkalar nomlari (xulosa) | ? | ? |
| OL-015 | «Сохранить отчет» / «Сохранение отчетов» | Eski menyuda «Сохранить отчет» bandi bor; yordamda yo'q. Ehtimol hisobotni loyiha ichida/papkada yoki Dropbox da saqlash. | ikkalasi ❓ | ❓ | S:Excel (menyu); K:Q_QA §4 (ochiq) | ? | ? |
| OL-016 | «GibLab Server» va «Облачный офис» sahifalari | Alohida mahsulot sahifalari: faqat logotip/sarlavha yoki «Раздел заполняется» — mazmuni yo'q. | ❓ | ❓ | H:server/home_ru, ad_ru, site/products/cloud_ru, individual_ru; S:server (GibLabServer) | ? | ? |
| OL-017 | Oflayn ishlash | Local — internetsiz; online — internet shart. | ikkalasi | ✅ (lokal server, internet shart emas) | H:_price_ru | — | — |
| OL-018 | Tizim talablari (Local) | Windows XP SP2/Vista/7, Pentium 4, 1 GB RAM, 10 GB disk (eskirgan). | local | n/a | H:site/products/_price_ru | — | — |

### 2.8. Sayt bo'limlari — faqat funksional da'volar (SITE)

Reklama matnlaridan faqat funksional da'volar olindi. «Technologies» (присадка xizmati, Cyflex900PRO, aspiratsiya) va hamkor sahifalari (KDT/Stancomplect, SCM/Doligno, Eskada-M, Borisov) — funksional mazmun yo'q yoki mavzudan tashqari.

| ID | Funksiya | Qanday ishlaydi | Versiya | Bizda | Dalil | Mur. | Ust. |
|---|---|---|---|---|---|---|---|
| SITE-001 | Yechim «Серийное производство»: hujjat tayyorlash | Konstruktor dasturlaridan (Woody2, PRO100, Bazis, 3DC) spetsifikatsiya: kromka, teshik, freza, komplektuyushchie; standart mahsulotlar kutubxonasi + ishlab chiqarish rejasi (mahsulot soni) → umumiy paketli kroy, boshqaruv dasturlari, material sarfi va ish hajmi. | ikkalasi | 🟡 (mahsulot+soni ✅; «standart mahsulotlar kutubxonasi» ❌) | H:site/products/serial_ru; K:Product.qty, mes.py | M | L |
| SITE-002 | Paketli optimal kroy | Plita soni pila markazi paketiga karrali; bir xil detallarni birlashtirish; tor detallarni blokka (umumiy kromkalash, keyin kesish). | ikkalasi | ✅ | H:site/products/serial_ru; K:optimizer.py (Кратность, Большой пакет, Объединение) | — | — |
| SITE-003 | Seriya uchun etiketkalar | Pila markazi bilan sinxron chop (paketlilik hisobida), peel-off printer, shtrixkodda detal ishlov dasturi nomi (CNC skanerlari uchun), kromka tomonlari rasmi, qoldiq etiketkasi, yig'ish sxemasidagi tartib raqami. | ikkalasi | 🟡 (QR, kromka sxemasi ✅; shtrixkodda XNC nomi ❌) | H:site/products/serial_ru; K:labels.py | M | M |
| SITE-004 | Yechim «Производственные услуги» | Buyurtmalar saytda yagona shaklda; sozlanadigan operatsiyalar; hisobotlar (ishlab chiqarish/ombor/mijoz uchun); har stanokka postprotsessor; etiketka shablonini o'zi sozlash (matn, rasm, shtrixkod, ishlov chizmali detal); GibSaw (CNC siz stanoklar uchun). | ikkalasi | 🟡 (print profillari ✅; etiketka dizayneri ❌) | H:site/products/service_ru; K:Print.tsx, labels.py | L | M |
| SITE-005 | Ochiq XML format va hisob dasturlari bilan integratsiya | Barcha ma'lumot XML (.project) da, texnologik statistika fayl ichida → hisob dasturlariga ulash oson. | ikkalasi | ✅ (REST/JSON + webhook) | H:site/products/service_ru; K:I_MES_INTEGRATION.md | — | — |
| SITE-006 | CNC stanok ro'yxati (sayt da'vosi) | Pila: SCM, HOLZMA, BIESSE, GIBEN, KDT, FELDER, NPS400…; ishlov markazlari: SCM, BIESSE, HOMAG, Genesis Evolution. | ikkalasi | 🟡 (nomlar ro'yxati bor, format shablonlari MES/foydalanuvchi namunasiga bog'liq) | S:site/about_ru; K:postprocessors.py | L | M |
| SITE-007 | Video-darslar («Быстрый старт», «XNC Редактор», присадка/frezerovka) | Sayt va yordamda video-dars havolalari. | ikkalasi | ❌ (D13 da rejalashtirilgan) | S:site/posterQuickStart, posterXNCEditor; H:order/welcome | M | L |
| SITE-008 | FAQ: o'lcham kiritish rejimlari | Uch rejim: zagotovka (ko'k), detal kromka bilan (yashil; pil o'lchami +prifugovka −kromka), prifugovkadan keyin kromkasiz (qizil, kursiv). Kromkalangan loyihada rejimni o'zgartirish tavsiya etilmaydi. | ikkalasi | ✅ | H:help/question/detailMode; K:sizes.py, D_UI_SPEC §D6 | — | — |
| SITE-009 | FAQ: pripusk (припуск на обработку заготовки) | Butun kroy bo'yicha parametr («Параметры раскроя») va har detal/tomon uchun; pil o'lchamiga qo'shiladi; kartada punktir chiziq. | ikkalasi | 🟡 (parametr va detal-tomon ✅; kartada punktir ❓) | H:help/question/stock; K:Part.allow_*, CSCutParams.machining_allowance | S | L |
| SITE-010 | Справка tuzilmasi | Bo'limlar: Что нового; katalog sozlash; etiketka sozlash; .project formati; qoldiqlar; importlar; operatsiyalar (O, CL, CS, EL, GR, XNC, LB); FAQ; Библиотека обработок; ParamGrid/ToolBar/button. | ikkalasi | 🟡 (Help.tsx kontekst yordami) | H:help/help_ru; K:Help.tsx, D_UI_SPEC §D13 | M | L |

### 2.9. Bizda GibLab'dan ortiq bo'lgan narsalar (importga tegishli)

- Excel/CSV: cp1251 va UTF-16 CSV, «1 200,5», «2 шт», «1200 мм» kabi sonlar; fayl oldindan ko'rish (A, B, C… ustun harflari) va sarlavhadan avto-moslash; o'tkazib yuborilgan qatorlar hisoboti (`skipped` + sabab), ogohlantirishlar (`warnings`).
- `.project` importi: xavfsiz XML (defusedxml), 100000 chegaralari, yoylar/massivlar/koordinata boshi, noma'lum XNC teglari haqida ogohlantirish, o'tkazib yuborilgan operatsiya turi va nomi ko'rsatiladi.
- MES: buyurtmani qayta yuborish (tasdiqlanmagan bo'lsa yangilanadi, lokal ish saqlanadi), webhooklar (`project.status`, `cutting.done`, `map.done`), QR-skaner (`/mes/scan`), JWT rollar (kroychi/texnolog/ko'ruvchi).

## 3. `update_ru.html` dan funksiyalar xronologiyasi

Yangiroq → eskiroq. Bu GibLab nimani rivojlantirayotganini ko'rsatadi: **nesting (CN)**, ko'proq **postprotsessor/stanok** formatlari, **etiketka dizayni**, XNC o'zgaruvchi/ifoda imkoniyatlari, seriya kroy sifati, import tuzatishlari (3DC, MPR). Sanalar talqini — 1-bo'limdagi eslatmaga qarang. Postprotsessor satrlari formati noma'lum bo'lgani uchun 🟡/❌ (namuna fayl kerak).

### 2023-05-17 (yozuv: «17.05.23 — Текущее»)

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-001 | Nesting (нестинговый раскрой): qoldiqlarni hisobga olish — detalsiz har joyda va detal ichki kesimlarida | ❌ | CN operatsiyasi yo'q (OpType.CN faqat nom) | L | L |
| UPD-002 | Nesting: etiketka o'rnini detalda ishlov yo'q joydan avtomatik topish | ❌ | CN yo'q; etiketka sxemasi qat'iy | M | L |
| UPD-003 | Nesting: kartani qo'lda tahrirlash — tanlanganlarni nuqta/chet bo'yicha «yopishtirib» ko'chirish, burish | ❌ | Listli kroy uchun qo'lda muharrir (`CutEditor`) bor, nesting uchun yo'q | L | L |
| UPD-004 | Nesting: saralash imkoniyati | ❌ | CN yo'q | S | L |
| UPD-005 | Postprotsessorlar: Bavelloni oyna (OptyWay R01), Excitech (E3/E4 GCode — detal va nesting), HolzHer (NCHops .hop), Scheer (ScheerWin + chop moduli), AES Alpha (SS + chop moduli), Panhans (.NCR) | 🟡 | Bizda Scheer va glass GCODE ro'yxatda; qolganlari ro'yxatda yo'q; format shablonlari foydalanuvchi namunasiga bog'liq | M | L |
| UPD-006 | Interfeys yangilandi: «Свойства детали» (takror ro'yxat: etiketka o'rni, qo'lda tahrir, saralash) | ✅ | Detal xossalari oynasi bor (Ctrl+Space / № ni ikki bosish) | — | — |

### 2021-05-12

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-007 | Varaq kroy optimizatsiyasi yaxshilandi (algoritm) | ✅ | Bizning optimizator; korpus bilan solishtirilgan (P_TAQQOSLASH) | — | — |
| UPD-008 | Detallar ro'yxatida «Минус количество» ustuni — ombordagi tayyor detallarni kroydan chiqarish | ✅ | `Part.minus_qty` (МК): kroyga = ОК − МК | — | — |
| UPD-009 | Optimizatsiyada detallarni guruhlash muammolari tuzatildi | ✅ | group_by none/length/width, fuzz-testlar | — | — |
| UPD-010 | Kroy muharririda detallarni guruhlanishini hisobga olib joylash | ❓ | `editor.py` guruh bilan ishlaydi; «guruh bilan joylash» qo'lda ekani sinalmagan | S | L |
| UPD-011 | «Нестинговый раскрой» operatsiyasi qo'shildi | ❌ | CN yo'q | L | L |
| UPD-012 | KDT GCode postprotsessori nesting uchun | ❌ | CN yo'q | M | L |
| UPD-013 | Excel import: mavjud loyihada faqat mahsulot sonini o'zgartirish | ❌ | XLS-014 | S | M |

### 2021-03-12

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-014 | Parametr «Большой пакет для серийного производства» | ✅ | `prefer_big_pack` | — | — |
| UPD-015 | «Процент заполнения для кратности» olib tashlandi — endi avtomatik hisoblanadi | ❓ | Bizda hali `fill_packet` (90 %) bor. Jonli GibLab versiyasi/sanasi noma'lum — 6-bo'lim savol 1 | S | M |
| UPD-016 | Polosalarda detallarni «подрезание» (qirqish) kamaytirildi | ❓ | Optimizator sifati; korpus bilan o'lchanadi | — | — |
| UPD-017 | «Операции», «Изделия», «Детали» panellari (GR/EL/SP, O «Материалы») ustunlarini sozlash va qo'shish | 🟡 | CS detallar uchun ustun sozlamasi (`ColumnSettings`) bor; Операции/Изделия uchun Ctrl+P ochiq (D2) | M | M |
| UPD-018 | Postprotsessor + chop moduli: Shelling (ShellingMCS) | 🟡 | Ro'yxatda `shelling_mcs` bor; format kerak | M | L |
| UPD-019 | Oyna kesish postprotsessori GCODE (NC Studio) | 🟡 | `glass_gcode` ro'yxatda | M | L |
| UPD-020 | KDT/WDX (Trepan) ikki tomonli ishlov: zenkovkali teshikning maks. uzunligi parametri | ❌ | Postprotsessor shabloni (foydalanuvchi formati) | S | L |
| UPD-021 | Yangi loyihaga «уникальный идентификатор» project.uuid parametri | 🟡 | Bizda `Project.id` (12 belgi) va `mes_order_ref`; alohida «uuid» yo'q | S | L |
| UPD-022 | XNC o'zgaruvchilari: allowanceT/B/L/R, etj/ett…ert (kromka prifugovka/qalinlik, 4 tomon), origin.x/y, xncSide, bySizeDetail | ✅ | `xnc.py` / `calc.py` — barchasi bor | — | — |

### 2020-10-23 (yozuv: «20.10.23» — YY.MM.DD deb talqin qilindi)

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-023 | Ishlov markazi postprotsessorlari: «Разворачивать деталь кромкой в …burchak» (afzallik/cheklov) va «uzun tomon gorizontal/vertikal» cheklovi | ❌ | Postprotsessor shablon/sozlama; foydalanuvchi stanogi aniqlangach | M | L |
| UPD-024 | Kroy kartasi chopi: QR-kod va shtrixkodlar | 🟡 | QR bor (`map_qr`); 1D shtrixkod yo'q | S | M |
| UPD-025 | Kroy kartalari miniatyurasi — A4 da 4 yoki 6 ta karta | ❌ | `render.py` da yo'q | S | L |
| UPD-026 | Parametrik freza qadami (chuqurlik va tekislik bo'yicha) tuzatildi | ❓ | XNC freza qadami (`J_XNC_SPEC`) tekshirilmagan | S | L |
| UPD-027 | 3DConstructor importi: zenkovkali va zenkovkasiz asboblarni ajratish | ❌ | 3DC importer yo'q (IMP-022) | S | L |
| UPD-028 | BIMA (ImaWop v6) postprotsessori | ❌ | Ro'yxatda yo'q | M | L |
| UPD-029 | Nanxing postprotsessorlari (CutSawFG, NXCutSaw) | 🟡 | Ro'yxatda bor; format kerak | M | L |
| UPD-030 | Bitta detal yoki qoldiq uchun bir necha etiketka (label.count, etiketka raqami) | 🟡 | Bizda har nusxa uchun bitta etiketka; bir nusxaga bir nechta yo'q | S | L |

### 2020-08-03 (yozuv: «20.08.03»)

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-031 | Frezerovka chizmasi yaxshilandi; to'rtburchak va ellips freza | ✅ | `MillRect`, `MillEllipse`, yoylar chizmada | — | — |
| UPD-032 | Cho'ntak/o'yiq (карман/выемка) frezerovkasi | ❓ | Maxsus buyruq yo'q (`MillRect` yopiq kontur bo'lishi mumkin) | M | M |
| UPD-033 | Chuqurlik bo'yicha pog'onali frezerovka | ❓ | `J_XNC_SPEC` dagi qadam parametrini tekshirish kerak | S | L |
| UPD-034 | XNC shablonida parametriklikni qayta hisoblash | ❌ | «Пересчитать параметричность» ma'nosi noma'lum (Q_QA §2) | M | L |
| UPD-035 | «Общие действия»: bir xil kod va material nomli operatsiyalarni birlashtirish; kromka operatsiyalarini kroy materiallari bo'yicha ajratish | ✅ | `actions/merge-same`, `split-edges` | — | — |
| UPD-036 | MPR va 3DConstructor import kamchiliklari tuzatildi | ❌ | Importerlar yo'q (IMP-022, IMP-029) | M | L |

### 2020-05-25 (yozuv: «20.05.25/1»)

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-037 | KDT/WDX XML postprotsessori: bir xil o'lchamli detallarni birlashtirish (paketli kroyda to'g'ri etiketka) | ❌ | Postprotsessor formati | S | L |
| UPD-038 | Homag CadMatic v4: kesim tartibi sozlamasi (torsovkadan yoki qoldiqdan) | ❌ | Postprotsessor formati | S | L |
| UPD-039 | Etiketka dizayni: detal chizmasida kromkalash, «Изображение» elementiga parametr bilan mazmun, ishlov turlari rasmlari (PrintLabel.exe/GibSaw.exe yangilanishi kerak) | 🟡 | Kromka sxemasi etiketkada bor; dizayner/elementlar yo'q | L | M |
| UPD-040 | 3DConstructor v7 import: «Составное наименование детали», orqa teshik bo'lsa aylantirish+ko'zgu sozlamasi soddalashtirildi | ❌ | IMP-022 | S | L |
| UPD-041 | MPR import: `@` belgili nisbiy koordinatalar | ❌ | IMP-029 | S | L |
| UPD-042 | XNC kodlash ifodalari: xncIndex, xncIndexInPart, xncSide | ✅ | `xnc.py` | — | — |
| UPD-043 | «Листы и остатки» jadvalida ifodali ustunlar | ❌ | Ustunlarda ifoda — D7 da «keyin» | M | L |

### 2020-04-25 (yozuv: «20.04.25/1»)

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-044 | 3DConstructor paz importida asbob o'lchami tuzatildi | ❌ | IMP-022 | S | L |
| UPD-045 | Etiketka va XNC shablon muharrirlaridagi noqulayliklar tuzatildi | ❓ | Bizda alohida muharrirlar yo'q | — | — |
| UPD-046 | Blokka guruhlangan detallar optimizatsiyasi tuzatildi | ✅ | group_by + optimizator testlari | — | — |
| UPD-047 | Справка: «Библиотека обработок» bo'limi | ❌ | CAT-012 | M | L |

### 2020-04-14 (yozuv: «20.04.14/1»)

| ID | Funksiya | Bizda | Izoh | Mur. | Ust. |
|---|---|---|---|---|---|
| UPD-048 | KDT/WDX (Trepan) 3 kallakli markazlar: ikki tomonli ishlov | ❌ | Postprotsessor formati | M | L |
| UPD-049 | Felder Format4 PC7 pila postprotsessori (etiketka tayyorlash bilan) | 🟡 | `felder_format4_pc7` ro'yxatda; format kerak | M | L |
| UPD-050 | XNC postprotsessorlarida cheklovlar | ❌ | Foydalanuvchi stanogi aniqlangach | M | L |
| UPD-051 | «Этикетки»: detal chizmasida kromka belgilari; rasmlarni ifoda orqali ko'rsatish | 🟡 | Kromka sxemasi bor; ifodali rasm yo'q | M | M |
| UPD-052 | Detallar kiritish jadvalida ishlov pripuskini tahrirlash | ✅ | `allow_top…allow_right` ustunlari | — | — |
| UPD-053 | «Торцовка остатков» → «Размер остатков с учетом торцовки» (nom) | ✅ | `remnant_size_incl_trim` | — | — |

## 4. Online ↔ Offline (Local) farqlari

Ishonch: **✔** yordam/skrinshotda aniq · **~** skrinshot yoki bilvosita belgidan xulosa · **❓** aniq emas.

| Mavzu | Online (giblab.com) | Local (GibLabLocal) | Ishonch | Dalil |
|---|---|---|---|---|
| Tarqatish | Bulutli veb-xizmat (giblab.com, «Облачный офис») | GibLabLocal: o'rnatiladigan dastur, USB himoya kaliti | ✔ | H:_price_ru |
| Internet | Shart | Shart emas (loyihalar lokal diskda) | ✔ | H:_price_ru |
| Narx | Hozircha bepul | Ish joyiga narx + qo'shimcha ish joylari; modullar alohida (varaq optimallashtirish, PRO100 import, postprotsessorlar, GibSaw — pullik; pogonaj, torets kromka, Bazis/Woody2/BCAD import, G-CODE — bepul) | ✔ | H:_price_ru |
| Postprotsessorlar | Demo; 2023-iyundan obuna ($50–70/oy har biri); ayrim kunlari o'chirilgan | Kalit bilan sotib olinadi, professional foydalanishga tavsiya | ✔ | H:post_ru |
| Hisob | ID, email, balans (grn) yon panelda; «Выйти»; «Статистика»; saytda ro'yxatdan o'tish | Hisob yo'q; «Лицензии» paneli (kalit/litsenziya) | ✔ (skrinshot) | S:Bazis |
| Loyiha saqlash | Serverda; ro'yxat: №, ID, Владелец, Состояние, Дата, Стоимость, Наименование | Lokal papka `projects` (ixtiyoriy Dropbox); ro'yxat: №, Наименование, Стоимость, Дата, Изменено | ✔ (skrinshot) | S:Bazis |
| Bazis importi | Yangi loyiha yaratib, faylni «Импортировать» | Skript chiqishini `projects` papkasiga saqlab, «Обновить» → «Открыть» | ✔ | H:import/Bazis_ru |
| Buyurtma holati va «Заказать» | Ro'yxatda «Состояние»; loyiha menyusida «Заказать» | Skrinshotlarda ro'yxat/menyuda holat ustuni va «Заказать» ko'rinmaydi | ~ | S:Bazis, serial1 |
| Buyurtma moduli (mijoz veb-formasi) | Brauzer moduli, ID + PIN, ijrochi logotipi | Dropbox papkalari orqali bir nechta ish joyiga ulanishi mumkin (xulosa) | ❓ | H:order/help_ru, help/goods_ru |
| Dropbox | «Личный кабинет» Dropbox tokeniga ulanadi | Lokal `projects\Dropbox` papkasi (skrinshot); token maydoni sozlamada | ❓ (ikkalasida ham bo'lishi mumkin) | H:site/dropbox; S:dropbox |
| Katalog (goods.xls) | Server/Dropbox ❓ | Fayl `GibLabLocal` papkasida yoki Dropbox da | ❓ | H:help/goods_ru |
| 1C bilan ombor almashinuvi | ❓ | HTTP (1C 8) va fayl (1C 7); fayl yo'llari lokal (`C:\GibLabLocal\projects\…`) | ~ | H:help/remainders_ru |
| GibSaw | Postprotsessor «GibCut» onlayn ro'yxatda bo'lishi ❓ | Postprotsessor skrinshoti Local dan (`.gibcut`); GibSaw alohida, USB kalit | ~ | H:site/helpGibsaw_ru; S:gibsaw |
| Servislar (catalog/content so'rovlari) | ❓ | ❓ | ❓ | H:help/service/* |
| «Сервисы» jadvali | ❓ | ❓ | ❓ | — |
| Brauzer | Chrome tavsiya; IE/Edge noto'g'ri ishlaydi | ❓ | ✔ (online) | H:browser_ru |
| Tillar | ru/ua/en/pl/tr | ❓ (yordam fayllari bir xil to'plamda) | ~ | H:help/* |
| Yangilanish | Serverda avtomatik (xulosa) | Yangi versiya o'rnatish (mexanizm yordamda yo'q) | ❓ | — |
| Tizim talablari | Brauzer | Windows XP SP2/Vista/7 (eskirgan), 1 GB RAM, 10 GB | ✔ | H:_price_ru |
| Mijoz ro'yxatdan o'tishi | Saytda «легкая регистрация» | Kerak emas (litsenziya kaliti) | ✔ | H:products/service_ru |
| Boshqa foydalanuvchi egaligi | «Владелец» ustuni (Мой/boshqa) | Yagona foydalanuvchi | ~ | S:Bazis |
| «GibLab Server» | — | Alohida mahsulot sahifasi, mazmuni yo'q | ❓ | H:server/home_ru |

**Faqat Online:** hisob (ID/email/balans), «Выйти», «Статистика», saytda ro'yxatdan o'tish, «Владелец» ustuni, Chrome talabi, postprotsessorlarning demo/obuna rejimi. **Faqat Local:** USB kalit va «Лицензии», internetsiz ishlash, lokal `projects` papkasi, narxnoma bo'yicha modul-modul sotib olish, 1C fayl almashinuvi (xulosa). **Ikkalasida:** importlar (Bazis, Excel, ABF…), kroy/operatsiyalar, GibSaw uchun `.gibcut` (xulosa), Справка. **❓:** Dropbox, buyurtma moduli, katalog manbasi, «Сервисы».

## 5. Yetishmayotganlar (🟡 va ❌) — ustuvorlik bo'yicha

### Yuqori (H) — 5 ta

| ID | Funksiya | Bizda | Mur. |
|---|---|---|---|
| XLS-001 | Oyna tuzilmasi: 4 tab (Детали, Простые операции, Материалы, Изделия) | 🟡 (faqat «Детали» ekvivalenti) | M |
| XLS-002 | Detallar: «Группировка → По изделиям» | ❌ | M |
| XLS-003 | Detallar: «Группировка → По материалам» | 🟡 (EL avto ✅; material bo'yicha CS ❌) | M |
| XLS-015 | Fayl formatlari: .xls (Compatibility mode, goods.xls) | ❌ (.xls o'qilmaydi) | S |
| CAT-001 | «Товары» (Каталог товаров) oynasi | 🟡 (tekis jadval + tur filtri; daraxt va rasm yo'q) | M |

### O'rta (M) — 25 ta

| ID | Funksiya | Bizda | Mur. |
|---|---|---|---|
| IMP-001 | «Импорт из других программ» oynasi | 🟡 (oyna bor, ishlaydigani faqat .project) | M |
| IMP-004 | Import profillari (Профиль: +, ✎, ✕) | 🟡 (faqat Excel) | S |
| IMP-015 | Bazis: kontur frezerovka, paz, «выемка» | 🟡 (kontur/yoy/paz ✅; «выемка» ❓) | S |
| XLS-004 | O'lcham rejimi («По размеру»: заготовки / детали / заготовки после прифуговки) | 🟡 (loyiha rejimi ishlatiladi) | S |
| XLS-006 | «Не добавлять деталь, если количество равно нулю» | ❌ (soni 0 detal qo'shiladi) | S |
| XLS-007 | Qo'shimcha ustunlar: Текстура, Наименование, «Поместить номер в наименование», Описание | 🟡 (tekstura/nom ✅; raqam-nomga va tavsif ❌) | S |
| XLS-011 | «Изделия» tabi | ❌ (Product maydonlari bor, import yo'q) | M |
| XLS-014 | «Faqat mahsulot sonini o'zgartirish» rejimi | ❌ (D2 da rejalashtirilgan, qilinmagan) | S |
| ORD-003 | Buyurtma pastki menyusi (ID, PIN, holat, tayyorlik, narx, tavsif) | 🟡 (holat+ID+narx bor; PIN/tavsif-panel yo'q) | S |
| ORD-005 | «Заказать» tugmasi | 🟡 (holat select orqali; ijrochi/tasdiq oynasi yo'q) | S |
| ORD-006 | Tayyorlik sanasi — «Утвержден» da belgilanadi | 🟡 (ready_date qo'lda) | S |
| ORD-008 | Varaq kroy qo'shish — material katalogidan | 🟡 (tekis katalog oynasi) | S |
| ORD-014 | Buyurtma ↔ ijrochi loyihalar ro'yxati | 🟡 (MES buyurtma → loyiha ✅) | M |
| CAT-002 | Katalog manbasi — Excel fayl (goods.xls) | 🟡 (`/catalog/import`: papka belgisi, rasm, parametr, ildiz ID yo'q) | S |
| CAT-003 | ID / ParentID / IsFolder daraxt modeli | 🟡 (parent_id, kind=folder bor; UI daraxt yo'q) | S |
| CAT-007 | Katalog xizmati: catalogGet / catalogSearch | 🟡 (`GET /catalog?kind&parent_id&q`) | S |
| CAT-008 | Kontent xizmati: list / save / load / folder / move / rename / delete | 🟡 (loyiha+papka ✅; XNC/etiketka shablon kutubxonasi — sozlama profillari) | M |
| SITE-003 | Seriya uchun etiketkalar | 🟡 (QR, kromka sxemasi ✅; shtrixkodda XNC nomi ❌) | M |
| SITE-004 | Yechim «Производственные услуги» | 🟡 (print profillari ✅; etiketka dizayneri ❌) | L |
| SITE-006 | CNC stanok ro'yxati (sayt da'vosi) | 🟡 (nomlar ro'yxati bor, format shablonlari MES/foydalanuvchi namunasiga bog'liq) | L |
| UPD-013 | Excel import: mavjud loyihada faqat mahsulot sonini o'zgartirish | ❌ | S |
| UPD-017 | «Операции», «Изделия», «Детали» panellari (GR/EL/SP, O «Материалы») ustunlarini sozlash va qo'shish | 🟡 | M |
| UPD-024 | Kroy kartasi chopi: QR-kod va shtrixkodlar | 🟡 | S |
| UPD-039 | Etiketka dizayni: detal chizmasida kromkalash, «Изображение» elementiga parametr bilan mazmun, ishlov turlari rasmlari (PrintLabel.exe/GibSaw.exe yangilanishi kerak) | 🟡 | L |
| UPD-051 | «Этикетки»: detal chizmasida kromka belgilari; rasmlarni ifoda orqali ko'rsatish | 🟡 | M |

### Past (L) — 65 ta

Ko'pi namuna fayl yoki aniq talab kelgunicha kutadi (postprotsessor satrlari stanok formatiga, importerlar namuna faylga bog'liq):

| ID | Funksiya | Bizda | Mur. |
|---|---|---|---|
| IMP-005 | Parametrlar jadvali (guruhlar, standartga qaytarish, «Справка») | ❌ | M |
| IMP-006 | Import sozlamalarini XML ga eksport / import | 🟡 (umumiy zaxira bor) | S |
| IMP-007 | «Экспортировать» — .project ga eksport | ❌ (qasddan) | M |
| IMP-016 | Bazis: komplektuyushchie (furnitura, mahkamlagich) | 🟡 (O importda o'tkazib yuboriladi + ogohlantirish) | M |
| IMP-017 | Bazis: profillar («Импортировать профили») | ❌ | M |
| IMP-018 | Bazis: eski yo'l — spetsifikatsiya XML (.obl/.bir) | ❌ | M |
| IMP-019 | Woody2: WES fayl | ❌ | M |
| IMP-020 | Woody2: XML fayl | ❌ | M |
| IMP-021 | BCAD: «Экспорт данных проекта» XML | ❌ | M |
| IMP-022 | 3D-Constructor v7 → .project | 🟡 (.project o'qiladi; 3DC namunasi sinalmagan) | M |
| IMP-023 | SketchUp ABF: DXF import | ❌ | L |
| IMP-024 | ABF: chuqurlik metka (layer) nomidan | ❌ | S |
| IMP-025 | ABF import parametrlari (kodirovka, operatsiya turi, chiqishlar, kontur freza) | ❌ | M |
| IMP-026 | ABF: teshik/paz turlari bo'yicha sozlash | ❌ | M |
| IMP-027 | PRO100 (.sto) | ❌ | M |
| IMP-028 | Ardis (.xml, .R41) · iLENIA (.pd4) · Imos (.fxm) | ❌ | M |
| IMP-029 | WoodWop MPR (.mpr) — detal ishlovi | ❌ | L |
| IMP-030 | Sayt da'volari: AutoCAD DXF va VBA makros orqali import | ❌ | — |
| XLS-005 | Majburiy ustun qoidalari | 🟡 (qator tashlanadi + hisobot; CL yo'q) | S |
| XLS-009 | Qo'shimcha guruhlar: (SP) Обработка поверхности, (GR) Пазование, (XNC) Обработка 1/2 | ❌ | M |
| XLS-012 | «Материалы» tabi | ❌ | M |
| XLS-013 | «Простые операции» tabi | ❌ (O yo'q) | M |
| XLS-017 | Ctrl+V: «Материалы» jadvaliga (O operatsiya) | ❌ (O yo'q) | S |
| ORD-009 | Pogonaj kroy qo'shish | ❌ (CL yo'q) | M |
| ORD-010 | Kroy sarlavhasi | 🟡 | S |
| CAT-005 | Dropbox ulanishi (access token) | ❌ (qasddan: MES SSO/MES katalogi) | M |
| CAT-012 | «Библиотека обработок» (tayyor frezerovka arxivlari) | ❌ | M |
| CAT-013 | UI-ta'rif hujjatlari (ParamGrid, ToolBar, button) | ❌ | L |
| OL-007 | Loyihalar ro'yxati ustunlari | 🟡 (ID, Владелец, Состояние, Дата, Стоимость bor; «Изменено» yo'q) | S |
| OL-009 | Loyiha egasi va loyihalar almashinuvi («Обмен проектами (заказами)») | 🟡 (owner maydoni bor; ulashish yo'q, MES SSO) | M |
| OL-012 | Interfeys tillari | 🟡 (ru/uz) | S |
| OL-013 | «Что нового» (Обновления) sahifasi | ❌ (ilova ichida yo'q; `docs/`) | S |
| SITE-001 | Yechim «Серийное производство»: hujjat tayyorlash | 🟡 (mahsulot+soni ✅; «standart mahsulotlar kutubxonasi» ❌) | M |
| SITE-007 | Video-darslar («Быстрый старт», «XNC Редактор», присадка/frezerovka) | ❌ (D13 da rejalashtirilgan) | M |
| SITE-009 | FAQ: pripusk (припуск на обработку заготовки) | 🟡 (parametr va detal-tomon ✅; kartada punktir ❓) | S |
| SITE-010 | Справка tuzilmasi | 🟡 (Help.tsx kontekst yordami) | M |
| UPD-001 | Nesting (нестинговый раскрой): qoldiqlarni hisobga olish — detalsiz har joyda va detal ichki kesimlarida | ❌ | L |
| UPD-002 | Nesting: etiketka o'rnini detalda ishlov yo'q joydan avtomatik topish | ❌ | M |
| UPD-003 | Nesting: kartani qo'lda tahrirlash — tanlanganlarni nuqta/chet bo'yicha «yopishtirib» ko'chirish, burish | ❌ | L |
| UPD-004 | Nesting: saralash imkoniyati | ❌ | S |
| UPD-005 | Postprotsessorlar: Bavelloni oyna (OptyWay R01), Excitech (E3/E4 GCode — detal va nesting), HolzHer (NCHops .hop), Scheer (ScheerWin + chop moduli), AES Alpha (SS + chop moduli), Panhans (.NCR) | 🟡 | M |
| UPD-011 | «Нестинговый раскрой» operatsiyasi qo'shildi | ❌ | L |
| UPD-012 | KDT GCode postprotsessori nesting uchun | ❌ | M |
| UPD-018 | Postprotsessor + chop moduli: Shelling (ShellingMCS) | 🟡 | M |
| UPD-019 | Oyna kesish postprotsessori GCODE (NC Studio) | 🟡 | M |
| UPD-020 | KDT/WDX (Trepan) ikki tomonli ishlov: zenkovkali teshikning maks. uzunligi parametri | ❌ | S |
| UPD-021 | Yangi loyihaga «уникальный идентификатор» project.uuid parametri | 🟡 | S |
| UPD-023 | Ishlov markazi postprotsessorlari: «Разворачивать деталь кромкой в …burchak» (afzallik/cheklov) va «uzun tomon gorizontal/vertikal» cheklovi | ❌ | M |
| UPD-025 | Kroy kartalari miniatyurasi — A4 da 4 yoki 6 ta karta | ❌ | S |
| UPD-027 | 3DConstructor importi: zenkovkali va zenkovkasiz asboblarni ajratish | ❌ | S |
| UPD-028 | BIMA (ImaWop v6) postprotsessori | ❌ | M |
| UPD-029 | Nanxing postprotsessorlari (CutSawFG, NXCutSaw) | 🟡 | M |
| UPD-030 | Bitta detal yoki qoldiq uchun bir necha etiketka (label.count, etiketka raqami) | 🟡 | S |
| UPD-034 | XNC shablonida parametriklikni qayta hisoblash | ❌ | M |
| UPD-036 | MPR va 3DConstructor import kamchiliklari tuzatildi | ❌ | M |
| UPD-037 | KDT/WDX XML postprotsessori: bir xil o'lchamli detallarni birlashtirish (paketli kroyda to'g'ri etiketka) | ❌ | S |
| UPD-038 | Homag CadMatic v4: kesim tartibi sozlamasi (torsovkadan yoki qoldiqdan) | ❌ | S |
| UPD-040 | 3DConstructor v7 import: «Составное наименование детали», orqa teshik bo'lsa aylantirish+ko'zgu sozlamasi soddalashtirildi | ❌ | S |
| UPD-041 | MPR import: `@` belgili nisbiy koordinatalar | ❌ | S |
| UPD-043 | «Листы и остатки» jadvalida ifodali ustunlar | ❌ | M |
| UPD-044 | 3DConstructor paz importida asbob o'lchami tuzatildi | ❌ | S |
| UPD-047 | Справка: «Библиотека обработок» bo'limi | ❌ | M |
| UPD-048 | KDT/WDX (Trepan) 3 kallakli markazlar: ikki tomonli ishlov | ❌ | M |
| UPD-049 | Felder Format4 PC7 pila postprotsessori (etiketka tayyorlash bilan) | 🟡 | M |
| UPD-050 | XNC postprotsessorlarida cheklovlar | ❌ | M |

### Nima qilish kerak — ish paketlari

| Paket | Nima | Tegadigan fayllar | Qamrab oladi | Ust. |
|---|---|---|---|---|
| WP-A. Excel import v2 | Ko'p tabli import: varaq nomi, oxirgi qator, «По размеру», material ustuni bo'yicha CS ni avto yaratish/topish, mahsulot ustuni bo'yicha Product, tavsif va «номер в наименование», «soni 0 qatorlarni qo'shmaslik» belgisi, `.xls` (xlrd yoki aniq xabar), faqat mahsulot soni rejimi, kengaytirilgan profil, «Изделия» tabi (kod/nom bo'yicha bog'lash, telefon/sana/bo'sh mahsulot). Pogonaj/O tablari — CL/O paydo bo'lgach. | `backend/app/services/importers.py`, `backend/app/main.py` (loyiha darajasidagi yangi endpoint; hozirgi `parts/import` saqlanadi), `frontend/src/features/cs/ExcelImport.tsx`, `features/project/ProjectMenu.tsx` (CS siz ham ochilsin), `frontend/scripts/i18n_src.py`, `backend/requirements.txt`, `backend/tests/` | XLS-001…015, UPD-013 | H |
| WP-B. «Товары» daraxt oynasi | Kategoriyalar daraxti + rasm + material jadvali + qidiruv; katalog importida papka belgisi, rasm, parametrlar, ildiz kategoriya ID lari; operatsiya turiga (typeId) qarab filtr. | `frontend/src/features/project/CatalogPicker.tsx`, `features/settings/Settings.tsx` (`Catalog`/`CatalogImport`), `backend/app/main.py` (`/catalog` daraxt), `backend/app/services/importers.py` (`import_catalog`), `backend/app/db.py` | CAT-001…003, 007 | H |
| WP-C. Import plagin infratuzilmasi | Plagin `register()` ga parametr sxemasi va profil; dinamik «Импорт из других программ» oynasi (parametr jadvali, profillar, standartga qaytarish); sozlamalarni eksport/import. Faqat yangi importer qo'shilganda kerak. | `backend/app/plugins/__init__.py`, `backend/app/main.py` (`/import/formats`), `frontend/src/features/project/ProjectMenu.tsx` (`ImportOther`), `api_extra.py` | IMP-001, 004–006 | M |
| WP-D. «Заказать» oqimi | Ijrochi/tasdiq oynasi, holat o'tish qoidalari, «Утвержден» da tayyorlik sanasi, mijoz uchun tavsif; webhook bilan. | `frontend/src/features/project/ProjectMenu.tsx`, `backend/app/main.py` (PATCH loyiha), `backend/app/services/mes.py` | ORD-003, 005, 006 | M |
| WP-E. MES jamoasiga topshirish | Mijoz portali (PIN, ID, forma), kontent sahifalari, GibSaw funksiyalari: detal darajasidagi «bajarildi», etiketka maydonlari, karta ko'rinishi sozlamalari. Bizning REST (`/mes/*`, `/catalog/sync`, `/remnants`) tayyor. | (MES kodi) · bizda `backend/app/api_extra.py`, `services/mes.py`, `frontend/src/features/workshop/Workshop.tsx` | ORD-001…002, 007, 013; GSW-001…011; CAT-004, 009…011 | M |
| WP-F. Etiketka/chop kengaytmalari | Bir detalga bir necha etiketka, 1D shtrixkod (Code128), A4 da 4/6 karta miniatyurasi, shtrixkodda XNC nomi. | `backend/app/services/labels.py`, `render.py`, `models.py` (LabelSettings/PrintSettings), `frontend/src/features/print/Print.tsx` | UPD-024, 025, 030, SITE-003 | M |
| WP-G. O (Комплектация) operatsiyasi | Furnitura jadvali (Код, Наименование, Ед.И, Кол, Цена), egasi — loyiha/mahsulot; Bazis/Excel/Ctrl+V importi. | `backend/app/models.py` (OMaterial), `plugins/legacy_project.py`, `calc.py`, `frontend/src/features/project/ProjectView.tsx` + yangi `features/o/OPanel.tsx` | IMP-016, XLS-013, 017 | L |
| WP-H. Boshqa CAD importerlari | Faqat namuna fayl va talab kelgach: har format uchun alohida `plugins/<nom>.py` (Woody2 WES/XML, BCAD XML, ABF DXF, 3DC, MPR, PRO100…). | `backend/app/plugins/*.py`, `backend/tests/fixtures/` | IMP-017…031 | L |
| WP-I. Nesting (CN) | Faqat LDSP bilan cheklanmaydigan (MDF fasad, qirrali detal) ish bo'lsa; yangi optimizator + muharrir + etiketka o'rni. | `backend/app/services/` (yangi modul), `models.py` (CN), `frontend/src/features/` (yangi) | UPD-001…004, 011, 012 | L |
| WP-J. Kontent | Tayyor frezerovka kutubxonasi (o'zimiz tayyorlaymiz), video-darslar, «Что нового» sahifasi, ilova ichidagi Справка bo'limlari. | `frontend/src/features/help/Help.tsx`, `docs/` | CAT-012, SITE-007, 010, OL-013 | L |

## 6. Aniqlashtirish savollari foydalanuvchiga

1. **GibLab versiyasi.** Hozir qaysi versiya/qaysi sana ishlatiladi («Справка → Что нового» dagi oxirgi sana)? Yordamga ko'ra «Процент заполнения для кратности» 2021-03 da olib tashlangan, bizning spetsifikatsiyada u bor — qaysi biri to'g'ri?
2. **Excel import.** Xodimlar Excel dan nimani va qanday faylda (.xls yoki .xlsx) yuklaydi? Material va mahsulot ustunli fayl shundaymi? Mijoz ismlarisiz 1–2 namuna fayl bera olasizmi? «Faqat mahsulot soni» rejimi kerakmi?
3. **Bazis skripti.** Hozir v1.86 — 1.861 gacha yangilash (qo'sh qo'shtirnoq tuzatishi) kerakmi? Eksportda «Комплектующие» yoqilganmi (korpusda O yo'q)? Bazis 11 uchun texnik qo'llab-quvvatli litsenziya bormi (skript cheklovi)?
4. **Boshqa CAD.** Woody2, BCAD, 3D-Constructor, SketchUp ABF, PRO100, Imos, Ardis, iLENIA, WoodWop MPR dan birortasi rejada bormi? Bo'lsa namuna fayllar kerak.
5. **Dropbox va katalog.** Dropbox to'liq kerak emasmi (MES katalogi)? `goods.xls` bormi? MES katalogi daraxt tuzilmasi (ishlab chiqaruvchi → qalinlik → material) va rasm/narx/ombor qaysi maydonlarda keladi?
6. **«Сервисы» va «Сохранение отчетов».** GibLab Настройки'dagi qaysi bo'lim (skrinshot bering)? Nimani sozlaydi?
7. **Mijoz buyurtma moduli.** Veb-forma (ID+PIN) kerakmi yoki MES portali yetarlimi? Shu band MES jamoasiga topshirilsinmi?
8. **GibSaw/sex.** Planshet va etiketka printeri modeli? Detal darajasida «tayyor» belgisi (har etiketkada) kerakmi yoki karta darajasi yetarlimi? Detal darajasi MES jamoasi vazifasimi?
9. **1C.** Korxonada 1C ombor almashinuvi bormi yoki faqat MES? (MES bo'lsa HTTP/fayl protokoli kerak emas.)
10. **`.project` eksport.** Parallel ishlash/qaytish yo'li uchun kerakmi? CLAUDE.md 4-qoida (GibLab formatlari nusxalanmaydi) bilan ziddiyat — ruxsat bering yoki rad eting.
11. **Nesting (CN).** MDF fasad/shpon kabi nesting talab qiladigan ish bormi? Yo'q bo'lsa UPD-001…004 ni butunlay rad etamiz.
12. **Etiketka/chop.** Bir detalga bir necha etiketka, 1D shtrixkod (CNC skaneri uchun XNC dastur nomi) va A4 da 4/6 karta chopi kerakmi?
13. **Foydalanuvchi/litsenziya modeli.** MES SSO yetarlimi (ID/email/balans tushunchalari kerak emas)? Loyihalarni foydalanuvchilar o'rtasida ulashish (Владелец) kerakmi?
14. **Postprotsessor formatlari.** Qaysi stanok (HolzHer, Panhans, Bavelloni, Excitech, AES Alpha, BIMA, KDT/Trepan, Homag CadMatic) — namuna fayl bilan.
