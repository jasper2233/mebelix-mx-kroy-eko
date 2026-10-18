// Backend modellari (app/models.py) bilan mos TypeScript turlari.

export type OpType = "O" | "CS" | "CN" | "CL" | "EL" | "SP" | "GR" | "XNC" | "LB";
export type SizeMode = "blank" | "detail" | "jointed";
export type StripSortV = 0 | 1 | 2 | 3;
export type FirstCut = 0 | 1 | 2 | 3 | 4;
export type Quality = "fast" | "normal" | "max";

export interface EdgeRef { op_id: string | null }
export interface GrooveSide { op_id: string | null; back_side: boolean }

export interface Part {
  id: string;
  uid: number;
  product_id: string | null;
  name: string;
  description: string;
  code: string;
  length: number;
  width: number;
  qty: number;
  minus_qty: number;                  // МК — omborda tayyor, kroyga kirmaydi
  grain: boolean;
  edge_top: EdgeRef; edge_bottom: EdgeRef; edge_left: EdgeRef; edge_right: EdgeRef;
  groove_top: GrooveSide; groove_bottom: GrooveSide; groove_left: GrooveSide; groove_right: GrooveSide;
  allow_top: number; allow_bottom: number; allow_left: number; allow_right: number;
  group_by: "none" | "length" | "width";
  group_min: number;
  group_max: number;
  xnc_op_ids: string[];
  surface_face_op: string | null;
  surface_back_op: string | null;
  used_qty: number;
  left_qty: number;
  /** (CL) `.project` importidagi xom uzunlik: manfiy (masalan -350) — Bazis hisoblab bo'lmagan detal; length 0 bo'lsa ko'rsatiladi. */
  src_length?: number | null;
  /** Jadval «Настройки» → «Настроенный Параметры» ustunlari qiymatlari (nom → matn, masalan «part.name1»). */
  user_params?: Record<string, string>;
}

export interface StockSheet {
  id: string;
  length: number;
  width: number;
  qty: number;
  is_remnant: boolean;
  trim_length: number | null;
  trim_width: number | null;
  end_offset_bottom: number | null;
  end_offset_right: number | null;
  description: string;
  used_qty: number;
  source_remnant_id: number | null;
}

export interface CSMaterialParams {
  thickness: number; price: number; est_fill_percent: number; cost_by_sheets: boolean;
  sheet_rounding: string; op_cost_base: number; op_price: number; remnant_min_side1: number;
  remnant_min_side2: number; remnant_min_area: number; remnant_size_incl_trim: boolean; min_part_size: number;
}

export interface CSCutParams {
  kerf: number; kerf_group: number | null; trim_length: number; trim_width: number; trim_includes_kerf: boolean;
  end_offset_bottom: number | null; end_offset_right: number | null; first_cut: FirstCut; use_grain: boolean;
  complex_strips: boolean;
  max_rotations: number; pack_height: number; multiplicity: number; fill_packet: number; quality: Quality;
  max_part_types_per_map: number; prefer_big_pack: boolean; strip_sort: StripSortV; in_strip_sort: StripSortV;
  min_strip_width: number; max_strip_width: number; max_strip_length: number; min_trim_cut: number;
  merge_parts: boolean; save_drawings: boolean; machining_allowance: number;
  stock_order: "list" | "economy";     // «Порядок листов»: ro'yxat tartibi (qat'iy) / material tejash (tartib tanlanadi)
}

export interface ELParams {
  count_material: boolean; width: number; thickness: number; jointing_width: number; waste_percent: number;
  overhang: number; min_glue_length: number; symbol: string; color: string; marker_lines: number;
  min_perp_side: number; price: number; material_round: number; op_price: number; work_round: number;
}

export interface GRParams {
  width: number; depth: number; offset: number; offset_inclusive: boolean; saw_thickness: number; price: number;
  usage: number; cut_length: number; passes: number;      // hisoblangan (faqat o'qish)
}

/** (SP) Обработка поверхности (W12): backend `models.SPParams`. `area_m2` / `material_m2` — hisoblangan (faqat o'qish). */
export interface SPParams {
  count_material: boolean; waste_percent: number; rest_side: number; size_mode: -1 | 0; op_price: number; price: number;
  area_m2: number; material_m2: number;
  length: number; width: number; thickness: number;   // material o'lchami (mm)
}

/** `GET .../surface-usage`: sirt ishlovi hisobi (detallar jadvali + jami). */
export interface SurfaceUsage {
  rows: { part_id: string; uid: number; material: string; length: number; width: number; front: boolean; back: boolean;
          sides: number; qty: number; calc_length: number; calc_width: number; area_m2: number; name: string }[];
  area_m2: number; material_m2: number; cost_material: number; cost_operation: number; cost: number;
}

export interface XncCommand {
  cmd: string;
  params: Record<string, string | number>;
  comment: string;
  enabled?: boolean;
  children: XncCommand[];
}

export interface XNCParams {
  by_part_size: boolean; length: number; width: number; thickness: number; qty: number; face_side: boolean;
  rotation: 0 | 90 | 180 | 270; mirror_x: boolean; mirror_y: boolean; origin: "LT" | "RT" | "LB" | "RB";
  program: XncCommand[]; drill_price: number; mill_price_m: number; saw_price_m: number; extra_cost: number;
  /** «Параметры» yorlig'ida kiritilgan Par qiymatlari {Par nomi: son yoki ifoda}; yo'q bo'lsa — Par.value. */
  par_values?: Record<string, number | string>;
  /** detaldan hisoblangan o'zgaruvchilar (faqat o'qish): matThickness, allowanceT … */
  part_vars?: Record<string, number>;
}

/** Dasturdagi Par buyrug'ining hisoblangan holati (GET /projects/{pid}/operations/{oid}/xnc-params). */
export interface XncParamState {
  name: string; label: string; type: "double" | "integer" | "boolean" | "string"; suffix: string; default: number | string | null;
  value: number | string | null; visible: boolean; readonly: boolean; n: string;
}

/** XNC shablon (kutubxona yozuvi): `lib:<kalit>` — o'rnatilgan, `u:<id>` — foydalanuvchi. */
export interface XncTemplateInfo {
  id: string; name: string; description: string; category: string; builtin: boolean; par_count: number; commands: number;
}
export interface XncTemplate extends XncTemplateInfo { program: XncCommand[]; par_values: Record<string, number | string> }

export interface XncPostprocessor {
  key: string; name: string; extension: string; builtin: boolean; profile_id?: number; machine?: boolean; available?: boolean;
  native?: boolean; note?: string; label?: string; order?: number;   // o'rnatilgan stanok formati, eslatma, oynadagi yozuv
  kind?: "saw" | "xnc" | "any";                                       // shablon konteksti (saw — pil markazi, XNC ro'yxatida yo'q)
}

export interface Placement {
  part_id: string; part_uid: number; x: number; y: number; length: number; width: number; rotated: boolean;
  /** (CN, W16) nesting: burilish (gradus, soat mili bo'yicha), tashqi kontur, ichki kesimlar va etiketka o'rni [cx, cy, w, h, burchak]; list koordinatalarida. */
  angle?: number; outline?: number[][]; holes?: number[][][]; label?: number[] | null;
}

export interface Offcut {
  x: number; y: number; length: number; width: number; kind: "remnant" | "waste"; number: number;
  business: boolean; raw_length: number; raw_width: number;
  /** (CN) > 0 — qoldiq shu uid li detalning ichki kesimida; 0 — detalsiz bo'sh joy. */
  in_part?: number;
}

export interface CutCommand { code: "R" | "T" | "C" | "P" | "W"; level: number; size: number; count: number; ref: string }

/** Kesish daraxti tuguni (list koordinatalarida). k: C — bolali, P — detal, W — chiqindi/qoldiq */
export interface TreeNode {
  x: number; y: number; l: number; w: number; k: "C" | "P" | "W";
  a?: "x" | "y"; c?: TreeNode[]; u?: number; o?: number; r?: number;
  /** guruh (blok) tuguni: bolalar orasidagi propil (W13) */
  g?: number;
}

export interface CutMap {
  index: number; sheet_id: string; sheet_length: number; sheet_width: number; is_remnant: boolean; copies: number;
  placements: Placement[]; offcuts: Offcut[]; commands: CutCommand[]; parts_count: number; cut_length_m: number;
  cuts_count: number; fill_percent: number; parts_area_m2: number; sheet_area_m2: number; remnant_area_m2: number;
  comment: string; done_count: number; packs: number; strips: TreeNode[];
  /** «Торцовка листа» (W13): shu kartaga alohida torsovka; null — list qatori / operatsiya qiymati */
  trim_length?: number | null; trim_width?: number | null; end_offset_bottom?: number | null; end_offset_right?: number | null;
}

export interface CuttingResult {
  maps: CutMap[]; total_sheets: number; total_parts: number; unplaced: string[]; total_cut_length_m: number;
  total_cuts: number; total_fill_percent: number; parts_area_m2: number; material_area_m2: number;
  remnant_area_m2: number; remnants: Offcut[]; variant: string; manual: boolean; remnants_saved: boolean;
  saved_remnant_ids: number[]; consumed_remnants: Record<string, number>; elapsed_s: number;
  sheets_per_pack: number; total_packs: number; material_qty_m2: number; warnings: string[];
  /** «Исп. кол-во» qoldiq qatorlari: mijoz olib ketadigan bo'laklar (kalit `b:UxE` / `r:UxE`, yuzdan birlarda) — omborga yozilmaydi. */
  taken_remnants?: Record<string, number>;
  /** (CL, W11) "linear" — pogonaj kroy: kartalar polosa (1D); `*_m2` maydonlar polosa eni bilan (L × eni) hisoblanadi. */
  kind?: "sheet" | "linear" | "nest"; material_len_m?: number; business_len_m?: number;
  /** (CN, W16) hisoblash ma'lumoti: trials, cells, elapsed_s, timed_out, input_rev, spacing, margin … */
  nest?: Record<string, unknown>;
}

/** (CN) Нестинговый раскрой (W16): backend `models.CNParams`. Hamma o'lchamlar — mm; `usage_m2` / `multiplicity` — hisoblangan (faqat o'qish). */
export interface CNParams {
  thickness: number; price: number; cost_by_sheets: boolean; sheet_rounding: string; est_fill_percent: number;
  op_cost_base: 0 | 1 | 2 | 3; op_price: number;
  tool_diameter: number; tool_offset: number | null; part_gap: number; margin: number; arc_tol: number;
  rot90: boolean; rot_step: number; use_grain: boolean; use_xnc_contours: boolean;
  remnant_min_side1: number; remnant_min_side2: number; remnant_min_area: number; min_part_size: number;
  label_w: number; label_h: number; quality: Quality; time_limit_s: number;
  /** auto — optimizator detallar tartibini o'zi tanlaydi; list — «Детали» jadvali tartibida joylanadi. */
  sort_mode: "auto" | "list";
  usage_m2: number; multiplicity: number;
}

/** `GET .../cn-quantities`: kroygacha (estimated) / keyin material (m²), listlar, kesim uzunligi va narx. */
export interface CnQuantities {
  estimated: boolean; sheets: number; sheets_total: number; material_qty_m2: number; sheet_area_m2: number; parts_area_m2: number;
  op_base: number; cut_length_m: number; multiplicity: number; cost_material: number; cost_operation: number;
}

/** `GET .../cn-shapes`: detal shakli (kontur / to'rtburchak), ichki kesimlar, etiketka o'rni va ogohlantirishlar. */
export interface CnShapeRow {
  id: string; uid: number; kind: "rect" | "contour"; area_mm2: number; perimeter_mm: number; width: number; height: number;
  holes: number; points: number; outline: number[][]; hole_rings: number[][][];
  label: number[] | null; label_free: number[] | null; label_fits: boolean; warnings: string[];
}
export interface CnShapes { parts: CnShapeRow[]; spacing: number; margin: number; bad: number; small: number }

/** (CN) Fon vazifasi (`POST …/cn/jobs`): state running | done | error | cancelled; `result` — tugagach qisqa xulosa. */
export interface CnJob {
  id: string; state: "running" | "done" | "error" | "cancelled"; progress: number; message: string; elapsed_s: number;
  error: string; quality: Quality;
  result: { sheets: number; fill: number; unplaced: number; elapsed_s: number; maps: number; warnings: number } | null;
}

/** (CL) Погонажный раскрой: backend `models.CLParams` (W11). `usage_m` / `multiplicity` — hisoblangan (faqat o'qish). */
export interface CLParams {
  width: number; thickness: number; kerf: number; trim: number; end_offset: number | null; pack_height: number;
  fill_packet: number; quality: Quality; waste_min: number; business_min: number; waste_incl_trim: boolean;
  min_part_len: number; machining_allowance?: number; price: number; price_by_strip: boolean; strip_rounding: string; est_fill_percent: number;
  op_cost_base: 0 | 1 | 2 | 3; op_price: number; usage_m: number; multiplicity: number;
  max_part_types_per_map: number; merge_parts: boolean; group_parts: number; save_drawings: boolean;
}

/** `GET .../cl-quantities`: kroygacha (estimated) / keyin material, polosa va kesim ko'rsatkichlari. */
export interface ClQuantities {
  estimated: boolean; strips: number; strips_total: number; material_len_m: number; business_len_m: number; parts_len_m: number;
  material_qty_m: number; cut_with_trim_m: number; cut_no_trim_m: number; op_base: number; multiplicity: number;
  cost_material: number; cost_operation: number;
}

/** `GET .../cs-quantities`: kroygacha (estimated) / keyin material va list miqdori. */
export interface CsQuantities {
  estimated: boolean; sheets: number; sheets_total: number; material_qty_m2: number; sheet_area_m2: number;
  parts_area_m2: number; cost_material: number; cost_operation: number;
}

export interface Operation {
  id: string; type: OpType; code: string; name: string; material_id: string | null; print: boolean;
  new_page: boolean; description: string; cs_material: CSMaterialParams | null; cs_cut: CSCutParams | null;
  parts: Part[]; sheets: StockSheet[]; result: CuttingResult | null; el: ELParams | null; gr: GRParams | null;
  xnc: XNCParams | null; xnc_part_id: string | null; o: OParams | null; cost_material: number; cost_operation: number;
  lb?: LBParams | null;
  sp?: SPParams | null;
  cl?: CLParams | null;
  cn?: CNParams | null;
}

/** (LB) Этикетки: backend `models.LBParams` (W4). Shablon/shablon parametrlari — `features/print/labelsApi.ts`. */
export interface LBParams {
  source: "parts" | "products" | "user"; mode: "sheet" | "roll"; rotate_page: 0 | 90; width_mm: number; height_mm: number;
  columns: number; rows: number; gap_mm: number; margin_mm: number | null; border: boolean;
  border_mode?: "none" | "perimeter" | null;      // «Границы»; null — eski `border` bayrog'idan
  part_selected_only?: boolean | null;              // «Выбранные детали»; null — ro'yxat bo'sh bo'lmasa yoqiq
  cs_op_id: string | null;
  print_parts: boolean; part_each: boolean; part_only_nonzero: boolean; part_selected: number[]; label_count: number;
  print_wastes: boolean; waste_each: boolean; waste_business_only: boolean; product_each: boolean; product_only_nonzero: boolean;
  template_id: string | null; template: Record<string, unknown> | null; params: Record<string, string | number | boolean>;
  fields: Record<string, unknown>[]; data: Record<string, unknown>[]; legacy_program: string;
}

/** (O) Комплектация: materiallar jadvali qatori (Стоимость = qty × price — hisoblanadi) */
export interface OMaterial { id: string; code: string; name: string; unit: string; qty: number; price: number;
  /** «Настроенный Параметры» ustunlari qiymatlari (masalan «material.name1» → matn) */
  user_params?: Record<string, string> }

export interface OParams {
  owner_product_id: string | null; materials: OMaterial[]; work_cost: number;
  multiplier: number;           // hisoblangan: egasi mahsulot soni (yoki 1) — faqat o'qish
  messages: string[];           // hisoblangan xabar kodlari («owner_lost»)
}

/** Mahsulot dasturi xabari (hisoblangan): info (Msg) | warning (xato ifoda / tushunilmagan buyruq) | error (Err — cheklov buzildi). */
export interface ProgMessage { level: "info" | "warning" | "error"; text: string; path: string }

export interface Product {
  id: string; code: string; name: string; qty: number; cost_material: number; cost_operation: number;
  order_info: string; ready_date: string; phone1: string; phone2: string; extra: Record<string, string>;
  description: string; messages: string[];
  /** «Программа» (W12): faqat boshqaruv buyruqlari; `par_values` — kiritilgan Par qiymatlari; `prog_*` — hisoblangan (faqat o'qish). */
  program?: XncCommand[]; par_values?: Record<string, number | string>; legacy_program?: string;
  prog_vars?: Record<string, number>; prog_messages?: ProgMessage[];
}

/** `GET .../products/{prid}/program-state`: Par parametrlari holati, o'zgaruvchilar va xabarlar (so'rov tilida). */
export interface ProgramState {
  params: XncParamState[]; vars: Record<string, number>; messages: ProgMessage[]; errors: number; warnings: number; problems: number;
}

/** `POST .../actions/recalc-parametric` hisoboti. */
export interface ParametricReport {
  products: { id: string; name: string; vars: number; errors: number; warnings: number; info: number; messages: ProgMessage[] }[];
  xnc: { id: string; code: string; name: string; errors: number; messages: string[] }[];
  totals: { products: number; programs: number; xnc: number; errors: number; warnings: number; xnc_errors: number };
}

export type OrderStatus = 0 | 1 | 2 | 3;

/** «Заказать» oqimi tarixi (W14): kim, qachon (UTC, ISO), qaysi holatdan qaysisiga; ijrochi/izoh — faqat ichki matn. */
export interface OrderLogEntry {
  at: string; user: string; from_status: OrderStatus; to_status: OrderStatus; executor: string; comment: string;
  ready_date: string; via: string;
}

export interface Project {
  id: string; number: number; name: string; folder_id: string | null; owner: string; currency: string;
  order_date: string; ready_date: string; note: string; status: OrderStatus; size_mode: SizeMode;
  operations: Operation[]; products: Product[]; mes_order_ref: string | null; customer: string;
  order_log?: OrderLogEntry[];       // eski loyihalarda yo'q (bo'sh)
}

export interface ProjectRow {
  id: string; number: number; owner: string; status: OrderStatus; order_date: string; cost: number; name: string;
  folder_id: string | null; customer: string; mes_order_ref: string | null; updated_at: string | null;
}

export interface Folder { id: string; name: string; parent_id: string | null }

/** Material bazasi tekshiruvi (2026-10-15): har kroy operatsiyasi uchun kerak / bazada / yetmaydi. */
export interface MaterialCheckItem {
  op_id: string; type: string; code: string; name: string; thickness: number | null; need: number; estimated: boolean;
  have: number | null; short: number | null; remnants: number; status: "ok" | "short" | "unknown";
  catalog_id: string | null; catalog_name: string | null;
}
export interface MaterialCheck {
  project_id: string; number: number; name: string; status: OrderStatus; ok: boolean; known: boolean; estimated: boolean;
  items: MaterialCheckItem[]; warnings: string[]; position?: number; next?: boolean;
}
export interface QueueInfo {
  count: number; statuses: number[]; next: { project_id: string; number: number; name: string } | null;
  rows: MaterialCheck[]; warnings: string[]; message: string;
}

export interface HistoryInfo { version: number; first: number; last: number; can_undo: boolean; can_redo: boolean }

export interface EdgeUsage {
  rows: { part_id: string; uid: number; material: string; op_type?: string; length: number; edges_len: number; width: number;
          edges_wid: number; qty: number; edge_m: number; name: string; narrow: boolean }[];
  work_m: number; material_m: number; narrow: number;
}

export interface XncStats {
  drills: number; mill_m: number; saw_m: number; unit_cost: number; qty: number; cost: number;
  errors?: number; warnings?: string[]; params?: XncParamState[];
  /** har xabar (`warnings[i]`) uchun manba buyruq yo'llari (0 dan, `pathKey`): dastur ro'yxatida qator qizil belgilanadi */
  warning_src?: string[][];
  /** Stanok cheklovlari (W8, «Настройки → XNC → Ограничения»): xabarlar, rejim, cheklov belgilagan qo'shimcha burish (gradus). */
  constraint_issues?: { level: "warn" | "error"; code: string; text: string; text_ru?: string; text_uz?: string;
                        command_path: string; count?: number }[];
  constraint_mode?: "off" | "warn" | "block"; constraint_turn?: number;
}

export interface Variant {
  variant: "optimal" | "length" | "width" | ClVariantKey; sheets: number; fill: number; cut_m: number; cuts: number;
  unplaced: number; remnant_m2: number; result: CuttingResult;
  /** (CL, W18) pogonaj kroy variantlari: material / деловой otxod uzunligi (m), kartalar soni; `same_as` — natijasi shu kalitli variant bilan bir xil. */
  material_len_m?: number; business_len_m?: number; maps?: number; same_as?: ClVariantKey | null;
}
export type ClVariantKey = "material" | "consumption" | "cuts" | "max";

export interface Remnant {
  id: number; material_code: string; material_name: string; length: number; width: number; thickness: number;
  qty: number; area_m2: number; source_project: string | null; source_number: number | null; source_op: string | null;
  note: string; created_at: string | null;
  /** Rezerv: qoldiqni band qilgan loyiha (id va raqami); bo'sh — erkin. */
  reserved_project?: string | null; reserved_number?: number | null;
  /** (CL, W11) погонажный qoldiq: `length` — uzunlik, `width` — polosa eni. */
  linear?: boolean;
}

export type HatchKind = "none" | "diag" | "cross" | "horizontal" | "vertical";

export interface PrintSettings {
  header: boolean; materials_list: boolean; warehouse: boolean; warehouse_cut_work: boolean;
  warehouse_edge_work: boolean; products_list: boolean; operations: boolean; xnc_stats: boolean;
  cs_parts: boolean; cs_unplaced: boolean; cs_sheets: boolean; cs_remnants: boolean; cs_maps: boolean;
  cs_commands: boolean; cs_size_mode: SizeMode | null; map_parts_list: boolean;
  map_part_label: "number" | "name" | "number_name" | "none"; map_edges: boolean; map_remnant_number: boolean; map_qr: boolean;
  map_header_fields: string[]; map_mirror: boolean; el_params: boolean; el_parts: boolean; xnc_drawing: boolean;
  el_header_work: boolean; el_header_material: boolean; gr_params: boolean; gr_parts: boolean;
  o_params: boolean; o_materials: boolean;
  sp_params?: boolean; sp_parts?: boolean;           // (SP) W12 — eski profillarda yo'q bo'lishi mumkin (backend standart bilan to'ldiradi)
  // (CL) W11 — pogonaj kroy chop sozlamalari (R5: 7 ta belgi + buyruqlar jadvali)
  cl_header?: boolean; cl_parts?: boolean; cl_group_by_product?: boolean; cl_unplaced?: boolean; cl_strips?: boolean;
  cl_remnants?: boolean; cl_maps?: boolean; cl_commands?: boolean;
  // (CN) W16 — nesting kroy chop sozlamalari
  cn_params?: boolean; cn_parts?: boolean; cn_unplaced?: boolean; cn_sheets?: boolean; cn_remnants?: boolean; cn_maps?: boolean;
  // (CS) v2.2 W2 — eski profillarda yo'q bo'lishi mumkin (backend standart bilan to'ldiradi)
  cs_title?: boolean; cs_group_by_product?: boolean; cs_edge_highlight?: boolean;
  map_orientation?: "portrait" | "landscape"; map_part_marks?: boolean; map_allowance?: boolean;
  map_num_font?: number; map_num_bold?: boolean; map_dim_font?: number; map_dim_bold?: boolean; map_dim_rotate?: boolean;
  map_part_fill?: string; map_part_hatch?: HatchKind; map_waste_fill?: string; map_waste_hatch?: HatchKind;
  page_margin_left: number; page_margin_right: number; page_margin_top: number; page_margin_bottom: number;
  // §11 (2026-10-15) — chop oynalari «Параметр | Значение»: yangi variantlar (eski profillarda yo'q bo'lishi mumkin; backend standart bilan to'ldiradi)
  materials_group_by_code?: boolean; products_list_single?: boolean; operations_list?: boolean; operations_list_single?: boolean;
  xnc_stats_group?: "none" | "material" | "product"; xnc_stat_cols?: PrintCol[];
  prod_header?: boolean; prod_operations?: boolean; prod_materials?: boolean; prod_parts?: boolean;
  page_mirror_margins?: boolean; page_footer_pos?: "bottom" | "top" | "none";
  cs_warehouse?: boolean; cs_stats?: boolean; cs_edge_symbols?: boolean; cs_parts_form?: "merged" | "sides";
  map_mirror_h?: "no" | "yes" | "cuts_v" | "cuts_h"; map_mirror_v?: boolean; map_part_expr?: string;
  map_edge_marker?: "lines" | "symbols" | "both"; map_edge_line_style?: "solid" | "dashed" | "dotted"; map_machining?: boolean;
  map_header_cols?: PrintCol[];
  xnc_back_mirror?: "horizontal" | "vertical" | "none"; xnc_origin_as_op?: boolean;
  xnc_origin?: "lt" | "t" | "rt" | "l" | "c" | "r" | "lb" | "b" | "rb";
  cl_warehouse?: boolean; cl_stats?: boolean;
}

/** Chop jadvali ustuni («Заголовок карт кроя», XNC «Статистика»): kalit, yoqilgan, kenglik (belgida). */
export interface PrintCol { key: string; on: boolean; width: number }

export interface LabelSettings {
  width_mm: number; height_mm: number; columns: number; qr: boolean; show_edges: boolean; show_product: boolean;
  show_map: boolean;
}

export interface PostprocessorProfile {
  id?: string; name: string; extension: string; per_map: boolean; encoding: string; newline: "lf" | "crlf";
  template: string; description: string;
}

export interface Profile<T = unknown> { id: number; scope: string; name: string; data: T; is_default: boolean }

export interface AppSettings {
  currency: string; language: "ru" | "uz"; input_mode_suggest: "none" | "blank" | "detail" | "jointed";
  remnant_confirm: boolean; default_sheet_length: number; default_sheet_width: number;
  mes_enabled: boolean;
}

export interface PpMachine {
  key: string; name: string; group: "saw" | "cnc"; enabled: boolean;
  profile_id: number | null; profile_name: string | null; bound: boolean;
  native?: boolean; native_ext?: string; native_note?: string;   // o'rnatilgan format (shablonsiz ishlaydi)
}
export interface PpMachines { prefix: boolean; groups: { key: "saw" | "cnc"; machines: PpMachine[] }[] }

export interface CatalogItem {
  id: string; parent_id: string | null; kind: string; code: string; name: string; unit: string; price: number;
  stock: number; thickness: number | null; length: number | null; width: number | null; params: Record<string, unknown>;
  has_image?: boolean;               // rasm bor (rasmning o'zi — `GET /catalog/{id}` → `image`)
}

export interface PostprocessorInfo {
  key: string; name: string; extension: string; builtin: boolean; profile_id?: number;
  machine?: boolean; available?: boolean;
  native?: boolean; note?: string; label?: string; order?: number;      // o'rnatilgan format, eslatma, oynadagi yozuv, tartib
}

export interface ImportPreview { sheets: string[]; columns: string[]; rows: string[][]; sheet?: string; format?: "xlsx" | "xls" | "csv" }

export interface Me { sub: string; name: string; roles: string[] }
