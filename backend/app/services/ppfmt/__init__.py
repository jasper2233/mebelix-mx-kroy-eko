"""O'rnatilgan stanok formatlari (postprotsessorlar) — korxona namunalaridan o'rganilgan formatlar (docs/mebelix/postprocessors/).

Har format — alohida modul (`ppfmt/<nom>.py`) va `@register(...)` bilan ro'yxatga olinadi:
  * group="saw" — pil markazi: CS kroy natijasidan fayl(lar). Generator: fn(job: SawJob) -> list[(fayl_nomi, bytes)]
  * group="cnc" — ishlov markazi (prisadka): bitta XNC dasturdan fayl. Generator: fn(job: DrillJob) -> list[(nom, bytes)]
    `batch` (ixtiyoriy): fn(jobs: list[DrillJob], project) -> list[(nom, bytes)] — loyihaning barcha XNC lari birga
    (masalan bir faylda bir nechta dastur); berilmasa har dastur alohida fayl.
Bir nechta fayl chiqsa — zip. Formatlar faqat toza ma'lumot (SawJob / DrillJob) bilan ishlaydi.
"""
from __future__ import annotations

import importlib
import io
import pkgutil
import re
import zipfile
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ...models import OpType, Operation, Project

Files = list[tuple[str, bytes]]


@dataclass
class Fmt:
    key: str                 # postprocessors.MACHINES dagi kalit (machine:<key>)
    name: str
    group: str               # saw | cnc
    ext: str
    fn: Callable[..., Files]
    batch: Optional[Callable[..., Files]] = None
    note: str = ""           # foydalanuvchiga: cheklovlar / ochiq savollar


REGISTRY: dict[str, Fmt] = {}


def register(key: str, name: str, group: str, ext: str, note: str = "", batch: Optional[Callable[..., Files]] = None):
    def deco(fn):
        REGISTRY[key] = Fmt(key, name, group, ext, fn, batch, note)
        return fn
    return deco


def set_batch(key: str):
    def deco(fn):
        REGISTRY[key].batch = fn
        return fn
    return deco


_loaded = False


def load_all() -> dict[str, Fmt]:
    """Barcha `ppfmt/*.py` modullarini yuklaydi (registratsiya uchun)."""
    global _loaded
    if not _loaded:
        _loaded = True
        for m in pkgutil.iter_modules(__path__):
            if not m.name.startswith("_"):
                try:
                    importlib.import_module(f"{__name__}.{m.name}")
                except Exception as e:  # noqa: BLE001 — bitta buzuq format qolganlarini to'xtatmasin
                    import logging
                    logging.getLogger("mebelix.ppfmt").warning("format moduli yuklanmadi: %s (%s)", m.name, e)
    return REGISTRY


# ───────────────────────── umumiy yordamchilar ─────────────────────────
def safe_name(s: str, dflt: str = "file", n: int = 60) -> str:
    """Fayl nomi: probel va qavslar ketma-ketligi → «_» (namunalardagi kabi), taqiqlangan belgilar olib tashlanadi."""
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", s or "").strip()
    s = re.sub(r"[\s()]+", "_", s).strip("_")
    return (s or dflt)[:n]


def zip_files(files: Files) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            z.writestr(name, data)
    return buf.getvalue()


def num(v: float, nd: int = 3) -> str:
    """Son: ortiqcha nollarsiz (1830, 4.5, 0.25)."""
    r = round(float(v), nd)
    if r == int(r):
        return str(int(r))
    return f"{r:.{nd}f}".rstrip("0").rstrip(".")


def order_text(project, order_info: str = "") -> str:
    """Fayllarga yoziladigan buyurtma / loyiha nomi: **joriy loyiha nomi** (foydalanuvchi qarori, 2026-10-04 — mahsulotdagi eski
    «Данные заказа» matni emas). Mahsulot matni loyiha nomi bilan bir xil bo'lsa (faqat «_» / bo'sh joy farqi) — o'sha yozuv
    shakli saqlanadi; loyiha nomi bo'sh bo'lsa — mahsulot matni."""
    name = (getattr(project, "name", "") or "").strip()
    oi = (order_info or "").strip()
    if not name:
        return oi
    norm = lambda t: re.sub(r"[\s_]+", " ", t).strip().lower()     # noqa: E731
    return oi if oi and norm(oi) == norm(name) else name


def num_hu(v: float, nd: int = 3) -> str:
    """`num` kabi, lekin o'nlik yozuv bo'yicha «yarim — yuqoriga» yaxlitlash (240.6865 → 240.687; float `round` 240.686 beradi)."""
    from decimal import ROUND_HALF_UP, Decimal
    d = Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    t = format(d, "f")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return "0" if t in ("-0", "") else t


# ───────────────────────── arra (CS) ─────────────────────────
@dataclass
class SawPart:
    uid: int
    name: str
    code: str
    length: float            # kroy o'lchami (op_part: pilniy) — namunalarda loyiha l/w
    width: float
    qty: int
    grain: bool
    product: str = ""
    product_code: str = ""
    edges: dict = field(default_factory=dict)     # side → {symbol, name, thickness} (top/bottom/left/right)
    xnc_face: str = ""       # lits tomoni XNC dastur kodi
    xnc_back: str = ""       # orqa tomoni XNC dastur kodi
    has_mill: bool = False
    has_drill: bool = False
    description: str = ""


@dataclass
class SawNode:
    """Kesish daraxti tuguni (list koordinatalarida, mm): kind C — kesim guruhi (axis x|y — bolalar shu o'q bo'ylab
    ketma-ket), P — detal (uid, rotated), W — chiqindi / qoldiq (rem — qoldiq raqami, 0 — chiqindi)."""
    x: float
    y: float
    l: float
    w: float
    kind: str
    axis: str = ""
    level: int = 0
    children: list["SawNode"] = field(default_factory=list)
    uid: int = 0
    rotated: bool = False
    rem: int = 0


@dataclass
class SawMap:
    index: int
    copies: int
    sheet_length: float
    sheet_width: float
    is_remnant: bool
    sheet_id: str
    tree: Optional[SawNode]
    placements: list[dict]
    offcuts: list[dict]          # {number, x, y, length, width, raw_length, raw_width, business, kind}
    commands: list[dict]
    fill: float = 0.0
    cut_length_m: float = 0.0
    trim_length: float = 0.0     # shu karta uchun torsovka (map → list → operatsiya)
    trim_width: float = 0.0


@dataclass
class SawJob:
    project: Project
    op: Operation
    order: str                   # buyurtma raqami (project.number)
    project_name: str
    customer: str
    material_name: str
    material_code: str
    thickness: float
    kerf: float
    trim_length: float
    trim_width: float
    pack_height: float
    max_rotations: int
    parts: list[SawPart]
    maps: list[SawMap]
    stock: list[dict]            # {id, length, width, qty, is_remnant}
    params: dict[str, Any]       # stanok sozlamalari («Настройки → Постпроцессоры», ParamGrid)
    order_date: str = ""
    ready_date: str = ""

    def part(self, uid: int) -> Optional[SawPart]:
        for p in self.parts:
            if p.uid == uid:
                return p
        return None

    @property
    def base_name(self) -> str:
        """`<buyurtma>_<loyiha>_<material>` (namunalardagi nomlash)."""
        # buyurtma raqami nom boshida bo'lsa (import qilingan «3161_…») yoki raqam yo'q (0) bo'lsa — takrorlanmaydi
        head = self.project_name if (self.order in ("", "0") or self.project_name.strip().startswith(self.order))             else f"{self.order}_{self.project_name}"
        return safe_name(f"{head}_{self.material_name}", "kroy", 80)


def _node(d: dict, level: int = 0) -> SawNode:
    n = SawNode(x=d.get("x", 0.0), y=d.get("y", 0.0), l=d.get("l", 0.0), w=d.get("w", 0.0), kind=d.get("k", "W"),
                axis=d.get("a", ""), level=level, uid=d.get("u", 0), rotated=bool(d.get("o")), rem=d.get("r", 0))
    n.children = [_node(c, level + 1) for c in d.get("c", [])]
    return n


def saw_job(project: Project, op: Operation, machine_key: Optional[str] = None) -> SawJob:
    from ..calc import op_part, total_qty
    from ..render import part_edges
    from ..calc import edge_map
    params: dict[str, Any] = {}
    if machine_key:
        try:
            from ..pp_machine_ctx import get_params
            params = get_params(machine_key)
        except Exception:      # noqa: BLE001 — sozlama sxemasi bo'lmasa standartlar
            params = {}
    emap = edge_map(project)
    xnc_by_id = {o.id: o for o in project.operations if o.type == OpType.XNC}
    prods = {p.id: p for p in project.products}
    parts: list[SawPart] = []
    for p in op.parts:
        ed = {}
        for side, e in part_edges(p, project).items():
            if not e:
                continue
            el = emap.get(getattr(p, f"edge_{side}").op_id)
            ed[side] = dict(symbol=e.get("symbol", ""), name=e.get("name", ""), thickness=el.thickness if el else 0.0)
        face = back = ""
        mill = drill = False
        for xid in p.xnc_op_ids:
            xo = xnc_by_id.get(xid)
            if not xo or not xo.xnc:
                continue
            if xo.xnc.face_side:
                face = face or xo.code
            else:
                back = back or xo.code
            stack = list(xo.xnc.program)
            while stack:                      # ichma-ich buyruqlar ham (IF / WHILE / Sub bloklari)
                c = stack.pop()
                if not c.enabled:
                    continue
                nm = str(getattr(c.cmd, "value", c.cmd)).lower()
                if nm.startswith("mill"):
                    mill = True
                elif nm.startswith("drill"):
                    drill = True
                stack.extend(c.children)
        pr = prods.get(p.product_id or "")
        q = op_part(op, p)
        parts.append(SawPart(uid=p.uid, name=p.name, code=p.code, length=q.length, width=q.width,
                             qty=total_qty(project, p), grain=p.grain, product=pr.name if pr else "",
                             product_code=pr.code if pr else "", edges=ed, xnc_face=face, xnc_back=back,
                             has_mill=mill, has_drill=drill, description=p.description))
    cut = op.cs_cut
    mat = op.cs_material
    res = op.result
    stock_by = {s.id: s for s in op.sheets}
    maps: list[SawMap] = []
    for m in (res.maps if res else []):
        st = stock_by.get(m.sheet_id)
        tl = m.trim_length if m.trim_length is not None else (getattr(st, "trim_length", None) if st else None)
        tw = m.trim_width if m.trim_width is not None else (getattr(st, "trim_width", None) if st else None)
        maps.append(SawMap(
            index=m.index, copies=m.copies, sheet_length=m.sheet_length, sheet_width=m.sheet_width,
            is_remnant=m.is_remnant, sheet_id=m.sheet_id, tree=_node(m.strips[0]) if m.strips else None,
            placements=[pl.model_dump() for pl in m.placements],
            offcuts=[o.model_dump() for o in m.offcuts], commands=[c.model_dump() for c in m.commands],
            fill=m.fill_percent, cut_length_m=m.cut_length_m,
            trim_length=float(tl if tl is not None else (cut.trim_length if cut else 0)),
            trim_width=float(tw if tw is not None else (cut.trim_width if cut else 0))))
    stock = [dict(id=s.id, length=s.length, width=s.width, qty=s.qty, is_remnant=bool(getattr(s, "is_remnant", False)))
             for s in op.sheets]
    return SawJob(project=project, op=op, order=str(project.number), project_name=project.name,
                  customer=project.customer or "", material_name=op.name or op.code or "material",
                  material_code=op.code or "", thickness=mat.thickness if mat else 0.0,
                  kerf=cut.kerf if cut else 0.0, trim_length=cut.trim_length if cut else 0.0,
                  trim_width=cut.trim_width if cut else 0.0, pack_height=getattr(cut, "pack_height", 0) or 0,
                  max_rotations=getattr(cut, "max_rotations", 4) if cut else 4,
                  parts=parts, maps=maps, stock=stock, params=params,
                  order_date=str(project.order_date), ready_date=str(project.ready_date))


# ───────────────────────── ishlov markazi (XNC) ─────────────────────────
@dataclass
class DrillJob:
    project: Project
    op: Operation
    order: str
    code: str                    # XNC dastur kodi (fayl nomi)
    name: str
    dx: float                    # zagotovka o'lchami (burishdan oldin)
    dy: float
    dz: float
    face: bool                   # True — lits tomoni, False — orqa
    prog: dict                   # services.xnc.machine_program natijasi (ops, tools, size …)
    ctx: dict                    # postprocessors.context_xnc (edges, part, …)
    params: dict[str, Any]
    raw: list[dict] = field(default_factory=list)   # hisoblangan xom buyruqlar (koordinata boshi/burishsiz): services.xnc.evaluate
    machine: str = ""            # stanok kaliti (asboblar jadvali standartlari uchun — ppfmt/tooling.py)


def drill_job(project: Project, op: Operation, machine_key: Optional[str] = None, long_side: str = "any") -> DrillJob:
    from ..postprocessors import context_xnc
    from .. import xnc as X
    params: dict[str, Any] = {}
    if machine_key:
        try:
            from ..pp_machine_ctx import get_params, get_tools
            params = dict(get_params(machine_key))
            params["tools"] = get_tools(machine_key)      # «Инструменты» jadvali: kalit → raqam / nom (ppfmt/tooling.py)
        except Exception:      # noqa: BLE001
            params = {}
    ctx = context_xnc(project, op, long_side)
    x = op.xnc
    try:
        raw = X.evaluate(x.program, x.length, x.width, x.thickness, X.program_vars(x), x.par_values)
        raw_ops = [dict(o) if isinstance(o, dict) else o for o in getattr(raw, "ops", raw)]
    except Exception:          # noqa: BLE001 — xom ro'yxat ixtiyoriy
        raw_ops = []
    xc = ctx["xnc"]
    return DrillJob(project=project, op=op, order=str(project.number), code=op.code or op.name or "xnc",
                    name=op.name or "", dx=x.length, dy=x.width, dz=x.thickness, face=bool(x.face_side),
                    prog={k: xc.get(k) for k in ("ops", "tools", "size", "extra_turn", "stats", "errors", "warnings")},
                    ctx=ctx, params=params, raw=raw_ops, machine=machine_key or "")


# ───────────────────────── ishga tushirish ─────────────────────────
def available(key: str) -> bool:
    return key in load_all()


class FormatError(ValueError):
    """Format cheklovi (masalan stanok qo'llamaydigan kesim darajasi) — foydalanuvchiga 400 xabar sifatida chiqadi."""


# «Макс. количество вращений» chegarasi (stanok formati shundan chuqur kesim daraxtini qo'llamaydi). Loyiha sozlamasi
# kattaroq bo'lsa — kroy shu chegara bilan qayta bajariladi (`main.postprocess`), keyin fayl chiqariladi.
ROT_LIMIT: dict[str, int] = {"fastpanel": 3, "scheer": 3, "giben_gdrive": 3, "holzma_cadmatic3": 4, "homag_chf": 4,
                             "kdt_ks33x": 4, "kdt_presize_qk": 4, "homag": 5}


def rot_limit(key: str, params: Optional[dict] = None) -> Optional[int]:
    """Stanok formati ruxsat etadigan burilishlar soni (versiyaga bog'liq bo'lishi mumkin: FastPanel 2.1.4 — 2, 2.1.5 — 3)."""
    if key == "fastpanel" and str((params or {}).get("version", "")).strip() == "2.1.4":
        return 2
    return ROT_LIMIT.get(key)


def run_saw(key: str, project: Project, op: Operation) -> tuple[str, bytes, str]:
    fmt = load_all()[key]
    job = saw_job(project, op, key)
    try:
        files = fmt.fn(job)
    except ValueError as e:
        raise FormatError(f"{fmt.name}: {e}") from e
    return _pack(files, job.base_name)


def run_cnc(key: str, project: Project, op: Operation, long_side: str = "any") -> tuple[str, bytes, str]:
    fmt = load_all()[key]
    job = drill_job(project, op, key, long_side)
    try:
        files = fmt.batch([job], project) if fmt.batch else fmt.fn(job)
    except ValueError as e:
        raise FormatError(f"{fmt.name}: {e}") from e
    return _pack(files, safe_name(f"{project.number}_{job.code}", "xnc"))


def run_cnc_project(key: str, project: Project, long_side: str = "any",
                    only: Optional[set[str]] = None) -> tuple[str, bytes, str]:
    """Loyihaning barcha XNC dasturlari bitta paketda (namunalardagi kabi: buyurtma bo'yicha zip). `only` — faqat shu
    operatsiyalar (oynada belgilanganlar)."""
    fmt = load_all()[key]
    jobs = [drill_job(project, o, key, long_side) for o in project.operations
            if o.type == OpType.XNC and o.xnc and (o.id in only if only is not None else o.print)]
    if not jobs:
        raise FormatError(f"{fmt.name}: XNC dasturlari tanlanmagan")
    try:
        files: Files = fmt.batch(jobs, project) if fmt.batch else [f for j in jobs for f in fmt.fn(j)]
    except ValueError as e:
        raise FormatError(f"{fmt.name}: {e}") from e
    files = _dedupe(files)
    return f"{safe_name(f'{project.number}_{project.name}', 'xnc')}.zip", zip_files(files), "application/zip"


def _dedupe(files: Files) -> Files:
    """Bir xil fayl nomlari: «nom (1).ext», «nom (2).ext» (namunalardagi kabi)."""
    seen: dict[str, int] = {}
    out: Files = []
    for name, data in files:
        if name in seen:
            seen[name] += 1
            stem, dot, ext = name.rpartition(".")
            name = f"{stem} ({seen[name]}).{ext}" if dot else f"{name} ({seen[name]})"
        else:
            seen[name] = 0
        out.append((name, data))
    return out


def _pack(files: Files, base: str) -> tuple[str, bytes, str]:
    files = _dedupe(files)
    if len(files) == 1:
        return files[0][0], files[0][1], "application/octet-stream"
    return f"{base}.zip", zip_files(files), "application/zip"
