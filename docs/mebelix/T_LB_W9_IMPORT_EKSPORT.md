# T-W9. LB — etiketka shablonlarini fayldan import va faylga eksport (LB-D)

Ruxsat va chegara (foydalanuvchi so'zlari, 2026-10-02): «tizim ommabop bo'lishi kerak, mijoz ixtiyori muhim … tayyor fayl import qilish va
eksport qilish ketyapti, noldan yasash emas». Demak: **mijozning o'z fayllari** ish vaqtida import/eksport qilinadi; boshqa dasturning
namuna shablonlari, rasmlari va matnlari bizning kodga, testlarga va repoga **kiritilmaydi** (testlar sintetik: `tests/w9_fixture.py`).
Dastur, kalit, litsenziya va yordam matnlariga tegilmaydi; eksport faylini boshqa dasturda ochib tekshirilmagan.

## 1. Nima bor

| Band | Holat |
|---|---|
| Importer `services/label_gl_import.py`: `<program>` XML → W4 JSON shabloni (+ `warnings`) | ✅ |
| Eksport `services/label_gl_export.py`: JSON shablon → `<program>` XML (+ `warnings`) | ✅ |
| Umumiy yordamchilar `services/label_gl_common.py` (xavfsiz XML, chegaralar, o'zgaruvchi nomlari, ifoda siljishi) | ✅ |
| API `POST /api/labels/import-file`, `POST /api/labels/export-xml`, `GET /api/label-templates/{id}/export-xml` (`api_label_io.py`) | ✅ |
| `.project` importi: LB operatsiyasining `program` i avtomatik shablonga o'giriladi (`label_import.py`) | ✅ |
| UI: «Импорт из файла» oynasi, «Экспорт JSON», «Экспорт XML» (`features/print/LabelImport.tsx`, «Шаблон» yorlig'i) | ✅ |
| Testlar `tests/test_labels_w9_import.py`, `test_labels_w9_export.py` (64 ta, sintetik fikstura `tests/w9_fixture.py`) | ✅ |

## 2. Fayl formati (faqat tuzilma)

Ildiz `<program columns dx dy gap margin printMode rows>`; bolalar: `par`, `var`, `xy`, `if` + `else` (aka-uka), `text`, `qrcode`, `rect`,
`image`, `part`. Barcha geometrik/mazmun atributlari — ifoda (bizning `services/expr.py`; ikkinchi dvigatel yo'q). `.lbl` va `.xml` — shu
`<program>` matni; `.project` — undagi `<operation typeId="LB" program="…">`. Ildiz `program` bo'lmasa — aniq xato (`Корневой тег «…»`).

## 3. Import: moslik jadvali

| Faylda | Shablonda | Izoh |
|---|---|---|
| `program dx dy` | `size {w,h}` (5…500 mm, chegaradan chiqsa qisqartiriladi — ogohlantirish) | |
| `program columns rows gap margin printMode` | `layout {mode, columns, rows, gap_mm, margin_mm}` | shablon ichida maslahat; «o'lchamni qo'llash» va eksport shuni ishlatadi |
| `par` (nomi standart o'zgaruvchi) | o'tkazib yuboriladi (`info.std_pars`) | muharrir uchun sinov qiymati; haqiqiy qiymat loyihadan ❓ (§8 savol 1) |
| `par` (boshqa nom) | `params[]` `{name,type,default,title←comment}` | default ifoda bo'lsa — `vars[]` ga aylanadi + ogohlantirish |
| `var` (ildizda) | `vars[]` `{name,expr,type,comment}` | `double` turida butun literal — haqiqiy son (7/2 = 3.5) |
| `var` (ichma-ich) | `{"t":"var"}` elementi | tur saqlanmaydi |
| `xy x y` | `group` `origin:[x,y]` — keyingi aka-ukalarni o'z ichiga oladi | (0, 0) bo'lsa — olib tashlanadi; `enable=false` — o'tkazib yuboriladi |
| `if condition` + keyingi `else` | `if` `{cond, then[], else[]}` | `expand` — faqat interfeys holati, e'tiborga olinmaydi |
| `text` | `text` | quyida |
| `qrcode x y sz text fillColor` | `barcode` kind=qr `{x,y,size,data,color}` | |
| `rect` | `rect` `{x,y,w,h,stroke{w,color},fill}` | `h=0` yoki `w=0` — `line` |
| `image imgdata` | `image` `{x,y,w,h,src}` | faqat ichki `data:image/png|jpeg` (≤ **200 KB**: shablon formati chegarasi; so'ralgan 256 KB dan past), magic-bayt tekshiriladi; SVG va boshqa — ogohlantirish |
| `part` | `part` `{x,y,w,h}` | detal chizmasi o'zimizcha chiziladi (ogohlantirish `part`) |
| `enable="false"` | element o'tkazib yuboriladi (ogohlantirish `disabled`) | `enable` ifoda bo'lsa — `if` ichiga o'raladi |

**`text`**: `x y text fontSize fontBold fontItalic fillColor fontName w h align ratio multiline wordBreak rowHeight valign`.
* `y` — **asosiy chiziq** (baseline) deb olinadi ❓; bizda `y` — yuqori chet: `y_top = y − fontSize·0.82` (`label_tpl` asosiy chiziqni `y + size·0.82` ga qo'yadi).
* `w` → `maxw` (kenglikka sig'dirish: shrift ≥ 60 % gacha kichrayadi, so'ng «…»); `ratio` qiymatidan qat'i nazar.
* `align=center|right` + `w` → `x` siljiydi: `x + w/2`, `x + w` (ifodalar: `(x)+(w)/2.0`; teskarisi eksportda aniq tiklanadi). `w` yo'q bo'lsa — chapga + ogohlantirish.
* `wordBreak` yoki `multiline` → `wrap` (+ `lines = h // rowHeight`, `line_h = rowHeight`) — taxminiy (ogohlantirish `multiline`).
* `fontName`: Arial (standart) / Courier* → `font:"mono"`; boshqasi element ichida saqlanadi, chopda Arial (ogohlantirish `font`). `valign` ≠ top — ogohlantirish.
* `rowHeight` faqat `wrap` bilan; `fillColor` `#rrggbb` ga keltiriladi (`rgb(…)` ham); qora — yozilmaydi.

**O'zgaruvchi nomlari.** `dx`, `dy` → `label.width`, `label.height`. Boshqalari `label_vars` taxalluslari bilan mos (W4 jadvali + W9 qo'shimchasi:
`indexInOperation`, `index_in_operation` → `part.index`; paz qisqa nomlari `grtc grtn grtw grtd grto` (+ `grb*`, `grl*`, `grr*`) → `groove.<tomon>.*`).
Qoldiq qatorida `length/width/detail.*` — qoldiq o'lchami, `count/totalCount/usedCount` — qoldiqlar soni (`copies`), `indexInOperation` — `waste.number` ❓.
Formatga ma'lum, bizda ma'lumot yo'q nomlar (`good`, `fullName`, `grts`, `grtoi` va h.k.) → ogohlantirish `var_nodata`; butunlay noma'lum nom → `unknown_var`
(ikkalasida ham chopda `#ERR`, jim bo'sh emas).

**Ogohlantirishlar** — `{code, key, count, message}`: `tag` (qo'llab-quvvatlanmaydigan teg, ichidagilari ham sanaladi), `attr` (`teg.atribut`), `disabled`, `skipped`,
`orphan_else`, `image_*`, `part`, `font`, `dash` (strokeDash), `hatch` (fillHatch), `multiline`, `valign`, `align`, `color`, `unknown_var`, `var_nodata`, `par_expr`,
`par_type`, `name`, `dup`, `limit`, `size`.

## 4. Eksport: moslik jadvali

Faqat importer o'qiydigan tuzilma yoziladi. Natija bir qatorli UTF-8 (`<?xml …?><program …>`).

| Bizning element | XML | Izoh / ogohlantirish |
|---|---|---|
| `text` | `text` | `maxw` → `w`; markaz/o'ng tekislashda `x` qutining chap chetiga qaytariladi; `y` → asosiy chiziq; `wrap` → `multiline`+`wordBreak`; `rotate` — yo'q (`rotate`) |
| `rect` | `rect` | `stroke`/`fill`; `radius` — yo'q (`radius`) |
| `line` | `rect` (h=0 yoki w=0) | qiyshiq chiziq — **o'tkazib yuboriladi** (`line`) |
| `image` | `image` | `imgdata=src`, `ratio=true` |
| `barcode` qr | `qrcode` | `rotate` — yo'q (`rotate`) |
| `barcode` code128 | — | **o'tkazib yuboriladi** (`barcode`): formatda 1D shtrixkod tegi kuzatilmagan |
| `part` | `part` | standart detal chizmasi atributlari |
| `edges` | `part` | eng yaqin element (`edges`) |
| `polyline` (W15) | `rect` (h=0 / w=0) segmentlari | faqat gorizontal/vertikal segmentli; qiyshiq bo'lsa — butunlay o'tkazib yuboriladi (`polyline`); to'ldirish yozilmaydi (`poly_fill`) |
| `arc`, `ellipse` (W15) | — | **o'tkazib yuboriladi** (`arc`, `ellipse`): formatda mos teg kuzatilmagan |
| `group` rotate=0 | `xy` + ichidagilar | keyingi aka-uka ham siljiydi (`xy_scope`); (0,0) — shunchaki ichidagilar; rotate ≠ 0 — **o'tkazib yuboriladi** (`group_rot`) |
| `if` / `else` | `if` + `else` | |
| `var` (element) | `var` | tur avtomatik |
| `params` | `par` | `title` → `comment` |
| `vars` | `var` | `type` bo'lsa shu, bo'lmasa avtomatik: son → double; `'…'`, `format/left/ns/now…` → string; taqqoslash, `not/and/or`, `empty/startswith…` → boolean; `if(c,a,b)` — `a` turi; yagona nom — jadvaldagi turi (ogohlantirish `type`) |
| ishlatilgan standart nomlar | `par` (e'lon) | sinov qiymati neytral (`""` / `0` / `false`) |
| `bold`/`italic`/`wrap` — ifoda | `false` | ifodani faylga yozib bo'lmaydi (`skipped`) |

O'zgaruvchi nomlari fayl nomiga qaytariladi: `label.width→dx`, `label.height→dy`, `part.thickness→thick`, `part.qty→count`, `part.total_qty→totalCount`,
`part.name→name`, `edge.<tomon>.symbol→ets|ebs|els|ers` (`…code→etc`, `…name→etn`, `…thickness→ett`, `…jointing→etj`), `xnc1.code→XNC1`, `xnc1.side→xncSide1`,
`groove.top.width→grtw`, `product.qty→product.count`, `part.uid→part.id`, snake_case taxalluslar (`part_uid`, `project_name`, …) → dotli nom va h.k. Faqat bizda bor nom
(`part.title`, `label.number`, `part.dims`, …) o'zgarmaydi — ogohlantirish `var`.

**Round-trip** (import → eksport → import): qo'llab-quvvatlanadigan qism uchun natija **teng** (testlar: `test_round_trip_import_export_import_is_equal`; eksport takrorlansa — bir xil matn).
Tengsizlik faqat atayin: `edges → part`, std `par` e'lonlari soni, `ratio=false → true`, hatch/dash ma'lumoti (import paytida yo'qoladi).
Korxona korpusi (qo'lda): 12 LB operatsiya (6 xil shablon) — 12/12 import → eksport → import teng.

## 5. Xavfsizlik va chegaralar

* XML: `defusedxml` (`forbid_dtd=True`) + `<!DOCTYPE`/`<!ENTITY` oldindan rad etiladi (UTF-16 ham); billion-laughs/XXE sinaldi.
* Fayl ≤ **5 MB** (413), `<program>` ≤ **5000** teg, chuqurlik ≤ **40**; shablon chegaralari W4 niki (≤ 500 element, ≤ 8 daraja, ifoda ≤ 1000 belgi, ≤ 50 parametr, ≤ 100 `vars`, ≤ 1 MB).
* Rasm: `data:image/png|jpeg;base64`, magic-bayt, ≤ 200 KB (shablon formati) — SVG rad.
* `.project` dan bir yo'la ≤ 20 xil shablon taklif qilinadi (bir xil matnlilar birlashtiriladi).
* Fayl serverda saqlanmaydi; saqlash faqat foydalanuvchi bosganda, tanlangan nom bilan (`label_template` profili).

## 6. API

* `POST /api/labels/import-file` — multipart `file` (`.lbl`/`.xml`/`.project`), ixtiyoriy `name`, `save` (true — kutubxonaga ham saqlaydi), `select` (saqlanadigan indekslar).
  Javob: `{filename, kind: program|project, items:[{index, source, name, ops, template, size, layout, warnings[], info{elements,params,vars,images,std_pars}, errors[], saved}], skipped:[{source,error}], more}`.
  `errors` — namuna qatorida ifoda tekshiruvi (`check_template`).
* `POST /api/labels/export-xml` `{template, layout?{mode,columns,rows,gap_mm,margin_mm,width_mm,height_mm}}` → `{xml, warnings[], filename}` (muharrirdagi joriy nusxa).
* `GET /api/label-templates/{id}/export-xml` — kutubxona/o'rnatilgan shablonni fayl sifatida (`X-Export-Warnings` — soni).
* Mavjud `GET …/export` (JSON) va `POST /label-templates/import` o'zgarmagan; UI saqlash uchun shuni ishlatadi.

## 7. UI

«Шаблон» yorlig'i, toolbar ostida: **«Импорт из файла»** (dialog: fayl tanlash → topilgan shablonlar ro'yxati (`.project` da bir nechta), har biri uchun nom, o'lcham/to'r, ogohlantirishlar,
namuna ma'lumotli ko'rinish, «Применить размер и сетку» belgisi → «Сохранить в библиотеку и выбрать»; `.json` ham shu oynada), **«Экспорт JSON»**, **«Экспорт XML»**
(joriy sahifa parametrlari — ustun/qator/oraliq/maydon/o'lcham — ildiz atributlariga yoziladi; ogohlantirishlar oynasi). Eski ikonka tugmalari (JSON eksport/import) shu tugmalarga almashtirildi.

## 8. Foydalanuvchiga savollar (taxmin qilingan joylar)

1. `par` nomi standart o'zgaruvchi bo'lsa (masalan `part.code`, `etn`) — fayldagi qiymat faqat **muharrirdagi sinov qiymati** deb olindi va tashlanadi. To'g'rimi (yoki chopda ham ishlatiladimi)?
2. Matn `y` si — **asosiy chiziq** (kromka nomlari tagiga tortilgan chiziqlar shuni ko'rsatadi; ko'rinish tekshirilgan). Haqiqiy chopdan solishtirish kerakmi?
3. `fontSize` — mm (60 mm balandlikdagi etiketkada 2…5 qiymatlar). `ratio=false` va `ratio=true` bir xil (kenglikka sig'dirish) qabul qilindi; `ratio` ning haqiqiy ma'nosi noma'lum.
4. `xy` — **nisbiy siljish** (to'planadi) va faqat o'z bloki ichida deb olindi; mutlaq/butun dastur bo'yicha bo'lishi mumkin (faylda faqat ildizda uchragan).
5. `fillHatch` ma'nosi noma'lum (kuzatilgan: bo'sh to'ldirishda 1, oq to'ldirishda 8): import — yaxlit to'ldirish; eksport — to'ldirish bor → 8, yo'q → 1.
6. Qoldiq qatorida `length/width/count/totalCount/indexInOperation` — qoldiq o'lchami, qoldiq nusxalari soni, qoldiq raqami deb taxmin qilindi.
7. Eksportda detal chizmasi (`part`) atributlari — standart ifodalar bilan yoziladi; Code128 `barcode` va burilgan `group` yozilmaydi (formatda mos tegi kuzatilmagan). Boshqa tizimda shtrixkod kerak bo'lsa — qaysi teg ishlatiladi (namuna fayl)?
8. Eksport faylini mijoz tizimida ochib tekshirish mumkin emas (shartga ko'ra GibLabga tegilmaydi) — faqat tuzilma bo'yicha mos; haqiqiy muvofiqlik mijoz fayli bilan sinab ko'rilgach tasdiqlanadi.
