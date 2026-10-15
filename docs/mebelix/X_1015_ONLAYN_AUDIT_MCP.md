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
