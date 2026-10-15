"""(CL) Погонажный раскрой — hisobot (chop) matnlari, ru / uz. `render.T` ga qo'shiladi (render.py), `cl_render` ishlatadi."""

CL_T: dict[str, dict[str, str]] = {
    "ru": {
        "cl": "Погонажный раскрой", "cl_params": "Параметры", "cl_width": "Ширина", "cl_thick": "Толщина",
        "cl_kerf": "Толщина пилы", "cl_trim": "Торцовка", "cl_end_offset": "Мин. отступ в конце",
        "cl_waste_min": "Мин. размер отхода", "cl_business_min": "Длина делового отхода",
        "cl_trim_waste": "Размер остатков с учетом торцовки", "cl_pack": "Высота пакета", "cl_mult": "Кратность",
        "cl_est_fill": "Расчетный процент заполнения", "cl_price": "Цена материала", "cl_usage": "Количество материала",
        "cl_cost_mat": "Стоимость материала", "cl_op_base": "Расчет стоимости операции по", "cl_op_price": "Цена операции",
        "cl_cost_op": "Стоимость операции", "cl_price_m": "за м", "cl_price_strip": "за полосу",
        "cl_base0": "Длине реза с торцовкой", "cl_base1": "Длине реза без торцовки", "cl_base2": "Длине материала",
        "cl_base3": "Длине деталей", "cl_edge_end": "О-ка торцов", "cl_strips": "Полосы", "cl_strip": "Полоса",
        "cl_remnants": "Остатки", "cl_strips_n": "Полосы", "cl_used": "Исп. Кол-во", "cl_kind": "Тип",
        "cl_k_strip": "Полоса", "cl_k_waste": "Отход", "cl_k_business": "Деловой отход", "cl_parts_len": "Длина деталей",
        "cl_mat_len": "Длина материала", "cl_business_len": "Деловой остаток", "cl_cuts_len": "Длина реза",
        "cl_stat": "Итого", "cl_commands": "Таблица команд", "cl_yes": "Да", "cl_no": "Нет", "cl_len_short": "Длина",
    },
    "uz": {
        "cl": "Pogonaj kroy", "cl_params": "Parametrlar", "cl_width": "Eni", "cl_thick": "Qalinligi",
        "cl_kerf": "Arra qalinligi", "cl_trim": "Torsovka", "cl_end_offset": "Oxiridagi min. otstup",
        "cl_waste_min": "Min. otxod o'lchami", "cl_business_min": "Deloviy otxod uzunligi",
        "cl_trim_waste": "Qoldiq o'lchami torsovkani hisobga olib", "cl_pack": "Paket balandligi", "cl_mult": "Kratnost",
        "cl_est_fill": "Hisobiy to'ldirish foizi", "cl_price": "Material narxi", "cl_usage": "Material miqdori",
        "cl_cost_mat": "Material qiymati", "cl_op_base": "Operatsiya narxi asosi", "cl_op_price": "Operatsiya narxi",
        "cl_cost_op": "Operatsiya qiymati", "cl_price_m": "1 m", "cl_price_strip": "1 polosa",
        "cl_base0": "Torsovka bilan kesim uzunligi", "cl_base1": "Torsovkasiz kesim uzunligi", "cl_base2": "Material uzunligi",
        "cl_base3": "Detallar uzunligi", "cl_edge_end": "Uchlar kromkasi", "cl_strips": "Polosalar", "cl_strip": "Polosa",
        "cl_remnants": "Qoldiqlar", "cl_strips_n": "Polosalar", "cl_used": "Ishlatildi", "cl_kind": "Tur",
        "cl_k_strip": "Polosa", "cl_k_waste": "Otxod", "cl_k_business": "Deloviy otxod", "cl_parts_len": "Detallar uzunligi",
        "cl_mat_len": "Material uzunligi", "cl_business_len": "Deloviy qoldiq", "cl_cuts_len": "Kesim uzunligi",
        "cl_stat": "Jami", "cl_commands": "Buyruqlar jadvali", "cl_yes": "Ha", "cl_no": "Yo'q", "cl_len_short": "Uzunlik",
    },
}
