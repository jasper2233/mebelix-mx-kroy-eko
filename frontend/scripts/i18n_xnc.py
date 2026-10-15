# -*- coding: utf-8 -*-
"""W1 · XNC muharriri: daraxt, Par kiritish, shablonlar kutubxonasi, ishlov markazi postprotsessori (i18n_src.py yuklaydi)."""

# ── daraxt muharriri ──
a("xnc.templates", "Шаблоны", "Shablonlar")
a("xnc.indent", "Внутрь блока (Ctrl+→)", "Blok ichiga (Ctrl+→)")
a("xnc.outdent", "Из блока наружу (Ctrl+←)", "Blokdan tashqariga (Ctrl+←)")
a("xnc.inside", "Добавлять внутрь выбранного блока (If, Else, While, DoWhile, Sub)",
  "Tanlangan blok (If, Else, While, DoWhile, Sub) ichiga qo'shish")
a("xnc.collapse", "Свернуть", "Yig'ish"); a("xnc.expand", "Развернуть", "Ochish")
a("xnc.svc", "Служебные команды (F4)", "Xizmat buyruqlari (F4)")
a("xnc.state", "Состояние (F9)", "Holat (F9)")
a("xnc.state_ok", "Ошибок и предупреждений нет", "Xato va ogohlantirishlar yo'q")
a("xnc.state_n", "Предупреждений: {{n}}", "Ogohlantirishlar: {{n}}")
a("xnc.stats_line", "Отверстий: {{d}} · фрезеровка: {{m}} м · пиление: {{s}} м",
  "Teshiklar: {{d}} · frezalash: {{m}} m · arralash: {{s}} m")
a("xnc.add_known", "Добавить параметр…", "Parametr qo'shish…"); a("xnc.param_custom", "Другой…", "Boshqa…")
a("xnc.block_empty", "пусто", "bo'sh")
a("xnc.type.double", "Число", "Son"); a("xnc.type.integer", "Целое", "Butun"); a("xnc.type.boolean", "Да / Нет", "Ha / Yo'q")
a("xnc.bool.true", "да", "ha"); a("xnc.bool.false", "нет", "yo'q")
a("xnc.opt.corr0", "0 — по центру", "0 — markazda"); a("xnc.opt.corr1", "1 — справа", "1 — o'ngda")
a("xnc.opt.corr2", "2 — слева", "2 — chapda"); a("xnc.opt.corr3", "3 — карман", "3 — cho'ntak")
a("xnc.opt.in0", "0 — автоматически", "0 — avtomatik"); a("xnc.opt.in1", "1 — простое опускание", "1 — oddiy tushish")
a("xnc.opt.out0", "0 — автоматически", "0 — avtomatik"); a("xnc.opt.out1", "1 — простое поднятие", "1 — oddiy ko'tarilish")

# parametr izohlari (tooltip)
for k, ru, uz in [
    ("X", "Координата X (по длине)", "X koordinata (uzunlik bo'yicha)"), ("Y", "Координата Y (по ширине)", "Y koordinata (en bo'yicha)"),
    ("Z", "Положение по толщине (Z)", "Qalinlik bo'yicha o'rni (Z)"), ("DP", "Глубина", "Chuqurlik"),
    ("T", "Имя инструмента (команда Tool)", "Asbob nomi (Tool buyrug'i)"), ("D", "Диаметр", "Diametr"),
    ("N", "Имя инструмента", "Asbob nomi"), ("AC", "Массив отверстий: количество", "Teshiklar massivi: soni"),
    ("AS", "Массив отверстий: шаг", "Teshiklar massivi: qadam"), ("AV", "Массив: по вертикали (true) или по горизонтали (false)",
                                                              "Massiv: vertikal (true) yoki gorizontal (false)"),
    ("M", "Середина по Z: true — по центру толщины, false — по Z", "Z bo'yicha o'rtada: true — qalinlik o'rtasi, false — Z qiymati"),
    ("C", "Коррекция на радиус фрезы", "Freza radiusi bo'yicha korreksiya"),
    ("SDP", "Шаг в глубину", "Chuqurlikka qadam"), ("SXY", "Шаг по плоскости (по умолчанию D/2)", "Tekislikdagi qadam (standart D/2)"),
    ("IN", "Тип входа фрезы", "Freza kirish turi"), ("OUT", "Тип выхода фрезы", "Freza chiqish turi"),
    ("R", "Радиус", "Radius"), ("DIR", "Направление дуги", "Yoy yo'nalishi"),
    ("CX", "Центр дуги X", "Yoy markazi X"), ("CY", "Центр дуги Y", "Yoy markazi Y"),
    ("X2", "Промежуточная точка X", "Oraliq nuqta X"), ("Y2", "Промежуточная точка Y", "Oraliq nuqta Y"),
    ("L", "Длина (по X до поворота)", "Uzunlik (burilishgacha X bo'yicha)"), ("W", "Ширина", "Eni"),
    ("A", "Угол поворота, градусы", "Burilish burchagi, gradus"), ("RL", "Полуось по длине", "Uzunlik bo'yicha yarim o'q"),
    ("RW", "Полуось по ширине", "En bo'yicha yarim o'q"), ("X1", "Начало паза X", "Paz boshi X"), ("Y1", "Начало паза Y", "Paz boshi Y"),
    ("P", "Параметр из файла (не используется)", "Fayldagi parametr (ishlatilmaydi)"),
    ("VER", "Версия записи из файла (не используется)", "Fayldagi yozuv versiyasi (ishlatilmaydi)"),
    ("name", "Имя", "Nomi"), ("value", "Значение / выражение", "Qiymat / ifoda"), ("type", "Тип", "Turi"),
    ("label", "Подпись в окне параметров", "Parametrlar oynasidagi yorliq"), ("visible", "Условие показа (выражение)", "Ko'rsatish sharti (ifoda)"),
    ("suffix", "Суффикс (например, мм)", "Qo'shimcha (masalan, mm)"), ("readonly", "Только чтение (выражение)", "Faqat o'qish (ifoda)"),
    ("cond", "Условие (выражение)", "Shart (ifoda)"), ("text", "Текст", "Matn"),
]:
    a(f"xnc.p.{k}", ru, uz)

# ── Par kiritish ──
a("xnc.par.title", "Параметры шаблона", "Shablon parametrlari")
a("xnc.par.default", "по умолчанию: {{v}}", "standart: {{v}}")
a("xnc.par.reset", "Вернуть значение по умолчанию", "Standart qiymatga qaytarish")
a("xnc.par.none", "В программе нет параметров (команда Par) — добавьте их на вкладке «Шаблон» или загрузите шаблон из библиотеки",
  "Dasturda parametr yo'q (Par buyrug'i) — «Dastur» yorlig'ida qo'shing yoki kutubxonadan shablon oling")
a("xnc.par.edit_hint", "Значения хранятся в операции; шаблон не меняется", "Qiymatlar operatsiyada saqlanadi; shablon o'zgarmaydi")

# ── shablonlar kutubxonasi ──
a("xnc.tpl.title", "Шаблоны XNC", "XNC shablonlari")
a("xnc.tpl.builtin", "Готовые образцы", "Tayyor namunalar"); a("xnc.tpl.mine", "Мои шаблоны", "Mening shablonlarim")
a("xnc.tpl.empty", "Своих шаблонов пока нет", "Hozircha o'z shablonlaringiz yo'q")
a("xnc.tpl.pick", "Выберите шаблон слева", "Chapdan shablonni tanlang")
a("xnc.tpl.save_current", "Сохранить программу как шаблон…", "Dasturni shablon sifatida saqlash…")
a("xnc.tpl.name_q", "Название шаблона", "Shablon nomi")
a("xnc.tpl.saved", "Шаблон сохранён", "Shablon saqlandi")
a("xnc.tpl.exists_q", "Шаблон «{{n}}» уже есть. Заменить?", "«{{n}}» shabloni mavjud. Almashtirilsinmi?")
a("xnc.tpl.apply_replace", "Заменить программу", "Dasturni almashtirish")
a("xnc.tpl.apply_append", "Добавить в конец", "Oxiriga qo'shish")
a("xnc.tpl.replace_q", "Заменить текущую программу шаблоном «{{n}}»?", "Joriy dastur «{{n}}» shabloni bilan almashtirilsinmi?")
a("xnc.tpl.applied", "Шаблон применён", "Shablon qo'llandi")
a("xnc.tpl.delete_q", "Удалить шаблон «{{n}}»?", "«{{n}}» shabloni o'chirilsinmi?")
a("xnc.tpl.export", "Экспорт (JSON)", "Eksport (JSON)"); a("xnc.tpl.import", "Импорт из файла…", "Fayldan import…")
a("xnc.tpl.imported", "Шаблон «{{n}}» импортирован", "«{{n}}» shabloni import qilindi")
a("xnc.tpl.bad_file", "Не удалось прочитать файл шаблона", "Shablon faylini o'qib bo'lmadi")
a("xnc.tpl.params", "Параметров: {{n}}", "Parametrlar: {{n}}"); a("xnc.tpl.commands", "Команд: {{n}}", "Buyruqlar: {{n}}")
a("xnc.tpl.cat.mill", "Фрезеровка", "Frezalash"); a("xnc.tpl.cat.drill", "Сверление", "Teshiklar")
a("xnc.tpl.cat.facade", "Фасады, накладки", "Fasad, nakladkalar"); a("xnc.tpl.cat.groove", "Пазы", "Pazlar")
a("xnc.tpl.cat.other", "Прочее", "Boshqa")
a("xnc.tpl.builtin_note", "Готовые образцы не изменяются — применяйте и правьте программу в операции или сохраните копию",
  "Tayyor namunalar o'zgarmaydi — operatsiyada qo'llang va tahrirlang yoki nusxasini saqlang")

# ── ishlov markazi postprotsessori ──
a("xnc.pp.title", "Постпроцессор (обрабатывающий центр)", "Postprotsessor (ishlov markazi)")
a("xnc.pp.output", "Формат", "Format"); a("xnc.pp.long_side", "Длинная сторона детали", "Detalning uzun tomoni")
a("xnc.pp.ls.any", "Как есть", "O'zgarishsiz"); a("xnc.pp.ls.horizontal", "По горизонтали", "Gorizontal")
a("xnc.pp.ls.vertical", "По вертикали", "Vertikal")
a("xnc.pp.download", "Скачать файл", "Faylni yuklab olish")
a("xnc.pp.note", "Координаты уже с учётом поворота, зеркала и начала координат; формат файла задаёт шаблон (Настройки → Постпроцессоры)",
  "Koordinatalar burish, ko'zgu va koordinata boshini hisobga olgan; fayl formatini shablon belgilaydi (Sozlamalar → Postprotsessorlar)")
a("xnc.pp.unbound", "формат не подключён", "format ulanmagan")
a("xnc.pp.builtin.json", "XNC JSON — вычисленные операции", "XNC JSON — hisoblangan amallar")

# ── DXF import ──
a("xnc.dxf.import", "Импорт из DXF", "DXF dan import")
a("xnc.dxf.title", "Импорт контура из DXF", "DXF dan kontur import")
a("xnc.dxf.file", "Файл DXF (ASCII)", "DXF fayl (ASCII)"); a("xnc.dxf.mode", "Куда добавить", "Qayerga qo'shish")
a("xnc.dxf.origin", "Начало координат", "Koordinata boshi")
a("xnc.dxf.origin_bbox", "Левый верхний угол чертежа → (0, 0)", "Chizmaning chap-yuqori burchagi → (0, 0)")
a("xnc.dxf.origin_zero", "Координаты DXF без сдвига", "DXF koordinatalari siljitilmaydi")
a("xnc.dxf.flip", "Отразить ось Y (в DXF вверх, в XNC вниз)", "Y o'qini aks ettirish (DXF da yuqoriga, XNC da pastga)")
a("xnc.dxf.depth", "Глубина (выражение)", "Chuqurlik (ifoda)"); a("xnc.dxf.tool_d", "Диаметр фрезы, мм", "Freza diametri, mm")
a("xnc.dxf.corr", "Коррекция на радиус", "Radius korreksiyasi")
a("xnc.dxf.drill_max", "Окружности до этого диаметра — отверстия (0 — нет)", "Shu diametrgacha aylanalar — teshik (0 — yo'q)")
a("xnc.dxf.run", "Импортировать", "Import qilish")
a("xnc.dxf.done", "DXF: контуров {{c}}, отверстий {{d}}", "DXF: konturlar {{c}}, teshiklar {{d}}")
a("xnc.dxf.note", "Читаются LINE, ARC, LWPOLYLINE, POLYLINE, CIRCLE; слои и цвета игнорируются. Концы линий и дуг, совпавшие с допуском 0,01 мм, соединяются в контур.",
  "LINE, ARC, LWPOLYLINE, POLYLINE, CIRCLE o'qiladi; qatlam va rang e'tiborsiz. Uchlari 0,01 mm aniqlikda mos tushgan chiziq va yoylar bitta konturga birlashadi.")

# ── yorliqlar ──
a("help.hk.xnc_editor", "XNC-редактор: F4 служебные команды, F9 состояние, Ctrl+←/→ уровень, Ctrl+↑/↓ переместить, Ctrl+Space параметры",
  "XNC muharriri: F4 xizmat buyruqlari, F9 holat, Ctrl+←/→ daraja, Ctrl+↑/↓ ko'chirish, Ctrl+Space parametrlar")
