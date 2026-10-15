# -*- coding: utf-8 -*-
"""Postprotsessor stanoklari: sozlamalar sxemasi (ParamGrid) va «Данные для этикеток» jadvali — interfeys matnlari (W7).
i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan). Parametr yorliqlarining o'zi (ru/uz) serverdan keladi (`pp_machine_schema.py`)."""

# ── ParamGrid ──
a("ppm.params.title", "Параметры станка", "Stanok parametrlari")
a("ppm.reset_all", "Сбросить всё к стандарту", "Hammasini standartga qaytarish")
a("ppm.reset_one", "Вернуть стандарт", "Standartga qaytarish")
a("ppm.default_is", "По умолчанию: {{v}}", "Standart: {{v}}")
a("ppm.modified", "Изменено относительно стандарта", "Standartdan farq qiladi")
a("ppm.dirty", "Есть несохранённые изменения", "Saqlanmagan o'zgarishlar bor")
a("ppm.other", "Другое…", "Boshqa…")
a("ppm.no_params", "У этого станка пока нет параметров", "Bu stanokda hozircha parametrlar yo'q")
a("ppm.path_hint", "Путь хранится как строка; сервер к файловой системе не обращается",
  "Yo'l satr sifatida saqlanadi; server fayl tizimiga murojaat qilmaydi")
a("ppm.save_blocked", "Исправьте ошибки в выражениях или названиях полей", "Ifodalar yoki maydon nomlaridagi xatolarni tuzating")

# ── «Данные для этикеток» ──
a("ppm.col.n", "№", "№")
a("ppm.col.name", "Наименование", "Nomi")
a("ppm.col.expr", "Выражение", "Ifoda")
a("ppm.col.value", "Значение на детали", "Detaldagi qiymat")
a("ppm.add_row", "Добавить поле", "Maydon qo'shish")
a("ppm.del_row", "Удалить поле", "Maydonni o'chirish")
a("ppm.reset_table", "Вернуть стандартную таблицу", "Standart jadvalni qaytarish")
a("ppm.reset_table_q", "Вернуть стандартные поля и выражения этого станка? Ваши изменения в таблице будут потеряны.",
  "Bu stanokning standart maydon va ifodalari qaytarilsinmi? Jadvaldagi o'zgarishlaringiz yo'qoladi.")
a("ppm.reset_row", "Вернуть стандартное выражение этого поля", "Bu maydonning standart ifodasini qaytarish")
a("ppm.preview_for", "Показать на детали:", "Detalda ko'rish:")
a("ppm.project_search", "Поиск проекта", "Loyiha qidirish")
a("ppm.sample","Образец (без проекта)", "Namuna (loyihasiz)")
a("ppm.sample_note", "Образец: деталь «Боковая панель» с кромкой", "Namuna: kromkali «Yon panel» detali")
a("ppm.no_cs", "Нет раскроя с деталями", "Detalli kroy yo'q")
a("ppm.empty_expr", "пусто → «»", "bo'sh → «»")
a("ppm.table_empty", "Нет полей. Нажмите «+», чтобы добавить", "Maydonlar yo'q. Qo'shish uchun «+» ni bosing")
a("ppm.fx_title", "Помощник по выражениям", "Ifoda yordamchisi")

# ── shablonga nima beriladi ──
a("ppm.ctx_title", "Что станок передаёт в шаблон формата", "Stanok format shabloniga nimalarni beradi")
a("ppm.ctx_doc",
  """machine — {key, name, group, params: {параметр: значение}, label_fields: [{name, expr}]}; если станок не выбран — None
maps[].placements[].label — {поле: значение}: «Данные для этикеток», вычислено для этой детали (тип значения сохраняется)
maps[].placements[].label_text — {поле: текст}
parts[].label, parts[].label_text — то же для списка деталей
label_warnings — [{field, expr, message, error, count, part_uid}]: ошибки выражений. Значение такого поля — «#ERR», не 0
Формат файла станка здесь не задаётся — его описывает ваш шаблон (Jinja).""",
  """machine — {key, name, group, params: {parametr: qiymat}, label_fields: [{name, expr}]}; stanok tanlanmagan bo'lsa — None
maps[].placements[].label — {maydon: qiymat}: «Данные для этикеток», shu detal uchun hisoblangan (qiymat turi saqlanadi)
maps[].placements[].label_text — {maydon: matn}
parts[].label, parts[].label_text — detallar ro'yxati uchun ham shunday
label_warnings — [{field, expr, message, error, count, part_uid}]: ifoda xatolari. Bunday maydon qiymati — «#ERR», 0 emas
Stanok fayl formati bu yerda berilmaydi — uni sizning shabloningiz (Jinja) tasvirlaydi.""")
a("ppm.ctx_machine", "Станок для контекста", "Kontekst uchun stanok")
a("ppm.ctx_machine_none", "— без станка —", "— stanoksiz —")
