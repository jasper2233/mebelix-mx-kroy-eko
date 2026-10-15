# O'xshashlik tekshiruvi: onlayn tizim ↔ MebeliX Kroy (2026-10-04)

Maqsad (foydalanuvchi qarori): hozircha har bir bo'lim, har bir satr va xatti-harakat xodimlar o'rgangan tizim bilan **bir xil**
bo'lsin (solishtirish va kamchiliklarni tez topish uchun); dizayn keyin o'zgartiriladi. Foydalanuvchining o'z qo'shimchalari
(u tizimda yo'q funksiyalar) joyida qoladi. Hammasi noldan yoziladi — kod, ikonka, logo, yordam matni ko'chirilmaydi.

## Usul (takrorlanadi)
Har ekranda ko'rinadigan barcha yozuvlar, tugma maslahatlari (`title`) va ro'yxat variantlari ikkala tizimdan yig'iladi va
solishtiriladi: `tools/parity/mxinv.mjs` (MX Kroy, Playwright) + sahifadagi `__inv()` (onlayn tizim, fayl sifatida saqlanadi) →
`tools/parity/invcmp.py` (foiz va yetishmayotganlar ro'yxati). Loyiha ikkalasida bir xil (35 detal, 36 XNC).
Bu o'lchov **yozuv va boshqaruv elementlari borligini** ko'rsatadi; joylashuv, xatti-harakat va hisob natijalari alohida
tekshiriladi (kroy — `P_TAQQOSLASH.md`, stanok fayllari — `postprocessors/SAVOLLAR.md`).

## Natija (yozuvlar bo'yicha)
| Ekran | Boshida | Tuzatishdan keyin |
|---|---|---|
| (CS) Раскрой | 88.8% | 100% |
| (CS) Параметры | 94.1% | 99.2% |
| (CS) Детали | 89.2% | 98.5% |
| (CS) Листы и остатки | 89.8% | 100% |
| (EL) Кромка | 94.6% | 99.1% |
| (XNC) Параметры | 89.9% | 100% |
| (XNC) Шаблон | 79.8% | 98.2% |
| **Jami (749 element)** | **82.7%** | **99.2%** |

Tuzatilgani: tugma maslahatlari (ko'chirish, postprotsessor, kroy ko'rsatkichlari, XNC buyruqlari nomlari, ko'zgu, rang tanlash,
operatsiyalar jadvali sarlavhalari), «Максимальное количество разновидностей…», «Объединить» va h.k. (`scripts/i18n_zz_parity.py`).
Manbadagi imlo xatolari («Експортировать», «Коментарий», «Окруление») takrorlanmaydi.

## 2-bosqich: qolgan ekranlar (2026-10-04 kech)
| Ekran | Natija |
|---|---|
| Loyihalar ro'yxati | 95.8% |
| «Изделия» | 89.2% (farq — pastki paneldagi loyiha ma'lumoti; boshqaruv elementlari mos) |
| (CL) Параметры / Детали | 94.4% / 100% |
| (SP) | 98.9% |
| (GR) | 100% |
| (O) | 100% |
| (LB) | 96.2% |
| «Печать отчета» menyusi | 100% |
| «Настройки» menyusi | 45% (hisobga oid va bulut bo'limlari yo'q — pastda) |
| **Jami 17 ekran, 1446 element** | **97.4%** |

Oynalar (yozuvlar ro'yxati qo'lda yig'ilgan): «Режимы ввода деталей» 100%, «XNC Редактор» 100%, «Товары» (katalog importi) 85%,
«Модуль заказов» 35% (bizda bunday modul yo'q).

## Hali yo'q (keyingi ish — haqiqiy funksiyalar)
* **«Настройки»:** «Сменить пароль», «Сменить email», «Выйти»; «Сохранить данные на локальный диск»; «Импорт из 3D-Constructor»;
  bulut papkalari (Dropbox, «Папка проектов / XNC шаблонов / этикеток»); **«Модуль заказов»** (onlayn buyurtma qabul qilish).
* **(CL) Параметры:** «Размер остатков с учетом торцовки», «Максимальное количество разновидностей деталей…», «Объединение деталей»,
  «Группировка деталей по свойствам», «Сохранение чертежа карт кроя».
* **(LB):** «На формат А4», «Макет», chegara variantlari («Нет границы» / «Границы по периметру»).
* **(SP):** «Режим размеров» → «Размер заготовки».
* «Товары» oynasi: «Родительский ID», «Единица измерения», «Отображать колонки».

## Hali yo'q — 1-bosqichdan
* (XNC) Шаблон: «Переменные» tugmasi, «Показать все изображение» (chizmani to'liq ko'rsatish).
* (EL): «Настройка символов и цветов» oynasi.
* (CS) Раскрой bo'sh holatida «Редактирование раскроя» (noldan qo'lda kroy).
* Stanok oynasida «Инструменты» / «Ограничения» / «Оптимизация» bo'limlari (bizda — sozlamalarda).

## Hali o'lchanmagan
(CN) nesting, «Общие действия» / eksport / import oynalarining ichki maydonlari, chop etish sozlamalari oynalari (har operatsiya turi),
hisobotning o'zi (PDF). Lokal versiya — tekshirilmadi (brauzerda ochiladigan lokal manzil berilmagan).

## 3-bosqich (2026-10-04 kech): yetishmayotganlar bajarildi → 17 ekran bo'yicha **99.2%** (1434 / 1446)
Bajarildi: «Настройки» menyusi (o'rganilgan tartib; parol / email / Dropbox / papkalar / «Модуль заказов» / «Выйти» — «MES server»
belgisi bilan, keyin ulanadi; «Сохранить данные на локальный диск» — barcha loyihalar ZIP), (CL) ning 5 parametri
(«Максимальное количество разновидностей…» optimizatorda haqiqiy cheklov; «Объединение деталей», «Группировка…», «Сохранение чертежа…»
— saqlanadi, kroyga ta'sir qilmaydi), (SP) «Размер заготовки», (LB) «Параметры» paneli (radio «На формат А4 / На принтер этикеток»,
«Макет», «Границы», «Выбранные детали»), «Товары» oynasi («Файл» / «Столбцы», «Родительский ID», «Единица измерения», «Размер»,
«Корневая категория», «Отображать колонки»), (EL) «Настройка символов и цветов», (XNC) «Переменные», «Инструменты»,
«Показать все изображение» (+ g'ildirak bilan kattalashtirish). Qolgan 12 element — o'lchov shovqini (loyiha ma'lumoti) va
loyihalar ro'yxatidagi «Выйти».
Ochiq: «Товары» dagi «Сортировка»; «Границы» ning boshqa variantlari; «Объединение деталей» / «Группировка…» ning asl ma'nosi;
(CL) «Толщина пилы для групповых деталей» va «Сортировка» guruhi; stanok oynasidagi «Ограничения» / «Оптимизация» varaqlari.
Testlar: backend 1878 o'tdi, e2e 11/11.
