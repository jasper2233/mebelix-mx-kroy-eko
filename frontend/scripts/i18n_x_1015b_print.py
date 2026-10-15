# -*- coding: utf-8 -*-
"""2026-10-15 (2-sessiya, §11) — «Печать отчета» sozlamalari oynalari: «Параметр | Значение» jadvallari, guruhlar, yangi
variantlar (zagolovok/talabnoma/statistika, kromka belgilari, ko'zgu rejimlari, XNC statistika ustunlari, kolontitul).
`a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi."""

# ── jadval ustunlari va oynalar ──
a("print.col.param", "Параметр", "Parametr"); a("print.col.value", "Значение", "Qiymat")
a("print.dlg.xnc", "Обработка", "Ishlov"); a("print.tab.stats", "Статистика", "Statistika"); a("print.tab.drawing", "Чертеж", "Chizma")
a("print.tab.parts", "Детали", "Detallar"); a("print.tab.general", "Общие", "Umumiy")
a("print.sec.xnc", "(XNC) Обработка", "(XNC) Ishlov")

# ── guruhlar ──
a("print.g.materials", "Материалы", "Materiallar"); a("print.g.warehouse", "Печать требования на склад", "Omborga talabnoma chop etish")
a("print.g.products", "Изделия", "Mahsulotlar"); a("print.g.operations", "Операции", "Operatsiyalar"); a("print.g.xnc", "Обработка", "Ishlov")
a("print.g.el_header", "Печатать в заголовке деталей", "Detallar sarlavhasida chop etish"); a("print.g.mirror", "Зеркало", "Ko'zgu")
a("print.g.part_marks", "Обозначение на детали", "Detaldagi belgilar"); a("print.g.remnant_marks", "Обозначение на остатке", "Qoldiqdagi belgilar")
a("print.g.num_style", "Стиль номера детали", "Detal raqami uslubi"); a("print.g.dim_style", "Стиль размеров", "O'lchamlar uslubi")
a("print.g.fill_style", "Стиль заливки", "To'ldirish uslubi"); a("print.g.barcode", "Штрихкод", "Shtrixkod")
a("print.g.extra", "Дополнительно (MebeliX)", "Qo'shimcha (MebeliX)"); a("print.g.origin", "Начало координат", "Koordinata boshi")

# ── qatorlar: umumiy ──
a("print.r.header_project", "Печать заголовка проекта", "Loyiha sarlavhasini chop etish")
a("print.r.materials_list", "Печать списка материалов", "Materiallar ro'yxatini chop etish")
a("print.r.materials_group", "Группировать материалы по коду", "Materiallarni kod bo'yicha guruhlash")
a("print.r.warehouse", "Печать требования на склад", "Omborga talabnomani chop etish")
a("print.r.warehouse_cut", "В требовании на склад печатать просто количество работы по резке", "Talabnomada faqat kesish ishi miqdorini chop etish")
a("print.r.warehouse_edge", "В требовании на склад печатать \"Длина кромки (работа)\"", "Talabnomada «Kromka uzunligi (ish)» ni chop etish")
a("print.r.products_list", "Печать списка изделий", "Mahsulotlar ro'yxatini chop etish")
a("print.r.products_single", "Печать списка изделий, если изделие одно", "Mahsulot bitta bo'lsa ham ro'yxatni chop etish")
a("print.r.operations_list", "Печать списка операций", "Operatsiyalar ro'yxatini chop etish")
a("print.r.operations_single", "Печать списка операций, если операция одна", "Operatsiya bitta bo'lsa ham ro'yxatni chop etish")
a("print.r.operations", "Печать операций", "Operatsiyalarni chop etish")
a("print.r.xnc_stats", "Печатать статистику по XNC операциям", "XNC operatsiyalari statistikasini chop etish")
a("print.r.print_header", "Печать заголовка", "Sarlavhani chop etish"); a("print.r.print_ops", "Печать операций", "Operatsiyalarni chop etish")
a("print.r.print_materials", "Печать материалов", "Materiallarni chop etish"); a("print.r.print_parts", "Печать деталей", "Detallarni chop etish")
a("print.r.print_warehouse", "Печать требования на склад", "Omborga talabnomani chop etish")
a("print.r.print_stats", "Печать статистики", "Statistikani chop etish")
a("print.r.print_unplaced", "Печать невместившихся деталей", "Sig'magan detallarni chop etish")
a("print.r.print_sheets", "Печать листов", "Listlarni chop etish"); a("print.r.print_remnants", "Печать остатков", "Qoldiqlarni chop etish")
a("print.r.print_maps", "Печать карт раскроев", "Kroy kartalarini chop etish"); a("print.r.print_strips", "Печать полос", "Polosalarni chop etish")
a("print.r.print_params", "Печать параметров", "Parametrlarni chop etish"); a("print.r.print_drawings", "Печать чертежей", "Chizmalarni chop etish")
a("print.r.el_work", "Длина кромкования (работа)", "Kromkalash uzunligi (ish)"); a("print.r.el_material", "Длина материала", "Material uzunligi")

# ── sahifa chegaralari ──
a("print.r.mirror_margins", "Зеркальные поля", "Ko'zgu chegaralar"); a("print.r.footer_pos", "Позиция колонтитула", "Kolontitul o'rni")
a("print.fp.bottom", "Внизу", "Pastda"); a("print.fp.top", "Вверху", "Yuqorida"); a("print.fp.none", "Нет", "Yo'q")

# ── (CS) Детали ──
a("print.r.group_products", "Группировать по изделиям", "Mahsulotlar bo'yicha guruhlash")
a("print.r.size_mode", "Режим вывода размеров деталей", "Detal o'lchamlarini chiqarish rejimi")
a("print.r.edge_highlight", "Выделять в колонке кромкования", "Kromka ustunida ajratib ko'rsatish")
a("print.r.edge_symbols", "Печать символов кромкования и вывести легенду", "Kromka belgilarini chop etish va legenda chiqarish")
a("print.r.parts_form", "Форма печати деталей", "Detallar chop shakli")
a("print.form.merged", "С объединенными по одному размеру кромками", "Bir o'lcham bo'yicha birlashtirilgan kromkalar bilan")
a("print.form.sides", "Кромки по каждой стороне отдельно", "Har tomon kromkasi alohida")

# ── (CS) Карты кроя ──
a("print.r.map_layout", "Макет карт кроя", "Kroy kartalari maketi"); a("print.r.map_parts_list", "Печатать список деталей", "Detallar ro'yxatini chop etish")
a("print.r.mirror_h", "Горизонтально", "Gorizontal"); a("print.r.mirror_v", "Вертикально", "Vertikal")
a("print.mir.no", "Нет", "Yo'q"); a("print.mir.yes", "Да", "Ha")
a("print.mir.cuts_v", "Начальное направление резов: По вертикали", "Dastlabki kesimlar yo'nalishi: Vertikal")
a("print.mir.cuts_h", "Начальное направление резов: По горизонтали", "Dastlabki kesimlar yo'nalishi: Gorizontal")
a("print.r.part_number", "Печать номера детали", "Detal raqamini chop etish"); a("print.r.part_name", "Печать наименования детали", "Detal nomini chop etish")
a("print.r.part_marks", "Печать маркеров обработки", "Ishlov belgilarini chop etish")
a("print.r.part_expr", "Печать значения выражения", "Ifoda qiymatini chop etish")
a("print.r.part_expr_hint", "например: name + \" / \" + qty", "masalan: name + \" / \" + qty")
a("print.r.edges", "Печать кромок", "Kromkalarni chop etish"); a("print.r.edge_marker", "Печать маркера кромок", "Kromka markerini chop etish")
a("print.em.lines", "Линии", "Chiziqlar"); a("print.em.symbols", "Символы", "Belgilar"); a("print.em.both", "Линии и символы", "Chiziqlar va belgilar")
a("print.r.edge_line_style", "Стиль линий маркера кромок", "Kromka markeri chiziq uslubi")
a("print.ls.solid", "Сплошная", "Yaxlit"); a("print.ls.dashed", "Штриховая", "Shtrix"); a("print.ls.dotted", "Пунктирная", "Nuqtali")
a("print.r.machining", "Печать обработки на деталях", "Detallarda ishlovni chop etish")
a("print.r.remnant_number", "Печать номера остатка", "Qoldiq raqamini chop etish")
a("print.r.font_size", "Размер шрифта", "Shrift o'lchami"); a("print.r.font_auto", "0 — авто", "0 — avto")
a("print.r.font_bold", "Жирный шрифт", "Qalin shrift"); a("print.r.font_rotate", "Разворачивать шрифты", "Shriftlarni burish")
a("print.r.fill_part", "Заливка панели", "Panel to'ldirishi"); a("print.r.fill_waste", "Заливка отходов", "Chiqindi to'ldirishi")
a("print.r.barcode_print", "Печатать", "Chop etish"); a("print.r.barcode_type", "Тип", "Turi"); a("print.r.barcode_data", "Данные", "Ma'lumot")
a("print.r.commands_table", "Таблица команд у карт", "Kartalar yonida buyruqlar jadvali")
a("print.r.allowance", "Припуск пунктиром на деталях", "Detallarda pripusk punktir bilan")
a("print.r.qr", "QR-код на карте", "Kartada QR kod"); a("print.r.lang", "Язык отчёта", "Hisobot tili")

# ── (XNC) ──
a("print.r.grouping", "Группировка", "Guruhlash"); a("print.grp.none", "Не группировать", "Guruhlamaslik")
a("print.grp.material", "Группировать по материалу", "Material bo'yicha guruhlash"); a("print.grp.product", "Группировать по изделию", "Mahsulot bo'yicha guruhlash")
a("print.r.back_mirror", "Зеркало для обратной стороны", "Orqa tomon uchun ko'zgu")
a("print.bm.horizontal", "Горизонтально", "Gorizontal"); a("print.bm.vertical", "Вертикально", "Vertikal"); a("print.bm.none", "Нет", "Yo'q")
a("print.r.origin_as_op", "Как установлено в операции", "Operatsiyada o'rnatilganidek")
a("print.r.origin_pos", "Положение на чертеже", "Chizmadagi o'rni")

# ── ustunlar jadvali («Заголовок карт кроя», XNC «Статистика») ──
a("print.cg.n", "№", "№"); a("print.cg.on", "Вкл", "Yoq."); a("print.cg.name", "Имя", "Nomi"); a("print.cg.desc", "Описание", "Tavsif")
a("print.cg.width", "Ш-на", "Eni"); a("print.cg.reset", "Восстановить значения по умолчанию", "Standart qiymatlarni tiklash")
a("print.cg.add_which", "— добавить столбец —", "— ustun qo'shish —")
a("print.hf.R", "отход, % (на карте / всего)", "chiqindi, % (kartada / jami)")
a("print.hf.T", "торцовка по длине / по ширине", "torsovka uzunlik / en bo'yicha")
for _k, _n, _ru, _uz in [
    ("n", "№", "Номер строки", "Qator raqami"), ("side", "Ст", "Сторона (лицевая / обратная)", "Tomon (yuz / orqa)"),
    ("code", "Код", "Код программы", "Dastur kodi"), ("name", "Наименование", "Наименование программы", "Dastur nomi"),
    ("length", "Д-на", "Длина детали", "Detal uzunligi"), ("width", "Ш-на", "Ширина детали", "Detal eni"),
    ("qty", "Кол", "Количество", "Soni"), ("drills", "Кол. св-ний", "Количество сверлений", "Teshiklar soni"),
    ("drill_price", "Цена св-ний", "Цена сверления", "Teshik narxi"), ("drill_cost", "Ст-ть св-ний", "Стоимость сверлений", "Teshiklar qiymati"),
    ("mill_len", "Длина фр-ния", "Длина фрезерования, м", "Frezalash uzunligi, m"), ("mill_price", "Цена фр-ния", "Цена фрезерования (м)", "Frezalash narxi (m)"),
    ("mill_cost", "Ст-ть фр-ния", "Стоимость фрезерования", "Frezalash qiymati"), ("saw_len", "Длина п-ния", "Длина пиления, м", "Arralash uzunligi, m"),
    ("saw_price", "Цена п-ния", "Цена пиления (м)", "Arralash narxi (m)"), ("saw_cost", "Ст-ть п-ния", "Стоимость пиления", "Arralash qiymati"),
    ("extra_cost", "Доп. ст-ть", "Дополнительная стоимость", "Qo'shimcha qiymat"), ("op_cost", "Ст-ть оп-и", "Стоимость операции", "Operatsiya qiymati"),
]:
    a(f"print.xc.{_k}.n", _n, _n); a(f"print.xc.{_k}.d", _ru, _uz)
