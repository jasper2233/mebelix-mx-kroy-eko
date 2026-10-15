# -*- coding: utf-8 -*-
"""W2 (CS bo'shliqlari): parametr yordami («?» / F1), halol «ishlamaydi» belgilari, miqdorlar, qoldiq «Исп. кол-во» va rezerv,
yorliqlar, chop sozlamalari. `a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi; shu yerdagi kalitlar mavjudlarini ustidan yozadi.
Matnlar o'zimiz yozgan (boshqa dasturlarning yordam matni ko'chirilmagan)."""

# ── Parametr yordami (CS-048): phelp.<kalit> — kalit Field `help` bilan bir xil ──
a("phelp.open", "Справка по параметру", "Parametr haqida yordam")
a("phelp.open_help", "Общая справка", "Umumiy yordam")
a("phelp.none", "Для этого параметра справка ещё не написана.", "Bu parametr uchun yordam hali yozilmagan.")

_PH_CS = {
 "thickness": ("Толщина плиты, мм. По ней считается кратность пакета (высота пакета ÷ толщина), а также толщина материала в отчётах и программах для ЧПУ.",
               "Plita qalinligi, mm. Paket karraligi (paket balandligi ÷ qalinlik) hamda hisobot va CNC dasturlardagi material qalinligi shundan olinadi."),
 "price": ("Цена материала. Если включено «Расчет стоимости по листам» — цена одного листа, иначе — цена 1 м². Остатки со склада всегда считаются по площади.",
           "Material narxi. «Narxni listlar bo'yicha hisoblash» yoqilgan bo'lsa — 1 list narxi, aks holda 1 m² narxi. Ombor qoldiqlari doim maydon bo'yicha hisoblanadi."),
 "est_fill": ("Ожидаемый процент заполнения листа. Нужен только для оценки расхода ДО раскроя: расход = площадь деталей × (2 − процент / 100). После раскроя берётся реальный результат.",
              "Listning kutilgan to'ldirilish foizi. Faqat kroygacha sarfni baholash uchun: sarf = detallar maydoni × (2 − foiz / 100). Kroydan keyin haqiqiy natija olinadi."),
 "material_qty": ("Расход материала. До раскроя — ориентировочный (отмечен «≈»), после раскроя — по результату (площадь листов минус деловые остатки). При «по листам» — в листах с учётом округления, иначе — в м².",
                  "Material sarfi. Kroygacha — taxminiy («≈» belgisi), kroydan keyin — natija bo'yicha (listlar maydoni − deloviy qoldiqlar). «Listlar bo'yicha» yoqilgan bo'lsa — yaxlitlash bilan listlarda, aks holda m² da."),
 "sheets_qty": ("Сколько листов нужно взять со склада целиком: до раскроя — оценка (≈), после раскроя — фактическое число листов в картах.",
                "Ombordan butun holda nechta list olish kerak: kroygacha — baho (≈), kroydan keyin — kartalardagi haqiqiy listlar soni."),
 "cost_by_sheets": ("Включено — цена материала задана за лист, стоимость = листы × цена. Выключено — цена за 1 м², стоимость = расход (м²) × цена.",
                    "Yoqilgan — material narxi 1 list uchun, qiymat = listlar × narx. O'chirilgan — narx 1 m² uchun, qiymat = sarf (m²) × narx."),
 "rounding": ("Как округлять расход листов в стоимости: до целого листа или последний неполный лист — до 1/2, 1/3, 1/4 (по длине, по ширине или в любом направлении).",
              "Narxda list sarfini qanday yaxlitlash: butun listgacha yoki oxirgi to'liq bo'lmagan list — 1/2, 1/3, 1/4 gacha (uzunlik, en yoki istalgan yo'nalishda)."),
 "cost_material": ("Стоимость материала = количество × цена; складские остатки считаются по площади. Только для чтения.",
                   "Material qiymati = miqdor × narx; ombor qoldiqlari maydon bo'yicha hisoblanadi. Faqat o'qish uchun."),
 "op_base": ("От чего считать стоимость раскроя: длина реза, периметр деталей, площадь деталей или площадь материала (без деловых остатков).",
             "Kroy ish narxi nimadan hisoblanadi: kesish uzunligi, detallar perimetri, detallar maydoni yoki material maydoni (deloviy qoldiqsiz)."),
 "op_price": ("Цена единицы работы выбранной основы (за метр реза или периметра, либо за м²).",
              "Tanlangan asosdagi ish birligi narxi (kesim yoki perimetr metriga, yoki m² ga)."),
 "cost_op": ("Стоимость операции = база × цена операции. Только для чтения.", "Operatsiya narxi = asos × ish narxi. Faqat o'qish uchun."),
 "rem1": ("Кусок листа считается остатком, если одна его сторона не меньше первого значения, а вторая — не меньше второго. Меньшие куски — отходы.",
          "List bo'lagi — bir tomoni birinchi qiymatdan, ikkinchisi ikkinchi qiymatdan kam bo'lmasa — qoldiq hisoblanadi. Kichiklari — chiqindi."),
 "rem2": ("Кусок листа считается остатком, если одна его сторона не меньше первого значения, а вторая — не меньше второго. Меньшие куски — отходы.",
          "List bo'lagi — bir tomoni birinchi qiymatdan, ikkinchisi ikkinchi qiymatdan kam bo'lmasa — qoldiq hisoblanadi. Kichiklari — chiqindi."),
 "rem_area": ("Остаток с площадью не меньше этого значения — деловой: его площадь не входит в расход материала, его можно записать на склад.",
              "Maydoni bu qiymatdan kam bo'lmagan qoldiq — deloviy: uning maydoni material sarfiga kirmaydi, omborga yozish mumkin."),
 "rem_trim": ("Считать размер остатка с учётом торцовки (по полезной зоне листа) или до самого края листа.",
              "Qoldiq o'lchamini torsovkani hisobga olib (list foydali zonasi bo'yicha) yoki list chetigacha hisoblash."),
 "min_part": ("Деталь, у которой меньшая сторона (пильный размер) меньше этого значения, в раскрой не попадает: появится предупреждение, деталь окажется среди невместившихся. Мелкие детали безопаснее сгруппировать в блок. Поведение других программ в этом месте уточняется.",
              "Kichik tomoni (arra o'lchami) bu qiymatdan kichik detal kroyga kirmaydi: ogohlantirish chiqadi, detal sig'magan detallar orasida bo'ladi. Kichik detallarni blokka guruhlash xavfsizroq. Boshqa dasturlardagi xulq bu joyda tekshirilmoqda."),
 "kerf": ("Толщина пропила пилы — расстояние между соседними резами. Учитывается между всеми деталями и остатками.",
          "Arra qalinligi — qo'shni kesimlar orasidagi masofa. Barcha detallar va qoldiqlar orasida hisobga olinadi."),
 "kerf_group": ("Пропил для деталей, сгруппированных в блок. Пусто — как основной пропил.", "Blokka guruhlangan detallar uchun propil. Bo'sh — asosiy propil bilan bir xil."),
 "trim_l": ("Торцовка по длине: срез вдоль длины листа с верхней стороны (уменьшает полезную ширину листа). Значение не включает пропил.",
            "Uzunlik bo'yicha torsovka: list uzunligi bo'ylab yuqori tomondan kesim (listning foydali enini kamaytiradi). Qiymat propilni o'z ichiga olmaydi."),
 "trim_w": ("Торцовка по ширине: срез вдоль ширины листа с левой стороны (уменьшает полезную длину листа). Значение не включает пропил.",
            "En bo'yicha torsovka: list eni bo'ylab chap tomondan kesim (listning foydali uzunligini kamaytiradi). Qiymat propilni o'z ichiga olmaydi."),
 "trim_kerf": ("Если включено, заданная торцовка уже содержит толщину пропила, и пропил к ней не добавляется.",
               "Yoqilgan bo'lsa, torsovka propil qalinligini o'z ichiga oladi va unga propil qo'shilmaydi."),
 "end_offset": ("Минимальный отступ снизу и справа по умолчанию равен торцовке; можно задать отдельно (0 — без реза). К значению добавляется пропил.",
                "Past va o'ngdagi minimal otstup standart bo'yicha torsovkaga teng; alohida berish mumkin (0 — kesimsiz). Qiymatga propil qo'shiladi."),
 "first_cut": ("Направление первых резов листа. «Любое» — программа выбирает лучший вариант; «предпочтительно» применяется только к картам с заполнением ниже порога пакета.",
               "List birinchi kesimlari yo'nalishi. «Istalgan» — dastur eng yaxshisini tanlaydi; «afzali» faqat to'ldirilishi paket chegarasidan past kartalarda qo'llanadi."),
 "use_grain": ("Учитывать текстуру: детали с отметкой «Ткт» не поворачиваются. Для материала без текстуры выключите — тогда любая деталь может быть повёрнута.",
               "Teksturani hisobga olish: «Ткт» belgili detallar aylantirilmaydi. Teksturasiz material uchun o'chiring — u holda istalgan detal aylantirilishi mumkin."),
 "complex": ("Сложные полосы могут начинаться с нескольких деталей и обычно дают лучшее заполнение. Если выключено — только простые полосы (одна деталь в начале).",
             "Murakkab polosalar bir necha detaldan boshlanishi mumkin va odatda yaxshiroq to'ldiradi. O'chiq bo'lsa — faqat oddiy polosalar (boshida bitta detal)."),
 "max_rot": ("Максимальное число уровней резов (вращений листа на станке). Чем больше, тем лучше раскрой, но не все станки позволяют больше 4.",
             "Kesim darajalari (stanokda list aylantirishlar) maksimal soni. Ko'p bo'lsa kroy yaxshiroq, lekin hamma stanok 4 dan ko'pini ruxsat etmaydi."),
 "pack_h": ("Максимальная высота подъёма пилы: определяет, сколько листов режется за один раз.", "Arraning maksimal ko'tarilish balandligi: bir martada nechta list kesilishini belgilaydi."),
 "mult": ("Кратность = высота пакета ÷ толщина материала (целая часть): сколько листов пакета режется одной картой. Только для чтения.",
          "Karralik = paket balandligi ÷ material qalinligi (butun qism): bir karta bilan paketdagi nechta list kesiladi. Faqat o'qish uchun."),
 "fill_packet": ("Если карта заполнена не ниже этого процента, программа старается повторить её на нескольких листах (резка пакетом).",
                 "Karta shu foizdan kam bo'lmagan to'ldirilsa, dastur uni bir necha listda takrorlashga harakat qiladi (paketda kesish)."),
 "max_types": ("Ограничение числа разных деталей на одной карте (удобно оператору). «Не ограничено» — без ограничения.",
               "Bir kartadagi turli detallar sonini cheklash (operatorga qulay). «Cheklanmagan» — cheklovsiz."),
 "big_pack": ("При равном числе листов выбирать раскрой с меньшим числом разных карт (больше одинаковых листов в пакете).",
              "Listlar soni teng bo'lsa, kamroq turli kartali kroyni tanlash (paketda ko'proq bir xil list)."),
 "quality": ("Время поиска раскроя: «Быстро» ≈ 1 с, «Стандарт» ≈ 1–4 с, «Максимум» — до 15 с (лучше на сложных заказах).",
             "Kroy qidirish vaqti: «Tez» ≈ 1 s, «Standart» ≈ 1–4 s, «Maksimal» — 15 s gacha (murakkab buyurtmalarda yaxshiroq)."),
 "sort_strips": ("Порядок полос на готовой карте: по убыванию, по возрастанию или узкие в центр (снижает перекос материала).",
                 "Tayyor kartada polosalar tartibi: kamayish, o'sish yoki torlari markazga (materialdagi kuchlanishni kamaytiradi)."),
 "sort_in": ("Порядок деталей внутри полосы — теми же способами.", "Polosa ichidagi detallar tartibi — shu usullar bilan."),
 "min_strip": ("Самая узкая полоса, которую удерживают зажимы станка; более узких программа не создаёт. 0 — без ограничения.",
               "Stanok qisqichlari ushlay oladigan eng tor polosa; bundan torini dastur yaratmaydi. 0 — cheklovsiz."),
 "max_strip": ("Верхняя граница ширины полосы. 0 — без ограничения.",
               "Polosa eni yuqori chegarasi. 0 — cheklovsiz."),
 "max_strip_len": ("Если полоса не помещается в станок по длине, программа поворачивает её узкой стороной (меняет направление первого реза).",
                   "Polosa stanokka uzunligi bo'yicha sig'masa, dastur uni tor tomoni bilan buradi (birinchi kesim yo'nalishi almashadi)."),
 "min_trim": ("Запрещает слишком узкие обрезки, которые трудно выполнить станком. Проверяется так: остаток + пропил не меньше этого значения. Лучше задавать больше толщины пропила.",
              "Stanok uchun qiyin bo'lgan juda tor qirqimlarni taqiqlaydi. Tekshiruv: qoldiq + propil bu qiymatdan kam emas. Propil qalinligidan katta qo'ygan ma'qul."),
 "merge": ("Флажок сохраняется в проекте; на результат раскроя сейчас не влияет.",
           "Katakcha loyihada saqlanadi; hozircha kroy natijasiga ta'sir qilmaydi."),
 "save_draw": ("Карты раскроя всегда сохраняются вместе с проектом.",
               "Kroy kartalari doim loyiha bilan saqlanadi."),
 "allowance": ("Припуск на обработку заготовки: добавляется с каждой стороны ко всем деталям (пильный размер = заготовка + припуск). Отдельный припуск детали задаётся в её свойствах. На карте припуск показан пунктиром.",
               "Zagotovka ishlov pripuski: barcha detallarga har tomondan qo'shiladi (arra o'lchami = zagotovka + pripusk). Alohida detal pripuski uning xossalarida beriladi. Kartada pripusk punktir bilan ko'rsatiladi."),
}
for _k, (_ru, _uz) in _PH_CS.items():
    a(f"phelp.{_k}", _ru, _uz)

# ── Halol belgilar (CS-020/021/022): optimizatorga ulanmagan sozlamalar ──
a("cs.p.merge_note", "на раскрой не влияет", "kroyga ta'sir qilmaydi")
a("cs.p.merge_hint", "Флажок сохраняется в проекте; на результат раскроя сейчас не влияет",
  "Katakcha loyihada saqlanadi; hozircha kroy natijasiga ta'sir qilmaydi")
a("cs.p.group_props", "Группировка деталей по свойствам", "Detallarni xossalar bo'yicha guruhlash")
a("cs.p.group_props_note", "доступно вместе с «Объединением деталей»", "«Detallarni birlashtirish» bilan birga")
a("cs.p.save_draw_note", "карты всегда сохраняются", "kartalar doim saqlanadi")
a("cs.p.save_draw_hint", "Карты раскроя всегда сохраняются вместе с проектом",
  "Kroy kartalari doim loyiha bilan saqlanadi")
a("cs.p.max_strip_hint", "0 — без ограничения", "0 — cheklovsiz")

# ── Kroygacha va kroydan keyin miqdorlar (CS-036/037) ──
a("cs.p.sheets_qty", "Количество листов", "List soni")
a("cs.p.estimated_hint", "≈ — предварительная оценка до раскроя", "≈ — kroygacha taxminiy baho")
a("cs.p.material_qty_hint", "До раскроя — оценка (≈): площадь деталей × (2 − % / 100). После раскроя: листы (или м² — площадь листов минус деловые остатки)",
  "Kroygacha — baho (≈): detallar maydoni × (2 − % / 100). Kroydan keyin: listlar (yoki m² — listlar maydoni minus deloviy qoldiqlar)")
a("cs.p.sheets_qty_hint", "До раскроя — оценка (≈), после раскроя — число листов в картах", "Kroygacha — baho (≈), kroydan keyin — kartalardagi listlar soni")

# ── Листы и остатки: «Исп. кол-во» (qoldiq) va rezerv ──
a("sheets.taken_hint", "Для остатков: сколько кусков забирает заказчик — они не записываются на склад (по умолчанию 0: записываются все). Остаток = Количество − Исп.",
  "Qoldiqlar uchun: mijoz nechta bo'lak olib ketadi — ular omborga yozilmaydi (standart 0: hammasi yoziladi). Qoldi = Soni − Ishl.")
a("sheets.taken_locked", "Остатки уже записаны на склад — сначала отмените запись", "Qoldiqlar omborga yozilgan — avval yozuvni bekor qiling")
a("rem.taken_note", "Забирает заказчик (не записывается на склад): {{n}}", "Mijoz olib ketadi (omborga yozilmaydi): {{n}}")
a("rem.opt_small", "Записывать мелкие (неделовые) остатки", "Mayda (deloviy bo'lmagan) qoldiqlarni yozish")
a("rem.opt_whole", "Записывать целые листы", "Butun listlarni yozish")
a("rem.opt_pending", "На склад записываются только деловые остатки.",
  "Omborga faqat deloviy qoldiqlar yoziladi.")
a("rem.reserved", "Резерв", "Rezerv")
a("rem.reserved_by", "проект №{{n}}", "№{{n}} loyiha")
a("rem.reserved_mine", "этот проект", "shu loyiha")
a("rem.release", "Снять резерв", "Rezervni bo'shatish")
a("rem.release_q", "Снять резерв с выбранных остатков? Проект, который их выбрал, не сможет списать их со склада, пока не выберет заново.",
  "Tanlangan qoldiqlar rezervi bo'shatilsinmi? Ularni tanlagan loyiha qayta tanlamaguncha ombordan chiqim qila olmaydi.")
a("rem.released", "Резерв снят: {{n}}", "Rezerv bo'shatildi: {{n}}")
a("rem.reserved_hint", "Остатки, зарезервированные другим проектом, выбрать нельзя. Резерв снимается, когда остаток убран из «Листы и остатки» или проект удалён.",
  "Boshqa loyiha band qilgan qoldiqlarni tanlab bo'lmaydi. Qoldiq «Listlar va qoldiqlar» dan olib tashlansa yoki loyiha o'chsa — rezerv bo'shaydi.")
a("sheets.reserved_row", "Зарезервирован этим проектом", "Shu loyiha band qilgan")

# ── Yorliqlar, tahrir, o'lcham qatorlari ──
a("editor.fullscreen", "Полный экран", "To'liq ekran")
a("editor.col.grain", "Ткт", "Tkt")
a("editor.size_hint", "Размеры — заготовка + припуск (как на карте)", "O'lchamlar — zagotovka + pripusk (kartadagidek)")
a("pp.delta_hint", "▽ △ ▷ ◁ — изменение стороны относительно строки выше: − толщина кромки, + ширина прифуговки, + припуск (в строке «пильный» вводится вручную)",
  "▽ △ ▷ ◁ — tomon o'zgarishi yuqoridagi qatorga nisbatan: − kromka qalinligi, + prifugovka eni, + pripusk («arra» qatorida qo'lda kiritiladi)")
a("pp.ma_note", "Общий припуск на обработку (параметры раскроя): {{mm}} мм с каждой стороны", "Umumiy ishlov pripuski (kroy parametrlari): har tomondan {{mm}} mm")
a("sizemode.suggest_hint", "Таблица деталей пуста — выберите режим ввода размеров (позже его можно сменить). Отключить предложение: Настройки → Режим ввода деталей → «Не предлагать».",
  "Detallar jadvali bo'sh — o'lcham kiritish rejimini tanlang (keyin o'zgartirish mumkin). Taklifni o'chirish: Sozlamalar → Detal kiritish rejimi → «Taklif qilmaslik».")
a("help.hk.cell_nav", "Таблицы: Tab/Enter — вправо; Shift+Tab/Shift+Enter — влево; Ctrl+Tab/Ctrl+Enter — вниз к первой ячейке (в конце — новая строка)",
  "Jadvallar: Tab/Enter — o'ngga; Shift+Tab/Shift+Enter — chapga; Ctrl+Tab/Ctrl+Enter — pastga birinchi katakka (oxirida — yangi qator)")
a("help.hk.fullscreen", "Редактор раскроя: полный экран (F9)", "Kroy tahrirlash oynasi: to'liq ekran (F9)")
a("help.hk.help", "Справка (в параметрах раскроя — по параметру в фокусе)", "Yordam (kroy parametrlarida — fokusdagi parametr bo'yicha)")

# ── Печать: CS qo'shimcha sozlamalar (CS-161/163/164/169/170/174–177) ──
a("print.f.cs_title", "Печать заголовка", "Sarlavha")
a("print.f.cs_group_by_product", "Группировать детали по изделиям", "Detallarni mahsulotlar bo'yicha guruhlash")
a("print.f.cs_edge_highlight", "Выделять в колонке кромкования", "Kromka ustunini ajratib ko'rsatish")
a("print.f.map_orientation", "Макет карт раскроя", "Kroy kartalari maketi")
a("print.orient.portrait", "Книжная", "Kitob (tik)")
a("print.orient.landscape", "Альбомная", "Albom (yotiq)")
a("print.f.map_part_marks", "Маркеры обработки на деталях (= * %)", "Detallarda ishlov belgilari (= * %)")
a("print.f.map_allowance", "Припуск пунктиром на деталях", "Detallarda pripusk punktir bilan")
a("print.f.map_num", "Номер детали", "Detal raqami")
a("print.f.map_dim", "Размеры", "O'lchamlar")
a("print.f.font_size", "Шрифт, pt (0 — авто)", "Shrift, pt (0 — avto)")
a("print.f.bold", "Жирный", "Qalin")
a("print.f.map_dim_rotate", "Разворачивать шрифты (вертикальный размер вдоль стороны)", "Yozuvlarni burish (vertikal o'lcham tomon bo'ylab)")
a("print.f.map_part_fill", "Заливка панели", "Detal to'ldirishi")
a("print.f.map_waste_fill", "Заливка отходов", "Chiqindi to'ldirishi")
a("print.f.hatch", "Штриховка", "Shtrixlash")
for _k, _ru, _uz in [("none", "Нет", "Yo'q"), ("diag", "Диагональная", "Diagonal"), ("cross", "Сетка", "To'r"),
                     ("horizontal", "Горизонтальная", "Gorizontal"), ("vertical", "Вертикальная", "Vertikal")]:
    a(f"print.hatch.{_k}", _ru, _uz)
a("print.group.cs_maps_style", "Оформление карт", "Kartalar ko'rinishi")
a("print.group.cs_parts", "Таблица деталей", "Detallar jadvali")
a("print.orient_hint", "«Альбомная»: карты печатаются на горизонтальных страницах A4 (в окне предпросмотра макет показан как есть)",
  "«Albom»: kartalar gorizontal A4 sahifalarda chop etiladi (ko'rish oynasida maket o'zgarishsiz ko'rsatiladi)")
