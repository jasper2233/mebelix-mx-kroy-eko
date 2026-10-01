# K. Boshqa operatsiyalar: CL, O, SP, GR, LB (va CN)

Hammasida umumiy: «Сохранить текущие параметры для использования по умолчанию», «?» yordam,
«Детали» tabi — shu operatsiya ishlatilgan detallar ro'yxati (faqat o'qish, Ctrl+Space — xossalar,
Home/↑/↓/End navigatsiya).

## K1. CL — Погонажный раскрой (chiziqli kroy: profil, planka, reyka)

**Параметры материала**: Ширина, Толщина (polosa kesimi).
**Параметры раскроя**: Толщина пилы · Торцовка (polosa boshidan) + «Минимальный отступ в конце» (standart = torsovka) ·
Высота пакета · Кратность (= paket / qalinlik, o'qish) · Процент заполнения для кратности.
Foydali uzunlik = `L − (torsovka + propil) − (otstup + propil)`; misol 1600 − (20+10)·2 = **1540**.
**Отход**: Мин. размер отхода · Длина делового отхода (shundan uzun — delovoy, sarfga kirmaydi) · Торцовка отходов.
**Стоимость**: Цена материала (1 m yoki 1 polosa — «Расчет стоимости по полосам» ga ko'ra) ·
Расчетный процент заполнения → `sarf = detallar uzunligi × (2 − %/100)` · Количество материала = sarf − delovoy ·
«Расчет стоимости операции по»: длине реза с торцовкой / без торцовки / по длине материала / по длине деталей ·
Цена операции · Стоимость операции. Yaxlitlash: к целому, по длине 1/2, 1/3, 1/4.
**Детали**: `Д-na | Кол | ОВ | ОН | ОЛ | ОП | Наименование | ОК | ИК | Ост` (en yo'q).
Bufer tartibi: `Д-на, Кол, ОВ, ОН, ОЛ, ОП, Наименование`.
**Полосы и отходы** jadvali — CS «Листы и остатки» kabi (polosa/qoldiq/delovoy).
**Раскрой**: kartalar (har polosa), status `№ S C Cp LT F`, buyruqlar T/P/W.
Reference: `services/cl_optimizer.py` (FFD + takrorlash), `calc.run_linear`, `calc.cl_cost`.

## K2. O — Комплектация и другие действия

Murakkab hisob talab qilmaydigan amallar: furnitura komplektatsiyasi, transport, o'rnatish, qadoqlash,
maxsus ko'rsatmalar.
**Параметры**: Владелец (loyiha yoki mahsulot — mahsulot bo'lsa miqdor va narx × mahsulot soni) ·
Стоимость материала (jadval yig'indisi) · Стоимость операции (ish) · Стоимость (jami) · Описание.
**Материалы** jadvali: `Код | Наименование | Ед.И | Кол | Цена | Стоимость (= Кол × Цена)`; Ctrl+V tartibi
`Код, Наименование, Ед.И, Кол, Цена`. Bazis-Mebelshik importida «комплектующие» shu yerga tushadi.

## K3. SP — Обработка поверхности (sirt: bo'yash, laklash, plyonka)

Параметры: Учитывать материал · Процент отхода · Длина остатка по краям · Режим размеров (pilniy / zagotovka) ·
Цена за 1 м². Detalda: «Лицевая сторона» va «Обратная сторона» uchun SP operatsiyasi tanlanadi.
Hisob: `yuza = (L + 2·ortiqcha) × (W + 2·ortiqcha) × tomonlar × ОК`, material = yuza × (1 + chiqindi%),
narx = yuza × narx_m². Reference: `calc.surface_usage`.

## K4. GR — Пазование

Параметры: Ширина (W), Глубина (D), Отступ (O) chetdan, «Отступ включительно», Толщина пилы
(o'tishlar = ⌈W / arra⌉), Цена метра паза → Стоимость = narx × Длина пазования.
Detalda 4 tomon (Сверху/Снизу — uzunlik bo'yicha, Слева/Справа — en bo'yicha) + tomon (lits/orqa) katakchasi.
**Детали**: `Товар | Длина | ПВ | ПН | Ширина | ПЛ | ПП | Кол-во | Д-на паза | Наименование`.
Detal nomiga `=` belgisi qo'shiladi. Reference: `calc.groove_usage`.

## K5. LB — Этикетки

`H_REPORTS_LABELS.md §H5`. Birinchi bosqich: detal va qoldiq etiketkasi (standart shablon: loyiha №, mahsulot,
detal nomi, o'lcham, kromka belgilar sxemasi, material, shtrixkod), brauzerdan chop (etiketka printeri CSS @page).

## K6. CN — Нестинговый раскрой

GibLab'da test holatida. MebeliX: keyingi bosqich (CNC nesting — egri shakllar). Hozir UI da ko'rsatilmaydi.

## K7. Bosqichlar ustuvorligi

1. CS, EL, GR, O (xodimlar hozir ishlatadi: CS, EL, XNC) — birinchi.
2. XNC (saqlash/narx/chizma), LB (standart etiketka).
3. CL, SP, XNC redaktor, postprotsessorlar, CN.
