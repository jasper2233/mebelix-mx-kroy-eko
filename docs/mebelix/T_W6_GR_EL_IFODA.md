# T. W6 paketi — GR, EL, ifoda API / yordamchisi, «Справка» va «Что нового» (v2.2, 2026-10-02)

## 1. Ifoda API (R17) va yordamchi komponent
- `GET /api/expr/functions` → `{groups[], functions[], constants[], operators[], limits}`. `functions[]` — 65 ta funksiya (`expr.FUNCTION_GROUPS`
  bilan bir xil): `group, name, signature, description(_ru/_uz), example, example_result, example_type, pure`. `description` — `Accept-Language`
  bo'yicha. Tavsif va misollar — `backend/app/services/expr_docs.py` (o'zimiz yozgan); misol natijalari dvigatelda **jonli** hisoblanadi
  (tasodifiy/vaqtga bog'liq `random`, `uuid`, `now` — tavsifiy matn / joriy sana).
- `POST /api/expr/check` `{expr, context?: {nom: son|matn|bool|null}, degrees?: bool}` →
  `{ok, type: integer|double|boolean|string|null, value, value_text, error, stage: syntax|eval|null}`. Faqat serverda hisoblanadi.
  Chegaralar: ifoda ≤ 1000 belgi (so'rovda ≤ 5000, undan ortig'i 422), 10 000 qadam, matn ≤ 10 000, `calculate` ≤ 4 daraja,
  kontekst ≤ 200 nom (nom ≤ 100 belgi, matn ≤ 1000, butun |x| ≤ 10¹⁵; aks holda 400). Dvigatel kutilmagan istisno bersa ham API 500 qaytarmaydi.
- Frontend: `frontend/src/shared/ExprHelper.tsx` — `<ExprHelper value onChange variables onInsert degrees compact/>` (tekshiruv + funksiyalar
  ro'yxati), alohida: `<ExprCheck/>`, `<ExprFunctions/>`, `<ExprLanguage/>`, `<ExprResult/>`, hooklar `useExprCatalog`, `useExprCheck`,
  funksiya `checkExpr`. W1 (XNC) va W4 (etiketka): `variables={[{name, label, sample}]}` bilan sinov qiymatlari beriladi, `onInsert` —
  imzoni kursor joyiga qo'yish. i18n kalitlari `exprh.*`.
- «Справка → Выражения»: til qoidalari, operatorlar, konstantalar, funksiyalar jadvali, tekshiruv oynasi.
- Dvigatel tuzatishi: `str.isdigit()` rost, lekin o'nlik raqam bo'lmagan belgilar (`²`, `①`) tokenizerda `AttributeError` berardi —
  endi sintaksis xatosi (`tests/test_expr_api_w6.py` da regressiya va fuzz).

## 2. GR (пазование)
- **Standart qiymatlar — bitta konstanta:** `models.GR_DEFAULTS` = W 4 / D 8 / O 10 mm, «Отступ включительно» ✓, arra 4 mm. Manba: `.project`
  formati (`format_ru`: `grWidth` 4, `grDepth` 8, `grOffset` 10, `grOffsetIncl` true, `grSawthick` 4). Avval kodda 4/10/16 turardi (manbasi
  topilmadi). Eski saqlangan loyihalar o'z qiymatlarini saqlaydi (modelda har maydon saqlanadi). Yangi operatsiya, importer (atribut yo'q bo'lsa)
  va panel shu konstantadan oladi. **Foydalanuvchi tasdig'i kerak** (hisobot §3).
- `gr_defaults` sozlama doirasi (`GRParams`; `usage/cut_length/passes` saqlanmaydi): panelda «Сохранить параметры по умолчанию»; yangi GR
  operatsiyasi (`main._new_operation`) shundan olinadi.
- `GET /api/projects/{pid}/operations/{oid}/groove-usage` (`api_gr.py`) → `{rows[], usage, cut_length, passes, cost}` (GR bo'lmagan operatsiya — 400).
- Importer: `grOffsetIncl`, `grSawthick` endi o'qiladi; 0 eni / arra — standartga.
- Panel (`features/el/GrPanel.tsx`): «Параметры» — W, D, O, «Отступ включительно», arra qalinligi, narx, hisoblangan uzunlik / o'tishlar / kesim
  uzunligi / narx (faqat o'qish), W/D/O sxemasi (o'zimiz chizgan, `GrSketch.tsx`); «Детали» — 10 ustunli jadval (`OpPartsGrid`).
- Chop: `Print.tsx` da «(GR) Пазование» bo'limi (`gr_params`, `gr_parts`).
- «Отступ включительно» **hisobga ta'sir qilmaydi** (uzunlik, narx, o'tishlar bundan mustaqil): ma'nosi (paz eni bilan sanaladimi yoki yo'qmi)
  yordamda yo'q — savol (hisobot §3). Bayroq loyihada saqlanadi va chop/yordamda ko'rsatiladi.

## 3. EL
- Har parametr yonida «?» (kontekst yordami) → «Справка → (EL) Кромка: параметры» shu bandga sakraydi (`HelpTip`, `helpStore.openHelp`).
- «Детали» jadvali: sarlavha bosilsa saralash, Ctrl+Space — detal xossalari, Home/End — birinchi/oxirgi qator, ↑/↓ — qatorlar
  (EL va GR uchun umumiy `OpPartsGrid.tsx`; qator № ustuni saralashdan keyin yangilanadi).
- Tegilmadi: kromka stanogi (`tool1`, ❓), hisob formulalari (`edge_usage` — o'zgarmagan; `tools/bench/el_check.py`: 303/303).

## 4. «Справка» va «Что нового»
- Bo'limlar: `keys, flow, cut, edge, el, gr, expr, machines, mes, whatsnew, about` (`features/help/helpStore.ts`, `Help.tsx`).
  «MES» matni panel tavsifi bilan to'ldirildi; «Станки и постпроцессор» — sozlamalardagi tayyor stanok nomlari ro'yxati (API'dan).
- «Что нового» (OL-013): ilova ichida, ru/uz, o'zimizning o'zgarishlar tarixi (v1.0, v2.0, v2.1, v2.2). **Yangi yozuv qo'shish:**
  `frontend/scripts/i18n_w6.py` dagi `_WN` ro'yxatida tegishli versiya ichiga `(qisqa nom ru, uz, tavsif ru, uz)` qo'shing (yangi versiya —
  yangi kalit `vNN`, ro'yxatning boshiga) → `python frontend/scripts/i18n_src.py`.
- i18n manbai: `frontend/scripts/i18n_w6.py`.

## 5. Testlar
`backend/tests/test_expr_api_w6.py` (ifoda API, hujjatlar, chegaralar, fuzz), `backend/tests/test_gr_el_w6.py` (GR standartlari, `gr_defaults`,
`groove-usage`, import, chop bayroqlari; EL kromka formulasi, yaxlitlash kodlari, «Учитывать материал», tor tomon ogohlantirishi).
