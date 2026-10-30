"""Excel import v2 — loyiha darajasida, ko'p tabli («Детали» + «Изделия»).

«Детали» tabi: ustunlarni moslash, **guruhlash** (izdeliya ustuni bo'yicha → `Product`; material ustuni bo'yicha → har
material uchun CS operatsiyani topish yoki yaratish), o'lcham rejimi («По размеру»: zagotovka / detal / prifugovkadan keyin),
boshlang'ich va oxirgi qator, varaq (nomi yoki raqami), «soni 0 bo'lgan detalni qo'shma», qo'shimcha ustunlar (tekstura,
nomga raqam qo'yish, tavsif, kod).
«Изделия» tabi: kod yoki nom bo'yicha bog'lash, soni, tavsif, telefon 1/2, sana, «bo'sh mahsulotlarni ham qo'sh».
`mode="products_qty"` — mavjud loyihada faqat mahsulotlar sonini yangilash (hech narsa qo'shilmaydi).

Xavfsizlik: fayl faqat xotirada o'qiladi (`importers.Book`: hajm/qator/ustun chegaralari, formula va makros bajarilmaydi);
bitta importda ko'pi bilan `MAX_IMPORT_PARTS` detal va `MAX_NEW_OPS` yangi CS operatsiya (noto'g'ri ustun tanlansa, ming
operatsiya yaratilmasin). Eski `parts/import` (`importers.import_parts_ex`) o'zgarmagan.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

from pydantic import BaseModel, Field, model_validator
from openpyxl.utils import column_index_from_string

from ..i18n import _
from ..models import OpType, Operation, Part, Product, Project, SizeMode, EdgeRef
from . import calc
from . import importers as imp
from .sizes import compute_sizes

MAX_IMPORT_PARTS = 20_000
MAX_NEW_OPS = 100
NAME_NUMBER_FMT = "{num} {name}"       # «Поместить номер в наименование»: qiymat nomning oldiga («3 Полка»); yordam formatni aytmaydi

PART_FIELDS = ("name", "length", "width", "qty", "grain", "edge_top", "edge_bottom", "edge_left", "edge_right",
               "code", "description", "material", "product", "number_in_name",
               # W18 (XLS-009): (SP) Обработка поверхности, (GR) Пазование, (XNC) Обработка 1/2 — services/import_v2_w18.py
               "sp_front", "sp_back", "gr_top", "gr_bottom", "gr_left", "gr_right", "xnc1", "xnc2")
EXTRA_FIELDS = ("sp_front", "sp_back", "gr_top", "gr_bottom", "gr_left", "gr_right", "xnc1", "xnc2")
PRODUCT_FIELDS = ("code", "name", "qty", "description", "phone1", "phone2", "date")


class ImportConfigError(ValueError):
    """Import sozlamasi noto'g'ri (foydalanuvchi xatosi → 400)."""


# ───────────────────────── Sozlama (so'rov) modeli ─────────────────────────
class _Range(BaseModel):
    enabled: bool = True
    sheet: int = Field(0, ge=0, le=1000)                  # varaq tartib raqami (0 dan)
    sheet_name: str = Field("", max_length=100)           # varaq nomi (berilsa — shu ishlatiladi; profil uchun qulay)
    start_row: int = Field(2, ge=1, le=imp.MAX_ROW_NO)
    end_row: int = Field(0, ge=0, le=imp.MAX_ROW_NO)      # 0 — oxirigacha
    map: dict[str, str] = {}                              # maydon → ustun harfi


class PartsTab(_Range):
    size_mode: Literal["project", "blank", "detail", "jointed"] = "project"     # fayldagi o'lchamlar ma'nosi
    skip_zero_qty: bool = False
    target_op: Optional[str] = None                       # material ko'rsatilmagan qatorlar uchun CS operatsiya id
    # W18 (XLS-005): «Ширина» bo'sh qator — погонажный detal → CL operatsiyasiga (standart: o'chiq — qator tashlanadi, avvalgidek)
    linear_no_width: bool = False
    target_cl: Optional[str] = None                       # material ko'rsatilmagan погонаж qatorlari uchun CL operatsiya id


class ProductsTab(_Range):
    enabled: bool = False
    link: Literal["code", "name"] = "name"                # «Связь с деталями»
    skip_zero_qty: bool = False
    add_empty: bool = False                               # «Добавлять пустые изделия»


class SimpleTab(_Range):
    """«Простые операции» (W18, XLS-013): qatorlar (Код, Наименование, Ед.И, Кол, Цена) → (O) Комплектация."""
    enabled: bool = False
    op_name: str = Field("", max_length=300)              # «Операция» ustuni bo'lmasa — yangi O operatsiya nomi
    target_op: Optional[str] = None                       # mavjud O operatsiyaga qo'shish (yangisi yaratilmaydi)


class MaterialsTab(_Range):
    """«Материалы» (W18, XLS-012): kod / nom → katalogdan topib CS / EL / SP / CL yaratish."""
    enabled: bool = False
    create_missing: bool = True                           # katalogda yo'q material — qator ustunlari bilan yaratiladi
    default_kind: Literal["sheet", "edge", "surface", "linear"] = "sheet"      # katalogda yo'q va «Тип» ustuni yo'q bo'lsa


class ExcelImportConfig(BaseModel):
    mode: Literal["full", "products_qty"] = "full"
    parts: PartsTab = PartsTab()
    products: ProductsTab = ProductsTab()
    simple: SimpleTab = SimpleTab()
    materials: MaterialsTab = MaterialsTab()

    @model_validator(mode="before")
    @classmethod
    def _parts_default(cls, v):
        """`parts` berilmagan-u, «Простые операции» / «Материалы» yoqilgan bo'lsa — «Детали» tabi o'chiq (API foydalanuvchisi
        faqat o'sha tabni yuboradi; «Детали» sukut bo'yicha yoqiq bo'lib qolgani eski `{parts: …}` so'rovlari uchun)."""
        if isinstance(v, dict) and "parts" not in v and any(isinstance(v.get(k), dict) and v[k].get("enabled")
                                                           for k in ("simple", "materials")):
            return {**v, "parts": {"enabled": False}}
        return v


@dataclass
class ImportReport:
    imported: int = 0                                          # qo'shilgan detallar
    skipped: list[dict] = field(default_factory=list)          # [{row, reason, tab}]
    warnings: list[str] = field(default_factory=list)
    created_edges: list[Operation] = field(default_factory=list)
    created_ops: list[Operation] = field(default_factory=list)  # avto yaratilgan CS
    touched_ops: list[Operation] = field(default_factory=list)  # detal qo'shilgan operatsiyalar (kroyi eskiradi)
    created_products: int = 0
    updated_products: int = 0
    changed_products: set = field(default_factory=set)         # soni o'zgargan mahsulotlar id
    zero_skipped: int = 0
    size_mode_changed: Optional[str] = None
    # W18: «Простые операции» (O), «Материалы», (SP)/(GR)/(XNC) ustun guruhlari, погонаж
    created_o: list[Operation] = field(default_factory=list)       # «Простые операции» tabidan yaratilgan O operatsiyalar
    simple_rows: int = 0                                           # O operatsiyalarga qo'shilgan material qatorlari
    materials_added: int = 0                                       # «Материалы» tabidan yaratilgan operatsiyalar
    materials_existing: int = 0                                    # allaqachon loyihada bor (qayta yaratilmadi)
    linear_imported: int = 0                                       # CL operatsiyasiga tushgan detallar («Ширина» bo'sh)
    linked: dict = field(default_factory=lambda: dict(sp=0, gr=0, xnc=0, xnc_new=0))   # bog'langan: SP / GR / XNC (yangi XNC op.)

    def summary(self) -> dict:
        return dict(imported=self.imported, skipped=self.skipped, warnings=self.warnings,
                    created_edges=[dict(id=o.id, name=o.name, symbol=o.el.symbol if o.el else "")
                                   for o in self.created_edges],
                    created_ops=[dict(id=o.id, name=o.name, type=o.type.value) for o in self.created_ops],
                    created_products=self.created_products, updated_products=self.updated_products,
                    zero_skipped=self.zero_skipped, size_mode_changed=self.size_mode_changed,
                    created_o=[dict(id=o.id, name=o.name, rows=len(o.o.materials) if o.o else 0) for o in self.created_o],
                    simple_rows=self.simple_rows, materials_added=self.materials_added,
                    materials_existing=self.materials_existing, linear_imported=self.linear_imported,
                    linked=dict(self.linked))


# ───────────────────────── Yordamchilar ─────────────────────────
def _fold(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).casefold()


def _cols(m: dict, allowed: tuple[str, ...]) -> dict[str, int]:
    out: dict[str, int] = {}
    for k, v in (m or {}).items():
        if k not in allowed:
            raise ImportConfigError(_("imp_bad_field", f=str(k)[:30]))
        v = (v or "").strip() if isinstance(v, str) else ""
        if not v:
            continue
        if not re.fullmatch(r"[A-Za-z]{1,3}", v) or column_index_from_string(v.upper()) > imp.MAX_COLS:
            raise ImportConfigError(_("imp_bad_column", v=v[:20]))
        out[k] = column_index_from_string(v.upper()) - 1
    return out


def _get(row: list, i: int | None):
    if i is None or i >= len(row) or row[i] is None or str(row[i]).strip() == "":
        return None
    return row[i]


def _text(row: list, i: int | None, n: int = 300) -> str:
    v = _get(row, i)
    return imp.cell_text(v).strip()[:n] if v is not None else ""


def _sheet_ref(tab: _Range):
    return tab.sheet_name.strip() or tab.sheet


def default_cs(name: str, code: str = "") -> Operation:
    """Yangi CS operatsiya: «Настройки» dagi standart parametrlar va standart list o'lchami (katalog bilan — API qatlamida)."""
    from ..models import CSCutParams, CSMaterialParams, StockSheet
    from . import settings
    from .saw_machines import effective_cs_defaults
    d = effective_cs_defaults()                    # material standarti + stanok parametrlari
    app = settings.get_default("app")
    return Operation(type=OpType.CS, code=code, name=name,
                     cs_material=CSMaterialParams.model_validate(d.get("material", {})),
                     cs_cut=CSCutParams.model_validate(d.get("cut", {})),
                     sheets=[StockSheet(length=app.get("default_sheet_length", 2750),
                                        width=app.get("default_sheet_width", 1830))])


@dataclass
class _FileProduct:
    key: str
    rno: int
    code: str
    name: str
    qty: int
    description: str
    phone1: str
    phone2: str
    date: str
    product: Product | None = None      # mavjud (loyihadan) yoki yangi (hali loyihaga qo'shilmagan)
    existing: bool = False
    used: bool = False


# ───────────────────────── «Изделия» tabi ─────────────────────────
def _read_products(bk: imp.Book, tab: ProductsTab, project: Project, rep: ImportReport,
                   qty_required: bool = False) -> tuple[dict[str, _FileProduct], set[str]]:
    """Mahsulotlar varag'i → {kalit: _FileProduct}; (kalit — kod yoki nom, `link` ga qarab), 0 soni bilan tashlanganlar."""
    cols = _cols(tab.map, PRODUCT_FIELDS)
    if tab.link not in cols:
        raise ImportConfigError(_("imp_need_product_col", f=_("imp_f_" + tab.link)))
    if qty_required and "qty" not in cols:
        raise ImportConfigError(_("imp_need_product_col", f=_("imp_f_qty")))
    out: dict[str, _FileProduct] = {}
    zero_keys: set[str] = set()
    idx_exist: dict[str, Product] = {}
    for pr in project.products:
        k = _fold(pr.code if tab.link == "code" else pr.name)
        if k:
            idx_exist.setdefault(k, pr)
    dups = 0
    for rno, row in bk.rows(_sheet_ref(tab), tab.start_row, tab.end_row):
        if all(_get(row, i) is None for i in cols.values()):
            continue
        code, name = _text(row, cols.get("code"), 100), _text(row, cols.get("name"))
        key_text = code if tab.link == "code" else name
        if not key_text:
            rep.skipped.append(dict(row=rno, tab="products", reason=_("imp_skip_empty", f=_("imp_f_" + tab.link))))
            continue
        qty = 1
        if "qty" in cols:
            raw = _get(row, cols["qty"])
            if raw is None:
                qty = 0                                         # bo'sh «Количество» — 0 (belgi yoqilsa, qo'shilmaydi)
            else:
                qty = imp.parse_qty(raw)
                if qty is None:
                    rep.skipped.append(dict(row=rno, tab="products", reason=_(
                        "imp_skip_qty", f=_("imp_f_qty"), v=imp.cell_text(raw).strip()[:30], n=imp.MAX_QTY)))
                    continue
        key = _fold(key_text)
        if key in out or key in zero_keys:
            dups += 1
            continue
        if qty == 0 and tab.skip_zero_qty:
            rep.zero_skipped += 1
            zero_keys.add(key)
            continue
        fp = _FileProduct(key=key, rno=rno, code=code, name=name or code, qty=qty,
                          description=_text(row, cols.get("description"), 2000), phone1=_text(row, cols.get("phone1"), 50),
                          phone2=_text(row, cols.get("phone2"), 50), date=_text(row, cols.get("date"), 40))
        ex = idx_exist.get(key)
        if ex is not None:
            fp.product, fp.existing = ex, True
        else:
            fp.product = Product(code=fp.code, name=fp.name, qty=fp.qty, description=fp.description,
                                 phone1=fp.phone1, phone2=fp.phone2, ready_date=fp.date)
        out[key] = fp
    if dups:
        rep.warnings.append(_("imp_prod_dups", n=dups))
    return out, zero_keys


def _products_qty(project: Project, bk: imp.Book, cfg: ExcelImportConfig, rep: ImportReport) -> None:
    """«Faqat mahsulot soni» rejimi: fayldagi soni mavjud mahsulotlarga yoziladi; yangi hech narsa qo'shilmaydi."""
    tab = cfg.products
    cols = _cols(tab.map, PRODUCT_FIELDS)
    if tab.link not in cols or "qty" not in cols:
        raise ImportConfigError(_("imp_need_product_col", f=_("imp_f_" + tab.link) + " / " + _("imp_f_qty")))
    by_key: dict[str, list[Product]] = {}               # kalit (kod/nom) → shu kalitli mavjud mahsulotlar
    for pr in project.products:
        k = _fold(pr.code if tab.link == "code" else pr.name)
        if k:
            by_key.setdefault(k, []).append(pr)
    seen: set[str] = set()
    dups = 0
    for rno, row in bk.rows(_sheet_ref(tab), tab.start_row, tab.end_row):
        if all(_get(row, i) is None for i in cols.values()):
            continue
        key_text = _text(row, cols.get(tab.link))
        if not key_text:
            rep.skipped.append(dict(row=rno, tab="products", reason=_("imp_skip_empty", f=_("imp_f_" + tab.link))))
            continue
        raw = _get(row, cols["qty"])
        qty = 0 if raw is None else imp.parse_qty(raw)
        if qty is None:
            rep.skipped.append(dict(row=rno, tab="products", reason=_(
                "imp_skip_qty", f=_("imp_f_qty"), v=imp.cell_text(raw).strip()[:30], n=imp.MAX_QTY)))
            continue
        if qty == 0 and tab.skip_zero_qty:
            rep.zero_skipped += 1
            continue
        key = _fold(key_text)
        found = by_key.get(key)
        if not found:
            rep.skipped.append(dict(row=rno, tab="products", reason=_("imp_prod_not_found", v=key_text[:60])))
            continue
        if key in seen:
            dups += 1                                       # fayldagi takror qator — birinchisi qoladi
            continue
        seen.add(key)
        for pr in found:
            rep.updated_products += 1
            if pr.qty != qty:
                pr.qty = qty
                rep.changed_products.add(pr.id)
    if dups:
        rep.warnings.append(_("imp_prod_dups", n=dups))


# ───────────────────────── «Детали» tabi ─────────────────────────
@dataclass
class _Staged:
    op: Operation
    part: Part
    rno: int
    extras: dict = field(default_factory=dict)        # W18: (SP)/(GR)/(XNC) ustun guruhlari katak matnlari
    linear: bool = False                              # W18: «Ширина» bo'sh → CL operatsiyasi detali


def _import_parts(project: Project, bk: imp.Book, cfg: ExcelImportConfig, rep: ImportReport,
                  make_cs: Callable[[str], Operation], files: dict[str, _FileProduct] | None,
                  zero_keys: set[str], make_op: Callable[..., Operation] | None = None) -> list[_Staged]:
    from . import import_v2_w18 as W18
    tab = cfg.parts
    cols = _cols(tab.map, PART_FIELDS)
    if "length" not in cols or "width" not in cols:
        raise ImportConfigError(_("imp_need_columns"))
    make_op = make_op or W18.default_make_op
    had_parts = any(o.parts for o in project.operations)
    edges = imp.EdgeResolver(project, rep.created_edges, rep.warnings)

    cs_ops = [o for o in project.operations if o.type == OpType.CS]
    cs_idx: dict[str, Operation] = {}
    for o in cs_ops:                                       # avval nom, so'ng kod bo'yicha
        for k in (o.name,):
            if _fold(k):
                cs_idx.setdefault(_fold(k), o)
    for o in cs_ops:
        if _fold(o.code):
            cs_idx.setdefault(_fold(o.code), o)
    default_op: list[Operation] = []
    no_material = [0]

    def default_cs_op() -> Operation:
        if default_op:
            return default_op[0]
        if tab.target_op:
            op = next((o for o in project.operations if o.id == tab.target_op), None)
            if op is None or op.type != OpType.CS:
                raise ImportConfigError(_("imp_target_not_cs", id=tab.target_op[:20]))
        elif cs_ops:
            op = cs_ops[0]
        else:
            op = new_cs(_("imp_default_material"))
        default_op.append(op)
        return op

    def new_cs(name: str) -> Operation:
        if len(rep.created_ops) >= MAX_NEW_OPS:
            raise ImportConfigError(_("imp_too_many_materials", n=MAX_NEW_OPS))
        op = make_cs(name)
        first_edge = rep.created_edges[0] if rep.created_edges else None
        at = next((i for i, o in enumerate(project.operations) if o is first_edge), len(project.operations))
        project.operations.insert(at, op)                  # yangi CS lar — shu importda yaratilgan kromkalardan oldin
        rep.created_ops.append(op)
        if _fold(op.name):
            cs_idx.setdefault(_fold(op.name), op)
        return op

    def resolve_op(mat: str) -> Operation:
        key = _fold(mat)
        if not key:
            no_material[0] += 1
            return default_cs_op()
        op = cs_idx.get(key)
        return op if op is not None else new_cs(mat)

    # W18 (XLS-005): «Ширина» bo'sh qator — погонажный detal → CL operatsiyasi (material ustuni bo'yicha; yo'q bo'lsa — standart CL)
    cl_ops = [o for o in project.operations if o.type == OpType.CL]
    cl_idx: dict[str, Operation] = {}
    for o in cl_ops:
        for k in (o.name, o.code):
            if _fold(k):
                cl_idx.setdefault(_fold(k), o)
    default_cl: list[Operation] = []

    def new_cl(name: str) -> Operation:
        if len(rep.created_ops) >= MAX_NEW_OPS:
            raise ImportConfigError(_("imp_too_many_materials", n=MAX_NEW_OPS))
        item = W18.catalog_svc.find_item("linear", name) if name else None
        op = make_op("CL", name or _("imp_default_linear"), "", item.id if item else None)
        W18._insert_op(project, op, rep)
        rep.warnings.append(_("imp_cl_created", name=op.name))
        for k in (op.name, op.code):
            if _fold(k):
                cl_idx.setdefault(_fold(k), op)
        return op

    def resolve_cl(mat: str) -> Operation:
        key = _fold(mat)
        if key:
            return cl_idx.get(key) or new_cl(mat)
        if default_cl:
            return default_cl[0]
        if tab.target_cl:
            op = next((o for o in project.operations if o.id == tab.target_cl), None)
            if op is None or op.type != OpType.CL:
                raise ImportConfigError(_("imp_target_not_cl", id=tab.target_cl[:20]))
        elif cl_ops:
            op = cl_ops[0]
        else:
            op = new_cl("")
        default_cl.append(op)
        return op

    # mahsulot: {kalit: Product}
    prod_cache: dict[str, Product] = {}
    value_products: list[Product] = []        # fayldagi «Изделия» varag'ida yo'q, qiymatdan yaratilganlar
    exist_by_name = {_fold(p.name): p for p in reversed(project.products) if _fold(p.name)}
    exist_by_code = {_fold(p.code): p for p in reversed(project.products) if _fold(p.code)}

    def resolve_product(text: str) -> Product | None | bool:
        """Product | False (qator tashlanadi: 0 sonli, qo'shilmaydigan mahsulot)."""
        key = _fold(text)
        if key in prod_cache:
            return prod_cache[key]
        pr: Product | None
        if files is not None and key in files:
            fp = files[key]
            fp.used = True
            pr = fp.product
        elif key in zero_keys:
            return False
        else:
            if files is not None:                          # «Изделия» varag'ida bor linkka qarab; yo'q — qiymatdan
                pr = (exist_by_code if cfg.products.link == "code" else exist_by_name).get(key)
            else:
                pr = exist_by_name.get(key) or exist_by_code.get(key)
            if pr is None:
                is_code = files is not None and cfg.products.link == "code"
                pr = Product(code=text[:100] if is_code else "", name=text[:300], qty=1)
                value_products.append(pr)
                rep.created_products += 1
        prod_cache[key] = pr
        return pr

    staged: list[_Staged] = []
    for rno, row in bk.rows(_sheet_ref(tab), tab.start_row, tab.end_row):
        if all(_get(row, i) is None for i in cols.values()):
            continue
        L, el_ = imp.check_dim(_get(row, cols["length"]), _("imp_f_length"))
        raw_w = _get(row, cols["width"])
        linear = bool(tab.linear_no_width and raw_w is None and el_ is None)      # XLS-005: eni bo'sh → погонаж (CL)
        W, ew_ = (0.0, None) if linear else imp.check_dim(raw_w, _("imp_f_width"))
        qty, eq_ = 1, None
        if "qty" in cols:
            raw = _get(row, cols["qty"])
            if raw is None:                                # GibLab: «Количество» bo'sh/son emas — detal qo'shilmaydi
                eq_ = _("imp_skip_empty", f=_("imp_f_qty"))
            else:
                q = imp.parse_qty(raw)
                if q is None:
                    eq_ = _("imp_skip_qty", f=_("imp_f_qty"), v=imp.cell_text(raw).strip()[:30], n=imp.MAX_QTY)
                else:
                    qty = q
        reasons = [r for r in (el_, ew_, eq_) if r]
        if reasons:
            rep.skipped.append(dict(row=rno, tab="parts", reason="; ".join(reasons)))
            continue
        if qty == 0 and tab.skip_zero_qty:
            rep.zero_skipped += 1
            continue
        prod_text = _text(row, cols.get("product"))
        product: Product | None | bool = resolve_product(prod_text) if prod_text else None
        if product is False:                                   # 0 sonli (qo'shilmagan) mahsulotning detali
            rep.zero_skipped += 1
            continue
        if len(staged) >= MAX_IMPORT_PARTS:
            raise ImportConfigError(_("imp_too_many_rows", n=MAX_IMPORT_PARTS))
        mat_text = _text(row, cols.get("material"))
        op = resolve_cl(mat_text) if linear else resolve_op(mat_text)
        name = _text(row, cols.get("name"))
        num = _text(row, cols.get("number_in_name"), 40)
        if num:
            name = NAME_NUMBER_FMT.format(num=num, name=name).strip()[:300]
        pt = Part(name=name, code=_text(row, cols.get("code"), 100), description=_text(row, cols.get("description"), 2000),
                  length=L, width=W, qty=qty, grain=_text(row, cols.get("grain"), 20).lower() in imp.TRUE,
                  product_id=product.id if product else None)
        for side in imp.SIDES:
            v = _get(row, cols.get(f"edge_{side}"))
            if v is not None:
                setattr(pt, f"edge_{side}", EdgeRef(op_id=edges.resolve(imp.cell_text(v), rno)))
        extras = {} if linear else {f: t for f in EXTRA_FIELDS if f in cols and (t := _text(row, cols[f], 100))}
        staged.append(_Staged(op, pt, rno, extras, linear))

    if no_material[0] and "material" in cols:
        rep.warnings.append(_("imp_mat_empty", n=no_material[0], name=default_cs_op().name or default_cs_op().code))
    for op in rep.created_ops:
        if len(rep.warnings) < 50 and op.type == OpType.CS:
            rep.warnings.append(_("imp_cs_created", name=op.name))
    rep.linear_imported = sum(1 for s in staged if s.linear)

    # O'lcham rejimi: fayldagi ma'noni loyiha rejimiga o'tkazish
    if tab.size_mode != "project" and staged:
        file_mode = SizeMode(tab.size_mode)
        if file_mode != project.size_mode:
            if not had_parts:                              # bo'sh loyiha — fayldagi raqamlar o'zgarmasin: loyiha rejimi almashadi
                project.size_mode = file_mode
                rep.size_mode_changed = file_mode.value
                rep.warnings.append(_("imp_mode_changed", m=file_mode.value))
            else:
                em = calc.edge_map(project)
                keep: list[_Staged] = []
                for s in staged:
                    if s.linear:                           # CL detalida eni yo'q — o'lcham rejimi o'tkazilmaydi
                        keep.append(s)
                        continue
                    sz = compute_sizes(s.part, file_mode, em)
                    L2, W2 = (round(v, 3) for v in getattr(sz, project.size_mode.value))
                    if L2 <= 0 or W2 <= 0:
                        rep.skipped.append(dict(row=s.rno, tab="parts", reason=_(
                            "imp_skip_nonpos", f=_("imp_f_length") + "/" + _("imp_f_width"), v=f"{L2:g}×{W2:g}")))
                        continue
                    s.part.length, s.part.width = L2, W2
                    keep.append(s)
                staged = keep

    # Mahsulotlarni loyihaga qo'shish: fayldagi tartibda, so'ng qiymatdan yaratilganlar
    new_products: list[Product] = []
    if files is not None:
        add_all = cfg.products.add_empty or not tab.enabled
        for fp in files.values():
            if not fp.existing and (fp.used or add_all):
                new_products.append(fp.product)
                rep.created_products += 1
    new_products += value_products
    # Hech narsa qo'shilmagan bo'sh standart «Изделие 1» — yangi mahsulotlar kelsa, olib tashlanadi
    if new_products:
        used_ids = {s.part.product_id for s in staged} | {p.product_id for o in project.operations for p in o.parts}
        project.products = [p for p in project.products if not _pristine_default(p) or p.id in used_ids]
    project.products.extend(new_products)

    # Detallarni operatsiyalarga qo'shish
    uid = max((p.uid for o in project.operations for p in o.parts), default=0)
    fallback = project.products[0].id if project.products else None
    touched: dict[str, Operation] = {}
    for s in staged:
        uid += 1
        s.part.uid = uid
        s.part.product_id = s.part.product_id or fallback
        s.op.parts.append(s.part)
        touched.setdefault(s.op.id, s.op)
    rep.imported = len(staged)
    rep.touched_ops = list(touched.values())
    W18.link_extras(project, staged, rep)                    # W18: (SP) / (GR) / (XNC) ustun guruhlari (uid berilgandan keyin)
    return staged


def _pristine_default(p: Product) -> bool:
    """Foydalanuvchi tegmagan standart mahsulot («Изделие 1» / «Mahsulot 1», soni 1, bo'sh maydonlar)."""
    return (p.name in ("Изделие 1", "Mahsulot 1") and p.qty == 1 and not (p.code or p.description or p.order_info
            or p.phone1 or p.phone2 or p.ready_date or p.extra or p.messages))


# ───────────────────────── Kirish nuqtasi ─────────────────────────
def run_import(project: Project, data: bytes, filename: str, cfg: ExcelImportConfig, *,
               make_cs: Callable[[str], Operation] | None = None,
               make_op: Callable[..., Operation] | None = None) -> ImportReport:
    """Excel/CSV → loyiha (`project` joyida o'zgaradi; saqlash chaqiruvchida). Xato — ImportConfigError / ValueError.
    `make_op(tur, nom, kod, katalog_id)` — yangi operatsiya yaratuvchi (API qatlamida katalog bilan; berilmasa — standart)."""
    from . import import_v2_w18 as W18
    rep = ImportReport()
    make_cs = make_cs or default_cs
    make_op = make_op or W18.default_make_op
    if cfg.mode == "products_qty":
        with imp.Book(data, filename) as bk:
            _products_qty(project, bk, cfg, rep)
    else:
        if not (cfg.parts.enabled or cfg.products.enabled or cfg.simple.enabled or cfg.materials.enabled):
            raise ImportConfigError(_("imp_nothing"))
        with imp.Book(data, filename) as bk:
            files, zero_keys = (None, set())
            if cfg.products.enabled:
                files, zero_keys = _read_products(bk, cfg.products, project, rep)
            if cfg.materials.enabled:                       # W18 «Материалы»: detallardan oldin — «Материал» ustuni shu operatsiyalarni topadi
                W18.import_materials(project, bk, cfg.materials, rep, make_op)
            if cfg.parts.enabled:
                _import_parts(project, bk, cfg, rep, make_cs, files, zero_keys, make_op)
            elif cfg.products.enabled:                      # faqat «Изделия»: hammasi qo'shiladi (bo'sh mahsulotlar ham)
                add = [fp.product for fp in (files or {}).values() if not fp.existing]
                if len(add) and project.products:
                    project.products = [p for p in project.products if not _pristine_default(p)]
                project.products.extend(add)
                rep.created_products += len(add)
            if cfg.simple.enabled:                          # W18 «Простые операции» → (O) Комплектация
                W18.import_simple(project, bk, cfg.simple, rep)
    if rep.skipped:
        rep.warnings.append(_("imp_rows_skipped", n=len(rep.skipped)))
    if rep.zero_skipped:
        rep.warnings.append(_("imp_zero_skipped", n=rep.zero_skipped))
    return rep
