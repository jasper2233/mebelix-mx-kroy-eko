"""Umumiy ifoda tili (matematik, mantiqiy va matn ifodalari) — XNC parametrlari, etiketka maydonlari, fayl nomi va
hisoblanadigan ustunlar uchun bitta dvigatel.

GibLab yordamidagi (funksional tavsif) til qoidalariga mos, noldan yozilgan: o'z tokenizeri va parseri, `ast`/`eval`
ishlatilmaydi, faqat reestrdagi funksiyalar, uzunlik/chuqurlik/qadam/matn chegaralari bor.

Tiplar: butun (32 bit), haqiqiy (double), mantiqiy, matn, `null`.
Operatorlar (ustuvorlik yuqoridan pastga): qavs, funksiya, `^` (daraja; o'ngdan chapga), unar `+ -`, `* / %`, `+ -`,
taqqoslash `< > <= >= = == <> !=`, `not`, `and`, `xor`, `or`. `if(shart, a, b)` — yalqov funksiya; eski yozuv
`a if shart else b` ham qabul qilinadi. Butun ÷ butun — butun (7/2 = 3); `%` — qoldiq (bo'linuvchi ishorasi bilan).
`'matn'` + son — birlashtirish. Burchaklar standart holda radianda (`degrees=True` — gradusda).
Xatolar — `ValueError` (matni foydalanuvchi tilida); jim 0 yo'q.
"""
from __future__ import annotations

import binascii
import datetime as _dt
import math
import random as _random
import re
import time
import uuid as _uuid
import zlib
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from functools import lru_cache
from typing import Any, Callable

from ..i18n import _

MAX_SRC = 1000          # ifoda uzunligi (belgi); XNC uchun chaqiruvchi toraytiradi
MAX_DEPTH = 64          # ichma-ich chuqurlik (qavs, unar, shart)
MAX_EVAL_DEPTH = 300    # hisoblash daraxti chuqurligi (uzun «a+b+c+…» zanjirlari ham shu chegarada)
MAX_STEPS = 10_000      # bitta hisoblashdagi tugunlar soni
MAX_TEXT = 10_000       # matn natijasi uzunligi
MAX_CALC_DEPTH = 4      # calculate() ichma-ich chuqurligi
INT_MAX = 2_147_483_647


def _err(key: str, **kw) -> ValueError:
    return ValueError(_(key, **kw))


# ───────────────────────── Tokenizer ─────────────────────────
_KEYWORDS = {"and", "or", "not", "xor", "true", "false", "null", "if", "else"}
_ESC = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "'": "'", '"': '"', "\\": "\\"}
_NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?")
_ID_RE = re.compile(r"[^\W\d]\w*(?:\.[^\W\d]\w*)*", re.UNICODE)


def _tokenize(src: str) -> list[tuple[str, Any]]:
    toks: list[tuple[str, Any]] = []
    i, n = 0, len(src)
    parens: list[bool] = []            # True — funksiya chaqiruvi qavsi (vergul — argument ajratgichi)
    while i < n:
        ch = src[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch.isdigit() or (ch == "." and i + 1 < n and src[i + 1].isdigit()):
            m = _NUM_RE.match(src, i)
            if m is None:                       # «²», «①» kabi: str.isdigit() rost, lekin o'nlik raqam emas
                raise _err("xnc.e_syntax")
            text = m.group(0)
            j = m.end()
            # o'nli vergul («1,5*dx»): funksiya argumentlari tashqarisida va ikki tomonida raqam bo'lsa
            if "." not in text and "e" not in text.lower() and j + 1 < n and src[j] == "," and re.match(r"\d", src[j + 1]) \
                    and not (parens and parens[-1]):
                m2 = re.compile(r"\d+").match(src, j + 1)
                text = text + "." + m2.group(0)
                j = m2.end()
            if re.fullmatch(r"\d+", text) and int(text) <= INT_MAX:
                toks.append(("num", int(text)))
            else:
                try:
                    toks.append(("num", float(text)))
                except ValueError as e:
                    raise _err("xnc.e_syntax") from e
            i = j
            continue
        if ch in "'\"":
            q, i, buf = ch, i + 1, []
            while True:
                if i >= n:
                    raise _err("xnc.e_syntax")
                c = src[i]
                if c == q:
                    i += 1
                    break
                if c == "\\":
                    i += 1
                    if i >= n:
                        raise _err("xnc.e_syntax")
                    e = src[i]
                    if e == "u":
                        hx = src[i + 1:i + 5]
                        if not re.fullmatch(r"[0-9a-fA-F]{4}", hx):
                            raise _err("xnc.e_syntax")
                        buf.append(chr(int(hx, 16)))
                        i += 5
                        continue
                    if e not in _ESC:
                        raise _err("xnc.e_syntax")
                    buf.append(_ESC[e])
                    i += 1
                    continue
                buf.append(c)
                i += 1
                if len(buf) > MAX_TEXT:
                    raise _err("xnc.e_too_long", n=MAX_TEXT)
            toks.append(("str", "".join(buf)))
            continue
        if ch.isalpha() or ch == "_":
            m = _ID_RE.match(src, i)
            if not m:
                raise _err("xnc.e_syntax")
            word = m.group(0)
            low = word.lower()
            i = m.end()
            if low in _KEYWORDS:
                toks.append(("kw", low))
            else:
                toks.append(("id", word))
            continue
        two = src[i:i + 2]
        if two in ("<=", ">=", "<>", "!=", "=="):
            toks.append(("op", two))
            i += 2
            continue
        if two == "**":                         # eski yozuv: daraja
            toks.append(("op", "^"))
            i += 2
            continue
        if ch in "+-*/%^<>=(),":
            if ch == "(":
                prev = toks[-1] if toks else None
                parens.append(prev is not None and (prev[0] == "id" or prev == ("kw", "if")))
            elif ch == ")":
                if parens:
                    parens.pop()
            toks.append(("op", ch))
            i += 1
            continue
        raise _err("xnc.e_forbidden")
    return toks


# ───────────────────────── Parser ─────────────────────────
class _Parser:
    def __init__(self, toks: list[tuple[str, Any]]):
        self.t = toks
        self.i = 0
        self.depth = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else ("end", None)

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, kind, val=None):
        tok = self.peek()
        if tok[0] == kind and (val is None or tok[1] == val):
            self.i += 1
            return True
        return False

    def expect(self, kind, val=None):
        if not self.accept(kind, val):
            raise _err("xnc.e_syntax")

    def enter(self):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise _err("xnc.e_steps")

    def leave(self):
        self.depth -= 1

    def parse(self):
        node = self.ternary()
        if self.peek()[0] != "end":
            raise _err("xnc.e_syntax")
        return node

    def ternary(self):
        self.enter()
        node = self.or_()
        if self.peek() == ("kw", "if"):                      # a if shart else b (eski yozuv)
            self.next()
            cond = self.or_()
            self.expect("kw", "else")
            other = self.ternary()
            node = ("if", cond, node, other)
        self.leave()
        return node

    def or_(self):
        node = self.xor_()
        while self.accept("kw", "or"):
            node = ("or", node, self.xor_())
        return node

    def xor_(self):
        node = self.and_()
        while self.accept("kw", "xor"):
            node = ("xor", node, self.and_())
        return node

    def and_(self):
        node = self.not_()
        while self.accept("kw", "and"):
            node = ("and", node, self.not_())
        return node

    def not_(self):
        if self.accept("kw", "not"):
            self.enter()
            node = ("not", self.not_())
            self.leave()
            return node
        return self.cmp_()

    def cmp_(self):
        node = self.add()
        ops = []
        while self.peek()[0] == "op" and self.peek()[1] in ("<", ">", "<=", ">=", "=", "==", "<>", "!="):
            op = self.next()[1]
            ops.append((op, self.add()))
        return ("cmp", node, ops) if ops else node

    def add(self):
        node = self.mul()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            node = ("bin", op, node, self.mul())
        return node

    def mul(self):
        node = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/", "%"):
            op = self.next()[1]
            node = ("bin", op, node, self.unary())
        return node

    def unary(self):
        if self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            self.enter()
            node = ("un", op, self.unary())
            self.leave()
            return node
        return self.power()

    def power(self):
        base = self.primary()
        if self.accept("op", "^"):
            self.enter()
            node = ("bin", "^", base, self.unary())          # o'ngdan chapga: 2^3^2 = 2^(3^2)
            self.leave()
            return node
        return base

    def primary(self):
        kind, val = self.next()
        if kind == "num":
            return ("lit", val)
        if kind == "str":
            return ("lit", val)
        if kind == "kw" and val in ("true", "false"):
            return ("lit", val == "true")
        if kind == "kw" and val == "null":
            return ("lit", None)
        if (kind == "kw" and val == "if") or kind == "id":
            name = val
            if self.accept("op", "("):
                args = []
                if not self.accept("op", ")"):
                    while True:
                        args.append(self.ternary())
                        if self.accept("op", ")"):
                            break
                        self.expect("op", ",")
                return ("call", name.lower(), args)
            if kind == "kw":
                raise _err("xnc.e_syntax")
            return ("var", name)
        if kind == "op" and val == "(":
            self.enter()
            node = self.ternary()
            self.leave()
            self.expect("op", ")")
            return node
        raise _err("xnc.e_syntax")


@lru_cache(maxsize=4096)
def _compile(src: str):
    try:
        return _Parser(_tokenize(src)).parse()
    except RecursionError as e:
        raise _err("xnc.e_steps") from e


def compile_check(src: str, max_len: int = MAX_SRC) -> None:
    """Faqat sintaksisni tekshiradi (hisoblamaydi): xatoda ValueError."""
    s = str(src).strip()
    if len(s) > max_len:
        raise _err("xnc.e_too_long", n=max_len)
    _compile(s)


# ───────────────────────── Qiymatlar ─────────────────────────
def _java_double(x: float) -> str:
    if x != x:
        return "NaN"
    if math.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    if x == 0:
        return "-0.0" if math.copysign(1.0, x) < 0 else "0.0"
    a = abs(x)
    if 1e-3 <= a < 1e7:
        s = repr(x)
        return s if "." in s else s + ".0"
    d = Decimal(repr(a))
    digits = "".join(map(str, d.as_tuple().digits)).rstrip("0") or "0"
    mant = digits[0] + "." + (digits[1:] or "0")
    return f"{'-' if x < 0 else ''}{mant}E{d.adjusted()}"


def to_text(v) -> str:
    """Qiymatni matnga aylantirish (Java uslubi: 2.0, 1.0E-5, true/false; null — bo'sh)."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return _java_double(v)
    return str(v)


def _num(v):
    """Sonli qiymat (mantiqiy → 1/0). Boshqa tur — xato."""
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return v
    raise _err("xnc.e_type")


def _norm_num(v):
    if isinstance(v, float):
        if v != v:
            raise _err("xnc.e_domain")
        return v
    if isinstance(v, int) and abs(v) > INT_MAX:
        return float(v)                    # 32-bitdan oshsa — haqiqiyga ko'tariladi
    return v


def _truthy(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip().lower() in ("true", "t", "1")
    return False


def _pow(a, b):
    a, b = float(_num(a)), float(_num(b))
    if abs(b) > 64 or abs(a) > 1e6:
        raise _err("xnc.e_pow")
    try:
        r = a ** b
    except ZeroDivisionError as e:
        raise _err("xnc.e_zero") from e
    except OverflowError as e:
        raise _err("xnc.e_range") from e
    if isinstance(r, complex):
        raise _err("xnc.e_domain")
    return r


def _arith(op: str, a, b):
    if op == "+" and (isinstance(a, str) or isinstance(b, str)):
        out = to_text(a) + to_text(b)
        if len(out) > MAX_TEXT:
            raise _err("xnc.e_too_long", n=MAX_TEXT)
        return out
    if op == "^":
        return _pow(a, b)
    x, y = _num(a), _num(b)
    both_int = isinstance(x, int) and isinstance(y, int)
    if op == "+":
        r = x + y
    elif op == "-":
        r = x - y
    elif op == "*":
        r = x * y
    elif op == "/":
        if y == 0:
            raise _err("xnc.e_zero")
        if both_int:
            q = abs(x) // abs(y)
            r = q if (x >= 0) == (y >= 0) else -q          # nolga qarab kesish (butun bo'lish)
        else:
            r = x / y
    else:                                                   # %
        if y == 0:
            raise _err("xnc.e_zero")
        r = int(math.fmod(x, y)) if both_int else math.fmod(x, y)       # Java: qoldiq ishorasi bo'linuvchiniki
    if isinstance(r, float) and math.isinf(r):
        raise _err("xnc.e_range")
    return _norm_num(r)


def _equal(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, str) or isinstance(b, str):
        return to_text(a) == to_text(b)
    return abs(float(_num(a)) - float(_num(b))) <= 1e-9


def _compare(op: str, a, b) -> bool:
    if op in ("=", "=="):
        return _equal(a, b)
    if op in ("<>", "!="):
        return not _equal(a, b)
    if isinstance(a, str) or isinstance(b, str) or a is None or b is None:
        x, y = to_text(a), to_text(b)
    else:
        x, y = float(_num(a)), float(_num(b))
    return {"<": x < y, ">": x > y, "<=": x <= y, ">=": x >= y}[op]


# ───────────────────────── Funksiyalar ─────────────────────────
class Ctx:
    """Hisoblash konteksti: o'zgaruvchilar, burchak birligi, soat, tasodifiy son manbasi, qadam hisoblagichi."""

    def __init__(self, env: dict | None, degrees: bool, clock: Callable[[], _dt.datetime] | None,
                 rng: _random.Random | None, lang: str, max_len: int):
        self.env = env or {}
        self.degrees = degrees
        self.clock = clock or _dt.datetime.now
        self.rng = rng or _random.Random()
        self.lang = lang
        self.max_len = max_len
        self.steps = 0
        self.calc_depth = 0


_CONST = {"pi": math.pi, "e": math.e}


def _text_arg(v) -> str:
    return to_text(v)


def _int_arg(v, name: str = "") -> int:
    x = _num(v)
    if isinstance(x, float):
        if not math.isfinite(x):
            raise _err("xnc.e_domain")
        return int(x)
    return x


def _f(fn):
    """Matematik funksiya: haqiqiy argumentlar, ValueError/OverflowError → domen xatosi."""
    def run(ctx, *a):
        try:
            r = fn(*[float(_num(x)) for x in a])
        except (ValueError, OverflowError, ZeroDivisionError) as e:
            raise _err("xnc.e_domain") from e
        return r
    return run


def _ang_in(ctx, x: float) -> float:
    return math.radians(x) if ctx.degrees else x


def _ang_out(ctx, x: float) -> float:
    return math.degrees(x) if ctx.degrees else x


def _trig(fn):
    def run(ctx, x):
        try:
            return fn(_ang_in(ctx, float(_num(x))))
        except (ValueError, OverflowError, ZeroDivisionError) as e:
            raise _err("xnc.e_domain") from e
    return run


def _atrig(fn):
    def run(ctx, x):
        try:
            return _ang_out(ctx, fn(float(_num(x))))
        except (ValueError, OverflowError, ZeroDivisionError) as e:
            raise _err("xnc.e_domain") from e
    return run


def _round(ctx, x, n=0):
    x = float(_num(x))
    d = _int_arg(n)
    if abs(d) > 12 or not math.isfinite(x):
        raise _err("xnc.e_domain")
    f = 10.0 ** d
    r = math.floor(x * f + 0.5 + 1e-9) / f            # yarim — +∞ ga (round(-1.5) = -1)
    return int(r) if d == 0 and abs(r) <= INT_MAX else r


def _minmax(pick):
    def run(ctx, *a):
        vals = [_num(x) for x in a]
        r = pick(vals)
        return float(r) if any(isinstance(x, float) for x in vals) else r      # aralash tur — haqiqiy
    return run


def _abs(ctx, x):
    return abs(_num(x))


def _sign(ctx, x):
    x = float(_num(x))
    return 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)


def _floor(ctx, x):
    return float(math.floor(float(_num(x))))


def _ceil(ctx, x):
    return float(math.ceil(float(_num(x))))


def _log10(x):
    return math.log10(x)


def _logx(x, b):
    return math.log(x) / math.log(b)


def _mid(ctx, s, start, length):
    s, a, n = _text_arg(s), _int_arg(start), _int_arg(length)
    a = max(a, 1)
    return s[a - 1:a - 1 + max(n, 0)]


def _left(ctx, s, n):
    return _text_arg(s)[:max(_int_arg(n), 0)]


def _right(ctx, s, n):
    s, n = _text_arg(s), max(_int_arg(n), 0)
    return s[len(s) - n:] if n else ""


def _pad(s, n, ch):
    s, n, ch = _text_arg(s), _int_arg(n), _text_arg(ch)[:1] or " "
    if n > MAX_TEXT:
        raise _err("xnc.e_too_long", n=MAX_TEXT)
    return s, max(n, 0), ch


def _lspace(ctx, s, n, ch):                             # yordam misoli: lspace('abc',5,'X') = 'abcXX'
    s, n, ch = _pad(s, n, ch)
    return s[:n] + ch * (n - len(s)) if len(s) < n else s[:n]


def _rspace(ctx, s, n, ch):                             # rspace('abc',5,'X') = 'XXabc'
    s, n, ch = _pad(s, n, ch)
    return ch * (n - len(s)) + s if len(s) < n else (s[len(s) - n:] if n else "")


def _rept(ctx, s, n):
    s, n = _text_arg(s), _int_arg(n)
    if n < 0 or len(s) * n > MAX_TEXT:
        raise _err("xnc.e_too_long", n=MAX_TEXT)
    return s * n


def _find(ctx, s, sub, start=1):
    s, sub, a = _text_arg(s), _text_arg(sub), max(_int_arg(start), 1)
    return s.find(sub, a - 1) + 1


def _findr(ctx, s, sub, start=None):
    s, sub = _text_arg(s), _text_arg(sub)
    end = len(s) if start is None else max(min(_int_arg(start), len(s)), 0)
    return s.rfind(sub, 0, end) + 1


_TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя", ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n",
                                                          "o", "p", "r", "s", "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "",
                                                          "y", "", "e", "yu", "ya"]))
_TRANSLIT.update(dict(zip("ўқғҳ", ["o'", "q", "g'", "h"])))


def _translit(ctx, s):
    out = []
    for ch in _text_arg(s):
        low = ch.lower()
        if low in _TRANSLIT:
            t = _TRANSLIT[low]
            out.append(t.capitalize() if ch != low else t)
        else:
            out.append(ch)
    return "".join(out)


def _crc16(ctx, s):                                      # CRC-16/ARC (poli 0x8005, aks, boshlang'ich 0): crc16('test') = 63534
    crc = 0
    for b in _text_arg(s).encode("utf-8"):
        crc ^= b
        for _i in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def _crc32(ctx, s):                                      # IEEE CRC-32, ishorali int32: crc32('test') = -662733300
    v = zlib.crc32(_text_arg(s).encode("utf-8")) & 0xFFFFFFFF
    return v - (1 << 32) if v >= (1 << 31) else v


def _double(ctx, v):
    if isinstance(v, str):
        try:
            return float(v.strip().replace(",", "."))
        except ValueError as e:
            raise _err("xnc.e_domain") from e
    return float(_num(v))


def _integer(ctx, v):
    if isinstance(v, str):
        try:
            return int(float(v.strip().replace(",", ".")))
        except ValueError as e:
            raise _err("xnc.e_domain") from e
    return int(_num(v))


def _boolean(ctx, v):
    return _truthy(v if isinstance(v, str) else to_text(v))


def _conv_dec(base_fmt):
    def run(ctx, v):
        n = _int_arg(v)
        if n < 0:
            n &= 0xFFFFFFFF
        return format(n, base_fmt)
    return run


def _conv_to_dec(base):
    def run(ctx, v):
        try:
            return int(_text_arg(v).strip(), base)
        except ValueError as e:
            raise _err("xnc.e_domain") from e
    return run


def _roman(ctx, v):
    n = _int_arg(v)
    if not 1 <= n <= 3999:
        raise _err("xnc.e_domain")
    out = []
    for val, sym in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                     (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= val:
            out.append(sym)
            n -= val
    return "".join(out)


def _calculate(ctx, s):
    if ctx.calc_depth >= MAX_CALC_DEPTH:
        raise _err("xnc.e_steps")
    src = _text_arg(s).strip()
    if len(src) > ctx.max_len:
        raise _err("xnc.e_too_long", n=ctx.max_len)
    ctx.calc_depth += 1
    try:
        return _run(_compile(src), ctx, 0)
    finally:
        ctx.calc_depth -= 1


# --- format (Java DecimalFormat quyi to'plami) ---
def _split_pattern(p: str) -> tuple[str, str, str]:
    """Naqsh → (prefiks, son qismi, suffiks). Qo'shtirnoq ichidagi belgilar oddiy matn."""
    out = ["", "", ""]
    part = 0
    i = 0
    while i < len(p):
        c = p[i]
        if c == "'":
            j = p.find("'", i + 1)
            if j == i + 1:
                out[part] += "'"
                i += 2
                continue
            if j < 0:
                raise _err("xnc.e_syntax")
            out[part] += p[i + 1:j]
            i = j + 1
            continue
        if c in "0#,.E" and part < 2 and not (part == 0 and c == "E"):
            if part == 0:
                part = 1
            out[1] += c
            i += 1
            continue
        if part == 1:
            part = 2
        out[part] += c
        i += 1
    return out[0], out[1], out[2]


def _format_number(pattern: str, value) -> str:
    subs = pattern.split(";")
    pos = subs[0]
    neg = subs[1] if len(subs) > 1 else None
    x = float(_num(value)) if not isinstance(value, bool) else float(value)
    if not math.isfinite(x):
        raise _err("xnc.e_domain")
    use = neg if (x < 0 and neg is not None) else pos
    pre, num, suf = _split_pattern(use)
    if x < 0 and neg is None:
        pre = "-" + pre
    mult = 1
    for txt in (pre, suf):
        if "%" in txt:
            mult = 100
        if "‰" in txt:
            mult = 1000
    pre, suf = pre.replace("¤", "¤"), suf
    mant, _e, exp = num.partition("E")
    ip, _d, fp = mant.partition(".")
    grouping = 0
    if "," in ip:
        grouping = len(ip) - ip.rfind(",") - 1
    min_int = ip.count("0")
    min_frac = fp.count("0")
    max_frac = len(fp.replace(",", ""))
    try:
        d = Decimal(repr(abs(x))) * mult
    except InvalidOperation as e:
        raise _err("xnc.e_domain") from e
    if _e:                                                 # ilmiy yozuv: mantissa·10^n
        exp_digits = exp.count("0") or 1
        n_exp = 0 if d == 0 else d.adjusted() - max(min_int, 1) + 1
        d = d.scaleb(-n_exp)
    q = Decimal(1).scaleb(-max_frac)
    try:
        d = d.quantize(q, rounding=ROUND_HALF_EVEN)
    except InvalidOperation as e:
        raise _err("xnc.e_range") from e
    s = format(d, "f")
    ints, _dot, fr = s.partition(".")
    fr = fr.rstrip("0") if len(fr) > min_frac else fr
    fr = fr.ljust(min_frac, "0")
    ints = ints.lstrip("0")
    if len(ints) < min_int:
        ints = ints.rjust(min_int, "0")
    if not ints and not fr:
        ints = "0"
    if grouping and len(ints) > grouping:
        parts = []
        while len(ints) > grouping:
            parts.insert(0, ints[-grouping:])
            ints = ints[:-grouping]
        ints = ",".join([ints] + parts)
    res = ints + ("." + fr if fr else "")
    if _e:
        res += "E" + ("-" if n_exp < 0 else "") + str(abs(n_exp)).rjust(exp_digits, "0")
    out = pre + res + suf
    if len(out) > MAX_TEXT:
        raise _err("xnc.e_too_long", n=MAX_TEXT)
    return out


def _format(ctx, pattern, value):
    return _format_number(_text_arg(pattern), value)


# --- now (Java SimpleDateFormat quyi to'plami) ---
_MONTHS_RU = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
_MONTHS_RU_SHORT = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
_DAYS_RU = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
_DAYS_RU_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
_MONTHS_UZ = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
_MONTHS_UZ_SHORT = ["yan", "fev", "mar", "apr", "may", "iyn", "iyl", "avg", "sen", "okt", "noy", "dek"]
_DAYS_UZ = ["dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba", "yakshanba"]
_DAYS_UZ_SHORT = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def _date_format(fmt: str, dt: _dt.datetime, lang: str) -> str:
    months, mshort, days, dshort = ((_MONTHS_UZ, _MONTHS_UZ_SHORT, _DAYS_UZ, _DAYS_UZ_SHORT) if lang == "uz"
                                    else (_MONTHS_RU, _MONTHS_RU_SHORT, _DAYS_RU, _DAYS_RU_SHORT))
    out: list[str] = []
    i, n = 0, len(fmt)
    while i < n:
        c = fmt[i]
        if c == "'":
            j = fmt.find("'", i + 1)
            if j == i + 1:
                out.append("'")
                i += 2
                continue
            if j < 0:
                raise _err("xnc.e_syntax")
            out.append(fmt[i + 1:j])
            i = j + 1
            continue
        if not c.isalpha():
            out.append(c)
            i += 1
            continue
        j = i
        while j < n and fmt[j] == c:
            j += 1
        cnt = j - i
        i = j

        def num(v, width=1):
            return str(v).rjust(width, "0")
        h24 = dt.hour
        if c == "G":
            out.append("н.э." if lang != "uz" else "m.a.")
        elif c == "y":
            out.append(num(dt.year % 100, 2) if cnt == 2 else num(dt.year, cnt))
        elif c == "M":
            out.append(num(dt.month, cnt) if cnt <= 2 else (mshort if cnt == 3 else months)[dt.month - 1])
        elif c == "w":
            out.append(num(dt.isocalendar()[1], cnt))
        elif c == "W":
            first = dt.replace(day=1).weekday()
            out.append(num((dt.day - 1 + first) // 7 + 1, cnt))
        elif c == "D":
            out.append(num(dt.timetuple().tm_yday, cnt))
        elif c == "d":
            out.append(num(dt.day, cnt))
        elif c == "F":
            out.append(num((dt.day - 1) // 7 + 1, cnt))
        elif c == "E":
            out.append((dshort if cnt <= 3 else days)[dt.weekday()])
        elif c == "a":
            out.append("AM" if h24 < 12 else "PM")
        elif c == "H":
            out.append(num(h24, cnt))
        elif c == "k":
            out.append(num(h24 or 24, cnt))
        elif c == "K":
            out.append(num(h24 % 12, cnt))
        elif c == "h":
            out.append(num(h24 % 12 or 12, cnt))
        elif c == "m":
            out.append(num(dt.minute, cnt))
        elif c == "s":
            out.append(num(dt.second, cnt))
        elif c == "S":
            out.append(num(dt.microsecond // 1000, cnt))
        elif c == "z":
            out.append(dt.tzname() or (time.tzname[0] if time.tzname else ""))
        elif c == "Z":
            off = dt.utcoffset() if dt.tzinfo else _dt.timedelta(seconds=-time.timezone)
            secs = int(off.total_seconds()) if off else 0
            out.append(f"{'+' if secs >= 0 else '-'}{abs(secs) // 3600:02d}{abs(secs) % 3600 // 60:02d}")
        else:
            raise _err("xnc.e_syntax")
    return "".join(out)


def _now(ctx, fmt):
    return _date_format(_text_arg(fmt), ctx.clock(), ctx.lang)


def _random_fn(ctx):
    return ctx.rng.random()


def _uuid_fn(ctx):
    return str(_uuid.UUID(int=ctx.rng.getrandbits(128), version=4))


def _trim(ctx, s):
    return _text_arg(s).strip()


# nom → (kamida, ko'pi bilan, funksiya(ctx, *args)); `if` — yalqov, `_run` ichida
_FUNCS: dict[str, tuple[int, int, Callable]] = {
    # matematik
    "abs": (1, 1, _abs), "acos": (1, 1, _atrig(math.acos)), "acot": (1, 1, _atrig(lambda x: math.atan(1 / x))),
    "asec": (1, 1, _atrig(lambda x: math.acos(1 / x))), "asin": (1, 1, _atrig(math.asin)), "atan": (1, 1, _atrig(math.atan)),
    "ceil": (1, 1, _ceil), "cos": (1, 1, _trig(math.cos)), "cosh": (1, 1, _f(math.cosh)),
    "cot": (1, 1, _trig(lambda x: 1 / math.tan(x))), "coth": (1, 1, _f(lambda x: 1 / math.tanh(x))), "exp": (1, 1, _f(math.exp)),
    "floor": (1, 1, _floor), "ln": (1, 1, _f(math.log)), "log": (1, 1, _f(_log10)), "log2": (1, 1, _f(math.log2)),
    "logx": (2, 2, _f(_logx)), "max": (1, 50, _minmax(max)), "min": (1, 50, _minmax(min)), "random": (0, 0, _random_fn),
    "round": (1, 2, _round), "sec": (1, 1, _trig(lambda x: 1 / math.cos(x))), "sign": (1, 1, _sign), "sin": (1, 1, _trig(math.sin)),
    "sinh": (1, 1, _f(math.sinh)), "sqrt": (1, 1, _f(math.sqrt)), "tan": (1, 1, _trig(math.tan)), "tanh": (1, 1, _f(math.tanh)),
    # aralash
    "calculate": (1, 1, _calculate), "format": (2, 2, _format), "now": (1, 1, _now), "uuid": (0, 0, _uuid_fn),
    # matn
    "len": (1, 1, lambda c, s: len(_text_arg(s))), "mid": (3, 3, _mid), "left": (2, 2, _left), "right": (2, 2, _right),
    "lspace": (3, 3, _lspace), "rspace": (3, 3, _rspace), "rept": (2, 2, _rept),
    "ns": (1, 1, lambda c, s: "" if s is None else to_text(s)),
    "empty": (1, 1, lambda c, s: s is None or to_text(s) == ""),
    "trim": (1, 1, _trim), "ltrim": (1, 1, lambda c, s: _text_arg(s).lstrip()), "rtrim": (1, 1, lambda c, s: _text_arg(s).rstrip()),
    "ucase": (1, 1, lambda c, s: _text_arg(s).upper()), "lcase": (1, 1, lambda c, s: _text_arg(s).lower()),
    "find": (2, 3, _find), "findr": (2, 3, _findr),
    "replace": (3, 3, lambda c, s, a, b: _text_arg(s).replace(_text_arg(a), _text_arg(b)) if _text_arg(a) else _text_arg(s)),
    "startswith": (2, 2, lambda c, s, p: _text_arg(s).startswith(_text_arg(p))),
    "endswith": (2, 2, lambda c, s, p: _text_arg(s).endswith(_text_arg(p))),
    "double": (1, 1, _double), "integer": (1, 1, _integer), "boolean": (1, 1, _boolean), "translit": (1, 1, _translit),
    "crc16": (1, 1, _crc16), "crc32": (1, 1, _crc32),
    # sonli o'zgartirishlar
    "dectohex": (1, 1, _conv_dec("x")), "hextodec": (1, 1, _conv_to_dec(16)), "dectooct": (1, 1, _conv_dec("o")),
    "octtodec": (1, 1, _conv_to_dec(8)), "dectobin": (1, 1, _conv_dec("b")), "bintodec": (1, 1, _conv_to_dec(2)),
    "roman": (1, 1, _roman),
}
_IMPURE = {"random", "uuid", "now"}

# yordam/avtoto'ldirish uchun funksiya ro'yxati (guruh, nom, imzo)
FUNCTION_GROUPS: dict[str, list[tuple[str, str]]] = {
    "math": [("abs", "abs(x)"), ("acos", "acos(x)"), ("acot", "acot(x)"), ("asec", "asec(x)"), ("asin", "asin(x)"),
             ("atan", "atan(x)"), ("ceil", "ceil(x)"), ("cos", "cos(x)"), ("cosh", "cosh(x)"), ("cot", "cot(x)"),
             ("coth", "coth(x)"), ("exp", "exp(x)"), ("floor", "floor(x)"), ("ln", "ln(x)"), ("log", "log(x)"),
             ("log2", "log2(x)"), ("logx", "logx(x, base)"), ("max", "max(a, b, …)"), ("min", "min(a, b, …)"),
             ("random", "random()"), ("round", "round(x[, n])"), ("sec", "sec(x)"), ("sign", "sign(x)"), ("sin", "sin(x)"),
             ("sinh", "sinh(x)"), ("sqrt", "sqrt(x)"), ("tan", "tan(x)"), ("tanh", "tanh(x)")],
    "misc": [("calculate", "calculate(text)"), ("if", "if(cond, a, b)"), ("format", "format(pattern, number)"),
             ("now", "now(pattern)"), ("uuid", "UUID()")],
    "text": [("len", "len(s)"), ("mid", "mid(s, start, length)"), ("left", "left(s, n)"), ("right", "right(s, n)"),
             ("lspace", "lspace(s, n, ch)"), ("rspace", "rspace(s, n, ch)"), ("rept", "rept(s, n)"), ("ns", "ns(s)"),
             ("empty", "empty(s)"), ("trim", "trim(s)"), ("ltrim", "ltrim(s)"), ("rtrim", "rtrim(s)"), ("ucase", "ucase(s)"),
             ("lcase", "lcase(s)"), ("find", "find(s, sub[, start])"), ("findr", "findr(s, sub[, start])"),
             ("replace", "replace(s, old, new)"), ("startswith", "startswith(s, p)"), ("endswith", "endswith(s, p)"),
             ("double", "double(s)"), ("integer", "integer(s)"), ("boolean", "boolean(s)"), ("translit", "translit(s)"),
             ("crc16", "crc16(s)"), ("crc32", "crc32(s)")],
    "convert": [("dectohex", "DecToHex(n)"), ("hextodec", "HexToDec(s)"), ("dectooct", "DecToOct(n)"), ("octtodec", "OctToDec(s)"),
                ("dectobin", "DecToBin(n)"), ("bintodec", "BinToDec(s)"), ("roman", "roman(n)")],
}


def function_names() -> list[str]:
    return sorted({*_FUNCS, "if"})


# ───────────────────────── Hisoblash ─────────────────────────
def _run(node, ctx: Ctx, depth: int):
    ctx.steps += 1
    if ctx.steps > MAX_STEPS or depth > MAX_EVAL_DEPTH:
        raise _err("xnc.e_steps")
    kind = node[0]
    if kind == "lit":
        return node[1]
    if kind == "var":
        name = node[1]
        if name in ctx.env:
            return ctx.env[name]
        low = name.lower()
        if low in _CONST:
            return _CONST[low]
        raise _err("xnc.e_unknown_var", name=name)
    if kind == "bin":
        return _arith(node[1], _run(node[2], ctx, depth + 1), _run(node[3], ctx, depth + 1))
    if kind == "un":
        v = _num(_run(node[2], ctx, depth + 1))
        return v if node[1] == "+" else _norm_num(-v)
    if kind == "cmp":
        left = _run(node[1], ctx, depth + 1)
        for op, right_node in node[2]:
            right = _run(right_node, ctx, depth + 1)
            if not _compare(op, left, right):
                return False
            left = right
        return True
    if kind == "and":
        return _truthy(_run(node[1], ctx, depth + 1)) and _truthy(_run(node[2], ctx, depth + 1))
    if kind == "or":
        return _truthy(_run(node[1], ctx, depth + 1)) or _truthy(_run(node[2], ctx, depth + 1))
    if kind == "xor":
        return _truthy(_run(node[1], ctx, depth + 1)) != _truthy(_run(node[2], ctx, depth + 1))
    if kind == "not":
        return not _truthy(_run(node[1], ctx, depth + 1))
    if kind == "if":                                          # a if shart else b
        return _run(node[2], ctx, depth + 1) if _truthy(_run(node[1], ctx, depth + 1)) else _run(node[3], ctx, depth + 1)
    if kind == "call":
        name, args = node[1], node[2]
        if name == "if":                                      # yalqov: faqat tanlangan shoxcha hisoblanadi
            if len(args) != 3:
                raise _err("xnc.e_func_args", name="if")
            return _run(args[1], ctx, depth + 1) if _truthy(_run(args[0], ctx, depth + 1)) else _run(args[2], ctx, depth + 1)
        spec = _FUNCS.get(name)
        if spec is None:
            raise _err("xnc.e_unknown_func", name=name)
        lo, hi, fn = spec
        if not lo <= len(args) <= hi:
            raise _err("xnc.e_func_args", name=name)
        vals = [_run(a, ctx, depth + 1) for a in args]
        r = fn(ctx, *vals)
        if isinstance(r, str) and len(r) > MAX_TEXT:
            raise _err("xnc.e_too_long", n=MAX_TEXT)
        return _norm_num(r) if isinstance(r, (int, float)) and not isinstance(r, bool) else r
    raise _err("xnc.e_forbidden")


def evaluate(expr, env: dict | None = None, *, degrees: bool = False, max_len: int = MAX_SRC,
             clock: Callable[[], _dt.datetime] | None = None, rng: _random.Random | None = None, lang: str = "ru"):
    """Ifodani hisoblaydi. Qaytaradi: None | bool | int | float | str. Xato — ValueError (foydalanuvchi tilida)."""
    if isinstance(expr, bool):
        return expr
    if isinstance(expr, (int, float)):
        return expr
    src = str(expr).strip()
    if len(src) > max_len:
        raise _err("xnc.e_too_long", n=max_len)
    if not src:
        raise _err("xnc.e_syntax")
    try:
        return _run(_compile(src), Ctx(env, degrees, clock, rng, lang, max_len), 0)
    except RecursionError as e:
        raise _err("xnc.e_steps") from e


def eval_number(expr, env: dict | None = None, *, degrees: bool = False, max_len: int = 200) -> float:
    """Sonli ifoda (XNC parametrlari): mantiqiy natija 1.0 / 0.0; matn/null — xato."""
    v = evaluate(expr, env, degrees=degrees, max_len=max_len)
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    raise _err("xnc.e_type")               # matn / null — son kutilgan joyda (W18: «operand turi noto'g'ri»)
