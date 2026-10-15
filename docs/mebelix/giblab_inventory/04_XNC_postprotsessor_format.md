# 04. (XNC) Обработка, XNC kutubxonasi, postprotsessorlar bo'limi va `.project` formati — funksiyalar inventari

> Maqsad: GibLab yordamidagi **funksional ma'noni** o'z so'zimiz bilan yozib, MebeliX Kroy bilan solishtirish.
> Foydalanuvchi ko'rsatmasi: **postprotsessorlarning ichki mantig'i (stanok fayl sintaksisi) kerak emas** — uni korxona
> dasturchilari yozadi. Bu hujjat faqat: stanoklar nomlari ro'yxati, sozlamalar tuzilishi va ulanish nuqtalarini tavsiflaydi.
> Yordamda aniq bo'lmagan format **o'ylab topilmagan** — «yordamda yo'q» deb belgilangan.
>
> **Manbalar** (faqat yordam sahifalari va ularning rasmlari, funksional ma'no uchun):
> `operations/xnc`, `libraryXNC`, `xnceditor` (bo'sh), `postprocessors/*`, `postprocessor_ru`, `format_ru` (+ `Example1.project`),
> `update_ru` (o'zgarishlar tarixi), `expression/*` (ifoda tili), `development/ParamGrid`, `labels_ru`, `import/*`
> (faqat XNC ga tegishli satrlar), hamda `images/xnc`, `images/postprocessor`, `images/libraryXNC` (yordam rasmlari).
> Rasmlar, ikonkalar, yordam matni ko'chirilmagan; rus atamalari ekrandagi nom sifatida saqlangan.
>
> **Dalil belgilari:** `H` — `operations/xnc.html` · `F` — `format_ru.html` (.project formati) · `U` — `update_ru` (o'zgarishlar) ·
> `E` — `expression/*` sahifalari · `IMG` — yordam rasmlari · `L` — topshiriqda keltirilgan jonli GibLab ekran kuzatuvi
> (oynalar/yorliqlar nomlari) · `K` — 205 ta real `.project` fayl skani (**faqat teg/atribut nomlari va hisoblagichlar**, mijoz
> ma'lumotlari hujjatga kirmagan) · qolganlari — bizning kod fayllari (kod o'qib tekshirilgan, ilova ishga tushirilmagan).
> Belgilar: ✅ to'liq · 🟡 qisman · ❌ yo'q · ❓ aniqlab bo'lmadi. Murakkablik: S ≤ yarim kun, M ≤ 2 kun, L undan ko'p.
> Ustuvorlik — mebel korxonasi uchun (H yuqori / M o'rta / L past). Korxonada XNC «ba'zan: ko'rish/chop» ishlatiladi
> (`M_STAFF_HABITS.md`), shuning uchun stanokka chiqarish va narx bandlari odatda M/L; **kroy natijasiga ta'sir qiluvchi
> xatolar (hisob noto'g'ri bo'lishi) — H**.
> Holat sanasi: 2026-10-02 (boshqa agent hozir «Stanoklar» sahifasini Settings.tsx ga qo'shayotgan edi — u ✅ deb sanalgan).

## 1. Qisqa xulosa

1. **Yordam juda kam matnli.** `xnc.html` (81 KB) deyarli butunlay base64 ikonkalar: matn — 3 yorliq nomi (Параметры / Шаблон /
   Стоимость), toolbar jadvallari, buyruqlar ro'yxati va «Точка входа для фрезы» uchun kirish/chiqish shabloni (RQG).
   Buyruqlar parametrlari **faqat `format_ru.html`** (`.project` formati) da; grafik redaktor yordami (`xnceditor`) va 7 ta
   postprotsessor sahifasi (G-Code, iLenia, KDT Trepan, MW310, TPA, WoodWop, XD WoodCam) **bo'sh**. Qo'shimcha ma'lumot: o'zgarishlar tarixi (`update_ru`), ifoda tili (`expression/*`),
   yordam rasmlari (frezalash turlari, Format4 yozuvlari, kutubxona).
2. **XNC operatsiyasi** — detalga biriktiriladigan CNC dasturi: 3 yorliq (Параметры — o'lcham, soni, narx, izoh · Шаблон — dastur
   redaktori · Стоимость — narx). Dastur: asbob (Инструмент), 5 xil teshik (frontal/chap/o'ng/yuqori/pastki), freza (kirish
   nuqtasi, to'g'ri chiziq, yoy, markazli yoy), paz (Пазование), koordinata boshi + 15 ta boshqaruv buyrug'i (Com, Par, Var, Set,
   If, Else, While, DoWhile, Break, Continue, Sub, Call, Ret, Msg, Err). Yangi buyruqlar (rasmlarda): yoy 3 nuqta, skrugleniye,
   to'rtburchak, ellips, Bezier; changelog: cho'ntak (карман), chuqurlikka qadam, parametrik shablonni qayta hisoblash.
3. **Bizda** XNC kerakli darajada ishlaydi: saqlash, import (205 faylda 9 698 XNC operatsiya; Q_QA: 210 fayl importi — 0 xato), chizma, narx/statistika
   (teshik 8359/8360, freza va paz 8360/8360 mos), ifodalar, boshqaruv buyruqlari, hisobot. **Yo'q**: shablon kutubxonasi/saqlash,
   DXF import, ishlov markazi formatiga chiqarish (XNC postprotsessor), grafik tahrir (sichqoncha), redaktor sozlamalari,
   kodlash ifodasi, etiketkada XNC kodlari.
4. **Kodda topilgan 4 ta nomuvofiqlik (H ustuvorlik, hisob/mosligiga ta'sir qiladi):**
   (a) teshik massivi `ac/as/av` importdan saqlanadi, lekin `xnc.py` uni sanamaydi va chizmaga chiqarmaydi (faqat `count` o'qiydi);
   (b) «atribut yozilmasa — oldingi qiymat» qoidasi (J2) kodda yo'q (docs `N_CHANGES_FROM_v1` da bor deb yozilgan);
   (c) GibLab ifoda tili farqlari: `if(c,a,b)` funksiyasi, `=`/`<>`, `^`, `xor`, `true/false` bizda ishlamaydi; trigonometriya GibLab
   yordamida **radian**, bizda **gradus**; butun/butun bo'linish va `round` (−1.5) semantikasi farq qiladi;
   (d) `ms` dagi `sdp/sxy/in/out`, `gr` dagi `c`, qirra teshigidagi `m` importda o'qilmaydi (statistikaga ta'sir qilmaydi, lekin
   stanokka chiqarishda kerak bo'ladi). Real 205 fayl faqat tool, var, bf/bl/br/bt/bb, ms, ml, mac, gr teglarini ishlatadi.
5. **Postprotsessorlar (GibLab):** «Постпроцессоры» oynasi = «Общие» tab + har stanokka alohida tab. Yordamda **aniq** yozilgan
   faqat: Felder Format4 (yozuvlar MA000/MA005/MA010/MA015 va foydalanuvchi to'ldiradigan maydonlar — rasm),
   Holzma PTX (fayl nomi ifodasi, PARTS_UDI), Biesse OSI+ (orientatsiya sozlamasi), Xilog3 (yuzalar F1..F5 koordinatalari — rasm). Qolganlari —
   stanokka fayl yetkazish ko'rsatmasi yoki bo'sh sahifa. Bizda stanoklar ro'yxati (31 nom), yoqish/o'chirish, shablon biriktirish
   va fayl nomi prefiksi **bor**; yetishmaydi: har stanok uchun sozlamalar sxemasi, fayl nomi ifodasi, etiketka ma'lumot jadvallari,
   XNC (ishlov markazi) konteksti.
6. **`.project`:** importer hujjatdagi deyarli hamma XNC/CS/EL/GR atributlarini o'qiydi; o'qilmaydiganlar — `allowanceT/B/L/R`,
   `groupInBlock*`, `dbId`, detal `description` (#kod), mahsulot `phone1/phone2/description`, `project.uuid`, `importBMV`, ba'zi XNC
   atributlari (4.1 jadvali) va CL/O/SP/LB operatsiyalari. **Eksport yo'q.**
7. **Hisob:** jami **133** XNC funksiyasi (XNC-001…133): ✅ **51** · 🟡 **27** · ❌ **45** · ❓ **10**; `.project` bo'yicha 23 ta qator (PRJ-001…023, 4.1).
   Ustuvorlik (❌+🟡 = 72 ta): H — 9 (XNC-016, 025, 046, 049, 051, 060, 071, 072, 095), M — 35, L — 28; yana 10 ta ❓ (9 ta L, 1 ta M) — 5-bo'lim.

## 2. XNC funksiyalari jadvali

### 2.1 Operatsiya oynasi — Параметры / Стоимость

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-001 | O'lcham DX / DY / DZ (Длина, Ширина, Толщина) | Zagotovka o'lchami; «По размеру детали» yoqiq va operatsiya detalga bog'langan bo'lsa detaldan olinadi (DZ — material qalinligi) | mm; detaldan | ✅ | H, F (`program dx/dy/dz`), `calc.sync_xnc`, `XncPanel.tsx` | S | H |
| XNC-002 | Количество | Detallar soni; detalga bog'langanda ОК − МК dan avtomatik to'ladi | butun ≥ 1 | ✅ | H, F (`count`), `calc.sync_xnc` | S | H |
| XNC-003 | Стоимость (jami) | Teshik va frezalash narxlari yig'indisi, soniga ko'paytiriladi; faqat o'qiladi | pul | ✅ | H, `xnc_cost` | S | M |
| XNC-004 | Описание | Maxsus belgilar / izoh | matn | ✅ | H, `XncPanel.tsx` | S | L |
| XNC-005 | «По размеру детали» (`bySizeDetail`) | Belgi: yoqilsa DX/DY/DZ detal o'lchamidan | true | ✅ | F, `XNCParams.by_part_size` | S | H |
| XNC-006 | Сторона детали (`side`) | Ishlov lits yoki orqa tomondan; ifodada `xncSide`. Real fayllarda `side` ba'zan `1`/`2` ko'rinishida (1 → lits deb olinadi, 2 → orqa) | true = lits | ✅ | F, K, `legacy_project.py` (`side`), `XNCParams.face_side` | S | H |
| XNC-007 | Поворот (`turn`) | 0/1/2/3 = 0/90/180/270° — chizma va (stanokka chiqarishda) detalni burish | 0 | ✅ | F, `_View`, importer | S | M |
| XNC-008 | Отзеркаливание (`mirHor`, `mirVert`) | Gorizontal / vertikal ko'zgu | false | ✅ | F, `_View` | S | M |
| XNC-009 | Начало координат (burchak: LT/RT/LB/RB) | Dastur koordinatalari qaysi burchakdan hisoblanadi. `.project` hujjatida bunday atribut yo'q — GibLab qayerda saqlashi aniq emas | LT | ✅ | L, J1, `XNCParams.origin` | S | M |
| XNC-010 | Код программы (`code`) | Dastur nomi/kodi — stanok fayl nomi va shtrixkod uchun; takrorlanmasligi kerak | matn | ✅ | F, `recode_xnc` | S | H |
| XNC-011 | Narx parametrlari (`priceBore`, `priceMill`, `priceCut`, `price`) | 1 teshik, 1 m freza, 1 m paz narxi va operatsiyaga qo'shimcha narx | 0 | ✅ | F, `XNCParams` | S | L |
| XNC-012 | Hisoblangan miqdor va narx (`countBore/Mill/Cut`, `costBore/Mill/Cut`, `cost`) | Teshiklar soni, freza va paz uzunligi (m), ularning narxi, birlik narxi | — | ✅ | F, `program_stats`, `xnc_check.py` (8359/8360; 8360/8360) | M | H |
| XNC-013 | Standart narxni saqlash («Сохранить текущие параметры для использования по умолчанию») | «Стоимость» yorlig'idagi joriy narxlar keyingi XNC operatsiyalar uchun standart bo'ladi | — | ❌ | H | S | L |
| XNC-014 | Detal chizmasi (kromka harflari bilan) | O'ngda detal konturi, kromka tomonlari harf bilan, teshik/freza/paz chizilgan | — | ✅ | L, J1, `xnc_drawing_svg` | M | H |
| XNC-015 | Выбрать деталь / Отменить деталь | XNC operatsiyasini detalga bog'lash yoki ajratish | — | 🟡 faqat detal xossalaridagi «+XNC» orqali; XNC panelida tanlash/ajratish tugmasi yo'q (detal maydoni faqat o'qiladi) | H, `PartDialogs.tsx`, `XncPanel.tsx` | S | M |
| XNC-016 | Открыть / Сохранить (shablon katalogi) | Operatsiya dasturini shablon papkasidan ochish va unga saqlash | — | ❌ | H, L («Папки: XNC шаблонов», D12) | M | H |
| XNC-017 | Справка (F1) | XNC kontekst yordami | — | 🟡 tugma bor, XNC bo'limi matni yo'q | H, `XncPanel.tsx`, `Help.tsx` | S | L |
| XNC-018 | Постпроцессор tugmasi (Конвертация в формат обрабатывающего центра) | XNC operatsiyasini tanlangan ishlov markazi formatiga o'tkazadi | — | ❌ (postprotsessor faqat CS kroy uchun) | H, `main.py` `postprocess` (`_need_cs`) | L | M |
| XNC-019 | Импорт из DXF | DXF chizmadan dastur oladi (qoidalari — qatlam/rang — yordamda yo'q) | — | ❌ | H (toolbar), IMG | L | M |
| XNC-020 | Chop: XNC statistikasi + chizma | Hisobotga XNC statistika jadvali va detal chizmasi | — | ✅ | L, D11, `render.py` | M | M |

### 2.2 Dastur buyruqlari — asbob va teshik

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-021 | Инструмент (`tool`) | Asbob nomi (`name`) va diametri (`d`, ifoda) e'lon qilinadi; keyingi teshik/freza shu nom bilan asbobni tanlaydi | `d` ifoda | ✅ | F, `xnc.py` (`Tool`), K (18 234 ta) | S | H |
| XNC-022 | «Включить» (`enable`) — har buyruqda | O'chirilgan buyruq bajarilmaydi (dasturdan vaqtincha chiqarish) | true | ❌ model, importer va evaluator da yo'q (K: 205 faylda ishlatilmagan) | F, `models.XncCommand` | S | M |
| XNC-023 | «Подпись» (`comment`) — har buyruqda | Buyruq izohi | matn | ✅ | F, `XncCommand.comment` | S | L |
| XNC-024 | Сверление фронтальное (`bf`) | Yuzadan teshik: `x`, `y` (ifoda), chuqurlik `dp`, asbob nomi | `dp` ≥ DZ — o'tuvchi | ✅ | F, H, IMG, `xnc.py`, K (53 935) | S | H |
| XNC-025 | Teshik massivi (`ac`, `as`, `av`) | Frontal teshikni qatorga ko'paytiradi: soni, qadam, yo'nalish (vertikal true / gorizontal false) | `ac`=1, `av`=false | 🟡 importer AC/AS/AV ni saqlaydi, lekin `xnc.py` faqat `count` o'qiydi — massiv sanalmaydi va chizilmaydi | F, IMG (AC=5), `xnc.py` (`cnt`), `legacy_project.py` | S | H |
| XNC-026 | Сверление слева (`bl`) | Chap qirradan teshik: `y`, `z`, `m`, `dp` | `m`=true | ✅ | F, IMG, `xnc.py`, K (8 580) | S | H |
| XNC-027 | Сверление справа (`br`) | O'ng qirradan teshik: `y`, `z`, `m`, `dp` | `m`=true | ✅ | F, IMG, K (8 021) | S | H |
| XNC-028 | Сверление сверху (`bt`) | Yuqori qirradan teshik: `x`, `z`, `m`, `dp` | `m`=true | ✅ | F, IMG, K (2 637) | S | H |
| XNC-029 | Сверление снизу (`bb`) | Pastki qirradan teshik: `x`, `z`, `m`, `dp` | `m`=true | ✅ | F, IMG, K (2 544) | S | H |
| XNC-030 | Qirra teshigi: «Середина по Z» (`m`) va `z` | `m`=true — qalinlik o'rtasida; false — `z` aniq/siljish (yordamda «координата / смещение» deb ikki xil yozilgan) | `m`=true | 🟡 importer `z` ni oladi, `m` ni o'qimaydi (K: 108 ta m=false); chizma va statistika `z` dan foydalanmaydi | F, K, `legacy_project.py` | S | M |
| XNC-031 | Qirra teshiklarida `ver` atributi | Yordamda yo'q; K: barcha 15 742 qirra teshigida «2» (format versiyasi bo'lishi mumkin — taxmin) | — | ❓ | K | S | L |

### 2.3 Dastur buyruqlari — frezalash

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-032 | Точка входа для фрезы (`ms`) | Kontur boshlanish nuqtasi: `x`, `y`, chuqurlik `dp`, asbob nomi; keyingi `ml/ma/mac` shu nuqtadan boshlanadi | `dp` ifoda (K: o'zgaruvchi `contMillDepth`) | ✅ | F, H, `xnc.py`, K (1 137) | S | H |
| XNC-033 | Korreksiya (`c`) | Asbob radiusi korreksiyasi: 0 — trayektoriya markazida, 1 — o'ngda, 2 — chapda, 3 — cho'ntak (карман) | 0 | 🟡 saqlanadi; c=3 uzunlikka kirmaydi, cho'ntakni to'ldirish va korreksiya chizmada yo'q | F, U (карманы), `program_stats` | M | M |
| XNC-034 | Chuqurlikka qadam (`sdp`) | Chuqur frezalashni bir necha o'tishga bo'ladi (пошаговое фрезерование вглубь) | ifoda | ❌ importer o'qimaydi | F, U | M | M |
| XNC-035 | Tekislikdagi qadam (`sxy`) | Cho'ntak to'ldirishda yon qadam | asbob `d/2` | ❌ (K: 352 ta ms da bor) | F, K | M | M |
| XNC-036 | Kirish turi (`in`) / chiqish turi (`out`) | `in`: 0 avto tanlash, 1 oddiy tushish; `out`: 0 avto, 1 oddiy ko'tarilish (yordamda «hali amalga oshirilmagan») | `in`=0, `out`=1 | ❌ importer o'qimaydi (K: 996 ta) | F, K | S | M |
| XNC-037 | Kirish/chiqish shabloni «RQG» | G — tur (0 avto, 1 tik, 2 urinma, 3 yon yoy); Q — Z bo'yicha qiya kirish (0/1); R — asbob radiusi koeffitsienti 1..5 (0 — stanok standarti). Stanok dasturiga bog'liq (yordamdagi jadval, rasmlar bilan): WoodWop va SCM Xilog uchun kirishda «avto» (G=0) qo'llanadi, chiqishda «avto» yo'q; Xilog'da kirish GIN, chiqish GOUT buyrug'i bilan, yoy (G=2) faqat radius korreksiyasi yoqilganda | G=0, R=0 | ❌ J2 dagi `mill_entry_code` kodda yo'q | H, J2 | M | M |
| XNC-038 | Фрезерование по прямой (`ml`) | Joriy nuqtadan (`x`,`y`) gacha to'g'ri chiziq | — | ✅ | F, IMG, `xnc.py`, K (2 653) | S | H |
| XNC-039 | Фрезерование по дуге (`ma`) | Oxirgi nuqta + radius `r` (manfiy — yo'nalish teskari), `dir` — soat strelkasi bo'yicha | — | ✅ | F, IMG, `arc_by_radius` | M | H |
| XNC-040 | Фрезерование по дуге с центром (`mac`) | Oxirgi nuqta + markaz (`cx`,`cy`) + yo'nalish; boshi = oxiri bo'lsa to'liq aylana | — | ✅ | F, IMG, `arc_sweep`, K (842) | M | H |
| XNC-041 | Yoy 3 nuqta bo'yicha | Boshi, oraliq nuqta (BX,BY) va oxiri orqali yoy | — | 🟡 bizda `MillArc3P` bor; GibLab teg/atribut nomlari yordamda yo'q | IMG, `arc_through` | M | M |
| XNC-042 | Скругление (fillet) | Ikki segment burchagini radius R bilan yumaloqlash | R | 🟡 palitrada bor (`MillFillet`), hisob va chizmada hisobga olinmaydi | IMG, `XncPanel.tsx`, `xnc.py` | M | M |
| XNC-043 | To'rtburchak frezalash | Rasmda: X,Y (markaz), L, W, burilish burchagi A, burchak radiusi R | — | 🟡 bizda X,Y,L,W,D; A va R yo'q; (X,Y) burchak yoki markaz ekani ❓ | IMG, U (20.08.03), `xnc.py` | M | M |
| XNC-044 | Ellips | Rasmda: X,Y (markaz), RL, RW, burilish burchagi A | — | 🟡 bizda A,B (burilishsiz); RL/RW ma'nosi (yarim o'q yoki to'liq) ❓ | IMG, U, `xnc.py` | M | L |
| XNC-045 | Bezier egri chizig'i | Ikonka resursi bor, matn yo'q | — | ❓ | IMG | L | L |

### 2.4 Paz, koordinata boshi va «oldingi qiymat» qoidasi

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-046 | Пазование (`gr`) | Arra bilan paz: boshi (`x1`,`y1`), oxiri (`x2`,`y2`; yo'q bo'lsa x1/y1), eni `t`, chuqurlik `dp`, korreksiya `c` (0 markaz, 1 o'ng, 2 chap), asbob nomi | — | 🟡 `c` va `p` (K: hujjatda yo'q, 441 ta) o'qilmaydi; hisob to'g'ri | F, `xnc.py`, K (619) | M | H |
| XNC-047 | Paz uzunligi / o'tishlar hisobi | Paz arra qalinligidan enli bo'lsa bir necha o'tishda; `countCut` shunga ko'ra | — | ✅ korpusga mos | `groove_passes`, `xnc_check.py`, `test_groove_passes` | M | M |
| XNC-048 | Начало координат (`xy`) | Dastur koordinata boshini siljitadi; ifodalarda `origin.x`, `origin.y` | — | ✅ | F, U, `xnc.py` (`Origin`), K | S | M |
| XNC-049 | «Oldingi qiymat» qoidasi | Atribut yozilmasa — shu turdagi oldingi buyruqdagi qiymat ishlatiladi (name, x, y, dp, ac, as, av, z, m, r, cx, cy …) | — | 🟡 J2 da yozilgan, evaluator da yo'q (yo'q atribut → 0 yoki standart); Bazis fayllarida hamma atribut yozilgani uchun sezilmaydi | F, J2, `xnc.py` | M | H |

### 2.5 Boshqaruv buyruqlari (dastur «Команды» — xizmat buyruqlari)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-050 | Комментарий (Com) | Izoh qatori, bajarilmaydi | — | ✅ | H, `xnc.py` | S | L |
| XNC-051 | Параметр (Par) | Shablon ishlatilganda foydalanuvchi kiritadigan parametr. GibLab parametr jadvali (tur, yorliq, ko'rinish sharti, qo'shimcha belgi, faqat o'qish) bilan bir xil tuzilishda bo'lishi ehtimol (taxmin) | — | 🟡 bizda Par = Var (nom, qiymat); kiritish oynasi va xossalar yo'q | H, `development/ParamGrid`, `xnc.py` | M | H |
| XNC-052 | Переменная (Var) | O'zgaruvchi e'lon qilish; turlari: integer, double, boolean, string | `double` | 🟡 faqat son (float) | H, E (types), K (`var`: name, type, expr, comment — 4 484 ta; hammasi double) | S | M |
| XNC-053 | Присвоить (Set) | O'zgaruvchiga qiymat berish | — | ✅ | H, `xnc.py` | S | H |
| XNC-054 | Если / Иначе (If / Else) | Shartli blok; Else bilan shart berilsa else-if | — | ✅ | H, `block()` | M | H |
| XNC-055 | Цикл WHILE / Цикл DO WHILE | Shartli sikl (oldingi / keyingi tekshirish) | — | ✅ cheksiz siklga qarshi chegara bilan | H, `block()` | M | M |
| XNC-056 | Прервать цикл / Продолжить | Sikldan chiqish / keyingi iteratsiya | — | ✅ | H, `block()` | S | M |
| XNC-057 | Подпрограмма / Вызвать подпрограмму / Выход | Qism dastur (Sub), chaqirish (Call), chiqish (Ret) | — | ✅ | H, `block()` | M | M |
| XNC-058 | Вывод сообщения (Msg) | Dastur bajarilganda xabar chiqaradi | — | 🟡 e'tiborsiz qoldiriladi, hech qayerda ko'rsatilmaydi | H, `xnc.py` (`Msg: continue`) | S | L |
| XNC-059 | Вывод ошибки (Err) | Xato xabari (to'xtatadimi yoki ogohlantiradimi — yordamda aniq emas) | — | ✅ ogohlantirish sifatida | H, `xnc.py` | S | L |
| XNC-060 | Buyruqlarni ichma-ich (daraxt) tahrirlash | If/While/Sub ichiga buyruq qo'shish | — | 🟡 model va evaluator `children` ni bajaradi; XNC paneli faqat tekis ro'yxat — blok ichiga qo'shib bo'lmaydi | `XncPanel.tsx`, `xnc.py` | M | H |
| XNC-061 | FOR sikli | Ikonka resursi bor (cmdFOR), buyruqlar jadvalida yo'q | — | ❓ | IMG | S | L |

### 2.6 Parametrik o'zgaruvchilar va ifoda tili

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-062 | `dx`, `dy`, `dz` | Zagotovka o'lchami ifodalarda | — | ✅ | F, `xnc.py` | S | H |
| XNC-063 | `allowanceT/B/L/R` | Zagotovka pripuski (yuqori/past/chap/o'ng) | 0 | ✅ | U (12.03.21), `calc.sync_xnc` | S | M |
| XNC-064 | Kromka o'zgaruvchilari `etj ett ebj ebt elj elt erj ert` | Har tomon kromkasi: `j` — prifugovka eni, `t` — qalinlik | 0 | ✅ | U, `calc.sync_xnc` | S | M |
| XNC-065 | `origin.x`, `origin.y`, `xncSide`, `bySizeDetail` | Koordinata boshi, tomon, «по размеру детали» | — | ✅ | U, `xnc.py` | S | M |
| XNC-066 | `xncIndex`, `xncIndexInPart` | Joriy operatsiya tartib raqami (loyihada / detalda) — kodlash uchun | — | ✅ | U (20.05.25/1), `calc.sync_xnc` | S | M |
| XNC-067 | Arifmetika: `+ - * / %` va daraja `^` | `%` — qoldiq; `^` — darajaga ko'tarish | — | 🟡 `^` rad etiladi (`**` ishlaydi) | E (mathExpression), `xnc.py` (`_BIN`) | S | M |
| XNC-068 | Butun son bo'linishi | Barcha operandlar butun bo'lsa natija ham butun (masalan 7/2 = 3); biri haqiqiy bo'lsa haqiqiy | — | ❓ bizda har doim haqiqiy (3.5) — shablonlarda farq chiqishi mumkin | E | S | M |
| XNC-069 | Taqqoslash `< > <= >= = == <> !=` | Mantiqiy natija true/false | — | 🟡 `=` va `<>` yo'q (`==`, `!=` bor) | E (boolExpression), `xnc.py` | S | M |
| XNC-070 | Mantiq `not and or xor`, `true/false` | Mantiqiy amallar va qiymatlar | — | 🟡 `xor` va `true/false` literallari yo'q | E | S | M |
| XNC-071 | `if(shart, a, b)` funksiyasi | Shartga ko'ra qiymat tanlash (GibLab ifodasida asosiy shartli konstruksiya) | — | ❌ bizda faqat `a if c else b` (Python uslubi) | E (boolExpression, miscFunctions), `xnc.py` | S | H |
| XNC-072 | Trigonometriya birligi (`sin cos tan`) | Yordam misollari **radian** ekanini ko'rsatadi (cos(1.5) = 0.0707, cos(pi) = −1) | — | 🟡 bizda **gradus** (J3) — shablon ko'chirilganda natija noto'g'ri bo'lishi mumkin; GibLab'da tekshirish kerak (6-bo'lim, savol 3) | E (mathFunctions), `xnc.py` (`_FUNCS`) | S | H |
| XNC-073 | `abs ceil floor round min max sqrt` | Standart matematik funksiyalar; `round(−1.5)` = −1, `round(2.5)` = 3 | — | ✅ (`round` manfiy .5 da farq: bizda −2) | E, `xnc.py` | S | L |
| XNC-074 | Qo'shimcha matematika: `acos acot asec asin atan cosh cot coth sec sinh tanh exp ln log log2 logx sign pi e random` | Teskari trig, giperbolik, logarifm, konstantalar | — | ❌ | E | S | L |
| XNC-075 | Satr turi va funksiyalari | Satr birlashtirish (`+`), `len mid left right lspace rspace rept ns empty trim ltrim rtrim ucase lcase find findr replace startswith endswith translit crc16 crc32 format` | — | ❌ (geometriya uchun kerak emas; kod/fayl nomi ifodalari uchun kerak) | E (stringFunctions, formatFunctions) | M | M |
| XNC-076 | Boshqa funksiyalar | `calculate` (satrdan hisoblash), `UUID`, `now(format)`, `DecToHex/HexToDec/DecToOct/OctToDec/DecToBin/BinToDec`, `roman` | — | ❌ | E (miscFunctions, nowFunction, numericConversion) | S | L |
| XNC-077 | «Пересчитать параметричность» | Changelog: XNC shablonida parametrikni qayta hisoblash imkoniyati; «Общие действия» da ham tugma bor | — | ❓ ma'nosi aniqlanmagan (Q_QA: qilinmadi) | U (20.08.03), Q_QA §2 | S | L |

### 2.7 Grafik redaktor (Шаблон yorlig'i)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-078 | Buyruqlar palitrasi | Asbob, 5 teshik, freza (kirish, to'g'ri, yoy, markazli yoy), koordinata boshi + xizmat buyruqlari tugmalari | — | ✅ 31 tugma (matnli, ikonkasiz) | H, `XncPanel.tsx` (PALETTE) | S | H |
| XNC-079 | Chizmani oldindan ko'rish | Dastur o'zgarganda detal chizmasi yangilanadi | — | ✅ (server SVG) | L, `xnc_drawing_svg` | M | H |
| XNC-080 | Sichqoncha bilan grafik chizish / nuqtani surish | Nuqta, chiziq, yoyni chizmada qo'yish va tahrir | — | ❌ (redaktor matn/parametr jadvali; chizma faqat ko'rish) | J7 (2-bosqich), `XncPanel.tsx` | L | M |
| XNC-081 | Показать все изображение | Chizmani oynaga sig'dirish (zoom-fit) | — | ❌ | H | S | L |
| XNC-082 | Panel со служебными командами (F4) | Xizmat (boshqaruv) buyruqlar panelini ko'rsatish/yashirish | F4 | 🟡 buyruqlar palitrada doim ko'rinadi, tugma/yorliq yo'q | H | S | L |
| XNC-083 | Состояние (F9) | Holat paneli — yordamda nima ko'rsatishi yozilmagan (bajarilish holati/xabarlar bo'lishi mumkin) | F9 | ❓ | H | S | L |
| XNC-084 | Переменные paneli | Dastur o'zgaruvchilari va qiymatlari | — | ❌ | H | S | M |
| XNC-085 | Добавить | Dasturga buyruq qo'shish | — | ✅ palitradan | H, `XncPanel.tsx` | S | H |
| XNC-086 | Qatorlarni ↑↓ ko'chirish, klonlash, o'chirish | Dastur tuzilmasini tahrirlash | — | ✅ | `XncPanel.tsx` | S | M |
| XNC-087 | Redaktor ichida Undo / Redo | Ikonkalar to'plamida bor (yordam matni yo'q) | — | 🟡 loyiha darajasidagi Ctrl+Z bor | IMG (ikonka nomlari), `store.editing` | S | L |
| XNC-088 | Buyruqni o'chirib/yoqish | Dasturda buyruqni vaqtincha o'chirish (`enable`) | — | ❌ (XNC-022 bilan bog'liq) | IMG, F | S | M |
| XNC-089 | Sozlash rejimi (breakpoint, qadam-baqadam, ishga tushirish) | Faqat ikonka nomlaridan taxmin; yordam matni yo'q | — | ❓ | IMG | L | L |
| XNC-090 | Buyruq parametrlarini ifoda sifatida kiritish | Har maydon son yoki ifoda (`dz/2`, `dx-50`) | — | ✅ | F, `XncPanel.tsx` (`parseParam`) | S | H |

### 2.8 Shablon va kutubxona (Библиотека обработок)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-091 | Shablonni faylga eksport / fayldan import | «Экспортировать» / «Импортировать» tugmalari: dasturni mahalliy faylga yozish/o'qish | — | ❌ | H | S | M |
| XNC-092 | Kutubxona: tipik frezalar to'plami | Yuklab olinadigan arxiv; rasmda 6 tur: bir tomonda radiusli kesim, ikki tomonda radiusli, doira kesim, ruchka ostida radiusli kesim, ruchka ostida to'rtburchak kesim, ikki tashqi radius | — | ❌ (shablonlarni o'zimiz noldan yozamiz) | `libraryXNC`, IMG | M | M |
| XNC-093 | Kutubxona: MDF fasad frezalari | Fasad panel profillari (rasmda 9 ta: arkali, yumaloq/kesilgan burchakli, egri yonli, chiziqli paz, burchak kvadratlari) | — | ❌ | `libraryXNC`, IMG | L | M |
| XNC-094 | Kutubxona: eshik nakladkalari | Eshik panellari uchun frezalar (rasmda 10 ta variant: katakli kesmalar, arka, to'lqinli, grek bezagi, kombinatsiyalar) | — | ❌ | `libraryXNC`, IMG | L | L |
| XNC-095 | Parametrik shablon | Dastur o'lcham (`dx/dy/dz`), pripusk, kromka va `Par` parametrlariga bog'liq bo'ladi — bitta shablon turli detalga mos | — | 🟡 ifodalar bor; Par kiritish oynasi yo'q (XNC-051) | H, F, U | M | H |
| XNC-096 | Mahsulot dasturi («Программа», parametrik mahsulot) | Mahsulot `program` (xml): parametrlar, o'zgaruvchilar, cheklovlar — mahsulot sonini/o'lchamini parametr orqali boshqaradi | — | ❌ (spec 3-bosqich) | F (product `program`), D4 | L | M |

### 2.9 Detalga biriktirish va kodlash

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-097 | Detalga XNC biriktirish | Detal xossalari → «Операции» → «Добавить: (XNC)»; operatsiya detalga havola qiladi | — | ✅ | J5, `add_xnc_for_part`, K (9 698 operatsiya — har birida 1 detal havolasi) | S | H |
| XNC-098 | Bir XNC — ko'p detal, bir detal — ko'p XNC | Detalda bir nechta XNC bo'lishi mumkin (`xncIndexInPart`) | — | ✅ | `Part.xnc_op_ids`, `calc.prune_xnc` | S | M |
| XNC-099 | Detal tavsifidagi `#kod` (lits) / `##kod` (orqa) | Probelsiz kodlar tavsifda: tomonga mos XNC dasturni nomi bo'yicha topish mexanizmi (yordamda faqat shu yozilgan) | — | ❌ real 205 faylda ishlatilmagan (0 / 11 971 detal tavsifi) | F, K, B_DOMAIN_RULES | M | L |
| XNC-100 | Detal jadvalida `'` belgisi | № yonida XNC bor detal belgisi | — | ✅ | `columns.tsx`, B_DOMAIN_RULES | S | M |
| XNC-101 | Kodlash (Кодирование) | Dastur kodini ifoda shabloni bilan yig'ish (o'lcham, tomon, `xncIndex`, `xncIndexInPart`, `xncSide`) | — | 🟡 faqat «Перекодировать XNC» (takrorlarga `-2`, `-3`); ifoda bilan yig'ish yo'q | U (20.05.25/1), L, `recode_xnc` | M | M |
| XNC-102 | «Объединить операции с одинаковым кодом и наименованием материала» | «Общие действия»: bir xil kod va material nomli XNC operatsiyalarni birlashtirish | — | ❌ («Оптимизировать операции» XNC ni birlashtirmaydi) | U (20.08.03), `main.py` | M | L |
| XNC-103 | Etiketkada XNC kodlari | Etiketka parametrlari `XNC1..XNC5`, `xncSideN`, `xncBSDN`; shtrixkod orqali stanokda dasturni ishga tushirish (har tomon uchun kamida 2 shtrixkod) | — | ❌ `labels.py` da XNC yo'q | `labels_ru`, `labels.py` | M | M |

### 2.10 Import (XNC bilan bog'liq)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-104 | Bazis-Mebelshik → `.project` (teshik, freza, paz) | Korxonaning asosiy oqimi: XNC dastur `program` xml sifatida keladi | — | ✅ 205 faylda 9 698 XNC operatsiya; importda xato yo'q (Q_QA) | `import/Bazis`, F, K, `legacy_project.py` | M | H |
| XNC-105 | MPR (WoodWop) importi | Changelog: MPR dan import tuzatishlari, nisbiy koordinatalar `@` belgisi bilan | — | ❌ | U | L | L |
| XNC-106 | Woody2 XML dan kontur ishlovi (XNC) | Import oynasida «Импорт контурной обработки (XNC)» belgisi | — | ❌ | `import/Woody` | M | L |
| XNC-107 | 3DConstructor / SketchUp-ABF / DXF import | Zenkovkali va zenkovkasiz asboblar ajratilishi; ABF dan DXF orqali, asbob nomi/diametri/chuqurligi profili | — | ❌ | U, `import/SketchUp.abf`, `import/parametr` | L | L |
| XNC-108 | Import sozlamalari: o'tuvchi teshik/freza pastdan chiqishi, o'tuvchi teshik asbobiga `S` qo'shimchasi | Skol bo'lmasligi uchun asbob teshikdan pastga chiqadi; asbob nomiga qo'shimcha | — | ❌ | `import/parametr`, `import/Bazis` | S | L |

### 2.11 XNC redaktor sozlamalari (Настройки → XNC Редактор) — `L` kuzatuvi

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-109 | Инструменты ro'yxati | Asboblar jadvali: Плоскость, Диаметр, Сквозное, Наименование, Глубина, Комментарий (qaysi tekislikda, diametr, o'tuvchi belgi, nom, chuqurlik, izoh) | — | ❌ asbob faqat dastur ichidagi `Tool` buyrug'ida | L (topshiriq), Q_QA §4 | M | M |
| XNC-110 | Палитра | Redaktor buyruqlar panelini sozlash (qaysi tugmalar ko'rinadi) | — | ❌ | L | S | L |
| XNC-111 | Ограничения | Redaktor cheklovlari — mazmuni noma'lum (changelog: «XNC postprotsessorlarida cheklovlar» qo'shilgan, XNC-125..127) | — | ❓ | L, U (20.04.14/1) | M | L |

### 2.12 Postprotsessor funksiyalari (batafsil — 3-bo'lim)

| ID | Funksiya | Qanday ishlaydi | Qiymatlar / standart | Bizda | Dalil | Murakkablik | Ustuvorlik |
|---|---|---|---|---|---|---|---|
| XNC-112 | Umumiy: stanok nomi prefiksi | «Добавлять префикс имени станка к названию файла» — fayl nomiga stanok nomi qo'shiladi | o'chiq | ✅ | L, `main.py` (`postprocess`), `machines_get/put` | S | M |
| XNC-113 | Umumiy: «Новый интерфейс» | Belgi; nimani o'zgartirishi noma'lum | — | ❓ | L | S | L |
| XNC-114 | Stanoklar nomlari ro'yxati | Har stanok o'z yorlig'ida; bizda 31 nom (19 pil markazi + 12 ishlov markazi) | — | 🟡 nomlar to'liq; `biesse_osi_plus` va `format4` «cnc» guruhida, lekin yordamda ular kroy kartalari/etiketkalar haqida (pil markazi) — guruhni tekshirish | L, `Biesse OSI+`, `Format4` sahifalari, `postprocessors.MACHINES` | S | M |
| XNC-115 | Yordam/changelogdagi qo'shimcha stanok nomlari | Bavelloni (shisha, OptyWay `.R01`), Excitech (E3/E4 GCode — detal ishlovi va nesting), HolzHer (NCHops `.hop`), Scheer (ScheerWin + chop moduli), AES Alpha (SS + chop moduli), Panhans (`.NCR`), KDT GCode (nesting), BIMA (ImaWop v6) | — | 🟡 Bavelloni, Excitech, HolzHer, AES Alpha, Panhans, KDT GCode, BIMA ro'yxatda yo'q (Scheer, Shelling MCS, Nanxing, NC Studio GlassGCODE bor) | U, `postprocessors.MACHINES` | S | L |
| XNC-116 | Stanokni yoqish/o'chirish va shablon biriktirish | Faqat yoqilgan stanok «Постпроцессор» ro'yxatida ko'rinadi; unga format shabloni (profil) biriktiriladi | — | ✅ | `api_extra.machines_put`, `Settings.tsx` (`MachinePane`), `test_machines_mes.py` | S | M |
| XNC-117 | Har stanok uchun alohida sozlamalar sxemasi | Har stanok yorlig'ida o'z maydonlari (quyidagi XNC-118..133) | — | ❌ faqat yoqish + shablon | `pp_machines` (`enabled`, `profile`, `prefix`) | M | M |
| XNC-118 | Fayl nomi shabloni (ifoda) | Ifoda; operatsiya parametrlari mavjud (Holzma PTX: standart `project.name + ' ' + operation.name`) | satr | ❌ bizda nom qat'iy: `{loyiha №}_{operatsiya kodi/nomi}` | `HolzmaPTX` sahifasi, `postprocessors.render_template` | S | M |
| XNC-119 | Fayl papkasi / kodlash / qator oxiri | Fayl parametrlari (L: «fayl parametrlari») | — | 🟡 kodlash va qator oxiri profilda bor; papka (yo'l) yo'q — brauzer yuklaydi | L, `PostprocessorProfile` | S | L |
| XNC-120 | Oldindan torsovka (предварительная торцовка) | Stanok sozlamasi (L: «torsovka oldindan kesish»); aniq ma'nosi yordamda yo'q | — | ❓ | L (D12) | M | L |
| XNC-121 | Etiketka uchun qo'shimcha ma'lumotlar | Ifodalar jadvali (qator = stanok yozuvi maydoni); «qatorni standartga qaytarish» va «detalning barcha parametrlari (o'zgaruvchilar)» ro'yxati tugmalari (Biesse OSI+, Format4) | ifoda | ❌ | `BiesseOsiPlus`, `Format4` sahifalari | M | M |
| XNC-122 | User defined part info records (PARTS_UDI) | Detal bo'yicha foydalanuvchi yozuvlari — ifodalar ro'yxati (Holzma PTX) | ifoda | ❌ | `HolzmaPTX` sahifasi | S | L |
| XNC-123 | Biesse OSI+: «Ориентация» | Kroy kartalari stanokda gorizontal yoki vertikal ko'rsatilishi | gor./vert. | ❌ (stanok formati hali yo'q) | `BiesseOsiPlus` | S | L |
| XNC-124 | Felder Format4: «Помещать остатки на карты кроя» | Belgi: stanok hisobga olinadigan qoldiqlar uchun ham etiketka chop etadi | o'chiq | ❌ | `Format4` | S | L |
| XNC-125 | Ishlov markazlari: «Разворачивать деталь кромкой в…» — afzallik | Detal kromka tomoni stol burchagiga qaratib aylantiriladi: chap-yuqori / chap-past / o'ng-yuqori / o'ng-past | 4 variant | ❌ (J6 da yozilgan, kodda yo'q) | U (20.10.23), J6 | M | M |
| XNC-126 | Ishlov markazlari: shu burilish — majburiy cheklov | Afzallik emas, qat'iy talab | 4 variant | ❌ | U (20.10.23) | M | M |
| XNC-127 | Ishlov markazlari: «Разворачивать деталь длинной стороной» | Uzun tomon gorizontal yoki vertikal bo'lsin | 2 variant | ❌ | U (20.10.23) | S | M |
| XNC-128 | KDT/WDX (Trepan) — ikki tomonlama ishlov | 3 kallakli markazlarda ikki tomonlama ishlov; zenkovkali teshikning maksimal uzunligi sozlamasi | — | ❌ | U (20.04.14/1, 12.03.21) | M | L |
| XNC-129 | Homag CadMatic v4 — kesish tartibi | Kesishni torsovkadan yoki qoldiqdan boshlash | 2 variant | ❌ | U (20.05.25/1) | S | L |
| XNC-130 | KDT/WDX XML — bir xil o'lchamli detallarni birlashtirish | Paketli kroyda etiketkalar to'g'ri chiqishi uchun | belgi | ❌ | U (20.05.25/1) | S | L |
| XNC-131 | Elmo3: kartani raqam bilan chaqirish | Barcha kartalar bitta arxivda; arxiv stanok USB'ida «SAW» papkasiga ochiladi; karta — «kroy raqami.karta raqami» (masalan 0561.0001) | — | 🟡 `per_map` zip bor; nomlash qoidasi shablonda yoziladi | `Elmo3`, IMG, `render_template` | S | L |
| XNC-132 | Fayllarni stanokka yetkazish ko'rsatmalari | Vitap Bridge: arxivdan chiqarib USB `\Bkp\Device\Cn\Drw\EDT` ga; BiesseWorks: dasturlar `C:\WNC\home\d_xnc\p_p\prog` dan yuqori papkaga qo'yilmasin; Nanxing NXCutSaw: AutoSAW da «Open File»; Elmo3: yuqoridagi tartib | — | ❌ (har stanok yorlig'ida izoh matni) | `VitapBridge`, `BiesseWorks`, `Elmo3`, `NXCutSaw.png` | S | L |
| XNC-133 | Xilog3 yuzalari va Format4 yozuvlari tavsifi | Xilog3: yuzalar F1..F5 koordinata o'qlari va yo'nalishlari (rasm); Format4: MA000/MA005/MA010/MA015 yozuvlari (rasm) — format ma'lumotlari postprotsessor dasturchilariga | — | ❌ (ma'lumot; kod emas) | `Xilog3`, `Format4`, IMG | S | L |

## 3. Postprotsessorlar bo'limi

### 3.1 GibLab «Постпроцессоры» oynasi tuzilishi

- **Yorliqlar:** «Общие» + har stanokka alohida yorliq. Stanoklar (`L`): SCM WinCut, SCM MaestroCut, HOLZMA PTX, HOLZMA CadMatic4,
  HOLZMA CadMatic3, Biesse OSI, Biesse NC300, FELDER Format4 PC6, FELDER Format4 PC7, F4Classic, Homag CHF 41/44/44 NPS400,
  KDT-PreSize QK, KDT-PreSize XML, Scheer, Nanxing CutSawFG, Nanxing NXCutSaw, Shelling MCS, ELMO 3, GlassGCODE (19 ta — pil
  markazlari). Ishlov markazlari (XNC) sahifalari yordamda alohida: Biesse OSI+, BiesseWorks, Format4, G-Code, iLenia, KDT Trepan,
  MW310, TPA, Vitap Bridge, WoodWop, XD WoodCam, Xilog3.
- **«Общие» yorlig'i:** «Новый интерфейс»; «Добавлять префикс имени станка к названию файла».
- **Har stanok yorlig'i** (`L`, D12 bo'yicha): fayl parametrlari, oldindan torsovka, etiketka ma'lumoti, «User defined part info
  records». Qaysi stanokda qaysi maydonlar borligi — quyidagi jadval (yordamda yozilgani).
- Yangi stanoklar va sozlamalar tarixi (`U`): qo'shilgan formatlar ro'yxati XNC-115; ishlov markazlari uchun «afzallik» va
  «cheklov» (XNC-125..127); KDT Trepan, CadMatic v4, KDT XML maxsus sozlamalari (XNC-128..130); Felder Format4 PC7 etiketkalar
  tayyorlash bilan; KDT GCode nesting uchun.
- Postprotsessor GibLab saytida demo sifatida bo'lgan, keyin obunaga o'tgan; mahalliy versiyada stanokka mos postprotsessorlar
  bilan beriladi (`post_ru`) — funksional ma'lumot emas.

### 3.2 Yordamdagi har stanok sahifasi nimani tavsiflaydi (faqat haqiqatan yozilgani)

| Sahifa | Yordamda yozilgan | Yordamda **yo'q** |
|---|---|---|
| Biesse OSI+ | «Ориентация» (kartalar stanokda gorizontal yoki vertikal); «Дополнительные данные для этикеток» jadvali (qatorlar ifodalar, qatorni standartga qaytarish va detalning barcha parametrlari ro'yxati tugmalari) | Fayl formati, maydonlar ro'yxati |
| BiesseWorks | Dasturlar stanokda `C:\WNC\home\d_xnc\p_p\prog` dan yuqori papkaga qo'yilmasligi kerak | Format, sozlamalar |
| Elmo3 (Altendorf) | Kartalar bitta arxivda saqlanadi → USB «SAW» papkasiga ochiladi → stanokda «Оптимизация / Карта кроя» → «man» → «kroy raqami.karta raqami» (rasm: 0561.0001) → «Старт» | Fayl formati |
| Format4 (Felder) | «Помещать остатки на карты кроя»; etiketka qo'shimcha ma'lumotlari jadvali; **rasmda fayl yozuvlari**: MA000 (sarlavha), MA005 (material kodi), MA010 (detal), MA015 (qo'shimcha detal ma'lumoti) — maydon pozitsiyalari va uzunliklari bilan; qizil ramkali maydonlar foydalanuvchi matni (sarlavha matni, material izohlari 1–3, qirra kodi, detal matnlari 1–11) | Fayl nomlash, sozlash tartibi |
| Holzma PTX | «Общие» → «Шаблон имени файла» (ifoda, qiymat turi satr, operatsiya parametrlari mavjud, standart `project.name+' '+operation.name`); «User defined part info records (PARTS_UDI)» — ifodalar ro'yxati | PTX fayl formati |
| Vitap Bridge | Dasturlar arxivdan chiqarilib USB'da `\Bkp\Device\Cn\Drw\EDT` papkasiga nusxalanadi | Format |
| Xilog3 | Faqat rasm: 5 ta yuza (F1 — asosiy, F2 — o'ng, F3 — chap, F4 — pastki, F5 — yuqori) uchun X/Y o'qlari yo'nalishi, «lh/rh» strelkalari (taxminan radius korreksiyasi tomoni) va yoy yo'nalishi (G3) | Matn, format |
| Nanxing NXCutSaw | Faqat skrinshot: stanok dasturida «Open File» orqali fayl yuklanadi | Matn, format |
| G-Code, iLenia, KDT Trepan, MW310, TPA, WoodWop, XD WoodCam | **Bo'sh sahifalar** | Hammasi |
| `postprocessor_ru` | Faqat «Biesse OSI PLUS» kartochkasi (rasm) | — |

**Xulosa:** stanok fayl formatlarining sintaksisi yordamda deyarli yo'q (faqat Format4 yozuvlari va Xilog3 yuzalari rasm sifatida) —
format mantiqini korxona dasturchilari o'zlari yozadi (foydalanuvchi ko'rsatmasiga mos). Bizga kerak: nomlar, sozlamalar sxemasi,
ulanish nuqtalari.

### 3.3 Bizning shablon tizimini moslashtirish (taklif)

Hozir: `postprocessors.py` — `BUILTIN` (csv, commands, dxf, json), `MACHINES` (31 nom: `saw` va `cnc` guruhlari), `pp_machines`
sozlamasi `{enabled, profile, prefix}`; foydalanuvchi shabloni — Jinja2 (xavfsiz sandbox, `PostprocessorProfile`: nom, kengaytma,
`per_map`, kodlash, qator oxiri); yuklab olish: `GET /projects/{pid}/operations/{oid}/postprocess?key=machine:<kalit>`. Faqat CS kroy.

**1) Stanoklar ro'yxati.** `MACHINES` ga XNC-115 dagi 7 ta nom qo'shiladi (guruh: `saw` / `cnc` / `glass`). Faqat nom + kalit + guruh.

**2) Har stanok uchun sozlamalar sxemasi (JSON).** `pp_machines` ga `settings` qo'shiladi; har stanokning maydonlari
`MACHINE_OPTIONS = {kalit: [maydon spetsifikatsiyalari]}` registrida (kalit, tur, standart, ru/uz yorliq) — UI shundan formani
quradi, server shundan tekshiradi. Faqat **yordamda tasdiqlangan** maydonlar (qolganlarini stanok dasturchisi qo'shadi):

```json
{
  "enabled": {"biesse_osi": true},
  "profile": {"biesse_osi": 12},
  "prefix": true,
  "settings": {
    "_common":          {"name_expr": "project.name + ' ' + op.name", "folder": "", "pre_trim": null},
    "biesse_osi_plus":  {"orientation": "horizontal"},
    "felder_format4_pc7": {"remnants_on_maps": false,
                          "label_fields": {"MA000.text": "", "MA005.headline1": "", "MA010.edge_code": "", "MA010.text1": ""}},
    "holzma_ptx":       {"name_expr": "project.name + ' ' + op.name", "parts_udi": []},
    "holzma_cadmatic4": {"cut_order": "from_trim"},
    "kdt_presize_xml":  {"merge_equal_parts": false},
    "kdt_trepan":       {"two_sided": false, "max_countersink_len": 0},
    "_cnc":             {"edge_corner": null, "edge_corner_mode": "preference",
                          "long_side": "any"}
  }
}
```

Izoh: `_common` va `_cnc` — barcha stanoklar / barcha ishlov markazlari uchun umumiy standartlar (stanok o'z qiymati bilan almashtiradi).
Yordamdagi Biesse OSI+ va Format4 sahifalari kroy kartalari/etiketkalar haqida bo'lgani uchun ular pil markazlari guruhiga tegishli bo'lishi ehtimol
(XNC-114). `orientation` ∈ {horizontal, vertical}; `cut_order` ∈ {from_trim, from_remnant}; `edge_corner` ∈ {LT, LB, RT, RB, null};
`edge_corner_mode` ∈ {preference, restriction} (afzallik / majburiy); `long_side` ∈ {any, horizontal, vertical}. Maydon nomlari bizniki
(GibLab nomlari emas); mazmuni yordam/changelog asosida. `label_fields` kalitlari Format4 rasmidagi foydalanuvchi maydonlariga mos
(boshqa stanoklarda — o'z ro'yxati). `pre_trim` ma'nosi aniq emas (savol 6) — vaqtincha sxemaga kiritilmasin.

**3) Yoqish/o'chirish.** Hozirgi `enabled`/`profile` (✅). Qo'shimcha: har stanokda «formati ulanmagan» belgisi (✅ bor), «Ishlov markazlari
(XNC)» guruhi uchun ham `postprocessors` ro'yxatida alohida bo'lim (hozir faqat `saw` ko'rsatiladi).

**4) Fayl nomi qoidalari.** (a) `name_expr` — Jinja ifoda (`{{ project.name }} {{ op.name }}`; GibLab PTX standartiga o'xshash standart);
(b) `prefix` — hozirgi (✅) `{stanok}_` ; (c) `_safe_name` (harf/raqam/`_-`) saqlanadi; kirill harflari ruxsat (`isalnum`); (d) `per_map` zip ichida
`{base}_{NN}.{ext}`; (e) Elmo3 kabi «kroy raqami.karta raqami» uchun kontekstga `map.number` (`0561.0001` ko'rinishi) qo'shiladi —
format yozishni dasturchi qiladi.

**5) XNC (ishlov markazi) konteksti.** Hozir kontekst faqat CS (`maps`, `parts`). XNC uchun `context_xnc(project, op)`:
`xnc = {code, name, dx, dy, dz, qty, side, turn, mirror_x, mirror_y, origin, part: {uid, name, edges}, ops: [...], tools: [...]}`, bu yerda
`ops` — `xnc.evaluate()` natijasi (ifodalar hisoblangan geometrik amallar ro'yxati: `kind`, `X`, `Y`, `Z`, `D`, `DP`, `T`, yoy parametrlari).
Burish/ko'zgu/koordinata boshi **oldindan qo'llangan** (chizma `_View` mantig'i) — shablon tayyor koordinata oladi. Cheklovlar
(XNC-125..127) shu bosqichda qo'llanadi. Endpoint: `GET /projects/{pid}/operations/{oid}/postprocess` XNC operatsiyaga ham ishlasin
(`_need_cs` dan keyin ajratish) va XNC-018 tugmasi shuni chaqirsin.

**6) Tegadigan fayllar:** `backend/app/services/postprocessors.py`, `backend/app/api_extra.py` (`machines_get/put`), `backend/app/main.py`
(`postprocess`), `backend/app/services/xnc.py` (`context_xnc`), `backend/app/models.py` (agar yangi model), `frontend/src/features/settings/Settings.tsx`
(`MachinePane` maydonlar formasi), `frontend/src/features/xnc/XncPanel.tsx` (XNC-018 tugmasi), `frontend/scripts/i18n_src.py`, testlar
(`test_machines_mes.py`).

## 4. `.project` formati: yetishmayotgan teglar/atributlar va eksport

Asos: `format_ru.html` (hujjat), `Example1.project` (misol) va 205 real fayl skani (`K`, faqat atribut nomlari). `legacy_project.py` o'qimaydigan
narsalar quyida. «Hujjatda» — `F` da yozilgan; «Real» — hujjatda yo'q, lekin Bazis/GibLab fayllarida bor.

### 4.1 O'qilmaydigan atribut/teglar (import)

| ID | Element.atribut | Manba | Ma'nosi | Hozir | Ustuvorlik |
|---|---|---|---|---|---|
| PRJ-001 | `part.allowanceT/B/L/R` | hujjatda | Zagotovka pripuski (yuqori/past/chap/o'ng) — XNC o'zgaruvchilari va pilniy o'lchamga ta'sir qiladi | O'qilmaydi (`Part.allow_*` bor, lekin importer to'ldirmaydi; real fayllarda yo'q) | M |
| PRJ-002 | `part.groupInBlock`, `groupInBlockMC`, `groupInBlockMaxC` | hujjatda | Detallarni blokka guruhlash (0/1 uzunlik/2 en; min/maks) | O'qilmaydi (`group_by/min/max` bor) | M |
| PRJ-003 | `part.description` (`#kod` / `##kod`) | hujjatda | XNC dastur kodlari | O'qilmaydi (`Part.description` faqat `part.designation` dan); real fayllarda detalda `description` yo'q | L |
| PRJ-004 | `part.cl`, `cw` | hujjatda + real | Pilniy o'lcham (ixtiyoriy) | O'qilmaydi; tekshiruv uchun foydali | L |
| PRJ-005 | `part.dbId` / list `dbId` | `remainders_ru` | Ombor (1C) ID | O'qilmaydi; real fayllarda yo'q | L |
| PRJ-006 | `part.usedCount`, `sheetId`, `business`, `waste`, `rl`, `rw` (list/qoldiq) | hujjatda + real | Ishlatilgan soni, qoldiq belgilari | Qoldiqlar (`waste`) o'tkazib yuboriladi (qasddan) | L |
| PRJ-007 | `part.position`, `part.eltMat/elbMat/ellMat/elrMat` | real | Pozitsiya raqami; har tomon kromka materiali nomi (matn) | O'qilmaydi (kromka operatsiyasi havolasi orqali nom olinadi) | L |
| PRJ-008 | `project.version`, `project.uuid`, `importBMV` | hujjatda (version) + real | Format versiyasi; loyiha UUID; Bazis import belgisi (185/205 faylda) | O'qilmaydi | L |
| PRJ-009 | `project.costOperation/costMaterial/cost` | hujjatda | Jami narxlar | Qasddan o'qilmaydi (qayta hisoblanadi) | L |
| PRJ-010 | `product.phone1`, `phone2`, `description`, `date`, `program` | hujjatda | Mahsulot: telefonlar, tavsif, tayyor sanasi, parametrik dastur | `Product.phone1/2` bor, importer to'ldirmaydi; `program` — yo'q | L |
| PRJ-011 | `operation.owner`, `costOperation/costMaterial/costTotal`, `description` (XNC/CS/EL) | hujjatda | Operatsiya egasi; narxlar; tavsif | XNC va EL tavsifi o'qilmaydi (GR/CS faqat qisman) | L |
| PRJ-012 | `material.count`, `material.used` | hujjatda | Operatsiyada material miqdori va vazifasi (`base`) | O'qilmaydi (`base` deb qabul qilinadi) | L |
| PRJ-013 | CS `cGroupParts`, `cSortPatterns`, `cutLength`, `cutCount` | real (hujjatda yo'q) | Guruhlash/saralash va kesim statistikasi satrlari | O'qilmaydi | L |
| PRJ-014 | EL `elPreMillingEqual`, `elLength` | real | Kromka parametrlari | O'qilmaydi | L |
| PRJ-015 | CS `draw`, `data` (kartalar) | hujjatda | Kroy kartalari | Qasddan o'qilmaydi (CLAUDE.md qoida 5) | — |
| PRJ-016 | CL / O / SP / LB operatsiyalari (+ `good typeId="simple"`, `band` pogonaj) | hujjatda | Погонажный раскрой, комплектация, обработка поверхности, этикетки | Importer o'tkazib yuboradi va ogohlantiradi; 205 faylda faqat CS, EL, XNC va 3 ta LB | L |
| PRJ-017 | XNC `ms`: `sdp`, `sxy`, `in`, `out` | hujjatda + real | Chuqurlik/tekislik qadami, kirish/chiqish | O'qilmaydi (K: `in/out` 996, `sxy` 352 ta) | M |
| PRJ-018 | XNC `gr`: `c`, `p` | hujjatda (`c`) + real (`p`) | Paz korreksiyasi; `p` hujjatda yo'q | O'qilmaydi | L |
| PRJ-019 | XNC qirra teshigi: `m`, `ver` | hujjatda (`m`) + real (`ver`) | Z o'rtada; `ver` hujjatda yo'q | O'qilmaydi | M |
| PRJ-020 | XNC har tegda `enable` | hujjatda | Buyruqni o'chirish | O'qilmaydi; real fayllarda yo'q | M |
| PRJ-021 | XNC `ml`/`mac`: `dp` | hujjatda | Chuqurlik (`ml`, `mac` da yozilishi mumkin) | O'qilmaydi (`ma` da o'qiladi) | L |
| PRJ-022 | XNC boshqaruv teglari (par, set, if, else, while …) va yangi frezalar (3 nuqtali yoy, to'rtburchak, ellips, fillet, Bezier) | — | **Teg nomlari yordamda yo'q**; real 205 faylda uchramaydi | Noma'lum teglar `unknown` ro'yxatiga tushadi va importda ogohlantiriladi (✅ to'g'ri xatti-harakat) | M — namuna `.project` kerak |
| PRJ-023 | XNC `var`: `expr`, `type`, `comment` | real | O'zgaruvchi e'loni (hujjatda teg yo'q) | ✅ o'qiladi (type e'tiborsiz — double) | — |

### 4.2 Eksport (bizda yo'q) — minimal talablar

Loyihaning o'z fayl formatini yozish (GibLab bilan ikki tomonlama ishlash, ma'lumotni qaytarish) kerak bo'lsa. Hujjat va `Example1.project` bo'yicha **minimal to'g'ri fayl**:

- Ildiz `<project version="1" currency="...">` (UTF-8 XML). O'lchamlar mm; mantiqiy — `true`/`false`; sana — epoch millisekund (`date`, `orderDate`; real fayllar).
- Hamma `id` — butun, loyiha bo'ylab noyob (`good`, `part`, `operation`). Havola: detalda kromka/paz — `"@operation#N"`; operatsiyada detal/material — `<part id=".."/>`, `<material id=".."/>`.
- `good typeId="product"` (`id`, `name`, `count`, `code`) + ichida `<part id l w count txt name elt/elb/ell/elr=...>` (o'lcham atributlari kiritish rejimiga mos: `l/w` yoki `dl/dw` yoki `jl/jw`).
- `good typeId="tool.cutting"` (`id`, parametrlar ixtiyoriy), `good typeId="sheet"` (`id`, `name`, `code`, `t`, `l`, `w`, `count`, `cost`; ichida `<part id l w count usedCount>` — list), `good typeId="band"` (`w`, `t`, `cost`) va `good typeId="tool.edgeline"`.
- `operation typeId="CS"` (`id`, `tool1`, `cSizeMode`, parametrlar ixtiyoriy) + `<part id/>` havolalar + `<material id/>`; `operation typeId="EL"` (`tool1`) + detallar + material.
- XNC: `operation typeId="XNC"` (`id`, `code`, `side`, `bySizeDetail`, `program`=xml satr — **majburiy**; `count`, `turn`, `mirHor`, `mirVert`, narxlar ixtiyoriy) + `<part id/>`; `program` ildiz `dx dy dz` va ichida `tool`, `var`, `bf/bl/br/bt/bb`, `ms/ml/ma/mac`, `gr`, `xy`.
- **Qasddan yozilmaydi:** CS `data` (ikkilik kartalar), `draw`; GibLab bu natijani qayta kroy qiladi.
- Qiyinchilik/ustuvorlik: M / L (korxonaga GibLab'ga qaytarish kerakmi — 6-bo'lim, savol 9). Ma'lumot egasi korxona; CLAUDE.md qoidasi 4 «fayl formatlari nusxalanmaydi» deydi — eksport faqat foydalanuvchi aniq so'rasa va faqat korxona o'z ma'lumotini chiqarishi uchun.
- Joy: `backend/app/plugins/` ga `legacy_project_export.py` (yangi), `GET /projects/{pid}/export?format=project`; test — `test_import_giblab_project` bilan aylanma (round-trip).

## 5. Yetishmayotganlar (❌ va 🟡) — ustuvorlik bo'yicha

### H (yuqori)

| # | Nima | Nega | Nima qilish | Tegadigan fayllar |
|---|---|---|---|---|
| 1 | Teshik massivi `AC/AS/AV` (XNC-025) | Importer saqlaydi, hisob/chizma sanamaydi → massivli GibLab shablonlarida teshiklar soni, narx va chizma noto'g'ri | `Drill*` da `AC/AS/AV` ni o'qib `count` ni hisoblash va holat jadvali/chizmada yoyish; test: `ac=3 as=32` | `backend/app/services/xnc.py` (`command`, `xnc_holes_table`, `xnc_drawing_svg`), `tests/test_qa_fix_calc.py` |
| 2 | «Oldingi qiymat» qoidasi (XNC-049) | J2 da talab, kodda yo'q — qo'lda yozilgan/kutubxona dasturlarida tushib qolgan atribut 0 bo'ladi | `_Run` da tur bo'yicha oxirgi qiymatlarni (name, x, y, dp, z, m, r, …) saqlash va yo'q atributga qo'llash | `xnc.py` (`_Run`, `command`) |
| 3 | Ifoda tili mosligi (XNC-067, 069, 070, 071, 072) | GibLab shablonlari `if(c,a,b)`, `=`, `<>`, `^`, `xor`, `true/false` ishlatadi; trig birligi farq qiladi | `eval_expr` ga `if()` funksiyasi, `=`/`<>`, `^`, `xor`, `true/false`, `pi`, `e` qo'shish; trig birligini GibLab bilan tekshirib tanlash (savol 3) | `xnc.py` (`_ev`, `_FUNCS`, `_BIN`, `_CMP`), `tests/test_integrity.py` |
| 4 | Ichma-ich buyruqlar tahriri (XNC-060) | `children` modeli bor, UI da blok ichiga qo'shib bo'lmaydi → If/While/Sub amalda foydalanib bo'lmaydi | Daraxt ko'rinishi (chekinish), «blok ichiga qo'shish», ko'chirish | `frontend/src/features/xnc/XncPanel.tsx` |
| 5 | XNC shablon saqlash/ochish + eksport/import (XNC-016, 091) | Shablon qayta ishlatilmaydi — har safar dastur qo'lda yoziladi | Shablonlar katalogi (settings profili `xnc_template`: nom, papka, `program`), «Открыть/Сохранить/Экспорт/Импорт» | `services/settings.py` (yangi scope), `main.py`, `XncPanel.tsx`, `i18n_src.py` |
| 6 | `Par` kiritish oynasi (XNC-051, 095) | Parametrik shablonning mohiyati: detalga qo'yilganda qiymat so'raladi | `Par` ga tur/yorliq/qiymat sxemasi; operatsiya «Параметры» da kiritish maydonlari | `models.py`, `xnc.py`, `XncPanel.tsx` |
| 7 | Importer: `m`, `enable`, `sdp/sxy/in/out`, `gr c/p` (XNC-022, 030, 034..036, 046, 088; PRJ-017..020) | Statistikaga ta'sir qilmaydi, lekin stanokka chiqarishda zarur; yo'qolgan ma'lumot | `program_to_commands` da o'qish; `XncCommand.enabled` (+ evaluator) | `legacy_project.py`, `models.py`, `xnc.py` |

### M (o'rta)

| # | Nima | Nega | Nima qilish | Tegadigan fayllar |
|---|---|---|---|---|
| 8 | XNC → ishlov markazi formatiga chiqarish (XNC-018, 117, 125..127) | Stanokka dastur chiqarish; formatni dasturchilar yozadi, bizga kontekst va tugma kerak | 3.3 bo'limi: `context_xnc`, `postprocess` ni XNC ga ochish, burish/cheklov qoidalari | `postprocessors.py`, `main.py`, `xnc.py`, `XncPanel.tsx` |
| 9 | Stanok sozlamalari sxemasi (XNC-117..124) | Hozir faqat yoqish + shablon | 3.3 bo'limi: `MACHINE_OPTIONS`, `settings` JSON, UI formasi, `name_expr` | `postprocessors.py`, `api_extra.py`, `Settings.tsx` |
| 10 | Frezalash turlari (XNC-033..036, 041..044) | Cho'ntak, chuqurlikka qadam, fillet, to'rtburchak A/R, ellips — chizma va hisob | `MillFillet` ni bajarish; `ms` `sdp/sxy/in/out`; `MillRect` `A`, `R`; namuna `.project` bilan teg nomlarini tasdiqlash | `xnc.py`, `legacy_project.py`, `XncPanel.tsx` |
| 11 | RQG kirish/chiqish kodi (XNC-037) | Kod bo'yicha stanok dasturiga moslash (WoodWop/Xilog) | `mill_entry_code()` ni yozish (spec: `213` → R=2, Q=1, G=3), `ms` `in/out` bilan bog'lash | `xnc.py` |
| 12 | Etiketkada XNC kodlari (XNC-103) | Stanokda dasturni shtrixkod bilan ishga tushirish | Etiketka kontekstiga `XNC1..5`, `xncSideN`, `xncBSDN` | `labels.py` |
| 13 | Kodlash ifodasi (XNC-101) | Dastur kodini o'lcham/tomon/indeksdan avtomatik yig'ish | Kod shabloni (ifoda) + «Кодирование» amali | `main.py`, `calc.py`, `ProjectMenu.tsx` |
| 14 | Satr funksiyalari (XNC-075) | Kod/fayl nomi/etiketka ifodalari uchun | Satr turi va `left/right/mid/len/trim/find/replace/format/translit` | `xnc.py` yoki umumiy `expr.py` |
| 15 | Kutubxona (XNC-092..094) | Ruchka kesmasi, fasad frezalari — tez-tez takrorlanadi | Shablonlarni noldan tayyorlash (parametrik, 5–10 ta tipik) | yangi shablonlar fixture |
| 16 | Redaktor sozlamalari: asboblar ro'yxati (XNC-109) | `Tool` nomlari bir joyda | Asbob katalogi (tekislik, diametr, o'tuvchi, nom, chuqurlik, izoh) | `settings.py`, `Settings.tsx`, `XncPanel.tsx` |
| 17 | O'zgaruvchilar paneli (XNC-084), Var turlari (XNC-052) | Dastur nosozligini topish | Panel: hisoblangan qiymatlar; `Var` ga `type` | `XncPanel.tsx`, `xnc.py` |
| 18 | DXF import (XNC-019) | Tayyor chizmadan dastur olish | Avval qoidani aniqlash (savol 7) | yangi `importers`/`xnc_dxf.py` |
| 19 | Detalga biriktirish tugmalari (XNC-015) | XNC panelidan detal tanlash/ajratish | Tugmalar | `XncPanel.tsx`, `main.py` |
| 20 | Importer: `allowance*`, `groupInBlock*` (PRJ-001, 002) | Detal pripuskini/guruhlashni yo'qotmaslik | Atributlarni `Part.allow_*`, `group_*` ga o'tkazish | `legacy_project.py` |
| 21 | Grafik tahrir — sichqoncha bilan nuqta/chiziq qo'yish (XNC-080) | Hozir chizma faqat ko'rish; GibLab redaktori grafik (J7 2-bosqich) | Avval 7–10 qatorlarni yopib, keyin SVG ustida nuqta tanlash/surish | `XncPanel.tsx`, `xnc.py` (SVG ga `data-` indekslar) |
| 22 | Mahsulot dasturi (parametrik mahsulot, XNC-096) | Mahsulot o'lchamini parametr bilan boshqarish (spec 3-bosqich) | `Product.program` + «Свойства → Программа» | `models.py`, `ProductProps.tsx`, `legacy_project.py` (`program`) |
| 23 | Stanoklar guruhini tekshirish (XNC-114) | `biesse_osi_plus`, `format4` yordamda kroy kartalari haqida | Guruhni `saw` ga ko'chirish yoki foydalanuvchi bilan tasdiqlash | `postprocessors.py` (`MACHINES`) |
| 24 | Butun son bo'linishi (XNC-068) | GibLab `7/2 = 3` bo'lishi mumkin; shablon ko'chirilganda farq | 6-bo'lim, 14-savol javobiga qarab | `xnc.py` (`_BIN`) |

### L (past)

Bularning hammasi mebel korxonasi kunlik ishiga ta'sir qilmaydi yoki ma'nosi noma'lum:

- ❌: XNC-013 (standart narx), 074, 076 (qo'shimcha funksiyalar), 081 (zoom-fit), 094 (eshik nakladkalari), 099 (`#kod`), 102 (operatsiyalarni birlashtirish),
  105–108 (MPR, Woody, 3DConstructor/ABF, import sozlamalari), 110 (palitra), 122–124 (PTX UDI, OSI+ orientatsiya, Format4 qoldiqlar), 128–130 (KDT, CadMatic, KDT XML), 132–133 (yetkazish ko'rsatmalari, format tavsiflari).
- 🟡: XNC-017 (yordam matni), 044 (ellips), 058 (Msg), 082 (F4), 087 (redaktor Undo), 115 (qo'shimcha stanok nomlari), 119 (papka), 131 (Elmo3).
- ❓: XNC-031 (`ver`), 045 (Bezier), 061 (FOR), 077 (parametriklikni qayta hisoblash), 083 (F9), 089 (sozlash rejimi), 111 (Ограничения), 113 («Новый интерфейс»), 120 (oldindan torsovka).
- PRJ-003..016 (importda qolgan atributlar) va `.project` eksporti (4.2) — korxona so'rasa.

## 6. Aniqlashtirish savollari (foydalanuvchiga)

1. **Qaysi ishlov markazi(lar) ishlatiladi** (WoodWop/Homag, Biesse, SCM Xilog, KDT, boshqa)? Postprotsessorni dasturchilar yozishi uchun ularga XNC operatsiya ma'lumotini qaysi ko'rinishda bersak qulay: JSON (hisoblangan amallar), XML (GibLab dastur formati) yoki Jinja shablon konteksti?
2. Hozirgi XNC dasturlarda **teshik massivi (`ac` > 1)** ishlatiladimi? (205 faylda hammasi `ac=1`; GibLab kutubxona shablonlarida odatda bo'ladi — xatolik #1 ni tuzatamizmi va qaysi shablonlarni ishlatasiz?)
3. GibLab XNC redaktorida **`sin(90)` nechaga teng** — 1 (gradus) yoki 0.894 (radian)? Yordam sahifasi radian ko'rsatadi; bizda gradus. Qayeringizda tekshirish mumkin bo'lsa (men GUI ga tegmayman).
4. Bazis eksportidagi XNC operatsiyalarda `side="1"` / `"2"` (1 338 ta) — **1 = lits, 2 = orqa** to'g'rimi? (Hozir shunday qabul qilingan.)
5. Qirra teshiklaridagi `m` (Середина по Z) va noma'lum `ver="2"` atributi — Bazis nimani yozadi? Z aniq koordinata (`m=false`) bo'lgan 108 ta teshikka e'tibor kerakmi?
6. «Предварительная торцовка» (stanok sozlamasida) va «Новый интерфейс» (Общие) nimani anglatadi? Ularning ekran nusxasi kerak.
7. **DXF import**: manba qaysi dastur (AutoCAD, ArtCAM, Bazis)? Qaysi qatlam/rang teshik, freza, paz deb o'qiladi? Namuna DXF va kutilgan XNC dastur kerak.
8. **Kutubxona:** qaysi fasad/eshik frezalari kerak (MDF fasad profillari, ruchka kesmasi)? Namuna GibLab `.project` (yangi frezalar: 3 nuqtali yoy, to'rtburchak, ellips, fillet, Bezier, Par/If/While) berilsa teg nomlarini aniqlaymiz.
9. **`.project` eksport** kerakmi (GibLab'ga qaytarish, ikki tomonlama ishlash) yoki faqat bir tomonlama migratsiya?
10. **Etiketkada XNC shtrixkodi** (`XNC1..XNC5`) stanokda dasturni ishga tushirish uchun ishlatiladimi? Qaysi stanok va shtrixkod o'qiydimi?
11. Redaktor sozlamalaridagi «Ограничения» nima (ekran nusxasi kerak); «Палитра» sozlamasi kerakmi?
12. XNC uchun **narx** (teshik/freza/paz) korxonada ishlatiladimi (CS kabi narx L deb olingan)? Ishlatilmasa narx bandlari (XNC-003, 011..013) past qoladi.
13. Qo'shimcha stanoklar (Bavelloni, Excitech, HolzHer, AES Alpha, Panhans, KDT GCode, BIMA) ro'yxatga kerakmi yoki faqat korxonaning haqiqiy stanoklari?
14. GibLab XNC ifodasida **`7/2` nechaga teng** (3 yoki 3.5) va `round(-1.5)` (−1 yoki −2)? Yordam butun/butun bo'linishni butun deb yozadi; bizda haqiqiy.
15. Biesse OSI+ va Format4 yordami kroy kartalari/etiketkalar haqida (pil markazi) — ular korxonada qaysi stanokka to'g'ri keladi? (Bizda ular «ishlov markazi» guruhida.)
