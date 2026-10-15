# Q. v2.1 — jonli GibLab bilan solishtirish, QA va tuzatishlar (2026-10-01)

## 1. Usul
1. Real GibLab (GibLabLocal) ochilib, korxonaning o'z loyihalarida ekranlar, menyular, dialoglar va kroy xatti-harakati
   MebeliX Kroy bilan yonma-yon solishtirildi (faqat funksional ma'no o'rganildi; kod, kalit, ikonka, matnlar olinmadi).
2. 205 ta real `.project` fayli bo'yicha avvalgi dastur saqlagan natijalar bilan raqamli solishtirish (`tools/bench`).
3. Uch mustaqil QA agenti (loyihalar/operatsiyalar/sozlamalar; CS kroy ekranlari; EL/GR/XNC/import/hisobot/MES) har biri
   alohida server va bazada Playwright orqali sinadi → 70+ nuqson. Ikki tuzatuvchi agent + koordinator tuzatdi.

## 2. GibLab bilan solishtirishdan topilgan va tuzatilgan asosiy narsalar
| Topilma | Tuzatish |
|---|---|
| **«Листы и остатки» ro'yxati — ustuvorlik tartibi.** GibLab ro'yxatni ochganda soni bo'yicha o'sish tartibida saralaydi (cheklangan qoldiq/qirqim listlar birinchi, `10000` «cheksiz» list oxirida) va kroyni shu tartibda bajaradi. Importer fayl tartibini olar, qoldiqlar umuman ishlatilmasdi. | `plugins/legacy_project.py` — tartib; `optimizer.py` — list tartibi variantlari, material maydoni bo'yicha tanlash, qoldiqqa ko'chirish, qoldiq birinchi qidiruv. 44 ko'p-listli kroyda material 608.2 → 574.0 m² (GibLab 581.9). |
| «Общие действия» da GibLab'da 6 ta amal bor | Qo'shildi: **«Перекодировать XNC»** (takror kodli XNC dasturlar -2, -3 …); hisobot ochilganda ogohlantirish. «Очистить проект»/«Пересчитать параметричность»/«KDT Sort line» — ma'nosi noma'lum, qilinmadi. |
| «Изделия → Свойства» faqat nom so'rardi | To'liq oyna: Общие, Данные заказа (`product.order`), Дополнительные параметры (`product.import = …`), Описание, Сообщения; importdan to'ldiriladi. |
| Umumiy ko'p kalitli «Сортировка» oynasi yo'q edi | `SortDialog` (Вкл / Напр / ↑↓ ustuvorlik) — Операции, Изделия, Детали. |
| Excel import profillari yo'q edi | `excel_import` profillari (ustun xaritasi + boshlang'ich qator). Avto-moslash tuzatildi («Длина детали» nom emas). |
| GibLab ro'yxatni saqlab qo'yadi (kroy/o'chirish — avtomatik saqlash) | Hujjatlandi: haqiqiy loyihalarda tajriba o'tkazilmaydi (CLAUDE.md qoida 12). |
| Chrome avtotarjimasi interfeysni inglizchaga aylantirardi | `index.html`: `translate="no"` + `notranslate`. |

## 3. QA topilmalari — tuzatilganlar (qisqa)
**Loyihalar ro'yxati:** tanlov fokusga ergashadi (noto'g'ri loyihani o'chirish xavfi yo'q), ko'p tanlov, Ctrl+A, F4, Ctrl+PgDn,
Shift+Del, «Выделить все», «Справка», sarlavha bo'yicha saralash (papkalar yuqorida), kirillcha qidiruv (katta-kichik harf),
`%`/`_` wildcard emas. **Jadvallar:** № ustuni tartib o'zgarganda yangilanadi; bo'sh katak 422 bermaydi; yangi kromka nomi
darhol tahrir rejimida; Ctrl+PgUp/PgDn/Insert. **Dialoglar:** Esc matn maydonida ham yopadi; tasdiq tugmasida fokus (Enter).
**Til:** `<html lang>`, server tilining yangi brauzerda qo'llanishi. **Sozlamalar:** varaq o'lchami/valyuta/profil nomi
tekshiruvi, zaxira importi dublikat yaratmaydi, 422 xabarlari tilga mos. **Tarix:** «Оптимизировать операции» bitta Ctrl+Z,
«Сохранить» bo'sh versiya yozmaydi. **CS:** parametr o'zgarishi natija/ombor qoldig'ini o'chirishdan oldin tasdiq; Ctrl+V da
«Д-на»dan boshlansa spetsifikatsiya tartibi, tashlab yuborilgan qatorlar haqida xabar; list/parametr chegaralari; kartada
kromka harfi, vertikal «en» kesilmaydi, g'ildirak xatosi yo'q; № ustunini ikki marta bosish — detal xossalari.
**Hisob-kitob:** XNC o'lcham/soni detal bilan sinxron; GR uzunlik/narx/hisobot; XNC ifodalari (`min/max/floor/ceil/tan`,
taqqoslash, `a if c else b`, J3 o'zgaruvchilari, If/Else/While/Sub/Call), yoylar chizmada; ombor «arvoh» qoldig'i
(A, keyin B bekor qilinganda) tuzatildi; hisobotda «Зеркально» matnni aks ettirmaydi; EL «умолч.» belgi/rangni saqlamaydi;
o'lchami 0/manfiy detal va qalin kromka jim yo'qolmaydi (ogohlantirish + `unplaced`); sahifalashda karta sarlavhasi
kartasidan ajralmaydi. **Server:** server tekshiruvlari (qiymat chegaralari, `folder_id`, mahsulot soni), MES qayta yuborish
lokal ma'lumotni yo'qotmaydi, webhook-test haqiqiy natijani qaytaradi (+qayta urinish), `{ref:path}`, JWT rollari (viewer
faqat o'qiydi), `.project` import (yoylar, koordinata boshi, massiv, GR, epoch sanalar, oversize list soni), Excel import
(`1 200,5`, `2 шт`, noma'lum kromka → yangi EL, cp1251 CSV, `skipped`/`warnings`).

## 4. Hali ochiq (ma'lum, qasddan qoldirilgan)
- **Foydalanuvchidan javob kerak:** (1) kromka qalinligi (PVC 1 mm) loyihalarda 0 — shunday qolsinmi; (2) arra stanogi
  modeli va postprotsessor formati (namuna fayl) — GibLab 19 xil stanok tayyor formati beradi, bizda shablon tizimi;
  (3) MES API manzillari/autentifikatsiya/webhook formati; (4) etiketka printeri va o'lchami; (5) **«Минимальная
  обрезка» ma'nosi**: validator `qoldiq + propil ≥ min` deb tekshiradi (propil 3, min 5 da 2 mm li chiqindi chiqishi
  mumkin) — spetsifikatsiya C3 «qoldiq ≥ propil+min» deydi; GibLab'da qaysi biri?
- Yangi loyiha 1 ta bo'sh CS «Материал1» bilan ochilishi (D1) — GibLab'da tasdiqlanmagan, qilinmadi.
- Каталог товаров oynasi (kategoriyalar daraxti, rasm), Ctrl+P ustun profillari Операции uchun, Свойства → «Программа»
  (parametrik mahsulot), «Режимы ввода деталей» taklifi bo'sh jadvalda, XNC Редактор sozlamalari (asboblar/palitra),
  «Сохранение отчетов», «Сервисы» jadvali, O/CL/SP/LB/CN operatsiyalari, DXF import, `.project` eksport.
- Optimizator: 2 ta ko'p-listli kroyda (1014 so'qoq, 1071 Mirshoxid kuxniya) GibLab juda zich joylashuv topgan;
  «Большой пакет» faqat «Процент заполнения для кратности» (90 %) dan yuqori kartalarni takrorlaydi (mo'ljallangan).
- `GET …/report.pdf` — `weasyprint` kerak (Windows'da GTK talab qiladi); PDF uchun brauzer «Chop etish → PDF».
- PostgreSQL yo'li (qidiruv `lower()`/`ESCAPE`) bu muhitda sinalmadi.

## 5. Tekshiruv natijalari (oxirgi)
- Backend: **223** test o'tdi (avval 91). Playwright e2e: **5** ssenariy (avval 3).
- Korpus (`compare.py normal`): **1186 list vs 1212** (15 kroyda kam, 1 da ko'p), деловой qoldiq 750 vs 652 m², xato 0.
- Ko'p-listli (`compare_stock.py`): **574.0 m² vs 581.9 m²** (6 kam, 36 teng, 2 ko'p), xato 0.
- Kromka 303/303, CNC teshik 8359/8360, freza 8360/8360, arra 8360/8360 (o'zgarmadi). 210 ta real fayl importi — 0 xato.
- Jonli GibLab bilan «1230 Jamshid 04 shkaf»: 1-kroy F 68.55 % / kesish 15.95 m, 2-kroy 1770×1830 F 92.12 % — GibLab bilan aynan bir xil.
- Ekran nusxalari: `docs/mebelix/screens_v3/`.
