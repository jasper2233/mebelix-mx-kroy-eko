# -*- coding: utf-8 -*-
"""W13 (CSE — «Редактирование раскроя»): ko'p tanlash, tahrir rejimlari (Shift, Shift+A, Shift+W), kartalar tartibi, karta
torsovkasi, detalni burish / almashtirish, saralanadigan jadval. `a(kalit, ru, uz)` — i18n_src.py ichida (exec) chaqiriladi;
shu yerdagi kalitlar mavjudlarini ustidan yozadi. Matnlar o'zimiz yozgan (boshqa dasturlarning yordam matni ko'chirilmagan)."""

# ── pastdagi maslahat qatori (mavjud kalitlar qayta yozildi) ──
a("editor.h_left", "выделить деталь или полосу; если выбрана деталь в списке — поставить её на свободное место",
  "detal yoki polosani tanlash; ro'yxatdan detal tanlangan bo'lsa — uni bo'sh joyga qo'yish")
a("editor.h_ctrl", "клик — добавить в выделение / убрать", "bosish — tanlovga qo'shish / olib tashlash")
a("editor.drag", "Рамка", "Ramka")
a("editor.h_band", "выделить всё внутри рамки (с Ctrl / Shift — добавить)", "ramka ichidagi hammasini tanlash (Ctrl / Shift — qo'shish)")
a("editor.h_shift", "режим редактирования: поставить выбранную деталь в место клика", "tahrir rejimi: tanlangan detalni bosilgan joyga qo'yish")
a("editor.h_alt", "то же с поворотом (если нет текстуры)", "xuddi shunday, aylantirib (tekstura bo'lmasa)")
a("editor.h_multi", "множественная вставка (ряд копий)", "ko'p qo'yish (nusxalar qatori)")
a("editor.h_block", "расширить блок до максимума", "blokni maksimumgacha kengaytirish")
a("editor.h_right", "удалить деталь / полосу (или всё выделенное)", "detal / polosani (yoki tanlanganlarni) o'chirish")

# ── панель инструментов ──
a("editor.pick_part_first", "Сначала выберите деталь в списке слева", "Avval chapdagi ro'yxatdan detalni tanlang")
a("editor.map_up", "Карту выше", "Kartani yuqoriga")
a("editor.map_down", "Карту ниже", "Kartani pastga")
a("editor.flip", "Повернуть деталь на 90° (если позволяют текстура и место)", "Detalni 90° burish (tekstura va joy ruxsat bersa)")
a("editor.replace", "Заменить выделенную деталь деталью, выбранной в списке", "Tanlangan detalni ro'yxatdan tanlangani bilan almashtirish")
a("editor.swap", "Поменять местами два выделенных элемента (одной полосы)", "Ikki tanlangan elementning (bitta polosadagi) o'rnini almashtirish")
a("editor.swap_two", "Выделите ровно два элемента одной полосы (Ctrl+клик)", "Bitta polosadagi aynan ikkita elementni tanlang (Ctrl+bosish)")
a("editor.select_all", "Выделить все детали карты", "Kartadagi hamma detalni tanlash")
a("editor.mode_multi", "Режим множественной вставки", "Ko'p qo'yish rejimi")
a("editor.mode_block", "Режим расширения блока", "Blokni kengaytirish rejimi")
a("editor.selected", "Выделено: {{n}}", "Tanlangan: {{n}}")

# ── список деталей ──
a("editor.sort_hint", "Клик — сортировка (по возрастанию / по убыванию / сброс)", "Bosilsa — saralash (o'sish / kamayish / bekor)")
a("editor.totals", "Итого", "Jami")

# ── Торцовка листа (карта) ──
a("editor.trim_title", "Торцовка листа", "List torsovkasi")
a("editor.trim_hint", "Значения действуют только на эту карту. Пустое поле — как в строке листа или параметрах раскроя (показано серым).",
  "Qiymatlar faqat shu kartaga tegishli. Bo'sh maydon — list qatori yoki kroy parametrlaridagidek (kulrang ko'rsatilgan).")
a("editor.trim_length", "Торцовка по длине (ТД)", "Uzunlik bo'yicha torsovka (TD)")
a("editor.trim_width", "Торцовка по ширине (ТШ)", "En bo'yicha torsovka (TSH)")
a("editor.trim_bottom", "Мин. отступ в конце — снизу", "Oxiridagi minimal otstup — pastda")
a("editor.trim_right", "Мин. отступ в конце — справа", "Oxiridagi minimal otstup — o'ngda")
a("editor.trim_zone", "Рабочая зона листа", "List foydali zonasi")
a("editor.trim_too_big", "значения слишком велики", "qiymatlar juda katta")
a("editor.trim_reset", "Как в параметрах", "Parametrlardagidek")
a("editor.trim_inherit_hint", "Пусто — значение из строки листа / параметров раскроя; снизу и справа по умолчанию равны торцовке",
  "Bo'sh — list qatori / kroy parametrlaridagi qiymat; pastda va o'ngda standart torsovkaga teng")

# ── Справка ──
a("help.hk.editor_select", "Редактор: выделить несколько (Ctrl+клик, рамка) / все детали карты (Ctrl+A)",
  "Tahrir: bir nechtasini tanlash (Ctrl+bosish, ramka) / kartadagi hamma detal (Ctrl+A)")
a("help.hk.editor_modes", "Редактор: Shift+клик — режим редактирования (поставить деталь); Shift+Ctrl/Alt — с поворотом; Shift+A — множественная вставка; Shift+W — расширить блок",
  "Tahrir: Shift+bosish — tahrir rejimi (detal qo'yish); Shift+Ctrl/Alt — aylantirib; Shift+A — ko'p qo'yish; Shift+W — blokni kengaytirish")
a("help.hk.editor_maps", "Редактор: переместить карту вверх / вниз в списке карт", "Tahrir: kartani kartalar ro'yxatida yuqoriga / pastga ko'chirish")
a("help.hk.map_comment", "Комментарий к карте", "Kartaga izoh")
a("help.hk.editor_trim", "Редактор: торцовка листа (Alt+T) / повернуть деталь (Alt+R)", "Tahrir: list torsovkasi (Alt+T) / detalni burish (Alt+R)")

a("help.text.cut", """Алгоритм: многоуровневый гильотинный раскрой (уровни = «Максимальное количество вращений»), учёт пропила, торцовки, минимальной обрезки и текстуры.
Строка статуса: № карта/всего · S размер листа · C листов/всего · Cp деталей · LT длина реза, м · F заполнение (детали ÷ (лист − деловой остаток)); набор показателей настраивается (Ctrl+P).
Таблица команд: T — торцовка, C — рез, P — рез детали, W — остаток; цифра — уровень.
Редактор: выберите деталь в списке и щёлкните по свободному (серому) месту — деталь встанет в угол. Клик — выделить деталь или полосу, Ctrl+клик и рамка мышью — выделить несколько (их можно удалить, перенести, клонировать вместе; Ctrl+A — все детали карты). Shift+клик — режим редактирования: поставить выбранную деталь в место клика (с Ctrl/Alt — с поворотом); Shift+A+клик — поставить столько копий, сколько поместится и осталось; Shift+W+клик — расширить блок («Группировка в блок») до максимума, раздвинув полосу. Правая кнопка — удалить (всё выделенное). Ctrl+↑ / Ctrl+↓ — переместить карту в списке; Alt+T — торцовка этой карты; F2 — комментарий; Alt+R — повернуть деталь; кнопки «заменить деталь» и «поменять местами» работают в пределах той же полосы.
Каждое действие проверяется: наложение, пропил, уровни резов, минимальная обрезка, число деталей и листов; остатки пересчитываются.""",
  """Algoritm: ko'p darajali gilyotina kroy (darajalar = «Maksimal aylanishlar soni»), propil, torsovka, minimal qirqim va tekstura hisobga olinadi.
Holat qatori: № karta/jami · S list o'lchami · C listlar · Cp detallar · LT kesish uzunligi, m · F to'ldirish (detallar ÷ (list − deloviy qoldiq)); ko'rsatkichlar to'plami sozlanadi (Ctrl+P).
Buyruqlar: T — torsovka, C — kesim, P — detal kesimi, W — qoldiq; raqam — daraja.
Tahrir: ro'yxatdan detalni tanlab, bo'sh (kulrang) joyni bosing — detal burchakka qo'yiladi. Bosish — detal yoki polosani tanlash, Ctrl+bosish va sichqoncha ramkasi — bir nechtasini tanlash (ularni birga o'chirish, ko'chirish, nusxalash mumkin; Ctrl+A — kartadagi hamma detal). Shift+bosish — tahrir rejimi: tanlangan detalni bosilgan joyga qo'yish (Ctrl/Alt bilan — aylantirib); Shift+A+bosish — sig'adigan va qolgan soncha nusxa qo'yish; Shift+W+bosish — blokni («Группировка в блок») polosani kengaytirib maksimumgacha to'ldirish. O'ng tugma — o'chirish (tanlanganlarning hammasi). Ctrl+↑ / Ctrl+↓ — kartani ro'yxatda ko'chirish; Alt+T — shu kartaning torsovkasi; F2 — izoh; Alt+R — detalni burish; «detalni almashtirish» va «o'rin almashtirish» tugmalari bitta polosa doirasida ishlaydi.
Har amal tekshiriladi: ustma-ust, propil, kesish darajalari, minimal qirqim, detal va list soni; qoldiqlar qayta hisoblanadi.""")
