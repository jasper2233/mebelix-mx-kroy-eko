# H. Hisobotlar, chop sozlamalari va etiketkalar

## H1. Hisobot tuzilmasi (PDF, xodimlar ko'rgan tartib)

1. **Sarlavha**: Loyiha nomi; ID muallif; ID loyiha (buyurtma №); buyurtma va tayyor sanasi;
   material, operatsiya va umumiy narx.
2. **Materiallar ro'yxati** (ixtiyoriy): `№ | Код | Наименование | Ед.И | Цена | Кол | Всего`.
3. **Требование на склад**: `№ | Тип | Код/Изделие | Наименование (+ «Листы: N шт  Длина реза: X м» / «Длина кромкования (работа): X м») | Ед.И | Кол`.
4. **Операции ro'yxati** (ixtiyoriy): `№ | Тип | Код/Изделие | Наименование | Ст. м-ла | Ст. оп-и | Ст-ть`.
5. Har **CS** operatsiya (yangi sahifadan, agar Н.Стр ✓):
   * «1. Детали (Размер заготовки)»: `№ | Длина | О-ка по длине | Ширина | О-ка по ширине | Кол | ИК | Ост | Наименование`
     (kromka katagida «(1) kromka nomi», XNC kodlari nom ostida «P1-1: 0000x005x0»);
   * «2. Листы»: `№ | Длина | Ширина | Площадь | Кол. листов | Цена (м2) | Общ. площадь | Сумма` + Всего;
   * «3. Отходы/Остатки» (ixtiyoriy): `№ | Длина | Ширина | Площадь | Кол. листов`;
   * **Kroy kartalari**: sarlavha `Material  №:1/2 S:2750/1830 C:1/2 Cp:18/19 LT:28.94/32.7 F:93.87%/92.31%`
     (ko'rsatkichlar profilga ko'ra), karta chizmasi, o'ngda jadval `№ | Дл | Шр | Кл | Мт`
     (Мт = «T» tekstura), legenda «A-1: kromka…», «B: …», «[*] Фрезерование (Радиусы)», «[T] Текстура»;
     izoh (F2) bo'lsa — sarlavha ostida; kartada QR/shtrixkod (ixtiyoriy).
   * A4 da 1 karta yoki **miniatyura rejimi** 4 yoki 6 karta.
6. Har **EL**: parametrlar bloki (en, qalinlik, prifugovka, chiqindi %, ortiqcha, min uzunlik, belgi, chiziqlar;
   material uzunligi/narxi, ish uzunligi/narxi) + `№ | Товар | Длина | О. дл. | Ширина | О. шр. | Кол | Дл. кр-ки | Наименование`.
7. Har **XNC** detal: chizma (o'lcham chiziqlari, frezalash yo'li, teshiklar jadvali `№ | X | Y | T/D | DP`) +
   **shtamp** (o'ngda vertikal): Наименование, Изделие, Деталь, Материал, Рм. заготовки, Рм. детали, Код, Количество («1 × 1 = 1 шт»), «По размеру детали».
8. Kolontitul: «Проект ID<№> <nom>», «Страница N».

## H2. «Настройки печати» (umumiy) — standart qiymatlar

| Bo'lim | Parametr | Standart |
|---|---|---|
| — | Печать заголовка проекта | Да |
| Материалы | Печать списка материалов · Группировать по коду | Нет · Нет |
| Требование на склад | Печать · количество работы по резке · «Длина кромки (работа)» | Да · Да · Да |
| Изделия | Печать списка · если изделие одно | Нет · Нет |
| Операции | Печать списка · если одна · Печать операций | Нет · Нет · Да |
| Обработка | Статистика по XNC | Нет |

## H3. (CS) chop sozlamalari

* **Общие** (bo'limlar): Печать заголовка Нет · требования на склад Нет · статистики Нет · деталей Да ·
  невместившихся деталей Нет · листов Да · остатков Нет · карт раскроев Да.
* **Детали**: Группировать по изделиям Нет · Режим вывода размеров «По размеру заготовки» (yoki detal) ·
  Выделять в колонке кромкования Нет · символы кромок + легенда Нет · Форма «С объединенными по одному размеру кромками».
* **Карты кроя**: Макет Книжная/Альбомная · Печатать список деталей Да · Зеркало (горизонтально/вертикально) ·
  Обозначение на детали: номер Да, наименование Да, маркеры обработки Нет, значение выражения, кромки Да,
  маркер кромок «Линии», стиль линий · обработка на деталях Нет · Обозначение на остатке: номер Да ·
  Стиль номера: шрифт 3, жирный Да · Стиль размеров: шрифт 6, разворачивать Да · Заливка панели/отходов ·
  Штрихкод: печатать Да, тип QRCode, данные (ifoda).
* **Заголовок карт кроя**: 12 ko'rsatkich (A_GLOSSARY) — Вкл + Ш-на; standart: №, S, C, Cp, LT, F.

## H4. Boshqa operatsiyalar chop sozlamalari

* **(EL)**: Печать заголовка Да · Печать деталей Да · «Печатать в заголовке деталей»: Длина кромкования (работа) Нет, Длина материала Нет.
* **(XNC)** «Статистика»: печатать Нет · Группировка по материалу · ustunlar: №, Ст (tomon), Код, Наименование,
  Д-на, Ш-на, Кол, Кол. св-ний, Цена св-ния, Ст-ть св-ния, Длина фр-ния, Цена фр-ния, Ст-ть фр-ния,
  Длина п-ния, Цена п-ния, Ст-ть п-ния, Доп. ст-ть, Ст-ть оп-и · «Чертеж» tabi (chizma sozlamalari).
* **Изделия**: Печать заголовка Нет · операций Нет · материалов Нет · деталей Да.
* **Поля страницы**: 10 / 10 / 8 / 10 mm, ko'zgu maydonlar Нет, kolontitul Внизу.
* Profil (masalan xodimlarning «KROYGA») — barcha shu sozlamalar to'plami; ✚ ✎ ✕.

## H5. Etiketkalar (LB)

**Parametrlar**: manba (foydalanuvchi ma'lumoti / mahsulotlar / detallar va qoldiqlar), o'lcham, ustunlar,
qatorlar, oraliq, sahifa chegaralari, chegaralar (border), soni; detallar: chop etish, har bir detal uchun,
faqat soni > 0, faqat tanlanganlar; qoldiqlar: chop etish, har bir qoldiq uchun; mahsulotlar: har biri uchun, soni > 0.
Foydalanuvchi ma'lumoti jadvali: nomi, tavsifi, turi, kengligi, standart qiymat.

**Shablon redaktori** (o'zimizniki, JSON): elementlar — polilinya boshi, chiziq, yoy, Bezier egri, to'rtburchak,
ellips, **matn**, **shtrixkod** (Code128/QR), rasm, koordinata boshi, burish, **detal chizmasi**, **kromka belgisi**.
Pozitsiya va mazmun — ifoda (`xnc.eval_expr` kabi xavfsiz hisoblagich + matn funksiyalari: left, right, trim,
find, rspace (chapdan to'ldirish), crc32).

**Ma'lumot qatorlari**: `GET /api/projects/{id}/labels?source=parts|remnants|products` (`services/labels.py`).
O'zgaruvchilar (bizniki → GibLab dagi eski nomi, eski shablonlarni ko'chirish uchun):

| MebeliX | GibLab | Ma'nosi |
|---|---|---|
| project_name / project_number / project_date / project_crc32 | project.name / — / project.date / project.crc32 | loyiha |
| product_name / product_code / product_qty / product_phone1/2 | product.name / .code / .count / .phone1/2 | mahsulot |
| material_name / material_code / thickness | material.name / material.code / thick | material |
| part_uid / part_code / part_name / part_description | part.id / part.code / name / description | detal |
| length, width (zagotovka) · detail_length/width · saw_length/width | length, width · detail.length/width · — | o'lchamlar |
| grain / qty / total_qty / used_qty / counter | txt / count / totalCount / usedCount / part.counter | |
| edge_{top,bottom,left,right}_{code,name,symbol,thickness} | etc/etn/ets/ett, ebc…, elc…, erc… | kromkalar |
| groove / mill / drill | groove / mill / drill | nomdagi belgilar |
| barcode | (ifoda) | [loyiha №][uid 4][hisoblagich 4] |
| remnant_number / business / map_index | waste / business | qoldiq etiketkasi |

**Shtrixkod tavsiyalari** (sanoat amaliyoti):
* 50 mm enga ~16 raqam yoki ~8 lotin harfi — skaner ishonchli o'qiydi; faqat raqam afzal.
* Eski printer chiziq tashlab ketishi mumkin — shtrixkodni vertikal joylash yoki etiketkani 90° burish.
* Shtrixkod mazmunini yonida matn bilan takrorlang.
* Har etiketka noyob bo'lsin (hisoblagich) — takror skanerlashdan himoya.
* CNC da dastur ishga tushirish uchun detalning har tomoniga alohida shtrixkod kerak bo'lishi mumkin.
* Bitta detalga bir nechta etiketka (`label_count`) — kerak bo'lsa.
