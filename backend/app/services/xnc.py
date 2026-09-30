"""XNC (CNC) dasturi: statistika, narx va chizma.

Dastur — buyruqlar daraxti (XncCommand). Parametrlar son yoki ifoda bo'lishi mumkin
(masalan DP="dz", X="dx/2"). Ifodalar xavfsiz hisoblanadi: faqat + - * / ( ) raqamlar,
o'zgaruvchilar (dx, dy, dz + Var/Par) va bir necha matematik funksiya.

Koordinatalar: boshlanish nuqtasi (origin) standart — chap-yuqori burchak, X o'ngga, Y pastga.
Buyruqlar:
  DrillFront X Y D DP [T]          — yuzadan teshik (DP ≥ dz — o'tuvchi)
  DrillLeft/Right  Y Z D DP [T]    — chap/o'ng qirradan teshik
  DrillTop/Bottom  X Z D DP [T]    — yuqori/pastki qirradan teshik
  MillStart X Y DP T D             — frezaning kirish nuqtasi, keyin MillLine / MillArcCenter (X Y [CX CY DIR])
  Groove X1 Y1 X2 Y2 DP W          — paz (arra bilan)
"""
from __future__ import annotations

import ast
import math
import operator as _op
from html import escape

from ..models import Operation, OpType, Project, XncCommand

_OPS = {ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul, ast.Div: _op.truediv,
        ast.USub: _op.neg, ast.UAdd: _op.pos, ast.Pow: _op.pow, ast.Mod: _op.mod}
_FUNCS = {"sin": lambda d: math.sin(math.radians(d)), "cos": lambda d: math.cos(math.radians(d)),
          "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "round": round}


MAX_EXPR = 200          # ifoda uzunligi (belgi)


def _pow(a: float, b: float) -> float:
    if abs(b) > 64 or abs(a) > 1e6:
        raise ValueError("Daraja juda katta")
    return a ** b


_OPS[ast.Pow] = _pow


def eval_expr(expr, env: dict[str, float]) -> float:
    if isinstance(expr, (int, float)):
        return float(expr)
    src = str(expr).replace(",", ".")
    if len(src) > MAX_EXPR:
        raise ValueError("Ifoda juda uzun")
    node = ast.parse(src, mode="eval").body

    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.Name):
            if n.id not in env:
                raise ValueError(f"Noma'lum o'zgaruvchi: {n.id}")
            return env[n.id]
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS:
            return float(_FUNCS[n.func.id](*[ev(a) for a in n.args]))
        raise ValueError("Ruxsat etilmagan ifoda")
    return ev(node)


def _num(p: dict, key: str, env: dict, default: float = 0.0) -> float:
    """Parametr qiymati; noto'g'ri ifoda (sintaksis, 0 ga bo'lish, toshish, cheksiz) — standart qiymat."""
    if key not in p or p[key] in ("", None):
        return default
    try:
        v = float(eval_expr(p[key], env))
    except Exception:  # noqa: BLE001 — foydalanuvchi ifodasi server xatosiga aylanmasin
        return default
    return v if math.isfinite(v) else default


def evaluate(cmds: list[XncCommand], dx: float, dy: float, dz: float) -> list[dict]:
    """Dasturni «yoyib» chiqadi: har geometrik amal hisoblangan qiymatlar bilan (chizma va statistika uchun)."""
    env = {"dx": dx, "dy": dy, "dz": dz}
    out: list[dict] = []
    tools: dict[str, float] = {}

    def walk(lst):
        for c in lst:
            p = dict(c.params)
            if c.cmd in ("Var", "Par", "Set"):
                name = str(p.get("name", ""))
                if name:
                    env[name] = _num(p, "value", env)
            elif c.cmd == "Tool":
                tools[str(p.get("N", p.get("name", "")))] = _num(p, "D", env)
            elif c.cmd.startswith("Drill"):
                t = str(p.get("T", ""))
                d = _num(p, "D", env, tools.get(t, 5.0))
                o = dict(kind=c.cmd, X=_num(p, "X", env), Y=_num(p, "Y", env), Z=_num(p, "Z", env, dz / 2),
                         D=d, DP=_num(p, "DP", env, dz), T=t,
                         count=max(1, min(1000, int(_num(p, "count", env, 1)))))
                # detal tashqarisidagi teshik (masalan, shablon kattaroq detal uchun yozilgan) — bajarilmaydi
                tol = 0.01
                if c.cmd == "DrillFront":
                    o["inside"] = -tol <= o["X"] <= dx + tol and -tol <= o["Y"] <= dy + tol
                elif c.cmd in ("DrillLeft", "DrillRight"):
                    o["inside"] = -tol <= o["Y"] <= dy + tol
                else:
                    o["inside"] = -tol <= o["X"] <= dx + tol
                out.append(o)
            elif c.cmd in ("MillStart", "MillLine", "MillArc", "MillArcCenter", "MillArc3P"):
                t = str(p.get("T", ""))
                out.append(dict(kind=c.cmd, X=_num(p, "X", env), Y=_num(p, "Y", env), CX=_num(p, "CX", env, float("nan")),
                                CY=_num(p, "CY", env, float("nan")), R=_num(p, "R", env), DIR=str(p.get("DIR", "")),
                                D=_num(p, "D", env, tools.get(t, 0.0)), DP=_num(p, "DP", env, dz), T=t))
            elif c.cmd == "MillRect":
                out.append(dict(kind="MillRect", X=_num(p, "X", env), Y=_num(p, "Y", env), L=_num(p, "L", env),
                                W=_num(p, "W", env), D=_num(p, "D", env)))
            elif c.cmd == "MillEllipse":
                out.append(dict(kind="MillEllipse", X=_num(p, "X", env), Y=_num(p, "Y", env), A=_num(p, "A", env),
                                B=_num(p, "B", env)))
            elif c.cmd == "Groove":
                x1, y1 = _num(p, "X1", env, _num(p, "X", env)), _num(p, "Y1", env, _num(p, "Y", env))
                if "L" in p and "X2" not in p:
                    x2, y2 = x1 + _num(p, "L", env), y1
                else:
                    x2, y2 = _num(p, "X2", env, x1), _num(p, "Y2", env, y1)
                out.append(dict(kind="Groove", X1=x1, Y1=y1, X2=x2, Y2=y2, DP=_num(p, "DP", env), W=_num(p, "W", env, 4)))
            if c.children:
                walk(c.children)
    walk(cmds)
    return out


def program_stats(cmds: list[XncCommand], dx: float, dy: float, dz: float) -> dict:
    ops = evaluate(cmds, dx, dy, dz)
    drills = sum(o["count"] for o in ops if o["kind"].startswith("Drill") and o.get("inside", True))
    mill = 0.0
    saw = 0.0
    pos = None
    for o in ops:
        k = o["kind"]
        if k == "MillStart":
            pos = (o["X"], o["Y"])
        elif k == "MillLine" and pos is not None:
            nxt = (o["X"], o["Y"]); mill += math.dist(pos, nxt); pos = nxt
        elif k in ("MillArc", "MillArcCenter", "MillArc3P") and pos is not None:
            nxt = (o["X"], o["Y"])
            chord = math.dist(pos, nxt)
            r = o["R"]
            if not r and not math.isnan(o["CX"]):
                r = math.dist(pos, (o["CX"], o["CY"]))
            mill += 2 * r * math.asin(min(1.0, chord / (2 * r))) if r and chord <= 2 * r else chord
            pos = nxt
        elif k == "MillRect":
            mill += 2 * (o["L"] + o["W"])
        elif k == "MillEllipse":
            a, b = o["A"] / 2, o["B"] / 2
            mill += math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
        elif k == "Groove":
            saw += math.dist((o["X1"], o["Y1"]), (o["X2"], o["Y2"]))
    return dict(drills=drills, mill_m=round(mill / 1000, 3), saw_m=round(saw / 1000, 3))


def xnc_cost(op: Operation) -> dict:
    x = op.xnc
    st = program_stats(x.program, x.length, x.width, x.thickness)
    unit = st["drills"] * x.drill_price + st["mill_m"] * x.mill_price_m + \
        st["saw_m"] * x.saw_price_m + x.extra_cost
    op.cost_material = 0
    op.cost_operation = round(unit * x.qty, 2)
    return {**st, "unit_cost": round(unit, 2), "qty": x.qty, "cost": op.cost_operation}


def xnc_holes_table(op: Operation) -> list[list]:
    x = op.xnc
    rows = []
    for o in evaluate(x.program, x.length, x.width, x.thickness):
        if o["kind"].startswith("Drill") and o.get("inside", True):
            side = {"DrillFront": "", "DrillLeft": "←", "DrillRight": "→", "DrillTop": "↑", "DrillBottom": "↓"}[o["kind"]]
            rows.append([len(rows) + 1, f"{o['X']:g}{side}", f"{o['Y']:g}", f"{o['D']:g}", f"{o['DP']:g}", o["T"]])
    return rows


def xnc_drawing_svg(op: Operation, project: Project | None = None, width_px: int = 560) -> str:
    """Detal chizmasi: kontur, kromkali tomonlar, teshiklar (yuza — doira, qirra — belgi), freza, paz, o'lchamlar."""
    x = op.xnc
    dx, dy = max(x.length, 1), max(x.width, 1)
    pad = max(dx, dy) * 0.12
    fs = max(dx, dy) / 38
    k = width_px / (dx + 2 * pad)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad:g} {-pad:g} {dx + 2 * pad:g} {dy + 2 * pad:g}" '
           f'width="{width_px}" height="{(dy + 2 * pad) * k:.0f}" font-family="Arial">',
           f'<rect x="0" y="0" width="{dx:g}" height="{dy:g}" fill="#F7E3C4" stroke="#333" stroke-width="{fs / 6:.2f}"/>']
    # kromkalar (bog'langan detaldan)
    if project is not None:
        from .render import part_edges, safe_color
        for o in project.operations:
            for p in o.parts:
                if op.id in p.xnc_op_ids:
                    ed = part_edges(p, project)
                    g = fs * 0.5
                    lines = {"top": (0, -g, dx, -g), "bottom": (0, dy + g, dx, dy + g),
                             "left": (-g, 0, -g, dy), "right": (dx + g, 0, dx + g, dy)}
                    for sd, e in ed.items():
                        x1, y1, x2, y2 = lines[sd]
                        out.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{safe_color(e["color"])}" '
                                   f'stroke-width="{fs * 0.35:.2f}"/>')
                        tx, ty = (x1 + x2) / 2, (y1 + y2) / 2
                        out.append(f'<text x="{tx:g}" y="{ty:g}" font-size="{fs:.1f}" text-anchor="middle" '
                                   f'dominant-baseline="middle" fill="#000">{escape(e["symbol"])}</text>')
    ops = evaluate(x.program, x.length, x.width, x.thickness)
    pos = None
    path: list[str] = []
    for o in ops:
        kd = o["kind"]
        if kd.startswith("Drill") and not o.get("inside", True):
            continue
        if kd == "DrillFront":
            r = max(o["D"] / 2, fs * 0.15)
            thru = o["DP"] >= x.thickness - 1e-6
            out.append(f'<circle cx="{o["X"]:g}" cy="{o["Y"]:g}" r="{r:g}" fill="{"#fff" if thru else "#c0392b"}" '
                       f'stroke="#c0392b" stroke-width="{fs / 8:.2f}"/>')
        elif kd in ("DrillLeft", "DrillRight", "DrillTop", "DrillBottom"):
            L = max(o["DP"], fs)
            if kd == "DrillLeft":
                seg = (0, o["Y"], L, o["Y"])
            elif kd == "DrillRight":
                seg = (dx, o["Y"], dx - L, o["Y"])
            elif kd == "DrillTop":
                seg = (o["X"], 0, o["X"], L)
            else:
                seg = (o["X"], dy, o["X"], dy - L)
            out.append(f'<line x1="{seg[0]:g}" y1="{seg[1]:g}" x2="{seg[2]:g}" y2="{seg[3]:g}" stroke="#127a6b" '
                       f'stroke-width="{max(o["D"], fs * 0.3):g}" stroke-opacity=".6"/>')
        elif kd == "MillStart":
            if path:
                out.append(f'<path d="{" ".join(path)}" fill="none" stroke="#7d3cc9" stroke-width="{fs / 4:.2f}"/>')
            path = [f"M {o['X']:g} {o['Y']:g}"]
            pos = (o["X"], o["Y"])
        elif kd in ("MillLine", "MillArc", "MillArcCenter", "MillArc3P") and pos is not None:
            if kd == "MillArcCenter" and not math.isnan(o["CX"]):
                r = math.dist(pos, (o["CX"], o["CY"]))
                sweep = 1 if o["DIR"] in ("true", "cw", "1") else 0
                path.append(f"A {r:g} {r:g} 0 0 {sweep} {o['X']:g} {o['Y']:g}")
            else:
                path.append(f"L {o['X']:g} {o['Y']:g}")
            pos = (o["X"], o["Y"])
        elif kd == "MillRect":
            out.append(f'<rect x="{o["X"]:g}" y="{o["Y"]:g}" width="{o["L"]:g}" height="{o["W"]:g}" fill="none" '
                       f'stroke="#7d3cc9" stroke-width="{fs / 4:.2f}"/>')
        elif kd == "Groove":
            out.append(f'<line x1="{o["X1"]:g}" y1="{o["Y1"]:g}" x2="{o["X2"]:g}" y2="{o["Y2"]:g}" stroke="#0e7d78" '
                       f'stroke-width="{max(o["W"], fs * 0.25):g}" stroke-dasharray="{fs:g} {fs / 2:g}" stroke-opacity=".75"/>')
    if path:
        out.append(f'<path d="{" ".join(path)}" fill="none" stroke="#7d3cc9" stroke-width="{fs / 4:.2f}"/>')
    # o'lchamlar
    out.append(f'<text x="{dx / 2:g}" y="{-pad * 0.45:g}" font-size="{fs * 1.2:.1f}" text-anchor="middle">{dx:g}</text>')
    out.append(f'<text x="{-pad * 0.45:g}" y="{dy / 2:g}" font-size="{fs * 1.2:.1f}" text-anchor="middle" '
               f'transform="rotate(-90 {-pad * 0.45:g} {dy / 2:g})">{dy:g}</text>')
    out.append("</svg>")
    return "".join(out)


def xnc_ops_for_part(project: Project, part_id: str) -> list[Operation]:
    return [o for o in project.operations if o.type == OpType.XNC and any(
        part_id == p.id and o.id in p.xnc_op_ids for op in project.operations for p in op.parts)]
