# J. XNC (CNC ishlov) — spetsifikatsiya

Xodimlar loyihasida XNC operatsiyalari bor (masalan «0000x005x0 № Панель»: 480×800 detalda
to'g'ri to'rtburchak frezalash; dastur: `N=Mill20 D=20`, `Var double contMillDepth=dz`,
`X=350 Y=400 DP=contMillDepth T=Mill20`, keyin 5 ta chiziq). Shuning uchun XNC kamida
**saqlash, ko'rsatish, narxlash va chizmada chop etish** darajasida kerak.

## J1. Operatsiya parametrlari (UI «Параметры»)

Изделие · Материал · Наименование · ☑ По размеру детали · Длина (DX) · Ширина (DY) · Толщина (DZ) ·
Количество · ☑ Лицевая сторона · Поворот (0°/90°/180°/270°) · Зеркало (X, Y) ·
Начало координат (Левый верхний / Правый верхний / Левый нижний / Правый нижний угол) · Стоимость · Описание.
O'ngda detal chizmasi (kromkalar harf bilan). Toolbar: Выбрать деталь · XNC Редактор · Кодирование ·
Отменить деталь · Свойства · standart saqlash · Открыть (shablonlar papkasidan) · Сохранить · Справка ·
Постпроцессор (CNC formatiga) · Импорт из DXF.

## J2. Dastur modeli

`XncCommand{cmd, params{}, enabled, comment, children[]}`. Parametr — son yoki **ifoda** (satr).
**Qoida:** atribut berilmasa — shu turdagi oldingi buyruqdagi qiymat ishlatiladi (X, Y, DP, T …).

| MebeliX `cmd` | GibLab tegi | Parametrlar |
|---|---|---|
| Tool | tool | name, D (diametr) |
| DrillFront | bf | name, X, Y, DP (chuqurlik), AC (massiv soni), AS (qadam), AV (vertikal massiv) |
| DrillLeft / DrillRight | bl / br | name, Y, Z (yoki M — o'rtada), DP |
| DrillTop / DrillBottom | bt / bb | name, X, Z (yoki M), DP |
| MillStart | ms | name, X, Y, DP, SDP (chuqurlikka qadam), C (korreksiya: 0 markaz, 1 o'ng, 2 chap, 3 cho'ntak — XNC ekran koordinatasida, Y pastga; stanok fayllarida Y yuqoriga bo'lgani uchun 1 → «chap»: Homag WRKL, TPA #40=1, Biesse CRC=2), SXY (tekislikdagi qadam, standart d/2), IN, OUT (kirish/chiqish turi) |
| MillLine | ml | X, Y, DP |
| MillArc | ma | X, Y, DP, R (manfiy — yo'nalish), DIR (soat mili bo'yicha) |
| MillArcCenter | mac | X, Y, CX, CY, DP, DIR |
| MillArc3P, MillFillet, MillRect, MillEllipse | — | yoy 3 nuqta (X2, Y2 — oraliq), yumaloqlash (R; qo'shni MillLine lar orasida), to'rtburchak (X, Y — markaz; L, W, A burilish, R burchak radiusi, DP, T, C), ellips (X, Y — markaz; RL, RW — yarim o'qlar, A) — T_W1_XNC.md |
| Groove | gr | name, X1, Y1, X2, Y2, T (en), DP, C (0 markaz, 1 o'ng, 2 chap) |
| Origin | xy | X, Y |
| Com, Par, Var, Set, If, Else, While, DoWhile, Break, Continue, Sub, Call, Ret, Msg, Err | — | boshqaruv: izoh, parametr, o'zgaruvchi, qiymat berish, shart, sikl, qism-dastur, xabar/xato |

**Freza kirish/chiqish kodi «RQG»** (masalan `213`): G — tur (0 avto, 1 tik tushish/ko'tarilish,
2 urinma bo'ylab, 3 yon yoy bo'ylab); Q — Z bo'yicha qiyalik bilan (1) yoki yo'q (0); R — asbob radiusi
ko'paytmasi 1..5 (0 — stanok standarti). `mill_entry_code("213") → R=2,Q=1,G=3`. Stanok dasturiga moslash
(WoodWop, Xilog) — postprotsessorda.

## J3. Ifodalardagi o'zgaruvchilar

`dx, dy, dz` (zagotovka) · `allowanceT/B/L/R` (pripusklar) · `etj, ett, ebj, ebt, elj, elt, erj, ert`
(kromka: j — prifugovka eni, t — qalinlik; t/b/l/r — tomon) · `origin.x, origin.y` · `xncSide` (1 lits, 0 orqa) ·
`bySizeDetail` · `xncIndex, xncIndexInPart` (kodlash uchun) · + Var/Par/Set orqali e'lon qilinganlar.
Funksiyalar: umumiy dvigatel `services/expr.py` (67 funksiya, `if(c,a,b)`, `=`/`<>`, `^`, `xor`; trig — radian). `Par` qiymatlari
(`XNCParams.par_values`) ham o'zgaruvchi (T_W1_XNC.md §3).
Xavfsiz hisoblagich: `services/xnc.py::eval_expr` (eval ishlatilmaydi).

## J4. Narx va statistika

`Стоимость единицы = teshiklar × Цена сверления + frezalash (m) × Цена фрезеровки + paz (m) × Цена пазования + Дополнительная стоимость`;
`Стоимость операции = birlik × Количество`. Hisob: `program_stats()` (teshiklar soni, frezalash va paz uzunligi).

## J5. Detal bilan bog'lash

* Detal xossalari → «Операции» → «Добавить: (XNC) Обработка» — detalga XNC biriktiriladi (`xnc_part_id`,
  `Part.xnc_op_ids`), «По размеру детали» ✓ bo'lsa DX/DY/DZ detal o'lchamidan.
* Detal jadvalida `№` yonida `'`, hisobotda nom ostida `P1-1: <kod>`.
* Kodlash (Кодирование): dastur nomi shabloni (masalan `0000x005x0` — o'lcham/indeks), ifodalar bilan.

## J6. Postprotsessor qoidalari (CNC)

«Detalni kromka tomoni bilan burchakka burish» (afzallik va majburiy cheklov: chap-yuqori/chap-past/
o'ng-yuqori/o'ng-past), «uzun tomon gorizontal/vertikal» — detalni stanok stoliga to'g'ri joylash uchun.
Birinchi bosqichda: dasturlarni JSON/XML eksport; aniq stanok formati keyin (qaysi stanok — aniqlanadi).

## J7. Bosqichlar

1. (hozir) Saqlash, import (GibLab XML), narx, detal chizmasida ko'rsatish, hisobot shtampi.
2. Grafik redaktor (chizish paneli, dastur daraxti, xossalar, holat F9, o'zgaruvchilar paneli).
3. Parametrik shablonlar kutubxonasi (ruchka teshiklari, fasad frezalari), DXF import, postprotsessorlar.
