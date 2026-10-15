# -*- coding: utf-8 -*-
"""W4 · LB (Этикетки): parametrlar, shablon muharriri, jonli ko'rish, kroy kartalari miniatyurasi. `a(kalit, ru, uz)` — i18n_src.py yuklaydi."""

a("lb.tab.params", "Параметры", "Parametrlar"); a("lb.tab.template", "Шаблон", "Shablon")
a("lb.tab.maps", "Миниатюры карт (A4)", "Karta miniatyuralari (A4)")
a("lb.all", "Все", "Hammasi")
a("lb.source", "Источник данных", "Ma'lumot manbai")
a("lb.src.parts", "Детали и остатки", "Detallar va qoldiqlar"); a("lb.src.products", "Изделия", "Mahsulotlar")
a("lb.src.user", "Пользовательские данные", "Foydalanuvchi ma'lumotlari")
a("lb.print_mode", "Печатать", "Chop etish")
a("lb.mode.sheet", "На формат A4 (сетка)", "A4 formatga (to'r)"); a("lb.mode.roll", "На принтер этикеток (по одной)", "Etiketka printeriga (bittadan)")
a("lb.width", "Ширина этикетки", "Etiketka eni"); a("lb.height", "Высота этикетки", "Etiketka balandligi")
a("lb.columns", "Столбцы", "Ustunlar"); a("lb.rows", "Строки", "Qatorlar"); a("lb.rows_hint", "0 — по размеру страницы", "0 — sahifaga sig'ganicha")
a("lb.gap", "Промежуток", "Oraliq"); a("lb.margin_on", "Поля страницы", "Sahifa maydonlari")
a("lb.border", "Границы (рамка этикетки)", "Chegaralar (etiketka ramkasi)")
a("lb.rotate", "Повернуть страницу на 90° (альбомная / поворот этикетки)", "Sahifani 90° burish (albom / etiketka burilishi)")
a("lb.parts_h", "Детали", "Detallar"); a("lb.print_parts", "Печатать детали", "Detallarni chop etish")
a("lb.part_each", "Для каждой детали (каждого экземпляра)", "Har bir detal uchun (har nusxaga)")
a("lb.part_nonzero", "Только если количество больше нуля", "Faqat soni noldan katta bo'lsa")
a("lb.label_count", "Этикеток на одну деталь", "Bir detalga etiketkalar soni")
a("lb.cs_op", "Материал (операция CS)", "Material (CS operatsiyasi)")
a("lb.selected", "Выбранные детали (ID через запятую)", "Tanlangan detallar (ID vergul bilan)")
a("lb.selected_hint", "Пусто — все детали", "Bo'sh — hamma detallar")
a("lb.wastes_h", "Остатки", "Qoldiqlar"); a("lb.print_wastes", "Печатать остатки", "Qoldiqlarni chop etish")
a("lb.waste_each", "Для каждого остатка (каждого листа)", "Har bir qoldiq uchun (har listga)")
a("lb.waste_business", "Только деловые остатки", "Faqat deloviy qoldiqlar")
a("lb.products_h", "Изделия", "Mahsulotlar"); a("lb.product_each", "Для каждого изделия (каждого экземпляра)", "Har bir mahsulot uchun (har nusxaga)")
a("lb.product_nonzero", "Только если количество больше нуля", "Faqat soni noldan katta bo'lsa")
a("lb.count", "Количество этикеток", "Etiketkalar soni")
a("lb.count_val", "{{n}} шт · страниц: {{p}}", "{{n}} ta · sahifalar: {{p}}")
a("lb.count_detail", "детали {{parts}}, остатки {{wastes}}, изделия {{products}}", "detallar {{parts}}, qoldiqlar {{wastes}}, mahsulotlar {{products}}")
a("lb.too_many", "Слишком много этикеток: {{n}} (максимум {{max}} за одну печать) — отфильтруйте детали (выбранные детали, материал).",
  "Etiketkalar juda ko'p: {{n}} (bir chopda ko'pi bilan {{max}}) — detallarni filtrlang (tanlangan detallar, material).")
a("lb.shown","показано {{n}} из {{t}}", "ko'rsatilgan {{n}} / {{t}}")
a("lb.legacy_note", "Из файла проекта сохранён старый шаблон; он не читается и не печатается — используется выбранный здесь шаблон.",
  "Loyiha faylidan eski shablon saqlangan; u o'qilmaydi va chop etilmaydi — bu yerda tanlangan shablon ishlatiladi.")
a("lb.save_defaults", "Сохранить параметры по умолчанию", "Parametrlarni standart qilib saqlash")
a("lb.tpl_save", "Сохранить в библиотеку", "Kutubxonaga saqlash"); a("lb.tpl_name", "Название шаблона", "Shablon nomi")
a("lb.tpl_delete", "Удалить из библиотеки", "Kutubxonadan o'chirish"); a("lb.tpl_delete_q", "Удалить шаблон «{{name}}» из библиотеки?", "«{{name}}» shablonini kutubxonadan o'chirilsinmi?")
a("lb.tpl_export", "Экспорт (JSON)", "Eksport (JSON)"); a("lb.tpl_import", "Импорт (JSON)", "Import (JSON)")
a("lb.tpl_copy", "Шаблон изменён: копия хранится в проекте", "Shablon o'zgartirilgan: nusxa loyihada saqlanadi")
a("lb.tpl_reset", "Вернуть шаблон из библиотеки", "Kutubxonadagi shablonni qaytarish")
a("lb.tpl_params", "Параметры шаблона", "Shablon parametrlari"); a("lb.tpl_vars", "Переменные шаблона", "Shablon o'zgaruvchilari")
a("lb.tpl_elements", "Элементы", "Elementlar"); a("lb.add", "Добавить элемент", "Element qo'shish")
a("lb.json_bad", "Неверный JSON", "JSON noto'g'ri")
a("lb.col.type", "Тип", "Turi"); a("lb.col.size", "Размер", "O'lcham"); a("lb.col.expr", "Выражение", "Ifoda")
for _k, _ru, _uz in [("text", "Текст", "Matn"), ("rect", "Прямоугольник", "To'g'ri to'rtburchak"), ("line", "Линия", "Chiziq"),
                     ("qr", "QR-код", "QR kod"), ("code128", "Штрихкод Code128", "Code128 shtrixkod"),
                     ("part", "Чертёж детали", "Detal chizmasi"), ("edges", "Схема кромок", "Kromka sxemasi"),
                     ("if", "Условие (If)", "Shart (If)"), ("group", "Группа (сдвиг, поворот)", "Guruh (siljish, burish)"),
                     ("var", "Переменная", "O'zgaruvchi"), ("image", "Изображение", "Rasm"), ("barcode", "Штрихкод", "Shtrixkod")]:
    a(f"lb.el.{_k}", _ru, _uz)
a("lb.vars_h", "Переменные и функции (клик — копировать)", "O'zgaruvchilar va funksiyalar (bosing — nusxa)")
a("lb.copied", "Скопировано: {{s}}", "Nusxa olindi: {{s}}")
a("lb.print", "Печать", "Chop etish"); a("lb.open", "Открыть в окне", "Oynada ochish")
a("lb.errors", "Ошибки в выражениях", "Ifodalardagi xatolar")
a("lb.errors_hint", "Исправьте до печати: такие элементы отмечены на этикетке красным «#ERR».", "Chopdan oldin tuzating: bunday elementlar etiketkada qizil «#ERR» bilan belgilanadi.")
a("lb.print_with_errors", "В шаблоне есть ошибки — всё равно печатать?", "Shablonda xatolar bor — baribir chop etilsinmi?")
a("lb.print_with_errors_text", "Элементы с ошибками будут отмечены красным «#ERR».", "Xatoli elementlar qizil «#ERR» bilan belgilanadi.")
a("lb.maps_hint", "Миниатюры карт кроя: 2 колонки на странице A4; рисунок и заголовок — как в отчёте (кромки, QR — по профилю печати).",
  "Kroy kartalari miniatyurasi: A4 sahifada 2 ustun; chizma va sarlavha — hisobotdagidek (kromka, QR — chop profiliga ko'ra).")
a("lb.maps_per", "Карт на листе A4", "A4 varaqda kartalar"); a("lb.maps_op", "Операция CS", "CS operatsiyasi")
a("lb.use_op", "Параметры:", "Parametrlar:"); a("lb.new_params", "Новые (не сохранены в проекте)", "Yangi (loyihada saqlanmagan)")
a("lb.to_op", "Создать операцию LB", "LB operatsiyasini yaratish")
a("lb.to_op_hint", "Сохранить эти параметры и шаблон в проекте как операцию LB", "Bu parametr va shablonni loyihada LB operatsiyasi sifatida saqlash")


# «Печать отчета» bo'limi nomi: endi detal QR etiketkasi emas, LB tizimi (shablon, qoldiq, mahsulot, A4 da kartalar)
a("print.sec.labels", "Этикетки", "Etiketkalar")
