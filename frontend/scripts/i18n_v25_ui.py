# v2.5 — onlayn ish oqimiga moslash (2026-10-03): ekranlarni solishtirishdan keyingi yorliqlar.
# i18n_src.py tomonidan exec qilinadi (`a(kalit, ru, uz)`).

# XNC «Параметры»: o'lcham yorliqlari va koordinata boshi to'liq nomi
a("xnc.dx", "Длина (DX)", "Uzunlik (DX)")
a("xnc.dy", "Ширина (DY)", "En (DY)")
a("xnc.dz", "Толщина (DZ)", "Qalinlik (DZ)")
a("xnc.origin_v.LT", "Левый верхний угол", "Chap yuqori burchak")
a("xnc.origin_v.RT", "Правый верхний угол", "O'ng yuqori burchak")
a("xnc.origin_v.LB", "Левый нижний угол", "Chap pastki burchak")
a("xnc.origin_v.RB", "Правый нижний угол", "O'ng pastki burchak")

# «Режим ввода размеров …» oynasi: sarlavha joriy rejim bilan, variantlar to'liq nom bilan
a("sizemode.opt_prefix", "Режим ввода размеров ", "O'lcham kiritish rejimi: ")

# Раскрой: kromkani kartada ko'rsatish katakchasi (ko'rsatkichlar qatorida)
a("cut.edges_toggle", "Кромка", "Kromka")

# Loyihalar ro'yxati: chap menyu ostidagi yordam matni
a("projects.open_hint", "Для открытия проекта — двойной клик по строке или Ctrl+Пробел",
  "Loyihani ochish — qatorni ikki marta bosing yoki Ctrl+Probel")

# «Печать отчета»: GibLab kabi — chap menyuda havolalar, sozlamalar oynalarda
a("print.ops_settings", "Настройки печати операций", "Operatsiyalar chop sozlamalari")
a("print.dlg.margins", "Поля страницы", "Sahifa chegaralari")
a("print.dlg.general", "Настройки печати", "Chop sozlamalari")
a("print.dlg.products", "Изделия", "Mahsulotlar")
a("print.sec.cs_main", "(CS) Листовой раскрой", "(CS) List kroy")
a("print.cstab.cs", "Общие", "Umumiy")
a("print.cstab.maps", "Карты кроя", "Kroy kartalari")
a("print.cstab.header", "Заголовок карт кроя", "Karta sarlavhasi")

# «Настройки»: «Режимы ввода деталей» — alohida oyna (GibLab kabi)
a("settings.inputmodes", "Режимы ввода деталей", "Detal kiritish rejimlari")
a("settings.inputmodes_q", "Вывод предложения на изменение режима ввода размеров деталей",
  "Detal o'lcham kiritish rejimini o'zgartirish taklifi")
a("settings.im.none", "Не предлагать", "Taklif qilmaslik")
a("settings.im.blank", "По размеру заготовки", "Zagotovka o'lchami bo'yicha")
a("settings.im.detail", "По размеру детали (с кромкой)", "Detal o'lchami bo'yicha (kromka bilan)")
a("settings.im.jointed", "По размеру заготовки после прифуговки (без кромки)", "Prifugovkadan keyingi zagotovka o'lchami (kromkasiz)")

# XNC «Стоимость»: GibLab kabi ikki ustun, to'liq yorliqlar
a("xnc.c.drill_price", "Цена сверления (1 отверстие)", "Teshik narxi (1 teshik)")
a("xnc.c.drills", "Количество сверлений", "Teshiklar soni")
a("xnc.c.drill_cost", "Стоимость сверлений", "Teshiklar narxi")
a("xnc.c.mill_price", "Цена фрезеровки (1 метр)", "Frezalash narxi (1 metr)")
a("xnc.c.mill_len", "Длина фрезерования", "Frezalash uzunligi")
a("xnc.c.mill_cost", "Стоимость фрезерования", "Frezalash narxi")
a("xnc.c.saw_price", "Цена пиления (1 метр)", "Arralash narxi (1 metr)")
a("xnc.c.saw_len", "Длина пиления", "Arralash uzunligi")
a("xnc.c.saw_cost", "Стоимость пиления", "Arralash narxi")
a("xnc.c.extra", "Дополнительная стоимость операции", "Operatsiya qo'shimcha narxi")

# (SP) «Параметры» — GibLab tartibi va yorliqlari
a("sp.p.len", "Длина", "Uzunlik")
a("sp.p.wid", "Ширина", "En")
a("sp.p.thk", "Толщина", "Qalinlik")
a("sp.p.price2", "Цена материала", "Material narxi")
a("sp.p.mat_area", "Площадь материала", "Material maydoni")
a("sp.p.op_price2", "Цена операции (м2)", "Operatsiya narxi (m²)")
a("sp.p.work_area", "Площадь деталей (работа)", "Detallar maydoni (ish)")

# XNC postprotsessor: o'rnatilgan format — loyihaning barcha dasturlari bitta zip da
a("xnc.pp.all_zip", "Все XNC проекта (zip)", "Loyihaning barcha XNC (zip)")

# LB — standart nom (ma'lumot manbai bilan, GibLab kabi)
a("ops.default.LB", "Этикетки: Детали и остатки", "Etiketkalar: detallar va qoldiqlar")

# «Листы и остатки»: «Удалить неиспользуемый материал»
a("sheets.remove_unused", "Удалить неиспользуемый материал", "Ishlatilmagan materialni o'chirish")
a("sheets.remove_unused_q", "Удалить неиспользуемые в раскрое строки листов: {{n}}?", "Kroyda ishlatilmagan list qatorlari o'chirilsinmi: {{n}}?")

# XNC asboblar paneli (GibLab kabi)
a("xnc.pick_part", "Выбрать деталь", "Detal tanlash")
a("xnc.unlink_part", "Отменить деталь", "Detaldan ajratish")
a("xnc.recode", "Кодирование", "Kodlash")
a("xnc.recode_q", "Коды XNC обработок с одинаковым кодом будут перекодированы (-2, -3 …). Продолжить?",
  "Bir xil kodli XNC dasturlar qayta kodlanadi (-2, -3 …). Davom etilsinmi?")

# «Постпроцессоры» oynasi (kroy paneli)
a("pp.dialog_title", "Постпроцессоры", "Postprotsessorlar")
a("pp.refit", "Формат станка допускает не более {{n}} вращений — раскрой выполнен заново с этим ограничением",
  "Stanok formati ko'pi bilan {{n}} burilishga ruxsat beradi — kroy shu cheklov bilan qayta bajarildi")

# XNC postprotsessor oynasi (ikki bosqich)
a("xnc.pp.tab_ops", "Операции", "Operatsiyalar")
a("xnc.pp.tab_params", "Параметры", "Parametrlar")
a("xnc.pp.col_sel", "Выб", "Tanl")
a("xnc.pp.col_code", "Код", "Kod")
a("xnc.pp.col_name", "Наименование", "Nomi")
a("xnc.pp.col_qty", "Кол", "Soni")
a("xnc.pp.select_all", "Выделить все", "Hammasini belgilash")
a("xnc.pp.select_none", "Снять выделенные", "Belgilashni olib tashlash")
a("xnc.pp.back", "К списку станков", "Stanoklar ro'yxatiga")
a("xnc.pp.params_hint", "Параметры станка, инструменты и ограничения — в разделе «Настройки → Постпроцессоры».",
  "Stanok parametrlari, asboblar va cheklovlar — «Sozlamalar → Postprotsessorlar» bo'limida.")

# «Инструменты» jadvali (stanok sozlamalari)
a("ppm.tools.title", "Инструменты", "Asboblar")
a("ppm.tools.hint", "Номер или имя инструмента на станке. Сверление большинство станков выбирает по диаметру — поле можно оставить пустым; для фрезы и пазовой пилы номер / имя обязательны.",
  "Asbobning stanokdagi raqami yoki nomi. Parmani ko'p stanoklar diametr bo'yicha o'zi tanlaydi — maydonni bo'sh qoldirish mumkin; freza va paz arrasi uchun raqam / nom shart.")
a("ppm.tools.kind", "Инструмент", "Asbob")
a("ppm.tools.plane", "Плоскость", "Tekislik")
a("ppm.tools.d", "Диаметр", "Diametr")
a("ppm.tools.ref", "Номер / имя на станке", "Stanokdagi raqam / nom")
a("ppm.tools.add", "Добавить", "Qo'shish")
a("ppm.tools.k.drill", "Сверло", "Parma")
a("ppm.tools.k.through", "Сверло сквозное", "O'tuvchi parma")
a("ppm.tools.k.mill", "Фреза", "Freza")
a("ppm.tools.k.saw", "Пазовая пила", "Paz arrasi")
a("ppm.tools.p.front", "Передняя", "Yuza")
a("ppm.tools.p.back", "Задняя", "Orqa yuza")
a("ppm.tools.p.left", "Левая", "Chap")
a("ppm.tools.p.right", "Правая", "O'ng")
a("ppm.tools.p.top", "Верхняя", "Yuqori")
a("ppm.tools.p.bottom", "Нижняя", "Pastki")
