# -*- coding: utf-8 -*-
"""(CN) Нестинговый раскрой va CNE — interfeys matnlari (W16). i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan).
Rus yorliqlari — xodimlar odatlangan atamalar; uz — to'liq o'zbekcha (lotin). Yordam matnlari (`phelp.cn_*`) — o'z so'zlarimiz."""

# ── operatsiyalar jadvali ──
a("ops.add_cn", "Добавить: (CN) Нестинговый раскрой", "Qo'shish: (CN) Nesting kroy")
a("ops.default.CN", "Нестинг {{n}} (ЛДСП 16)", "Nesting {{n}} (LDSP 16)")

# ── panel: yorliqlar ──
a("cn.tab.params", "Параметры", "Parametrlar")
a("cn.tab.parts", "Детали", "Detallar")
a("cn.tab.sheets", "Листы и остатки", "Listlar va qoldiqlar")
a("cn.tab.cut", "Раскрой", "Kroy")
a("cn.save_default", "Сохранить текущие параметры для использования по умолчанию", "Joriy parametrlarni standart sifatida saqlash")
a("cn.apply_default", "Применить стандартные параметры (кроме толщины и цены)", "Standart parametrlarni qo'llash (qalinlik va narxdan tashqari)")
a("cn.defaults_saved", "Параметры нестингового раскроя сохранены как стандартные", "Nesting kroy parametrlari standart sifatida saqlandi")
a("cn.params_invalidate_q", "Изменить параметр? Текущий раскрой будет удалён.", "Parametr o'zgartirilsinmi? Joriy kroy o'chiriladi.")

# ── «Параметры» ──
a("cn.p.material", "Параметры материала", "Material parametrlari")
a("cn.p.thickness", "Толщина", "Qalinligi")
a("cn.p.thickness_hint", "Толщина листа — для кратности и поиска остатков на складе", "List qalinligi — kratnost va ombordan qoldiq qidirish uchun")
a("cn.p.cost", "Стоимость", "Narx")
a("cn.p.price", "Цена материала", "Material narxi")
a("cn.p.price_hint", "«По листам» ✓ — цена одного листа; ☐ — цена одного м²", "«Listlar bo'yicha» ✓ — bitta list narxi; ☐ — 1 m² narxi")
a("cn.p.per_sheet", "за лист", "1 list uchun")
a("cn.p.per_m2", "за м²", "1 m² uchun")
a("cn.p.est_fill", "Расчетный процент заполнения", "Hisobiy to'ldirish foizi")
a("cn.p.est_fill_hint", "Для предварительного расчёта до раскроя: расход = площадь деталей × (2 − процент / 100)", "Kroydan oldingi taxmin: sarf = detallar maydoni × (2 − foiz / 100)")
a("cn.p.material_qty", "Количество материала", "Material miqdori")
a("cn.p.material_qty_hint", "После раскроя: площадь использованных листов минус деловые остатки", "Kroydan keyin: ishlatilgan listlar maydoni minus deloviy qoldiqlar")
a("cn.p.sheets_qty", "Количество листов", "Listlar soni")
a("cn.p.sheets_qty_hint", "Новые листы (остатки со склада считаются отдельно); с учётом округления", "Yangi listlar (ombor qoldiqlari alohida); yaxlitlash hisobga olingan")
a("cn.p.cost_by_sheets", "Расчет стоимости по листам", "Narxni listlar bo'yicha hisoblash")
a("cn.p.rounding", "Округление — Листы", "Yaxlitlash — listlar")
a("cn.p.cost_material", "Стоимость материала", "Material qiymati")
a("cn.p.op_base", "Расчет стоимости операции по", "Operatsiya narxini hisoblash asosi")
a("cn.opbase.0", "Длине реза (контуры деталей)", "Kesim uzunligi (detal konturlari)")
a("cn.opbase.1", "Периметру деталей (внешний контур)", "Detallar perimetri (tashqi kontur)")
a("cn.opbase.2", "Площади деталей", "Detallar maydoni")
a("cn.opbase.3", "Площади материала", "Material maydoni")
a("cn.p.op_price", "Цена операции", "Operatsiya narxi")
a("cn.p.op_price_hint", "Цена за единицу выбранного основания (метр реза / м²)", "Tanlangan asos birligiga narx (kesim metri / m²)")
a("cn.p.cut_length", "Длина реза", "Kesim uzunligi")
a("cn.p.cut_length_hint", "Сумма длин всех контуров (внешних и внутренних вырезов); до раскроя — оценка по периметрам", "Barcha konturlar (tashqi va ichki kesimlar) uzunligi yig'indisi; kroydan oldin — perimetrlar bo'yicha taxmin")
a("cn.p.cost_op", "Стоимость операции", "Operatsiya qiymati")
a("cn.p.remnant", "Остаток", "Qoldiq")
a("cn.p.rem1", "Мин. размер остатка первой стороны", "Qoldiq 1-tomoni min. o'lchami")
a("cn.p.rem_hint", "Остаток — прямоугольник без деталей (в том числе внутри вырезов деталей), одна сторона не меньше первого значения, вторая — не меньше второго", "Qoldiq — detalsiz to'rtburchak (detal ichki kesimlari ham), bir tomoni birinchi qiymatdan, ikkinchisi ikkinchi qiymatdan kam emas")
a("cn.p.rem2", "Мин. размер остатка второй стороны", "Qoldiq 2-tomoni min. o'lchami")
a("cn.p.rem_area", "Площадь делового остатка", "Deloviy qoldiq maydoni")
a("cn.p.rem_area_hint", "Остаток не меньше этой площади — деловой: не входит в расход материала, его можно записать на склад", "Bu maydondan kam bo'lmagan qoldiq — deloviy: material sarfiga kirmaydi, omborga yozilishi mumkin")
a("cn.p.limits", "Ограничения раскроя", "Kroy cheklovlari")
a("cn.p.min_part", "Мин. размер детали", "Min. detal o'lchami")
a("cn.p.min_part_hint", "Деталь, у которой меньшая сторона меньше этого значения, в раскрой не входит (0 — без ограничения)", "Kichik tomoni bu qiymatdan kam detal kroyga kirmaydi (0 — cheklov yo'q)")
a("cn.p.tool", "Инструмент и расстояния", "Asbob va masofalar")
a("cn.p.tool_d", "Диаметр инструмента", "Asbob diametri")
a("cn.p.tool_d_hint", "Диаметр фрезы: между двумя деталями должна пройти фреза", "Frezer diametri: ikki detal orasidan freza o'tishi kerak")
a("cn.p.tool_offset", "Смещение инструмента (оффсет)", "Asbob siljishi (ofset)")
a("cn.p.tool_offset_hint", "Расстояние от центра фрезы до контура детали. Пусто — половина диаметра", "Freza markazidan detal konturigacha masofa. Bo'sh — diametrning yarmi")
a("cn.p.as_half", "D/2", "D/2")
a("cn.p.part_gap", "Доп. расстояние между деталями", "Detallar orasidagi qo'shimcha masofa")
a("cn.p.part_gap_hint", "Добавляется к расстоянию, которое занимает фреза", "Freza egallagan masofaga qo'shiladi")
a("cn.p.min_gap", "Мин. расстояние между деталями", "Detallar orasidagi min. masofa")
a("cn.p.min_gap_hint", "Вычисляется: max(диаметр, 2 × оффсет) + доп. расстояние. В расчёте к нему добавляется запас на аппроксимацию дуг ({{arc}} мм)", "Hisoblanadi: max(diametr, 2 × ofset) + qo'shimcha masofa. Hisobda unga yoylarni yaqinlashtirish zaxirasi ({{arc}} mm) qo'shiladi")
a("cn.p.margin", "Отступ от края", "Chetdan otstup")
a("cn.p.margin_hint", "Минимальное расстояние от контура детали до края листа", "Detal konturidan list chetigacha minimal masofa")
a("cn.p.arc_tol", "Точность дуг (допуск)", "Yoylar aniqligi (dopusk)")
a("cn.p.arc_tol_hint", "Максимальная ошибка замены дуги ломаной, мм. Меньше — точнее, но дольше расчёт", "Yoyni siniq chiziq bilan almashtirishning maksimal xatosi, mm. Kichik — aniqroq, lekin hisob uzoqroq")
a("cn.p.rotation", "Повороты и текстура", "Burilishlar va tekstura")
a("cn.p.rot90", "Повороты 0 / 90 / 180 / 270°", "Burilishlar 0 / 90 / 180 / 270°")
a("cn.p.rot90_hint", "Выключено — детали раскладываются только в исходной ориентации (0°)", "O'chirilgan — detallar faqat dastlabki yo'nalishda (0°) joylanadi")
a("cn.p.rot_step", "Шаг свободного поворота", "Erkin burilish qadami")
a("cn.p.rot_step_hint", "Дополнительные углы с этим шагом (0 — выключено). Деталь с текстурой допускает только 0° и 180°", "Shu qadamli qo'shimcha burchaklar (0 — o'chiq). Teksturali detal faqat 0° va 180° ga ruxsat beradi")
a("cn.p.deg", "град.", "grad.")
a("cn.p.use_grain", "Учет текстуры", "Teksturani hisobga olish")
a("cn.p.use_grain_hint", "Детали с Ткт ✓ не поворачиваются на 90° (только 0° и 180°)", "Tkt ✓ detallar 90° ga burilmaydi (faqat 0° va 180°)")
a("cn.p.use_xnc", "Контуры из XNC", "XNC konturlari")
a("cn.p.use_xnc_hint", "Брать контур детали из связанной XNC-программы; выключено — деталь прямоугольная (Д × Ш)", "Detal konturini bog'langan XNC dasturidan olish; o'chirilgan — detal to'rtburchak (Uz × En)")
a("cn.p.label", "Место под этикетку", "Etiketka uchun joy")
a("cn.p.label_w", "Этикетка: ширина", "Etiketka: eni")
a("cn.p.label_h", "Этикетка: высота", "Etiketka: balandligi")
a("cn.p.label_hint", "Размер этикетки: на детали ищется место без обработки (показывается пунктиром). 0 — не искать", "Etiketka o'lchami: detalda ishlovsiz joy qidiriladi (punktir bilan ko'rsatiladi). 0 — qidirilmaydi")
a("cn.p.prefs", "Оптимизация", "Optimizatsiya")
a("cn.p.quality", "Качество раскроя", "Kroy sifati")
a("cn.p.quality_hint", "Быстро — минимум времени; Стандарт — сбалансированно; Максимум — дольше ищет лучшее размещение", "Tez — minimal vaqt; Standart — muvozanatli; Maksimal — eng yaxshi joylashuvni uzoqroq qidiradi")
a("cn.p.sort_mode", "Сортировка деталей при раскрое", "Kroyda detallarni saralash")
a("cn.p.sort_mode_hint", "Авто — программа сама выбирает порядок; По списку деталей — порядок изменяется кнопкой «Сортировка» на вкладке «Детали»", "Avto — dastur tartibni o'zi tanlaydi; Detallar ro'yxati bo'yicha — tartib «Detallar» tabidagi «Saralash» tugmasi bilan o'zgaradi")
a("cn.sort.auto", "Авто", "Avto")
a("cn.sort.list", "По списку деталей", "Detallar ro'yxati bo'yicha")
a("cn.p.time_limit", "Предел времени расчёта", "Hisob vaqti chegarasi")
a("cn.p.time_limit_hint", "0 — стандартное для выбранного качества. По истечении времени берётся лучшее найденное размещение", "0 — tanlangan sifatga standart. Vaqt tugasa topilgan eng yaxshi joylashuv olinadi")
a("cn.p.sec", "с", "s")
a("cn.p.note", "Раскрой нестингом: контуры деталей плотно размещаются на листе; допускаются повороты. Детали раскраиваются фрезой, а не пилой.", "Nesting kroy: detal konturlari listga zich joylanadi; burilishlarga ruxsat. Detallar arra bilan emas, freza bilan kesiladi.")

# ── «Детали» ──
a("cn.xnc_contour", "XNC: контур детали (внешний контур и вырезы)", "XNC: detal konturi (tashqi kontur va kesimlar)")
a("cn.col.shape", "Форма", "Shakl")
a("cn.col.shape_hint", "Прямоугольник или контур из XNC-программы; число внутренних вырезов", "To'rtburchak yoki XNC dasturidagi kontur; ichki kesimlar soni")
a("cn.shape.rect", "Прямоугольник", "To'rtburchak")
a("cn.shape.contour", "Контур", "Kontur")
a("cn.shape.holes", "{{n}} вн. выр.", "{{n}} ichki kesim")
a("cn.shape.title", "Форма детали", "Detal shakli")
a("cn.shape.pick", "Выберите деталь в таблице", "Jadvaldan detalni tanlang")
a("cn.shape.none", "Форма не определена для этой детали (не входит в раскрой)", "Bu detal uchun shakl aniqlanmadi (kroyga kirmaydi)")
a("cn.shape.bbox", "Габарит", "Gabarit")
a("cn.shape.perimeter", "Периметр", "Perimetr")
a("cn.shape.label_ok", "Место под этикетку найдено (пунктир)", "Etiketka uchun joy topildi (punktir)")
a("cn.shape.label_no", "Место под этикетку не найдено: вся поверхность занята обработкой или мала", "Etiketka uchun joy topilmadi: butun sirt ishlov bilan band yoki kichik")
a("cn.parts.skipped", "Не войдут в раскрой: {{n}}", "Kroyga kirmaydi: {{n}}")
a("cn.parts.skipped_hint", "Детали с неверным размером или меньше минимального ({{mm}} мм)", "O'lchami noto'g'ri yoki minimaldan ({{mm}} mm) kichik detallar")

# ── «Листы и остатки» ──
a("cn.sheets.hint", "Кол-во = 10000 — без ограничения. Остатки со склада раскраиваются в первую очередь; порядок строк = порядок использования. Остаток «Д5⊂3» — внутри выреза детали 3.",
  "Soni = 10000 — cheklanmagan. Ombor qoldiqlari birinchi navbatda kroy qilinadi; qatorlar tartibi = ishlatish tartibi. «Д5⊂3» qoldiq — 3-detalning ichki kesimida.")
a("cn.sheets.in_part_hint", "⊂ — остаток внутри выреза детали (в скобках номер детали)", "⊂ — qoldiq detal kesimi ichida (detal raqami ko'rsatilgan)")

# ── «Раскрой» ──
a("cn.cut.done", "Раскрой: {{n}} лист(ов), F {{fill}}% ({{s}} с)", "Kroy: {{n}} list, F {{fill}}% ({{s}} s)")
a("cn.cut.cancelled", "Раскрой остановлен", "Kroy to'xtatildi")
a("cn.cut.failed", "Ошибка раскроя", "Kroyda xato")
a("cn.cut.elapsed", "{{s}} с", "{{s}} s")
a("cn.cut.stop", "Остановить", "To'xtatish")
a("cn.cut.empty_hint", "Нажмите «Раскроить» — контуры деталей будут плотно размещены на листах.", "«Kroy qilish» ni bosing — detal konturlari listlarga zich joylanadi.")
a("cn.cut.label_spots", "Показать места под этикетки", "Etiketka o'rinlarini ko'rsatish")
a("cn.cut.map_parts", "Детали карты", "Karta detallari")
a("cn.cut.size", "Габарит", "Gabarit")
a("cn.cut.rem_no", "Остаток", "Qoldiq")
a("cn.cut.rem_where", "Где", "Qayerda")
a("cn.cut.in_part", "в детали {{uid}}", "{{uid}}-detal ichida")
a("cn.ind.num", "Номер карты / всего", "Karta raqami / jami")
a("cn.ind.S", "Длина / ширина листа", "List uzunligi / eni")
a("cn.ind.C", "Количество листов на карте / всего", "Kartadagi listlar soni / jami")
a("cn.ind.Cp", "Деталей на карте / всего", "Kartadagi detallar / jami")
a("cn.ind.LT", "Длина реза, м (контуры деталей): карта / всего", "Kesim uzunligi, m (detal konturlari): karta / jami")
a("cn.ind.F", "Заполнение, % (площадь деталей / площадь листа)", "To'ldirish, % (detallar maydoni / list maydoni)")
a("cn.ind.R", "Отход, %: карта / всего", "Otxod, %: karta / jami")
a("cn.ind.CT", "Количество контуров (резов): карта / всего", "Konturlar (kesimlar) soni: karta / jami")
a("cn.ind.AP", "Площадь деталей, м²: карта / всего", "Detallar maydoni, m²: karta / jami")
a("cn.ind.AM", "Площадь листов, м²: карта / всего", "Listlar maydoni, m²: karta / jami")
a("cn.ind.AW", "Площадь деловых остатков, м²: карта / всего", "Deloviy qoldiqlar maydoni, m²: karta / jami")

# ── CNE ──
a("cn.ed.title", "Редактирование нестингового раскроя", "Nesting kroyni tahrirlash")
a("cn.ed.select_first", "Выделите деталь на карте", "Kartada detalni tanlang")
a("cn.ed.select_part", "Выберите деталь в таблице слева", "Chapdagi jadvaldan detalni tanlang")
a("cn.ed.size_hint", "Габарит детали (с учётом поворота — на карте)", "Detal gabariti (burilish xaritada hisobga olinadi)")
a("cn.ed.list_hint", "Выберите деталь и щёлкните по свободному месту карты (Alt — с поворотом на 90°); двойной щелчок — автоматически", "Detalni tanlab, xaritaning bo'sh joyini bosing (Alt — 90° burib); ikki marta bosish — avtomatik")
a("cn.ed.h_left", "выделить / перетащить деталь", "detalni tanlash / sudrab ko'chirish")
a("cn.ed.h_shift", "выделить несколько", "bir nechtasini tanlash")
a("cn.ed.h_right", "убрать деталь", "detalni olib tashlash")
a("cn.ed.h_arrows", "сдвиг на 1 / 10 мм", "1 / 10 mm siljitish")
a("cn.ed.h_slide", "прижать к краю / соседней детали", "chetga / qo'shni detalga yopishtirish")
a("cn.ed.h_rotate", "поворот на 90°", "90° burish")
a("cn.ed.h_snap", "прижать по точке", "nuqta bo'yicha yopishtirish")
a("cn.ed.slide_left", "Прижать влево", "Chapga yopishtirish")
a("cn.ed.slide_right", "Прижать вправо", "O'ngga yopishtirish")
a("cn.ed.slide_up", "Прижать вверх", "Yuqoriga yopishtirish")
a("cn.ed.slide_down", "Прижать вниз", "Pastga yopishtirish")
a("cn.ed.snap_mode", "Прижать по точке: точка детали → целевая точка", "Nuqta bo'yicha yopishtirish: detal nuqtasi → nishon nuqta")
a("cn.ed.snap_select", "Сначала выделите деталь", "Avval detalni tanlang")
a("cn.ed.snap_from", "Укажите точку на выбранной детали (синие точки)", "Tanlangan detaldagi nuqtani ko'rsating (ko'k nuqtalar)")
a("cn.ed.snap_to", "Укажите целевую точку: угол другой детали или рабочей зоны (зелёные точки)", "Nishon nuqtani ko'rsating: boshqa detal yoki ish zonasi burchagi (yashil nuqtalar)")
a("cn.ed.rot_cw", "Повернуть на 90° по часовой", "Soat mili bo'yicha 90° burish")
a("cn.ed.rot_ccw", "Повернуть на 90° против часовой", "Soat miliga qarshi 90° burish")
a("cn.ed.rot_angle", "Повернуть на угол…", "Burchakka burish…")
a("cn.ed.angle_abs", "Угол детали, градусы", "Detal burchagi, gradus")
a("cn.ed.angle_rel", "Повернуть выделенные на угол, градусы", "Tanlanganlarni burchakka burish, gradus")
a("cn.ed.angle_hint", "По часовой стрелке. Деталь с текстурой допускает только 0° и 180°", "Soat mili bo'yicha. Teksturali detal faqat 0° va 180° ga ruxsat beradi")
a("cn.ed.angle_bad", "Введите число", "Son kiriting")
a("cn.ed.renest", "Перераскроить эту карту (детали карты и неразмещённые — заново)", "Shu kartani qayta joylash (karta detallari va joylanmaganlar — qaytadan)")
a("cn.ed.renest_q", "Перераспределить детали на этой карте?", "Shu kartadagi detallar qayta joylansinmi?")
a("cn.ed.renest_text", "Детали карты и неразмещённые детали будут размещены на этом листе заново. Если результат хуже — действие отклоняется.", "Karta detallari va joylanmaganlar shu listga qaytadan joylanadi. Natija yomonroq bo'lsa — amal rad etiladi.")
a("cn.ed.copies_hint", "Количество листов: сколько одинаковых листов режется по этой карте", "Listlar soni: shu karta bo'yicha nechta bir xil list kesiladi")
a("cn.ed.conflict", "Результат изменён в другом окне — откройте редактор заново", "Natija boshqa oynada o'zgartirilgan — muharrirni qaytadan oching")

a("help.hk.cn_editor_keys", "Редактор нестинга (CNE): сдвиг ← ↑ → ↓ (Shift — 10 мм), прижать Ctrl+← ↑ → ↓, поворот R / Shift+R, прижать по точке S",
  "Nesting muharriri (CNE): siljitish ← ↑ → ↓ (Shift — 10 mm), yopishtirish Ctrl+← ↑ → ↓, burish R / Shift+R, nuqta bo'yicha yopishtirish S")

# ── «Печать отчета» ──
a("print.sec.cn", "(CN) Нестинговый раскрой", "(CN) Nesting kroy")
a("print.f.cn_params", "Печать параметров", "Parametrlarni chop etish")
a("print.f.cn_parts", "Печать деталей", "Detallarni chop etish")
a("print.f.cn_unplaced", "Печать невместившихся деталей", "Sig'magan detallarni chop etish")
a("print.f.cn_sheets", "Печать листов", "Listlarni chop etish")
a("print.f.cn_remnants", "Печать остатков", "Qoldiqlarni chop etish")
a("print.f.cn_maps", "Печать карт раскроев", "Kroy kartalarini chop etish")

# ── yordam: parametr haqida (F1 / «?») ──
_H = {
    "cn_thickness": ("Толщина", "Qalinligi",
                     "Толщина листа. Нужна для кратности (сколько листов режется за один проход) и для подбора остатков со склада той же толщины.",
                     "List qalinligi. Kratnost (bir o'tishda nechta list kesiladi) va ombordan shu qalinlikdagi qoldiqlarni tanlash uchun kerak."),
    "cn_price": ("Цена материала", "Material narxi",
                 "«По листам» ✓ — цена одного листа; выключено — цена одного м² (стоимость = м² × цена). Остатки со склада считаются по цене за м².",
                 "«Listlar bo'yicha» ✓ — bitta list narxi; o'chirilgan — 1 m² narxi (qiymat = m² × narx). Ombor qoldiqlari 1 m² narxida hisoblanadi."),
    "cn_est_fill": ("Расчетный процент заполнения", "Hisobiy to'ldirish foizi",
                    "Нужен только до раскроя: расход ≈ площадь деталей × (2 − процент/100). После раскроя берутся реальные площади листов.",
                    "Faqat kroydan oldin kerak: sarf ≈ detallar maydoni × (2 − foiz/100). Kroydan keyin listlarning haqiqiy maydoni olinadi."),
    "cn_material_qty": ("Количество материала", "Material miqdori",
                        "Расход в м². После раскроя: площадь использованных новых листов минус деловые остатки (они уходят на склад и в расход не входят). До раскроя — оценка со знаком «≈».",
                        "Sarf m² da. Kroydan keyin: ishlatilgan yangi listlar maydoni minus deloviy qoldiqlar (ular omborga ketadi, sarfga kirmaydi). Kroydan oldin — «≈» belgili taxmin."),
    "cn_sheets_qty": ("Количество листов", "Listlar soni",
                      "Сколько новых листов уйдёт в раскрой (с учётом выбранного округления). Остатки со склада учитываются отдельно.",
                      "Kroyga nechta yangi list ketadi (tanlangan yaxlitlash hisobga olingan). Ombor qoldiqlari alohida hisoblanadi."),
    "cn_cost_by_sheets": ("Расчет стоимости по листам", "Narxni listlar bo'yicha hisoblash",
                          "Включено — стоимость материала = количество листов × цена листа; выключено — м² × цена м².",
                          "Yoqilgan — material qiymati = listlar soni × list narxi; o'chirilgan — m² × 1 m² narxi."),
    "cn_rounding": ("Округление — Листы", "Yaxlitlash — listlar",
                    "Как считать последний неполный лист: до целого или до доли площади. Работает вместе с расчётом по листам.",
                    "Oxirgi to'lmagan listni qanday sanash: butungacha yoki maydon ulushigacha. Listlar bo'yicha hisob bilan birga ishlaydi."),
    "cn_cost_material": ("Стоимость материала", "Material qiymati",
                         "Цена × количество материала (до раскроя — оценка). Только чтение.",
                         "Narx × material miqdori (kroydan oldin — taxmin). Faqat o'qish."),
    "cn_op_base": ("Расчет стоимости операции по", "Operatsiya narxini hisoblash asosi",
                   "Что умножается на цену операции: длина реза (сумма длин всех контуров), периметр деталей (внешние контуры), площадь деталей или площадь материала.",
                   "Operatsiya narxiga nima ko'paytiriladi: kesim uzunligi (barcha konturlar uzunligi yig'indisi), detallar perimetri (tashqi konturlar), detallar maydoni yoki material maydoni."),
    "cn_op_price": ("Цена операции", "Operatsiya narxi",
                    "Цена за единицу выбранного основания (метр или м²). Стоимость операции = основание × цена.",
                    "Tanlangan asos birligiga (metr yoki m²) narx. Operatsiya qiymati = asos × narx."),
    "cn_cut_length": ("Длина реза", "Kesim uzunligi",
                      "Сумма длин всех контуров: внешних и внутренних вырезов деталей. До раскроя — по периметрам деталей. Только чтение.",
                      "Barcha konturlar uzunligi yig'indisi: detallarning tashqi va ichki kesimlari. Kroydan oldin — detallar perimetrlari bo'yicha. Faqat o'qish."),
    "cn_cost_op": ("Стоимость операции", "Operatsiya qiymati",
                   "Основание × цена операции. Только чтение.", "Asos × operatsiya narxi. Faqat o'qish."),
    "cn_rem1": ("Мин. размер остатка первой стороны", "Qoldiq 1-tomoni min. o'lchami",
                "Свободный прямоугольник без деталей (в том числе внутри выреза детали) считается остатком, если одна сторона не меньше первого значения, а вторая — не меньше второго.",
                "Detalsiz bo'sh to'rtburchak (detal ichki kesimi ham) qoldiq hisoblanadi, agar bir tomoni birinchi qiymatdan, ikkinchisi ikkinchi qiymatdan kam bo'lmasa."),
    "cn_rem2": ("Мин. размер остатка второй стороны", "Qoldiq 2-tomoni min. o'lchami",
                "См. «Мин. размер остатка первой стороны»: остаток должен быть не меньше обоих значений.",
                "«Qoldiq 1-tomoni min. o'lchami» ga qarang: qoldiq ikkala qiymatdan kam bo'lmasligi kerak."),
    "cn_rem_area": ("Площадь делового остатка", "Deloviy qoldiq maydoni",
                    "Остаток с площадью не меньше этого значения — деловой: не входит в расход материала и может быть записан на склад.",
                    "Maydoni bu qiymatdan kam bo'lmagan qoldiq — deloviy: material sarfiga kirmaydi va omborga yozilishi mumkin."),
    "cn_min_part": ("Мин. размер детали", "Min. detal o'lchami",
                    "Деталь, у которой меньшая сторона меньше этого значения, в раскрой не входит (появляется предупреждение). 0 — без ограничения.",
                    "Kichik tomoni bu qiymatdan kam detal kroyga kirmaydi (ogohlantirish chiqadi). 0 — cheklov yo'q."),
    "cn_tool_d": ("Диаметр инструмента", "Asbob diametri",
                  "Диаметр фрезы. Между контурами двух соседних деталей должна пройти фреза, поэтому расстояние не меньше диаметра.",
                  "Frezer diametri. Ikki qo'shni detal konturi orasidan freza o'tishi kerak, shuning uchun masofa diametrdan kam bo'lmaydi."),
    "cn_tool_offset": ("Смещение инструмента (оффсет)", "Asbob siljishi (ofset)",
                       "Расстояние от центра фрезы до контура детали. Пусто — половина диаметра. Если 2 × оффсет больше диаметра, расстояние между деталями определяется им.",
                       "Freza markazidan detal konturigacha masofa. Bo'sh — diametrning yarmi. 2 × ofset diametrdan katta bo'lsa, detallar orasidagi masofa shu bilan aniqlanadi."),
    "cn_part_gap": ("Доп. расстояние между деталями", "Detallar orasidagi qo'shimcha masofa",
                    "Дополнительный зазор между деталями сверх того, что занимает фреза (например, на перемычки или допуск).",
                    "Freza egallaganidan tashqari detallar orasidagi qo'shimcha oraliq (masalan, ko'prikcha yoki dopusk uchun)."),
    "cn_min_gap": ("Мин. расстояние между деталями", "Detallar orasidagi min. masofa",
                   "Вычисляется: max(диаметр, 2 × оффсет) + доп. расстояние. Раскрой и проверка результата требуют не меньшего расстояния между контурами (плюс малый запас на аппроксимацию дуг). Только чтение.",
                   "Hisoblanadi: max(diametr, 2 × ofset) + qo'shimcha masofa. Kroy va natijani tekshirish konturlar orasida kamida shu masofani talab qiladi (yoylarni yaqinlashtirish uchun kichik zaxira bilan). Faqat o'qish."),
    "cn_margin": ("Отступ от края", "Chetdan otstup",
                  "Минимальное расстояние от контура детали до края листа. Пунктиром на карте показана рабочая зона.",
                  "Detal konturidan list chetigacha minimal masofa. Xaritada punktir bilan ish zonasi ko'rsatilgan."),
    "cn_arc_tol": ("Точность дуг (допуск)", "Yoylar aniqligi (dopusk)",
                   "Дуги контура заменяются ломаной линией. Допуск — максимальное отклонение, мм. Меньше значение — точнее контур, но больше точек и дольше расчёт.",
                   "Kontur yoylari siniq chiziq bilan almashtiriladi. Dopusk — maksimal og'ish, mm. Kichik qiymat — kontur aniqroq, lekin nuqtalar ko'p va hisob uzoqroq."),
    "cn_rot90": ("Повороты 0 / 90 / 180 / 270°", "Burilishlar 0 / 90 / 180 / 270°",
                 "Разрешены повороты детали на 0°, 90°, 180°, 270°. Выключено — только исходная ориентация. Деталь с текстурой: только 0° и 180°.",
                 "Detalni 0°, 90°, 180°, 270° ga burishga ruxsat. O'chirilgan — faqat dastlabki yo'nalish. Teksturali detal: faqat 0° va 180°."),
    "cn_rot_step": ("Шаг свободного поворота", "Erkin burilish qadami",
                    "Дополнительные углы с заданным шагом в градусах (например, 15 → 15°, 30°, …). 0 — выключено. Больше углов — плотнее раскладка, но дольше расчёт.",
                    "Berilgan qadamli (gradus) qo'shimcha burchaklar (masalan, 15 → 15°, 30°, …). 0 — o'chiq. Burchaklar ko'p — joylashuv zichroq, lekin hisob uzoqroq."),
    "cn_use_grain": ("Учет текстуры", "Teksturani hisobga olish",
                     "Деталь с признаком «Ткт» не поворачивается на 90° и 270° — волокна идут вдоль листа (допустимы 0° и 180°).",
                     "«Tkt» belgili detal 90° va 270° ga burilmaydi — tolalar list bo'ylab ketadi (0° va 180° mumkin)."),
    "cn_use_xnc": ("Контуры из XNC", "XNC konturlari",
                   "Контур детали берётся из связанной XNC-программы: замкнутый внешний контур фрезы и замкнутые внутренние контуры (вырезы). Выключено — деталь считается прямоугольником Д × Ш.",
                   "Detal konturi bog'langan XNC dasturidan olinadi: frezaning yopiq tashqi konturi va yopiq ichki konturlar (kesimlar). O'chirilgan — detal Uz × En to'rtburchak hisoblanadi."),
    "cn_label": ("Место под этикетку", "Etiketka uchun joy",
                 "Размер этикетки. На каждой детали ищется свободное от обработки место этого размера (показывается пунктиром при включённом режиме). 0 — не искать.",
                 "Etiketka o'lchami. Har bir detalda ishlovdan bo'sh shu o'lchamdagi joy qidiriladi (rejim yoqilganda punktir bilan ko'rsatiladi). 0 — qidirilmaydi."),
    "cn_quality": ("Качество раскроя", "Kroy sifati",
                   "Быстро — минимум времени; Стандарт — сбалансированно; Максимум — дольше ищет лучшее размещение.",
                   "Tez — minimal vaqt; Standart — muvozanatli; Maksimal — eng yaxshi joylashuvni uzoqroq qidiradi."),
    "cn_sort_mode": ("Сортировка деталей при раскрое", "Kroyda detallarni saralash",
                     "Авто — программа сама выбирает порядок размещения деталей (обычно от крупных к мелким). По списку деталей — детали размещаются в том порядке, в каком они стоят на вкладке «Детали»; порядок меняется кнопкой «Сортировка».",
                     "Avto — dastur detallarni joylash tartibini o'zi tanlaydi (odatda kattadan kichikka). Detallar ro'yxati bo'yicha — detallar «Detallar» tabidagi tartibda joylanadi; tartib «Saralash» tugmasi bilan o'zgaradi."),
    "cn_time_limit": ("Предел времени расчёта", "Hisob vaqti chegarasi",
                      "Сколько секунд максимум ищется размещение. 0 — стандартное для качества (быстро 3 / стандарт 10 / максимум 40 с). По истечении берётся лучший найденный вариант.",
                      "Joylashuv eng ko'pi bilan necha soniya qidiriladi. 0 — sifatga standart (tez 3 / standart 10 / maksimal 40 s). Vaqt tugasa topilgan eng yaxshi variant olinadi."),
}
for _k, (_tru, _tuz, _hru, _huz) in _H.items():
    a(f"phelp_t.{_k}", _tru, _tuz)
    a(f"phelp.{_k}", _hru, _huz)
