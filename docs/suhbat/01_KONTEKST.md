# MebeliX Kroy — loyiha konteksti (Claude Code har sessiyada o'qiydi)

> Bu fayl `CLAUDE.md` orqali avtomatik yuklanadi. Katta bosqichdan keyin «Holat» va «Keyingi ishlar» bo'limlarini
> yangilang. To'liq suhbat tarixi — `docs/suhbat/02_SUHBAT_TARIXI.md`, ish tarixi — `git log`.

## Kim, nima, nega
- Buyurtmachi — O'zbekistondagi mebel korxonasi egasi (claude.ai loyihasi «jasur giblab»). Muloqot **o'zbekcha (lotin)**,
  norasmiy; javoblar qisqa va aniq bo'lsin, savol bo'lsa — so'rang (taxmin qilmang).
- Maqsad: korxonaning **o'z** listli kroy (raskroy) dasturi **«MebeliX Kroy»** — xodimlarga tanish ish oqimi
  (hozir ular GibLab ishlatadi), MES/ERP bilan REST orqali ulanadi, **aniqligi GibLab'dan yaxshi bo'lishi shart**.
- Xodimlar detallarni Bazis-Mebelshik → GibLab `.project` (XML) orqali oladi; GibLab Windows'da, USB himoya kaliti bilan.

## Qat'iy cheklovlar (foydalanuvchi so'zlari — o'zgarmaydi)
- «lekin giblabni sertifikatiga tegma yani kalitiga . u aftorning huquqi»
- «qaytaraman hech bir tizimni buzmoqchi emasman . men uzimni tizimimni qurmoqchiman»
- «hech birini aftorlik huquqiga tegma va urganib chiq» (GibLab va SketchCut PRO — faqat o'rganish)
- «yana bir narsa giblabni sertifikatiga tegma . u aftorligi himoyasida . bizga uzimizning dastur qiziq , boshqalarniki emas»
- Dastlabki prompt: «GibLab kodini, JS/CSS fayllarini, ikonkalarini, logosini, nomini, yordam matnlarini, fayl
  formatlarini nusxalama va yuklab olma. Hamma narsa noldan yoziladi.» · Backend: «Uni buzma — kengaytir.»
  · Postprotsessor: «bizning arra stanogimiz formati (formatni men beraman)».
- Amalda: HASP/Sentinel/litsenziya fayllariga tegilmaydi, ikkilik fayllar/GWT kodi dekompilyatsiya qilinmaydi, yordam
  matnlari ko'chirilmaydi (faqat funksional ma'noni tushunish uchun o'qiladi); interfeysda «GibLab» so'zi yo'q.
  GibLab/SketchCut arxivlari bu loyihaga kiritilmagan.

## Tarix (qisqa)
1. **2026-09-30** — v1 paket (`PROMPT_CLAUDE_CODE.md`, `UI_SPEC.md`, `screens/`) bo'yicha noldan: FastAPI backend,
   gilyotina optimizatori (kesish daraxti), React+TS frontend (AG Grid, ru/uz), qoldiqlar ombori, hisobot, QR
   etiketkalar, postprotsessor shablonlari, MES API, `.project` importi, sex rejimi, Docker, e2e; mustaqil tekshiruvlar
   (XSS, ombor yaxlitligi, NaN, guruhlash fuzz). Foydalanuvchi avvalgi HTML prototiplarni («GibLab_Pro.html» va h.k.)
   «xodimlarni chalkashtiradi» deb rad etgan — interfeys xodimlarga tanish joylashuvda qayta qurilgan.
2. **2026-10-01** — v2 yangilanish paketi (`docs/mebelix/`) qo'llandi: N1 biznes qoidalari, UI tafsilotlari, yorliqlar;
   205 ta real `.project` bilan solishtirish; optimizator kuchaytirildi (ustunli joylash, bin completion, SVC,
   qoldiqni yig'ish, qat'iy muddatlar); mustaqil agent ko'rib chiqdi (4 kamchilik tuzatildi).
3. **2026-10-01** — VS Code + Claude Code uchun to'liq zip (shu hujjatlar bilan).
4. **2026-10-01 (kech)** — v2.1: **jonli GibLab** (GibLabLocal) bilan ekranma-ekran solishtirish + 3 mustaqil QA agenti
   (70+ nuqson) + tuzatishlar. Hammasi `docs/mebelix/Q_QA_V2_1.md` da. Asosiylari: «Листы и остатки» ustuvorlik tartibi
   (GibLab soni bo'yicha o'sish tartibida ishlatadi) va ko'p-listli optimizator, mahsulot «Свойства», umumiy
   «Сортировка», Excel import profillari, XNC kodlarini noyob qilish, XNC/GR hisobi, ombor «arvoh» qoldig'i, server
   tekshiruvlari, MES qayta yuborish, JWT rollari, loyihalar ro'yxati klaviaturasi/ko'p tanlov.

## Holat (2026-10-01, v2.1)
- Korpus (205 loyiha, 397 kroy, avvalgi dastur saqlagan natija bilan) — `docs/mebelix/P_TAQQOSLASH.md`:
  «Стандарт» **1186 list vs 1212** (15 kroyda kam, 1 chegaraviy kroyda +1; o'lchovlar orasida 1185–1189), деловой
  qoldiq **750 vs 652 m²**, kesish −1.2 %; «Быстро» 1212 vs 1212 (≤ 2 s). Kromka metri 303/303 mos, CNC 8359–8360/8360
  mos. Tekshiruv xatosi 0. **Ko'p-listli** (qoldiq + butun list, 44 kroy; `compare_stock.py`): **574.0 vs 581.9 m²**.
- Jonli GibLab bilan «1230 Jamshid 04 shkaf»: kroy natijalari aynan bir xil (F 68.55 %, 15.95 m; 1770×1830 F 92.12 %).
- Testlar: backend **223** (SQLite; PostgreSQL yo'li sinalmagan), Playwright e2e **5**, TypeScript toza.
- «Detskiy kravat» benchmarki: 2 list, 1-list 92.83 % (max rejim 93.18 %; GibLab 93.87 %).

## Holat (2026-10-24 — kroy ustuvorligi: eng kam material, keyin qoldiq; xodim loyihasi «4421»)
* **Muammo:** ro'yxatda soni cheklangan qoldiq (2500×650) + cheksiz butun list. MX «по списку» rejimida qoldiqni albatta
  ishlatib, qoldiq + 2 butun list kesdi (11.69 m², katta деловой qoldiqlar) — detallar qoldiq + 1 listga sig'maydi, ya'ni qoldiq
  butun listni tejamaydi. To'g'risi — 2 butun list (10.07 m²).
* **Foydalanuvchi qoidasi:** ustuvorlik HAR DOIM eng kam list / material (maksimal detal sig'dirish); деловой qoldiq — undan keyin.
* **Tuzatish** (`optimizer._optimize_tree`): «по списку» rejimida ham list tartiblari variantlari sinaladi; ro'yxat tartibi
  ustun, lekin boshqa tartib (joylashmagan, material maydoni) bo'yicha QAT'IY yaxshiroq bo'lsa — o'sha olinadi. Qoldiq butun
  listni tejasa — avvalgidek birinchi ishlatiladi. Test `tests/test_cs_stock_min_material.py`.
* **2-qadam (o'sha kuni):** to'g'ri javob qoldiq + 1 list (6.66 m²; qoldiqqa 2385×449 + 1400×100 + 1400×70). Listlar to'plami qidiruvi
  (`_composition_search`) vaqt yetmay ishlamasdi — endi kafolatlangan vaqt va tarkiblarga teng ulush. Foydalanuvchi qoidasi: ro'yxatga
  qo'shilgan HAR QANDAY qoldiq (fayldan, ombordan `is_remnant`, soni kam list) bir xil mantiqda — `is_remnant` maxsus holatlari olib
  tashlandi (`_stock_orders`, `_limited_first`, ro'yxat tartibi), faqat qoldiqlardan iborat tarkiblar ham sinaladi. Korpus: 1191 list,
  ko'p listli 571.8 m² (avval 603.9), xato 0. Ochiq: 1014 / 1071 (eski tizim 89–91 % zich joylashuv topgan, MX topa olmaydi).
* **Ombordagi qoldiq taklifi (qilindi, 2026-10-24):** foydalanuvchi qoidasi — kesish DOIM butun listlardan boshlanadi, faqat ularga
  sig'magan detallar uchun qoldiq omboriga murojaat. Kroydan keyin `GET .../remnant-offer`: oxirgi butun list detallari omborda shu
  materialdan (kalit, listli, qalinlik ±0.01, boshqa loyihada band emas) bor qoldiq qo'shilsa umumiy material KAMAYADIMI (butun operatsiya tez qayta hisob, ≤ 8 s) — bo'lsa oyna (tejash m²)
  «Остаток со склада» (`features/cs/RemnantOffer.tsx`): «Кроить из остатка» → `from-remnants` + qayta kroy; qoldiq material tejamasa
  avtomatik olib tashlanadi (band bekor); «Нет, целый лист». Kartalar tartibi: butun listlar avval, qoldiqlar oxirida (`_build_result`).
  Detal belgisi «Из ост.» (`Part.from_remnant`, ustun standart yashirin — TAB tartibi o'zgarmasin): belgili detallar avval ro'yxatdagi
  qoldiq listlarga, qolgani «До кроить» qoidasi bilan (`calc._from_remnant_first`). Testlar `test_remnant_offer.py`, e2e `remnant_offer.spec.ts`.

* **Oldingi listlar zich, qoldiq faqat oxirida (2026-10-24, xodim loyihasi «4407»):** 5- va 6-listlar yarim-yarim to'lib, ikkalasida
  2.2 m² dan деловой qoldiq qolardi. Sabab: yakuniy bosqich (`_compact_tail` tanlovi) jami деловой maydonini maksimal qilardi,
  `_rebalance_tail` esa «jami деловой kamaymasin» sharti bilan oldingi listni zichlashni rad etardi. Endi baho: 1) oxirgi listda eng
  kam detal (oldingilar maksimal zich), 2) деловой (`_parts_area`). Natija: 5-list 3 × 2104×506 + 988×600, 6-listda 3 detal +
  bitta 3.18 m² qoldiq; xodim loyihasi serverda qayta kesildi. Listlar to'plami qidiruvi: eng arzon tarkibga vaqtning ⅔ qismi
  (kichik qoldiq qo'shilganda keraksiz qoldiq kesilardi). Test `test_cs_tail_dense_first.py`. Korpus: listlar 1191–1194 (alohida
  qayta ishga tushirilganda farqli kroylar teng — vaqt tebranishi), ko'p listli 573.7 m², xato 0.

## Holat (2026-10-24 kech — qoldiq qoidalari: bazaga yuborish va bazadan topish, MES bilan)
* **Foydalanuvchi qarori:** ombor ma'lumotlari MES bazasida; MX o'z vazifasini bajaradi (onlayn tizimdagidek), MX da — bazaga
  YUBORISH qoidasi, bazadan TOPIB QO'SHISH qoidasi va umumiy sozlamalar. Javoblar: foiz = qoldiq / butun list maydoni; foiz material
  TURI (LDSP, AKRIL …) va kerak bo'lsa aniq material bo'yicha; faqat foiz hal qiladi; kichik qoldiq mijozga beriladi; qoldiq list
  arradan chiqqach (MES signali, har karta) mavjud; taklif — oyna; sotish — qoldiq butunligicha, narx = qoldiq m² / list m² × list narxi;
  mijozdan olib qolish narxi pastroq — MES da. Xotira: `remnant-warehouse-rules`.
* **Qilindi:** «Настройки → Правила остатков» (`features/settings/RemnantRules.tsx`, scope `remnant_rules`, `services/remnant_rules.py`):
  ombor manbasi (MES / lokal), tur va material foizlari, ombordagi jami (soni, m², list %), avtomatik yozish, MES kutish, qidiruv
  chegarasi. Ombor manbasi qatlami `services/remnant_store.py` (MES API — `docs/mebelix/MES_QOLDIQ_V1.md`; lokal — hozirgi jadval).
  Lokal ombor: holat (mavjud / band / arrani kutmoqda / tugagan), `qty_pending`, karta bo'yicha qatorlar, MES «map done» signali bilan
  mavjudga o'tish (`warehouse.on_map_done`), kirim-chiqim jurnali `remnant_moves` + MES ga yuborish navbati (`remnant_outbox.py`,
  `remnant.move` voqeasi). CS belgisi «Использовать остатки со склада» (`CSCutParams.use_warehouse`, standart o'chiq — taklif
  oynasi faqat belgi bilan; topilmasa «omborda mos qoldiq yo'q»), taklifda foiz va mijozga narxi. Material nomlari katta-kichik harf /
  bo'shliqsiz solishtiriladi. Hisobot «Остатки» — «%» va «На склад / Клиенту». Testlar `test_remnant_rules.py`, e2e `remnant_rules.spec.ts`.
* **Ochiq:** MES tomonidagi API (MES dasturchilari, shartnoma tayyor); MES ulangach «Источник склада → База MES» va manzil.
* **XNC ishi MES ga (2026-10-25):** foydalanuvchi qarori — MES moliya har asbob ishiga alohida narx qo'yadi (parma — teshik, freza / arra —
  metr). `services/xnc_tool_stats.py` (asbob kesimida, `xnc.evaluate` dan; 2898 dasturda `program_stats` bilan farq 0), MES paketida
  `xnc_tools`, `GET /projects/{pid}/xnc-tools`. Sozlama «Настройки → MES интеграция → XNC → MES» (`settings` `xnc_mes`,
  `services/xnc_mes.py`, `features/settings/XncMes.tsx`): yoqish, nima yuboriladi, asboblarning MES kodlari, loyiha bo'yicha oldindan
  ko'rish; loyihada «XNC работа» varag'i (`XncWorkPanel.tsx`). Testlar `test_xnc_tool_stats.py`, e2e `xnc_mes.spec.ts`.
* **Qoldiqqa detal tanlash (2026-10-25):** «Остатки: расход» → qoldiq yonida «Детали на остаток» (`features/project/RemnantAssign.tsx`):
  detallar ptichka + soni bilan; «Авто» — butun list sarfini eng ko'p kamaytiradigan to'plam (operatsiyaning o'z sifat rejimida; qoldiq
  tejamasa — qoldiqni eng zich to'ldiradigan); tanlov detallar ro'yxatiga yoziladi (`Part.remnant_id`, `remnant_count`). Tanlangan
  detallar qoldiqqa sig'masa — saqlanmaydi va kroy to'xtaydi (`calc.RemnantFitError`, 400 «не помещаются в остаток №…»). Kroyda
  bog'langan detallar FAQAT o'sha qoldiq listiga, qolgani «До кроить» qoidasi bilan. Bazaga qoldiq o'lchami — kroy kartasidagi
  haqiqiy (tozalangan) o'lcham (`clean_edges`, qayta ishlatishda torsovkasiz); qoldiq faqat aynan material kodi bo'yicha.
  Testlar `test_remnant_assign.py`, e2e `remnant_assign.spec.ts`, `picker_checkbox.spec.ts` (jadval tanlash katagi tuzatildi).

## Holat (2026-10-30 — detal soni o'zgarganda kroy saqlanadi, xodim loyihasi «1275»)
* **Muammo:** xodim ortiqcha detallar (sokl) sonini 0 qilib kesadi, keyin sonini qaytaradi va «До кроить» bilan davom etmoqchi.
  Onlayn tizim kroyni saqlaydi, qaytarilgan detallar qizil («kroyga kirmagan») bo'ladi va bo'sh joyga / yangi listga qo'shiladi.
  MX esa har qanday son o'zgarishida kroyni o'chirib yuborardi.
* **Tuzatish** (`main._keep_or_invalidate`): CS da kroyga kirgan har detal o'lchami / kromkasi / teksturasi o'zgarmagan va soni
  joylanganidan kam bo'lmasa — kroy saqlanadi (son oshirish, yangi detal qo'shish, kroyga kirmagan detalni o'chirish). Mahsulot soni
  o'zgarsa — butun buyurtma o'zgaradi, kroy avvalgidek eskiradi. Test `test_cs_keep_cut_on_qty.py`.
* **Tartibsiz qoldiqlar (AKRIL Mokriy):** sabab — xodimlar loyihasida pila 6 mm (faylda va onlayn tizimda 3 mm). 6 mm da 3 × 237
  (+ 2 propil) 717 balandlikka sig'maydi, shuning uchun onlayn tartib imkonsiz. Pila 3 mm da MX tartibi onlayn bilan bir xil
  (qoldiq bo'laklari 4 vs onlayn 10).
* **Pila nega 6 bo'ldi (bazadagi tarixdan):** 10-29 da operator 1000105 da pilani 3 → 6 qilgan; «oxirgi qo'yilgan qoladi» qoidasi
  (2026-10-26) uni korxona standartiga yozgan; Bazis fayllarida pila yo'q — 1000106 «1274» va 1000107 «1275» importda 6 mm olgan.
* **«Раскроечные станки»** (foydalanuvchi qarori, onlayn tizimdagi `tool.cutting` kabi): `services/saw_machines.py`,
  `api_saw_machines.py`, «Настройки → Раскроечные станки» (`features/cs/sawMachines.tsx`). Har stanokning o'z standarti
  (`MACHINE_FIELDS`: pila, торцовка, отступ, вращения, paket, polosalar, min. обрезка). Operator loyihada o'zgartirsa — faqat
  o'sha loyihada (`_remember_cs_defaults` bu maydonlarni yozmaydi); CS «Параметры» da «Станок» tanlovi va sariq farq oynasi
  («Вернуть стандарт станка»). Yangi CS / import (faylda yo'q qiymatlar) — loginning o'z stanogi («Мой станок»), bo'lmasa asosiy.
  Standartni o'zgartirish — yozuv roli + o'sha loginning PAROLI (`auth.confirm_password`), kim / qachon yoziladi; umumiy
  `/settings/saw_machines` yozuvi yopiq (403). Korxonaga tegishli (RLS). Testlar `test_saw_machines.py`, e2e `saw_machines.spec.ts`.

## Holat (2026-10-30 — «Учет текстуры» har doim yoqiq)
* **Foydalanuvchi qoidasi:** CS «Учет текстуры» har doim ✓; operator o'chirsa — faqat o'sha ishda, keyingi ishda yana ✓ (korxona
  standartiga yozilmaydi — `CS_CUT_SKIP`). Fayl formati tavsifi ham: «csTexture … По умолчанию: true».
* **Topilgan xato:** importer `csTexture` atributi yo'q bo'lsa teksturani O'CHIQ qilardi (2026-10-23 qarori) va ba'zi yo'llarda detallar
  «Ткт» saqlanib qolardi → 7 ta xodim loyihasida teksturali detallar burilib joylangan (3191 / 3197 / 3200 DUB VATAN, 3204 / 319602
  BELI KARONA, 2108 DUB VATAN, 320302 ASTANA — jami 114 detal). Tuzatildi: atribut yo'q — yoqiq, detal «Ткт» fayldagidek;
  katalog materiali teksturani o'chirmaydi. Test `test_rules_v2.py::test_import_missing_cstexture_means_grain_on`.

## Holat (2026-10-30 kech — chetdagi tor ustun: sokl, xodim loyihasi «1275» AKRIL Mokriy)
* **Muammo:** 8 fasad 717×337 + 3 fasad 237×604 + 3 sokl 100×1150, list 2440×1220. Onlayn tizim — 1 list (F 90.65 %): 1-kesim
  o'ngda 100 mm ustunni ajratadi (3-sokl tik, list eni bo'ylab), chapda fasadlar va 2 sokl. MX — 2 list (3-sokl yangi listda),
  to'liq «Раскроить» da ham.
* **Sabab:** daraxt qidiruvi 1-darajada kompozit blokni qolgan HAMMA joy bilan quradi — chetda tor ustun qoldiradigan variant
  hech bir strategiyada yo'q edi.
* **Tuzatish** (`optimizer._best_sheet.tail_col`, faqat «hammasi shu listga sig'sin» qidiruvida va detallar maydoni listga sig'sa):
  uzun-tor detallar (ko'ndalang ≥ 75 % list eni, eni ≤ 15 %) chetdagi ustunga, qolgan torroq hudud — to'liq qidiruv, ichki chegarada
  min. obrezka tekshiriladi (`_trim_violations`). Test `test_cs_tail_column.py`. Korpus: xato 0; farq qilgan 6 kroy alohida
  ishga tushirilganda avvalgidek (yuklama tebranishi).

## Holat (2026-10-26 kech — KDT pilniy markaz va prisadka: stanokdagi real fayllar bilan)
* **Foydalanuvchi talabi:** MX dan KDT ga chiqadigan fayllar (arra va prisadka) stanokda ishlayotgan fayllar bilan MANTIQAN bir xil
  bo'lsin (nusxa emas). Manba — `post/` (10 buyurtma: arra zip, prisadka zip, `.project` lar; repoga kirmaydi).
* **Topildi:** MX ning KDT generatorlari eski (2021) shaklda edi; stanokda yangi versiya ishlaydi. Arra XML — bitta qator, alifbo
  tartibi, `print_code`, chuqur qatlam siljishi 2.5, bo'laklar tartibi, material papkasi, lotin nomlar, etiketkalar 640×480 + QR
  (= prisadka dasturi nomi). Prisadka — `KDTPanelFormat` (eski `AndersonXMLdata` emas): bitta detal — bitta fayl (orqa teshiklar 8),
  Y pastdan, kromkali kontur, `Path` freza, asbob yo'li (eng yaqin), qirra teshiklari tartibi, orqada paz bo'lsa detal ag'dariladi.
  Etiketkalar Pillow o'rnatilmagani uchun umuman chiqmasdi (o'rnatildi, `requirements.txt`). Micro QR (skanerlar o'qimaydi) →
  oddiy QR (etiketka va hisobot).
* **Natija:** prisadka 680 dan 629 bayt-ma-bayt, qolgani — faqat asbob yo'li tartibi; arra — real XML dagi kroydan tiklab
  32/32 mantiqan bir xil (foydalanuvchi aniqlashtirdi: `.project` — MX kroyi, onlayn tizimda qayta kesilib fayllar olingan;
  shuning uchun arra `.project` dagi kroy bilan emas, faylning o'z kroyi bilan tekshirildi). MX o'z kroyi bilan: 32 arra + 817
  prisadka, xato 0 (`pp_kdt_own_cut.py`). Stanoklar: KDT KS832 (arra), KDT KD-612KHS (prisadka).
  Batafsil: `docs/mebelix/postprocessors/kdt-joriy-versiya.md`. Yangi kalitlar: `kdt_panel`, eski — `kdt_presize_xml_v1`,
  `kdt_trepan`. Arra generatori: polosa bolalari karta koordinatasi tartibida (`_saw_giben.pattern`). Testlar
  `test_ppfmt_kdt_current.py`; real fayllar — `tools/bench/pp_kdt_real.py`.

## Holat (2026-10-26 — sozlamalar audit: har raqam haqiqiy ta'sir qiladi, onlayn tizim bilan)
* **Foydalanuvchi talabi:** sozlamadagi raqamlar faqat ko'rinish uchun emas — o'zgarsa kroyga / hisobga ta'sir qilsin (masalan
  торцовка 5 yoki 10 mm), onlayn tizim bilan funksional bir xil.
* **Usul:** (1) MX da har CS parametrini bittadan o'zgartirib kesish (`sweep`), (2) yordam sahifalari + kod bo'yicha audit
  (CS / EL / CL / GR / SP), (3) onlayn tizimda «test uchun» papkasida sintetik loyiha bilan jonli variantlar (торцовка 10, пила 5,
  мин. обрезка 20, qoldiq chegaralari, вращений 2, высота пакета 16 / 40 / 80) — MX bilan solishtirildi.
* **Natija:** torsovka (2 → 10: birinchi detal (5,5) → (13,13)), pila, min. obrezka, qoldiq chegaralari, вращения, polosa cheklovlari,
  min. detal — ikkala tizimda ta'sir qiladi. «Расчетный %» va «Округление листов» — faqat narx (yordamdagidek).
* **Tuzatildi:**
  - «Минимальный размер детали» dan kichik detal — kroy bajarilmaydi, onlayndagi xato («Размер детали N8 меньше ограничения …»);
    avval MX jimgina chetga qoldirardi (`main._cut_input_error`, i18n `small_part_block`).
  - Polosa eni (min / max) va maks. polosa uzunligi HAR qidiruv yo'lida (gfree, SVC, to'plam qidiruvi …) — `optimizer._strips_ok`.
  - «По длине / ширине предпочтительно»: to'ldirilishi «Процент заполнения для кратности» dan past kartada yo'nalish majburiy (yordamdagidek).
  - EL metri tayyor o'lcham bo'yicha (kiritish rejimidan qat'i nazar, GR dagidek); korpus EL 303/303 mos.
  - Paket (foydalanuvchi qarori): onlayn tizim kartalarni kratnostga tenglashtirish uchun ortiqcha list sarflaydi (sinov: 6 vs 5) —
    MX eng kam materialni saqlaydi, teng variantlar ichida paketlar soni kam bo'lganini tanlaydi (`_job_key`, `_PACK_K`).
  - «Oxirgi qo'yilgan qoladi» CS ga ham (foydalanuvchi qarori; onlayn tizimda faqat «Сохранить как по умолчанию» tugmasi bilan):
    `main._remember_cs_defaults` (qalinlik, list narxi, «Учет текстуры» — yo'q); importer faylda yo'q CS qiymatlarini `cs_defaults`
    dan oladi (`legacy_project._cs_defaults`). Xodimlar serverida standart onlayn import qiymatlariga keltirildi (вращений 4).
* Testlar: `test_cs_strip_limits_all_paths.py`, `test_cs_min_part_block.py`, `test_el_remember_defaults.py` (CS qismi).

## Holat (2026-10-25 kech — EL parametrlari eslab qolinadi)
* **Muammo (xodim loyihasi «1000084», EL «1-19 kashmir»):** xodim 30 / 100 / 40 qo'ydi, ekranda yana 20 / 0 / 0. Bazadagi tarix:
  30 / 100 / 40 saqlangan, keyin «Длина остатка по краям» ga yana 20 yozilgan va ketma-ket Ctrl+Z (13 marta) qiymatlarni import
  holatiga qaytargan. Asl sabab: Bazis faylida EL ish parametrlari yo'q, importer ularni qattiq 20 / 0 / 0 qilardi — har yangi
  loyihada xodim qayta tuzatishi kerak edi.
* **Onlayn tizim (jonli, «test uchun / test»):** qiymat Enter bilan ham, Enter siz (boshqa joy / operatsiya almashtirilganda) ham
  saqlanadi; Bazis faylini import qilganda EL ga o'z standartini qo'yadi — korxona eksportlarida (`online_2026-10-19`, 8 fayl)
  doim `elRestSide=30`, `elMinSize=100`, `elMinDimDetail=40`, `elWidthPreJoint=1`.
* **MX (foydalanuvchi qarori: «qo'yilgan sozlama qolishi kerak, foydalanuvchi o'zgartirmaguncha»):** EL da ish parametri
  (`overhang`, `min_glue_length`, `min_perp_side`, `jointing_width`, `waste_percent`, `marker_lines`, yaxlitlash, `count_material`)
  o'zgarsa — korxona standarti `el_defaults` ga avtomatik yoziladi (`main._remember_el_defaults`); importer faylda yo'q qiymatlarni
  shu standartdan oladi (`legacy_project._el_defaults`), qo'lda qo'shilgan EL ham. Materialga xos maydonlar (eni, qalinligi,
  narxi, belgi, rang) eslab qolinmaydi. Xodimlar serverida standart 30 / 100 / 40, prifugovka 1 qilindi.
  Testlar `test_el_remember_defaults.py`, e2e `el_params_remember.spec.ts`; testlar orasida standart tiklanadi (`conftest`).

## Holat (2026-10-24 — postprotsessorlar onlayn tizim bilan BIR XIL kroyda)
* Foydalanuvchi talabi: tanlangan stanokka ketadigan fayl aynan o'sha stanok o'qiydigan bo'lsin; onlayn bilan bir xil bo'lguncha
  tekshirish, xatolarni ko'rsatish. Usul: onlayn sinov loyihasi (`test uchun / Без имени`) kesilib, har stanok fayli va
  `.project` yuklab olindi; MX onlayn kroyni `data` blokidan tiklaydi (`tools/bench/pp_online_cut.py`, faqat solishtiruv uchun —
  importer o'zgarmagan) → generator → bayt-ma-bayt (`tools/bench/pp_online_same_cut.py`, `pp_online_cn.py`).
* Natija va xatolar ro'yxati: `docs/mebelix/postprocessors/SOLISHTIRUV_2026-10-24.md`. Tuzatildi: Scheer bloklar soni, F4Classic
  detal raqami, PC6 kromka bayroqlari va lotin yozuvi, AES / Shelling lotin, PC6/PC7/G57/KDT XML list va material raqamlari
  (`StockSheet.uid`, `Operation.material_uid` import qilinadi), PTX mahsulot raqami, MaestroCut UTF-8 va bo'sh kromka,
  XDWoodCam UTF-8, frezalash bayrog'i (`render.part_mill_flag`: teshib o'tuvchi kesim bo'lsa false — korxona PC7 bilan).
* Qoida: onlayn (2021) va korxonaning o'z stanok namunalari farq qilsa — korxona namunasi ustun (OSI tartibi, PTX 30-maydon, Syntec).
* Yangi: Altendorf (ELMO) `.saw`, Lisec (XOpt) `.DAT`, (CN) nesting — NCStudio / KDT GCode / WoodWOP / TPA / BiesseWorks (guruh
  `nest`, CN kroy oynasida). Admin saqlagan kirish ro'yxatidan keyin qo'shilgan o'rnatilgan formatlar standart ochiq (`pp_access.known`).
* Testlar: `tests/test_ppfmt_online_1024.py`.

## Holat (2026-10-23 kech — EL parametrlari «qaytib qolishi»)
* **Muammo:** xodim EL «Длина остатка по краям / Мин. оклеиваемая длина / Мин. размер стороны» ni Enter bilan ketma-ket
  saqlaganda ekranda eski qiymat qaytib chiqdi. Bazada to'g'ri saqlangan edi (server logida har urinishda 3 ta PATCH 200,
  loyiha qayta ochilganda yangi qiymatlar). Sabab: tunnel orqali oldingi PATCH javobi (to'liq loyiha) keyingisidan KEYIN
  keladi va eski loyiha keshga yozilib, maydon eski qiymatga qaytadi. Kechikish simulyatsiyasida takrorlandi.
* **Umumiy tuzatish (barcha panellar uchun):** `Project.rev` — `store.save` qulf ostida bazadagi oldingi yozuvdan +1
  (mijoz/tarix qiymati e'tiborsiz; o'zgarmagan saqlashda o'sha). Frontend `applyProject` va `useProject` keshdagi
  loyihadan eskiroq `rev` li javobni qabul qilmaydi. Testlar: `tests/test_project_rev.py`, `e2e/el_params_latency.spec.ts`.

## Holat (2026-10-23 kech — деловой qoldiq tartibi va kattaligi, `uzgarishlar/` xodim loyihasi)
* **Muammo:** oxirgi listda «Сортировка полос: по убыванию» qoldiqli eng keng polosani (1405×100 ×2 + деловой 1332×653)
  list TEPASIGA qo'ydi, detallar (2375×414 ×2, 2005×330) undan keyin. Qidiruv kattaroq qoldiqni ham topmagan
  (qo'lda tuzatilgani 2375×653).
* **Umumiy qoida 1** (`optimizer._safe_reorder` → `_reorder(keep_last=…)`, `_has_remnant`): polosalarni saralashda
  qoldiq (деловой / «Остаток» o'lchamidagi) bo'lagi bor polosa **har doim detalli polosalardan keyin** turadi —
  detallar list boshidan (tepa-chap), qoldiq oxirida. Ichki darajada ham (`in_strip_sort`) shunday.
* **Umumiy qoida 2** (`_split_variants`, `_corner_S`; `_compact_sheet` ichida): to'liq bo'lmagan listda detal turlari
  ikki guruhga bo'linib sinaladi — A: list eni to'la tor ustunlar, B: qolgan joy boshida ko'ndalang tor polosa; qolgani
  bitta burchak qoldiq (≤ 6 tur, optimistik baho bo'yicha kesiladi). Natija: 2534×653 = 1.65 m² (avval 0.87; qo'lda 1.55).
* Korpus `compare.py normal`: listlar 1196 → 1193, teng kroylarda деловой 818.1 → 822.4 m², kesish ~bir xil, xato 0
  (kamaygan alohida holatlar yakka ishga tushirilganda eski natija — 12 parallel jarayondagi vaqt shovqini).
  Testlar: `tests/test_cs_remnant_strip_order.py`.
* **Uzaytirilgan qidiruv:** oxirgi listda деловой sig'adigan bo'sh joy bo'lsa-yu, asosiy siqish (0.8 s) topmasa — bir marta
  `compact_s × 3` (TOTAL_CAP ichida). `test_last_sheet_waste_is_one_business_remnant` avval tasodifiy (6 dan 2–4) edi — endi barqaror.
  `_split_variants` optimistik baho bo'yicha erta to'xtaydi (yaxshiroq bo'lishi mumkin bo'lmasa).
* Barcha 67 loyiha xotirada qayta hisoblandi (bazaga yozilmadi): 222 kroy, xato 0; «qoldiq detallardan oldin» kartalar 30 → 2.
* **«не сортировать» da ham** (`_remnants_last`, barcha ichki darajalar, blok tugunlaridan tashqari): qoldiqli bo'lak detalli
  bo'lakdan keyin. 225 kroy qayta hisob: «qoldiq oldinda» 30 → 1 — qolgan bitta kartada almashtirish ichki qirindini
  «Минимальная обрезка» dan kichik qilardi (`_safe_reorder` rad etadi — kesib bo'lmaydigan karta chiqmasin).

## Holat (2026-10-19 — `uzgarishlar/` papkasidagi 3 muammo)
* **A4 hisobot:** «Печать отчета» endi A4 sahifali PDF ko'rsatadi (`services/pdf_render.py`: WeasyPrint → shu kompyuterdagi Chrome/Edge
  headless; `GET|POST /projects/{pid}/report.pdf`), kolontitul chapda «Проект: nom», o'ngda «Страница N». PDF yasab bo'lmasa — eski HTML.
  Asboblar panelida «Экранный вид / Формат A4» almashtirgichi (localStorage `mx.print.view`). Test: `test_report_pdf_a4.py`.
* **«Настройки» (detallar ustunlari):** sarlavha «Настройки», standart tartib Наименование, Д-на, Ш-на, Кол, Ткт, ОВ…ОП, Код, ID, ОК, МК, ИК,
  Ост, Описание, Изделие, Группировка; «Ш-на» da standart kenglik raqami; yuqorida «Восстановить значения по умолчанию», pastda
  «Настройка значений по умолчанию» (`PUT /settings/part_columns/default`). Ustun nomini tahrirlash, № qatori, foydalanuvchi ustunlari — qoldi.
* **Karta o'lchamlari:** ingichka uzun detalda (2325×140) en yozuvi sig'masa — yuqori-o'ng burchakda gorizontal (`MapView.tsx`, `render.map_svg`).
* **Tillar aralashmasin** (foydalanuvchi qarori): ruscha UI — faqat ruscha, o'zbekcha — faqat o'zbekcha (`scripts/i18n_zzz_lang_pure.py`,
  qoldiq prefiksi `rem.p` Д/Q, backend `i18n.py` uz xabarlari).
* **Kroy tahriri:** Shift bosilganda tanlangan detal sharpasi kursor ortidan yuradi (bo'sh joy burchagiga yopishadi, sig'masa qizil);
  Shift + sudrash — kartadagi detalni bo'sh joyga ko'chirish (backend `relocate` amali, `editor.py`); Shift ushlab Ctrl — aylantirish.
* **Karta shrifti:** ekranda hamma kartada 13 px (`MAP_FONT_PX`), chopda 10 px; detal raqami o'lchamlar bilan bir xil o'lchamda.
* XNC (detal → «XNC Редактор»): nomsiz detalda ishlov nomi = kod; detal tanlanmasa xabar chiqadi.
* **Onlayn tizim bilan jonli solishtiruv (2026-10-19, «test uchun / 5000 kupe»):** detallar paneli «XNC Редактор» onlaynda
  alohida OYNA (dastur + chizma, o'ngda «Сверление» ro'yxati, teshik oynasi X/Y/DP/D/massiv, Ok/Отмена) → MX'da
  `features/xnc/PartXncDialog.tsx` (asboblar — `xnc_tools`; «Отмена» yaratilgan XNC ni o'chiradi / dasturni qaytaradi; e2e `part_xnc.spec.ts`).
  Karta shrifti onlayn bilan o'lchab 16 px qilindi; tik ingichka detalda uzunlik va en raqamlari ustma-ust (`dim-l-v`).
  «Настройки» oynasi deyarli bir xil (farq: onlaynda kenglik belgilarda, MX'da px). Onlayn hisobot sahifasi uzoq yuklanib qotdi.
* **Detallar ustunlari kengligi — belgilarda** (foydalanuvchi qarori, onlayndagidek: 35, 7, 10 …): `columns.tsx` `DEFAULT_CH`, `partColsFromData`
  (eski px profillar o'qilganda belgiga o'giriladi, saqlashda `unit: "ch"`). Tahrir oynasi kartasida chiqindi o'lchamlari (`wasteDims`).
* **Onlayn tizimni boshqarish (2026-10-19):** alohida Chrome nusxasi `tools/giblab/start_chrome.ps1` (port 9222, profil
  `../giblab-chrome-profile`, foydalanuvchi bir marta o'zi kiradi; qotsa `-Restart`), buyruq qatori `tools/giblab/gl.mjs`
  (status / shot / projects / open / tab / click / eval / run) + qadam skriptlari `tools/giblab/steps/` (shots, export_ids, colset, el_info).
  MCP drayveri tuzatildi: ajratilgan sarlavha/qator jadvallari, ildizga qaytish, 1-asosli operatsiya raqami, qatorni ko'rinadigan joyga
  aylantirish, «Открыть» orqali ochish, papka yuklanishini ~4 daqiqagacha kutish (xodimlar papkalari ~2 daqiqa), «Експортировать».
  MX tomoni: `tools/parity/mxshots.mjs` (bir xil ekranlar), `tools/parity/smoke_all.py` (papkadagi har loyihada hamma formatlar/hisobot).
* **Ustun kengliklari — onlayndagidek mutanosib:** kenglik (belgilar) = jadval eniga cho'zilish ulushi (`flex`), «№» — qat'iy;
  kataloglarda onlayn «Настройки» raqamlari (EL 30/9/10/9/10/7/15/20, O 20/35/8/8/8/10/8/10, CS listlar 12…/7/20, detallar 35/7/7/5/5/10…).
* **Ko'p loyiha solishtiruvi:** «Taqqoslash 2026-10-19» papkasida 10 loyiha (xodimlarning 6 tasi onlayndan eksport) — barcha CS operatsiyalarda
  listlar soni teng, F/деловой teng yoki yaxshi; joylashmagan detallar — listdan katta (teksturali) detallar, onlayn tizimda ham joylashmaydi.
* **3-bosqich (Настройки, detal oynalari):** «Свойства» — «№ в изделии» mahsulot detallari ID tartibida (onlayndagidek), bog'langan XNC
  chizmasi ko'rsatiladi, standart ochiq bo'lim — «Группировка»; «Групповые действия над выделенными деталями» sarlavhasi; «Перенести»
  ro'yxatida avval shu turdagi operatsiyalar (CS→CL ko'chirish — bizning W18 qo'shimchamiz, qoldi). Ingichka polosalar kartada bir qatorda
  (uzunlik / raqam / en). Onlayn: «Импорт из Excel» va «Импорт из других программ» darhol fayl oynasini ochadi; hisobot sahifasi 6+ daqiqa
  yuklanadi; tahrir oynasi canvas'i avtomatik bosishlarni qabul qilmaydi.
* **Foydalanuvchi qoidasi (2026-10-19):** savol tug'ilsa — onlayn tizim bilan bir xil; onlaynda o'zgartirish mumkin bo'lgan narsa MX'da ham bo'lsin.
  Shu bo'yicha: «Режимы ввода деталей» → «По размеру детали (с кромкой)», XNC asbobi Bore35 «Сквозное» o'chirildi (sozlamalar bazasida);
  EL «Детали» — onlayndagidek 60 ustun (`el/elExtraCols.ts`, 52 tasi standart yashirin), CS «Детали» — +22 ustun (ПВСт…ППСт, П/С/Ф,
  XNC1…5 kod/tomon/«по размеру детали»), CS «Листы» — DB ID, ID, «МЗап».
* **«МЗап»** (`StockSheet.min_fill_percent`): kartaning to'ldirishi (F) chegaradan past bo'lsa, shu list soni mos kartalar soniga
  tushiriladi va kroy qayta bajariladi (≤ 3 marta) — `optimizer._enforce_min_fill`, CL: `cl_optimizer.optimize_linear` (o'ram);
  cheklov yo'q bo'lsa xulq o'zgarmaydi. Test: `test_min_fill_percent.py`.
* Kroysiz «Редактирование раскроя» (CS va CL bo'sh holatida havola, bo'sh natijadan qo'lda kartalar) — e2e `edit_empty.spec.ts`.
  Chop kartasida ingichka polosalar bir qatorda (`render.map_svg` `row_mode`).
* LB (etiketka) parametrlari onlayn tartibida (Печатать → Количество → Размер → «Макет»), SP sarlavhasi «Параметры материала».
  «3154 Ishxona» solishtiruvi: faylda mahsulot soni 100, onlayn tizim natijasi esa 1 dona uchun eskirgan — MX 1 dona bilan kesganda
  listlar teng (1 / 1). Onlayn «Печать отчета» sahifasi katta loyihalarda 6+ daqiqa yuklanadi — chop sozlamalari oynalari jonli
  solishtirilmadi (avvalgi skrinlar asosida mos).
* **Detal «XNC Редактор» oynasi to'liq (2026-10-19, foydalanuvchi shikoyati bo'yicha):** onlayn tartibidagi yuqori panel — Обратная сторона,
  Свойства, Начало координат (ЛВ/ЛН/ПВ/ПН), Поворот, butun dasturni akslantirish (X→dx-X, Y→dy-Y; chap↔o'ng, yuqori↔past teshik,
  yoy yo'nalishi), tanlanganlarni siljitib / akslantirib nusxalash (dastur oxiriga), Отменить/Вернуть, Удалить, Вверх/Вниз, Инструменты,
  Показать все, Настройки, Справка; «Чертеж» varag'i (`GET /operations/{oid}/xnc-sheet`: o'lchamli chizma + teshiklar jadvali + shtamp);
  «Сообщения» ro'yxati; «Отмена» dastur va parametrlarni tiklaydi. Modul `xnc/xncTransform.ts`, muharrir API `XncProgApi`.
  e2e `part_xnc_toolbar.spec.ts` har tugmani tekshiradi. Onlayn panel tugmalari ro'yxati MCP orqali o'qilib solishtirildi
  (`tools/giblab/steps/titles.mjs` ↔ `tools/parity/mxtitles.mjs`): qo'shildi CL «Детали» TXT olish/qo'yish va o'lchamlarni almashtirish
  (CL'da uzunlik saqlanadi — faqat tomonlar), XNC «Шаблон» fayl tugmalari «Экспортировать / Импортировать». Teshiklar jadvalida yon
  teshiklar koordinatasi (o'ng — DX, past — DY).
* **CS «Детали» klaviatura oqimi (2026-10-19, onlaynda o'lchandi `tools/giblab/steps/tab_probe.mjs`):** TAB qator bo'ylab o'ngga; oxirgi
  qatorning oxirgi katagidan keyin darhol yangi qator (0×0, davomiy raqam), fokus nomida (`act.append`); qator chegarasida «№» o'tkazib
  yuboriladi, Shift+TAB orqaga; probel Ткт / ОВ…ОП da (kromka navbati). e2e `parts_tab_flow.spec.ts`.
* **Fokus va hover (2026-10-19, onlaynda haqiqiy sichqoncha bilan o'lchandi `steps/tab_start2.mjs`: yorliq bosilgach fokus jadvalda,
  1-TAB — 1-qator «Наименование»; qator ustida hover-oyna yo'q):** varaq ochilganda / yorliq bosilganda fokus 1-qatorning «№» katagida (`Grid focusFirst`, `focusGridIn`; CS/CL/CN
  detallar va listlar, EL, O); yorliqlar TAB tartibidan chiqarilgan; detal qatori ustidagi hover-oyna olib tashlandi. e2e `grid_focus_first.spec.ts`.
* **MES MX faylini o'qimasdi (2026-10-19, sabab topildi va tuzatildi):** korxona MES'i (`MebeliX-Mes-System`, `orders/files.py`)
  CS operatsiyasida kroy kartalari (`data` bloki) bo'lmasa faylni 422 «GibLabda hali optimizatsiya qilinmagan» bilan rad etadi; MX
  eksporti bu blokni yozmasdi. Foydalanuvchi qarori: MX blokni o'zi yozadi va fayl onlayn eksport bilan bir xil bo'ladi.
  `services/project_export_cut.py` (format — MES dekoderi `csblob.py` tavsifi; yozuvlar = MX «Таблица команд» T/C/P/W), CS statistikasi
  (`cMaterialCount…cutLength`), list qatorlari `usedCount`, деловой qoldiqlar (`waste/business/sheetId`, CS ro'yxatida ham), detal
  `usedCount` + `eltMat…`, EL `elLength` + material soni, XNC `countBore/Mill/Cut`, narx atributlari 0, `version="21052101"`.
  Tekshiruv: MES'ning o'z kodi (parse_project + build_cutmap + self_check) 10 ta Bazis loyihasi + 5001 da — hammasi qabul
  (kirill nomli mahsulot fayli ikkala tizimda rad etiladi); kataklar detal o'lchamiga mos, ustma-ust yo'q. Test `test_export_cut_blob.py`.
  Onlayn tizimda import → kroy → eksport: `tools/giblab/steps/import_cut_export.mjs` (faqat «test uchun»).
* **Kroy tahriri — onlayn tizimdagidek (2026-10-21, «test uchun» da jonli tekshirildi):** detal / polosa o'chirilganda butun karta
  burchakka zichlanadi (qatorlar eng katta qolgan detalgacha qisqaradi, bo'sh qator yo'qoladi, «Расширить полосу» ham qaytadi);
  «Развернуть резы» (Ctrl+R) — tanlanmasa butun list, polosa / bo'sh joy tanlansa o'sha polosa: detallar joyida, 1-kesish o'qi
  almashadi, qayta bosilsa qaytadi (imkonsiz bo'lsa — eski qayta joylash). MX qo'shimchasi: zichlash burchagi (LT standart / RT / LB / RB)
  — «Настройки» umumiy (`app.edit_pack_corner`) va tahrir oynasida har list uchun (`CutMap.pack_corner`), yangi detal ham shu burchakka
  qo'yiladi. Shift ushlab Alt yoki Ctrl — sharpa aylanadi. Modul `services/editor_pack.py`; testlar `test_editor_pack.py`, e2e `edit_pack.spec.ts`.
  Onlayn drayver «odam tezligida» (`GIBLAB_PACE_MS`, standart 450 ms har bosish oldidan) — tez bosishda tizim qotardi.
* **«До кроить» va tahrir tugmalari onlayndagidek (2026-10-21, jonli tekshirildi):** onlaynda «До кроить» qolgan detallarni tayyor
  kartaning bo'sh joyiga qo'yadi (joylanganlar o'z joyida, kartalar soni o'zgarmaydi). MX: `services/cut_rest.fill_existing` — har
  kartaning bo'sh barglari kichik list sifatida optimizatorga, natija `editor.rebuild` bilan tekshiriladi; sig'maganlari — yangi listlar.
  Foydalanuvchi talabi: operator tanlaydi — «До кроить» oynasi (standart: bo'sh joylarga + yangi listlar; yoki faqat yangi listlar;
  `optimize?fill_free=false`); qoldiqlar omborga yozilgan bo'lsa tayyor kartalar o'zgarmaydi. «В начало / В конец» — onlayndagidek
  har bosishda bir qadam, tanlov saqlanadi. Tahrir oynasida «Таблица команд» ↔ «Таблица карт». Testlar `test_cut_rest_fill.py`,
  e2e `cut_rest.spec.ts`.
* **GibLab yordami bo'yicha audit (2026-10-21, `GibLabLocal/pages/help/*_ru.html` — faqat ma'no):** tahrir kombinatsiyalari
  yordamdagidek — `[SHIFT]+[CTRL]/[ALT]+click` bosib turish (almashtirgich emas); «Развернуть резы» detallar ANIQ joyida (daraxt
  koordinatalardan quriladi, zichlanmaydi), imkonsiz bo'lsa onlayn tizim hech narsa qilmaydi — MX operatordan so'raydi
  (`rotate_keep` → «qayta kesish», `mode: relayout`); detal o'chirish hech qachon rad etilmaydi (zichlash qoidaga to'g'ri kelmasa —
  zichlamasdan). Jadvallarda Home/End — birinchi/oxirgi qator (`Grid`), «Листы»/«Полосы»/O — Enter/Ctrl+Enter navigatsiyasi va oxirida
  yangi qator (`shared/grid/excelNav.ts`), O — Shift+Del, F1 — ochiq operatsiya mavzusi, LB foydalanuvchi maydonlari Ctrl+↑/↓,
  CL tahriri — Ctrl+click ko'p tanlash, Shift+A+click ko'p nusxa (`place` `fill`), «Ширина»/«Ткт» ustunlari. XNC: kalta detalda teskari
  kesim 2×D. Stress-test (25 loyiha × 40 tasodifiy amal, 3 xil urug', «До кроить» bilan) — xato 0 (scratchpad `ed/stress.py`).
  2-qism: LB shablon — «Кривая безье» (`bezier`: boshi, 2 boshqaruv nuqtasi, oxiri; SVG `C`, ZPL — siniq chiziq, tugunlarini
  sudrash), dizaynerda F4 (xizmat buyruqlari) / F9 («Состояние» paneli); «Справка» — yangi mavzular: kroy tahriri (barcha tugma va
  kombinatsiyalar), CL, O, LB, qoldiqlar ombori; F1 — ochiq operatsiya mavzusi (CS/CL/EL/GR/O/LB). 1C qoldiq almashinuvi — MES orqali
  (foydalanuvchi qarori 2026-10-21, MX da qilinmaydi). Ochiq:
  PP Panhans/Excitech/KDT nesting/Bavelloni/NC Studio (namuna fayl kerak); CS «Листы» «Наименование» ustuni onlayndagidek qoldirildi.
* **Foydalanuvchi videosi (lokal GibLab, «1268 Akmal», 2026-10-21; nutq faster-whisper bilan matnga o'girildi):** fasadlarni bitta
  listga qo'lda terib, qolganini «До кроить» bilan. MX'ga qo'shildi: Shift bilan qo'yishda kesim yo'nalishini KURSOR tanlaydi (detal
  o'ng tomonida — gorizontal, pastida — vertikal (foydalanuvchi qarori: teskari tanlov); sharpada yashil kesim chiziqlari; `place` `{x, y}`, `editor.split_for`); bo'sh joyni
  bosish — uning polosasi tanlanadi; bo'sh joyga o'ng tugma — butun qator qaytarib olinadi; «Сузить полосы» (`narrow`) va Ctrl+Q
  (toraytirish, bo'lmasa kengaytirish); Ctrl bilan tanlangan detallar + «Развернуть резы» — ularning umumiy polosasi; tahrir
  kartasida g'ildirak zoom (o'rta tugma — surish); «До кроить» oynasi olib tashlandi (foydalanuvchi: «keragi yo'q» — darhol bo'sh
  joylarga, keyin yangi list), bo'sh joyni to'ldirishda ikkala kesish yo'nalishi sinaladi.
  «До кроить» bo'sh joyni to'ldirish `intensive` qidiruv bilan (ota o'qi bo'ylab — bir daraja chuqurroq): videodagi stsenariy MX'da
  takrorlanganda 1-list F 91.73 % (onlayn ham 91.73 %), 2-listga aynan o'sha 4 detal. Onlayn F деловой qoldiqni maxrajdan chiqarmaydi
  (2-list 54.84 %), MX chiqaradi (75.5 %) — joylashuv bir xil.
* **XNC teshiklar chizmasi onlayndagidek (2026-10-21, foydalanuvchi skrini «1268 / 01_004 bok»):** yon (qirra) teshik yuzada — sverlo
  diametri enida, DP uzunlikda to'rtburchak kanal + uzuq o'q; yon polosada — D enida to'rtburchak + uzuq o'q; yuza teshigi kesimlari
  polosalarda — ichi bo'yalmagan to'rtburchak + uzuq o'q (`xnc._sec_rect`). «X» yozuvi strelka ustida. Shift bilan qo'yishda kesim
  yo'nalishi teskari qilindi (kursor o'ngda — gorizontal). «До кроить» — har karta uchun 4 boshlanish varianti, eng ko'p maydon
  (`cut_rest.FIRST_VARIANTS`). Onlayn «1244 Prihojka» XNC paneli bilan yonma-yon: tuzilish bir xil; farq — belgilar (ikonkalar) uslubi.
* **Bosib turilgan TAB (2026-10-21, foydalanuvchi shikoyati):** jadvalda TAB bosib turilsa klaviatura takrori (`repeat`) kursorni
  qo'yib yuborilguncha surardi, jadval oxirida esa har takror yangi qator qo'shardi (1, 2, 3 … qator). Endi takror e'tiborsiz
  (`hotkeys.swallowTabRepeat` — barcha jadvallar: `suppressGridKey`, `excelNavKey`, CS/CL/CN detallari), CS `append` bir vaqtda
  bitta. e2e `parts_tab_append_once.spec.ts`. Yangilanish (foydalanuvchi): TAB 1 soniyadan ko'p bosib turilsa — takrorlar bilan keyingi
  kataklarga o'tib boradi (`TAB_HOLD_MS`), jadval oxirida takror qator qo'shmaydi.
* **Qator belgilash onlayndagidek (2026-10-21, «test uchun» da jonli o'lchandi, `tools/giblab/steps/sel_probe3.mjs`):** bosish — bitta,
  Shift+bosish — oraliq, Ctrl+bosish — qo'shish / olib tashlash, Shift+Ctrl+bosish — oraliq mavjudiga qo'shiladi, Shift+↑/↓ — oraliqni
  kengaytirish / qisqartirish (tayanch — oxirgi oddiy / Ctrl bosilgan qator), oddiy ↑/↓ — faqat yangi qator, Del — belgilanganlar
  o'chiriladi. Shift+strelka va ↑/↓ — umumiy `Grid` (barcha ko'p tanlovli jadvallar). e2e `parts_row_select.spec.ts`.
  Foydalanuvchi talabi (2026-10-21): klaviatura bilan kelingan qator (TAB / Enter / strelka / yangi qator / o'chirishdan keyin) belgilanadi —
  butun qator ko'k, kursor katagi oq + qora ramka (`grid.css`); TAB 1 s dan keyin har 2-takrorda bir katak (`TAB_HOLD_EVERY`);
  detal o'chirilsa kursor oldingi (o'rniga kelgan) qatorga, o'sha ustunga. Jonli: onlayn «Операции» — bitta qatorli tanlov (MX ham).
  Oyna kichrayganda onlayn tizimda shrift / qator balandligi o'zgarmaydi (14.67 px / 21 px), ustunlar mutanosib torayadi;
  MX: kroy kartasi yozuvlari karta bilan birga kichrayadi (`MapView` `MAP_REF_SCALE` 0.3 px/mm dan kichikda, min 5 px).
  Detallar jadvalida qator balandligi o'zgarmaydi, uzun nom / kromka nomi qirqiladi (foydalanuvchi tasdiqladi: onlayndagidek;
  `columns.tsx` `clip`, avvalgi `wrapText`/`autoHeight` olib tashlandi).
  Tuzatishlar (foydalanuvchi, 2026-10-21 kech): bosib turilgan TAB jadval oxirida to'xtab qolardi (oldingi tuzatish takrorda qator
  qo'shishni butunlay o'chirgan edi) — endi bittadan qator qo'shib davom etadi (`appending` himoyasi kursor yangi qatorga o'tguncha);
  tezlik — dastlabkining 75 % (`TAB_HOLD_SPEED`); «№» ustunida sichqoncha bilan sudrab oraliq belgilash (Ctrl — oldingisi saqlanadi);
  Shift+strelka fokus hodisasi ikki marta kelganda tanlov buzilmaydi. Oyna kichraytirilsa yuqori (Операции) panel endi oyna
  balandligining ulushi (`ui.topFrac`, `mxk_top_f`) — ikkala panel nisbatni saqlab o'zgaradi (avval qat'iy 246 px edi).
  e2e `zz_tab_hold_real.spec.ts` (CDP haqiqiy takror), `window_resize_ratio.spec.ts`.
  Bosib turilgan TAB bilan qator qo'shishdagi qotish (2026-10-21): kursor yangi qatorga server javobini kutardi (lokal 13 ms,
  tunnelda 0.2–0.6 s). Onlayn tizimda o'lchandi — u qatorni darhol yaratadi, pauza yo'q (~47 ms/katak). MX: qator darhol keshga
  (id brauzerda — `newPartId`, server band id ni almashtiradi), POST fonda; detallarga tegadigan barcha so'rovlar bitta navbatda
  (`CsParts.mutate`); qo'shish javobi katak tahriri yopilgach qo'llanadi; yangi qatorda tahrir oldindan ochilmaydi (harf yozilsa
  boshlanadi). Klaviatura bilan qator belgilash endi tugmadan keyin (`Grid.keySelect`) — kechikkan fokus hodisalariga bog'liq emas.
  Server yuklamasi (ish bazasi nusxasi, eng katta loyiha 2 MB / 432 XNC): har saqlashda barcha XNC dasturlari qayta hisoblanardi —
  `xnc_stats` keshi (recalc 79 → 24 ms, tahrir 138 → 106 ms). Bir jarayon + SQLite: 10–20 kishi bir vaqtda katta loyihalarni
  tahrirlasa p95 2–4 s — ko'p foydalanuvchi uchun PostgreSQL + bir nechta jarayon (loyiha qulfi bazada) kerak (taklif, hali qilinmagan).
  Sichqoncha bilan tez bosishda ko'k qator kursordan orqada qolardi (2026-10-21, o'lchandi: CPU ×4, haqiqiy loyiha): jadval
  kutubxonasi kursorni `mousedown` da, qator tanlovini esa `click` da (tugma qo'yib yuborilganda, +60–90 ms) qilardi. Endi tanlov
  `Grid.selectOnDown` — tugma bosilgan zahoti (oddiy / Ctrl / Shift / Shift+Ctrl), kutubxonaning `enableClickSelection` o'chirilgan;
  hamma jadvallar (bitta `Grid`). e2e `zz_click_lag.spec.ts` (ko'k < 30 ms).
  Sekin server (500 ms) + sekin kompyuter (CPU ×6) bilan TAB va tez bosish — ko'k qator kursordan qolmaydi (`zz_tab_sel_sync.spec.ts`).
* **«Листы и остатки» va EL onlayn bilan (2026-10-21, «test uchun» 1244 Prihojka):** EL «Детали» — ustunlar, qiymatlar, 9 tugma (nom va
  kombinatsiya) bir xil; farqlar tuzatildi: saralash faqat Длина / Окл. дл. / Ширина / Окл. шр. / Д-на кромки, qatorlar kulrang (faqat o'qish,
  `.oparts-grid`). «Листы» — 8 tugma bir xil (MX + «Добавить остатки со склада», «∞»); onlayn «Настройки»: МОН / МОП / МЗап / DB ID / ID
  o'chiq → MX «ОН/ОП» nomi «МОН/МОП», sukut bo'yicha yashirin. Qolgan farq: MX kroydan chiqqan деловой qoldiqni ro'yxatda alohida qator
  qilib ko'rsatadi («Наименование» ustuni shu uchun ko'rinadigan) — onlaynda yo'q. Ustun nomini o'zgartirish MX da ham bor
  (barcha `ColumnSettings` — «Имя» katagi; avvalgi «yo'q» xulosasi xato edi). 2026-10-22: onlayn «Листы» da qator belgilash jonli
  sinaldi (test loyihaga 5 vaqtinchalik qator qo'shib, keyin o'chirildi; kroy saqlandi) — ko'p qatorli, detallar jadvalidagi qoidalar
  bilan bir xil; MX «Листы» ham `multiRow` (umumiy `Grid`).
* **`.project` eksport fayli nomi onlayndagidek (2026-10-22, foydalanuvchi: Bazis «33095 Begzod.project» → onlayn
  «33095_Begzod.project»):** `project_export.safe_filename` — bo'shliqlar «_»; ZIP takrorlari «_(2)». Ichki tuzilish o'zgarmagan.
* **Ko'p abonentli tuzilish, 1-bosqich (2026-10-22, foydalanuvchi qarori: 5 000 → 100 000+ korxona, abonent = alohida korxona):**
  PostgreSQL (portativ, localhost) + RLS bilan korxonalar ajratilishi, bazadagi foydalanuvchilar (xesh), jarayonlararo qulflar,
  4 jarayonli server; xodimlar serveri PostgreSQL ga ko'chirildi (ma'lumot to'liq). Batafsil — `docs/mebelix/Y_MASSHTAB_ABONENTLAR.md`.
  2-bosqich (2026-10-22): kroy / nesting / PDF — navbat + alohida hisob ishchilari (`app/worker.py`, `run_server.bat` 6 ta ishga
  tushiradi, `worker.log`), loyihalar ro'yxati JSON siz + sahifalab, tarix zlib bilan (82 → 31 MB), sozlama keshi NOTIFY bilan,
  katalog kaliti (korxona, id). Server qayta ishga tushirilganda ishchilar ham to'xtatiladi (`backend/worker.pid`).
* **Nanxing SyntecCad (.scx) stanokda xato berdi (2026-10-22):** «Mill path node not on panel outline». Sabab — MX eski (2021 onlayn)
  formatni yozardi; stanok lokal tizimning yangi formatini yeydi. Generator korxona namunasi (8/8 bayt-ma-bayt, xodimlar serverida ham)
  va MES generatori qoidalari bo'yicha qayta yozildi; MES bilan 141 loyiha / 6192 faylda 6162 bir xil, qolganlari tushuntirilgan
  (MES xatolari: cho'ntak c=3 tashqariga). Umumiy topilma: `<var>` siz `throughCutDepth` MX'da frezani barcha formatlarda
  tashlab yuborardi — tuzatildi (`xnc._Run`). Batafsil: `docs/mebelix/postprocessors/nanxing-synteccad.md`.
* **Rangli belgilar, 1-bosqich (2026-10-21, foydalanuvchi qarori «o'zimiz rangli chizamiz»):** onlayn tizim belgilari nusxalanmaydi;
  MX belgilariga ma'no bo'yicha rang — `shared/iconTone.ts` (qo'shish — yashil, o'chirish — qizil, strelka / saqlash — ko'k, asboblar —
  jigarrang, papka — sariq), `IconBtn`, varaq yorliqlari, loyiha menyusi. 2-bosqich: operatsiya turlari — o'z rangli SVG
  (`shared/opIcons.tsx`: CS taxta, EL ko'k lenta, XNC parma …), XNC buyruq belgilari rangli (`xnc/cmdView.tsx`: taxta / parma /
  freza / boshqaruv), chap panel belgilari oq kvadrat ustida rangli (`.side-ico`).
* **XNC frezalash ko'rinishi (2026-10-21):** chizmada freza izi asbob diametri enida, uzuq markaz chizig'i,
  boshlanish nuqtasi (doira + xoch), skvoz kesim ajratadigan bo'lak och rangda (korreksiya tomoni; yopiq konturda — ichi).
  Testlar `test_xnc_mill_drawing.py`, e2e `xnc_mill_drawing.spec.ts`. Mantiqiy XNC parametri «1.0» ko'rinishida kelsa ham yoy
  yo'nalishi to'g'ri o'qiladi (`_is_ccw`).
  **«Подрезка на выходе» 2026-10-22 da butunlay olib tashlandi** (foydalanuvchi qarori: burg'ulash stanogida muammo chiqarishi
  mumkin; onlayn tizimdagidek — stanok dasturiga qo'shimcha kesim qo'shilmaydi). Chizma, `machine_program`, sozlama, ✂ tugmasi
  yo'q; eski loyihalardagi `exit_precut` maydoni o'qilganda e'tiborsiz qoldiriladi. Eski modul — `backups/removed_precut_2026-10-22/`.
* **Tor oyna, XNC Редактор, Чертеж (2026-10-22, foydalanuvchi skrinlari + onlayn «5000 kupe / tom» bilan jonli solishtirildi):**
  - Oyna kichrayganda butun interfeys mutanosib kichrayadi: `shared/uiZoom.ts` — `#root` ga CSS `zoom` = min(1, en/1200, bo'y/640),
    `vh`/`vw` o'rniga `--vh`/`--vw`. Sichqoncha → px joylari `uiZoom()` ga bo'linadi; AG Grid: aniq `rowHeight`/`headerHeight`,
    `popupParent=body`, oxirgi qator uchun `--ag-zoom-fix`. Sarlavha qatorlari bo'linmaydi (`header.css`). Foydalanuvchining MX
    varag'i brauzerda 125 % kattalashtirilgan edi (manzil qatorida lupa) — masshtab buni ham qoplaydi.
  - Detal «XNC Редактор» oynasi: yorliqlar va «DX=…» qatori endi cho'zilmaydi (avval oynaning yarmi bo'sh, chizma siqilgan edi);
    onlayn tartib — dastur ro'yxati tepada, chizma pastda butun enda, palitra chapda (`xnc.css` `.part-xnc-main .xnc-editor` grid);
    sarlavhada detal kiritish rejimi nomi («По размеру детали (с кромкой)»).
  - «Чертеж» varag'i onlayn varaqdagidek: `xnc_drawing_svg(sheet=True)` (oq detal, qora chiziqlar, raqamlangan teshiklar, tekstura) +
    `_sheet_dims` (umumiy uzunlik / balandlik strelkali; X ordinata — qirraga yaqinlari pastda, qolganlari tepada; Y ordinata o'ngda),
    `render.xnc_sheet_html` (ramka, teshiklar jadvali №/X/Y/T + «Ø= DP=» guruhlari, «Лицевая сторона», «Кромкооблицовка», shtamp
    «Деталь №n(id) nom»), tepada «Операция» tanlovi (detalning XNC'lari). Testlar `test_xnc_sheet.py`, e2e `ui_zoom.spec.ts`;
    barcha e2e 900×640 oynada ham o'tdi.
  - 2026-10-23 tekshiruv: onlayn tizim 900×640 oynada masshtablamaydi (menyu va jadvallar kesiladi, aylantirish chiziqlari) — MX esa
    hammasini to'liq ko'rsatadi (atayin qoldirildi, MX afzalligi). Onlayn dastur ro'yxati ham Tool / Var qatorlarini ko'rsatadi — MX bilan
    bir xil. Ustun kengligini sudrash masshtabda kursor ostida qoladi (`Grid.tsx`: pointer/mouse hodisalarida `clientX` masshtabga
    bo'linadi; ustunlarni sudrab ko'chirish o'chirilgan — `suppressMovable`), e2e `ui_zoom.spec.ts`.
* **XNC to'liq audit, 1-bosqich (2026-10-23, onlayn «test uchun / 5000 kupe» bilan tugma-tugma, CDP skrinlar):**
  - Dastur ro'yxati menyusi: «Горизонтальное / Вертикальное отзеркаливание» (onlayn: «Отзеркалить с копированием?» — Ha: nusxa
    tanlangandan keyin, Yo'q: o'zi; `dx-975` ↔ 975, chap ↔ o'ng teshik). MX ustunligi: yoy (DIR), korreksiya C 1↔2, burchak A,
    ko'p tanlov (onlaynda yoy uchun o'chiq). `askChoice` (uch tugma) — `shared/dialogs.tsx`.
  - Копировать / Вырезать / Удалить — barcha tanlangan qatorlar; «Удалить» onlayn kabi tasdiq so'raydi (`treeOps.removeMany`).
  - Palitradan qo'shilganda «Свойства» darhol ochiladi (onlayn kabi; maydonlar MX standartlari bilan); yangi buyruqda «Отмена» —
    buyruq olib tashlanadi (onlaynda bo'sh qator qolardi).
  - «Кодирование»: Настройки / Ок / Отмена; sozlama `xnc_coding` (Добавить номер операции / стороны, ifoda; standart onlayn ifoda
    `now('yyMMddHHmmss')+rspace(crc16(project.name),5,'0')+rspace(part.id,4,'0')` — crc16 natijasi onlayn bilan bir xil),
    `services/xnc_coding.py`, `POST /actions/xnc-coding[?preview=1]`; bog'lanmagan XNC kodi o'zgarmaydi; tomon raqami 1/2 (lits/orqa
    — taxmin, onlaynda tekshirilmagan).
  - Ko'zgu belgilari: lucide `FlipHorizontal2` bu versiyada gorizontal chiziq (vertikal ko'rinish) — `TrianglesCenterlineDashedVertical`
    (= gorizontal ko'zgu) ishlatiladi. «Стоимость сверления» yozuvi. (O) «Код/Изделие» — import qilingan loyihada ham egasi nomi.
  - Import (ochiq loyihaga): fayldagi detal ID lari saqlanadi (onlayn kabi; avval 1.. qayta raqamlanardi), band / takror ID — keyingi
    bo'sh raqam (`project_merge.append_project`). Jadvallar: overlay aylantirish chiziqli Chrome'da (Windows 11) oxirgi ustun
    («ОК», «Всего») chiziq ostida qolardi — `Grid.tsx SCROLLBAR_W` (o'lchanadi, 0 bo'lsa 16). (CL) «Стоимость материала (м)»,
    «Цена операции (метр/рез)». CS / EL / CL / O / Изделия / Общие действия — tugma-tugma onlayn bilan mos (skrinlar bilan).
  - «Печать отчета»: onlayn kabi — kodi bo'sh XNC bo'lsa «Обнаружена XNC операция с пустым кодом!» + «Кодирование» oynasi
    (bir xil kodlar ham shu oynaga). Hisobot uzunliklari ≤ 3 xona, ortiqcha nolsiz (`render.fmt3`: 113.299, 50).
  - Kroy taqqoslash («5000 kupe»): LMDF — MX 105.51 m / onlayn 113.30 m (5 list ikkalasida); XDF — MX normal F 86.96 % LT 24.62,
    onlayn F 81.69 % LT 22.23 (MX oxirgi listni yaxshiroq to'ldiradi — katta qoldiq; fast rejimi 81.69 % / 22.14 m).
  - XNC «Ограничения» onlayn oynadagidek: «Режим» Выключить / Не строго / Строго; yangi guruh «Минимальное расстояние между центром
    горизонтального отверстия и краем детали» (`hole_end_*`; ❓ ma'no — tomon uchlarigacha); «Строго» — buzilgan XNC stanok fayliga
    chiqmaydi (`api_xnc.strict_guard`, 400 + sabab). Ish bazasida onlayndagidek: Строго + paz chetdan 30 mm (4 tomon) — 2026-10-23.
    «Палитра» → tezkor panellar («Сверление», `xnc_palette.panels`) — o'chirilsa detal XNC oynasida o'ng panel yo'q.
  - Kroyga kirmagan detal qatori — onlayn kabi fon yo'q, yozuv #FF6600 (ID, № — oddiy), tanlanganda ko'k (`styles.css .row-left`).
  - Import: CS da `csTexture` yo'q — «Учет текстуры» o'chiq va detallar «Ткт» belgisiz (onlayn standartni yozmaydi; 1305 ta CS;
    aniq `csTexture="false"` — detal belgisi saqlanadi, bizning eksport aylanishi uchun).
  - XNC «Шаблон» → «+ Добавить» = onlayn «Открыть шаблоны обработки» (`XncTemplateBrowser.tsx`): papkalar, eskizlar
    (`GET /xnc/templates/{id}/thumb.svg`), Добавить папку / Переместить / Переименовать / Удалить / Вверх / Домой, «Открыть» — dastur
    oxiriga. Standart papkalar (bizning parametrli dasturlar, `services/xnc_templates_std.py`): «Типовые фрезеровки» 14, «Фасады МДФ» 9,
    «Образцы MebeliX» 7. Foydalanuvchi papkalari — `xnc_tpl_folders` sozlamasi, shablon `folder` maydoni. Chiqindi bo'lagi aniqlash
    (`xnc._cutoff_polygon`) chet bo'ylab / urinma yo'llarda ham to'g'ri.
  - Audit (2026-10-23, kechki): GR / SP / LB parametrlari onlayn bilan maydonma-maydon bir xil (MX'da qo'shimchalar bor);
    GR detallar jadvali ustunlari kengaytirildi. Kroy muharriri — onlayn yordamdagi 22 ta sichqoncha/klaviatura amali
    haqiqiy brauzerda (`e2e/cut_editor_combos.spec.ts`) ishlaydi. (CL) «Толщина пилы для групповых деталей» endi tahrirlanadi
    (`CLParams.kerf_group`, import/eksport `swSawthickDiv`; CL «Объединение деталей» kabi kroyga ta'sirsiz saqlanadi).
  - Ochiq: MillStart «Вперед» ma'nosi (yordamda yo'q)
  - Eski yozuv: (CL) «Толщина пилы для групповых деталей» onlaynda tahrirlanadi, MX da o'chiq (qiymat ishlatilmaydi).
  - Ochiq: MillStart «Вперед» (true) maydoni — fayllarda yo'q, yordamda yo'q, ma'nosi aniqlanmadi. Onlayn loyiha yopilganda
    o'zgarishlar avtomatik saqlanadi — tajribadan keyin asl holatga qaytarish shart.
* **Xodimlar serveri** (`../run_server.bat`, :8000, tunnel `run_public.bat`) shu kodda ishlaydi. Har o'zgarishdan keyin:
  `python tools/backup_db.py` (ish bazasi zaxirasi → `../backups/`, oxirgi 10) → frontend build → server qayta ishga tushiriladi.
  Xodimlar kiritgan ma'lumot va saqlangan sozlamalar (`settings_profiles`) o'zgartirilmaydi. Faqat atayin o'zgartirilgan sozlama farq qiladi
  (standart qiymat o'zgaradi, saqlangan yozuv emas).

## Holat (2026-10-18 — postprotsessorlarga kirish + MES paketi v1)
* **Postprotsessorlarga kirish** (foydalanuvchi qarori): mijoz uchun ochilgan stanok postprotsessorlari — admin hal qiladi
  (`services/pp_access.py`, `GET/PUT /api/postprocessors/access`, «Настройки → Постпроцессоры → stanok» katakchasi; standart —
  bugun ishlayotganlarning hammasi). Yopiqlari ro'yxatlarda nomi bilan kulrang, bosilmaydi; server 403 (kroy, XNC, «Выделить все», MES paketi).
  2-qaror: MebeliX'ning o'z formatlari (`mx:csv|commands|dxf|json`, `mx:xnc_json`, `mx:mes_export`, `mx:mes_package`) va stanoksiz
  shablonlar (`pp:<id>`) ham shunday — «Постпроцессоры → Форматы MebeliX» yorlig'i, `closed_extra` (standart — hammasi ochiq);
  shablon muharriri ko'rinishi (`POST /postprocessors/preview`) va MES sxemasi ochiq qoladi.
* **MES paketi v1**: shartnoma `docs/mebelix/MES_PAKET_V1.md`, quruvchi `services/mes_package.py`, `GET /api/projects/{id}/mes-package?version=1`
  (yubormaydi). «MES» tugmasi — MES tomoni tayyor bo'lgach. Testlar: `test_pp_access_x1018.py`, `test_mes_package_x1018.py`, e2e `pp_access.spec.ts`.

## Holat (2026-10-15, v2.9 — onlayn solishtiruv, ko'p-kroyli audit, MCP)
* Foydalanuvchi talabi: onlayn tizim bilan solishtirish (ayniqsa bitta loyihada bir nechta kroy va listlar), har funksiyani tekshirish, MCP yozish.
  Hammasi — `docs/mebelix/X_1015_ONLAYN_AUDIT_MCP.md` (korpus faktlari, jonli solishtiruv jadvali, 12 tuzatish, 10 savol).
* **MCP serveri** `mcp/` (Node 24, SDK 1.32, Playwright 1.64; 83 vosita: `mx_*`, `compare_*`, `giblab_*`), `.mcp.json` ildizda va `MebeliX_Kroy/` da;
  `npm run build` → `dist/`; `npm test`. Onlayn tizim: `GIBLAB_MODE=cdp|profile`, yozish faqat `GIBLAB_ALLOW_WRITE=1` + `GIBLAB_WORK_FOLDER`.
* Yangi: `POST /projects/{pid}/actions/optimize-all` («Раскроить все операции»), `cs_cut.stock_order` (**list — standart, foydalanuvchi qarori**
  / economy — material tejash; korpus 44 ko'p-listli: 603.9 / 574.0 vs avvalgi 581.9 m²), «Объединить» endi qalinlik + list o'lchamini solishtiradi va listlarni birlashtiradi,
  CS o'chirishda XNC soni ogohlantiriladi, listdan katta detal ogohlantirishi, `from-remnants` qalinlik tekshiruvi (`force`), katalog `sync` qisman
  yangilash + tekshiruv, `set_sheets` (dublikat id 422, otstup eskirtiradi, yo'q qoldiq 404), nusxada ombor havolalari tozalanadi.
* Onlayn solishtiruv: 5000 kupe — MX 18 list vs 18 (F, деловой teng; kesish −7 %); 3120 kuxniya — 5 CS listlar teng, joylashmagan detallar ikkala
  tizimda bir xil. Onlayn «Раскрой» varag'i katta loyihada tabni muzlatadi (tizim tomonida); «Общие действия» — 3 amal, bizda shu + qo'shimchalar.
* Foydalanuvchi javoblari (2026-10-15): «Порядок листов» standarti — **qat'iy ro'yxat**; CS o'chirilganda XNC ham o'chadi (hozirgidek);
  qalinligi boshqa operatsiyalar birlashtirilmaydi; **buyurtmalar navbati + material bazasi tekshiruvi** — `services/material_check.py`,
  `api_queue.py` (`/projects/{pid}/material-check`, `/queue`), `features/projects/QueueDialog.tsx`, «Заказать» blokida «Материал» qatori,
  MCP `mx_material_check` / `mx_queue`.
* E2E `lists.spec.ts` (Ctrl+A → Del) tebranishi tuzatildi: `Projects.tsx onCellFocused` — tanlangan qatorga kechikkan fokus ko'p tanlovni
  buzmaydi (3 marta ketma-ket 11/11).
* Tekshiruv: backend to'liq to'plam o'tdi (+10 `test_x1015_audit.py`, +1 `test_x1015_queue.py`), e2e **11/11**, `tsc` toza, MCP testlari
  3/3. Hali git'ga commit qilinmagan.
* **LT qoidasi** (X_1015 §12): onlayn «Таблица команд» dan qayta qurilgan — har qator (T/C/P × K) = bitta arra yurishi, uzunligi =
  bo'lakning ko'ndalang o'lchami; 5 karta aynan (113.3 m). Bizda chuqur tugundagi oxirgi (chegaraga tegib turgan) bo'lak sanalmas edi —
  `optimizer._build_map` tuzatildi (5000 kupe 5-karta 15.67 → 17.618 m; qolgan farq joylashuvning o'zi), optimizator maqsadi o'zgarmadi;
  `tests/test_x1015b_lt.py` (+5).

## Holat (2026-10-04 tun, v2.8 — «bir xil» bosqichi)
* **Foydalanuvchi qarori:** hozircha har bo'lim / satr xodimlar o'rgangan tizim bilan bir xil (solishtirish oson bo'lishi uchun), dizayn
  keyin (Claude design) o'zgartiriladi; o'z qo'shimchalari qoladi; buyurtmalar moduli / bulut papkalari / hisob — **MES server** (keyin).
  Fayllarda joriy loyiha nomi (`ppfmt.order_text`); tizim universal — hamma stanok modeli / versiyasi; etiketka — GibSaw / MES.
* O'lchov: `docs/mebelix/W_OXSHASHLIK_TEKSHIRUVI.md` (17 ekran, 99.2%), usul va skriptlar — `tools/parity/`; kuzatilgan tavsif — `W_PARITY_SPEC.md`.
* Yangi generatorlar (onlayn namunalardan, bayt-ma-bayt): IMA, Holz-Her NC-HOPS, Masterwood MW310, G CODE, AES Sirius (qisman), Scheer,
  KDT V3.3.0P, Felder F4Classic; jami 43 format. Namunalar: `post prtsessorlar/ONLINE_2026-10-04/` (repoga kirmaydi).
  Asboblar jadvali: `ppfmt/tooling.py` + «Настройки → Постпроцессоры → stanok → Инструменты». Burilish chegarasi: `ppfmt.rot_limit`.
* Ochiq savollar: `postprocessors/SAVOLLAR.md` (Selco OSI `Chk` — stanok tekshiradi, algoritm yo'q → NC300 tavsiya).

## Holat (2026-10-04 kech, v2.7 — onlayn GibLab postprotsessorlari bilan parallel sinov)
* **Parallel sinov** (bitta loyiha ikkala tizimda; natija — `docs/mebelix/postprocessors/SAVOLLAR.md` boshida): prisadka 10 format /
  325 fayl — 217 bayt-ma-bayt bir xil, 100 faqat nom/vaqt, 8 oxirgi kasr raqam; arra 18 format — tuzilishi bir xil
  (farq: etiketka bloblari — ko'chirilmaydi).
* Tuzatildi: yoy-chet aniq kesishuvi (`ppfmt/_cnc2.cut_poly`), Syntec yaxlitlash (`num_hu`), BiesseWorks `TIN/AIN`, AES kromka nomi.
* Yangi: **Felder F4Classic** generatori (`ppfmt/felder_f4classic.py`), stanok formati burilishlarni cheklasa kroyni avtomatik
  qayta bajarish (`ppfmt.ROT_LIMIT`, `main._refit_rotations`, sarlavha `X-PP-Refit`; ombordagi qoldiq bo'lsa — xabar).
* UI: XNC chizmasi «yoyilgan» ko'rinishda (yuza + 4 yon ko'rinish, xoch belgili teshiklar, qirra teshigi kanali, X/Y belgisi,
  lits ko'rsatkichi — `xnc.xnc_drawing_svg`); kroy panelida «Постпроцессоры» oynasi (`features/cs/PpPick.tsx`, stanoklar tartibi va
  yozuvlari — `postprocessors.PP_LABELS`).
* Sinov usuli (takrorlash uchun): scratchpad `ppgen.py` / `cncgen.py` / `cncall.py` / `cmp.py` — loyiha importi → format → solishtirish.
  Onlayn tizimda dialoglarni JS `__tick()` qadamlari + haqiqiy klaviatura (space) bilan boshqarish kerak (sintetik bosishda
  yuklab olish kechikadi); CadMatic v3 / GDrive / NC300 / Scheer / MW310 brauzerning tizim oynasini chiqaradi — qo'lda sinaladi.

## Holat (2026-10-04, v2.6 — o'rnatilgan postprotsessorlar + jonli onlayn GibLab solishtiruvi)
- **Postprotsessorlar:** foydalanuvchi `post prtsessorlar/` da 37 stanok uchun namuna fayllar berdi (27 arra + 10 prisadka) va
  ularni dasturga qo'shishni so'radi. `backend/app/services/ppfmt/` — **35 ta o'rnatilgan generator** (25 arra, 10 prisadka);
  `machine:<kalit>` — shablon biriktirilmagan bo'lsa o'rnatilgan format ishlaydi; `GET /api/postprocessors/native`,
  `GET /api/projects/{pid}/postprocess-xnc?key=machine:<k>` (loyihaning barcha XNC lari zip da). Tavsiflar, internet tadqiqoti va
  savollar — `docs/mebelix/postprocessors/` (`README.md`, `SAVOLLAR.md`, `WEB_*.md`). Tekshiruv: `tools/bench/pp_cnc_check*.py`,
  `pp_saw_check_*.py` (namunalar bilan bayt-ma-bayt + bizning optimizator bilan end-to-end). GibLab ichki etiketka bloblari
  nusxalanmaydi, fayllarda «GibLab» so'zi yo'q (CLAUDE.md 14-qoida yangilangan).
  Prisadka: TPA / Biesse Works / Xilog / HIRZT / KDT WDX / XDWoodCam 958/958, Startech 16/16, Syntec 947, WoodWOP 940, Daron 875.
- **Jonli onlayn GibLab** (Chrome kengaytmasi) bilan 27 farq tuzatildi — `docs/mebelix/V_ONLAYN_SOLISHTIRISH.md` (3 qism).
- **Optimizator:** деловой qoldiq iloji boricha butun polosa (`REMNANT_CORNER_WEIGHT=0.75`); cheklangan listlarda sig'may
  qolgan detallar uchun `_fit_limited` (bin completion) — «Стандарт»/«Максимум»da hammasi joylashadi.
- **Importer:** eski fayllarda kromka belgisi/rangi tartib bo'yicha, XNC soni bog'langan detaldan; `save_drawings` standart o'chiq.
- Testlar: backend ~1900 (ppfmt 118+), e2e 10/11 (`lists.spec.ts` Ctrl+A — eski muammo, sababi hali topilmagan).
- Keyingi: ochiq savollar (`postprocessors/SAVOLLAR.md` — qaysi stanoklar bor, OSI `Chk`, stanokda sinov); bo'sh jadvallarda
  «Добавить / Вставить / Справка» havolalari; hammasi hali git'ga commit qilinmagan (foydalanuvchi ruxsati kutilmoqda).

## Holat (2026-10-15 kech, v2.10 — katta loyihalar bilan ekranma-ekran solishtiruv, 2-sessiya)
* «5000 kupe» va «3120 kuxniya» onlayn ↔ MX: 59 farq topildi va tuzatildi (import ID/egalik/EL, CS/CL/EL/O panellari, jadvallar,
  karta yozuvlari, «Таблица команд», LT qoidasi, XNC chizma/daraxt, hisobot tuzilmasi, chop sozlamalari property-grid oynalari).
  Batafsil: `docs/mebelix/X_1015_ONLAYN_AUDIT_MCP.md` §8–§13; topilmalar ro'yxati sessiya scratchpad `audit/findings_main.md`.
* Ochiq: onlayn «Минимальный отступ в конце» har stek oxirida; «P1-1» formati; onlayn «test» sandbox tozalash (256 ortiqcha op).

## Holat (2026-10-03, v2.5 — onlayn GibLab bilan ekran solishtirish, 1-qism)
- Chrome kengaytmasi ulanmadi → onlayn GibLab skrinlari (`screens/`, `screens_v2/`) bilan solishtirildi; 9 farq tuzatildi
  (chap panel akkordeoni, yuqori jadval balandligi, kromka ustunlari to'liq, kroydan keyingi qoldiq oynasi standart o'chiq,
  ichki «Q-N» matnlari olib tashlandi, XNC «Параметры» joylashuvi, o'lcham rejimi oynasi, «Отмена», EL «(CS)» prefiksi).
  Batafsil — `docs/mebelix/V_ONLAYN_SOLISHTIRISH.md`. Backend 1663 test o'tdi; e2e 10/11 (`lists.spec.ts` — oldindan bor).
- Keyingi: kengaytma ulangach qolgan oynalarni jonli solishtirish.

## Holat (2026-10-02 kech, v2.4 — 18 paket tugadi)
- 4-to'lqin: etiketka vizual redaktori + ZPL, nesting (CN), OEE/ishlab chiqarish analitikasi, import infratuzilmasi va qolgan kichik bo'shliqlar (W15–W18).
  Testlar: backend **1663**, e2e **11**, tsc toza; korpus XNC 8359/8360/8360, EL 303/303; optimizator katta korpusda 5583 vs GibLab 5639.
  Hali yo'q: haqiqiy CAD importerlari (namuna fayllar kerak), ZPL ni printerda sinash, MES integratsiyasi (korxona MES jamoasi), postprotsessor formatlari (korxona dasturchilari).

## Holat (2026-10-02 kech, v2.3 — GibLab funksiyalarining asosiy qismi bajarildi)
- 14 ta paket (W1–W14) tugadi: XNC muharriri/cheklovlar/asboblar, CS bo'shliqlari va chop, Excel v2 + katalog daraxti, etiketka tizimi (LB-A/B + `.lbl`/`program` import/eksport),
  O, CL, SP, mahsulot «Программа», GR/EL, ifoda API, stanok sozlamalari (ParamGrid), CSE rejimlari, «Заказать» oqimi, `.project` eksporti, burilishlar 1…6.
  To'liq ro'yxat va natijalar — `docs/mebelix/R_GIBLAB_FEATURE_MATRIX.md`; paket hujjatlari `T_*.md`; ochiq savollar — `U_OCHIQ_SAVOLLAR.md`.
- Foydalanuvchining 1248 fayllik korpusi (`giblab project`): importer 1248/1248, `.project` round-trip 1248/1248; optimizator katta korpusda cheksiz listlarda 5582 vs GibLab 5639.
  Onlayn GibLab (build 2021-05-21) lokal (2023-05-17) dan eski; ko'rik — `docs/mebelix/giblab_inventory/06_online_korik.md`.
- Testlar: backend 1264 (1 skip), e2e 9, tsc toza. Hali yo'q (4-to'lqin): etiketka vizual redaktori (LB-C), nesting (CN), boshqa CAD importerlari (namuna kerak), OEE.

## Holat (2026-10-02, v2.2 — oraliq)
- Foydalanuvchi qarori: **MES integratsiyasi va postprotsessor formatlari — korxona dasturchilarida** (GibSaw ham MES ichida); bizda:
  chap panelda xira «MES» qatori (Sozlamalar → «MES интеграция» katakchasi yoqilsa faol, 6 bo'limli karkas panel,
  `features/mes/MesPanel.tsx`), postprotsessor **stanok nomlari ro'yxati** (31 ta, yoqish + shablon ulash, `services/postprocessors.py::MACHINES`,
  `/api/postprocessors/machines`). Maqsad — GibLab (local + online) ning hamma funksiyalari + MES/OEE («EKO tizim»).
- 5 ta mustaqil inventar (`docs/mebelix/giblab_inventory/`, ≈ 856 band) → `R_GIBLAB_FEATURE_MATRIX.md` (matritsa, to'lqinlar, savollar).
- Yangi umumiy **ifoda dvigateli** `services/expr.py` (tipli, 67 funksiya; XNC va keyingi etiketka/ustun formulalari shuni ishlatadi) — 190 test.
  XNC: teshik massivi AC/AS/AV, «oldingi qiymat», `enabled`; trigonometriya **radianda**, butun÷butun — butun (GibLab yordamiga mos; tekshirish kerak).
- Backend testlar 423 o'tdi (v2.2 boshida), e2e 6. Parallel ishchi agentlar (W1–W6) uchun qoidalar: `docs/mebelix/S_ISH_QOIDALARI.md`.

## Ishga tushirish va tekshirish
- Windows: `run.bat` → http://localhost:8000 · ishlab chiqish: `dev.bat` (backend :8000 + Vite :5173) yoki VS Code
  «Run and Debug» → «Full stack». Linux/macOS: `./run.sh`, `./dev.sh`. API hujjati: `/docs`.
- Backend testlari: `cd backend && pytest -q` (≈2–3 daqiqa). PostgreSQL: `MEBELIX_TEST_DB_URL=postgresql+psycopg://...`.
- E2E: `cd frontend && npm ci && npx playwright install chromium && npm run e2e` (boshqa Chrome: `PW_CHROMIUM=...`).
  Windows'da Node o'rnatilmagan bo'lsa — portativ `tools/node` (git'ga kirmaydi; `run.bat`/`dev.bat` uni o'zi ishlatadi);
  yo'lda bo'sh joy bo'lsa `MEBELIX_PYTHON` to'liq yo'l bilan beriladi (config uni qo'shtirnoqqa oladi); tizim Chrome:
  `PW_CHROMIUM="C:\Program Files\Google\Chrome\Application\chrome.exe"`.
- Korpus: `cd tools/bench && python3 compare.py normal` (≈8 daqiqa, 2 yadro), `el_check.py`, `xnc_check.py`;
  korpusni qayta qurish: `corpus_build.py` (`tools/bench/projects/` — korxona fayllari, git'ga kirmaydi).
- i18n: matnlar faqat `frontend/scripts/i18n_src.py` da → `python frontend/scripts/i18n_src.py` → `src/i18n/*.json`;
  backend xabarlari — `backend/app/i18n.py`.
- Frontend o'zgarsa `npm run build` (backend `frontend/dist` ni xizmat qiladi; dist git'ga kirmaydi, zipda yig'ilgan).

## Texnik eslatmalar (tuzoqlar)
- Optimizator vaqt byudjeti bilan ishlaydi → kompyuter yuklamasiga qarab natija ±1 list tebranishi mumkin; testlar aniq
  joylashuvga bog'lanmasin. Har natija `services/validate.py` dan o'tishi shart.
- Kesim darajasi = burilish raqami (≤ «Макс. количество вращений»); qirindi 0 yoki ≥ min. obrezka (list chetida emas).
- `colpack.py` numpy talab qiladi (`requirements.txt` da bor). Yangi detal Ткт = «Учет текстуры» (berilmasa).
- `optimize()` bosqichlari: asosiy qidiruv → 3 bosqichli polosa muqobili → (list kamayishi mumkin bo'lsa) bin completion
  + SVC (yechimga yaqin bo'lsa uzaytiriladi) → oxirgi/boshqa listlarda qoldiqni yig'ish. Vaqtlar: `QUALITY_BUDGET`,
  `IMPROVE_BUDGET`, `TOTAL_CAP`, `COMPACT_BUDGET`.
- Korxona fayllarida mijoz ismlari bor — `tools/bench/projects/` va `docs/suhbat/ilovalar/` ommaviy repoga chiqmasin.
- **GibLab oynasi bilan ishlash (jonli solishtirish):** GibLab «Раскроить» / «Удаление раскроя» / list tartibini o'zgartirish
  kabi amallardan keyin loyihani **darhol diskka saqlaydi** (`.project` fayli o'zgaradi; Yandex.Disk sinxron papkasi!).
  Haqiqiy loyihada tajriba o'tkazmang: avval nusxa oling, faqat ochish/ko'rish dialoglari xavfsiz. «Экспортировать» —
  dialogsiz `Downloads` ga yuklaydi; «Импортировать» — mahalliy fayl oynasini ochadi.
- **Listlar ustuvorligi:** `Operation.sheets` tartibi = kroy tartibi (optimizator `_stock_orders` bilan qo'shimcha variantlar
  sinaydi va **ishlatilgan material maydoni** bo'yicha tanlaydi). Import: soni (`qty`) bo'yicha o'sish; `10000` = cheksiz.
  Real fayllarda `count="100000"` ham uchraydi → importer 10000 ga qisqartiradi (modellarda qat'iy chegaralar bor,
  eski JSON esa «legacy» kontekstda qisqartirib o'qiladi).
- Frontend jadvallarida AG Grid qatorlari DOM tartibida emas, `row-index` bo'yicha joylashadi — e2e testlarda
  `.ag-row[row-index="N"]` ishlating. Chrome avtotarjimasi `translate="no"` bilan o'chirilgan.
- PowerShell himoyasi `Remove-Item`/«Delete» so'zi bor buyruqlarni bo'sh joyli yo'llarda to'sib qo'yishi mumkin —
  fayl yaratish uchun Write/Edit vositalaridan foydalaning, bazani `Move-Item` bilan chetga oling.

## Keyingi ishlar (backlog)
- Foydalanuvchidan javob kerak: (1) kromka qalinligi 0 qolsinmi; (2) arra stanogi modeli va postprotsessor formati
  (namuna fayl); (3) MES API manzillari, auth, webhook; (4) etiketka printeri va o'lchami.
- Qo'shimcha savol (v2.1): **«Минимальная обрезка»** ma'nosi — validator `qoldiq + propil ≥ min` deb tekshiradi
  (propil 3, min 5 da 2 mm chiqindi chiqishi mumkin); spetsifikatsiya C3 «qoldiq ≥ propil+min». GibLab'da qaysi biri?
- UI (v2 spetsifikatsiyasidan qolgan, past ustuvorlik): «Свойства» → «Программа» (parametrik mahsulot), «Заказать» (MES)
  oynasi (ijrochi), Каталог товаров oynasi (kategoriyalar daraxti, rasm), Ctrl+P ustun profillari (Операции),
  «Режимы ввода деталей» taklifi, XNC Редактор sozlamalari, «Сервисы»/«Сохранение отчетов», O/CL/SP/LB/CN operatsiyalari,
  DXF import, `.project` eksport; GibLab'ning «Очистить проект» / «Пересчитать параметричность» ma'nosini aniqlash;
  Docker compose'ni real muhitda sinash; PostgreSQL yo'lini (qidiruv `lower()` + `ESCAPE`) sinash. To'liq ro'yxat —
  `docs/mebelix/Q_QA_V2_1.md` §4.
- Optimizator: ko'p-listli 2 kroy (1014 so'qoq, 1071 Mirshoxid kuxniya) — GibLab 8.8 % chiqindili zich joylashuv topgan.
- Optimizator g'oyalari: chegaraviy kroylar (corpus #129 «1034 Sarvar op4», #348 «1096 Sarvar op8», #162, #273) vaqtga
  qarab ±1 list — barqarorlik uchun list tejash qidiruvlarini parallel jarayonlarda ishlatish yoki vaqt o'rniga ish hajmi
  chegarasi; «Быстро» rejimida 23 kroyda +1 list; ≈ 75 kroyda деловой qoldiq GibLab'dan kam (u bir nechta o'rta bo'lak
  qoldiradi); kravat 1-listi 92.83 % vs 93.87 %.

## Fayllar xaritasi
- `backend/app/main.py` (REST), `api_extra.py` (ombor, sozlamalar, MES), `models.py` (Pydantic, v1 migratsiyalari),
  `services/optimizer.py` + `colpack.py` (kroy), `validate.py`, `editor.py` (qo'lda tahrir), `calc.py` (narx, kromka,
  sarf), `xnc.py`, `render.py` (hisobot), `labels.py`, `postprocessors.py`, `plugins/legacy_project.py` (.project import).
- `frontend/src/features/cs/*` (detallar, parametrlar, listlar, kroy), `shared/hotkeys.ts`, `store/ui.ts`, `e2e/kroy.spec.ts`.
- `docs/mebelix/` — v2 spetsifikatsiyalar (A–O) va taqqoslash (P); `docs/suhbat/` — suhbat arxivi; `tools/bench/` — korpus.
