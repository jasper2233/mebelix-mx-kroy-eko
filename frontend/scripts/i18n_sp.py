# -*- coding: utf-8 -*-
"""(SP) Обработка поверхности — interfeys matnlari (W12). i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan)."""

# ── operatsiyalar jadvali ──
a("ops.default.SP", "Материал поверхности{{n}}", "Sirt materiali{{n}}")

# ── panel: parametrlar ──
a("sp.g.material", "Материал", "Material")
a("sp.g.size", "Размеры", "O'lchamlar")
a("sp.p.count_material", "Учитывать материал", "Materialni hisobga olish")
a("sp.p.waste", "Процент отхода материала", "Material chiqindi foizi")
a("sp.p.rest", "Длина остатка по краям", "Chetlardagi qoldiq uzunligi")
a("sp.p.rest_hint", "Добавляется к длине и ширине детали с каждого края при расчёте расхода материала",
  "Material sarfini hisoblashda detal uzunligi va eniga har chetdan qo'shiladi")
a("sp.p.price", "Цена материала (м²)", "Material narxi (m²)")
a("sp.p.size_mode", "Режим размеров", "O'lcham rejimi")
a("sp.p.size_mode_hint", "Какой размер детали берётся для площади обработки: пильный (заготовка + припуск) или заготовка",
  "Ishlov maydoni uchun detalning qaysi o'lchami olinadi: pilniy (zagotovka + pripusk) yoki zagotovka")
a("sp.size.saw", "Пильный размер", "Pilniy o'lcham")
a("sp.size.blank", "Размер заготовки", "Zagotovka o'lchami")
a("sp.p.op_price", "Цена операции за 1 м²", "Operatsiya narxi (1 m²)")
a("sp.p.area", "Площадь обработки", "Ishlov maydoni")
a("sp.p.material_m2", "Расход материала", "Material sarfi")
a("sp.p.mat_cost", "Стоимость материала", "Material narxi")
a("sp.p.op_cost", "Стоимость операции", "Operatsiya narxi")
a("sp.p.cost", "Стоимость", "Jami narx")
a("sp.defaults_saved", "Параметры обработки поверхности сохранены как стандартные", "Sirt ishlovi parametrlari standart sifatida saqlandi")
a("sp.help", "Площадь = (длина × ширина) × число сторон × количество; материал = площадь с остатком по краям × (1 + % отхода); сторона назначается детали в окне «Свойства» или в колонках ЛП / ТП",
  "Maydon = (uzunlik × en) × tomonlar soni × soni; material = chetlardagi qoldiqli maydon × (1 + chiqit %); tomon detalga «Xossalar» oynasida yoki YuzS / OrqS ustunlarida belgilanadi")

# ── «Детали» ──
a("sp.col.front", "Лиц.", "Old")
a("sp.col.back", "Обр.", "Orqa")
a("sp.col.area", "Площадь, м²", "Maydon, m²")
a("sp.hint", "Обработка назначается детали в окне «Свойства» (раздел «(SP) Обработка поверхности») или в колонках ЛП / ТП таблицы деталей.",
  "Ishlov detalga «Xossalar» oynasida («(SP) Sirt ishlovi» bo'limi) yoki detallar jadvalidagi YuzS / OrqS ustunlarida belgilanadi.")

# ── окно «Свойства» детали ──
a("pp.surface_face", "Лицевая сторона", "Old (lits) tomon")
a("pp.surface_back", "Обратная сторона", "Orqa tomon")

# ── «Печать отчета» ──
a("print.sec.sp", "(SP) Обработка поверхности", "(SP) Sirt ishlovi")
a("print.f.sp_params", "Параметры и расчёт (площадь, материал, стоимость)", "Parametrlar va hisob (maydon, material, narx)")
a("print.f.sp_parts", "Детали с обработкой поверхности", "Sirt ishlovi bor detallar")
