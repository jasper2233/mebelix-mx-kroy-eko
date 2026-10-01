# F. Ma'lumotlar modeli v2

Manba haqiqat: `backend/app/models.py` (Pydantic) va `backend/app/db.py` (SQLAlchemy).
Loyiha — bitta JSON hujjat (`projects.data`), ro'yxat/qidiruv uchun ustunlar alohida.

## F1. Daraxt

```
Project
 ├─ products[]: Product (name, code, qty, description, order_data, ready_date, phone1/2, extra{}, program[])
 └─ operations[]: Operation (type, code, name, material_id, owner_product_id, print, new_page, description,
                             cost_material, cost_operation)
      ├─ CS: cs_material, cs_cut, parts[], sheets[], result
      ├─ CL: cl, parts[] (width=0), sheets[] (polosalar), cl_result
      ├─ EL: el            ├─ GR: gr          ├─ SP: sp
      ├─ O : o (materials[], owner)           ├─ LB: lb (template)
      └─ XNC: xnc (program[]), xnc_part_id
Part: uid, product_id, name, description, code, length, width, qty, minus_qty, grain,
      edge_top/bottom/left/right {op_id}, groove_* {op_id, front}, allow_*, group_by/min/max,
      xnc_op_ids[], surface_face_op, surface_back_op, used_qty, left_qty, extra{}
StockSheet: kind(sheet|remnant|business), origin(input|stock|result), length, width, qty, used_qty,
            trim_length, trim_width, end_offset_bottom, end_offset_right, db_id, source_map, description
CuttingResult: maps[CutMap], total_*, material_qty_m2, business_area_m2, waste_area_m2, remnants[], warnings[]
CutMap: index, sheet_id, sheet_length/width, copies, packs, placements[], offcuts[], commands[],
        parts_count, cut_length_m, cuts_count, fill_percent, waste_percent, *_area_m2, trim_*, first_cut, comment
```

## F2. v1 → v2 maydon o'zgarishlari (migratsiya)

| Model | v1 | v2 | Harakat |
|---|---|---|---|
| CSCutParams | `trim_length` X ni kamaytirardi | endi **Y (en)** ni kamaytiradi (yuqori chet) | semantika o'zgardi |
| CSCutParams | `trim_width` Y ni kamaytirardi | endi **X (uzunlik)** ni (chap chet) | semantika o'zgardi |
| CSCutParams | `trim_both_sides`, `min_end_offset` | olib tashlandi → `end_offset_bottom`, `end_offset_right` (None = torsovka) | JSON dan o'chirish |
| CSCutParams | `multiplicity: int = 2` | `Optional[int] = None` (avto = floor(pack/qalinlik)) | |
| CSCutParams | `min_trim_cut` | endi optimizatorda **qo'llanadi** | |
| CSCutParams | — | `group_props: list[str]` | yangi |
| CSMaterialParams | `price_per_m2` | olib tashlandi: `cost_by_sheets` ✓ → list narxi, ☐ → m² narxi | |
| CSMaterialParams | `remnant_min_area` | `business_area` | nomi o'zgardi |
| CSMaterialParams | — | `has_grain` | yangi (yangi detal Ткт standarti) |
| CSMaterialParams | `op_cost_base: int` | `OpCostBase` **str** enum (`cut_length`, `part_perimeter`, `part_area`, `material_area`) | |
| ELParams | `material_rounding`, `work_rounding`: float qadam | **int kod** (o'nlik×10 + rejim) | |
| GRParams | width 4, depth 10, offset 16, price | + `offset_inclusive`, `saw_thickness`; standart depth 8, offset 10 | |
| Part | `grain=False` | `grain=True` (lekin API da material `has_grain` dan olinadi) | |
| Part | — | `minus_qty`, `extra` | yangi |
| GrooveSide | `back_side` | `front: bool = True` | invert |
| StockSheet | `is_remnant: bool` | `kind` + `origin` (+ `is_remnant` property) | |
| StockSheet | — | `end_offset_*`, `db_id`, `source_map` | yangi |
| Offcut.kind | remnant/waste | waste/remnant/**business** | |
| CutMap | — | `packs`, `waste_percent`, `offcut_area_m2`, `trim_*`, `first_cut` | yangi |
| CuttingResult | — | `total_packs`, `total_cuts`, `business_area_m2`, `waste_area_m2`, `material_qty_m2`, `warnings` | yangi |
| Operation | — | `owner_product_id`, `cl`, `cl_result`, `sp`, `o`, `lb` | yangi |
| Product | name, code, qty | + description, order_data, ready_date, phone1/2, extra, program | |
| Project | — | `uuid`, `executor` | yangi |
| CLParams, SPParams, OParams, OMaterial, LBParams, CLBar, CLResult | — | yangi modellar | |

Eski JSON loyihalarni o'qish uchun `migrate_v1_to_v2(data: dict)` funksiyasini yozing (Claude Code vazifasi):
trim qiymatlari almashtirilmaydi (qiymatlar bir xil bo'lgani uchun odatda 2/2), `is_remnant` → `kind`,
`remnant_min_area` → `business_area`, `price_per_m2=True` → `cost_by_sheets=False`,
`op_cost_base` int → str (0 cut_length, 1 part_perimeter, 2 part_area, 3 material_area),
EL yaxlitlash float → kod (0 → 10), `back_side` → `front = not back_side`.

## F3. Jadvallar (db.py)

| Jadval | Maqsad | v2 |
|---|---|---|
| folders | papkalar daraxti | — |
| projects | loyiha JSON + indeks ustunlar | + `executor` |
| project_history | undo/redo versiyalari | — |
| catalog_items | MES katalogi (daraxt) | + `grain`, `image_url`; kind: folder/sheet/linear/edge/surface/simple |
| settings_profiles | standartlar, chop profillari, ustun profillari, Excel import profillari, ko'rsatkichlar | API qo'shildi |
| remnants | ombordagi qoldiqlar | + `mes_id`, `material_name`, `kind`, `linear`, `status`, `reserved_project` |

`settings_profiles.scope` qiymatlari: `cs_cut`, `cs_material`, `el`, `gr`, `sp`, `cl`, `print`,
`part_columns`, `product_columns`, `operation_columns`, `excel_import`, `map_indicators`, `size_mode_prompt`.

## F4. Hodisalar (MES uchun)

| Hodisa | Qachon | Yuk |
|---|---|---|
| `project.ordered` | «Заказать» | project id, number, executor, status |
| `project.status_changed` | holat o'zgardi | eski/yangi holat |
| `cutting.done` | kroy tugadi | material kodi, listlar soni, material m², qoldiqlar |
| `remnants.saved` | qoldiqlar omborga | ro'yxat |
Webhook: `MES_WEBHOOK_URL` (POST JSON), qayta urinish bilan (outbox jadvali — Claude Code qo'shadi).
