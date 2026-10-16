# -*- coding: utf-8 -*-
"""2026-10-16 — QA tuzatishlari (umumiy UI, X_1015 §14): «Листы и остатки» xabarlari, «Сортировка» izohi,
sarlavha sanalari ogohlantirishi. `a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi."""

# «Листы и остатки» (#21): yagona qator o'chirilmaydi; «Удалить неиспользуемый материал» — o'chiradigan narsa yo'q
a("sheets.last_row", "Единственную строку листов удалить нельзя — измените её или добавьте другую",
  "Yagona list qatorini o'chirib bo'lmaydi — uni o'zgartiring yoki boshqasini qo'shing")
a("sheets.nothing_unused", "Все строки листов использованы в раскрое — удалять нечего",
  "Barcha list qatorlari kroyda ishlatilgan — o'chiriladigan narsa yo'q")

# «Сортировка» oynasi (#21): izoh matni (maslahat o'rniga)
a("sort.note", "Отметьте столбцы (Вкл); порядок строк сверху вниз — приоритет сортировки, ↑↓ меняют его",
  "Ustunlarni belgilang (Yoq.); qatorlar tartibi yuqoridan pastga — saralash ustuvorligi, ↑↓ uni o'zgartiradi")

# Loyiha sarlavhasi (#17): «Дата готовности» «Дата заказа» dan oldin bo'lmaydi
a("header.ready_before_order", "Дата готовности не может быть раньше даты заказа — установлена дата заказа",
  "Tayyor bo'lish sanasi buyurtma sanasidan oldin bo'lishi mumkin emas — buyurtma sanasi qo'yildi")
