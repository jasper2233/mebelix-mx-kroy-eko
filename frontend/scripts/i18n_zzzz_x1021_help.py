# -*- coding: utf-8 -*-
# 2026-10-21: «Справка» — yangi mavzular (kroy tahriri, CL, O, etiketkalar, qoldiqlar ombori). Matnlar MX uchun o'zimizniki;
# tugma va kombinatsiyalar xodimlar o'rgangan joylashuvdagidek. i18n_src.py tomonidan exec qilinadi.
a("help.topic.editor", "Редактирование раскроя: клавиши и мышь", "Kroyni tahrirlash: tugmalar va sichqoncha")
a("help.topic.cl", "(CL) Погонажный раскрой", "(CL) Pogonaj kroy")
a("help.topic.o", "(O) Комплектация", "(O) Komplektatsiya")
a("help.topic.lb", "(LB) Этикетки и шаблоны", "(LB) Etiketkalar va shablonlar")
a("help.topic.remnants", "Склад остатков", "Qoldiqlar ombori")

a("help.text.editor",
  """Окно «Редактирование раскроя» (вкладка «Раскрой» → кнопка редактирования). Изменения проверяются сервером: пропил, уровни резов, минимальная обрезка, количество деталей и листов. «Ок» — сохранить, «Отмена» — выйти без изменений.

Мышь
• Клик — выделить деталь или полосу (клик по свободному месту выделяет его полосу).
• Ctrl+клик — добавить в выделение / убрать; рамка мышью — выделить всё внутри.
• Правая кнопка — удалить деталь или полосу (если она в выделении — всё выделенное). После удаления карта уплотняется к выбранному углу.
• Shift+клик — режим редактирования: деталь из списка ставится в место клика (встаёт по линии реза).
• Shift+Ctrl или Shift+Alt (удерживать) + клик — то же с поворотом детали (если нет текстуры).
• Shift+A+клик — поставить столько копий, сколько поместится и осталось.
• Shift+W+клик — для деталей с группировкой в блок: расширить блок до максимума.
• Shift+перетаскивание — перенести деталь карты на свободное место.

Клавиши
• Ctrl+Z / Ctrl+Y — отменить / вернуть.
• Ctrl+← / Ctrl+→ — переместить выделенное на одну позицию к началу / к концу полосы.
• Ctrl+C — клонировать полосу или деталь в свободное место этой полосы.
• Ctrl+R — развернуть резы: детали остаются на месте, меняется направление первого реза (без выделения — весь лист). Если на месте нельзя — программа предложит перекроить область.
• Ctrl+Q — расширить полосу за счёт следующего свободного места.
• Del — удалить выделенное. Ctrl+F — показать только детали с остатком.
• Ctrl+↑ / Ctrl+↓ — переместить карту в списке; Home / ↑ / ↓ / End — первая / предыдущая / следующая / последняя карта.
• Alt+T — торцовка этой карты; F2 — комментарий; F9 — полный экран; Ctrl+Enter — «Ок».

Кнопки
Добавить / удалить карту, количество листов, торцовка, в начало / в конец, клонировать, развернуть резы, расширить полосу, удалить, фильтр, карта вверх / вниз. «Таблица команд» над списком карт показывает команды пилы (Кд, Р, К, Д).
Дополнительно в MebeliX: угол уплотнения для листа, автоматическая постановка, поворот / замена / обмен деталей, выделить все.

«До кроить» (вкладка «Раскрой»): детали, не вошедшие в раскрой, ставятся в свободные места готовых карт (разложенные детали остаются на месте), остальные — на новые листы. Можно выбрать «только на новые листы».""",
  """«Kroyni tahrirlash» oynasi («Kroy» varag'i → tahrirlash tugmasi). Har o'zgarish serverda tekshiriladi: propil, kesim darajalari, minimal obrezka, detal va listlar soni. «Ok» — saqlash, «Bekor qilish» — o'zgarishsiz chiqish.

Sichqoncha
• Bosish — detal yoki polosani tanlash (bo'sh joy bosilsa — uning polosasi).
• Ctrl+bosish — tanlovga qo'shish / olib tashlash; sichqoncha bilan ramka — ichidagilarning hammasi.
• O'ng tugma — detal yoki polosani o'chirish (tanlov ichida bo'lsa — butun tanlov). O'chirilgach karta tanlangan burchakka zichlanadi.
• Shift+bosish — tahrir rejimi: ro'yxatdagi detal bosilgan joyga qo'yiladi (kesish chizig'iga tekislanadi).
• Shift+Ctrl yoki Shift+Alt (bosib turiladi) + bosish — xuddi shunday, detal aylantirilgan (tekstura bo'lmasa).
• Shift+A+bosish — sig'adigan va qolgan miqdorcha nusxa qo'yish.
• Shift+W+bosish — blokka guruhlangan detallar: blokni eng ko'p songacha kengaytirish.
• Shift+sudrash — kartadagi detalni bo'sh joyga ko'chirish.

Tugmalar
• Ctrl+Z / Ctrl+Y — bekor qilish / qaytarish.
• Ctrl+← / Ctrl+→ — tanlanganni polosa boshiga / oxiriga bir qadam surish.
• Ctrl+C — polosa yoki detalni shu polosadagi bo'sh joyga nusxalash.
• Ctrl+R — kesish yo'nalishini almashtirish: detallar joyida, birinchi kesim yo'nalishi almashadi (tanlanmasa — butun list). Joyida bo'lmasa — dastur hududni qayta kesishni taklif qiladi.
• Ctrl+Q — polosani keyingi bo'sh joy hisobiga kengaytirish.
• Del — tanlanganni o'chirish. Ctrl+F — faqat qoldig'i bor detallar.
• Ctrl+↑ / Ctrl+↓ — kartani ro'yxatda ko'chirish; Home / ↑ / ↓ / End — birinchi / oldingi / keyingi / oxirgi karta.
• Alt+T — shu karta torsovkasi; F2 — izoh; F9 — to'liq ekran; Ctrl+Enter — «Ok».

Asboblar
Karta qo'shish / o'chirish, listlar soni, torsovka, boshiga / oxiriga, nusxalash, kesish yo'nalishi, polosani kengaytirish, o'chirish, filtr, kartani yuqoriga / pastga. Kartalar ro'yxati ustidagi «Buyruqlar jadvali» — arra buyruqlari (Kd, R, K, D).
MebeliX qo'shimchalari: list uchun zichlash burchagi, avtomatik joylash, detalni burish / almashtirish / o'rin almashtirish, hammasini tanlash.

«Qolgan detallarni kroy qilish» («Kroy» varag'i): kroyga kirmagan detallar tayyor kartalarning bo'sh joylariga qo'yiladi (joylanganlar o'z joyida), qolganlari — yangi listlarga. «Faqat yangi listlarga» ni tanlash mumkin.""")

a("help.text.cl",
  """(CL) Погонажный раскрой — раскрой профиля, кромки, столешниц и других длинномеров на хлысты.
Параметры: ширина и толщина материала, пропил, торцовка и минимальный отступ в конце, высота пакета и кратность, процент заполнения для кратности, минимальные размеры отхода и делового остатка, цена материала и способ расчёта стоимости операции.
Детали: длина, количество, кромки, наименование; Ctrl+Space — свойства, Space — смена кромки, Ctrl+PgUp / Ctrl+PgDn — вставить / добавить строку, Del — удалить, Ctrl+↑↓ — переместить, Tab/Enter — вправо, Ctrl+Tab/Ctrl+Enter — вниз (в конце — новая строка), Home / End — первая / последняя строка, Ctrl+V — вставка из Excel.
Полосы и остатки: длины хлыстов и их количество; используемые остатки из склада.
Раскрой: «Раскроить», «До кроить», постпроцессор, таблица команд; редактор: Ctrl+клик — несколько деталей, Shift+A+клик — несколько копий, Ctrl+←/→ — в начало / в конец, Alt+←/→ — на шаг, Shift+↑/↓ — на соседнюю карту, Del / правая кнопка — удалить, Ctrl+F — фильтр, F9 — полный экран.""",
  """(CL) Pogonaj kroy — profil, kromka, stoleshnitsa va boshqa uzun materiallarni xlistlarga kesish.
Parametrlar: material eni va qalinligi, propil, torsovka va oxirdagi minimal otstup, paket balandligi va karrali, karrali uchun to'ldirish foizi, chiqindi va deloviy qoldiqning minimal o'lchamlari, material narxi va operatsiya narxini hisoblash usuli.
Detallar: uzunlik, soni, kromkalar, nomi; Ctrl+Space — xossalar, Space — kromkani almashtirish, Ctrl+PgUp / Ctrl+PgDn — qator qo'shish, Del — o'chirish, Ctrl+↑↓ — ko'chirish, Tab/Enter — o'ngga, Ctrl+Tab/Ctrl+Enter — pastga (oxirida yangi qator), Home / End — birinchi / oxirgi qator, Ctrl+V — Excel'dan qo'yish.
Polosalar va qoldiqlar: xlist uzunliklari va soni; ombordagi qoldiqlar.
Kroy: «Kroy qilish», «Qolgan detallarni kroy qilish», postprotsessor, buyruqlar jadvali; tahrir: Ctrl+bosish — bir nechta detal, Shift+A+bosish — bir nechta nusxa, Ctrl+←/→ — boshiga / oxiriga, Alt+←/→ — bir qadam, Shift+↑/↓ — qo'shni kartaga, Del / o'ng tugma — o'chirish, Ctrl+F — filtr, F9 — to'liq ekran.""")

a("help.text.o",
  """(O) Комплектация и другие действия — фурнитура, крепёж, работы и любые позиции заказа, которые не режутся.
Вверху — владелец, стоимость материалов, работы и итог, описание. Таблица: код, наименование, единица, количество, цена, стоимость.
Клавиши таблицы: Ctrl+PgUp — вставить строку, Ctrl+PgDn — добавить в конец, Del / Shift+Del — удалить, Ctrl+↑ / Ctrl+↓ — переместить, Ctrl+K — копия строки, Tab/Enter — вправо, Shift+Tab — влево, Ctrl+Tab/Ctrl+Enter — вниз (в конце — новая строка), Home / End — первая / последняя строка, Ctrl+V — вставка из Excel, Ctrl+P — настройка колонок.""",
  """(O) Komplektatsiya va boshqa amallar — furnitura, mahkamlagichlar, ishlar va buyurtmaning kesilmaydigan har qanday pozitsiyalari.
Yuqorida — egasi, materiallar, ish va jami narx, izoh. Jadval: kod, nom, birlik, soni, narx, qiymat.
Jadval tugmalari: Ctrl+PgUp — qator qo'shish, Ctrl+PgDn — oxiriga qo'shish, Del / Shift+Del — o'chirish, Ctrl+↑ / Ctrl+↓ — ko'chirish, Ctrl+K — qator nusxasi, Tab/Enter — o'ngga, Shift+Tab — chapga, Ctrl+Tab/Ctrl+Enter — pastga (oxirida yangi qator), Home / End — birinchi / oxirgi qator, Ctrl+V — Excel'dan qo'yish, Ctrl+P — ustunlar sozlamasi.""")

a("help.text.lb",
  """(LB) Этикетки — печать наклеек на детали, отходы и изделия.
Параметры: источник (детали — каждая / с количеством больше нуля / выделенные; отходы; изделия), размер этикетки, столбцы и строки на листе, промежутки, поля, границы, количество, макет (шаблон).
Пользовательские данные: Ctrl+PgUp — вставить поле, Del — удалить, Ctrl+↑ / Ctrl+↓ — переместить.
Шаблон (визуальный редактор): текст, прямоугольник, линия, полилиния, дуга, кривая Безье, эллипс, штрихкод и QR, изображение, чертёж детали, схема кромки, группа (начало координат и вращение), условие, переменная. Поля задаются числом или выражением.
Клавиши редактора: F4 — служебные команды (группа, условие, переменная) в списке «Добавить», F9 — «Состояние» (значения переменных), Ctrl+Z/Y, Ctrl+D — дубликат, Ctrl+G — группа, стрелки — сдвиг (Shift — крупнее, Alt — точнее), Ctrl+0 — показать всё.
Шаблоны можно открыть / сохранить в каталоге и импортировать / экспортировать файлы .lbl. Печать — в разделе «Печать», также ZPL для термопринтеров.""",
  """(LB) Etiketkalar — detallar, chiqindilar va mahsulotlar uchun yorliqlarni chop etish.
Parametrlar: manba (detallar — har biri / soni noldan katta / tanlanganlar; chiqindilar; mahsulotlar), etiketka o'lchami, listdagi ustun va qatorlar, oraliqlar, hoshiyalar, chegaralar, soni, maket (shablon).
Foydalanuvchi ma'lumotlari: Ctrl+PgUp — maydon qo'shish, Del — o'chirish, Ctrl+↑ / Ctrl+↓ — ko'chirish.
Shablon (vizual muharrir): matn, to'rtburchak, chiziq, poliliniya, yoy, Bezye egri chizig'i, ellips, shtrixkod va QR, rasm, detal chizmasi, kromka sxemasi, guruh (koordinata boshi va burish), shart, o'zgaruvchi. Maydonlar son yoki ifoda bilan beriladi.
Muharrir tugmalari: F4 — «Qo'shish» ro'yxatida xizmat buyruqlari (guruh, shart, o'zgaruvchi), F9 — «Holat» (o'zgaruvchilar qiymatlari), Ctrl+Z/Y, Ctrl+D — nusxa, Ctrl+G — guruh, strelkalar — siljitish (Shift — kattaroq, Alt — aniqroq), Ctrl+0 — hammasini ko'rsatish.
Shablonlarni katalogda ochish / saqlash va .lbl fayllarni import / eksport qilish mumkin. Chop — «Chop etish» bo'limida, termoprinterlar uchun ZPL ham bor.""")

a("help.text.remnants",
  """Склад остатков — деловые остатки листов после раскроя и их повторное использование.
После раскроя деловые остатки можно записать на склад (кнопка на вкладке «Раскрой» или предложение после раскроя — включается в «Настройках»). Склад: «Настройки → Склад остатков» — материал, размеры, толщина, количество, площадь, источник (номер заказа), дата, примечание; поиск, добавление, удаление.
В операции (CS) кнопка «Листы и остатки → со склада» добавляет подходящие остатки того же материала и толщины в список листов; при раскрое они используются в первую очередь (порядок — по списку). Остатки, зарезервированные другим заказом, выбрать нельзя.
«Исп. кол-во» у остатков в результате раскроя — сколько кусков забирает заказчик (они не идут на склад).""",
  """Qoldiqlar ombori — kroydan keyingi deloviy qoldiqlar va ulardan qayta foydalanish.
Kroydan keyin deloviy qoldiqlar omborga yoziladi («Kroy» varag'idagi tugma yoki kroydan keyingi taklif — «Sozlamalar» da yoqiladi). Ombor: «Sozlamalar → Qoldiqlar ombori» — material, o'lchamlar, qalinlik, soni, maydoni, manba (buyurtma raqami), sana, izoh; qidirish, qo'shish, o'chirish.
Operatsiyada (CS) «Listlar va qoldiqlar → ombordan» tugmasi shu material va qalinlikdagi mos qoldiqlarni listlar ro'yxatiga qo'shadi; kroyda ular birinchi navbatda ishlatiladi (tartib — ro'yxat bo'yicha). Boshqa buyurtma band qilgan qoldiqni tanlab bo'lmaydi.
Kroy natijasidagi qoldiqlarning «Ishl.» ustuni — buyurtmachi olib ketadigan bo'laklar soni (ular omborga tushmaydi).""")
