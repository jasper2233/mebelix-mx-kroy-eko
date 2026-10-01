# A. Lug'at (glossariy): RU ↔ UZ ↔ kod

Xodimlar ekranda **ruscha yorliqlarni** ko'radi (ba'zi ustunlar o'zbekcha qayta nomlangan).
Kodda inglizcha nomlar ishlatiladi. Bu jadval uchalasini bog'laydi — Claude Code UI matnlarini
va API maydonlarini shundan oladi.

## Asosiy tushunchalar

| RU (UI da) | UZ | Kod / API | Izoh |
|---|---|---|---|
| Проект | Loyiha | `Project` | bitta buyurtma (masalan «Detskiy kravat») |
| Папка | Papka | `Folder` | loyihalar papkasi (masalan «Я 2026 arxiv») |
| Изделие | Mahsulot | `Product` | mebel buyumi (shkaf, krovat); soni `qty` |
| Операция | Operatsiya | `Operation` | CS, CL, EL, GR, SP, XNC, O, LB |
| Деталь | Detal | `Part` | kesiladigan bo'lak |
| Лист | List | `StockSheet(kind="sheet")` | to'liq plita (2750×1830 va h.k.) |
| Остаток | Qoldiq | `kind="remnant"` | o'lchami min chegaradan katta bo'lak |
| Деловой остаток | Delovoy (ishchi) qoldiq | `kind="business"` | maydoni ≥ chegarasi; sarfga kirmaydi |
| Отход | Chiqindi | `kind="waste"` | qolgan hamma kichik bo'laklar |
| Карта кроя / раскроя | Kroy kartasi | `CutMap` | bitta list (yoki bir xil listlar paketi) sxemasi |
| Раскрой | Kroy | `CuttingResult` | barcha kartalar |
| Раскроить | Kroy qilish | `POST .../optimize` | |
| До кроить | Qolganini kroy qilish | `POST .../optimize?mode=remaining` | eski kartalar o'zgarmaydi |
| Удаление раскроя | Kroyni o'chirish | `DELETE .../result` | |
| Полоса | Polosa | strip (daraja 1 bo'lak) | |
| Пакет | Paket | `CutMap.packs` | bir vaqtda kesiladigan listlar to'plami |
| Кратность | Karralik | `multiplicity` | = floor(paket balandligi / qalinlik) |
| Высота пакета | Paket balandligi | `pack_height` | arra ko'tarilish balandligi |
| Вращение | Burilish/daraja | `max_rotations` | gilyotina kesish darajalari soni (2..6) |
| Пропил / толщина пилы | Propil / arra qalinligi | `kerf` | |
| Торцовка | Torsovka (chetni tekislash) | `trim_length`, `trim_width` | |
| Минимальный отступ в конце | Oxirgi minimal otstup | `end_offset_bottom/right` | |
| Минимальная обрезка | Minimal kesib tashlash | `min_trim_cut` | yupqa tilim qoldirmaslik |
| Текстура | Tekstura (yog'och naqshi) | `grain` | ✓ bo'lsa detal aylantirilmaydi |
| Кромка / кромкооблицовка | Kromka / kromkalash | `EL` | |
| Прифуговка | Prifugovka (kromkadan oldin frezalash) | `jointing_width` | |
| Пазование | Pazovanie (ariqcha) | `GR` | |
| Обработка поверхности | Sirt ishlovi | `SP` | |
| Обработка (XNC) | CNC ishlov | `XNC` | parmalash/frezalash dasturi |
| Комплектация | Komplektatsiya | `O` | furnitura, transport, yig'ish va h.k. |
| Этикетки | Etiketkalar | `LB` | |
| Погонажный раскрой | Pogonaj (chiziqli) kroy | `CL` | profil, planka |
| Нестинговый раскрой | Nesting kroy | `CN` | keyingi bosqich |
| Постпроцессор | Postprotsessor | — | stanok faylini yaratish |
| Заказать | Buyurtma berish | `POST .../order` | ijrochiga yuborish |
| Требование на склад | Omborga talabnoma | `GET .../warehouse` | |
| Припуск на обработку | Ishlov pripuski | `allow_*`, `machining_allowance` | |

## Detal jadvali ustunlari (standart profil)

| Ustun (xodimlar ko'radi) | Asl RU ma'nosi | Kod | Izoh |
|---|---|---|---|
| № | номер | `uid` | ' (apostrof) — detalda XNC bor |
| детал номи | Наименование | `name` | belgilar: `=` paz, `*` frezer, `%` parmalash |
| Д-на | Длина | `length` | |
| Ш-на | Ширина | `width` | |
| Сони | Кол | `qty` | |
| Ткт | Текстура | `grain` | Space bilan almashtiriladi |
| ОВ | Оклейка сверху (по длине) | `edge_top` | |
| ОН | Оклейка снизу (по длине) | `edge_bottom` | |
| ОЛ | Оклейка слева (по ширине) | `edge_left` | |
| ОП | Оклейка справа (по ширине) | `edge_right` | |
| Код | Код | `code` | |
| ID | уникальный идентификатор | `uid` | |
| ОК | Общее количество | `effective_qty` | = Сони × mahsulot soni (− МК) |
| ИК / Ишлатилди | Используемое количество | `used_qty` | kroyga kirgan |
| Ост / Колдик | Остаток | `left_qty` | kirmay qolgan |
| МК | Минус количество | `minus_qty` | ombordan olinadi |
| Изох | Описание | `description` | `#KOD` lits / `##KOD` orqa tomon XNC |

## «Листы и остатки» ustunlari

| Ustun | RU | Kod |
|---|---|---|
| Длина / Ширина | | `length` / `width` |
| Сони | Количество | `qty` (10000 = cheklanmagan) |
| Квадрати | Площадь | hisoblanadi |
| Ишлатилди | Исп. Кол-во | `used_qty` (list: kroyda ishlatilgan; qoldiq: mijoz oladigan bo'laklar) |
| Колдик | Остаток | `qty − used_qty` |
| ТД / ТШ | Торцовка по длине / ширине (shu list uchun) | `trim_length` / `trim_width` |
| Изох | Описание | `description` |

## Kroy kartasi ko'rsatkichlari (status qatori / chop sarlavhasi)

| Belgi | Ma'nosi |
|---|---|
| № | karta raqami / jami kartalar |
| S | list o'lchami (uzunlik/en) |
| C | kartadagi listlar soni / jami listlar |
| Cp | kartadagi detallar / jami detallar |
| LT | kesish uzunligi (m) kartada / jami |
| F | to'ldirish % kartada / o'rtacha |
| R | chiqindi % kartada / jami |
| CT | kesishlar soni kartada / jami |
| T | torsovka uzunlik bo'yicha / en bo'yicha |
| AP | detallar maydoni kartada / jami |
| AM | material maydoni kartada / jami |
| AW | chiqindi+qoldiq maydoni kartada / jami |

## Buyruqlar jadvali (Таблица команд)

| Kod | Ma'nosi |
|---|---|
| `R` | listni 90° burish (birinchi kesishlar en bo'yicha bo'lsa) |
| `Tx` | torsovka (x — daraja) |
| `Cx` | oddiy kesish (bo'lakka ajratish) |
| `Px` | detalni ajratuvchi yakuniy kesish |
| `Wx` | qoldiq/chiqindi (ref — qoldiq raqami) |

Ustunlar: `Кд` (kod+daraja) · `Р` (o'lcham) · `К` (soni) · `Д` (detal/qoldiq raqami).
