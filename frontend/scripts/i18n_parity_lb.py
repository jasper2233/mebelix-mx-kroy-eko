# Parity (W_PARITY_SPEC §5, §6): (LB) «Параметры» paneli va «Товары» (katalog importi) oynasi — yozuvlar xodimlar o'rgangan
# ko'rinishdagi so'zlar bilan. `a(...)` mavjud kalitni ham almashtiradi (fayl i18n_lb*.py / i18n_w3.py dan keyin yuklanadi).

# ── (LB) «Параметры» ──
a("lb.mode.sheet", "На формат А4", "A4 formatga")
a("lb.mode.roll", "На принтер этикеток", "Etiketka printeriga")
a("lb.count", "Количество", "Soni")
a("lb.size", "Размер", "O'lcham")
a("lb.size_hint", "Ширина × высота этикетки, мм", "Etiketka eni × balandligi, mm")
a("lb.layout_h", "Макет", "Maket")
a("lb.border", "Границы", "Chegaralar")
a("lb.border_none", "Нет границы", "Chegara yo'q")
a("lb.border_perimeter", "Границы по периметру", "Perimetr bo'yicha chegaralar")
a("lb.print_parts", "Печать деталей", "Detallarni chop etish")
a("lb.part_each", "Для каждой детали", "Har bir detal uchun")
a("lb.part_each_hint", "Отдельная этикетка на каждый экземпляр детали", "Detalning har bir nusxasiga alohida etiketka")
a("lb.part_nonzero", "Только если количество больше нуля", "Faqat soni noldan katta bo'lsa")
a("lb.selected", "Выбранные детали", "Tanlangan detallar")
a("lb.selected_ids", "ID деталей", "Detal ID lari")
a("lb.selected_hint", "ID деталей через запятую", "Detal ID lari vergul bilan")
a("lb.print_wastes", "Печать остатков", "Qoldiqlarni chop etish")
a("lb.waste_each", "Для каждого остатка", "Har bir qoldiq uchun")
a("lb.waste_each_hint", "Отдельная этикетка на каждый лист карты кроя", "Kroy kartasining har bir listiga alohida etiketka")
a("lb.product_each", "Для каждого изделия", "Har bir mahsulot uchun")
a("lb.extra_h", "Дополнительно", "Qo'shimcha")
a("lb.rotate", "Повернуть страницу на 90°", "Sahifani 90° burish")
a("lb.pages", "страниц: {{p}}", "sahifalar: {{p}}")

# ── «Товары» (katalog importi) ──
a("catalog.imp.title", "Товары", "Tovarlar")
a("catalog.imp.tab_file", "Файл", "Fayl")
a("catalog.imp.tab_cols", "Столбцы", "Ustunlar")
a("catalog.imp.show_cols", "Отображать колонки", "Ustunlarni ko'rsatish")
a("catalog.imp.show_cols_hint", "Отмеченные колонки показываются на вкладке «Столбцы» и импортируются; остальные пропускаются",
  "Belgilangan ustunlar «Ustunlar» varag'ida ko'rsatiladi va import qilinadi; qolganlari o'tkazib yuboriladi")
a("catalog.imp.root", "Корневая категория", "Ildiz kategoriya")
a("catalog.imp.root_hint", "Категория (тип материала), в которую попадают товары из файла",
  "Fayldagi tovarlar tushadigan kategoriya (material turi)")
a("catalog.imp.extra", "Дополнительно", "Qo'shimcha")
a("catalog.imp.root_ids", "ID корневых папок в файле", "Fayldagi ildiz papkalar ID si")
a("catalog.imp.col", "Колонка файла", "Fayl ustuni")
a("catalog.imp.field", "Поле", "Maydon")
a("catalog.imp.sample", "Пример", "Namuna")
a("catalog.imp.no_file", "Сначала выберите файл на вкладке «Файл»", "Avval «Fayl» varag'ida faylni tanlang")
for _k, _ru, _uz in [("parent_id", "Родительский ID", "Ota ID"), ("isfolder", "Папка", "Papka"),
                     ("unit", "Единица измерения", "O'lchov birligi"), ("size", "Размер", "O'lcham")]:
    a(f"catalog.f.{_k}", _ru, _uz)
