# -*- coding: utf-8 -*-
"""(O) Комплектация и другие действия — interfeys matnlari (W5). i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan)."""

# ── operatsiyalar jadvali ──
a("ops.add_o", "Добавить: (O) Комплектация", "Qo'shish: (O) Komplektatsiya")
a("ops.default.O", "Комплектация {{n}}", "Komplektatsiya {{n}}")

# ── panel: yorliqlar va parametrlar ──
a("o.tab.materials", "Материалы", "Materiallar")
a("o.p.owner", "Владелец", "Egasi")
a("o.p.owner_project", "Проект", "Loyiha")
a("o.p.owner_item", "№{{n}} {{name}} ({{qty}} шт)", "№{{n}} {{name}} ({{qty}} dona)")
a("o.p.owner_hint", "Если владелец — изделие, количество каждой позиции и стоимость операции умножаются на количество этого изделия",
  "Egasi mahsulot bo'lsa, har bir pozitsiya soni va operatsiya narxi shu mahsulot soniga ko'paytiriladi")
a("o.p.mat_cost", "Стоимость материала", "Material narxi")
a("o.p.op_cost", "Стоимость операции", "Ish narxi")
a("o.p.cost", "Стоимость", "Jami narx")
a("o.p.description", "Описание", "Izoh")
a("o.p.mult_hint", "Количество материалов и стоимость операции умножены на количество изделия: {{n}}",
  "Material miqdori va ish narxi mahsulot soniga ko'paytirildi: {{n}}")
a("o.msg.owner_lost", "Изделие-владелец удалено — операция теперь принадлежит проекту",
  "Egasi bo'lgan mahsulot o'chirildi — operatsiya endi loyihaga tegishli")

# ── materiallar jadvali ──
a("o.col.code", "Код", "Kod")
a("o.col.name", "Наименование", "Nomi")
a("o.col.unit", "Ед.И", "Birlik")
a("o.col.qty", "Кол", "Soni")
a("o.col.price", "Цена", "Narx")
a("o.col.sum", "Стоимость", "Summa")
a("o.add", "Добавить строку", "Qator qo'shish")
a("o.insert", "Вставить строку перед текущей", "Joriy qator oldiga qo'yish")
a("o.from_catalog", "Добавить из каталога товаров", "Tovarlar katalogidan qo'shish")
a("o.catalog_title", "Каталог товаров — комплектующие", "Tovarlar katalogi — komplektlar")
a("o.paste_hint",
  "Вставка из Excel / Open Office: столбцы Код, Наименование, Ед.И, Кол, Цена. Скопируйте ячейки (Ctrl+C), щёлкните в таблице и нажмите Ctrl+V",
  "Excel / Open Office dan qo'yish: ustunlar Kod, Nomi, Birlik, Soni, Narx. Katakchalarni nusxalang (Ctrl+C), jadvalni bosing va Ctrl+V")
a("o.empty", "Таблица материалов пуста — добавьте строку (Ctrl+PgDn) или вставьте данные из Excel (Ctrl+V)",
  "Materiallar jadvali bo'sh — qator qo'shing (Ctrl+PgDn) yoki Excel dan qo'ying (Ctrl+V)")
a("o.total", "Всего позиций: {{n}}", "Jami pozitsiyalar: {{n}}")
a("o.total_mult", "с учётом количества изделия (× {{n}})", "mahsulot soni bilan (× {{n}})")
a("o.pasted", "Добавлено строк: {{n}}", "Qo'shilgan qatorlar: {{n}}")
a("o.paste_nothing", "Нечего добавлять", "Qo'shiladigan narsa yo'q")
a("o.paste_skipped", "Пропущено строк: {{n}}", "O'tkazib yuborilgan qatorlar: {{n}}")
a("o.defaults_saved", "Параметры комплектации сохранены как стандартные", "Komplektatsiya parametrlari standart sifatida saqlandi")

# ── «Печать отчета» ──
a("print.sec.o", "(O) Комплектация", "(O) Komplektatsiya")
a("print.f.o_params", "Параметры (владелец, стоимость, описание)", "Parametrlar (egasi, narx, izoh)")
a("print.f.o_materials", "Таблица материалов", "Materiallar jadvali")
