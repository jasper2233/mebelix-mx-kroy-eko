"""MebeliX Kroy — ma'lumotlar modellari (Pydantic v2).

Terminlar (UZ / RU):
  Loyiha / Проект, Operatsiya / Операция, Mahsulot (izdeliya) / Изделие,
  Detal / Деталь, List / Лист, Qoldiq / Остаток, Kroy kartasi / Карта кроя,
  Kromka / Кромка, Pazovanie / Пазование, Torsovka / Торцовка, Propil / Пропил.
Barcha o'lchamlar — mm, maydon — m², uzunlik hisobotda — m.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _id() -> str:
    return uuid4().hex[:12]


# ───────────────────────── Enumlar ─────────────────────────
class OpType(str, Enum):
    O = "O"      # Komplektatsiya va boshqa amallar
    CS = "CS"    # Listli kroy
    CN = "CN"    # Nesting kroy (keyinroq)
    CL = "CL"    # Pogonaj kroy
    EL = "EL"    # Kromka
    SP = "SP"    # Sirt ishlovi
    GR = "GR"    # Pazovanie
    XNC = "XNC"  # CNC ishlov
    LB = "LB"    # Etiketkalar


class OrderStatus(int, Enum):
    NOT_ORDERED = 0   # Не заказан
    ORDERED = 1       # Заказан
    APPROVED = 2      # Утвержден
    READY = 3         # Готов


class SizeMode(str, Enum):
    BLANK = "blank"             # Заготовка o'lchami
    DETAIL = "detail"           # Detal o'lchami (kromka bilan)
    JOINTED = "jointed"         # Prifugovkadan keyingi (kromkasiz)


class SheetRounding(str, Enum):
    WHOLE = "11"; ANY_1_2 = "12"; ANY_1_3 = "13"; ANY_1_4 = "14"
    W_1_2 = "22"; W_1_3 = "23"; W_1_4 = "24"
    L_1_2 = "32"; L_1_3 = "33"; L_1_4 = "34"


class OpCostBase(int, Enum):
    CUT_LENGTH = 0       # Kesish uzunligi bo'yicha
    PART_PERIMETER = 1   # Detal perimetri
    PART_AREA = 2        # Detal maydoni
    MATERIAL_AREA = 3    # Material maydoni


class FirstCutDir(int, Enum):
    ANY = 0; LENGTH = 1; WIDTH = 2; LENGTH_PREF = 3; WIDTH_PREF = 4


class StripSort(int, Enum):
    DESC = 0; ASC = 1; NARROW_CENTER = 2; NONE = 3


# ───────────────────────── Detal ─────────────────────────
class EdgeRef(BaseModel):
    """Detal tomonidagi kromka: EL operatsiyasi id si (None = kromka yo'q)."""
    op_id: Optional[str] = None


class GrooveSide(BaseModel):
    op_id: Optional[str] = None
    back_side: bool = False     # Tomoni (lits/orqa)


class Part(BaseModel):
    id: str = Field(default_factory=_id)
    uid: int = 0                        # ID (loyiha ichidagi raqam)
    product_id: Optional[str] = None    # Изделие
    name: str = ""
    description: str = ""
    code: str = ""
    length: float                        # kiritilgan uzunlik (size_mode ga qarab)
    width: float
    qty: int = 1
    grain: bool = False                  # Ткт — teksturani hisobga ol, aylantirma
    # Kromka: top/bottom — uzunlik bo'yicha, left/right — eni bo'yicha
    edge_top: EdgeRef = EdgeRef()
    edge_bottom: EdgeRef = EdgeRef()
    edge_left: EdgeRef = EdgeRef()
    edge_right: EdgeRef = EdgeRef()
    groove_top: GrooveSide = GrooveSide()
    groove_bottom: GrooveSide = GrooveSide()
    groove_left: GrooveSide = GrooveSide()
    groove_right: GrooveSide = GrooveSide()
    # Ishlov berish uchun pripusk (▽ △ ▷ ◁)
    allow_top: float = 0; allow_bottom: float = 0
    allow_left: float = 0; allow_right: float = 0
    # Guruhlash (blokga birlashtirish)
    group_by: Literal["none", "length", "width"] = "none"
    group_min: int = 0
    group_max: int = 0
    xnc_op_ids: list[str] = []           # bog'langan XNC operatsiyalar
    surface_face_op: Optional[str] = None
    surface_back_op: Optional[str] = None
    used_qty: int = 0                    # ИК (kroyga kirgan)
    left_qty: int = 0                    # Ост (kirmay qolgan)


# ───────────────────────── Listlar / qoldiqlar ─────────────────────────
class StockSheet(BaseModel):
    id: str = Field(default_factory=_id)
    length: float
    width: float
    qty: int = 10000                     # 10000 = cheklanmagan
    is_remnant: bool = False             # ombordagi qoldiq
    trim_length: Optional[float] = None  # ТД (bo'sh bo'lsa umumiy parametr)
    trim_width: Optional[float] = None   # ТШ
    description: str = ""
    used_qty: int = 0


# ───────────────────────── Parametrlar ─────────────────────────
class CSMaterialParams(BaseModel):
    thickness: float = 16
    price: float = 0                         # 1 list / 1 m² narxi
    price_per_m2: bool = False
    est_fill_percent: float = 90             # Расчетный процент заполнения
    cost_by_sheets: bool = True              # Расчет стоимости по листам
    sheet_rounding: SheetRounding = SheetRounding.WHOLE
    op_cost_base: OpCostBase = OpCostBase.CUT_LENGTH
    op_price: float = 0                      # 1 m / 1 m² narxi
    remnant_min_side1: float = 1000
    remnant_min_side2: float = 500
    remnant_min_area: float = 0.5            # m²
    remnant_size_incl_trim: bool = True
    min_part_size: float = 30


class CSCutParams(BaseModel):
    kerf: float = 3                          # Толщина пилы
    kerf_group: Optional[float] = None       # guruh detallar uchun
    trim_length: float = 2                   # Торцовка по длине
    trim_width: float = 2                    # Торцовка по ширине
    trim_includes_kerf: bool = False
    trim_both_sides: bool = True             # torsovka listning ikkala chetidan
    min_end_offset: float = 0
    first_cut: FirstCutDir = FirstCutDir.ANY
    use_grain: bool = True                   # Учет текстуры
    complex_strips: bool = True              # Использовать сложные полосы (3-bosqich)
    max_rotations: int = 6
    pack_height: float = 40                  # Высота пакета (mm)
    multiplicity: int = 2                    # Кратность
    fill_packet: float = 90                  # Процент заполнения для кратности (%)
    quality: Literal["fast", "normal", "max"] = "normal"   # kroy sifati / vaqt (Tez / Standart / Maksimal)
    max_part_types_per_map: int = 0          # 0 = cheklanmagan
    prefer_big_pack: bool = True
    strip_sort: StripSort = StripSort.DESC
    in_strip_sort: StripSort = StripSort.NONE
    min_strip_width: float = 0
    max_strip_width: float = 0
    max_strip_length: float = 10000
    min_trim_cut: float = 5                  # Минимальная обрезка
    merge_parts: bool = False
    save_drawings: bool = True
    machining_allowance: float = 0           # Припуск на обработку заготовки


class ELParams(BaseModel):
    count_material: bool = True
    width: float = 19
    thickness: float = 0                     # kromka qalinligi → detal o'lchamidan ayriladi
    jointing_width: float = 0                # Ширина прифуговки
    waste_percent: float = 0
    overhang: float = 20                     # Длина остатка по краям (har uchida)
    min_glue_length: float = 100
    symbol: str = "A"
    color: str = "#000000"
    marker_lines: int = 1
    min_perp_side: float = 40
    price: float = 0                         # 1 m material
    material_rounding: float = 0             # 0 = yaqiniga
    op_price: float = 0                      # 1 m ish
    work_rounding: float = 0


class GRParams(BaseModel):
    width: float = 4
    depth: float = 10
    offset: float = 16
    price: float = 0


# ───────────────────────── XNC dasturi ─────────────────────────
XncCmd = Literal[
    "Com", "Par", "Var", "Set", "If", "Else", "While", "DoWhile", "Break",
    "Continue", "Sub", "Call", "Ret", "Msg", "Err", "Tool",
    "DrillFront", "DrillLeft", "DrillRight", "DrillTop", "DrillBottom",
    "MillStart", "MillLine", "MillArc", "MillArcCenter", "MillArc3P",
    "MillFillet", "MillRect", "MillEllipse", "Groove", "Origin",
]


class XncCommand(BaseModel):
    cmd: XncCmd
    params: dict[str, str | float] = {}      # X, Y, DP, D, T, R, ...
    comment: str = ""
    children: list["XncCommand"] = []


class XNCParams(BaseModel):
    by_part_size: bool = True
    length: float = 0; width: float = 0; thickness: float = 16
    qty: int = 1
    face_side: bool = True
    rotation: Literal[0, 90, 180, 270] = 0
    mirror_x: bool = False; mirror_y: bool = False
    origin: Literal["LT", "RT", "LB", "RB"] = "LT"
    program: list[XncCommand] = []
    drill_price: float = 0; mill_price_m: float = 0; saw_price_m: float = 0
    extra_cost: float = 0


# ───────────────────────── Operatsiya ─────────────────────────
class Operation(BaseModel):
    id: str = Field(default_factory=_id)
    type: OpType
    code: str = ""
    name: str = ""
    material_id: Optional[str] = None    # MES katalogidagi tovar
    print: bool = True                   # П-ть
    new_page: bool = True                # Н.Стр
    description: str = ""
    cs_material: Optional[CSMaterialParams] = None
    cs_cut: Optional[CSCutParams] = None
    parts: list[Part] = []               # CS/CL uchun
    sheets: list[StockSheet] = []
    result: Optional["CuttingResult"] = None
    el: Optional[ELParams] = None
    gr: Optional[GRParams] = None
    xnc: Optional[XNCParams] = None
    xnc_part_id: Optional[str] = None
    cost_material: float = 0
    cost_operation: float = 0

    @property
    def cost(self) -> float:
        return self.cost_material + self.cost_operation


class Product(BaseModel):
    id: str = Field(default_factory=_id)
    code: str = ""
    name: str
    qty: int = 1
    cost_material: float = 0
    cost_operation: float = 0


class Project(BaseModel):
    id: str = Field(default_factory=_id)
    number: int = 0                      # Заказ ID
    name: str = "Nomsiz"
    folder_id: Optional[str] = None
    owner: str = ""
    currency: str = "UZS"
    order_date: date = Field(default_factory=date.today)
    ready_date: date = Field(default_factory=date.today)
    note: str = ""
    status: OrderStatus = OrderStatus.NOT_ORDERED
    size_mode: SizeMode = SizeMode.DETAIL
    operations: list[Operation] = []
    products: list[Product] = []
    mes_order_ref: Optional[str] = None  # MES tizimidagi buyurtma


# ───────────────────────── Kroy natijasi ─────────────────────────
class Placement(BaseModel):
    part_id: str
    part_uid: int
    x: float; y: float                   # list chap-yuqori burchagidan (mm)
    length: float; width: float          # joylashgan holatdagi o'lcham
    rotated: bool = False


class Offcut(BaseModel):
    x: float; y: float; length: float; width: float   # foydali (torsovkadan keyingi) o'lcham
    kind: Literal["remnant", "waste"]
    number: int = 0                      # qoldiq raqami (Д1, Д2...)
    business: bool = False               # деловой остаток: maydoni ≥ «Площадь делового остатка»
    raw_length: float = 0                # xom o'lcham (list chetigacha) — omborga shu yoziladi
    raw_width: float = 0


class CutCommand(BaseModel):
    """R — listni burish, T — torsovka, C — kesish, P — detal kesish, W — chiqindi."""
    code: Literal["R", "T", "C", "P", "W"]
    level: int = 1
    size: float
    count: int = 1
    ref: str = ""                        # detal yoki qoldiq raqami


class CutMap(BaseModel):
    index: int
    sheet_id: str
    sheet_length: float; sheet_width: float
    is_remnant: bool = False             # ombordagi qoldiqdan kesilgan
    copies: int = 1                      # C: shu kartadan nechta list
    placements: list[Placement] = []
    offcuts: list[Offcut] = []
    commands: list[CutCommand] = []
    parts_count: int = 0                 # Ср
    cut_length_m: float = 0              # LT
    cuts_count: int = 0                  # CT
    fill_percent: float = 0              # F
    parts_area_m2: float = 0             # AP
    sheet_area_m2: float = 0             # AM
    remnant_area_m2: float = 0           # AW — деловой qoldiqlar maydoni (sarfdan ayiriladi)
    comment: str = ""
    strips: list[dict] = []              # kesish daraxti (chizish va qo'lda tahrir uchun)


class CuttingResult(BaseModel):
    maps: list[CutMap] = []
    total_sheets: int = 0
    total_parts: int = 0
    unplaced: list[str] = []             # part id lari
    total_cut_length_m: float = 0
    total_cuts: int = 0
    total_fill_percent: float = 0
    parts_area_m2: float = 0
    material_area_m2: float = 0
    remnant_area_m2: float = 0           # деловой qoldiqlar (sarfga kirmaydi)
    remnants: list[Offcut] = []
    variant: str = ""                    # tanlangan variant (optimal / uzunlik / eni)
    manual: bool = False                 # qo'lda tahrirlangan


Operation.model_rebuild()
XncCommand.model_rebuild()
