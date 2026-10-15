# Yetishmayotgan elementlar: kuzatilgan ko'rinish (2026-10-04)

Xodimlar o'rgangan onlayn tizimda bor, MebeliX Kroy'da hali yo'q elementlarning **kuzatilgan** tavsifi (ekrandan o'qilgan yozuvlar
va tartib). Hammasi noldan yoziladi; yozuvlar — aynan shu so'zlar bilan (rus), o'zbekchasi — to'liq tarjima.

## 1. (EL) «Настройка символов и цветов» oynasi
EL «Параметры» panelining asboblar qatorida tugma (maslahat: «Настройка символов и цветов»). Oyna: asboblar — qo'shish
(«Вставить [CTRL]+[PAGE UP]»), o'chirish («Удалить [DEL]»), «Переместить вверх [CTRL]+[UP]», «Переместить вниз [CTRL]+[DOWN]»;
jadval ustunlari: «№», «Символ», «Цвет» (katak rang bilan to'ldirilgan); standart qatorlar A, B, C, D … (har biriga o'z rangi);
pastda «Ок», «Отмена». Ma'nosi: yangi kromka operatsiyasiga navbatdagi belgi va rang shu jadvaldan beriladi
(bizda importda `_EL_COLORS` — `backend/app/plugins/legacy_project.py`). EL panelida: «Символ для обозначения» (1 belgi, yonida
«Только 1 символ»), «Цвет для обозначения» — «Цвет» tugmasi (maslahat «Выбор цвета»), «Линии маркировки» (ro'yxat 1…).

## 2. (XNC) «Шаблон»: «Переменные» va «Инструменты» oynalari, «Показать все изображение»
Chizma ustidagi asboblar qatorida tugmalar (maslahatlar): «Показать все изображение» (chizmani oynaga to'liq sig'dirish),
«Панель со служебными командами (F4)», «Состояние (F9)», «Переменные», «Инструменты», «Пересчитать параметричность», «Добавить»,
«Справка», eksport, import.
* **«Переменные»** oynasi: jadval «№ | Наименование | Описание | Тип | Значение», faqat «Ок». Qatorlar (tartib bilan):
  `allowanceB` Припуск на обработку заготовки - Снизу (double), `allowanceL` … - Слева, `allowanceR` … - Справа, `allowanceT` … - Сверху,
  `bySizeDetail` По размеру детали (boolean, katakcha), `dx` Длина, `dy` Ширина, `dz` Толщина,
  `ebj` Оклейка кромки снизу. - Ширина прифуговки, `ebt` Оклейка кромки снизу. - Толщина, `elj` / `elt` … слева, `erj` / `ert` … справа,
  `etj` / `ett` … сверху, `origin.x` Начало координат X, `origin.y` Начало координат Y, `xncSide` Сторона (boolean),
  so'ng dasturning o'z parametrlari / o'zgaruvchilari. Qiymatlar — joriy hisoblangan qiymat (faqat o'qish).
* **«Инструменты»** oynasi: jadval «Наименование | Диаметр | Комментарий» (dasturda ishlatilishi mumkin bo'lgan asboblar:
  Bore35, Bore26, Bore25, Bore20, Bore18, Bore15, Bore10, Bore8, Bore7, Bore5, Bore4.5, Bore3 …), «Ок», «Отмена».
  Bizda bu ro'yxat — «Настройки → XNC редактор → Инструменты» (shu ma'lumot ko'rsatiladi).

## 3. (CL) «Параметры» — yetishmayotgan parametrlar
Panel tartibi: «Параметры материала» (Ширина, Толщина, … «Количество полос», «Расчет стоимости по полосам», «Округление Полосы»:
К целому / По длине 1/2 / 1/3 / 1/4; operatsiya narxi asosi: Длине реза с торцовкой / без торцовки / По длине деталей /
По длине материала), **«Остаток»: «Размер остатков с учетом торцовки»**, «Ограничения»: «Минимальный размер детали»,
«Параметры раскроя»: «Толщина пилы для групповых деталей», «Минимальный отступ в конце»,
**«Максимальное количество разновидностей деталей на карте кроя»** (ro'yxat: Не ограничено, 1 … 10), «Предпочтения», «Сортировка»,
**«Объединение деталей»**, **«Группировка деталей по свойствам»**, **«Сохранение чертежа карт кроя»**.
Qalin bilan belgilanganlar bizda (CL) da yo'q; (CS) da shu nomdagi parametrlar bor — ma'nosi o'sha (pogonaj uchun).

## 4. (SP) «Режим размеров»
«Параметры материала» ostida: «Режим размеров» — radio: «Пильный размер» (standart) / «Размер заготовки».
Maydon hisobi: detal o'lchami pilniy (kromkagacha) yoki zagotovka (pripusk bilan) o'lchamidan olinadi.

## 5. (LB) «Параметры»
Chap ustun: «Источник данных» (ro'yxat: «Детали и остатки», …, «Пользов-кие данные»); **«Печатать»** — radio:
**«На формат А4»** / «На принтер этикеток»; «Количество» (faqat o'qish, dona); «Размер» (masalan 210x297, mm);
**«Макет»**: «Столбцы» (dona), «Строки» (dona), «Промежуток» (mm), ☐ «Поля страницы», **«Границы»** (ro'yxat: **«Нет границы»**,
**«Границы по периметру»**, …).
O'ng ustun: «Детали»: ☑ «Печать деталей», ☐ «Для каждой детали», ☐ «Только если количество больше нуля», ☐ «Выбранные детали»;
«Остатки»: ☑ «Печать остатков», ☐ «Для каждого остатка».

## 6. «Товары» (katalog importi) oynasi
Varaqlar «Файл», «Столбцы»; ustunlar ro'yxati: ID, **Родительский ID**, Папка, Код, Наименование, **Единица измерения**, Цена, Склад,
Изображение, Параметры, Размер, Толщина, Длина, Ширина; «Лист», «Начальная строка», «Сортировка», **«Отображать колонки»**,
«Корневая категория»: Листовой материал, Погонажный материал, Материал кромок, Материал поверхностей.

## 7. «Настройки» menyusi (tartib)
Сменить пароль · Сменить email · Режимы ввода деталей · Постпроцессоры · XNC Редактор · Сохранить данные на локальный диск ·
Импорт из 3D-Constructor · Dropbox · Папка проектов · Папка XNC шаблонов · Папка этикеток · Каталог товаров · Модуль заказов ·
Загрузить настройки · Выгрузить настройки. Pastda: «Выйти».
**Foydalanuvchi qarori (2026-10-04):** buyurtmalar moduli, bulut papkalari va hisob (parol / email) — **MES serveri** bajaradi;
bizda bu bandlar «MES server» belgisi bilan turadi, keyin ulanadi.
