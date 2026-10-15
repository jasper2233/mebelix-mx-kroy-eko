# -*- coding: utf-8 -*-
"""W6 paketi matnlari: GR paneli, EL/GR parametr yordami, ifoda yordamchisi, «Справка» bo'limlari, «Что нового».
`i18n_src.py` shu faylni o'zi yuklaydi (`a(kalit, ru, uz)`); ishga tushirish: `python frontend/scripts/i18n_src.py`.
Eslatma: ifoda yordamchisi kalitlari `exprh.*` (boshqa to'lqinlar `expr.*` ishlatsa to'qnashmasin)."""

# ───────────────────────── GR paneli va chop ─────────────────────────
a("print.sec.gr", "(GR) Пазование", "(GR) Pazlash")
a("print.f.gr_params", "Параметры паза и расчёт", "Paz parametrlari va hisob")
a("print.f.gr_parts", "Детали с пазом", "Pazli detallar")
a("gr.groove", "Параметры паза", "Paz parametrlari")
a("gr.p.width", "Ширина", "Eni")
a("gr.p.depth", "Глубина", "Chuqurlik")
a("gr.p.offset", "Отступ", "Chetdan masofa")
a("gr.p.offset_incl", "Отступ включительно", "Masofa inklyuziv")
a("gr.p.saw", "Толщина пилы", "Arra qalinligi")
a("gr.p.price", "Цена м-ра паза", "1 m paz narxi")
a("gr.p.usage", "Д-на паза", "Paz uzunligi")
a("gr.p.passes", "Число проходов", "O'tishlar soni")
a("gr.p.cut", "Длина пропила", "Kesim (propil) uzunligi")
a("gr.p.cost", "Стоимость", "Narx (jami)")
a("gr.saw_hint", "Паз шире пилы прорезается за несколько проходов: ⌈W / толщина пилы⌉",
  "Arradan keng paz bir necha o'tishda kesiladi: ⌈W / arra qalinligi⌉")
a("gr.passes_hint", "⌈ширина паза / толщина пилы⌉, не меньше 1", "⌈paz eni / arra qalinligi⌉, kamida 1")
a("gr.defaults_saved", "Параметры паза сохранены как стандартные", "Paz parametrlari standart sifatida saqlandi")
a("gr.col.top", "ПВ", "PV"); a("gr.col.bottom", "ПН", "PN"); a("gr.col.left", "ПЛ", "PL"); a("gr.col.right", "ПП", "PP")
a("gr.col.len_m", "Д-на паза, м", "Paz uz., m")
a("gr.back", "обр.", "orqa")
a("gr.sketch", "Схема паза: W — ширина, D — глубина, O — отступ от края", "Paz sxemasi: W — eni, D — chuqurlik, O — chetdan masofa")
a("gr.sketch_edge", "край детали", "detal cheti")
a("oparts.keys_hint", "Ctrl+Space — свойства · Home / End / ↑ / ↓ — строки · клик по заголовку — сортировка",
  "Ctrl+Space — xossalar · Home / End / ↑ / ↓ — qatorlar · sarlavha bosilsa — saralash")

# ───────────────────────── «Справка»: bo'limlar ─────────────────────────
a("help.topic.el", "(EL) Кромка: параметры", "(EL) Kromka: parametrlar")
a("help.topic.gr", "(GR) Пазование", "(GR) Pazlash")
a("help.topic.expr", "Выражения", "Ifodalar")
a("help.topic.machines", "Станки и постпроцессор", "Stanoklar va postprotsessor")
a("help.topic.whatsnew", "Что нового", "Yangiliklar")
a("help.about_param", "Что это за параметр? (Справка)", "Bu qanday parametr? (Yordam)")
# mavjud yorliq matnlari kengaytirildi (EL/GR «Детали» jadvallari)
a("help.hk.maps_nav", "Навигация по картам кроя и по строкам таблиц «Детали» (EL / GR)",
  "Kroy kartalari va «Detallar» (EL / GR) jadvali qatorlari bo'ylab yurish")
a("help.hk.properties", "Свойства детали (в том числе в таблицах EL / GR); в списке проектов — открыть",
  "Detal xossalari (EL / GR jadvallarida ham); loyihalar ro'yxatida — ochish")

a("help.el.intro",
  """Операция (EL) описывает один вид кромки: ленту, расход, цену и обозначение. Кромка назначается сторонам деталей в колонках ОВ / ОН (по длине) и ОЛ / ОП (по ширине) таблицы деталей.
Здесь — смысл каждого параметра; сами формулы — в разделе «Кромка: формулы». Значок «?» рядом с параметром открывает этот раздел на нужном месте.""",
  """(EL) operatsiyasi bitta kromka turini tasvirlaydi: lenta, sarf, narx va belgi. Kromka detallar jadvalidagi OV / ON (uzunlik bo'ylab) va OL / OP (en bo'ylab) ustunlarida detal tomonlariga tayinlanadi.
Bu yerda har bir parametrning ma'nosi; formulalar — «Kromka: formulalar» bo'limida. Parametr yonidagi «?» belgisi shu bo'limning kerakli joyini ochadi.""")
_EL = {
    "count_material": ("Если отмечено, в стоимость кромки входит материал (длина материала × цена); если снято — считается только работа по оклейке.",
                       "Belgilansa, kromka narxiga material (material uzunligi × narx) ham kiradi; olib tashlansa — faqat yopishtirish ishi hisoblanadi."),
    "width": ("Ширина ленты кромки, мм. Справочная величина (обычно из каталога); на длину и стоимость не влияет.",
              "Kromka lentasining eni, mm. Ma'lumot uchun (odatda katalogdan); uzunlik va narxga ta'sir qilmaydi."),
    "thickness": ("Толщина кромки, мм. Кромкованная сторона готовой детали становится больше на эту величину, поэтому при расчёте размеров она вычитается из размера «детали с кромкой».",
                  "Kromka qalinligi, mm. Kromkalangan tomon tayyor detalda shu qadar kattalashadi, shuning uchun o'lchamlar hisobida «kromkali detal» o'lchamidan ayriladi."),
    "jointing": ("Ширина прифуговки, мм: слой, который станок снимает с торца перед наклейкой. Заготовка больше размера «после прифуговки» на эту величину.",
                 "Prifugovka eni, mm: stanok yopishtirishdan oldin chetdan olib tashlaydigan qatlam. Zagotovka «prifugovkadan keyingi» o'lchamdan shuncha katta."),
    "waste": ("Процент отхода: надбавка на потери при оклейке. Длина материала умножается на (1 + процент / 100).",
              "Chiqindi foizi: yopishtirishdagi yo'qotishlar uchun qo'shimcha. Material uzunligi (1 + foiz / 100) ga ko'paytiriladi."),
    "overhang": ("Длина остатка по краям, мм: запас, который станок срезает с каждого конца кромкуемой стороны. К каждой стороне добавляется 2 × значение (при 20 мм сторона 1000 мм расходует 1040 мм).",
                 "Chetlardagi qoldiq uzunligi, mm: stanok kromkalanadigan tomonning har ikki uchidan qirqib tashlaydigan zapas. Har tomonga 2 × qiymat qo'shiladi (20 mm da 1000 mm tomon 1040 mm sarflaydi)."),
    "min_glue": ("Минимальная оклеиваемая длина, мм. Если кромкуемая сторона короче, расход материала считается по этому значению (длина работы остаётся фактической).",
                 "Minimal yopishtiriladigan uzunlik, mm. Kromkalanadigan tomon undan qisqa bo'lsa, material sarfi shu qiymat bo'yicha hisoblanadi (ish uzunligi haqiqiyligicha qoladi)."),
    "symbol": ("Символ обозначения (одна буква): подписывается у кромкованной стороны на карте раскроя и на этикетке. Для новой кромки назначается автоматически (A, B, C…) и в общие параметры по умолчанию не сохраняется.",
               "Belgi (bitta harf): kroy kartasi va etiketkada kromkalangan tomon yonida yoziladi. Yangi kromka uchun avtomatik beriladi (A, B, C…) va umumiy standartga saqlanmaydi."),
    "color": ("Цвет, которым название кромки выделяется в таблице деталей и на чертеже детали. Для новой кромки подбирается автоматически.",
              "Detallar jadvali va detal chizmasida kromka nomi shu rang bilan ajratiladi. Yangi kromka uchun avtomatik tanlanadi."),
    "lines": ("Линии маркировки: сколько линий (1–3) рисуется у кромкованной стороны на карте раскроя и на этикетке; помогает различать виды кромки.",
              "Markirovka chiziqlari: kroy kartasi va etiketkada kromkalangan tomon yonida nechta chiziq (1–3) chiziladi; kromka turlarini farqlashga yordam beradi."),
    "min_perp": ("Минимальный размер стороны, перпендикулярной кромке, мм. Если у детали с кромкой эта сторона уже указанной, строка в «Деталях» подсвечивается и выводится предупреждение: станок такую деталь не удержит.",
                 "Kromkaga perpendikulyar tomonning minimal o'lchami, mm. Kromkali detalning bu tomoni undan tor bo'lsa, «Detallar»dagi qator ajratiladi va ogohlantirish chiqadi: stanok bunday detalni ushlay olmaydi."),
    "price": ("Цена материала — цена одного метра кромки.", "Material narxi — 1 m kromka narxi."),
    "mat_round": ("Округление длины материала. Код = (число знаков после запятой) × 10 + режим (0 — к ближайшему, 1 — к большему, 2 — к меньшему). Например [0.00] — до сотых к ближайшему, ⌈0.0⌉ — вверх до десятых.",
                  "Material uzunligini yaxlitlash. Kod = (kasr xonalari soni) × 10 + rejim (0 — yaqiniga, 1 — kattaga, 2 — kichikka). Masalan [0.00] — yuzdan birgacha yaqiniga, ⌈0.0⌉ — o'ndan birgacha yuqoriga."),
    "mat_len": ("Расчётная длина материала (только чтение): Σ (max(сторона; мин. оклеиваемая длина) + 2 × остаток) × количество × (1 + отход %), затем округление.",
                "Hisoblangan material uzunligi (faqat o'qish): Σ (max(tomon; min. yopishtiriladigan uzunlik) + 2 × qoldiq) × soni × (1 + chiqindi %), so'ng yaxlitlash."),
    "mat_cost": ("Стоимость материала = длина материала × цена материала (если отмечено «Учитывать материал»).",
                 "Material narxi = material uzunligi × material narxi («Materialni hisobga olish» belgilangan bo'lsa)."),
    "op_price": ("Цена операции — цена одного метра оклейки (работа кромкования).", "Operatsiya narxi — 1 m yopishtirish (kromkalash ishi) narxi."),
    "work_round": ("Округление длины кромкования — те же коды, что и для материала, но применяются к длине работы.",
                   "Kromkalash uzunligini yaxlitlash — material bilan bir xil kodlar, lekin ish uzunligiga qo'llanadi."),
    "work_len": ("Длина кромкования (работа, только чтение): сумма длин всех кромкуемых сторон × количество — без отхода, остатков и минимальной длины.",
                 "Kromkalash uzunligi (ish, faqat o'qish): kromkalanadigan barcha tomonlar uzunligi yig'indisi × soni — chiqindi, qoldiq va minimal uzunliksiz."),
    "op_cost": ("Стоимость операции = длина кромкования × цена операции.", "Operatsiya narxi = kromkalash uzunligi × operatsiya narxi."),
    "cost": ("Стоимость = стоимость материала + стоимость операции.", "Narx = material narxi + operatsiya narxi."),
}
for _k, (_ru, _uz) in _EL.items():
    a(f"help.el.{_k}", _ru, _uz)

a("help.gr.intro",
  """Операция (GR) описывает паз: ширину W, глубину D, отступ O от края и толщину пилы. Паз назначается стороне детали в окне «Свойства» (или в колонках ПВ / ПН / ПЛ / ПП): ПВ и ПН — паз по длине (сверху / снизу), ПЛ и ПП — по ширине (слева / справа); отдельно выбирается сторона — лицевая или обратная. К названию детали с пазом добавляется «=».
Стоимость считается по длине пазования; материал в этой операции не расходуется. Значок «?» рядом с параметром открывает этот раздел на нужном месте.""",
  """(GR) operatsiyasi pazni tasvirlaydi: eni W, chuqurligi D, chetdan masofa O va arra qalinligi. Paz detal tomoniga «Xossalar» oynasida (yoki PV / PN / PL / PP ustunlarida) tayinlanadi: PV va PN — uzunlik bo'ylab (yuqori / past), PL va PP — en bo'ylab (chap / o'ng); alohida tomon tanlanadi — lits yoki orqa. Pazli detal nomiga «=» qo'shiladi.
Narx pazlash uzunligi bo'yicha hisoblanadi; bu operatsiyada material sarflanmaydi. Parametr yonidagi «?» belgisi shu bo'limning kerakli joyini ochadi.""")
_GR = {
    "width": ("Ширина паза W, мм. Если она больше толщины пилы, паз прорезается за несколько проходов: ⌈W / толщина пилы⌉.",
              "Paz eni W, mm. Arra qalinligidan katta bo'lsa, paz bir necha o'tishda kesiladi: ⌈W / arra qalinligi⌉."),
    "depth": ("Глубина паза D, мм.", "Paz chuqurligi D, mm."),
    "offset": ("Отступ O, мм: расстояние от края детали до паза.", "Chetdan masofa O, mm: detal chetidan pazgacha masofa."),
    "offset_incl": ("Флажок способа отсчёта отступа (с учётом ширины паза или без). Хранится в проекте; на длину пазования и стоимость не влияет.",
                    "Masofa qanday sanalishini belgilovchi bayroq (paz eni bilan yoki alohida). Loyihada saqlanadi; pazlash uzunligi va narxga ta'sir qilmaydi."),
    "saw": ("Толщина пилы, мм — ширина реза инструмента. Определяет число проходов: ⌈W / толщина пилы⌉, не меньше одного.",
            "Arra qalinligi, mm — asbob kesimining eni. O'tishlar sonini belgilaydi: ⌈W / arra qalinligi⌉, kamida bitta."),
    "price": ("Цена метра паза — цена одного метра длины пазования.", "1 m paz narxi — pazlash uzunligining 1 metri narxi."),
    "usage": ("Длина пазования (только чтение): сумма длин пазованных сторон деталей × количество (ОК − МК), в метрах.",
              "Pazlash uzunligi (faqat o'qish): detallarning pazlangan tomonlari uzunligi yig'indisi × soni (OK − MK), metrda."),
    "passes": ("Число проходов пилы: ⌈ширина паза / толщина пилы⌉.", "Arra o'tishlari soni: ⌈paz eni / arra qalinligi⌉."),
    "cut": ("Длина пропила (только чтение): длина пазования × число проходов — фактическая длина резов.",
            "Kesim (propil) uzunligi (faqat o'qish): pazlash uzunligi × o'tishlar soni — kesimlarning haqiqiy uzunligi."),
    "cost": ("Стоимость = длина пазования × цена метра паза. Материал в пазовании не считается.",
             "Narx = pazlash uzunligi × 1 m paz narxi. Pazlashda material hisoblanmaydi."),
}
for _k, (_ru, _uz) in _GR.items():
    a(f"help.gr.{_k}", _ru, _uz)

a("help.text.expr",
  """Выражения используются в параметрах XNC-программ, а по мере развития — в этикетках и вычисляемых колонках. Везде действует один язык.

Типы: целое (32 бита), дробное (double), логическое (true / false), строка ('в одинарных кавычках'), null.
Целое ÷ целое = целое (7 / 2 = 3); если есть дробное — результат дробный (7.0 / 2 = 3.5). Строка + число склеивается: 'x' + 1 = 'x1'.
Порядок действий (от сильного к слабому): скобки и функции; ^ (степень, справа налево); унарные + −; * / %; + −; сравнения < > <= >= = == <> !=; not; and; xor; or.
Условие: if(условие, да, нет) — вычисляется только выбранная ветвь (допустима и запись «a if условие else b»).
Углы в sin, cos, tan и обратных функциях — в радианах (cos(pi) = −1); в окне проверки можно включить градусы.
Ошибки не скрываются: деление на ноль, неизвестная функция или переменная, неверный тип — сообщение с причиной (результат никогда не заменяется нулём молча).
Пределы: до 1000 символов в выражении, до 10 000 шагов вычисления, результат-строка до 10 000 символов, calculate() — вложенность до 4.
Выражение проверяется и вычисляется на сервере: то, что показывает окно «Проверка выражения», — именно то, что получит программа.""",
  """Ifodalar XNC dasturlari parametrlarida, rivojlanishi bilan esa etiketkalar va hisoblanadigan ustunlarda ishlatiladi. Hamma joyda bitta til amal qiladi.

Turlar: butun (32 bit), kasr (double), mantiqiy (true / false), satr ('bitta qo'shtirnoqda'), null.
Butun ÷ butun = butun (7 / 2 = 3); kasr qatnashsa — natija kasr (7.0 / 2 = 3.5). Satr + son birlashadi: 'x' + 1 = 'x1'.
Amallar tartibi (kuchlidan kuchsizga): qavslar va funksiyalar; ^ (daraja, o'ngdan chapga); unar + −; * / %; + −; taqqoslash < > <= >= = == <> !=; not; and; xor; or.
Shart: if(shart, ha, yo'q) — faqat tanlangan tarmoq hisoblanadi («a if shart else b» yozuvi ham mumkin).
sin, cos, tan va teskari funksiyalarda burchak — radianda (cos(pi) = −1); tekshirish oynasida gradusni yoqish mumkin.
Xatolar yashirilmaydi: nolga bo'lish, noma'lum funksiya yoki o'zgaruvchi, noto'g'ri tur — sabab bilan xabar (natija hech qachon jimgina nolga almashtirilmaydi).
Chegaralar: ifoda 1000 belgigacha, hisoblash 10 000 qadamgacha, natija-satr 10 000 belgigacha, calculate() — ichma-ichlik 4 gacha.
Ifoda serverda tekshiriladi va hisoblanadi: «Ifodani tekshirish» oynasi ko'rsatgan natija — dastur oladigan natijaning o'zi.""")

a("help.text.machines",
  """«Настройки → Постпроцессоры → Станки» содержит готовый список станков: пильные центры и обрабатывающие центры (XNC). Названия — справочные; формат файла для каждого станка задаёт шаблон предприятия (Jinja) или внешний постпроцессор.
1. Отметьте станки, которые есть на предприятии, — они появятся в «Раскрой → Постпроцессор».
2. Подключите к станку шаблон формата (из списка «Станки предприятия»). Пока шаблон не подключён, станок помечен «формат не подключён», и файл не выгружается.
3. «Добавлять имя станка в начало имени файла» — чтобы файлы разных станков не путались.
Структуру файла (формат программы) даёт предприятие: для настройки шаблона нужен образец формата. Ниже — станки из списка (включённые отмечены ✓).""",
  """«Sozlamalar → Postprotsessorlar → Stanoklar» tayyor stanoklar ro'yxatini beradi: pil markazlari va ishlov markazlari (XNC). Nomlar — ma'lumot uchun; har stanok fayl formatini korxona shabloni (Jinja) yoki tashqi postprotsessor belgilaydi.
1. Korxonada bor stanoklarni belgilang — ular «Kroy → Postprotsessor» ro'yxatida chiqadi.
2. Stanokka format shablonini ulang («Korxona stanoklari» ro'yxatidan). Shablon ulanmaguncha stanok «format ulanmagan» deb belgilanadi va fayl chiqarilmaydi.
3. «Fayl nomi boshiga stanok nomini qo'shish» — turli stanok fayllari aralashib ketmasligi uchun.
Fayl tuzilishini (dastur formatini) korxona beradi: shablonni sozlash uchun format namunasi kerak. Pastda — ro'yxatdagi stanoklar (yoqilganlari ✓ bilan).""")

# «MES» bo'limi: ilgari mavjud matn o'rniga (panel tavsifi bilan to'ldirilgan; i18n_src.py dagi `help.text.mes` ni almashtiradi)
a("help.text.mes",
  """Заказы приходят из MES (POST /api/mes/orders) — проект создаётся автоматически с операциями по материалам и кромкам.
На каждой карте кроя и этикетке детали — QR-код. В цеху режим «Цех (сканер QR)» (#/sex): сканируйте карту → «Раскроено» (+1), статус уходит в MES через webhook.
Склад деловых остатков общий для всех проектов.

Панель «MES» (левое меню). Пока интеграция выключена, пункт серый. Включение — «Настройки → MES интеграция». В панели шесть разделов: «Обзор» (состояние связи), «Заказы MES», «Отправка результатов», «Склад и каталог», «Журнал обмена» и «Связь и API» (адреса, webhook, JWT).
Реальные обмены подключает команда MES предприятия: разделы-заготовки показывают, какие функции появятся; рабочая часть сейчас — «Связь и API».""",
  """Buyurtmalar MES dan keladi (POST /api/mes/orders) — loyiha materiallar va kromkalar bo'yicha avtomatik yaratiladi.
Har kroy kartasi va detal etiketkasida QR kod bor. Sexda «Sex rejimi (QR skaner)» (#/sex): kartani skanerlang → «Kesildi» (+1), holat webhook orqali MES ga ketadi.
Deloviy qoldiqlar ombori barcha loyihalar uchun umumiy.

«MES» paneli (chap menyu). Integratsiya o'chiq paytda band xira. Yoqish — «Sozlamalar → MES integratsiyasi». Panelda oltita bo'lim: «Umumiy ko'rinish» (aloqa holati), «MES buyurtmalari», «Natijalarni yuborish», «Ombor va katalog», «Almashinuv jurnali» va «Aloqa va API» (manzillar, webhook, JWT).
Haqiqiy almashinuvni korxona MES jamoasi ulaydi: bo'limlar-karkaslar qanday funksiyalar paydo bo'lishini ko'rsatadi; hozir ishlaydigan qism — «Aloqa va API».""")

# ───────────────────────── Ifoda yordamchisi (shared/ExprHelper.tsx) ─────────────────────────
a("exprh.check_title", "Проверка выражения", "Ifodani tekshirish")
a("exprh.placeholder", "Например: left(trim(name), 3) + '-' + format('00', qty)", "Masalan: left(trim(name), 3) + '-' + format('00', qty)")
a("exprh.empty", "Введите выражение — результат появится здесь", "Ifodani kiriting — natija shu yerda chiqadi")
a("exprh.checking", "Проверка…", "Tekshirilmoqda…")
for _k, _ru, _uz in [("integer", "целое", "butun"), ("double", "дробное", "kasr"), ("boolean", "логическое", "mantiqiy"),
                     ("string", "строка", "satr"), ("null", "пусто", "bo'sh")]:
    a(f"exprh.type.{_k}", _ru, _uz)
a("exprh.stage.syntax", "Синтаксис", "Sintaksis"); a("exprh.stage.eval", "Вычисление", "Hisoblash")
a("exprh.degrees", "Углы в градусах", "Burchaklar gradusda")
a("exprh.server_note", "Выражение вычисляется на сервере", "Ifoda serverda hisoblanadi")
a("exprh.variables", "Пробные значения переменных", "O'zgaruvchilarning sinov qiymatlari")
a("exprh.functions", "Функции", "Funksiyalar")
a("exprh.search", "Поиск функции…", "Funksiyani qidirish…")
a("exprh.group_all", "Все", "Hammasi")
a("exprh.col.function", "Функция", "Funksiya"); a("exprh.col.description", "Описание", "Tavsif")
a("exprh.col.example", "Пример → результат", "Misol → natija")
a("exprh.insert", "Вставить в выражение", "Ifodaga qo'yish")
a("exprh.not_found", "Ничего не найдено", "Hech narsa topilmadi")
a("exprh.demo.dx", "Длина детали (пример)", "Detal uzunligi (misol)"); a("exprh.demo.dy", "Ширина детали (пример)", "Detal eni (misol)")
a("exprh.demo.name", "Название (пример)", "Nomi (misol)"); a("exprh.demo.qty", "Количество (пример)", "Soni (misol)")
a("exprh.operators", "Операторы и записи", "Operatorlar va yozuvlar")
a("exprh.constants", "Константы", "Konstantalar")

# ───────────────────────── «Что нового» ─────────────────────────
# Tuzilma: (kalit, sarlavha ru/uz, sana, qisqacha ru/uz, [(qisqa nom ru, uz, tavsif ru, uz), …]); yangisi — birinchi (kalit tartibi kamayib boradi).
# Boshqa to'lqinlar (W1–W5) o'z o'zgarishlarini tegishli versiya ro'yxatiga qo'shadi.
a("whatsnew.intro", "История изменений MebeliX Kroy. Новое — сверху.", "MebeliX Kroy o'zgarishlar tarixi. Yangisi — tepada.")
_WN = [
    ("v23", ("Версия 2.3", "Versiya 2.3"), "2026-10-02",
     ("Настройки станков, XNC-ограничения, этикетки, экспорт проекта, погонаж (CL), обработка поверхности (SP), режимы редактора карт, заказ и импорт из других программ.",
      "Stanok sozlamalari, XNC cheklovlari, etiketkalar, loyiha eksporti, pogonaj (CL), sirt ishlovi (SP), karta muharriri rejimlari, buyurtma va boshqa dasturlardan import."),
     [("Станки: параметры по группам", "Stanoklar: guruhlangan parametrlar",
       "для 19 пильных центров — сгруппированные параметры (общие, печать этикеток, торцовка, ограничения и др.) с отметкой изменённых значений и кнопкой возврата к стандарту; таблицы «Данные для этикеток» (название → выражение) с живым просмотром на реальной детали; для станков с файлом этикетки — выбор шаблона из библиотеки и просмотр («Открыть»).",
       "19 ta pil markazi uchun guruhlangan parametrlar (umumiy, etiketka chop etish, torsovka, cheklovlar va h.k.) — o'zgargan qiymatlar belgilanadi, standartga qaytarish tugmasi bor; «Etiketkalar uchun ma'lumotlar» jadvallari (nom → ifoda) haqiqiy detalda jonli ko'rinish bilan; etiketka fayli bor stanoklar uchun — kutubxonadan shablon tanlash va ko'rish («Открыть»)."),
      ("XNC: ограничения, инструменты, палитра", "XNC: cheklovlar, asboblar, palitra",
       "«Настройки → XNC редактор»: ограничения станка (габариты детали, отступы отверстий и пазов, расстояние фрезы, поворот «длинной стороной» или «кромкой в угол») с предупреждениями в панели программы; таблица инструментов (диаметр, сквозное, глубина); палитра команд (порядок и включение).",
       "«Sozlamalar → XNC muharriri»: stanok cheklovlari (detal gabariti, teshik va paz masofalari, freza masofasi, «uzun tomon» yoki «kromka burchakka» burish) dastur panelida ogohlantirishlar bilan; asboblar jadvali (diametr, teshib o'tish, chuqurlik); buyruqlar palitrasi (tartib va yoqish)."),
      ("Шаблоны этикеток: файлы", "Etiketka shablonlari: fayllar",
       "импорт и экспорт готовых шаблонов этикеток (файлы программ и проектов) в удобный формат; шаблоны попадают в библиотеку и доступны в «Этикетки» и в настройках станков.",
       "tayyor etiketka shablonlarini (dastur va loyiha fayllari) qulay formatga import va eksport qilish; shablonlar kutubxonaga tushadi va «Etiketkalar» hamda stanok sozlamalarida mavjud bo'ladi."),
      ("Экспорт проекта и повороты", "Loyiha eksporti va burilishlar",
       "«Экспортировать» сохраняет проект в файл .project (один файл или ZIP для нескольких проектов); число поворотов в раскрое — от 1 до 6; «Мин. размер детали» — в «Общих» параметрах.",
       "«Eksport» loyihani .project fayliga saqlaydi (bitta fayl yoki bir nechta loyiha uchun ZIP); kroydagi burilishlar soni — 1 dan 6 gacha; «Detalning min. o'lchami» — «Umumiy» parametrlarda."),
      ("Погонажный раскрой (CL) и CLE", "Pogonaj kroy (CL) va CLE",
       "раскрой погонажных деталей по полосам: параметры, детали, полосы и отходы, карта полосы, ручной редактор карт (CLE), печать, деловые остатки на складе, импорт и экспорт проекта.",
       "pogonaj detallarni polosalar bo'yicha kroy qilish: parametrlar, detallar, polosalar va otxodlar, polosa kartasi, qo'lda karta muharriri (CLE), chop, ombordagi deloviy qoldiqlar, loyihani import va eksport."),
      ("Обработка поверхности (SP) и «Программа» изделия", "Sirt ishlovi (SP) va mahsulot «Dasturi»",
       "операция «Обработка поверхности» (площадь, расход материала, стоимость, привязка к лицевой и обратной стороне детали); в «Изделия → Свойства» — вкладка «Программа» (параметры, переменные, ограничения и сообщения), «Пересчитать параметричность» в «Общих действиях».",
       "«Sirt ishlovi» operatsiyasi (maydon, material sarfi, narx, detalning old va orqa tomoniga bog'lash); «Mahsulotlar → Xossalar» da — «Dastur» yorlig'i (parametrlar, o'zgaruvchilar, cheklovlar va xabarlar), «Umumiy amallar» da «Parametrikni qayta hisoblash»."),
      ("Редактор карт раскроя (CSE)", "Kroy kartalari muharriri (CSE)",
       "выбор нескольких деталей, Shift+A и Shift+W, торцовка карты, порядок карт, защита от одновременного изменения карты в двух окнах.",
       "bir nechta detalni tanlash, Shift+A va Shift+W, karta torsovkasi, kartalar tartibi, kartani ikki oynada bir vaqtda o'zgartirishdan himoya."),
      ("Заказ", "Buyurtma",
       "кнопка «Заказать» и статусы заказа (не заказан → заказан → утверждён → готов) с историей и правами по ролям; столбец «Изменено» и «Очистить проект» в «Общих действиях».",
       "«Buyurtma» tugmasi va buyurtma holatlari (buyurtma qilinmagan → buyurtma qilingan → tasdiqlangan → tayyor) tarix va rollar bo'yicha huquqlar bilan; «Umumiy amallar» da «O'zgargan» ustuni va «Loyihani tozalash»."),
      ("XNC: перетаскивание, скругление, текстовые параметры", "XNC: sudrab ko'chirish, yumaloqlash, matnli parametrlar",
       "команды в дереве программы переносятся мышью (клавиатура по-прежнему работает); скругление угла между линией и дугой и между дугами; текстовый параметр «Par»; на чертеже видно поворот по ограничениям станка («Вид на станке»); для обработки с обратной стороны отступы отверстий и пазов считаются с учётом зеркала.",
       "dastur daraxtidagi buyruqlar sichqoncha bilan ko'chiriladi (klaviatura avvalgidek ishlaydi); chiziq va yoy hamda yoylar orasidagi burchakni yumaloqlash; matnli «Par» parametri; chizmada stanok cheklovlari bo'yicha burilish ko'rinadi («Stanokdagi ko'rinish»); orqa tomondan ishlovda teshik va paz masofalari akslantirish hisobga olingan holda hisoblanadi."),
      ("CL: свойства детали, варианты, до кроить", "CL: detal xossalari, variantlar, dokroy",
       "окно «Свойства» детали погонажа; «Варианты» — сравнение вариантов раскроя (меньше материала, меньше расход, меньше резов, максимальное качество); «До кроить» — новые детали на оставшиеся полосы без изменения готовых карт; групповые действия (SP, перенос в другую операцию); переменные полосы в этикетках.",
       "pogonaj detalining «Xossalar» oynasi; «Variantlar» — kroy variantlarini solishtirish (kam material, kam sarf, kam kesim, maksimal sifat); «Dokroy» — tayyor kartalarni o'zgartirmay yangi detallarni qolgan polosalarga joylash; guruhli amallar (SP, boshqa operatsiyaga ko'chirish); etiketkalarda polosa o'zgaruvchilari."),
      ("Импорт из других программ", "Boshqa dasturlardan import",
       "окно со списком форматов (проект .project и ещё семь форматов — они серые, пока нет модуля и образца файла), параметры импорта по группам, профили (именованные наборы) и «Восстановить стандартные», экспорт и импорт профилей в JSON / XML.",
       "formatlar ro'yxati bilan oyna (.project loyiha fayli va yana yettita format — modul va namuna fayl bo'lmaguncha xira), guruhlangan import parametrlari, profillar (nomlangan to'plamlar) va «Standartni tiklash», profillarni JSON / XML ga eksport va import."),
      ("Импорт из Excel: вкладки и группы столбцов", "Excel dan import: tablar va ustun guruhlari",
       "новые вкладки «Простые операции» (комплектация) и «Материалы» (из каталога: лист, кромка, поверхность, погонаж); столбцы (SP) обработка поверхности, (GR) пазование, (XNC) обработка 1 / 2 по коду шаблона; строки без ширины — в погонаж (CL); корневые категории каталога хранятся на сервере.",
       "yangi «Простые операции» (komplektatsiya) va «Материалы» (katalogdan: varaq, kromka, sirt, pogonaj) tablari; (SP) sirt ishlovi, (GR) pazlash, (XNC) ishlov 1 / 2 ustunlari shablon kodi bo'yicha; eni yo'q qatorlar — pogonajga (CL); katalogning ildiz kategoriyalari serverda saqlanadi."),
      ("Список проектов", "Loyihalar ro'yxati",
       "столбец «№» — номер строки в списке (отдельно от ID заказа).",
       "«№» ustuni — ro'yxatdagi qator raqami (buyurtma ID sidan alohida).")]),
    ("v22", ("Версия 2.2", "Versiya 2.2"), "2026-10-02",
     ("Панель MES, станки, единый язык выражений, доработки XNC, пазования и кромки, справка.",
      "MES paneli, stanoklar, yagona ifoda tili, XNC, pazlash va kromka takomillashtirildi, yordam."),
     [("Панель «MES»", "«MES» paneli",
       "в левом меню пункт серый, пока интеграция выключена; включается в «Настройки → MES интеграция». Шесть разделов (обзор, заказы, результаты, склад и каталог, журнал, связь и API).",
       "chap menyuda integratsiya o'chiq paytda band xira; «Sozlamalar → MES integratsiyasi» da yoqiladi. Oltita bo'lim (umumiy ko'rinish, buyurtmalar, natijalar, ombor va katalog, jurnal, aloqa va API)."),
      ("Станки (постпроцессор)", "Stanoklar (postprotsessor)",
       "готовый список пильных и обрабатывающих центров: отметка «используется на предприятии», подключение шаблона формата, префикс имени станка в имени файла; станки видны в «Раскрой → Постпроцессор».",
       "pil va ishlov markazlarining tayyor ro'yxati: «korxonada ishlatiladi» belgisi, format shablonini ulash, fayl nomiga stanok nomi old qo'shimchasi; stanoklar «Kroy → Postprotsessor» da ko'rinadi."),
      ("Единый язык выражений", "Yagona ifoda tili",
       "типы (целое, дробное, логическое, строка, null), операторы if / xor / = / <> / ^, строки, format и now, 65 функций и константы pi, e; понятные ошибки и пределы. Проверка выражений на сервере и раздел «Справка → Выражения» с таблицей функций.",
       "turlar (butun, kasr, mantiqiy, satr, null), if / xor / = / <> / ^ operatorlari, satrlar, format va now, 65 funksiya va pi, e konstantalari; tushunarli xatolar va chegaralar. Ifodalarni serverda tekshirish va funksiyalar jadvali bilan «Yordam → Ifodalar» bo'limi."),
      ("XNC: массив отверстий и «предыдущее значение»", "XNC: teshiklar massivi va «oldingi qiymat»",
       "массив отверстий (AC / AS / AV), правило «предыдущее значение» для контура и паза, «Включить» для команд, целочисленные переменные; углы в выражениях — в радианах.",
       "teshiklar massivi (AC / AS / AV), kontur va paz uchun «oldingi qiymat» qoidasi, buyruqlar uchun «Yoqish», butun turdagi o'zgaruvchilar; ifodalarda burchaklar — radianda."),
      ("Пазование (GR)", "Pazlash (GR)",
       "в панели: толщина пилы, «Отступ включительно», длина пазования, число проходов, длина пропила и стоимость, схема W / D / O, «Сохранить параметры по умолчанию»; вкладка «Детали» с десятью колонками; раздел в настройках печати. Стандарт: 4 / 8 / 10 мм, как в формате проекта.",
       "panelda: arra qalinligi, «Masofa inklyuziv», pazlash uzunligi, o'tishlar soni, kesim uzunligi va narx, W / D / O sxemasi, «Standart qiymatlarni saqlash»; o'n ustunli «Detallar» yorlig'i; chop sozlamalarida bo'lim. Standart: 4 / 8 / 10 mm, loyiha formatidagidek."),
      ("Кромка (EL)", "Kromka (EL)",
       "значок «?» у каждого параметра открывает справку на нужном месте; в таблице «Детали»: сортировка по заголовку, Ctrl+Space — свойства детали, Home / End / ↑ / ↓ — строки.",
       "har parametr yonidagi «?» belgisi yordamni kerakli joyda ochadi; «Detallar» jadvalida: sarlavha bo'yicha saralash, Ctrl+Space — detal xossalari, Home / End / ↑ / ↓ — qatorlar."),
      ("Справка", "Yordam",
       "новые разделы: «Кромка: параметры», «Пазование», «Выражения», «Станки и постпроцессор», «Что нового»; описание панели «MES».",
       "yangi bo'limlar: «Kromka: parametrlar», «Pazlash», «Ifodalar», «Stanoklar va postprotsessor», «Yangiliklar»; «MES» paneli tavsifi."),
      ("Импорт проектов", "Loyihalarni import",
       "для операций пазования читаются отступ включительно и толщина пилы; недостающие значения берутся из формата (4 / 8 / 10 мм).",
       "pazlash operatsiyalari uchun inklyuziv masofa va arra qalinligi o'qiladi; yetishmaydigan qiymatlar formatdan olinadi (4 / 8 / 10 mm).")]),
    ("v21", ("Версия 2.1", "Versiya 2.1"), "2026-10-01",
     ("Сверка с результатами прежней программы, три независимые проверки и исправления.",
      "Avvalgi dastur natijalari bilan solishtirish, uchta mustaqil tekshiruv va tuzatishlar."),
     [("«Листы и остатки»: порядок использования", "«Listlar va qoldiqlar»: ishlatish tartibi",
       "листы используются в порядке списка — сначала ограниченные по количеству; раскрой по нескольким листам и остаткам стал заметно экономнее.",
       "listlar ro'yxat tartibida ishlatiladi — avval soni cheklanganlar; bir nechta list va qoldiqli kroy sezilarli tejamliroq bo'ldi."),
      ("Общие действия", "Umumiy amallar",
       "«Перекодировать XNC» (повторяющиеся коды программ получают -2, -3 …) и предупреждение при открытии отчёта.",
       "«XNC qayta kodlash» (takror kodli dasturlar -2, -3 … oladi) va hisobot ochilganda ogohlantirish."),
      ("Изделия → Свойства", "Mahsulotlar → Xossalar",
       "полное окно: общие данные, данные заказа, дополнительные параметры, описание, сообщения; заполняется из импорта.",
       "to'liq oyna: umumiy ma'lumotlar, buyurtma ma'lumotlari, qo'shimcha parametrlar, tavsif, xabarlar; importdan to'ldiriladi."),
      ("Сортировка", "Saralash",
       "общее окно сортировки по нескольким столбцам (операции, изделия, детали).",
       "bir nechta ustun bo'yicha umumiy saralash oynasi (operatsiyalar, mahsulotlar, detallar)."),
      ("Импорт из Excel", "Excel dan import",
       "профили импорта (сопоставление столбцов и начальная строка); улучшено автоопределение столбцов.",
       "import profillari (ustunlar moslashtirilishi va boshlang'ich qator); ustunlarni avto-aniqlash yaxshilandi."),
      ("Проверки и исправления", "Tekshiruvlar va tuzatishlar",
       "более 70 исправлений: список проектов, таблицы, диалоги, язык, настройки, история, расчёты XNC и пазования, склад остатков, отчёты, серверные проверки, MES, импорт.",
       "70 dan ortiq tuzatish: loyihalar ro'yxati, jadvallar, dialoglar, til, sozlamalar, tarix, XNC va pazlash hisoblari, qoldiqlar ombori, hisobotlar, server tekshiruvlari, MES, import."),
      ("Точность расчётов", "Hisoblar aniqligi",
       "метраж кромки совпал в 303 из 303 проверенных раскроев; отверстия — 8359 из 8360, фрезеровка и пиление — 8360 из 8360; ошибок проверки раскроя нет.",
       "kromka metri 303 ta tekshirilgan kroydan 303 tasida mos tushdi; teshiklar — 8360 dan 8359, frezalash va arralash — 8360 dan 8360; kroy tekshiruvida xato yo'q.")]),
    ("v20", ("Версия 2.0", "Versiya 2.0"), "2026-10-01",
     ("Бизнес-правила, интерфейс и сравнение на реальных проектах.", "Biznes qoidalari, interfeys va real loyihalarda solishtirish."),
     [("Бизнес-правила и интерфейс", "Biznes qoidalari va interfeys",
       "формулы кромки, размеров и стоимости, подписи интерфейса и колонок приведены к привычным сотрудникам.",
       "kromka, o'lchamlar va narx formulalari, interfeys va ustun yorliqlari xodimlar odatlangan ko'rinishga keltirildi."),
      ("Сверка на реальных проектах", "Real loyihalarda solishtirish",
       "205 проектов предприятия сравнены с результатами прежней программы.",
       "korxonaning 205 ta loyihasi avvalgi dastur natijalari bilan solishtirildi."),
      ("Оптимизатор", "Optimizator",
       "колонное размещение, добор до целого листа, сбор остатка, жёсткие сроки расчёта.",
       "ustunli joylash, butun listgacha to'ldirish, qoldiqni yig'ish, qat'iy hisoblash muddatlari.")]),
    ("v10", ("Версия 1.0", "Versiya 1.0"), "2026-09-30",
     ("Первая рабочая версия.", "Birinchi ishchi versiya."),
     [("Основа", "Asos",
       "гильотинный раскрой листовых материалов, склад деловых остатков, отчёты с QR, этикетки деталей, шаблоны постпроцессора, REST API для MES, импорт проектов, режим цеха (сканер QR), русский и узбекский интерфейс.",
       "list materiallarni gilyotina usulida kroy qilish, deloviy qoldiqlar ombori, QR li hisobotlar, detal etiketkalari, postprotsessor shablonlari, MES uchun REST API, loyihalarni import, sex rejimi (QR skaner), rus va o'zbek interfeysi.")]),
]
for _v, (_tru, _tuz), _date, (_sru, _suz), _items in _WN:
    a(f"whatsnew.{_v}.title", _tru, _tuz)
    a(f"whatsnew.{_v}.date", _date, _date)
    a(f"whatsnew.{_v}.summary", _sru, _suz)
    for _i, (_tagru, _taguz, _dru, _duz) in enumerate(_items, 1):
        a(f"whatsnew.{_v}.i{_i:02d}.t", _tagru, _taguz)
        a(f"whatsnew.{_v}.i{_i:02d}.d", _dru, _duz)
