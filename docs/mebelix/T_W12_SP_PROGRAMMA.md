# T. W12 — (SP) «Обработка поверхности» va mahsulotning «Программа» yorlig'i (parametrik mahsulot)

Manba: `.project` format tavsifi (SP atributlari: `spCalcMat`, `spWastePRC`, `spRestSide`, `spSizeMode`, `spCost`; mahsulot `program` —
«Программа с параметрами, переменными и ограничениями»), onlayn ko'rik (`giblab_inventory/06_online_korik.md`: «Свойства» → «Программа»,
palitra Com Par Var Set IF Else WD DW Brk Con Sub Call Ret Msg Err), XNC evaluatorimiz (W1). **SP yordami GibLabda yo'q**, mahsulot
dasturining teg/atribut nomlari ham hujjatda yo'q — shuning uchun «❓» bilan belgilangan qarorlar bitta konstanta orqasida va
quyidagi «Savollar» ro'yxatida.

## 1. (SP) Обработка поверхности

**Model** (`models.SPParams`, `Operation.sp`): `count_material` (spCalcMat), `waste_percent` (spWastePRC), `rest_side` (spRestSide, mm),
`size_mode` (spSizeMode: −1 pilniy, 0 zagotovka; standart `SP_DEFAULT_SIZE_MODE = −1` ❓), `op_price` (spCost — 1 m² ish narxi),
`price` (material 1 m² narxi: katalog / material `good.cost`), hisoblangan `area_m2`, `material_m2` (faqat o'qish).
Detalga bog'lash — `Part.surface_face_op` / `surface_back_op` (modelda avvaldan bor edi; eski JSON o'zgarishsiz ochiladi). Standart —
`sp_defaults` sozlamasi (`PUT /api/settings/sp_defaults/default`; hisoblangan maydonlar saqlanmaydi).

**Hisob** (`calc.surface_usage`, har saqlashda `recalc_project`):
```
L × W          = pilniy o'lcham (size_mode −1: zagotovka + pripusk + «Припуск на обработку») yoki zagotovka (0)
ishlov maydoni = Σ L×W × tomonlar (lits/orqa, 0..2) × (ОК − МК)                       [m²]
material sarfi = Σ (L+2r)×(W+2r) × tomonlar × (ОК − МК) × (1 + chiqit %)               [m²]   (faqat «Учитывать материал» ✓)
cost_operation = ishlov maydoni × spCost;   cost_material = material sarfi × material narxi
```
`REST_BOTH_EDGES` (`sp_ops.py`): `True` — qoldiq har chetda (2·r), `False` — bir chetda (r) ❓. Yaxlitlash kodi yo'q (formatda yo'q).
Mahsulot narxiga ishlov maydoni ulushi bo'yicha taqsimlanadi (`product_costs`); ombor talabnomasida qator `SP` (material sarfi, m², narx, summa);
hisobotda «(SP)» bo'limi (`PrintSettings.sp_params` / `sp_parts`, `services/sp_render.py`); MES eksportida `area_m2` / `material_m2`.
Operatsiya o'chirilsa (yoki yetim havola qolsa) detaldagi havolalar tozalanadi (`delete_operation`, `calc.prune_surface_refs`).
Sirt ishlovi bog'lanishi kroyni eskirtirmaydi (`_PART_NON_CUT`).

**UI:** `features/sp/SpPanel.tsx` — «Параметры» | «Детали» (EL/GR panellari kabi; `OpPartsGrid` qayta ishlatilgan, `GET …/surface-usage`);
detal «Свойства» oynasida «(SP)» bo'limi (Лицевая / Обратная), detallar jadvalida ixtiyoriy ustunlar «ЛП / ТП» (`surface_face` / `surface_back`,
EL ustunlari kabi tahrirlanadi), «Печать отчета» → «(SP) Обработка поверхности», `IMPLEMENTED` da SP, katalogdan «surface» materiali SP ga aylanadi.

**Etiketka (W4):** `surface.front.{has,name,code}`, `surface.back.{…}` + taxalluslar `surfFront`, `surfBack` (= SP operatsiya nomi; inventar LB-070).

**`.project` importi** (`sp_ops.from_project_xml`, `link_parts`): `spCalcMat/spWastePRC/spRestSide/spSizeMode/spCost`; material (`<material id>` → `good`)
nom, kod va narx beradi, bo'lmasa `typeName`. Detallarga havolalar — operatsiyaning `<part id>` bolalari. **Format detal atributida lits/orqa
tomonni tavsiflamaydi ❓** → birinchi SP — lits (old) tomon, detal ikkinchi SP ga ham havola qilsa — orqa; har SP uchun bitta ogohlantirish.
Real korpusda SP yo'q (0), shuning uchun sintetik testlar. **W10 eksporti** (`project_export._sp`) shu atribut nomlarini yozadi
(`spCalcMat spWastePRC spRestSide spSizeMode spCost`, `<part id>` bolalari; material narxi eksportda tushib qoladi — W10 ogohlantiradi).

**Excel importi (W3) uchun bog'lanish nuqtasi** (XLS-009, «(SP) Обработка поверхности» ustun guruhi) — W3 fayllariga tegilmadi:
`services/sp_ops.find_or_create(project, matn)` (kod yoki nom bo'yicha mavjud SP, bo'lmasa standart parametrlar bilan yangisi; `EdgeResolver` kabi) va
`sp_ops.attach(part, "front" | "back", sp_op | None)`. Ustun → tomon xaritasi W3 ning ishi.

## 2. Mahsulot «Программа» (parametrik mahsulot)

**Model:** `Product.program: list[XncCommand]` (xuddi shu `XncCommand`; ruxsat etilgani — `Com Par Var Set If Else While DoWhile Break Continue Sub Call Ret Msg Err`,
≤ 5000 buyruq), `Product.par_values` (kiritilgan Par qiymatlari, W1 `XNCParams.par_values` kabi), `Product.legacy_program` (importda tushunilmagan dastur matni),
hisoblangan (faqat o'qish): `prog_vars` (`{nom: son}`), `prog_messages` (`[{level: info | warning | error, text, path}]`). Eski JSON da maydonlar yo'q — bo'sh dastur.

**Hisob** (`services/product_program.py`): XNC evaluator'ining «quruq» rejimi — `xnc.evaluate_control` (`_Run(dry=True)`; kichik refaktor:
dx/dy/dz va detal o'zgaruvchilari yo'q, geometrik buyruq bajarilmaydi — ogohlantirish «Программа 5: DrillFront … bajarilmaydi»; `Msg`/`Err` xabarlari yig'iladi).
Ifodalar — `expr.py`; Par/tsikl/qadam chegaralari XNC bilan bir xil (sikl ≤ 10 000, jami ≤ 100 000 qadam, chaqiruv chuqurligi ≤ 32). Dasturda `product.qty`
va `product.index` ko'rinadi. Natija har saqlashda (`calc.recalc_project` → `product_program.apply`) mahsulotga yoziladi; dasturi yo'q mahsulotga tegilmaydi.
- `Msg` → `info`, `Err` → `error` («cheklov buzildi»; hisob davom etadi, hech narsa bloklanmaydi ❓), ifoda/dastur xatosi → `warning`.
- `PROG_MSG_INTERPOLATE = True` ❓: `Msg`/`Err` matnidagi `{ifoda}` qiymat bilan almashtiriladi (yordamda yo'q; o'chirib qo'yish mumkin).
- Xato jim 0 ga aylanmaydi: noma'lum o'zgaruvchi, 0 ga bo'lish va h.k. — `warning` xabari.

**Kontekst `product.<nom>`** ❓ (GibLab hujjatida yo'q — bizning qaror): dasturning Par/Var/Set o'zgaruvchilari
- XNC ifodalarida: detalga bog'langan XNC operatsiyasining `part_vars` ga `product.<nom>` sifatida yoziladi (`calc.sync_xnc`),
- etiketka (va W7 ishlov markazi konteksti) ifodalarida: `EnvBuilder._product` — detal va mahsulot qatorlarida (dasturi yo'q mahsulotda — 0, xato emas).
Mavjud standart nomlar (`index name code qty count description phone1 phone2 date order`) bilan to'qnashsa — **mavjud ustun**: dastur o'zgaruvchisi
uzatilmaydi va ogohlantirish beriladi (`RESERVED_NAMES`, `CTX_PREFIX`). Faqat sonlar uzatiladi. Cheklov: etiketka muharririning
«tekshirish» (namuna qatori) rejimi loyihasiz ishlaydi — `product.<nom>` ishlatilgan shablon u yerda «noma'lum o'zgaruvchi» deb ko'rinadi, haqiqiy chopda ishlaydi.

**API:** `PATCH /projects/{pid}/products/{prid}` (`{program, par_values}`), `GET …/products/{prid}/program-state` (Par holati, o'zgaruvchilar, xabarlar — so'rov tilida).

**UI:** `ProductProps.tsx` — «Свойства» | «Программа» yorliqlari. «Программа»: chapda `features/xnc/ProgramEditor.tsx` (boshqaruv buyruqlari palitrasi, ichma-ich
daraxt — W1 `treeOps.ts`, `XncProgramTab.ParamRow`), o'ngda «Параметры» (W1 `ParForm`, `Par` kiritish maydonlari), «Переменные изделия» (`product.<nom>`) va
«Сообщения» (info/ogohlantirish/xato). Ro'yxat «Свойства» yorlig'idagi «Сообщения» ga ham qo'shiladi; loyiha sarlavhasida ⚠ belgisi (Err / xato soni, bosilsa «Изделия»).
`XncProgramTab.tsx` ga faqat `export` qo'shildi (`ParamRow`, `defaultFor`); ParForm — `x: Pick<XNCParams,"par_values">`, ixtiyoriy `title/hint`.
Keyingi bosqich (W8 tugagach): XNC «Шаблон» muharririni ham `ProgramEditor` ga o'tkazib, dublikatni yo'qotish.

**`.project` importi** (`product_program.from_xml`): mahsulot `program` (xml) atributi. **Teg/atribut nomlari hujjatda yo'q (real korpusda mahsulot `program` 0 ta) ❓** —
taxmin: teg = buyruq nomi kichik harfda (`par var set if else while dowhile break continue sub call ret msg err com`, qisqa `wd dw brk con`), atributlar `name`,
`value|expr`, `cond|expr|condition`, `text|msg`, `label type visible suffix readonly`, `comment`, `enable`. Tanilmagan (yoki geometrik) teg jim o'tkazilmaydi:
ogohlantirish + asl matn `legacy_program` da saqlanadi (W10 eksporti uni qaytarib yozadi), mahsulotda «tanilmagan buyruqlar bajarilmaydi» ogohlantirishi turadi.
O'qilmagan xml / 5000 dan ortiq buyruq / chuqurlik > 32 — xuddi shunday.

## 3. «Пересчитать параметричность» (taxminiy ma'no ❓)

Lokal GibLab «Общие действия» dagi punkt, ma'nosi hujjatlanmagan (XNC changelog 20.08.03: «shablonda parametrikni qayta hisoblash»). Bizda: `POST /projects/{pid}/actions/recalc-parametric` —
hamma mahsulot dasturlari qayta hisoblanadi, mahsulot o'zgaruvchilari XNC `part_vars` ga yangilanadi, har XNC dasturi ifodalari qayta baholanadi;
javob `{project, report: {products, xnc, totals}}` (xato/xabarlar bilan). Ma'lumot o'zgarmagan bo'lsa tarixga bo'sh versiya yozilmaydi. Dialogda bitta punkt; natija — toast (qisqa xulosa).
Ifodalar bizda har saqlashda jonli hisoblanadi, shuning uchun amal asosan «tekshiruv + eskirgan holatni tuzatish» vazifasini bajaradi.

## 4. Testlar
`tests/test_sp_w12_calc.py` (27: model, formulalar, rejimlar, ombor, narx taqsimoti, API, eski JSON, hisobot, MES, etiketka, import, Excel hook),
`tests/test_product_program_w12.py` (30: Par/Var/If/Else/While/DoWhile/Sub/Call/Ret/Msg/Err, tsikl va chuqurlik chegaralari, geometriya/`dx`, nomlar qoidalari,
API va chegaralar 422, `product.<nom>` XNC va etiketkada, import, action, eski JSON). XNC korpusi (`tools/bench/xnc_check.py`) 8359/8360/8360 — o'zgarmadi.

## 5. Savollar (foydalanuvchiga)
1. **SP tomoni `.project` da**: format detal atributida lits/orqa SP havolasini ko'rsatmaydi. Hozir: birinchi SP — lits, ikkinchisi — orqa. To'g'rimi? (GibLabda SP li detalni saqlab, faylni ko'rsatish kerak.)
2. **`spSizeMode` standarti** (−1 pilniy yoki 0 zagotovka) va **`spRestSide`** (har chetda 2·r mi, bir chetda r mi) — GibLabda tekshirish kerak.
3. **Parametrik mahsulot detal o'lchamini boshqaradimi?** Hozir dasturning Par/Var natijasi faqat `product.<nom>` sifatida XNC va etiketka ifodalarida ko'rinadi, detal uzunligi/eniga ta'sir qilmaydi.
   Real GibLabda mahsulot dasturi detallarni o'zgartirsa — qanday (ifoda detal o'lchamida)? Namuna kerak.
4. **`Err` nima qiladi?** Hozir faqat xabar + sarlavhada ⚠ (kroy / «Заказать» bloklanmaydi). Bloklash kerakmi?
5. **`product.<nom>` qarori** (XNC/etiketka konteksti) va `Msg`/`Err` matnida `{ifoda}` — to'g'rimi yoki GibLabda boshqacha?
6. **Mahsulot `program` xml teglari** — namuna `.project` (mahsulot dasturi bor) kerak; hozirgi nomlar taxmin.
7. **«Пересчитать параметричность»** ma'nosi (yuqoridagi taxmin to'g'rimi?).

## 6. Boshqa paketlarga ta'siri
- W3 (Excel): `sp_ops.find_or_create` / `attach` (yuqorida). W10 (eksport): SP va `program`/`legacy_program` ishlatiladi (`_sp`, `_product_attrs` allaqachon moslangan).
- W4/W7/W9 (etiketka, ishlov markazi kontekstlari): `label_vars` ga `surface.*`, `surfFront/surfBack`, `product.<nom>` qo'shildi (`VARS` 152 → 158).
- W1/W8 (XNC): `XNCParams.part_vars` ga `product.<nom>` kalitlari qo'shilishi mumkin (nuqtali nom; `_Run` ularni o'zgaruvchi sifatida o'qiydi); `xnc._Run` ga `dry` rejimi, `EvalOps.notes/violations/vars`
  qo'shildi (oddiy XNC hisobi o'zgarmadi). `Msg` endi `notes` ga tushadi (XNC hisobiga ta'sirsiz).
- `render.fmt` (umumiy) `:g` format ishlatadi — 6 raqamdan ortiq sonlar «1.13283e+06» bo'lib chiqadi (loyiha sarlavhasi, EL/GR qiymatlari). SP bo'limi o'z formatlovchisini ishlatadi; umumiy `fmt` ni tuzatish — W-egasi / yetakchi ishi.
