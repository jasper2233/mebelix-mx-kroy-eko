# -*- coding: utf-8 -*-
"""W8 · «Настройки → XNC»: Инструменты, Палитра, Ограничения; cheklov xabarlari (i18n_src.py yuklaydi)."""

a("settings.page.xnc", "XNC редактор", "XNC muharriri")
a("xs.tab.tools", "Инструменты", "Asboblar"); a("xs.tab.palette", "Палитра", "Palitra"); a("xs.tab.limits", "Ограничения", "Cheklovlar")
a("xs.defaults", "Стандартные значения", "Standart qiymatlar")
a("xs.discard", "Отменить изменения", "O'zgarishlarni bekor qilish")
a("xs.unsaved", "Есть несохранённые изменения", "Saqlanmagan o'zgarishlar bor")

# ── Инструменты ──
a("xs.col.plane", "Плоскость", "Tekislik"); a("xs.col.d", "Диаметр", "Diametr"); a("xs.col.through", "Сквозное", "Teshib o'tuvchi")
a("xs.col.name", "Наименование", "Nomi"); a("xs.col.depth", "Глубина", "Chuqurlik"); a("xs.col.comment", "Комментарий", "Izoh")
a("xs.col.icon", "Иконка", "Belgi")
for k, ru, uz in [("front", "Передняя", "Old (frontal)"), ("left", "Левая", "Chap"), ("right", "Правая", "O'ng"),
                  ("top", "Верхняя", "Yuqori"), ("bottom", "Нижняя", "Pastki")]:
    a(f"xs.plane.{k}", ru, uz)
a("xs.tools.hint",
  "Если команда сверления не задаёт диаметр или глубину, они берутся по имени инструмента (поле T): сначала Tool в программе, затем эта таблица. "
  "Имена из таблицы предлагаются в командах Tool, сверления, фрезеровки и пазования.",
  "Agar burg'ulash buyrug'i diametr yoki chuqurlikni bermasa, ular asbob nomi (T maydoni) bo'yicha olinadi: avval dasturdagi Tool, keyin shu jadval. "
  "Jadvaldagi nomlar Tool, burg'ulash, frezalash va pazlash buyruqlarida taklif qilinadi.")
a("xs.tools.empty", "Таблица пуста — нажмите «+» или «Стандартные значения»", "Jadval bo'sh — «+» yoki «Standart qiymatlar» ni bosing")
a("xs.tools.invalid", "Имя инструмента не должно быть пустым или повторяться в одной плоскости; диаметр больше нуля",
  "Asbob nomi bo'sh bo'lmasligi va bir tekislikda takrorlanmasligi kerak; diametr noldan katta bo'lsin")
a("xs.tools.defaults_q", "Заменить таблицу стандартным набором инструментов (изменения не сохранены до «Сохранить»)?",
  "Jadval standart asboblar to'plami bilan almashtirilsinmi («Saqlash» gacha o'zgarish saqlanmaydi)?")

# ── Палитра ──
a("xs.pal.hint", "Выключенные команды не показываются в палитре редактора XNC. Порядок строк — порядок кнопок.",
  "O'chirilgan buyruqlar XNC muharriri palitrasida ko'rinmaydi. Qatorlar tartibi — tugmalar tartibi.")
a("xs.pal.count", "Включено: {{n}} из {{m}}", "Yoqilgan: {{n}} / {{m}}")
a("xs.pal.all", "Включить все", "Hammasini yoqish")

# ── Ограничения ──
a("xs.c.mode_label", "Режим", "Rejim")
a("xs.c.mode.off", "Выключить", "O'chirish"); a("xs.c.mode.warn", "Предупреждать", "Ogohlantirish")
a("xs.c.mode.block", "Ошибка (блокировать)", "Xato (bloklash)")
a("xs.c.mode_hint.off", "Ограничения не проверяются, деталь не разворачивается.",
  "Cheklovlar tekshirilmaydi, detal burilmaydi.")
a("xs.c.mode_hint.warn", "Нарушения показываются как предупреждения; деталь разворачивается по настройкам.",
  "Buzilishlar ogohlantirish sifatida ko'rsatiladi; detal sozlamalarga ko'ra buriladi.")
a("xs.c.mode_hint.block", "Нарушения показываются как ошибки; деталь разворачивается по настройкам.",
  "Buzilishlar xato sifatida ko'rsatiladi; detal sozlamalarga ko'ra buriladi.")
a("xs.c.range_bad", "Минимум больше максимума — исправьте значения", "Minimal qiymat maksimaldan katta — qiymatlarni to'g'rilang")
a("xs.c.size", "Габаритные размеры деталей", "Detal gabaritlari")
a("xs.c.length_min", "Длина(X) минимум", "Uzunlik(X) minimum"); a("xs.c.length_max", "Длина(X) максимум", "Uzunlik(X) maksimum")
a("xs.c.width_min", "Ширина(Y) минимум", "Eni(Y) minimum"); a("xs.c.width_max", "Ширина(Y) максимум", "Eni(Y) maksimum")
a("xs.c.thickness_min", "Толщина(Z) минимум", "Qalinlik(Z) minimum"); a("xs.c.thickness_max", "Толщина(Z) максимум", "Qalinlik(Z) maksimum")
a("xs.c.rotate_long", "Разворачивать деталь длинной стороной", "Detalni uzun tomoni bo'yicha burish")
a("xs.c.long.horizontal", "По горизонтали", "Gorizontal"); a("xs.c.long.vertical", "По вертикали", "Vertikal")
a("xs.c.rotate_corner", "Разворачивать деталь кромкой в", "Detalni kromka bilan burchakka burish")
for k, ru, uz in [("LT", "Левый верхний угол", "Chap yuqori burchak"), ("RT", "Правый верхний угол", "O'ng yuqori burchak"),
                  ("LB", "Левый нижний угол", "Chap pastki burchak"), ("RB", "Правый нижний угол", "O'ng pastki burchak")]:
    a(f"xs.c.corner.{k}", ru, uz)
a("xs.c.hole_center", "Максимальное расстояние между центром горизонтального отверстия и фронтальной плоскостью",
  "Gorizontal teshik markazidan frontal tekislikkacha eng katta masofa")
for k, ru, uz in [("top", "Сверление сверху", "Yuqoridan burg'ulash"), ("bottom", "Сверление снизу", "Pastdan burg'ulash"),
                  ("left", "Сверление слева", "Chapdan burg'ulash"), ("right", "Сверление справа", "O'ngdan burg'ulash")]:
    a(f"xs.c.hc.{k}", ru, uz)
a("xs.c.groove", "Пазование", "Pazlash")
a("xs.c.groove_h", "Горизонтальное пазование", "Gorizontal pazlash"); a("xs.c.groove_v", "Вертикальное пазование", "Vertikal pazlash")
a("xs.c.allowed", "разрешено", "ruxsat etilgan")
a("xs.c.groove_margin", "Минимальный отступ от края детали к пазу", "Detal chetidan pazgacha eng kichik masofa")
for k, ru, uz in [("top", "Сверху", "Yuqoridan"), ("bottom", "Снизу", "Pastdan"), ("left", "Слева", "Chapdan"), ("right", "Справа", "O'ngdan")]:
    a(f"xs.c.gm.{k}", ru, uz)
a("xs.c.mill", "Фрезерование (радиусы)", "Frezalash (radiuslar)")
a("xs.c.mill_max", "Максимальное расстояние от детали до фрезы", "Detaldan frezagacha eng katta masofa")
a("xs.c.drill", "Ограничения по сверлению", "Burg'ulash cheklovlari")
a("xs.c.avoid_bottom", "Нежелательные горизонтальные сверления снизу", "Pastdan gorizontal burg'ulash — nomaqbul")
a("xs.c.preference", "предпочтение", "afzallik")
a("xs.c.blind_depth", "Для вертикальных глухих отверстий глубина сверления должна быть меньше толщины детали на",
  "Vertikal ko'r teshiklar uchun burg'ulash chuqurligi detal qalinligidan kamida shuncha kam bo'lsin")
a("xs.c.hole_gap", "Минимальное расстояние между краями отверстий", "Teshiklar chetlari orasidagi eng kichik masofa")
a("xs.c.edge_front", "Минимальное расстояние между краем детали и краем фронтального отверстия",
  "Detal chetidan frontal teshik chetigacha eng kichik masofa")
a("xs.c.edge_horizontal", "Минимальное расстояние между краем детали и краем горизонтального отверстия",
  "Detal chetidan gorizontal teshik chetigacha eng kichik masofa")

# ── Xabarlar (XNC paneli) ──
a("xs.issues.title", "Ограничения станка: {{n}}", "Stanok cheklovlari: {{n}}")
a("xs.issues.go", "Перейти к команде", "Buyruqqa o'tish")
a("xs.issues.turn", "Деталь повёрнута на {{n}}° (ограничения станка)", "Detal {{n}}° ga burildi (stanok cheklovlari)")
