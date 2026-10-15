# T. W8 paketi — XNC muharriri sozlamalari: Инструменты · Палитра · Ограничения (2026-10-02)

Manba: `giblab_inventory/06_online_korik.md` §3 (onlayn «XNC Редактор» dialogi, uch yorliq), `04_XNC_postprotsessor_format.md`
(XNC-109 asboblar, XNC-110 palitra, XNC-111/125–127 cheklovlar). Sxemalar va nomlar bizniki; faqat funksional ma'no olingan.
UI: **Настройки → XNC редактор** (`features/xnc/XncSettings.tsx`), XNC panelida cheklov xabarlari va asbob nomi takliflari.

## 1. Modullar
| Nima | Fayl |
|---|---|
| Cheklovlar modeli (`XncConstraints`), tekshiruv (`check_program`), burish hisobi (`pick_turn`), `analyze`, `stats_fields` | `backend/app/services/xnc_constraints.py` |
| Asboblar jadvali (`XncToolsDoc`, `ToolLib`), palitra (`XncPalette`), hisob uchun keshlangan jadval (`current_library`) | `backend/app/services/xnc_tools.py` |
| Hisobda zaxira (`tool_lib`, `set_tool_library_provider`), `cmd_path`, `machine_program(…, constraints)` | `backend/app/services/xnc.py` (kichik Edit) |
| `context_xnc(…, constraints)`: `constraints`, `constraint_issues`, `extra_turn`, `rotation` | `backend/app/services/postprocessors.py` |
| Sozlama doiralari `xnc_constraints` / `xnc_tools` / `xnc_palette` + kesh yangilanishi | `backend/app/services/settings.py` |
| `GET …/xnc-constraints`, postprotsessorga cheklovlarni uzatish, asboblar jadvalini ulash | `backend/app/api_xnc.py` |
| `xnc-stats` ga `constraint_issues`, `constraint_mode`, `constraint_turn` | `backend/app/main.py` (3 qator) |
| UI | `frontend/src/features/xnc/{XncSettings,XncIssues}.tsx`, `xncSettingsApi.ts`; `XncProgramTab.tsx` (palitra, T/N takliflari, F9), `XncPanel.tsx`, `Settings.tsx` (1 qator) |
| i18n | `frontend/scripts/i18n_xnc_w8.py` (`xs.*`, `settings.page.xnc`), `backend/app/i18n.py` (`xnc_cn.*`, `xnc_tools_*`) |
| Testlar | `backend/tests/test_xnc_w8_constraints.py` (43), `test_xnc_w8_tools.py` (14) |

## 2. Ma'lumot tuzilmalari (`/api/settings/<doira>/default`, GET/PUT)
**`xnc_constraints`**: `mode` (`off|warn|block`, standart `off`); har son cheklovi `{enabled, value}` (mm): `length_min 200`, `length_max 3000`,
`width_min 70`, `width_max 950`, `thickness_min 12`, `thickness_max 60`, `hole_center_{top,bottom,left,right} 30`,
`groove_margin_{top,bottom,left,right} 30`, `mill_max_distance 100`, `blind_depth_margin 2`, `hole_gap_min 5`, `hole_edge_front_min 4`,
`hole_edge_horizontal_min 3` (hammasi `enabled=false`); `rotate_long_side` (`off|horizontal|vertical`), `rotate_corner_on` + `rotate_corner`
(`LT|RT|LB|RB`); belgilar `{enabled, value}`: `groove_horizontal` (value — «ruxsat», standart true), `groove_vertical` (false),
`avoid_bottom_horizontal` (value — «afzallik», true). Eski/qisman JSON: ichki obyektda `value` yo'q bo'lsa — shu maydonning standarti; noma'lum
kalitlar e'tiborsiz; yoqilgan `min > max` — 4xx.
**`xnc_tools`**: `{tools: [{plane: front|left|right|top|bottom, d, through, name, depth|null, comment}]}`. Standart: frontal `Bore35/26/25/20/18/15/10/8/7/5/4.5/3`,
chap/o'ng/yuqori/pastki `Bore8`, `Bore4.5` (20 qator; nom — diametrdan, o'zimiz yozdik). (tekislik, nom) takrorlanmaydi; `through` faqat frontal.
**`xnc_palette`**: `{items: [{cmd, enabled}]}` — tartib = tugmalar tartibi; noma'lum buyruq tashlanadi, yetishmaganlari oxiriga (yoqilgan) qo'shiladi.

## 3. Hisob va tekshiruv qoidalari
- **Asbob zaxirasi.** Diametr: buyruqdagi `D` → dasturdagi `Tool` → jadval (tekislik+nom, keyin faqat nom) → standart (teshik 5, paz 4, freza 0). Teshik chuqurligi
  (`DP` berilmaganda va oldingi buyruqdan meros bo'lmasa): jadvaldagi `through` → qalinlik; `depth` berilgan → shu; aks holda qalinlik. `Tool` buyrug'ida `D` yo'q va nom jadvalda
  bor → jadval diametri. Jadval **faqat ulangan bo'lsa** (`api_xnc` import qilinganda) qatnashadi — skriptlar/korpus tekshiruvi avvalgidek (`program_stats(…, tool_lib={})`).
  Korpus: `xnc_check.py` **8359 / 8360 / 8360** (jadvalsiz ham, `--lib` bilan ham, 8360 dasturning hammasida natija aynan bir xil).
- **Rejim.** `off` — tekshiruv ham, avtomatik burish ham yo'q. `warn` — xabarlar `level=warn`. `block` — `level=error`.
  Istisno: `avoid_bottom_horizontal` da `value=true` («afzallik») bo'lsa daraja doim `warn`.
- **Stanok orientatsiyasi.** Hamma tekshiruv `machine_program` natijasida (burish/ko'zgu/koordinata boshi qo'llangan; X — burishdan keyingi uzunlik, Y — en, Z — qalinlik;
  «yuqori/past/chap/o'ng» — shu holatda). Xabar: `{level, code, text (so'rov tili), text_ru, text_uz, command_path ("2.3", 1 dan; detal darajasida ""), count}`;
  massiv teshiklar bitta qator (`×N`); ro'yxat ≤ 100 qator + «yana N».
- **Tekshiruvlar (kodlar):** `len_min/len_max/wid_min/wid_max/thk_min/thk_max`; `hole_center_far` (gorizontal teshik Z > chegara, tomon bo'yicha);
  `groove_horizontal/groove_vertical` (taqiqlangan paz), `groove_margin`; `mill_far`; `bottom_horizontal`; `blind_depth` (ko'r frontal teshik DP > qalinlik − X);
  `hole_gap` (chetlar orasi, bir tekislikda; saralab qo'shnilarni solishtiradi); `hole_edge_front`; `hole_edge_horizontal`.
- **Burish.** `xnc.machine_program(op, project, long_side="any", constraints=None)`: aniq `long_side` (so'rov parametri) cheklovdan ustun; aks holda `constraints.rotate_long_side`.
  «Kromka bilan burchakka»: `pick_turn` — (a) «uzun tomon» talabi bergan juftlikdagi (0/180 yoki 90/270) burishlardan, (b) birinchi kromkali tomon burchakning ikki
  tomonidan biriga tushadigan **eng kichik** burish (avval o'zgarishsiz). Natija: `extra_turn` (qo'shimcha burish), `rotation = {long_side, corner, target, rule, turn}`;
  `context_xnc.turn` = mavjud burish + `extra_turn`, `edges_final` shunga mos. Hisoblash faqat ma'lumot: chizma (`xnc.svg`) burilmaydi, stanok formati yo'q.

## 4. Konstantalar (`services/xnc_constraints.py`) — ❓ qarorlar (yordamda aniq emas)
| Konstanta | Standart | Nima |
|---|---|---|
| `CORNER_EDGE_RULE` | `"first"` | Bir nechta kromkali tomon bo'lsa — birinchisi (`EDGE_ORDER`: yuqori, past, chap, o'ng) burchakka tushadi. `"max"` — burchakdagi kromkali tomonlar soni eng ko'p burish |
| `GROOVE_MARGIN_ALL_SIDES` | `True` | «Paz chetidan min. masofa»: pazning chegaraviy to'rtburchagi 4 tomon bo'yicha (chetdan chetgacha paz chap/o'ng chegarani buzadi). `False` — faqat ko'ndalang tomonlar |
| `MAX_ISSUES`, `MAX_PAIRS` | 100, 400 | Xabarlar va teshik juftliklari chegarasi |
| `LIB_TTL` (`xnc_tools.py`) | 3 s | Hisobdagi asboblar jadvali keshi (sozlama yozilganda darhol yangilanadi) |

## 5. Foydalanuvchiga savollar (hisobotda ham)
1. «Режим» qiymatlari (onlayn faqat «Выключить» ko'rindi): `off / warn / block` bizning taxminimiz. `block` hozir faqat xabar darajasini («xato») belgilaydi — eksportni **to'smaydi**. To'ssinmi?
2. «Paz» ikki katakcha (chap — yoqish, o'ng — ichki belgi): ichki belgi **«ruxsat»** deb olindi (gorizontal — ruxsat, vertikal — taqiq). To'g'rimi? Gorizontal/vertikal paz — detal (stanok holatidagi) X/Y bo'yicha.
3. «Минимальный отступ от края детали к пазу»: chetdan chetgacha o'tuvchi paz (orqa devor pazi) chap/o'ng chegarani buzadi (`GROOVE_MARGIN_ALL_SIDES`). Maqsad shumi yoki faqat ko'ndalang masofa?
4. «Фрезерование (Радиусы) — максимальное расстояние от детали до фрезы»: frezaning detal to'rtburchagidan **tashqaridagi** eng uzoq nuqtasi (uchlar bo'yicha) deb olindi. To'g'rimi?
5. «Gorizontal teshik markazidan frontal tekislikkacha» = yon teshikning Z si (frontal yuzadan); tomon — burishdan keyingi stanok tomoni. Orqa yuzadan ishlov (`face_side=false`) alohida hisobga olinmagan.
6. «(предпочтение)» — «Нежелательные горизонтальные сверления снизу» yonidagi ichki belgi sifatida: belgi bor — doim ogohlantirish, yo'q — rejimga qarab xato.
7. «Kromka bilan burchakka»: bir nechta kromka bo'lsa qaysi biri burchakda bo'lishi kerak? Hozir — birinchi kromkali tomon (`CORNER_EDGE_RULE`). «Afzallik / majburiy» (XNC-125/126) farqi bizda ma'lumot-hisobda
   farq qilmagani uchun kiritilmadi — kerakmi? Shuningdek burish bilan birga ko'zgu (mirror) ham ruxsatmi?
8. «Палитра»: onlayn dialogda faqat bitta qator («Сверление») ko'rindi; bizda hamma 31 buyruq (yoqish/o'chirish + tartib). Boshqacha (guruhlab) kerakmi?
9. Asbob «Глубина» ustuni: teshik chuqurligi **standarti** (buyruqda `DP` bo'lmasa) deb olindi; «Сквозное» — chuqurlik = qalinlik. Yordamda ma'nosi yo'q — tasdiqlang.
