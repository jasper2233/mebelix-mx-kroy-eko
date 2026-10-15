# -*- coding: utf-8 -*-
"""W15 · LB-C/LB-D: etiketka vizual redaktori (lbd.*), ZPL chiqarish (lbz.*), foydalanuvchi ma'lumotlari (lbu.*). `a(kalit, ru, uz)` — i18n_src.py yuklaydi."""

# ── yorliqlar va yangi elementlar ──
a("lb.tab.designer", "Визуальный редактор", "Vizual redaktor")
a("lb.tab.data", "Данные", "Ma'lumotlar")
a("lb.open_designer", "Открыть в визуальном редакторе", "Vizual redaktorda ochish")
a("lb.el.polyline", "Полилиния", "Poliliniya")
a("lb.el.arc", "Дуга", "Yoy")
a("lb.el.ellipse", "Эллипс", "Ellips")

# ── визуальный редактор ──
a("lbd.page", "Этикетка (страница)", "Etiketka (sahifa)")
a("lbd.tpl_name", "Название шаблона", "Shablon nomi")
a("lbd.default", "по умолчанию", "standart")
a("lbd.param_value", "Значение параметра в этом проекте", "Parametrning shu loyihadagi qiymati")
a("lbd.limit", "Предел шаблона: не более {{n}} элементов и {{d}} уровней вложенности", "Shablon chegarasi: ko'pi bilan {{n}} element va {{d}} ichma-ich daraja")
a("lbd.copied", "Скопировано элементов: {{n}}", "Nusxa olingan elementlar: {{n}}")
a("lbd.group_siblings", "Группировать можно только элементы одного списка (одного уровня)", "Faqat bitta ro'yxatdagi (bir daraja) elementlarni guruhlash mumkin")
a("lbd.unwrap_fail", "Разгруппировать можно группу без поворота с числовым сдвигом или блок If", "Burilishsiz, sonli siljishli guruhni yoki If blokini yoyish mumkin")
a("lbd.replace_q", "Заменить шаблон проекта?", "Loyiha shabloni almashtirilsinmi?")
a("lbd.replace_text", "В проекте хранится изменённая копия шаблона — она будет потеряна. Чтобы сохранить правки, сначала нажмите «Сохранить в библиотеку».",
  "Loyihada shablonning o'zgartirilgan nusxasi bor — u yo'qoladi. O'zgarishlarni saqlash uchun avval «Kutubxonaga saqlash» ni bosing.")
a("lbd.replace_ok", "Заменить", "Almashtirish")
a("lbd.maximize", "На весь экран", "To'liq ekran")
a("lbd.restore", "Свернуть", "Kichraytirish")
a("lbd.dup", "Дублировать", "Nusxa qo'shish")
a("lbd.group", "Сгруппировать", "Guruhlash")
a("lbd.wrap_if", "Обернуть в условие (If)", "Shart (If) ichiga o'rash")
a("lbd.unwrap", "Разгруппировать / убрать условие", "Guruhni yoyish / shartni olib tashlash")
a("lbd.front", "На передний план", "Eng oldinga")
a("lbd.forward", "Вперёд", "Oldinga")
a("lbd.backward", "Назад", "Orqaga")
a("lbd.back", "На задний план", "Eng orqaga")
a("lbd.align_all", "Выровнять", "Tekislash")
for _k, _ru, _uz in [("left", "По левому краю", "Chap chet bo'yicha"), ("centerH", "По центру (гориз.)", "Markaz bo'yicha (gor.)"), ("right", "По правому краю", "O'ng chet bo'yicha"),
                     ("top", "По верхнему краю", "Yuqori chet bo'yicha"), ("centerV", "По центру (верт.)", "Markaz bo'yicha (vert.)"), ("bottom", "По нижнему краю", "Pastki chet bo'yicha")]:
    a(f"lbd.align.{_k}", _ru, _uz)
a("lbd.zoom_out", "Уменьшить", "Kichraytirish")
a("lbd.zoom_in", "Увеличить", "Kattalashtirish")
a("lbd.fit", "Вписать в окно", "Oynaga sig'dirish")
a("lbd.grid", "Показать сетку", "To'rni ko'rsatish")
a("lbd.snap", "Привязка к сетке и направляющим", "To'r va yo'naltiruvchilarga yopishish")
a("lbd.snap_off", "отключить на время", "vaqtincha o'chirish")
a("lbd.guides", "Направляющие линии", "Yo'naltiruvchi chiziqlar")
a("lbd.kind.part", "Образец: деталь", "Namuna: detal")
a("lbd.kind.waste", "Образец: остаток", "Namuna: qoldiq")
a("lbd.kind.product", "Образец: изделие", "Namuna: mahsulot")
a("lbd.kind.user", "Образец: свои данные", "Namuna: o'z ma'lumotim")
a("lbd.src_sample", "Данные: образец", "Ma'lumot: namuna")
a("lbd.src_project", "Данные: строки проекта", "Ma'lumot: loyiha qatorlari")
a("lbd.tab.props", "Свойства", "Xossalar")
a("lbd.tab.layers", "Слои", "Qatlamlar")
a("lbd.tab.vars", "Переменные и функции", "O'zgaruvchilar va funksiyalar")
a("lbd.vars_short", "значения на образце", "namunadagi qiymatlar")
a("lbd.multi", "Выбрано элементов: {{n}}", "Tanlangan elementlar: {{n}}")
a("lbd.multi_hint", "Перетаскивайте вместе, стрелки — сдвиг, «Выровнять» — по краям/центру; свойства — у одного элемента.", "Birga siljiting, strelkalar — siljitish, «Tekislash» — chet/markaz bo'yicha; xossalar — bitta element uchun.")
a("lbd.sel", "выбрано", "tanlangan")
a("lbd.elements", "Элементов", "Elementlar")
a("lbd.keys_hint", "Del — удалить · Ctrl+D — дубль · Ctrl+Z/Y — отмена/возврат · стрелки — сдвиг (Shift ×10, Alt 0.1) · Alt — без привязки · Ctrl+колесо — масштаб",
  "Del — o'chirish · Ctrl+D — nusxa · Ctrl+Z/Y — bekor/qaytarish · strelkalar — siljitish (Shift ×10, Alt 0.1) · Alt — yopishishsiz · Ctrl+g'ildirak — masshtab")
a("lbd.no_elements", "В шаблоне нет элементов. Добавьте элемент кнопкой «Добавить элемент».", "Shablonda element yo'q. «Element qo'shish» tugmasi bilan qo'shing.")
a("lbd.img_type", "Допустимы только изображения PNG или JPEG", "Faqat PNG yoki JPEG rasm mumkin")
a("lbd.img_size", "Изображение больше 200 КБ", "Rasm 200 KB dan katta")
a("lbd.img_pick", "Выбрать…", "Tanlash…")
a("lbd.no_image", "нет изображения", "rasm yo'q")
a("lbd.clear", "Очистить", "Tozalash")
a("lbd.pt_add", "Точка", "Nuqta")
a("lbd.branch", "Ветка для новых элементов", "Yangi elementlar uchun shox")
a("lbd.flag_expr", "Задать выражением", "Ifoda bilan berish")
a("lbd.flag_lit", "Вернуть флажок", "Belgini qaytarish")
a("lbd.vars_hint", "Нажмите переменную — она вставится в активное поле выражения (или скопируется). Справа — значение на образце.", "O'zgaruvchini bosing — faol ifoda maydoniga qo'yiladi (yoki nusxa olinadi). O'ngda — namunadagi qiymat.")
a("lbd.vars_tpl", "Параметры и переменные шаблона", "Shablon parametr va o'zgaruvchilari")
a("lbd.fx_title", "Выражение — проверка и функции", "Ifoda — tekshirish va funksiyalar")
a("lbd.fx_apply", "Применить", "Qo'llash")
for _k, _ru, _uz in [
    ("text", "Текст (выражение)", "Matn (ifoda)"), ("x", "X, мм", "X, mm"), ("y", "Y, мм", "Y, mm"), ("w", "Ширина", "Eni"), ("h", "Высота", "Balandligi"),
    ("size", "Размер", "O'lcham"), ("maxw", "Макс. ширина", "Maks. eni"), ("align", "Выравнивание", "Tekislash"), ("rotate", "Поворот °", "Burish °"),
    ("font", "Шрифт", "Shrift"), ("bold", "Жирный", "Qalin"), ("italic", "Курсив", "Kursiv"), ("wrap", "Перенос", "Qatorlarga bo'lish"),
    ("lines", "Строк", "Qatorlar"), ("line_h", "Межстрочный", "Qator oralig'i"), ("color", "Цвет", "Rang"), ("stroke", "Линия", "Chiziq"),
    ("fill", "Заливка", "To'ldirish"), ("radius", "Скругление", "Yumaloqlash"), ("x1", "X1", "X1"), ("y1", "Y1", "Y1"), ("x2", "X2", "X2"), ("y2", "Y2", "Y2"),
    ("src", "Изображение", "Rasm"), ("kind", "Вид", "Turi"), ("data", "Данные (выражение)", "Ma'lumot (ifoda)"), ("quiet", "Тихая зона", "Bo'sh zona"),
    ("ec", "Коррекция ошибок", "Xato tuzatish"), ("caption", "Текст под кодом", "Kod ostidagi matn"), ("origin.0", "Сдвиг X", "Siljish X"), ("origin.1", "Сдвиг Y", "Siljish Y"),
    ("cond", "Условие (выражение)", "Shart (ifoda)"), ("name", "Имя", "Nomi"), ("expr", "Выражение", "Ifoda"), ("points", "Точки (X, Y)", "Nuqtalar (X, Y)"),
    ("closed", "Замкнуть", "Yopiq"), ("cx", "Центр X", "Markaz X"), ("cy", "Центр Y", "Markaz Y"), ("r", "Радиус", "Radius"), ("a1", "Угол начала °", "Boshlanish burchagi °"),
    ("a2", "Угол конца °", "Tugash burchagi °"), ("rx", "Радиус X", "Radius X"), ("ry", "Радиус Y", "Radius Y"), ("comment", "Комментарий", "Izoh")]:
    a(f"lbd.f.{_k}", _ru, _uz)

# ── ZPL ──
a("lbz.btn", "Скачать ZPL", "ZPL yuklab olish")
a("lbz.btn_hint", "Шаблон в формате ZPL II (Zebra) — файл .zpl", "Shablon ZPL II (Zebra) formatida — .zpl fayl")
a("lbz.title", "Скачать ZPL (Zebra)", "ZPL yuklab olish (Zebra)")
a("lbz.download", "Скачать ZPL", "ZPL yuklab olish")
a("lbz.save_default", "Сохранить как стандарт", "Standart sifatida saqlash")
a("lbz.hint", "Этикетки превращаются в команды ZPL II (^XA … ^XZ) и сохраняются в файл .zpl. Прямой отправки на принтер нет: файл копируют на принтер (Zebra Setup Utilities, `copy /b файл.zpl \\\\ПК\\принтер` и т.п.). Позиции и шрифт приблизительные — проверьте на первой этикетке.",
  "Etiketkalar ZPL II (^XA … ^XZ) buyruqlariga o'giriladi va .zpl faylga saqlanadi. Printerga to'g'ridan yuborish yo'q: fayl printerga ko'chiriladi (Zebra Setup Utilities, `copy /b fayl.zpl \\\\PC\\printer` va h.k.). Joylashuv va shrift taxminiy — birinchi etiketkada tekshiring.")
a("lbz.dpi", "Разрешение принтера", "Printer zichligi")
a("lbz.font", "Шрифт ^A", "^A shrifti")
a("lbz.font_hint", "0 — встроенный масштабируемый шрифт; для кириллицы — файл шрифта в памяти принтера, например E:ARIAL.TTF", "0 — o'rnatilgan masshtablanadigan shrift; kirill uchun — printer xotirasidagi shrift fayli, masalan E:ARIAL.TTF")
a("lbz.utf8", "Кодировка UTF-8 (^CI28)", "UTF-8 kodlash (^CI28)")
a("lbz.emit_size", "Писать размер (^PW, ^LL)", "O'lchamni yozish (^PW, ^LL)")
a("lbz.header", "ZPL Header (в начало каждой этикетки)", "ZPL Header (har etiketka boshiga)")
a("lbz.header_hint", "Команды ~ (например ~SD — тёмность) пишутся перед ^XA, остальные (^PR, ^MD, ^CW …) — после размера. ^XA и ^XZ удаляются.",
  "~ buyruqlari (masalan ~SD — qoralik) ^XA dan oldin, qolganlari (^PR, ^MD, ^CW …) o'lchamdan keyin yoziladi. ^XA va ^XZ olib tashlanadi.")
a("lbz.count", "Этикеток: {{n}} (в просмотре: {{shown}})", "Etiketkalar: {{n}} (ko'rinishda: {{shown}})")
a("lbz.preview", "Просмотр ZPL (первые этикетки)", "ZPL ko'rinishi (birinchi etiketkalar)")

# ── пользовательские данные ──
a("lbu.hint", "Свои строки для этикеток: задайте поля (имя → переменная user.<имя>), затем заполните таблицу или вставьте из Excel (Ctrl+V). Колонка «Кол-во» — число копий этикетки строки.",
  "Etiketkalar uchun o'z qatorlaringiz: maydonlarni belgilang (nom → user.<nom> o'zgaruvchisi), so'ng jadvalni to'ldiring yoki Excel dan qo'ying (Ctrl+V). «Soni» ustuni — qator etiketkasi nusxalari soni.")
a("lbu.field", "Поле", "Maydon")
a("lbu.fields", "Поля (схема данных)", "Maydonlar (ma'lumot sxemasi)")
a("lbu.add_field", "Добавить поле", "Maydon qo'shish")
a("lbu.f_name", "Имя (user.…)", "Nomi (user.…)")
a("lbu.f_title", "Заголовок", "Sarlavha")
a("lbu.f_type", "Тип", "Turi")
a("lbu.f_default", "По умолчанию", "Standart")
a("lbu.name_bad", "Латиница, цифры, «_»; не с цифры; без повторов", "Lotin harf, raqam, «_»; raqamdan boshlanmasin; takrorsiz")
a("lbu.rows", "Данные (строки этикеток)", "Ma'lumotlar (etiketka qatorlari)")
a("lbu.header_row", "Первая строка при вставке — заголовки", "Qo'yishda birinchi qator — sarlavhalar")
a("lbu.paste", "Вставить из буфера", "Buferdan qo'yish")
a("lbu.paste_hint", "Строки из буфера (Excel) добавляются в конец; в ячейке Ctrl+V вставляет с этого места", "Bufer (Excel) qatorlari oxiriga qo'shiladi; katakda Ctrl+V shu joydan qo'yadi")
a("lbu.paste_denied", "Нет доступа к буферу обмена: щёлкните ячейку и нажмите Ctrl+V", "Buferga ruxsat yo'q: katakni bosib Ctrl+V bosing")
a("lbu.pasted", "Вставлено строк: {{n}}", "Qo'yilgan qatorlar: {{n}}")
a("lbu.add_row", "Строка", "Qator")
a("lbu.clear", "Очистить", "Tozalash")
a("lbu.count", "Строк: {{rows}} · этикеток к печати: {{labels}}", "Qatorlar: {{rows}} · chop etiladigan etiketkalar: {{labels}}")
a("lbu.no_fields", "Нет полей: добавьте поле или вставьте таблицу из Excel — поля создадутся сами.", "Maydon yo'q: maydon qo'shing yoki Excel jadvalini qo'ying — maydonlar o'zi yaratiladi.")
a("lbu.qty", "Кол-во", "Soni")
a("lbu.no_template", "Шаблон не использует поля данных (user.…).", "Shablon ma'lumot maydonlaridan (user.…) foydalanmaydi.")
a("lbu.make_template", "Создать шаблон по полям", "Maydonlar bo'yicha shablon yaratish")
a("lbu.open_designer", "Открыть редактор", "Redaktorni ochish")
