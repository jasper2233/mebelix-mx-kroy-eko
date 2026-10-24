# Yozuvlarni xodimlar o'rgangan onlayn tizimdagi so'zlar bilan bir xil qilish (2026-10-04, ekranma-ekran tekshiruvdan keyin).
# Faqat ruscha matn almashtiriladi (o'zbekchasi o'zgarmaydi); yangi kalitlar — `a(...)`. Fayl nomi `zz` — eng oxirida yuklanadi.
def ru(key, text):
    T[key] = (text, T[key][1] if key in T else text)

a("app.move_up", "Переместить вверх [CTRL]+[UP]", "Yuqoriga ko'chirish [CTRL]+[UP]")
a("app.move_down", "Переместить вниз [CTRL]+[DOWN]", "Pastga ko'chirish [CTRL]+[DOWN]")
a("ops.col.print_hint", "Печатать. Выводить на печать содержимое данной операции.", "Chop etish. Shu operatsiya mazmunini chop etishga chiqarish.")
a("ops.col.new_page_hint", "Печатать с новой страницы.", "Yangi sahifadan chop etish.")
a("ops.col.cost_mat_hint", "Стоимость материала", "Material narxi")
a("ops.col.cost_op_hint", "Стоимость операции", "Operatsiya narxi")
a("ops.col.cost_hint", "Стоимость = стоимость материала + стоимость операций", "Narx = material narxi + operatsiyalar narxi")
a("xnc.mirror_h", "Горизонтальное отзеркаливание", "Gorizontal ko'zgu")
a("xnc.mirror_v", "Вертикальное отзеркаливание", "Vertikal ko'zgu")
a("el.pick_color", "Выбор цвета", "Rang tanlash")
ru("cut.pp", "Постпроцессор (Конвертация в формат пильной станции)")
ru("xnc.pp.title", "Постпроцессор (Конвертация в формат обрабатывающего центра)")
ru("cut.ind.C", "Количество листов в карте раскроя / Общее количество листов в раскрое")
ru("cut.ind.Cp", "Количество деталей на карте раскроя / Общее количество деталей в раскрое")
ru("cut.ind.LT", "Длина реза на карте кроя / Общая длина реза в раскрое")
ru("cut.ind.F", "Процент заполнения на карте кроя / Процент заполнения раскроя")
ru("cs.p.max_types", "Максимальное количество разновидностей деталей на карте кроя")
ru("pcd.total", "Общее количество. (Количество деталей) * (Количество изделий)")
ru("xnc.svc", "Панель со служебными командами (F4)")
# XNC buyruqlari nomlari
for _k, _v in (("MillStart", "Точка входа для фрезы"), ("MillLine", "Фрезерование по прямой"), ("MillArc", "Фрезерование по дуге"),
               ("MillArcCenter", "Фрезерование по дуге c центром"), ("MillArc3P", "Фрезерование дуги по 3 точкам"),
               ("MillFillet", "Фрезерование сопряжение/скругление"), ("MillRect", "Фрезерование прямоугольника"),
               ("MillEllipse", "Фрезерование эллипса"), ("While", "Цикл WHILE"), ("DoWhile", "Цикл DO WHILE"),
               ("Break", "Прервать цикл"), ("Call", "Вызвать подпрограмму"), ("Ret", "Выход из подпрограммы или программы"),
               ("Msg", "Вывод сообщения"), ("Err", "Вывод ошибки")):
    ru("xnc.cmd." + _k, _v)
ru("xnc.outdent", "Переместить на уровень выше [CTRL]+[LEFT]")
ru("xnc.indent", "Переместить на уровень ниже [CTRL]+[RIGHT]")
ru("ops.merge", "Объединить")
# 2-bosqich (loyihalar ro'yxati, mahsulotlar, CL / SP / GR / O / LB)
ru("projects.up", "Перейти в верхнюю папку")
ru("projects.home", "Домой")
ru("projects.open_hint", "Для открытия проекта - двойной клик по соответствующей строке или нажмите [CTRL]+[Пробел]")
ru("products.zero_all", "Установить для всех количество в ноль")
ru("cl.p.rounding", "Округление Полосы")
ru("cs.p.rounding", "Округление Листы")
ru("lb.src.user", "Пользов-кие данные")
a("optype.tip.CS", "(CS) Листовой раскрой", "(CS) Listli kroy")
a("optype.tip.CL", "(CL) Погонажный раскрой", "(CL) Pogonaj kroy")
a("optype.tip.CN", "(CN) Нестинговый раскрой", "(CN) Nesting kroy")
a("optype.tip.EL", "(EL) Кромка", "(EL) Kromka")
a("optype.tip.SP", "(SP) Обработка поверхности", "(SP) Yuza ishlovi")
a("optype.tip.GR", "(GR) Пазование", "(GR) Paz ochish")
a("optype.tip.XNC", "(XNC) Обработка", "(XNC) Ishlov")
a("optype.tip.O", "(O) Комплектация и другие действия", "(O) Komplektatsiya va boshqa amallar")
a("optype.tip.LB", "(LB) Этикетки", "(LB) Etiketkalar")

# «Настройки» menyusi (tartib — o'rganilgan menyu bo'yicha); MES serveri bajaradigan bandlar
a("settings.m.password", "Сменить пароль", "Parolni almashtirish")
a("settings.m.email", "Сменить email", "Emailni almashtirish")
a("settings.m.save_local", "Сохранить данные на локальный диск", "Ma'lumotlarni mahalliy diskka saqlash")
a("settings.m.import3d", "Импорт из 3D-Constructor", "3D-Constructor dan import")
a("settings.m.import3d_hint", "Импорт проектов: «Проекты → Импортировать» или «Проект → Импорт из других программ»",
  "Loyihalar importi: «Loyihalar → Import» yoki «Loyiha → Boshqa dasturlardan import»")
a("settings.m.dropbox", "Dropbox", "Dropbox")
a("settings.m.dir_projects", "Папка проектов", "Loyihalar papkasi")
a("settings.m.dir_xnc", "Папка XNC шаблонов", "XNC shablonlari papkasi")
a("settings.m.dir_labels", "Папка этикеток", "Etiketkalar papkasi")
a("settings.m.orders", "Модуль заказов", "Buyurtmalar moduli")
a("settings.m.logout", "Выйти", "Chiqish")
a("settings.mes_later", "Этот раздел выполняет MES-сервер — будет подключён позже", "Bu bo'limni MES serveri bajaradi — keyin ulanadi")
ru("settings.page.xnc", "XNC Редактор")

# Bir nechta loyiha faylini import (2026-10-18)
a("projects.imported_n", "Импортировано проектов: {{n}} из {{total}}", "Import qilingan loyihalar: {{n}} / {{total}}")
a("import.merged", "Добавлено в проект файлов: {{n}} из {{total}}", "Loyihaga qo'shilgan fayllar: {{n}} / {{total}}")
a("import.merge_line", "{{file}}: операций {{ops}}, деталей {{parts}}", "{{file}}: operatsiyalar {{ops}}, detallar {{parts}}")

# Hisobot ko'rinishi: A4 sahifali PDF (standart) / ekran HTML
a("print.view_a4", "Формат A4", "A4 format")
a("print.view_html", "Экранный вид", "Ekran ko'rinishi")
