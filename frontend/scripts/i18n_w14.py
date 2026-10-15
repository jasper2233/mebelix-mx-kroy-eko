# -*- coding: utf-8 -*-
"""«Заказать» oqimi, loyiha ro'yxati ustunlari va «Общие действия» — interfeys matnlari (W14).
i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan)."""

# ── «Заказать» oynasi va chap panel ──
a("order.title_order", "Заказать", "Buyurtma berish")
a("order.title_state", "Состояние заказа", "Buyurtma holati")
a("order.manage", "Состояние заказа…", "Buyurtma holati…")
a("order.current", "Сейчас", "Hozir")
a("order.new_state", "Новое состояние", "Yangi holat")
a("order.action.1", "Заказать", "Buyurtma berish")
a("order.action.2", "Утвердить", "Tasdiqlash")
a("order.action.3", "Отметить готовым", "Tayyor deb belgilash")
a("order.kind.forward", "вперёд", "oldinga")
a("order.kind.skip", "вперёд, пропуская шаг", "oldinga, qadamni o'tkazib")
a("order.kind.back", "назад", "orqaga")
a("order.confirm", "Применить", "Qo'llash")
a("order.done", "Состояние: {{status}}", "Holat: {{status}}")
a("order.ready_date", "Дата готовности", "Tayyor bo'lish sanasi")
a("order.ready_required", "Укажите дату готовности — при утверждении она обязательна",
  "Tayyorlik sanasini ko'rsating — tasdiqlashda majburiy")
a("order.executor", "Исполнитель", "Ijrochi")
a("order.executor_ph", "Участок, отдел или ФИО", "Bo'lim, uchastka yoki F.I.Sh.")
a("order.comment", "Комментарий", "Izoh")
a("order.internal_hint", "Внутренняя заметка: сохраняется в истории проекта и никуда не отправляется. В MES уходит только смена состояния.",
  "Ichki yozuv: loyiha tarixida saqlanadi va hech qayerga yuborilmaydi. MES ga faqat holat o'zgarishi ketadi.")
a("order.warnings", "Обратите внимание (не блокирует):", "Diqqat (bloklamaydi):")
a("order.lock_on", "Редактирование заблокировано: заказ в состоянии «{{status}}»",
  "Tahrirlash bloklangan: buyurtma «{{status}}» holatida")
a("order.history", "История состояний", "Holatlar tarixi")
a("order.history_empty", "Записей пока нет", "Hozircha yozuv yo'q")
a("order.col.when", "Когда", "Qachon")
a("order.col.user", "Кто", "Kim")
a("order.col.change", "Переход", "O'tish")
a("order.col.note", "Исполнитель · комментарий", "Ijrochi · izoh")
a("order.edit_warn", "Правки после утверждения", "Tasdiqdan keyingi tahrir")
a("order.edit_warn_title", "Заказ в состоянии «{{status}}»: правки не блокируются, но могут не попасть в производство — то, что уже передано в цех, не изменится.",
  "Buyurtma «{{status}}» holatida: tahrirlash bloklanmaydi, lekin ishlab chiqarishga yetib bormasligi mumkin — sexga berilgan ma'lumot o'zgarmaydi.")
a("order.edit_locked", "Редактирование заблокировано", "Tahrirlash bloklangan")

# ── «Общие действия»: «Очистить проект» ──
a("common.clear", "Очистить проект", "Loyihani tozalash")
a("common.clear_hint", "Удалить результаты раскроя; детали и операции сохраняются (можно отменить)",
  "Kroy natijalarini o'chirish; detallar va operatsiyalar saqlanadi (bekor qilish mumkin)")
a("clear.q", "Очистить проект «{{name}}»?", "«{{name}}» loyihasini tozalaymi?")
a("clear.text", "Будут удалены результаты раскроя: операций — {{ops}}, карт — {{maps}}. Детали, операции и их параметры сохранятся. Действие можно отменить (Ctrl+Z).",
  "Kroy natijalari o'chiriladi: operatsiyalar — {{ops}} ta, kartalar — {{maps}} ta. Detallar, operatsiyalar va ularning parametrlari saqlanadi. Amalni bekor qilish mumkin (Ctrl+Z).")
a("clear.text_wh", "Остатки, записанные на склад из этого раскроя (операций: {{n}}), будут списаны со склада; при отмене на склад они не вернутся.",
  "Shu kroydan omborga yozilgan qoldiqlar (operatsiyalar: {{n}} ta) ombordan chiqariladi; bekor qilinsa ham omborga qaytmaydi.")
a("clear.text_order", "Заказ в состоянии «{{status}}»: результаты раскроя уже могли пойти в производство.",
  "Buyurtma «{{status}}» holatida: kroy natijalari ishlab chiqarishga berilgan bo'lishi mumkin.")
a("clear.ok", "Очистить", "Tozalash")
a("clear.nothing", "Результатов раскроя нет — очищать нечего", "Kroy natijalari yo'q — tozalanadigan narsa yo'q")
a("clear.done", "Очищено: операций — {{ops}}, карт — {{maps}}", "Tozalandi: operatsiyalar — {{ops}} ta, kartalar — {{maps}} ta")

# ── Loyihalar ro'yxati ──
a("projects.col.changed", "Изменено", "O'zgargan")
a("projects.filter.all", "Все состояния", "Barcha holatlar")
a("projects.filter.title", "Фильтр по состоянию", "Holat bo'yicha filtr")
