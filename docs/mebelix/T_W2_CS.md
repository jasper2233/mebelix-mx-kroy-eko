# T. W2 paketi — CS (listli kroy) bo'shliqlari (2026-10-02)

Manba: `giblab_inventory/01_CS_CSE_qoldiqlar.md` 4-bo'lim. Optimizator (`optimizer.py`, `colpack.py`) o'zgarmadi.
Raqamlar — shu bo'limdagi № lar.

## 1. Qilinganlar

| № | ID | Nima | Qaerda |
|---|---|---|---|
| 6 | CS-081, CSE-002 | Detallar jadvali ostidagi «Площадь» (va ixtiyoriy «area» ustuni) — **pilniy o'lcham** (zagotovka + pripusk) bo'yicha, kromkali detal o'lchami bo'yicha emas. Tahrir ro'yxatida Д-на/Ш-на — kartadagi (pripuskli zagotovka) o'lcham, yangi **Ткт** ustuni | `CsParts.tsx` `summary`, `columns.tsx` `area`, `CutEditor.tsx` |
| 8 | CS-036/037 | «Количество материала» va yangi «Количество листов» kroygacha ham ko'rinadi: taxminiy (≈) = detallar maydoni × (2 − taxminiy foiz/100), list soni = ⌈sarf / list maydoni⌉. Kroydan keyin — natijadan. Hisob backendda (`calc.cs_cost` info, endpoint `GET …/operations/{oid}/cs-quantities`). «Количество материала» birligi «по листам» ga qarab (list / m²) — D5 bo'yicha | `calc.py`, `api_cs_w2.py`, `CsParams.tsx`, `csHooks.ts` |
| 12 | DM-010 | Kartada pripusk **punktir** to'rtburchagi (detal ichida; burilgan detalda tomonlar kromka kabi almashadi). Ekran (`MapView`) va chop (`render.map_svg`); chopda `map_allowance` bilan o'chiriladi; pripusk 0 bo'lsa hech narsa chizilmaydi | `MapView.tsx`, `render.py` |
| 4 | CS-163/164/169/170/174–177, CS-161 | Chop sozlamalari: Книжная/Альбомная, izdeliya bo'yicha guruhlash, ishlov belgilari, kromka ustunini ajratish, shrift o'lcham/qalinligi/«разворачивать», detal/chiqindi rangi + shtrixlash, CS sarlavhasi — `H_REPORTS_LABELS.md` jadvali | `models.py` `PrintSettings`, `render.py`, `Print.tsx` + `PrintCsExtra.tsx` |
| 13 | CS-077, 075, 106, CSE-017, 003 | Shift+Enter, Ctrl+Enter/Ctrl+Tab, Shift+Del, Ctrl+PgUp (Листы — joriydan oldin), Home/End va F9 (tahrir) — `E_HOTKEYS.md` E8 | `CsParts.tsx`, `CsSheets.tsx`, `CutEditor.tsx`, `hotkeys.ts` |
| 14 | CS-082, DM-006, DM-007 | Д-на/Ш-на sarlavha va qiymat ranglari (ko'k / yashil / qizil kursiv); ▽△▷◁ ustunlarida har qatorda delta (−kromka, +prifugovka; «пильный» da pripusk kiritiladi); bo'sh jadvalda rejim taklifi («Настройки → Режим ввода деталей» ≠ «Не предлагать» bo'lsa, har loyihada bir marta; standart — taklif yo'q) | `columns.tsx`, `PartDialogs.tsx`, `CsParts.tsx`, `csW2.css` |
| 10 | CS-048 | Parametr yonida «?» va F1 (fokusdagi parametr yordami): 40 ta parametr, matn o'zimiz yozgan ru/uz (`phelp.*`); `Field help="…"` / `Check help="…"` | `ui.tsx`, `ParamHelp.tsx`, `paramHelpStore.ts`, `i18n_cs_w2.py` |
| 7 | CS-020/021/022 | Optimizatorga **ulanmagan** sozlamalar halol: «Объединение деталей» — o'chirilgan, belgilanmagan katak + «не работает — назначение уточняется (Q-2)»; «Группировка по свойствам» — o'chirilgan; «Сохранение чертежа карт кроя» — o'chirilgan (karta doim saqlanadi, Q-15). `merge_parts`/`save_drawings` modelda saqlanadi, optimizator ishlatmaydi | `CsParams.tsx` |
| 20 | CS-161, CS-014 | CS bo'lim sarlavhasi belgisi (`cs_title`); max polosa eni yonida «ma'nosi aniqlanmoqda» izohi (xulq o'zgarmadi) | |
| 3 | REM-004 / CS-104 | Qoldiq qatorida **«Исп. кол-во»** (mijoz olib ketgan bo'laklar): tahrirlanadi, omborga yozilmaydi; `Остаток = Количество − Исп.`. **Standart 0 — eski xulq (hammasi yoziladi).** Omborga yozilgach o'zgartirib bo'lmaydi (avval yozuvni bekor qiling). «Mayda qoldiq / butun list yozish» — komit oynasida o'chirilgan katakchalar (Q-5) | `models.py` `CuttingResult.taken_remnants`, `warehouse.py`, `api_cs_w2.py` (`PUT …/result/taken`, `GET …/remnant-groups`), `CsSheets.tsx`, `RemnantCommit.tsx` |
| 5 | REM-009 | **Rezerv:** `remnants.reserved_project` (migratsiya `db._migrate`, SQLite/PostgreSQL `ALTER TABLE ADD COLUMN`). Qoldiq «Листы и остатки» ga qo'shilganda loyiha uchun band qilinadi (butun qator); boshqa loyiha qo'sha olmaydi (409), qo'lda `PUT sheets` ham, omborga chiqim (`commit`) ham rad etiladi. Rezerv loyiha saqlanganda qoldiq listdan chiqqan bo'lsa yoki loyiha o'chsa avtomatik bo'shaydi (`store.save/delete`); eskirgan (loyihasi yo'q) rezerv to'siq emas. Ombor boshqaruvchisi uchun «Снять резерв» (`POST /remnants/reservations/release`) — tanlash oynasida | `db.py`, `warehouse.py`, `store.py`, `main.py` (3 joyda), `api_extra.py` (1 qator), `CsSheets.tsx` |

## 2. Qilinmaganlar va nega

* №1 postprotsessor (namuna fayl kerak), №2 «Минимальная обрезка» ma'nosi (jonli tekshiruv kerak), №11 CSE ko'p tanlash / Shift+A / Shift+W / kartalar tartibi (Q-8 javobsiz), optimizator algoritmi — topshiriqda taqiqlangan.
* №9 (CS-066 nomdagi belgilar) — Q-7 javobsiz.
* №20: **CS-039** «Стоимость (м2)» (ma'nosi noma'lum, Q-4), **CS-046** min. detal o'lchami (GibLab xulqi tasdiqlanmagan, Q-3 — bizdagi xulq: kroyga kirmaydi + ogohlantirish, o'zgarmadi), **CS-002** propil > 0 (Q-13: bizda 0 ruxsat) — foydalanuvchi javobini kutadi; **CS-022** — №7 da yuqorida.
* №16–19 (SP, CL, 1C, katalog daraxti) — boshqa to'lqin.

## 3. Standartlar va xavfsizlik

* Yangi `PrintSettings`/`CuttingResult` maydonlari standart qiymat bilan: eski profil/loyiha JSON ochiladi (testlar bor). Standartda SVG chiqishi avvalgidek (faqat pripusk > 0 bo'lgan loyihalarda punktir qo'shiladi; `map_allowance` bilan o'chadi).
* `render.py`: ranglar `safe_color` + model regexi (`#rrggbb`) dan o'tadi; guruh sarlavhasi va barcha matn `escape` qilinadi.
* «Исп. кол-во» kaliti: `b:UxE` / `r:UxE` (U×E — foydali o'lcham, yuzdan birlarda butun son; frontend va backend bir xil formula).
* Rezerv — qator darajasida (butun qator, soni qanday bo'lmasin). Qisman rezerv (soni bo'yicha) qilinmagan.

## 4. Testlar

`backend/tests/test_cs_w2_print.py` (13), `test_cs_w2_calc.py` (6), `test_cs_w2_remnants.py` (12): chop sozlamalari, pripusk geometriyasi (burilgan/ko'zgu), kvantlar (kroygacha/keyin), «Исп. кол-во» oqimi, rezerv (to'qnashuv, bo'shatish, eskirgan, atomik, undo/redo), migratsiya.

Rezerv va loyiha saqlash: `store.save` har saqlashda `warehouse.sync_reservations` chaqiradi — loyiha listlarida turmagan qoldiq rezervi bo'shatiladi, listda turgan va hech kim band qilmagan qoldiq band qilinadi (eski loyihalar va undo/redo uchun).
