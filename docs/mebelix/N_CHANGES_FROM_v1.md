# N. v1 → v2 o'zgarishlar ro'yxati (Claude Code uchun aniq vazifalar)

Har band: **nima**, **nega** (qaysi manba), **qayerda** (fayl), **qanday tekshiriladi** (test).
Reference kod: `backend/` (v2 to'liq nusxa). Loyihangizdagi backend v1 dan o'zgargan bo'lsa —
fayllarni ko'r-ko'rona almashtirmang, har bandni birlashtiring.

## N1. Tuzatishlar (v1 dagi xatolar)

| # | Nima | v1 | v2 (to'g'ri) | Fayl | Test |
|---|---|---|---|---|---|
| 1 | Torsovka o'qlari | trim_length uzunlikni kamaytirardi | trim_length = **yuqori** chet → **en**; trim_width = **chap** chet → **uzunlik**; past/o'ngda minimal otstup | optimizer.`_make_layout` | test_trim_example_manual |
| 2 | Minimal otstup | `trim_both_sides`, `min_end_offset` | `end_offset_bottom`, `end_offset_right` (None = torsovka), list qatorida ham | models, optimizer | test_end_offsets_override |
| 3 | Kromka formulasi | ish = Σmax(tomon,min), material = Σ(tomon+2·ortiqcha) | **ish = Σ tomon**; **material = Σ(max(tomon,min)+2·ortiqcha)×(1+chiqindi%)** | calc.edge_usage | test_edge_usage_matches_giblab, test_edge_min_length_rule |
| 4 | Kromka yaxlitlash | float qadam | GibLab kodi (o'nlik×10+rejim) | calc.round_code | test_rounding_codes |
| 5 | Taxminiy sarf | area / (list × to'ldirish%) | **detallar maydoni × (2 − %/100)** | calc.estimate_consumption_m2 | test_estimate_formula |
| 6 | Material narxi | price_per_m2 alohida bayroq | «по листам» ✓ → list narxi; ☐ → m² narxi | calc.cs_cost | test_cost_by_sheets_and_m2 |
| 7 | Material miqdori | material maydoni | **material − delovoy qoldiqlar** | optimizer, calc | test_cost_by_sheets_and_m2 |
| 8 | Qoldiq turlari | remnant/waste | waste / remnant / **business** (maydon chegarasi) | optimizer.classify | test_classify_remnants |
| 9 | min_trim_cut | e'tiborsiz | yupqa tilim qoidasi (ichki va list chetida) | optimizer.`_Ctx.gap_ok` | test_min_trim_cut_rule |
| 10 | max_rotations | e'tiborsiz | gilyotina darajalari chegarasi | optimizer | test_max_rotations_two_levels |
| 11 | max_strip_length | polosani qisqartirardi | yo'nalishni almashtiradi | optimizer.`_allowed_dirs` | test_max_strip_length_forces_direction |
| 12 | Karralik | kiritiladi (2) | **avtomatik** floor(paket/qalinlik), paketlar soni | calc.multiplicity | test_pattern_repetition_copies |
| 13 | T2 torsovka | bir marta | **har polosada** (GibLab buyruqlar jadvalidagi kabi) | optimizer.`_Emitter` | API test (buyruqlar) |
| 14 | Yangi detal Ткт | ☐ | material teksturali bo'lsa ✓ | main.add_parts | — |

## N2. Optimizator qayta yozildi (rekursiv gilyotina)

* 3 daraja o'rniga **2..6 daraja** (qatorda bir nechta detal, ichma-ich bo'laklar).
* Polosa tanlashda **oldindan ko'rish** (lookahead) — sifat: «Detskiy kravat» 1-list 91.53 % → **92.83 %** (GibLab 93.87 %).
* Saralash (polosalar, polosa ichida; «torlar o'rtaga»), blok (guruh) detallar, kartani takrorlash + paketlar,
  afzal yo'nalish (oxirgi list), minimal detal o'lchami ogohlantirishi, vaqt byudjeti (20 s).
* Buyruqlar jadvali GibLab tartibida (R, T1, C1, T2, P2/C2, P3…, W). Test: test_strip_sort_desc, test_first_cut_width_only.

## N3. Yangi funksiyalar (backend)

| Funksiya | Endpoint / fayl |
|---|---|
| «До кроить» | `POST .../optimize?mode=remaining` (calc.run_cutting) |
| Kroy natijasidagi qoldiqlar «Листы и остатки» da | `GET .../stock-table` |
| Karta izohi (F2) | `PUT .../maps/{n}/comment` |
| Karta sarlavhasi (12 ko'rsatkich, profil) | `GET .../maps/{n}/header`, render.INDICATORS |
| SVG: kromka chiziqlari/harflari, qoldiq raqamlari, tanlangan detal | render.map_svg |
| Buferdan qo'yish (Ctrl+V), yo'q kromkani yaratish | `POST .../parts/paste` (importers.parse_clipboard) |
| Shift+Space perimetr kromka | `POST .../parts/bulk/edges-cycle` |
| Ctrl+W endi paz va pripusklarni ham buradi | `.../parts/bulk/swap` |
| GibLab/Bazis XML import | `POST /api/projects/import-giblab` (giblab_project.py) |
| Operatsiyalarni saralash | `POST .../operations/sort` |
| Kromkani materiallar bo'yicha ajratish (Общие действия) | `POST .../actions/split-edges-by-material` |
| «Заказать» | `POST /api/projects/{id}/order` |
| Mahsulot narxlari (1 dona) | `GET .../product-costs` (calc.product_costs) |
| Undo/Redo holati | `GET .../history-state` |
| Sozlama profillari (standart saqlash) | `GET/PUT/DELETE /api/settings/{scope}/{name}` |
| Katalogdan material tanlash | `POST .../material/{item_id}` |
| Qoldiqlar ombori (MES) | `/api/stock/remnants`, `.../remnants/load`, `.../remnants/save` |
| Etiketka ma'lumotlari | `GET .../labels?source=parts|remnants|products` (labels.py) |
| Paz, sirt, komplektatsiya, pogonaj hisoblari | calc.groove_usage, surface_usage, o_cost, run_linear/cl_cost; cl_optimizer.py |
| Kroygacha taxmin | `GET .../estimate` |
| XNC: davom etuvchi parametrlar, yangi o'zgaruvchilar, taqqoslash, RQG kodi | xnc.py |
| FastAPI lifespan (on_event o'rniga) | main.py |

## N4. Hujjatlar

v1 `UI_SPEC.md` → `docs/D_UI_SPEC_v2.md` (to'ldirilgan). Yangi: A..O hujjatlari, `02_YAKUNIY_XULOSA.md`.
v1 `PROMPT_CLAUDE_CODE.md` kuchda; ustiga `01_UPDATE_PROMPT_CLAUDE_CODE.md`.

## N5. Testlar

v1 `tests/test_kroy.py` **o'rniga** `tests/test_v2.py` (31 test) + `tests/conftest.py` (vaqtinchalik baza).
v1 testidagi kromka qiymati (4.896) v2 da yaxlitlash kodi tufayli 4.9 bo'ladi — v1 testini o'chiring.
