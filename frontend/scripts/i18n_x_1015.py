# -*- coding: utf-8 -*-
"""2026-10-15 — onlayn tizim bilan solishtiruv va audit tuzatishlari: «Порядок листов» (CS), «Раскроить все операции»,
CS o'chirishda XNC ogohlantirishi. `a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi."""

# CS «Параметры» → «Предпочтения»: listlar ro'yxati tartibi (ombor qoldiqlari va soni cheklangan listlar avval — xodimlar
# o'rgangan tizim xulqi) yoki material tejash (bir nechta tartib sinaladi, eng kam maydon tanlanadi — bizning kengaytma)
a("cs.p.stock_order", "Порядок листов", "Listlar tartibi")
a("cs.stock_order.list", "Строго по списку (остатки — сначала)", "Qat'iy ro'yxat bo'yicha (qoldiqlar — avval)")
a("cs.stock_order.economy", "Экономия материала (подбор порядка)", "Material tejash (tartib tanlanadi)")
a("cs.p.stock_order_hint", "По списку — листы и остатки используются строго в порядке списка «Листы и остатки» (остатки со склада и листы с ограниченным количеством — сначала, если на них помещаются детали). Экономия материала — программа пробует несколько порядков и берёт вариант с наименьшей площадью материала.",
  "Ro'yxat bo'yicha — listlar «Листы и остатки» ro'yxati tartibida qat'iy ishlatiladi (ombordagi qoldiqlar va soni cheklangan listlar — detal sig'sa, avval). Material tejash — dastur bir nechta tartibni sinab, material maydoni eng kam variantni oladi.")
a("phelp.stock_order", "Порядок использования листов из вкладки «Листы и остатки». «По списку» — как в привычной системе: остатки и листы с ограниченным количеством расходуются первыми, если на них помещается хотя бы одна деталь, затем — листы без ограничения. «Экономия материала» — программа сравнивает несколько порядков и выбирает тот, где суммарная площадь использованных листов меньше (может пропустить мелкий остаток ради целого листа).",
  "«Листы и остатки» varag'idagi listlardan foydalanish tartibi. «Ro'yxat bo'yicha» — odatiy tizimdagidek: qoldiqlar va soni cheklangan listlar, agar ularga kamida bitta detal sig'sa, birinchi ishlatiladi, keyin cheksiz listlar. «Material tejash» — dastur bir nechta tartibni solishtirib, ishlatilgan listlar maydoni eng kam bo'lganini tanlaydi (butun list evaziga mayda qoldiqni tashlab ketishi mumkin).")

# «Общие действия» → «Раскроить все операции» (bizning qo'shimcha; onlayn tizimda yo'q)
a("common.cut_all", "Раскроить все операции", "Barcha operatsiyalarni kroy qilish")
a("common.cut_all_hint", "Все операции раскроя (листовой, погонажный, нестинг) по очереди; одно действие для Ctrl+Z. Операции без деталей или листов пропускаются с сообщением.",
  "Barcha kroy operatsiyalari (listli, pogonaj, nesting) ketma-ket; Ctrl+Z uchun bitta amal. Detali yoki listi yo'q operatsiyalar xabar bilan o'tkazib yuboriladi.")
a("common.cut_all_done", "Раскроено операций: {{n}}, с ошибкой: {{e}}", "Kroy qilingan operatsiyalar: {{n}}, xato bilan: {{e}}")

# «Очередь заказов» va material bazasi tekshiruvi (foydalanuvchi talabi, 2026-10-15)
a("queue.title", "Очередь заказов и материал в базе", "Buyurtmalar navbati va bazadagi material")
a("queue.set.open", "Не готовые (все)", "Tayyor bo'lmaganlar (hammasi)")
a("queue.set.ordered", "Заказанные и утвержденные", "Buyurtma qilingan va tasdiqlanganlar")
a("queue.set.draft", "Не заказанные", "Buyurtma qilinmaganlar")
a("queue.set.all", "Все проекты", "Barcha loyihalar")
a("queue.col.material", "Материал (нужно / в базе)", "Material (kerak / bazada)")
a("queue.col.result", "Итог", "Xulosa")
a("queue.need", "нужно", "kerak"); a("queue.have", "в базе", "bazada"); a("queue.remnants", "остатков на складе", "ombordagi qoldiq")
a("queue.ok", "Материал есть полностью", "Material to'liq bor")
a("queue.short", "Не хватает ({{n}}): {{list}}", "Yetmaydi ({{n}}): {{list}}")
a("queue.unknown", "Нет в каталоге: {{n}} — остаток неизвестен", "Katalogda yo'q: {{n}} — qoldiq noma'lum")
a("queue.no_cut_ops", "Нет операций раскроя с деталями", "Detalli kroy operatsiyalari yo'q")
a("queue.is_next", "следующий", "navbatdagi")
a("queue.open_next", "Открыть следующий (№{{n}})", "Navbatdagini ochish (№{{n}})")
a("queue.fill_base", "Пополните базу материалов:", "Material bazasini to'ldiring:")

# Operatsiyani o'chirish: CS/CL/CN bilan birga detallariga bog'langan XNC dasturlari ham o'chadi
a("ops.delete_xnc_q", "Удалить операцию «{{name}}»? Вместе с ней будут удалены {{n}} программ ЧПУ (XNC), привязанных к её деталям.",
  "«{{name}}» operatsiyasi o'chirilsinmi? U bilan birga detallariga bog'langan {{n}} ta CNC (XNC) dasturi ham o'chadi.")
