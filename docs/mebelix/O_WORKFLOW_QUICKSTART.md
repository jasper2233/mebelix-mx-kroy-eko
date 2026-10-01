# O. Ish oqimi — xodim ko'zi bilan (MebeliX'da xuddi shunday bo'lishi kerak)

GibLab'ning o'z video-darsi (6 daqiqa) va xodimlar loyihalari asosida. Har qadam yonida MebeliX API.

## O1. Tezkor boshlash (qo'lda kiritish)

| # | Xodim nima qiladi | Ekranda | MebeliX |
|---|---|---|---|
| 1 | Tizimga kiradi | kabinet: loyihalar ro'yxati | MES SSO |
| 2 | «Добавить» (Ctrl+PgDn) → nom yozadi | modal «Введите имя проекта» | `POST /api/projects` |
| 3 | Loyiha ochiladi | 1 CS «Материал1», «№1 Изделие1 (1шт)» | avtomatik |
| 4 | CS qatorida «Каталог товаров» → ishlab chiqaruvchi → qalinlik → rang | «Товары» oynasi | `GET /api/catalog`, `POST .../material/{id}` |
| 5 | Kromka qo'shadi (+EL) → nomini yozadi («Ясень 1 мм») → en/qalinlik | EL «Параметры» | `POST .../operations {type: EL}` |
| 6 | Ikkinchi kromka (2 mm) — belgi B | | |
| 7 | CS qatorini tanlab «Детали» tabini ochadi | birinchi marta — o'lcham rejimi oynasi | profil `size_mode_prompt` |
| 8 | Klaviatura bilan: `720 Tab 280 Tab 10 Tab` (Ткт ✓ standart) `Space` kromka… | jadval, «Площадь», «Кол-во» jonli | `POST .../parts` |
| 9 | Nom ustunida qo'shimcha shartlar (`=`, `*`, `%`) | | |
| 10 | «Раскрой» tabi → «Раскроить» | kartalar, status qatori, miniatyuralar | `POST .../optimize` |
| 11 | Yana detal qo'shadi → «До кроить» | faqat yangi kartalar | `?mode=remaining` |
| 12 | Parametrlarni o'zgartirib qayta kroy (masalan yo'nalish «По длине») | | `PUT .../operations/{id}` + optimize |
| 13 | Kartadagi detalni bosadi — bir xillari ajraladi; ikki marta — xossalar | | frontend |
| 14 | «Печать отчета» → profil → PDF | 1-sahifa: materiallar, talabnoma, operatsiyalar | `GET .../report` |
| 15 | «Заказать» → ijrochi ID/email | holat «Заказан» | `POST .../order` |

## O2. Bazis-Mebelshik dan (asosiy kundalik oqim)

1. Bazis'da loyiha → «GibLabExport» skripti → fayl.
2. MebeliX: «Импорт из других программ» → «Bazis/GibLab XML» → fayl → yangi loyiha
   (`POST /api/projects/import-giblab`): mahsulotlar, CS/EL/XNC operatsiyalar, detallar, kromkalar.
3. Kroychi material nomlarini katalogdan tanlaydi (kod bog'lanadi), kerak bo'lsa kromka rangini qo'yadi
   (masalan «!СмЧт» — to'q sariq).
4. Kroy → tekshirish → izoh (F2) → «KROYGA» profili bilan chop → sex.
5. Qoldiqlar: ombordan yuklash (kroydan oldin), saqlash (kroydan keyin).

## O3. Excel dan

«Импорт из Excel» → fayl → tablar (Детали/Материалы/Изделия/Простые операции) → ustun xaritasi →
profil saqlash → import. Yoki Excel'da ustunlarni tanlab Ctrl+C → MebeliX detallar jadvalida Ctrl+V.

## O4. Kroyni qo'lda to'g'rilash

«Редактирование раскроя» → chapdan detalni sudrab kartaga (Shift bilan tahrir rejimi) → Alt/Ctrl bilan burish →
o'ng tugma bilan o'chirish → «Ок». Natija saqlanadi, statistika qayta hisoblanadi.
