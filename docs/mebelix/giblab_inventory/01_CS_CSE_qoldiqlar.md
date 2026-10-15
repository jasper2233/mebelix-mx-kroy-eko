# 01. (CS) Листовой раскрой, (CSE) tahrir va qoldiqlar (остатки) — funksiyalar inventari

> Maqsad: GibLab yordamidagi **funksional ma'noni** o'z so'zimiz bilan yozib, MebeliX Kroy bilan solishtirish.
> Manba (faqat yordam sahifalari, funksional ma'no uchun): `operations/cs_ru`, `operations/cse_ru`, `remainders_ru`,
> `question/stock` (припуск), `question/detailMode` (kiritish rejimlari), `question/help_ru`, `goods_ru` va ularning
> rasmlari. Yordam matni ko'chirilmagan; rus atamalari — ekrandagi nomlar bo'lgani uchun saqlangan.
> «Bizda» holati **kodni o'qib** aniqlangan (ilova jonli ishga tushirilmagan); dalil ustunida fayl ko'rsatilgan.
> Belgilar: ✅ to'liq · 🟡 qisman · ❌ yo'q · ❓ aniqlab bo'lmadi. Murakkablik: S ≤ yarim kun, M ≤ 2 kun, L undan ko'p.
> Ustuvorlik — mebel korxonasi uchun (H yuqori / M o'rta / L past). Korxonada narxlar ishlatilmaydi, kroy/kartalar/chop/izoh
> har kuni ishlatiladi (`M_STAFF_HABITS.md`), shuning uchun narx bilan bog'liq bandlar odatda L.

## 1. Qisqa xulosa

1. (CS) — plita materiallarini (LDSP, MDF, DVP, shisha, metall list) gilyotina usulida kesish xaritasini hisoblovchi operatsiya.
2. Oynasi 4 tabdan iborat: **Параметры → Детали → Листы и остатки → Раскрой**; beshinchi bo'lim — **Печать** (alohida chap menyu).
3. Ish oqimi: material va arra parametrlari → detallar (qo'lda yoki Excel/Ctrl+V) → list/qoldiqlar ro'yxati → «Раскроить» → xaritalarni ko'rish/tahrir → chop/postprotsessor.
4. Detal o'lchami kiritish rejimiga (заготовка / деталь с кромкой / после прифуговки) bog'liq; arraga boradigan «пильный» o'lcham = zagotovka + pripusk.
5. Optimizator parametrlari: propil, torsovka (+ minimal otstup), birinchi kesish yo'nalishi, tekstura, murakkab polosa, burilishlar soni, polosa chegaralari, paket/karralik, saralash.
6. Qoldiq (остаток) — kroydan keyin qolgan, ikkala tomoni minimal o'lchamdan katta bo'lak; maydoni yetarli bo'lsa «деловой остаток» va u material sarfiga kirmaydi.
7. Narx: material (list yoki m² bo'yicha) + operatsiya (4 xil asos: kesish uzunligi, detallar perimetri, material yoki detallar maydoni).
8. (CSE) — tayyor xaritani qo'lda tahrirlash: detal/polosa qo'yish, ko'chirish, klonlash, burish, o'chirish, karta qo'shish/o'chirish, undo/redo.
9. Qoldiqlar ombor bilan almashinuvi yordamda 1C (HTTP va fayl) orqali ta'riflangan: yuklash, tanlanganlar hisoboti, saqlash.
10. Bizda (MebeliX Kroy) asosiy oqim, optimizator, qo'lda tahrir va qoldiq ombori bor; bo'shliqlar — chop uslublari, ba'zi tahrir rejimlari, «Объединение деталей», qoldiq «Исп. кол-во», pripusk punktiri.

## 2. Funksiyalar jadvali

### 2.1 Параметры — kroy parametrlari (Параметры раскроя)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CS-001 | Operatsiya oynasi: 4 tab + Печать | CS oynasi Параметры, Детали, Листы и остатки, Раскрой tablaridan iborat; chop alohida bo'lim | tablar tartibi shu | ✅ | `frontend/src/features/cs/CsPanel.tsx`, `features/print/Print.tsx` | S | H |
| CS-002 | Толщина пилы | Arra qalinligi — har ikki kesim orasidagi propil; 0 dan katta bo'lishi shart, aniqlik 0.0001 | bizda std 3 mm | ✅ | `models.py` `CSCutParams.kerf` (0..50; 0 ham ruxsat — Q-13) | S | H |
| CS-003 | Торцовка по длине | List yuqori chetidan torsovka + pastda minimal otstup; qiymat propilni o'z ichiga olmaydi. Foydali en = W − 2·(torsovka + propil); 0 — torsovka yo'q | ≥ 0; bizda std 2 mm | ✅ | `optimizer._zone`, `B_DOMAIN_RULES.md` B3 | S | H |
| CS-004 | Торцовка по ширине | Chap chetdan torsovka + o'ngda minimal otstup. Foydali uzunlik = L − 2·(torsovka + propil); 0 — yo'q | ≥ 0; std 2 mm | ✅ | `optimizer._zone` | S | H |
| CS-005 | Минимальный отступ в конце (снизу / справа) | Pastki va o'ng chetdagi minimal otstupni torsovkadan alohida belgilash (tugma/havola orqali) | belgilanmasa torsovka qiymati | ✅ | `CsParams.tsx` `EndOffsets`, `CSCutParams.end_offset_*` | S | M |
| CS-006 | Начальное направление резов | Birinchi kesishlar yo'nalishi: Любое (optimizator tanlaydi — eng yaxshi natija) / По длине / По ширине | 5 qiymat; std Любое | ✅ | `FirstCutDir`, `optimizer._axes_for` | S | H |
| CS-007 | «По длине / По ширине предпочтительно» | Faqat to'ldirilishi «Процент заполнения для кратности» dan past kartalarda tanlangan yo'nalish majburlanadi (oxirgi qoldiq kerakli tomonda qolishi uchun) | — | ✅ | `optimizer._run_job` (fill < `fill_packet`) | M | M |
| CS-008 | Учет текстуры (material darajasida) | O'chirilsa barcha detallarda Ткт e'tiborga olinmaydi — detal aylantirilishi mumkin (teksturasiz materialga mos) | std ✓ | ✅ | `CSCutParams.use_grain` | S | H |
| CS-009 | Использовать сложные полосы | Oddiy polosa bitta detaldan boshlanadi; murakkab polosa bir necha detaldan boshlanishi mumkin va ko'pincha yaxshi natija beradi | std ✓ | ✅ | `complex_strips`, `optimizer._Cfg.composite` | M | H |
| CS-010 | Максимальное количество вращений | Kesim darajalari (burilishlar) sonini cheklaydi; ko'p bo'lsa optimallik oshadi; ba'zi arra stanoklari 4 gacha ruxsat beradi | bizda 2..6, std 6 | ✅ | `max_rotations`, `validate.py`, `editor.rebuild` | M | H |
| CS-011 | Сортировать полосы | Tayyor kartada polosalar tartibi: kamayish / o'sish / «Узкие в центр» (materialdagi kuchlanishni kamaytiradi) | bizda + «Не сортировать»; std По убыванию | ✅ | `StripSort`, `optimizer._reorder` | S | M |
| CS-012 | Сортировать в полосе | Polosa ichidagi bo'laklar tartibi, xuddi shu variantlar | std Не сортировать | ✅ | `in_strip_sort` | S | M |
| CS-013 | Минимальная ширина полосы | Stanok qisqichlari ushlay oladigan eng tor polosa; optimizator undan tor polosa hosil qilmaydi | 0 = cheklov yo'q | ✅ | `min_strip_width`, `optimizer._best_sheet` | S | M |
| CS-014 | Максимальная ширина полосы | Faqat ekran nusxasida ko'rinadi (matnda tavsif yo'q): polosa enining yuqori chegarasi deb talqin qilingan | 0 = cheksiz | ✅ | `max_strip_width`; `st1.png` | S | L |
| CS-015 | Максимальная длина полосы | Polosa stanokka uzunligi bo'yicha sig'masa, optimizator uni tor tomoni bilan buradi (1-kesish yo'nalishi almashadi) | bizda std 10000 | ✅ | `max_strip_length`, `optimizer._best_sheet` (faqat ikkala yo'nalish ruxsat bo'lsa) | S | M |
| CS-016 | Минимальная обрезка | Stanok chetga juda yupqa kesim (0..5 mm tilim) qilganda detal siljishi/arra qizishi muammosi uchun; yordam uni **propil qalinligidan katta** qo'yishni tavsiya qiladi | bizda std 5 mm | 🟡 | `min_trim_cut`, `validate._check_trim` — ma'nosi tasdiqlanmagan (Q-1) | M | H |
| CS-017 | Высота пакета | Arraning maksimal ko'tarilish balandligi (paket balandligi chegarasi) | bizda std 40 mm | ✅ | `pack_height` | S | M |
| CS-018 | Кратность (faqat o'qish) | Bir kesishda kesiladigan listlar soni = Высота пакета / material qalinligi | 40/16 → 2 | ✅ | `calc.sheets_per_pack`, `CsParams.tsx` | S | M |
| CS-019 | Процент заполнения для кратности | Karta to'ldirilishi shu foizga yetsa/oshsa optimizator listlarni paketga (bir xil kartalar) birlashtirishga harakat qiladi | bizda std 90 % | ✅ | `fill_packet`, `optimizer._run_job` (reps) | M | M |
| CS-020 | Объединение деталей (belgi) | Ekranda bor; yordamda tavsiflanmagan (ehtimol bir xil detallarni birlashtirib kesish) | — | 🟡 | UI'da o'chirilgan «doim yoqilgan» belgi; `merge_parts` faqat saqlanadi/importlanadi, optimizator ishlatmaydi | L | M |
| CS-021 | Группировка деталей по свойствам (havola) | «Объединение деталей» yoqilganda faollashadi; qaysi xossalar bo'yicha guruhlashni tanlash oynasi bo'lsa kerak | — | ❌ | `F_DATA_MODEL_v2.md`da `group_props` yozilgan, lekin `models.py`/UI'da yo'q | M | L |
| CS-022 | Сохранение чертежа карт кроя (belgi) | Xarita chizmalarini loyiha bilan birga saqlash-saqlamaslik | std ✓ | 🟡 | UI'da o'chirilgan «doim yoqilgan» belgi; `save_drawings` ishlatilmaydi | S | L |
| CS-023 | Припуск на обработку заготовки (umumiy) | Hamma detalga perimetr bo'yicha bir xil pripusk; detal xossalarida «пильный» o'lcham shuncha kattalashadi | mm, bizda std 0 | ✅ | `machining_allowance`, `services/sizes.py` | S | M |

### 2.2 Параметры — material, narx, qoldiq (Параметры материала / Стоимость / Остаток)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CS-030 | Толщина (material) | Material qalinligi; karralik hisobi va narx uchun | mm | ✅ | `CSMaterialParams.thickness` | S | H |
| CS-031 | Цена материала | 1 list yoki 1 m² narxi («по листам» belgisiga qarab) | UZS | ✅ | `price`, `calc.material_prices` | S | L |
| CS-032 | Расчет стоимости по листам | ✓ — narx 1 list uchun, ☐ — 1 m² uchun | bizda std ✓ | ✅ | `cost_by_sheets` | S | L |
| CS-033 | Округление «Листы» | Sarflanadigan list sonini yaxlitlash (to'liq listga yoki 1/2, 1/3, 1/4 ulush; en/uzunlik bo'yicha) | ekran nusxasida «К целому» | ✅ | `SheetRounding` (10 kod), `calc._rounded_sheet_count` | S | L |
| CS-034 | Расчетный процент заполнения | Kroygacha sarfni baholash uchun taxminiy to'ldirish foizi | std 90 % | ✅ | `est_fill_percent` | S | L |
| CS-035 | Расход материала (kroygacha formula) | Sarf = detallar maydoni × (2 − taxminiy foiz/100) | misol 1 m², 90 % → 1.1 m² | ✅ | `calc.estimate_consumption_m2` (arra o'lchami maydoni) | S | L |
| CS-036 | Количество материала (faqat o'qish) | Kroygacha — taxminiy sarf; kroydan keyin — sarf minus деловой qoldiq maydoni | m² | 🟡 | Kroydan keyin ✅; kroygacha UI bo'sh (`CsParams.tsx` `matQty = res ? … : null`), hisob backendda bor | S | M |
| CS-037 | Количество листов | «Количество материала» yonida alohida «шт» maydoni | шт | 🟡 | Bizda bitta maydon: «по листам» ✓ bo'lsa listlar, aks holda m²; ikkalasi birga ko'rinmaydi | S | L |
| CS-038 | Стоимость материала | Цена материала × Расход материала | UZS | ✅ | `calc.cs_cost` | S | L |
| CS-039 | Стоимость материала (м2) (faqat o'qish) | Faqat ekran nusxasida bor; ma'nosi yordamda yo'q (taxminan: 1 m² ning hisoblangan narxi) | — | ❓ | — (Q-4) | S | L |
| CS-040 | Расчет стоимости операции по | 4 asos: Длина реза (karta kesish uzunligi × shu kartadagi listlar), Периметр деталей, Площадь материала (деловой qoldiqsiz), Площадь деталей | std Длина реза | ✅ | `OpCostBase`, `calc.cs_cost` | S | L |
| CS-041 | Цена операции (метр/рез) | Tanlangan asosdagi 1 birlik ish narxi | UZS | ✅ | `op_price` | S | L |
| CS-042 | Стоимость операции | Kroy ishining umumiy narxi | UZS | ✅ | `Operation.cost_operation` | S | L |
| CS-043 | Мин. размер остатка 1-й / 2-й стороны | Qoldiq deb hisoblanadigan bo'lakning ikkala tomonining minimal o'lchami | bizda std 1000 / 500 mm | ✅ | `remnant_min_side1/2`, `optimizer._classify` | S | H |
| CS-044 | Площадь делового остатка | Shu maydondan katta qoldiq «деловой» — material sarfiga kirmaydi | bizda std 0.5 m² | ✅ | `remnant_min_area` | S | H |
| CS-045 | Торцовка остатков | Qoldiq o'lchami torsovkani hisobga olib (foydali zona) yoki list chetigacha hisoblanadi | bizda std ✓ (foydali zona) | ✅ | `remnant_size_incl_trim`, `optimizer._leaf_remnant` | S | M |
| CS-046 | Минимальный размер детали (Ограничения) | Faqat ekran nusxasida; juda kichik detallar kroyga kirmasligi/ogohlantirishi (taxminiy) | bizda std 30 mm | 🟡 | `min_part_size`, `calc._small_warning` — GibLab xatti-harakati tasdiqlanmagan (Q-3) | S | M |
| CS-047 | Сохранить текущие параметры по умолчанию | Joriy parametrlarni yangi operatsiyalar uchun standart qilish | — | ✅ | `CsParams.tsx` `saveDefault`, `PUT /settings/cs_defaults/default` | S | M |
| CS-048 | Справка (F1) va parametr yonida «?» | F1 — yordam; ekranda har parametr yonida yashil «?» belgisi (kontekst yordam) | F1 | 🟡 | Umumiy «Справка» bo'limi bor; parametr yonida «?» yo'q, faqat tooltip (`ui.tsx` `Field.hint`) | M | M |

### 2.3 Детали — jadval, tezkor tugmalar, detal xossalari

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CS-060 | Jadval ustunlari | Д-на, Ш-на, Кол, Ткт, ОВ, ОН, ОЛ, ОП, Наименование, ОК, ИК, Ост | — | ✅ | `features/cs/columns.tsx` (+ Ctrl+P profil) | S | H |
| CS-061 | Д-на / Ш-на | Detal uzunligi/eni; qaysi o'lcham (zagotovka/detal/prifugovkadan keyin) ekanligi kiritish rejimiga bog'liq | mm | ✅ | `services/sizes.py`, `features/cs/sizes.ts` | S | H |
| CS-062 | Кол | Detal soni (bitta mahsulotdagi) | — | ✅ | `Part.qty` | S | H |
| CS-063 | Ткт | Belgi ✓ — detal kroyda aylantirilmaydi; Space bilan almashadi | — | ✅ | `Part.grain`, `CsParts.tsx` `spaceKey` | S | H |
| CS-064 | ОВ / ОН | Kromka yuqori/past — **uzunlik** bo'ylab yopishtiriladi | EL belgisi (A, B…) | ✅ | `Part.edge_top/bottom` | S | H |
| CS-065 | ОЛ / ОП | Kromka chap/o'ng — **en** bo'ylab | — | ✅ | `Part.edge_left/right` | S | H |
| CS-066 | Наименование + belgilar `=` `*` `%` | Nomga yozilgan belgi amalni bildiradi: `=` pazlash, `*` frezerlash (radius), `%` parmalash | — | 🟡 | Bizda belgilar GR/XNC operatsiyalaridan avtomatik hosil bo'ladi (`partMarks`, `render.part_marks`); nomga qo'lda yozilganini tahlil qilmaymiz (Q-7) | S | M |
| CS-067 | ОК | Umumiy soni = detal soni × mahsulotlar soni | — | ✅ | `calc.total_qty`, ustun `total` | S | H |
| CS-068 | ИК | Kroyga kirgan detallar soni | — | ✅ | `Part.used_qty`, `calc._account` | S | H |
| CS-069 | Ост | Kroyga kirmay qolgan detallar soni | — | ✅ | `Part.left_qty` | S | H |
| CS-070 | Свойства детали | Detal xossalari oynasi (Ctrl+Space; № ustunini ikki marta bosish) | — | ✅ | `PartDialogs.tsx` `PartProperties` | S | H |
| CS-071 | Space — kromkani almashtirish | ОВ/ОН/ОЛ/ОП katagida navbatdagi kromkaga o'tkazadi | bo'sh → A → B … | ✅ | `CsParts.tsx` `cycleEdge` | S | H |
| CS-072 | Shift+Space — perimetr bo'yicha kromka | To'rt tomonga bir xil kromka | — | ✅ | `spaceKey(true)` | S | H |
| CS-073 | Ctrl+PgUp — qator qo'shish | Joriy qatordan oldin yangi qator | — | ✅ | `act.insert` | S | H |
| CS-074 | Ctrl+PgDn — qator qo'shish (oxiriga) | Jadval oxiriga yangi qator | — | ✅ | `gotoDraft` (pastki qoralama qator) | S | H |
| CS-075 | Del / Shift+Del — o'chirish | Tanlangan qatorni o'chiradi | — | 🟡 | Del ✅; Shift+Del ro'yxatga olinmagan (`hotkeys.ts`) | S | L |
| CS-076 | Ctrl+↑ / Ctrl+↓ | Qatorni yuqoriga/pastga ko'chirish | — | ✅ | `act.move` | S | M |
| CS-077 | Tab/Enter, Shift+Tab/Shift+Enter, Ctrl+Tab/Ctrl+Enter | O'ngga (oxirida pastki qator, jadval oxirida yangi qator); chapga (qator boshida — oldingi qator); pastga — qator boshiga | — | 🟡 | Tab/Enter/Shift+Tab bor (`suppressKeyboardEvent`); Shift+Enter va Ctrl+Tab/Ctrl+Enter kodda ko'rinmadi | S | M |
| CS-078 | Home / ↑ / ↓ / End | Birinchi / oldingi / keyingi / oxirgi qatorga o'tish | — | ✅ | AG Grid standarti | S | L |
| CS-079 | Ctrl+V — Excel/OpenOffice dan qo'yish | Ustun tartibi: Д-на, Ш-на, Кол, Ткт, ОВ, ОН, ОЛ, ОП, Наименование; manba katakchalari nusxalanib jadvalga yoziladi | — | ✅ | `CsParts.tsx` `onPaste` | M | H |
| CS-080 | Qo'yishda noma'lum kromka nomi | Operatsiyalarda yo'q kromka nomi yangi EL (kromkalash) operatsiyasi sifatida qo'shiladi | — | ✅ | `onPaste` (`POST /operations` type EL) | S | M |
| CS-081 | Jadval ostidagi umumiy ko'rsatkichlar | «Площадь» va soni jonli ko'rsatiladi; GibLab'da maydon **zagotovka** o'lchamidan hisoblanadi (rasmlarda: 0.745 / 0.75 m²) | m² | 🟡 | Bizda `sz.detail` (kromkali detal) maydoni — kromka qalinligi > 0 bo'lsa farq (`CsParts.tsx` `summary`) | S | M |
| CS-082 | Д-на/Ш-на sarlavha va qiymat ranglari | Kiritish rejimiga qarab: zagotovka — ko'k, detal — yashil, prifugovkadan keyin — qizil kursiv | — | 🟡 | Ranglar faqat detal xossalari oynasida (`styles.css` `.sz-*`); jadval sarlavhasida yo'q | S | L |
| CS-083 | Detal xossalari oynasi (asosiy) | Chizma (kromka belgilari bilan), Изделие, Наименование, Описание, Толщина, Текстура, Количество/Всего, o'lchamlar jadvali, operatsiyalar ro'yxati, (EL)/(GR) bo'limlari | — | ✅ | `PartProperties` | M | H |
| CS-084 | Группировать в блок по | Detalni blokka guruhlash: Нет / Длине / Ширине + min va max soni; blok bir butun joylanadi | — | ✅ | `Part.group_by/min/max`, `optimizer.group_items` | M | M |
| CS-085 | (SP) Обработка поверхности bo'limi | Detalga sirt ishlovi operatsiyasini bog'lash | — | ❌ | `PartDialogs.tsx` bo'lim o'chirilgan (`disabled`); SP operatsiyasi yo'q | M | L |
| CS-086 | «Дополнительные параметры» (detal) | Detalga erkin «kalit = qiymat» maydonlari | — | ❌ | `Part` modelida `extra` yo'q (mahsulotda bor) | S | L |
| CS-087 | Detalga XNC ishlov qo'shish | Detal oynasida «Добавить: (XNC) Обработка»; parametrlar bo'limi | — | ✅ | `add_xnc_for_part` (`main.py`), `PartDialogs.tsx` | S | M |
| CS-088 | № в изделии / № в раскрое | Detalning mahsulotdagi va kroydagi tartib raqami | — | ✅ | `PartProperties` pastki qatori, `mapsOfPart` | S | L |

### 2.4 O'lcham kiritish rejimlari va pripusk (detailMode, stock)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| DM-001 | Rejim: заготовка | Kiritilgan o'lcham = zagotovka; prifugovka/kromka qalinligi undan hisoblanadi, pilniy o'lcham o'zgarmaydi | 3 rejimdan biri | ✅ | `SizeMode.BLANK`, `sizes.py` | S | H |
| DM-002 | Rejim: деталь (с кромкой) | Kiritilgan o'lcham = kromkali tayyor detal; pilniy o'lcham kromka qalinligiga kamayadi, prifugovkaga ko'payadi | Std (xodimlar) | ✅ | `SizeMode.DETAIL` | S | H |
| DM-003 | Rejim: заготовка после прифуговки (без кромки) | Kiritilgan o'lcham = kromkasiz, prifugovkadan keyingi; pilniy o'lcham prifugovkaga ko'payadi | — | ✅ | `SizeMode.JOINTED` | S | M |
| DM-004 | Rejimni o'zgartirish ogohlantirishi | Detallar kiritilib kromka qo'yilgandan keyin rejim o'zgartirilmasligi tavsiya etiladi — o'lchamlar qayta hisoblanadi | — | ✅ | `SizeModeDialog` (`sizemode.hint`) | S | L |
| DM-005 | To'rt xil o'lcham jadvali | Детали / заготовки после прифуговки / заготовки / пильный; kiritilgan qator rang bilan ajratiladi | — | ✅ | `PartProperties` `sizeRow`, `sizes.py` | S | M |
| DM-006 | Tomonlar bo'yicha o'zgarish ustunlari ▽ △ ▷ ◁ | Har qatorda har tomon uchun alohida delta ko'rinadi (−kromka, +prifugovka, +pripusk); «пильный» qatorida pripusk qo'lda kiritiladi | — | 🟡 | Faqat «пильный» qatorida pripusk kiritiladi; boshqa qatorlarda delta ko'rsatilmaydi | S | L |
| DM-007 | Rejim tanlash oynasi (bo'sh jadvalda) | Detallar jadvali bo'sh ochilganda rejim so'raladi; sozlamada o'chirib qo'yish mumkin | — | 🟡 | Rejim havolasi/oynasi bor; avtomatik taklif va «so'ramaslik» sozlamasi yo'q (`Q_QA_V2_1.md` §4) | S | L |
| DM-008 | Kromka qalinligi va prifugovka eni ta'siri | EL parametrlari («Толщина», «Ширина прифуговки») detal o'lchamiga ta'sir qiladi (kromkali tomonlar bo'yicha) | — | ✅ | `ELParams.thickness/jointing_width`, `sizes.py` | S | H |
| DM-009 | Detal/tomon pripuskini alohida berish | Pripusk ayrim detalga va ayrim tomonga qo'lda beriladi (detal xossalari) | mm | ✅ | `Part.allow_*` | S | M |
| DM-010 | Pripuskni kartada punktir chiziq bilan ko'rsatish | Kroy kartasida pripusk detal ichida punktir chiziq sifatida chiziladi | — | ❌ | `MapView.tsx`, `render.map_svg` — chizilmaydi | S | L |

### 2.5 Листы и остатки (jadval)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CS-100 | Jadval ustunlari | Наименование (tur), Длина, Ширина, Площадь, Количество, Исп. Кол-во, Остаток | — | ✅ | `CsSheets.tsx` (+ ТД/ТШ/otstup ustunlari bizda qo'shimcha) | S | H |
| CS-101 | Qator turi | Лист / остаток / деловой остаток (kroydan keyingi qoldiqlar jadvalga qator bo'lib qo'shiladi) | — | ✅ | `CsSheets.tsx` `resultRows`, `sheets.kind.*` | S | H |
| CS-102 | Количество | List uchun — kroyga beriladigan boshlang'ich son; qoldiq uchun — kroy natijasidagi son | bizda 10000 = cheksiz | ✅ | `StockSheet.qty` | S | H |
| CS-103 | Исп. Кол-во (list) | Kroyda ishlatilgan list soni | — | ✅ | `calc._account` | S | H |
| CS-104 | Исп. Кол-во (qoldiq) | Qoldiq uchun — mijoz olib ketadigan bo'laklar soni (qo'lda kiritiladi) | — | ❌ | Natija qatorlarida ustun tahrirlanmaydi, ombor ham hisobga olmaydi (`CsSheets.tsx`) | M | M |
| CS-105 | Остаток = Количество − Исп. | Hisoblanadigan qoldiq soni | — | ✅ | `CsSheets.tsx` ustun `left` | S | M |
| CS-106 | Jadval tugmalari | Qator qo'shish (Ctrl+PgUp/PgDn), o'chirish (Del/Shift+Del), ↑↓ (Ctrl+↑↓), navigatsiya | — | 🟡 | Ctrl+PgUp ham oxiriga qo'shadi (joriydan oldin emas); Shift+Del yo'q; list tartibi = ustuvorlik (`hotkeys` "sheets") | S | L |

### 2.6 Раскрой — xaritalar ko'rinishi

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CS-120 | «Раскроить» | Optimizatsiyani ishga tushiradi; natija kartalar ro'yxati | — | ✅ | `CsCut.tsx` `runCutting`, `POST .../optimize` | M | H |
| CS-121 | Karta ko'rinishi | Detal/qoldiq/chiqindi, ichida raqam va o'lcham; tanlangan detalning barcha nusxalari ajratiladi | — | ✅ | `MapView.tsx` | M | H |
| CS-122 | Masshtab | Sichqoncha g'ildiragi bilan kattalashtirish | — | ✅ | `CsCut.tsx` wheel (1×..6×) | S | M |
| CS-123 | Kartalar bo'ylab navigatsiya | Birinchi / oldingi / keyingi / oxirgi karta (Home/↑/↓/End) | — | ✅ | `CsCut.tsx` `useHotkeys("cut")` | S | M |
| CS-124 | Karta izohi (F2) | Har kartaga izoh yozish; chopda ko'rinadi | — | ✅ | `act.comment`, `PATCH .../maps/{idx}` | S | H |
| CS-125 | Постпроцессор | Kroyni arra stanogi formatiga o'tkazadi | stanokka bog'liq | 🟡 | Shablon tizimi + csv/commands/dxf/json bor; haqiqiy stanok formati foydalanuvchidan kutilmoqda | L | H |
| CS-126 | Statistika qatori | № (karta/jami), S (list o'lchami), C (kartadagi/jami listlar), Cp (detallar), LT (kesish uzunligi), F (to'ldirish %) | — | ✅ | `CsCut.tsx` `INDICATORS` (12 ta, sozlanadi) | S | H |
| CS-127 | Таблица команд | Ustunlar: Кд (buyruq), Р (o'lcham), К (soni), Д (detal/qoldiq raqami) | — | ✅ | `CsCut.tsx` `commands-table` | M | M |
| CS-128 | Buyruq kodlari | Tx — torsovka, Cx — oddiy kesim, Px — detalni ajratuvchi yakuniy kesim, Wx — qoldiq; x = daraja (burilish raqami) | — | ✅ | `CutCommand`, `optimizer._build_map` (+ `R` — list burish, bizda qo'shimcha) | M | M |
| CS-129 | Panellar almashtirgichi | O'ng panelda miniatyuralar ↔ buyruqlar jadvali | — | ✅ | `CsCut.tsx` `toggle-commands` | S | L |
| CS-130 | «Редактирование раскроя» ga o'tish | Xaritani qo'lda tahrirlash oynasini ochadi | — | ✅ | `btn-edit-cut` → `CutEditor` | S | H |

### 2.7 Печать (CS) — chop sozlamalari (cs_params9 rasmi)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CS-160 | Chop profili va chap menyu | Профиль (✚ ✎ ✕), Поля страницы, Настройки печати, Изделия va har operatsiya (CS/CL/EL) uchun alohida sozlama | — | ✅ | `Print.tsx`, `PrintSettings` | M | H |
| CS-161 | Печать заголовка | CS bo'limining sarlavhasini chop etish/etmaslik | — | 🟡 | Loyiha sarlavhasi umumiy (`header`); CS bo'limi sarlavhasi doim chiqadi (`render._cs_section`) | S | L |
| CS-162 | Печать деталей | Detallar jadvalini chop etish | — | ✅ | `cs_parts` | S | H |
| CS-163 | Выделить колонку кромкования | Kromka ustunini ajratib ko'rsatish | — | ❌ | `PrintSettings` da yo'q | S | L |
| CS-164 | Группировать детали по изделиям | Detallar jadvalini mahsulotlar bo'yicha guruhlash | — | ❌ | `PrintSettings` da yo'q; `render._cs_section` guruhlamaydi | S | M |
| CS-165 | Печать невместившихся деталей | Kroyga sig'magan detallar jadvali | — | ✅ | `cs_unplaced` | S | H |
| CS-166 | Печать листов | Ishlatilgan listlar jadvali | — | ✅ | `cs_sheets` | S | M |
| CS-167 | Печать отходов | Qoldiq/chiqindilar jadvali | — | ✅ | `cs_remnants` | S | M |
| CS-168 | Печать карт раскроев | Xaritalarni chop etish | — | ✅ | `cs_maps` | S | H |
| CS-169 | Печать обработки на деталях | Xaritadagi detallar ustida ishlov (pazlash/frezalash/parmalash) belgilarini chop etish | — | ❌ | `PrintSettings` da yo'q (belgilar faqat jadval/legendada) | S | M |
| CS-170 | Ориентация карт раскроя | Karta sahifasi: Книжная / Альбомная | — | ❌ | `PrintSettings` da yo'q | M | M |
| CS-171 | Заголовок карт кроя | Karta sarlavhasida: detallar soni, kesish uzunligi, to'ldirish foizi (belgilab tanlanadi) | — | ✅ | `map_header_fields` (N,S,C,Cp,LT,F … 11 ta) | S | H |
| CS-172 | Печать кромок (detalda) | Kartadagi detalda kromka chiziqlari | — | ✅ | `map_edges` | S | H |
| CS-173 | Печать наименования детали | Detal ichida nom (raqam bilan/siz) | — | ✅ | `map_part_label` | S | M |
| CS-174 | Стиль номера детали | Detal raqami shrift o'lchami va qalinligi | masalan 10, qalin ✗ | ❌ | Shrift avtomatik hisoblanadi (`render.map_svg` `fs`) | S | L |
| CS-175 | Стиль размеров | O'lcham yozuvi shrifti, qalinligi, «Разворачивать шрифты» (vertikal yozuvni burish) | masalan 12, qalin ✓ | ❌ | `render.map_svg` — qat'iy | S | L |
| CS-176 | Заливка панели | Detal to'ldirishi: rang va shtrixlash (shablon) | — | ❌ | `COLORS` qat'iy | S | L |
| CS-177 | Заливка отходов | Chiqindi to'ldirishi: rang va shtrixlash | — | ❌ | `COLORS` qat'iy | S | L |

### 2.8 (CSE) Редактирование раскроя — qo'lda tahrir

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CSE-001 | Tahrir oynasi | Chapda detallar jadvali, o'ngda karta; har amalda ИК/Ост yangilanadi | — | ✅ | `CutEditor.tsx`, `services/editor.py` | L | H |
| CSE-002 | Detallar jadvali ustunlari | Длина, Ширина (zagotovka), Кол-во, Исп. Кол., Остаток, Ткт, Наименование | — | 🟡 | Mahsulot/uzunlik/en/son/ishl./qoldiq/nom bor; **Ткт ustuni yo'q**, o'lchamlar zagotovka emas, kiritilgan qiymat (`CutEditor.tsx` `ed-parts`) | S | M |
| CSE-003 | Полноэкранный режим (F9) | Tahrir oynasini butun ekranga yoyish | F9 | 🟡 | Oyna doim to'liq ekran (`Modal full`); F9 yorlig'i yo'q | S | L |
| CSE-004 | Отменить (Ctrl+Z) | Oxirgi amalni bekor qilish | — | ✅ | `CutEditor.tsx` `undo` | S | H |
| CSE-005 | Вернуть (Ctrl+Y) | Bekor qilingan amalni qaytarish | — | ✅ | `redo` | S | H |
| CSE-006 | Добавить карту кроя | Bo'sh yangi karta (list tanlanadi) | — | ✅ | `editor._apply add_map` | M | M |
| CSE-007 | Удалить карту кроя | Kartani o'chirish | — | ✅ | `delete_map` | S | M |
| CSE-008 | Количество листов | Karta nechta bir xil list uchun ekanligini o'zgartirish | — | ✅ | `copies` (`C:` maydoni) | S | M |
| CSE-009 | Торцовка листа | Karta (list) torsovkasini tahrirlash tugmasi; ma'nosi yordamda ochilmagan | — | ❌ | Tahrir oynasida yo'q (list qatorida ТД/ТШ bor, kartada o'zgartirib bo'lmaydi) (Q-8) | M | L |
| CSE-010 | Переместить вначало (Ctrl+←) | Tanlangan polosa/detalni o'z darajasida boshiga ko'chirish | — | ✅ | `editor._move to=start` | M | M |
| CSE-011 | Переместить вконец (Ctrl+→) | Oxiriga ko'chirish | — | ✅ | `_move to=end` | M | M |
| CSE-012 | Клонировать полосу или деталь (Ctrl+C) | Tanlanganning nusxasini bo'sh joyga qo'yish | — | ✅ | `_clone` | M | M |
| CSE-013 | Развернуть резы (Ctrl+R) | Tanlangan hududni boshqa yo'nalishdagi kesim bilan qayta joylash | — | ✅ | `_rotate` | L | M |
| CSE-014 | Удалить выделенное (DEL / o'ng tugma) | Detal yoki polosani olib tashlash (joyi chiqindiga aylanadi) | — | ✅ | `_remove`, `onPick` button=2 | S | H |
| CSE-015 | Отфильтровать нулевые детали (Ctrl+F) | Qoldig'i 0 detallarni ro'yxatdan yashirish | — | ✅ | `onlyLeft` | S | L |
| CSE-016 | Переместить карту вверх/вниз (Ctrl+↑/↓) | Kartalar tartibini o'zgartirish | — | ❌ | `CutEditor.tsx` — yo'q (Ctrl+↑↓ bog'lanmagan) | M | L |
| CSE-017 | Kartalar bo'ylab Home / ↑ / ↓ / End | Birinchi/oldingi/keyingi/oxirgi kartaga o'tish | — | 🟡 | PgUp/PgDn/↑/↓ bor; Home/End yo'q | S | L |
| CSE-018 | Detal/polosani tanlash | Sichqoncha bilan bosish | — | ✅ | `MapView` `onPick` | S | H |
| CSE-019 | Ko'p tanlash (Ctrl+bosish) | Bir nechta detal/polosani birga tanlash | — | ❌ | `sel` — yagona yo'l (`path`) | M | L |
| CSE-020 | Tahrir rejimi (Shift+bosish) | Chap tugma bilan detal qo'yish rejimi | — | 🟡 | Bizda ro'yxatdan detal tanlab bo'sh joyga bosiladi; Shift ota tugunni tanlaydi | S | M |
| CSE-021 | Shift+Ctrl/Alt+bosish | Teksturasi bo'lmagan detalni burib qo'yish | — | ✅ | `place` (rotated = Alt yoki Ctrl bosilgan); tekstura tekshiruvi `editor._place` | S | M |
| CSE-022 | Shift+A+bosish — ko'p qo'yish | Bir bosishda ko'p nusxa joylash | — | ❌ | Faqat bitta nusxa (`place`); `place_auto` — alohida | M | L |
| CSE-023 | Shift+W+bosish — blok bilan tahrir | Guruhlangan (blok) detallar uchun polosani blokdagi maksimal detal soniga kengaytirish | — | ❌ | `Ctrl+Q` (`expand`) boshqacha: bo'sh joy hisobiga kengaytiradi | M | L |

### 2.9 Qoldiqlar (остатки) va ombor almashinuvi

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| REM-001 | Qoldiq turlarini ajratish | Chiqindi / qoldiq (ikkala tomon ≥ chegara) / деловой qoldiq (maydon ≥ chegara) | — | ✅ | `optimizer._classify`, `B_DOMAIN_RULES.md` B4 | S | H |
| REM-002 | Деловой qoldiq sarfga kirmaydi | Material sarfi (Количество материала) delovoy qoldiq maydoniga kamayadi | — | ✅ | `calc.cs_cost`, `CuttingResult.material_qty_m2` | S | H |
| REM-003 | Qoldiqlar kartada raqamlanadi va jadvalga tushadi | Har qoldiq raqam oladi (Д1, Д2…), «Листы и остатки»da qator bo'ladi | — | ✅ | `Offcut.number`, `CsSheets.tsx` `resultRows` | S | H |
| REM-004 | Qoldiqlarni omborga saqlash | Kroydan so'ng qoldiq/list ma'lumoti omborga yoziladi: loyiha ichki id, tashqi id, tur (list/qoldiq), delovoy belgisi, o'lcham, boshlang'ich va ishlatilgan son, loyiha nomi/fayli | — | 🟡 | Faqat деловой qoldiqlar (xom o'lcham) yoziladi va ishlatilgan ombor qoldiqlari kamayadi; butun listlar va mayda qoldiqlar yozilmaydi (`warehouse.commit`) (Q-5) | M | H |
| REM-005 | Ombordan qoldiqlarni yuklash | Material kodi bo'yicha ombordagi qoldiqlar ro'yxati keladi (id, uzunlik, en, soni, izoh) va kroyda ishlatiladi | — | ✅ | `RemnantPicker`, `POST .../sheets/from-remnants`, `GET /remnants` | M | H |
| REM-006 | Material kodi bilan moslash | So'rov materialning kodi (masalan `EG.W1000ST2.18`) bilan filtrlanadi | — | ✅ | `warehouse.material_key` (kod yoki nom), `useRemnants(code)` | S | M |
| REM-007 | Qoldiq id'si loyihada saqlanadi | Kroyda ishlatilgan qoldiqning ombor id'si loyihada qoladi (keyin ombor yangilanadi) | `dbId` | ✅ | `StockSheet.source_remnant_id` | S | H |
| REM-008 | Qoldiq izohi | Ombordagi qoldiqqa erkin izoh | — | ✅ | `RemnantRow.note` | S | L |
| REM-009 | Tanlangan qoldiqlar hisoboti (rezerv) | Qoldiqlar kroy uchun tanlanganda omborga «shu qoldiqlar band» deb xabar yuboriladi | — | ❌ | Rezerv/holat yo'q: faqat kroydan keyin `commit`da yechiladi; `F_DATA_MODEL` dagi `reserved_project` ustuni `db.py`da yo'q | M | M |
| REM-010 | Almashinuv natijasi/xatosi | Muvaffaqiyatli bo'lsa OK, aks holda ombor xato matnini qaytaradi va foydalanuvchiga ko'rsatiladi | — | ✅ | `warehouse.WarehouseConflict` (409 + matn) | S | M |
| REM-011 | 1C HTTP protokoli (1С Бухгалтерия 8) | Tashqi tizimga POST: type=load/report/save, sheet (list yoki погонаж), code, project, project.name, date; javob — matn qatorlari | — | ❌ | Yo'q; bizda ichki ombor + MES REST (`GET /api/remnants`); MES manzillari kutilmoqda (Q-6) | L | L |
| REM-012 | 1C fayl almashinuvi (Бухгалтерия 7) | Almashinuv `.request`/`.response`/`.output` fayllari orqali | — | ❌ | Yo'q (Q-6) | M | L |
| REM-013 | Pogonaj (CL) qoldiqlari | Almashinuvda sheet=false — chiziqli material qoldiqlari | — | ❌ | `RemnantRow` da `linear` yo'q (`F_DATA_MODEL` §F3 bilan nomuvofiq) | M | L |

### 2.10 Material katalogi (goods)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| CAT-001 | Katalog jadvali va ustunlari | Excel faylda: ID, ota-ID, papka belgisi, kod, nom, birlik, narx, qalinlik, uzunlik, en | `goods.xls` | 🟡 | `CatalogItemRow` shu maydonlarning ko'pini saqlaydi; Excel/Dropbox fayli emas, MES sinxroni va import (`/catalog/import`, `/catalog/sync`) | M | L |
| CAT-002 | Kategoriyalar daraxti | Ildiz → ishlab chiqaruvchi → qalinlik → o'lcham → tovar (papka belgisi + ota-ID) | — | 🟡 | DB'da `parent_id`/`folder` bor; UI — tekis ro'yxat va tur filtri (`CatalogPicker.tsx`) | M | L |
| CAT-003 | Ustun xaritasini sozlash | «Настройки → Товары»da jadval qatorlarini fayl ustunlariga moslash | — | ✅ | `Settings.tsx` Catalog import (`col_map`) | S | L |
| CAT-004 | Katalogdan material tanlash | Tanlangan tovar kod, nom, narx, qalinlik va list o'lchamini operatsiyaga yozadi | — | ✅ | `main._new_operation` (+ kerf/trim/tekstura `params` dan) | S | M |
| CAT-005 | Katalogni umumiy papkada ulashish | Fayl umumiy (Dropbox) papkada turib, ko'p ish joyi va onlayn modul bilan ishlatiladi | — | 🟡 | Dropbox kerak emas: MES katalogi + `POST /catalog/sync` | M | L |

## 3. Algoritmik talablar

### 3.1 GibLab yordami optimizator xatti-harakati haqida nima deydi

| Mavzu | Yordamdagi ma'no (o'z so'zimiz) | Bizda |
|---|---|---|
| Kesim darajasi | «Вращение» — kesish yo'nalishi almashuvi; maksimal soni cheklanadi (ba'zi stanoklarda ≤ 4). Ko'proq daraja = yaxshiroq joylashuv | ✅ daraja = burilish raqami, ≤ `max_rotations` (2..6), har natija `validate.py` dan o'tadi |
| Polosa turlari | Oddiy polosa bitta detaldan boshlanadi; murakkab polosa bir nechtasidan | ✅ `complex_strips` ☐ bo'lsa 3-daraja yopiladi |
| Torsovka va foydali zona | Torsovka listning yuqori va chap chetida (propil bilan), qarama-qarshi chetda — minimal otstup; 0 — torsovka yo'q | ✅ bir xil formula (`optimizer._zone`) |
| Birinchi kesish yo'nalishi | Любое/По длине/По ширине; «предпочтительно» faqat to'ldirilishi pastroq kartalarda | ✅ `_axes_for` + `fill_packet` chegarasi |
| Paket / karralik | Paket = Высота пакета / qalinlik; to'ldirilish chegaradan yuqori bo'lsa listlarni paketga birlashtirishga harakat | ✅ bir xil kartani takrorlash (`copies`), `prefer_big_pack` bizning qo'shimcha |
| Polosa chegaralari | Min eni (qisqich), max uzunlik (sig'masa buriladi); ekran nusxasida max eni ham bor | ✅ `min/max_strip_width`, `max_strip_length` |
| Saralash | Polosalar va polosa ichi: kamayish / o'sish / tor o'rtada | ✅ `_reorder` |
| Minimal obrezka | Yupqa chet kesimini cheklaydi; yordam «propildan katta bo'lsin» deydi | 🟡 `validate._check_trim`: qoldiq + propil ≥ min (Q-1) |
| Qoldiq qoidalari | Ikkala tomon ≥ chegara — qoldiq; maydon ≥ chegara — деловой; деловой sarfga kirmaydi; «Торцовка остатков» o'lchamni belgilaydi | ✅ `_classify`, `_leaf_remnant`, `calc.cs_cost` |
| Tekstura | Ткт ✓ detal kroyda aylantirilmaydi; material darajasida o'chirish mumkin | ✅ `can_rotate = not (use_grain and grain)` |
| Blok (guruh) | Detal xossalarida «Группировать в блок по длине/ширине» + min/max soni; tahrirda blok uchun alohida rejim | ✅ optimizatorda (`group_items`); 🟡 qo'lda tahrirda faqat umumiy amallar |
| Birlashtirish | «Объединение деталей» va «Группировка по свойствам» — ma'nosi yordamda yo'q | ❌ optimizator ishlatmaydi (Q-2) |
| Pripusk | Detal pilniy o'lchamiga qo'shiladi; kartada punktir bilan ko'rsatiladi | ✅ o'lchamda; ❌ punktir |
| Ustunlar (kolonka) | Yordamda alohida tavsif yo'q | — (bizda `colpack.py` — ichki yaxshilash) |
| Narx formulalari | Sarf (kroygacha) = detallar maydoni × (2 − foiz/100); Количество = sarf − деловой qoldiq; Стоимость = narx × sarf; operatsiya narxi 4 asosda | ✅ `calc.py` (formulalar bir xil) |
| Listlar ustuvorligi | Yordamda yo'q (jonli oynada aniqlangan: son bo'yicha o'sish, cheksiz oxirida) | ✅ `_stock_orders`, importer (`CLAUDE.md` qoida 13) |

### 3.2 Bizning optimizator (`C_CS_OPTIMIZER_SPEC.md`) bilan farqlar

1. **Минимальная обрезка** — spetsifikatsiya C3 «qoldiq ≥ propil+min» deydi, validator «qoldiq + propil ≥ min», yordam esa qiymatni propildan katta qo'yishni maslahat beradi (bu «tilim + propil» talqiniga yaqinroq, chunki faqat tilimning o'ziga qo'llansa, propildan katta qilishning ma'nosi bo'lmasdi). **Hal etilmagan** — Q-1.
2. **Объединение деталей / Группировка по свойствам** — GibLab'da mavjud, bizda optimizatorga ulanmagan (UI'da «doim yoqilgan» deb ko'rsatiladi, aslida hech nima qilmaydi).
3. **Paket/karralik** — yordam paketni faqat to'ldirilish foiziga bog'laydi; bizda qo'shimcha «Большой пакет» va faqat **bir xil** kartalarni takrorlash. GibLab turlicha kartalarni bitta paketga birlashtiradimi — noma'lum (Q-12).
4. **Karta darajasidagi torsovka** (CSE «Торцовка листа») — bizda list qatori (ТД/ТШ) orqali, tayyor kartada o'zgartirib bo'lmaydi.
5. **Pripusk punktiri** — optimizatorga ta'sir qilmaydi, faqat ko'rsatish.
6. **Qo'lda tahrir rejimlari** — ko'p tanlash, ko'p qo'yish, blok bilan kengaytirish yo'q; `Ctrl+Q` (kengaytirish) bizniki, yordamda yo'q.
7. **Bizda qo'shimcha** (yordamda ko'rinmagan): `quality` (fast/normal/max), `max_part_types_per_map`, `kerf_group`, `trim_includes_kerf`, variantlar solishtirish, `R` buyrug'i, ombor «arvoh» himoyasi.

## 4. Yetishmayotganlar ro'yxati (❌ va 🟡), ustuvorlik bo'yicha

| № | ID | Nima qilish kerak | Tegadigan fayllar | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|
| 1 | CS-125 | Haqiqiy arra stanogi postprotsessor formatini qo'shish (namuna fayl kelganda): shablon + sinov. Foydalanuvchi javobisiz boshlab bo'lmaydi | `services/postprocessors.py`, `tpl_sandbox.py`, `api_extra.py` | L | H |
| 2 | CS-016 | «Минимальная обрезка» ma'nosini jonli GibLab'da tekshirib (propil 3 / min 5 holati), validator va C3 ni bir xil qilish | `services/validate.py`, `optimizer.py` (`_fits`, `_trim_violations`), `C_CS_OPTIMIZER_SPEC.md` | M | H |
| 3 | REM-004, CS-104 | Qoldiqlarni omborga yozishni to'ldirish: mijoz olib ketgan («Исп. кол-во») qoldiqlarni belgilash va ularni omborga yozmaslik; (savolga qarab) mayda va butun list ma'lumotini ham yozish | `warehouse.py`, `main.py` (`/remnants/commit`), `CsSheets.tsx`, `RemnantCommit.tsx`, `models.py` | M | H |
| 4 | CS-164, CS-170, CS-169, CS-174, CS-175, CS-163 | Chop sozlamalarini kengaytirish: guruhlash (изделия bo'yicha), Книжная/Альбомная, ishlov belgilari, kromka ustunini ajratish, shrift o'lcham/qalinligi | `models.py` `PrintSettings`, `render.py` (`_cs_section`, `map_svg`), `Print.tsx`, `i18n_src.py`, `H_REPORTS_LABELS.md` | M | M |
| 5 | REM-009 | Tanlangan qoldiqlarni kroy tugamasdan band qilish (rezerv) — ko'p foydalanuvchi to'qnashuvini oldini olish | `db.py` (`RemnantRow.reserved_*`), `warehouse.py`, `main.py` (`from-remnants`), `RemnantPicker` | M | M |
| 6 | CS-081, CSE-002 | Detallar jadvalidagi «Площадь»ni zagotovka maydoni bo'yicha hisoblash; tahrir ro'yxatida zagotovka o'lchami va Ткт ustuni | `CsParts.tsx` (`summary`), `CutEditor.tsx`, `e2e/kroy.spec.ts` | S | M |
| 7 | CS-020, CS-021, CS-022 | «Объединение деталей» va «Группировка по свойствам» ma'nosini aniqlab (Q-2) amalga oshirish; aniqlanmaguncha belgini yashirish yoki «hozircha ishlamaydi» deb ko'rsatish | `models.py`, `optimizer.py` (`group_items`), `CsParams.tsx` | M | M |
| 8 | CS-036, CS-037 | Kroygacha «Количество материала» (taxminiy) va «Количество листов»ni birga ko'rsatish | `CsParams.tsx`, `calc.cs_cost` (`info`), `main.py` (javobga qo'shish) | S | M |
| 9 | CS-066 | Nomga qo'lda yozilgan `=` `*` `%` belgilarini ham tanish (Excel/Bazis importdan kelsa) — Q-7 ga qarab | `CsParts.tsx`, `sizes.ts` `partMarks`, `render.part_marks` | S | M |
| 10 | CS-048 | Parametr yonida «?» va kontekst yordami (o'zimiz yozgan matn): F1 shu parametrga ochilsin | `ui.tsx` (`Field`), `Help.tsx`, `i18n_src.py` | M | M |
| 11 | CSE-009, CSE-016, CSE-019, CSE-022, CSE-023, CSE-020 | Qo'lda tahrir: kartada torsovka, kartalar tartibi (Ctrl+↑↓), ko'p tanlash, ko'p qo'yish (Shift+A), blok bilan kengaytirish (Shift+W), Shift+bosish rejimi — **avval** xodimlar ularni ishlatishini aniqlash (Q-8) | `editor.py`, `CutEditor.tsx`, `MapView.tsx` | L | L |
| 12 | DM-010 | Kartada pripusk punktir chizig'i (ekran va chop) | `MapView.tsx`, `render.map_svg` | S | L |
| 13 | CS-077, CS-075, CS-106, CSE-017, CSE-003 | Mayda yorliqlar: Shift+Enter, Ctrl+Tab/Enter, Shift+Del, Ctrl+PgUp (joriydan oldin), Home/End (tahrirda), F9 | `CsParts.tsx`, `CsSheets.tsx`, `CutEditor.tsx`, `hotkeys.ts`, `E_HOTKEYS.md` | S | L |
| 14 | CS-082, DM-006, DM-007 | Д-на/Ш-на sarlavha ranglari; ▽△▷◁ ustunlari barcha o'lcham qatorlarida; bo'sh jadvalda rejim taklifi | `columns.tsx`, `PartDialogs.tsx`, `styles.css` | S | L |
| 15 | CS-176, CS-177 | Chopda detal/chiqindi to'ldirish rangi va shtrixlash tanlovi | `PrintSettings`, `render.py`, `Print.tsx` | S | L |
| 16 | CS-085, CS-086 | Detalda (SP) sirt ishlovi va «Дополнительные параметры» (`extra`) | `models.py`, `PartDialogs.tsx`, SP operatsiyasi | M | L |
| 17 | REM-013 | Pogonaj qoldiqlari uchun `linear` bayrog'i (CL operatsiyasi bilan birga) | `db.py`, `warehouse.py` | M | L |
| 18 | REM-011, REM-012 | 1C bilan almashinuv (HTTP/fayl) — faqat korxona 1C ishlatsa; aks holda MES REST bilan yopiladi | `api_extra.py`, `services/mes.py` | L | L |
| 19 | CAT-001, CAT-002, CAT-005 | Katalog daraxti (papkalar) UI'da va Excel/MES sinxroni | `CatalogPicker.tsx`, `Settings.tsx`, `main.py` (`/catalog`) | M | L |
| 20 | CS-161, CS-014, CS-022, CS-046, CS-039, CS-002 | Kichik tuzatishlar: CS bo'lim sarlavhasi belgisi, max polosa eni, chizma saqlash belgisi, min detal ma'nosi, «Стоимость (м2)», propil > 0 tekshiruvi | `PrintSettings`, `CsParams.tsx`, `models.py` | S | L |

## 5. Aniqlashtirish kerak bo'lgan savollar (yordam javob bermaganlar)

1. **Q-1. «Минимальная обрезка».** GibLab'da bu qiymat tilimning (chiqindi chetining) o'zi uchunmi yoki tilim + propil uchunmi? Tekshirish: propil 3, min 5 bilan 2 mm li tilim hosil qiladigan karta chiqadimi? Yordam faqat «propildan katta qiling» deydi.
2. **Q-2. «Объединение деталей» va «Группировка деталей по свойствам».** Xodimlar ishlatadimi? GibLab'da yoqilganda xarita qanday o'zgaradi (bir xil detallar bitta blok bo'lib kesiladimi)? Qaysi xossalar bo'yicha guruhlanadi?
3. **Q-3. «Минимальный размер детали».** Kichik detal kroyga umuman kirmaydimi yoki faqat ogohlantirishmi? (Yordam matnida yo'q, faqat ekran nusxasida.)
4. **Q-4. «Количество листов» va «Стоимость материала (м2)».** Bu maydonlar nimani ko'rsatadi, tahrirlanadimi? Kroygacha ham to'ladimi?
5. **Q-5. Qoldiqlar.** (a) «Исп. кол-во» — mijoz olib ketgan qoldiqlar omborga yozilmasligi kerakmi? (b) Деловой bo'lmagan mayda qoldiqlar ham omborda kerakmi? (c) Butun listlar ombori ham MebeliX'da yuritiladimi yoki MES'dami?
6. **Q-6. Tashqi tizim.** Korxona 1C ishlatadimi yoki faqat MES? MES API manzillari, autentifikatsiya, webhook formati (mavjud ochiq savol).
7. **Q-7. Nomdagi belgilar.** Bazis eksportidan kelgan detal nomlarida qo'lda `=` `*` `%` belgilari uchraydimi? Bo'lsa, ularni ham amal belgisi deb tanishimiz kerakmi?
8. **Q-8. «Торцовка листа» (tahrirda).** Xodimlar nima uchun ishlatadi (kartaga alohida torsovka)? Ko'p tanlash, ko'p qo'yish (Shift+A), blok bilan kengaytirish (Shift+W) va kartalar tartibini o'zgartirish tahrirda kerakmi?
9. **Q-9. Chop.** Kartalar qaysi yo'nalishda (Книжная/Альбомная) chop etiladi? Shrift o'lchami va to'ldirish ranglarini xodimlar o'zgartiradimi? Miniatyura rejimi (A4 ga 4–6 karta) kerakmi?
10. **Q-10. Postprotsessor.** Arra stanogi modeli va namuna fayl (mavjud ochiq savol).
11. **Q-11. Pripusk.** «Припуск на обработку заготовки» korxonada ishlatiladimi? Ishlatilsa — xaritada punktir kerakmi?
12. **Q-12. Paket.** GibLab turlicha kartalarni bitta paketga birlashtiradimi yoki faqat bir xil kartalarnimi? (Bizda faqat bir xil.)
13. **Q-13. Propil.** GibLab 0 dan katta propil talab qiladi; bizda 0 ham mumkin — shunday qolsinmi?
14. **Q-14. Burilishlar soni.** Korxona arra stanogi necha burilishgacha ruxsat beradi (yordam ba'zilarida 4 deydi)? Standart 6 qolsinmi?
15. **Q-15. «Сохранение чертежа карт кроя».** O'chirilsa nima bo'ladi (loyiha hajmi kichrayadimi, xarita keyin qayta hisoblanadimi)? Bizda xarita doim saqlanadi — yetarlimi?

## 6. Bizda bor, yordamda ko'rinmagan (hisobga kirmagan)

`quality` (Tez / Standart / Maksimal), variantlar solishtirish oynasi, `kerf_group`, `max_part_types_per_map`, `trim_includes_kerf`, ТД/ТШ/otstup list qatorida, `До кроить`, MES webhook/skaner, ombor «arvoh» himoyasi, 12 ta status ko'rsatkichi, ustun profillari (Ctrl+P), Excel import profillari.
