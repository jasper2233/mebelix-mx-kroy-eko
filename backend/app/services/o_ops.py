"""(O) Комплектация и другие действия — hisob, ombor talabnomasi, mahsulot narxi, buferdan (Excel) qo'yish, MES.

Operatsiya murakkab hisobsiz ishlar uchun (furnitura, qadoq, transport, o'rnatish): egasi (loyiha yoki mahsulot) +
materiallar jadvali (Код, Наименование, Ед.И, Кол, Цена) + qo'lda ish narxi + izoh. Batafsil — `docs/mebelix/T_O_KOMPLEKTATSIYA.md`.

    mult           = mahsulot soni        (egasi mahsulot bo'lsa)  |  1  (egasi — loyiha)
    cost_material  = round(Σ(qty × price) × mult, 2)
    cost_operation = round(work_cost × mult, 2)
    omborga qty    = qty × mult

Bu modul `calc.py` dan chaqiriladi (u yerda qayta eksport qilinadi) va `calc` ni import qilmaydi (aylanma bog'lanish yo'q).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

from pydantic import BaseModel, Field

from ..i18n import _
from ..models import O_MAX_ROWS, OMaterial, OParams, OpType, Operation, Project

DEFAULT_UNIT = "шт"

# Savol 3.x (loyiha darajasidagi O narxi): False — loyiha egasi bo'lgan O narxi mahsulotlarga TAQSIMLANMAYDI (faqat loyiha
# jamida). True bo'lsa — mahsulotlarga ularning soniga proporsional (har dona teng ulush) taqsimlanadi.
SPREAD_PROJECT_OWNED = False

# Buferdan qo'yishda katta matn chegarasi (belgi) — api_o.PasteIn bilan bir xil
PASTE_MAX_CHARS = 2_000_000


class ODefaults(BaseModel):
    """`o_defaults` sozlamasi: yangi O operatsiyasi uchun ish narxi va yangi qatorlarning standart birligi."""
    work_cost: float = Field(0, ge=0, le=1e9, allow_inf_nan=False)
    unit: str = Field(DEFAULT_UNIT, min_length=1, max_length=20)


# ───────────────────────── Yaratish / egasi ─────────────────────────
def new_params(defaults: Optional[dict] = None) -> OParams:
    """Yangi O operatsiyasi parametrlari (`o_defaults` bo'yicha ish narxi)."""
    d = defaults or {}
    try:
        wc = float(d.get("work_cost") or 0)
    except (TypeError, ValueError):
        wc = 0.0
    return OParams(work_cost=min(max(wc, 0.0), 1e9))


def default_unit(defaults: Optional[dict] = None) -> str:
    u = ((defaults or {}).get("unit") or "").strip()
    return u[:20] or DEFAULT_UNIT


def owner_ok(project: Project, op: Operation) -> bool:
    """`owner_product_id` bo'sh yoki loyihadagi mavjud mahsulot (server tekshiruvi: aks holda 422)."""
    pid = op.o.owner_product_id if op.o else None
    return not pid or any(pr.id == pid for pr in project.products)


def owner_product(project: Project, p: OParams):
    if not p.owner_product_id:
        return None
    return next((pr for pr in project.products if pr.id == p.owner_product_id), None)


def o_multiplier(project: Project, p: OParams) -> float:
    """Egasi mahsulot bo'lsa — uning soni (0 ham bo'lishi mumkin), aks holda 1."""
    pr = owner_product(project, p)
    return float(pr.qty) if pr is not None else 1.0


def prune_o_owners(project: Project) -> None:
    """Mahsulot o'chirilgan (yoki MES yangilashida yo'qolgan) bo'lsa — operatsiya loyiha egasiga o'tadi va
    `OParams.messages` ga «owner_lost» kodi yoziladi (UI ogohlantiradi; foydalanuvchi yopguncha turadi)."""
    ids = {pr.id for pr in project.products}
    for op in project.operations:
        if op.type == OpType.O and op.o and op.o.owner_product_id and op.o.owner_product_id not in ids:
            op.o.owner_product_id = None
            if "owner_lost" not in op.o.messages:
                op.o.messages.append("owner_lost")


# ───────────────────────── Hisob ─────────────────────────
def material_sum(p: OParams) -> float:
    """Jadval bo'yicha Σ(qty × price) — 1 mahsulot / loyiha uchun (ko'paytirgichsiz)."""
    return math.fsum(m.qty * m.price for m in p.materials)


def o_cost(project: Project, op: Operation) -> dict:
    """O operatsiyasi narxi: `Operation.cost_material / cost_operation` ga yoziladi (ko'paytirgich bilan, 2 xonagacha).
    `op.o` bo'lmasa (eski JSON) — bo'sh parametrlar yaratiladi (xato emas)."""
    if op.o is None:
        op.o = OParams()
    p = op.o
    mult = o_multiplier(project, p)
    base = material_sum(p)
    op.cost_material = round(base * mult, 2)
    op.cost_operation = round(p.work_cost * mult, 2)
    p.multiplier = mult
    return dict(mult=mult, per_unit_material=round(base, 2), rows=len(p.materials),
                cost_material=op.cost_material, cost_operation=op.cost_operation)


def product_shares(project: Project, op: Operation) -> dict[str, float]:
    """Mahsulot narxiga ulush (calc.product_costs uchun): egasi mahsulot → butun narx shunga; egasi loyiha →
    SPREAD_PROJECT_OWNED=False da bo'sh (taqsimlanmaydi)."""
    p = op.o
    if p is None:
        return {}
    if owner_product(project, p) is not None:
        return {p.owner_product_id: 1.0}            # type: ignore[dict-item]
    if SPREAD_PROJECT_OWNED:
        return {pr.id: float(pr.qty) for pr in project.products if pr.qty > 0}
    return {}


def o_warehouse_rows(project: Project, op: Operation) -> list[dict]:
    """«Требование на склад»: har material qatori — Тип `O`, Код, Наименование (`op.name — material`), Ед.И (o'zining),
    Кол = qty × mult. mult = 0 (mahsulot soni 0) yoki qty = 0 — qator chiqmaydi."""
    p = op.o
    if p is None:
        return []
    mult = o_multiplier(project, p)
    if mult <= 0:
        return []
    out = []
    for m in p.materials:
        q = m.qty * mult
        if q <= 0 or not (m.code or m.name):
            continue
        title = m.name or m.code
        out.append(dict(op_id=op.id, type="O", code=m.code, name=f"{op.name} — {title}" if op.name else title,
                        unit=m.unit, unit_code="", qty=round(q, 3), note="", price=m.price,
                        sum=round(q * m.price, 2)))
    return out


def mes_payload(project: Project, op: Operation) -> dict:
    """MES `mes-export` da O operatsiyasi: egasi, ko'paytirgich, ish narxi va materiallar (1 dona va jami)."""
    p = op.o or OParams()
    mult = o_multiplier(project, p)
    return dict(owner_product_id=p.owner_product_id, multiplier=mult, work_cost=p.work_cost,
                materials=[dict(code=m.code, name=m.name, unit=m.unit, qty=m.qty, price=m.price,
                                qty_total=round(m.qty * mult, 3)) for m in p.materials])


# ───────────────────────── `.project` (Bazis / korxona fayli) importi ─────────────────────────
def _f(v, d: float = 0.0) -> float:
    try:
        x = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d
    return x if math.isfinite(x) else d


def from_project_xml(oe, goods: dict, products: dict, warnings: list[str]) -> Operation:
    """`<operation typeId="O">` → `Operation(type=O)`. Format (yordam «Формат файлов проектов»): standart atributlar
    (typeName, description, costOperation, costMaterial, owner, printable, startNewPage) + `<material id count/>` havolalari —
    ular `<good typeId="simple" code name unit count cost/>` (oddiy material) ga ishora qiladi.

    * Qator: Код/Наименование/Ед.И — good dan; Кол — `<material count>` (yo'q bo'lsa good.count), Цена — good.cost.
    * Egasi: `owner` mahsulot good id si bo'lsa — shu mahsulot (`products`: fayldagi good id → Product), aks holda loyiha.
    * Ish narxi: `costOperation`. Egasi mahsulot (soni q > 1) bo'lsa va faylning `costMaterial` si Σ(Кол × Цена) × q ga teng
      (1 dona uchun emas, barcha mahsulotlar uchun yozilgan) bo'lsa — narxlar q ga bo'linadi (ogohlantirish bilan).
      Real faylda O yo'q — bu taxmin (savol hisobotda), ikkala holatda ham foydalanuvchi natijani ko'radi.
    `printable` / `startNewPage` ni chaqiruvchi o'rnatadi."""
    name = (oe.get("typeName") or oe.get("name") or "").strip() or "Комплектация"
    ref = (oe.get("owner") or "").strip()
    owner = products.get(ref)
    if ref and owner is None and ref not in ("0", "-1") and ref not in goods:
        warnings.append(_("imp_o_owner", name=name, ref=ref))
    mats: list[OMaterial] = []
    for me in oe.findall("material"):
        mid = (me.get("id") or "").strip()
        g = goods.get(mid)
        if g is None:
            warnings.append(_("imp_o_material", name=name, ref=mid or "?"))
            continue
        qty = _f(me.get("count"), _f(g.get("count"), 1.0))
        mats.append(OMaterial(code=(g.get("code") or "")[:100], name=(g.get("name") or "")[:300],
                              unit=((g.get("unit") or "").strip() or DEFAULT_UNIT)[:20],
                              qty=min(max(qty, 0.0), 1e9), price=min(max(_f(g.get("cost"), 0.0), 0.0), 1e9)))
    work = min(max(_f(oe.get("costOperation"), 0.0), 0.0), 1e9)
    if owner is not None and owner.qty > 1 and oe.get("costMaterial") is not None:
        base = math.fsum(m.qty * m.price for m in mats)
        cm = _f(oe.get("costMaterial"), -1.0)
        tol = 0.01 * max(1.0, cm)
        if cm >= 0 and base > 0 and abs(cm - base * owner.qty) <= tol and abs(cm - base) > tol:
            work = round(work / owner.qty, 2)
            warnings.append(_("imp_o_scaled", name=name, q=owner.qty))
    return Operation(type=OpType.O, code=(oe.get("code") or "")[:100], name=name,
                     description=oe.get("description") or "",
                     o=OParams(owner_product_id=owner.id if owner is not None else None,
                               materials=mats[:O_MAX_ROWS], work_cost=work))


# ───────────────────────── Buferdan (Excel / jadval) qo'yish ─────────────────────────
@dataclass
class PasteResult:
    rows: list[OMaterial] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)        # [{row, reason}] — row: qo'yilgan matndagi qator raqami (1 dan)
    warnings: list[str] = field(default_factory=list)


# ustun sarlavhasi so'zlari (bitta katak butunlay shunga teng bo'lsa) — birinchi qator sarlavha deb o'tkaziladi
_HEADER_WORDS = re.compile(
    r"(код|kod|code|артикул|наименование|название|nomi|nom|name|ед\.?\s*и\.?|ед\.?\s*изм\.?|birlik|unit|"
    r"кол\.?|кол-во|количество|soni|miqdor|qty|count|цена|narx|price|стоимость|summa|cost)", re.I)
_UNIT_SUFFIX = re.compile(r"[\d.,\s -]+([^\W\d_]+)\.?\s*$")


def _is_header(cells: list[str]) -> bool:
    return sum(1 for c in cells if c and _HEADER_WORDS.fullmatch(c.strip())) >= 2


def _unquote(c: str) -> str:
    c = c.strip()
    if len(c) >= 2 and c[0] == '"' and c[-1] == '"':          # Excel: tab/qator ko'chirishi bor katak qo'shtirnoqda
        return c[1:-1].replace('""', '"').strip()
    return c


def parse_paste(text: str, room: int = O_MAX_ROWS, default_unit: str = DEFAULT_UNIT) -> PasteResult:
    """Buferdan (TSV) qo'yish: qatorlar `\\n` bilan, kataklar `\\t` bilan; Excel o'ragan qo'shtirnoqlar ochiladi.
    Butunlay bo'sh qator (matnda `\\n\\n`) jim o'tkaziladi; qolgan qoidalar — `parse_rows`."""
    rows = ((rno, [_unquote(c) for c in line.split("\t")])
            for rno, line in enumerate(text.replace("\r", "").split("\n"), 1)
            if line.strip() or "\t" in line)
    return parse_rows(rows, room, default_unit)


def parse_rows(rows: Iterable[tuple[int, list[str]]], room: int = O_MAX_ROWS,
               default_unit: str = DEFAULT_UNIT) -> PasteResult:
    """Katak qatorlari `(qator raqami, [katak, …])` → materiallar. Ustunlar tartibi `Код, Наименование, Ед.И, Кол, Цена`
    (qolgan ustunlar — masalan «Стоимость» — e'tiborga olinmaydi, u hisoblanadi). Buferdan qo'yish (`parse_paste`) ham,
    Excel importi («Простые операции» / «Материалы» tabi — W3) ham shu funksiyadan foydalanishi mumkin.

    * `1 200,5`, `1.200,5`, `2 шт` kabi sonlar `importers.parse_number` bilan o'qiladi; Кол bo'sh — 1, Цена bo'sh — 0,
      Ед.И bo'sh — Кол dagi birlik qo'shimchasi («2 шт» → шт) yoki `default_unit`.
    * Faqat ajratgichlardan iborat qator («\\t\\t») — «bo'sh qator» sifatida `skipped` ga yoziladi. Birinchi qator ustun
      sarlavhasiga o'xshasa (Код/Наименование/…) — ogohlantirish bilan o'tkaziladi.
    * Nomi ham, kodi ham yo'q, son emas / manfiy / juda katta, matni uzun qator, yoki `room` (qolgan joy, jami ≤ 5000)
      tugagan — `skipped` ga (qator raqami + sabab); hech narsa jim tashlanmaydi."""
    from .importers import parse_number                      # tarkibiy son o'qish: «1 200,5», «2 шт»
    res = PasteResult()
    first = True
    for rno, cells in rows:
        cells = [str(c if c is not None else "").strip() for c in cells]
        if first:
            first = False
            if _is_header(cells):
                res.warnings.append(_("o_header_skipped", row=rno))
                continue
        if not any(cells):
            res.skipped.append(dict(row=rno, reason=_("o_skip_empty")))
            continue
        code, name, unit, qty_s, price_s = (cells + [""] * 5)[:5]
        if not code and not name:
            res.skipped.append(dict(row=rno, reason=_("o_skip_noname")))
            continue
        reasons: list[str] = []

        def num(raw: str, label: str, default: float) -> float:
            if raw == "":
                return default
            v = parse_number(raw)
            if v is None:
                reasons.append(_("imp_skip_nan", f=_(label), v=raw[:30]))
                return default
            if v < 0:
                reasons.append(_("o_skip_neg", f=_(label), v=f"{v:g}"))
            elif v > 1e9:
                reasons.append(_("imp_skip_big", f=_(label), v=f"{v:g}"))
            return v
        qty = num(qty_s, "o_f_qty", 1.0)
        price = num(price_s, "o_f_price", 0.0)
        if not unit and qty_s:                                  # «2 шт» → birlik shtuk
            m = _UNIT_SUFFIX.search(qty_s)
            unit = m.group(1) if m else ""
        unit = unit or default_unit
        for val, lim, label in ((code, 100, "o_f_code"), (name, 300, "o_f_name"), (unit, 20, "o_f_unit")):
            if len(val) > lim:
                reasons.append(_("o_skip_long", f=_(label), n=lim))
        if not reasons and len(res.rows) >= room:
            reasons.append(_("o_skip_limit", n=O_MAX_ROWS))
        if reasons:
            res.skipped.append(dict(row=rno, reason="; ".join(reasons)))
            continue
        res.rows.append(OMaterial(code=code, name=name, unit=unit, qty=qty, price=price))
    if res.skipped:
        res.warnings.append(_("imp_rows_skipped", n=len(res.skipped)))
    return res
