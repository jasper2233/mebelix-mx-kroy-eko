# 02. (CL) Погонажный раскрой va (CLE) — funksiyalar inventari va amalga oshirish spetsifikatsiyasi

Sana: 2026-10-02 · Muallif: mahsulot tahlili (agent) · Holat: qoralama, foydalanuvchi savollari (§6) kutilmoqda.

**Manbalar (faqat funksional ma'noni tushunish uchun o'qilgan, matn ko'chirilmagan, hammasi o'z so'zlarim bilan):**
GibLab yordam sahifalari `cl_ru`, `cle_ru`, `remainders_ru`, `goods_ru` (+ bo'limlar ro'yxati uchun `help_ru`) va ularga
bog'langan rasmlar (`cl_params1/2/4/5`, `cs_params5/7`); bizning `CLAUDE.md`, `docs/suhbat/01_KONTEKST.md`,
`docs/mebelix/` (A, B, C, D, E, F, G, H, K, L, Q), `backend/app/*`, `frontend/src/features/*`; korxona korpusi (205 ta
`.project`) — faqat operatsiya **turlari soni** sanaldi (mijoz ma'lumotlari hujjatga kiritilmagan). GibLab dasturi, kaliti,
`.exe/.dll/.jar/.cache.html/.rpc` fayllari ochilmagan, GUI ishlatilmagan, bizning kod o'zgartirilmagan.

**Dalil belgilari:** `Y:cl/<bo'lim>` — `cl_ru` yordamidagi bo'lim; `Y:cle` — `cle_ru`; `Y:ost` — `remainders_ru`;
`Y:tov` — `goods_ru`; `R1` torsovka sxemasi (`cl_params1`), `R2` otxod torsovkasi (`cl_params2`), `R4` kroy ekrani
(`cl_params4`), `R5` chop dialogi (`cl_params5`), `R6` paket sxemasi (`cs_params5`), `R7` detal tomonlari (`cs_params7`);
`R4-hisob` — rasmdagi raqamlardan men chiqargan hisob (taxmin, §6 da tasdiqlash so'raladi); `K1`, `G4`, `B5` … — bizning
`docs/mebelix/` bo'limlari; `fayl:qator` — bizning kod.

**«Bizda» belgilari:** ✅ bor va CL uchun o'zgarishsiz ishlaydi · 🟡 qisman (model / umumiy kod / CS analogi bor, CL uchun
tugallanmagan) · ❌ yo'q · ❓ yordam javob bermaydi, aniqlashtirish kerak.
**Murakkablik:** S ≤ 0.5 kun, M 1–3 kun, L > 3 kun. **Ustuvorlik:** H — birinchi ishlaydigan CL uchun shart (MVP),
M — to'liqlik uchun muhim, L — kam uchraydi / keyin.

---

## 1. Qisqa xulosa

**CL nima.** Погонажный раскрой — bir o'lchovli kesish (1D cutting stock): profil, plintus, bruss, truba kabi **polosa**
(xlom) materialini kerakli uzunlikdagi bo'laklarga kesish. Detalning uzunligi va soni muhim; eni polosa eniga teng (u faqat
kesim uzunligi, kromka va narx hisobi uchun kerak). Maqsad — materialni kam sarflash, qoldiqni (деловой отход) saqlab
qayta ishlatish, kesim ishini (kesim soni, uzunligi) hisoblash va arra stanogiga uzatish.

**Ish oqimi.**
```
Material (katalog yoki qo'lda: eni, qalinligi, narx 1 m)            ─► «Параметры» (kerf, torsovka, paket, otxod, narx)
  ─► Detallar: Д-на × Кол, ixtiyoriy ОВ/ОН/ОЛ/ОП kromka, nom belgilari  ─► «Детали» (Excel dan Ctrl+V mumkin)
  ─► Polosalar: uzunlik × soni (+ ombor qoldiqlari)                    ─► «Полосы и отходы»
  ─► «Раскроить»: optimizatsiya  ─► kartalar (har karta = bitta sxema × C nusxa), buyruqlar jadvali (T/C/P/W)
  ─► qo'lda tahrir (CLE) · postprotsessor (arra formati) · chop (hisobot) · narx (material + operatsiya)
  ─► qoldiqlar: деловой отход omborga, jadvalda «Исп. Кол-во» (mijoz oladigan bo'laklar)
```

**Tuzilma.** Operatsiya paneli 4 yorliq: `Параметры` · `Детали` · `Полосы и отходы` · `Раскрой`; alohida: tahrir oynasi
(CLE) va chop sozlamasi. CS (listli kroy) panelining soddalashtirilgan 1D varianti — shuning uchun **infratuzilmaning
ko'pi qayta ishlatiladi** (jadval komponenti, yorliqlar, narx/qoldiq/chop/MES mexanizmlari), yangi narsa asosan **optimizator**,
**1D karta chizmasi** va **CL parametrlari**.

**CL va CLE farqi.** CL — operatsiyaning o'zi: parametrlar, detallar, polosalar, avtomatik kroy, kartalarni ko'rish, chop. CLE —
tayyor kroyni **qo'lda tahrirlash** oynasi (alohida, to'liq ekranga o'tishi mumkin): chapda detallar jadvali
(qolgan/ishlatilgan sonlar jonli), o'ngda kartalar; detalni polosaga qo'yish/olib tashlash, karta qo'shish/o'chirish,
polosa nusxalari sonini va torsovkani o'zgartirish. CLE parametrlarni o'zgartirmaydi, faqat natijani; oyna yordami CS tahririga
deyarli aynan o'xshash (shuning uchun «Ширина»/«Ткт»/«aylantirish» CL da ma'nosiz qolgan bo'lishi mumkin — Q13).
Burchak (qiyshiq) kesim, tekstura yo'nalishi, kesish usuli tanlash — CL yordamida **yo'q**: faqat to'g'ri (90°) ko'ndalang kesim.

**Rasmlardan chiqarilgan muhim aniqliklar (tekshirilgan raqamlar):**
1. Foydali uzunlik `U = L − (T_boshi + k) − (T_oxiri + k)`; misol 1600 mm, torsovka 20, propil 10 → **1540** (R1). Kartadagi
   chizma: `20 | k10 | 780 | k10 | 500 | k10 | 150 | k10 | otxod 80 | k10 | 20` = 1600 (R1).
2. «Торцовка отходов»: ✓ — otxod toza uzunligi **80**; ☐ — otxod oxirgi torsovka zonasini ham o'z ichiga oladi: **110 = 80 + 10 + 20** (R2).
3. Statistika qatori (R4): `S: 3200/600` (polosa uzunligi/eni), `C: 1/17`, `Cp: 5/80`, `LT: 3.6/58.2`, `F: 96.88%/97.81%`.
   Hisob (R4-hisob): 3-kartada detallar 800+800+500+500+500 = 3100 → `F = 3100/3200 = 96.875 %` ✓;
   kesimlar soni 6 → `LT = 6 × 0.6 m = 3.6 m` ✓ (propil 10, torsovka 20 da: 2·20 + 6·10 = 100 = 3200 − 3100 ✓);
   jami `97 × 0.6 = 58.2 m` ✓ (97 = 80 detal + 17 polosa). Demak **LT = kesimlar soni × polosa eni**, **F = Σ detal uzunligi ÷ polosa uzunligi**.
4. Detal «Ширина» ustuni hisobotda polosa eniga teng (R5 fonida 500, S: 2400/500) — ya'ni CL detalning eni alohida kiritilmaydi.
5. **Korxonada CL ishlatilmaydi:** 205 ta real loyihada operatsiyalar: CS 635, EL 377, XNC 9698, LB 3, **CL 0** (O/SP/GR ham 0).
   Kromka lentalari (`band`, 377 ta) CL emas, EL materiali. Demak CL — biznes talabi emas, **to'liqlik/kelajak** funksiyasi;
   real CL namunasi va solishtirish ma'lumoti **yo'q** (§6 Q1).

---

## 2. Funksiyalar jadvali

Ustunlar: `ID` · Funksiya · Qanday ishlaydi · Qiymatlar / standart · Bizda · Dalil · Murakkablik · Ustuvorlik.
«Standart» yordamda ko'rsatilmagan bo'lsa «taklif» deb belgilangan (GibLab standarti noma'lum).

### 2.1. Operatsiya va panel (umumiy)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-001 | CL operatsiya turi | Operatsiyalar ro'yxatida alohida tur: polosa (profil, plintus, bruss, truba) uzunligi bo'yicha 1D kesish va hisob | tur kodi `CL`, ikonka — chiziqli kesish | 🟡 | `models.py:60` enum bor; `opmeta.tsx:14` IMPLEMENTED da yo'q → `OperationsTable.tsx:38–41` da «later» bilan o'chirilgan | S | H |
| CL-002 | Panel yorliqlari | To'rt yorliq: Параметры · Детали · Полосы и отходы · Раскрой; yordamda ichki sarlavha «Листы и отходы» deb ham yozilgan, ekranda — «Полосы и отходы» | tartib shu | ❌ | Y:cl, R4 | S | H |
| CL-003 | Standart parametrlarni saqlash | «Сохранить текущие параметры для использования по умолчанию» — keyingi yangi CL shu qiymatlar bilan yaratiladi | scope `cl_defaults` (taklif) | 🟡 | Y:cl/Действия; `settings.py:50` SCOPES da cs/el bor, cl yo'q | S | M |
| CL-004 | Kontekst yordami | F1 va har parametr yonida «?» — shu panel/parametr yordami | o'z matnimiz (uz+ru) | 🟡 | Y:cl; D0 §2; `Help.tsx` | S | L |
| CL-005 | Katalogdan material tanlash | «Каталог товаров»dan погонажный (kind=linear) tovar: kod, nom, narx, qalinlik, standart polosa uzunligi/eni operatsiyaga yoziladi | katalog ustunlari: ID, Родитель, Папка, Код, Наименование, Ед.И, Цена, Т-на, Д-на, Ш-на | 🟡 | Y:tov; `db.py:96` kind=linear bor; `OperationsTable.tsx:161` faqat edge→EL, qolgani→CS | S | M |
| CL-006 | Operatsiyalar jadvali qatori | CL qatori: tur, kod, nom, Ст. м-ла, Ст. оп-и, П-ть, Н.Стр; nusxa, tartib, o'chirish, saralash | umumiy jadval | 🟡 | `OperationsTable.tsx`; CL narxi hisoblanmaydi (`calc.recalc_project` CL ni bilmaydi) | S | H |
| CL-007 | «Общие действия»: bir xil operatsiyalarni birlashtirish | Bir xil (tur, kod, nom) CS/CL/EL operatsiyalari bitta bo'ladi | — | ✅ | `main.py:1007` CL ni biladi | S | L |
| CL-008 | Detallarni CS↔CL ga ko'chirish (Ctrl+M) | Tanlangan detallar boshqa kroy operatsiyasiga o'tadi | — | 🟡 | `main.py:1228` CL ga ruxsat bor; eni/kromka semantikasi tekshirilmagan | S | L |
| CL-009 | Mahsulot narxi ulushi | CL narxi mahsulotlar «Ст. м-ла/Ст. оп-и» ga detal uzunligi × soni ulushi bo'yicha taqsimlanadi | — | ❌ | B10; `calc.py:584` CS/EL/GR/XNC | S | M |
| CL-010 | «Требование на склад»: CL qatori | Profil nomi, birlik «полоса» (yoki m), soni; chopda «Длина реза» ixtiyoriy | — | ❌ | B11; `calc.warehouse_request` faqat CS/EL | S | M |

### 2.2. Параметры материала

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-011 | Ширина | Polosa eni (mm). Hamma CL detalning eni shu; kartada polosa balandligi, `S` ko'rsatkichi, kesim uzunligi (LT) hisobi shundan | yordamda standart yo'q; rasmlarda 360 / 500 / 600; taklif 100 | ❌ | Y:cl/Параметры материала; R1, R4, R5 | S | H |
| CL-012 | Толщина | Polosa qalinligi — faqat kratnost (paket) hisobi va tovar ma'lumoti uchun | taklif 16 mm | ❌ | Y:cl; R6 | S | H |

### 2.3. Параметры раскроя

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-013 | Толщина пилы | Har bir kesim kengligi; aniqlik 0.0001; qat'iy **> 0** (CS da 0 mumkin) | taklif 3 mm | 🟡 | Y:cl; `models.py:218` kerf `ge=0` — CL uchun `gt=0` kerak | S | H |
| CL-014 | Торцовка | Polosa **boshidan** kesib tashlanadigan chet; qiymat propilni o'z ichiga olmaydi; 0 → torsovka kesimi ham, uning propili ham yo'q; `≥ 0`, aniqlik 0.0001 | taklif 0 (misolda 20) | 🟡 | Y:cl; R1; B3 (CS semantikasi boshqa) | S | H |
| CL-015 | «Минимальный отступ в конце» | Polosa **oxirida** qoldiriladigan minimal chet; havola/tugma orqali alohida beriladi; berilmasa torsovka qiymati olinadi | standart = Торцовка | 🟡 | Y:cl; D5 (CS dagi shu havola); `models.py:223` | S | H |
| CL-016 | Foydali uzunlik | `U = L − (T_boshi + k) − (T_oxiri + k)`; 0 bo'lgan tomonda `T+k` qo'shilmaydi | tekshiruv: 1600, 20, 10 → 1540 | ❌ | Y:cl; R1; L #13 (hujjatda bor, kodda va testda yo'q) | S | H |
| CL-017 | Высота пакета | Arra ko'tarilishining maksimal balandligi (paket chegarasi) | taklif 40 mm | 🟡 | Y:cl; R6; `models.py:229` (CS) | S | M |
| CL-018 | Кратность | Bir vaqtda kesiladigan polosalar soni = ⌊paket balandligi / qalinlik⌋; faqat o'qish | 40/16 → 2 | 🟡 | Y:cl; B9; `calc.py:111` (CS) | S | M |
| CL-019 | Процент заполнения для кратности | Polosa to'ldirilishi shu foizdan ≥ bo'lsa, optimizator bir xil polosalarni paketga birlashtirishga intiladi (kichik to'ldirilganlar uchun majburlamaydi) | taklif 90 % | 🟡 | Y:cl; `models.py:231`; `optimizer.py:1377` (CS) | M | M |

### 2.4. Отход (qoldiq)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-020 | Мин. размер отхода | Shundan qisqa qoldiq bo'lak otxod sifatida jadvalga yozilmaydi (oddiy chiqindi) | taklif 100 mm; birlik savol (Q3) | ❌ | Y:cl/Отход; G4 `cMinDimRegWaste1` | S | H |
| CL-021 | Длина делового отхода | Shundan uzun otxod — «деловой»: omborga yoziladi, material sarfiga kirmaydi | taklif 500 mm; G4 da birlik «m» deyilgan | ❌ | Y:cl; G4 `cBusinessWaste` | S | H |
| CL-022 | Торцовка отходов | ✓: otxod uzunligi torsovkagacha (80); ☐: otxod oxirgi propil va torsovka zonasini ham oladi (110) va oxirgi torsovka kesimi qilinmaydi | R2 misoli: 80 / 110 | 🟡 | Y:cl; R2; B4 `remnant_size_incl_trim` (2D analogi) | S | H |
| CL-023 | Otxod turlari | Jadvalda uch tur: polosa / отход / деловой отход; kichik bo'laklar jadvalga kirmaydi | — | 🟡 | Y:cl/Полосы и отходы; `models.py:502` `Offcut.business` | S | H |

### 2.5. Стоимость

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-024 | Цена материала | 1 metr polosa narxi | `price` ≥ 0 | ❌ | Y:cl/Стоимость; `models.py:192` (CS narxi 1 list/1 m²) | S | H |
| CL-025 | Narx birligi «по полосам» + yaxlitlash | Bizning K1 va `.project` (G4) da polosa bo'yicha narx va yaxlitlash kodlari bor (11 butun; 32/33/34 uzunlik bo'yicha 1/2, 1/3, 1/4) — CL yordam sahifasida **yo'q** | kod 11/32/33/34 | ❓ | K1; G4 `cCostByItem(Round)` | M | L |
| CL-026 | Расчетный процент заполнения | Kroygacha taxminiy sarf uchun foiz | taklif 90 % | 🟡 | Y:cl; `models.py:194` (CS) | S | H |
| CL-027 | Расход материала (kroygacha) | `Σ detal uzunligi × (2 − p/100)` (m) | misol: 10 m, 90 % → 11 m | ❌ | Y:cl; B5 (CS: maydon) | S | H |
| CL-028 | Количество материала | Расход − деловой otxod uzunligi. Kroydan keyin: ishlatilgan polosalar uzunligi − деловой otxodlar | m (taklif) | ❌ | Y:cl; B5 | S | H |
| CL-029 | Стоимость материала | `Цена × Расход (Количество)` | — | ❌ | Y:cl | S | H |
| CL-030 | Расчет стоимости операции по | To'rt asos: «Длине реза с торцовкой» · «Длине реза без торцовки» · «Длине материала» (delovoy otxodsiz) · «Длине деталей» | taklif: 1-asos; G4 `cCostType` 0..3 | 🟡 | Y:cl; G4; `models.py:87` (CS ning boshqa 4 asosi) | S | H |
| CL-031 | Цена операции | Tanlangan asos birligiga narx; yorlig'ida «(метр/рез)» | birlik savol (Q5) | 🟡 | Y:cl; `models.py:198` | S | H |
| CL-032 | Стоимость операции | `asos × narx`; kroygacha taxminiy | `cost_operation` | ❌ | Y:cl; `models.py:416` maydon bor, hisob yo'q | S | H |

### 2.6. Детали (jadval va kiritish)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-033 | Detallar CRUD (API) | Detal qo'shish/tahrir/o'chirish/ko'chirish/saralash — operatsiya turidan mustaqil | — | ✅ | `main.py:1089–1288` (`op.parts`) | S | H |
| CL-034 | Jadval ustunlari | `Д-на · Кол · ОВ · ОН · ОЛ · ОП · Наименование · ОК · ИК · Ост` (eni ustuni yo'q) | ustun profili Ctrl+P (D0) | ❌ | Y:cl/Детали; K1 | M | H |
| CL-035 | Д-на | Detal uzunligi; 0 = to'ldirilmagan qator (kroyga kirmaydi) | mm, 0.0001 | 🟡 | `models.py:121` | S | H |
| CL-036 | Кол | Detal soni | 0…100000 | ✅ | `models.py:123`; `calc.effective_qty` | S | H |
| CL-037 | ОВ / ОН | Detalning uzun tomonlaridagi kromka (EL ga havola); Space — navbatdagi EL, Shift+Space — hamma tomon | bo'sh→A→B→… | 🟡 | Y:cl; R7; D6; `models.py:127` | S | H |
| CL-038 | ОЛ / ОП | Detalning uchlaridagi (eni bo'ylab) kromka; uzunlikni kromka qalinligiga kamaytiradi | uzunlik = polosa eni | 🟡 | Y:cl; R7; `calc.py:389` da eni 0 → ОЛ/ОП kromka metri 0 chiqadi (xato) | S | M |
| CL-039 | Наименование va belgilar | Nomga `=` (pazovanie), `*` (freza/radius), `%` (parmalash) belgisi qo'yiladi | — | 🟡 | Y:cl; B12 | S | M |
| CL-040 | ОК / ИК / Ост | ОК = Кол × mahsulot soni; ИК — kroyga kirgan; Ост — kirmay qolgan | ИК + Ост = ОК − МК | ✅ | Y:cl; B8; `calc._account` | S | H |
| CL-041 | O'lcham kiritish rejimlari | «заготовка / деталь / после прифуговки» va 4 o'lcham (pilniy) — CL da ОЛ/ОП kromka qalinligi va prifugovka uzunlikka ta'sir qiladimi — yordam aytmaydi | ❓ | ❓ | B2; `sizes.py`; Q8 | M | M |
| CL-042 | Ishlov pripuski (▽△▷◁) | Uzunlikka (▷◁) pripusk qo'shiladimi — CL uchun ❓ | — | ❓ | B2 | S | L |
| CL-043 | Detal xossalari (Ctrl+Space) | 4 o'lcham, kromka/paz/XNC/sirt, mahsulot (CL da «Ширина» maydoni yashirin yoki faqat o'qish) | — | 🟡 | Y:cl/Действия; `PartDialogs.tsx` (CS) | M | M |
| CL-044 | Excel / OpenOffice dan Ctrl+V | Ustun tartibi `Д-на, Кол, ОВ, ОН, ОЛ, ОП, Наименование`; noma'lum kromka nomi → yangi EL operatsiyasi | — | 🟡 | Y:cl; G6; `importers.py` (CS tartibi, yangi EL avtomatik ✅) | S | H |
| CL-045 | Jadval navigatsiyasi | Tab/Enter — o'ngga va oxirida keyingi qator (jadval oxirida yangi); Shift+Tab/Enter — chapga; Ctrl+Tab/Enter — pastga qator boshiga; Home/↑/↓/End | — | 🟡 | Y:cl; E3; `shared/grid`, `hotkeys.ts` | S | H |
| CL-046 | Qator amallari | Ctrl+PgUp (joriydan oldin qo'shish), Ctrl+PgDn (oxiriga), Del / Shift+Del, Ctrl+↑/↓ (ko'chirish) | — | 🟡 | Y:cl; E3 | S | H |
| CL-047 | Tekshiruv: detal sig'maydi | Detal foydali uzunlikdan uzun yoki eni polosadan katta bo'lsa — ogohlantirish, kroyga kirmaydi | taklif (yordamda yo'q) | ❌ | §3.8 | S | H |
| CL-048 | Jami uzunlik va soni | Jadval ostida «Длина: X м», «Кол-во: N шт» (CS dagi Площадь/Кол-во analogi) | taklif | ❌ | D6 | S | L |
| CL-049 | Ustun profili (Ctrl+P), saralash, klon, guruhli amallar | CS detallar jadvali kabi | — | 🟡 | D0 §5–6; `ColumnSettings.tsx`; API ✅, CL UI ❌ | S | L |
| CL-050 | Min. detal uzunligi | `.project` da `cMinDimDetail` bor, CL yordami parametr sifatida ko'rsatmaydi | ❓ | ❓ | G4; Q9 | S | L |

### 2.7. Полосы и отходы

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-051 | Jadval ustunlari | `№ · Наименование (tur) · Длина · Ширина · Площадь · Количество · Исп. Кол-во · Остаток`; Площадь = Д × Ш (hisoblanadi) | — | 🟡 | Y:cl/Полосы и отходы; `CsSheets.tsx` | M | H |
| CL-052 | Bir nechta polosa uzunligi | Har qator — polosa turi: uzunlik, eni, soni (masalan 6000 va 3000) | taklif: katalogdagi standart uzunlik | 🟡 | `models.py:161` `StockSheet` | S | H |
| CL-053 | Cheksiz son | CS da `10000` = cheksiz; CL da shu qoida ❓ | taklif 10000 | ❓ | `models.py:165`; Q17 | S | H |
| CL-054 | Polosalar ustuvorligi | Ro'yxat tartibi = ishlatish tartibi; yuklashda soni bo'yicha o'sish (CS da jonli tekshirilgan) — CL da ❓ | taklif: CS bilan bir xil | ❓ | memory `giblab-sheet-priority`; Q2 | S | H |
| CL-055 | Natija qatorlari | Kroydan keyin jadvalga отход va деловой отход qatorlari qo'shiladi: Количество — natijadagi soni; Исп. Кол-во — mijoz olib ketadigan bo'laklar | — | 🟡 | Y:cl; `CsSheets.tsx:74` | S | M |
| CL-056 | Остаток | `Количество − Исп. Кол-во` | — | ✅ | Y:cl; `StockSheet.used_qty` | S | M |
| CL-057 | Qator amallari | Insert/Add/Delete/↑/↓ (Ctrl+PgUp, Ctrl+PgDn, Del, Ctrl+↑/↓) | — | 🟡 | Y:cl; E3 | S | H |
| CL-058 | Ombor qoldig'ini qo'shish | Omborning погонажный qoldiqlari (uzunlik × eni × soni) ro'yxatdan tanlanib qo'shiladi | — | 🟡 | Y:ost (sheet=false); `main.py:1368` `_need_cs` | S | M |
| CL-059 | Polosa uchun alohida torsovka | CS jadvalida ТД/ТШ bor; CL jadvalida ustun ko'rsatilmagan, lekin CLE da «Торцовка листа» bor | ❓ | ❓ | Y:cle; Q7 | M | L |

### 2.8. Раскрой (karta ekrani)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-060 | «Раскроить» | Kroyni hisoblash; natija — kartalar ro'yxati (bo'sh holatda markazda tugma) | — | ❌ | Y:cl/Раскрой; `main.py:1410` `_need_cs` to'sadi | L | H |
| CL-061 | Karta chizmasi | Polosa gorizontal: detallar to'q sariq (ichida №, pastida uzunlik), otxod ko'k (raqami), chet/torsovka kulrang, propil — qora chiziq; polosa balandligi eniga mutanosib | — | ❌ | R1, R2, R4 | M | H |
| CL-062 | Masshtab va aylantirish | Sichqoncha g'ildiragi — masshtab; gorizontal/vertikal scroll | — | 🟡 | Y:cl Рис.5; `MapView.tsx` (2D) | S | M |
| CL-063 | Detalni tanlash | Bosilgan detal va uning barcha nusxalari to'qroq rangda | — | 🟡 | R4; D8 | S | M |
| CL-064 | Statistika qatori | `№` karta/jami · `S` uzunlik/eni · `C` polosalar soni karta/jami · `Cp` detallar karta/jami · `LT` kesim uzunligi karta/jami (m) · `F` to'ldirish % karta/jami | R4: 3/8 · 3200/600 · 1/17 · 5/80 · 3.6/58.2 · 96.88%/97.81% | 🟡 | Y:cl; R4; A_GLOSSARY | S | H |
| CL-065 | LT formulasi | Kesimlar soni × polosa eni (m). R4: 6 × 0.6 = 3.6; jami 97 × 0.6 = 58.2 (97 = 80 detal + 17 polosa). Otxod bo'lagi uchun qo'shimcha kesim hisoblanadimi — aniq emas | — | ❌ | R4-hisob; Q5, Q6 | S | H |
| CL-066 | F formulasi | Σ detal uzunligi ÷ polosa uzunligi (3100/3200 = 96.88 %); torsovka va propil «to'lmagan» hisoblanadi | — | ❌ | R4-hisob | S | H |
| CL-067 | Miniatyuralar paneli | O'ngda har karta kichik chizmasi + `№:1 S:3200/600 C:5` (C — shu kartadagi polosalar soni); tanlangani ko'k fonda | — | 🟡 | R4; D8 | S | M |
| CL-068 | «Таблица команд» | Ustunlar `Кд · Р · К · Д`: Tx torsovka, Cx oddiy kesim, Px detalni ajratuvchi yakuniy kesim, Wx otxod; x — daraja (burilish raqami). CL da daraja har doim 1 mi, C ishlatiladimi — ❓ | — | 🟡 | Y:cl; C5 (CS); Q6 | M | H |
| CL-069 | Panel almashtirgich | Miniatyuralar paneli ↔ buyruqlar jadvali | — | 🟡 | R4 | S | L |
| CL-070 | Karta navigatsiyasi | Birinchi / oldingi / keyingi / oxirgi karta tugmalari (Home / ↑ / ↓ / End) | — | 🟡 | Y:cl; E5 | S | M |
| CL-071 | Karta izohi | Tugma orqali karta uchun izoh (F2); chopda ko'rinadi | — | 🟡 | R4; `models.py:536` `CutMap.comment` | S | L |
| CL-072 | Постпроцессор | Kroyni arra stanogi formatiga o'tkazish tugmasi | format foydalanuvchidan | 🟡 | Y:cl; `postprocessors.py:13` (CS konteksti) | M | L |
| CL-073 | Удаление раскроя | Kroyni o'chirish; omborga yozilgan qoldiqlar bekor qilinadi | — | 🟡 | `main.py:1438` generic ✅, UI ❌ | S | H |
| CL-074 | Редактирование раскроя | CLE oynasini ochish | §2.10 | ❌ | Y:cle | S | M |
| CL-075 | «До кроить» | CL yordamida tilga olinmagan | ❓ | ❓ | D8 (CS); Q11 | M | L |
| CL-076 | Takrorlanuvchi karta | Bir xil sxemali polosalar bitta kartada, `C` — nusxalar soni | — | 🟡 | R4; `CutMap.copies` | S | H |
| CL-077 | Paketlar soni | `⌈C / kratnost⌉` arra sikllari | — | 🟡 | R6; `calc._packets` | S | M |
| CL-078 | Otxod raqamlash | Otxod/деловой kartada ko'k, raqami; buyruqlarda `W` qatori `Д` ustunida | — | 🟡 | R1, R2; `Offcut.number` | S | M |

### 2.9. Optimizatsiya (algoritm xususiyatlari)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-079 | 1D kesish yechimi | Barcha detal nusxalari (ОК − МК) polosalarga joylanadi; detal bo'linmaydi, aylantirilmaydi | — | ❌ | Y:cl; K1 aytgan `cl_optimizer.py` kodda **yo'q** (`services/` da yo'q) | L | H |
| CL-080 | Propil hisobi | Qo'shni ikki bo'lak orasida bitta propil | — | ❌ | R1 | S | H |
| CL-081 | Torsovka hisobi | Boshida va oxirida (oxirgisi — «минимальный отступ») | — | ❌ | R1 | S | H |
| CL-082 | Ko'p turdagi, cheklangan polosa | Har turdan faqat jadvaldagi soncha; tur ro'yxat tartibida ishlatiladi | — | ❌ | Y:cl/Полосы | M | H |
| CL-083 | Qoldiq-polosalar birinchi | Ombor qoldiqlari (cheklangan son) avval ishlatiladi | CS da tasdiqlangan | ❌ | Y:ost; memory `giblab-sheet-priority` | M | M |
| CL-084 | Деловой otxod sarfdan ayiriladi | Qayta ishlatiladigan otxod material sarfiga/narxga kirmaydi | — | ❌ | Y:cl/Стоимость | S | H |
| CL-085 | Paketlash afzalligi | To'ldirilishi ≥ foiz bo'lgan sxemalar bir xil nusxalarda paketga yig'iladi | — | ❌ | Y:cl | M | M |
| CL-086 | Sig'maydigan detallar | Hech bir polosaga sig'masa — «невместившиеся» ro'yxati va ogohlantirish | — | ❌ | R5 («невместившихся деталей»); `calc.py:174–196` (CS dagi `_small_warning/_bad_warning`) | S | H |
| CL-087 | Sifat rejimi | Tez / Standart / Maksimal vaqt-sifat kelishuvi | CL yordamida yo'q | 🟡 | `models.py:232` (CS) | S | L |
| CL-088 | Natija tekshiruvi (validate) | Har natija mustaqil tekshiriladi (propil, torsovka, soni, polosa chegarasi) | — | ❌ | `validate.py` (CS), CLAUDE.md qoida 8 | M | H |

### 2.10. CLE — Редактирование погонажного раскроя

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-089 | CLE oynasi | Chapda detallar jadvali, o'ngda kartalar; qo'lda kroy tuzish/tuzatish | — | ❌ | Y:cle; `CutEditor.tsx` (CS, 2D) | L | M |
| CL-090 | Jadval ustunlari | `Длина · Ширина · Кол-во · Исп. Кол. · Остаток · Ткт · Наименование`; «Ткт» — aylantirmaslik belgisi (CL da ma'nosi ❓, CS dan qolgan bo'lishi mumkin) | — | ❌ | Y:cle; Q13 | S | M |
| CL-091 | Полноэкранный режим | To'liq ekran | F9 | ❌ | Y:cle | S | L |
| CL-092 | Отменить / Вернуть | Tahrir bosqichlarini qaytarish/takrorlash | Ctrl+Z / Ctrl+Y | 🟡 | Y:cle; `CutEditor.tsx` (CS) | M | M |
| CL-093 | Добавить карту кроя | Yangi bo'sh karta | — | ❌ | Y:cle | S | M |
| CL-094 | Удалить карту кроя | Kartani o'chirish (detallar «Остаток» ga qaytadi) | — | ❌ | Y:cle | S | M |
| CL-095 | Количество листов | Kartadagi polosa nusxalari soni (C) ni belgilash | — | ❌ | Y:cle | S | M |
| CL-096 | Торцовка листа | Karta/polosa uchun torsovkani o'zgartirish — qaysi qiymat ekani ❓ | — | ❓ | Y:cle; Q7 | M | L |
| CL-097 | Detalni boshiga / oxiriga ko'chirish | Tanlangan detal polosa boshiga/oxiriga | Ctrl+← / Ctrl+→ | ❌ | Y:cle | S | L |
| CL-098 | Tanlangan detalni o'chirish | Polosadan olib tashlash | Del, o'ng tugma | ❌ | Y:cle | S | M |
| CL-099 | Nol qoldiqli detallarni filtrlash | Jadvalda «Остаток = 0» larni yashirish | Ctrl+F | ❌ | Y:cle; E6 | S | L |
| CL-100 | Kartani ko'chirish | Kartani ro'yxatda yuqoriga/pastga | Ctrl+↑ / Ctrl+↓ | ❌ | Y:cle | S | L |
| CL-101 | Karta navigatsiyasi | Birinchi/oldingi/keyingi/oxirgi | Home / ↑ / ↓ / End | ❌ | Y:cle | S | L |
| CL-102 | Detalni tanlash | Bosish — bitta; Ctrl+bosish — bir nechta | — | ❌ | Y:cle | S | M |
| CL-103 | Tahrir rejimi | Shift+bosish: tanlangan detalni polosaga joylash | — | ❌ | Y:cle | M | M |
| CL-104 | Aylantirish bilan tahrir | Shift+Ctrl/Alt+bosish — «teksturasi bo'lmasa detalni burib». 1D da ma'nosiz (CS dan nusxa bo'lishi mumkin) | ❓ | ❓ | Y:cle; Q13 | S | L |
| CL-105 | Ko'p marta joylash | Shift+A+bosish — ketma-ket bir necha nusxa | — | ❌ | Y:cle | S | L |
| CL-106 | Tekshiruv va saqlash | Tahrirdan keyin sig'ish tekshiruvi (propil, torsovka), natijani saqlash, statistikani qayta hisoblash | — | ❌ | `editor.rebuild`, `PUT result` (CS, `_need_cs`) | M | M |

### 2.11. Chop (hisobot)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-107 | (CL) chop sozlamalari | «Печать отчета» chap menyusi → «Настройки печати операций» → (CL) Погонажный раскрой: 7 ta belgi | — | ❌ | Y:cl/Печать; R5; `models.py:572` faqat `cs_*` | M | M |
| CL-108 | Печать заголовка | Operatsiya sarlavhasi (material, parametrlar) | ✓ (R5) | ❌ | R5 | S | M |
| CL-109 | Печать деталей | Detallar jadvali (`№ · Длина · Ширина · …`; eni = polosa eni) | ✓ | ❌ | R5 | S | M |
| CL-110 | Группировать детали по изделия | Detallar mahsulotlar bo'yicha guruhlanadi | ☐ | ❌ | R5 | S | L |
| CL-111 | Печать невместившихся деталей | Sig'magan detallar bo'limi | ✓ | ❌ | R5 | S | M |
| CL-112 | Печать полос | Ishlatilgan polosalar jadvali | ✓ | ❌ | R5 | S | M |
| CL-113 | Печать отходов | Otxod/qoldiqlar jadvali | ✓ | ❌ | R5 | S | M |
| CL-114 | Печать карт раскроев | Kartalar chizmalari; sarlavha `№:1/3 S:2400/500 C:1/3 Cp:6/21 …` | ✓ | ❌ | R5 | M | M |
| CL-115 | Chop profillari | «Профиль» tanlash va ✚ ✎ ✕ | — | 🟡 | R5; D11 | S | L |

### 2.12. Qoldiqlar, katalog, boshqa operatsiyalar va integratsiya

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | M | U |
|---|---|---|---|---|---|---|---|
| CL-116 | Qoldiqlar almashinuvi | Ombor/ERP dan material kodi bo'yicha polosa-qoldiqlarni yuklash; kroyda tanlanganini hisobot qilish; yangi qoldiqlarni omborga yozish; погонажный/листовой — bayroq (`sheet=false`) | bizda MES REST (1C o'rniga) | 🟡 | Y:ost; `warehouse.py` (`assert CS`), `api_extra.py` | M | M |
| CL-117 | Qoldiq yozuvi | `id, uzunlik, eni, soni[, izoh]` | — | 🟡 | Y:ost; `db.py:118` `RemnantRow` (`thickness` bor, chiziqli bayroq yo'q) | S | M |
| CL-118 | Omborga yozish maydonlari | loyihadagi id, tashqi id, tur (polosa/qoldiq), деловой, uzunlik, eni, boshlang'ich soni, ishlatilgan soni | — | 🟡 | Y:ost | S | M |
| CL-119 | Qoldiqni tasdiqlash/bekor qilish | Commit/rollback, ombor yaxlitligi | — | 🟡 | `warehouse.py` | S | M |
| CL-120 | Kromka hisobi (EL) | CL detallarining ОВ/ОН/ОЛ/ОП kromkasi EL operatsiyasi hisobiga kiradi | ОЛ/ОП uzunligi = polosa eni | 🟡 | B6; `calc.py:381` CL ni sanaydi, eni 0 muammosi | S | M |
| CL-121 | Paz hisobi (GR) | CL detallaridagi paz EL kabi hisobga kiradi | — | 🟡 | `calc.py:436`; eni 0 muammosi | S | L |
| CL-122 | XNC bog'lash | Nomdagi `%`/`*` va XNC dasturi CL detaliga — qo'llanishi ❓ | — | ❓ | `main.py:1318` (CS qalinligi) | S | L |
| CL-123 | `.project` importi | CL operatsiya: tool1, cTrimW, cTrimEW, cFillRep, cCostType, cMinDimRegWaste1, cBusinessWaste, cTrimWaster … | — | ❌ | G4; `legacy_project.py:407` o'tkazib yuboradi | M | L |
| CL-124 | MES hodisasi | `cutting.done` CL uchun (polosalar soni, uzunlik, qoldiq) | — | ❌ | F4; `main.py:1419` | S | M |
| CL-125 | Etiketkalar | Detal/polosa etiketkasi (QR) | CL yordamida yo'q | ❓ | K5 | M | L |

### 2.13. CL da kerak bo'lmaydigan CS funksiyalari (ataylab tushirilgan)

Birinchi kesish yo'nalishi, burilishlar soni, «Сложные полосы», polosa/ustun saralash, min/max polosa eni, max polosa
uzunligi, detal teksturasi va aylanishi (kerak bo'lsa faqat CLE da ❓), detallarni blokka guruhlash, `kerf_group`,
«Мин. размер детали»-ning ikki o'lchamli ma'nosi. Bular CL yordamida ham yo'q. Shuningdek CL yordamida **yo'q**:
burchak/qiyshiq kesim (faqat 90°), kesish usullari tanlash, «kombinatsiya»/qidiruv chuqurligi parametri, narxni polosa
ichidagi bo'lak bo'yicha hisoblash. Agar korxonaga plintus/profilda 45° kesim kerak bo'lsa — bu GibLab'da ham yo'q yangi
funksiya bo'ladi (Q23).

### 2.14. Tezkor tugmalar (yig'ma; to'liq ro'yxat `E_HOTKEYS.md` ga qo'shiladi)

| Kontekst | Tugma | Amal |
|---|---|---|
| Detallar / Polosalar jadvali | Ctrl+Space | Свойства (faqat detallar) |
| | Space / Shift+Space | kromkani almashtirish / perimetr (ОВ ОН ОЛ ОП katagida) |
| | Ctrl+PgUp / Ctrl+PgDn | qator qo'shish (joriydan oldin) / oxiriga |
| | Del, Shift+Del | o'chirish |
| | Ctrl+↑ / Ctrl+↓ | qatorni ko'chirish |
| | Tab, Enter / Shift+Tab, Shift+Enter | o'ngga (oxirida yangi qator) / chapga |
| | Ctrl+Tab, Ctrl+Enter | pastga, qator boshiga |
| | Home / ↑ / ↓ / End | birinchi / oldingi / keyingi / oxirgi qator |
| | Ctrl+V | Excel dan qo'yish (faqat Detallar) |
| Раскрой | Home / ↑ / ↓ / End | birinchi / oldingi / keyingi / oxirgi karta |
| | F2 | karta izohi |
| | g'ildirak | masshtab |
| CLE | F9 | to'liq ekran |
| | Ctrl+Z / Ctrl+Y | orqaga / oldinga |
| | Ctrl+← / Ctrl+→ | detalni boshiga / oxiriga |
| | Del, o'ng tugma | tanlangan detalni o'chirish |
| | Ctrl+F | nol qoldiqli detallarni filtrlash |
| | Ctrl+↑ / Ctrl+↓ | kartani yuqoriga / pastga |
| | Home / ↑ / ↓ / End | karta navigatsiyasi |
| | chap / Ctrl+chap | detalni tanlash / ko'p tanlash |
| | Shift+chap | tahrir rejimi |
| | Shift+Ctrl(Alt)+chap | tahrir + aylantirish (CL da ❓) |
| | Shift+A+chap | ko'p marta joylash |

### 2.15. Yig'ma

Jami **125** funksiya: ✅ 5 · 🟡 53 · ❌ 55 · ❓ 12. Ustuvorlik: H 51 · M 46 · L 28. Murakkablik: S 98 · M 24 · L 3.
H ustuvorlikdan ❌ 24, 🟡 22, ✅ 3, ❓ 2 — MVP ning asosiy ish hajmi shu 51 ta (asosan parametrlar, jadval, optimizator, karta, narx).
✅ larning hammasi — operatsiya turidan mustaqil backend primitivlari (detallar CRUD, ОК/ИК/Ост, polosa «Остаток», operatsiyalarni
birlashtirish); CL uchun ko'rinadigan UI hozircha **yo'q** (turlar dialogida «later» bilan o'chirilgan).

---

## 3. Algoritmik spetsifikatsiya (1D cutting stock)

### 3.1. GibLab nimani aytadi (kafolatlar) va nimani aytmaydi

**Yordam kafolatlagan (tasdiqlangan):**
1. Har ikki qo'shni bo'lak orasida 1 propil; boshida torsovka + propil; oxirida «минимальный отступ» + propil (R1).
2. Torsovka = 0 bo'lsa o'sha tomonda kesim yo'q (propil ham qo'shilmaydi) (Y:cl/Параметры раскроя).
3. Qoldiq tasnifi: `Мин. размер отхода` dan kichik — hisobga olinmaydi; undan ≥ — **отход**; `Длина делового отхода` dan ≥ — **деловой отход** (sarfga kirmaydi); `Торцовка отходов` otxod o'lchamini belgilaydi (R2).
4. Polosalar jadvali: tur, uzunlik, eni, soni; ishlatilganlar `Исп. Кол-во`; otxodlar natijada jadvalga qo'shiladi.
5. Paketlash: kratnost = ⌊paket / qalinlik⌋; foiz ≥ chegara bo'lsa paketga birlashtirishga intiladi.
6. Narx: material (m), operatsiya (4 asos); kroygacha taxmin `Σ × (2 − p/100)`.

**Yordam aytmaydi (optimizatsiya mazmuni):** maqsad funksiya, polosa tanlash tartibi, ustuvorlik, detallarni polosa ichida
tartiblash, vaqt/sifat rejimi, tengsizlikda qaror qoidasi. Shuning uchun quyidagi §3.3–3.7 — **bizning talablarimiz**
(CS tajribasi va 1D nazariyasiga asoslangan), GibLab xulq-atvori emas; Q1–Q2 javoblari kelganda tuzatiladi.

### 3.2. Kirish

```
items   : har detal NUSXASI (ОК − МК marta): uid, part_id, p = pilniy uzunlik (sizes.compute_sizes → saw[0], eni = op.cl.width)
stock   : polosa turlari ro'yxat tartibida: L, w, qty (10000 = cheksiz), source_remnant_id?, is_remnant
params  : k (propil > 0), T_boshi, T_oxiri (None → T_boshi), waste_min, business_min, waste_incl_trim,
          pack_height, thickness, fill_packet, quality
```
Tozalash: `p ≤ 0` yoki bir tomoni 0 → «bad» (jim emas, ogohlantirish, CS dagi `warn_bad_size` kabi); `min_part_len`
dan kichik → «small» (agar parametr qabul qilinsa, Q9); hech bir polosaga sig'maydigan (`p > U_max`) → `unplaced` + ogohlantirish.

### 3.3. Geometriya va qoidalar (har polosa uchun)

Belgilar: `L` polosa uzunligi, `k` propil, `T_s` boshidagi torsovka, `T_e = oxirgi otstup ?? T_s`, `p_i` — joylashgan detallar.
```
a_s = (T_s > 0) ? T_s + k : 0          a_e = (T_e > 0) ? T_e + k : 0
U   = L − a_s − a_e                    # foydali uzunlik
R   = U − Σp_i − (n−1)·k   ≥ 0        # sig'ish sharti  ⇔  Σ(p_i + k) ≤ U + k   (oxirgi propil «bepul»: u oxirgi torsovka kesimi)
```
Bu bir o'lchovli «og'irlik = p_i + k, sig'im = U + k» ko'rinishidagi to'plam-sumka masalasi.

**Oxiridagi qoldiq.** `R = 0` — aniq sig'di (oxirgi detal kesimi = oxirgi torsovka kesimi). `0 < R ≤ k` — otxod bo'lagi yo'q,
qoldiq oxirgi torsovkaga qo'shiladi. `R > k` — otxod bo'lagi `W = R − k`.
`W_xom = W + (T_e > 0 ? k + T_e : 0)` (= `R + T_e`) — `Торцовка отходов` ☐ bo'lganda otxod uzunligi (R2: 80 → 110).
Tasnif: `W_hisob = waste_incl_trim ? W : W_xom`; `W_hisob < waste_min` → oddiy chiqindi (jadvalga yozilmaydi, ajratuvchi kesim
qilinmaydi — taklif, Q6); `≥ waste_min` → **отход**; `≥ business_min` → **деловой отход**. Omborga yoziladigan o'lcham — `W_xom`
(polosa oxirigacha, `Offcut.raw_length` analogi).

**Kesimlar soni** (`cuts_count`, LT hisobi uchun): `[T_s>0] + (n − 1) + c_oxir`, bunda `T_e>0` bo'lsa `c_oxir = 1 + [otxod bo'lagi
bor ∧ waste_incl_trim ✓ ∧ W ≥ waste_min]`, `T_e = 0` bo'lsa `c_oxir = [R > 0]`. (Tekshiruv: R1 → 1+2+2 = 5; R4 3-karta → 1+4+1 = 6 ✓.)
«Без торцовки» asosida: `cuts − [T_s>0] − [T_e>0]`.

**Statistika (polosa/karta/jami):**
```
F          = Σp_i / L · 100                         # karta; jami: Σ(copies·Σp) / Σ(copies·L)
cut_len_m  = cuts_count · w / 1000                   # karta (1 polosa); jami = Σ copies · cut_len_m
packs      = ⌈copies / kratnost⌉,  kratnost = max(1, ⌊pack_height / thickness⌋)
material_qty_m   = Σ copies·L − Σ copies·W_delovoy      (m, /1000)
estimate_m       = Σ(p·ОК_eff) · (2 − est_fill/100)      (kroygacha, m)
cost_material    = price · (material_qty_m yoki estimate_m)
cost_operation   = op_price · asos;  asos ∈ {kesim uzunligi (torsovka bilan/siz), material uzunligi (delovoysiz), detallar uzunligi}
```

### 3.4. Maqsad funksiya (taklif, leksikografik)

1. **Hamma detal joylansin** (`unplaced` minimal; ideal 0).
2. **Sarflangan material minimal:** `Σ copies·L − Σ delovoy otxod` (ya'ni «sarf»; delovoy qoldiq «bepul»).
3. Polosalar soni minimal (ro'yxat ustuvorligi saqlanib).
4. Turli sxemalar (kartalar) soni minimal — bir xil sxema ko'p nusxada (paketga qulay; `prefer_big_pack` analogi).
5. Kesimlar soni / kesim uzunligi minimal.
6. Qoldiq bitta uzun bo'lakda jamlansin (oxirgi polosada, delovoy bo'lishi uchun).
7. To'ldirilishi ≥ `fill_packet` sxemalar uchun nusxalar soni kratnostga bo'linsin (imkon bo'lsa).
Polosa ichidagi tartib: uzundan qisqaga (taklif; Q10).

### 3.5. Algoritm (amalga oshirish tavsiyasi)

1. **Normallashtirish:** o'lchamlar butun birlikka (0.01 mm) keltiriladi; teng uzunliklar guruhlanadi (`d_i`), tipik: ≤ 300 xil uzunlik, ≤ 20 000 nusxa (`MEBELIX_MAX_CUT_ITEMS` chegarasi saqlanadi).
2. **Quyi chegara:** `LB = ⌈Σ(p_i + k)·d_i / (U + k)⌉` (eng uzun polosa bo'yicha) — sifat o'lchovi va to'xtash sharti.
3. **Quruvchi bosqich (ketma-ket evristika):** polosa turlari ro'yxat tartibida; har tur uchun takroran **chegaralangan sumka (bounded knapsack) DP** — og'irlik `p_i + k`, sig'im `U + k`, maqsad `Σp_i` maksimal, teng bo'lsa nusxa soni kam; topilgan sxema qolgan talab yetguncha **c marta** takrorlanadi (karta nusxalari). Cheksiz oxirgi turda — shu davom etadi. Murakkablik ≈ `d · (U+k)/δ`, numpy bilan soniyadan kam.
4. **Boshlang'ich yuqori chegara:** FFD/BFD (K1 aytgan «FFD + takrorlash») — DP natijasi undan yomon bo'lmasligi shart (test).
5. **Yaxshilash:** (a) oxirgi `r ≤ 4` polosani olib, qolgan multiset (≤ ~40 detal) ni **bin-completion / DFS** bilan eng kam polosaga qayta joylash; (b) juft/uchlik almashtirishlar (2↔1, 2↔2) bilan qoldiqni bitta polosaga yig'ish; (c) vaqt byudjeti `fast ≤ 1 s`, `normal ≤ 5 s`, `max ≤ 20 s` (≤ 2000 nusxa). `fast/normal` **deterministik** (vaqtga bog'liq tasodif yo'q) — CS dagi ±1 list tebranishi takrorlanmasin.
6. **Birlashtirish:** bir xil sxemalar bitta kartaga (`copies`), kartalar tartibi: ishlatilish tartibida; qoldiq raqamlari kartalar bo'ylab davomli (Д1, Д2…).
7. **Paket:** `fill ≥ fill_packet` sxemalarda nusxa sonini kratnost ko'paytmasiga yaqinlashtirish (ikkilamchi; natijani yomonlashtirmaydi).
8. **Natijani qurish:** `commands` (§3.6), statistika, `validate_cl`.

### 3.6. Buyruqlar jadvali (CL uchun taklif)

Misol (R1: L=1600, w=360, T=20, k=10; detal № 3=780, 1=500, 2=150; otxod 80, № 1):
```
Кд  Р     К  Д
T1  20    1         ← boshidagi torsovka
P1  780   1  3      ← detal № 3 ni ajratuvchi kesim
P1  500   1  1
P1  150   1  2
W1  80    1  1      ← otxod № 1 (ko'k)
T1  20    1         ← oxirgi torsovka kesimi (otxod ajratilgandagina)
```
`x` daraja CL da doim 1 (burilish yo'q). Ketma-ket bir xil `P1` lar `К` bilan birlashadi. Aniq GibLab ko'rinishi — namuna kerak (Q6).
Karta: `cuts_count = 5`, `cut_length_m = 5·0.36 = 1.8`, `F = 1430/1600 = 89.375 %`; detal koordinatalari `x = 30, 820, 1330`, otxod `x = 1490`, uzunlik 80 (`raw_length = 110`).

### 3.7. Kirish/chiqish shartnomasi

```
optimize_linear(items, stock, cl: CLParams, *, time_limit=None) -> CuttingResult
  CutMap.sheet_length = polosa uzunligi, sheet_width = polosa eni, copies = C
  Placement(x = polosa boshidan, y = 0, length = p, width = w, rotated = False)
  Offcut(x, y = 0, length = W_hisob, width = w, kind, number, business, raw_length = W_xom, raw_width = w)
  CutCommand(code ∈ {T, P, W} (+ C ixtiyoriy), level = 1, size, count, ref)
```

### 3.8. Tekshiruv qoidalari (`validate_cl`, har natija o'tishi shart)

1. Har karta uchun `R ≥ 0` (sig'ish), joylashuv koordinatalari ketma-ket, propil `k` oraliqda, boshida `a_s`, oxirida `a_e` saqlangan.
2. Σ(`copies` × shu detaldan joylangan) ≤ ОК − МК; `ИК + Ост = ОК − МК`; ortiqcha joylash yo'q.
3. Har polosa turi bo'yicha ishlatilgan ≤ `qty` (10000 = cheksiz).
4. Otxod tasnifi (`waste_min`, `business_min`, `waste_incl_trim`) formulaga mos; `raw_length` polosa oxirigacha.
5. Statistika (F, LT, C, Cp, packs, material_qty) qayta hisoblab mos kelishi.
6. `unplaced` va ogohlantirishlar: sig'maydigan, «bad» o'lchamli detallar jim yo'qolmasin.
7. Detal eni (kromka bilan) polosa enidan katta bo'lsa — ogohlantirish (Q8).
8. Natija deterministik: bir xil kirish → bir xil chiqish (`fast/normal`).

### 3.9. Qabul testlari (yozilishi kerak)

| № | Kirish | Kutilgan |
|---|---|---|
| T-CL-1 | L=1600, T=20, k=10 | `U = 1540` (L #13) |
| T-CL-2 | T-CL-1 + detallar 780, 500, 150 | otxod `W = 80`; ☐ torsovka otxodi → `110`; `cuts = 5` |
| T-CL-3 | L=3200, T=20, k=10; 800×2 + 500×3 | `R = 0`, `cuts = 6`, `F = 96.875 %`, `LT = 6·w` (R4) |
| T-CL-4 | T_s = 0, T_e = 0 | `U = L`, kesimlar = `n − 1 + [R>0]` |
| T-CL-5 | `price` = 1000/m, `est = 90 %`, Σ = 10 m | kroygacha sarf 11 m, narx 11 000 |
| T-CL-6 | Tasodifiy 200 ta ko'rinish (har biri 20–400 detal) | har natija `validate_cl` dan o'tadi; polosalar ≤ FFD; ≥ 95 % holatda ≤ `LB + 1` |
| T-CL-7 | Cheklangan qoldiq-polosalar + cheksiz | qoldiqlar ro'yxat tartibida birinchi ishlatiladi |
| T-CL-8 | Detal uzunligi `> U_max` | `unplaced`, ogohlantirish, kroy qolganlar uchun davom etadi |

---

## 4. Ma'lumot modeli taklifi

### 4.1. Qayta ishlatiladigan va yangi

| Element | Qaror | Izoh |
|---|---|---|
| `OpType.CL` | mavjud | `models.py:60` |
| `Part` | **o'zgarishsiz qayta ishlatiladi** | `length`, `qty`, `minus_qty`, `edge_*`, `groove_*`, `name`, `description`, `product_id`, `used_qty`, `left_qty`; `width` CL da **0 saqlanadi** va hisobda `op.cl.width` olinadi; `grain`, `group_*`, `allow_top/bottom` ishlatilmaydi |
| `StockSheet` | **qayta ishlatiladi** | `length`, `width` (= `cl.width`, jadvalda ko'rinadi), `qty` (10000 cheksiz), `is_remnant`, `source_remnant_id`, `used_qty`, `description`; `trim_*`/`end_offset_*` v1 da ishlatilmaydi (Q7) |
| `CSMaterialParams`, `CSCutParams` | **qayta ishlatilmaydi** | CS ga xos maydonlar ko'p (burilish, yo'nalish, tekstura…); ular CL panelida chalg'itadi |
| `CLParams` (yangi) | bitta yassi model | `ELParams`/`GRParams` uslubida; `Operation.cl: Optional[CLParams]` (F1 hujjatida `cl` deb rejalashtirilgan, kodda yo'q) |
| `CuttingResult`, `CutMap`, `Placement`, `Offcut`, `CutCommand` | **qayta ishlatiladi** + 3 ta qo'shimcha maydon | chizma/chop/MES/ombor/`_account` shu natijaga bog'langan; alohida `CLResult` ikkilanish keltiradi |
| `RemnantRow` | `linear: bool` ustuni qo'shiladi | `db.py` migratsiya jadvaliga yozuv; `width` allaqachon bor |
| `settings.SCOPES` | `cl_defaults` | `CLParams` ni standart sifatida |

### 4.2. `CLParams` (Pydantic maydon nomlari)

```python
class CLCostBase(int, Enum):              # «Расчет стоимости операции по»
    CUT_WITH_TRIM = 0     # Длина реза с торцовкой
    CUT_NO_TRIM   = 1     # Длина реза без торцовки
    MATERIAL_LEN  = 2     # Длина материала (деловой отход ayirib)
    PARTS_LEN     = 3     # Длина деталей

class CLParams(Base):
    # Параметры материала
    width: float = Field(100, gt=0, le=20000)            # Ширина (mm) — hamma detal eni
    thickness: float = Field(16, ge=0, le=1000)          # Толщина (kratnost uchun)
    # Параметры раскроя
    kerf: float = Field(3, gt=0, le=50)                  # Толщина пилы (> 0)
    trim: float = Field(0, ge=0, le=500)                 # Торцовка (boshida)
    end_offset: Optional[float] = Field(None, ge=0, le=500)   # Минимальный отступ в конце (None = trim)
    pack_height: float = Field(40, ge=0, le=1000)        # Высота пакета
    fill_packet: float = Field(90, ge=0, le=100)         # Процент заполнения для кратности
    quality: Literal["fast", "normal", "max"] = "normal" # (bizning kengaytma)
    # Отход
    waste_min: float = Field(100, ge=0, le=20000)        # Мин. размер отхода (mm)
    business_min: float = Field(500, ge=0, le=20000)     # Длина делового отхода (mm; birlik — Q3)
    waste_incl_trim: bool = True                         # Торцовка отходов
    min_part_len: float = Field(0, ge=0, le=10000)       # ❓ cMinDimDetail (Q9)
    # Стоимость
    price: float = Field(0, ge=0, le=1e9)                # Цена материала (1 m yoki 1 polosa — price_by_strip)
    price_by_strip: bool = False                         # ❓ K1/G4: «по полосам» (Q4)
    strip_rounding: SheetRounding = SheetRounding.WHOLE  # ❓ 11/32/33/34 (faqat price_by_strip=True da)
    est_fill_percent: float = Field(90, ge=0, le=100)    # Расчетный процент заполнения
    op_cost_base: CLCostBase = CLCostBase.CUT_WITH_TRIM  # Расчет стоимости операции по
    op_price: float = Field(0, ge=0, le=1e9)             # Цена операции
    # hisoblangan, faqat o'qish (har saqlashda yangilanadi)
    usage_m: float = 0                                   # Расход / Количество материала (m)
    multiplicity: int = 1                                # Кратность
```
`_legacy_ranges` validatori (eski JSON chegaradan chiqsa qisqartirish) boshqa modellardagi kabi qo'shiladi.
Ichki ma'no «mm» (D5 bilan bir xil); `business_min` UI da mm (G4 dagi «m» — Q3 da tasdiqlanadi).

### 4.3. Natija maydonlari (CL uchun)

| Maydon | CL da ma'nosi |
|---|---|
| `CutMap.sheet_length / sheet_width / copies / packs` | polosa uzunligi / eni / bir xil polosalar soni / arra sikllari |
| `CutMap.placements` | `x` boshidan, `y = 0`, `length = p`, `width = w`, `rotated = False` |
| `CutMap.offcuts` | otxod (`kind`, `number`, `business`, `raw_length`) |
| `CutMap.commands` | `T/P/W` (daraja 1) |
| `CutMap.parts_count / cut_length_m / cuts_count / fill_percent` | Cp / LT (= kesimlar × w) / kesim soni / F |
| `CutMap.strips` | CL da bo'sh (daraxt yo'q) — qo'lda tahrir 1D ro'yxat orqali |
| `CuttingResult.total_sheets` | jami polosa (alias: «полос») |
| **yangi** `CuttingResult.kind: Literal["sheet","linear"] = "sheet"` | UI/chop/ombor tarmoqlanishi uchun |
| **yangi** `CuttingResult.material_len_m: float` | ishlatilgan polosalar uzunligi (m) |
| **yangi** `CuttingResult.business_len_m: float` | деловой otxodlar uzunligi (m); `material_qty_m2` o'rniga `Количество материала` = `material_len_m − business_len_m` |

`PrintSettings`: `cl_header, cl_parts, cl_group_by_product, cl_unplaced, cl_strips, cl_remnants, cl_maps` (R5 dagi 7 ta belgi;
standart `✓ ✓ ☐ ✓ ✓ ✓ ✓`).

### 4.4. Kodda tegiladigan joylar

| Fayl | O'zgarish |
|---|---|
| `models.py` | `CLCostBase`, `CLParams`, `Operation.cl`, `CuttingResult` 3 maydon, `PrintSettings.cl_*` |
| `services/cl_optimizer.py` (yangi) | `optimize_linear`, `validate_cl`, DP/FFD/bin-completion |
| `services/calc.py` | `_items_for` CL varianti; `run_linear`; `cl_cost`; `usable_length`; `estimate_consumption_m`; `_packets` (qalinlik/paket `cl` dan); `recalc_project` CL tarmog'i; `product_costs` (CL ulushi); `warehouse_request` (CL qatori); `edge_usage` va `groove_usage` da CL eni = `op.cl.width` |
| `main.py` | `_new_operation` (CL standarti + katalog `linear`); `_need_cs` → `_need_cut` (CS yoki CL); `update_operation` natijani CL uchun ham saqlash (`:861`); `_cl_params_stale`; `sheets_from_remnants` va `PUT result` CL ga; MES webhook |
| `services/warehouse.py` | `commit/rollback` da `assert CS` → CS yoki CL, `thickness` `cl` dan, `linear` bayroq |
| `db.py` | `RemnantRow.linear` + `_MIGRATIONS` |
| `services/settings.py` | `cl_defaults` scope |
| `services/render.py` | `_cl_section`, `map_svg` 1D tarmog'i, talabnoma qatori |
| `services/postprocessors.py` | CL konteksti (`strip_length`, `pieces`, `copies`) |
| `plugins/legacy_project.py` | `CL` tarmog'i (G4 xaritasi) — past ustuvorlik |
| `i18n.py`, `i18n_src.py` | xabarlar (detal sig'maydi, bad o'lcham…) va yorliqlar |
| `frontend` | `opmeta.tsx` IMPLEMENTED; `OperationsTable.tsx` (`defName`, tugma); `CatalogPicker.tsx` (linear→CL); `ProjectView.tsx` (panel tanlash); `features/cl/*` (yangi); `api/types.ts`; `Print.tsx`; e2e |

---

## 5. Ekranlar (D_UI_SPEC uslubida; CS paneli namuna)

### D-CL1. Panel va yorliqlar
`CsTabs` ga o'xshash 4 yorliq: `Параметры` · `Детали` · `Полосы и отходы` · `Раскрой`; o'ngda: «Сохранить текущие параметры для
использования по умолчанию», «Применить стандарт», «?» (F1). Faol yorliq `store/ui.ts` da (`csTab` qayta ishlatiladi:
`params | parts | sheets | cut`). Operatsiya nomi o'rta panelda `CL` nishoni bilan.

### D-CL2. «Параметры» (CS paneli kabi 2 ustun)
**Chap ustun:** *Параметры материала* — Ширина (mm), Толщина (mm). *Стоимость* — Цена материала (за м), Расчетный процент
заполнения (%), Количество материала (faqat o'qish, «N м»), Стоимость материала (o'qish), Расчет стоимости операции по (4 qiymatli
ro'yxat), Цена операции, Стоимость операции (o'qish). *Отход* — Мин. размер отхода, Длина делового отхода, ☐/☑ Торцовка отходов.
**O'ng ustun:** *Параметры раскроя* — Толщина пилы, Торцовка, havola «Минимальный отступ в конце: N мм» (oyna: ☐ «Минимальный отступ
в конце» + qiymat; belgilanmaguncha torsovka qiymati ko'rinadi, Ок/Отмена — CS dagi D5 oynasi kabi), Высота пакета, Кратность
(faqat o'qish, «N шт»), Процент заполнения для кратности; *Предпочтения* — Качество (Tez/Standart/Maks).
Har parametr yonida yashil «?». Kroy natijasini eskirtiradigan parametr (propil, torsovka, otxod qoidalari, eni…) o'zgarsa —
tasdiq modal oynasi (CS dagi `params_invalidate` mantiqi); narx maydonlari eskirtirmaydi.

### D-CL3. «Детали»
Jadval ustunlari: `№ | Д-на | Кол | ОВ | ОН | ОЛ | ОП | Наименование | ОК | ИК | Ост` (+ Ctrl+P profilida: Код, МК, Изох, ID;
`Ш-на` — yo'q). Kromka katagi — EL nomi, EL rangida; Space — keyingi EL; Shift+Space — to'rt tomon. Yangi qator: Кол = 1.
Pastki toolbar: «Режим ввода размеров» havolasi (CL da ❓ — Q8), Excel ikonkasi, **Длина: X м**, **Кол-во: N шт** (jonli).
Ctrl+V tartibi `Д-на, Кол, ОВ, ОН, ОЛ, ОП, Наименование`. Tooltip: Изделие, № в изделии, № в раскрое, id. Ctrl+Space — detal xossalari
(`Ширина` o'qish, polosa eni). Qator amallari va yorliqlar — `E3`. Kroydan keyin `ИК/Ост` jonli; `Ост > 0` qator ogohlantirish rangida.

### D-CL4. «Полосы и отходы»
Jadval: `№ | Наименование (Полоса / Отход / Деловой отход) | Длина | Ширина | Площадь | Количество | Исп. Кол-во | Остаток | Изох`.
Yangi operatsiyada bitta qator: katalogdagi (yoki 6000 mm) polosa, `Ширина` = `cl.width` (avtomatik), `Количество` = 10000
(cheksiz — Q17). Toolbar: ✚ qo'shish, ✕, ↑↓, «Qoldiqlarni ombordan yuklash», «Qoldiqlarni omborga saqlash» (kroydan keyin).
Kroydan keyin jadval oxirida otxod qatorlari (faqat o'qish, `Исп. Кол-во` tahrirlanadi). Ro'yxat tartibi = ishlatish tartibi (Q2).

### D-CL5. «Раскрой»
```
[Раскроить] [Редактирование раскроя] [Комментарий F2] [Удаление раскроя] [Постпроцессор] [◀ ▶ ⏮ ⏭]       [?]
№: 3/8 │ S: 3200/600 │ C: 1/17 │ Cp: 5/80 │ LT: 3.6/58.2 │ F: 96.88%/97.81%          ┌ Миниатюры ─┐ [Таблица команд]
┌──────────────────────────────────────────────────────────────────────────────────┐ │ ▭▭▭▭▭ №:1  │
│ ▒ │ 800 │ 800 │ 500 │ 500 │ 500 │▒                                                  │ │ ▭▭▭▭▭ №:2  │
│   1    1     2     2     2                                                          │ │ ▭▭▭▭ №:3 ◄ │
└──────────────────────────────────────────────────────────────────────────────────┘ └────────────┘
```
Status satri ko'rsatkichlari: № S C Cp LT F (sozlanadi — Ctrl+P, CS kabi; CL da qo'shimcha ko'rsatkichlar ❓).
Karta: detal to'q sariq (№ ichida, uzunlik pastda chapda), tanlangani va uning nusxalari to'qroq; otxod ko'k + raqam; chetlar kulrang;
g'ildirak — masshtab; ikki marta bosish — detal xossalari. O'ng panel: miniatyuralar `№:N S:L/W C:c` ↔ «Таблица команд»
(`№ | Кд | Р | К | Д`). Kroy yo'q bo'lsa — markazda «Раскроить» va «Редактирование раскроя».

### D-CL6. CLE oynasi (Редактирование погонажного раскроя)
Chap: detallar jadvali `Длина | Ширина | Кол-во | Исп. Кол. | Остаток | Ткт | Наименование` (CL da `Ширина`/`Ткт` — faqat o'qish yoki
yashirin, Q13). O'ng: karta + miniatyuralar. Toolbar: Полноэкранный (F9) · Отменить (Ctrl+Z) · Вернуть (Ctrl+Y) · Добавить карту ·
Удалить карту · Количество листов · Торцовка листа · Вначало (Ctrl+←) · Вконец (Ctrl+→) · Удалить деталь (Del / o'ng tugma) ·
Фильтр нулевых (Ctrl+F) · Карта ↑/↓ (Ctrl+↑/↓) · Home/↑/↓/End. Sichqoncha: chap — tanlash; Ctrl+chap — ko'p tanlash; Shift+chap —
tahrir rejimi (detalni polosaga qo'yish); Shift+A+chap — ko'p qo'yish. Har tahrirdan keyin `validate_cl`, ortiqcha detal qizil;
Ok → `PUT .../result`.

### D-CL7. Chop (CL)
`Печать отчета` → «Настройки печати операций» → (CL) Погонажный раскрой: 7 belgi (R5). Hisobot bo'limlari: Детали
(`№ | Длина | Ширина | …`), Невместившиеся, Полосы, Отходы, Карты раскроя (sarlavha `№ S C Cp …`, chizma, izoh). A4 da 1 karta yoki
miniatyura rejimi. Talabnoma (`Требование на склад`) da CL qatori.

---

## 6. Aniqlashtirish kerak bo'lgan savollar

Yordam va rasmlar javob bermaganlar. «Taklif» — javob kelguncha qabul qilingan ish farazi. Jonli GibLab oynasidan foydalanish
bu vazifada taqiqlangan, shuning uchun javoblar foydalanuvchidan (real CL namunasi/eksport/ekran) kerak.

| № | Savol | Nima uchun muhim | Taklif (faraz) |
|---|---|---|---|
| Q1 | GibLab CL optimizatorining maqsadi nima: eng kam polosami yoki eng kam sarfmi (delovoy otxod hisobga olinadimi)? 3–5 real CL topshirig'i va GibLab natijasini (polosalar, kartalar) olib bo'ladimi? | Qabul mezoni va solishtirish; korpusda CL **0 ta** | §3.4 leksikografik; namuna kelguncha LB va FFD bilan solishtiramiz |
| Q2 | Polosalar ishlatish tartibi CL da ham ro'yxat tartibimi (soni bo'yicha o'sish, cheklanganlar birinchi)? | CS da jonli tasdiqlangan, CL ❓ | CS bilan bir xil |
| Q3 | «Длина делового отхода» va «Мин. размер отхода» birligi — mm yoki m? Standart qiymatlari? | UI va importer | UI mm; importda G4 «m» bo'lsa ×1000 |
| Q4 | «Цена материала» faqat metr uchunmi yoki «по полосам» + yaxlitlash (11/32/33/34) ham bormi? | K1/G4 bor, CL yordami aytmaydi | v1: faqat metr; `price_by_strip` keyin |
| Q5 | «Цена операции (метр/рез)» birligi nima? «Длина реза» = kesimlar soni × polosa eni (R4 raqamlari shuni ko'rsatadi) — tasdiqlanadimi? | Narx hisobi | metr; LT = kesim × eni |
| Q6 | Buyruqlar jadvali CL da qanday ko'rinadi: faqat T/P/W mi, `C` ishlatiladimi, oxirgi torsovka alohida `T` qatori bo'ladimi, otxod bo'lagidan keyingi kesim kesimlar soniga kiradimi (R4: 97 = 80 + 17 — otxodsiz hol)? | `LT`, narx, postprotsessor | §3.6 |
| Q7 | «Торцовка листа» (CLE) polosa boshidagi/oxiridagi qaysi qiymatni o'zgartiradi? Polosalar jadvalida ТД/ТШ yo'q — qatorga xos torsovka bormi? | Model (`StockSheet.trim_*`) | v1 da yo'q |
| Q8 | CL detalda o'lcham kiritish rejimlari (заготовка/деталь/после прифуговки), pripusk va ОЛ/ОП kromka qalinligi **uzunlikka** ta'sir qiladimi? Detal eni (kromka bilan) polosa enidan katta bo'lsa nima bo'ladi? | `compute_sizes` CL da | CS formulasi, eni = `cl.width` |
| Q9 | «Минимальный размер детали» (`cMinDimDetail`) va «Минимальная обрезка» CL da bormi? | Qo'shimcha parametrlar | yo'q (`min_part_len` ixtiyoriy) |
| Q10 | Polosa ichida detallar tartibi (kamayish/o'sish/aralash)? | Chizma/stanok tartibi | uzundan qisqaga |
| Q11 | «До кроить» CL da bormi? | Funksiya hajmi | yo'q (v1) |
| Q12 | «Количество листов» CLE da nimani o'zgartiradi — kartaning `C` sonini (polosa nusxalari)? | CLE | ha, `copies` |
| Q13 | CLE jadvalidagi «Ширина» va «Ткт», hamda Shift+Ctrl+bosish «aylantirish» CL da ma'noga egami yoki CS dan qolgan? | UI ortiqcha elementlari | yashirish |
| Q14 | Qoldiqlar CL da kodi bo'yicami yoki (uzunlik × eni) bo'yicami? Omborga yozilganda eni, qalinligi nima bo'ladi? | Ombor sxemasi (`linear`) | kod + uzunlik; eni = `cl.width` |
| Q15 | Polosa qatorlari **turli eni**da bo'la oladimi (jadvalda «Ширина» ustuni bor) yoki hamma qator = `cl.width`? | `StockSheet.width` | hammasi = `cl.width` |
| Q16 | «Процент заполнения для кратности» aniq mantiqi (chegaradan past sxemalar uchun paket umuman ishlatilmaydimi)? | Paket afzalligi | §3.5-7 |
| Q17 | Polosa soni uchun «cheksiz» belgisi (10000) CL da ham qo'llanadimi? Eng ko'p detal soni chegarasi? | Validatsiya | CS kabi |
| Q18 | «Требование на склад» da CL birligi: polosa (B11) yoki metr (K1: «1 m yoki 1 polosa»)? | Hisobot | `price_by_strip` ga qarab |
| Q19 | Arra stanogi (CL) postprotsessor formati — namuna fayl. | CL-072 | foydalanuvchi beradi |
| Q20 | Korxonaga CL umuman kerakmi (205 loyihada 0 ta)? Qaysi materiallar (plintus, profil) kesiladi, qanday uzunlikda? | Ustuvorlik va standartlar | to'liqlik uchun, past ustuvorlik |
| Q21 | Etiketka/shtrixkod CL kroyida (har polosa yoki detal) kerakmi? | CL-125 | yo'q (v1) |
| Q22 | Hisobot bo'limlari tartibi va nomlari (rasmda «4. Раскрой») — to'liq namuna chop. | CL-107…114 | §D-CL7 |
| Q23 | Plintus/profilda burchakli (45°) kesim kerakmi? GibLab CL da bunday imkon yordamda ko'rinmaydi. | Model: detalga `angle` maydoni, kesim eni va sig'im formulasi o'zgaradi | v1 da yo'q |

---

## 7. Amalga oshirish rejasi

| Bosqich | Mazmun | Bog'liqlik | Hajm (kishi-kun) |
|---|---|---|---|
| 0 | Savollar Q1–Q8, Q20 bo'yicha qarorlar; kamida 1–2 real CL namunasi (ekran/hisobot) | foydalanuvchi | 0.5 |
| 1 | Backend model: `CLParams`, `Operation.cl`, `_new_operation`, `cl_defaults`, `recalc_project` CL tarmog'i, `usable_length`, `cl_cost`, taxminiy sarf; unit testlar T-CL-1/2/3/5 | — | 2 |
| 2 | `cl_optimizer.py`: normallashtirish, DP, FFD/BFD, ro'yxat tartibi/cheklangan miqdor, otxod tasnifi, buyruqlar, statistika, `validate_cl`; testlar T-CL-4/6/7/8; 1D benchmark (tasodifiy + LB) | 1 | 4 |
| 3 | API: `optimize/result/variants` CL ga ochiladi (`_need_cut`), invalidatsiya (`_cl_params_stale`), `_account`, talabnoma, mahsulot narxi, MES hodisasi, `edge/groove` eni tuzatishi | 1, 2 | 1.5 |
| 4 | Frontend MVP: `features/cl/` (Params, Parts, Sheets, Cut), 1D karta chizmasi, buyruqlar jadvali, `OperationsTable`/`CatalogPicker`/`ProjectView` ulanishi, i18n (ru/uz), e2e | 1–3 | 4 |
| 5 | Chop: `PrintSettings.cl_*`, `Print.tsx` dialogi, `_cl_section`, 1D `map_svg`, talabnoma qatori | 2–4 | 1.5 |
| 6 | Ombor: `RemnantRow.linear`, `warehouse` commit/rollback CL, «Ombordan yuklash/saqlash», qoldiq ro'yxati | 3 | 1.5 |
| 7 | CLE (1D tahrir): jadval + karta, undo/redo, tekshiruv, saqlash | 4 | 3 |
| 8 | Postprotsessor shabloni (namuna fayl kerak), `.project` importi (CL), Excel import profili, etiketka (ixtiyoriy) | namuna | 2 |
| 9 | Mustaqil QA (CS dagi 3 agentli sxema), `K_OPERATIONS` va `01_KONTEKST.md` yangilash, `IMPLEMENTED` ga `CL` qo'shish (xususiyat bayrog'i) | hammasi | 1 |
| **Jami** | MVP (1–4) ≈ **11.5**; to'liq (1–9) ≈ **20.5** kishi-kun | | |

**MVP ta'rifi (H ustuvorlik):** CL-001/002, parametrlar, detallar, polosalar, «Раскроить», karta + buyruqlar jadvali, narx, tekshiruv.
**Xavflar:** (1) GibLab bilan natija mosligi — namuna bo'lmasa solishtirib bo'lmaydi (Q1); (2) CL ishlatilmaganligi sababli
foydalanuvchi talabi bo'lmasligi — MVP dan keyin to'xtash mumkin; (3) `calc.edge_usage/groove_usage` da `width = 0` xatosi
(CL-038) CL qo'shilmasa ham kelajakdagi import uchun xavfli — bosqich 3 da tuzatiladi.
**Joriy etish:** `IMPLEMENTED` ga `CL` faqat 1–5 bosqich va QA dan keyin; avval feature-flag orqasida.
