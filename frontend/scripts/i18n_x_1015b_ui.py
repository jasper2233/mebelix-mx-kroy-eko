# -*- coding: utf-8 -*-
"""2026-10-15, 2-sessiya — ekran mosligi (CS/CL/EL/O panellari va jadvallari onlayn tizim bilan bir xil ko'rinishda).
`a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi. Bu fayl `i18n_cl.py`, `i18n_cs_w2.py`, `i18n_parity_clsp.py` dan
KEYIN yuklanadi, shuning uchun bir nechta mavjud kalit shu yerda qayta belgilanadi (yorliqlar onlayn tizimdagi so'zlar bilan)."""

# ── Parametr panellari: bizning qo'shimcha qatorlar guruhi (asosiy ro'yxat onlayn bilan bir xil qoladi) ──
a("cs.p.extra", "Дополнительно (MebeliX)", "Qo'shimcha (MebeliX)")
a("cs.p.extra_hint", "Параметры, которых нет в привычной системе: собственные настройки MebeliX Kroy",
  "Odatiy tizimda yo'q parametrlar: MebeliX Kroy ning o'z sozlamalari")

# «Группировка деталей по свойствам» — havola (tugma emas); yordam matni «?» orqali
a("phelp_t.group_props", "Группировка деталей по свойствам", "Detallarni xossalar bo'yicha guruhlash")
a("phelp.group_props", "В привычной системе ссылка открывает выбор свойств, по которым одинаковые детали объединяются в одну позицию раскроя; она доступна вместе с флажком «Объединение деталей». В MebeliX Kroy одинаковые детали объединяются автоматически, поэтому отдельная настройка не требуется — ссылка оставлена для единообразия.",
  "Odatiy tizimda bu havola bir xil detallar bitta kroy pozitsiyasiga qaysi xossalar bo'yicha birlashtirilishini tanlash oynasini ochadi; u «Объединение деталей» belgisi bilan birga faol. MebeliX Kroy da bir xil detallar avtomatik birlashtiriladi, shuning uchun alohida sozlama kerak emas — havola bir xillik uchun qoldirilgan.")
a("phelp.merge", "Флажок сохраняется в проекте и в экспорте. В MebeliX Kroy одинаковые детали объединяются при раскрое автоматически, поэтому на результат раскроя флажок не влияет. Вместе с ним становится доступна ссылка «Группировка деталей по свойствам».",
  "Belgi loyihada va eksportda saqlanadi. MebeliX Kroy da bir xil detallar kroyda avtomatik birlashtiriladi, shuning uchun belgi kroy natijasiga ta'sir qilmaydi. U bilan birga «Группировка деталей по свойствам» havolasi faol bo'ladi.")
a("phelp.save_draw", "Флажок сохраняется в проекте и в экспорте. Карты раскроя в MebeliX Kroy всегда сохраняются вместе с проектом, поэтому на работу программы флажок не влияет.",
  "Belgi loyihada va eksportda saqlanadi. MebeliX Kroy da kroy kartalari doim loyiha bilan birga saqlanadi, shuning uchun belgi dastur ishiga ta'sir qilmaydi.")
a("phelp.material_qty", "Расход материала. До раскроя — ориентировочный расчёт (по проценту заполнения, см. подсказку поля), после раскроя — по результату: площадь листов минус деловые остатки. При «Расчет стоимости по листам» — в листах с учётом округления, иначе — в м².",
  "Material sarfi. Kroygacha — taxminiy hisob (to'ldirish foizi bo'yicha, maydon maslahatiga qarang), kroydan keyin — natija bo'yicha: listlar maydoni minus deloviy qoldiqlar. «Narxni listlar bo'yicha hisoblash» yoqilgan bo'lsa — yaxlitlash bilan listlarda, aks holda m² da.")
a("phelp.sheets_qty", "Сколько листов нужно взять со склада целиком: до раскроя — оценка по проценту заполнения, после раскроя — фактическое число листов в картах.",
  "Ombordan butun holda nechta list olish kerak: kroygacha — to'ldirish foizi bo'yicha baho, kroydan keyin — kartalardagi haqiqiy listlar soni.")

# ── CL «Параметры»: onlayn tizimdagi yorliqlar («Остаток», metrda «Длина делового остатка», to'liq «Минимальный размер детали») ──
a("cl.p.rem_min", "Мин. размер остатка", "Min. qoldiq o'lchami")
a("cl.p.business_len", "Длина делового остатка", "Deloviy qoldiq uzunligi")
a("cl.p.business_len_hint", "Значение в метрах (10 = 10000 мм); в проекте хранится в мм", "Qiymat metrda (10 = 10000 mm); loyihada mm da saqlanadi")
a("cl.p.min_part", "Минимальный размер детали", "Detalning minimal o'lchami")
a("cl.p.kerf_group_hint", "В погонажном раскрое детали в блоки не группируются — значение не используется",
  "Pogonaj kroyda detallar blokka guruhlanmaydi — qiymat ishlatilmaydi")
a("phelp_t.cl_waste_min", "Мин. размер остатка", "Min. qoldiq o'lchami")
a("phelp.cl_waste_min", "Остаток короче этого значения считается обычным отходом: в таблицу остатков не попадает и отдельный рез для него не делается.",
  "Bundan qisqa qoldiq oddiy chiqindi hisoblanadi: qoldiqlar jadvaliga kirmaydi va uning uchun alohida kesim qilinmaydi.")
a("phelp_t.cl_business_min", "Длина делового остатка", "Deloviy qoldiq uzunligi")
a("phelp.cl_business_min", "Остаток не короче этого значения — деловой: не входит в расход материала и может быть записан на склад для повторного использования. Задаётся в метрах (10 = 10000 мм).",
  "Bundan kam bo'lmagan qoldiq — deloviy: material sarfiga kirmaydi va qayta ishlatish uchun omborga yozilishi mumkin. Metrda beriladi (10 = 10000 mm).")
a("phelp_t.cl_min_part", "Минимальный размер детали", "Detalning minimal o'lchami")
a("phelp_t.cl_kerf_group", "Толщина пилы для групповых деталей", "Guruh detallar uchun arra qalinligi")
a("phelp.cl_kerf_group", "В листовом раскрое — пропил для деталей, сгруппированных в блок. В погонажном раскрое детали в блоки не группируются, поэтому значение не используется; поле оставлено для единообразия с листовым раскроем.",
  "Listli kroyda — blokka guruhlangan detallar uchun propil. Pogonaj kroyda detallar blokka guruhlanmaydi, shuning uchun qiymat ishlatilmaydi; maydon listli kroy bilan bir xillik uchun qoldirilgan.")
a("phelp.cl_kerf", "Ширина одного пропила. Между двумя соседними деталями всегда один пропил; в погонажном раскрое значение строго больше нуля. Рез только прямой (90°) поперечный: деталь не делится и не поворачивается.",
  "Bitta propil kengligi. Ikki qo'shni detal orasida doim bitta propil bor; pogonaj kroyda qiymat qat'iy noldan katta. Kesim faqat to'g'ri (90°) ko'ndalang: detal bo'linmaydi va aylantirilmaydi.")

# ── Jadvallar ──
a("pcd.name", "Наименование детали", "Detal nomi")
a("el.col.edge_m", "Д-на кромки", "Kromka uz.")
a("el.col.edge_m_hint", "Длина кромки, м", "Kromka uzunligi, m")
a("el.col.material_hint", "Изделие и операция раскроя (материал) детали", "Detalning mahsuloti va kroy operatsiyasi (materiali)")
a("sheets.col.cl_trim_hint", "Торцовка полосы — из параметров операции («Торцовка»)", "Polosa torsovkasi — operatsiya parametridan («Торцовка»)")

# ── CS «Раскрой»: o'ng panel havolasi (eskizlarga qaytish) ──
a("cut.maps_table", "Таблица карт", "Kartalar jadvali")

# ── Loyihalar ro'yxati: o'z loyihasi ──
a("projects.owner_me", "Мой", "Mening")

# ── (O) Комплектация: bitta mahsulot uchun narx va «ИК» / «Всего» ustunlari ──
a("o.p.cost_one", "Стоимость x 1шт", "Narx x 1 dona")
a("o.p.cost_one_hint", "Материалы + работа для одного изделия (без умножения на количество изделия)",
  "Bitta mahsulot uchun materiallar + ish (mahsulot soniga ko'paytirilmagan)")
a("o.col.used", "ИК", "IK")
a("o.col.used_hint", "Используемое количество = Кол × количество изделия-владельца", "Ishlatiladigan soni = Soni × ega mahsulot soni")
a("o.col.total", "Всего", "Jami")
a("o.col.total_hint", "Стоимость × количество изделия-владельца", "Narx × ega mahsulot soni")

# «≈» belgisi endi ko'rsatilmaydi (onlayn tizimdagidek oddiy son) — baho ekanligi faqat maslahatda
a("cs.p.estimated_hint", "Предварительная оценка до раскроя (после раскроя — по результату)", "Kroygacha taxminiy baho (kroydan keyin — natija bo'yicha)")
