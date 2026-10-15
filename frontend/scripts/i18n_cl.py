# -*- coding: utf-8 -*-
"""(CL) Погонажный раскрой и CLE — interfeys matnlari (W11). i18n_src.py shu faylni o'zi yuklaydi (`a` — o'sha yerdan).
Rus yorliqlari — xodimlar odatlangan atamalar; uz — to'liq o'zbekcha (lotin). Yordam matnlari (`phelp.cl_*`) — o'z so'zlarimiz."""

# ── operatsiyalar jadvali ──
a("ops.add_cl", "Добавить: (CL) Погонажный раскрой", "Qo'shish: (CL) Pogonaj kroy")
a("ops.default.CL", "Материал{{n}}", "Material{{n}}")

# ── panel: yorliqlar ──
a("cl.tab.params", "Параметры", "Parametrlar")
a("cl.tab.parts", "Детали", "Detallar")
a("cl.tab.sheets", "Полосы и остатки", "Polosalar va qoldiqlar")
a("cl.tab.cut", "Раскрой", "Kroy")
a("cl.save_default", "Сохранить текущие параметры для использования по умолчанию", "Joriy parametrlarni standart sifatida saqlash")
a("cl.apply_default", "Применить стандартные параметры (кроме ширины, толщины и цены)", "Standart parametrlarni qo'llash (eni, qalinligi va narxidan tashqari)")
a("cl.defaults_saved", "Параметры погонажного раскроя сохранены как стандартные", "Pogonaj kroy parametrlari standart sifatida saqlandi")
a("cl.params_invalidate_q", "Изменить параметр? Текущий раскрой будет удалён.", "Parametr o'zgartirilsinmi? Joriy kroy o'chiriladi.")

# ── «Параметры» ──
a("cl.p.material", "Параметры материала", "Material parametrlari")
a("cl.p.width", "Ширина", "Eni")
a("cl.p.width_hint", "Ширина полосы (профиля). Ширина каждой детали равна ширине полосы", "Polosa (profil) eni. Har bir detalning eni polosa eniga teng")
a("cl.p.thickness", "Толщина", "Qalinligi")
a("cl.p.thickness_hint", "Толщина полосы — для кратности (сколько полос режется за один проход пакета)", "Polosa qalinligi — kratnost uchun (paketda bir o'tishda nechta polosa kesiladi)")
a("cl.p.cost", "Стоимость", "Narx")
a("cl.p.price", "Цена материала", "Material narxi")
a("cl.p.per_m", "за м", "1 m uchun")
a("cl.p.per_strip", "за полосу", "1 polosa uchun")
a("cl.p.est_fill", "Расчетный процент заполнения", "Hisobiy to'ldirish foizi")
a("cl.p.est_fill_hint", "Для предварительного расчёта до раскроя: расход = сумма длин деталей × (2 − процент / 100)", "Kroydan oldingi taxmin: sarf = detallar uzunligi yig'indisi × (2 − foiz / 100)")
a("cl.p.material_qty", "Количество материала", "Material miqdori")
a("cl.p.material_qty_hint", "После раскроя: длина использованных полос минус деловые остатки", "Kroydan keyin: ishlatilgan polosalar uzunligi minus deloviy qoldiqlar")
a("cl.p.strips_qty", "Количество полос", "Polosalar soni")
a("cl.p.strips_qty_hint", "Новые полосы (остатки со склада считаются отдельно); с учётом округления, если включён расчёт по полосам", "Yangi polosalar (ombor qoldiqlari alohida); polosa bo'yicha hisob yoqilgan bo'lsa yaxlitlash bilan")
a("cl.p.by_strip", "Расчет стоимости по полосам", "Narxni polosa bo'yicha hisoblash")
a("cl.p.rounding", "Округление — Полосы", "Yaxlitlash — polosalar")
a("cl.p.cost_material", "Стоимость материала", "Material qiymati")
a("cl.p.op_base", "Расчет стоимости операции по", "Operatsiya narxini hisoblash asosi")
a("cl.p.op_price", "Цена операции", "Operatsiya narxi")
a("cl.p.op_price_hint", "Цена за единицу выбранного основания (метр реза, метр материала или метр деталей)", "Tanlangan asos birligiga narx (kesim metri, material metri yoki detallar metri)")
a("cl.p.cost_op", "Стоимость операции", "Operatsiya qiymati")
a("cl.p.waste", "Отход", "Otxod")
a("cl.p.waste_min", "Мин. размер отхода", "Min. otxod o'lchami")
a("cl.p.waste_min_hint", "Более короткий обрезок — обычный мусор, в таблицу остатков не попадает", "Bundan qisqa qirqim — oddiy chiqindi, qoldiqlar jadvaliga kirmaydi")
a("cl.p.business_min", "Длина делового отхода", "Deloviy otxod uzunligi")
a("cl.p.business_min_hint", "Остаток не короче этого — деловой: не входит в расход, записывается на склад", "Bundan kam bo'lmagan qoldiq — deloviy: sarfga kirmaydi, omborga yoziladi")
a("cl.p.trim_waste", "Торцовка отходов", "Otxodlar torsovkasi")
a("cl.p.trim_waste_hint", "☑ — длина отхода без торцовки (80), последний торцевой рез делается; ☐ — отход включает зону торцовки (110)", "☑ — otxod uzunligi torsovkasiz (80), oxirgi torsovka kesimi qilinadi; ☐ — otxod torsovka zonasini ham oladi (110)")
a("cl.p.limits", "Ограничения раскроя", "Kroy cheklovlari")
a("cl.p.min_part", "Мин. размер детали", "Min. detal o'lchami")
a("cl.p.min_part_hint", "Деталь короче этого значения в раскрой не входит (0 — без ограничения)", "Bundan qisqa detal kroyga kirmaydi (0 — cheklov yo'q)")
a("cl.round.11", "К целому", "Butungacha")
a("cl.round.32", "По длине 1/2", "Uzunlik bo'yicha 1/2")
a("cl.round.33", "По длине 1/3", "Uzunlik bo'yicha 1/3")
a("cl.round.34", "По длине 1/4", "Uzunlik bo'yicha 1/4")
a("cl.opbase.0", "Длине реза с торцовкой", "Torsovka bilan kesim uzunligi")
a("cl.opbase.1", "Длине реза без торцовки", "Torsovkasiz kesim uzunligi")
a("cl.opbase.2", "Длине материала", "Material uzunligi")
a("cl.opbase.3", "Длине деталей", "Detallar uzunligi")
a("cl.p.cut", "Параметры раскроя", "Kroy parametrlari")
a("cl.p.kerf", "Толщина пилы", "Arra qalinligi")
a("cl.p.kerf_hint", "Ширина одного пропила; в погонажном раскрое строго больше 0", "Bitta propil kengligi; pogonaj kroyda qat'iy 0 dan katta")
a("cl.p.trim", "Торцовка", "Torsovka")
a("cl.p.trim_hint", "Обрезка начала полосы (без пропила); 0 — торцовочного реза нет", "Polosa boshini kesib tashlash (propilsiz); 0 — torsovka kesimi yo'q")
a("cl.p.end_offset", "Минимальный отступ в конце", "Oxiridagi minimal otstup")
a("cl.p.end_offset_hint", "Минимальный край, остающийся в конце полосы. Пока не задан — равен торцовке", "Polosa oxirida qoladigan minimal chet. Berilmaguncha torsovkaga teng")
a("cl.p.as_trim", "как торцовка", "torsovka kabi")
a("cl.p.pack_h", "Высота пакета", "Paket balandligi")
a("cl.p.pack_hint", "Максимальная высота пилы по вертикали (для кратности)", "Arraning maksimal ko'tarilish balandligi (kratnost uchun)")
a("cl.p.mult", "Кратность", "Kratnost")
a("cl.p.mult_hint", "Сколько полос режется за один проход = ⌊высота пакета / толщина⌋ (только чтение)", "Bir o'tishda nechta polosa kesiladi = ⌊paket balandligi / qalinlik⌋ (faqat o'qish)")
a("cl.p.fill_packet", "Процент заполнения для кратности", "Kratnost uchun to'ldirish foizi")
a("cl.p.fill_packet_hint", "Не влияет на выбор карт (пока не подключён): количество пакетов считается ⌈C / кратность⌉", "Kartalarni tanlashga ta'sir qilmaydi (hozircha ulanmagan): paketlar soni ⌈C / kratnost⌉")
a("cl.p.prefs", "Предпочтения", "Afzalliklar")
a("cl.p.quality", "Качество раскроя", "Kroy sifati")
a("cl.p.note_angle", "Только прямой (90°) поперечный рез; деталь не делится и не поворачивается", "Faqat to'g'ri (90°) ko'ndalang kesim; detal bo'linmaydi va aylantirilmaydi")

# ── «Детали» ──
a("cl.col.length", "Д-на", "Uzunlik")
a("cl.col.edge_left_hint", "Оклейка кромки торца слева (ОЛ). Длина кромки = ширина полосы", "Chap uch kromkasi (ОЛ). Kromka uzunligi = polosa eni")
a("cl.col.edge_right_hint", "Оклейка кромки торца справа (ОП). Длина кромки = ширина полосы", "O'ng uch kromkasi (ОП). Kromka uzunligi = polosa eni")
a("cl.tip.saw", "Пильный размер (длина × ширина полосы)", "Arra o'lchami (uzunlik × polosa eni)")
a("cl.tip.uncomputed", "Длина не рассчитана (в файле: {{v}}) — укажите длину", "Uzunlik hisoblanmagan (faylda: {{v}}) — uzunlikni kiriting")
a("cl.paste_hint", "Вставка из Excel (Ctrl+V): столбцы Длина, Кол, ОВ, ОН, ОЛ, ОП, Наименование. Скопируйте ячейки, щёлкните в таблице и нажмите Ctrl+V",
  "Excel dan qo'yish (Ctrl+V): ustunlar Uzunlik, Soni, ОВ, ОН, ОЛ, ОП, Nomi. Katakchalarni nusxalang, jadvalni bosing va Ctrl+V")
a("cl.paste_nothing", "Нечего вставлять (нужна длина)", "Qo'yadigan ma'lumot yo'q (uzunlik kerak)")
a("cl.paste_skipped", "Пропущено строк: {{n}} (нет длины или это не число)", "O'tkazib yuborilgan qatorlar: {{n}} (uzunlik yo'q yoki son emas)")
a("cl.sort_length_asc", "По длине (возр.)", "Uzunlik (o'sish)")
a("cl.length_total", "Длина", "Uzunlik")
a("cl.uncomputed", "Не рассчитано: {{n}}", "Hisoblanmagan: {{n}}")
a("cl.uncomputed_hint", "Длина этих деталей не рассчитана (в файле — отрицательное значение). Укажите длину — они войдут в раскрой",
  "Bu detallarning uzunligi hisoblanmagan (faylda manfiy qiymat). Uzunlikni kiriting — kroyga kiradi")

# ── «Полосы и отходы» ──
a("sheets.kind.strip", "Полоса", "Polosa")
a("cl.sheets.width_hint", "Равна ширине материала (параметры); у всех полос одинаковая", "Material eniga teng (parametrlar); hamma polosada bir xil")
a("cl.sheets.hint", "Кол-во = 10000 — без ограничения. Остатки со склада раскраиваются в первую очередь; порядок строк = порядок использования.",
  "Soni = 10000 — cheklanmagan. Ombor qoldiqlari birinchi navbatda kroy qilinadi; qatorlar tartibi = ishlatish tartibi.")

# ── «Раскрой» ──
a("cl.cut.done", "Раскрой: {{n}} полос ({{m}} м), F {{fill}}% ({{s}} с)", "Kroy: {{n}} polosa ({{m}} m), F {{fill}}% ({{s}} s)")
a("cl.cut.empty_hint", "Нажмите «Раскроить» — детали будут размещены на полосах.", "«Kroy qilish» ni bosing — detallar polosalarga joylanadi.")
a("cl.cut.remnant_strip", "остаток", "qoldiq")
a("cl.ind.num", "Номер карты / всего", "Karta raqami / jami")
a("cl.ind.S", "Длина / ширина полосы", "Polosa uzunligi / eni")
a("cl.ind.C", "Количество полос на карте / всего", "Kartadagi polosalar soni / jami")
a("cl.ind.Cp", "Деталей на карте / всего", "Kartadagi detallar / jami")
a("cl.ind.LT", "Длина реза, м (резы × ширина полосы): карта / всего", "Kesim uzunligi, m (kesimlar × polosa eni): karta / jami")
a("cl.ind.F", "Заполнение, % (длина деталей / длина полосы)", "To'ldirish, % (detallar uzunligi / polosa uzunligi)")
a("cl.ind.CT", "Количество резов: карта / всего", "Kesimlar soni: karta / jami")
a("cl.ind.T", "Торцовка в начале / в конце", "Boshidagi / oxiridagi torsovka")
a("cl.ind.M", "Длина материала, м: карта / всего", "Material uzunligi, m: karta / jami")

# ── CLE ──
a("cl.ed.title", "Редактирование погонажного раскроя", "Pogonaj kroyni tahrirlash")
a("cl.ed.select_first", "Выделите деталь на карте", "Kartada detalni tanlang")
a("cl.ed.select_part", "Выберите деталь в таблице слева", "Chapdagi jadvaldan detalni tanlang")
a("cl.ed.size_hint", "Пильный размер (с учётом кромки торцов и прифуговки)", "Arra o'lchami (uchlardagi kromka va prifugovka hisobga olingan)")
a("cl.ed.h_left", "выделить деталь / поставить выбранную деталь на свободное место", "detalni tanlash / tanlangan detalni bo'sh joyga qo'yish")
a("cl.ed.h_right", "убрать деталь", "detalni olib tashlash")
a("cl.ed.h_ends", "в начало / в конец полосы", "polosa boshiga / oxiriga")
a("cl.ed.h_step", "на одну позицию", "bir pozitsiyaga")
a("cl.ed.h_transfer", "в предыдущую / следующую карту", "oldingi / keyingi kartaga")
a("cl.ed.map_up", "Карту выше", "Kartani yuqoriga")
a("cl.ed.map_down", "Карту ниже", "Kartani pastga")
a("cl.ed.step_left", "Сдвинуть влево", "Chapga surish")
a("cl.ed.step_right", "Сдвинуть вправо", "O'ngga surish")
a("cl.ed.to_prev_map", "В предыдущую карту", "Oldingi kartaga")
a("cl.ed.to_next_map", "В следующую карту", "Keyingi kartaga")
a("cl.ed.copies_hint", "Количество листов: сколько одинаковых полос режется по этой карте", "Polosalar soni: shu karta bo'yicha nechta bir xil polosa kesiladi")
a("cl.ed.trims_hint", "Торцовка листа: торцовка в начале / в конце именно этой полосы", "Torsovka: aynan shu polosaning boshi / oxiridagi torsovka")
a("cl.ed.trim", "Торцовка", "Torsovka")
a("cl.ed.dblclick", "двойной щелчок по детали в таблице", "jadvalda detalni ikki marta bosish")

a("help.hk.cl_editor_keys", "Погонажный редактор (CLE): деталь в начало / в конец (Ctrl+←/→), на одну позицию (Alt+←/→), в соседнюю карту (Shift+↑/↓)",
  "Pogonaj muharrir (CLE): detalni boshiga / oxiriga (Ctrl+←/→), bir pozitsiyaga (Alt+←/→), qo'shni kartaga (Shift+↑/↓)")

# ── «Печать отчета» ──
a("print.sec.cl", "(CL) Погонажный раскрой", "(CL) Pogonaj kroy")
a("print.f.cl_header", "Печать заголовка (параметры)", "Sarlavhani chop etish (parametrlar)")
a("print.f.cl_parts", "Печать деталей", "Detallarni chop etish")
a("print.f.cl_group_by_product", "Группировать детали по изделиям", "Detallarni mahsulotlar bo'yicha guruhlash")
a("print.f.cl_unplaced", "Печать невместившихся деталей", "Sig'magan detallarni chop etish")
a("print.f.cl_strips", "Печать полос", "Polosalarni chop etish")
a("print.f.cl_remnants", "Печать отходов", "Otxodlarni chop etish")
a("print.f.cl_maps", "Печать карт раскроев", "Kroy kartalarini chop etish")
a("print.f.cl_commands", "Таблица команд рядом с картой", "Karta yonida buyruqlar jadvali")

# ── yordam: parametr haqida (F1 / «?») ──
_H = {
    "cl_width": ("Ширина", "Eni",
                 "Ширина полосы (профиля, плинтуса, бруска). У погонажного раскроя нет отдельной ширины детали — каждая деталь имеет ширину полосы; она нужна для длины реза, кромки и площади.",
                 "Polosa (profil, plintus, bruss) eni. Pogonaj kroyda detalning alohida eni yo'q — har bir detal polosa eniga ega; u kesim uzunligi, kromka va maydon hisobi uchun kerak."),
    "cl_thickness": ("Толщина", "Qalinligi",
                     "Толщина полосы. Используется только для кратности: сколько полос пила режет за один проход (высота пакета / толщина).",
                     "Polosa qalinligi. Faqat kratnost uchun: arra bir o'tishda nechta polosa kesadi (paket balandligi / qalinlik)."),
    "cl_price": ("Цена материала", "Material narxi",
                 "Цена одного метра полосы. Если включён «Расчет стоимости по полосам» — цена одной полосы. Остатки со склада считаются по той же цене за метр.",
                 "Bir metr polosa narxi. «Narxni polosa bo'yicha hisoblash» yoqilgan bo'lsa — bitta polosa narxi. Ombor qoldiqlari ham shu 1 m narxida hisoblanadi."),
    "cl_est_fill": ("Расчетный процент заполнения", "Hisobiy to'ldirish foizi",
                    "Нужен только до раскроя: расход ≈ сумма длин деталей × (2 − процент/100). Например, 10 м деталей при 90 % → 11 м. После раскроя берутся реальные длины.",
                    "Faqat kroydan oldin kerak: sarf ≈ detallar uzunligi yig'indisi × (2 − foiz/100). Masalan, 10 m detal 90 % da → 11 m. Kroydan keyin haqiqiy uzunliklar olinadi."),
    "cl_material_qty": ("Количество материала", "Material miqdori",
                        "Расход в метрах. После раскроя: длина всех использованных полос минус деловые остатки (они уходят на склад и в расход не входят). До раскроя — оценка со знаком «≈».",
                        "Sarf metrda. Kroydan keyin: ishlatilgan barcha polosalar uzunligi minus deloviy qoldiqlar (ular omborga ketadi, sarfga kirmaydi). Kroydan oldin — «≈» belgili taxmin."),
    "cl_strips_qty": ("Количество полос", "Polosalar soni",
                      "Сколько новых полос уйдёт в раскрой. Остатки со склада учитываются отдельно. При округлении по длине последняя полоса считается долей (1/2, 1/3, 1/4).",
                      "Kroyga nechta yangi polosa ketadi. Ombor qoldiqlari alohida hisoblanadi. Uzunlik bo'yicha yaxlitlashda oxirgi polosa ulush (1/2, 1/3, 1/4) hisoblanadi."),
    "cl_by_strip": ("Расчет стоимости по полосам", "Narxni polosa bo'yicha hisoblash",
                    "Включено — стоимость материала = количество полос × цена полосы; выключено — метры × цена метра.",
                    "Yoqilgan — material qiymati = polosalar soni × polosa narxi; o'chirilgan — metrlar × 1 m narxi."),
    "cl_rounding": ("Округление — Полосы", "Yaxlitlash — polosalar",
                    "Как считать последнюю неполную полосу при расчёте по полосам: до целой или до доли длины (1/2, 1/3, 1/4). Работает только вместе с расчётом по полосам.",
                    "Polosa bo'yicha hisobda oxirgi to'lmagan polosani qanday sanash: butungacha yoki uzunlik ulushigacha (1/2, 1/3, 1/4). Faqat polosa bo'yicha hisob bilan ishlaydi."),
    "cl_cost_material": ("Стоимость материала", "Material qiymati",
                         "Цена материала × количество материала (до раскроя — оценка). Только чтение.",
                         "Material narxi × material miqdori (kroydan oldin — taxmin). Faqat o'qish."),
    "cl_op_base": ("Расчет стоимости операции по", "Operatsiya narxini hisoblash asosi",
                   "Что умножается на цену операции: длина реза с торцовкой (резы × ширина полосы), длина реза без торцовочных резов, длина материала (без деловых остатков) или суммарная длина деталей.",
                   "Operatsiya narxiga nima ko'paytiriladi: torsovka bilan kesim uzunligi (kesimlar × polosa eni), torsovka kesimlarisiz uzunlik, material uzunligi (deloviy qoldiqsiz) yoki detallar uzunligi yig'indisi."),
    "cl_op_price": ("Цена операции", "Operatsiya narxi",
                    "Цена за единицу выбранного основания (метр). Стоимость операции = основание × цена.",
                    "Tanlangan asos birligiga (metr) narx. Operatsiya qiymati = asos × narx."),
    "cl_cost_op": ("Стоимость операции", "Operatsiya qiymati",
                   "Основание × цена операции. До раскроя резов приблизительно: по два реза на деталь × ширина полосы. Только чтение.",
                   "Asos × operatsiya narxi. Kroydan oldin kesimlar taxminan: har detalga ikkitadan kesim × polosa eni. Faqat o'qish."),
    "cl_waste_min": ("Мин. размер отхода", "Min. otxod o'lchami",
                     "Остаток короче этого значения считается обычным мусором: в таблицу остатков не попадает и отдельный рез для него не делается.",
                     "Bundan qisqa qoldiq oddiy chiqindi hisoblanadi: qoldiqlar jadvaliga kirmaydi va uning uchun alohida kesim qilinmaydi."),
    "cl_business_min": ("Длина делового отхода", "Deloviy otxod uzunligi",
                        "Остаток не короче этого значения — деловой: не входит в расход материала и может быть записан на склад для повторного использования.",
                        "Bundan kam bo'lmagan qoldiq — deloviy: material sarfiga kirmaydi va qayta ishlatish uchun omborga yozilishi mumkin."),
    "cl_trim_waste": ("Торцовка отходов", "Otxodlar torsovkasi",
                      "Включено: длина отхода берётся без зоны торцовки (например 80), после отхода делается ещё один торцевой рез. Выключено: отход включает пропил и торцовку (110), последнего торцевого реза нет.",
                      "Yoqilgan: otxod uzunligi torsovka zonasisiz olinadi (masalan 80), otxoddan keyin yana bitta torsovka kesimi qilinadi. O'chirilgan: otxod propil va torsovkani ham oladi (110), oxirgi torsovka kesimi yo'q."),
    "cl_min_part": ("Мин. размер детали", "Min. detal o'lchami",
                    "Деталь короче этого значения не попадает в раскрой (появляется предупреждение). 0 — без ограничения.",
                    "Bundan qisqa detal kroyga kirmaydi (ogohlantirish chiqadi). 0 — cheklov yo'q."),
    "cl_kerf": ("Толщина пилы", "Arra qalinligi",
                "Ширина одного пропила. Между двумя соседними деталями всегда один пропил; в погонажном раскрое значение строго больше нуля.",
                "Bitta propil kengligi. Ikki qo'shni detal orasida doim bitta propil bor; pogonaj kroyda qiymat qat'iy noldan katta."),
    "cl_trim": ("Торцовка", "Torsovka",
                "Сколько срезается с начала полосы (без учёта пропила). Полезная длина = длина − (торцовка + пропил) − (отступ в конце + пропил). При 0 торцовочного реза нет.",
                "Polosa boshidan qancha kesib tashlanadi (propilsiz). Foydali uzunlik = uzunlik − (torsovka + propil) − (oxiridagi otstup + propil). 0 bo'lsa torsovka kesimi yo'q."),
    "cl_end_offset": ("Минимальный отступ в конце", "Oxiridagi minimal otstup",
                      "Минимальный край в конце полосы. Пока не задан — равен торцовке.",
                      "Polosa oxiridagi minimal chet. Berilmaguncha torsovkaga teng."),
    "cl_pack_h": ("Высота пакета", "Paket balandligi",
                  "Максимальная высота подъёма пилы: в один проход режется столько полос, сколько помещается по высоте.",
                  "Arraning maksimal ko'tarilish balandligi: bir o'tishda balandlikka sig'gancha polosa kesiladi."),
    "cl_mult": ("Кратность", "Kratnost",
                "Сколько полос режется за один проход = ⌊высота пакета / толщина⌋. Количество проходов (пакетов) на карте = ⌈количество полос / кратность⌉. Только чтение.",
                "Bir o'tishda nechta polosa kesiladi = ⌊paket balandligi / qalinlik⌋. Kartadagi o'tishlar (paketlar) soni = ⌈polosalar soni / kratnost⌉. Faqat o'qish."),
    "cl_fill_packet": ("Процент заполнения для кратности", "Kratnost uchun to'ldirish foizi",
                       "Зарезервировано: схемы с заполнением не ниже этого процента должны собираться в пакеты. В этой версии на выбор карт не влияет.",
                       "Zaxira: to'ldirilishi shu foizdan kam bo'lmagan sxemalar paketga yig'ilishi kerak. Bu versiyada kartalarni tanlashga ta'sir qilmaydi."),
    "cl_quality": ("Качество раскроя", "Kroy sifati",
                   "Быстро — минимум времени; Стандарт — сбалансированно; Максимум — дольше ищет лучшее размещение. Результат всегда одинаков при одинаковых данных.",
                   "Tez — minimal vaqt; Standart — muvozanatli; Maksimal — eng yaxshi joylashuvni uzoqroq qidiradi. Bir xil ma'lumotda natija doim bir xil."),
}
for _k, (_tru, _tuz, _hru, _huz) in _H.items():
    a(f"phelp_t.{_k}", _tru, _tuz)
    a(f"phelp.{_k}", _hru, _huz)
