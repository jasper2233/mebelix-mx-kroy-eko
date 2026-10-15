# W18 / WP-C: «Импорт из других программ» (importx.*), Excel yangi tablari (xi18.*), katalog ildiz kategoriyalari.
# `a(kalit, ru, uz)` — i18n_src.py ichida aniqlangan; bu fayl uni yuklaydi (S_ISH_QOIDALARI.md).

# ───────────────────────── «Импорт из других программ» ─────────────────────────
a("importx.formats", "Форматы", "Formatlar")
a("importx.ready", "модуль есть", "modul bor")
a("importx.none", "нет модуля", "modul yo'q")
a("importx.no_module", "Нет модуля импорта — предоставьте образец файла", "Import moduli yo'q — namuna faylni bering")
a("importx.params", "Параметры импорта", "Import parametrlari")
a("importx.no_params", "У этого формата нет настраиваемых параметров.", "Bu formatda sozlanadigan parametrlar yo'q.")
a("importx.profile", "Профиль", "Profil")
a("importx.profile_none", "— стандартные —", "— standart —")
a("importx.profile_save", "Сохранить профиль", "Profilni saqlash")
a("importx.profile_new", "Сохранить как новый профиль", "Yangi profil sifatida saqlash")
a("importx.profile_name", "Название профиля", "Profil nomi")
a("importx.profile_delete_q", "Удалить профиль «{{name}}»?", "«{{name}}» profili o'chirilsinmi?")
a("importx.profile_replace_q", "Профиль «{{name}}» уже есть. Заменить его текущими параметрами?",
  "«{{name}}» profili bor. Uni joriy parametrlar bilan almashtirasizmi?")
a("importx.dirty", "есть несохранённые изменения", "saqlanmagan o'zgarishlar bor")
a("importx.reset_all", "Восстановить стандартные", "Standartni tiklash")
a("importx.help", "Справка", "Yordam")
a("importx.export", "Экспорт профилей этого формата", "Shu format profillarini eksport")
a("importx.export_json", "В файл JSON", "JSON faylga")
a("importx.export_xml", "В файл XML", "XML faylga")
a("importx.import_profiles", "Импорт профилей из файла (JSON / XML)", "Profillarni fayldan import (JSON / XML)")
a("importx.profiles_done", "Профили: создано {{c}}, заменено {{r}}, переименовано {{n}}, пропущено {{s}}",
  "Profillar: yaratildi {{c}}, almashtirildi {{r}}, qayta nomlandi {{n}}, o'tkazib yuborildi {{s}}")
a("importx.run", "Выбрать файл и импортировать", "Fayl tanlash va import qilish")
a("importx.run_hint", "Файлы: {{x}}. Результат — новый проект.", "Fayllar: {{x}}. Natija — yangi loyiha.")

# ───────────────────────── Excel: «Простые операции», «Материалы», (SP)/(GR)/(XNC) ustun guruhlari ─────────────────────────
a("import.tabs.simple", "Простые операции", "Oddiy operatsiyalar")
a("import.tabs.materials", "Материалы", "Materiallar")
# «Детали»: (SP) / (GR) / (XNC) ustun guruhlari va погонаж
for _k, _ru, _uz in (("sp_front", "(SP) Лицевая", "(SP) Old tomon"), ("sp_back", "(SP) Обратная", "(SP) Orqa tomon"),
                     ("gr_top", "(GR) Сверху", "(GR) Yuqori"), ("gr_bottom", "(GR) Снизу", "(GR) Past"),
                     ("gr_left", "(GR) Слева", "(GR) Chap"), ("gr_right", "(GR) Справа", "(GR) O'ng"),
                     ("xnc1", "(XNC) Обработка 1", "(XNC) Ishlov 1"), ("xnc2", "(XNC) Обработка 2", "(XNC) Ishlov 2")):
    a(f"import.f.{_k}", _ru, _uz)
a("xi18.group_extra", "Доп. операции: (SP) Обработка поверхности · (GR) Пазование · (XNC) Обработка",
  "Qo'shimcha operatsiyalar: (SP) Sirt ishlovi · (GR) Pazlash · (XNC) Ishlov")
a("xi18.extra_hint", "SP и GR — название или код операции (если такой нет — создаётся); XNC — код шаблона (название шаблона, lib:…); «-» — без операции. Шаблон не найден — предупреждение.",
  "SP va GR — operatsiya nomi yoki kodi (yo'q bo'lsa yaratiladi); XNC — shablon kodi (shablon nomi, lib:…); «-» — operatsiyasiz. Shablon topilmasa — ogohlantirish.")
a("xi18.linear", "Погонаж: строки без ширины → CL", "Pogonaj: eni yo'q qatorlar → CL")
a("xi18.linear_hint", "Если «Ширина» пуста, строка — погонажная деталь и попадает в операцию CL (по столбцу «Материал»)",
  "«Ширина» bo'sh bo'lsa, qator — pogonaj detal va CL operatsiyasiga tushadi («Материал» ustuni bo'yicha)")
a("xi18.target_cl", "Операция CL", "CL operatsiyasi")
# «Простые операции» (O)
a("xi18.simple_op", "Операция (O) Комплектация", "(O) Komplektatsiya operatsiyasi")
a("xi18.simple_op_name", "Название", "Nomi")
a("xi18.simple_target", "Добавить в", "Qo'shish")
a("xi18.simple_new", "— новая операция —", "— yangi operatsiya —")
a("xi18.simple_hint", "Если есть столбец «Операция» — для каждого значения создаётся своя операция; иначе одна (название выше).",
  "«Операция» ustuni bo'lsa — har qiymat uchun alohida operatsiya yaratiladi; bo'lmasa bitta (yuqoridagi nom).")
a("xi18.simple_cols_hint", "Код или наименование обязательно. Кол — по умолчанию 1, Цена — 0; «Изделие» — владелец операции.",
  "Kod yoki nom shart. Кол — standart 1, Цена — 0; «Изделие» — operatsiya egasi.")
for _k, _ru, _uz in (("code", "Код", "Kod"), ("name", "Наименование", "Nomi"), ("unit", "Ед.И", "Birlik"), ("qty", "Кол", "Soni"),
                     ("price", "Цена", "Narx"), ("operation", "Операция", "Operatsiya"), ("product", "Изделие", "Mahsulot")):
    a(f"import.sf.{_k}", _ru, _uz)
# «Материалы»
a("xi18.mat_create_missing", "Создавать материалы, которых нет в каталоге", "Katalogda yo'q materiallarni yaratish")
a("xi18.mat_default_kind", "Тип по умолчанию", "Standart tur")
a("xi18.mat_hint", "Материал ищется в каталоге по коду, затем по наименованию; тип операции (лист / кромка / поверхность / погонаж) — из каталога.",
  "Material katalogdan avval kod, so'ng nom bo'yicha qidiriladi; operatsiya turi (varaq / kromka / sirt / pogonaj) — katalogdan.")
a("xi18.mat_cols_hint", "Код или наименование обязательно. Остальные столбцы используются только для материалов, которых нет в каталоге.",
  "Kod yoki nom shart. Qolgan ustunlar faqat katalogda yo'q materiallar uchun ishlatiladi.")
for _k, _ru, _uz in (("code", "Код", "Kod"), ("name", "Наименование", "Nomi"), ("kind", "Тип", "Tur"), ("thickness", "Толщина", "Qalinlik"),
                     ("length", "Длина", "Uzunlik"), ("width", "Ширина", "En"), ("price", "Цена", "Narx")):
    a(f"import.mf.{_k}", _ru, _uz)
# hisobot
a("xi18.rep_simple", "строк комплектации: {{n}} (операций: {{m}})", "komplektatsiya qatorlari: {{n}} (operatsiyalar: {{m}})")
a("xi18.rep_materials", "материалов создано: {{n}}, уже были: {{m}}", "materiallar yaratildi: {{n}}, avvaldan bor: {{m}}")
a("xi18.rep_linear", "погонаж → CL: {{n}}", "pogonaj → CL: {{n}}")
a("xi18.rep_linked", "привязано: SP {{s}}, GR {{g}}, XNC {{x}}", "bog'landi: SP {{s}}, GR {{g}}, XNC {{x}}")
