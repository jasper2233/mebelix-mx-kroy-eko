# -*- coding: utf-8 -*-
"""i18n manbai: har kalit uchun (ru, uz). `python scripts/i18n_src.py` → src/i18n/ru.json, uz.json.
ru — rus yorliqlari + xodimlar odatlangan o'zbekcha (kirill) ustun nomlari; uz — to'liq o'zbekcha (lotin)."""
import json, os

T = {}
def a(key, ru, uz=None):
    T[key] = (ru, uz if uz is not None else ru)

# ── app ──
a("app.add", "Добавить", "Qo'shish"); a("app.cancel", "Отмена", "Bekor qilish"); a("app.choose", "Выбрать", "Tanlash")
a("app.clone", "Клонировать", "Nusxalash"); a("app.close", "Закрыть", "Yopish"); a("app.delete", "Удалить", "O'chirish")
a("app.down", "Вниз", "Pastga"); a("app.insert", "Вставить", "Qo'yish"); a("app.loading", "Загрузка…", "Yuklanmoqda…")
a("app.no", "Нет", "Yo'q"); a("app.yes", "Да", "Ha"); a("app.no_rows", "Нет строк", "Qatorlar yo'q"); a("app.ok", "Ок", "Ok")
a("app.pcs", "шт", "dona"); a("app.properties", "Свойства", "Xossalar"); a("app.save", "Сохранить", "Saqlash")
a("app.saved", "Сохранено", "Saqlandi"); a("app.sort", "Сортировка", "Saralash"); a("app.up", "Вверх", "Yuqoriga")
a("u.m", "м", "m"); a("u.m2", "м²", "m²"); a("u.mm", "мм", "mm"); a("u.pcs", "шт", "dona")

# ── menu ──
a("menu.language", "Язык", "Til"); a("menu.project", "Проект", "Loyiha"); a("menu.projects", "Проекты", "Loyihalar")
a("menu.print", "Печать отчета", "Hisobot chop etish"); a("menu.settings", "Настройки", "Sozlamalar")
a("menu.close_project", "Закрыть проект", "Loyihani yopish"); a("menu.help", "Справка", "Yordam")
a("menu.refresh", "Обновить", "Yangilash"); a("menu.open", "Открыть", "Ochish"); a("menu.add", "Добавить", "Qo'shish")
a("menu.add_folder", "Добавить папку", "Papka qo'shish"); a("menu.move", "Переместить", "Ko'chirish")
a("menu.rename", "Переименовать", "Qayta nomlash"); a("menu.copy", "Копировать", "Nusxa olish"); a("menu.delete", "Удалить", "O'chirish")
a("menu.import", "Импортировать", "Import"); a("menu.export", "Экспортировать", "Eksport")
a("menu.undo", "Отменить", "Bekor qilish"); a("menu.redo", "Вернуть", "Qaytarish"); a("menu.save", "Сохранить", "Saqlash")
a("menu.common_actions", "Общие действия", "Umumiy amallar"); a("menu.import_excel", "Импорт из Excel", "Excel dan import")
a("menu.import_other", "Импорт из других программ", "Boshqa dasturlardan import")
a("menu.fullscreen", "Полный экран (все сочетания клавиш)", "To'liq ekran (barcha yorliqlar)")
a("menu.fullscreen_hint", "В полноэкранном режиме работают Ctrl+W, Ctrl+PgUp и др., которые браузер обычно занимает",
  "To'liq ekranda brauzer band qiladigan Ctrl+W, Ctrl+PgUp va boshqalar ishlaydi")
a("menu.order", "Заказать", "Buyurtma"); a("menu.order_id", "Заказ ID", "Buyurtma ID"); a("menu.cost", "Стоимость", "Narx")
a("menu.cost_mat", "С-ть материала", "Material narxi"); a("menu.cost_op", "С-ть операций", "Ish narxi")
a("menu.workshop", "Цех (сканер QR)", "Sex rejimi (QR skaner)")
for i, (ru, uz) in enumerate([("Не заказан", "Buyurtma qilinmagan"), ("Заказан", "Buyurtma qilingan"), ("Утвержден", "Tasdiqlangan"), ("Готов", "Tayyor")]):
    a(f"status.{i}", ru, uz)

# ── projects ──
a("projects.col.id", "ID", "ID"); a("projects.col.owner", "Владелец", "Egasi"); a("projects.col.status", "Состояние", "Holati")
a("projects.col.date", "Дата", "Sana"); a("projects.col.cost", "Стоимость", "Narx"); a("projects.col.name", "Наименование", "Nomi")
a("projects.up", "В папку выше", "Yuqori papkaga"); a("projects.home", "Корневая папка", "Bosh papka"); a("projects.root", "Проекты", "Loyihalar")
a("projects.search", "Поиск…", "Qidirish…"); a("projects.new", "Новый проект", "Yangi loyiha")
a("projects.new_name", "Наименование проекта", "Loyiha nomi"); a("projects.default_name", "Новый проект", "Yangi loyiha")
a("projects.new_folder", "Новая папка", "Yangi papka"); a("projects.default_folder", "Новая папка", "Yangi papka")
a("projects.delete_q", "Удалить проект «{{name}}»?", "«{{name}}» loyihasi o'chirilsinmi?")
a("projects.delete_folder_q", "Удалить папку «{{name}}»?", "«{{name}}» papkasi o'chirilsinmi?")
a("projects.delete_folder_text", "Будут удалены все вложенные папки и проекты.", "Ichidagi barcha papka va loyihalar ham o'chiriladi.")
a("projects.importing", "Импорт проекта…", "Loyiha import qilinmoqda…")
a("projects.imported", "Проект «{{name}}» импортирован", "«{{name}}» import qilindi")
a("projects.import_warnings", "Импорт выполнен, замечаний: {{n}}", "Import bajarildi, ogohlantirishlar: {{n}}")

# ── header ──
a("header.name", "Наименование", "Nomi"); a("header.currency", "Валюта", "Valyuta"); a("header.order_date", "Дата заказа", "Buyurtma sanasi")
a("header.ready_date", "Дата готовности", "Tayyor bo'lish sanasi"); a("header.customer", "Заказчик", "Buyurtmachi")
a("header.note", "Примечание (Изох)", "Izoh"); a("header.save_currency", "Сохранить валюту по умолчанию", "Valyutani standart sifatida saqlash")
a("header.currency_saved", "Валюта {{cur}} сохранена по умолчанию", "{{cur}} standart valyuta sifatida saqlandi")
a("project.no_op", "Добавьте операцию (CS — листовой раскрой) на панели «Операции»", "«Операции» panelida operatsiya qo'shing (CS — listli kroy)")
a("project.current_product", "Текущее изделие (новые детали добавляются в него)", "Joriy mahsulot (yangi detallar shunga qo'shiladi)")

# ── common actions / import ──
a("common.merge", "Объединить операции с одинаковым кодом и наименованием", "Bir xil kod va nomli operatsiyalarni birlashtirish")
a("common.merge_hint", "Детали одинаковых материалов собираются в одну операцию", "Bir xil materialdagi detallar bitta operatsiyaga yig'iladi")
a("common.split_edges", "Разделить операции кромки по материалам раскроя", "Kromka operatsiyalarini kroy materiallari bo'yicha ajratish")
a("common.split_edges_hint", "Для каждого материала — своя операция кромки (удобно для отчёта)", "Har material uchun alohida kromka operatsiyasi")
a("common.optimize_ops", "Оптимизировать операции", "Operatsiyalarni optimallashtirish")
a("common.optimize_ops_hint", "Удалить пустые, объединить одинаковые, упорядочить CS → EL → GR → XNC", "Bo'shlarini o'chirish, bir xillarini birlashtirish, tartiblash")
a("common.done", "Выполнено", "Bajarildi")
a("common.recode_xnc", "Перекодировать XNC обработки", "XNC dasturlarni qayta kodlash")
a("common.recode_xnc_dups", "Повторяющихся кодов: {{n}} — будут добавлены суффиксы -2, -3…", "Takrorlanuvchi kodlar: {{n}} — -2, -3… qo'shimchalari qo'shiladi")
a("common.recode_xnc_none", "Все коды XNC обработок уникальны", "Barcha XNC kodlari noyob")
a("common.recode_xnc_ok", "Перекодировать", "Qayta kodlash")
a("print.recode_q", "Найдены XNC обработки с одинаковым кодом: {{n}}", "Bir xil kodli XNC dasturlar topildi: {{n}}")
a("print.recode_text", "Имена файлов станка не должны повторяться. Сделать коды уникальными (-2, -3…)?",
  "Stanok fayl nomlari takrorlanmasligi kerak. Kodlar noyob qilinsinmi (-2, -3…)?")
a("import.choose_file", "Выбрать файл", "Faylni tanlash"); a("import.other_hint", "Файлы других программ импортируются плагинами.", "Boshqa dastur fayllari plaginlar orqali import qilinadi.")
a("import.supported", "поддерживается", "qo'llab-quvvatlanadi"); a("import.plugin_later", "плагин позже", "plagin keyinroq")
a("import.run", "Импортировать", "Import qilish"); a("import.start_row", "Начальная строка", "Boshlang'ich qator")
a("import.target", "Операция", "Operatsiya"); a("import.importing", "Импорт…", "Import…")
a("import.done", "Импортировано: {{n}}", "Import qilindi: {{n}}")
a("import.excel_hint", "Выберите файл Excel (.xlsx) или CSV. Затем укажите, в каком столбце какое поле.", "Excel (.xlsx) yoki CSV faylni tanlang, so'ng ustunlarni belgilang.")
for k, ru, uz in [("name", "Наименование", "Nomi"), ("length", "Длина", "Uzunlik"), ("width", "Ширина", "En"), ("qty", "Кол-во", "Soni"),
                  ("grain", "Текстура", "Tekstura"), ("edge_top", "Кромка ОВ", "Kromka yuqori"), ("edge_bottom", "Кромка ОН", "Kromka pastki"),
                  ("edge_left", "Кромка ОЛ", "Kromka chap"), ("edge_right", "Кромка ОП", "Kromka o'ng"), ("code", "Код", "Kod")]:
    a(f"import.f.{k}", ru, uz)

# ── operations ──
a("ops.tab", "Операции", "Operatsiyalar"); a("ops.col.type", "Тип", "Tur"); a("ops.col.code", "Код/Изделие", "Kod/Mahsulot")
a("ops.col.name", "Наименование", "Nomi"); a("ops.col.cost_mat", "Ст. м-ла", "Material"); a("ops.col.cost_op", "Ст. оп-и", "Ish")
a("ops.col.cost", "Ст-ть", "Jami"); a("ops.col.print", "П-ть", "Chop"); a("ops.col.new_page", "Н.Стр", "Yangi bet")
a("ops.add_cs", "Добавить: (CS) Листовой раскрой", "Qo'shish: (CS) Listli kroy"); a("ops.add_el", "Добавить: (EL) Кромка", "Qo'shish: (EL) Kromka")
a("ops.add_gr", "Добавить: (GR) Пазование", "Qo'shish: (GR) Pazlash"); a("ops.add_xnc", "Добавить: (XNC) Обработка", "Qo'shish: (XNC) Ishlov")
a("ops.add_op", "Операция", "Operatsiya"); a("ops.catalog", "Каталог товаров", "Tovarlar katalogi")
a("ops.merge", "Объединить одинаковые", "Bir xillarini birlashtirish"); a("ops.choose_type", "Выберите тип операции", "Operatsiya turini tanlang")
a("ops.later", "Будет в следующих версиях", "Keyingi versiyalarda")
a("ops.default.CS", "Материал {{n}} (ЛДСП 16)", "Material {{n}} (LDSP 16)")
a("ops.default.EL", "Кромка {{n}}", "Kromka {{n}}")
a("ops.default.GR", "Пазование{{n}}", "Pazlash{{n}}")
a("ops.delete_q", "Удалить операцию «{{name}}»?", "«{{name}}» operatsiyasi o'chirilsinmi?")
for k, ru, uz in [("O", "Комплектация и другие действия", "Komplektatsiya va boshqa amallar"), ("CS", "Листовой раскрой", "Listli kroy"),
                  ("CN", "Нестинговый раскрой", "Nesting kroy"), ("CL", "Погонажный раскрой", "Pogonaj kroy"), ("EL", "Кромка", "Kromka"),
                  ("SP", "Обработка поверхности", "Sirt ishlovi"), ("GR", "Пазование", "Pazlash"), ("XNC", "Обработка", "CNC ishlov"),
                  ("LB", "Этикетки", "Etiketkalar")]:
    a(f"optype.{k}", ru, uz)

# ── products ──
a("products.tab", "Изделия", "Mahsulotlar"); a("products.col.code", "Код", "Kod"); a("products.col.name", "Наименование", "Nomi")
a("products.col.qty", "Кол", "Soni"); a("products.col.cost_mat", "Ст. м-ла", "Material"); a("products.col.cost_op", "Ст. оп-и", "Ish")
a("products.col.cost", "Стоимость", "Narx (1 dona)"); a("products.col.total", "Всего", "Jami")
a("products.props", "Наименование изделия", "Mahsulot nomi"); a("products.parts", "Детали", "Detallar")
a("products.zero_all", "Установить всем количество 0", "Hammasini 0 soniga"); a("products.zero_q", "Установить количество 0 всем изделиям?", "Barcha mahsulotlar soni 0 qilinsinmi?")
a("products.zero_filter", "Скрыть изделия с количеством 0", "Nol sonlilarni yashirish"); a("products.new_name", "Наименование изделия", "Mahsulot nomi")
a("products.default_name", "Изделие {{n}}", "Mahsulot {{n}}")
a("products.delete_q", "Удалить изделие «{{name}}»?", "«{{name}}» mahsuloti o'chirilsinmi?")
a("products.delete_text", "Будут удалены и все его детали.", "Uning barcha detallari ham o'chiriladi.")

# ── CS ──
a("cs.tab.params", "Параметры", "Parametrlar"); a("cs.tab.parts", "Детали", "Detallar"); a("cs.tab.sheets", "Листы и остатки", "Listlar va qoldiqlar")
a("cs.tab.cut", "Раскрой", "Kroy")
a("cs.save_default", "Сохранить текущие параметры как стандартные", "Joriy parametrlarni standart sifatida saqlash")
a("cs.apply_default", "Применить стандартные параметры", "Standart parametrlarni qo'llash")
a("cs.defaults_saved", "Стандартные параметры сохранены", "Standart parametrlar saqlandi")
P = {
 "material": ("Параметры материала", "Material parametrlari"), "thickness": ("Толщина", "Qalinlik"), "cost": ("Стоимость", "Narx"),
 "price": ("Цена материала", "Material narxi"), "per_m2": ("за м²", "1 m² uchun"), "est_fill": ("Расчетный процент заполнения", "Taxminiy to'ldirish foizi"),
 "material_qty": ("Количество материала", "Material miqdori"), "sheets_u": ("Листы", "list"),
 "cost_by_sheets": ("Расчет стоимости по листам", "Narxni listlar bo'yicha hisoblash"), "rounding": ("Округление листы", "Listlarni yaxlitlash"),
 "cost_material": ("Стоимость материала (Лист)", "Material narxi (list)"), "op_base": ("Расчет стоимости операции по", "Ish narxini hisoblash asosi"),
 "op_price": ("Цена операции (метр/рез)", "Ish narxi (metr)"), "cost_op": ("Стоимость операции", "Ish narxi"),
 "remnant": ("Остаток", "Qoldiq"), "rem1": ("Мин. размер остатка первой стороны", "Qoldiq 1-tomoni min. o'lchami"),
 "rem2": ("Мин. размер остатка второй стороны", "Qoldiq 2-tomoni min. o'lchami"), "rem_area": ("Площадь делового остатка", "Deloviy qoldiq maydoni"),
 "rem_trim": ("Размер остатков с учетом торцовки", "Qoldiq o'lchami torsovka bilan"), "limits": ("Ограничения", "Cheklovlar"),
 "min_part": ("Минимальный размер детали", "Detalning min. o'lchami"), "cut": ("Параметры раскроя", "Kroy parametrlari"),
 "kerf": ("Толщина пилы", "Arra qalinligi"), "kerf_group": ("Толщина пилы для групповых деталей", "Guruh detallar uchun arra"),
 "trim_l": ("Торцовка по длине", "Uzunlik bo'yicha torsovka"), "trim_w": ("Торцовка по ширине", "En bo'yicha torsovka"),
 "trim_l_hint": ("Срез вдоль длины листа (уменьшает ширину)", "List uzunligi bo'ylab kesim (enni kamaytiradi)"),
 "trim_w_hint": ("Срез вдоль ширины листа (уменьшает длину)", "List eni bo'ylab kesim (uzunlikni kamaytiradi)"),
 "trim_kerf": ("Торцовка включает толщину пропила", "Torsovka propil qalinligini o'z ichiga oladi"),
 "end_offset": ("Минимальный отступ в конце", "Oxiridagi minimal otstup"),
 "end_offset_hint": ("Торцовка сверху и слева; внизу и справа остаётся минимальный отступ (по умолчанию — как торцовка). К каждому значению добавляется пропил; 0 — без реза.",
                     "Torsovka yuqori va chap chetdan; past va o'ngda minimal otstup qoladi (standart — torsovka kabi). Har qiymatga propil qo'shiladi; 0 — kesim yo'q."),
 "offset_bottom": ("Минимальный отступ снизу", "Pastdagi minimal otstup"), "offset_right": ("Минимальный отступ справа", "O'ngdagi minimal otstup"),
 "offset_bottom_s": ("снизу", "past"), "offset_right_s": ("справа", "o'ng"),
 "per_sheet": ("за лист", "1 list uchun"), "price_hint": ("При «Расчет стоимости по листам» — цена одного листа, иначе — цена 1 м²",
                                                          "«Listlar bo'yicha hisob» belgilansa — 1 list narxi, aks holda 1 m² narxi"),
 "est_fill_hint": ("До раскроя: расход = площадь деталей × (2 − % / 100)", "Kroygacha: sarf = detallar maydoni × (2 − % / 100)"),
 "material_qty_hint": ("После раскроя: листы (или м² — площадь листов минус деловые остатки)", "Kroydan keyin: listlar (yoki m² — listlar maydoni minus deloviy qoldiqlar)"),
 "mult_hint": ("Рассчитывается автоматически: Высота пакета / Толщина материала", "Avtomatik: Paket balandligi / Material qalinligi"),
 "first_cut": ("Начальное направление резов", "Birinchi kesish yo'nalishi"), "use_grain": ("Учет текстуры", "Teksturani hisobga olish"),
 "complex": ("Использовать сложные полосы", "Murakkab polosalar"), "max_rot": ("Максимальное количество вращений", "Maksimal aylanishlar soni"),
 "pack_h": ("Высота пакета", "Paket balandligi"), "mult": ("Кратность", "Karralik"), "fill_packet": ("Процент заполнения для кратности", "Karralik uchun to'ldirish %"),
 "max_types": ("Макс. кол-во разновидностей деталей на карте", "Kartada detal turlari (maks.)"), "unlimited": ("Не ограничено", "Cheklanmagan"),
 "prefs": ("Предпочтения", "Afzalliklar"), "big_pack": ("Большой пакет", "Katta paket"), "quality": ("Качество раскроя (время)", "Kroy sifati (vaqt)"),
 "quality_hint": ("Быстро ≈ 1 с, Стандарт ≈ 1–4 с, Максимум — до 15 с (лучше на сложных заказах)", "Tez ≈ 1 s, Standart ≈ 1–4 s, Maksimal — 15 s gacha"),
 "sorting": ("Сортировка", "Saralash"), "sort_strips": ("Сортировать полосы", "Polosalarni saralash"), "sort_in": ("Сортировать в полосе", "Polosa ichida saralash"),
 "min_strip": ("Минимальная ширина полосы", "Polosa min. eni"), "max_strip": ("Максимальная ширина полосы", "Polosa maks. eni"),
 "max_strip_len": ("Максимальная длина полосы", "Polosa maks. uzunligi"), "min_trim": ("Минимальная обрезка", "Minimal qirqim"),
 "min_trim_hint": ("Остаток между деталью и резом меньше этого значения недопустим (кроме края листа)", "Detal va kesim orasidagi bundan kichik qoldiq taqiqlanadi"),
 "merge": ("Объединение деталей", "Detallarni birlashtirish"), "save_draw": ("Сохранение чертежа карт кроя", "Kroy kartalari chizmasini saqlash"),
 "allowance": ("Припуск на обработку заготовки", "Zagotovka ishlov pripuski"),
}
for k, (ru, uz) in P.items():
    a(f"cs.p.{k}", ru, uz)
for code, ru, uz in [("11", "К целому", "Butungacha"), ("12", "Любое 1/2", "Istalgan 1/2"), ("13", "Любое 1/3", "Istalgan 1/3"), ("14", "Любое 1/4", "Istalgan 1/4"),
                     ("22", "По ширине 1/2", "En bo'yicha 1/2"), ("23", "По ширине 1/3", "En bo'yicha 1/3"), ("24", "По ширине 1/4", "En bo'yicha 1/4"),
                     ("32", "По длине 1/2", "Uzunlik bo'yicha 1/2"), ("33", "По длине 1/3", "Uzunlik bo'yicha 1/3"), ("34", "По длине 1/4", "Uzunlik bo'yicha 1/4")]:
    a(f"cs.round.{code}", ru, uz)
for i, (ru, uz) in enumerate([("Длине реза", "Kesish uzunligi"), ("Периметру деталей", "Detallar perimetri"), ("Площади деталей", "Detallar maydoni"), ("Площади материала", "Material maydoni")]):
    a(f"cs.opbase.{i}", ru, uz)
for i, (ru, uz) in enumerate([("Любое", "Istalgan"), ("По длине", "Uzunlik bo'yicha"), ("По ширине", "En bo'yicha"), ("По длине предпочтительно", "Afzali uzunlik bo'yicha"), ("По ширине предпочтительно", "Afzali en bo'yicha")]):
    a(f"cs.first.{i}", ru, uz)
for i, (ru, uz) in enumerate([("По убыванию", "Kamayish tartibida"), ("По возрастанию", "O'sish tartibida"), ("Узкие в центр", "Torlari markazga"), ("Не сортировать", "Saralamaslik")]):
    a(f"cs.sort.{i}", ru, uz)
for k, ru, uz in [("fast", "Быстро", "Tez"), ("normal", "Стандарт", "Standart"), ("max", "Максимум", "Maksimal")]:
    a(f"cs.quality.{k}", ru, uz)
for k, ru, uz in [("blank", "заготовки", "zagotovka"), ("detail", "детали (с кромкой)", "detal (kromka bilan)"), ("jointed", "после прифуговки (без кромки)", "prifugovkadan keyin (kromkasiz)")]:
    a(f"sizemode.{k}", ru, uz)
a("sizemode.hint", "При смене режима значения размеров пересчитываются так, чтобы физический размер детали не изменился.",
  "Rejim o'zgarsa o'lchamlar detalning jismoniy o'lchami saqlanadigan qilib qayta hisoblanadi.")

# ── parts ──
a("parts.size_mode", "Режим ввода размеров детали", "O'lcham kiritish rejimi"); a("parts.area", "Площадь", "Maydon"); a("parts.count", "Кол-во", "Soni")
a("parts.xnc_editor", "XNC Редактор", "XNC muharriri"); a("parts.paste_hint", "Вставить из буфера (Ctrl+V): скопируйте строки из Excel и нажмите Ctrl+V в таблице",
  "Buferdan qo'yish (Ctrl+V): Excel dan qatorlarni nusxalab jadvalda Ctrl+V bosing")
a("parts.pasted", "Вставлено: изменено {{u}}, добавлено {{c}}", "Qo'yildi: {{u}} ta o'zgardi, {{c}} ta qo'shildi")
a("parts.paste_skipped", "Пропущено строк: {{n}} (нет длины/ширины или это не числа)", "O'tkazib yuborilgan qatorlar: {{n}} (uzunlik/en yo'q yoki son emas)")
a("parts.paste_nothing","Нечего вставлять (нужны длина и ширина)", "Qo'yadigan ma'lumot yo'q (uzunlik va en kerak)")
a("parts.edges_created", "Добавлены новые кромки ({{n}}): {{names}}", "Yangi kromkalar qo'shildi ({{n}}): {{names}}")
a("parts.deleted", "Удалено деталей: {{n}} (Ctrl+Z — отменить)", "{{n}} ta detal o'chirildi (Ctrl+Z — qaytarish)")
a("parts.grain_off_all", "Снять текстуру у всех", "Hammasidan teksturani olish"); a("parts.grain_on_all", "Установить текстуру всем", "Hammasiga tekstura qo'yish")
a("parts.grain_off", "Снять текстуру", "Teksturani olish"); a("parts.grain_on", "Установить текстуру", "Tekstura qo'yish")
a("parts.swap", "Поменять размеры местами", "O'lchamlarni almashtirish"); a("parts.group", "Групповые действия", "Guruhli amallar")
a("parts.move_to", "Перенести в другую операцию", "Boshqa operatsiyaga ko'chirish"); a("parts.columns", "Настройки колонок", "Ustunlar sozlamasi")
a("parts.filter", "Показать только не вошедшие в раскрой", "Faqat kroyga kirmaganlar"); a("parts.no_target", "Нет другой операции раскроя", "Boshqa kroy operatsiyasi yo'q")
for k, ru, uz in [("uid", "По ID", "ID bo'yicha"), ("name", "По наименованию", "Nomi bo'yicha"), ("length", "По длине (убыв.)", "Uzunlik (kamayish)"),
                  ("width", "По ширине (убыв.)", "En (kamayish)"), ("area", "По площади (убыв.)", "Maydon (kamayish)"), ("product", "По изделию", "Mahsulot bo'yicha")]:
    a(f"parts.sort.{k}", ru, uz)

# column titles (short) and descriptions
COLS = {
 "num": ("№", "№", "Номер строки", "Qator raqami"),
 "article": ("Арт", "Art", "Изделие - Код", "Mahsulot kodi"),
 "name": ("детал номи", "Detal nomi", "Наименование и отметка действия = Пазование * Фрезеровка (Радиусы) % Сверление", "Nomi va belgilar: = paz, * freza, % teshik"),
 "length": ("Д-на", "Uzunlik", "Длина", "Uzunlik"), "width": ("Ш-на", "En", "Ширина", "En"),
 "qty": ("Сони", "Soni", "Количество", "Soni"), "grain": ("Ткт", "Tkt", "Учитывать текстуру. Не вращать деталь в раскрое", "Tekstura — detal aylantirilmaydi"),
 "edge_top": ("ОВ", "K.Yu", "Оклейка кромки сверху. По длине", "Kromka yuqori (uzunlik bo'ylab)"),
 "edge_bottom": ("ОН", "K.Pa", "Оклейка кромки снизу. По длине", "Kromka pastki (uzunlik bo'ylab)"),
 "edge_left": ("ОЛ", "K.Ch", "Оклейка кромки слева. По ширине", "Kromka chap (en bo'ylab)"),
 "edge_right": ("ОП", "K.O'", "Оклейка кромки справа. По ширине", "Kromka o'ng (en bo'ylab)"),
 "product_name": ("Махсулот", "Mahsulot", "Изделие - Наименование", "Mahsulot nomi"),
 "used": ("ИК", "Ishl.", "Используемое количество. Количество деталей вошедших в раскрой", "Kroyga kirgan soni"),
 "left": ("Ост", "Qoldi", "Остаток. Количество деталей не вошедших в раскрой", "Kroyga kirmagan soni"),
 "description": ("Изох", "Izoh", "Описание", "Izoh"), "code": ("Код", "Kod", "Код", "Kod"),
 "uid": ("ID", "ID", "Уникальный идентификатор", "Noyob raqam"),
 "total": ("ОК", "Jami", "Общее количество = (Количество деталей) × (Количество изделий)", "Jami soni = detal soni × mahsulot soni"),
 "minus": ("МК", "Minus", "Минус количество", "Minus soni"),
 "group_by": ("Группировка", "Guruhlash", "Группировка в блок", "Blokka guruhlash"),
 "group_min": ("ГКmin", "GKmin", "Группировка в блок: минимальное количество", "Blok: minimal soni"),
 "group_max": ("ГКmax", "GKmax", "Группировка в блок: максимальное количество", "Blok: maksimal soni"),
 "product_qty": ("ИзК", "M.soni", "Изделие - Количество", "Mahsulot soni"), "product_num": ("Изд.№", "M.№", "Изделие - Номер", "Mahsulot raqami"),
 "part_num": ("Дет.№", "D.№", "Деталь - Номер в изделии", "Mahsulotdagi raqam"), "op_num": ("Оп.№", "Op.№", "Номер в операции", "Operatsiyadagi raqam"),
 "blank_l": ("Зг.Дл", "Zg.U", "Заготовка - Длина", "Zagotovka uzunligi"), "blank_w": ("Зг.Шр", "Zg.E", "Заготовка - Ширина", "Zagotovka eni"),
 "detail_l": ("Дт.Дл", "Dt.U", "Деталь - Длина", "Detal uzunligi"), "detail_w": ("Дт.Шр", "Dt.E", "Деталь - Ширина", "Detal eni"),
 "jointed_l": ("Пф.Дл", "Pf.U", "После прифуговки - Длина", "Prifugovkadan keyin uzunlik"), "jointed_w": ("Пф.Шр", "Pf.E", "После прифуговки - Ширина", "Prifugovkadan keyin en"),
 "saw_l": ("Пл.Дл", "Arr.U", "Пильный размер - Длина", "Arra o'lchami uzunlik"), "saw_w": ("Пл.Шр", "Arr.E", "Пильный размер - Ширина", "Arra o'lchami en"),
 "allow_top": ("▽", "▽", "Припуск сверху", "Pripusk yuqori"), "allow_bottom": ("△", "△", "Припуск снизу", "Pripusk pastki"),
 "allow_left": ("▷", "▷", "Припуск слева", "Pripusk chap"), "allow_right": ("◁", "◁", "Припуск справа", "Pripusk o'ng"),
 "groove_top": ("ПВ", "PzYu", "Пазование сверху", "Paz yuqori"), "groove_bottom": ("ПН", "PzPa", "Пазование снизу", "Paz pastki"),
 "groove_left": ("ПЛ", "PzCh", "Пазование слева", "Paz chap"), "groove_right": ("ПП", "PzO'", "Пазование справа", "Paz o'ng"),
 "surface_face": ("ЛП", "YuzS", "Обработка поверхности: лицевая", "Sirt ishlovi: old tomoni"), "surface_back": ("ТП", "OrqS", "Обработка поверхности: обратная", "Sirt ishlovi: orqa tomoni"),
 "xnc": ("XNC", "XNC", "Операции XNC детали", "Detal XNC operatsiyalari"), "area": ("Площ.", "Maydon", "Площадь (м²) × общее количество", "Maydon (m²) × jami soni"),
}
for k, (ru, uz, dru, duz) in COLS.items():
    a(f"pc.{k}", ru, uz)
    a(f"pcd.{k}", dru, duz)
a("tip.product", "Изделие", "Mahsulot"); a("tip.num_in_product", "№ в изделии", "Mahsulotdagi №"); a("tip.num_in_cut", "№ в раскрое", "Kroydagi karta №")
a("tip.detail", "Размер детали", "Detal o'lchami"); a("tip.jointed", "После прифуговки", "Prifugovkadan keyin")
a("tip.blank", "Заготовка", "Zagotovka"); a("tip.saw", "Пильный", "Arra o'lchami")

# column settings
a("cols.profile", "Профиль", "Profil"); a("cols.standard", "Стандарт", "Standart"); a("cols.new_profile", "Новый профиль", "Yangi profil")
a("cols.profile_name", "Мой профиль", "Mening profilim"); a("cols.delete_q", "Удалить профиль колонок?", "Ustunlar profili o'chirilsinmi?")
a("cols.reset", "Восстановить значения по умолчанию", "Standartni tiklash"); a("cols.on", "Вкл", "Yoq."); a("cols.name", "Имя", "Nomi")
a("cols.desc", "Описание", "Tavsif"); a("cols.width", "Ш-на", "Kenglik")

# part properties
a("pp.title", "Деталь", "Detal"); a("pp.operations", "Операции", "Operatsiyalar"); a("pp.add_xnc", "Добавить: (XNC) Обработка", "Qo'shish: (XNC) Ishlov")
a("pp.product", "Изделие", "Mahsulot"); a("pp.name", "Наименование", "Nomi"); a("pp.description", "Описание", "Izoh"); a("pp.code", "Код", "Kod")
a("pp.qty", "Количество", "Soni"); a("pp.total", "Всего", "Jami"); a("pp.grain", "Текстура", "Tekstura"); a("pp.size", "Размер", "O'lcham")
a("pp.length", "Длина", "Uzunlik"); a("pp.width", "Ширина", "En")
a("pp.sz.detail", "детали", "detal"); a("pp.sz.jointed", "заготовки после прифуговки", "prifugovkadan keyin"); a("pp.sz.blank", "заготовки", "zagotovka")
a("pp.sz.saw", "пильный", "arra o'lchami"); a("pp.grouping", "Группировка", "Guruhlash")
a("pp.group.none", "Нет", "Yo'q"); a("pp.group.length", "По длине", "Uzunlik bo'yicha"); a("pp.group.width", "По ширине", "En bo'yicha")
a("pp.group_min", "Минимальное количество", "Minimal soni"); a("pp.group_max", "Максимальное количество", "Maksimal soni")
a("pp.side.top", "Сверху (по длине)", "Yuqori (uzunlik)"); a("pp.side.bottom", "Снизу (по длине)", "Pastki (uzunlik)")
a("pp.side.left", "Слева (по ширине)", "Chap (en)"); a("pp.side.right", "Справа (по ширине)", "O'ng (en)")
a("pp.back_side", "Обратная сторона", "Orqa tomoni"); a("pp.xnc_params", "XNC Параметры", "XNC parametrlari")

# sheets / remnants
a("sheets.col.length", "Длина", "Uzunlik"); a("sheets.col.width", "Ширина", "En"); a("sheets.col.qty", "Сони", "Soni")
a("sheets.col.area", "Квадрати", "Maydon"); a("sheets.col.used", "Ишлатилди", "Ishlatildi"); a("sheets.col.left", "Колдик", "Qoldi")
a("sheets.col.trim_l", "ТД", "TU"); a("sheets.col.trim_w", "ТШ", "TE"); a("sheets.col.note", "Изох", "Izoh")
a("sheets.col.trim_l_hint", "Торцовка по длине для этого листа (пусто — из параметров)", "Shu list uchun uzunlik bo'yicha torsovka (bo'sh — parametrdan)")
a("sheets.col.trim_w_hint", "Торцовка по ширине для этого листа (пусто — из параметров)", "Shu list uchun en bo'yicha torsovka (bo'sh — parametrdan)")
a("sheets.col.end_b", "МОН", "MOP"); a("sheets.col.end_r", "МОП", "MOO"); a("sheets.col.kind", "Наименование", "Nomi")
a("sheets.kind.sheet", "Лист", "List"); a("sheets.kind.stock", "Остаток (склад)", "Qoldiq (ombor)")
a("sheets.kind.remnant", "Остаток", "Qoldiq"); a("sheets.kind.business", "Деловой остаток", "Deloviy qoldiq")
a("sheets.from_warehouse", "Добавить остатки со склада", "Ombordan qoldiq qo'shish"); a("sheets.unlimited", "Количество не ограничено (10000)", "Cheklanmagan son (10000)")
a("sheets.hint", "Сони = 10000 — без ограничения. Остатки со склада раскраиваются в первую очередь. ТД/ТШ — своя торцовка для листа.",
  "Soni = 10000 — cheklanmagan. Ombordagi qoldiqlar birinchi navbatda kesiladi. TU/TE — shu list uchun alohida torsovka.")
a("rem.material", "Материал", "Material"); a("rem.code", "Код материала", "Material kodi"); a("rem.thickness", "Толщ.", "Qalinlik")
a("rem.source", "Источник", "Manba"); a("rem.note", "Примечание", "Izoh"); a("rem.date", "Дата", "Sana")
a("rem.all_materials", "Показать все материалы", "Barcha materiallar")
a("rem.picker_hint", "Остатки на складе для материала «{{code}}». Выберите и нажмите «Добавить».", "«{{code}}» materiali qoldiqlari. Tanlab «Qo'shish» ni bosing.")
a("rem.commit_title", "Деловые остатки → склад", "Deloviy qoldiqlar → ombor")
a("rem.commit_text", "Записать деловые остатки раскроя на склад (материал «{{code}}»)? Использованные остатки склада будут списаны.",
  "Kroydan qolgan deloviy qoldiqlar omborga yozilsinmi («{{code}}»)? Ishlatilgan ombor qoldiqlari hisobdan chiqariladi.")
a("rem.already", "Остатки уже записаны на склад.", "Qoldiqlar omborga yozilgan.")
a("rem.commit", "Записать на склад", "Omborga yozish"); a("rem.later", "Позже", "Keyinroq"); a("rem.rollback", "Отменить запись", "Yozuvni bekor qilish")
a("rem.none", "Деловых остатков нет", "Deloviy qoldiq yo'q"); a("rem.consumed", "Списывается со склада", "Ombordan chiqariladi")
a("rem.committed", "Записано на склад: {{n}}", "Omborga yozildi: {{n}}"); a("rem.rolled_back", "Запись остатков отменена", "Qoldiqlar yozuvi bekor qilindi")
a("rem.add", "Добавить остаток", "Qoldiq qo'shish"); a("rem.delete_q", "Удалить остаток со склада?", "Qoldiq ombordan o'chirilsinmi?")
a("rem.total", "Остатков: {{n}}, площадь {{a}} м²", "Qoldiqlar: {{n}}, maydoni {{a}} m²")

# cut
a("cut.run", "Раскроить", "Kroy qilish"); a("cut.busy", "Раскрой…", "Kroy qilinmoqda…"); a("cut.busy_rest", "До кроить…", "Qolganlarini kroy…")
a("cut.done", "Раскрой: {{sheets}} лист(ов), F {{fill}}% ({{s}} с)", "Kroy: {{sheets}} list, F {{fill}}% ({{s}} s)")
a("cut.unplaced", "не вместилось: {{n}}", "sig'madi: {{n}}")
a("cut.recut_q", "Раскроить заново? Текущий раскрой будет заменён.", "Qaytadan kroy qilinsinmi? Joriy kroy almashtiriladi.")
a("cut.recut_saved", "Остатки этого раскроя записаны на склад — запись будет отменена.", "Bu kroy qoldiqlari omborga yozilgan — yozuv bekor qilinadi.")
a("cut.delete", "Удаление раскроя", "Kroyni o'chirish"); a("cut.delete_q", "Удалить раскрой?", "Kroy o'chirilsinmi?")
a("cut.variants", "Сравнить варианты раскроя", "Kroy variantlarini solishtirish"); a("cut.edit", "Редактирование раскроя", "Kroyni tahrirlash")
a("cut.rest", "До кроить (только оставшиеся детали)", "Qolgan detallarni kroy qilish"); a("cut.comment", "Комментарий к карте", "Kartaga izoh")
a("cut.pp", "Постпроцессор (файл для станка)", "Postprotsessor (stanok fayli)")
a("cut.remnants_commit", "Деловые остатки → склад", "Deloviy qoldiqlar → ombor"); a("cut.remnants_saved", "Остатки записаны на склад", "Qoldiqlar omborga yozilgan")
a("cut.labels", "Этикетки деталей (QR)", "Detal etiketkalari (QR)"); a("cut.empty_hint", "Нажмите «Раскроить» — детали будут размещены на листах.", "«Kroy qilish» ni bosing.")
a("cut.no_parts", "Сначала добавьте детали на вкладке «Детали».", "Avval «Detallar» tabida detallar qo'shing.")
a("cut.first", "Первая", "Birinchi"); a("cut.prev", "Предыдущая", "Oldingi"); a("cut.next", "Следующая", "Keyingi"); a("cut.last", "Последняя", "Oxirgi")
a("cut.maps", "Карты кроя", "Kroy kartalari"); a("cut.commands", "Таблица команд", "Buyruqlar jadvali")
a("cut.cmd.code", "Кд", "Kd"); a("cut.cmd.size", "Р", "O'l"); a("cut.cmd.count", "К", "S"); a("cut.cmd.ref", "Д", "D")
a("cut.remnant_sheet", "остаток", "qoldiq"); a("cut.manual", "раскрой изменён вручную", "qo'lda tahrirlangan")
a("cut.done_count", "В цеху раскроено: {{d}}/{{c}}", "Sexda kesildi: {{d}}/{{c}}")

# editor
a("editor.title", "Редактирование раскроя", "Kroyni tahrirlash"); a("editor.horizontal", "Горизонтальный интерфейс", "Gorizontal joylashuv")
a("editor.h_shift", "выделить полосу (родителя)", "polosani (ota tugunni) tanlash"); a("editor.lmb", "Клик левой кнопкой мыши", "Sichqoncha chap tugmasi")
a("editor.h_left", "выделить / установить выбранную деталь на свободное место", "tanlash / tanlangan detalni bo'sh joyga qo'yish")
a("editor.h_alt", "установить деталь с поворотом", "detalni aylantirib qo'yish"); a("editor.rmb", "Клик правой кнопкой мыши", "O'ng tugma")
a("editor.h_right", "удалить деталь/полосу", "detal/polosani o'chirish")
a("editor.col.product", "Товар", "Mahsulot"); a("editor.col.qty", "Кол-во", "Soni"); a("editor.col.used", "Исп.", "Ishl."); a("editor.col.left", "Остаток", "Qoldi")
a("editor.add_map", "Добавить карту", "Karta qo'shish"); a("editor.delete_map", "Удалить карту", "Kartani o'chirish")
a("editor.delete_map_q", "Удалить текущую карту?", "Joriy karta o'chirilsinmi?"); a("editor.to_start", "В начало", "Boshiga"); a("editor.to_end", "В конец", "Oxiriga")
a("editor.rotate", "Развернуть резы (перекроить область в другом направлении)", "Kesish yo'nalishini almashtirish")
a("editor.expand", "Расширить полосу", "Polosani kengaytirish"); a("editor.auto_place", "Разместить выбранную деталь автоматически", "Tanlangan detalni avtomatik joylash")
a("editor.only_left", "Только неразмещённые", "Faqat joylanmaganlar"); a("editor.select_first", "Выделите деталь или полосу на карте", "Kartada detal yoki polosani tanlang")
a("editor.saved", "Раскрой сохранён", "Kroy saqlandi"); a("editor.discard_q", "Закрыть без сохранения изменений?", "O'zgarishlar saqlanmasdan yopilsinmi?")
a("editor.no_maps", "Нет карт — добавьте карту", "Kartalar yo'q — karta qo'shing")
a("editor.sel_part", "Деталь", "Detal"); a("editor.sel_free", "Свободное место", "Bo'sh joy"); a("editor.sel_strip", "Полоса", "Polosa")

# variants
a("variants.optimal", "Оптимальный", "Optimal"); a("variants.length", "Первый рез по длине", "1-kesim uzunlik bo'yicha")
a("variants.width", "Первый рез по ширине", "1-kesim en bo'yicha"); a("variants.sheets", "Листов", "Listlar")
a("variants.cuts", "Резов", "Kesimlar"); a("variants.remnant", "Деловой остаток", "Deloviy qoldiq"); a("variants.unplaced", "Не вместилось", "Sig'madi")
a("variants.time", "Время", "Vaqt"); a("variants.apply", "Применить выбранный", "Tanlanganini qo'llash"); a("variants.busy", "Расчёт трёх вариантов…", "Uchta variant hisoblanmoqda…")
a("variants.applied", "Вариант применён", "Variant qo'llandi")

# EL / GR
a("el.p.material", "Параметры материала", "Material parametrlari"); a("el.p.count_material", "Учитывать материал", "Materialni hisobga olish")
a("el.p.width", "Ширина", "En"); a("el.p.thickness", "Толщина", "Qalinlik"); a("el.p.thickness_hint", "Вычитается из размера детали (после прифуговки)", "Detal o'lchamidan ayriladi")
a("el.p.jointing", "Ширина прифуговки", "Prifugovka eni"); a("el.p.usage", "Расход материалов", "Material sarfi")
a("el.p.waste", "Процент отхода материала", "Chiqindi foizi"); a("el.p.overhang", "Длина остатка по краям", "Chetlardagi zapas uzunligi")
a("el.p.min_glue", "Мин. оклеиваемая длина", "Min. yopishtiriladigan uzunlik"); a("el.p.marking", "Обозначение", "Belgilash")
a("el.p.symbol", "Символ для обозначения", "Belgi"); a("el.p.one_char", "Только 1 символ", "Faqat 1 belgi"); a("el.p.color", "Цвет для обозначения", "Rang")
a("el.p.lines", "Линии маркировки", "Markirovka chiziqlari"); a("el.p.min_perp", "Мин. размер стороны детали, перпендикулярной кромке", "Kromkaga perpendikulyar tomonning min. o'lchami")
a("el.p.price", "Цена материала", "Material narxi"); a("el.p.mat_round", "Округление длины материала", "Material uzunligini yaxlitlash")
a("el.p.mat_len", "Длина материала", "Material uzunligi"); a("el.p.mat_cost", "Стоимость материала", "Material narxi (jami)")
a("el.p.op_price", "Цена операции (м)", "Ish narxi (m)"); a("el.p.work_round", "Округление длины кромкования", "Kromkalash uzunligini yaxlitlash")
a("el.p.work_len", "Длина кромкования (работа)", "Kromkalash uzunligi (ish)"); a("el.p.op_cost", "Стоимость операции", "Ish narxi (jami)")
a("el.p.cost", "Стоимость", "Jami narx"); a("el.p.description", "Описание", "Izoh")
a("el.round.0", "к ближайшему", "yaqiniga"); a("el.round.1", "к большему", "kattaga"); a("el.round.2", "к меньшему", "kichikka")
a("el.round_hint", "Код округления: число знаков после запятой и направление (как в отчёте)", "Yaxlitlash: kasr xonalari soni va yo'nalishi (hisobotdagi kabi)")
a("el.col.material", "Товар", "Material"); a("el.col.length", "Длина", "Uzunlik"); a("el.col.edges_len", "Окл. дл.", "Kr. uz.")
a("el.col.width", "Ширина", "En"); a("el.col.edges_wid", "Окл. шр.", "Kr. en"); a("el.col.qty", "ОК", "Jami")
a("el.col.edge_m", "Д-на кромки, м", "Kromka, m"); a("el.col.name", "Наименование", "Nomi")
a("el.total", "Итого", "Jami"); a("el.work", "работа", "ish"); a("el.material", "материал", "material")
a("el.defaults_saved", "Параметры кромки сохранены как стандартные", "Kromka parametrlari standart sifatida saqlandi")
a("gr.width", "Ширина паза", "Paz eni"); a("gr.depth", "Глубина", "Chuqurlik"); a("gr.offset", "Отступ от края", "Chetdan masofa")
a("gr.price", "Цена (м)", "Narx (m)"); a("gr.hint", "Паз назначается детали в окне «Свойства» или в колонках ПВ/ПН/ПЛ/ПП.", "Paz detal «Xossalar» oynasida yoki PV/PN/PL/PP ustunlarida belgilanadi.")

# XNC
a("xnc.tab.program", "Шаблон", "Dastur"); a("xnc.tab.cost", "Стоимость", "Narx"); a("xnc.program", "Программа", "Dastur")
a("xnc.empty", "Программа пуста — добавьте команды слева", "Dastur bo'sh — chapdan buyruq qo'shing"); a("xnc.add_param", "Параметр", "Parametr")
a("xnc.param_name", "Имя параметра", "Parametr nomi"); a("xnc.comment", "Комментарий", "Izoh")
a("xnc.drill_price", "Цена сверления", "Teshik narxi"); a("xnc.mill_price", "Цена фрезеровки (1 м)", "Frezalash narxi (1 m)")
a("xnc.saw_price", "Цена пиления (1 м)", "Arralash narxi (1 m)"); a("xnc.extra", "Дополнительная стоимость", "Qo'shimcha narx")
a("xnc.unit_cost", "Стоимость единицы", "Bir dona narxi"); a("xnc.qty", "Количество", "Soni"); a("xnc.op_cost", "Стоимость операции", "Ish narxi")
a("xnc.product", "Изделие", "Mahsulot"); a("xnc.material", "Материал", "Material"); a("xnc.detail", "Деталь", "Detal")
a("xnc.by_part", "По размеру детали", "Detal o'lchami bo'yicha"); a("xnc.face", "Лицевая сторона", "Old tomoni")
a("xnc.rotation", "Поворот", "Burish"); a("xnc.mirror", "Зеркало", "Ko'zgu"); a("xnc.origin", "Начало координат", "Koordinata boshi")
a("xnc.cost", "Стоимость", "Narx")
for cmd, ru, uz in [("Com", "Комментарий", "Izoh"), ("Par", "Параметр", "Parametr"), ("Var", "Переменная", "O'zgaruvchi"), ("Set", "Присвоить", "Qiymat berish"),
                    ("If", "Если", "Agar"), ("Else", "Иначе", "Aks holda"), ("While", "Цикл «пока»", "Sikl"), ("DoWhile", "Цикл с постусловием", "Sikl (keyin shart)"),
                    ("Break", "Прервать", "To'xtatish"), ("Continue", "Продолжить", "Davom"), ("Sub", "Подпрограмма", "Qism dastur"), ("Call", "Вызов", "Chaqirish"),
                    ("Ret", "Возврат", "Qaytish"), ("Msg", "Сообщение", "Xabar"), ("Err", "Ошибка", "Xato"), ("Tool", "Инструмент", "Asbob"),
                    ("DrillFront", "Сверление фронтальное", "Yuzadan teshik"), ("DrillLeft", "Сверление слева", "Chapdan teshik"),
                    ("DrillRight", "Сверление справа", "O'ngdan teshik"), ("DrillTop", "Сверление сверху", "Yuqoridan teshik"),
                    ("DrillBottom", "Сверление снизу", "Pastdan teshik"), ("MillStart", "Точка входа фрезы", "Freza kirish nuqtasi"),
                    ("MillLine", "Фрезерование: прямая", "Freza: to'g'ri chiziq"), ("MillArc", "Фрезерование: дуга (радиус)", "Freza: yoy (radius)"),
                    ("MillArcCenter", "Фрезерование: дуга с центром", "Freza: markazli yoy"), ("MillArc3P", "Фрезерование: дуга по 3 точкам", "Freza: 3 nuqtali yoy"),
                    ("MillFillet", "Скругление", "Yumaloqlash"), ("MillRect", "Фрезерование: прямоугольник", "Freza: to'rtburchak"),
                    ("MillEllipse", "Фрезерование: эллипс", "Freza: ellips"), ("Groove", "Пазование", "Paz"), ("Origin", "Начало координат", "Koordinata boshi")]:
    a(f"xnc.cmd.{cmd}", ru, uz)

# print
a("print.profile", "Профиль", "Profil"); a("print.standard", "Стандарт", "Standart"); a("print.new_profile", "Новый профиль печати", "Yangi chop profili")
a("print.profile_name", "Мой профиль", "Mening profilim"); a("print.delete_q", "Удалить профиль печати?", "Chop profili o'chirilsinmi?")
a("print.language", "Язык отчёта", "Hisobot tili"); a("print.sections", "Настройки печати", "Chop sozlamalari")
for k, ru, uz in [("general", "Общие", "Umumiy"), ("cs", "(CS) Детали и листы", "(CS) Detallar va listlar"), ("maps", "(CS) Карты кроя", "(CS) Kroy kartalari"),
                  ("header", "(CS) Заголовок карт", "(CS) Karta sarlavhasi"), ("el", "(EL) Кромка", "(EL) Kromka"), ("xnc", "(XNC) Обработка", "(XNC) Ishlov"),
                  ("labels", "Этикетки деталей (QR)", "Detal etiketkalari (QR)")]:
    a(f"print.sec.{k}", ru, uz)
for k, ru, uz in [("header", "Печать заголовка", "Sarlavha"), ("materials_list", "Материалы (список)", "Materiallar ro'yxati"),
                  ("warehouse", "Требование на склад", "Omborga talabnoma"), ("warehouse_cut_work", "Количество работы по резке", "Kesish ishi miqdori"),
                  ("warehouse_edge_work", "Длина кромки (работа)", "Kromka uzunligi (ish)"), ("products_list", "Изделия", "Mahsulotlar"),
                  ("operations", "Операции", "Operatsiyalar"), ("xnc_stats", "Обработка (статистика XNC)", "Ishlov (XNC statistikasi)"),
                  ("cs_parts", "Детали", "Detallar"), ("cs_unplaced", "Невместившиеся детали", "Sig'magan detallar"), ("cs_sheets", "Листы", "Listlar"),
                  ("cs_remnants", "Остатки", "Qoldiqlar"), ("cs_maps", "Карты кроя", "Kroy kartalari"), ("cs_commands", "Таблица команд у карт", "Kartalar yonida buyruqlar"),
                  ("cs_size_mode", "Режим размеров деталей", "Detal o'lchamlari rejimi"), ("map_parts_list", "Список деталей у карты", "Karta yonida detallar ro'yxati"),
                  ("map_part_label", "Подпись детали", "Detal yozuvi"), ("map_edges", "Кромки линиями", "Kromkalar chiziq bilan"),
                  ("map_remnant_number", "Номер остатка", "Qoldiq raqami"), ("map_qr", "Штрихкод QRCode на карте", "Kartada QR kod"),
                  ("map_mirror", "Зеркально", "Ko'zgu"), ("el_params", "Параметры кромки", "Kromka parametrlari"), ("el_parts", "Детали с кромкой", "Kromkali detallar"),
                  ("el_header_work", "В заголовке деталей: длина кромкования (работа)", "Detallar sarlavhasida: kromkalash uzunligi (ish)"),
                  ("el_header_material", "В заголовке деталей: длина материала", "Detallar sarlavhasida: material uzunligi"),
                  ("xnc_drawing", "Чертежи деталей XNC", "XNC detal chizmalari")]:
    a(f"print.f.{k}", ru, uz)
for k, ru, uz in [("number", "Номер", "Raqam"), ("name", "Наименование", "Nomi"), ("number_name", "Номер и наименование", "Raqam va nomi")]:
    a(f"print.label.{k}", ru, uz)
for k, ru, uz in [("N", "номер карты / всего", "karta / jami"), ("S", "размер листа", "list o'lchami"), ("C", "листов по карте / всего", "listlar / jami"),
                  ("Cp", "деталей на карте / всего", "detallar / jami"), ("LT", "длина реза, м", "kesish uzunligi, m"), ("CT", "количество резов", "kesimlar soni"),
                  ("F", "заполнение, %", "to'ldirish, %"), ("AP", "площадь деталей, м²", "detallar maydoni, m²"), ("AM", "площадь листа, м²", "list maydoni, m²"),
                  ("AW", "деловой остаток, м²", "deloviy qoldiq, m²")]:
    a(f"print.hf.{k}", ru, uz)
a("print.header_hint", "Показатели в заголовке каждой карты кроя.", "Har kroy kartasi sarlavhasidagi ko'rsatkichlar.")
a("print.project_mode", "Как в проекте", "Loyihadagidek"); a("print.save_profile", "Сохранить настройки в профиль", "Sozlamalarni profilga saqlash")
a("print.open_project", "Откройте проект, чтобы напечатать отчёт.", "Hisobot uchun loyihani oching.")
a("print.print", "Печать", "Chop etish"); a("print.open", "Открыть в новом окне", "Yangi oynada ochish")
a("print.pdf_hint", "PDF: в окне печати выберите «Сохранить как PDF»", "PDF: chop oynasida «PDF sifatida saqlash» ni tanlang")
a("print.lbl.op", "Материал", "Material"); a("print.lbl.all", "Все материалы", "Barcha materiallar"); a("print.lbl.width", "Ширина этикетки", "Etiketka eni")
a("print.lbl.height", "Высота этикетки", "Etiketka balandligi"); a("print.lbl.columns", "Колонок на A4", "A4 da ustunlar")
a("print.lbl.columns_hint", "0 — термопринтер (по одной этикетке на страницу)", "0 — termoprinter (har sahifada bitta)")
a("print.lbl.qr", "QR-код (для сканера MES)", "QR kod (MES skaneri uchun)"); a("print.lbl.show_edges", "Схема кромок", "Kromka sxemasi")
a("print.lbl.show_product", "Изделие", "Mahsulot"); a("print.lbl.show_map", "Номер карты кроя", "Kroy kartasi raqami")
a("print.lbl.hint", "Этикетки печатаются в порядке выхода деталей из пилы (по картам).", "Etiketkalar arradan chiqish tartibida (kartalar bo'yicha).")

# settings
for k, ru, uz in [("general", "Общие", "Umumiy"), ("pp", "Постпроцессоры", "Postprotsessorlar"), ("remnants", "Склад остатков", "Qoldiqlar ombori"),
                  ("catalog", "Каталог товаров", "Tovarlar katalogi"), ("mes", "MES интеграция", "MES integratsiyasi"), ("backup", "Загрузить / выгрузить настройки", "Sozlamalarni yuklash / chiqarish")]:
    a(f"settings.page.{k}", ru, uz)
a("settings.currency", "Валюта по умолчанию", "Standart valyuta"); a("settings.language", "Язык интерфейса", "Interfeys tili")
a("settings.input_mode", "Режим ввода деталей (предлагать)", "Detal kiritish rejimi (taklif)"); a("settings.no_suggest", "Не предлагать", "Taklif qilmaslik")
a("settings.input_mode_hint", "Какой режим ввода размеров предлагать для новых проектов", "Yangi loyihalar uchun qaysi o'lcham rejimini taklif qilish")
a("settings.remnant_confirm", "После раскроя предлагать записать деловые остатки на склад", "Kroydan keyin qoldiqlarni omborga yozishni taklif qilish")
a("settings.default_sheet", "Размер листа по умолчанию", "Standart list o'lchami")
a("settings.fullscreen_hint", "Совет: меню «Проект → Полный экран» включает все сочетания клавиш (Ctrl+W, Ctrl+PgUp), которые браузер иначе перехватывает.",
  "Maslahat: «Loyiha → To'liq ekran» brauzer band qiladigan yorliqlarni (Ctrl+W, Ctrl+PgUp) ham yoqadi.")
a("pp_ed.new", "Новый", "Yangi"); a("pp_ed.builtin", "Встроенные", "O'rnatilgan"); a("pp_ed.user", "Станки предприятия", "Korxona stanoklari")
a("pp_ed.name", "Наименование", "Nomi"); a("pp_ed.ext", "Расширение", "Kengaytma"); a("pp_ed.encoding", "Кодировка", "Kodlash")
a("pp_ed.newline", "Конец строки", "Qator oxiri"); a("pp_ed.per_map", "Отдельный файл на каждую карту (zip)", "Har karta alohida fayl (zip)")
a("pp_ed.context", "Какие данные доступны в шаблоне", "Shablonda qanday ma'lumotlar bor")
a("pp_ed.context_doc", """project — {name, number, customer, order_date, ready_date, currency, mes_order_ref}
op      — {name, code, thickness, kerf, trim_length, trim_width, sheets_per_pack}
maps    — [{index, copies, packs, sheet_length, sheet_width, is_remnant, fill, cut_length_m, cuts,
            placements: [{n, uid, name, code, x, y, length, width, rotated, edges}],
            commands:   [{n, code, level, size, count, ref}],      code: T/C/P/W, level: 1..6
            remnants:   [{number, x, y, length, width, business}]}]
parts   — [{uid, name, code, length, width, qty, used, left, grain, edges}]
map     — текущая карта (если «отдельный файл на карту»)
f(v, n=1) — число с точкой; now — дата-время
machine — {key, name, group, params, label_fields} при выборе станка (иначе None); placements[].label — «Данные для этикеток»; label_warnings — ошибки выражений
Синтаксис: {{ выражение }}, {% for ... %} ... {% endfor %}, {% if ... %} ... {% endif %}""",
  """project — {name, number, customer, order_date, ready_date, currency, mes_order_ref}
op      — {name, code, thickness, kerf, trim_length, trim_width, sheets_per_pack}
maps    — [{index, copies, packs, sheet_length, sheet_width, is_remnant, fill, cut_length_m, cuts,
            placements: [{n, uid, name, code, x, y, length, width, rotated, edges}],
            commands:   [{n, code, level, size, count, ref}],      code: T/C/P/W, level: 1..6
            remnants:   [{number, x, y, length, width, business}]}]
parts   — [{uid, name, code, length, width, qty, used, left, grain, edges}]
map     — joriy karta («har karta alohida fayl» yoqilgan bo'lsa)
f(v, n=1) — sonni formatlash; now — sana-vaqt
machine — stanok tanlanganda {key, name, group, params, label_fields} (aks holda None); placements[].label — «Данные для этикеток»; label_warnings — ifoda xatolari
Sintaksis: {{ ifoda }}, {% for ... %} ... {% endfor %}, {% if ... %} ... {% endif %}""")
a("pp_ed.preview", "Проверить на раскрое", "Kroyda tekshirish"); a("pp_ed.no_sample", "Откройте проект с раскроем", "Kroyli loyihani oching")
a("pp_ed.files", "OK, файлов: {{n}}", "OK, fayllar: {{n}}"); a("pp_ed.choose", "Выберите или создайте постпроцессор", "Postprotsessorni tanlang yoki yarating")
a("pp_ed.delete_q", "Удалить постпроцессор?", "Postprotsessor o'chirilsinmi?")
a("pp_ed.new_name", "Новый станок", "Yangi stanok")
a("pp.builtin.csv", "CSV — список резки", "CSV — kesish ro'yxati")
a("pp.builtin.commands", "Команды резки (TXT, для оператора)", "Kesish buyruqlari (TXT, operator uchun)")
a("pp.builtin.dxf", "DXF — карты раскроя (CAD/CAM)", "DXF — kroy kartalari (CAD/CAM)")
a("pp.builtin.json", "MES JSON — полный результат", "MES JSON — to'liq natija")
a("colset.auto", "авто", "avto")
a("cut.view_settings", "Настройки", "Sozlamalar"); a("cut.show_commands", "Показывать таблицу команд", "Buyruqlar jadvalini ko'rsatish")
a("products.settings", "Настройки", "Sozlamalar")
a("cut.packs", "Пакеты", "Paketlar")
a("cut.packs_hint", "Пакетов (циклов пилы) на карте / всего; листов в пакете: {{n}}", "Kartadagi / jami paketlar (arra sikllari); paketda {{n}} list")
a("print.hf.PK", "пакеты: на карте / всего × листов в пакете", "paketlar: kartada / jami × paketdagi listlar")
a("el.narrow", "{{n}} дет. — сторона, перпендикулярная кромке, меньше {{mm}} мм", "{{n}} detal — kromkaga perpendikulyar tomon {{mm}} mm dan kichik")
a("parts.small", "Мелкие: {{n}}", "Kichik: {{n}}")
a("parts.small_hint", "Детали со стороной меньше «Мин. размера детали» ({{mm}} мм): резать опасно — сгруппируйте в блок (Свойства → Группировка)",
  "Tomoni «Min. detal o'lchami» ({{mm}} mm) dan kichik detallar: kesish xavfli — blokka guruhlang (Xossalar → Guruhlash)")
a("cs.p.kerf_group_hint", "Пропил между деталями блока (группировка). Пусто — как основной пропил", "Blok (guruh) detallari orasidagi propil. Bo'sh — asosiy propil")
a("cs.p.pack_hint", "Максимальная высота подъёма пилы. Листов в пакете (Кратность) = Высота пакета ÷ толщина материала",
  "Arraning maksimal ko'tarilish balandligi. Paketdagi listlar (Karralik) = Paket balandligi ÷ material qalinligi")
a("cs.p.fill_packet_hint", "Карта с заполнением не ниже этого % повторяется на следующих листах (резка пакетом)",
  "To'ldirish shu % dan kam bo'lmagan karta keyingi listlarda takrorlanadi (paketda kesish)")
a("cs.p.big_pack_hint", "При равном числе листов выбирается раскрой с меньшим числом разных карт (больше одинаковых листов в пакете)",
  "Listlar soni teng bo'lsa — kamroq turli kartali kroy tanlanadi (paketda ko'proq bir xil list)")
a("cs.p.complex_hint", "Полосы переменной ширины из нескольких рядов деталей. Выключено — только простые полосы",
  "Bir necha qator detaldan iborat o'zgaruvchan enli polosalar. O'chiq — faqat oddiy polosalar")
a("cs.p.merge_hint", "В MebeliX всегда включено: одинаковые детали объединяются при раскрое автоматически",
  "MebeliX da doim yoqilgan: bir xil detallar kroyda avtomatik birlashtiriladi")
a("cs.p.save_draw_hint", "В MebeliX всегда включено: карты раскроя сохраняются вместе с проектом",
  "MebeliX da doim yoqilgan: kroy kartalari loyiha bilan birga saqlanadi")
a("cs.p.min_part_hint", "Детали со стороной меньше этого размера в раскрой не входят (будет предупреждение); сгруппируйте их в блок",
  "Tomoni bundan kichik detallar kroyga kirmaydi (ogohlantirish chiqadi); ularni blokka guruhlang")
a("warn_small_parts", "{{n}} дет. меньше «Мин. размер детали» ({{mm}} мм) — не вошли в раскрой",
  "{{n}} ta detal «Min. detal o'lchami» ({{mm}} mm) dan kichik — kroyga kirmadi")
a("pp.group_hint", "По длине: блок = k × длина + пропилы; по ширине: блок = k × ширина + пропилы. Блок кроится как одна деталь и режется на детали пропилом для групповых деталей. 0 — без ограничения",
  "Uzunlik bo'yicha: blok = k × uzunlik + propillar; en bo'yicha: blok = k × en + propillar. Blok bitta detal kabi kroy qilinadi va guruh propili bilan detallarga bo'linadi. 0 — cheklanmagan")
a("catalog.all", "Все", "Hammasi"); a("catalog.kind", "Тип", "Tur"); a("catalog.code", "Код", "Kod"); a("catalog.name", "Наименование", "Nomi")
a("catalog.thickness", "Толщ.", "Qalinlik"); a("catalog.size", "Размер", "O'lcham"); a("catalog.price", "Цена", "Narx"); a("catalog.stock", "Склад", "Omborda")
a("catalog.unit", "Ед.", "Birlik"); a("catalog.import", "Импорт из Excel", "Excel dan import"); a("catalog.default_kind", "Тип по умолчанию", "Standart tur")
a("catalog.delete_q", "Удалить товар из каталога?", "Tovar katalogdan o'chirilsinmi?")
a("catalog.empty_hint", "Каталог пуст. Он заполняется из MES (POST /api/catalog/sync) или импортом Excel в «Настройки → Каталог товаров».",
  "Katalog bo'sh. U MES dan (POST /api/catalog/sync) yoki «Sozlamalar → Tovarlar katalogi» da Excel importi orqali to'ldiriladi.")
a("catalog.mes_hint", "Каталог синхронизируется из MES через API; здесь можно загрузить его из Excel.", "Katalog MES dan API orqali keladi; bu yerda Excel dan yuklash mumkin.")
for k, ru, uz in [("sheet", "Лист", "List"), ("edge", "Кромка", "Kromka"), ("linear", "Погонаж", "Pogonaj"), ("surface", "Поверхность", "Sirt"), ("folder", "Папка", "Papka")]:
    a(f"catalog.kinds.{k}", ru, uz)
for k, ru, uz in [("id", "ID", "ID"), ("parent_id", "Родит. ID", "Ota ID"), ("code", "Код", "Kod"), ("name", "Наименование", "Nomi"), ("unit", "Ед.изм", "Birlik"),
                  ("price", "Цена", "Narx"), ("stock", "Склад", "Ombor"), ("thickness", "Толщина", "Qalinlik"), ("length", "Длина", "Uzunlik"),
                  ("width", "Ширина", "En"), ("kind", "Тип", "Tur")]:
    a(f"catalog.f.{k}", ru, uz)
a("mes.intro", "MebeliX Kroy подключается к MES через REST API. Основные точки:", "MebeliX Kroy MES ga REST API orqali ulanadi. Asosiy nuqtalar:")
a("mes.ep.orders", "принять заказ MES → создать проект (материалы, кромки, детали)", "MES buyurtmasi → loyiha")
a("mes.ep.order", "результат по заказу (расход, остатки, стоимость, карты)", "buyurtma natijasi (sarf, qoldiq, narx, kartalar)")
a("mes.ep.export", "то же по ID проекта", "loyiha ID bo'yicha")
a("mes.ep.catalog", "материалы и цены из MES", "MES dan materiallar va narxlar"); a("mes.ep.scan", "QR этикетки/карты → информация", "Etiketka/karta QR → ma'lumot")
a("mes.ep.done", "карта раскроена в цеху (+1)", "karta sexda kesildi (+1)"); a("mes.ep.remnants", "склад деловых остатков", "deloviy qoldiqlar ombori")
a("mes.webhook", "Webhook: при смене статуса проекта, после раскроя и при отметке карты отправляется POST на MES_WEBHOOK_URL (Bearer MES_WEBHOOK_TOKEN).",
  "Webhook: loyiha holati o'zgarsa, kroydan keyin va karta belgilanganda MES_WEBHOOK_URL ga POST yuboriladi (Bearer MES_WEBHOOK_TOKEN).")
a("mes.test", "Отправить тестовый webhook", "Sinov webhook yuborish"); a("mes.sent", "Отправлено: {{url}}", "Yuborildi: {{url}}")
a("mes.jwt", "Если сервер работает с MEBELIX_AUTH_REQUIRED=1, вставьте JWT-токен MES SSO (или откройте приложение по ссылке ?token=...).",
  "Server MEBELIX_AUTH_REQUIRED=1 bilan ishlasa, MES SSO JWT tokenini kiriting (yoki ?token=... havolasi bilan oching).")
a("mes.logout", "Выйти", "Chiqish")
# MES bo'limi (chap panel): yoqilmaguncha xira; ichida integratsiya paneli karkasi
a("menu.mes", "MES", "MES"); a("menu.mes_off", "Включите в «Настройки → MES интеграция»", "«Sozlamalar → MES integratsiyasi» da yoqing")
a("mes.enable", "Включить интеграцию с MES", "MES bilan integratsiyani yoqish")
a("mes.enable_hint", "Пока выключено, пункт «MES» в левом меню серый и не нажимается. Включите, когда MES подключена: откроется панель интеграции.",
  "O'chiq bo'lsa, chap paneldagi «MES» bandi xira va bosilmaydi. MES ulangach yoqing: integratsiya paneli ochiladi.")
a("mes.enabled_on", "Интеграция с MES включена", "MES integratsiyasi yoqildi"); a("mes.enabled_off", "Интеграция с MES выключена", "MES integratsiyasi o'chirildi")
for k, ru, uz in [("overview", "Обзор", "Umumiy ko'rinish"), ("orders", "Заказы MES", "MES buyurtmalari"), ("results", "Отправка результатов", "Natijalarni yuborish"),
                  ("stock", "Склад и каталог", "Ombor va katalog"), ("log", "Журнал обмена", "Almashinuv jurnali"), ("api", "Связь и API", "Aloqa va API")]:
    a(f"mes.page.{k}", ru, uz)
for k, ru, uz in [("fetch", "Получить заказы", "Buyurtmalarni olish"), ("create_project", "Создать проект", "Loyiha yaratish"),
                  ("send", "Отправить результат", "Natijani yuborish"), ("retry", "Повторить", "Qayta yuborish"),
                  ("sync_remnants", "Синхронизировать остатки", "Qoldiqlarni sinxronlash"), ("sync_catalog", "Синхронизировать каталог", "Katalogni sinxronlash"),
                  ("refresh", "Обновить", "Yangilash")]:
    a(f"mes.act.{k}", ru, uz)
for k, ru, uz in [("ref", "№ заказа MES", "MES buyurtma №"), ("project", "Проект", "Loyiha"), ("status", "Статус", "Holat"), ("date", "Дата", "Sana"),
                  ("received", "Получен", "Qabul qilingan"), ("operation", "Операция", "Operatsiya"), ("maps", "Карты", "Kartalar"), ("sent", "Отправлен", "Yuborilgan"),
                  ("material", "Материал", "Material"), ("qty", "Кол-во (Kroy)", "Soni (Kroy)"), ("mes_qty", "Кол-во (MES)", "Soni (MES)"), ("diff", "Разница", "Farq"),
                  ("time", "Время", "Vaqt"), ("direction", "Направление", "Yo'nalish"), ("event", "Событие", "Hodisa")]:
    a(f"mes.col.{k}", ru, uz)
a("mes.stub.orders", "Заказы, пришедшие из MES: номер, проект, статус. Сейчас заказ принимается вызовом POST /api/mes/orders.",
  "MES dan kelgan buyurtmalar: raqam, loyiha, holat. Hozir buyurtma POST /api/mes/orders chaqiruvi bilan qabul qilinadi.")
a("mes.stub.results", "Результат раскроя (карты, расход, остатки, стоимость) и статусы, отправляемые в MES.",
  "Kroy natijasi (kartalar, sarf, qoldiq, narx) va MES ga yuboriladigan holatlar.")
a("mes.stub.stock", "Сверка складов остатков и каталога материалов с MES.", "Qoldiqlar ombori va material katalogini MES bilan solishtirish.")
a("mes.stub.log", "Журнал входящих и исходящих событий обмена с MES.", "MES bilan almashinuvning kiruvchi va chiquvchi hodisalari jurnali.")
a("mes.stub.empty", "Данных пока нет", "Hozircha ma'lumot yo'q")
a("mes.stub.note", "Раздел-заготовка: подключение к реальной MES выполняет команда разработчиков MES; кнопки станут активными после подключения.",
  "Karkas bo'lim: haqiqiy MES bilan ulashni MES dasturchilari jamoasi bajaradi; tugmalar ulangach faollashadi.")
a("mes.ov.state", "Состояние связи", "Aloqa holati"); a("mes.ov.state_stub", "не подключена (заготовка)", "ulanmagan (karkas)")
a("mes.ov.rest", "Приём заказов и результатов", "Buyurtma va natijalarni qabul qilish"); a("mes.ov.rest_v", "REST API доступен (см. «Связь и API»)", "REST API tayyor («Aloqa va API» ga qarang)")
a("mes.ov.gibsaw", "Цеховой экран (GibSaw)", "Sex ekrani (GibSaw)"); a("mes.ov.gibsaw_v", "работает в составе MES предприятия", "korxona MES tarkibida ishlaydi")
a("mes.ov.plan", "Запланированные разделы:", "Rejalashtirilgan bo'limlar:")
a("xnc.enabled", "Включить", "Yoqish")
# Postprotsessorlar: stanok nomlari ro'yxati (format mantig'ini korxona dasturchilari qo'shadi)
a("pp.machines", "Станки", "Stanoklar"); a("pp.group.saw", "Пильные центры", "Pil markazlari"); a("pp.group.cnc", "Обрабатывающие центры (XNC)", "Ishlov markazlari (XNC)")
a("pp.machine_enable", "Станок используется на предприятии (показывать в «Постпроцессор»)", "Stanok korxonada ishlatiladi («Postprotsessor» ro'yxatida ko'rsatiladi)")
a("pp.machine_template", "Шаблон формата", "Format shabloni"); a("pp.machine_none", "— не подключён —", "— ulanmagan —")
a("pp.machine_bound", "Формат: «{{n}}»", "Format: «{{n}}»")
a("pp.machine_unbound_note", "Формат этого станка ещё не подключён: выберите шаблон из списка «Станки предприятия» или добавьте новый.",
  "Bu stanokning formati hali ulanmagan: «Korxona stanoklari» ro'yxatidan shablonni tanlang yoki yangisini qo'shing.")
a("pp.machine_hint", "Названия станков — готовый список; сам формат файла задаёт шаблон (Jinja) либо внешний постпроцессор предприятия.",
  "Stanok nomlari tayyor ro'yxat; fayl formatini shablon (Jinja) yoki korxonaning tashqi postprotsessori belgilaydi.")
a("pp.machine_prefix", "Добавлять имя станка в начало имени файла", "Fayl nomi boshiga stanok nomini qo'shish")
a("pp.machine_unbound", "формат не подключён", "format ulanmagan")
a("backup.hint", "Сохраните все профили (стандартные параметры, печать, колонки, постпроцессоры) в файл или загрузите их на другой компьютер.",
  "Barcha profillarni faylga saqlang yoki boshqa kompyuterga yuklang.")
a("backup.export", "Экспорт профилей", "Profillarni eksport"); a("backup.import", "Импорт профилей", "Profillarni import")
a("backup.imported", "Импортировано профилей: {{n}}", "Import qilingan profillar: {{n}}")

# help
for k, ru, uz in [("keys", "Сочетания клавиш", "Klaviatura yorliqlari"), ("flow", "Порядок работы", "Ish tartibi"), ("cut", "Раскрой и редактирование", "Kroy va tahrir"),
                  ("edge", "Кромка: формулы", "Kromka: formulalar"), ("mes", "MES и цех", "MES va sex"), ("about", "О программе", "Dastur haqida")]:
    a(f"help.topic.{k}", ru, uz)
a("help.key", "Клавиши", "Tugmalar"); a("help.action", "Действие", "Amal")
for k, ru, uz in [("undo_redo", "Отменить / Вернуть", "Bekor qilish / Qaytarish"), ("clone", "Клонировать", "Nusxalash"), ("delete", "Удалить", "O'chirish"),
                  ("move_updown", "Переместить вверх / вниз", "Yuqoriga / pastga"), ("properties", "Свойства (в списке проектов — открыть)", "Xossalar (ro'yxatda — ochish)"),
                  ("insert_row", "Вставить строку", "Qator qo'yish"), ("add_row", "Добавить строку в конец", "Oxiriga qator qo'shish"),
                  ("space_edges", "Ткт / кромка: смена (Space), кромка по периметру (Shift+Space)", "Ткт / kromka: almashtirish (Space), perimetr bo'yicha kromka (Shift+Space)"),
                  ("paste", "Вставить из буфера (Excel)", "Buferdan (Excel) qo'yish"),
                  ("group", "Групповые действия", "Guruhli amallar"), ("grain_off_on", "Снять / установить текстуру", "Teksturani olish / qo'yish"),
                  ("swap", "Поменять длину и ширину", "Uzunlik ↔ en"), ("move_to_op", "Перенести в другую операцию", "Boshqa operatsiyaga ko'chirish"),
                  ("columns", "Настройки колонок (в раскрое — подписи деталей)", "Ustunlar sozlamasi"), ("filter", "Фильтр (нулевые / не вошедшие)", "Filtr"),
                  ("help", "Справка", "Yordam"), ("maps_nav", "Навигация по картам кроя", "Kroy kartalari bo'ylab"),
                  ("editor_keys", "Редактор: развернуть резы / расширить полосу / клонировать / в начало-конец", "Tahrir: yo'nalish / kengaytirish / nusxa / boshi-oxiri")]:
    a(f"help.hk.{k}", ru, uz)
a("help.keys_note", "Ctrl+W и Ctrl+PgUp браузер использует сам: используйте Alt+W / Alt+PgUp / Insert или включите «Полный экран» в меню «Проект».",
  "Ctrl+W va Ctrl+PgUp ni brauzer o'zi band qiladi: Alt+W / Alt+PgUp / Insert dan foydalaning yoki «Loyiha» menyusida «To'liq ekran» ni yoqing.")
a("help.text.flow", """1. Проекты → «Добавить» (или заказ приходит из MES автоматически).
2. Операции: добавьте (CS) Листовой раскрой — по одной операции на материал; (EL) Кромка — по одной на тип кромки.
3. Вкладка «Детали»: вводите Наименование → Enter → Длина → Ширина → Кол-во (новая строка внизу), или вставьте из Excel (Ctrl+V).
   Колонки ОВ/ОН (по длине) и ОЛ/ОП (по ширине) — выберите операцию кромки.
4. «Листы и остатки»: размер листа; кнопка «склад» добавляет деловые остатки со склада.
5. «Раскрой» → «Раскроить». Можно сравнить варианты, отредактировать вручную, «До кроить».
6. После раскроя деловые остатки записываются на склад (с подтверждением).
7. «Печать отчета»: требование на склад, детали, листы, карты кроя с QR, кромка, этикетки деталей.
8. Постпроцессор выгружает файл для станка по шаблону предприятия.""",
  """1. Loyihalar → «Qo'shish» (yoki buyurtma MES dan avtomatik keladi).
2. Operatsiyalar: (CS) Listli kroy — har material uchun bittadan; (EL) Kromka — har kromka turi uchun.
3. «Detallar»: Nomi → Enter → Uzunlik → En → Soni (pastdagi yangi qator), yoki Excel dan Ctrl+V.
   OV/ON (uzunlik bo'ylab) va OL/OP (en bo'ylab) ustunlarida kromkani tanlang.
4. «Listlar va qoldiqlar»: list o'lchami; «ombor» tugmasi ombordagi qoldiqlarni qo'shadi.
5. «Kroy» → «Kroy qilish». Variantlarni solishtirish, qo'lda tahrirlash, «qolganlarini kroy» mumkin.
6. Kroydan keyin deloviy qoldiqlar omborga yoziladi (tasdiq bilan).
7. «Hisobot chop etish»: omborga talabnoma, detallar, listlar, QR kodli kartalar, kromka, etiketkalar.
8. Postprotsessor korxona shabloni bo'yicha stanok faylini beradi.""")
a("help.text.cut", """Алгоритм: многоуровневый гильотинный раскрой (уровни = «Максимальное количество вращений»), учёт пропила, торцовки, минимальной обрезки и текстуры.
Строка статуса: № карта/всего · S размер листа · C листов/всего · Cp деталей · LT длина реза, м · F заполнение (детали ÷ (лист − деловой остаток)).
Таблица команд: T — торцовка, C — рез, P — рез детали, W — остаток; цифра — уровень.
Редактор: выберите деталь в списке и щёлкните по свободному (серому) месту — деталь встанет в угол; Alt/Ctrl — с поворотом; правая кнопка — удалить; Shift — выделить полосу.
Каждое действие проверяется: наложение, пропил, минимальная обрезка, число деталей и листов.""",
  """Algoritm: ko'p darajali gilyotina kroy (darajalar = «Maksimal aylanishlar soni»), propil, torsovka, minimal qirqim va tekstura hisobga olinadi.
Holat qatori: № karta/jami · S list o'lchami · C listlar · Cp detallar · LT kesish uzunligi, m · F to'ldirish (detallar ÷ (list − deloviy qoldiq)).
Buyruqlar: T — torsovka, C — kesim, P — detal kesimi, W — qoldiq; raqam — daraja.
Tahrir: ro'yxatdan detalni tanlab, bo'sh (kulrang) joyni bosing — detal burchakka qo'yiladi; Alt/Ctrl — aylantirib; o'ng tugma — o'chirish; Shift — polosani tanlash.
Har amal tekshiriladi: ustma-ust, propil, minimal qirqim, detal va list soni.""")
a("help.text.edge", """Размеры: деталь (с кромкой) → после прифуговки = деталь − толщина кромки → заготовка = + ширина прифуговки → пильный = + припуски.
Кромки ОВ/ОН идут по длине (уменьшают ширину), ОЛ/ОП — по ширине (уменьшают длину).
Расход: материал = Σ(сторона + 2 × длина остатка по краям) × (1 + отход %); работа = Σ max(сторона, мин. оклеиваемая длина).""",
  """O'lchamlar: detal (kromka bilan) → prifugovkadan keyin = detal − kromka qalinligi → zagotovka = + prifugovka eni → arra o'lchami = + pripusklar.
OV/ON kromkalar uzunlik bo'ylab (enni kamaytiradi), OL/OP — en bo'ylab (uzunlikni kamaytiradi).
Sarf: material = Σ(tomon + 2 × chetdagi zapas) × (1 + chiqindi %); ish = Σ max(tomon, min. yopishtiriladigan uzunlik).""")
a("help.text.mes", """Заказы приходят из MES (POST /api/mes/orders) — проект создаётся автоматически с операциями по материалам и кромкам.
На каждой карте кроя и этикетке детали — QR-код. В цеху режим «Цех (сканер QR)» (#/sex): сканируйте карту → «Раскроено» (+1), статус уходит в MES через webhook.
Склад деловых остатков общий для всех проектов.""",
  """Buyurtmalar MES dan keladi (POST /api/mes/orders) — loyiha materiallar va kromkalar bo'yicha avtomatik yaratiladi.
Har kroy kartasi va detal etiketkasida QR kod bor. Sexda «Sex rejimi (QR skaner)» (#/sex): kartani skanerlang → «Kesildi» (+1), holat webhook orqali MES ga ketadi.
Deloviy qoldiqlar ombori barcha loyihalar uchun umumiy.""")
a("help.text.about", """MebeliX Kroy — программа раскроя листовых материалов для мебельного производства, интегрированная с MES.
Код написан с нуля; иконки — Lucide (открытая лицензия); таблицы — AG Grid Community.""",
  """MebeliX Kroy — mebel ishlab chiqarish uchun listli materiallarni kroy qilish dasturi, MES bilan integratsiyalangan.
Kod noldan yozilgan; ikonkalar — Lucide (ochiq litsenziya); jadvallar — AG Grid Community.""")

# workshop
a("ws.title", "Цех — сканер QR", "Sex — QR skaner"); a("ws.back", "Назад", "Orqaga"); a("ws.placeholder", "Отсканируйте QR карты кроя или этикетки детали…", "Kroy kartasi yoki etiketka QR kodini skanerlang…")
a("ws.find", "Найти", "Topish"); a("ws.hint", "Наведите сканер на QR-код — данные появятся здесь.", "Skanerni QR kodga tuting — ma'lumot shu yerda chiqadi.")
a("ws.project", "Проект", "Loyiha"); a("ws.product", "Изделие", "Mahsulot"); a("ws.material", "Материал", "Material"); a("ws.copy", "Экземпляр", "Nusxa")
a("ws.edges", "Кромки", "Kromkalar"); a("ws.maps", "Карты кроя", "Kroy kartalari"); a("ws.map", "Карта", "Karta"); a("ws.cut", "Раскроено", "Kesildi")
a("ws.mark", "Раскроено +1", "Kesildi +1"); a("ws.marked", "Отмечено", "Belgilandi")
a("print.margins", "Поля страницы", "Sahifa chegaralari")
for k, ru, uz in [("left", "Слева", "Chapdan"), ("right", "Справа", "O'ngdan"), ("top", "Сверху", "Yuqoridan"), ("bottom", "Снизу", "Pastdan")]:
    a(f"print.margin.{k}", ru, uz)
# kroy kartasi ko'rsatkichlari (status qatori, Ctrl+P)
a("cut.indicators", "Показатели в строке состояния", "Holat qatoridagi ko'rsatkichlar")
a("cut.ind_reset", "Восстановить значения по умолчанию", "Standart qiymatlarni tiklash")
for k, ru, uz in [("num", "Номер карты раскроя / Общее количество карт", "Karta raqami / Jami kartalar"),
                  ("S", "Размер листа (Длина / Ширина)", "List o'lchami (Uzunlik / En)"),
                  ("C", "Количество листов в карте / Общее количество листов", "Kartadagi listlar / Jami listlar"),
                  ("Cp", "Количество деталей на карте / Общее количество деталей", "Kartadagi detallar / Jami detallar"),
                  ("LT", "Длина реза на карте / Общая длина реза, м", "Kartadagi kesish uzunligi / Jami, m"),
                  ("F", "Процент заполнения на карте / Общий", "Kartaning to'ldirilishi / Umumiy"),
                  ("R", "Процент отхода на карте / Общий", "Kartadagi chiqindi foizi / Umumiy"),
                  ("CT", "Количество резов на карте / Общее", "Kartadagi kesimlar soni / Jami"),
                  ("T", "Торцовка по длине / по ширине листа", "Torsovka: uzunlik / en bo'yicha"),
                  ("AP", "Площадь деталей на карте / Общая, м²", "Kartadagi detallar maydoni / Jami, m²"),
                  ("AM", "Площадь материала на карте / Общая, м²", "Karta material maydoni / Jami, m²"),
                  ("AW", "Площадь деловых остатков на карте / Общая, м²", "Kartadagi deloviy qoldiqlar / Jami, m²")]:
    a(f"cut.ind.{k}", ru, uz)

# ── mahsulot «Свойства» oynasi ──
a("pprops.title", "Свойства", "Xossalar"); a("pprops.tab", "Свойства", "Xossalar")
a("pprops.g.general", "Общие", "Umumiy"); a("pprops.name", "Наименование", "Nomi"); a("pprops.code", "Код", "Kod")
a("pprops.g.order", "Данные заказа", "Buyurtma ma'lumotlari"); a("pprops.order_info", "Данные заказа", "Buyurtma ma'lumotlari")
a("pprops.ready_date", "Дата готовности", "Tayyor bo'lish sanasi"); a("pprops.phone1", "Телефон 1", "Telefon 1"); a("pprops.phone2", "Телефон 2", "Telefon 2")
a("pprops.g.extra", "Дополнительные параметры", "Qo'shimcha parametrlar"); a("pprops.key", "Параметр", "Parametr"); a("pprops.value", "Значение", "Qiymat")
a("pprops.add_param", "Добавить параметр", "Parametr qo'shish"); a("pprops.description", "Описание", "Tavsif")
a("pprops.messages", "Сообщения", "Xabarlar"); a("pprops.no_messages", "Нет сообщений", "Xabarlar yo'q")

# ── QA tuzatishlari: ro'yxat tanlovi, katalog, postprotsessor nomi ──
a("menu.select_all", "Выделить все", "Hammasini tanlash")
a("projects.delete_many_q", "Удалить выбранные элементы: {{n}}?", "Tanlangan elementlar o'chirilsinmi: {{n}}?")
a("catalog.not_supported", "Этот тип материала пока нельзя добавить как операцию", "Bu turdagi materialni hozircha operatsiya sifatida qo'shib bo'lmaydi")
a("pp_ed.name_required", "Укажите название профиля", "Profil nomini kiriting")

a("cs.params_invalidate_q", "Результат раскроя будет удалён", "Kroy natijasi o'chiriladi")
a("cs.params_invalidate_text", "Изменение этого параметра делает текущий раскрой недействительным. Продолжить? (Ctrl+Z вернёт)",
  "Bu parametr o'zgarsa joriy kroy yaroqsiz bo'ladi. Davom etilsinmi? (Ctrl+Z qaytaradi)")
a("cs.params_invalidate_rem", "Раскрой будет удалён, а записанные на склад остатки — возвращены (списаны со склада). Продолжить? (Ctrl+Z вернёт раскрой)",
  "Kroy o'chiriladi, omborga yozilgan qoldiqlar esa ombordan qaytarib olinadi. Davom etilsinmi? (Ctrl+Z kroyni qaytaradi)")

a("import.skipped", "Пропущено строк: {{n}}", "O'tkazib yuborilgan qatorlar: {{n}}")
a("backup.bad_file","Файл не является резервной копией настроек (JSON)", "Fayl sozlamalar zaxirasi (JSON) emas")
a("mes.test_failed", "Не удалось отправить тестовое событие", "Test hodisasini yuborib bo'lmadi")

# ── Excel import profillari ──
a("import.profile", "Профиль", "Profil"); a("import.profile_none", "— без профиля —", "— profilsiz —")
a("import.profile_new", "Сохранить как новый профиль", "Yangi profil sifatida saqlash"); a("import.profile_save", "Сохранить профиль", "Profilni saqlash")
a("import.profile_name", "Название профиля", "Profil nomi"); a("import.profile_delete_q", "Удалить профиль?", "Profil o'chirilsinmi?")

# ── umumiy «Сортировка» oynasi (ko'p kalitli) ──
a("sort.title", "Сортировка", "Saralash"); a("sort.col.on", "Вкл", "Yoq"); a("sort.col.name", "Наименование", "Nomi"); a("sort.col.desc", "Напр", "Yo'n.")
a("sort.desc_hint", "Напр — по убыванию", "Yo'n. — kamayish tartibida"); a("sort.all", "Включить / выключить все", "Hammasini yoqish / o'chirish")
a("sort.up", "Приоритет выше", "Ustuvorlik yuqori"); a("sort.down", "Приоритет ниже", "Ustuvorlik pastroq")
a("sort.dialog", "Сортировка…", "Saralash…"); a("sort.none", "Выберите хотя бы один столбец", "Kamida bitta ustunni tanlang")
for k, ru, uz in [("type", "Тип", "Tur"), ("code", "Код", "Kod"), ("name", "Наименование", "Nomi"), ("qty", "Количество", "Soni"),
                  ("cost_material", "Стоимость материала", "Material narxi"), ("cost_operation", "Стоимость операции", "Ish narxi"),
                  ("cost", "Стоимость", "Narx"), ("print", "Печатать", "Chop etish"), ("new_page", "Печать с новой страницы", "Yangi sahifadan"),
                  ("uid", "№ (ID)", "№ (ID)"), ("product", "Изделие", "Mahsulot"), ("length", "Длина", "Uzunlik"), ("width", "Ширина", "En"),
                  ("grain", "Текстура", "Tekstura"), ("area", "Площадь", "Maydon"), ("description", "Описание", "Tavsif")]:
    a(f"sortcol.{k}", ru, uz)

# ── qo'shimcha bo'limlar: scripts/i18n_<nom>.py (har biri shu yerdagi `a(kalit, ru, uz)` ni ishlatadi) ──
import glob
for _f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n_*.py"))):
    if os.path.basename(_f) != "i18n_src.py" and not os.path.basename(_f).startswith("i18n_check"):   # i18n_check_uz.py — tekshiruv, manba emas
        exec(compile(open(_f, encoding="utf-8").read(), _f, "exec"), globals())


def nest(flat, idx):
    out = {}
    for k in sorted(flat):
        cur = out
        parts = k.split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
            if not isinstance(cur, dict):
                raise SystemExit(f"kalit to'qnashuvi: {k}")
        cur[parts[-1]] = flat[k][idx]
    return out

here = os.path.dirname(os.path.abspath(__file__))
for idx, lang in ((0, "ru"), (1, "uz")):
    with open(os.path.join(here, "..", "src", "i18n", f"{lang}.json"), "w", encoding="utf-8") as f:
        json.dump(nest(T, idx), f, ensure_ascii=False, indent=1)

# uz-Cyrl — o'zbek kirill: uz (lotin) dan avtomatik (backend/app/uz_translit.py + uz_cyrl_overrides.json; backend ham shuni ishlatadi).
# Istisnolar fayli brauzer transliteratori (src/i18n/translit.ts) uchun src/i18n ga nusxalanadi.
import importlib.util, shutil
_bapp = os.path.join(here, "..", "..", "backend", "app")
_spec = importlib.util.spec_from_file_location("uz_translit", os.path.join(_bapp, "uz_translit.py"))
_tr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tr)
with open(os.path.join(here, "..", "src", "i18n", "uz-Cyrl.json"), "w", encoding="utf-8") as f:
    json.dump(nest({k: (v[0], _tr.to_cyrillic(v[1])) for k, v in T.items()}, 1), f, ensure_ascii=False, indent=1)
shutil.copyfile(os.path.join(_bapp, "uz_cyrl_overrides.json"), os.path.join(here, "..", "src", "i18n", "uz_cyrl_overrides.json"))
print(len(T), "kalit")
