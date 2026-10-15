# T. W18 · XNC bo'shliqlari (3-blok): sudrab ko'chirish, MillFillet, matn Par, chizmada burish, orqa yuza, F4

Avvalgi paketlarning (`T_W1_XNC.md`, `T_W8_XNC_SOZLAMALAR.md`) «Qilinmadi» qoldiqlari. Hamma qaror bitta konstanta orqasida (jadval §6);
yordamda aniq bo'lmagan joylar «❓» va §7 savollarda.

## 1. Fayllar
| Nima | Fayl |
|---|---|
| MillFillet geometriyasi (toza: chiziq / yoy, urinma aylana) | `backend/app/services/xnc_fillet.py` (yangi) |
| Fillet integratsiyasi, matn Par / Var, chizmada burish | `backend/app/services/xnc.py` (`apply_fillets`, `par_string`, `xnc_drawing_svg(turn, turned)`, `machine_program()["face_back"]`) |
| Orqa yuza cheklovlari | `backend/app/services/xnc_constraints.py` (`BACK_FACE_MIRROR`, `machine_side`, `pick_turn(back=)`) |
| Matn Par `.project` eksporti | `backend/app/services/project_export_xnc.py` (3 qator) |
| `eval_number`: matn natijasi — «operand turi noto'g'ri» | `backend/app/services/expr.py` (1 qator) |
| Chizma endpointi (`machine=true`) | `backend/app/main.py::xnc_svg` |
| Xabarlar | `backend/app/i18n.py` (`xnc.w_fillet_*`, `xnc.e_str_long`, `xnc.turn_badge*`) |
| Sudrab ko'chirish (toza amal + HTML5 DnD) | `frontend/src/features/xnc/treeOps.ts` (`moveTo`, `canDrop`), `treeDnd.ts` (yangi hook), `XncProgramTab.tsx`, `ProgramEditor.tsx` (mahsulot «Программа» si ham), `xnc.css` |
| Matn Par UI | `ParForm.tsx`, `xncSchema.ts` (`PAR_TYPES`, `isTextParam`), `XncProgramTab.tsx::ParamRow(text)`, `types.ts::XncParamState` |
| Stanokdagi ko'rinish tugmasi | `XncPanel.tsx` (`xnc-machine-view`) |
| i18n | `frontend/scripts/i18n_w18_xnc.py` |
| Testlar | `backend/tests/test_w18_xnc.py` (21), `frontend/scripts/check_treeops.mjs` (toza amal, 8700+ tekshiruv) |

## 2. Sichqoncha bilan sudrab ko'chirish
Daraxtdagi har qator `draggable`. Tashlash joyi qator balandligi bo'yicha: **blok** (If / Else / While / DoWhile / Sub) qatorida yuqori chorak — «oldin»,
o'rta — **ichiga** (blokning oxiriga), pastki chorak — «keyin»; oddiy qatorda yuqori yarmi — «oldin», pastki — «keyin». Ko'rsatkich: `data-drop="before|after|inside"`
(chiziq / ramka), sudralayotgan qator `data-dragging="1"` (xira). Mantiq — `treeOps.moveTo(prog, from, target, pos)` (toza, kirishni o'zgartirmaydi, yangi dastur + tanlov):
o'ziga yoki o'z ichiga (avlodiga) tashlash taqiqlangan; oddiy buyruq «ichiga» bo'lmaydi; joyi o'zgarmasa `null`; ko'chirilgan buyruq ichidagilari bilan ketadi; yo'llar
ko'chirishdan oldingi daraxtga nisbatan, keyingi qo'shnilar indeksi moslanadi. Klaviatura (Ctrl+←/→/↑/↓, Ctrl+K, Del) o'zgarmagan. Tekshiruv:
`node frontend/scripts/check_treeops.mjs` (tasodifiy daraxtlarda: to'plam saqlanishi, ko'chirilgan buyruq yangi yo'lda, nishonga nisbatan joylashuv, qolganlar tartibi, taqiqlar) va
haqiqiy Chromium'da (Playwright, DOM + REST): oldin/keyin/ichiga, o'z ichiga tashlash rad, Ctrl+↓, F4.
`data-testid`: qatorlar `prog-item-<yo'l>` (XNC: «1.0» — 1-qatorning 1-bolasi; mahsulot dasturi: `pprog-item-…`), ro'yxat `xnc-program`.

## 3. MillFillet: chiziq–yoy, yoy–chiziq, yoy–yoy (`xnc_fillet.py`)
Qo'shni ikki kontur segmenti (MillLine / MillArc / MillArcCenter / MillArc3P). Qoida: burilish tomoni `s` (±1, tangent vektor ko'paytmasi) → har segmentning `s` tomonga `R` ga
siljitilgani (chiziq — parallel; yoy — o'sha markaz, radius `ρ − s·d·R`) → fillet markazi ularning kesishmasi (≤ 2 nuqta) → nomzod yaroqli, agar urinish nuqtalari o'z segmentining
ichida bo'lsa; yaroqlilar orasidan burchak P ga eng yaqini. Qisqartirilgan yoy **markazli shaklga** (MillArcCenter) o'tadi (aylana o'zgarmaydi); keyingi yoy T2 dan boshlanadi.
Xabarlar (burchak o'zgarishsiz): `w_fillet_geom` (qo'shni segment emas: MillStart, MillRect…), `w_fillet_none` (urinma aylana yo'q: offsetlar kesishmaydi), `w_fillet_big` (R katta);
burchaksiz (to'g'ri chiziq, urinma davomi, qaytish) — jim. Chizma, `machine_program` (`fillet: true`) va statistika bir xil `evaluate()` natijasini ishlatadi.
Testlar: qo'lda hisoblangan chiziq–yoy (urinish nuqtalari, markaz, uzunlik), 800 tasodifiy holat (4 birikma ham ≥ 160 tadan): R masofa, ikkala segmentga urinish, segment ichida
yotish, **G1 uzluksizlik** (T1, T2 da yo'nalish), rad etilganda sababi xabarda.

## 4. Matn (string) Par
`Par type=string`: `value` (standart) va operatsiyada kiritilgan qiymat (`par_values[nom]`) — **matn** (ifoda emas; `xnc.PAR_STRING_LITERAL=True`; False — ifoda sifatida hisoblanib matnga aylanadi).
Qiymat o'zgaruvchiga matn bo'lib yoziladi: `par + '.nc'`, `len(par)`, `par = 'abc'`, `If cond="mode = 'B'"` — hammasi `expr.py` ning tipli qiymatlari bilan. Sonli parametrda matn ishlatilsa —
jim 0 emas, «operand turi noto'g'ri» xabari va buyruq bajarilmaydi. Bo'sh kiritilgan qiymat — «kiritilmagan» (standart); `readonly` — kiritilgan qiymat e'tiborsiz. Chegara: 200 belgi
(`MAX_PAR_STRING`; `par_values` modeli ham 200 dan ortig'ini rad etadi, uzun standart qiymat qisqartiriladi + xabar). Son sifatida kelgan matn (UI «123» ni songa aylantirgan bo'lsa) «5.0» emas «5» bo'ladi.
`Var type=string` / matn o'zgaruvchiga `Set` ham ishlaydi (qiymat — ifoda, natija matnga aylantiriladi). Mahsulot «Программа» sida matn Par ishlaydi, lekin `product.<nom>` kontekstiga faqat sonlar uzatiladi
(matn o'zgaruvchilar kirmaydi). `.project` eksporti: `<var type="string" expr="'matn'"/>` (satr literali `\` va `'` bilan ekranlangan) ❓ — GibLab bu `var` turini qabul qilishi tasdiqlanmagan.
UI: «Параметры» yorlig'ida matn maydoni (`par-<nom>`, ≤ 200 belgi), «Шаблон» da `Par.type` ro'yxatida «Строка», `value` matn sifatida saqlanadi («007» songa aylanmaydi).

## 5. Chizmada cheklov burishi (W8 `extra_turn`)
`xnc_drawing_svg(op, project, width, turn=0, turned=False)`: `turn` (0/90/180/270) berilsa chizma tagida `↻ …` yozuvi chiqadi (`<g class="xnc-turn" data-turn data-turned>`; `DRAW_TURN_BADGE`);
`turned=True` — chizma stanokdagi (qo'shimcha burilgan) holatda chiziladi, kromka belgilari ham aylanadi. Endpoint: `GET …/xnc.svg?machine=true`; `turn` — `xnc_constraints.analyze()["extra_turn"]`
(rejim off — 0, hech narsa o'zgarmaydi). UI: chizma ustida «Вид на станке» katakchasi (`xnc-machine-view`), faqat yozuv bor bo'lganda ko'rinadi; chizma konteyneri `xnc-drawing`.

## 6. Orqa yuza (`face_side=false`) uchun cheklov hisobi
`xnc_constraints.BACK_FACE_MIRROR = "x"` ❓: orqa yuzadan ishlovda detal stanokka ag'dariladi (kitob varag'i kabi: **chap ↔ o'ng**, yuqori/past o'zgarmaydi); dastur tomonlari detalning o'z holatida,
cheklovlar esa stanok tomonlari uchun yoziladi → `machine_side(tomon, back)`. Ta'sir qiladi: gorizontal teshik `hole_center_<tomon>`, paz `groove_margin_<tomon>`, `avoid_bottom_horizontal` («y» da),
«kromka bilan burchakka burish» (`pick_turn(back=True)`: burishdan keyingi tomon akslanadi). Ta'sir qilmaydi: gabarit, paz yo'nalishi, teshiklar orasi / chetidan masofa, freza (tomonga bog'liq emas).
`"y"` — gorizontal o'q (yuqori ↔ past), `"none"` — akslanmaydi. `machine_program()` ga `face_back` qo'shildi (ishlov markazi kontekstida `xnc.face` allaqachon bor).

## 7. F4 xizmat buyruqlari — tekshiruv natijasi
* 15 ta xizmat buyrug'i (Com Par Var Set If Else While DoWhile Break Continue Sub Call Ret Msg Err) onlayn palitra bilan **aynan mos** (`06_online_korik.md`); `Tool` xizmat emas.
* F4 va «ListTree» tugmasi (`xnc-svc`) xizmat buyruqlarini palitrada yashiradi/ko'rsatadi (E_HOTKEYS E7 bilan mos); F9 — holat paneli.
* Topilgan nuqson (tuzatildi): daraxtdagi «Включить» katakchasi bosilgach fokus `INPUT` da qolib, ↑/↓/F4/F9 yorliqlari ishlamay qolardi — `onChange` da `blur()`.
* Qoldi: F4/F9 matn maydoni ichida ishlamaydi (umumiy `hotkeys.ts` qoidasi: faqat F1 «ALWAYS»); loyihalar ro'yxatida F4 = «Переместить» — boshqa maydon, to'qnashmaydi.
* FOR sikli (`cmdFOR` ikonkasi) — yordamda tavsif yo'q (XNC-061 ❓), qo'shilmadi.

## 8. Qarorlar / konstantalar
| Konstanta | Standart | Joy |
|---|---|---|
| `PAR_STRING_LITERAL` | `True` — Par matni ifoda emas | `xnc.py` |
| `MAX_PAR_STRING` | 200 | `xnc.py` |
| `DRAW_TURN_BADGE` | `True` | `xnc.py` |
| `BACK_FACE_MIRROR` | `"x"` (chap ↔ o'ng) | `xnc_constraints.py` |
| `FLAT_EPS_LINE / FLAT_EPS_ARC / POS_EPS` | 1e-9 / 1e-7 / 1e-7 | `xnc_fillet.py` |

## 9. Foydalanuvchiga savollar
1. Orqa yuzadan ishlovda stanok tomonlari qanday akslanadi: tik o'q atrofida ag'darish (chap ↔ o'ng) to'g'rimi yoki gorizontal (yuqori ↔ past)? (`BACK_FACE_MIRROR`)
2. Matn Par qiymati ifoda emas, oddiy matn bo'lsin (hozir) yoki GibLabdagidek ifoda? Bo'sh kiritilgan matn — «standartga qaytarish» (hozir) yoki haqiqiy bo'sh satr?
3. `.project` eksportida matn Par `<var type="string" expr="'…'">` shaklida — GibLabda ochilishini bitta fayl bilan tekshirish kerak.
4. Chizma stanok cheklovi bergan burishda qanday ko'rinsin: yozuv + ixtiyoriy «Вид на станке» (hozir) yoki chizma doim stanok holatida?
5. FOR sikli (XNC-061) kerakmi? Yordamda yo'q.
