# T. LB W15 — vizual etiketka redaktori (LB-C), LB-D qoldiqlari, ZPL chiqarish (v2.4, 2026-10-02)

Hamma narsa noldan, o'z so'zlarimiz bilan. W4 shablon modeli (`T_LB_ETIKETKA.md`) va W9 import/eksport (`T_LB_W9_IMPORT_EKSPORT.md`) **o'zgarmadi — kengaydi**:
eski shablonlar xuddi shunday ochiladi, chop etiladi, XML ga eksport qilinadi (testlar: `test_old_templates_open_unchanged`).

## 1. Holat

| Band | Holat |
|---|---|
| Vizual redaktor («Визуальный редактор» yorlig'i): mm masshtabli sahifa, tanlash/ko'chirish/o'lcham/ko'p tanlash/rubber band, to'r + yopishish + yo'naltiruvchi chiziqlar, xossalar paneli (ifoda + ExprHelper), qatlamlar, o'zgaruvchilar paneli (sinov qiymatlari), undo/redo, klaviatura, kattalashtirish, to'liq ekran | ✅ |
| Yangi element turlari `polyline`, `arc`, `ellipse`: render, redaktor, W9 eksport (yozib bo'lmaydiganlari — ogohlantirish) | ✅ |
| `source=user` UI — «Данные» yorlig'i: maydonlar sxemasi + qatorlar jadvali (Excel Ctrl+V), turga keltirish, shablon yaratish | ✅ |
| ZPL II chiqarish (`label_zpl.py`): `.zpl` fayl, 203/300 dpi, «ZPL Header», UTF-8 (`^CI28`), shrift, burish, hex escape; «Скачать ZPL» oynasi | ✅ (printerda tekshirilmagan — §7, savollar) |
| Mavjud jadval/JSON muharriri («Шаблон» yorlig'i) | ✅ saqlandi (muqobil rejim; «Открыть в визуальном редакторе» tugmasi qo'shildi) |
| Bezye egri, WD/DW sikllari (LB-043, LB-053) | ❌ keyin (so'ralmagan) |
| Printerga to'g'ridan yuborish (drayver/tarmoq) | ❌ atayin yo'q — faqat fayl |

## 2. Fayllar

Backend: `services/label_zpl.py` (ZPL), `services/label_user.py` (foydalanuvchi maydonlari), `api_label_w15.py` (`design`, ZPL endpointlari);
kichik tahrirlar: `label_tpl.py` (yangi turlar, `Renderer(mark=True)`, `text_model`, `render_parts`), `label_gl_export.py` (`_shape`), `label_vars.py`
(`user.*` turga keltirish, `sample_env(row=)`), `label_schema.py` (`ZplSettings`), `settings.py` (`label_zpl` scope), `models.py` (`LBParams.fields` tekshiruvi),
`main.py` (1 qator), `i18n.py` (xabarlar).
Frontend: `features/print/designer/` (`LabelDesigner.tsx`, `DesignCanvas.tsx`, `Inspector.tsx`, `PagePanel.tsx`, `SidePanels.tsx`, `FxInput.tsx`, `model.ts`, `designerApi.ts`,
`designer.css`), `UserData.tsx`, `ZplDialog.tsx`; kichik: `LabelsPanel.tsx` (yorliqlar, «Скачать ZPL»), `labelsApi.ts`; `scripts/i18n_lb_w15.py`.
Testlar: `tests/test_labels_w15_{elements,zpl,user}.py` (104 ta).

## 3. Shablon modeliga qo'shimchalar (W4 JSON; `"v": 1` o'sha)

| `t` | Maydonlar (hammasi ifoda; son ham ifoda) |
|---|---|
| `polyline` | `points: [[x, y], …]` (2…200 nuqta; har koordinata ifoda bo'lishi mumkin), `closed` (bool/ifoda), `stroke` (son yoki `{w, color}`), `fill` |
| `arc` | `cx cy r a1 a2` (gradus; 0° — o'ngga, **musbat yo'nalish soat strelkasi bo'yicha** — Y pastga bo'lgani uchun), `stroke`, `fill` (to'ldirish — sektor); \|a2−a1\| ≥ 360 — to'liq aylana |
| `ellipse` | `cx cy rx ry`, `stroke`, `fill` |

`stroke` ham, `fill` ham berilmasa — 0.2 mm qora chiziq (`rect` da — chiziqsiz; chunki eski xulq saqlandi). Ifoda xatosi (`points[2][1]` kabi maydon nomi bilan)
`#ERR` va xato ro'yxatida; element boshiga birinchi xato (boshqa elementlar kabi). `Renderer(mark=True)` — redaktor uchun har element `<g data-p="2.then.1" data-t="…">` ichida
(oddiy chop chiqishi o'zgarmagan — testda tekshirilgan).

**W9 moslik (qo'shimcha qatorlar):** eksportda faqat gorizontal/vertikal segmentli, to'ldirishsiz `polyline` chiziq-`rect` lar bilan yoziladi; qiyshiq segmentli
poliliniya butunlay o'tkazib yuboriladi (`polyline`), to'ldirish yozilmaydi (`poly_fill`), `arc` va `ellipse` — o'tkazib yuboriladi (`arc`, `ellipse`: formatda mos teg yo'q).
Import: formatda bunday teglar kuzatilmagan — noma'lum teg `tag` ogohlantirishi bilan tushadi (o'zgarmadi). Round-trip: qo'llab-quvvatlanadigan qism teng, eksport takrorlansa — bir xil matn.

## 4. Vizual redaktor

**Arxitektura.** Ifodalar faqat serverda hisoblanadi (CLAUDE.md 14-qoida): redaktor `POST /api/label-templates/design` ga ishchi nusxani yuboradi, server namuna (yoki loyiha
qatori) bilan SVG chizadi — har element `<g data-p>` ichida. Brauzer chizilgan SVG dan `getBBox()` + `getScreenCTM()` bilan har elementning etiketka (mm) koordinatalaridagi
chegaraviy to'rtburchagini va ota-guruh matritsasini oladi → hit-test, tanlash ramkasi, tutqichlar. Ifodali koordinatali elementlar (`pad`, `label.width-2*pad` …) ham ko'chadi:
o'zgarish **delta** sifatida yoziladi (`shiftExpr`): son — qo'shiladi, ifoda — oxiridagi «± son» birlashtiriladi (`pad + 3` + 1.5 → `pad + 4.5`), aks holda `ifoda + d`.
Burilgan guruh ichidagi elementlar ham to'g'ri ko'chadi (delta mahalliy koordinatalarga teskari matritsa bilan o'giriladi). SVG hujjatga qo'shilishdan oldin tozalanadi
(script/foreignObject/`on*`/tashqi `href` olib tashlanadi — chuqur himoya).

**Ish oqimi.** Ishchi nusxa redaktorda (`doc`); har o'zgarish bitta tarix qadami (`past/future`, 100 ta; bir xil maydon/siljitishning tez takrorlari birlashadi), 350 ms
kechikish bilan `PATCH …/operations/{id}` `lb.template` ga yoziladi (loyiha ichidagi nusxa; «Сохранить в библиотеку» — kutubxonaga). Tashqi o'zgarish (kutubxonadan boshqa shablon,
import) aniqlansa — ishchi nusxa almashadi (kanonik JSON solishtiriladi: server normalizatsiyasi farqi hisobga olinmaydi).

**Boshqaruv.** Sichqoncha: bosish — tanlash; Shift/Ctrl+bosish — qo'shish/olib tashlash; bo'sh joyda tortish — rubber band; elementni tortish — ko'chirish (3 px dan keyin);
tutqichlar: rect/rasm/detal/kromka/ellips/Code128 — 8 tutqich; matn — chap/o'ng (`maxw`); QR — burchak (o'lcham); chiziq/poliliniya — tugunlar. Yopishish: to'r (0.5/1/2/5 mm), boshqa
elementlarning chetlari/markazlari va sahifa chetlari/markazi (qizil chiziq); **Alt** — vaqtincha o'chirish. Klaviatura (`label-designer` maydoni): ←↑→↓ 0.5 mm (Shift ×10, Alt 0.1), Del, Ctrl+D (nusxa),
Ctrl+C/V, Ctrl+A, Ctrl+Z / Ctrl+Y (Ctrl+Shift+Z), Ctrl+G (guruh), Ctrl+Shift+G (yoyish), Ctrl+] / [ (tartib; Shift — eng oldinga/orqaga), Ctrl+0 / = / − (masshtab), Esc.
Ctrl+g'ildirak — masshtab. Tartib/guruh/If-ga o'rash/yoyish/tekislash (6 usul) — asboblar qatorida. Namuna turi (detal/qoldiq/mahsulot/o'z ma'lumot) va «namuna | loyiha qatorlari» (‹ n/N ›) — jonli ko'rinish manbai.
**Xossalar:** x, y, w, h, shrift o'lchami, tekislash, rang, qalinlik, to'ldirish, burish, `bold/italic/wrap` (belgi yoki ifoda), poliliniya nuqtalari jadvali, rasm yuklash (PNG/JPEG ≤ 200 KB), izoh;
har ifoda maydonida «ƒ» — `ExprHelper` oynasi (funksiyalar + tekshirish, kontekst — namunadagi qiymatlar). Ifoda xatosi — qizil maydon + xato matni + qatlamlar ro'yxatida va kanvasda belgi.
Sahifa paneli (hech narsa tanlanmaganda): nom, o'lcham, A4 to'r / rulon, ustun/qator/oraliq/maydon/chegara/burish (`LBParams`), shablon parametrlari (qiymatlari bilan) va `vars`.
Pastda — o'zgaruvchilar va funksiyalar (qiymatlari bilan): bosilsa fokusdagi ifoda maydoniga qo'yiladi.

**Cheklovlar.** ≤ 500 element, ≤ 8 daraja (server bilan bir xil; oshsa — xabar). `if` ning faqat chizilayotgan shoxi kanvasda ko'rinadi (ikkinchisini — namuna turini almashtirib yoki
qatlamlardan tanlab tahrirlash). Bezye egri yo'q. Burilgan (o'z `rotate`i bor) elementlar faqat ko'chiriladi (o'lcham tutqichi yo'q).

## 5. `source=user` («Пользовательские данные»)

`LBParams.fields`: `[{name, title, type: string|integer|double|boolean, width, default}]` — `name` → `user.<name>` (lotin harf/raqam/`_`, ≤ 31 belgi, takrorsiz). Yaroqsiz maydon (noto'g'ri/takror nom,
dict emas) **tashlanadi**, noma'lum tur «string» bo'ladi — rad etilmaydi: `PATCH` butun operatsiyani qayta tekshirgani uchun saqlangan eski/import qilingan sxema operatsiyani buzmasligi shart
(`.project` importi ham takror nomni tashlaydi va turlarni 4 tagacha keltiradi; korpus 1248/1248 import, 12 LB operatsiya — HTML va ZPL xatosiz). UI faqat to'g'ri sxemani yuboradi (xato nomlar qizil). `LBParams.data`: `[{qty, <name>: qiymat}]` (≤ 10 000 qator; `qty` — nusxalar soni, standart 1; jami ≤ 10 000 etiketka). Qiymatlar matn bo'lib saqlanadi,
chop paytida tur bo'yicha o'giriladi (`label_user.coerce_user_value`: probel/NBSP olib tashlanadi, vergul — kasr nuqtasi, «да/yes/1» — true; bo'sh — maydon standarti yoki tur noli); turi
ko'rsatilmagan eski maydon qiymatni o'zgartirmaydi. UI: maydonlar jadvali (xato nomlar qizil), qatorlar jadvali (100 qator/sahifa), **Excel Ctrl+V** (katak ichida: shu joydan boshlab, yetishmagan
qator/maydonlar yaratiladi; qo'shtirnoqli katakchalar; «birinchi qator — sarlavhalar»), «Вставить из буфера», jami etiketkalar soni. Manba birinchi marta «Пользовательские данные» tanlanganda 2 ta
standart maydon (`title`, `code`) va ularni chop etadigan shablon yaratiladi; shablon `user.*` ni ishlatmasa — «Создать шаблон по полям».

## 6. API (hammasi `/api` ostida)

`POST /label-templates/design` — `{template, params, width_mm, height_mm, kind: part|waste|product|user, fields?, row?, project_id?+lb?+index?, values}` → `{svg, width, height, errors[], warnings[], values{}, tpl_values{}, meta}`.
`GET /projects/{pid}/operations/{oid}/lb/labels/zpl` (`dpi`, `header`, `utf8`, `font`, `emit_size`, `lang`) va `POST /projects/{pid}/lb/labels/zpl` (`{lb, zpl{…}}`) — `.zpl` fayl (UTF-8,
`Content-Disposition: attachment`, `X-ZPL-Labels`, `X-ZPL-Warnings`); `POST /projects/{pid}/lb/labels/zpl/preview` — birinchi etiketkalar ZPL matni + ogohlantirishlar (JSON);
`POST /label-templates/zpl` — shablonning bitta namunaviy etiketkasi. ZPL sozlamalari — `GET/PUT /settings/label_zpl/default` (`ZplSettings`); so'rovdagi qiymat standartni bosadi.

## 7. ZPL: moslik jadvali va taxminlar

`^XA`, `^CI28` (UTF-8), `^PW`, `^LL`, `^LH0,0`, [sarlavha], elementlar, `^XZ` — har etiketka bitta blok. mm → nuqta: `round(mm·dpi/25.4)`.
**«ZPL Header»**: `~` buyruqlari (`~SD15`) `^XA` dan **oldin**, qolganlari (`^PR`, `^MD`, `^CW` …) `^LH0,0` dan keyin; `^XA`/`^XZ` olib tashlanadi, boshqaruv belgilari tozalanadi, ≤ 2000 belgi.

| Element | ZPL |
|---|---|
| `text` | `^FO x,y ^A0N,h,w ^FD…^FS` (h = o'lcham·dpi/25.4·`TEXT_H_K`, w = h·`TEXT_W_K`; qatorlar alohida maydon; markaz/o'ng tekislash — `^FB w,1,0,C\|R`; oq matn — `^FR`; shrift `font` sozlamasi: `0`, `A`…, yoki `^A@` + `E:ARIAL.TTF`) |
| `rect` | `^GB w,h,qalinlik,B\|W,yumaloqlash(0…8)`; quyuq to'ldirish (yorqinlik < 0.45) — qalinlik = kichik tomon; oq (≥ 0.97) — `W`; oraliq ranglar to'ldirilmaydi |
| `line`, `polyline` | gorizontal/vertikal — `^GB`, qiyshiq — `^GD w,h,t,B,L\|R`; yopiq poliliniya — oxirgi kesma; to'ldirish yo'q (`fill` ogohlantirishi) |
| `arc` | 10° li xordalar (`^GD`/`^GB`) — taxminiy (`arc`); to'liq aylana — `^GC` |
| `ellipse` | `^GE w,h,t`; aylana — `^GC d,t` |
| `barcode qr` | `^BQN,2,<modul 1…10>` + `^FD<EC>A,<ma'lumot>^FS` (modul = o'lcham/(modullar+2·quiet)); belgilangan maydon ichida markazlashadi |
| `barcode code128` | `^BY<modul 1…10>` + `^BC<yo'nalish>,<balandlik>,<Y\|N>,N,N,A` (avtomatik to'plam almashishi) |
| `part`, `edges` | o'zimizcha chizilgan detal chizmasi/kromka sxemasi: `^GB`/`^GD` + matn (SVG geometriyasining nusxasi) |
| `group` | koordinata siljishi + burish (faqat 90° ga karrali aniq; boshqasi yaqin 90° ga yaxlitlanadi — `rotate` ogohlantirishi); `rotate_page=90` — fizik eni = H |
| `image` | o'tkaziladi (`image` ogohlantirishi) |

**Xavfsizlik:** `^FD` ichidagi `^`, `~`, `_` belgilari `^FH_` + `_5E`, `_7E`, `_5F` ko'rinishida yoziladi (shablon matni formatni buza olmaydi: `'^XZ^XA'` → `_5EXZ_5EXA`); testlar chiqishni
buyruqlar ro'yxatiga ajratib faqat ma'lum buyruqlar borligini tekshiradi.
**Ogohlantirishlar** (JSON/UI): `image`, `rotate`, `fill`, `arc`, `qr_small`, `bc_dense`, `nonascii` (UTF-8 o'chiq: translit + «?»), `clip` (manfiy koordinata 0 ga), `font` (Latin-1 dan tashqari belgilar:
o'rnatilgan shriftda kirill/«№»/«…» yo'q — printerga TTF yuklab `E:ARIAL.TTF` ko'rsatiladi).
**Printerda/Labelary da tekshirilmagan (taxmin):** shrift balandligi/kengligi nisbati (`TEXT_H_K=1.0`, `TEXT_W_K=1.0`), o'rnatilgan shrift 0 ning Arial dan torroqligi, burilgan matn/shtrixkod `^FO` boshi
(aylantirilgan chegaraviy to'rtburchakning chap-yuqori burchagi deb olingan), `^BQ` ning bo'sh zonasi. Konstantalar `label_zpl.py` boshida.

## 8. Testlar

`test_labels_w15_elements.py` (30): tuzilma/chegara, render, ifoda xatolari, `mark`, W9 eksport/round-trip, `design` API, eski shablon mosligi.
`test_labels_w15_zpl.py` (25): qat'iy tuzilma (buyruqlar ro'yxati), DPI, sarlavha/escape/injection, har element, burish, API/fayl/sozlama scope i, `source=user`.
`test_labels_w15_user.py` (49): sxema tozalash/tekshiruv, turga keltirish (jadval), Excel qiymatlari, qty/chegara, eski JSON va `.project` importi, XML/UTF-8 uchun yaroqsiz belgilar (yakka surrogat).
Frontend `tsc` toza; UI — alohida portda (8815) Playwright skriptlari (scratchpad: `w15_seed.py`, `w15_flow1…5.cjs`, `w15_shots.cjs`), `model.ts` toza funksiyalari — `w15_model_test.mjs`;
korxona korpusi (1248 fayl) bilan LB importi/HTML/ZPL tekshiruvi — `w15_corpus_lb.py` (1248/1248 import, 12 LB operatsiya xatosiz).

## 9. Foydalanuvchiga savollar

1. ZPL ni **haqiqiy printerda** (yoki Labelary da) tekshirib bering: matn o'lchami/joylashuvi (`TEXT_H_K`, `TEXT_W_K`), markazlash, burilgan matn/shtrixkod, QR o'lchami to'g'rimi? Qaysi printer modeli/DPI (203/300), etiketka 58×60.5 yoki 58×40?
2. Kirill matn uchun printerga qaysi TTF yuklanadi (`E:ARIAL.TTF`)? Standart shrift sifatida `E:ARIAL.TTF` qilib qo'yaylikmi?
3. F4Classic «ZPL sarlavhasi» — odatda nima yoziladi (namuna matn)? Hozir: erkin matn; `~` buyruqlari `^XA` dan oldin.
4. Rasm (logotip) ZPL ga kerakmi (`^GFA` — bitmap)? Hozir o'tkaziladi + ogohlantirish.
5. Bezye egri va WD/DW sikllari (LB-043, LB-053) kerakmi? Poliliniya/yoy/ellips yetarlimi?
6. `arc` burchak yo'nalishi (soat strelkasi bo'yicha, 0° — o'ngga) — xodimlarga qulaymi? (Y pastga bo'lgani uchun tanlandi.)
7. Eski dasturdan o'tgan shablonda `polyline/arc/ellipse` yo'q — mijoz fayllarida bunday chizmalar uchragan bo'lsa, namuna fayl bersangiz importerga qo'shamiz.
