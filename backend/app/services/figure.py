"""Figurali detal: arraga to'g'ri to'rtburchak (zagotovka) beriladi, keyin XNC «teshib o'tuvchi» freza bilan figura / burchak
kesiladi. Bu modul arrachi va kromkachi cheki uchun detal figurasini hisoblaydi (2026-11-22, foydalanuvchi talabi):

  removed — kesib olib tashlanadigan qism(lar): chekda yo'l-yo'l chiziq (shtrix) bilan; halqalar `evenodd` qoidasi bilan
            chiziladi (tashqi figura konturi bo'lsa — to'rtburchak + kontur halqasi: oradagi qism shtrixlanadi);
  cuts    — kesishdan keyin paydo bo'ladigan YANGI qirralar (detal ichidan o'tgan freza yo'li): har birida uzunlik va
            kromka (bo'lsa) — kromka belgisi chekda shu qirra bo'ylab, metraji EL hisobiga (`calc.edge_usage`) qo'shiladi.

Koordinatalar — detalning chap-yuqori burchagidan, X uzunlik bo'ylab (o'ngga), Y en bo'ylab (pastga), mm; y = 0 — «top»
(elt) tomoni, x = 0 — «left» (ell). Bu XNC chizmasining fizik ko'rinishi (`xnc.machine_program`, burishsiz) bilan bir xil; orqa
yuzadagi dastur lits yuzaga akslantiriladi (`xnc_constraints.machine_side` — chap ↔ o'ng).

Yangi qirra kromkasi — manba ustuvorligi:
  1. Bazis `.project` ichidagi `<part mxFigure>` (`Part.figure_edges`): korxona eksport skripti 2.00 MX har kontur
     elementining kromkasini XNC koordinatalarida va EL havolasi bilan yozadi (v2); zaxira — `tools/bazis/` skripti (v1);
  2. avtomatik qoida (`.project` da egri / kesilgan qirra kromkasi yozilmaydi — 114 loyihada tekshirildi):
     - kesilgan bo'lak biror tomonni deyarli butunlay (≥ FULL_SIDE) olib tashlasa (yoy tepa, figurali yuqori qirra) —
       yangi qirra o'sha tomon kromkasini oladi (tomon yo'q bo'ldi, kromkasi figuraga o'tadi);
     - eski eksport (≤ 1.99) tutash tomonga «!СмЧт <material>» yozgan bo'lsa — shu kromka (figurali element kromkali belgisi);
     - aks holda (burchak kesigi, yumaloq burchak) — kesilgan bo'lak tekkan HAMMA tomonlarda bir xil kromka bo'lsa — shu kromka,
       bittasida bo'lmasa — kromkasiz (masalan orqa / ko'rinmas burchak);
     - detal ichidagi yopiq kesim (rakovina, teshik) — kromkasiz.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Optional

from ..models import OpType, Operation, Part, Project

FULL_SIDE = 0.95            # tomon «butunlay olib tashlangan» ulushi
ON_SIDE_TOL = 0.6           # nuqta tomon ustida deb hisoblanadigan masofa, mm
MIN_CUT_LEN = 1.0           # bundan qisqa yangi qirra e'tiborsiz, mm
OUTLINE_COVER = 0.90        # yopiq kontur detal tashqi konturi bo'lishi uchun gabaritning ulushi
THROUGH_TOL = 0.5           # chuqurlik ≥ qalinlik − THROUGH_TOL — teshib o'tadi
SMCHT = "!СмЧт"              # eski Bazis eksporti: «смотри чертёж» — figurali qirra kromkasi tutash tomonga yozilgan
_SIDES = ("top", "right", "bottom", "left")
_CACHE: dict[str, dict] = {}
_CACHE_MAX = 512


def _xops(project: Project, part: Part) -> list[Operation]:
    return [o for o in project.operations if o.type == OpType.XNC and o.xnc and o.id in (part.xnc_op_ids or [])]


def _has_through_mill(op: Operation) -> bool:
    from .render import _flatten
    return any(c.enabled and c.cmd in ("MillStart", "MillRect", "MillEllipse") for c in _flatten(op.xnc.program))


def _contours(project: Project, op: Operation) -> tuple[list[dict], float, float]:
    """Teshib o'tuvchi freza konturlari fizik (burishsiz) koordinatalarda: [{start, segs, C}], dx, dy."""
    from . import xnc as X
    x = op.xnc
    op2 = op if not x.rotation else op.model_copy(update={"xnc": x.model_copy(update={"rotation": 0})})
    prog = X.machine_program(op2, project)
    dx, dy = float(prog["size"]["length"]), float(prog["size"]["width"])
    th = float(x.thickness or 0.0)
    back = not bool(x.face_side)
    out: list[dict] = []
    cur: Optional[dict] = None

    def fx(px: float) -> float:
        return dx - px if back else px

    def close():
        nonlocal cur
        if cur is not None and cur["segs"] and not cur["pocket"] and cur["dp"] >= th - THROUGH_TOL:
            out.append(cur)
        cur = None
    for o in prog["ops"]:
        k = o.get("kind")
        if k == "mill_start":
            close()
            if o.get("ok", True) is False:
                continue
            c = int(o.get("correction") or 0)
            if back and c in (1, 2):
                c = 3 - c                              # akslantirish korreksiya tomonini almashtiradi
            cur = dict(start=(fx(o["x"]), o["y"]), segs=[], C=c, pocket=bool(o.get("pocket")),
                       dp=float(o.get("depth") or th))
        elif k == "mill_line" and cur is not None:
            cur["segs"].append(dict(type="line", x=fx(o["x"]), y=o["y"]))
            cur["dp"] = max(cur["dp"], float(o.get("depth") or 0.0))
        elif k == "mill_arc" and cur is not None:
            cw = bool(o.get("clockwise"))
            cur["segs"].append(dict(type="arc", x=fx(o["x"]), y=o["y"], cx=fx(o["cx"]), cy=o["cy"], r=float(o["radius"]),
                                    cw=(not cw) if back else cw, sweep=math.radians(abs(float(o.get("angle") or 0.0)))))
            cur["dp"] = max(cur["dp"], float(o.get("depth") or 0.0))
        else:
            close()
            if k in ("rect", "ellipse") and not o.get("pocket") and float(o.get("depth") or th) >= th - THROUGH_TOL:
                pts = []
                for s in o.get("path") or []:
                    if s.get("type") == "arc" and pts:
                        # yoy → nuqtalar (3° qadam)
                        a0 = math.atan2(pts[-1][1] - s["cy"], pts[-1][0] - s["cx"])
                        a1 = math.atan2(s["y"] - s["cy"], s["x"] - s["cx"])
                        sw = (a1 - a0) % (2 * math.pi) if s.get("clockwise") else -((a0 - a1) % (2 * math.pi))
                        r = s.get("radius") or math.dist(pts[-1], (s["cx"], s["cy"]))
                        n = max(2, int(abs(sw) / math.radians(3)) + 1)
                        pts += [(s["cx"] + r * math.cos(a0 + sw * i / n), s["cy"] + r * math.sin(a0 + sw * i / n))
                                for i in range(1, n + 1)]
                    else:
                        pts.append((s["x"], s["y"]))
                if len(pts) >= 3:
                    pts = [(fx(a), b) for a, b in pts]
                    out.append(dict(start=pts[0], segs=[dict(type="line", x=a, y=b) for a, b in pts[1:] + [pts[0]]], C=0,
                                    pocket=False, dp=th))
    close()
    return out, dx, dy


def _plen(pts) -> float:
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def _side_of(p, W: float, H: float, tol: float = ON_SIDE_TOL) -> Optional[str]:
    d = {"top": abs(p[1]), "bottom": abs(H - p[1]), "left": abs(p[0]), "right": abs(W - p[0])}
    s = min(d, key=d.get)
    return s if d[s] <= tol else None


def _side_cover(poly, W: float, H: float) -> dict[str, float]:
    """Bo'lak chegarasining har tomonga tushgan uzunligi (mm)."""
    cov = {s: 0.0 for s in _SIDES}
    for a, b in zip(poly, poly[1:] + poly[:1]):
        sa, sb = _side_of(a, W, H), _side_of(b, W, H)
        if sa and sa == sb:
            cov[sa] += math.dist(a, b)
        elif sa and sb and sa != sb:
            # burchak orqali o'tgan kesma (ikki tomon uchi) — ikkalasiga bo'linadi
            for s in (sa, sb):
                cov[s] += math.dist(a, b) / 2
    return cov


def _r(v: float) -> float:
    return round(float(v), 1)


def _ring(pts) -> list[list[float]]:
    return [[_r(a), _r(b)] for a, b in pts]


def _auto_edge(cov: dict[str, float], W: float, H: float, edges: dict) -> tuple[Optional[str], str]:
    """(tomon | None, qoida) — yangi qirra qaysi tomon kromkasini oladi."""
    full = {"top": W, "bottom": W, "left": H, "right": H}
    gone = [s for s in _SIDES if full[s] > 0 and cov[s] >= FULL_SIDE * full[s]]
    if gone:
        with_edge = [s for s in gone if s in edges]
        return (with_edge[0], "side") if with_edge else (None, "side")
    touched = [s for s in _SIDES if cov[s] > ON_SIDE_TOL * 2]
    if not touched:
        return None, "inner"
    # Eski Bazis eksporti (≤ 1.99) figurali element kromkasini tutash tomonga «!СмЧт <material>» bilan yozadi —
    # bu aynan shu kesim kromkali ekanining belgisi
    smcht = [s for s in touched if s in edges and str(edges[s].get("name") or "").startswith(SMCHT)]
    if smcht:
        return smcht[0], "smcht"
    refs = {edges[s]["op_id"] if s in edges else None for s in touched}
    if None in refs or len(refs) != 1:
        return None, "corner"
    return touched[0], "corner"


def _split_runs(ring, W: float, H: float) -> list[list[tuple[float, float]]]:
    """Yopiq tashqi kontur → detal ichidan o'tgan bo'laklari (to'rtburchak tomonlari ustidagi qismlari tashlanadi)."""
    n = len(ring)
    on = [_side_of(p, W, H) is not None for p in ring]
    if all(not v for v in on):
        return [list(ring) + [ring[0]]]
    k0 = next(i for i in range(n) if on[i])
    runs, cur = [], [ring[k0]]
    for t in range(1, n + 1):
        p = ring[(k0 + t) % n]
        q_on = on[(k0 + t) % n]
        prev = cur[-1]
        mid = ((prev[0] + p[0]) / 2, (prev[1] + p[1]) / 2)
        if q_on and _side_of(mid, W, H) is not None:
            if len(cur) >= 2:
                runs.append(cur)
            cur = [p]
        else:
            cur.append(p)
            if q_on:
                runs.append(cur)
                cur = [p]
    return [r for r in runs if len(r) >= 2 and _plen(r) >= MIN_CUT_LEN]


def _piece_for_run(run, W: float, H: float):
    """Tashqi konturning ichki bo'lagi (ikki uchi tomonlarda) ajratadigan KICHIK bo'lak."""
    from . import xnc as X
    a, b = run[0], run[-1]
    # uchlarni biroz tashqariga cho'zamiz — `_cutoff_polygon` yo'l detaldan kirib-chiqishini kutadi
    def ext(p, q):
        dx, dy = p[0] - q[0], p[1] - q[1]
        ln = math.hypot(dx, dy) or 1.0
        return (p[0] + dx / ln * 2, p[1] + dy / ln * 2)
    pts = [ext(a, run[1])] + list(run) + [ext(b, run[-2])]
    return X._cutoff_polygon(pts[0], [dict(type="line", x=x, y=y) for x, y in pts[1:]], W, H, 0)


def compute(project: Project, part: Part) -> Optional[dict]:
    """Detal figurasi yoki None (teshib o'tuvchi freza yo'q — oddiy to'rtburchak)."""
    xops = [o for o in _xops(project, part) if _has_through_mill(o)]
    if not xops:
        return None
    from .render import part_edges
    edges = {s: dict(e) for s, e in part_edges(part, project).items()}
    for s in edges:
        edges[s]["op_id"] = getattr(part, f"edge_{s}").op_id
    key = hashlib.sha1(json.dumps([[o.xnc.model_dump(mode="json") for o in xops], sorted((s, e["op_id"]) for s, e in edges.items()),
                                   [getattr(part, "figure_edges", None)]], sort_keys=True, default=str).encode()).hexdigest()
    hit = _CACHE.get(key)
    if hit is not None:
        return json.loads(json.dumps(hit))
    from . import xnc as X
    removed: list[list[list[float]]] = []
    cuts: list[dict] = []
    W = H = 0.0
    for op in xops:
        try:
            conts, W, H = _contours(project, op)
        except Exception:  # noqa: BLE001 — buzuq dastur: figura yo'q (XNC tekshiruvi xatoni o'zi ko'rsatadi)
            continue
        for c in conts:
            pts = X._sample(c["start"], c["segs"])
            if len(pts) < 2:
                continue
            closed = math.dist(pts[0], pts[-1]) < 0.05
            inside = [X._inside_rect(p, W, H) for p in pts]
            if closed and all(inside) or closed and all(_side_of(p, W, H) is not None or ins for p, ins in zip(pts, inside)):
                ring = pts[:-1]
                xs, ys = [p[0] for p in ring], [p[1] for p in ring]
                outline = (max(xs) - min(xs)) >= OUTLINE_COVER * W and (max(ys) - min(ys)) >= OUTLINE_COVER * H
                if outline:
                    removed.append(_ring([(0, 0), (W, 0), (W, H), (0, H)]))
                    removed.append(_ring(ring))
                    for run in _split_runs(ring, W, H):
                        piece = _piece_for_run(run, W, H)
                        cov = _side_cover(piece, W, H) if piece else {s: 0.0 for s in _SIDES}
                        side, rule = _auto_edge(cov, W, H, edges)
                        cuts.append(_cut(run, side, rule, edges))
                else:
                    removed.append(_ring(ring))
                    cuts.append(_cut(list(ring) + [ring[0]], None, "inner", edges))
                continue
            poly = X._cutoff_polygon(c["start"], c["segs"], W, H, c["C"])
            if not poly or not any(inside):
                continue
            removed.append(_ring(poly))
            i = inside.index(True)
            j = len(inside) - 1 - inside[::-1].index(True)
            run = [poly[0], *pts[i:j + 1], poly[len(pts[i:j + 1]) + 1]]
            cov = _side_cover(poly, W, H)
            side, rule = _auto_edge(cov, W, H, edges)
            cuts.append(_cut(run, side, rule, edges))
    cuts = [c for c in cuts if c["length"] >= MIN_CUT_LEN]
    if not removed:
        return None
    cuts = _apply_bazis(part, cuts, edges)
    res = dict(size=[_r(W), _r(H)], removed=removed, cuts=cuts,
               edge_mm=round(sum(c["length"] for c in cuts if c.get("edge")), 1))
    if len(_CACHE) > _CACHE_MAX:
        _CACHE.clear()
    _CACHE[key] = res
    return json.loads(json.dumps(res))


def _cut(run, side: Optional[str], rule: str, edges: dict) -> dict:
    e = edges.get(side) if side else None
    return dict(path=_ring(run), length=round(_plen(run), 1), rule=rule, source="auto",
                edge=(dict(op_id=e["op_id"], side=side, symbol=e["symbol"], name=e["name"], color=e["color"]) if e else None))


BAZIS_MATCH_MM = 2.0        # yangi qirra bo'lagi Bazis kesmasidan shu masofada bo'lsa — o'sha kesma kromkasi


def _bazis_edge(s: dict, project_edges: dict) -> Optional[dict]:
    op_id = s.get("op_id")
    if op_id and op_id in project_edges:
        sd, e = project_edges[op_id]
        return dict(op_id=op_id, side=sd, symbol=e["symbol"], name=e["name"], color=e["color"])
    if op_id or s.get("name") or s.get("symbol"):
        # kromka bor, EL operatsiyasi detal tomonlarida yo'q — belgisi/nomi bilan; op_id bo'lsa metraji hisobga kiradi
        return dict(op_id=op_id, side=None, symbol=s.get("symbol") or "?", name=s.get("name") or "", color="#000")
    return None


def _edge_key(e: Optional[dict]):
    return None if not e else (e.get("op_id"), e.get("symbol"), e.get("name"))


def _apply_bazis(part: Part, cuts: list[dict], edges: dict) -> list[dict]:
    """Bazis yozgan kontur kromkalari (`Part.figure_edges`: [{x1, y1, x2, y2, op_id|None, name, symbol}]) — yangi qirralarga
    geometrik moslash. Har yangi qirra kesmalarga bo'linadi: har kesma o'rtasiga eng yaqin (≤ BAZIS_MATCH_MM) Bazis kesmasi
    uning kromkasini beradi; bir xil kromkali ketma-ket bo'laklar bitta qirraga birlashadi (bitta kesimda kromkali va
    kromkasiz qism bo'lishi mumkin — masalan U-o'yiqning tubi). Mos kelmagan bo'lak — avtomatik qoida natijasi qoladi."""
    src = getattr(part, "figure_edges", None) or []
    if not src:
        return cuts
    project_edges = {e["op_id"]: (s, e) for s, e in edges.items()}
    out: list[dict] = []
    for c in cuts:
        p = c["path"]
        pieces: list[tuple[list, Optional[dict], bool]] = []          # (nuqtalar, kromka, bazis-mos)
        for a, b in zip(p, p[1:]):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            best, bd = None, BAZIS_MATCH_MM
            for s in src:
                d = _dist_seg(mid, (s["x1"], s["y1"]), (s["x2"], s["y2"]))
                if d <= bd:
                    best, bd = s, d
            if best is None:
                e, hit = c.get("edge"), False
            else:
                e, hit = _bazis_edge(best, project_edges), True
            if pieces and pieces[-1][2] == hit and _edge_key(pieces[-1][1]) == _edge_key(e):
                pieces[-1][0].append(b)
            else:
                pieces.append(([a, b], e, hit))
        for pts, e, hit in pieces:
            ln = round(_plen(pts), 1)
            if ln < 0.05:
                continue
            nc = dict(c, path=[list(q) for q in pts], length=ln, edge=e)
            if hit:
                nc["source"], nc["rule"] = "bazis", "bazis"
            out.append(nc)
    return out


def _arc_pts(p1, p2, c, mid=None, ccw: Optional[bool] = None, sag: float = 0.1) -> list[tuple[float, float]]:
    """Yoy nuqtalari: markaz `c`, uchlar p1→p2; yo'nalish o'rta nuqtadan (`mid`) yoki `ccw` (burchak o'sadi) dan.
    Qadam — vatar egilishi ≤ `sag` mm."""
    r = math.dist(p1, c)
    if r <= 1e-9:
        return [tuple(p1), tuple(p2)]
    a0 = math.atan2(p1[1] - c[1], p1[0] - c[0])
    a1 = math.atan2(p2[1] - c[1], p2[0] - c[0])
    up = (a1 - a0) % (2 * math.pi) or 2 * math.pi          # burchak o'sib boradigan yo'l
    dn = -((a0 - a1) % (2 * math.pi) or 2 * math.pi)
    if mid is not None:
        am = math.atan2(mid[1] - c[1], mid[0] - c[0])
        sw = up if (am - a0) % (2 * math.pi) < up else dn
    else:
        sw = up if (ccw is None or ccw) else dn
    step = 2 * math.acos(max(-1.0, min(1.0, 1 - sag / r))) if r > sag else math.pi / 2
    n = max(2, int(abs(sw) / max(step, 1e-3)) + 1)
    return [(c[0] + r * math.cos(a0 + sw * i / n), c[1] + r * math.sin(a0 + sw * i / n)) for i in range(n + 1)]


def bazis_edges(raw: str, L: float, W: float, side_ops: dict[str, Optional[str]], el_ops: list[Operation],
                ref_ops: Optional[dict[str, Operation]] = None) -> list[dict]:
    """Bazis `<part mxFigure="…">` atributi → `Part.figure_edges`. Ikki manba:

    v2 (`"frame": "xnc"`) — Bazis eksport skriptining o'zi (GibLabExport 2.00 MX): kontur elementlari XNC dasturi
    koordinatalarida (x o'ngga, y pastga, zagotovkaning chap-yuqori burchagidan) — figura hisobi bilan bir xil, o'zgartirilmaydi;
    `el` — `.project` dagi EL operatsiya havolasi (`@operation#N`, `ref_ops` orqali), `mat` / `sign` — kromka nomi / belgisi;
    yoyda `cx, cy` va o'rta nuqta `mx, my` (yoki `dir`: true — burchak o'sadi).

    v1 — alohida skript (`tools/bazis/mx_figura_kromka.js`): Bazis panelining o'z koordinatalarida; o'qlar mosligi
    noma'lum — 8 ta yo'nalishdan (almashtirish × X/Y ko'zgu) 4 tomon kromkasiga (elt/elb/ell/elr) eng mosi tanlanadi.
    Xato / bo'sh — []."""
    try:
        d = json.loads(raw)
        segs = d.get("segs") or []
    except (ValueError, AttributeError):
        return []
    if not segs or L <= 0 or W <= 0:
        return []
    if d.get("frame") == "xnc":
        return _bazis_edges_xnc(segs, el_ops, ref_ops or {})
    by_name = {(o.name or "").strip().lower(): o.id for o in el_ops if o.name}
    by_sym = {(o.el.symbol or "").strip(): o.id for o in el_ops if o.el and o.el.symbol}
    lines: list[tuple[float, float, float, float, Optional[str], str, str]] = []
    for s in segs:
        try:
            x1, y1, x2, y2 = (float(s[k]) for k in ("x1", "y1", "x2", "y2"))
        except (KeyError, TypeError, ValueError):
            continue
        mat = str(s.get("mat") or "").strip()
        sign = str(s.get("sign") or "").strip()
        op_id = (by_name.get(mat.lower()) or by_sym.get(sign)) if (mat or sign) else None
        has = bool(mat or sign)
        tag = ("E" if has else "")
        if "cx" in s and "cy" in s:
            cx, cy = float(s["cx"]), float(s["cy"])
            r = math.dist((x1, y1), (cx, cy))
            a0, a1 = math.atan2(y1 - cy, x1 - cx), math.atan2(y2 - cy, x2 - cx)
            sw = (a1 - a0) % (2 * math.pi) if s.get("ccw", True) else -((a0 - a1) % (2 * math.pi))
            n = max(2, int(abs(sw) / math.radians(5)) + 1)
            pts = [(cx + r * math.cos(a0 + sw * i / n), cy + r * math.sin(a0 + sw * i / n)) for i in range(n + 1)]
            for a, b in zip(pts, pts[1:]):
                lines.append((a[0], a[1], b[0], b[1], op_id, mat, sign + tag))
        else:
            lines.append((x1, y1, x2, y2, op_id, mat, sign + tag))
    if not lines:
        return []
    xs = [v for ln in lines for v in (ln[0], ln[2])]
    ys = [v for ln in lines for v in (ln[1], ln[3])]
    x0, y0, bw, bh = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    best, best_score = None, -1e9
    for swap in (False, True):
        sw_, sh_ = (bh, bw) if swap else (bw, bh)
        if abs(sw_ - L) > max(2.0, 0.02 * L) or abs(sh_ - W) > max(2.0, 0.02 * W):
            continue
        for fx in (False, True):
            for fy in (False, True):
                def tr(x, y, swap=swap, fx=fx, fy=fy):
                    u, v = x - x0, y - y0
                    if swap:
                        u, v = v, u
                    return (L - u if fx else u), (W - v if fy else v)
                cand = []
                for x1, y1, x2, y2, op_id, mat, sg in lines:
                    a, b = tr(x1, y1), tr(x2, y2)
                    cand.append(dict(x1=round(a[0], 2), y1=round(a[1], 2), x2=round(b[0], 2), y2=round(b[1], 2),
                                     op_id=op_id, name=mat, symbol=sg.rstrip("E"), edge=sg.endswith("E")))
                score = 0.0
                for c in cand:
                    m = ((c["x1"] + c["x2"]) / 2, (c["y1"] + c["y2"]) / 2)
                    sa, sb = _side_of((c["x1"], c["y1"]), L, W, 2.5), _side_of((c["x2"], c["y2"]), L, W, 2.5)
                    side = _side_of(m, L, W, 2.5) if sa is not None and sa == sb else None
                    if side is None:
                        continue
                    ln = math.dist((c["x1"], c["y1"]), (c["x2"], c["y2"]))
                    score += ln if bool(side_ops.get(side)) == c["edge"] else -ln
                if score > best_score:
                    best, best_score = cand, score
    if best is None:
        return []
    return [dict(x1=c["x1"], y1=c["y1"], x2=c["x2"], y2=c["y2"], op_id=c["op_id"] if c["edge"] else None,
                 name=c["name"], symbol=c["symbol"]) for c in best]


def _bazis_edges_xnc(segs: list, el_ops: list[Operation], ref_ops: dict[str, Operation]) -> list[dict]:
    """mxFigure v2: XNC koordinatalaridagi kontur elementlari → kesmalar (yoylar ≤ 0.1 mm vatar bilan)."""
    by_name = {(o.name or "").strip().lower(): o for o in el_ops if o.name}
    out: list[dict] = []
    for s in segs:
        try:
            p1 = (float(s["x1"]), float(s["y1"]))
            p2 = (float(s["x2"]), float(s["y2"]))
        except (KeyError, TypeError, ValueError):
            continue
        mat = str(s.get("mat") or "").strip()
        sign = str(s.get("sign") or "").strip()
        ref = str(s.get("el") or "").strip()
        op = ref_ops.get(ref) if ref else None
        if op is None and mat:
            op = by_name.get(mat.lower())
        has = bool(ref or mat)
        sym = sign or ((op.el.symbol if op is not None and op.el else "") or "")
        name = (op.name if op is not None else "") or mat
        if "cx" in s and "cy" in s:
            try:
                c = (float(s["cx"]), float(s["cy"]))
                mid = (float(s["mx"]), float(s["my"])) if "mx" in s and "my" in s else None
            except (TypeError, ValueError):
                continue
            pts = _arc_pts(p1, p2, c, mid=mid, ccw=bool(s.get("dir", True)))
        else:
            pts = [p1, p2]
        for a, b in zip(pts, pts[1:]):
            out.append(dict(x1=round(a[0], 3), y1=round(a[1], 3), x2=round(b[0], 3), y2=round(b[1], 3),
                            op_id=(op.id if op is not None else None) if has else None,
                            name=name if has else "", symbol=sym if has else ""))
    return out


def _dist_seg(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def edge_mm_by_op(project: Project, part: Part) -> dict[str, float]:
    """Figuradagi kromkali yangi qirralar uzunligi (mm, 1 dona detal uchun) — EL operatsiyasi bo'yicha."""
    f = compute(project, part)
    out: dict[str, float] = {}
    for c in (f or {}).get("cuts", []):
        e = c.get("edge")
        if e and e.get("op_id"):
            out[e["op_id"]] = out.get(e["op_id"], 0.0) + c["length"]
    return out
