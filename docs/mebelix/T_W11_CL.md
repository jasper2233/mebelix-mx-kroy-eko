# T. W11 — (CL) Погонажный раскрой va CLE (bir o'lchovli kroy)

Sana: 2026-10-02 · Holat: 1–5 bosqichlar + QA (import/eksport/MES qo'shilgan) · Asos: `giblab_inventory/02_CL_CLE.md` (125 funksiya).
Yordam sahifalari faqat funksional ma'noni tushunish uchun o'qilgan; matn, rasm, kod ko'chirilmagan; barcha formulalar §3 da o'z so'zlarimiz bilan.

## 1. Nima qilindi
| Qatlam | Fayl |
|---|---|
| Model | `models.py`: `CLCostBase`, `CLParams` (yassi, `Operation.cl`), `CL_DEFAULTS`, `Part.src_length`, `CuttingResult.kind / material_len_m / business_len_m`, `PrintSettings.cl_*` (8 ta) |
| Optimizator | `services/cl_optimizer.py` — 1D (DP bitset + FFD + bin-completion + bo'sh joyni jamlash), `validate_cl`, `lower_bound` |
| Hisob | `services/cl_calc.py` (`run_linear`, `cl_cost`, `cl_warehouse_rows`, `mes_payload`, `cl_params_stale`), `calc.op_part` (detal eni = polosa eni) |
| CLE | `services/cl_editor.py` (11 ta amal, `rebuild`, `result_rev`) |
| Chop | `services/cl_render.py` (1D karta SVG + hisobot bo'limi), `services/cl_labels.py` (ru/uz matnlar) |
| Import / eksport | `services/cl_import.py` (`legacy_project.py` da chaqiriladi), `services/cl_export.py` (`project_export.py` da chaqiriladi) |
| API | `api_cl.py` (`cl-quantities`, `cl-edit/rev`); umumiy yo'llar (`optimize`, `edit`, `result`, `remnants/*`, `sheets/from-remnants`, `maps/{i}.svg`, `postprocess`, `report`, `warehouse`) operatsiya turiga qarab CL ga yo'naltiriladi |
| Ombor | `RemnantRow.linear` (+ migratsiya), `warehouse.commit/rollback/business_remnants` CL ni biladi, `GET /remnants?linear=` |
| Sozlamalar | `cl_defaults` scope (`settings.py`) |
| UI | `features/cl/*` (`ClPanel`, `ClParams`, `ClParts`, `ClSheets`, `ClCut`, `StripMap`, `ClEditor`, `clHooks`, `cl.css`), `opmeta.tsx` (IMPLEMENTED), `OperationsTable.tsx`, `CatalogPicker.tsx`, `ProjectView.tsx`, `Print.tsx` (kichik Edit), `CsSheets.tsx::RemnantPicker` (`linear` bayrog'i), `i18n_cl.py` |
| Testlar | `tests/test_cl_w11_{optimizer,calc,api,import}.py` (+ `test_o_operation.py` da CL→CN ga o'zgartirildi: CL endi import qilinadi) |
| Benchmark | `tools/bench/cl_bench.py` |

## 2. Qarorlar jadvali (hammasi bitta konstanta / maydon orqasida)
| № | Qaror | Qayerda | Asos / holat |
|---|---|---|---|
| 1 | Maqsad funksiyasi leksikografik: **1)** hamma detal joylansin, **2)** kam material (Σ polosa uzunligi), **3)** ko'proq деловой otxod, **4)** kam xil karta, **5)** kam kesim | `cl_optimizer.OBJECTIVE = "material"` | foydalanuvchi talabi; `"consumption"` — hujjat §3.4 (sarf = material − деловой, so'ng polosalar soni). Q1 |
| 2 | `F = Σ detal uzunligi / polosa uzunligi` (деловой otxod maxrajdan ayirilmaydi) | `cl_optimizer.F_NET_OF_BUSINESS = False` | R4 hisobi (3100/3200 = 96.88 %); real CL fayllarida `cFilling = cPartAmount / cMaterialAmount` — shuni tasdiqlaydi. CS da esa деловой ayiriladi |
| 3 | `LT = kesimlar × polosa eni` | `make_map` | R4: 6 × 0.6 = 3.6 m |
| 4 | Detal eni polosa eniga teng: `Part.width = 0` saqlanadi, hisobda `cl.width` (`calc.op_part`); `StockSheet.width` har saqlashda `cl.width` ga tenglashtiriladi | `calc.op_part`, `cl_calc.normalize_sheets` | hujjat §6 Q8/Q15 (taklif). CL-038 (ОЛ/ОП metri 0) shu bilan tuzatildi |
| 5 | «Торцовка отходов» ✓ = otxod toza uzunligi (80), oxirgi torsovka kesimi qilinadi; ☐ = otxod torsovkani ham oladi (110), kesim yo'q. Maydon nomi `waste_incl_trim` (CS dagi `remnant_size_incl_trim` bilan bir xil ma'no) | `CLParams.waste_incl_trim` | R2 |
| 6 | Oddiy chiqindi (`W < waste_min`) uchun ajratuvchi kesim qilinmaydi va u qoldiq jadvaliga kirmaydi | `cl_optimizer.layout` | hujjat §3.3 (taklif). Q6 |
| 7 | Standart qiymatlar: torsovka **10** (format «по умолчанию»), propil **3** (korxona loyihalari), `waste_min` 100, `business_min` **1000** (format: 1 m), `fill_packet` 90, `est_fill_percent` 90, polosa eni 100, qalinlik 16, polosa uzunligi 6000 | `models.CL_DEFAULTS` | hujjat taklifi (torsovka 0, `business_min` 500) o'rniga fayl formatining standartlari olindi |
| 8 | `cBusinessWaste` importda metr: `qiymat < 50` → ×1000 mm; `≥ 50` → mm deb olinadi. Eksportda `business_min/1000` | `cl_import.BUSINESS_M_THRESHOLD` | format: «По умолчанию: 1м» (real faylda `10`). Q3 |
| 9 | `cCPF` (Расчетный процент) importda `0.9` ham, `0.1` ham 90 % ga keladi (`_fill_pct`); real fayllarda `0.9` va `cPartsAmountP × 1.1 = cMaterialAmountP` | `legacy_project._fill_pct` | format tavsifidagi `(1.0 − cCPF)` bilan real ma'lumot ziddiyatda — real ma'lumot asos |
| 10 | Polosalar ro'yxat tartibi = ustuvorlik; ketma-ket cheksiz turlar orasidan eng zich sxema tanlanadi; kartalar tartibi — polosa ro'yxati tartibi (qoldiqlar birinchi). Material kam bo'lsa, ro'yxatdagi qoldiq ishlatilmasligi mumkin | `cl_optimizer._shp`, `optimize_linear` | CS dagi tekshirilgan qoida + 1-qaror. Q2 |
| 11 | Detal ichida polosadagi tartib: uzundan qisqaga | `_norm` | hujjat Q10 taklifi |
| 12 | «Торцовка листа» (CLE) — shu kartaga alohida **boshi va oxiri** torsovkasi: `CutMap.trim_length` = T_boshi, `CutMap.end_offset_right` = T_oxiri (W13 maydonlari qayta ishlatildi; CL da har doim aniq qiymat, `None` bo'lsa parametrdan) | `cl_editor` `trims`, `cl_optimizer.make_map` | Q7 (yordam javob bermaydi) |
| 13 | CLE: «Количество листов» = `CutMap.copies`; `Ткт` / aylantirish CL da yo'q (yashirilgan) | `cl_editor` | Q12, Q13 |
| 14 | «До кроить», «Варианты» CL da yo'q; sifat rejimi (fast/normal/max) bor | `main.optimize_op/cutting_variants` | Q11. Q1 |
| 15 | Narx: material = `price × (material uzunligi − деловой)` (m); `price_by_strip` — polosalar soni (11 / 32 / 33 / 34 yaxlitlash); operatsiya — 4 asos (§3). Kroygacha: `Σ × (2 − p/100)`; kesim — har detalga 2 kesim × polosa eni | `cl_calc.cl_cost` | hujjat §3.3; formatdagi `cTrimLengthP/CountP` ta'rifi. Q4, Q5 |
| 16 | Talabnoma: m (yoki `price_by_strip` bo'lsa — polosa); ombor qoldiq-polosalari alohida qatorlarda | `cl_warehouse_rows` | Q18 |
| 17 | Omborga faqat деловой qoldiq yoziladi, o'lchami — xom (`raw_length`), `length × eni` tartibi **almashtirilmaydi**; `RemnantRow.linear = True`; CS faqat listli, CL faqat погонажный qoldiqni tanlaydi (400) | `warehouse.py`, `main.sheets_from_remnants` | Q14 |
| 18 | `fill_packet` («Процент заполнения для кратности») saqlanadi va eksport qilinadi, lekin kartalarni tanlashga **ta'sir qilmaydi** (UI da halol yozilgan); paketlar soni `⌈C / kratnost⌉` | `CLParams.fill_packet`, i18n `cl.p.fill_packet_hint` | Q16 |
| 19 | Burchakli (45°) kesim, tekstura, aylantirish — yo'q | — | hujjat §2.13, Q23 |

## 3. Formulalar (hammasi testda)
- Foydali uzunlik `U = L − (T_b + k) − (T_o + k)`; torsovka 0 bo'lgan tomonda `T + k` qo'shilmaydi. **1600, T 20, k 10 → 1540.**
- Sig'ish: `Σ(p + k) ≤ U + k` (og'irlik `p + k`, sig'im `U + k`); `R = U − Σp − (n−1)·k ≥ 0`.
- Oxirgi detaldan keyin: `R = 0` — oxirgi kesim = torsovka kesimi; `0 < R ≤ k` — otxod yo'q; `R > k` — `W = R − k`, xom `R + T_o`.
- **Misol (R1/R2): 780 + 500 + 150, L 1600, T 20, k 10:** x = 30, 820, 1330; otxod x = 1490, **80** (xom **110**); kesimlar **5**; F = 89.38 %; LT = 1.8 m. ☐ Торцовка отходов: otxod **110**, kesimlar 4.
- **Misol (R4): 800×2 + 500×3, L 3200, T 20, k 10:** `R = 0`, kesimlar **6**, **F = 96.88 %**, **LT = 6 × 0.6 = 3.6 m**.
- Kesimlar: `[T_b>0] + (n−1) + (T_o>0 ? 1 + [otxod ∧ ☑] : [R>0])`. «Torsovkasiz» asos: kesimlar − `[T_b>0]` − `[T_o>0]`.
- Operatsiya narxi asoslari (`cCostType`): 0 kesim uzunligi (torsovka bilan) · 1 torsovkasiz · 2 material uzunligi (деловой otxodsiz) · 3 detallar uzunligi.
- Kroygacha: `10 m × (2 − 0.9) = 11 m` (T-CL-5: narx 1000/m → 11 000).

## 4. `.project` importi / eksporti
**Xarita (CL operatsiya + `band` tovari + `tool.cutting`):**
| Fayl | Maydon |
|---|---|
| `band`: `w`, `t`, `cost`, `name`, `code`, `<part count l w>` | `cl.width`, `cl.thickness`, `cl.price`, `op.name/code`, `op.sheets` (soni bo'yicha o'sish; `10000` — cheksiz; eni = `cl.width`) |
| `tool.cutting`: `swSawthick`, `swPackageHeight` | `cl.kerf`, `cl.pack_height` |
| `cTrimW` (yoki `cTrimL`), `cTrimEW` (< 0 → torsovka) | `cl.trim`, `cl.end_offset` |
| `cFillRep`, `cCPF` | `cl.fill_packet`, `cl.est_fill_percent` |
| `cCostType`, `cCostCut`, `cCostByItem`, `cCostByItemRound` | `cl.op_cost_base`, `cl.op_price`, `cl.price_by_strip`, `cl.strip_rounding` |
| `cMinDimRegWaste1`, `cBusinessWaste` (m), `cTrimWaste`/`cTrimWaster` | `cl.waste_min`, `cl.business_min`, `cl.waste_incl_trim` |
| `cMinDimDetail`, `cSizeMode` | `cl.min_part_len`, `project.size_mode` (faqat CL bo'lsa — CL ning rejimi) |
| `<part id>` (detal) | `Part` (`width = 0`; `elt/elb/ell/elr` kromka havolalari ishlaydi) |

**Manfiy uzunlik qoidasi (qat'iy).** CL detalida `l < 0` (masalan `l="-350" w="7"`; `dl/jl/cl` ham shunday) — Bazis hisoblab bo'lmagan detal belgisi: real fayllarda `cPartsAmountP` shu manfiy yig'indi (−1.4 m = 4 × −350 mm), ya'ni GibLab uni ham hisoblamagan.
1. Detal **import qilinadi**: `length = 0`, `width = 0`, `qty` saqlanadi, xom qiymat `Part.src_length = −350` (eksportda qaytariladi).
2. `length = 0` qator kroyga kirmaydi; `Ост = ОК`; UI da ogohlantirish rangida «⚠ −350», jadval ostida «Не рассчитано: N»; kroydan keyin `res.warnings` va `unplaced` da ko'rinadi (jim yo'qolmaydi).
3. Xodim uzunlikni kiritsa (`length > 0`) — detal oddiy: `src_length` e'tiborga olinmaydi.
4. `|l|` uzunlik sifatida ISHLATILMAYDI (taxmin qilinmaydi). Almashtirish: `cl_import.CL_NEGATIVE_LENGTH_MODE = "abs"`.
5. CS operatsiyasiga tegishli manfiy detal — avvalgidek import qilinmaydi (ogohlantirish `imp_neg_parts`); CL ga ulangan bo'lsa — yuqoridagi qoida.
6. Importda ogohlantirish: `imp_cl_uncomputed` («CL: N det. … 0 uzunlik bilan import qilindi»).

Real 3 ta CL operatsiya (2 fayl) bilan sinov (mijoz nomlarisiz, umumiy): hammasi o'qildi; 1 tasida 4 detal hisoblangan (`l > 0`), 2 tasida jami 8 detal manfiy (hisoblanmagan) — qoidaga ko'ra `length = 0` + ogohlantirish. Sintetik real-uslubdagi fikstura testda (`test_cl_w11_import.py`); real fayllar bilan test `MEBELIX_REAL_PROJECTS=<papka>` muhit o'zgaruvchisi bilan ishga tushadi (standart — o'tkazib yuboriladi).

**Eksport (W10 `project_export.py` ga qo'shildi):** `SUPPORTED` ga CL; detallar `part_size_attrs` (eni = polosa eni; hisoblanmagan — xom manfiy), operatsiya `cl_operation` (tool + band + stock `part` + `operation CL`). Sxema (`project_schema.OP_ATTRS["CL"]`) tekshiruvidan o'tadi, qayta import parametrlarni tiklaydi (test).

## 5. API
| Yo'l | CL uchun |
|---|---|
| `POST /projects/{pid}/operations` `{type:"CL", material_id?}` | `cl_defaults` + katalog (`kind=linear`) → `cl`, bitta polosa (6000, ∞) |
| `PATCH …/operations/{oid}` `{cl:{…}}` | kroyni eskirtiradigan o'zgarish (propil, torsovka, otxod, eni, min. detal) natijani o'chiradi; narx / sifat — yo'q |
| `POST …/optimize?quality=` | 1D optimizator; javob — `CuttingResult(kind="linear")` |
| `POST …/edit` `{result, action}` | CLE amallari: `add_map delete_map copies place place_auto remove move transfer trims move_map comment` |
| `PUT …/result?base=` | CLE saqlash: `rebuild` + `validate_cl`; `base` — `GET …/cl-edit/rev` izi (409 — boshqa oynada o'zgargan) |
| `GET …/cl-quantities` | kroygacha / keyin material (m), polosalar, kesim uzunligi, narx |
| `GET …/maps/{i}.svg` | 1D karta SVG |
| `GET …/remnants`, `POST …/remnants/commit|rollback`, `PUT …/result/taken`, `GET …/remnant-groups` | CL da ham (deloviy qoldiq, «Исп. кол-во») |
| `POST …/sheets/from-remnants` | faqat `linear` qoldiq (aks holda 400); polosa eni = `cl.width` |
| `GET /remnants?linear=true|false` | погонажный / listli qoldiqlar; berilmasa — hammasi |
| `GET /projects/{pid}/report`, `/warehouse` | CL bo'limi va talabnoma qatori |

## 6. Optimizator
Algoritm: deterministik (tugun / iteratsiya byudjeti, vaqtga bog'liq tasodif yo'q) — **1)** `LB = ⌈Σ(p+k)/(U+k)⌉`; **2)** nomzodlar: ketma-ket «eng zich sxema» (chegaralangan to'plam-sumka, Python `int` bitset: `reach |= reach << w`), «eng katta detal majburiy» varianti, FFD (pastki kafolat); har sxema `c` marta takrorlanadi (karta nusxalari); **3)** yaxshilash: eng bo'sh polosalar detallarini bin-completion/DFS bilan bitta kam polosaga, Fleszar–Hindi usulida bo'sh joyni jamlash (1–0 ko'chirish va 1–1 almashtirish), tasodifiy (urug'li) kombinatsiyalar uchun aniq qayta joylash; cheksiz turlar orasida qisqaroq polosaga «tushirish»; **4)** `_score` bo'yicha eng yaxshisi.

`tools/bench/cl_bench.py` (sintetik; ~ shu mashinada):
| Sinf (N = 200, 20–400 detal) | `=LB` | `LB+1` | `≥ LB+2` | ≤ LB+1 | FFD dan yomon | vaqt (normal) |
|---|---|---|---|---|---|---|
| realistik: detal polosaning 3–30 % i | 186 | 14 | 0 | **100 %** | 0 | o'rtacha 30 ms, max 250 ms |
| qiyin: 3–45 % | 114 | 72 | 14 | 93 % | 0 | o'rtacha 90 ms, max 340 ms |
| juda qiyin: 3–80 % (LB zaif) | 8 | 31 | 161 | 20 % | 0 | o'rtacha 70 ms |
| 1000 detal (300 xil uzunlik) | LB = 243, natija 243 | | | | | **0.17 s** (fast 0.13, max 0.16) |
| 20000 detal (`MEBELIX_MAX_CUT_ITEMS` chegarasi; 50–1000 xil uzunlik) | LB ga nisbatan +0.1…0.4 % | | | | | fast 0.3–1.8 s, normal 2.2–5.6 s (FFD segment daraxti bilan; avval 12–22 s) |

Izoh: detal polosa yarmiga yaqinlashganda `LB` (uzluksiz quyi chegara) zaiflashadi (butun sonli cheklov), shuning uchun «≤ LB+1» u yerda optimizator kamchiligi emas: `LB+2` chiqqan kichik instanslarda (38–49 detal) aniq DFS 30 mln tugunda ham bitta kam polosani topa olmadi (isbotlanmadi ham). Kichik instanslar (≤ 9 detal, 200 ta, bitta va ikki cheksiz tur) — **aniq optimum bilan 200/200 mos** (brute-force DP, testda).

## 7. UI va yorliqlar
Panel: `Параметры | Детали | Полосы и отходы | Раскрой` (CS paneli namunasida; tab holati `csTab` umumiy). «Параметры» — chap: material (eni, qalinligi), narx (narx, hisobiy foiz, material miqdori, polosalar soni, polosa bo'yicha, yaxlitlash, qiymat, asos, operatsiya narxi/qiymati), otxod (min. otxod, деловой uzunlik, ☑ Торцовка отходов), cheklov (min. detal); o'ng — kroy (propil, torsovka, «Минимальный отступ в конце» oynasi, paket balandligi, kratnost, to'ldirish foizi, sifat). Har parametr yonida «?» (F1). «Детали» — `Д-на · Кол · ОВ · ОН · ОЛ · ОП · Наименование · ОК · ИК · Ост`, pinned yangi qator, Excel Ctrl+V (`Д-на, Кол, ОВ, ОН, ОЛ, ОП, Наименование`), Space / Shift+Space kromka, Ctrl+M, filtr. «Раскрой» — 1D karta (SVG, g'ildirak masshtabi), holat qatori `№ S C Cp LT F CT T M`, miniatyuralar ↔ buyruqlar jadvali, qoldiqlarni omborga yozish, postprotsessor (csv/commands/json/dxf).

Yorliqlar: **Раскрой** `Home ↑ ↓ End / ← →` — karta; `F2` izoh; `Ctrl+P` ko'rinish; g'ildirak — masshtab. **CLE:** `F9` to'liq ekran; `Ctrl+Z/Y`; `Ctrl+←/→` detalni polosa boshiga/oxiriga; `Alt+←/→` bir pozitsiyaga; `Shift+↑/↓` qo'shni kartaga; `Del` / o'ng tugma — olib tashlash; `Ctrl+↑/↓` — kartani ko'chirish; `Ctrl+F` — nol qoldiqlilarni yashirish; `PgUp/PgDn/Home/End` — karta; chap tugma — detalni tanlash / tanlangan detalni bo'sh joyga qo'yish; jadvalda detalni ikki marta bosish — birinchi mos polosaga. `Ctrl+Enter` — saqlash.

## 8. Testlar
`tests/test_cl_w11_optimizer.py` (T-CL-1…8, brute-force 200 ta, tasodifiy 200 ta ×2, determinizm, 1000 detal ≤ 2 s), `test_cl_w11_calc.py` (T-CL-5, narx asoslari, kromka/paz eni, talabnoma, mahsulot ulushi), `test_cl_w11_api.py` (operatsiya, kroy, CLE, qoldiq, hisobot, MES, defaults/katalog), `test_cl_w11_import.py` (import / eksport / real fayllar — ixtiyoriy).

## 9. Ochiq savollar (foydalanuvchiga)
1. **Maqsad:** «kam material → ko'proq деловой → kam kesim» (hozir) yoki «kam sarf = material − деловой»? (`OBJECTIVE`). Real CL namunasi (3–5 topshiriq + GibLab natijasi) berilsa solishtiramiz (Q1).
2. **F** da деловой otxod ayirilsinmi (`F_NET_OF_BUSINESS`; CS da ayiriladi)?
3. **Qoldiq-polosalar tartibi:** ro'yxatdagi qoldiq-polosa material kam sarflanishi uchun ishlatilmay qolishi mumkin (1-qaror) — GibLab doim ro'yxat tartibida ishlatadimi (Q2)?
4. `cBusinessWaste` birligi (m / mm) va `Мин. размер отхода` standartlari (Q3); `cCostByItem` + yaxlitlash CL da bormi (Q4); «Цена операции (метр/рез)» — metrmi (Q5).
5. Buyruqlar jadvali (T/P/W, `C` ishlatilmaydi) va otxoddan keyingi kesim kesimlar soniga kiradimi (Q6) — namuna chop kerak.
6. «Торцовка листа» — boshi/oxiri qiymatlarini kartaga yozish to'g'rimi (Q7)? Polosa qatorlarida ТД/ТШ yo'q.
7. Detal eni kromka bilan polosa enidan katta bo'lsa nima bo'ladi (Q8) — hozir eni = polosa eni, tekshiruv yo'q.
8. Manfiy uzunlik (hisoblanmagan): `length = 0` (hozir) yoki `|l|` ishlatilsinmi? Bazis'da manfiy belgi aniq nimani bildiradi?
9. «Процент заполнения для кratnosti» mantiqi (Q16); «До кроить» (Q11); 45° kesim kerakmi (Q23); etiketka (Q21); postprotsessor formati — namuna fayl (Q19).
10. Korxonaga CL kerakmi (205 loyihada 0 ta, Q20) — hozir to'liqlik uchun.

## 10. Boshqa paketlarga ta'sir
- **W10:** `project_export.py` ga 4 ta kichik Edit (CL; `cl_export.py` da yozilgan) — eksport testlari o'tadi.
- **W2:** `api_cs_w2.py::_cut` (qoldiq-guruhlar va «Исп. кол-во» CL da ham), `CsSheets.tsx::RemnantPicker` (`linear` bayrog'i), `hooks.ts::useRemnants(…, linear)`.
- **W13:** CL natijasida `CutMap.trim_length / end_offset_right` aniq qiymatlar (CL ma'nosi §2-12); `editor_w13` tegilmadi.
- **Umumiy:** `calc.py` (`op_part`, `sheets_per_pack`, `recalc_project`, `product_costs`, `warehouse_request`), `main.py` (`_need_cut`, CL tarmoqlari), `render.py` (2 ta kichik Edit), `postprocessors.py` (CL konteksti), `mes.py`, `db.py` (`remnants.linear`), `i18n.py`, `settings.py`, `legacy_project.py`, `types.ts`, `hooks.ts`, `Print.tsx`.
- `test_o_operation.py`: «CL o'tkazib yuboriladi» tekshiruvi CN ga almashtirildi (CL endi import qilinadi).
