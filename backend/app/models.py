"""MebeliX Kroy — ma'lumotlar modellari (Pydantic v2).

Terminlar (UZ / RU):
  Loyiha / Проект, Operatsiya / Операция, Mahsulot (izdeliya) / Изделие,
  Detal / Деталь, List / Лист, Qoldiq / Остаток, Kroy kartasi / Карта кроя,
  Kromka / Кромка, Pazovanie / Пазование, Torsovka / Торцовка, Propil / Пропил.
Barcha o'lchamlar — mm, maydon — m², uzunlik hisobotda — m.
"""
from __future__ import annotations

import math
import re
from datetime import date
from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .i18n import _


def _id() -> str:
    return uuid4().hex[:12]


class Base(BaseModel):
    """Umumiy asos: cheksiz / NaN sonlar kirishda qabul qilinmaydi (422). Saqlashda (JSON) ular konstanta bo'lib
    chiqadi va store.save ularni 0 ga almashtiradi — loyiha hech qachon «ochilmaydigan» holatga tushmaydi."""
    model_config = ConfigDict(allow_inf_nan=False, ser_json_inf_nan="constants")


# ───────────────────────── Qiymat chegaralari (server tomonida tekshiruv) ─────────────────────────
MAX_QTY = 100000          # detal / mahsulot soni (kroy 60 s dan oshmasligi uchun)
MAX_DIM = 100000.0        # eng katta o'lcham, mm (100 m)
LEGACY_CTX = {"legacy": True}


def _legacy(info) -> bool:
    """Eski saqlangan JSON (bazadan yuklash, .mxk.json import) — chegaradan chiqqan qiymat rad etilmaydi, qisqartiriladi.
    API orqali yangi kiritilgan qiymat (PUT/PATCH/POST, Excel, MES) esa qat'iy tekshiriladi (422/400)."""
    ctx = getattr(info, "context", None)
    return isinstance(ctx, dict) and bool(ctx.get("legacy"))


def _fix_range(data: dict, key: str, lo: float, hi: float, *, integer: bool = False, below=None) -> None:
    """Eski ma'lumotda son chegaradan chiqqan bo'lsa — [lo, hi] ga qisqartiradi (`below` berilsa — qat'iy `> lo`
    chegara: lo dan oshmagan qiymat shunga almashtiriladi). Son bo'lmagan qiymatga tegilmaydi (oddiy tekshiruv
    xabar beradi)."""
    v = data.get(key)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or v in (float("inf"), float("-inf")):
        return
    if below is not None and v <= lo:
        v = below
    v = min(max(v, lo), hi)
    data[key] = int(round(v)) if integer else float(v)


# ───────────────────────── Foydalanuvchi parametrlari (jadval «Настройки» → «Настроенный Параметры» ustunlari) ─────────────────────────
USER_PARAMS_MAX = 100          # bitta qatordagi parametrlar soni
USER_PARAM_NAME_MAX = 40       # nom uzunligi (ustun kaliti bilan bir xil chegara)
USER_PARAM_VALUE_MAX = 1000    # qiymat uzunligi (ifoda kontekstidagi matn chegarasi bilan bir xil)
# nom — ifoda tilidagi o'zgaruvchi (services/expr.py `_ID_RE`): «part.name1», «material.rang»
USER_PARAM_NAME_RE = re.compile(r"[^\W\d]\w*(?:\.[^\W\d]\w*)*\Z", re.UNICODE)


def _user_params(v, info) -> dict[str, str]:
    """Qatordagi foydalanuvchi parametrlari: qiymatlar MATN sifatida saqlanadi (son / mantiqiy qiymat matnga aylantiriladi,
    null — o'chiriladi). Yangi kiritishda noto'g'ri nom / juda uzun qiymat — xato; eski JSON da — tashlab yuboriladi / qisqartiriladi."""
    if v is None:
        return {}
    if not isinstance(v, dict):
        if _legacy(info):
            return {}
        raise ValueError(_("val_up_obj"))
    legacy = _legacy(info)
    out: dict[str, str] = {}
    for k, val in v.items():
        if val is None:
            continue
        name = str(k)
        if len(name) > USER_PARAM_NAME_MAX or not USER_PARAM_NAME_RE.match(name):
            if legacy:
                continue
            raise ValueError(_("val_up_name", name=name[:USER_PARAM_NAME_MAX]))
        if isinstance(val, bool):
            s = "true" if val else "false"
        elif isinstance(val, (int, float)):
            if isinstance(val, float) and not math.isfinite(val):
                if legacy:
                    continue
                raise ValueError(_("val_up_nan", name=name))
            s = str(int(val)) if isinstance(val, float) and val.is_integer() and abs(val) < 1e15 else str(val)
        elif isinstance(val, str):
            s = val
        else:
            if legacy:
                continue
            raise ValueError(_("val_up_type", name=name))
        if len(s) > USER_PARAM_VALUE_MAX:
            if not legacy:
                raise ValueError(_("val_up_len", name=name, n=USER_PARAM_VALUE_MAX))
            s = s[:USER_PARAM_VALUE_MAX]
        out[name] = s
    if len(out) > USER_PARAMS_MAX:
        if not legacy:
            raise ValueError(_("val_up_count", n=USER_PARAMS_MAX))
        out = dict(list(out.items())[:USER_PARAMS_MAX])
    return out


def user_params_of(attrs, prefix: str, reserved=()) -> dict[str, str]:
    """XML atributlaridan foydalanuvchi parametrlari («part.<nom>» / «material.<nom>» → jadval «Настроенный Параметры» ustunlari).
    Nomi ifoda o'zgaruvchisi bo'la olmaydigan yoki juda uzun atributlar o'tkazib yuboriladi; qiymat ≤ 1000 belgi."""
    out: dict[str, str] = {}
    for k, v in attrs.items():
        if (k.startswith(prefix) and k not in reserved and v != "" and len(k) <= USER_PARAM_NAME_MAX
                and USER_PARAM_NAME_RE.match(k) and len(out) < USER_PARAMS_MAX):
            out[k] = v[:USER_PARAM_VALUE_MAX]
    return out

# ───────────────────────── Enumlar ─────────────────────────
class OpType(str, Enum):
    O = "O"      # Komplektatsiya va boshqa amallar
    CS = "CS"    # Listli kroy
    CN = "CN"    # Nesting kroy (W16: services/cn_*.py)
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
class EdgeRef(Base):
    """Detal tomonidagi kromka: EL operatsiyasi id si (None = kromka yo'q)."""
    op_id: Optional[str] = None


class GrooveSide(Base):
    op_id: Optional[str] = None
    back_side: bool = False     # Tomoni (lits/orqa)


class Part(Base):
    id: str = Field(default_factory=_id)
    uid: int = 0                        # ID (loyiha ichidagi raqam)
    product_id: Optional[str] = None    # Изделие
    name: str = ""
    description: str = ""
    code: str = ""
    # 0 — to'ldirilmagan (bo'sh) qator: kroyga kirmaydi (UI «qator qo'shish» 0×0 yuboradi); manfiy — rad etiladi
    length: float = Field(ge=0, le=MAX_DIM)   # kiritilgan uzunlik (size_mode ga qarab)
    width: float = Field(ge=0, le=MAX_DIM)
    qty: int = Field(1, ge=0, le=MAX_QTY)
    minus_qty: int = Field(0, ge=0, le=MAX_QTY)   # МК — omborda tayyor (kroyga kirmaydi): kroyga = ОК − МК
    grain: bool = False                  # Ткт — teksturani hisobga ol, aylantirma
    from_remnant: bool = False           # «Из остатка» — kroyda avval ro'yxatdagi qoldiq listlarga (soni cheklangan) joylanadi
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
    # (CL) `.project` importidagi XOM uzunlik (W11): manfiy qiymat («-350») Bazis'dan kelgan, hisoblanmagan detalni bildiradi —
    # `length` 0 qo'yiladi (kroyga kirmaydi), xom qiymat shu yerda saqlanadi (eksport/ko'rsatma uchun). length > 0 bo'lsa e'tiborga olinmaydi.
    src_length: Optional[float] = None
    # Jadval «Настройки» → «Настроенный Параметры» ustunlari qiymatlari (nom → matn; masalan «part.name1»). Kroyga ta'sirsiz.
    user_params: dict[str, str] = Field(default_factory=dict)

    @field_validator("user_params", mode="before")
    @classmethod
    def _user_params(cls, v, info):
        return _user_params(v, info)

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "length", 0, MAX_DIM)
            _fix_range(data, "width", 0, MAX_DIM)
            _fix_range(data, "qty", 0, MAX_QTY, integer=True)
            _fix_range(data, "minus_qty", 0, MAX_QTY, integer=True)
        return data


# ───────────────────────── Listlar / qoldiqlar ─────────────────────────
class StockSheet(Base):
    id: str = Field(default_factory=_id)
    length: float = Field(gt=0, le=20000)
    width: float = Field(gt=0, le=20000)
    qty: int = Field(10000, ge=0, le=10000)      # 10000 = cheklanmagan
    is_remnant: bool = False             # ombordagi qoldiq
    trim_length: Optional[float] = Field(None, ge=0, le=500)   # ТД (bo'sh bo'lsa umumiy parametr)
    trim_width: Optional[float] = Field(None, ge=0, le=500)    # ТШ
    end_offset_bottom: Optional[float] = Field(None, ge=0, le=500)   # minimal otstup pastda (bo'sh — operatsiyadagi)
    end_offset_right: Optional[float] = Field(None, ge=0, le=500)    # minimal otstup o'ngda
    description: str = ""
    used_qty: int = 0
    source_remnant_id: Optional[int] = None   # ombordagi qoldiq (remnants jadvali) — kroydan keyin hisobdan chiqariladi
    # «МЗап» — минимальный процент заполнения: shu listdan kesilgan karta to'ldirishi (F) bundan past bo'lsa, list ishlatilmaydi
    # (qoldiq ortiqcha kesilib, mayda bo'lakka aylanmasin); bo'sh — cheklov yo'q
    min_fill_percent: Optional[float] = Field(None, ge=0, le=100)
    # import qilingan `.project` dagi list qatori id si (`<part id>`) — stanok fayllarida list raqami shundan (onlayn tizimdagidek)
    uid: Optional[int] = Field(None, ge=0, le=2_000_000_000)

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "length", 0.0, 20000, below=1.0)       # o'lcham musbat bo'lishi shart
            _fix_range(data, "width", 0.0, 20000, below=1.0)
            _fix_range(data, "qty", 0, 10000, integer=True)
            for k in ("trim_length", "trim_width", "end_offset_bottom", "end_offset_right"):
                _fix_range(data, k, 0, 500)
            _fix_range(data, "min_fill_percent", 0, 100)
        return data


# ───────────────────────── Parametrlar ─────────────────────────
class CSMaterialParams(Base):
    # 0 — «zamena material» kabi to'ldirilmagan material (korxona loyihalarida 27 ta; qalinligi 0 .. 350 mm uchraydi)
    thickness: float = Field(16, ge=0, le=1000)
    price: float = Field(0, ge=0, le=1e9)    # «по листам» ✓ — 1 list narxi; ☐ — 1 m² narxi
    price_per_m2: bool = False               # eskirgan (v1): yuklashda narx ma'nosiga aylantiriladi
    est_fill_percent: float = Field(90, ge=0, le=100)    # Расчетный процент заполнения
    cost_by_sheets: bool = True              # Расчет стоимости по листам
    sheet_rounding: SheetRounding = SheetRounding.WHOLE
    op_cost_base: OpCostBase = OpCostBase.CUT_LENGTH
    op_price: float = Field(0, ge=0, le=1e9)             # 1 m / 1 m² narxi
    remnant_min_side1: float = Field(1000, ge=0, le=20000)
    remnant_min_side2: float = Field(500, ge=0, le=20000)
    remnant_min_area: float = Field(0.5, ge=0, le=1000)  # m²
    remnant_size_incl_trim: bool = True
    min_part_size: float = Field(30, ge=0, le=10000)

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            for k, lo, hi in (("thickness", 0, 1000), ("price", 0, 1e9), ("est_fill_percent", 0, 100),
                              ("op_price", 0, 1e9), ("remnant_min_side1", 0, 20000), ("remnant_min_side2", 0, 20000),
                              ("remnant_min_area", 0, 1000), ("min_part_size", 0, 10000)):
                _fix_range(data, k, lo, hi)
        return data


class CSCutParams(Base):
    kerf: float = Field(3, ge=0, le=50)                  # Толщина пилы
    kerf_group: Optional[float] = Field(None, ge=0, le=50)   # guruh detallar uchun
    trim_length: float = Field(2, ge=0, le=500)          # Торцовка по длине
    trim_width: float = Field(2, ge=0, le=500)           # Торцовка по ширине
    trim_includes_kerf: bool = False
    end_offset_bottom: Optional[float] = Field(None, ge=0, le=500)   # «Минимальный отступ в конце» — pastda (None = торцовка по длине)
    end_offset_right: Optional[float] = Field(None, ge=0, le=500)    # o'ngda (None = торцовка по ширине)
    first_cut: FirstCutDir = FirstCutDir.ANY
    use_grain: bool = True                   # Учет текстуры
    complex_strips: bool = True              # Использовать сложные полосы (3-bosqich)
    max_rotations: int = Field(6, ge=1, le=6)            # 1 — faqat birinchi kesim (polosalar); onlayn GibLabda ro'yxat 2…6
    pack_height: float = Field(40, ge=0, le=1000)        # Высота пакета (mm)
    multiplicity: int = 2                    # eskirgan: Кратность endi avtomatik = ⌊paket / qalinlik⌋
    fill_packet: float = Field(90, ge=0, le=100)         # Процент заполнения для кратности (%)
    quality: Literal["fast", "normal", "max"] = "normal"   # kroy sifati / vaqt (Tez / Standart / Maksimal)
    max_part_types_per_map: int = Field(0, ge=0, le=10000)   # 0 = cheklanmagan
    prefer_big_pack: bool = True
    # «Порядок листов» (foydalanuvchi qarori, 2026-10-15): list (standart) — «Листы и остатки» ro'yxati tartibi qat'iy
    # (ombor qoldiqlari, so'ng soni cheklangan listlar, oxirida cheksiz; sig'gan detal bo'lsa mayda qoldiq ham avval kesiladi —
    # xodimlar odati); economy — bir nechta tartib sinaladi va eng kam material maydoni tanlanadi (korpus, 44 ko'p-listli kroy:
    # list 603.9 m², economy 574.0 m², avvalgi tizim 581.9 m²).
    stock_order: Literal["list", "economy"] = "list"
    strip_sort: StripSort = StripSort.DESC
    in_strip_sort: StripSort = StripSort.NONE
    min_strip_width: float = Field(0, ge=0, le=20000)
    max_strip_width: float = Field(0, ge=0, le=20000)
    max_strip_length: float = Field(10000, ge=0, le=100000)
    min_trim_cut: float = Field(5, ge=0, le=500)         # Минимальная обрезка
    merge_parts: bool = False
    save_drawings: bool = False                          # Сохранение чертежа карт кроя (GibLab standarti — o'chiq)
    machining_allowance: float = Field(0, ge=0, le=500)  # Припуск на обработку заготовки

    @model_validator(mode="before")
    @classmethod
    def _v1_offsets(cls, data, info):
        """v1: trim_both_sides / min_end_offset → end_offset_bottom / end_offset_right. Eski saqlangan JSON dagi
        chegaradan chiqqan qiymatlar (masalan, arra −3, burilishlar 99) — chegaraga qisqartiriladi."""
        if isinstance(data, dict) and "end_offset_bottom" not in data and "end_offset_right" not in data:
            if data.get("trim_both_sides") is False:
                data = {**data, "end_offset_bottom": 0.0, "end_offset_right": 0.0}
            else:
                try:
                    mo = float(data.get("min_end_offset") or 0)
                except (TypeError, ValueError):
                    mo = 0.0
                if mo > 0:
                    data = {**data, "end_offset_bottom": mo, "end_offset_right": mo}
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            for k, lo, hi in (("kerf", 0, 50), ("kerf_group", 0, 50), ("trim_length", 0, 500), ("trim_width", 0, 500),
                              ("end_offset_bottom", 0, 500), ("end_offset_right", 0, 500), ("pack_height", 0, 1000),
                              ("fill_packet", 0, 100), ("min_strip_width", 0, 20000), ("max_strip_width", 0, 20000),
                              ("max_strip_length", 0, 100000), ("min_trim_cut", 0, 500),
                              ("machining_allowance", 0, 500)):
                _fix_range(data, k, lo, hi)
            _fix_range(data, "max_rotations", 1, 6, integer=True)
            _fix_range(data, "max_part_types_per_map", 0, 10000, integer=True)
        return data


def step_to_round_code(step) -> int:
    """v1 yaxlitlash qadami → kod: 0/bo'sh → [0.00] yaqiniga (20); 0.01 → ⌈0.00⌉ (21); 0.1 → ⌈0.0⌉ (11);
    0.5 va 1 → ⌈0⌉ (1)."""
    try:
        v = float(step or 0)
    except (TypeError, ValueError):
        return 20
    if v <= 0:
        return 20
    if v <= 0.011:
        return 21
    if v <= 0.11:
        return 11
    return 1


class ELParams(Base):
    count_material: bool = True
    width: float = Field(19, ge=0, le=1000)
    thickness: float = Field(0, ge=0, le=1000)          # kromka qalinligi → detal o'lchamidan ayriladi
    jointing_width: float = Field(0, ge=0, le=1000)     # Ширина прифуговки
    waste_percent: float = Field(0, ge=0, le=100)
    overhang: float = Field(20, ge=0, le=10000)         # Длина остатка по краям (har uchida)
    min_glue_length: float = Field(100, ge=0, le=100000)
    symbol: str = Field("A", max_length=3)
    color: str = "#000000"
    marker_lines: int = Field(1, ge=0, le=3)            # «Линии маркировки»: 0 — chiziqsiz, 1..3
    min_perp_side: float = Field(40, ge=0, le=100000)
    price: float = Field(0, ge=0)                        # 1 m material
    material_round: int = 20                 # «Округление длины материала»: kod = o'nlik×10 + rejim
    op_price: float = Field(0, ge=0)                     # 1 m ish
    work_round: int = 20                     # «Округление длины кромкования» (0 yaqiniga, 1 katta, 2 kichik)

    @model_validator(mode="before")
    @classmethod
    def _v1_rounding(cls, data, info):
        """v1 dagi yaxlitlash qadami (m, 0 — yo'q) → yaxlitlash kodi. Eski saqlangan JSON dagi chegaradan chiqqan
        qiymatlar (masalan, chiqindi −200 %, belgi chiziqlari 9) — chegaraga qisqartiriladi."""
        if isinstance(data, dict):
            data = dict(data)
            for old_k, new_k in (("material_rounding", "material_round"), ("work_rounding", "work_round")):
                if old_k in data and new_k not in data:
                    data[new_k] = step_to_round_code(data.get(old_k))
            if _legacy(info):
                _fix_range(data, "waste_percent", 0, 100)
                _fix_range(data, "marker_lines", 0, 3, integer=True)
                for k, hi in (("width", 1000), ("thickness", 1000), ("jointing_width", 1000), ("overhang", 10000),
                              ("min_glue_length", 100000), ("min_perp_side", 100000), ("price", float("inf")),
                              ("op_price", float("inf"))):
                    _fix_range(data, k, 0, hi)
                if isinstance(data.get("symbol"), str):
                    data["symbol"] = data["symbol"][:3]
        return data


# GR standart qiymatlari — BITTA manba. `.project` formatidagi atributlarning «по умолчанию» qiymatlari
# (grWidth 4, grDepth 8, grOffset 10, grOffsetIncl true, grSawthick 4 mm). Avval kodda 4/10/16 turgan edi (manbasi noma'lum) —
# format bilan bir xillashtirildi; yangi operatsiya, importer (atribut yo'q bo'lsa) va panel shu konstantadan foydalanadi.
GR_DEFAULTS: dict = dict(width=4.0, depth=8.0, offset=10.0, offset_inclusive=True, saw_thickness=4.0)


class GRParams(Base):
    """GR — Пазование (B7/K4): paz eni, chuqurligi, chetdan masofa, arra qalinligi, 1 m paz narxi.
    usage / cut_length / passes — hisoblangan qiymatlar (calc.groove_usage; har saqlashda yangilanadi, faqat o'qish)."""
    width: float = Field(GR_DEFAULTS["width"], gt=0, le=1000)
    depth: float = Field(GR_DEFAULTS["depth"], ge=0, le=1000)
    offset: float = Field(GR_DEFAULTS["offset"], ge=0, le=10000)
    offset_inclusive: bool = GR_DEFAULTS["offset_inclusive"]            # «Отступ включительно»
    saw_thickness: float = Field(GR_DEFAULTS["saw_thickness"], gt=0, le=100)    # «Толщина пилы»: o'tishlar = ⌈en / arra⌉
    price: float = Field(0, ge=0)            # Цена метра паза
    usage: float = 0                         # Длина пазования, m (Σ pazli tomonlar × (ОК − МК))
    cut_length: float = 0                    # Длина пропила, m = usage × o'tishlar
    passes: int = 1                          # arra o'tishlari soni

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "width", 0.0, 1000, below=4)
            _fix_range(data, "saw_thickness", 0.0, 100, below=4)
            _fix_range(data, "depth", 0, 1000)
            _fix_range(data, "offset", 0, 10000)
            _fix_range(data, "price", 0, float("inf"))
        return data


# SP standart «Режим размеров» (spSizeMode: -1 — пильный размер, 0 — заготовка). Formatda «по умолчанию» yozilmagan ❓ —
# bitta konstanta: -1 (pilniy o'lcham: zagotovka + pripusk). T_W12_SP_PROGRAMMA.md.
SP_DEFAULT_SIZE_MODE = -1


class SPParams(Base):
    """SP — Обработка поверхности (W12; format: spCalcMat / spWastePRC / spRestSide / spSizeMode / spCost). Detalning lits / orqa
    tomoni `Part.surface_face_op` / `surface_back_op` orqali shu operatsiyaga bog'lanadi (EL kromka kabi).
    `area_m2` / `material_m2` — hisoblangan (calc.surface_usage; har saqlashda yangilanadi, faqat o'qish)."""
    count_material: bool = True                     # spCalcMat «Учитывать материал»
    waste_percent: float = Field(0, ge=0, le=100)   # spWastePRC «Процент отхода материала»
    rest_side: float = Field(0, ge=0, le=10000)     # spRestSide «Длина остатка по краям», mm (har chetda)
    size_mode: int = Field(SP_DEFAULT_SIZE_MODE, ge=-1, le=0)   # spSizeMode: -1 pilniy o'lcham, 0 zagotovka
    op_price: float = Field(0, ge=0, le=1e9)        # spCost «Цена операции за 1 м²»
    price: float = Field(0, ge=0, le=1e9)           # material narxi, 1 m² (katalogdan; formatda — material good `cost`)
    # material o'lchami («Длина / Ширина / Толщина», GibLab kabi; hozircha hisobga ta'sir qilmaydi — savol ochiq)
    length: float = Field(2200, ge=0, le=100000)
    width: float = Field(800, ge=0, le=100000)
    thickness: float = Field(1, ge=0, le=1000)
    area_m2: float = 0                              # ishlov maydoni, m² (Σ tomon maydoni × soni)
    material_m2: float = 0                          # material sarfi, m² (chiqit % va chetdagi qoldiq bilan)

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "waste_percent", 0, 100)
            _fix_range(data, "rest_side", 0, 10000)
            _fix_range(data, "op_price", 0, 1e9)
            _fix_range(data, "price", 0, 1e9)
            if data.get("size_mode") not in (-1, 0):
                data["size_mode"] = SP_DEFAULT_SIZE_MODE
        return data


# ───────────────────────── CL — Погонажный раскрой (W11) ─────────────────────────
class CLCostBase(int, Enum):
    """«Расчет стоимости операции по» (`.project`: cCostType)."""
    CUT_WITH_TRIM = 0      # Длине реза с торцовкой
    CUT_NO_TRIM = 1        # Длине реза без торцовки
    MATERIAL_LEN = 2       # Длине материала (деловой остаток ayirilib)
    PARTS_LEN = 3          # Длине деталей


# CL standart qiymatlari — BITTA manba (importer atribut bo'lmasa shuni oladi; panel va testlar ham). Manba: `.project` formatining
# «по умолчанию» qiymatlari (cTrimW 10, cMinDimRegWaste1 100, cBusinessWaste 1 m, cFillRep 0.9, cCPF → 90 %) va bizning korxona
# loyihalari (propil 3 mm). T_W11_CL.md §3 — qaysi qiymat taxmin ekani.
CL_DEFAULTS: dict = dict(width=100.0, thickness=16.0, kerf=3.0, trim=10.0, pack_height=40.0, fill_packet=90.0,
                         waste_min=100.0, business_min=1000.0, est_fill_percent=90.0, strip_length=6000.0)


class CLParams(Base):
    """CL — (CL) Погонажный раскрой: profil, plintus, bruss kabi polosa (xlom) materialini kerakli uzunlikdagi bo'laklarga kesish.
    Hamma o'lchamlar — mm (faqat `usage_m` — m). Detalning eni yo'q: u polosa eniga (`width`) teng.
    Torsovka / otstup / propil geometriyasi: foydali uzunlik `U = L − (T_boshi + k) − (T_oxiri + k)` (T = 0 bo'lsa o'sha tomonda
    `T + k` qo'shilmaydi). `waste_incl_trim` (Торцовка отходов, `cTrimWaste`): ✓ — otxod toza uzunligi (80), ☐ — otxod oxirgi
    torsovka zonasini ham oladi (110) va oxirgi torsovka kesimi qilinmaydi. `usage_m` / `multiplicity` — hisoblangan, faqat o'qish
    (calc.cl_cost har saqlashda yangilaydi)."""
    # Параметры материала
    width: float = Field(CL_DEFAULTS["width"], gt=0, le=20000)           # Ширина (polosa eni; hamma detal eni shu)
    thickness: float = Field(CL_DEFAULTS["thickness"], ge=0, le=1000)    # Толщина (kratnost / paket hisobi uchun)
    # Параметры раскроя
    kerf: float = Field(CL_DEFAULTS["kerf"], gt=0, le=50)                # Толщина пилы (CL da qat'iy > 0)
    kerf_group: Optional[float] = Field(None, ge=0, le=50)               # Толщина пилы для групповых деталей (swSawthickDiv; None — asosiy)
    trim: float = Field(CL_DEFAULTS["trim"], ge=0, le=500)               # Торцовка (polosa boshidan); 0 — torsovka kesimi yo'q
    end_offset: Optional[float] = Field(None, ge=0, le=500)              # Минимальный отступ в конце (None — torsovka qiymati)
    pack_height: float = Field(CL_DEFAULTS["pack_height"], ge=0, le=1000)    # Высота пакета
    fill_packet: float = Field(CL_DEFAULTS["fill_packet"], ge=0, le=100)     # Процент заполнения для кратности
    quality: Literal["fast", "normal", "max"] = "normal"                 # kroy sifati / vaqt (bizning kengaytma)
    # Отход
    waste_min: float = Field(CL_DEFAULTS["waste_min"], ge=0, le=20000)   # Мин. размер отхода (mm): qisqasi — oddiy chiqindi
    business_min: float = Field(CL_DEFAULTS["business_min"], ge=0, le=20000)     # Длина делового отхода (mm)
    waste_incl_trim: bool = True                                         # Торцовка отходов (✓ — toza uzunlik)
    min_part_len: float = Field(0, ge=0, le=10000)                       # Мин. размер детали (cMinDimDetail); 0 — cheklov yo'q
    # Припуск на обработку заготовки (cAllowanceWorkpiece; CS dagi kabi): pilniy uzunlikka har uchidan qo'shiladi
    machining_allowance: float = Field(0, ge=0, le=500)
    # W-parity (2026-10-04): (CS) dagi shu nomli parametrlar. «Размер остатков с учетом торцовки» — yuqoridagi `waste_incl_trim`
    # (bitta `cTrimWaste` atributi; kirishda `remnant_size_incl_trim` kaliti ham qabul qilinadi).
    max_part_types_per_map: int = Field(0, ge=0, le=10000)               # Макс. кол-во разновидностей деталей на карте (0 — cheklanmagan)
    merge_parts: bool = False                                            # Объединение деталей (cCombiningParts) — saqlanadi, kroyga ta'sirsiz
    group_parts: int = Field(0, ge=0, le=1000000)                        # Группировка деталей по свойствам (cGroupParts) — saqlanadi
    save_drawings: bool = False                                          # Сохранение чертежа карт кроя (cSaveDrawCut; CS bilan bir xil)
    # Стоимость
    price: float = Field(0, ge=0, le=1e9)                                # Цена материала: 1 m (price_by_strip — 1 polosa)
    price_by_strip: bool = False                                         # Расчет стоимости по полосам (cCostByItem)
    strip_rounding: SheetRounding = SheetRounding.WHOLE                  # Округление — Полосы (11 / 32 / 33 / 34)
    est_fill_percent: float = Field(CL_DEFAULTS["est_fill_percent"], ge=0, le=100)   # Расчетный процент заполнения
    op_cost_base: CLCostBase = CLCostBase.CUT_WITH_TRIM
    op_price: float = Field(0, ge=0, le=1e9)                             # Цена операции (1 m kesim / material / detal)
    # hisoblangan (faqat o'qish)
    usage_m: float = 0                                                   # Расход / Количество материала (m)
    multiplicity: int = 1                                                # Кратность = ⌊Высота пакета / Толщина⌋

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and "remnant_size_incl_trim" in data:
            # (CS) nomi bilan kelgan «Размер остатков с учетом торцовки» → CL maydoni `waste_incl_trim` (aniq berilgani ustun)
            data = dict(data)
            v = data.pop("remnant_size_incl_trim")
            if "waste_incl_trim" not in data and isinstance(v, bool):
                data["waste_incl_trim"] = v
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "max_part_types_per_map", 0, 10000, integer=True)
            _fix_range(data, "group_parts", 0, 1000000, integer=True)
            for k in ("merge_parts", "save_drawings"):                   # eski / buzilgan yozuv: mantiqiy bo'lmasa — standart
                if k in data and not isinstance(data[k], bool):
                    data.pop(k)
            _fix_range(data, "width", 0.0, 20000, below=CL_DEFAULTS["width"])
            _fix_range(data, "kerf", 0.0, 50, below=CL_DEFAULTS["kerf"])        # CL da propil > 0
            if "kerf_group" in data and not (isinstance(data["kerf_group"], (int, float)) and 0 <= data["kerf_group"] <= 50):
                data.pop("kerf_group")
            for k, lo, hi in (("thickness", 0, 1000), ("trim", 0, 500), ("end_offset", 0, 500), ("pack_height", 0, 1000),
                              ("fill_packet", 0, 100), ("waste_min", 0, 20000), ("business_min", 0, 20000),
                              ("min_part_len", 0, 10000), ("price", 0, 1e9), ("est_fill_percent", 0, 100),
                              ("machining_allowance", 0, 500),
                              ("op_price", 0, 1e9)):
                _fix_range(data, k, lo, hi)
        return data


# ───────────────────────── CN — Нестинговый раскрой (W16; mantiq — services/cn_*.py) ─────────────────────────
# CN standart qiymatlari — BITTA manba (T_W16_CN.md §3). GibLabning CN operatsiyasi hujjatlashtirilmagan (yordam sahifasi yo'q) —
# hamma qiymat bizning qarorimiz; har biri parametr orqasida.
CN_DEFAULTS: dict = dict(tool_diameter=6.0, margin=5.0, part_gap=0.0, thickness=16.0, est_fill_percent=80.0,
                         remnant_min_side1=300.0, remnant_min_side2=150.0, remnant_min_area=0.1)


class CNParams(Base):
    """CN — (CN) Нестинговый раскрой: kontur detallarni listga zich joylash (raster «pastki-chap» evristikasi — services/cn_nest.py).
    Hamma o'lchamlar — mm. Detal konturi: bog'langan XNC dasturining yopiq freza konturi yoki oddiy to'rtburchak (L × W).
    Detallar orasidagi talab etilgan masofa `spacing = max(tool_diameter, 2·tool_offset) + part_gap` (asbob ikki detal orasidan o'tadi),
    detal konturi list chetidan kamida `margin` uzoqlikda. `usage_m2` / `multiplicity` — hisoblangan, faqat o'qish."""
    # Material va narx
    thickness: float = Field(CN_DEFAULTS["thickness"], ge=0, le=1000)
    price: float = Field(0, ge=0, le=1e9)                        # «по листам» ✓ — 1 list narxi; ☐ — 1 m² narxi
    cost_by_sheets: bool = True
    sheet_rounding: SheetRounding = SheetRounding.WHOLE
    est_fill_percent: float = Field(CN_DEFAULTS["est_fill_percent"], ge=0, le=100)     # Расчетный процент заполнения
    op_cost_base: OpCostBase = OpCostBase.CUT_LENGTH             # kesim uzunligi = konturlar perimetri
    op_price: float = Field(0, ge=0, le=1e9)
    # Asbob va masofalar
    tool_diameter: float = Field(CN_DEFAULTS["tool_diameter"], gt=0, le=100)
    tool_offset: Optional[float] = Field(None, ge=0, le=100)     # asbob markazi konturdan masofasi (None — diametr / 2)
    part_gap: float = Field(CN_DEFAULTS["part_gap"], ge=0, le=500)       # asbob diametridan tashqari qo'shimcha masofa
    margin: float = Field(CN_DEFAULTS["margin"], ge=0, le=500)           # kontur — list chetigacha masofa
    arc_tol: float = Field(0.25, ge=0.02, le=1.0)                # yoylarni siniq chiziqqa yaqinlashtirish xatosi, mm
    # Aylantirish va tekstura
    rot90: bool = True                                           # 0 / 90 / 180 / 270 burilishlar (o'chiq — faqat 0)
    rot_step: float = Field(0, ge=0, le=90)                      # qo'shimcha erkin burchak qadami, gradus (0 — o'chiq)
    use_grain: bool = True                                       # Учет текстуры: Ткт detal faqat 0° / 180°
    use_xnc_contours: bool = True                                # bog'langan XNC dastur konturini ishlatish (o'chiq — to'rtburchak)
    # Qoldiq qoidalari (CS dagi kabi; qoldiq — detalsiz to'rtburchak, shu jumladan detal ichki kesimlarida)
    remnant_min_side1: float = Field(CN_DEFAULTS["remnant_min_side1"], ge=0, le=20000)
    remnant_min_side2: float = Field(CN_DEFAULTS["remnant_min_side2"], ge=0, le=20000)
    remnant_min_area: float = Field(CN_DEFAULTS["remnant_min_area"], ge=0, le=1000)    # m²: деловой qoldiq
    min_part_size: float = Field(0, ge=0, le=10000)              # shundan kichik detal kroyga kirmaydi (0 — cheklov yo'q)
    # Etiketka o'rni (UPD-002)
    label_w: float = Field(40, ge=0, le=1000)
    label_h: float = Field(20, ge=0, le=1000)
    # Optimizatsiya
    quality: Literal["fast", "normal", "max"] = "normal"
    sort_mode: Literal["auto", "list"] = "auto"                  # «Сортировка»: auto — optimizator tartibni o'zi tanlaydi; list — detallar ro'yxati tartibida joylanadi
    time_limit_s: float = Field(0, ge=0, le=600)                 # 0 — darajaga mos standart (fast 3 / normal 10 / max 40 s)
    # hisoblangan (faqat o'qish)
    usage_m2: float = 0                                          # Количество материала (m²)
    multiplicity: int = 1

    @property
    def offset(self) -> float:
        """Asbob markazining detal konturidan masofasi."""
        return self.tool_diameter / 2 if self.tool_offset is None else self.tool_offset

    @property
    def spacing(self) -> float:
        """Ikki detal konturi orasidagi eng kam masofa."""
        return max(self.tool_diameter, 2 * self.offset) + self.part_gap

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "tool_diameter", 0.0, 100, below=CN_DEFAULTS["tool_diameter"])
            for k, lo, hi in (("thickness", 0, 1000), ("price", 0, 1e9), ("est_fill_percent", 0, 100), ("op_price", 0, 1e9),
                              ("tool_offset", 0, 100), ("part_gap", 0, 500), ("margin", 0, 500), ("arc_tol", 0.02, 1.0),
                              ("rot_step", 0, 90), ("remnant_min_side1", 0, 20000), ("remnant_min_side2", 0, 20000),
                              ("remnant_min_area", 0, 1000), ("min_part_size", 0, 10000), ("label_w", 0, 1000),
                              ("label_h", 0, 1000), ("time_limit_s", 0, 600)):
                _fix_range(data, k, lo, hi)
        return data


# ───────────────────────── XNC dasturi ─────────────────────────
XncCmd = Literal[
    "Com", "Par", "Var", "Set", "If", "Else", "While", "DoWhile", "Break",
    "Continue", "Sub", "Call", "Ret", "Msg", "Err", "Tool",
    "DrillFront", "DrillLeft", "DrillRight", "DrillTop", "DrillBottom",
    "MillStart", "MillLine", "MillArc", "MillArcCenter", "MillArc3P",
    "MillFillet", "MillRect", "MillEllipse", "Groove", "Origin",
]


class XncCommand(Base):
    cmd: XncCmd
    params: dict[str, str | float] = {}      # X, Y, DP, D, T, R, ...
    comment: str = ""
    enabled: bool = True                     # «Включить» (GibLab `enable`): o'chirilgan buyruq (va bolalari) bajarilmaydi
    children: list["XncCommand"] = []


class XNCParams(Base):
    """«По размеру детали» ✓ va operatsiya detalga bog'langan (Operation.xnc_part_id) bo'lsa — length/width/thickness
    va qty har saqlashda detaldan yangilanadi (calc.sync_xnc): DX/DY — detal o'lchami, DZ — material qalinligi,
    qty = ОК − МК. part_vars — detaldan hisoblangan ifoda o'zgaruvchilari (J3), faqat o'qish."""
    by_part_size: bool = True
    length: float = 0; width: float = 0; thickness: float = 16
    qty: int = Field(1, ge=0, le=MAX_QTY)
    face_side: bool = True
    rotation: Literal[0, 90, 180, 270] = 0
    mirror_x: bool = False; mirror_y: bool = False
    origin: Literal["LT", "RT", "LB", "RB"] = "LT"
    program: list[XncCommand] = []
    drill_price: float = 0; mill_price_m: float = 0; saw_price_m: float = 0
    extra_cost: float = 0
    part_vars: dict[str, float] = {}         # allowanceT/B/L/R, etj…ert, xncIndex, xncIndexInPart
    # «Параметры» yorlig'ida kiritilgan Par qiymatlari: {Par nomi: son yoki ifoda}. Yo'q bo'lsa — Par.value (standart).
    # Mantiqiy (boolean) Par: 1 / 0. Eski JSON da maydon yo'q — {} (hammasi standart qiymat).
    par_values: dict[str, float | str] = {}

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "qty", 0, MAX_QTY, integer=True)
        return data

    @field_validator("par_values")
    @classmethod
    def _par_values_limits(cls, v):
        if len(v) > 200:
            raise ValueError(_("val_pv_count", n=200))
        for k, val in v.items():
            if len(k) > 100 or (isinstance(val, str) and len(val) > 200):
                raise ValueError(_("val_pv_len", a=100, b=200))
        return v


# ───────────────────────── O — Комплектация и другие действия ─────────────────────────
O_MAX_ROWS = 5000         # materiallar jadvalidagi qatorlar chegarasi


class OMaterial(Base):
    """Komplektatsiya jadvali qatori (Код, Наименование, Ед.И, Кол, Цена). «Стоимость» = qty × price — saqlanmaydi."""
    id: str = Field(default_factory=_id)
    code: str = Field("", max_length=100)         # Код
    name: str = Field("", max_length=300)         # Наименование
    unit: str = Field("шт", max_length=20)        # Ед.И (шт, м, м², компл. …) — erkin matn
    qty: float = Field(1, ge=0, le=1e9)           # Кол (kasr ruxsat) — 1 mahsulot / loyiha uchun
    price: float = Field(0, ge=0, le=1e9)         # Цена (1 birlik)
    user_params: dict[str, str] = Field(default_factory=dict)   # «Настроенный Параметры» ustunlari (masalan «material.name1»)

    @field_validator("user_params", mode="before")
    @classmethod
    def _user_params(cls, v, info):
        return _user_params(v, info)

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "qty", 0, 1e9)
            _fix_range(data, "price", 0, 1e9)
            for k, n in (("code", 100), ("name", 300), ("unit", 20)):
                if isinstance(data.get(k), str):
                    data[k] = data[k][:n]
        return data


class OParams(Base):
    """O operatsiyasi parametrlari (K2 / inventar 03 §3). `multiplier` va `messages` — hisoblangan (faqat o'qish):
    calc.recalc_project har saqlashda yangilaydi (multiplier = egasi mahsulot bo'lsa uning soni, aks holda 1)."""
    owner_product_id: Optional[str] = None        # Владелец: None = butun loyiha; aks holda Product.id
    materials: list[OMaterial] = Field(default_factory=list, max_length=O_MAX_ROWS)
    work_cost: float = Field(0, ge=0, le=1e9)     # Стоимость операции (ish narxi), qo'lda; 1 mahsulot / loyiha uchun
    multiplier: float = 1                         # hisoblangan: egasi mahsulot soni (yoki 1)
    messages: list[str] = Field(default_factory=list, max_length=20)   # hisoblangan xabar kodlari (masalan «owner_lost»)

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "work_cost", 0, 1e9)
            if isinstance(data.get("materials"), list):
                data["materials"] = data["materials"][:O_MAX_ROWS]
            if isinstance(data.get("messages"), list):
                data["messages"] = data["messages"][:20]
        return data


# ───────────────────────── LB — etiketkalar ─────────────────────────
LB_MAX_LABELS = 10_000          # bitta chop (HTML) dagi etiketkalar chegarasi (DoS himoyasi)


LB_PAGE_W, LB_PAGE_H = 210.0, 297.0      # «На формат А4»
LB_MARGIN_MM = 6.0                        # «Поля страницы» yoqilganda standart maydon (fayl formatida faqat bayroq; qiymat — ❓)


class LBParams(Base):
    """LB — Этикетки (inventar 03 §2.4, §4.3): sahifa parametrlari, manba va tanlov bayroqlari, shablon (kutubxonadan yoki
    loyiha ichidagi nusxa), shablon parametrlari qiymatlari. Qaysi maydon ❓ ekani — docs/mebelix/T_LB_ETIKETKA.md.
    `legacy_program` — `.project` importidagi eski shablon matni: o'qilmaydi va chop etilmaydi, faqat ma'lumot yo'qolmasin
    uchun saqlanadi."""
    source: Literal["parts", "products", "user"] = "parts"     # detallar (va qoldiqlar) / mahsulotlar / foydalanuvchi qatorlari
    mode: Literal["sheet", "roll"] = "sheet"                   # «На формат A4» / «На принтер этикеток» (standart — eski xulq: A4 to'r)
    rotate_page: Literal[0, 90] = 0                            # printer yo'nalishi (roll: sahifa va mazmun; sheet: landshaft)
    # Etiketka o'lchami: rulon rejimida — foydalanuvchi kiritadi; A4 rejimida (rows ≥ 1) — sahifa va to'rdan HISOBLANADI
    # (`label_size()`), bu maydonlar faqat saqlanadi (rulonga qaytilganda ishlatiladi). Korxona `.project` fayllarida o'lcham yo'q.
    width_mm: float = Field(58, gt=0, le=500)
    height_mm: float = Field(40, gt=0, le=500)
    # Yangi operatsiya standarti — kuzatilgan tizimdagi kabi (2026-10-16): 1×1, oraliq 0, «Поля страницы» o'chiq, «Нет границы».
    columns: int = Field(1, ge=1, le=20)
    rows: int = Field(1, ge=0, le=50)                          # A4: ≥ 1; 0 — faqat eski saqlangan ma'lumot (avto qatorlar + qo'lda o'lcham)
    gap_mm: float = Field(0, ge=0, le=50)
    margin_mm: Optional[float] = Field(None, ge=0, le=50)      # None = «Поля страницы» o'chiq; yoqilganda standart LB_MARGIN_MM
    border: bool = False
    # «Границы»: none — «Нет границы», perimeter — «Границы по периметру». None — eski ma'lumot / eski mijoz: `border` bayrog'idan
    # olinadi (`border_kind`); berilgan bo'lsa — u ustun va `border` shunga moslanadi.
    border_mode: Optional[Literal["none", "perimeter"]] = None
    cs_op_id: Optional[str] = None                             # faqat shu CS operatsiya (None = hammasi)
    # detallar va qoldiqlar
    print_parts: bool = True
    part_each: bool = False                                    # «Для каждой детали»: har nusxaga alohida etiketka
    part_only_nonzero: bool = False                            # «Только если количество больше нуля»: soni 0 bo'lgan detallar chiqmaydi
    part_selected: list[int] = Field(default_factory=list, max_length=20000)    # detal uid lari (bo'sh = hammasi)
    # «Выбранные детали» katakchasi: True — faqat `part_selected` dagi detallar (ro'yxat bo'sh bo'lsa — hech biri), False — ro'yxat
    # e'tiborga olinmaydi; None — eski ma'lumot / eski mijoz: ro'yxat bo'sh bo'lmasa — tanlov ishlaydi (`selected_uids`).
    part_selected_only: Optional[bool] = None
    label_count: int = Field(1, ge=1, le=20)                   # bir detal nusxasiga etiketkalar soni
    print_wastes: bool = True
    waste_each: bool = False
    waste_business_only: bool = False                          # faqat деловой qoldiqlar
    # mahsulotlar
    product_each: bool = False
    product_only_nonzero: bool = False                         # korxona fayllarida productONZ="false" (standart)
    # shablon
    template_id: Optional[str] = Field(None, max_length=60)    # «builtin:<kalit>» yoki «profile:<id>» (None = o'rnatilgan standart)
    template: Optional[dict] = None                            # loyiha ichidagi nusxa (g'olib)
    params: dict[str, str | float | bool] = Field(default_factory=dict)     # shablon parametrlari (Par) qiymatlari
    fields: list[dict] = Field(default_factory=list, max_length=50)         # source=user: {name,title,type,width,default}
    data: list[dict] = Field(default_factory=list, max_length=10000)        # source=user qatorlari
    legacy_program: str = Field("", max_length=300_000)

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "width_mm", 0.0, 500, below=58)
            _fix_range(data, "height_mm", 0.0, 500, below=40)
            _fix_range(data, "columns", 1, 20, integer=True)
            _fix_range(data, "rows", 0, 50, integer=True)
            _fix_range(data, "gap_mm", 0, 50)
            _fix_range(data, "margin_mm", 0, 50)
            _fix_range(data, "label_count", 1, 20, integer=True)
        return data

    @model_validator(mode="after")
    def _template_ok(self, info):
        """Loyihaga yangi yozilayotgan shablon tuzilmasi tekshiriladi (eski saqlangan JSON — tegilmaydi: chopda xato ko'rsatiladi)."""
        if self.template is not None and not _legacy(info):
            from .services.label_tpl import normalize_template      # kech import: models → services aylanishi yo'q
            self.template = normalize_template(self.template)
        if self.fields and not _legacy(info):                       # W15: source=user maydonlar sxemasi (nom, tur, takror)
            from .services.label_user import normalize_fields
            self.fields = normalize_fields(self.fields, strict=False)       # yaroqsizlari tashlanadi (eski saqlangan ma'lumot PATCH ni buzmasin)
        if self.border_mode is not None:                            # «Границы» ro'yxati ustun: eski `border` bayrog'i shunga moslanadi
            self.border = self.border_mode != "none"
        return self

    @property
    def border_kind(self) -> str:
        """Amaldagi chegara turi: none | perimeter."""
        return self.border_mode or ("perimeter" if self.border else "none")

    @property
    def auto_size(self) -> bool:
        """A4 rejimida etiketka o'lchami sahifa va to'rdan hisoblanadi (kuzatilgan tizim: «Размер» faqat ko'rsatiladi).
        Eski saqlangan ma'lumot (rows=0 — «sig'ganicha») — qo'lda berilgan width_mm × height_mm saqlanadi (avvalgidek chop etilsin)."""
        return self.mode == "sheet" and self.rows >= 1

    def page_size(self) -> tuple[float, float]:
        """A4 sahifa (mm): rotate_page=90 — albom."""
        return (LB_PAGE_H, LB_PAGE_W) if self.rotate_page == 90 else (LB_PAGE_W, LB_PAGE_H)

    def label_size(self) -> tuple[float, float]:
        """Amaldagi etiketka o'lchami (mm): A4 (rows ≥ 1) — (sahifa − 2·maydon − (n−1)·oraliq) / n, 0.01 mm gacha pastga
        yaxlitlanadi (to'r sahifaga aniq sig'sin); rulon va eski A4 (rows=0) — width_mm × height_mm."""
        if not self.auto_size:
            return float(self.width_mm), float(self.height_mm)
        pw, ph = self.page_size()
        m = float(self.margin_mm or 0.0)
        cols, rows, gap = max(1, self.columns), max(1, self.rows), float(self.gap_mm)
        w = (pw - 2 * m - (cols - 1) * gap) / cols
        h = (ph - 2 * m - (rows - 1) * gap) / rows
        return max(1.0, math.floor(w * 100 + 1e-6) / 100), max(1.0, math.floor(h * 100 + 1e-6) / 100)

    def effective(self) -> "LBParams":
        """Chop/ko'rish uchun nusxa: width_mm/height_mm — amaldagi (hisoblangan) o'lcham. Saqlanmaydi."""
        if not self.auto_size:
            return self
        w, h = self.label_size()
        return self.model_copy(update={"width_mm": w, "height_mm": h})

    def selected_uids(self) -> Optional[set[int]]:
        """«Выбранные детали»: None — tanlov yo'q (hamma detallar); to'plam — faqat shu uid lar (bo'sh to'plam — hech biri)."""
        on = bool(self.part_selected) if self.part_selected_only is None else self.part_selected_only
        return set(self.part_selected) if on else None


# ───────────────────────── Operatsiya ─────────────────────────
class Operation(Base):
    id: str = Field(default_factory=_id)
    type: OpType
    code: str = ""
    name: str = ""
    material_id: Optional[str] = None    # MES katalogidagi tovar
    material_uid: Optional[int] = Field(None, ge=0, le=2_000_000_000)   # import qilingan fayldagi material (`<good id>`) raqami
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
    o: Optional[OParams] = None          # (O) Комплектация: материалы, ish narxi, egasi
    lb: Optional[LBParams] = None        # (LB) Этикетки: sahifa, manba, shablon
    sp: Optional[SPParams] = None        # (SP) Обработка поверхности (W12)
    cl: Optional[CLParams] = None        # (CL) Погонажный раскрой (W11): parts / sheets / result shu operatsiyada, `sheets` — polosalar
    cn: Optional[CNParams] = None        # (CN) Нестинговый раскрой (W16): parts / sheets / result shu operatsiyada (CS kabi)
    cost_material: float = 0
    cost_operation: float = 0

    @model_validator(mode="after")
    def _cn_defaults(self):
        """(CN, W16) nesting operatsiyasida parametrlar har doim bor (parametrsiz yaratilgan yozuv — standart qiymatlar)."""
        if self.type == OpType.CN and self.cn is None:
            self.cn = CNParams()
        return self

    @model_validator(mode="after")
    def _v1_price(self):
        """v1: «price_per_m2» bayrog'i → narx ma'nosi «Расчет стоимости по листам» ga bog'liq (✓ — 1 list, ☐ — 1 m²)."""
        m = self.cs_material
        if m is not None and m.price_per_m2:
            if m.cost_by_sheets:
                sh = next((x for x in self.sheets if not x.is_remnant and not x.source_remnant_id), None)
                if sh is not None:
                    m.price = round(m.price * sh.length * sh.width / 1e6, 2)
                else:
                    m.cost_by_sheets = False
            m.price_per_m2 = False
        return self

    @model_validator(mode="after")
    def _cl_defaults(self):
        """(CL, W11) погонажный operatsiyada parametrlar har doim bor (API orqali parametrsiz yaratilgan eski yozuv — standart qiymatlar)."""
        if self.type == OpType.CL and self.cl is None:
            self.cl = CLParams()
        return self

    @property
    def cost(self) -> float:
        return self.cost_material + self.cost_operation


PROG_MAX_NODES = 5000        # mahsulot dasturidagi buyruqlar (ichma-ichlari bilan) chegarasi
PROG_MAX_MESSAGES = 100      # mahsulot dasturi xabarlari (Msg / Err / xatolar) chegarasi


class ProgMessage(Base):
    """Mahsulot dasturi xabari (hisoblangan): daraja info (Msg) | warning (ifoda / dastur xatosi) | error (Err — cheklov buzildi)."""
    level: Literal["info", "warning", "error"] = "info"
    text: str = Field("", max_length=500)
    path: str = Field("", max_length=60)      # buyruq yo'li («2.3», 1 dan boshlab)


class Product(Base):
    id: str = Field(default_factory=_id)
    code: str = ""
    name: str
    qty: int = Field(1, ge=0, le=MAX_QTY)
    cost_material: float = 0
    cost_operation: float = 0
    # «Свойства» oynasi (Общие / Данные заказа / Дополнительные параметры / Описание / Сообщения)
    order_info: str = ""                 # Данные заказа
    ready_date: str = ""                 # Дата готовности (erkin matn)
    phone1: str = ""
    phone2: str = ""
    extra: dict[str, str] = {}           # Дополнительные параметры (kalit = qiymat), masalan product.import = bm.1.86
    description: str = ""
    messages: list[str] = []             # import / hisob xabarlari (faqat o'qish uchun)
    # «Программа» yorlig'i (W12, parametrik mahsulot): faqat boshqaruv buyruqlari (Com Par Var Set If Else While DoWhile Break
    # Continue Sub Call Ret Msg Err — services/product_program.py). Eski JSON da maydonlar yo'q — bo'sh dastur.
    program: list[XncCommand] = []
    par_values: dict[str, float | str] = {}          # «Параметры»: kiritilgan Par qiymatlari {nom: son yoki ifoda}
    legacy_program: str = Field("", max_length=300_000)   # `.project` importidagi tushunilmagan dastur matni (o'qilmaydi, yo'qolmasin)
    prog_vars: dict[str, float] = {}                 # hisoblangan (faqat o'qish): dastur o'zgaruvchilari → `product.<nom>`
    prog_messages: list[ProgMessage] = Field(default_factory=list, max_length=PROG_MAX_MESSAGES)   # hisoblangan: Msg / Err / xatolar

    @model_validator(mode="before")
    @classmethod
    def _legacy_ranges(cls, data, info):
        if isinstance(data, dict) and _legacy(info):
            data = dict(data)
            _fix_range(data, "qty", 0, MAX_QTY, integer=True)
        return data

    @field_validator("par_values")
    @classmethod
    def _par_values_limits(cls, v):
        if len(v) > 200:
            raise ValueError(_("val_pv_count", n=200))
        for k, val in v.items():
            if len(k) > 100 or (isinstance(val, str) and len(val) > 200):
                raise ValueError(_("val_pv_len", a=100, b=200))
        return v

    @field_validator("program")
    @classmethod
    def _program_limits(cls, v):
        n, stack = 0, list(v)
        while stack:
            c = stack.pop()
            n += 1
            if n > PROG_MAX_NODES:
                raise ValueError(_("val_prog_nodes", n=PROG_MAX_NODES))
            stack.extend(c.children)
        return v


class OrderLogEntry(Base):
    """«Заказать» oqimi tarixi (W14): holat o'zgarishi — kim, qachon, qaysi holatdan qaysisiga. `executor` / `comment` —
    faqat ichki matn (MES ga yuborilmaydi). Loyiha JSON ida saqlanadi (undo/redo holat bilan birga yuradi)."""
    at: str = ""                         # UTC, ISO: 2026-10-02T09:12:33Z
    user: str = Field("", max_length=100)
    from_status: OrderStatus = OrderStatus.NOT_ORDERED
    to_status: OrderStatus = OrderStatus.NOT_ORDERED
    executor: str = Field("", max_length=200)
    comment: str = Field("", max_length=1000)
    ready_date: str = ""                 # shu qadamda belgilangan tayyorlik sanasi (ISO) yoki ""
    via: str = "order"                   # order = «Заказать» oynasi / POST .../order; patch = PATCH sarlavha


class Project(Base):
    id: str = Field(default_factory=_id)
    number: int = 0                      # Заказ ID
    name: str = ""
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
    customer: str = ""                   # buyurtmachi
    order_log: list[OrderLogEntry] = []  # «Заказать» oqimi tarixi (W14); eski JSON da yo'q — bo'sh
    # Saqlash versiyasi (`store.save` qulf ostida +1): brauzer eskiroq javobni (tunnel orqali kechikib kelgan oldingi
    # PATCH javobi) keshga yozmaydi — aks holda yangi kiritilgan qiymat ekranda eskisiga «qaytib qolardi» (2026-10-23)
    rev: int = 0

    # Butun loyihani yuklash (bazadan, undo/redo, .mxk.json import) — eski JSON dagi chegaradan chiqqan qiymatlar
    # qisqartiriladi (loyiha «ochilmaydigan» bo'lib qolmasin). API da alohida kelgan Part / Operation / ELParams va h.k.
    # esa qat'iy tekshiriladi (422).
    @classmethod
    def model_validate(cls, obj, **kw):
        kw.setdefault("context", LEGACY_CTX)
        return super().model_validate(obj, **kw)

    @classmethod
    def model_validate_json(cls, json_data, **kw):
        kw.setdefault("context", LEGACY_CTX)
        return super().model_validate_json(json_data, **kw)


# ───────────────────────── Kroy natijasi ─────────────────────────
class Placement(Base):
    part_id: str
    part_uid: int
    x: float; y: float                   # list chap-yuqori burchagidan (mm)
    length: float; width: float          # joylashgan holatdagi o'lcham
    rotated: bool = False
    # (CN, W16) nesting: x, y, length, width — kontur o'rovchi to'rtburchagi (bbox); haqiqiy joylashuv — burchak + kontur.
    # Server ularni detal shakli va (angle, x, y) dan qayta hisoblaydi — mijozdan kelgan outline / holes ishonilmaydi.
    angle: float = 0.0                   # burilish, gradus (ekranda soat mili bo'yicha; Y pastga)
    outline: list[list[float]] = []      # tashqi kontur, list koordinatalarida [[x, y], …] (yopiq, oxirgi nuqta takrorlanmaydi)
    holes: list[list[list[float]]] = []  # ichki konturlar (teshik / kesim)
    label: Optional[list[float]] = None  # etiketka o'rni [cx, cy, w, h, burchak] — detalda ishlov yo'q joy (UPD-002)


class Offcut(Base):
    x: float; y: float; length: float; width: float   # foydali (torsovkadan keyingi) o'lcham
    kind: Literal["remnant", "waste"]
    number: int = 0                      # qoldiq raqami (Д1, Д2...)
    business: bool = False               # деловой остаток: maydoni ≥ «Площадь делового остатка»
    raw_length: float = 0                # xom o'lcham (list chetigacha) — omborga shu yoziladi
    raw_width: float = 0
    in_part: int = 0                     # (CN) qoldiq shu uid li detalning ichki kesimida (0 — detalsiz bo'sh joy)


class CutCommand(Base):
    """R — listni burish, T — torsovka, C — kesish, P — detal kesish, W — chiqindi."""
    code: Literal["R", "T", "C", "P", "W"]
    level: int = 1
    size: float
    count: int = 1
    ref: str = ""                        # detal yoki qoldiq raqami


class CutMap(Base):
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
    done_count: int = 0                  # sexda kesib bo'lingan nusxalar (MES kuzatuvi)
    packs: int = 0                       # paketlar soni (arra sikllari): ⌈C / paketdagi listlar⌉
    strips: list[dict] = []              # kesish daraxti (chizish va qo'lda tahrir uchun)
    # «Торцовка листа» (CSE-009, W13): shu kartaga alohida torsovka. None — list qatori / operatsiya qiymati.
    trim_length: Optional[float] = Field(None, ge=0, le=500)         # ТД
    trim_width: Optional[float] = Field(None, ge=0, le=500)          # ТШ
    end_offset_bottom: Optional[float] = Field(None, ge=0, le=500)   # minimal otstup pastda
    end_offset_right: Optional[float] = Field(None, ge=0, le=500)    # minimal otstup o'ngda
    # tahrirda zichlash burchagi (o'chirishdan keyin detallar shu burchakka suriladi): LT/RT/LB/RB; None — umumiy sozlama
    pack_corner: Optional[Literal["LT", "RT", "LB", "RB"]] = None


class CuttingResult(Base):
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
    material_qty_m2: float = 0           # Количество материала = listlar maydoni − деловой qoldiqlar
    remnants: list[Offcut] = []
    warnings: list[str] = []             # ogohlantirishlar (masalan, juda kichik detallar kroyga kirmadi)
    sheets_per_pack: int = 1             # paketda birga kesiladigan listlar (Кратность, Высота пакета / qalinlik)
    total_packs: int = 0                 # jami paketlar (arra sikllari)
    variant: str = ""                    # tanlangan variant (optimal / uzunlik / eni)
    manual: bool = False                 # qo'lda tahrirlangan
    remnants_saved: bool = False         # деловой qoldiqlar omborga yozilgan
    saved_remnant_ids: list[int] = []    # omborga yozilgan qoldiqlar (bekor qilish uchun)
    saved_remnant_qty: dict[str, int] = {}   # har yozilgan qator uchun qo'shilgan soni (id → soni)
    consumed_remnants: dict[str, int] = {}   # ombordan ishlatilgan qoldiqlar: id → soni
    # «Исп. кол-во» (qoldiq qatori): mijoz olib ketadigan bo'laklar — omborga yozilmaydi. Kalit: «b:UxE» (деловой) /
    # «r:UxE» (oddiy qoldiq), U×E — foydali (torsovkadan keyingi) o'lcham. Standart bo'sh = barchasi yoziladi (eski xulq).
    taken_remnants: dict[str, int] = {}
    elapsed_s: float = 0                 # hisoblash vaqti
    # (CL) pogonaj kroy (W11): kind="linear" — kartalar polosa (1D), `*_m2` maydonlar polosa eni bilan (L × eni) hisoblanadi
    kind: Literal["sheet", "linear", "nest"] = "sheet"       # (CN, W16) "nest" — nesting: placements konturli (angle / outline / holes)
    material_len_m: float = 0            # kroyga kirgan polosalar uzunligi (m)
    business_len_m: float = 0            # деловой qoldiqlar uzunligi (m) — sarfdan ayiriladi (Количество материала = material − business)
    nest: dict = {}                      # (CN) hisoblash ma'lumoti: kirish izi (`input_rev`), urug', sinovlar, katak (mm) va h.k.


Operation.model_rebuild()
XncCommand.model_rebuild()


# ───────────────────────── Chop etish sozlamalari (profil) ─────────────────────────
class PrintCol(Base):
    """Chop jadvali ustuni («Заголовок карт кроя», XNC «Статистика»): kalit, yoqilgan, kenglik (belgida)."""
    key: str = Field(..., min_length=1, max_length=32)
    on: bool = True
    width: int = Field(10, ge=1, le=200)


# «Заголовок карт кроя» ko'rsatkichlari (kalit, standart yoqilgan, kenglik): №, S, C, Cp, LT, F yoqilgan; qolganlari o'chiq.
MAP_HEADER_COLS: list[tuple[str, bool, int]] = [
    ("N", True, 8), ("S", True, 12), ("C", True, 8), ("Cp", True, 8), ("LT", True, 12), ("F", True, 12),
    ("R", False, 12), ("CT", False, 8), ("T", False, 10), ("AP", False, 12), ("AM", False, 12), ("AW", False, 12),
    ("PK", False, 10),                                  # paketlar — bizning qo'shimcha ko'rsatkich
]
# XNC «Статистика» jadvali ustunlari (18 ta): kalit, standart yoqilgan, kenglik
XNC_STAT_COLS: list[tuple[str, bool, int]] = [
    ("n", True, 8), ("side", True, 5), ("code", True, 30), ("name", True, 25), ("length", True, 8), ("width", True, 8),
    ("qty", True, 7), ("drills", True, 8), ("drill_price", False, 10), ("drill_cost", False, 12), ("mill_len", True, 9),
    ("mill_price", False, 11), ("mill_cost", False, 12), ("saw_len", True, 9), ("saw_price", False, 11),
    ("saw_cost", False, 12), ("extra_cost", False, 10), ("op_cost", True, 12),
]


def _cols(spec: list[tuple[str, bool, int]]) -> list["PrintCol"]:
    return [PrintCol(key=k, on=o, width=w) for k, o, w in spec]


class PrintSettings(Base):
    """«Печать отчета» profili: qaysi bo'limlar chop etiladi va qanday. Oynalar — xodimlar o'rgangan tizimdagi
    «Параметр | Значение» jadvallari (§11, 2026-10-15); standart qiymatlar — o'sha tizimning standartlari."""
    header: bool = True                       # loyiha sarlavhasi
    materials_list: bool = False
    materials_group_by_code: bool = False     # «Группировать материалы по коду»: bir xil kodli qatorlar yig'iladi
    warehouse: bool = True                    # Требование на склад
    warehouse_cut_work: bool = True           # talabnomada kesish uzunligi
    warehouse_edge_work: bool = True          # talabnomada «Длина кромки (работа)»
    products_list: bool = False
    products_list_single: bool = False        # «Печать списка изделий, если изделие одно»
    operations_list: bool = False             # «Печать списка операций» (jadval: Тип, Код, Наименование, narxlar)
    operations_list_single: bool = False      # «…, если операция одна»
    operations: bool = True                   # «Печать операций» (har operatsiya bo'limi)
    xnc_stats: bool = False                   # «Печатать статистику по XNC операциям»
    xnc_stats_group: Literal["none", "material", "product"] = "material"   # XNC statistikasi «Группировка»
    xnc_stat_cols: list[PrintCol] = []        # XNC «Статистика» ustunlari (bo'sh — XNC_STAT_COLS standarti)
    # «Изделия» oynasi: mahsulotlar ro'yxati chop etilganda har mahsulot bloki
    prod_header: bool = False                 # Печать заголовка (kod, nom, soni)
    prod_operations: bool = False             # Печать операций (mahsulot detallari bor operatsiyalar)
    prod_materials: bool = False              # Печать материалов (shu operatsiyalarning talabnoma qatorlari)
    prod_parts: bool = True                   # Печать деталей (mahsulot detallari jadvali)
    # (CS) «Общие» — standartlar xodimlar o'rgangan tizimdagidek: zagolovok / talabnoma / statistika / sig'maganlar / qoldiqlar — yo'q
    cs_warehouse: bool = False                # «Печать требования на склад» (shu operatsiya qatorlari)
    cs_stats: bool = False                    # «Печать статистики» (listlar, detallar, F, LT, maydonlar)
    cs_parts: bool = True
    cs_unplaced: bool = False
    cs_sheets: bool = True
    cs_remnants: bool = False
    cs_maps: bool = True
    cs_commands: bool = False                 # kartalar yonida buyruqlar jadvali
    cs_size_mode: Optional[SizeMode] = None   # None — loyiha rejimi
    map_parts_list: bool = True               # karta yonida detallar jadvali (№ Дл Шр Кл Мт)
    map_part_label: Literal["number", "name", "number_name", "none"] = "number_name"
    map_edges: bool = True                    # kromkalar chiziq + belgi bilan
    map_remnant_number: bool = True
    map_qr: bool = True                       # har kartada QR (MES skaneri uchun)
    map_header_fields: list[str] = ["N", "S", "C", "Cp", "LT", "F"]
    map_mirror: bool = False
    # (CS) — v2.2 W2 kengaytmalari (hammasi standart qiymat bilan: eski profillar o'zgarishsiz ochiladi va chop etiladi)
    cs_title: bool = True                     # CS bo'limi sarlavhasi «N. (CS) Листовой раскрой: <material>» (standart — bor:
                                              # usiz detallar jadvali qaysi materialga tegishli ekani ko'rinmaydi)
    cs_group_by_product: bool = False         # detallar jadvali mahsulotlar bo'yicha guruhlanadi
    cs_edge_highlight: bool = False           # «Выделять в колонке кромкования»: kromkali kataklar ajratiladi
    map_orientation: Literal["portrait", "landscape"] = "portrait"   # kartalar sahifasi: Книжная / Альбомная
    map_part_marks: bool = False              # detal ustida ishlov belgilari (= pazlash, * frezerlash, % teshik)
    map_allowance: bool = True                # pripusk punktir chizig'i (pripusk > 0 bo'lgandagina chiziladi)
    map_num_font: float = Field(0, ge=0, le=40)     # detal raqami shrifti, pt (0 — avto)
    map_num_bold: bool = True
    map_dim_font: float = Field(0, ge=0, le=40)     # o'lchamlar shrifti, pt (0 — avto)
    map_dim_bold: bool = True                 # «Стиль размеров → Жирный шрифт» (standart Да, §11)
    map_dim_rotate: bool = True               # «Разворачивать шрифты»: vertikal (en) yozuv burib yoziladi
    map_part_fill: str = Field("#F2A541", pattern=r"^#[0-9a-fA-F]{6}$")     # detal to'ldirish rangi
    map_part_hatch: Literal["none", "diag", "cross", "horizontal", "vertical"] = "none"
    map_waste_fill: str = Field("#CBCED3", pattern=r"^#[0-9a-fA-F]{6}$")    # chiqindi to'ldirish rangi
    map_waste_hatch: Literal["none", "diag", "cross", "horizontal", "vertical"] = "none"
    # (EL) / (XNC)
    el_params: bool = True
    el_parts: bool = True
    el_header_work: bool = False              # detallar sarlavhasida «Длина кромкования (работа)»
    el_header_material: bool = False          # detallar sarlavhasida «Длина материала»
    xnc_drawing: bool = True
    # (GR)
    gr_params: bool = True                    # paz parametrlari va hisob bloki
    gr_parts: bool = True                     # pazli detallar jadvali (Д-на паза)
    # (O) Комплектация
    o_params: bool = True                     # parametrlar bloki (egasi, narxlar, izoh)
    o_materials: bool = True                  # materiallar jadvali (Код, Наименование, Ед.И, Кол, Цена, Стоимость)
    # (SP) Обработка поверхности (W12)
    sp_params: bool = True                    # parametrlar va hisob bloki (maydon, material, narx)
    sp_parts: bool = True                     # sirt ishlovi bor detallar jadvali
    # (CL) Погонажный раскрой (W11; chop dialogidagi 7 belgi + buyruqlar jadvali)
    cl_header: bool = True                    # Печать заголовка (material, parametrlar)
    cl_parts: bool = True                     # Печать деталей
    cl_group_by_product: bool = False         # Группировать детали по изделиям
    cl_unplaced: bool = True                  # Печать невместившихся деталей
    cl_strips: bool = True                    # Печать полос
    cl_remnants: bool = True                  # Печать отходов
    cl_maps: bool = True                      # Печать карт раскроев
    cl_commands: bool = False                 # kartalar yonida buyruqlar jadvali (bizning qo'shimcha)
    # (CN) Нестинговый раскрой (W16)
    cn_params: bool = True                    # parametrlar va hisob bloki
    cn_parts: bool = True                     # detallar jadvali (shakl, maydon)
    cn_unplaced: bool = True                  # sig'magan detallar
    cn_sheets: bool = True                    # ishlatilgan listlar
    cn_remnants: bool = True                  # qoldiqlar (detalsiz joy va ichki kesimlar)
    cn_maps: bool = True                      # nesting kartalari (kontur chizmasi)
    # «Поля страницы» (mm)
    page_margin_left: float = 10
    page_margin_right: float = 10
    page_margin_top: float = 8
    page_margin_bottom: float = 10
    page_mirror_margins: bool = False         # «Зеркальные поля»: chap sahifada chap/o'ng chegaralar almashadi
    page_footer_pos: Literal["bottom", "top", "none"] = "bottom"   # «Позиция колонтитула» (chopda: loyiha, sahifa raqami)
    # (CS) «Детали» (§11)
    cs_edge_symbols: bool = False             # «Печать символов кромкования и вывести легенду»: kromka katagida belgi + legenda
    cs_parts_form: Literal["merged", "sides"] = "merged"   # «Форма печати деталей»: o'lcham bo'yicha birlashtirilgan / har tomon alohida
    # (CS) «Карты кроя» (§11)
    map_mirror_h: Literal["no", "yes", "cuts_v", "cuts_h"] = "no"   # «Зеркало → Горизонтально»: yo'q / ha / birinchi kesimlar tik / yotiq bo'lsa
    map_mirror_v: bool = False                # «Зеркало → Вертикально»
    map_part_expr: str = Field("", max_length=300)   # «Печать значения выражения»: detal ustida ifoda qiymati (services/expr.py)
    map_edge_marker: Literal["lines", "symbols", "both"] = "lines"   # «Печать маркера кромок»
    map_edge_line_style: Literal["solid", "dashed", "dotted"] = "solid"   # «Стиль линий маркера кромок»
    map_machining: bool = False               # «Печать обработки на деталях»: XNC teshiklari va pazlar karta detalida
    map_header_cols: list[PrintCol] = []      # «Заголовок карт кроя» jadvali (bo'sh — map_header_fields dan quriladi)
    # (XNC) «Чертеж» (§11)
    xnc_back_mirror: Literal["horizontal", "vertical", "none"] = "horizontal"   # «Зеркало для обратной стороны»
    xnc_origin_as_op: bool = False            # «Начало координат → Как установлено в операции»
    xnc_origin: Literal["lt", "t", "rt", "l", "c", "r", "lb", "b", "rb"] = "lt"   # chizmadagi koordinata boshi belgisi o'rni
    # (CL) «Общие» (§11)
    cl_warehouse: bool = False                # «Печать требования на склад»
    cl_stats: bool = False                    # «Печать статистики»

    @model_validator(mode="after")
    def _sync_print_cols(self):
        """Ustun jadvallari ↔ eski maydonlar: `map_header_cols` bo'sh bo'lsa `map_header_fields` dan quriladi, aks holda
        `map_header_fields` undan olinadi (hisobot shu ro'yxatni o'qiydi). XNC ustunlari bo'sh — standart. Eski «Зеркально»
        belgisi (`map_mirror`) «Горизонтально: Да» ga ko'chadi; `map_mirror` = (map_mirror_h == "yes") saqlanadi."""
        known = {k: w for k, _, w in MAP_HEADER_COLS}
        given = self.model_fields_set
        on_cols = [c.key for c in self.map_header_cols if c.on and c.key in known]
        on_fields = [k for k in self.map_header_fields if k in known]
        if not self.map_header_cols or ("map_header_fields" in given and on_fields != on_cols):
            # ustunlar yo'q (eski profil) yoki mijoz faqat eski ro'yxatni o'zgartirgan — ustunlar ro'yxatdan quriladi
            w = {c.key: c.width for c in self.map_header_cols}
            self.map_header_cols = [PrintCol(key=k, on=True, width=w.get(k, known[k])) for k in on_fields] + \
                [PrintCol(key=k, on=False, width=w.get(k, wd)) for k, wd in known.items() if k not in on_fields]
        self.map_header_fields = [c.key for c in self.map_header_cols if c.on and c.key in known]
        if not self.xnc_stat_cols:
            self.xnc_stat_cols = _cols(XNC_STAT_COLS)
        if "map_mirror" in given:                   # eski mijoz «Зеркально» belgisini o'zgartirgan
            if self.map_mirror and self.map_mirror_h != "yes":
                self.map_mirror_h = "yes"
            elif not self.map_mirror and self.map_mirror_h == "yes":
                self.map_mirror_h = "no"
        self.map_mirror = self.map_mirror_h == "yes"
        return self


class LabelSettings(Base):
    """Detal etiketkalari (termoprinter): o'lcham mm va maydonlar."""
    width_mm: float = Field(58, gt=0, le=500)
    height_mm: float = Field(40, gt=0, le=500)
    columns: int = Field(3, ge=0, le=20)      # A4 varaqda ustunlar (0 — termoprinter, bittadan)
    qr: bool = True
    show_edges: bool = True
    show_product: bool = True
    show_map: bool = True


class PostprocessorProfile(Base):
    """Foydalanuvchi postprotsessori: stanok formati shablon (Jinja2, xavfsiz sandbox) bilan yoziladi."""
    id: str = Field(default_factory=_id)
    name: str
    extension: str = "txt"
    per_map: bool = False                     # har karta alohida fayl (zip)
    encoding: str = "utf-8"
    newline: Literal["lf", "crlf"] = "crlf"
    template: str = ""
    description: str = ""

