# X. Onlayn tizim bilan solishtiruv, ko'p-kroyli loyihalar auditi va MCP serveri (2026-10-15)

Foydalanuvchi talabi: MX Kroy ni onlayn tizim (giblab.com, Chrome'da ochiq) bilan solishtirish, umumiy ishlash prinsiplaridagi
farqlarni to'ldirish — ayniqsa **bitta loyiha ichida bir nechta kroy (CS) va ularning listlari**; har funksiyani sinchiklab tekshirish;
onlayn tizim bilan ishlash uchun **MCP** yozish. Qoidalar o'zgarmadi: onlayn tizimning kodi / resurslari / kaliti ishlatilmaydi,
faqat ko'rish va o'qish; yozuvchi amallar faqat «test uchun» papkasida va bu sessiyada ishlatilmadi.

## 1. Korpus faktlari (1248 `.project`, mijoz nomlarisiz)
* 913 fayl (73 %) — bir nechta CS: 2 ta — 354, 3 — 226, 4 — 136, 5 — 91, 6 — 44, 7…14 — 62 fayl. Jami 3507 CS (1928 natijali), 2002 EL, 43 439 XNC.
* Bitta detal ikki CS da — 0 holat; bitta material ikki CS da — 2 fayl; EL operatsiyasi bir nechta CS ga umumiy — 220 fayl.
* `cPartCount` = Σ detal soni (1868/1928; qolganida mahsulot soni > 1). `cSizeMode` loyiha ichida aralashmaydi.
* `waste="true"` qatorlar (1330) — hamisha joriy kroyning o'z natijasi (деловой, `usedCount` 0, `dbId` yo'q); keyingi loyihada stock
  sifatida ishlatilmaydi (859 cheklangan qatorning 1 tasi avvalgi qoldiqqa teng). Xodimlar qoldiqni oddiy list qatori sifatida qo'lda
  yozadi (875 qator soni < 10000). → importerning `waste` qatorlarni tashlab yuborishi to'g'ri.
* Cheklangan (qoldiq) qatorlar: to'liq ishlatilgan 174, qisman 3, cheksiz list ishlatilgani holda ishlatilmagan 13 (mayda qoldiqlar).

## 2. Onlayn tizim bilan jonli solishtiruv (Chrome kengaytmasi, faqat ko'rish)
| Nima | Onlayn | MX Kroy | Natija |
|---|---|---|---|
| «Общие действия» | 3 amal: «Объединить операции с одинаковым кодом и наименованием материала», «Разделить операции кромкования по материалам кроя», «Оптимизировать операции» | shu 3 + «Пересчитать параметричность», «Перекодировать XNC», «Очистить проект» + yangi **«Раскроить все операции»** | mos; qo'shimchalar bizniki |
| «Листы и остатки» ustunlari (xodimlar sozlagan) | Длина · Ширина · Сони · Квадрати · Ишлатилди · Колдик · ТД · ТШ · Изох | bir xil (`A_GLOSSARY`) | mos |
| 5000 kupe (test papkasi) | LMDF: 5 list, 47 detal, LT 113.3 m, F 87.96 %; XDF: 2 list | LMDF: 5 list, F 87.96 %, LT 103.57 m; XDF: 2 list, F 81.69 % | listlar va F teng, kesish −9 % |
| 3120 kuxniya (5 CS, 141 detal) | LDSP 8 list (F 93.85), XDF 2, AKRIL KASHMIR 4, Stolishnitsa 2, AKRIL OQ 2 (fayldagi saqlangan natija) | 8 (F 92.15), 2 (81.69), 4 (88.99), 2 (86.46), 2 (86.26) | listlar teng; joylashmagan 1 + 2 detal — ikkala tizimda ham (listdan katta / tekstura bilan sig'maydi: `cPartCount` 140/24) |
| «Раскрой» varag'i (3120) | brauzer renderini daqiqalab band qiladi (tab muzlaydi) | — | onlayn tizim tomonidagi muammo; kichik loyihalarda ishlaydi |

MCP `compare_project` bilan (import → hamma CS kesish → fayl bilan jadval): 5000 kupe — **18 list vs 18**, деловой 7.07 vs 7.07 m²,
kesish 251.5 vs 270.5 m, joylashmagan 0.

## 3. Audit (2 mustaqil agent, faqat o'qish) — topilgan va tuzatilganlar
| № | Nuqson | Tuzatish |
|---|---|---|
| 1 | «Объединить одинаковые» faqat kod + nom bo'yicha: «Devor» 100 va 200 mm bitta 100 mm operatsiyaga qo'shilardi; birlashtirilgan operatsiyaning list qatorlari yo'qolardi | `main._merge_key` — material qalinligi va asosiy list o'lchami ham solishtiriladi; `_merge_sheets` — qatorlar birlashadi (soni qo'shiladi) |
| 2 | «Раскроить все» yo'q (har CS alohida) | `POST /projects/{pid}/actions/optimize-all` (bitta tarix qadami, har operatsiya natija/xato) + «Общие действия → Раскроить все операции» |
| 3 | CS o'chirilganda detallarga bog'langan XNC dasturlari jimgina o'chardi | tasdiq oynasida soni aytiladi (`ops.delete_xnc_q`) |
| 4 | «Разделить кромку по материалам» nusxasi belgisi/rangini takrorlardi | `el_symbols.next_style` — keyingi bo'sh belgi va rang |
| 5 | «Минимальный отступ в конце» list qatorida o'zgarsa natija eskirmasdi | `set_sheets` — otstuplar ham solishtiriladi |
| 6 | Listlar ro'yxatida bir xil `id` li ikki qator qabul qilinardi; omborda yo'q `source_remnant_id` jimgina saqlanardi; `description` cheksiz | 422 / 404 / 500 belgi |
| 7 | Boshqa qalinlikdagi qoldiq qo'shilib, chiqimda yolg'on «не хватает остатков» (409) | `from-remnants`: qalinlik mos kelmasa 400 (UI «Показать все материалы» → `force=true`); `_same_remnant` material kodini solishtirmaydi (raqamlar qayta berilmaydi) |
| 8 | Nusxa loyiha ombor havolalarini (`source_remnant_id`) saqlardi | nusxada tozalanadi (import kabi) |
| 9 | `POST /catalog/sync` yuborilmagan maydonlarni o'chirardi, tekshiruv yo'q | mavjud tovarda faqat yuborilgan maydonlar (qisman yangilash), `kind` ro'yxati, narx/ombor ≥ 0, uzunlik chegaralari |
| 10 | Katalogda yo'q `material_id` bilan operatsiya yaratilardi | 404 |
| 11 | Listdan katta detal jimgina «sig'magan» bo'lardi | natija ogohlantirishi «N дет. больше любого листа» |
| 12 | List tartibi: optimizator ro'yxat tartibini qat'iy bajarmaydi (eng kam maydon tanlaydi) | yangi parametr **«Порядок листов»** (`cs_cut.stock_order`): `list` (qat'iy, **standart — foydalanuvchi qarori**) / `economy` (avvalgi xulq: tartiblar sinaladi, eng kam maydon). Korpus (44 ko'p-listli kroy): qat'iy **603.9 m²**, economy **574.0 m²**, avvalgi tizim 581.9 m² (onlayn tizim ham ba'zan mayda qoldiqlarni tashlab ketadi: 1014 so'qoq 1.51 m²) |

Tekshirilgan va mos (o'zgartirilmadi): import (CS/EL/XNC soni, material, detallar = `cPartCount`, kromka va XNC havolalari, umumiy EL),
har CS alohida kroy, Ctrl+M (boshqa CS ga ko'chirish — kromka/XNC saqlanadi, qalinlik yangilanadi), undo/redo, hisobot (har CS bo'limi),
etiketkalar (hamma CS), MES eksport (hamma CS), `.project` eksport → qayta import (tuzilma teng), qoldiqlar oqimi (chiqim/rezerv/bekor),
«Листы и остатки» tugmalari («Сортировка», «Удалить неиспользуемый материал» — allaqachon bor).

## 4. MCP serveri (`mcp/`, `.mcp.json`)
Node 24 + `@modelcontextprotocol/sdk` 1.32 + Playwright 1.64 + zod 4; **83 vosita**: `mx_*` (REST: loyihalar, operatsiyalar, detallar,
listlar, kroy, natija, qoldiqlar ombori, katalog, hisobot/etiketka, postprotsessor, MES, sozlamalar, `mx_api`), `compare_*`
(fayl bilan / onlayn bilan), `giblab_*` (brauzer: ro'yxat, loyiha, operatsiyalar, varaqlar, jadvallar, ko'rsatkichlar, dialoglar,
inventar, skrinshot; yozuvchilar `GIBLAB_ALLOW_WRITE=1` + `GIBLAB_WORK_FOLDER`). Sahifa kutubxonasi `window.__gl` (`giblab_pagelib`) Chrome
kengaytmasi bilan ham ishlatiladi. Testlar: `npm test` (tahlilchi + stdio tutun testi, MX bilan), `GIBLAB_TEST=1 npx tsx --test
test/giblab.test.ts` (Chrome profil rejimi, kirish sahifasi). CLI: `node scripts/compare-file.mjs <fayl.project> [normal] [--keep]`.
Batafsil — `mcp/README.md`.

## 5. Foydalanuvchiga savollar (taxmin qilinmadi)
**Javob berilgan (2026-10-15):** 5 — standart **qat'iy ro'yxat** (`stock_order="list"`); 4 — ha, qalinligi boshqa operatsiyalar birlashtirilmaydi.
1. CS o'chirilganda onlayn tizimda uning XNC dasturlari ro'yxatda qoladimi? (bizda o'chadi, endi ogohlantirish bilan.) — qayta tushuntirildi, javob kutilmoqda.
2. «Клонировать» CS — detallarning XNC dasturlari ham nusxalanadimi? (bizda havolalar tushib qoladi.)
3. «Оптимизировать операции» onlayn tizimda aynan nima qiladi (bo'sh operatsiyalar, tartib, birlashtirish)?
4. ✅ Bir xil nomli, lekin qalinligi boshqa ikki CS «Объединить» da birlashtirilmaydi.
5. ✅ «Порядок листов» standarti — qat'iy ro'yxat (xodimlar odati); «Экономия материала» — tanlov.
6. «Заявка на склад»: har operatsiya uchun alohida qator (hozirgi, onlayn kabi) yoki material bo'yicha yig'ilgan? Hisobot sarlavhasida
   jami listlar / m² / kesish kerakmi?
7. Nusxa loyiha avval omborga yozilgan qoldiqlarni yana yozishi mumkin (ikki marta) — bloklansinmi?
8. MES: qoldiqlar chiqim/bekor hodisalari (webhook), butun listlar zaxirasi (`catalog.stock`) — MES tomonidami?
9. Qoldiq ombori oynasida boshqa qalinlik faqat «Показать все материалы» bilan qo'shiladi — to'g'rimi?
10. Importda `count=0` list qatorlari (korpusda 13) ko'rsatilsinmi (onlayn ko'rsatadi, biz tashlaymiz)?

## 7. Buyurtmalar navbati va material bazasi (foydalanuvchi javobi, 2026-10-15)
Talab: loyihalar navbat (kelish) tartibida ko'riladi; birinchisi uchun bazada material bormi tekshiriladi, bo'lmasa keyingi
buyurtmaga o'tiladi va «bazani to'ldirish kerak» ogohlantirishi beriladi.
* `services/material_check.py`, `api_queue.py`: `GET /projects/{pid}/material-check` — har kroy operatsiyasi (CS/CL/CN) uchun
  **kerak** (kroydan keyin — kartalardagi butun listlar; kroygacha — ≈ taxmin), **bazada** — material katalogi `stock` (tovar
  `material_id`, bo'lmasa kod / nom bo'yicha), **yetmaydi**, ombordagi qoldiqlar soni; holat ok / short / unknown (katalogda yo'q).
  `GET /queue?statuses=0,1,2&limit=100` — navbat raqam tartibida, `next` — material to'liq bor birinchi loyiha, `warnings` — «№…: …
  pополните базу». Zaxira (`stock`) MES `catalog/sync` yoki «Каталог товаров» orqali yuritiladi; hech narsa avtomatik kamaytirilmaydi.
* UI: loyihalar ro'yxatida tugma «Очередь заказов и материал в базе» (`QueueDialog.tsx`: jadval, navbatdagi yashil, yetmaganlar
  qizil, «Пополните базу материалов» ro'yxati, «Открыть следующий»); loyiha ichida «Заказать» blokida «Материал» qatori
  (✓ / yetmaydi / katalogda yo'q, maslahatda tafsilot). MCP: `mx_material_check`, `mx_queue`. Test: `tests/test_x1015_queue.py`.
* Savol 2 (CS o'chirilganda XNC, klon) — foydalanuvchi: hozirgidek qolsin (A).

## 6. Tekshiruv
Backend: to'liq to'plam **1878 o'tdi, 1 o'tkazib yuborildi** (shu jumladan yangi `tests/test_x1015_audit.py` — 10 test); korpus
`compare_stock.py normal` (44 ko'p-listli kroy): economy 574.0 m² (o'zgarmadi), qat'iy `list` 603.9 m², avvalgi tizim 581.9 m², tekshiruv xatosi 0.
Frontend `tsc` toza, `vite build` qurildi; e2e avval **10/11** (`lists.spec.ts`: Ctrl+A → Del tasdig'ida 1 loyiha — 2026-10-03 dan beri ma'lum edi).
Kutubxonalar minor versiyalarga yangilandi (`npm update`: @playwright/test 1.64.1, vite 8.3.4, i18next 26.4.5, react-i18next 17.0.16,
lucide-react 1.57.0, @tanstack/react-query 5.104.2, @vitejs/plugin-react 6.1.2; React 19 / TypeScript 7 — major, alohida bosqich) —
shundan keyin e2e **11/11**; Playwright skripti bilan ham tekshirildi: Ctrl+A → 3 tanlov, Del → «Удалить выбранные элементы: 3?».
MCP: `tsc` toza, tutun testi 2/2 (MX bilan), drayver testi 1/1 (Chrome profil, kirish sahifasi).

## §9 Import va hisobot mosligi (2026-10-15, 2-sessiya)
Onlayn tizim bilan yonma-yon solishtiruv (`5000 kupe`, test papkasi) topilmalari F8, F20, F25, F35–F39 bo'yicha tuzatishlar
(`plugins/legacy_project.py`, `services/o_ops.py`, `services/project_export.py`, `services/project_schema.py`, `services/render.py`;
testlar `tests/test_x1015b_import.py` — 12 ta):
* **F8** — detal «ID» (`Part.uid`) endi fayldagi `<part id="N">` raqami (onlayn «ID» ustuni: 18, 2, 3, 4, 6, 7 …), detal bir nechta
  operatsiyada bo'lsa ham o'sha raqam; yaroqsiz id (yo'q / butun emas / ≤ 0) va bitta operatsiya ichida takrorlangan raqam — fayldagi eng
  kattasidan keyingi bo'sh raqam. Hech narsa ketma-ket uid ga tayanmaydi (`store.next_uid` = max + 1; muharrir uid ni operatsiya ichida
  noyob deb biladi — shunday qoladi). `.project` eksporti detal id sifatida `uid` ni yozadi (qolgan id lar eng katta uid dan keyin,
  loyiha bo'ylab noyob) — aylanma import raqamlarni saqlaydi.
* **F20** — `elLineMark="0"` → «Линии маркировки» 0 (avval 1 ga ko'tarilardi); kartada kromka chizig'i chizilmaydi, belgi o'lcham yozuvida.
* **F25** — O operatsiyasi egasi: mahsulot ichidagi `<operation id="N"/>` havolasi (real fayllar shunday yozadi) → «Владелец» = mahsulot,
  operatsiyalar jadvalida «Код/Изделие» mahsulot nomi; `owner` atributi avvalgidek ishlaydi. Eksport havolani mahsulot ichiga yozadi
  (sxema: `operation@good[product]`, id mavjud operatsiyaga ishora qilishi shart).
* **Hisobot** (`render.py`): jadvallar sahifa kengligida (`width:100%`, kataklar o'raladi; kalit-qiymat va karta yonidagi jadvallar o'z
  kengligida); sanalar «дд.мм.гггг»; «Требование на склад» — `№` operatsiya raqami (XNC lar sanaladi: ikkinchi mahsulot 29, 30, 31, 32),
  O — bitta qator `№ | O | mahsulot | nomi` + `N.1, N.2 …` material qatorlari (Код, Наименование, Ед.И, Кол), CS qoldiq qatorlari `N.k`;
  CS detallar jadvalida nom ostida `P1-1: <XNC kod>` (nomda «= * %» yo'q); karta sarlavhasi ikki qatorda (material / `№:3/5 S:… C:… Cp:…
  LT:… F:…`); o'lcham yozuvida kromka belgilari («1984 A», «2000 AA» — shu tomon bo'ylab kromkalar); karta yonidagi jadval «Мт» = `T`
  (tekstura) + `%` `*` `=`; legenda «[T] Текстура», «[%] Сверление», «[*] …», «[=] …», keyin «A: <kromka nomi>». Chop sozlamalari
  (`map_parts_list`, `map_part_marks`, `cs_maps`, `warehouse` …) avvalgidek ishlaydi.
* ❓ Tekshirish (shanba/yakshanba, onlayn): ikki dasturli detalda (5000 kupe, detal 16 «bok»: lits + orqa) nom ostidagi yozuv —
  bizda `P1-1` / `P2-1` (tomon-tartib); onlaynda qanday? Legenda tartibi (belgilar → kromkalar) va karta sarlavhasining ikki qatorligi
  ham PDF da qayta ko'riladi.
* Moslashtirilgan eski testlar: `test_integrations.py` (uid lar endi fayldagi 11, 12, 13), `test_export_w10_roundtrip.py`
  (id ta'riflari — faqat ildizdagi good/operation + mahsulot ichidagi part; mahsulot ichidagi `<operation id>` — havola),
  `test_o_operation.py` (talabnoma: O qatori + N.1; «Изделия» ro'yxati bitta mahsulotda `products_list_single` bilan), `test_qa_fix_calc.py` (legenda «A: …», «Линии маркировки» EL blokida),
  `test_x1015_queue.py` (navbat alohida papka bo'yicha — umumiy test bazasi kattalashganda `limit` ga sig'maydi).
  Eslatma: bitta detal ikki kroy operatsiyasida bo'lsa (korpusda 0 holat) uid ikkalasida bir xil — `mes/scan` birinchi
  topilganini qaytaradi (avvalgidek, QR da operatsiya yo'q).

## §8 Ekran mosligi (2026-10-15, 2-sessiya)
Maqsad: CS / CL / EL / O panellari va jadvallari xodimlar o'rgangan onlayn tizim bilan bir xil ko'rinishda (topilmalar F1–F7, F9,
F11–F16, F19, F21–F24, F26, F33 — `scratchpad/audit/findings_main.md`). Backend, `features/print`, `features/xnc` ga tegilmadi.
* **Parametr panellari** (`cs/CsParams.tsx`, `cl/ClParams.tsx`, `el/ElPanel.tsx`): bayroqlar yorliq ustunida, har biri alohida qator
  (`shared/ui.tsx` → `CheckRow`); «Группировка деталей по свойствам» — havola (`LinkRow`; «Объединение деталей» o'chiq bo'lsa xira,
  bosilsa «?» yordami ochiladi); «Объединение деталей» va «Сохранение чертежа карт кроя» — oddiy saqlanadigan katakchalar (kroyga
  ta'sirsiz); to'q sariq izohlar olib tashlandi — ma'nosi `phelp.*` yordam matnlarida. Narx birligi faqat «UZS» (CS, CL), «≈» yo'q
  (baho ekanligi — maslahatda). CS: «Торцовка включает толщину пропила», «Процент заполнения для кратности», «Порядок листов»,
  «Качество раскроя» → o'ng ustun oxirida «Дополнительно (MebeliX)». CL: «Остаток» guruhi («Мин. размер остатка» mm, «Длина делового
  остатка» — **metrda**, 10 = 10000 mm, loyihada mm saqlanadi), «Минимальный размер детали», bo'sh «Толщина пилы для групповых деталей»
  (o'chirilgan — 1D kroyda guruh detallar yo'q), «Сортировка» guruhi, bizning «Процент заполнения…» va «Качество…» — «Дополнительно (MebeliX)».
  CL da «Предпочтения» guruhi qoldirilmadi (onlayndagi mazmuni ko'rilmagan — savol).
* **Backend egasiga eslatma:** CS «Объединение деталей» endi haqiqiy katakcha, lekin `main._CUT_NON_CUT` da `merge_parts` yo'q — kroy
  natijasi bo'lsa o'zgartirish «natija o'chadi» tasdig'ini so'raydi. `merge_parts` ni `_CUT_NON_CUT` ga qo'shish tavsiya etiladi.
* **Jadvallar.** CS «Детали» (`cs/columns.tsx`): nomda «= * %» belgilari yo'q (belgilar faqat kartalar / hisobot uchun — `sizes.partMarks`),
  «детал номи» bo'sh joyni egallaydi (flex). CS «Листы и остатки» (`CsSheets.tsx`): standart ustunlar № | Длина | Ширина | Сони | Квадрати |
  Ишлатилди | Колдик | ТД | ТШ | Изох; «Наименование / ОН / ОП» faqat qoldiq qatorlari bo'lganda; doim bitta tanlangan qator (ko'k fon).
  CL «Детали» (`ClParts.tsx`): № | детал номи | Д-на | Сони | ОВ | ОН | ОЛ | ОП | Код | ID | ОК (+ bizning ИК, Ост). CL «Полосы и остатки»
  (`ClSheets.tsx`): … | ТШ | Изох — «ТШ» faqat o'qish uchun: 1D optimizator torsovkani operatsiya parametridan oladi, polosaga alohida
  qiymat ishlatilmaydi (backend kengaytirilsa tahrirlanadigan qilish mumkin). EL «Детали»: «Товар» = mahsulot nomi + «(CS) material»,
  tartib detal ID bo'yicha, sarlavha «Д-на кромки» (birlik m — maslahatda).
* **CS «Раскрой»** (`MapView.tsx`, `CsCut.tsx`): detal yozuvi standart — faqat ID (katta, markazda; `store/ui.ts` `mapLabel` standarti
  `number`, Ctrl+P «Подпись детали» o'zgartiradi); o'lcham yozuvlari monospace qalin, en raqamlari o'ng chetda ustma-ust (sig'masa — burilgan
  matn), uzunlik pastki chapda. «Таблица команд»: «К» ustunida har qatorda soni (1 ham), T qatorlari oddiy rangda, havola
  «Таблица карт» ↔ «Таблица команд» (CL da ham).
* **Boshqa:** «Изделия» narx ustunlari «0.00» (`shared/ui.tsx` `money2`); loyihalar ro'yxatida «Владелец» = «Мой» o'z loyihasi uchun
  (`useMe`); (O) «Стоимость x 1шт» qatori, «Материалы» da «ИК» (Кол × mahsulot soni) va «Всего» (Стоимость × mahsulot soni).
* i18n: `frontend/scripts/i18n_x_1015b_ui.py` (yangi kalitlar; `cl.p.min_part`, `el.col.edge_m`, `pcd.name`, bir nechta `phelp*` qayta
  belgilandi — fayl `i18n_cl.py`/`i18n_cs_w2.py` dan keyin yuklanadi). Tekshiruv: `tsc` toza, `npm run build` qurildi, skrinshotlar
  (jonli :8000, «5000_kupe») — scratchpad `shots_1015b/` (13 ekran, konsol xatosiz); Playwright e2e: to'liq to'plam 10/11 — bitta
  tutun testi `xnc.svg` da HTTP 500 bilan yiqildi (shu daqiqalarda boshqa agent `services/xnc.py` / `render.py` ni tahrirlayotgan edi;
  joriy kod bilan alohida backendda 200, `smoke.spec.ts` qayta yuritilganda 5/5 o'tdi — vaqtinchalik).
* Ochiq: CL «Предпочтения» guruhi mazmuni (onlaynda ko'rilmagan); CL «ТШ» tahrirlanadigan bo'lishi uchun backend 1D optimizatorga polosa
  torsovkasi kerak; F15 shrift — monospace qalin (onlayn shriftining aynan nomi noma'lum).

## 10. XNC chizma mosligi (2026-10-15, 2-sessiya)
Topilmalar F27–F32 + yetakchining jonli tekshiruvi (tekstura belgisi, xato matni, qalinlik ko'rsatkichi) bo'yicha XNC muharriri onlayn
ko'rinishga moslashtirildi; loyiha «3120_kuxniya» (stoleshnitsa — freza o'yig'i, pb-bok — burchak frezasi + qirra teshiklari, tr pol — 4 tomon
qirra teshiklari, tk-bok — paz, tom — orqa yuzadagi paz) Playwright skrinshotlarida tekshirildi.
* **Chizma** (`services/xnc.py::xnc_drawing_svg`, konstantalar `DRAW_*`): umumiy o'lcham yozuvlari («2000», «347») standart **o'chiq**
  (`DRAW_DIMS=False`; endpoint `xnc.svg?dims=true`, UI da «Размеры» katakchasi); yuza teshigi — aylana + aylanadan chiqib turuvchi xoch,
  ekranda **kamida 4 px radius** (`DRAW_MIN_HOLE_PX`; UI chizma maydonining eni/balandligini `width`/`height` bilan yuboradi — masshtab
  shundan); yon ko'rinishlardagi chuqurlik kesimlari o'chirildi (`DRAW_HOLE_SECTIONS=False`); qirra teshigi (bl/br/bt/bb) — yuzada chetdan
  ichkariga **yupqa chuqurlik chizig'i** (oxirida D kengligida chiziqcha) + yon polosada **ko'ndalang chiziqcha** (eski katta doira-xoch va
  punktir kanal yo'q); detal **Ткт** bo'lsa yuza markazida 3 ta yupqa kulrang gorizontal chiziq (tekstura belgisi, uzunlik ≈ 1/3, burishda
  aylanadi; Ткт o'chiq — chiziq yo'q); dasturning birinchi xatosi yoki bo'sh nom — chizma markazida **qizil qalin matn** (`xnc.err_name_empty`);
  qalinlik ko'rsatkichi: lits — strelka pastga, orqa — yuqoriga (avvaldan shunday, saqlandi); orqa yuzada kromka harflari
  `BACK_FACE_MIRROR` («x», chap ↔ o'ng) bo'yicha akslanadi, dastur koordinatalari o'zgarmaydi.
* **«Программа» daraxti** (`features/xnc/cmdView.tsx`): buyruq nomi matni o'rniga **belgi** (o'zimiz chizgan 16×16 SVG: asbob, tik teshik,
  qirra teshigi 4 tomon, paz, freza boshlanishi/chiziq/yoy/markazli yoy/3 nuqta/yumaloqlash/to'rtburchak/ellips, koordinata boshi,
  izoh/parametr/o'zgaruvchi/shart/sikl/…); asosiy parametrlar **qalin kalit** bilan («**X**=391 **Y**=50 **DP**=9 **T**=Bore5»,
  «**N**=Bore5 **D**=5», «double **throughBoreDepth**=dz+3.00 ;Глубина…»); standart qiymatlar yashiriladi (AC=1, AS AC=1 da, AV=false,
  M=true va u bilan Z, C=0, IN=0, OUT=1, DIR=false, SDP=0, SXY bo'sh, A=0, MillRect R=0, import atributlari VER / P=0) — to'liq ro'yxat
  xossalar muharririda; qator oddiy shriftda, qisqarmaydi (panel gorizontal aylantiriladi), buyruq nomi — maslahatda.
* **«Параметры»**: «Наименование» (operatsiya nomi, tahrirlanadi) — «Материал» dan keyin, «Деталь» ikkinchi qator; «Зеркало» — ikkita
  belgi-tugma (gorizontal / vertikal, bosilgani faol). i18n: `scripts/i18n_x_1015b_xnc.py`.
* Tekshiruv: `pytest -k xnc` — 239 o'tdi (+8 yangi `tests/test_x1015b_xnc_drawing.py`; `test_qa_fix_calc.py`, `test_w18_xnc.py` dagi
  o'lcham yozuvi tekshiruvlari `dims=True` bilan); `tsc` toza, `npm run build` qurildi. Shu paytda boshqa agentlar o'zgartirayotgan
  hisobot (`render.py`) testlari (`test_marker_lines_zero_and_counts`, `test_grouping_blocks_packets_and_limits` — «-3:», «PK:» matnlari)
  yiqilib turibdi — XNC ga aloqasi yo'q.
* Tekshirilmadi: onlayn tizimning o'zi bu sessiyada ochilmadi (yetakchi kuzatuvi asos); paz C=0 va Y=0 (chet bo'ylab «LED PAZ») onlaynda
  qanday chizilishi, orqa yuzada chizmaning o'zi akslanadimi (bizda faqat kromka harflari) — savol.

## §11 Chop sozlamalari oynalari (2026-10-15, 2-sessiya)
Topilmalar F40, F41, F46–F53 («Печать отчета» oynalari) bo'yicha; boshqa agentning hisobot HTML tahrirlariga (F35–F39) tegilmadi.
* **Oynalar** — hammasi «Параметр | Значение» jadvali (`features/print/PrintGrid.tsx`: `PropGrid`, `ColumnsGrid`; sxemalar — `printDialogs.tsx`;
  `print.css`): guruh sarlavha qatorlari yig'iladi, qiymat katagida joyida Да/Нет, ro'yxat, son, matn; pastda o'ngda «Ок | Отмена».
  Chap panel (`Print.tsx`): «Профиль» + ✚ ✎ ✕ → «Поля страницы», «Настройки печати», «Изделия» → «Настройки печати операций»:
  (CS) (CL) (CN) (EL) (SP) (XNC) + bizning (GR), (O), «Этикетки»; «Язык отчёта» — pastda (bizning qo'shimcha). Sarlavhalar o'rgangan
  tizimdagidek: (XNC) → «Обработка» [Статистика | Чертеж]; (CS) [Общие | Детали | Карты кроя | Заголовок карт кроя]; (CL) [Общие | Детали].
  Bizning qo'shimchalar guruh oxirida yoki «Дополнительно (MebeliX)» guruhida («Таблица команд у карт», «Припуск пунктиром», «Печать чертежей»).
* **Ustunlar jadvallari** («Заголовок карт кроя», XNC «Статистика»): «№ | Вкл | Имя | Описание | Ш-на», «Восстановить значения по умолчанию»,
  ↑ ↓ + ×. Model: `PrintCol`, `map_header_cols` (13: №, S, C, Cp, LT, F yoqilgan; R, CT, T, AP, AM, AW va bizning PK o'chiq) ↔ eski
  `map_header_fields` (validator: eski mijoz faqat ro'yxatni o'zgartirsa — ro'yxat ustun, kengliklar saqlanadi), `xnc_stat_cols` (18 ustun;
  Вкл/Ш-на F50 bo'yicha, F50 da ko'rinmaganlari taxmin: Ст-ть фр-ния, Цена п-ния, Ст-ть п-ния, Доп. ст-ть — o'chiq; Длина п-ния, Ст-ть оп-и — yoqilgan).
  Ш-na hozircha faqat XNC statistika jadvalida ustun kengligi sifatida ishlaydi (karta sarlavhasi matn).
* **Yangi `PrintSettings` maydonlari va hisobot** (`render.py` — yordamchilar fayl oxirida, ulash nuqtalari kichik; `cl_render.py`):
  `materials_group_by_code` (bir xil kodli qatorlar yig'iladi), `products_list_single`, `operations_list` / `operations_list_single`
  (ro'yxatlar; bitta mahsulot/operatsiya bo'lsa faqat «…если одно» Да da), `prod_header/operations/materials/parts` («Изделия» oynasi —
  ro'yxat ostida har mahsulot bloki), `xnc_stats_group` (material / mahsulot / yo'q) + ustunlar, `page_mirror_margins` (`@page :left`),
  `page_footer_pos` (`@page @bottom|top-center` — chop/PDF da «Проект ID… — стр. N», Chrome 131+; nom CSS satrida qochiriladi),
  `cs_warehouse` / `cs_stats` / `cl_warehouse` / `cl_stats` (operatsiya ichida talabnoma va statistika), `cs_edge_symbols` (kromka katagida
  EL belgisi + legenda), `cs_parts_form` (merged / sides — ОВ ОН ОЛ ОП ustunlari), `map_mirror_h` (Нет / Да / «Начальное направление резов:
  По вертикали | По горизонтали» — daraxt ildizi o'qi bo'yicha) + `map_mirror_v` (SVG vertikal aks, matnlar o'qiladigan), `map_part_label="none"`
  (raqam va nom ikkalasi o'chiq), `map_part_expr` (`services/expr.py`; o'zgaruvchilar: name, code, uid, length, width, qty, total_qty, grain,
  material, thickness, product_name, product_code, rotated), `map_edge_marker` (chiziq / belgi / ikkalasi), `map_edge_line_style`
  (yaxlit / shtrix / nuqta), `map_machining` (XNC yuza teshiklari va pazlar karta detalida, burilish bilan), `xnc_back_mirror` (orqa tomon
  dasturi chizmasi: gorizontal / vertikal / yo'q — faqat chop nusxasida `mirror_x/y`), `xnc_origin_as_op` / `xnc_origin` (saqlanadi; chizmada
  hali qo'llanmaydi — `xnc.py` chizmasi boshqa agentda).
* **Standartlar** o'rgangan tizim bo'yicha: `cs_title`, `cs_unplaced`, `cs_remnants` → Нет; `map_dim_bold` → Да (testlar yangilandi:
  `test_cs_w2_print`, `test_qa_fix_calc`, `test_api`). Ataylab saqlanganlar: (CL) 8 belgi (F51 da hammasi Нет — bizda Да, aks holda CL
  bo'limi bo'sh chiqadi); shrift «3 / 6» — bizda 0 = avto (pt), o'sha tizimning birligi noma'lum.
* **Savollar:** (1) «Зеркало → Горизонтально» standarti o'sha tizimda «Начальное направление резов: По вертикали» — bizda «Нет»
  (aks holda kartalar ekrandan farq qiladi); (2) «Форма печати деталей» ikkinchi variantining nomi; (3) «Печать маркера кромок» ro'yxati;
  (4) «Начало координат» 9 pozitsiyasi chizmaga qanday ta'sir qiladi; (5) CL standartlari.
* **Tekshiruv:** `tests/test_x1015b_print.py` (12), chop bilan bog'liq to'plam 281, to'liq backend to'plami — 940 o'tdi, 1 o'tkazib yuborildi, 1 xato (`test_o_operation.py:290` — talabnomada O qatorlarini guruhlash, F37, boshqa agentning joriy ishi; chop sozlamalariga bog'liq emas — uning yangilangan testi bilan qayta yurgizilganda o'tdi); `tsc` toza, `vite build`;
  Playwright skrinshotlar (13 oyna, jonli ilova, 5000_kupe) — xatosiz.

## §12 LT (kesish uzunligi) qoidasi (2026-10-15)
Muammo: bir xil loyihada, bir xil list soni va F bilan LT farq qilardi (5000 kupe CS1: onlayn 113.3 m, bizda 103.57 m; boshqa loyiha
270.5 / 251.5 m). Onlayn «Таблица команд» (5 karta, LT 26.85 / 22.79 / 24.1 / 20.42 / 19.13 m) dan kesish geometriyasi mustaqil
qayta qurildi va 10 gipoteza sinaldi (skript — scratchpad `audit/lt_analysis.py`; qoida testi — `backend/tests/test_x1015b_lt.py`).
* **Qoida (beshala karta ±0.005 m aniq):** jadvalning **har qatori** (T, C, P; «К» marta) — bitta arra yurishi, uzunligi —
  **kesilayotgan bo'lakning ko'ndalang o'lchami**: 1-daraja (T1, C1) — list tomoni to'liq (list burilgan «R» bo'lsa 2750, aks holda
  1830); 2-daraja (T2, C2, P2) — polosa eni (C1 ning Р qiymati); 3-daraja (C3, P3) — bo'lak o'lchami (C2 ning Р) va h.k. (daraja
  o'qi almashib boradi). Propil qo'shilmaydi; T1 va har polosaning T2 si sanaladi; K marta sanaladi; har stackda **oxirgi kesim ham
  sanaladi** (P qatori — detalni ajratadigan haqiqiy kesim, uzunligi detalning boshqa tomoni). Natija: 26.855 / 22.793 / 24.102 /
  20.419 / 19.130 = 113.299 m (onlayn 26.85 — oddiy yaxlitlash). Rad etilganlar: torsovkasiz (90.8), faqat T1 / T2, T uzun tomon
  bo'ylab (132.0), T2 kartada bir marta, ≥ 3-darajada oxirgi kesim sanalmaydi (96.8), K bir marta, propil qo'shiladi (113.6).
* Onlayn geometriya fakti: polosa eni = 3-daraja stack yig'indisi + propil + **2 mm** («Минимальный отступ в конце» har stack oxirida,
  masalan 1711 = 600+3+600+3+500+5, 487 = 101+3+378+5) — shuning uchun u yerda har detaldan keyin kesim bor.
* **Bizdagi farq (formula):** `optimizer._build_map` chuqur (≥ 3-daraja) tugunda chegaraga tegib turgan **oxirgi bo'lakni sanamas edi**
  (jismoniy kesim yo'q deb). Bizning 5 kartada faqat 5-kartada: 1948×1451 bo'lak ichidagi oxirgi C3 500 (1.948 m) — LT 15.67 → 17.618 m;
  1–4-kartalar bir xil. Qolgan farq (bizda 105.51 m vs onlayn 113.3 m) — **joylashuvning o'zi** (onlayn ko'proq 3–4-daraja bo'lak va
  har stackda qo'shimcha «отступ» kesimi ishlatadi; bizning joylashuv kam kesimli). Formula endi bir xil: LT = jadval qatorlari yig'indisi.
* **Tuzatish:** `_build_map` — har P/C qatori sanaladi; o'rtadagi chiqindi (W dan keyin yana bo'lak kelsa) ham kesim (onlayn «W — рез
  отхода»); CT (`cuts_count`) ham shu qoidada. `_tree_cut_len` (nomzod listlarni saralash) ataylab eskicha — optimizator maqsadi
  o'zgarmadi. UI «LT» (status qatori, «Таблица карт», hisobot, narx, OEE) shu maydonlardan oladi — alohida o'zgarish yo'q.
  Testlar: `test_x1015b_lt.py` — 5 onlayn karta (LT va jadval qatorma-qator), bizning 5-karta (17.618), o'rta W, optimizator chiqishida
  LT = jadval funksiyasi; `test_optimizer.py::test_cut_length_single_part_like_giblab` (3.76 m) o'zgarmadi.

## §13 2-sessiya yakuni (2026-10-15 kech): katta loyihalar bilan ekranma-ekran solishtiruv
Usul: «5000 kupe» (4 CS, 2 EL, CL, 2 O, 46 XNC; onlayn «test uchun» sandbox + lokal fayl) va «3120 kuxniya» (141 XNC: frezalash,
paz, orqa/qirra teshiklari) ikkala tizimda ochildi; Chrome kengaytmasi orqali 25+ ekran va oyna yonma-yon skrinshot va JS dump
bilan solishtirildi (CS/CL/EL/O/XNC parametrlari, jadvallar, listlar, kroy kartasi, «Таблица команд», XNC chizma/daraxt/stoimost,
«Изделия», «Общие действия», hisobot PDF sahifalari, 9 ta chop sozlamalari oynasi, «Редактирование раскроя», «Постпроцессоры»,
«Настройки»). 59 ta farq (`scratchpad/audit/findings_main.md`, F1–F59) → 5 tuzatuvchi agent (§8–§12), hammasi bajarildi.
Nega avval o'tkazib yuborilgan: oldingi solishtiruv yozuvlar ro'yxati (inventar, 99.2 %) va yakuniy raqamlar (listlar, F %) darajasida
edi — maydonlar joylashuvi, ustunlar tartibi, ID semantikasi, chizma uslubi, hisobot tuzilmasi, LT formulasi alohida tekshirilmagan;
katta loyiha onlayn tabni muzlatgani uchun kichik loyihada ko'rilgan edi.
Asosiy natijalar: import detal ID = fayldagi id (onlayn bilan bir xil), O egasi mahsulot, EL «Линии маркировки» 0; CS/CL/EL
panellari checkbox-qatorlar bilan, qo'shimchalar «Дополнительно (MebeliX)» guruhida; jadvallar to'liq kenglikda, ustunlar onlayn
tartibida; karta: faqat ID, monospace o'lchamlar, «К» ustuni; LT qoidasi (har T/C/P qatori × K — ko'ndalang o'lcham) — 5 onlayn karta
±0.005 m; XNC: ikonkali daraxt, qalin kalitlar, tekstura chiziqlari, mayda teshiklar, qirra teshiklari, xato matni chizmada, qalinlik
strelkasi; hisobot: 100 % kenglik, dd.mm.yyyy, talabnoma raqamlari = operatsiya raqami, O guruhlangan, «P1-1: kod», karta sarlavhasi
2 qator, «Мт» ustuni, legenda; chop sozlamalari — property-grid oynalar onlayn qatorlari/standartlari bilan.
Ochiq: (1) onlayn «Минимальный отступ в конце» har stek oxirida (2 mm + propil) qo'llanadi — bizning optimizator faqat list
oxirida; LT va kartalar shu sababli hali farq qiladi (listlar soni teng); (2) «P1-1» formati taxmin; (3) CL «Предпочтения» guruhi
mazmuni ko'rilmadi; (4) onlayn «test» sandbox loyihasida import sinovi tufayli 256 ortiqcha operatsiya qoldi (o'chirish tasdiqi
tizim oynasi — qo'lda yoki MCP drayveri bilan tozalash kerak); (5) internet tadqiqoti (`scratchpad/audit/internet_giblab.md`,
93 bandli ro'yxat) va hujjat bo'shliqlari (`docs_gaps.md`) — keyingi to'lqin uchun.
Tekshiruv: backend to'liq to'plam (quyida), frontend `tsc` toza, `vite build`, e2e 11/11; jonli ilova qayta ishga tushirildi.

### §10a XNC chizmasi — ikkinchi o'tish (2026-10-15 kech, foydalanuvchi skrinshotlari bo'yicha)
Foydalanuvchi onlayn «Шаблон» ekranini yonma-yon ko'rsatdi: bizniki kichik va chiziqlar qalin («qo'pol») edi. Tuzatildi
(`services/xnc.py`): barcha konturlar ekranda 1 px (`lw = pxmm(1)`), yon ko'rinishlar haqiqiy qalinlikda (16 mm → ≈8 px), oraliq
5 px, hoshiya kichik (chizma maydonning ≈ 90 % ini egallaydi), yuza teshigining yon polosalardagi oq proyeksiyasi qaytarildi
(`DRAW_HOLE_SECTIONS`), teshik aylanasi to'ldirishsiz, mayda teshik — 2 px nuqta + xoch, tekstura chiziqlari to'q jigarrang 1 px,
koordinata va qalinlik belgilari yupqa. Frontend: palitra — xizmat buyruqlari matn, geometriya buyruqlari ikonkalar; chizma
maydoni chegarasiz; daraxt qatorlarida checkbox faqat kursor ustida / o'chirilgan qatorda; tanlangan qator ko'k.
Onlaynda buyruq xossalari ikki marta bosishda alohida oynada («Свойства: Сверление фронтальное»: X (по длине), Y (по ширине),
DP (глубина), «Массив»: Количество / Шаг / По вертикали, T (инструмент) = dasturdagi asboblar ro'yxati «N=Bore3 D=3», Коментарий,
Ок/Отмена) — bizda ham shunday oyna (Enter / F2 / ikki marta bosish; «Отмена» ochilgandagi holatga qaytaradi; `xnc.pl.*` qisqa
yorliqlar). Hali farq: onlaynda ifoda ostida hisoblangan qiymat ko'rinadi; «Шаг» maydoni bo'lmasa ham ko'rsatiladi.
