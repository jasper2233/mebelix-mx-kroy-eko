# R. GibLab (local + online) funksiyalari matritsasi va ish rejasi (v2.2, 2026-10-02)

Manba: 5 ta mustaqil inventar (`giblab_inventory/01…05`), GibLab yordam sahifalari (faqat funksional ma'noni tushunish
uchun o'qildi, o'z so'zlarimiz bilan yozildi), bizning kod. GibLab dasturi, kaliti va litsenziyasiga tegilmadi; GUI sinovlari
o'tkazilmadi — «❓» joylar foydalanuvchi bilan tekshiriladi.

## 1. Jami holat

| Inventar | Bandlar | ✅ | 🟡 | ❌ | ❓ / boshqa |
|---|---|---|---|---|---|
| 01 CS, CSE, qoldiqlar, material katalogi | 158 | 110 | 25 | 22 | 1 |
| 02 CL, CLE (погонажный раскрой) | 125 | 5 | 53 | 55 | 12 |
| 03 EL, GR, O, LB, ifodalar tili, katalog, UI komponentlari | 250 | 55 | 63 | 124 | 8 |
| 04 XNC, postprotsessor, `.project` formati | 133 + 23 | 51 | 27 | 45 | 10 |
| 05 import, buyurtma, GibSaw, online↔offline, yangilanishlar | 167 | 33 | 42 | 53 | 11 ❓, 17 MES-jamoasiga, 11 n/a |
| **Jami** | **≈ 856** | **≈ 254** | **≈ 210** | **≈ 299** | |

Eng muhim kuzatuv: korxonaning 205 ta real loyihasida faqat **CS (635), EL (377), XNC (9698), LB (3)** operatsiyalari bor;
**CL, O, GR, SP yo'q**. Shuning uchun CS/EL/XNC/LB ning to'liqligi birinchi o'rinda, CL/O — «to'liqlik» uchun keyingi to'lqinda.

## 2. Ataylab qilinmaydiganlar (sabab bilan)

| Nima | Sabab |
|---|---|
| GibLab litsenziyasi, HASP kaliti, «Лицензии», online hisob/balans/«Выйти» | foydalanuvchi talabi + mualliflik huquqi; MES SSO yetarli |
| MES integratsiyasining ichki mantig'i, mijoz buyurtma portali (ID+PIN), GibSaw (sex ekrani) | MES jamoasiga topshirilgan; bizda REST + xira «MES» paneli karkasi tayyor |
| Postprotsessorlar ichki formati | korxona dasturchilarida; bizda stanok nomlari ro'yxati + shablon ulash tayyor |
| `.project` **eksport** | CLAUDE.md 4-qoida (formatlar nusxalanmaydi) — foydalanuvchi ruxsatisiz yo'q (savol 10) |
| Dropbox, 1C, «Сервисы» | MES katalogi/REST bilan yopiladi; aniq talab kelguncha yo'q |
| Boshqa CAD importerlari (Woody2, BCAD, ABF, PRO100, Imos, Ardis, iLENIA, MPR) | namuna fayl va talab kerak (savol 4) |
| Nesting (CN) | LDSP/MDF faqat to'g'ri to'rtburchak detal; talab kelsa (savol 11) |

## 3. Bu sessiyada bajarilganlar

| Band | Holat |
|---|---|
| Chap panelda xira «MES» qatori → «Sozlamalar → MES integratsiyasi» katakchasi yoqilsa faol, 6 bo'limli panel karkasi | ✅ |
| Postprotsessor stanoklari: 19 pil markazi + 12 ishlov markazi, yoqish, shablon ulash, fayl nomi prefiksi, «Раскрой → Постпроцессор» da ko'rinishi | ✅ |
| Umumiy ifoda dvigateli `services/expr.py` (tipli, 67 funksiya, `if/xor/=/<>/^`, `format`, `now`, matn funksiyalari, xavfsizlik chegaralari) + 190 test | ✅ |
| XNC: teshik massivi AC/AS/AV, «oldingi qiymat» qoidasi, «Включить» (`enable`), butun tipli o'zgaruvchi, ifoda tili GibLab yordamiga mos | ✅ |

**Qaror (tekshirish kerak):** XNC ifodalarida trigonometriya endi **radianda** (yordam misollari: `cos(pi) = −1`), butun÷butun — butun
(`7/2 = 3`). Eski spetsifikatsiya (J3) gradus degan edi; bitta konstanta (`xnc.XNC_DEGREES`) bilan almashtiriladi. Korxona
fayllarida funksiya ishlatilmaydi (korpus 0), shuning uchun hisob natijalari o'zgarmadi.

## 4. Ish to'lqinlari (ustuvorlik bo'yicha)

### 1-to'lqin — kundalik ishlatiladigan operatsiyalar to'liqligi (parallel, har biri alohida fayllarda)
| № | Paket | Qamrab oladi | Asosiy fayllar |
|---|---|---|---|
| W1 | **XNC muharriri** | ichma-ich daraxt (If/Else/While/Sub), `Par` kiritish oynasi, shablon saqlash/ochish/eksport/import + tayyor kutubxona, `ms` qo'shimchalari (sdp, sxy, in/out, c), importer yetishmayotgan atributlar, fillet hisobi | `xnc.py`, `XncPanel.tsx`, `legacy_project.py` (XNC qismi) |
| W2 | **CS bo'shliqlari** | detal maydoni (zagotovka bo'yicha), kroygacha material/list miqdori, pripusk punktiri, chop sozlamalari (yo'nalish, guruhlash, ishlov belgilari, shrift), qoldiqlar («Исп. кол-во», rezerv), mayda yorliqlar, CSE rejimlari | `features/cs/*`, `render.py`, `warehouse.py`, `Print.tsx` |
| W3 | **Excel import v2 + katalog daraxti** | 4 tab, material/mahsulot bo'yicha guruhlash, o'lcham rejimi, `.xls`, «faqat mahsulot soni», «Товары» daraxt oynasi + goods.xls | `importers.py`, `ExcelImport.tsx`, `CatalogPicker.tsx`, `Settings.tsx` (katalog) |
| W4 | **LB etiketka tizimi (LB-A/B)** | LB operatsiyasi parametrlari, JSON shablon + ifodali maydonlar (yangi dvigatel), qoldiq/mahsulot etiketkasi, Code128, bir detalga bir necha etiketka, A4 da 4/6 karta | `labels.py`, `models.py` (LBParams), `Print.tsx` |
| W5 | **O (Комплектация)** | model, hisob, panel, hisobot, `.project` importi | `models.py`, `calc.py`, yangi `features/o/` |
| W6 | **GR + EL + ifoda API** | GR panel bo'shliqlari, EL kichik kamchiliklari, `/api/expr/functions` + `/api/expr/check`, «Что нового» sahifasi | `features/el/*`, `gr` qismi, `api_extra.py` |

### 2-to'lqin (W7–W10) va 3-to'lqin (W11–W14) — BAJARILDI (2026-10-02; hujjatlar `T_*.md`, savollar `U_OCHIQ_SAVOLLAR.md`)
| Paket | Natija | Yangi test |
|---|---|---|
| W7 | 19 stanokning sozlamalar sxemasi (75 parametr, ParamGrid) + «Данные для этикеток» jadvallari (nom → ifoda, jonli ko'rinish), Jinja kontekstida `machine`/`label` | 28 |
| W8 | XNC «Ограничения» (rejim, gabarit, teshik/paz/freza cheklovlari, burish), «Инструменты» (20 standart asbob), «Палитра» (31 buyruq) | 57 |
| W9 | Etiketka shablonlarini import/eksport (`program` XML ↔ JSON; 12 real shablon 12/12 aylanishi teng) | 64 |
| W10 | `.project` eksporti (1248/1248 round-trip teng), burilishlar 1…6, `min_part_size` «Общие» da | 60 |
| W11 | (CL) погонажный раскрой + CLE: 1D optimizator (brute-force tekshirilgan), panel, xarita, chop, qoldiq (`linear`), import/eksport | ~70 |
| W12 | (SP) Обработка поверхности, mahsulot «Программа» (Par/Var/Err/Msg, `product.*`), «Пересчитать параметричность» | 57 |
| W13 | CSE: ko'p tanlash, Shift+A/Shift+W, karta torsovkasi, kartalar tartibi, 409 himoyasi (200 fuzz) | 44 |
| W14 | «Заказать» oqimi (holat o'tishlari, rollar, tarix), ro'yxat «Изменено», «Очистить проект» | 74 |

**Yakuniy tekshiruv (yetakchi):** backend **1264 test o'tdi** (1 skip), e2e **9/9** (6 + 3 tutun testi: hamma operatsiya turlari, sozlamalar, dialoglar), `tsc` toza,
build o'tdi; korpus XNC 8359/8360/8360, EL kromka 303/303; optimizator: kichik korpus 1188 vs 1212 (shovqin ±2), katta korpus cheksiz listlarda **5582 vs GibLab 5639**,
tekshiruv xatosi 0. Tuzatilgan: `render.fmt` (6 raqamdan ortiq qiymatlarda kasr yo'qolishi), e2e (qo'lda tahrirdan keyingi qoldiq taklifi oynasi).

### 4-to'lqin — BAJARILDI (W15–W18)
| Paket | Natija | Yangi test |
|---|---|---|
| W15 | Etiketka **vizual redaktori** (sichqoncha, to'r/yopishish, xossalar, undo, qatlamlar, ifoda paneli), polilinya/yoy/ellips, `source=user` jadvali (Excel Ctrl+V), **ZPL chiqarish** (fayl) | 104 |
| W16 | (CN) **nesting**: kontur/teshikli detallar, raster pastki-chap + FFT, ichki kesimlarga joylash, mustaqil `validate_cn`, CNE tahrir (slide/snap), fon vazifasi, postprotsessor ma'lumoti | 91 |
| W17 | **OEE** va ishlab chiqarish analitikasi: A×P×Q, smenalar, to'xtash sabablari, Pareto, MES uchun hodisa API (idempotent), sex rejimi hodisalari, panel (MES → OEE va «Настройки → Производство») | 110 |
| W18 | «Импорт из других программ» infratuzilmasi (7 format xira — namuna yo'q), import profillari, Excel «Простые операции/Материалы/SP/GR/XNC», XNC drag&drop va fillet, CL xossalar/variantlar/до кроить, «№» ustuni | 95 |

**Yakuniy tekshiruv (v2.4):** backend **1663 test** (1 skip), e2e **11/11**, `tsc` toza, build o'tdi; korpus XNC 8359/8360/8360, EL 303/303; optimizator: kichik 1188 vs 1212,
katta cheksiz listlarda **5583 vs GibLab 5639**, xato 0. Server :8000 da, mavjud bazada migratsiyalar xatosiz.

### Hali qolgan (namuna/ruxsat/qaror kerak)
Haqiqiy CAD importerlari (PRO100, Imos fxm, BM xml/obl, BCAD xml, Woody2 xml/wes, WoodWop mpr, iLENIA pd4) — **namuna fayllar kelganda**; ZPL ni haqiqiy printerda sinash;
`.project` eksportini GibLab nusxasida sinash; nesting uchun korxona XNC namunalari; OEE sozlamalarini zavod bilan kelishish; etiketka/stanok formatlari (foydalanuvchi dasturchilari);
MES integratsiyasi (korxona MES jamoasi). Ochiq savollar — `U_OCHIQ_SAVOLLAR.md`.

Onlayn ko'rikdan: operatsiya turlari — O, CS, **CN (!ТЕСТ!)**, CL, EL, SP, GR, XNC, LB; onlayn «Общие действия» da 3 amal (lokalda 6); onlayn importlar:
PRO100, Imos (fxm), BM (xml, obl), BCAD (xml), Woody2 (xml, wes), WoodWop (mpr), iLENIA (pd4).

### 1-to'lqin natijasi (6 ta paket tugadi; hujjatlar `T_*.md`)
| Paket | Natija | Hujjat |
|---|---|---|
| W1 XNC muharriri | ichma-ich daraxt, `Par` kiritish, shablon kutubxonasi (7 namuna), frezalash kengaytmalari, importer atributlari, ishlov markazi konteksti (`machine:<kalit>`), DXF import; 104 test | `T_W1_XNC.md` |
| W2 CS bo'shliqlari | detal maydoni (pilniy), kroygacha miqdor, pripusk punktiri, chop sozlamalari (yo'nalish, guruhlash, shrift, rang), «Исп. кол-во», qoldiq rezervi, «?»/F1, yorliqlar; 31 test | `T_W2_CS.md` |
| W3 Excel v2 + katalog | 2 tabli import (Детали/Изделия), guruhlash, `.xls`, «faqat soni», profil, «Товары» daraxt + rasm; 33 test | `T_W3_IMPORT_KATALOG.md` |
| W4 LB etiketka | LB operatsiyasi, JSON shablon + ifodalar, Code128, bir detalga ko'p etiketka, A4 da 4/6 karta, 4 namuna shablon; 109 test | `T_LB_ETIKETKA.md` |
| W5 O komplektatsiya | model, hisob, panel, Excel Ctrl+V, katalog, hisobot, `.project` importi; 29 test | `T_O_KOMPLEKTATSIYA.md` |
| W6 GR/EL/ifoda API | GR panel va `gr_defaults`, `/api/expr/*`, «Справка» + «Что нового», EL «?» va saralash; 95 test | `T_W6_GR_EL_IFODA.md` |
Yig'ish: backend **824 test o'tdi**, e2e **6/6**, `tsc` toza, korpus XNC 8359/8360/8360, EL kromka 303/303.

## 5. Foydalanuvchiga savollar (takrorlarsiz, ustuvorlik bo'yicha)

> **2026-10-02 (kech):** foydalanuvchi `giblab project` papkasini (1248 fayl) berdi — ko'p savollarga javob u yerda (§6). Quyida
> javob topilganlari belgilangan (✅ javob berilgan), qolganlari ochiq.

**A. Tekshirish kerak (GibLab oynasida 5 daqiqalik sinov)**
1. XNC redaktorida `sin(90)` nechaga teng — 1 (gradus) yoki 0.89 (radian)? `7/2` — 3 yoki 3.5? Bizda hozir radian va 3.
2. «Минимальная обрезка»: propil 3, min 5 bo'lsa, 2 mm li tilim hosil qiladigan karta chiqadimi? (bizning validator «qoldiq + propil ≥ min» deydi).
3. «Объединение деталей» va «Группировка деталей по свойствам» yoqilganda karta qanday o'zgaradi? Xodimlar ishlatadimi?
4. «Минимальный размер детали» — kichik detal kroyga umuman kirmaydimi yoki faqat ogohlantirishmi?

**B. Korxona ma'lumotlari**
5. Excel dan nima va qanday faylda yuklanadi (`.xls` yoki `.xlsx`)? Mijoz ismlarisiz 1–2 namuna bera olasizmi?
6. Etiketka printeri turi/o'lchami; hozirgi etiketka namunasi (GibLab `.lbl`) — ularni import qilishga ruxsat?
7. Qoldiqlar: «Исп. кол-во» — mijoz olib ketgan qoldiq omborga yozilmasinmi? Mayda (deloviy emas) qoldiq va butun listlar MebeliX omborida yuritiladimi yoki MES'dami?
8. Katalog manbasi: MES (daraxt tuzilmasi?) yoki Excel (`goods.xls`)? Rasmlar bormi?
9. Bazis `side="1"/"2"` — 1 = lits, 2 = orqa to'g'rimi? (1338 XNC dastur hisoblanmay qoladi).
10. `.project` **eksport** kerakmi (parallel ishlash / qaytish yo'li)? CLAUDE.md 4-qoida bilan ziddiyat — ruxsat bering yoki rad eting.
11. Nesting (MDF fasad/shpon) bilan ishlanadimi? Yo'q bo'lsa UPD-001…004 butunlay rad etiladi.
12. Arra stanogining burilishlar soni (yordam ba'zida 4 deydi), standart 6 qolsinmi? Propil 0 mumkinmi?
13. Boshqa CAD (Woody2, BCAD, 3D-Constructor, SketchUp ABF, PRO100, iLENIA, MPR) — qaysilari rejada? Bo'lsa namuna fayl.
14. Pogonaj (CL), furnitura (O) va paz (GR) ishlatiladimi? Hozircha loyihalarda yo'q — qilamiz, lekin oxirgi navbatda.

## 6. Real loyihalar papkasi tahlili (`giblab project`, 1248 fayl) — savollarga javoblar

Faqat o'qildi (GibLab da ochilmadi), mijoz nomlarisiz jamlama hisoblar. Importerimiz **1248/1248** faylni o'qiydi (7 s); GibLab
saqlagan 945 fayl + Bazis'dan to'g'ridan-to'g'ri kelgan 303 fayl (faqat `importBMV`).

| Savol | Javob (ma'lumotdan) |
|---|---|
| ✅ Kromka qalinligi 0 qolsinmi (A) | Yo'q: **hamma 1418 EL operatsiyada `t=1`**, kenglik 19, prifugovka 1, `elRestSide` 30 (kam: 40/12/20); yaxlitlash 20 (851) va 10 (567) |
| ✅ Min. obrezka / propil | `swMinPruning` **5**, propil **3** (2212/2214), `swTrimIncludeSaw=false`, torsovka 2/2 (2204/2211). «propil 3, min 5» holati real standart |
| ✅ Burilishlar soni (12) | **4** (1898/2214), 6 (152), 3 (116), 5 (48) — standart 4 ga yaqin; yangi CS uchun taklif: 4 |
| ✅ «Объединение деталей» / «Группировка» (3) | **Hech qachon ishlatilmaydi**: `cCombiningParts=false` (2211/2211), `cGroupParts=0` — W2 dagi «o'chirilgan» ko'rinishi yetarli |
| ✅ «Сохранение чертежа» (Q-15) | **hamma joyda o'chiq** (`cSaveDrawCut=false`) — talab yo'q |
| ✅ Etiketka printeri/o'lchami (6) | 12 ta LB: **A4 varaq, 2×4 to'r** (`printMode=0`), `source=2` (89×60.25 mm) — W4 ning standarti («sheet») to'g'ri; rulon printer talabi yo'q |
| ✅ Bazis `side` (9) | qiymatlar `true` (29 146) / `false` (940) — «1/2» emas; `face_side` allaqachon shunday o'qiladi; `turn=0`, ko'zgu yo'q |
| ✅ O (komplektatsiya) formati | 5 ta real O: `<operation typeId="O"><material id count/>` → `simple` tovar (kod, nom, birlik «шт», soni, narx 0); `owner` atributi yo'q — W5 importeri mos ishlaydi (10 qator o'qildi) |
| ✅ CL (погонаж) | faqat 3 ta, Bazis'dan kelgan, hisoblanmagan (manfiy miqdorlar, `l=3200`) — talab yo'q; importer CL detallarini o'tkazib yuboradi + ogohlantiradi |
| ✅ Qoldiqlar (5) | 1221 ta list yozuvida `waste` qoldiq bor, 40 790 detalda `usedCount` — qoldiq tizimi ishlatiladi; «Исп. кол-во» mantig'i to'g'ri yo'nalishda |
| ✅ Valyuta | `сум` (487) va `UZS` (458) — ikkalasi ham uchraydi |
| Online ↔ Local | `version="21052101"` = **onlayn build (2021-05-21)**, `23051701` = **lokal build (2023-05-17)**, ikkalasi 2026 yilda parallel ishlatilgan. Lokalga xos (yangilanish jurnali): nesting yaxshilanishlari, 6 yangi postprotsessor (Bavelloni, Excitech, HolzHer, Scheer, AES Alpha, Panhans), «Свойства детали»; fayl atributlari: CS `cSortPatterns`, EL `elPreMillingEqual`. Faqat onlayn: hisob/balans, serverdagi loyihalar, Dropbox, buyurtma («Заказать»), postprotsessor obunasi |
| `.gibcut` | GibSaw'ning yopiq ikkilik fayli (UTF-16 satrlar) — o'qimaymiz/yozmaymiz (formatlarni nusxalamaslik qoidasi; GibSaw MES ichida) |

**Foydalanuvchi javoblari (2026-10-02, kech):**
1. `sin(90)` / `7/2`: foydalanuvchi ham bilmaydi — internetdan izlandi (GibLab hujjati internetda yo'q); yagona manba — GibLab yordamining ifoda sahifalari
   (radian; butun÷butun — butun) → shunday qoldi (`xnc.XNC_DEGREES`).
2. «Минимальный размер детали» — sex uskunasiga qarab **har xil, GibLab sozlamalarida bor** → bizda sozlanadigan parametr (`min_part_size`, kichik detalda ogohlantirish;
   W10 umumiy standart orqali sozlanishini tekshiradi).
3. Excel namunasi — keyinroq (Bazis mutaxassisi hozir yo'q).
4. `.lbl`/etiketka shablonlari import **va** `.project` eksport — **ruxsat berildi** (CLAUDE.md 4-qoida istisnosi): maqsad — ommabop tizim, mijoz ixtiyori; tayyor fayl
   import/eksport, GibLabning o'z namunalarini ko'chirish emas → W9 (etiketka) va W10 (`.project`).
5. Burilishlar: universal, ixtiyoriy tanlanadi, GibLab bilan kamida bir xil (GibLab ro'yxati: 2…6) → 1…6 (W10).
6. Onlayn GibLab ko'rildi: `giblab_inventory/06_online_korik.md` (19 stanok sozlamalari, XNC cheklovlari, buyurtma moduli) → W7 (stanok sozlamalari), W8 (XNC cheklovlari).

**Hali ochiq (ma'lumotda javob yo'q):** `sin(90)`/`7/2` (jonli GibLab), «Минимальный размер детали» ma'nosi, `.xls` namuna, katalog manbasi,
`.lbl` import ruxsati, `.project` eksport ruxsati, boshqa CAD, nesting (CN) kerakmi.

**Katta benchmark** (1877 kroy, 59 690 detal, GibLab 5825 list; `BENCH_*` muhit o'zgaruvchilari, `tools/bench/corpus_build.py`): natija
`docs/mebelix/P_TAQQOSLASH.md` §4b ga yoziladi.
