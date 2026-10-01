# D. Interfeys spetsifikatsiyasi v2 (to'liq, v1 + yangilari)

> Maqsad: GibLab'ga o'rgangan xodim MebeliX Kroy'da **o'qitishsiz** ishlay olsin — joylashuv, tablar,
> ustunlar tartibi, tugmalar joyi, yorliqlar bir xil. Dizayn (rang, shrift, ikonka, logo) — o'zimizniki.
> v1 dagi `UI_SPEC.md` ning barcha bandlari kuchda; bu hujjat ularni to'ldiradi va aniqlashtiradi.
> Rasm havolalari: v1 `screens/NN_*.jpg`, v2 `screens_v2/NN_*.jpg`.

---

## D0. Umumiy qoidalar (hamma ekranlar uchun)

1. **Akkordeon chap panel**: Язык · Проект(ы) · Печать отчета · Настройки · Закрыть проект · Справка.
   Loyiha yopiq bo'lsa «Проект» o'rniga «Проекты» (ro'yxat menyusi).
2. **Har parametr yonida yashil «?» belgisi** — bosilganda kontekst yordami shu parametr bo'limiga ochiladi.
   Har panel sarlavhasida «?» (F1) — shu panel yordami (screens_v2/35).
3. **Jadvallar** Excel kabi: katak tahriri, Enter/Tab bilan o'ngga va oxirida yangi qator, Shift+Tab/Shift+Enter
   orqaga, Ctrl+Tab/Ctrl+Enter pastga (qator boshiga), Home/↑/↓/End, Ctrl+V — Excel dan qo'yish,
   Ctrl+PgUp — qator qo'shish (joriydan oldin), Ctrl+PgDn — oxiriga qo'shish, Del/Shift+Del — o'chirish,
   Ctrl+↑/↓ — ko'chirish. To'liq ro'yxat: `E_HOTKEYS.md`.
4. **«Сохранить текущие параметры для использования по умолчанию»** — har parametrlar panelida;
   `PUT /api/settings/{scope}/default` (yangi operatsiya shu qiymatlar bilan yaratiladi).
5. **Umumiy «Сортировка» oynasi** (screens_v2/41): jadval ustunlari ro'yxati — `№ | Вкл ☐ | Наименование | Напр ☐`
   (Напр — kamayish), ↑↓ bilan ustuvorlik; hamma jadvallarda bir xil komponent.
6. **Ustun sozlamalari (Ctrl+P)** — profil (Standart, Uslugiya …), ✚ ✎ ✕, «Восстановить значения по умолчанию»,
   jadval: `№ | Вкл | Имя (sarlavha, tahrirlanadi) | Описание | Ш-на`. Detallar, Изделия, Операции,
   EL/GR/SP detallari, O materiallari jadvallarida (v1 screens/33).
7. Undo/Redo holati tugmalarda (Отменить/Вернуть faol/nofaol) — `GET /api/projects/{id}/history-state`.
   «Сохранить» — o'zgarish bor bo'lsa faol (MebeliX avtomatik saqlaydi, tugma — «hozir saqlash»).
8. Tasdiqlash so'rovlari brauzer `alert/confirm` emas, **ichki modal** bo'lsin.

## D1. Loyihalar ro'yxati («Проекты»)

Menyu: Обновить · Открыть · Добавить (Ctrl+PgDn) · Добавить папку · Переместить (F4) · Переименовать (F2) ·
Копировать · Удалить (Del, Shift+Del) · Выделить все (Ctrl+A) · Справка.
Yo'l satri: «Yuqori papka», «Uy», joriy yo'l. Jadval: `ID | Владелец | Состояние | Дата | Стоимость | Наименование`.
Ochish: ikki marta bosish yoki Ctrl+Space. Yangi loyiha: nom so'raladi (modal), ochilganda
1 mahsulot («Изделие1») va 1 bo'sh CS operatsiya («Материал1») bo'ladi.

## D2. Loyiha oynasi

Sarlavha: `Наименование` · `Валюта` (+ standart saqlash) · `Дата заказа` · `Дата готовности` · izoh maydoni · ✕.
Chap «Проект» menyusi: Справка · Обновить · Отменить · Вернуть · Сохранить · Общие действия ·
Експортировать · Импортировать · Импорт из Excel · Импорт из других программ · **Заказать** (holat select) +
mini-jadval `Заказ ID | Стоимость | С-ть материала | С-ть операций`.

* **Заказать**: modal «ijrochi ID yoki email» → `POST /api/projects/{id}/order` (MES bo'lim/foydalanuvchi).
* **Общие действия** (v1 screens/15): (1) bir xil kod+material nomli operatsiyalarni birlashtirish;
  (2) kromka operatsiyalarini kroy materiallari bo'yicha ajratish; (3) optimallashtirish (nofaol).
* **Импорт из других программ**: 1-bosqichda **GibLab .project / Bazis-Mebelshik (GibLabExport skripti) XML**
  — `POST /api/projects/import-giblab`. Qolganlari (PRO100, Imos, BCAD, Woody, WoodWop, iLENIA) keyin.
* **Импорт из Excel**: fayl → oyna: tablar «Детали», «Материалы», «Изделия», «Простые операции»;
  har tabda list (sheet) va ustun xaritasi; **profillar** (✚ saqlash) — keyingi safar tanlanadi;
  «faqat mahsulot sonini yangilash» rejimi.

## D3. «Операции» jadvali

Ustunlar: `№ | Тип (ikonka+kod) | Код/Изделие | Наименование | Ст. м-ла | Ст. оп-и | Ст-ть | П-ть ☑ | Н.Стр ☑`.
EL qatori nomi kromka rangida. Toolbar (chapdan): + CS · + EL · + GR · + XNC · **+ Операция** (turini tanlash) ·
Клонировать Ctrl+K · Каталог товаров · Объединить · Сортировка · Удалить Del · ↑ Ctrl+↑ · ↓ Ctrl+↓ · Справка F1.
Yangi EL: nomi darhol tahrir rejimida (inline), belgi avtomatik A, B, C …

**«Товары» (Каталог товаров) oynasi** (screens_v2/40): chapda «Категории» daraxti (ishlab chiqaruvchi →
qalinlik, masalan Egger → ЛДСП 16 мм), o'ngda «Изображение», pastda «Материалы» jadvali
`№ | Код | Наименование | Ед.И | Цена | Т-на | Д-на | Ш-на` + Поиск + Обновить + Настройки; Ок/Отмена.
Tanlanganda operatsiyaga kod, nom, narx, qalinlik, list o'lchami, tekstura yoziladi
(`POST .../material/{item_id}`). Manba — MES katalogi (hozir xodimlarda Dropbox katalog **ishlamayapti** —
«invalid_access_token» xatosi; MebeliX bu muammoni yo'q qiladi).

## D4. «Изделия» jadvali va mahsulot xossalari

Jadval: `№ | Код | Наименование | Кол | Ст. м-ла | Ст. оп-и | Стоимость | Всего` (narxlar 1 dona uchun, Всего = × Кол).
Toolbar: Свойства Ctrl+Space · Детали · hammasini 0 · Сортировка · nol sonlilar filtri Ctrl+F · ↑↓ ·
Вставить Ctrl+PgUp · Клонировать Ctrl+K · Удалить Del · Настройки Ctrl+P.

**Свойства (mahsulot)** (screens_v2/38-39): tablar «Свойства» | «Программа».
Свойства: guruhlar — *Общие* (Наименование, Код), *Данные заказа* (Данные заказа, Дата готовности,
Телефон 1, Телефон 2), *Дополнительные параметры* (kalit=qiymat, masalan `product.import = bm.1.86`);
pastda «Описание» va «Сообщения». «Программа» — parametrik mahsulot dasturi (XNC redaktoridagi buyruqlar
paneli: Com, Par, Var, Set, IF, Else, WD, DW, Brk, Con, Sub, Call, Ret, Msg, Err) — 3-bosqich.

## D5. CS — «Параметры» (v1 screens/01, screens_v2/35)

v1 jadvali to'g'ri, quyidagilar aniqlashtirildi:
* `Кратность` — **faqat o'qish** (= floor(Высота пакета / Толщина)).
* `Количество материала` — kroydan keyin «N Листы» (yoki m²), `Количество листов` — «N шт».
* «Минимальный отступ в конце» havolasi → oyna (screens_v2/34): ☐ «Минимальный отступ снизу» [mm],
  ☐ «Минимальный отступ справа» [mm] (belgilanmaguncha nofaol, torsovka qiymati ko'rinadi); Ок/Отмена.
* «Группировка деталей по свойствам» havolasi — faqat «Объединение деталей» ✓ bo'lsa faol.
* «Цена материала» yorlig'i «Расчет стоимости по листам» holatiga qarab: «за лист» / «за м²».
* Standart qiymatlar (xodimlar profili): propil 3, torsovka 2/2, yo'nalish Любое, tekstura ✓, murakkab polosa ✓,
  aylanish 6, paket 40, turlar cheklanmagan, katta paket ✓, polosa saralash «По убыванию», polosa ichida
  «Не сортировать», min/max polosa eni 0/0, max uzunlik 10000, min kesish 5, qoldiq 1000/500, delovoy 0.5 m²,
  min detal 30, taxminiy to'ldirish 90 %.

## D6. CS — «Детали» (v1 screens/02)

* Detallar jadvali **bo'sh** holda birinchi ochilganda «Режим ввода размеров детали» oynasi chiqadi
  (3 radio: заготовки / детали (с кромкой) / после прифуговки) — sozlamada o'chirilishi mumkin
  («Режимы ввода деталей»: не предлагать / …) (v1 screens/13, 24).
* Yangi qatorda **Ткт standart ✓** (material teksturali bo'lsa).
* **Space**: Ткт katagida — belgini almashtiradi; ОВ/ОН/ОЛ/ОП katagida — kromkani navbatdagi EL ga
  almashtiradi (bo'sh → A → B → … → bo'sh); **Shift+Space** — to'rt tomonga bir xil kromka (perimetr).
* Kromka katagi matni: EL nomi, EL rangida; tanlash ro'yxatida «(A) Ясень 1 мм» ko'rinishi.
* Ctrl+V: Excel dan ustun tartibi `Д-на, Ш-на, Кол, Ткт, ОВ, ОН, ОЛ, ОП, Наименование`; noma'lum kromka nomi —
  yangi EL operatsiyasi avtomatik yaratiladi (`POST .../parts/paste`).
* Pastki toolbar: `Режим ввода размеров детали (…)` havolasi, Excel/XNC ikonkalar, ☐TXT/☑TXT (hammasiga),
  uzunlik↔en, guruh, sozlama, **Площадь: X м2**, **Кол-во: N шт** (jonli).
* Tooltip: Изделие, № в изделии, № в раскрое, id, 4 o'lcham (v1 UI_SPEC §5.2).
* Detal xossalari: № ustunini ikki marta bosish yoki Ctrl+Space (v1 screens/29-31); o'lchamlar jadvalida
  kiritish rejimi qatori rang bilan (B2).

## D7. CS — «Листы и остатки» (v1 screens/03)

Jadval kroydan keyin **qoldiqlarni ham** ko'rsatadi: `Наименование` ustuni (List / Qoldiq / Delovoy qoldiq),
`Ишлатилди` — list uchun kroyda ishlatilgan; qoldiq uchun mijoz oladigan bo'laklar (tahrirlanadi),
`Колдик` = soni − ishlatilgan. Toolbar: «omborsdan qoldiqlarni yuklash» (`.../remnants/load`),
«qoldiqlarni omborga saqlash» (`.../remnants/save`), ↑↓, ✚, ✕, sozlama. Ustunlarda ifoda (formula) ishlatish — keyin.

## D8. CS — «Раскрой» (v1 screens/04-06)

* Kroy yo'q: markazda katta «Раскроить» va «Редактирование раскроя» havolalari.
* Status qatori ko'rsatkichlari **sozlanadi** (Ctrl+P oynasi, screens_v2/36): 12 ko'rsatkich
  (№, S, C, Cp, LT, F yoqilgan; R, CT, T, AP, AM, AW o'chiq), kengliklari; «Восстановить значения по умолчанию».
* Toolbar: Редактирование раскроя · **До кроить** · Комментарий (F2) · Удаление раскроя · Постпроцессор · Справка.
* **Комментарий (F2)**: karta ustida izoh satri (masalan «da»), tahrirlanadi (`PUT .../maps/{n}/comment`),
  chopda karta sarlavhasi ostida (screens_v2/37).
* Karta: detal — to'q sariq, bosilgan detal va **uning barcha nusxalari** — to'qroq; qoldiq — ko'k, markazida raqam;
  chiqindi — kulrang; detal ichida raqam, pastda uzunlik (+kromka harfi, masalan «820 A»), o'ngda en (vertikal);
  kromkali tomon — qalin chiziq (1..3). Sichqoncha g'ildiragi — masshtab. Ikki marta bosish — detal xossalari.
* O'ngda miniatyuralar (`№1 S:2750/1830 C:1`) va «Таблица команд» (`№ | Кд | Р | К | Д`).
* Namuna natija: screens_v2/99.

## D9. EL — Кромка (screens_v2/42)

Параметры: v1 bilan bir xil + yaxlitlash ro'yxatlari 15 variant: `[0] к ближайшему, ⌈0⌉ к большему, ⌊0⌋ к меньшему,
[0.0] …, [0.00] …, [0.000] …, [0.0000] …` (kodlar 0,1,2,10,11,12,20,…,42); «Линии маркировки» 0..3;
«Символ для обозначения» — 1 belgi; «Цвет» tugmasi. Детали tabi: `№ | Товар | ⇕Длина | ⇕Окл. дл. | ⇕Ширина |
⇕Окл. шр. | ОК | ⇕Д-на кромки | Наименование` (sarlavha bosilsa saralash) + ↑↓ navigatsiya.

## D10. XNC, GR, SP, O, CL, LB

Tafsilot: `J_XNC_SPEC.md`, `K_OPERATIONS_CL_O_SP_GR_LB.md`.

## D11. Печать отчета

Chap panel: Профиль (select + ✚ ✎ ✕; xodimlarda «KROYGA»), Поля страницы, Настройки печати, Изделия,
«Настройки печати операций»: (CS) (CL) (CN) (EL) (SP) (XNC). O'ngda PDF ko'rinishi (sahifalar miniatyurasi,
yuklab olish, chop etish). Oynalar:
* **Поля страницы** (screens_v2/43): Слева 10, Справа 10, Сверху 8, Снизу 10 мм, Зеркальные поля Нет,
  Позиция колонтитула Внизу.
* **Настройки печати** (v1 screens/22): Печать заголовка; Материалы (список, группировать по коду);
  Требование на склад (печатать; количество работы по резке; «Длина кромки (работа)»); Изделия (список;
  если одно); Операции (список; если одна; печать операций); Обработка (статистика XNC).
* **Изделия** (screens_v2/44): Печать заголовка Нет, Печать операций Нет, Печать материалов Нет, Печать деталей Да.
* **(CS)** (v1 screens/23): tablar Общие / Детали / Карты кроя / Заголовок карт кроя (to'liq: `H_REPORTS_LABELS.md`).
* **(EL)** (screens_v2/45): Печать заголовка Да, Печать деталей Да; «Печатать в заголовке деталей»:
  Длина кромкования (работа) Нет, Длина материала Нет.
* **(XNC)** (screens_v2/46): tablar Статистика (печатать статистику Да/Нет, Группировка по материалу,
  18 ustunli jadval) va Чертеж.

## D12. Настройки

Режимы ввода деталей · Постпроцессоры (Общие: «Добавлять префикс имени станка к названию файла»;
har stanok: fayl parametrlari, torsovka oldindan kesish, etiketka ma'lumoti, «User defined part info records») ·
XNC Редактор · Каталог товаров (MES) · Папки (проектов, XNC шаблонов, этикеток) · profil import/eksport (JSON).
«Сменить пароль/email», Dropbox, «Модуль заказов», GibLabLocal.ini — **kerak emas** (MES SSO va MES buyurtmalari).

## D13. Справка (yordam)

* F1 / «?» — kontekst bo'limi (panel yoki parametr) yon oynada.
* Yordam oynasi yuqorisida: ← → (tarix), «Видеоурок» (qisqa video yoki GIF), «Сочетания клавиш» (joriy panel yorliqlari).
* Yordam matnlari **o'zimiz yozamiz** (o'zbek + rus), GibLab matnlari ko'chirilmaydi.
