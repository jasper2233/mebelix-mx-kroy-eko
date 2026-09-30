"""XNC (CNC) dasturi: statistika va narx.

Dastur — buyruqlar daraxti (XncCommand). Parametrlar son yoki ifoda bo'lishi
mumkin (masalan DP="dz", X="dx/2"). Ifodalar xavfsiz hisoblanadi:
faqat + - * / ( ) raqamlar va o'zgaruvchilar (dx, dy, dz + Var/Par).
"""
from __future__ import annotations

import ast
import math
import operator as _op

from ..models import Operation, XncCommand

_OPS = {ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul, ast.Div: _op.truediv,
        ast.USub: _op.neg, ast.UAdd: _op.pos, ast.Pow: _op.pow, ast.Mod: _op.mod}
_FUNCS = {"sin": lambda d: math.sin(math.radians(d)), "cos": lambda d: math.cos(math.radians(d)),
          "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "round": round}


def eval_expr(expr, env: dict[str, float]) -> float:
    if isinstance(expr, (int, float)):
        return float(expr)
    node = ast.parse(str(expr).replace(",", "."), mode="eval").body

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


def program_stats(cmds: list[XncCommand], dx: float, dy: float, dz: float) -> dict:
    env = {"dx": dx, "dy": dy, "dz": dz}
    drills = 0
    mill = 0.0
    saw = 0.0
    pos = None

    def walk(lst):
        nonlocal drills, mill, saw, pos
        for c in lst:
            p = {k: v for k, v in c.params.items()}
            if c.cmd in ("Var", "Par", "Set"):
                name = str(p.get("name", ""))
                if name:
                    env[name] = eval_expr(p.get("value", 0), env)
            elif c.cmd.startswith("Drill"):
                drills += int(eval_expr(p.get("count", 1), env))
            elif c.cmd == "MillStart":
                pos = (eval_expr(p.get("X", 0), env), eval_expr(p.get("Y", 0), env))
            elif c.cmd == "MillLine" and pos is not None:
                nxt = (eval_expr(p.get("X", pos[0]), env), eval_expr(p.get("Y", pos[1]), env))
                mill += math.dist(pos, nxt); pos = nxt
            elif c.cmd in ("MillArc", "MillArcCenter", "MillArc3P") and pos is not None:
                nxt = (eval_expr(p.get("X", pos[0]), env), eval_expr(p.get("Y", pos[1]), env))
                r = eval_expr(p.get("R", 0), env)
                chord = math.dist(pos, nxt)
                if r and chord <= 2 * r:
                    mill += 2 * r * math.asin(chord / (2 * r))
                else:
                    mill += chord
                pos = nxt
            elif c.cmd == "MillRect":
                mill += 2 * (eval_expr(p.get("L", 0), env) + eval_expr(p.get("W", 0), env))
            elif c.cmd == "MillEllipse":
                a = eval_expr(p.get("A", 0), env) / 2; b = eval_expr(p.get("B", 0), env) / 2
                mill += math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
            elif c.cmd == "Groove":
                saw += eval_expr(p.get("L", 0), env)
            if c.children:
                walk(c.children)
    walk(cmds)
    return dict(drills=drills, mill_m=round(mill / 1000, 3), saw_m=round(saw / 1000, 3))


def xnc_cost(op: Operation) -> dict:
    x = op.xnc
    st = program_stats(x.program, x.length, x.width, x.thickness)
    unit = st["drills"] * x.drill_price + st["mill_m"] * x.mill_price_m + \
        st["saw_m"] * x.saw_price_m + x.extra_cost
    op.cost_material = 0
    op.cost_operation = round(unit * x.qty, 2)
    return {**st, "unit_cost": round(unit, 2), "qty": x.qty, "cost": op.cost_operation}
