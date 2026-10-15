# -*- coding: utf-8 -*-
"""OEE va ishlab chiqarish analitikasi (W17) — interfeys matnlari. i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan)."""

# ── umumiy / kirish nuqtalari ──
a("app.edit", "Изменить", "Tahrirlash")
a("mes.page.oee", "OEE", "OEE")
a("settings.page.production", "Производство (OEE)", "Ishlab chiqarish (OEE)")
a("oee.title", "OEE — эффективность оборудования", "OEE — uskunalar samaradorligi")
a("oee.subtitle", "Готовность × производительность × качество", "Tayyorlik × unumdorlik × sifat")
a("oee.tab.overview", "Обзор", "Umumiy ko'rinish")
a("oee.tab.events", "События", "Hodisalar")
a("oee.tab.machines", "Станки", "Stanoklar")
a("oee.tab.shifts", "Смены", "Smenalar")
a("oee.tab.reasons", "Причины", "Sabablar")
a("oee.tab.params", "Параметры", "Parametrlar")

# ── фильтры ──
a("oee.period_label", "Период", "Davr")
for k, ru, uz in [("today", "Сегодня", "Bugun"), ("yesterday", "Вчера", "Kecha"), ("last7", "7 дней", "7 kun"), ("last14", "14 дней", "14 kun"),
                  ("last30", "30 дней", "30 kun"), ("this_week", "Неделя", "Hafta"), ("this_month", "Месяц", "Oy"), ("custom", "Период…", "Davr…")]:
    a(f"oee.period.{k}", ru, uz)
for k, ru, uz in [("hour", "По часам", "Soat bo'yicha"), ("shift", "По сменам", "Smena bo'yicha"), ("day", "По дням", "Kun bo'yicha"),
                  ("week", "По неделям", "Hafta bo'yicha")]:
    a(f"oee.group.{k}", ru, uz)
a("oee.all_machines", "Все станки", "Hamma stanoklar")
a("oee.all_types", "Все типы", "Hamma turlar")
a("oee.refresh", "Обновить", "Yangilash")
a("oee.csv", "CSV", "CSV")
a("oee.load_error", "Не удалось загрузить данные OEE", "OEE ma'lumotlarini yuklab bo'lmadi")

# ── пустое состояние и демо ──
a("oee.empty_title", "Нет станков для учёта OEE", "OEE hisobi uchun stanoklar yo'q")
a("oee.empty_text",
  "Добавьте станок (например, пильный центр) и его идеальные скорости. События приходят из MES (POST /api/oee/events), из цеха (кнопки «Раскроено» и «Остановка» в режиме цеха) или вводятся вручную.",
  "Stanok (masalan, arra markazi) va uning ideal tezliklarini qo'shing. Hodisalar MES dan (POST /api/oee/events), sexdan (sex rejimidagi «Kesildi» va «To'xtash» tugmalari) keladi yoki qo'lda kiritiladi.")
a("oee.add_machine", "Добавить станок", "Stanok qo'shish")
a("oee.demo_title", "Демо-данные", "Demo-ma'lumot")
a("oee.demo_hint", "Только для показа и проверки (MEBELIX_DEMO=1, роль администратора): 2 синтетических станка на 14 дней. Реальные события не затрагиваются.",
  "Faqat ko'rsatish va tekshirish uchun (MEBELIX_DEMO=1, administrator roli): 14 kunlik 2 ta sintetik stanok. Haqiqiy hodisalarga tegilmaydi.")
a("oee.demo_seed", "Создать демо-данные (14 дней)", "Demo-ma'lumot yaratish (14 kun)")
a("oee.demo_clear", "Удалить демо-данные", "Demo-ma'lumotni o'chirish")
a("oee.demo_done", "Создано демо-событий: {{n}}", "Demo-hodisalar yaratildi: {{n}}")
a("oee.demo_cleared", "Демо-данные удалены", "Demo-ma'lumot o'chirildi")
a("oee.no_events", "Нет событий за период", "Davr uchun hodisalar yo'q")
a("oee.no_points", "Нет данных для графика", "Grafik uchun ma'lumot yo'q")
a("oee.no_data_point", "Нет смен или данных", "Smena yoki ma'lumot yo'q")
a("oee.no_downtime", "Остановок за период нет", "Davr ichida to'xtashlar yo'q")
a("oee.no_shifts", "Нет смен за период (проверьте календарь смен)", "Davr uchun smenalar yo'q (smena kalendarini tekshiring)")

# ── показатели ──
a("oee.kpi.oee", "OEE", "OEE")
a("oee.kpi.oee_hint", "OEE = A × P × Q", "OEE = A × P × Q")
a("oee.kpi.a", "Готовность (A)", "Tayyorlik (A)")
a("oee.kpi.a_hint", "Время работы / плановое время", "Ish vaqti / rejalashtirilgan vaqt")
a("oee.kpi.a_sub", "Работа {{run}} / план {{plan}}", "Ish {{run}} / reja {{plan}}")
a("oee.kpi.a_stop", "Простои {{stop}} (без причины {{idle}})", "To'xtashlar {{stop}} (sababsiz {{idle}})")
a("oee.kpi.p", "Производительность (P)", "Unumdorlik (P)")
a("oee.kpi.p_hint", "Идеальное время / время работы (не более 100 %)", "Ideal vaqt / ish vaqti (100 % dan oshmaydi)")
a("oee.kpi.p_sub", "Цикл {{avg}} с при идеале {{ideal}} с ({{unit}})", "Sikl {{avg}} s, ideal {{ideal}} s ({{unit}})")
a("oee.kpi.p_capped", "Ограничено 100 % (расчёт {{raw}})", "100 % bilan cheklangan (hisob {{raw}})")
a("oee.kpi.q", "Качество (Q)", "Sifat (Q)")
a("oee.kpi.q_hint", "Годные / всего произведено", "Yaroqli / jami ishlab chiqarilgan")
a("oee.kpi.q_sub", "Годных {{good}} из {{total}} {{unit}}; доля брака {{bad}}", "Yaroqli {{good}} / {{total}} {{unit}}; brak ulushi {{bad}}")
a("oee.mat.title", "Материал (в OEE не входит)", "Material (OEE ga kirmaydi)")
a("oee.mat.fill", "Заполнение листа (F)", "List to'ldirilishi (F)")
a("oee.mat.waste", "Отход без деловых остатков", "Delovoy qoldiqsiz otxod")
a("oee.mat.sub", "{{sheets}} лист. · {{m2}} м² · деловые остатки {{rem}} м²", "{{sheets}} list · {{m2}} m² · delovoy qoldiq {{rem}} m²")
a("oee.mat.hint", "Заполнение = площадь деталей / площадь листов; отход = (листы − детали − деловые остатки) / листы. Считается по картам кроя с данными о площадях",
  "To'ldirilish = detallar maydoni / list maydoni; otxod = (list − detal − delovoy qoldiq) / list. Maydon ma'lumoti bor kroy kartalari bo'yicha")
a("oee.band.low", "Низкий", "Past")
a("oee.band.mid", "Средний", "O'rtacha")
a("oee.band.high", "Высокий", "Yuqori")
a("oee.band.none", "нет данных", "ma'lumot yo'q")
a("oee.line.oee", "OEE", "OEE")
a("oee.line.availability", "Готовность (A)", "Tayyorlik (A)")
a("oee.line.performance", "Производительность (P)", "Unumdorlik (P)")
a("oee.line.quality", "Качество (Q)", "Sifat (Q)")
a("oee.unit_short.sheet", "лист.", "list")
a("oee.unit_short.part", "дет.", "detal")

# ── единицы ──
a("oee.u.h", "ч", "soat")
a("oee.u.min", "мин", "daq")
a("oee.u.min_n", "{{n}} мин", "{{n}} daq")
a("oee.u.s", "с", "s")
a("oee.u.mm_s", "мм/с", "mm/s")
a("oee.u.m_min", "м/мин", "m/daq")

# ── предупреждения ──
a("oee.warn.no_calendar", "Календарь смен не настроен: плановое время = 0, показатели не рассчитываются (вкладка «Смены»)",
  "Smena kalendari sozlanmagan: rejalashtirilgan vaqt = 0, ko'rsatkichlar hisoblanmaydi («Smenalar» bo'limi)")
a("oee.warn.no_ideal", "Для {{count}} событий неизвестен идеальный цикл (нет данных о резах или скоростях станка): P их не учитывает",
  "{{count}} ta hodisa uchun ideal sikl noma'lum (kesim ma'lumoti yoki stanok tezligi yo'q): P ularni hisobga olmaydi")
a("oee.warn.p_capped", "P ограничена 100 %: фактический цикл быстрее идеального — проверьте идеальные скорости станка",
  "P 100 % bilan cheklangan: haqiqiy sikl idealdan tez — stanokning ideal tezliklarini tekshiring")
a("oee.warn.unit_fallback", "Единицу брака не удалось пересчитать ({{count}}): неизвестно число деталей на лист — взято 1:1",
  "Brak birligini o'tkazib bo'lmadi ({{count}}): listdagi detal soni noma'lum — 1:1 olindi")
a("oee.warn.outside_shift", "Вне смен выпущено {{count}} лист. — в OEE не учтено (параметр «работа вне смены»)",
  "Smenadan tashqari {{count}} list ishlab chiqarilgan — OEE ga kirmadi («smenadan tashqari ish» parametri)")
a("oee.warn.no_data", "Нет событий по станкам: {{machines}} (в сводку не входят)", "Stanoklar bo'yicha hodisa yo'q: {{machines}} (yig'indiga kirmaydi)")
a("oee.warn.open_downtime", "Открытых остановок: {{count}} — считаются до возобновления работы или до текущего момента",
  "Ochiq to'xtashlar: {{count}} — ish qayta boshlangunicha yoki hozirgacha hisoblanadi")

# ── график, Парето, таблицы ──
a("oee.trend", "Динамика", "Dinamika")
a("oee.table_view", "Таблица", "Jadval")
a("oee.pareto", "Причины простоев (Парето)", "To'xtash sabablari (Pareto)")
a("oee.pareto_total", "Всего: {{v}}", "Jami: {{v}}")
a("oee.cumulative", "Накопленная доля", "Kumulyativ ulush")
a("oee.idle_name", "Простой без записи (причина не указана)", "Yozuvsiz bo'shliq (sabab ko'rsatilmagan)")
a("oee.tip.minutes", "Минуты", "Daqiqa")
a("oee.tip.count", "Случаев", "Holatlar")
a("oee.tip.share", "Доля", "Ulush")
a("oee.planned_note", "Плановые остановки (в OEE не входят)", "Rejalashtirilgan to'xtashlar (OEE ga kirmaydi)")
a("oee.by_machine", "По станкам", "Stanoklar bo'yicha")
a("oee.shift_table", "Смены", "Smenalar")
for k, ru, uz in [("period", "Период", "Davr"), ("date", "Дата", "Sana"), ("shift", "Смена", "Smena"), ("planned", "План", "Reja"), ("run", "Работа", "Ish"),
                  ("stop", "Простой", "To'xtash"), ("produced", "Выпущено", "Ishlab chiqarildi"), ("rejected", "Брак, %", "Brak, %"),
                  ("machine", "Станок", "Stanok"), ("time", "Время", "Vaqt"), ("details", "Подробности", "Tafsilot"), ("source", "Источник", "Manba")]:
    a(f"oee.col.{k}", ru, uz)

# ── события ──
a("oee.type.run", "Резка (лист/карта)", "Kesish (list/karta)")
a("oee.type.downtime", "Остановка", "To'xtash")
a("oee.type.reject", "Брак", "Brak")
a("oee.ev.list", "События", "Hodisalar")
a("oee.ev.add", "Добавить событие", "Hodisa qo'shish")
a("oee.ev.edit", "Событие", "Hodisa")
a("oee.ev.total", "Всего: {{n}}", "Jami: {{n}}")
a("oee.ev.type", "Тип", "Tur")
a("oee.ev.start", "Начало", "Boshlanish")
a("oee.ev.end_open", "Конец (пусто — идёт)", "Tugash (bo'sh — davom etmoqda)")
a("oee.ev.end_open_hint", "Пустой конец — остановка ещё идёт; её закроет следующая запись о работе или кнопка «Возобновить»",
  "Tugash bo'sh bo'lsa to'xtash davom etmoqda; uni keyingi ish yozuvi yoki «Davom ettirish» tugmasi yopadi")
a("oee.ev.reason", "Причина", "Sabab")
a("oee.ev.run_end", "Время окончания", "Tugash vaqti")
a("oee.ev.run_start", "Время начала (необязательно)", "Boshlanish vaqti (ixtiyoriy)")
a("oee.ev.run_start_hint", "Если не указано, начало определяется по предыдущему событию станка", "Ko'rsatilmasa, boshlanish stanokning avvalgi hodisasidan aniqlanadi")
a("oee.ev.sheets", "Листов (карт)", "List (karta) soni")
a("oee.ev.parts", "Деталей", "Detallar")
a("oee.ev.reject_qty", "Брак в этой записи", "Shu yozuvdagi brak")
a("oee.ev.cut_length", "Длина реза одного листа", "Bitta listning kesish uzunligi")
a("oee.ev.cuts", "Резов на листе", "Listdagi kesimlar soni")
a("oee.ev.ideal", "Идеальный цикл листа", "List ideal sikli")
a("oee.ev.ideal_hint", "Необязательно: идеальное время одного листа. Если пусто — считается по длине реза, числу резов и скоростям станка",
  "Ixtiyoriy: bitta listning ideal vaqti. Bo'sh bo'lsa — kesish uzunligi, kesimlar soni va stanok tezliklaridan hisoblanadi")
a("oee.ev.reject_time", "Время обнаружения", "Aniqlangan vaqt")
a("oee.ev.reject_count", "Количество брака", "Brak soni")
a("oee.ev.note", "Примечание", "Izoh")
a("oee.ev.tz_hint", "Время завода (UTC{{h}})", "Zavod vaqti (UTC{{h}})")
a("oee.ev.d_sheets", "{{n}} лист.", "{{n}} list")
a("oee.ev.d_parts", "{{n}} дет.", "{{n}} detal")
a("oee.ev.d_reject", "брак {{n}} {{u}}", "brak {{n}} {{u}}")
a("oee.ev.open", "идёт", "davom etmoqda")
a("oee.ev.delete_q", "Удалить событие?", "Hodisani o'chirasizmi?")
a("oee.gap.title", "Простои без причины", "Sababsiz bo'shliqlar")
a("oee.gap.hint", "Периоды без записей внутри смены: назначьте причину — они станут остановками", "Smena ichidagi yozuvsiz davrlar: sabab belgilang — ular to'xtashga aylanadi")
a("oee.gap.assign", "Назначить причину", "Sabab belgilash")
a("oee.gap.choose", "Выберите причину", "Sababni tanlang")

# ── станки ──
a("oee.m.intro",
  "Идеальный цикл листа = длина реза / скорость + число резов × время смены реза + время загрузки листа (по карте кроя). Скорости задаются для каждого станка; события присылает MES по ключу станка.",
  "List ideal sikli = kesish uzunligi / tezlik + kesimlar soni × kesim almashinuvi vaqti + list yuklash vaqti (kroy kartasi bo'yicha). Tezliklar har stanok uchun beriladi; hodisalarni MES stanok kaliti bilan yuboradi.")
a("oee.m.none", "Станки не добавлены", "Stanoklar qo'shilmagan")
a("oee.m.add", "Добавить станок", "Stanok qo'shish")
a("oee.m.edit", "Станок", "Stanok")
a("oee.m.key", "Ключ", "Kalit")
a("oee.m.key_hint", "Латиница, цифры, . _ - ; по этому ключу MES присылает события", "Lotin harflari, raqam, . _ - ; MES hodisalarni shu kalit bilan yuboradi")
a("oee.m.name", "Название", "Nomi")
a("oee.m.kind", "Тип", "Turi")
a("oee.m.pp", "Станок постпроцессора", "Postprotsessor stanogi")
a("oee.m.pp_hint", "Связь со списком станков «Настройки → Постпроцессоры» (необязательно)", "«Sozlamalar → Postprotsessorlar» stanoklar ro'yxati bilan bog'lash (ixtiyoriy)")
a("oee.m.pp_none", "— свободный станок —", "— erkin stanok —")
a("oee.m.ideal", "Идеальные скорости", "Ideal tezliklar")
a("oee.m.speed", "Скорость резки", "Kesish tezligi")
a("oee.m.speed_hint", "Идеальная скорость реза, мм/с (1000 мм/с = 60 м/мин)", "Ideal kesish tezligi, mm/s (1000 mm/s = 60 m/daq)")
a("oee.m.speed_short", "Скорость, мм/с", "Tezlik, mm/s")
a("oee.m.change", "Смена реза", "Kesim almashinuvi")
a("oee.m.change_hint", "Время между резами: возврат, позиционирование", "Kesimlar orasidagi vaqt: qaytish, joylash")
a("oee.m.change_short", "Рез, с", "Kesim, s")
a("oee.m.load", "Загрузка листа", "List yuklash")
a("oee.m.load_hint", "Время загрузки одного листа (пакета)", "Bitta list (paket) yuklash vaqti")
a("oee.m.load_short", "Загрузка, с", "Yuklash, s")
a("oee.m.unit_s", "Идеальный цикл единицы", "Birlik ideal sikli")
a("oee.m.unit_s_hint", "Для станков без данных о резах (кромкование и др.): идеальное время одной единицы",
  "Kesim ma'lumoti yo'q stanoklar uchun (kromkalash va b.): bitta birlikning ideal vaqti")
a("oee.m.unit_s_short", "Цикл ед., с", "Birlik sikli, s")
a("oee.m.active", "Активен", "Faol")
a("oee.m.from_pp", "Из постпроцессора", "Postprotsessordan")
a("oee.m.suggest_ok", "Скорость взята из настроек постпроцессора: {{v}} мм/с ({{a}})", "Tezlik postprotsessor sozlamasidan olindi: {{v}} mm/s ({{a}})")
a("oee.m.suggest_none", "В настройках постпроцессора нет данных о скорости", "Postprotsessor sozlamasida tezlik ma'lumoti yo'q")
a("oee.m.example", "Пример: лист с 12 м реза и 20 резами → идеальный цикл {{s}} с", "Misol: 12 m kesim va 20 ta kesimli list → ideal sikl {{s}} s")
a("oee.m.delete_q", "Удалить станок «{{n}}»?", "«{{n}}» stanogini o'chirasizmi?")
a("oee.m.force_q", "У станка «{{n}}» есть события. Удалить станок вместе со всеми событиями?", "«{{n}}» stanogida hodisalar bor. Stanokni barcha hodisalari bilan o'chirasizmi?")
for k, ru, uz in [("saw", "Пильный центр", "Arra markazi"), ("edge", "Кромкооблицовочный", "Kromkalash"), ("cnc", "Обрабатывающий центр", "Ishlov markazi"),
                  ("other", "Другое", "Boshqa")]:
    a(f"oee.kind.{k}", ru, uz)

# ── смены ──
a("oee.s.intro",
  "Время смен — по времени завода (UTC{{h}}). Станок с собственными сменами использует только их, остальные — общие. Перерывы — плановые остановки: вычитаются из планового времени.",
  "Smena vaqtlari — zavod vaqti bilan (UTC{{h}}). O'z smenasi bor stanok faqat shularni ishlatadi, qolganlari — umumiylarni. Tanaffuslar — rejalashtirilgan to'xtash: rejalashtirilgan vaqtdan ayiriladi.")
a("oee.s.none", "Смены не заданы — OEE не рассчитывается", "Smenalar berilmagan — OEE hisoblanmaydi")
a("oee.s.add", "Добавить смену", "Smena qo'shish")
a("oee.s.add_off", "Выходной / праздник", "Dam olish / bayram")
a("oee.s.edit", "Смена", "Smena")
a("oee.s.name", "Название", "Nomi")
a("oee.s.machine_hint", "Пусто — общая смена для всех станков", "Bo'sh — hamma stanoklar uchun umumiy smena")
a("oee.s.weekdays", "Дни недели", "Hafta kunlari")
a("oee.s.time", "Начало — конец", "Boshlanish — tugash")
a("oee.s.time_hint", "Конец раньше начала — смена переходит через полночь", "Tugash boshlanishdan oldin bo'lsa — smena yarim tundan o'tadi")
a("oee.s.breaks", "Перерывы", "Tanaffuslar")
a("oee.s.add_break", "Добавить перерыв", "Tanaffus qo'shish")
a("oee.s.break_name", "Название", "Nomi")
a("oee.s.valid", "Действует (даты)", "Amal qilish (sanalar)")
a("oee.s.valid_hint", "Необязательно; даты по времени завода, включительно", "Ixtiyoriy; sanalar zavod vaqtida, shu kunlar ham kiradi")
a("oee.s.dates", "Даты (включительно)", "Sanalar (shu kunlar ham)")
a("oee.s.off_title", "Выходные и праздники", "Dam olish va bayramlar")
a("oee.s.off_none", "Нет записей", "Yozuvlar yo'q")
a("oee.s.delete_q", "Удалить смену?", "Smenani o'chirasizmi?")
a("oee.s.preview", "Календарь недели", "Hafta kalendari")
a("oee.s.preview_none", "На этой неделе смен нет", "Bu haftada smenalar yo'q")
for i, (ru, uz) in enumerate([("Пн", "Du"), ("Вт", "Se"), ("Ср", "Ch"), ("Чт", "Pa"), ("Пт", "Ju"), ("Сб", "Sh"), ("Вс", "Ya")]):
    a(f"oee.wd.{i}", ru, uz)

# ── причины ──
a("oee.r.intro",
  "Причины остановок и брака. «Плановая» остановка вычитается из планового времени и не снижает готовность (A). Паузы без записей внутри смены (не короче порога) учитываются как «простой без записи».",
  "To'xtash va brak sabablari. «Rejalashtirilgan» to'xtash rejalashtirilgan vaqtdan ayiriladi va tayyorlikni (A) kamaytirmaydi. Smena ichidagi yozuvsiz pauzalar (chegaradan kam bo'lmasa) «yozuvsiz bo'shliq» sifatida hisoblanadi.")
a("oee.r.add", "Добавить причину", "Sabab qo'shish")
a("oee.r.edit", "Причина", "Sabab")
a("oee.r.code", "Код", "Kod")
a("oee.r.code_hint", "Строчная латиница, цифры, _ ; по этому коду MES присылает причину", "Kichik lotin harflari, raqam, _ ; MES sababni shu kod bilan yuboradi")
a("oee.r.name", "Название", "Nomi")
a("oee.r.name_ru", "Название (рус.)", "Nomi (rus)")
a("oee.r.name_uz", "Название (узб.)", "Nomi (o'zbek)")
a("oee.r.kind", "Тип", "Turi")
a("oee.r.kind_downtime", "Причины остановок", "To'xtash sabablari")
a("oee.r.kind_reject", "Причины брака", "Brak sabablari")
a("oee.r.planned", "Плановая остановка", "Rejalashtirilgan to'xtash")
a("oee.r.planned_hint", "Например, перерыв или плановое обслуживание: время вычитается из планового", "Masalan, tanaffus yoki rejali xizmat: vaqt rejalashtirilgan vaqtdan ayiriladi")
a("oee.r.planned_short", "Плановая", "Reja")
a("oee.r.delete_q", "Удалить причину «{{n}}»?", "«{{n}}» sababini o'chirasizmi?")

# ── параметры ──
a("oee.p.tz", "Часовой пояс завода", "Zavod soat poyasi")
a("oee.p.tz_hint", "Смещение от UTC в часах (Узбекистан: +5)", "UTC dan siljish soatda (O'zbekiston: +5)")
a("oee.p.idle", "Порог простоя без записи", "Yozuvsiz bo'shliq chegarasi")
a("oee.p.idle_hint", "Пауза без событий короче порога — работа (смена карты); не короче — «простой без записи»",
  "Hodisasiz pauza chegaradan qisqa bo'lsa — ish (karta almashtirish); kam bo'lmasa — «yozuvsiz bo'shliq»")
a("oee.p.cap", "Предел цикла без начала", "Boshlanishsiz sikl chegarasi")
a("oee.p.cap_hint", "Для событий без времени начала: длительность работы ≤ коэффициент × идеальное время", "Boshlanish vaqti yo'q hodisalar uchun: ish davomiyligi ≤ koeffitsient × ideal vaqt")
a("oee.p.unit", "Единица выпуска", "Ishlab chiqarish birligi")
a("oee.p.unit_hint", "В чём считаются выпуск, брак и среднее время цикла", "Ishlab chiqarish, brak va o'rtacha sikl nimada hisoblanadi")
a("oee.p.unit_sheet", "Лист (карта)", "List (karta)")
a("oee.p.unit_part", "Деталь", "Detal")
a("oee.p.overtime", "Работа вне смены входит в плановое время", "Smenadan tashqari ish rejalashtirilgan vaqtga kiradi")
a("oee.p.overtime_hint", "Выключено: выпуск вне смен не учитывается в OEE (показывается в предупреждении)", "O'chiq: smenadan tashqari ishlab chiqarish OEE ga kirmaydi (ogohlantirishda ko'rsatiladi)")
a("oee.p.formulas", "Формулы", "Formulalar")
a("oee.p.f_oee", "OEE = A × P × Q", "OEE = A × P × Q")
a("oee.p.f_a", "A (готовность) = время работы / плановое время; плановое = смена − перерывы − плановые остановки",
  "A (tayyorlik) = ish vaqti / rejalashtirilgan vaqt; rejalashtirilgan = smena − tanaffuslar − rejalashtirilgan to'xtashlar")
a("oee.p.f_p", "P (производительность) = идеальное время / время работы, не более 100 %", "P (unumdorlik) = ideal vaqt / ish vaqti, 100 % dan oshmaydi")
a("oee.p.f_q", "Q (качество) = годные / всего произведено", "Q (sifat) = yaroqli / jami ishlab chiqarilgan")
a("oee.p.f_idle", "Пауза без событий ≥ {{min}} мин — «простой без записи» (уменьшает A)", "Hodisasiz pauza ≥ {{min}} daq — «yozuvsiz bo'shliq» (A ni kamaytiradi)")
a("oee.p.f_bands", "Цвета: < {{low}} % — красный, {{low}}–{{high}} % — жёлтый, ≥ {{high}} % — зелёный", "Ranglar: < {{low}} % — qizil, {{low}}–{{high}} % — sariq, ≥ {{high}} % — yashil")

# ── режим цеха ──
a("oee.ws.machine", "Станок", "Stanok")
a("oee.ws.choose", "Выберите станок", "Stanokni tanlang")
a("oee.ws.stop", "Остановка", "To'xtash")
a("oee.ws.stopped", "Остановка", "To'xtash")
a("oee.ws.since", "{{m}} мин", "{{m}} daq")
a("oee.ws.resume", "Возобновить работу", "Ishni davom ettirish")
a("oee.ws.resumed", "Работа возобновлена", "Ish davom ettirildi")
a("oee.ws.stop_title", "Причина остановки", "To'xtash sababi")
a("oee.ws.stop_hint", "Станок: {{m}}. Выберите причину — время остановки пойдёт в OEE.", "Stanok: {{m}}. Sababni tanlang — to'xtash vaqti OEE ga yoziladi.")
a("oee.ws.note", "Примечание (необязательно)", "Izoh (ixtiyoriy)")
