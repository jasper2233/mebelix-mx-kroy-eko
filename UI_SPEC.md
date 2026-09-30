# MebeliX Kroy — Interfeys spetsifikatsiyasi (UI_SPEC)

Bu hujjat hozir xodimlar ishlatayotgan GibLab interfeysini **ekran-ma-ekran** tasvirlaydi.
Maqsad — MebeliX Kroy xodimlarga tanish bo'lishi: joylashuv, ustunlar tartibi, tugmalar,
klaviatura yorliqlari bir xil. Har bir bo'lim yonida `screens/` papkasidagi rasm ko'rsatilgan.

> **Mualliflik huquqi qoidasi.** Biz faqat *ish jarayoni va maydonlar tuzilishini* takrorlaymiz.
> GibLab nomi, logotipi, ikonkalari, yordam matnlari, kodi, fayl formatlari va dizayn
> elementlarini (ranglar/shriftlar aynan nusxasi) **ko'chirmaymiz**. Ikonkalar — ochiq litsenziyali
> to'plamdan (Lucide / Tabler), logo — MebeliX. Rasmlardagi GibLab logosi faqat ma'lumot uchun.

---

## 0. Umumiy joylashuv (Layout)

```
┌──────────────┬───────────────────────────────────────────────────────────────┐
│  LOGO        │ Наименование [__________]   Изоҳ (textarea)             [X]   │
│  ID, email,  │ Валюта [UZS] 💾  Дата заказа [__]  Дата готовности [__]       │
│  balans      ├───────────────────────────────────────────────────────────────┤
├──────────────┤ [Операции][Изделия]                        toolbar  ▲ ▼ ?    │
│ ▸ Язык       │  ЮҚОРИ JADVAL (operatsiyalar yoki mahsulotlar)                │
│ ▾ Проект     ├───────────────────────────────────────────────────────────────┤
│   menyu…     │ (CS) <tanlangan operatsiya nomi>        №1 <mahsulot> (1шт)   │
│              │ [Параметры][Детали][Листы и остатки][Раскрой]   toolbar ? │
│ ▸ Печать     │  PASTKI PANEL (operatsiya turiga qarab o'zgaradi)             │
│ ▸ Настройки  │                                                               │
│ ▸ Закрыть    │                                                               │
│ ▸ Справка    │                                                               │
└──────────────┴───────────────────────────────────────────────────────────────┘
```

* Chap panel — **akkordeon** (bir vaqtda bitta bo'lim ochiq): Язык, Проект, Печать отчета,
  Настройки, Закрыть проект, Справка. Loyiha yopiq bo'lsa «Проект» o'rniga «Проекты» (ro'yxat).
* Yuqori jadval va pastki panel orasidagi chegara sudrab o'zgartiriladi (splitter).
* Tanlangan qator — och ko'k fon. Jadvallar Excel kabi: katakni bosib tahrirlash, Enter/Tab,
  strelkalar bilan harakat, Esc — bekor qilish.
* Til: UZ / RU (xodimlar hozir ruscha yorliqlar va o'zlari o'zgartirgan o'zbekcha ustun
  nomlarini ko'rishadi: «детал номи», «Сони», «Ишлатилди», «Колдик», «Изох»). Ustun nomlari
  foydalanuvchi profilida sozlanadi (§ 9.3).

---

## 1. Loyihalar ro'yxati (Проекты)

Chap menyu: Обновить, Открыть, Добавить, Добавить папку, Переместить, Переименовать,
Копировать, Удалить, Справка. Ochish — ikki marta bosish yoki **Ctrl+Space**.

Yuqorida: «Yuqori papkaga», «Uy», joriy yo'l (masalan `Я 2026 arxiv /`).
Jadval ustunlari: **ID | Владелец | Состояние | Дата | Стоимость | Наименование**.
Papkalar ro'yxat boshida (ikonka bilan). Holatlar: Не заказан / Заказан / Утвержден / Готов.

API: `GET /api/folders`, `GET /api/projects?folder_id=`, `POST /api/projects`, `/copy`, `DELETE`.

---

## 2. Loyiha sarlavhasi va chap «Проект» menyusi

Sarlavha maydonlari: **Наименование, Валюта (+ «standart sifatida saqlash» tugmasi),
Дата заказа, Дата готовности**, o'ngda erkin izoh maydoni, `X` — loyihani yopish.

«Проект» menyusi (screens/01): Справка, Обновить, Отменить (Ctrl+Z), Вернуть (Ctrl+Y),
Сохранить, **Общие действия**, Експортировать, Импортировать, Импорт из Excel,
Импорт из других программ, **Заказать** (holat select) va mini-jadval:
`Заказ ID | Стоимость | С-ть материала | С-ть операций`.

* **Общие действия** (screens/15): «Bir xil kod va material nomli operatsiyalarni birlashtirish»,
  «Kromka operatsiyalarini kroy materiallari bo'yicha ajratish», «Operatsiyalarni optimallashtirish».
* **Импорт из других программ** (screens/16): PRO100, Imos (fxm), БМ (xml, obl), BCAD (xml),
  Woody2, WoodWop (mpr), iLENIA (pd4). *MebeliX: birinchi bosqichda faqat Excel/CSV va MES API;
  qolganlari keyin plagin sifatida.*
* Eksport — loyihani JSON (`.mxk.json`) faylga yuklab olish.

---

## 3. Yuqori jadval: «Операции» (screens/01)

Ustunlar: **№ | Тип (ikonka+kod) | Код/Изделие | Наименование | Ст. м-ла | Ст. оп-и | Ст-ть | П-ть ☑ | Н.Стр ☑**
(П-ть — hisobotda chop etish, Н.Стр — yangi sahifadan).

Toolbar (chapdan o'ngga): Qo'shish: (CS) Листовой раскрой · (EL) Кромка · (GR) Пазование ·
(XNC) Обработка · **+ Операция** (turini tanlash oynasi) · Клонировать **Ctrl+K** ·
Каталог товаров · Объединить · Сортировка · Удалить **Del** · Yuqoriga **Ctrl+↑** ·
Pastga **Ctrl+↓** · Справка **F1**.

«Выберите тип операции» oynasi (screens/14): (O) Комплектация и другие действия, (CS) Листовой
раскрой, (CN) Нестинговый раскрой, (CL) Погонажный раскрой, (EL) Кромка, (SP) Обработка
поверхности, (GR) Пазование, (XNC) Обработка, (LB) Этикетки. *1-bosqich: CS, EL, GR, XNC.*

## 4. Yuqori jadval: «Изделия» (screens/12)

Ustunlar: **№ | Код | Наименование | Кол | Ст. м-ла | Ст. оп-и | Стоимость | Всего**.
Toolbar: Свойства (Ctrl+Space), Детали, Hammasini 0 soniga, Сортировка, Nol sonlilarni filtr
(Ctrl+F), ↑↓, Вставить (Ctrl+PgUp), Клонировать (Ctrl+K), Удалить (Del), Настройки (Ctrl+P).
Mahsulot soni o'zgarsa — barcha detallarning **ОК = Сони × mahsulot soni** qayta hisoblanadi.

---

## 5. CS — Листовой раскрой (pastki panel, 4 ta tab)

### 5.1 «Параметры» (screens/01) — ikki ustun

**Chap: Параметры материала**
| Maydon | Standart | Izoh |
|---|---|---|
| Ширина / Толщина | – / 16 мм | |
| Цена материала | 0 UZS | 1 list (yoki m²) narxi |
| Расчетный процент заполнения | 90 % | kroygacha taxminiy hisob |
| Количество материала / Количество листов | avtomatik | |
| ☑ Расчет стоимости по листам | ✓ | |
| Округление листы | К целому | К целому, Любое 1/2, 1/3, 1/4, По ширине 1/2…1/4, По длине 1/2…1/4 |
| Стоимость материала (Лист) | hisoblangan | |
| Расчет стоимости операции по | Длине реза | Длине реза / Периметру деталей / Площади деталей / Площади материала |
| Цена операции (метр/рез) · Стоимость операции | 0 | |
| **Остаток:** Мин. размер 1-й стороны / 2-й стороны | 1000 / 500 | деловой остаток chegarasi |
| Площадь делового остатка | 0.5 м² | |
| ☑ Размер остатков с учетом торцовки | ✓ | |
| **Ограничения:** Минимальный размер детали | 30 | |

**O'ng: Параметры раскроя**
| Maydon | Standart | Variantlar |
|---|---|---|
| Толщина пилы | 3 мм | |
| Толщина пилы для групповых деталей | – | |
| Торцовка по длине / по ширине | 2 / 2 мм | |
| ☐ Торцовка включает толщину пропила | | |
| Минимальный отступ в конце | havola → oyna | |
| Начальное направление резов | Любое | Любое, По длине, По ширине, По длине предпочтительно, По ширине предпочтительно |
| ☑ Учет текстуры · ☑ Использовать сложные полосы | | |
| Максимальное количество вращений | 6 | 2…6 |
| Высота пакета · Кратность | 40 мм · 2 | |
| Макс. количество разновидностей деталей на карте | Не ограничено | 1…10 |
| Предпочтения: ☑ Большой пакет | | |
| Сортировать полосы / в полосе | По убыванию / Не сортировать | По убыванию, По возрастанию, Узкие в центр, Не сортировать |
| Мин./Макс. ширина полосы · Макс. длина полосы | 0 / 0 / 10000 | |
| Минимальная обрезка | 5 | |
| ☐ Объединение деталей · Группировка деталей по свойствам (havola) | | |
| ☑ Сохранение чертежа карт кроя · Припуск на обработку заготовки | 0 | |

Panel toolbar: «Joriy parametrlarni standart sifatida saqlash», Справка.

### 5.2 «Детали» (screens/02) — asosiy ish joyi

Yuqori qator: **Режим ввода размеров детали (с кромкой)** (havola → oyna, screens/13:
заготовки / детали (с кромкой) / после прифуговки (без кромки)), Excel/XNC ikonkalar,
☐TXT (tekstura hammasiga), ☑TXT, uzunlik↔en almashtirish, guruh, sozlama,
**Площадь: 4.777 м2**, **Кол-во: 19 шт** (jonli yig'indi).

Ustunlar (standart profil, xodimlar ko'radigan tartib):
**№ | детал номи | Д-на | Ш-на | Сони | Ткт ☐ | ОВ | ОН | ОЛ | ОП | Код | ID | ОК**
* ОВ/ОН — kromka yuqori/pastki (uzunlik bo'yicha), ОЛ/ОП — chap/o'ng (en bo'yicha).
  Katakda kromka nomi; bosilganda — loyihadagi EL operatsiyalari ro'yxati (dropdown).
  Kromka nomi EL operatsiyasi rangi bilan bo'yaladi (masalan !СмЧт — to'q sariq).
* № yonida `'` belgisi — detalda XNC ishlov bor (6', 9', 10').
* Nomga belgi qo'shiladi: `=` пазование, `*` фрезеровка (радиусы), `%` сверление.
* Qator ustiga sichqoncha → tooltip: Изделие, № в изделии, № в раскрое, id, 4 xil o'lcham
  (детали / после прифуговки / заготовки / пильный).

Toolbar: Свойства **Ctrl+Space**, XNC Редактор, ↑ **Ctrl+↑**, ↓ **Ctrl+↓**, Вставить
**Ctrl+PgUp**, Клонировать **Ctrl+K**, Удалить **Del**, Вставить из буфера **Ctrl+V**
(Excel dan nusxa), Справка **F1**, Групповые действия **Ctrl+B**, Сортировка, Снять текстуру
**Ctrl+D**, Установить текстуру **Ctrl+E**, Поменять размеры местами **Ctrl+W**,
Перенести в другую операцию **Ctrl+M**, Настройки колонок **Ctrl+P**.
Pastda bo'sh qator — yangi detal kiritish (Enter → keyingi katak, oxirgi katakdan keyin yangi qator).

**Свойства детали** oynasi (screens/29-31): chapda detal chizmasi (kromkalar qalin chiziq),
ostida «Операции» ro'yxati (+ Добавить: (XNC) Обработка). O'ngda: Изделие (select),
Наименование, Описание, Толщина (read-only), Количество, Всего, ☐Текстура; o'lchamlar jadvali
4 qator (детали / заготовки после прифуговки / заготовки / пильный) × Длина, Ширина, ▽ △ ▷ ◁
(pripusklar). Yig'iladigan bo'limlar: **Группировка** (Нет / По длине / По ширине, мин./макс.
количество), **(EL) Кромка** (4 tomon select), **(SP) Обработка поверхности**,
**(GR) Пазование** (4 tomon: ☐tomon + select), **XNC Параметры**. Tepada «Дополнительные параметры».

**Групповые действия** (screens/32): har maydon oldida ☐ — faqat belgilanganlari o'zgaradi:
Изделие, Наименование, Описание, Длина, Ширина, Количество, Текстура, 4 kromka,
SP лицевая/обратная, 4 pazovanie.

**Настройки колонок** (screens/33): profil (Standart, Uslugiya…), + / ✎ / ✕, «Standartni tiklash».
Jadval: № | Вкл ☐ | Имя (qisqa sarlavha, tahrirlanadi) | Описание | Ш-на (kenglik).
To'liq ustunlar ro'yxati (51+): Арт, детал номи, Д-на, Ш-на, Сони, Ткт, ОВ, ОН, ОЛ, ОП,
Изделие-Наименование, ИК (ишлатилган), Ост (кирмай қолган), Изох, Код, ID, ОК, МК,
Группировка, ГКmin, ГКmax, Изделие-Количество, Изделие-Номер, Деталь-Номер, Номер в операции,
Зг.Дл/Шр, Дт.Дл/Шр, Пф.Дл/Шр, Пл.Дл/Шр, ▽△▷◁, ПВ ПН ПЛ ПП (+ Ст), ЛП, ТП, П, С, Ф, XNC1…

### 5.3 «Листы и остатки» (screens/03)

Ustunlar: **№ | Длина | Ширина | Сони | Квадрати | Ишлатилди | Колдик | ТД | ТШ | Изох**
(Сони=10000 → cheklanmagan; ТД/ТШ — shu list uchun alohida torsovka; Ишлатилди — kroyda
ishlatilgan listlar; Колдик — qolgan). Toolbar: omborsdan qoldiq qo'shish, «0», ↑↓, +, ✕, sozlama.

### 5.4 «Раскрой» (screens/04, 05)

Yuqori status qatori: `№: 1/2 | S: 2750/1830 | C: 1/2 | Cp: 18/19 | LT: 28.94/32.7 | F: 93.87%/92.31%`
va sahifalash (Первая **Home**, Предыдущая **↑**, Следующая **↓**, Последняя **End**).
* № — karta/jami; S — list o'lchami; C — shu kartadagi listlar soni/jami listlar;
  Cp — detallar kartada/jami; LT — kesish uzunligi m kartada/jami; F — to'ldirish % kartada/o'rtacha.
* Markazda karta: detallar **to'q sariq**, chiqindi **kulrang**, qoldiq **ko'k**; har detalda raqam
  (katta), pastki-chap burchakda uzunlik, o'ng tomonda en (vertikal matn).
* O'ngda karta miniatyuralari ro'yxati (`№1 S:2750/1830 C:1`) + **Таблица команд** (screens/05):
  `№ | Кд | Р | К | Д` — buyruq (T torsovka, C kesish, P detal kesish, W chiqindi, R burish,
  raqam — daraja), o'lcham, soni, detal/qoldiq raqami.
* Toolbar: **Раскроить** (katta tugma, kroy yo'q bo'lsa), Редактирование раскроя, **До кроить**
  (faqat qolgan detallarni), Комментарий, Удаление раскроя, Постпроцессор (stanok formatiga),
  Настройки (Ctrl+P), Справка.

**Редактирование раскроя** (screens/06) — to'liq ekran oynasi: chapda detallar ro'yxati
(№ | Товар | Длина | Ширина | Кол-во | Исп. | Остаток | Наименование), o'ngda karta.
Toolbar: Отменить Ctrl+Z, Вернуть Ctrl+Y, Добавить/Удалить карту, Торцовка, В начало
Ctrl+←, В конец Ctrl+→, Клонировать Ctrl+C, Развернуть резы Ctrl+R, Расширить полосу Ctrl+Q,
Удалить Del, Filtr (Ctrl+F), ↑↓. Pastda yordam: **Shift** — tahrir rejimi, chap tugma — detal
qo'yish, **Alt/Ctrl** — detalni aylantirish, o'ng tugma — detal/polosani o'chirish.
«Горизонтальный интерфейс» almashtirgich, Ок / Отмена.

---

## 6. EL — Кромка (screens/07, 08)

**Параметры** — chap: ☑Учитывать материал, Ширина 19, Толщина 0, Ширина прифуговки 0;
Расход: Процент отхода 0 %, Длина остатка по краям 20 мм, Мин. оклеиваемая длина 100 мм;
Обозначение: Символ (1 belgi, «A»), Цвет, Линии маркировки (1..3);
Ограничения: мин. размер стороны, перпендикулярной кромке 40 мм.
O'ng — Стоимость: Цена материала, Округление длины материала ([0.0] к ближайшему…),
Длина материала (м), Стоимость материала, Цена операции (м), Округление длины кромкования,
Длина кромкования (работа), Стоимость операции, Стоимость, Описание.

**Детали**: `№ | Товар | Длина | Окл. дл. | Ширина | Окл. шр. | ОК | Д-на кромки | Наименование`
(read-only, CS operatsiyalardan yig'iladi).

Formula (GibLab hisobotiga mos tekshirilgan):
`material = Σ(tomon + 2×остаток по краям) × (1+отход%)`, `ish = Σ max(tomon, мин. длина)`.

## 7. XNC — Обработка (screens/09-12)

Tablar: **Параметры | Шаблон | Стоимость**.
* Параметры: Изделие, Материал, Наименование, ☑По размеру детали, Длина DX, Ширина DY,
  Толщина DZ, Количество, ☑Лицевая сторона, Поворот (0/90/180/270), Зеркало (X/Y),
  Начало координат (4 burchak), Стоимость, Описание. O'ngda detal chizmasi (kromka harflari A).
  Toolbar: Выбрать деталь, XNC Редактор, Кодирование, Отменить деталь, Свойства, Standart
  saqlash, Открыть, Сохранить, Справка, Постпроцессор.
* Шаблон — grafik redaktor: chapda buyruqlar paneli (Com, Par, Var, Set, IF, Else, WD, DW, Brk,
  Con, Sub, Call, Ret, Msg, Err + Инструмент, Сверление фронт/слева/справа/сверху/снизу,
  Точка входа, Фрезерование прямая/дуга/дуга с центром/3 точки/скругление/прямоугольник/эллипс,
  Пазование, Начало координат). O'ngda «Программа» daraxti (`N=Mill20 D=20`,
  `Var double contMillDepth=dz`, `X=350 Y=400 DP=contMillDepth T=Mill20`, …).
* Стоимость: Цена сверления × кол-во, Цена фрезеровки (1 м) × длина, Цена пиления × длина,
  Дополнительная стоимость, Стоимость единицы, Количество, Стоимость операции.
*1-bosqichda XNC: dastur saqlash + narx; grafik redaktor 2-bosqich.*

---

## 8. Печать отчета (screens/17-23)

Chap menyu: Профиль (select + ✚ ✎ ✕), Поля страницы, Настройки печати, Изделия,
Настройки печати операций: (CS), (CL), (CN), (EL), (SP), (XNC).
Hisobot PDF (brauzerda ko'rish/yuklab olish/chop):
1. Sarlavha: Проект, ID автора, ID проекта, даты, стоимости.
2. **Требование на склад**: № | Тип | Код | Наименование (Листы: N шт, Длина реза: X м) | Ед.И | Кол.
3. Har CS: Детали jadvali (№ | Длина | О-ка по длине | Ширина | О-ка по ширине | Кол | ИК | Ост |
   Наименование), Листы jadvali (Длина | Ширина | Площадь | Кол. листов | Цена | Общ. площадь | Сумма),
   so'ng kroy kartalari — sarlavha `Material  №:1/2 S:… C:… Cp:… LT:… F:…`, o'ngda karta
   detallari jadvali (№ | Дл | Шр | Кл | Мт) va kromka legendasi `A-1: kromka…`, `[*] Фрезерование`.
4. Har EL: parametrlar + detallar jadvali.
5. Har XNC detal: chizma (o'lchamlar, teshiklar jadvali) + shtamp (Наименование, Изделие,
   Деталь, Материал, Рм. заготовки, Рм. детали, Код, Количество).

«Настройки печати» (screens/22): Печать заголовка; Материалы (список, группировать по коду);
Требование на склад (печатать, количество работы по резке, «Длина кромки (работа)»);
Изделия; Операции; Обработка (статистика XNC) — har biri Да/Нет.
«(CS) настройки» (screens/23) tablar: Общие (разделы: заголовок, требование, статистика,
детали, невместившиеся, листы, остатки, карты), Детали (группировать по изделиям, режим
размеров, выделять кромки, символы кромок + легенда, форма печати), Карты кроя (макет
книжная/альбомная, список деталей, зеркало, номер/наименование детали, маркеры, кромки
«Линии», номер остатка, шрифт размеры, заливка, **штрихкод QRCode**), Заголовок карт
(12 ta ko'rsatkich: №, S, C, Cp, LT, F, R, CT, T, AP, AM, AW — yoqish/kenglik).

## 9. Настройки (screens/24-28)
* Сменить пароль / email — *MebeliX da MES SSO orqali, kerak emas.*
* **Режимы ввода деталей** (screens/24): «Taklif chiqarish» — Не предлагать / заготовки /
  детали (с кромкой) / после прифуговки.
* **Постпроцессоры** (screens/25-26): Общие + stanoklar (SCM, Holzma PTX/CadMatic, Biesse,
  Homag, Felder, KDT, Nanxing, Schelling, ELMO, GlassGCODE). Stanok sozlamasi: fayl parametrlari,
  торцовка (oldindan kesish), этикетка. *1-bosqich: faqat bizdagi stanok formati.*
* **Каталог товаров** (screens/27): Excel fayl, list, boshlang'ich qator, ustunlar xaritasi
  (ID, Родительский ID, Папка, Код, Наименование, Ед.изм, Цена, Склад, Изображение, Параметры,
  Толщина, Длина, Ширина) va ildiz kategoriyalar (лист, погонаж, кромки, поверхности).
  *MebeliX: katalog MES dan API orqali (`POST /api/catalog/sync`).*
* **Модуль заказов** (screens/28) — onlayn buyurtma; *MebeliX da MES buyurtmalari bilan almashtiriladi.*
* Saqlash/yuklash sozlamalari (ini) → *MebeliX: profil JSON import/eksport.*

## 10. Klaviatura yorliqlari (bir xil bo'lishi SHART)

| Yorliq | Amal |
|---|---|
| Ctrl+Z / Ctrl+Y | Отменить / Вернуть |
| Ctrl+K | Клонировать |
| Del | Удалить |
| Ctrl+↑ / Ctrl+↓ | Yuqoriga / pastga ko'chirish |
| Ctrl+Space | Свойства (va ro'yxatda — ochish) |
| Ctrl+PgUp | Вставить qator |
| Ctrl+V | Buferdan (Excel) qo'yish |
| Ctrl+B | Групповые действия |
| Ctrl+D / Ctrl+E | Teksturani olish / qo'yish |
| Ctrl+W | Uzunlik ↔ en |
| Ctrl+M | Boshqa operatsiyaga ko'chirish |
| Ctrl+P | Ustun sozlamalari |
| Ctrl+F | Nol qoldiqli/sonli filtr |
| F1 | Yordam |
| Home / ↑ / ↓ / End | Kroy kartalari bo'ylab |
| Ctrl+R / Ctrl+Q / Ctrl+C / Ctrl+←→ | (tahrirda) rezlarni aylantirish / polosani kengaytirish / klon / boshiga-oxiriga |

## 11. Ekran rasmlari indeksi

| Fayl | Nima |
|---|---|
| 01_CS_parametrlar | Asosiy oyna, CS Параметры |
| 02_CS_detallar | Detallar jadvali |
| 03_CS_listlar_qoldiqlar | Listlar va qoldiqlar |
| 04_CS_raskroy_karta | Kroy kartasi |
| 05_CS_buyruqlar_jadvali | Buyruqlar jadvali |
| 06_raskroyni_tahrirlash | Kroyni qo'lda tahrirlash |
| 07/08_EL_* | Kromka parametr / detallar |
| 09/10/11_XNC_* | XNC parametr / shablon / narx |
| 12_Izdeliya_va_XNC_dastur | Изделия jadvali + XNC dastur |
| 13_olcham_kiritish_rejimi | O'lcham kiritish rejimi |
| 14_operatsiya_turi_tanlash | Operatsiya turi |
| 15_umumiy_amallar | Общие действия |
| 16_boshqa_dasturdan_import | Import |
| 17–21_hisobot_* | PDF hisobot sahifalari |
| 22/23_*chop_sozlamalari | Chop sozlamalari |
| 24_detal_kiritish_rejimlari | Sozlama |
| 25/26_postprotsessor* | Postprotsessorlar |
| 27_tovar_katalogi, 28_buyurtma_moduli | Katalog / buyurtma |
| 29–31_detal_xossalari* | Detal xossalari oynasi |
| 32_guruhli_amallar | Guruhli tahrir |
| 33_detal_ustun_sozlamalari | Ustunlar sozlamasi (to'liq ro'yxat) |
