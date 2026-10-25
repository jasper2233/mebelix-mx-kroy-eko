"""MES paketi v1: tayyor kroyni MebeliX Kroy (MX) dan MES ga topshirish uchun JSON («ishlab chiqarish paketi»).

Shartnoma hujjati — `docs/mebelix/MES_PAKET_V1.md` (o'zbekcha, JSON sxema va sintetik misol bilan). Bu modul faqat
paketni QURADI (`GET /api/projects/{id}/mes-package?version=1`); hech qayerga yubormaydi — yuborish va MES dashboardiga
o'tish («MES» tugmasi) MES tomoni tayyor bo'lgach qo'shiladi.

Asosiy qoidalar (MES ingest bilan mos):
  * Detal nusxasi QR: `{buyurtma}_{mahsulot}_{detal}[_n]` — bitta nusxada suffikssiz, bir nechta bo'lsa `_1.._n`
    (MES `instance_qr`). Buyurtma raqami noma'lum bo'lsa `qr` — null, `key` (`{mahsulot}_{detal}`) beriladi.
  * Kodlar skaner o'qiy oladigan ASCII bo'lishi kerak (MES `_scannable`): mos kelmasa `warnings` ga yoziladi.
  * Foydali (деловой) qoldiq: har jismoniy nusxa alohida yozuv (`sheet_copy`), ID `ATX-{buyurtma}-{n}` (material/list tartibida).
  * Kesish xaritasi: `cut_maps[].sheets[]` = MES `CutmapSheet` (no — global andoza raqami, L, W, mult, cells, cuts).
  * Postprotsessor fayllari — FAQAT mijoz uchun ochilgan (`services/pp_access.py`) va ishlaydigan stanoklar; har fayl
    stanokka bog'langan; sha256 nazorat summasi. MES ishlov oqimi faqat fayl kelgan bo'lsa ishga tushadi (`machining`).
Sarf (`consumption`) va omborga yoziladigan qoldiqlar (`remnants[].to_warehouse`) MES da avtomatik hujjat bo'ladi
(foydalanuvchi qarori, 2026-10-18).
"""
from __future__ import annotations

import base64
import hashlib
import re
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..i18n import _
from ..models import OpType, Operation, PostprocessorProfile, Project

PACKAGE_FORMAT = "mebelix.kroy.mes-package"
VERSION = 1
MAX_INLINE_BYTES = 40 * 1024 * 1024       # inline fayllar yig'indisi (base64 dan oldin); oshsa — files=meta tavsiya
_MES_NUMBER = re.compile(r"^B-\d{4}-\d+$")  # MES buyurtma raqami (B-YYYY-NNN)
_SIDE = {"top": "t", "bottom": "b", "left": "l", "right": "r"}


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ───────────────────────── Sxema (pydantic) ─────────────────────────
class PackageMeta(_M):
    format: Literal["mebelix.kroy.mes-package"] = PACKAGE_FORMAT
    version: Literal[1] = 1
    generated_at: str                               # UTC, ISO 8601 («2026-10-18T09:12:33Z»)
    generator: str = "MebeliX Kroy"
    checksum_algorithm: Literal["sha256"] = "sha256"
    units: dict[str, str] = Field(default_factory=lambda: dict(length="mm", area="m2", edge="m"))


class Source(_M):
    system: Literal["mebelix-kroy"] = "mebelix-kroy"
    project_id: str                                 # MX loyiha id (hex)
    project_number: int                             # MX «Заказ ID»
    project_name: str
    customer: str = ""
    mes_order_id: Optional[int] = None              # MES `order.id` (MX hozir saqlamaydi — so'rov parametri / kelishiladi)
    mes_order_number: Optional[str] = None          # MES `order.number` (B-YYYY-NNN) — QR va ATX shu bilan quriladi
    mes_order_ref: Optional[str] = None             # MX `mes_order_ref` (xom qiymat)
    kind: Literal["bazis_file", "project_file", "manual"]   # Bazis fayli / boshqa kroy fayli importi / qo'lda
    order_date: str = ""
    ready_date: str = ""
    currency: str = "UZS"


class Product(_M):
    mx_id: str
    code: str                                       # QR uchun ishlatilgan kod (bo'sh bo'lsa — nomi)
    name: str
    qty: int


class Material(_M):
    ref: str                                        # MX operatsiya id (paket ichidagi havola)
    kind: Literal["sheet", "linear", "nest"]
    code: str
    name: str
    thickness: float
    catalog_id: Optional[str] = None                # MES katalog kodi bo'lishi kutiladi (M-LD-…; kelishiladi)


class EdgeBand(_M):
    ref: str                                        # MX EL operatsiya id
    code: str
    name: str
    symbol: str
    thickness: float
    width: float
    work_m: float                                   # yopishtirish uzunligi (m)
    material_m: float                               # material sarfi (m), zaxira bilan
    catalog_id: Optional[str] = None


class PartEdge(_M):
    ref: str                                        # edge_bands[].ref
    symbol: str
    name: str


class PartInstance(_M):
    n: Optional[int] = None                         # nusxa raqami (bitta nusxada None)
    qr: Optional[str] = None                        # {buyurtma}_{key}[_n]
    pattern_no: Optional[int] = None                # cut_maps[].sheets[].no
    cell_index: Optional[int] = None                # shu andozadagi cells[].cell
    sheet_copy: Optional[int] = None                # andozaning nechanchi jismoniy listi (1..mult)


class PackagePart(_M):
    mx_id: str
    mx_uid: int                                     # MX «ID» (loyiha ichida noyob raqam, etiketkada)
    key: str                                        # {mahsulot}_{detal}
    product_code: str
    product_mx_id: Optional[str] = None
    code: str
    name: str
    material_ref: str
    length: float
    width: float
    thickness: float
    qty_total: int                                  # ОК = detal soni × mahsulot soni
    qty_from_stock: int = 0                         # МК — omborda tayyor (kesilmaydi)
    grain: bool = False
    edges: dict[str, PartEdge] = Field(default_factory=dict)    # l / r / t / b
    xnc_refs: list[str] = Field(default_factory=list)            # xnc_programs[].mx_op_id
    instances: list[PartInstance] = Field(default_factory=list)


class SheetUse(_M):
    material_ref: str
    length: float
    width: float
    qty: int                                        # ishlatilgan listlar (jismoniy)
    source: Literal["new", "remnant"]
    remnant_id: Optional[int] = None                # MX qoldiqlar ombori id (source=remnant)


class CutCell(_M):
    cell: int                                       # 1 dan (andoza ichida)
    x: float
    y: float
    w: float                                        # list uzunligi (L) yo'nalishida
    h: float                                        # list eni (W) yo'nalishida
    waste: bool = False                             # True — qoldiq katagi
    part_uid: Optional[int] = None
    part_key: Optional[str] = None
    rot: bool = False
    eW: Optional[list[Optional[str]]] = None        # [chap, o'ng] kromka belgilari (joylashgan holatda)
    eH: Optional[list[Optional[str]]] = None        # [tepa, past]
    business: Optional[bool] = None                 # qoldiq: foydali (деловой)
    remnant_no: Optional[int] = None                # MX qoldiq raqami (Д1, Д2 …)
    angle: Optional[float] = None                   # (nest) burilish, gradus
    outline: Optional[list[list[float]]] = None     # (nest) kontur, list koordinatalarida


class CutLine(_M):
    x1: float
    y1: float
    x2: float
    y2: float


class CutCommand(_M):
    code: Literal["R", "T", "C", "P", "W"]
    level: int
    size: float
    count: int
    ref: str = ""


class CutSheet(_M):
    no: int                                         # global andoza raqami (barcha materiallar bo'ylab, 1 dan)
    index: int                                      # MX operatsiya ichidagi karta raqami
    L: float
    W: float
    mult: int                                       # shu andozadan nechta list
    is_remnant: bool = False
    remnant_id: Optional[int] = None
    fill_percent: float = 0
    cut_length_m: float = 0
    cells: list[CutCell] = Field(default_factory=list)
    cuts: list[CutLine] = Field(default_factory=list)          # gilyotina chiziqlari (sheet: bor; linear/nest: bo'sh)
    commands: list[CutCommand] = Field(default_factory=list)  # arra buyruqlari (R/T/C/P/W)


class CutMapMaterial(_M):
    material_ref: str
    kind: Literal["sheet", "linear", "nest"]
    kerf: float = 0
    sheets: list[CutSheet] = Field(default_factory=list)


class Remnant(_M):
    id: Optional[str] = None                        # ATX-{buyurtma}-{n} (buyurtma raqami noma'lum bo'lsa None)
    n: int                                          # paket ichidagi tartib raqami (ATX raqami)
    material_ref: str
    material_code: str
    material_name: str
    thickness: float
    sheet_no: int                                   # cut_maps[].sheets[].no
    sheet_copy: int                                 # 1..mult
    remnant_no: int                                 # MX Д raqami
    length: float                                   # foydali o'lcham (torsovkadan keyin)
    width: float
    raw_length: float                               # xom o'lcham (list chetigacha)
    raw_width: float
    to_warehouse: bool = True                       # False — mijoz olib ketadi («Исп. кол-во»)


class Consumption(_M):
    material_ref: str
    type: str                                       # CS / CL / CN / EL / SP / O
    code: str
    name: str
    unit: str                                       # sheets | pcs | m | m2 | …
    qty: float
    remnant_id: Optional[int] = None                # ombordagi qoldiqdan ishlatilgan list


class XncProgram(_M):
    mx_op_id: str
    code: str
    name: str
    qty: int
    part_uid: Optional[int] = None
    part_key: Optional[str] = None
    stats: dict[str, float] = Field(default_factory=dict)       # drills, mill_m, saw_m


class XncToolOpUse(_M):
    """Asbob shu XNC operatsiyada (1 dona detal uchun qiymatlar; `qty` — nechta detal)."""
    op_id: str
    code: str = ""
    part_id: Optional[str] = None
    part_uid: Optional[int] = None
    part_name: str = ""
    qty: int = 0
    holes: int = 0
    mill_m: float = 0
    saw_m: float = 0


class XncToolWork(_M):
    """Asbob qilgan ish (2026-10-25: MES moliya har asbobga alohida narx qo'yadi — parma — teshik, freza / arra — metr).
    kind: drill | mill | saw; side: face | side (parma); through — yuza teshigi detalni teshib o'tadi. Qiymatlar — buyurtma
    bo'yicha jami (nusxalar bilan)."""
    kind: Literal["drill", "mill", "saw"]
    name: str
    d: float
    key: str = ""                       # asbob kaliti (kind|nom|diametr|tomon|teshib_o'tadi)
    mes_code: str = ""                  # MES (moliya) dagi asbob kodi — «Настройки → MES интеграция → XNC → MES»
    known: bool = True                  # «bizning asboblar» ro'yxatida va faol (ro'yxat bo'sh bo'lsa — hammasi true)
    mismatch: bool = False              # asbob nomidagi raqam diametrga mos emas (dasturda adashib yozilgan bo'lishi mumkin)
    side: str = ""
    through: bool = False
    depths: list[float] = Field(default_factory=list)
    holes: int = 0
    mill_m: float = 0
    mill_pass_m: float = 0              # chuqurlik qadamlari (SDP) bilan
    saw_m: float = 0
    parts: int = 0                      # nechta detal (dona)
    ops: int = 0                        # nechta XNC operatsiya
    uses: list[XncToolOpUse] = Field(default_factory=list)


class XncToolSummary(_M):
    enabled: bool = True                # sozlamada XNC → MES o'chirilgan bo'lsa — false va bo'sh
    xnc_ops: int = 0                    # XNC operatsiyalar soni
    xnc_parts: int = 0                  # XNC ishlovi bor detallar (dona)
    tools: list[XncToolWork] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)   # unknown_tool:… — ro'yxatda yo'q asbob; name_diameter_mismatch:…


class MachineRef(_M):
    key: str                                        # MX stanok kaliti
    name: str
    label: str
    group: Literal["saw", "cnc"]
    mes_machine_id: Optional[int] = None            # MES `machine.id` — bog'lash jadvali kelishiladi


class PostprocessorFile(_M):
    format_id: str                                  # machine:<key>
    machine: MachineRef
    source: Literal["native", "template"]           # o'rnatilgan generator / korxona shabloni
    op_ref: str                                     # material_ref (saw) yoki xnc_programs[].mx_op_id (cnc)
    part_keys: list[str] = Field(default_factory=list)          # cnc: dastur bog'langan detal kaliti
    file_name: str
    media_type: str
    size: int                                       # bayt
    sha256: str                                     # hex, xom baytlar bo'yicha
    content_base64: Optional[str] = None            # files=inline
    url: Optional[str] = None                       # files=meta: MX dan qayta olish yo'li (Bearer bilan)


class Machining(_M):
    rule: str = "MES ishlov oqimi faqat shu paketda postprotsessor fayli kelgan stanok/detal uchun ishga tushadi"
    saw_ready: bool = False
    cnc_ready: bool = False
    files: int = 0


class MesPackageV1(_M):
    package: PackageMeta
    source: Source
    products: list[Product] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)
    edge_bands: list[EdgeBand] = Field(default_factory=list)
    parts: list[PackagePart] = Field(default_factory=list)
    sheets: list[SheetUse] = Field(default_factory=list)
    cut_maps: list[CutMapMaterial] = Field(default_factory=list)
    remnants: list[Remnant] = Field(default_factory=list)
    consumption: list[Consumption] = Field(default_factory=list)
    xnc_programs: list[XncProgram] = Field(default_factory=list)
    xnc_tools: XncToolSummary = Field(default_factory=XncToolSummary)     # (2026-10-25) asbob bo'yicha ish — moliya uchun
    postprocessor_files: list[PostprocessorFile] = Field(default_factory=list)
    machining: Machining = Field(default_factory=Machining)
    warnings: list[str] = Field(default_factory=list)


def json_schema() -> dict:
    return MesPackageV1.model_json_schema()


# ───────────────────────── Yordamchilar ─────────────────────────
def scannable(code: str) -> bool:
    """MES qoidasi: ID ga kiradigan kod faqat ko'rinadigan ASCII (skaner klaviatura sifatida yozadi)."""
    return bool(code) and code.isascii() and code.isprintable()


def instance_qr(order_number: Optional[str], key: str, n: Optional[int]) -> Optional[str]:
    if not order_number:
        return None
    return f"{order_number}_{key}" + ("" if n is None else f"_{n}")


def source_kind(project: Project) -> str:
    """Bazis fayli (mahsulotda `product.import` belgisi), boshqa kroy fayli importi (import parametrlari / dastur matni)
    yoki qo'lda kiritilgan loyiha."""
    if any(any(k.startswith("product.import") for k in pr.extra) for pr in project.products):
        return "bazis_file"
    if any(pr.extra or pr.legacy_program for pr in project.products):
        return "project_file"
    return "manual"


def _thickness(op: Operation) -> float:
    if op.type == OpType.CL and op.cl:
        return float(op.cl.thickness)
    if op.type == OpType.CN and op.cn:
        return float(op.cn.thickness)
    return float(op.cs_material.thickness) if op.cs_material else 0.0


def _kind(op: Operation) -> str:
    return {OpType.CL: "linear", OpType.CN: "nest"}.get(op.type, "sheet")


def _cut_lines(strips: list[dict], L: float, W: float) -> list[CutLine]:
    """Kesish daraxtidan (`CutMap.strips`) gilyotina chiziqlari: har ichki tugunda qo'shni bolalar chegarasi ota hududi
    bo'ylab (o'q «x» — bolalar X bo'yicha, chiziq vertikal); ildiz atrofidagi torsovka chiziqlari ham. Chiziq — bolaning
    oxirgi chegarasi (propil shu yerdan boshlanadi)."""
    out: list[CutLine] = []
    eps = 1e-6
    if not strips:
        return out
    root = strips[0]

    def f(v) -> float:
        try:
            return round(float(v or 0), 2)
        except (TypeError, ValueError):
            return 0.0
    rx, ry, rl, rw = f(root.get("x")), f(root.get("y")), f(root.get("l")), f(root.get("w"))
    if rx > eps:
        out.append(CutLine(x1=rx, y1=0, x2=rx, y2=W))
    if rx + rl < L - eps:
        out.append(CutLine(x1=rx + rl, y1=0, x2=rx + rl, y2=W))
    if ry > eps:
        out.append(CutLine(x1=rx, y1=ry, x2=rx + rl, y2=ry))
    if ry + rw < W - eps:
        out.append(CutLine(x1=rx, y1=ry + rw, x2=rx + rl, y2=ry + rw))

    def walk(n: dict, depth: int) -> None:
        if depth > 64 or n.get("k") != "C":
            return
        kids = [c for c in (n.get("c") or []) if isinstance(c, dict)]
        x, y, l, w = f(n.get("x")), f(n.get("y")), f(n.get("l")), f(n.get("w"))
        for i, c in enumerate(kids):
            if i < len(kids) - 1:
                if n.get("a") == "x":
                    e = f(c.get("x")) + f(c.get("l"))
                    out.append(CutLine(x1=round(e, 2), y1=y, x2=round(e, 2), y2=round(y + w, 2)))
                else:
                    e = f(c.get("y")) + f(c.get("w"))
                    out.append(CutLine(x1=x, y1=round(e, 2), x2=round(x + l, 2), y2=round(e, 2)))
            walk(c, depth + 1)
    walk(root, 0)
    return out


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


# ───────────────────────── Qurish ─────────────────────────
def build(project: Project, *, mes_order_id: Optional[int] = None, mes_order_number: Optional[str] = None,
          pp: str = "enabled", files: str = "inline") -> MesPackageV1:
    """Paketni quradi (loyiha o'zgarmaydi). `pp`: enabled (standart — ochilgan ∧ yoqilgan ∧ ishlaydigan stanoklar) |
    all (ochilgan ∧ ishlaydigan hammasi) | none | vergul bilan stanok kalitlari (`machine:` ixtiyoriy; yopiq — 403,
    noma'lum — 400). `files`: inline (base64) | meta (faqat nom/hajm/sha256 + MX url)."""
    from ..i18n import LANG
    from .calc import edge_usage, op_part, total_qty, warehouse_request
    from .postprocessors import MACHINE_BY_KEY, pp_label
    from .render import part_edges, rotate_edges
    from .warehouse import rem_key

    if files not in ("inline", "meta"):
        raise HTTPException(400, _("mes_pkg_files"))
    warns: list[str] = []
    ref = (project.mes_order_ref or "").strip() or None
    number = (mes_order_number or "").strip() or (ref if ref and _MES_NUMBER.match(ref) else None)
    if not number:
        warns.append("mes_order_number yo'q: detal QR va ATX ID lari MES tomonda quriladi (key / n berilgan)")
    elif not scannable(number):
        warns.append(f"Buyurtma raqami «{number}» skaner o'qiy oladigan ASCII emas")

    src = Source(project_id=project.id, project_number=project.number, project_name=project.name, customer=project.customer,
                 mes_order_id=mes_order_id, mes_order_number=number, mes_order_ref=ref, kind=source_kind(project),
                 order_date=str(project.order_date), ready_date=str(project.ready_date), currency=project.currency)

    # mahsulotlar (kodi bo'sh bo'lsa — nomi, MES dagi kabi); paketga faqat detallari borlari kiradi (pastda)
    prod_code: dict[str, str] = {pr.id: (pr.code or "").strip() or (pr.name or "").strip() or pr.id[:8]
                                 for pr in project.products}

    cut_ops = [o for o in project.operations if o.type in (OpType.CS, OpType.CL, OpType.CN)]
    materials = [Material(ref=o.id, kind=_kind(o), code=o.code, name=o.name, thickness=_thickness(o), catalog_id=o.material_id)
                 for o in cut_ops]
    edge_bands: list[EdgeBand] = []
    for o in project.operations:
        if o.type == OpType.EL and o.el:
            u = edge_usage(project, o)
            edge_bands.append(EdgeBand(ref=o.id, code=o.code, name=o.name, symbol=o.el.symbol or "", thickness=o.el.thickness,
                                       width=o.el.width, work_m=float(u["work_m"]), material_m=float(u["material_m"]),
                                       catalog_id=o.material_id))

    # detallar va kalitlar (MES: takror kalit — kod oxiriga «-2», «-3»)
    parts: list[PackagePart] = []
    by_id: dict[str, PackagePart] = {}
    used_keys: set[str] = set()
    for o in cut_ops:
        for pt in o.parts:
            if pt.length <= 0:
                continue
            pcode = prod_code.get(pt.product_id or "", "0")
            code = (pt.code or "").strip() or f"{pt.uid:03d}"
            key, base, k = f"{pcode}_{code}", code, 2
            while key in used_keys:
                code = f"{base}-{k}"; k += 1
                key = f"{pcode}_{code}"
            if code != base:
                warns.append(f"Takror detal kaliti «{pcode}_{base}» → «{key}» (MX ID {pt.uid})")
            used_keys.add(key)
            if not scannable(code):
                warns.append(f"Detal kodi «{code}» (MX ID {pt.uid}) skaner o'qiy olmaydigan belgiga ega")
            ed = {_SIDE[s]: PartEdge(ref=getattr(pt, f"edge_{s}").op_id or "", symbol=e["symbol"], name=e["name"])
                  for s, e in part_edges(pt, project).items()}
            qty = total_qty(project, pt)
            pp_ = PackagePart(mx_id=pt.id, mx_uid=pt.uid, key=key, product_code=pcode,
                              product_mx_id=pt.product_id if pt.product_id in prod_code else None,
                              code=code, name=pt.name, material_ref=o.id, length=pt.length,
                              width=op_part(o, pt).width, thickness=_thickness(o), qty_total=qty,
                              qty_from_stock=min(qty, max(0, pt.minus_qty or 0)), grain=pt.grain, edges=ed,
                              xnc_refs=list(pt.xnc_op_ids),
                              instances=[PartInstance(n=None if qty == 1 else i,
                                                      qr=instance_qr(number, key, None if qty == 1 else i))
                                         for i in range(1, qty + 1)])
            parts.append(pp_)
            by_id[pt.id] = pp_

    used_products = {p.product_mx_id for p in parts}
    products: list[Product] = []
    for pr in project.products:
        if pr.id not in used_products:
            continue
        code = prod_code[pr.id]
        if not scannable(code):
            warns.append(f"Mahsulot kodi «{code}» skaner o'qiy olmaydigan belgiga ega (faqat lotin harf/raqam)")
        products.append(Product(mx_id=pr.id, code=code, name=pr.name, qty=pr.qty))
    if any(p.product_mx_id is None for p in parts):
        warns.append("Mahsulotga bog'lanmagan detallar bor — mahsulot kodi «0» deb olindi")

    # kesish xaritalari, listlar, qoldiqlar, nusxa ↔ katak bog'lanishi
    next_inst: dict[str, int] = {}
    cut_maps: list[CutMapMaterial] = []
    sheets: dict[tuple, SheetUse] = {}
    remnants: list[Remnant] = []
    no = 0
    for o in cut_ops:
        res = o.result
        if not res or not res.maps:
            warns.append(f"«{o.name}» ({o.code}) kroy qilinmagan — kesish xaritasi yo'q")
            continue
        src_parts = {p.id: p for p in o.parts}
        stock = {s.id: s for s in o.sheets}
        kerf = float(o.cs_cut.kerf) if o.type == OpType.CS and o.cs_cut else float(o.cl.kerf) if o.type == OpType.CL and o.cl else 0.0
        cm = CutMapMaterial(material_ref=o.id, kind=_kind(o), kerf=kerf)
        taken_left = {k: int(v or 0) for k, v in (res.taken_remnants or {}).items()}
        for m in res.maps:
            no += 1
            st = stock.get(m.sheet_id)
            rid = st.source_remnant_id if st else None
            is_rem = bool(m.is_remnant or (st and (st.is_remnant or st.source_remnant_id)))
            sk = (o.id, m.sheet_length, m.sheet_width, is_rem, rid)
            su = sheets.setdefault(sk, SheetUse(material_ref=o.id, length=m.sheet_length, width=m.sheet_width, qty=0,
                                                source="remnant" if is_rem else "new", remnant_id=rid))
            su.qty += m.copies
            cells: list[CutCell] = []
            for pl in m.placements:
                pt = src_parts.get(pl.part_id)
                pk = by_id.get(pl.part_id)
                ew = eh = None
                if pt is not None and o.type != OpType.CN:
                    e = rotate_edges(part_edges(pt, project), pl.rotated)
                    sym = lambda s: (e.get(s) or {}).get("symbol") if e.get(s) else None   # noqa: E731
                    ew, eh = [sym("left"), sym("right")], [sym("top"), sym("bottom")]
                c = CutCell(cell=len(cells) + 1, x=pl.x, y=pl.y, w=pl.length, h=pl.width, part_uid=pl.part_uid,
                            part_key=pk.key if pk else None, rot=pl.rotated, eW=ew, eH=eh,
                            angle=pl.angle if o.type == OpType.CN else None,
                            outline=pl.outline if o.type == OpType.CN and pl.outline else None)
                cells.append(c)
                if pk is not None:                      # nusxalar shu katakka (har jismoniy list uchun bittadan)
                    for cp in range(1, m.copies + 1):
                        i = next_inst.get(pk.mx_id, 0)
                        if i < len(pk.instances):
                            pk.instances[i].pattern_no, pk.instances[i].cell_index, pk.instances[i].sheet_copy = no, c.cell, cp
                            next_inst[pk.mx_id] = i + 1
            for of in m.offcuts:
                if of.kind != "remnant":
                    continue
                c = CutCell(cell=len(cells) + 1, x=of.x, y=of.y, w=of.length, h=of.width, waste=True,
                            business=bool(of.business), remnant_no=of.number or None)
                cells.append(c)
                if not of.business:
                    continue
                for cp in range(1, m.copies + 1):
                    k = rem_key(True, of.length, of.width)
                    to_wh = True
                    if taken_left.get(k, 0) > 0:
                        taken_left[k] -= 1
                        to_wh = False
                    n = len(remnants) + 1
                    remnants.append(Remnant(id=f"ATX-{number}-{n}" if number else None, n=n, material_ref=o.id,
                                            material_code=o.code, material_name=o.name, thickness=_thickness(o),
                                            sheet_no=no, sheet_copy=cp, remnant_no=of.number, length=of.length, width=of.width,
                                            raw_length=of.raw_length or of.length, raw_width=of.raw_width or of.width,
                                            to_warehouse=to_wh))
            cm.sheets.append(CutSheet(
                no=no, index=m.index, L=m.sheet_length, W=m.sheet_width, mult=m.copies, is_remnant=is_rem, remnant_id=rid,
                fill_percent=m.fill_percent, cut_length_m=m.cut_length_m, cells=cells,
                cuts=_cut_lines(m.strips, m.sheet_length, m.sheet_width) if o.type == OpType.CS else [],
                commands=[CutCommand(code=c.code, level=c.level, size=c.size, count=c.count, ref=c.ref) for c in m.commands]))
        cut_maps.append(cm)
    unbound = [p for p in parts if any(i.pattern_no is None for i in p.instances[:max(0, p.qty_total - p.qty_from_stock)])]
    if unbound:
        warns.append("Kesish xaritasida joyi yo'q nusxalar: " + ", ".join(f"{p.key} (MX ID {p.mx_uid})" for p in unbound[:10])
                     + (f" va yana {len(unbound) - 10} ta" if len(unbound) > 10 else ""))

    consumption = [Consumption(material_ref=r.get("op_id", ""), type=str(r.get("type", "")), code=str(r.get("code", "")),
                               name=str(r.get("name", "")), unit=str(r.get("unit_code", "")), qty=float(r.get("qty") or 0),
                               remnant_id=r.get("remnant_id"))
                   for r in warehouse_request(project)]

    # XNC dasturlari
    xncs: list[XncProgram] = []
    part_by_xnc: dict[str, PackagePart] = {}
    for p_ in parts:
        for x in p_.xnc_refs:
            part_by_xnc.setdefault(x, p_)
    for o in project.operations:
        if o.type != OpType.XNC or not o.xnc:
            continue
        stats: dict[str, float] = {}
        try:
            from .xnc import machine_program
            st = machine_program(o, project, "any", None).get("stats") or {}
            stats = {k: float(v) for k, v in st.items() if isinstance(v, (int, float))}
        except Exception as e:  # noqa: BLE001 — bitta buzuq dastur paketni to'xtatmasin
            warns.append(f"XNC «{o.code or o.name}»: dastur hisoblanmadi ({e})")
        lp = part_by_xnc.get(o.id)
        xncs.append(XncProgram(mx_op_id=o.id, code=o.code, name=o.name, qty=o.xnc.qty, part_uid=lp.mx_uid if lp else None,
                               part_key=lp.key if lp else None, stats=stats))

    pkg = MesPackageV1(package=PackageMeta(generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
                       source=src, products=products, materials=materials, edge_bands=edge_bands, parts=parts,
                       sheets=list(sheets.values()), cut_maps=cut_maps, remnants=remnants, consumption=consumption,
                       xnc_programs=xncs, xnc_tools=_xnc_tools(project, warns), warnings=warns)

    # postprotsessor fayllari — faqat ochilgan stanoklar
    keys = _select_machines(pp)
    pkg.postprocessor_files = _pp_files(project, keys, files, warns, part_by_xnc, MACHINE_BY_KEY,
                                        lambda k: pp_label(k, LANG.get()))
    total = sum(f.size for f in pkg.postprocessor_files)
    if files == "inline" and total > MAX_INLINE_BYTES:
        raise HTTPException(400, _("mes_pkg_too_big", n=round(total / 1048576, 1)))
    pkg.machining = Machining(saw_ready=any(f.machine.group == "saw" for f in pkg.postprocessor_files),
                              cnc_ready=any(f.machine.group == "cnc" for f in pkg.postprocessor_files),
                              files=len(pkg.postprocessor_files))
    return pkg


def _select_machines(pp: str) -> list[str]:
    """Paketga kiradigan stanoklar. Yopiq stanok hech qachon kirmaydi: aniq so'ralsa — 403."""
    from . import pp_access
    from .postprocessors import MACHINE_BY_KEY, MACHINES
    opened = pp_access.open_keys()
    v = (pp or "enabled").strip()
    if v == "none":
        return []
    if v in ("enabled", "all"):
        from . import settings
        en = {k for k, x in ((settings.get_default("pp_machines") or {}).get("enabled") or {}).items() if x}
        return [k for k, _n, _g in MACHINES if pp_access.usable(k, opened) and (v == "all" or k in en)]
    out: list[str] = []
    for raw in v.split(","):
        k = raw.strip()
        k = k.split(":", 1)[1] if k.startswith("machine:") else k
        if not k:
            continue
        if k not in MACHINE_BY_KEY:
            raise HTTPException(400, _("pp_machine_unknown", k=k[:60]))
        pp_access.require_open(k)
        if k not in out:
            out.append(k)
    return out


def _pp_files(project: Project, keys: list[str], files: str, warns: list[str], part_by_xnc: dict, machine_by_key: dict,
              label) -> list[PostprocessorFile]:
    from . import pp_access, ppfmt, settings
    from .postprocessors import _safe_name, render_template, render_template_xnc, template_kind
    cfg = settings.get_default("pp_machines") or {}
    enabled = {k for k, v in (cfg.get("enabled") or {}).items() if v}
    bound = {k: v for k, v in (cfg.get("profile") or {}).items() if v is not None}
    prefix = bool(cfg.get("prefix", False))
    native = ppfmt.load_all()
    out: list[PostprocessorFile] = []
    for mk in keys:
        name, grp = machine_by_key[mk]
        if not pp_access.usable(mk):
            warns.append(f"«{label(mk)}» postprotsessori sozlanmagan (o'rnatilgan format yo'q yoki shablon/stanok o'chiq) — fayl yo'q")
            continue
        mref = MachineRef(key=mk, name=name, label=label(mk), group=grp)
        prof = None
        if mk in bound:
            pr = settings.get_profile("postprocessor", bound[mk])
            if pr is None or mk not in enabled:
                warns.append(f"«{label(mk)}»: shablon topilmadi yoki stanok o'chiq — fayl yo'q")
                continue
            prof = PostprocessorProfile.model_validate(pr["data"])
            kind = template_kind(prof.template)
            if (grp == "saw" and kind == "xnc") or (grp == "cnc" and kind == "saw"):
                warns.append(f"«{label(mk)}»: shablon boshqa stanok turi uchun — fayl yo'q")
                continue
        elif mk not in native or native[mk].group != grp:
            continue
        if grp == "saw":
            targets = [o for o in project.operations if o.type == OpType.CS and o.result and o.result.maps]
        else:
            targets = [o for o in project.operations if o.type == OpType.XNC and o.xnc]
        for o in targets:
            try:
                if grp == "saw":
                    fname, data, mime = render_template(prof, project, o, mk) if prof else ppfmt.run_saw(mk, project, o)
                else:
                    if prof:
                        from .xnc_constraints import load as cons_load
                        fname, data, mime = render_template_xnc(prof, project, o, "any", mk, constraints=cons_load())
                    else:
                        fname, data, mime = ppfmt.run_cnc(mk, project, o, "any")
            except Exception as e:  # noqa: BLE001 — format cheklovi / shablon xatosi: paket qoladi, fayl yo'q
                warns.append(f"«{label(mk)}» / «{o.code or o.name}»: fayl chiqmadi ({str(e)[:200]})")
                continue
            if prefix:
                fname = f"{_safe_name(name, 'machine', 30)}_{fname}"
            lp = part_by_xnc.get(o.id) if grp == "cnc" else None
            url = (f"/api/projects/{project.id}/operations/{o.id}/postprocess?key=machine:{mk}"
                   + ("&refit=copy" if grp == "saw" else ""))
            out.append(PostprocessorFile(format_id=f"machine:{mk}", machine=mref, source="template" if prof else "native",
                                         op_ref=o.id, part_keys=[lp.key] if lp else [], file_name=fname, media_type=mime,
                                         size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                                         content_base64=_b64(data) if files == "inline" else None,
                                         url=url if files == "meta" else None))
    return out


def _xnc_tools(project: Project, warns: list[str]) -> XncToolSummary:
    """Asbob bo'yicha XNC ishi (services/xnc_tool_stats.py); hisoblab bo'lmasa — bo'sh + ogohlantirish."""
    try:
        from .xnc_mes import mes_view
        from .xnc_tool_stats import project_tool_summary
        return XncToolSummary.model_validate(mes_view(project_tool_summary(project)))
    except Exception as e:  # noqa: BLE001
        warns.append(f"XNC asboblar ishi hisoblanmadi ({e})")
        return XncToolSummary()
