"""(CN) Нестинговый раскрой — hisobot (chop) matnlari, ru / uz. `render.T` ga qo'shiladi (render.py), `cn_render` ishlatadi."""

CN_T: dict[str, dict[str, str]] = {
    "ru": {
        "cn": "Нестинговый раскрой", "cn_params": "Параметры", "cn_thick": "Толщина", "cn_tool": "Диаметр фрезы",
        "cn_offset": "Отступ траектории от контура", "cn_gap": "Доп. расстояние между деталями", "cn_spacing": "Мин. расстояние между деталями",
        "cn_margin": "Отступ от края листа", "cn_rot": "Повороты", "cn_rot_none": "нет", "cn_rot_90": "0/90/180/270°",
        "cn_rot_free": "шаг {s}°", "cn_grain": "Учёт текстуры", "cn_xnc": "Контуры из XNC", "cn_yes": "Да", "cn_no": "Нет",
        "cn_price": "Цена материала", "cn_price_sheet": "за лист", "cn_price_m2": "за м²", "cn_est_fill": "Расчетный процент заполнения",
        "cn_usage": "Количество материала", "cn_cost_mat": "Стоимость материала", "cn_op_base": "Расчет стоимости операции по",
        "cn_op_price": "Цена операции", "cn_cost_op": "Стоимость операции", "cn_base0": "Длине реза (периметр контуров)",
        "cn_base1": "Периметру деталей", "cn_base2": "Площади деталей", "cn_base3": "Площади материала",
        "cn_quality": "Оптимизация", "cn_parts_t": "Детали", "cn_shape": "Форма", "cn_shape_rect": "прямоуг.", "cn_shape_contour": "контур",
        "cn_holes": "Вырезов", "cn_area": "Площадь, м²", "cn_perim": "Периметр, м", "cn_remnants": "Остатки",
        "cn_in_part": "В детали №", "cn_free": "Свободное место", "cn_kind": "Тип", "cn_business": "Деловой", "cn_plain": "Остаток",
        "cn_sheets": "Листы", "cn_label": "Место этикетки",
    },
    "uz": {
        "cn": "Nesting kroy", "cn_params": "Parametrlar", "cn_thick": "Qalinligi", "cn_tool": "Freza diametri",
        "cn_offset": "Trayektoriyaning konturdan masofasi", "cn_gap": "Detallar orasidagi qo'shimcha masofa",
        "cn_spacing": "Detallar orasidagi min. masofa", "cn_margin": "List chetidan masofa", "cn_rot": "Burilishlar", "cn_rot_none": "yo'q",
        "cn_rot_90": "0/90/180/270°", "cn_rot_free": "{s}° qadam", "cn_grain": "Tekstura hisobi", "cn_xnc": "XNC konturlari",
        "cn_yes": "Ha", "cn_no": "Yo'q", "cn_price": "Material narxi", "cn_price_sheet": "1 list", "cn_price_m2": "1 m²",
        "cn_est_fill": "Hisobiy to'ldirish foizi", "cn_usage": "Material miqdori", "cn_cost_mat": "Material qiymati",
        "cn_op_base": "Operatsiya narxi asosi", "cn_op_price": "Operatsiya narxi", "cn_cost_op": "Operatsiya qiymati",
        "cn_base0": "Kesim uzunligi (konturlar perimetri)", "cn_base1": "Detallar perimetri", "cn_base2": "Detallar maydoni",
        "cn_base3": "Material maydoni", "cn_quality": "Optimizatsiya", "cn_parts_t": "Detallar", "cn_shape": "Shakl",
        "cn_shape_rect": "to'rtburchak", "cn_shape_contour": "kontur", "cn_holes": "Ichki kesimlar", "cn_area": "Maydon, m²",
        "cn_perim": "Perimetr, m", "cn_remnants": "Qoldiqlar", "cn_in_part": "Detal №", "cn_free": "Bo'sh joy", "cn_kind": "Tur",
        "cn_business": "Deloviy", "cn_plain": "Qoldiq", "cn_sheets": "Listlar", "cn_label": "Etiketka o'rni",
    },
}
