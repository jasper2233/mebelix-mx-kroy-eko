# -*- coding: utf-8 -*-
"""W-parity (2026-10-04): (CL) «Параметры» — yetishmayotgan beshta parametr (W_PARITY_SPEC.md §3). i18n_src.py shu faylni o'zi
yuklaydi (`a` — o'sha yerdan; `i18n_cl.py` dan keyin yuklanadi). (SP) «Режим размеров» matnlari — `i18n_sp.py` da."""

# ── «Остаток»: «Размер остатков с учетом торцовки» (model maydoni — `waste_incl_trim`) ──
a("cl.p.remnant", "Остаток", "Qoldiq")
a("cl.p.rem_trim", "Размер остатков с учетом торцовки", "Qoldiq o'lchami torsovkani hisobga olib")
a("cl.p.rem_trim_hint",
  "☑ — длина остатка без зоны торцовки (80), последний торцевой рез делается; ☐ — остаток включает зону торцовки (110)",
  "☑ — qoldiq uzunligi torsovka zonasisiz (80), oxirgi torsovka kesimi qilinadi; ☐ — qoldiq torsovka zonasini ham oladi (110)")
a("cl.p.limits", "Ограничения", "Cheklovlar")

# ── «Параметры раскроя» ──
a("cl.p.max_types", "Максимальное количество разновидностей деталей на карте кроя", "Kroy kartasidagi detal xillarining maksimal soni")
a("cl.p.max_types_hint", "Сколько разных длин деталей может быть на одной полосе. «Не ограничено» — без ограничения",
  "Bitta polosada nechta xil uzunlikdagi detal bo'lishi mumkin. «Cheklanmagan» — cheklovsiz")
a("cl.p.unlimited", "Не ограничено", "Cheklanmagan")
a("cl.p.merge", "Объединение деталей", "Detallarni birlashtirish")
a("cl.p.merge_hint", "Флажок сохраняется в проекте; детали одинаковой длины при погонажном раскрое объединяются всегда",
  "Belgi loyihada saqlanadi; pogonaj kroyda bir xil uzunlikdagi detallar doim birlashtiriladi")
a("cl.p.group_props", "Группировка деталей по свойствам", "Detallarni xossalar bo'yicha guruhlash")
a("cl.p.group_props_hint", "Значение сохраняется в проекте; на погонажный раскрой не влияет",
  "Qiymat loyihada saqlanadi; pogonaj kroyga ta'sir qilmaydi")
a("cl.p.save_draw", "Сохранение чертежа карт кроя", "Kroy kartalari chizmasini saqlash")
a("cl.p.save_draw_hint", "Флажок сохраняется в проекте и в экспорте; карты раскроя сохраняются вместе с проектом всегда",
  "Belgi loyihada va eksportda saqlanadi; kroy kartalari loyiha bilan birga doim saqlanadi")
a("cl.p.no_effect", "на раскрой не влияет", "kroyga ta'sir qilmaydi")

# ── F1 yordam (phelp_t — sarlavha, phelp — matn) ──
for _k, (_tru, _tuz, _hru, _huz) in {
    "cl_trim_waste": ("Размер остатков с учетом торцовки", "Qoldiq o'lchami torsovkani hisobga olib",
                      "Включено: длина остатка берётся без зоны торцовки (например 80), после остатка делается ещё один торцевой рез. Выключено: остаток включает пропил и торцовку (110), последнего торцевого реза нет. По этой длине остаток относится к отходу или деловому остатку.",
                      "Yoqilgan: qoldiq uzunligi torsovka zonasisiz olinadi (masalan 80), qoldiqdan keyin yana bitta torsovka kesimi qilinadi. O'chirilgan: qoldiq propil va torsovkani ham oladi (110), oxirgi torsovka kesimi yo'q. Qoldiq shu uzunlik bo'yicha otxod yoki deloviy qoldiq deb olinadi."),
    "cl_max_types": ("Максимальное количество разновидностей деталей на карте кроя", "Kroy kartasidagi detal xillarining maksimal soni",
                     "Ограничивает число разных длин деталей на одной полосе (карте кроя): оператору проще сортировать. Разновидность — пильная длина детали. При ограничении полос может понадобиться больше. «Не ограничено» — без ограничения.",
                     "Bitta polosadagi (kroy kartasidagi) xil uzunliklar sonini cheklaydi: operatorga saralash osonroq. Xil — detalning pilniy uzunligi. Cheklovda ko'proq polosa kerak bo'lishi mumkin. «Cheklanmagan» — cheklovsiz."),
    "cl_merge": ("Объединение деталей", "Detallarni birlashtirish",
                 "Флажок сохраняется в проекте и в экспорте. В погонажном раскрое детали одинаковой длины всегда считаются одной позицией, поэтому на результат раскроя флажок не влияет.",
                 "Belgi loyihada va eksportda saqlanadi. Pogonaj kroyda bir xil uzunlikdagi detallar doim bitta pozitsiya hisoblanadi, shuning uchun belgi kroy natijasiga ta'sir qilmaydi."),
    "cl_group_props": ("Группировка деталей по свойствам", "Detallarni xossalar bo'yicha guruhlash",
                       "Значение сохраняется в проекте и в экспорте. На погонажный раскрой не влияет.",
                       "Qiymat loyihada va eksportda saqlanadi. Pogonaj kroyga ta'sir qilmaydi."),
    "cl_save_draw": ("Сохранение чертежа карт кроя", "Kroy kartalari chizmasini saqlash",
                     "Флажок сохраняется в проекте и в экспорте. Карты раскроя сохраняются вместе с проектом всегда; на раскрой флажок не влияет.",
                     "Belgi loyihada va eksportda saqlanadi. Kroy kartalari loyiha bilan birga doim saqlanadi; belgi kroyga ta'sir qilmaydi."),
}.items():
    a(f"phelp_t.{_k}", _tru, _tuz)
    a(f"phelp.{_k}", _hru, _huz)
