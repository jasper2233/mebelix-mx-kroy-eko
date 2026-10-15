"""(CN) Nesting geometriyasi (W16): detal konturi, aylantirish, ofset, shakl chegaralari.

Detal shakli (`Shape`): tashqi kontur + ichki konturlar (teshik / kesim), hammasi o'z koordinatalarida (bbox burchagi (0, 0), X o'ngga, Y pastga, mm).
Manba: (1) detalga bog'langan XNC dasturining YOPIQ, «teshib o'tuvchi» freza konturlari (`MillStart … Mill*`, `MillRect`, `MillEllipse`),
(2) bo'lmasa — oddiy to'rtburchak L × W. Yoylar siniq chiziqqa `arc_tol` xato bilan (inscribed — chiziq yoyning ichida) yaqinlashtiriladi;
nesting bu xatoni masofa zaxirasi (`arc_tol`) sifatida hisobga oladi (`cn_nest`).

Konturlar orientatsiyasi: tashqi — musbat (shoelace), ichki — manfiy; tashqi normal (dy, −dx)/len har doim materialdan CHIQQAN tomonga qaraydi.
Burchak: musbat — ekranda soat mili bo'yicha (Y pastga), XNC «Поворот» kabi.

Qaror konstantalari (hammasi shu faylning boshida; T_W16_CN.md §2):
  OUTLINE_COVER     — yopiq kontur detal tashqi konturi bo'lishi uchun detal o'lchamining kamida shu ulushini egallashi kerak;
  CLOSE_TOL         — kontur «yopiq» deb hisoblanadigan boshi-oxiri masofasi (mm);
  THROUGH_TOL       — chuqurlik ≥ qalinlik − THROUGH_TOL bo'lsa kontur «teshib o'tadi» (aks holda cho'ntak: shaklga ta'sir qilmaydi).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

Pt = tuple[float, float]
Ring = list[Pt]

OUTLINE_COVER = 0.90
CLOSE_TOL = 0.10
THROUGH_TOL = 0.50
MAX_POINTS = 600            # bitta kontur nuqtalari chegarasi (oshsa — soddalashtiriladi)
MAX_RINGS = 200             # bitta detaldagi ichki konturlar chegarasi
MAX_SHAPE_POINTS = 3000     # bitta detal shaklidagi nuqtalar yig'indisi chegarasi (oshsa — soddalashtirish, keyin to'rtburchak)
MIN_RING_AREA = 1e-3        # mm²: bundan kichik kontur «nol»


# ───────────────────────── Asosiy amallar ─────────────────────────
def signed_area(r: Ring) -> float:
    """Shoelace imzoli maydon (musbat — (0,0)→(L,0)→(L,W)→(0,W) tartibi)."""
    n = len(r)
    if n < 3:
        return 0.0
    a = np.asarray(r, dtype=float)
    x, y = a[:, 0], a[:, 1]
    return float(0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def ring_area(r: Ring) -> float:
    return abs(signed_area(r))


def ring_perimeter(r: Ring) -> float:
    if len(r) < 2:
        return 0.0
    a = np.asarray(r, dtype=float)
    d = np.roll(a, -1, axis=0) - a
    return float(np.sum(np.hypot(d[:, 0], d[:, 1])))


def ring_bbox(r: Ring) -> tuple[float, float, float, float]:
    a = np.asarray(r, dtype=float)
    return float(a[:, 0].min()), float(a[:, 1].min()), float(a[:, 0].max()), float(a[:, 1].max())


def rect_ring(length: float, width: float) -> Ring:
    return [(0.0, 0.0), (float(length), 0.0), (float(length), float(width)), (0.0, float(width))]


def clean_ring(r: Ring, eps: float = 1e-9) -> Ring:
    """Ketma-ket takror nuqtalar va yopuvchi (birinchisiga teng) nuqta olib tashlanadi."""
    out: Ring = []
    for p in r:
        p = (float(p[0]), float(p[1]))
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append(p)
    while len(out) > 1 and abs(out[0][0] - out[-1][0]) <= eps and abs(out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


def orient_ring(r: Ring, positive: bool = True) -> Ring:
    """Konturni kerakli orientatsiyaga keltiradi (musbat / manfiy shoelace imzosi)."""
    return r if (signed_area(r) >= 0) == positive else r[::-1]


def rot_cs(angle_deg: float) -> tuple[float, float]:
    """cos / sin; 90° ning karralilarida aniq 0 / ±1 (hisob shovqini yo'q)."""
    a = angle_deg % 360.0
    for k, (c, s) in enumerate(((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0))):
        if abs(a - 90.0 * k) < 1e-12 or abs(a - 90.0 * k - 360.0) < 1e-12:
            return c, s
    r = math.radians(a)
    return math.cos(r), math.sin(r)


def transform_ring(r: Ring, angle_deg: float, tx: float = 0.0, ty: float = 0.0) -> Ring:
    """Burish (koordinata boshi atrofida; musbat — ekranda soat mili bo'yicha) + siljitish."""
    c, s = rot_cs(angle_deg)
    return [(c * x - s * y + tx, s * x + c * y + ty) for x, y in r]


def point_in_ring(p: Pt, r: Ring) -> bool:
    """Just-even-odd; chegaradagi nuqta uchun natija aniqlanmagan (chaqiruvchilar chegara holatini alohida tekshiradi)."""
    x, y = p
    inside = False
    n = len(r)
    j = n - 1
    for i in range(n):
        xi, yi = r[i]
        xj, yj = r[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _dp(pts: np.ndarray, lo: int, hi: int, tol: float, keep: np.ndarray) -> None:
    """Douglas–Peucker (iterativ): pts[lo..hi] oralig'i."""
    stack = [(lo, hi)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        p, q = pts[a], pts[b]
        seg = pts[a + 1:b]
        d = q - p
        ln = math.hypot(d[0], d[1])
        if ln < 1e-12:
            dist = np.hypot(seg[:, 0] - p[0], seg[:, 1] - p[1])
        else:
            dist = np.abs(d[0] * (seg[:, 1] - p[1]) - d[1] * (seg[:, 0] - p[0])) / ln
        k = int(np.argmax(dist))
        if dist[k] > tol:
            m = a + 1 + k
            keep[m] = True
            stack.append((a, m))
            stack.append((m, b))


def simplify_ring(r: Ring, tol: float) -> Ring:
    """Yopiq konturni soddalashtirish (Douglas–Peucker; chetlanish ≤ tol). Kamida 3 nuqta qoladi."""
    r = clean_ring(r)
    n = len(r)
    if n <= 3 or tol <= 0:
        return r
    pts = np.asarray(r, dtype=float)
    far = int(np.argmax(np.hypot(pts[:, 0] - pts[0, 0], pts[:, 1] - pts[0, 1])))
    keep = np.zeros(n, dtype=bool)
    keep[0] = keep[far] = True
    _dp(pts, 0, far, tol, keep)                                   # 0 … far
    ext = np.vstack([pts[far:], pts[:1]])                          # far … n−1, 0
    sub_keep = np.zeros(len(ext), dtype=bool)
    sub_keep[0] = sub_keep[-1] = True
    _dp(ext, 0, len(ext) - 1, tol, sub_keep)
    for k in range(1, len(ext) - 1):
        if sub_keep[k]:
            keep[far + k] = True
    out = [r[i] for i in range(n) if keep[i]]
    return out if len(out) >= 3 else r[:3]


def limit_points(r: Ring, max_points: int = MAX_POINTS, tol: float = 0.05) -> Ring:
    """Nuqtalar soni max_points dan oshmaguncha chetlanish chegarasini oshirib boradi (qo'pol, lekin tez)."""
    r = clean_ring(r)
    t = tol
    for _ in range(40):
        if len(r) <= max_points:
            return r
        t *= 1.6
        r = simplify_ring(r, t)
    return r


# ───────────────────────── Yoylar ─────────────────────────
def arc_points(start: Pt, center: Pt, radius: float, sweep_rad: float, clockwise: bool, tol: float,
               end: Optional[Pt] = None) -> list[Pt]:
    """Yoy nuqtalari (boshi kirmaydi, oxiri kiradi). `clockwise` — ekranda (Y pastga) soat mili bo'yicha; sweep > 0.
    Xato (vatar chuqurligi) ≤ tol. `end` berilsa oxirgi nuqta aynan shu (yopilish aniqligi)."""
    if radius <= 1e-12 or sweep_rad <= 1e-12:
        return [end] if end is not None else []
    step = 2.0 * math.acos(max(-1.0, min(1.0, 1.0 - tol / radius))) if tol < radius else math.pi / 2
    step = max(step, 1e-3)
    n = max(1, int(math.ceil(sweep_rad / step - 1e-9)))
    a0 = math.atan2(start[1] - center[1], start[0] - center[0])
    sgn = 1.0 if clockwise else -1.0
    out: list[Pt] = []
    for i in range(1, n + 1):
        a = a0 + sgn * sweep_rad * i / n
        out.append((center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)))
    if end is not None:
        out[-1] = (float(end[0]), float(end[1]))
    return out


# ───────────────────────── Shakl ─────────────────────────
@dataclass
class Shape:
    """Detal shakli: tashqi kontur (musbat) + ichki konturlar (manfiy); bbox burchagi (0, 0).
    `marks` — ishlov belgilari (etiketka o'rnini topish uchun): {"drills": [(x, y, r)], "paths": [([(x, y)…], yarim_kenglik)],
    "grooves": [(x1, y1, x2, y2, yarim_kenglik)]}, shu koordinatalarda."""
    outer: Ring
    holes: list[Ring] = field(default_factory=list)
    kind: str = "rect"                                   # rect | contour
    src: tuple[float, float] = (0.0, 0.0)                # kutilgan o'lcham (L, W) — detal / XNC
    warns: list[tuple[str, dict]] = field(default_factory=list)
    marks: dict = field(default_factory=dict)
    origin: tuple[float, float] = (0.0, 0.0)             # normallashtirishda ayrilgan siljish (XNC koordinatasi → shakl)

    @property
    def bbox_size(self) -> tuple[float, float]:
        x0, y0, x1, y1 = ring_bbox(self.outer)
        return x1 - x0, y1 - y0

    @property
    def area(self) -> float:
        """Sof maydon (tashqi − ichki kesimlar), mm²."""
        return ring_area(self.outer) - sum(ring_area(h) for h in self.holes)

    @property
    def perimeter(self) -> float:
        return ring_perimeter(self.outer) + sum(ring_perimeter(h) for h in self.holes)

    @property
    def is_rect(self) -> bool:
        return self.kind == "rect" and not self.holes

    @property
    def n_points(self) -> int:
        return len(self.outer) + sum(len(h) for h in self.holes)


def rect_shape(length: float, width: float) -> Shape:
    return Shape(outer=rect_ring(length, width), kind="rect", src=(float(length), float(width)))


@dataclass
class Oriented:
    """Aylantirilgan shakl: nuqtalar [0, bw] × [0, bh] ichida; `ox, oy` — aylantirilgan nuqtalarga qo'shilgan siljish."""
    angle: float
    outer: Ring
    holes: list[Ring]
    bw: float
    bh: float
    ox: float
    oy: float


def orient_shape(shape: Shape, angle: float) -> Oriented:
    """Shaklni `angle` ga burib, bbox burchagini (0, 0) ga keltiradi. Joylashtirishda: list nuqtasi = lokal + (x, y)."""
    c, s = rot_cs(angle)
    rot = [[(c * px - s * py, s * px + c * py) for px, py in ring] for ring in [shape.outer, *shape.holes]]
    xs = [p[0] for p in rot[0]]
    ys = [p[1] for p in rot[0]]
    x0, y0 = min(xs), min(ys)
    ox, oy = -x0, -y0
    outer = [(px + ox, py + oy) for px, py in rot[0]]
    holes = [[(px + ox, py + oy) for px, py in ring] for ring in rot[1:]]
    return Oriented(angle=angle % 360.0, outer=outer, holes=holes, bw=max(xs) - x0, bh=max(ys) - y0, ox=ox, oy=oy)


def place_shape(shape: Shape, angle: float, x: float, y: float) -> tuple[Ring, list[Ring], float, float]:
    """Shaklni list koordinatalariga qo'yish: (tashqi, ichki konturlar, bbox eni, bbox bo'yi); (x, y) — aylantirilgan shakl
    o'rovchi to'rtburchagining chap-yuqori burchagi."""
    o = orient_shape(shape, angle)
    return ([(px + x, py + y) for px, py in o.outer], [[(px + x, py + y) for px, py in h] for h in o.holes], o.bw, o.bh)


# ───────────────────────── XNC dasturidan kontur ─────────────────────────
@dataclass
class Contour:
    ring: Ring
    closed: bool
    through: bool
    source: str = "mill"                                 # mill | rect | ellipse
    depth: float = 0.0


def _contours_from_ops(ops: list[dict], thickness: float, tol: float) -> tuple[list[Contour], dict]:
    """`xnc.machine_program` amallaridan (jismoniy koordinatalar) konturlar va ishlov belgilari."""
    out: list[Contour] = []
    marks: dict = {"drills": [], "paths": [], "grooves": []}
    cur: Optional[dict] = None

    def finish():
        nonlocal cur
        if cur is None:
            return
        pts = cur["pts"]
        closed = len(pts) >= 3 and math.dist(pts[0], pts[-1]) <= CLOSE_TOL
        ring = clean_ring(pts)
        depth = max(cur["depths"]) if cur["depths"] else thickness
        through = (not cur["pocket"]) and depth >= thickness - THROUGH_TOL
        if len(ring) >= 2:
            out.append(Contour(ring, closed and len(ring) >= 3, through, "mill", depth))
            marks["paths"].append((list(pts), max(cur.get("d", 0.0) / 2, 1.0)))
        cur = None

    for o in ops:
        k = o.get("kind")
        if k == "mill_start":
            finish()
            if o.get("ok", True) is False:
                continue
            cur = {"pts": [(o["x"], o["y"])], "depths": [o.get("depth") or thickness], "pocket": bool(o.get("pocket")),
                   "d": float(o.get("d") or 0.0)}
        elif k == "mill_line" and cur is not None:
            cur["pts"].append((o["x"], o["y"]))
            cur["depths"].append(o.get("depth") or thickness)
        elif k == "mill_arc" and cur is not None:
            start = cur["pts"][-1]
            cen = (o["cx"], o["cy"])
            r = o.get("radius") or math.dist(start, cen)
            sweep = math.radians(o.get("angle") or 0.0)
            cur["pts"].extend(arc_points(start, cen, r, sweep, bool(o.get("clockwise")), tol, end=(o["x"], o["y"])))
            cur["depths"].append(o.get("depth") or thickness)
        else:
            finish()
            if k == "drill":
                if o.get("face") == "front" and o.get("d"):
                    marks["drills"].append((o["x"], o["y"], float(o["d"]) / 2))
            elif k == "rect":
                pts: list[Pt] = []
                for sgm in o.get("path", []):
                    if sgm["type"] == "arc" and pts:
                        r = sgm.get("radius") or math.dist(pts[-1], (sgm["cx"], sgm["cy"]))
                        a0 = math.atan2(pts[-1][1] - sgm["cy"], pts[-1][0] - sgm["cx"])
                        a1 = math.atan2(sgm["y"] - sgm["cy"], sgm["x"] - sgm["cx"])
                        sw = (a1 - a0) % (2 * math.pi) if sgm.get("clockwise") else (a0 - a1) % (2 * math.pi)
                        if sw < 1e-9:
                            sw = 2 * math.pi
                        pts.extend(arc_points(pts[-1], (sgm["cx"], sgm["cy"]), r, sw, bool(sgm.get("clockwise")), tol,
                                              end=(sgm["x"], sgm["y"])))
                    else:
                        pts.append((sgm["x"], sgm["y"]))
                ring = clean_ring(pts)
                if len(ring) >= 3:
                    depth = o.get("depth") or thickness
                    through = (not o.get("pocket")) and depth >= thickness - THROUGH_TOL
                    out.append(Contour(ring, True, through, "rect", depth))
                    marks["paths"].append((ring + [ring[0]], max(float(o.get("d") or 0.0) / 2, 1.0)))
            elif k == "ellipse":
                ring = clean_ring([(q["x"], q["y"]) for q in o.get("path", [])])
                if len(ring) >= 3:
                    ring = simplify_ring(ring, tol)
                    depth = o.get("depth") or thickness
                    through = (not o.get("pocket")) and depth >= thickness - THROUGH_TOL
                    out.append(Contour(ring, True, through, "ellipse", depth))
                    marks["paths"].append((ring + [ring[0]], max(float(o.get("d") or 0.0) / 2, 1.0)))
            elif k == "groove":
                marks["grooves"].append((o["x1"], o["y1"], o["x2"], o["y2"], max(float(o.get("width") or 0.0) / 2, 1.0)))
    finish()
    return out, marks


def xnc_contours(project, xop, tol: float) -> tuple[list[Contour], dict, tuple[float, float]]:
    """XNC operatsiyasi konturlari (burilmagan, jismoniy chap-yuqori koordinatalarda), ishlov belgilari va (L, W) o'lcham."""
    from . import xnc as X
    x = xop.xnc
    op2 = xop if not x.rotation else xop.model_copy(update={"xnc": x.model_copy(update={"rotation": 0})})
    prog = X.machine_program(op2, project)
    size = (float(prog["size"]["length"]), float(prog["size"]["width"]))
    cons, marks = _contours_from_ops(prog["ops"], float(x.thickness or 0.0), tol)
    return cons, marks, size


def shape_from_contours(contours: list[Contour], marks: dict, size: tuple[float, float], tol: float) -> Optional[Shape]:
    """Yopiq «teshib o'tuvchi» konturlardan shakl: eng katta (o'lchamning ≥ 90 % ini egallovchi) kontur — tashqi chegara,
    uning ichidagilari — ichki kesimlar; tashqi chegara bo'lmasa — to'rtburchak size, konturlar uning ichidagi kesimlar.
    Hech qanday yopiq teshuvchi kontur bo'lmasa — None (oddiy to'rtburchak)."""
    L, W = size
    warns: list[tuple[str, dict]] = []
    closed = [c for c in contours if c.closed and c.through and ring_area(c.ring) > MIN_RING_AREA]
    for c in contours:
        if not c.closed and c.through and len(c.ring) >= 2:
            warns.append(("cn.w_open_contour", {}))
    if not closed:
        return None
    rings: list[Ring] = []
    for c in closed:
        r0 = simplify_ring(c.ring, tol * 0.05)
        r1 = limit_points(r0)
        if len(r1) < len(r0) and abs(ring_area(r1) - ring_area(r0)) > 0.01 * max(ring_area(r0), 1.0):
            # nuqtalar chegarasiga sig'dirish shaklni sezilarli buzadi (> 1 % maydon) — to'rtburchak (xavfsiz o'rovchi)
            warns.append(("cn.w_complex_rect", dict(n=len(r0), max=MAX_POINTS)))
            r = rect_shape(L, W)
            r.warns = warns
            r.marks = marks
            return r
        rings.append(r1)
    cover = []
    for r in rings:
        x0, y0, x1, y1 = ring_bbox(r)
        cover.append((x1 - x0) >= OUTLINE_COVER * L - 1e-9 and (y1 - y0) >= OUTLINE_COVER * W - 1e-9)
    cands = [(ring_area(r), i) for i, r in enumerate(rings) if cover[i]]
    if cands:
        oi = max(cands)[1]
        outer = orient_ring(rings[oi], True)
        inner = [r for i, r in enumerate(rings) if i != oi]
        kind = "contour"
    else:
        outer = rect_ring(L, W)
        inner = list(rings)
        kind = "rect"
    holes: list[Ring] = []
    for r in inner:
        if sum(1 for p in r if point_in_ring(p, outer)) * 2 >= len(r):        # ko'pchilik nuqtalari tashqi kontur ichida
            holes.append(orient_ring(r, False))
        else:
            warns.append(("cn.w_contour_outside", {}))
    if not holes and kind == "rect":
        return None
    if len(holes) > MAX_RINGS:
        warns.append(("cn.w_complex", dict(n=len(holes), max=MAX_RINGS)))
        holes = holes[:MAX_RINGS]
    # umumiy murakkablik chegarasi: nuqtalar yig'indisi MAX_SHAPE_POINTS dan oshsa — halqalar qo'pol soddalashtiriladi (tol ortadi);
    # baribir oshsa — detal to'rtburchak sifatida joylanadi (nesting vaqti chegaralangan bo'lishi uchun)
    total = len(outer) + sum(len(h) for h in holes)
    tol_up = tol
    while total > MAX_SHAPE_POINTS and tol_up < 20 * tol:
        tol_up *= 1.8
        outer = simplify_ring(outer, tol_up)
        holes = [simplify_ring(h, tol_up) for h in holes]
        total = len(outer) + sum(len(h) for h in holes)
    if total > MAX_SHAPE_POINTS:
        warns.append(("cn.w_complex_rect", dict(n=total, max=MAX_SHAPE_POINTS)))
        r = rect_shape(L, W)
        r.warns = warns
        r.marks = marks
        return r
    # normallashtirish: tashqi kontur bbox burchagi (0, 0)
    x0, y0, _x1, _y1 = ring_bbox(outer)
    sh = lambda ring: [(px - x0, py - y0) for px, py in ring]
    out_n = sh(outer)
    holes_n = [sh(h) for h in holes]
    mk = {"drills": [(a - x0, b - y0, r) for a, b, r in marks.get("drills", [])],
          "paths": [([(a - x0, b - y0) for a, b in pts], hw) for pts, hw in marks.get("paths", [])],
          "grooves": [(a - x0, b - y0, c - x0, d - y0, hw) for a, b, c, d, hw in marks.get("grooves", [])]}
    return Shape(outer=out_n, holes=holes_n, kind="contour" if (kind == "contour" or holes_n) else "rect", src=(L, W),
                 warns=warns, marks=mk, origin=(x0, y0))


def part_shape(project, op, part, size: tuple[float, float], use_xnc: bool, tol: float) -> Shape:
    """Detal shakli. `size` — detalning pilniy o'lchami (L, W). Bog'langan XNC konturi bo'lmasa (yoki `use_xnc` o'chiq) — to'rtburchak.
    Ishlov belgilari (etiketka o'rni uchun) bog'langan XNC dan har holda yig'iladi."""
    L, W = size
    shape = rect_shape(L, W)
    if project is None or not part.xnc_op_ids:
        return shape
    from ..models import OpType
    xops = [o for o in project.operations if o.type == OpType.XNC and o.xnc and o.id in part.xnc_op_ids]
    if not xops:
        return shape
    all_c: list[Contour] = []
    marks: dict = {"drills": [], "paths": [], "grooves": []}
    sz = size
    for xo in xops:
        try:
            cons, mk, sz = xnc_contours(project, xo, tol)
        except Exception:  # noqa: BLE001 — buzuq dastur: to'rtburchak
            shape.warns.append(("cn.w_xnc_failed", {}))
            continue
        all_c += cons
        for k in marks:
            marks[k] += mk[k]
    if not use_xnc:
        shape.marks = marks
        return shape
    got = shape_from_contours(all_c, marks, sz, tol)
    if got is None:
        shape.marks = marks
        return shape
    bw, bh = got.bbox_size
    if abs(bw - L) > 1.0 or abs(bh - W) > 1.0:
        got.warns.append(("cn.w_size_differs", dict(cw=f"{bw:g}", ch=f"{bh:g}", pw=f"{L:g}", ph=f"{W:g}")))
    return got


# ───────────────────────── Ofset ─────────────────────────
def _seg_pair_params(a: np.ndarray, b: np.ndarray):
    """Barcha (i, j) segment juftliklari uchun kesishish parametrlari (t_i, u_j) va yaroqlilik niqobi (qat'iy ichki kesishish)."""
    p, r = a, b - a                                          # (m, 2)
    q, s = a, b - a
    rxs = r[:, None, 0] * s[None, :, 1] - r[:, None, 1] * s[None, :, 0]
    qp = q[None, :, :] - p[:, None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (qp[..., 0] * s[None, :, 1] - qp[..., 1] * s[None, :, 0]) / rxs
        u = (qp[..., 0] * r[:, None, 1] - qp[..., 1] * r[:, None, 0]) / rxs
    eps = 1e-9
    ok = (np.abs(rxs) > 1e-12) & (t > eps) & (t < 1 - eps) & (u > eps) & (u < 1 - eps)
    return t, u, ok


def offset_ring(ring: Ring, d: float, tol: float = 0.1) -> list[Ring]:
    """Konturni materialdan TASHQARIGA d ga siljitadi (d > 0: material kengayadi — tashqi kontur kattalashadi, ichki kontur
    (teshik) kichrayadi; d < 0 — teskari). Burchaklarda yumaloq ulanish (xato ≤ tol). Ichki o'zaro kesishishlar olib tashlanadi;
    natija — bir nechta kontur bo'lishi mumkin (yoki bo'sh: teshik butunlay yopilgan). Asbob yo'li ma'lumoti uchun (nesting masofalari
    bunga bog'liq emas). Orientatsiya: tashqi — musbat."""
    ring = clean_ring(ring)
    if len(ring) < 3 or d == 0:
        return [ring] if ring else []
    if d < 0:
        return [r[::-1] for r in offset_ring(ring[::-1], -d, tol)]
    dd = float(d)
    n = len(ring)
    P = np.asarray(ring, dtype=float)
    E = np.roll(P, -1, axis=0) - P
    L = np.hypot(E[:, 0], E[:, 1])
    U = E / L[:, None]
    N = np.stack([U[:, 1], -U[:, 0]], axis=1)                    # materialdan chiqqan normal
    step = 2.0 * math.acos(max(-1.0, min(1.0, 1.0 - tol / dd))) if tol < dd else math.pi / 2
    step = max(step, 1e-2)
    raw: list[Pt] = []
    for i in range(n):
        pv = (i - 1) % n
        p = P[i]
        n0, n1 = N[pv], N[i]
        cross = U[pv][0] * U[i][1] - U[pv][1] * U[i][0]
        dot = float(np.dot(n0, n1))
        a = p + dd * n0
        b = p + dd * n1
        if cross > 1e-12:                                       # qavariq: yoy
            ang = math.atan2(cross, dot)
            m = max(1, int(math.ceil(ang / step)))
            raw.append((a[0], a[1]))
            for k in range(1, m):
                th = ang * k / m
                c, s = math.cos(th), math.sin(th)
                v = (c * n0[0] - s * n0[1], s * n0[0] + c * n0[1])
                raw.append((p[0] + dd * v[0], p[1] + dd * v[1]))
            raw.append((b[0], b[1]))
        elif cross < -1e-12:                                    # botiq: ikki nuqta (kesishuvchi halqa keyin olib tashlanadi)
            raw.append((a[0], a[1]))
            raw.append((b[0], b[1]))
        else:
            raw.append((b[0], b[1]))
    raw = clean_ring(raw, 1e-9)
    m = len(raw)
    if m < 3:
        return []
    A = np.asarray(raw, dtype=float)
    B = np.roll(A, -1, axis=0)
    t, u, ok = _seg_pair_params(A, B)
    cuts: list[list[float]] = [[] for _ in range(m)]
    ii, jj = np.nonzero(ok)
    for i, j in zip(ii.tolist(), jj.tolist()):
        if i == j:
            continue
        cuts[i].append(float(t[i, j]))
    # segmentlarni bo'lish; o'rta nuqtasi asl konturdan ≥ d − tol uzoqda bo'lgan bo'laklar qoladi
    P2 = P
    E2 = np.roll(P, -1, axis=0) - P
    L2 = np.maximum(np.hypot(E2[:, 0], E2[:, 1]), 1e-12)

    def dist_to_ring(pt: np.ndarray) -> float:
        w = pt[None, :] - P2
        tt = np.clip(np.einsum("ij,ij->i", w, E2) / (L2 * L2), 0.0, 1.0)
        q = P2 + E2 * tt[:, None]
        return float(np.min(np.hypot(pt[0] - q[:, 0], pt[1] - q[:, 1])))

    thr = dd - tol - 1e-6
    edges: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for i in range(m):
        ts = sorted(set([0.0, 1.0] + cuts[i]))
        for t0, t1 in zip(ts[:-1], ts[1:]):
            if t1 - t0 < 1e-12:
                continue
            pa = A[i] + (B[i] - A[i]) * t0
            pb = A[i] + (B[i] - A[i]) * t1
            if dist_to_ring((pa + pb) / 2) >= thr:
                edges.append(((float(pa[0]), float(pa[1])), (float(pb[0]), float(pb[1]))))
    if not edges:
        return []
    key = lambda p: (round(p[0], 5), round(p[1], 5))
    nxt: dict[tuple, list[tuple]] = {}
    pos: dict[tuple, Pt] = {}
    for a_, b_ in edges:
        ka, kb = key(a_), key(b_)
        pos[ka], pos[kb] = a_, b_
        nxt.setdefault(ka, []).append(kb)
    rings: list[Ring] = []
    used: set[tuple] = set()
    for start in list(nxt.keys()):
        if start in used:
            continue
        chain = [start]
        used.add(start)
        cur = start
        closed = False
        for _ in range(len(edges) + 2):
            outs = [k for k in nxt.get(cur, []) if k == start or k not in used]
            if not outs:
                break
            nk = outs[0]
            if nk == start:
                closed = True
                break
            chain.append(nk)
            used.add(nk)
            cur = nk
        if closed and len(chain) >= 3:
            r = clean_ring([pos[k] for k in chain])
            if len(r) >= 3 and ring_area(r) > MIN_RING_AREA:
                rings.append(r)
    return rings
