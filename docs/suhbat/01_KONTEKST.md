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
