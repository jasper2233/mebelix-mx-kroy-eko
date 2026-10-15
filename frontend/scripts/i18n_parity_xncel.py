# -*- coding: utf-8 -*-
"""(EL) «Настройка символов и цветов»; (XNC) «Шаблон»: «Показать все изображение», «Переменные», «Инструменты»
(docs/mebelix/W_PARITY_SPEC.md §1, §2; i18n_src.py yuklaydi)."""

# ── EL ──
a("el.sym.title", "Настройка символов и цветов", "Belgilar va ranglarni sozlash")
a("el.sym.insert", "Вставить [CTRL]+[PAGE UP]", "Qo'yish [CTRL]+[PAGE UP]")
a("el.sym.delete", "Удалить [DEL]", "O'chirish [DEL]")
a("el.sym.col.symbol", "Символ", "Belgi")
a("el.sym.col.color", "Цвет", "Rang")
a("el.color_btn", "Цвет", "Rang")

# ── XNC ──
a("xnc.fit", "Показать все изображение", "Tasvirni to'liq ko'rsatish")
a("xnc.vars.title", "Переменные", "O'zgaruvchilar")
a("xnc.vars.col.name", "Наименование", "Nomi")
a("xnc.vars.col.desc", "Описание", "Tavsif")
a("xnc.vars.col.type", "Тип", "Turi")
a("xnc.vars.col.value", "Значение", "Qiymat")
a("xnc.tools.title", "Инструменты", "Asboblar")
a("xnc.tools.hint", "Список инструментов: Настройки → XNC редактор → Инструменты",
  "Asboblar ro'yxati: Sozlamalar → XNC muharriri → Asboblar")
for _k, _ru, _uz in [
    ("allowanceB", "Припуск на обработку заготовки - Снизу", "Zagotovka ishlovi uchun pripusk - Pastdan"),
    ("allowanceL", "Припуск на обработку заготовки - Слева", "Zagotovka ishlovi uchun pripusk - Chapdan"),
    ("allowanceR", "Припуск на обработку заготовки - Справа", "Zagotovka ishlovi uchun pripusk - O'ngdan"),
    ("allowanceT", "Припуск на обработку заготовки - Сверху", "Zagotovka ishlovi uchun pripusk - Yuqoridan"),
    ("bySizeDetail", "По размеру детали", "Detal o'lchami bo'yicha"),
    ("dx", "Длина", "Uzunlik"), ("dy", "Ширина", "En"), ("dz", "Толщина", "Qalinlik"),
    ("ebj", "Оклейка кромки снизу. - Ширина прифуговки", "Pastki kromka. - Prifugovka eni"),
    ("ebt", "Оклейка кромки снизу. - Толщина", "Pastki kromka. - Qalinlik"),
    ("elj", "Оклейка кромки слева. - Ширина прифуговки", "Chap kromka. - Prifugovka eni"),
    ("elt", "Оклейка кромки слева. - Толщина", "Chap kromka. - Qalinlik"),
    ("erj", "Оклейка кромки справа. - Ширина прифуговки", "O'ng kromka. - Prifugovka eni"),
    ("ert", "Оклейка кромки справа. - Толщина", "O'ng kromka. - Qalinlik"),
    ("etj", "Оклейка кромки сверху. - Ширина прифуговки", "Yuqori kromka. - Prifugovka eni"),
    ("ett", "Оклейка кромки сверху. - Толщина", "Yuqori kromka. - Qalinlik"),
    ("origin_x", "Начало координат X", "Koordinata boshi X"),
    ("origin_y", "Начало координат Y", "Koordinata boshi Y"),
    ("xncSide", "Сторона", "Tomon"),
]:
    a("xnc.vars.d." + _k, _ru, _uz)
