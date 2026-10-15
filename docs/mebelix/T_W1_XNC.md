# T. W1 paketi — XNC muharriri to'liqligi (2026-10-02)

Spetsifikatsiya: `J_XNC_SPEC.md`, inventar: `giblab_inventory/04_XNC_postprotsessor_format.md`. Bu hujjat — W1 da qo'shilgan narsalar,
qabul qilingan **qarorlar** (yordamda aniq bo'lmagan joylar bitta konstanta orqasida) va ma'lumot tuzilmalari.

## 1. Modullar
| Nima | Fayl |
|---|---|
| Hisob (Par, fillet, rect/ellipse, cho'ntak, `machine_program`) | `backend/app/services/xnc.py` |
| Shablonlar kutubxonasi (o'rnatilgan 7 namuna, saqlash/eksport/import, qo'shish) | `backend/app/services/xnc_templates.py`, scope `xnc_template` (`settings.py`) |
| API: shablonlar, Par holati, DXF, XNC postprotsessor | `backend/app/api_xnc.py` |
| Ishlov markazi konteksti, `json` format, Jinja shablon | `backend/app/services/postprocessors.py` (`context_xnc`, `run_builtin_xnc`, `render_template_xnc`) |
| DXF → kontur (ixtiyoriy) | `backend/app/services/xnc_dxf.py` |
| `.project` importi: yangi atributlar | `backend/app/plugins/legacy_project.py` |
| UI: daraxt, Par formasi, shablonlar, postprotsessor, DXF | `frontend/src/features/xnc/*` (`treeOps.ts` — toza daraxt amallari) |
| Testlar | `backend/tests/test_xnc_w1_{mill,par,templates,import,postprocess,dxf}.py` |

## 2. Qarorlar (konstantalar `xnc.py` boshida)
| Konstanta / qoida | Standart | Asos |
|---|---|---|
| `POCKET_COUNTS_IN_LENGTH` | `False` — `C=3` (cho'ntak) kontur «длина фрезерования» ga **kirmaydi** | korpusda `ms c=3` bo'lgan 4 dasturda saqlangan `countMill = 0` (kontur uzunligi 24 mm bo'lsa ham) — qoida tasdiqlandi |
| `RECT_XY_IS_CENTER` | `True` — `MillRect` (X, Y) = markaz | yordam rasmi (`hMillRect`): X,Y markazda; **taxmin** — orientatsiya/birlik tasdiqlanmagan |
| `ANGLE_DEGREES` | `True` — `A` gradusda, musbat: +X dan +Y tomonga | ifodalardagi trig radian, lekin burchak atributi gradus deb olindi (**taxmin**) |
| `MillEllipse` | `RL`, `RW` — yarim o'qlar (rasmdagi RL/RW), `A` — burilish; eski `A`,`B` (to'liq o'qlar, burilishsiz) o'qiladi | rasm (`hMillEllipse`); **taxmin** |
| `MillFillet R` | oldingi va keyingi `MillLine` orasidagi burchakni yumaloqlaydi; qo'shni chiziq bo'lmasa yoki R katta bo'lsa — burchak o'zgarmaydi + ogohlantirish | rasm (`hMillFillet`); chiziq–yoy va yoy–yoy **qilinmagan** |
| Qirra teshigi `M` | `M` berilsa: `true` — Z = dz/2 (z e'tiborsiz), `false` — Z; `M` yo'q (eski dastur) — Z aniq | korpus: `m=true` da `z` doim dz/2 |
| `SDP`, `SXY`, `IN`, `OUT` | hisobga ta'sir qilmaydi (bir o'tish), kontekstga chiqadi; `SXY` standart `D/2` | yordam; ko'p o'tish uzunligi noma'lum |
| Par `readonly` | rost bo'lsa kiritilgan qiymat e'tiborsiz, qiymat doim `value` ifodasidan | `ParamGrid` ma'nosi (`readOnly`) |
| `ELLIPSE_TOL` | 0.05 mm — ellips siniq chiziqqa yaqinlashtirish (chizma, kontekst) | — |

## 3. Par (parametr) sxemasi
`Par` buyrug'i `params`: `name`, `value` (standart qiymat/ifoda), `label` (yorliq), `type` (`double` | `integer` | `boolean`),
`visible` (ifoda: maydon ko'rinadimi), `suffix` (birlik matni), `readonly` (ifoda). Manba — `development/ParamGrid` sahifasi
(parametr jadvali: tur, yorliq, ko'rinish sharti, faqat o'qish); XNC `Par` uchun alohida yordam yo'q. Qilinmagan: `allowedNull`,
`multiline`, matn turi (XNC ifodalari faqat sonli o'zgaruvchi bilan ishlaydi).
Qiymatlar operatsiyada: `XNCParams.par_values = {nom: son | ifoda}` (eski JSON da yo'q → `{}`, hammasi standart). Hisobda Par
o'zgaruvchiga aylanadi (integer — kasr tashlanadi, boolean — 1/0). `GET /projects/{pid}/operations/{oid}/xnc-params` yoki
`xnc-stats.params` — hisoblangan holat (`value`, `default`, `visible`, `readonly`).

## 4. Shablon fayl formati (eksport/import, JSON)
```json
{"app": "MebeliX Kroy", "kind": "xnc_template", "version": 1, "name": "…", "description": "", "category": "mill|drill|facade|groove|",
 "program": [XncCommand…], "par_values": {}}
```
Chegaralar: ≤ 3000 buyruq, ichma-ich ≤ 24. O'rnatilgan namunalar (`lib:<kalit>`): `pocket_rect`, `hole_circle`, `outline_rounded`,
`facade_frame`, `row32`, `side_panel`, `back_groove` — hammasi `Par` + `dx/dy/dz` bilan parametrik, ru/uz yorliqlar; foydalanuvchi
shablonlari `u:<id>`. `POST …/xnc/apply-template {template, mode: replace|append}`: qo'shishda mavjud dasturdagi bilan bir nomli
`Par` qayta e'lon qilinmaydi.

## 5. Ishlov markazi konteksti (`context_xnc`) — Jinja shablonda `xnc`
`xnc = {code, name, qty, face: front|back, turn, mirror_x, mirror_y, origin, size{length,width} (burishdan keyin), blank{length,width,thickness},
part{uid,name,code,length,width,qty}|null, edges / edges_final {top,bottom,left,right: {symbol,name,thickness,joint}}, ops[], tools[], params[],
stats{drills,mill_m,saw_m}, errors, warnings, extra_turn}`. Koordinatalar: burish / ko'zgu / koordinata boshi **oldindan qo'llangan**
(detalning chap-yuqori burchagidan, X o'ngga, Y pastga, mm). `ops[]` turlari: `drill` (face: front|left|right|top|bottom; qirra teshigida (x,y) —
kiradigan chekkadagi nuqta), `mill_start` (pocket, correction, step_depth, step_xy, entry, exit), `mill_line`, `mill_arc` (markaz, radius,
`clockwise` — ekranda soat mili), `rect` / `ellipse` (+ `path`), `groove` (passes). Endpoint: `GET /projects/{pid}/operations/{oid}/postprocess?key=json`
(yoki `profile_id`, yoki `key=machine:<kalit>` — faqat `cnc` guruhi), ixtiyoriy `long_side=horizontal|vertical|any` (ishlov markazi cheklovi
«uzun tomon»: kerak bo'lsa qo'shimcha 90° burish). Stanok formatini korxona dasturchilari shablonda yozadi.

## 6. Klaviatura (XNC muharriri, `E_HOTKEYS` E7 + E3)
Ctrl+←/→ — blokdan chiqarish / blok ichiga (oldingi qo'shni If/Else/While/DoWhile/Sub), Ctrl+↑/↓ — ko'chirish, Ctrl+K — nusxa,
Del — o'chirish, ↑/↓/Home/End — tanlov, ←/→ — yig'ish/ochish, Ctrl+Space — buyruq xossalari, F4 — xizmat buyruqlari, F9 — holat paneli
(muharrir ichida global «to'liq ekran» F9 o'rniga). Palitradan qo'shish: tanlanganidan keyin; «ichiga» tugmasi (yoki yangi blokdan keyin
avtomatik) — blokning oxiriga.

## 7. Ochiq savollar
Hisobotdagi «Foydalanuvchiga savollar» bo'limiga qarang (tasdiqlanmagan taxminlar yuqoridagi jadvalda «taxmin» deb belgilangan).
