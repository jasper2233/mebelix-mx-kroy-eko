# -*- coding: utf-8 -*-
"""W3: Excel import v2 va «Товары» (katalog daraxti) yorliqlari. `i18n_src.py` shu faylni o'zi yuklaydi."""

# ── Excel import v2 ──
a("import.excel_hint",
  "Выберите файл Excel (.xlsx, .xls) или CSV. Затем укажите, в каком столбце какое поле: вкладка «Детали» — детали, группировка по изделиям и материалам; вкладка «Изделия» — список изделий.",
  "Excel (.xlsx, .xls) yoki CSV faylni tanlang, so'ng ustunlarni belgilang: «Детали» tabi — detallar, mahsulot va material bo'yicha guruhlash; «Изделия» tabi — mahsulotlar ro'yxati.")
a("import.tabs.parts", "Детали", "Detallar")
a("import.tabs.products", "Изделия", "Mahsulotlar")
a("import.tab_enabled", "Импортировать эту вкладку", "Shu tabni import qilish")
a("import.general", "Общие", "Umumiy")
a("import.sheet", "Лист", "Varaq")
a("import.end_row", "Конечная строка", "Oxirgi qator")
a("import.end_row_hint", "0 — до конца", "0 — oxirigacha")
a("import.grouping", "Группировка", "Guruhlash")
a("import.grouping_hint",
  "По изделиям: значение столбца — изделие (находится или создаётся). По материалам: значение столбца — материал, для каждого находится или создаётся операция CS. Без столбца материала детали идут в выбранную операцию.",
  "Mahsulot bo'yicha: ustun qiymati — mahsulot (topiladi yoki yaratiladi). Material bo'yicha: ustun qiymati — material, har biri uchun CS operatsiyasi topiladi yoki yaratiladi. Material ustunisiz detallar tanlangan operatsiyaga tushadi.")
a("import.grouping_short", "Столбец значений: изделие / материал (см. подсказку)", "Qiymatlar ustuni: mahsulot / material (qarang: izoh)")
a("import.data", "Данные", "Ma'lumot")
a("import.by_size", "По размеру", "O'lcham bo'yicha")
a("import.size_mode.project", "как в проекте", "loyihadagidek")
a("import.size_mode.blank", "заготовки", "zagotovkalar")
a("import.size_mode.detail", "детали", "detallar")
a("import.size_mode.jointed", "заготовки после прифуговки", "prifugovkadan keyingi zagotovkalar")
a("import.skip_zero", "Не добавлять деталь, если количество равно нулю", "Soni nolga teng detalni qo'shmaslik")
a("import.target_auto", "— авто (по материалу) —", "— avto (material bo'yicha) —")
a("import.columns", "Столбцы", "Ustunlar")
a("import.required_hint", "* — обязательные. Если «Длина», «Ширина» или «Кол-во» пусто или не число — строка пропускается и показывается в отчёте.",
  "* — majburiy. «Длина», «Ширина» yoki «Кол-во» bo'sh yoki son bo'lmasa — qator o'tkazib yuboriladi va hisobotda ko'rsatiladi.")
for k, ru, uz in [("material", "Материал", "Material"), ("product", "Изделие", "Mahsulot"), ("description", "Описание", "Tavsif"),
                  ("number_in_name", "Номер в наименование", "Nomga raqam")]:
    a(f"import.f.{k}", ru, uz)
for k, ru, uz in [("code", "Код", "Kod"), ("name", "Наименование", "Nomi"), ("qty", "Количество", "Soni"), ("description", "Описание", "Tavsif"),
                  ("phone1", "Телефон 1", "Telefon 1"), ("phone2", "Телефон 2", "Telefon 2"), ("date", "Дата", "Sana")]:
    a(f"import.pf.{k}", ru, uz)
a("import.link", "Связь с деталями", "Detallar bilan bog'lash")
a("import.link_qty", "Сопоставление с изделиями проекта", "Loyiha mahsulotlari bilan moslash")
a("import.link_code", "По коду", "Kod bo'yicha")
a("import.link_name", "По наименованию", "Nom bo'yicha")
a("import.skip_zero_prod", "Не добавлять изделие, если количество равно нулю", "Soni nolga teng mahsulotni qo'shmaslik")
a("import.add_empty", "Добавлять пустые изделия (без деталей)", "Bo'sh mahsulotlarni ham qo'shish (detalsiz)")
a("import.qty_only", "Только количество изделий", "Faqat mahsulotlar soni")
a("import.qty_only_hint",
  "В существующем проекте обновляется только количество изделий (по коду или наименованию); ничего нового не добавляется.",
  "Mavjud loyihada faqat mahsulotlar soni yangilanadi (kod yoki nom bo'yicha); yangi hech narsa qo'shilmaydi.")
a("import.check", "Проверить", "Tekshirish")
a("import.check_hint", "Показать результат без изменения проекта", "Loyihani o'zgartirmasdan natijani ko'rsatish")
a("import.check_result", "Результат проверки", "Tekshiruv natijasi")
a("import.rep_qty", "будет обновлено изделий: {{n}}", "yangilanadigan mahsulotlar: {{n}}")
a("import.rep_full", "деталей: {{n}}, новых операций CS: {{m}}, новых изделий: {{p}}, новых кромок: {{e}}",
  "detallar: {{n}}, yangi CS operatsiyalari: {{m}}, yangi mahsulotlar: {{p}}, yangi kromkalar: {{e}}")
a("import.rep_zero", "с нулевым количеством пропущено: {{n}}", "soni 0 bo'lgani o'tkazib yuborildi: {{n}}")
a("import.rep_more", "ещё {{n}}", "yana {{n}} ta")
a("import.done_ext", "Импортировано деталей: {{n}} · новых операций CS: {{m}} · новых изделий: {{p}}",
  "Import qilingan detallar: {{n}} · yangi CS operatsiyalari: {{m}} · yangi mahsulotlar: {{p}}")
a("import.done_qty", "Обновлено изделий: {{n}}", "Yangilangan mahsulotlar: {{n}}")

# ── «Товары» ──
a("catalog.categories", "Категории", "Kategoriyalar")
a("catalog.all_materials", "Все материалы", "Barcha materiallar")
a("catalog.unfiled", "Без категории", "Kategoriyasiz")
a("catalog.image", "Изображение", "Rasm")
a("catalog.no_image", "Нет изображения", "Rasm yo'q")
a("catalog.image_upload", "Загрузить изображение", "Rasm yuklash")
a("catalog.image_remove", "Убрать изображение", "Rasmni olib tashlash")
a("catalog.image_bad", "Нужен PNG, JPEG, GIF или WebP до {{n}} КБ", "PNG, JPEG, GIF yoki WebP kerak, {{n}} KB gacha")
a("catalog.th", "Т-на", "Qalinl.")
a("catalog.len", "Д-на", "Uzunl.")
a("catalog.wid", "Ш-на", "En")
a("catalog.delete_folder", "Удалить папку со всем содержимым", "Papkani ichidagilari bilan o'chirish")
a("catalog.delete_folder_q", "Удалить папку и всё её содержимое из каталога?", "Papka va uning ichidagi hamma narsa katalogdan o'chirilsinmi?")
a("catalog.limit_hint", "Показаны первые {{n}} позиций — уточните папку или поиск.", "Dastlabki {{n}} ta pozitsiya ko'rsatildi — papka yoki qidiruvni aniqlashtiring.")
a("catalog.import_done", "Импортировано: {{n}} (папок: {{f}}, материалов: {{m}}, изображений: {{i}})",
  "Import qilindi: {{n}} (papkalar: {{f}}, materiallar: {{m}}, rasmlar: {{i}})")
a("catalog.id_prefix", "Префикс ID", "ID prefiksi")
a("catalog.roots", "Корневая категория", "Ildiz kategoriya")
a("catalog.roots_hint", "ID корневой папки для каждого типа материала (пусто — тип по умолчанию)", "Har bir material turi uchun ildiz papka ID si (bo'sh — standart tur)")
for k, ru, uz in [("sheet", "Листовой материал", "List material"), ("linear", "Погонажный материал", "Pogonaj material"),
                  ("edge", "Материал кромок", "Kromka materiali"), ("surface", "Материал поверхностей", "Sirt materiali")]:
    a(f"catalog.roots_{k}", ru, uz)
a("catalog.import_hint",
  "Выберите файл каталога (.xlsx, .xls, .csv): столбцы ID, родительский ID, папка (1/0), код, наименование, ед.изм., цена, склад, изображение, параметры, толщина, длина, ширина.",
  "Katalog faylini tanlang (.xlsx, .xls, .csv): ID, ota ID, papka (1/0), kod, nom, birlik, narx, ombor, rasm, parametrlar, qalinlik, uzunlik, en ustunlari.")
for k, ru, uz in [("isfolder", "Папка (1/0)", "Papka (1/0)"), ("image", "Изображение", "Rasm"), ("params", "Параметры", "Parametrlar")]:
    a(f"catalog.f.{k}", ru, uz)
