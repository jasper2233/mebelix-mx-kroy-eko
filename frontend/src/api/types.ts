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
}

export interface StockSheet {
  id: string;
  length: number;
  width: number;
  qty: number;
  is_remnant: boolean;
  trim_length: number | null;
  trim_width: number | null;
  description: string;
  used_qty: number;
  source_remnant_id: number | null;
}

export interface CSMaterialParams {
  thickness: number; price: number; price_per_m2: boolean; est_fill_percent: number; cost_by_sheets: boolean;
  sheet_rounding: string; op_cost_base: number; op_price: number; remnant_min_side1: number;
  remnant_min_side2: number; remnant_min_area: number; remnant_size_incl_trim: boolean; min_part_size: number;
}

export interface CSCutParams {
  kerf: number; kerf_group: number | null; trim_length: number; trim_width: number; trim_includes_kerf: boolean;
  trim_both_sides: boolean; min_end_offset: number; first_cut: FirstCut; use_grain: boolean; complex_strips: boolean;
  max_rotations: number; pack_height: number; multiplicity: number; fill_packet: number; quality: Quality;
  max_part_types_per_map: number; prefer_big_pack: boolean; strip_sort: StripSortV; in_strip_sort: StripSortV;
  min_strip_width: number; max_strip_width: number; max_strip_length: number; min_trim_cut: number;
  merge_parts: boolean; save_drawings: boolean; machining_allowance: number;
}

export interface ELParams {
  count_material: boolean; width: number; thickness: number; jointing_width: number; waste_percent: number;
  overhang: number; min_glue_length: number; symbol: string; color: string; marker_lines: number;
  min_perp_side: number; price: number; material_rounding: number; op_price: number; work_rounding: number;
}

export interface GRParams { width: number; depth: number; offset: number; price: number }

export interface XncCommand {
  cmd: string;
  params: Record<string, string | number>;
  comment: string;
  children: XncCommand[];
}

export interface XNCParams {
  by_part_size: boolean; length: number; width: number; thickness: number; qty: number; face_side: boolean;
  rotation: 0 | 90 | 180 | 270; mirror_x: boolean; mirror_y: boolean; origin: "LT" | "RT" | "LB" | "RB";
  program: XncCommand[]; drill_price: number; mill_price_m: number; saw_price_m: number; extra_cost: number;
}

export interface Placement {
  part_id: string; part_uid: number; x: number; y: number; length: number; width: number; rotated: boolean;
}

export interface Offcut {
  x: number; y: number; length: number; width: number; kind: "remnant" | "waste"; number: number;
  business: boolean; raw_length: number; raw_width: number;
}

export interface CutCommand { code: "R" | "T" | "C" | "P" | "W"; level: number; size: number; count: number; ref: string }

/** Kesish daraxti tuguni (list koordinatalarida). k: C — bolali, P — detal, W — chiqindi/qoldiq */
export interface TreeNode {
  x: number; y: number; l: number; w: number; k: "C" | "P" | "W";
  a?: "x" | "y"; c?: TreeNode[]; u?: number; o?: number; r?: number;
}

export interface CutMap {
  index: number; sheet_id: string; sheet_length: number; sheet_width: number; is_remnant: boolean; copies: number;
  placements: Placement[]; offcuts: Offcut[]; commands: CutCommand[]; parts_count: number; cut_length_m: number;
  cuts_count: number; fill_percent: number; parts_area_m2: number; sheet_area_m2: number; remnant_area_m2: number;
  comment: string; done_count: number; packs: number; strips: TreeNode[];
}

export interface CuttingResult {
  maps: CutMap[]; total_sheets: number; total_parts: number; unplaced: string[]; total_cut_length_m: number;
  total_cuts: number; total_fill_percent: number; parts_area_m2: number; material_area_m2: number;
  remnant_area_m2: number; remnants: Offcut[]; variant: string; manual: boolean; remnants_saved: boolean;
  saved_remnant_ids: number[]; consumed_remnants: Record<string, number>; elapsed_s: number;
  sheets_per_pack: number; total_packs: number;
}

export interface Operation {
  id: string; type: OpType; code: string; name: string; material_id: string | null; print: boolean;
  new_page: boolean; description: string; cs_material: CSMaterialParams | null; cs_cut: CSCutParams | null;
  parts: Part[]; sheets: StockSheet[]; result: CuttingResult | null; el: ELParams | null; gr: GRParams | null;
  xnc: XNCParams | null; xnc_part_id: string | null; cost_material: number; cost_operation: number;
}

export interface Product {
  id: string; code: string; name: string; qty: number; cost_material: number; cost_operation: number;
}

export type OrderStatus = 0 | 1 | 2 | 3;

export interface Project {
  id: string; number: number; name: string; folder_id: string | null; owner: string; currency: string;
  order_date: string; ready_date: string; note: string; status: OrderStatus; size_mode: SizeMode;
  operations: Operation[]; products: Product[]; mes_order_ref: string | null; customer: string;
}

export interface ProjectRow {
  id: string; number: number; owner: string; status: OrderStatus; order_date: string; cost: number; name: string;
  folder_id: string | null; customer: string; mes_order_ref: string | null; updated_at: string | null;
}

export interface Folder { id: string; name: string; parent_id: string | null }

export interface HistoryInfo { version: number; first: number; last: number; can_undo: boolean; can_redo: boolean }

export interface EdgeUsage {
  rows: { part_id: string; uid: number; material: string; length: number; edges_len: number; width: number;
          edges_wid: number; qty: number; edge_m: number; name: string; narrow: boolean }[];
  work_m: number; material_m: number; narrow: number;
}

export interface XncStats { drills: number; mill_m: number; saw_m: number; unit_cost: number; qty: number; cost: number }

export interface Variant {
  variant: "optimal" | "length" | "width"; sheets: number; fill: number; cut_m: number; cuts: number;
  unplaced: number; remnant_m2: number; result: CuttingResult;
}

export interface Remnant {
  id: number; material_code: string; material_name: string; length: number; width: number; thickness: number;
  qty: number; area_m2: number; source_project: string | null; source_number: number | null; source_op: string | null;
  note: string; created_at: string | null;
}

export interface PrintSettings {
  header: boolean; materials_list: boolean; warehouse: boolean; warehouse_cut_work: boolean;
  warehouse_edge_work: boolean; products_list: boolean; operations: boolean; xnc_stats: boolean;
  cs_parts: boolean; cs_unplaced: boolean; cs_sheets: boolean; cs_remnants: boolean; cs_maps: boolean;
  cs_commands: boolean; cs_size_mode: SizeMode | null; map_parts_list: boolean;
  map_part_label: "number" | "name" | "number_name"; map_edges: boolean; map_remnant_number: boolean; map_qr: boolean;
  map_header_fields: string[]; map_mirror: boolean; el_params: boolean; el_parts: boolean; xnc_drawing: boolean;
}

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
}

export interface CatalogItem {
  id: string; parent_id: string | null; kind: string; code: string; name: string; unit: string; price: number;
  stock: number; thickness: number | null; length: number | null; width: number | null; params: Record<string, unknown>;
}

export interface PostprocessorInfo { key: string; name: string; extension: string; builtin: boolean; profile_id?: number }

export interface ImportPreview { sheets: string[]; columns: string[]; rows: string[][] }

export interface Me { sub: string; name: string; roles: string[] }
