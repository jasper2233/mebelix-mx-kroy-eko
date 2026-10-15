# U. Ochiq savollar (v2.3) — hozirgi standart bilan

Har qatorda: savol → hozir nima qilingan (konstanta orqasida; javobga qarab bir joydan almashtiriladi). Paket hujjatlari: `T_*.md`.

## A. Tezda tekshiriladigan (GibLab oynasida 1–2 daqiqa)
| № | Savol | Hozir |
|---|---|---|
| A1 | XNC ifodasida `sin(90)` va `7/2` | radian; butun÷butun — butun (`xnc.XNC_DEGREES=False`) |
| A2 | «Минимальная обрезка»: propil 3 / min 5 da 2 mm li tilim chiqadimi | validator: `qoldiq + propil ≥ min` |
| A3 | «Минимальный размер детали» — kichik detal kroyga kirmaydimi yoki faqat ogohlantirishmi | kroyga kirmaydi + ogohlantirish |
| A4 | XNC «Режим» (Ограничения) qiymatlari | `off / warn / block` (taxmin); `block` eksportni to'smaydi |
| A5 | SP: lits/orqa tomon formatda qanday; `spSizeMode` standarti; `spRestSide` (har chetda 2r yoki r) | birinchi SP — lits; −1 (pilniy); har chetda r |
| A6 | Mahsulot «Программа» detal o'lchamiga ta'sir qiladimi; `Err` nimani bloklaydi | ta'sir qilmaydi; faqat xabar va ⚠ |
| A7 | `Номер → nomga` formati (Excel), Excel «Дата» ustuni | nomning oldiga («3 Полка»); `ready_date` |

## B. Korxona qarorlari
| № | Savol | Hozir |
|---|---|---|
| B1 | Yangi CS uchun burilishlar soni | 6 (xodimlar 4 ishlatadi) — 4 qilinsinmi? |
| B2 | «Утвержден»/«Готов» ni kim qo'ya oladi; holatni o'tkazib yuborish; orqaga qaytarish | yozish huquqi bor hamma rol; o'tkazib yuborish ruxsat; orqaga — faqat admin/texnolog |
| B3 | Tasdiqlangandan keyin tahrirni bloklash | o'chiq (faqat ogohlantirish; `MEBELIX_ORDER_LOCK_FROM`) |
| B4 | «Исп. кол-во» (mijoz olib ketgan qoldiq); mayda qoldiq va butun list omborda | standart eski xulq; mayda/butun — o'chirilgan katakchalar |
| B5 | Qoldiq rezervi: muddat; kim bo'shata oladi | muddatsiz; hamma |
| B6 | Qo'lda tahrirdan keyin деловой qoldiqni omborga yozish taklifi | bor («Позже» bilan yopiladi) |
| B7 | Etiketka printeri (A4 2×4 yoki 58×60.5 termo/ZPL); `part.counter` ma'nosi; qoldiq etiketkasi faqat деловойми | A4 varaq; nusxa raqami; hamma qoldiq |
| B8 | CL: korxonada ishlatiladimi (205 loyihada 0; 1248 da 3, hisoblanmagan) | to'liqlik uchun tayyor; manfiy `l` → `length=0` + ogohlantirish |
| B9 | O narxi mahsulotlarga taqsimlansinmi | yo'q (loyiha darajasida) |
| B10 | Katalog: rasm manbasi, ildiz kategoriya ID lari | data-URI/URL yuklash; brauzerda saqlanadi |

## C. Maxsus ma'nolar (GibLab hujjatida yo'q — taxmin)
- **XNC:** `MillRect` (X,Y) markazmi; `MillEllipse` RL/RW yarim o'qmi; `MillFillet`; `sdp/sxy` uzunlikka kiradimi; qirra teshigi `m`/`ver`; «Разворачивать деталь кromkoy в углу» — qaysi kromka (hozir: birinchi kromkali tomon, `CORNER_EDGE_RULE="first"`); paz chetidan masofa barcha tomondanmi; freza masofasi; Палитра (31 buyruq).
- **Etiketka:** standart nomli `par` qiymati sinov qiymatimi; `y` — baseline; `fontSize` — mm; `xy` — nisbiy siljish; `fillHatch`; qoldiq qatorida `length/width/count`; Code128 eksport uchun teg nomi.
- **Postprotsessor sozlamalari:** Maestro/CadMatic4/OSI jadvallarining oxirgi qatorlari va ro'yxati to'liq ko'rinmagan tanlovlar variantlari (skrinshot/matn kerak); `mill/drill/groove` qiymat turi; Holzma PTX «Шаблон имени файла».
- **CL:** optimizator maqsadi (kam material / kam sarf), F foizi maxraji, qoldiq-polosa ustuvorligi, `cBusinessWaste` birligi (m), «по полосам» yaxlitlash, buyruqlar jadvali va otxoddan keyingi kesim, 45° kesim.
- **CSE:** «Торцовка листа» tahrirda nima uchun; ro'yxatdan detalni oddiy bosish bilan qo'yish; Shift+W xulqi; parallel tahrirda 409 (qayta ochish yetarlimi).
- **Buyurtma:** MES webhookida tayyorlik sanasi; `PATCH {status}` sanasiz ishlashi; «Готов» uchun qat'iy shart; «Очистить проект» (hozir: faqat kroy natijalari); «KDT Sort line»; `merge-same` da list zaxiralari.
- **`.project` eksport:** `version="1"` GibLabda ochiladimi (nusxada sinab ko'ring); `max_rotations=1` eksportda 2 ga ko'tarilsinmi (onlayn ro'yxat 2…6).
- **Parametrik mahsulot:** `.project` da mahsulot `program` xml tegi nomlari (namuna kerak); `product.<nom>` o'zgaruvchi nomlash.

## C2. 4-to'lqin (W15–W18) savollari
- **ZPL:** printer modeli/DPI va etiketka o'lchami (58×60.5 yoki 58×40); kirill uchun printerdagi TTF; «ZPL Header» odatdagi matni; logotip (`^GFA`) kerakmi — **ZPL ni haqiqiy printerda (yoki Labelary da) sinab ko'rish kerak**.
- **Nesting (CN):** freza korreksiyasi (kontur = tayyor chegara yoki asbob markazi yo'li); ko'prikchalar, ichki konturlarni birinchi kesish, kirish/chiqish yoyi; qoldiq qoidalari (300/150 mm, 0.1 m²); detallar orasi 6 mm + list cheti 5 mm; vaqt (`fast/normal/max` = 3/10/40 s); G-code formati (KDT va h.k.) — namuna.
- **OEE:** smenadan tashqari ishlab chiqarish OEE ga kirsinmi; «buyurtma yo'q» rejalashtirilmagan to'xtashmi; `idle` chegarasi (5 min); haqiqiy kesish tezligi/kesim almashinuvi/list yuklash vaqti (taxmin: 1000 mm/s, 5 s, 25 s); ishlab chiqarilgan birlik (karta yoki detal); sabab kodlari MES bilan; smena kalendari (Du–Sha 08:00–17:00, UTC+5).
- **Import infratuzilma:** qaysi CAD namunasi birinchi; Excel «Простые операции/Материалы» tarkibi (mijoz fayli); «Ширина» bo'sh qator CL ga tushsinmi (hozir yo'q); XNC ustuni kodi (shablon yoki mavjud operatsiya); orqa yuza akslanishi (chap↔o'ng yoki yuqori↔past).
- **CL variantlari:** 4 variant to'plami va «До кроить» ma'nosi to'g'rimi; omborga yozilgan qoldiq-polosa «qolgan» hisoblanadimi.

## D. Berilishi kerak bo'lgan fayllar
`.xls/.xlsx` Excel namunasi (mijoz ismlarisiz), goods.xls, mahsulot dasturi bor `.project`, real CL fayli GibLab natijasi bilan, Woody2/BCAD/ABF/PRO100/Imos/iLENIA/mpr namunalari (importerlar uchun).
