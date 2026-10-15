# T. LB — etiketka tizimi (W4: LB-A parametrlar + LB-B JSON shablon, ifodali maydonlar)

Manba: `giblab_inventory/03_EL_GR_O_LB_ifodalar.md` §2.4–2.7, §4, Ilova B; `05_…` WP-F; `H_REPORTS_LABELS.md` §H5. Hamma narsa noldan,
o'z so'zlarimiz bilan yozilgan (eski dasturning shablon fayli o'qilmaydi, yordam matni ko'chirilmagan). Ifoda dvigateli — tayyor
`services/expr.py` (ikkinchi dvigatel yozilmagan).

## 1. Nima bor (holat)

| Band | Holat |
|---|---|
| LB — loyiha operatsiyasi (tur dialogida faol, «Операции» jadvalida qator, klon/o'chirish/tartib) | ✅ |
| `LBParams` (LB-002…018, 023, 058): manba, A4/rulon, o'lcham, ustun/qator/oraliq/maydon/chegara, tanlov bayroqlari, shablon, parametr qiymatlari | ✅ (❓ belgilari §3) |
| JSON shablon: matn, ifodali matn, to'g'ri to'rtburchak, chiziq, rasm, QR, **Code128 (noldan SVG)**, detal chizmasi, kromka sxemasi, guruh (siljish/burish), If/Else, `Var`/`Par` | ✅ |
| O'zgaruvchilar kontekst provayderi: `project.*`, `product.*`, `material.*`, `part.*`, `edge.*`, `groove.*`, `xnc1…5.*`, `map.*`, `waste.*`, `label.*` + taxalluslar | ✅ |
| Qoldiq etiketkasi, mahsulot etiketkasi, bir detalga bir necha etiketka (`label_count`, `label.index/count/number`), tanlangan detallar | ✅ |
| A4 da **4 / 6 kroy kartasi miniatyurasi** chopi | ✅ |
| Shablon kutubxonasi (`label_template` sozlama scope i), 4 ta o'rnatilgan namuna, import/eksport (JSON) | ✅ |
| Ifoda xatosi chopdan oldin muharrirda: ro'yxat + jadvalda qizil qator + etiketkada qizil «#ERR» (jim 0 yo'q) | ✅ |
| Ko'rish/chop: A4 to'r va rulon (`@page`), 90° burish, ≤ 10 000 etiketka/chop | ✅ |
| Vizual redaktor (drag-drop, undo/redo), polilinya/yoy/ellips, foydalanuvchi ma'lumotlari jadvali UI si | ✅ **W15** — qarang `T_LB_W15_REDAKTOR_ZPL.md` (Bezye egri va siklar WD/DW — yo'q) |
| Mijozning tayyor shablon faylini (`.lbl`/`.xml` — `<program>`; `.project` dagi LB shabloni) import va `<program>` XML ga eksport | ✅ **W9** — qarang `T_LB_W9_IMPORT_EKSPORT.md` (foydalanuvchi ruxsati 2026-10-02); `.project` importida shablon avtomatik o'giriladi |
| ZPL II (Zebra) chiqarish — `.zpl` fayl, 203/300 dpi, «ZPL Header» | ✅ **W15** — `T_LB_W15_REDAKTOR_ZPL.md` (printerda tekshirilmagan; TSPL/ESC yo'q; printerga to'g'ridan yuborish yo'q) |

Eski qat'iy QR etiketka (`GET/POST /api/projects/{pid}/labels`, `labels.labels_html`, `LabelSettings`) **o'zgarishsiz** — e2e va mavjud
testlar buzilmaydi. Yangi tizimdagi standart shablon `builtin:detail` uning shablon ko'rinishi: QR matni bir xil `MXK:<№>:<uid>:<i>/<n>`
(MES skaneri `GET /api/mes/scan/{kod}` o'qiydi).

## 2. Fayllar

Backend (yangi): `services/barcode.py` (Code128 + QR yo'li), `services/label_tpl.py` (shablon dvigateli: tekshiruv + SVG),
`services/label_vars.py` (qatorlar va muhit), `services/label_builtin.py` (4 namuna), `services/label_print.py` (maket, HTML, kartalar
miniatyurasi), `services/label_import.py` (`.project` LB), `services/label_schema.py` (`label_template` scope modeli), `api_labels.py`.
Kichik tahrirlar: `models.py` (`LBParams`, `Operation.lb`), `main.py` (`_new_operation` LB + 1 qator `include_router`), `settings.py`
(`lb_defaults`, `label_template`), `i18n.py` (`lb.*`), `plugins/legacy_project.py` (`typeId="LB"`), `services/labels.py`
(`edge_icon_parts` ajratildi — chiqish bir xil).
Frontend: `features/print/LabelsPanel.tsx` (+ `labelsApi.ts`, `labels.css`), `scripts/i18n_lb.py`; kichik: `opmeta.tsx` (`IMPLEMENTED`),
`ProjectView.tsx` (LB paneli), `Print.tsx` («Этикетки» bo'limi → `LabelsPrint`; eski forma bloki endi ishlatilmaydi), `api/types.ts`.
Testlar: `tests/test_labels_w4_{barcode,template,print,import}.py` (109 ta).

## 3. `LBParams` (`Operation.lb`)

| Maydon | Standart | Ma'nosi | Holat |
|---|---|---|---|
| `source` | `parts` | `parts` — detallar (+qoldiqlar), `products`, `user` (qo'lda qatorlar; UI — W15: «Данные» yorlig'i, `T_LB_W15_REDAKTOR_ZPL.md` §5) | taxmin: GibLab 2/1/0 |
| `mode` | `sheet` | A4 to'r / etiketka printeri (bittadan). **Standart «sheet»** (eski xulq: 3 ustun A4); spetsifikatsiyada «roll» edi | ❓ printer noma'lum |
| `rotate_page` | 0 | 90 — A4 albom (sheet) yoki sahifa+mazmun burilishi (roll) | ✅ |
| `width_mm`, `height_mm` | 58 × 40 | etiketka o'lchami (5…500) | ✅ |
| `columns`, `rows` | 3, 0 | A4 da ustun/qator; `rows=0` — sahifaga sig'ganicha | ✅ |
| `gap_mm`, `margin_mm`, `border` | 2, 6 (None — maydon yo'q), true | oraliq, «Поля страницы», chegara | ✅ |
| `cs_op_id` | None | faqat shu CS (None — hamma) | bizniki |
| `print_parts`, `part_each`, `part_only_nonzero` | true | detallar; «Для каждой детали» (har nusxaga); «soni > 0». `part_each=false` — detalga bitta | LB-011/012/013 |
| `part_selected` | [] | tanlangan detal ID lari (bo'sh — hamma) | LB-014 (fayldagi `partSelected` — faqat bayroq, ro'yxat yo'q) ❓ |
| `label_count` | 1 | **bir detal nusxasiga etiketkalar** (1…20) | WP-F |
| `print_wastes`, `waste_each`, `waste_business_only` | false, true, false | qoldiq etiketkalari (`kind=remnant`; har list nusxasiga); faqat деловой | LB-015/016; «waste_business_only» bizniki ❓ |
| `product_each`, `product_only_nonzero` | false, true | mahsulot etiketkalari (har nusxaga / mahsulotga bitta) | LB-017/018 |
| `template_id` | None | `builtin:<kalit>` yoki `profile:<id>` (None — `builtin:detail`) | ✅ |
| `template` | None | loyiha ichidagi nusxa (g'olib; GibLab `program` o'rnida) | ✅ |
| `params` | {} | shablon parametrlari (`Par`) qiymatlari | ✅ |
| `fields`, `data` | [] | `source=user` sxemasi/qatorlari (qatorda `qty`) | LB-019 (UI — LB-D) |
| `legacy_program` | "" | `.project` dagi eski shablon matni (asl nusxa, yo'qolmasin uchun): **W9 dan** u `template` ga o'giriladi va operatsiya shuni chop etadi; o'girib bo'lmasa — o'qilmaydi, standart shablon ishlatiladi | — |

`lb_defaults` scope — «Сохранить параметры по умолчанию» (tanlov, nusxa shablon, qatorlar saqlanmaydi). Eski `labels` (LabelSettings) profillari
endi faqat eski endpoint uchun.

## 4. Shablon formati

```json
{ "v": 1, "name": "…", "size": {"w": 58, "h": 40},
  "params": [{"name": "margin", "type": "double|integer|string|boolean", "default": 2, "title": "…"}],
  "vars":   [{"name": "code", "expr": "''+project.number+rspace(right(part.id,4),4,'0')"}],
  "elements": [ … ] }
```
Koordinatalar mm; chap-yuqori, X → o'ng, Y → past. **Har geometrik/mazmun maydoni — ifoda** (`expr.py`); oddiy son ham ifoda; **matn
literali qo'shtirnoq bilan** (`"'PAZ'"`). `vars` — ketma-ket hisoblanadi (faqat o'lcham/parametrga bog'liq bo'lganlar bir marta);
`label.width`, `label.height` — chop o'lchami (shablon unga moslashadi; `size` — tavsiya). `if/else`, `group`, `var` ichma-ich.

| `t` | Maydonlar |
|---|---|
| `text` | `x y text size maxw align(left/center/right) bold italic color font(mono) rotate wrap lines line_h` — `maxw`: avval shrift ≥ 60 % gacha kichrayadi, so'ng «…» bilan kesiladi; `wrap` — qatorlarga bo'lish; `\n` — qator |
| `rect` | `x y w h stroke(son yoki {w,color}) fill radius` |
| `line` | `x1 y1 x2 y2 stroke` |
| `image` | `x y w h src` — faqat `data:image/png|jpeg;base64`, ≤ 200 KB (SVG rad etiladi) |
| `barcode` | `kind: qr | code128`, `data` (ifoda), `x y`, qr: `size quiet ec`; code128: `w h caption quiet`; `rotate` — 90° (CNC/vertikal) |
| `part` | detal chizmasi (`x y w h`): nisbatga mos to'rtburchak, uzunlik/en, kromka rangli qalin chiziq + belgi (muhitdan) |
| `edges` | kromka sxemasi (`x y w h`) — eski etiketkadagi ikonka |
| `group` | `rotate origin:[x,y] elements` — koordinata boshi siljishi + burish |
| `if` | `cond then[] else[]` |
| `var` | `name expr` — ketma-ket o'zgaruvchi |

Chegaralar: ≤ 500 element, ≤ 8 daraja, ifoda ≤ 1000 belgi, shablon ≤ 1 MB, parametr ≤ 50, `vars` ≤ 100, o'lchamlar 5…500 mm,
koordinatalar ±5000 (kesiladi), matn ≤ 1000 belgi. Code128: ASCII 32…126, ≤ 200 belgi (B va C to'plami avtomatik; 4+ raqam — C);
ingichka shtrixkod/QR (modul < 0.19 / 0.3 mm) — **ogohlantirish**.

## 5. O'zgaruvchilar (to'liq ro'yxat — `GET /api/label-variables`, muharrirda «Переменные и функции»)

| Guruh | Nomlar |
|---|---|
| `project.*` | `name number date ready_date description currency owner customer mes crc16 crc32` |
| `product.*` | `index name code qty count description phone1 phone2 date order` |
| `material.*` | `name code thickness` (CS operatsiya) |
| `part.*` | `id uid code name title(belgi+nom) description marks index length width blank_length/width detail_length/width jointed_length/width saw_length/width thickness dims qty total_qty used_qty copy copies counter grain groove mill drill qr` |
| `edge.<top|bottom|left|right>.*` | `has symbol name code thickness jointing color lines`; `edge.count` |
| `groove.<tomon>.*` | `has code name width depth offset back` |
| `xnc1…xnc5.*` | `code side by_size` |
| `map.*` | `index total copies sheet_length sheet_width fill qr` |
| `waste.*` | `number length width area business` |
| `label.*` | `number total index count kind code width height lang` |

Taxalluslar (qiymat bir xil): 03 Ilova B snake_case (`part_uid`, `edge_top_symbol`, `project_crc32` …) va eski qisqa nomlar (`ets elc… thick txt
count totalCount usedCount length width detail.length XNC1 xncSide1 business waste`). Qator turiga mos kelmaydigan o'zgaruvchi bo'sh qiymatga ega
(satr «», son 0) — bitta shablon turli qatorlar bilan xato bermaydi; imlo xatosi — xato.

`part.length/width` — kiritilgan o'lcham (loyiha o'lcham rejimida; eski etiketka shuni chiqaradi); `length/width` taxallusi — zagotovka (GibLab ma'nosi).
`part.counter` = nusxa raqami (i) ❓; chop bo'yicha noyob raqam — `label.number`. Mahsulot kodi `MXK:<№>:P<n>:<i>/<m>`, qoldiq kodi — karta QR i
(`MXK:<№>:<op>:<karta>`, MES skaneri o'qiydi); mahsulot kodini MES hali o'qimaydi.

**Keyin / yo'q** (ma'lumot bizda yo'q yoki ma'nosi noaniq): `surfFront/surfBack` (SP yo'q), paz uchun alohida tomon nomi (`grtn` — bor: `groove.*.name`,
lekin «tomon» ma'nosi ❓), `xncBSD` real ma'nosi, `waste`/`business` ning «detal» turidagi ma'nosi, foydalanuvchi ma'lumotlari (`user.<nom>` — backend bor, UI yo'q).

## 6. O'rnatilgan namunalar

| Kalit | Qator turi | Mazmuni |
|---|---|---|
| `detail` (standart) | detal / qoldiq / mahsulot | eski etiketka ko'rinishi (sarlavha, ID, nom, o'lcham, material, mahsulot, `i/n · karta`, kromka sxemasi, QR=`label.code`); parametrlar `qr show_edges show_product show_map` |
| `detail_c128` | detal | Code128 (`loyiha № + detal ID (oxirgi 4) + hisoblagich (4)`), detal chizmasi, matn takrori |
| `waste` | qoldiq | `Д№`, деловой belgisi, o'lcham, maydon, karta, karta QR i |
| `product` | mahsulot | nom (2 qator), kod, soni, mijoz, telefon, sana, QR |

Namuna tanlanganda etiketka o'lchami shablon `size` iga o'rnatiladi. O'zgartirilsa — nusxa loyihada (`template`), «Сохранить в библиотеку» — profilga.

## 7. API (`api_labels.py`; hammasi `/api` ostida)

`GET /label-templates` · `GET /label-templates/{builtin:kalit|profile:id}` · `POST /label-templates/check` (tuzilma, sintaksis, namuna qatorida hisoblash) ·
`POST /label-templates/preview` (loyihasiz) · `GET …/{id}/export` · `POST /label-templates/import` · `GET /label-variables` ·
`GET /projects/{pid}/operations/{oid}/lb/count|labels|rows` · `POST /projects/{pid}/lb/count|labels|preview` (saqlanmagan `LBParams` bilan) ·
`GET /projects/{pid}/map-sheets?per_page=4|6&op_id=&profile_id=&lang=` · kutubxona CRUD — umumiy `/settings/label_template`, standart — `/settings/lb_defaults/default`.
`preview` javobi: `{html, total, rendered, pages, counts, errors[], warnings[], template, truncated}` (birinchi 6 ta ko'rsatiladi, birinchi 300 tasida xato qidiriladi).

## 8. Chop maketi, xavfsizlik, unumdorlik

* **sheet**: `@page A4 (albom — rotate_page=90)`, `margin` = «Поля», grid `columns × rows` (rows=0 — sig'ganicha), sahifa-sahifa; sig'masa — ogohlantirish.
  **roll**: `@page` = etiketka (90° — sahifa va mazmun burilgan), har etiketka alohida sahifa. Chiqish: HTML + inline SVG; brauzer «Печать».
* **Kartalar miniatyurasi**: `render.map_svg` (kromka chiziqlari, detal raqami) + `map_header` + kichik karta QR i (profil: `map_edges`, `map_qr`,
  `map_mirror`, `map_header_fields`); **4 — albom 2×2, 6 — kitob 2×3** (qaror: karta nisbati 1.5, shu usulda sahifa to'liqroq to'ladi ❓).
* **Xavfsizlik**: skript yo'q (`render.REPORT_CSP` sarlavha + `<meta>`), matn escape, boshqaruv belgilari olib tashlanadi, rang — `safe_color`, rasm — faqat
  PNG/JPEG data URI, shtrixkod/QR — faqat SVG yo'l; testlar chiqishni XML sifatida o'qib teg/atributlarni tekshiradi.
* **DoS**: bir chopda ≤ 10 000 etiketka (oshsa — 422, ko'rish esa ishlayveradi); sanash arifmetika bilan (10¹⁰ dona ham tez); ifoda chegaralari `expr.py` da.
* **Tezlik** (shu mashinada, 1 jarayon, HTML yig'ish bilan): 10 000 etiketka × 30 ifoda ≈ **2.1 s**; 30 murakkab ifoda (`if/format/left` + 90 oddiy) ≈ 4.8 s;
  standart `detail` (≈ 30 ifoda + noyob QR) ≈ 4.4 s (29 MB HTML); `detail_c128` ≈ 1.1 s. >400 etiketkada QR niqobi qidirilmaydi (≈ 5× tez; QR to'g'ri, har qanday o'quvchi o'qiydi).
  Ifoda hisoblash ≈ 5 µs; qator ma'lumotiga bog'liq bo'lmagan `vars` (o'lcham/parametr) bir marta hisoblanadi.

## 9. `.project` importi va ochiq savollar

`typeId="LB"` endi import qilinadi (avval o'tkazib yuborilar edi): `printMode` (0 → A4, 1 → rulon ❓), `columns rows gap margin source printParts partEach
partONZ printWastes wasteEach productEach productONZ`, `fields` (BASE64 XML sxema), o'lcham — `program` ildizidagi `dx/dy`; `program` matni `legacy_program` da
(asl nusxa; W9 dan `program` shablonga o'giriladi — `T_LB_W9_IMPORT_EKSPORT.md`), ogohlantirish beriladi. Korxona korpusidagi 3 LB operatsiyasi xatosiz o'qiladi (2×4 A4, 89×60.25 mm, source=2).

**Savollar** (qaror foydalanuvchida):
1. Etiketka printeri turi/o'lchami (`mode` standarti: sheet yoki roll; ZPL/TSPL kerakmi) — hozir A4 + «Печать» brauzer orqali.
2. ~~Korxona `.lbl`/`program` shablonlarini bizning JSON ga o'giruvchi importer (LB-D) yozishga ruxsat bormi?~~ — **ruxsat berilgan (2026-10-02)**: W9, `T_LB_W9_IMPORT_EKSPORT.md`.
3. `printMode`: 0 — A4, 1 — printer deb qabul qilindi (real fayllarda 0 + 2×4 to'r) — to'g'rimi? `margin=true` qiymati (mm) fayl formatida yo'q — standart 6 mm.
4. `part.counter` ma'nosi: nusxa raqami (i) yoki loyiha bo'yicha ketma-ket etiketka raqami (`label.number`)? Shtrixkodda necha raqam kerak?
5. Qoldiq etiketkasi: faqat деловой qoldiqlarmi yoki hammasimi (standart — hammasi, `waste_business_only` bilan toraytiriladi)?
6. Y o'qi: yuqoridan pastga (XNC/kartalar kabi) saqlandi — xodimlar eski shablondan koordinata ko'chiradimi?
7. Kartalar miniatyurasi: 4 ta — albom 2×2, 6 ta — kitob 2×3 yetarlimi (yoki boshqa joylashuv)?
8. Mahsulot etiketkasi kodi (`MXK:<№>:P<n>:…`) MES skaneri tomonidan o'qilishi kerakmi?
