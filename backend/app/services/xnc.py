"""XNC (CNC) dasturi: statistika, narx va chizma.

Dastur — buyruqlar daraxti (XncCommand). Parametrlar son yoki ifoda bo'lishi mumkin
(masalan DP="dz", X="dx/2"). Ifodalar xavfsiz hisoblanadi (`eval` ishlatilmaydi) — umumiy dvigatel `services/expr.py`:
o'zgaruvchilar (dx, dy, dz, J3 dagi allowanceT/B/L/R, etj…ert, xncSide, bySizeDetail, origin.x/y, xncIndex… +
Var/Par/Set), operatorlar va 67 funksiya (sin/cos radianda, if(c,a,b), min, max, round, …).
«Включить» (`enabled`) o'chirilgan buyruq va uning bolalari bajarilmaydi. Berilmagan atribut — shu turdagi oldingi
buyruqdagi ifoda (name, x, y, z, dp, ac, as, r, cx, cy …); frontal teshik massivi: AC (soni), AS (qadam),
AV (true — Y bo'ylab, false — X bo'ylab).

Koordinatalar: boshlanish nuqtasi (origin) standart — chap-yuqori burchak, X o'ngga, Y pastga.
Buyruqlar:
  DrillFront X Y D DP [T]          — yuzadan teshik (DP ≥ dz — o'tuvchi)
  DrillLeft/Right  Y Z D DP [T]    — chap/o'ng qirradan teshik
  DrillTop/Bottom  X Z D DP [T]    — yuqori/pastki qirradan teshik
  MillStart X Y DP T D             — frezaning kirish nuqtasi, keyin MillLine / MillArc / MillArcCenter / MillArc3P
  MillArc X Y R [DIR]              — radius bo'yicha yoy (R < 0 — teskari yo'nalish); MillArcCenter X Y CX CY [DIR];
                                     MillArc3P X Y X2 Y2 (X2,Y2 — oraliq nuqta)
  Groove X1 Y1 X2 Y2 DP W [C P]    — paz (arra bilan); C — korreksiya (0 markaz, 1 o'ng, 2 chap)
  Origin X Y                       — koordinata boshini (X, Y) ga o'rnatadi (asosiy boshlang'ichga nisbatan)
Frezalash kengaytmalari (W1):
  MillStart + SDP (chuqurlikka qadam), SXY (tekislikdagi qadam, standart D/2), IN / OUT (kirish / chiqish turi),
    C (korreksiya: 0 markaz, 1 o'ng, 2 chap, 3 cho'ntak). C=3 kontur uzunligi «длина фрезерования» ga KIRMAYDI
    (`POCKET_COUNTS_IN_LENGTH`; korxona fayllaridagi saqlangan countMill=0 bilan tasdiqlangan).
  MillFillet R                     — oldingi va keyingi kontur segmenti orasidagi burchakni R radius bilan yumaloqlaydi:
    oldingi segment qisqaradi, orasiga markazli yoy qo'shiladi (qo'shnilar: MillLine yoki yoy — chiziq–yoy, yoy–chiziq,
    yoy–yoy ham; geometriya — xnc_fillet.py).
  MillRect X Y L W [A R D]         — to'rtburchak: (X, Y) — MARKAZ (`RECT_XY_IS_CENTER`), A — burilish (gradus),
    R — burchak radiusi. MillEllipse X Y RL RW [A]: markaz, yarim o'qlar, burilish (eski A, B — to'liq o'qlar).
Par (parametr): name, value (standart), label, type (double|integer|boolean|string), visible, suffix, readonly —
  qiymat operatsiyadagi `XNCParams.par_values[name]` dan olinadi (yo'q bo'lsa — value). `string` (W18): qiymat — matn
  (ifoda emas; `PAR_STRING_LITERAL`), ifodalarda satr (`par + '.nc'`, `len(par)`, `par = 'abc'`); Var type=string ham bor.
Boshqaruv (J2): If{cond} [+ Else] / While{cond} / DoWhile{cond} — `children` ichidagi buyruqlar bajariladi;
Sub{name} — qism dastur (children), Call{name}; Ret, Break (Brk), Continue (Con); Err{text} — xato xabari.
Cheksiz sikldan himoya: har sikl ≤ MAX_LOOP_ITER iteratsiya, jami ≤ MAX_STEPS qadam.
Ifodadagi xato jim 0 ga aylanmaydi: `warnings` va `errors` hisoblagichiga tushadi, noto'g'ri koordinatali
teshik bajarilmaydi (sanalmaydi, chizilmaydi).
"""
from __future__ import annotations

import math
import re
from html import escape

from ..i18n import _
from ..models import Operation, OpType, Project, XNCParams, XncCommand
from . import expr as _expr
from . import xnc_fillet as _F

MAX_EXPR = 200         # ifoda uzunligi (belgi)
MAX_VALUE = 1e6         # mebel detali uchun ma'nosiz katta qiymat (1 km dan ortiq) — xato
MAX_STEPS = 100_000     # dasturning jami bajariladigan buyruqlari (cheksiz tsiklga qarshi)
MAX_LOOP_ITER = 10_000  # bitta sikl iteratsiyalari
MAX_CALL_DEPTH = 32     # qism dasturlar ichma-ich chaqiruvi
MAX_OPS = 20_000        # dasturdan chiqadigan geometrik amallar
MAX_WARNINGS = 50       # xabarlar ro'yxati uzunligi (hisoblagich esa to'liq)
MAX_PARS = 200          # bir dasturdagi kiritiladigan parametrlar (Par) soni
MAX_PAR_STRING = 200    # matn (string) Par / Var qiymati uzunligi (belgi); `XNCParams.par_values` chegarasi bilan bir xil

# Qarorlar (yordamda aniq emas — bitta konstanta orqasida; tasdiqlanmagan taxminlar R_… hisobotida):
POCKET_COUNTS_IN_LENGTH = False   # C=3 (cho'ntak) kontur uzunligi countMill ga kirmaydi (korpusda 4 dastur: saqlangan 0)
RECT_XY_IS_CENTER = True          # MillRect (X, Y) — markaz (yordam rasmida); False — chap-yuqori burchak
ANGLE_DEGREES = True              # MillRect / MillEllipse «A» burilish burchagi gradusda (ifodalardagi trig — radian)
ELLIPSE_TOL = 0.05                # ellipsni siniq chiziqqa yaqinlashtirish xatosi, mm
PROG_MSG_INTERPOLATE = True       # mahsulot dasturi (W12): Msg / Err matnidagi `{ifoda}` qiymat bilan almashtiriladi (yordamda yo'q ❓)
PAR_STRING_LITERAL = True         # Par type=string: `value` (standart) va kiritilgan qiymat — MATN (ifoda emas). False — ifoda sifatida
                                  # hisoblanadi (masalan 'abc' + 'd'), natija matnga aylantiriladi ❓ (yordamda matn turi tavsifi yo'q)
# Mahsulot dasturida ruxsat etilgan (boshqaruv) buyruqlar — geometrik buyruqlar quruq rejimda bajarilmaydi (ogohlantirish)
CONTROL_CMDS = frozenset({"Com", "Par", "Var", "Set", "If", "Else", "While", "DoWhile", "Break", "Continue", "Sub", "Call",
                          "Ret", "Msg", "Err"})

# Asboblar jadvali (sozlama «Настройки → XNC → Инструменты», W8): buyruqdagi `T` nomi bo'yicha diametr (`D`) va teshik chuqurligi
# (`DP`) zaxirasi. Ustuvorlik: buyruqdagi qiymat → dasturdagi `Tool` → sozlama jadvali → standart. Jadvalni `api_xnc` ulaydi
# (`set_tool_library_provider`); ulanmagan bo'lsa (skriptlar, korpus tekshiruvi) hisob avvalgidek, faqat dasturga qarab.
_TOOL_LIB_PROVIDER = None
_DRILL_PLANE = {"DrillFront": "front", "DrillLeft": "left", "DrillRight": "right", "DrillTop": "top", "DrillBottom": "bottom"}


def set_tool_library_provider(fn) -> None:
    """fn() → `.find(nom, tekislik)` metodli jadval (services.xnc_tools.ToolLib) yoki None."""
    global _TOOL_LIB_PROVIDER
    _TOOL_LIB_PROVIDER = fn


def _default_tool_lib():
    fn = _TOOL_LIB_PROVIDER
    if fn is None:
        return None
    try:
        return fn()
    except Exception:  # noqa: BLE001 — sozlama xatosi hisobni buzmasin
        return None


# ───────────────────────── Ifoda hisoblagich ─────────────────────────
# Umumiy dvigatel: services/expr.py (tipli: butun/haqiqiy/mantiqiy/matn; `if()`, `=`, `<>`, `^`, `xor`, 67 funksiya).
# XNC parametrlari — sonli ifodalar: mantiqiy natija 1.0 / 0.0, matn — xato. Burchaklar radianda (yordam misollari:
# cos(pi) = −1); gradusda yozilgan shablonlar uchun `sin(a*pi/180)`.
XNC_DEGREES = False

# o'zgaruvchilar: detaldan hisoblanmaganda (bog'lanmagan operatsiya) — standart qiymatlar
DEFAULT_VARS: dict[str, float] = {
    "allowanceT": 0.0, "allowanceB": 0.0, "allowanceL": 0.0, "allowanceR": 0.0,
    "etj": 0.0, "ett": 0.0, "ebj": 0.0, "ebt": 0.0, "elj": 0.0, "elt": 0.0, "erj": 0.0, "ert": 0.0,
    "xncSide": 1.0, "bySizeDetail": 1.0, "xncIndex": 1.0, "xncIndexInPart": 1.0,
    "origin.x": 0.0, "origin.y": 0.0,
}


def eval_expr(expr, env: dict[str, float]) -> float:
    """Ifodani hisoblaydi (son). Xato — ValueError (matni foydalanuvchi tilida) yoki ZeroDivisionError /
    OverflowError. Mantiqiy natija 1.0 / 0.0."""
    return _expr.eval_number(expr, env, degrees=XNC_DEGREES, max_len=MAX_EXPR)

def _describe(e: BaseException) -> str:
    if isinstance(e, ZeroDivisionError):
        return _("xnc.e_zero")
    if isinstance(e, OverflowError):
        return _("xnc.e_range")
    if isinstance(e, (RecursionError, MemoryError)):
        return _("xnc.e_forbidden")
    if isinstance(e, ValueError):
        return str(e) or _("xnc.e_domain")
    return _("xnc.e_domain")


# ───────────────────────── Dasturni bajarish ─────────────────────────
class EvalOps(list):
    """Dastur «yoyilgan» amallari ro'yxati (+ xato hisoblagichi, xabarlar va Par parametrlari holati)."""
    problems: int = 0
    messages: list
    params: list            # bajarilgan Par buyruqlari: name, label, type, value, default, visible, readonly, suffix
    notes: list             # Msg / Err (W12): {level: info | error, text, n} — mahsulot dasturi («Сообщения»); XNC hisobiga ta'sir qilmaydi
    violations: int = 0     # bajarilgan Err buyruqlari soni (cheklov buzilishi; xabarlar ro'yxati qirqilsa ham to'liq)
    vars: dict              # quruq rejim (evaluate_control): dastur oxiridagi o'zgaruvchilar

    def __init__(self):
        super().__init__()
        self.messages = []
        self.params = []
        self.notes = []
        self.vars = {}


# buyruq → (guruh, oldingi qiymat olinadigan atributlar); freza buyruqlari bitta guruhda (kontur davomi)
_INHERIT: dict[str, tuple[str, tuple[str, ...]]] = {
    "DrillFront": ("drill_f", ("T", "X", "Y", "DP", "AC", "AS")),
    "DrillLeft": ("drill_l", ("T", "Y", "Z", "DP")), "DrillRight": ("drill_r", ("T", "Y", "Z", "DP")),
    "DrillTop": ("drill_t", ("T", "X", "Z", "DP")), "DrillBottom": ("drill_b", ("T", "X", "Z", "DP")),
    "MillStart": ("mill", ("T", "X", "Y", "DP")), "MillLine": ("mill", ("X", "Y", "DP")),
    "MillArc": ("mill", ("X", "Y", "DP", "R")), "MillArcCenter": ("mill", ("X", "Y", "CX", "CY", "DP")),
    "MillFillet": ("fillet", ("R",)),
    "Groove": ("groove", ("T", "X1", "Y1", "DP")),
}
_SIG_BREAK, _SIG_CONT, _SIG_RET, _SIG_STOP = "break", "continue", "ret", "stop"
_MILL = ("MillStart", "MillLine", "MillArc", "MillArcCenter", "MillArc3P")
_SEGMENTS = _MILL[1:]                  # kontur segmentlari (MillFillet qo'shnilari)
_NAN = float("nan")


def par_type(raw) -> str:
    """Par turi: double (standart) | integer | boolean | string (matn, W18)."""
    t = str(raw or "").strip().lower()
    if t in ("int", "integer"):
        return "integer"
    if t in ("bool", "boolean"):
        return "boolean"
    if t in ("str", "string", "text"):
        return "string"
    return "double"


def coerce_par(v: float, typ: str) -> float:
    """Par qiymatini turiga keltirish: butun — kasr qismi tashlanadi, mantiqiy — 1.0 / 0.0."""
    if typ == "integer":
        return float(int(v))
    if typ == "boolean":
        return 1.0 if v == v and v != 0 else 0.0
    return v


def plain_text(v) -> str:
    """Matn Par / Var qiymati: son bo'lsa «5.0» emas «5» (UI «123» ni songa aylantirgan bo'lishi mumkin); bool — true/false."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return str(int(v)) if v == v and abs(v) < 1e15 and v == int(v) else repr(v)
    return str(v)


class _Run:
    def __init__(self, dx: float, dy: float, dz: float, variables: dict | None, pars: dict | None = None, tool_lib=None,
                 dry: bool = False):
        self.lib = tool_lib or None                     # sozlamadagi asboblar jadvali (zaxira)
        self.cur_n = ""                                 # bajarilayotgan buyruq yo'li («2.3») — amallarga yoziladi
        # chizmada belgilash uchun: buyruqning daraxtdagi haqiqiy yo'li (0 dan, «1.2» — frontend `pathKey` bilan bir xil) va
        # chaqiruv (Call) joylari — Sub tanasi Call orqali bajarilsa, amal Sub ichidagi buyruqqa ham, Call qatoriga ham tegishli
        self.cur_src = ""
        self.call_src: list[str] = []
        self.sub_src: dict[str, str] = {}               # Sub nomi → daraxtdagi yo'li (0 dan)
        # dry — «quruq» rejim (mahsulot dasturi, W12): faqat boshqaruv/o'zgaruvchi buyruqlari; geometriya ham, dx/dy/dz ham,
        # detal o'zgaruvchilari ham yo'q (ularga murojaat — «noma'lum o'zgaruvchi»)
        self.dry = dry
        self.env: dict[str, float] = {} if dry else dict(DEFAULT_VARS)
        for k, v in (variables or {}).items():
            try:
                self.env[str(k)] = float(v)
            except (TypeError, ValueError):
                pass
        if not dry:
            self.env.update(dx=dx, dy=dy, dz=dz)
        self.seed = set(self.env)                       # tashqaridan berilgan nomlar (dastur natijasidan chiqariladi)
        self.defined: set[str] = set()                  # dastur o'zi e'lon qilgan / o'zgartirgan nomlar (Par, Var, Set)
        self.pars: dict = dict(pars or {})            # operatsiyada kiritilgan Par qiymatlari (nom → qiymat/ifoda)
        self.out = EvalOps()
        self.tools: dict[str, float] = {}
        self.subs: dict[str, list] = {}
        self.prev: dict[str, dict] = {}              # «oldingi qiymat» qoidasi: guruh → {atribut: ifoda}
        self.ox = self.oy = 0.0
        self.steps = 0
        self.depth = 0
        self.loop_depth = 0
        self.stopped = False

    # --- xabarlar ---
    def warn(self, msg: str, /, **kw) -> None:
        self.out.problems += 1
        if len(self.out.messages) < MAX_WARNINGS:
            text = _(msg, **kw)
            if self.dry and text.startswith("XNC"):      # mahsulot dasturida «XNC 2.1 (Var): …» emas, «Программа 2.1 (Var): …»
                text = _("pp.label") + text[3:]
            self.out.messages.append(text)

    def note(self, level: str, p: dict, n: str) -> None:
        """Msg (info) / Err (error): matn va buyruq yo'li. Quruq rejimda matndagi `{ifoda}` hisoblanadi (PROG_MSG_INTERPOLATE)."""
        text = str(p.get("text", "") or "")
        if self.dry and PROG_MSG_INTERPOLATE and "{" in text:
            text = self.interpolate(text, n)
        if level == "error":
            self.out.violations += 1
        if len(self.out.notes) < MAX_WARNINGS:
            self.out.notes.append(dict(level=level, text=text or ("Err" if level == "error" else ""), n=n))

    def interpolate(self, text: str, n: str) -> str:
        """`{ifoda}` → qiymat (sonlar: butun bo'lsa nuqtasiz). Xato ifoda matnda o'z holicha qoladi va ogohlantirish yoziladi."""
        def rep(m) -> str:
            try:
                v = _expr.evaluate(m.group(1), self.env, degrees=XNC_DEGREES, max_len=MAX_EXPR)
                if isinstance(v, float) and math.isfinite(v):
                    return str(int(v)) if v == int(v) and abs(v) < 1e15 else f"{v:.6g}"
                return _expr.to_text(v)
            except Exception as e:  # noqa: BLE001 — foydalanuvchi ifodasi server xatosiga aylanmasin
                self.warn("xnc.w_param", n=n, cmd="Msg", param="text", e=_describe(e))
                return m.group(0)
        return re.sub(r"\{([^{}]{1,200})\}", rep, text)

    # --- parametrlar ---
    def num(self, c: XncCommand, p: dict, key: str, n: str, default: float = 0.0, required: bool = False):
        """Parametr qiymati. Berilmagan / bo'sh — standart qiymat. Noto'g'ri ifoda (sintaksis, noma'lum o'zgaruvchi,
        0 ga bo'lish, toshish, cheksiz) — xabar yoziladi; required bo'lsa None (buyruq bajarilmaydi), aks holda
        standart qiymat."""
        if key not in p or p[key] in ("", None):
            return default
        try:
            v = float(eval_expr(p[key], self.env))
            if not math.isfinite(v) or abs(v) > MAX_VALUE:
                raise ValueError(_("xnc.e_range"))
        except Exception as e:  # noqa: BLE001 — foydalanuvchi ifodasi server xatosiga aylanmasin
            self.warn("xnc.w_param", n=n, cmd=c.cmd, param=key, e=_describe(e))
            return None if required else default
        return v

    def flag(self, c: XncCommand, p: dict, key: str, n: str, default: bool = False) -> bool:
        """Mantiqiy parametr (true/false, 1/0 yoki ifoda)."""
        raw = p.get(key)
        if raw in (None, ""):
            return default
        try:
            v = _expr.evaluate(raw, self.env, degrees=XNC_DEGREES, max_len=MAX_EXPR)
            return bool(_expr._truthy(v))
        except Exception as e:  # noqa: BLE001
            self.warn("xnc.w_param", n=n, cmd=c.cmd, param=key, e=_describe(e))
            return default

    def inherit(self, cmd: str, p: dict) -> dict:
        """Berilmagan atribut — shu turdagi oldingi buyruqdagi ifoda (GibLab qoidasi)."""
        spec = _INHERIT.get(cmd)
        if spec is None:
            return p
        group, keys = spec
        prev = self.prev.setdefault(group, {})
        out = dict(p)
        for k in keys:
            if cmd == "Groove" and k in ("X1", "Y1") and k[0] in p and p[k[0]] not in (None, ""):
                continue                                  # X / Y yozuvi ishlatilgan
            if out.get(k) in (None, ""):
                if k in prev:
                    out[k] = prev[k]
            else:
                prev[k] = out[k]
        return out

    def par(self, c: XncCommand, p: dict, n: str, name: str) -> None:
        """Par — shablon parametri: qiymat operatsiyada kiritilgan (`pars[name]`), yo'q bo'lsa — `value` ifodasi.
        `readonly` (ifoda) rost bo'lsa kiritilgan qiymat e'tiborga olinmaydi (qiymat doim `value` dan). `visible` (ifoda) —
        kiritish maydoni ko'rinadimi (hisobga ta'sir qilmaydi). Natija `out.params` ga yoziladi (UI formasi uchun)."""
        typ = par_type(p.get("type"))
        if typ == "string":
            self.par_string(c, p, n, name)
            return
        default = self.num(c, p, "value", n, 0.0, True)
        visible = self.flag(c, p, "visible", n, True)
        readonly = self.flag(c, p, "readonly", n, False)
        v = default
        ov = self.pars.get(name)
        if not readonly and ov not in (None, ""):
            try:
                v = float(eval_expr(ov, self.env)) if isinstance(ov, str) else float(ov)
                if not math.isfinite(v) or abs(v) > MAX_VALUE:
                    raise ValueError(_("xnc.e_range"))
            except Exception as e:  # noqa: BLE001 — kiritilgan qiymat noto'g'ri: standart qiymatga qaytiladi
                self.warn("xnc.w_param", n=n, cmd=c.cmd, param="value", e=_describe(e))
                v = default
        if v is not None:
            v = coerce_par(v, typ)
            self.env[name] = v
            self.defined.add(name)
        if default is not None:
            default = coerce_par(default, typ)
        if len(self.out.params) < MAX_PARS:
            self.out.params.append(dict(name=name, label=str(p.get("label", "") or ""), type=typ,
                                        suffix=str(p.get("suffix", "") or ""), default=default, value=v,
                                        visible=visible, readonly=readonly, n=n))

    def text(self, c: XncCommand, raw, n: str, param: str) -> str | None:
        """Matn qiymati (W18): `PAR_STRING_LITERAL` — o'zi (son bo'lsa «5.0» emas «5»), aks holda ifoda natijasi matnga
        aylantiriladi. Uzun matn `MAX_PAR_STRING` gacha qisqartiriladi (xabar bilan); ifoda xatosi — xabar + None."""
        try:
            if PAR_STRING_LITERAL:
                s = plain_text(raw)
            else:
                s = _expr.to_text(_expr.evaluate(raw, self.env, degrees=XNC_DEGREES, max_len=MAX_EXPR))
        except Exception as e:  # noqa: BLE001
            self.warn("xnc.w_param", n=n, cmd=c.cmd, param=param, e=_describe(e))
            return None
        if len(s) > MAX_PAR_STRING:
            self.warn("xnc.w_param", n=n, cmd=c.cmd, param=param, e=_("xnc.e_str_long", n=MAX_PAR_STRING))
            s = s[:MAX_PAR_STRING]
        return s

    def par_string(self, c: XncCommand, p: dict, n: str, name: str) -> None:
        """Matn (string) Par: standart — `value` (matn); operatsiyada kiritilgan qiymat (`pars[name]`) bo'sh bo'lmasa — shu
        (`readonly` rost bo'lsa kiritilgan qiymat e'tiborsiz). Qiymat o'zgaruvchiga matn sifatida yoziladi (ifodalarda satr:
        `par + '.nc'`, `len(par)`, `par = 'abc'` …); sonli parametrda ishlatilsa — «matn» xatosi (jim 0 emas)."""
        visible = self.flag(c, p, "visible", n, True)
        readonly = self.flag(c, p, "readonly", n, False)
        raw = p.get("value")
        default = self.text(c, raw, n, "value") if raw not in (None, "") else ""
        if default is None:
            default = ""
        v = default
        ov = self.pars.get(name)
        if not readonly and ov not in (None, ""):
            got = self.text(c, ov, n, "value")
            v = default if got is None else got
        self.env[name] = v
        self.defined.add(name)
        if len(self.out.params) < MAX_PARS:
            self.out.params.append(dict(name=name, label=str(p.get("label", "") or ""), type="string",
                                        suffix=str(p.get("suffix", "") or ""), default=default, value=v,
                                        visible=visible, readonly=readonly, n=n))

    def cond(self, c: XncCommand, p: dict, n: str) -> bool:
        raw = p.get("cond")
        if raw in (None, ""):
            self.warn("xnc.w_cond_empty", n=n, cmd=c.cmd)
            return False
        try:
            v = float(eval_expr(raw, self.env))
        except Exception as e:  # noqa: BLE001
            self.warn("xnc.w_cond_bad", n=n, cmd=c.cmd, e=_describe(e))
            return False
        return v == v and v != 0

    def emit(self, o: dict) -> None:
        if len(self.out) >= MAX_OPS:
            if not self.stopped:
                self.warn("xnc.w_ops_limit", max=MAX_OPS)
                self.stopped = True
            return
        o.setdefault("cmd_path", self.cur_n)
        o.setdefault("src", [self.cur_src, *reversed(self.call_src)] if self.cur_src else list(reversed(self.call_src)))
        self.out.append(o)

    # --- asboblar jadvali (sozlama) ---
    def tool_d(self, t: str, plane: str | None, default: float) -> float:
        """Asbob diametri: dasturdagi Tool → sozlama jadvali → standart."""
        if t in self.tools:
            return self.tools[t]
        lt = self.lib.find(t, plane) if self.lib and t else None
        return float(lt.d) if lt is not None else default

    def tool_dp(self, t: str, plane: str | None, default: float) -> float:
        """Teshik chuqurligi (DP berilmaganda): jadvaldagi asbob o'tuvchi bo'lsa — qalinlik, chuqurlik berilgan bo'lsa — shu."""
        lt = self.lib.find(t, plane) if self.lib and t else None
        if lt is None or lt.through:
            return default
        return float(lt.depth) if lt.depth else default

    # --- bajarish ---
    def collect_subs(self, lst: list, src: str = "") -> None:
        for i, c in enumerate(lst):
            if not c.enabled:
                continue
            if c.cmd == "Sub":
                nm = str(c.params.get("name", "")).strip()
                if nm:
                    self.subs[nm] = c.children
                    self.sub_src[nm] = f"{src}{i}"
            if c.children:
                self.collect_subs(c.children, f"{src}{i}.")

    def block(self, lst: list, path: str, src: str | None = None):
        """`path` — bajarilish yo'li («2.3», 1 dan; Call tanasi chaqiruv yo'li ostida), `src` — daraxtdagi haqiqiy yo'l prefiksi
        (0 dan; None — `path` bilan bir xil daraxt)."""
        last_if = None            # If/Else zanjiri: None — zanjir yo'q, True — shoxcha bajarilgan, False — yo'q
        if src is None:
            src = ".".join(str(int(q) - 1) for q in path.strip(".").split(".")) + "." if path else ""
        for i, c in enumerate(lst):
            n = f"{path}{i + 1}"
            sn = f"{src}{i}"
            self.steps += 1
            if self.stopped:
                return _SIG_STOP
            if self.steps > MAX_STEPS:
                self.warn("xnc.w_steps", max=MAX_STEPS)
                self.stopped = True
                return _SIG_STOP
            cmd = c.cmd
            p = c.params
            if cmd == "Com" or not c.enabled:             # izoh yoki «Включить» o'chirilgan — bolalari bilan o'tkaziladi
                continue
            if cmd == "If":
                last_if = self.cond(c, p, n)
                if last_if:
                    sig = self.block(c.children, n + ".", sn + ".")
                    if sig:
                        return sig
                continue
            if cmd == "Else":
                if last_if is None:
                    self.warn("xnc.w_else_alone", n=n)
                    continue
                has_cond = p.get("cond") not in (None, "")
                if last_if:                              # oldingi shoxcha bajarilgan
                    if not has_cond:
                        last_if = None
                    continue
                if has_cond:                             # «else if»
                    if self.cond(c, p, n):
                        last_if = True
                        sig = self.block(c.children, n + ".", sn + ".")
                        if sig:
                            return sig
                else:
                    last_if = None
                    sig = self.block(c.children, n + ".", sn + ".")
                    if sig:
                        return sig
                continue
            last_if = None
            if cmd in ("While", "DoWhile"):
                it = 0
                self.loop_depth += 1
                try:
                    while True:
                        if cmd == "While" and not self.cond(c, p, n):
                            break
                        it += 1
                        if it > MAX_LOOP_ITER:
                            self.warn("xnc.w_loop_limit", n=n, cmd=cmd, max=MAX_LOOP_ITER)
                            break
                        sig = self.block(c.children, n + ".", sn + ".")
                        if sig == _SIG_BREAK:
                            break
                        if sig in (_SIG_RET, _SIG_STOP):
                            return sig
                        if cmd == "DoWhile" and not self.cond(c, p, n):
                            break
                finally:
                    self.loop_depth -= 1
                continue
            if cmd in ("Break", "Continue"):
                if self.loop_depth <= 0:
                    self.warn("xnc.w_flow_outside", n=n, cmd=cmd)
                    continue
                return _SIG_BREAK if cmd == "Break" else _SIG_CONT
            if cmd == "Ret":
                return _SIG_RET
            if cmd == "Sub":                              # ta'rif — joyida bajarilmaydi (collect_subs da yig'ilgan)
                continue
            if cmd == "Call":
                name = str(p.get("name", "")).strip()
                body = self.subs.get(name)
                if body is None:
                    self.warn("xnc.w_sub_missing", n=n, name=name)
                    continue
                if self.depth >= MAX_CALL_DEPTH:
                    self.warn("xnc.w_depth", n=n, max=MAX_CALL_DEPTH)
                    continue
                self.depth += 1
                saved, self.loop_depth = self.loop_depth, 0
                self.call_src.append(sn)                  # Sub tanasidagi amallar shu Call qatoriga ham tegishli
                try:
                    sig = self.block(body, n + ".", self.sub_src.get(name, "") + ".")
                finally:
                    self.depth -= 1
                    self.loop_depth = saved
                    self.call_src.pop()
                if sig == _SIG_STOP:
                    return sig
                continue
            if cmd == "Msg":
                self.note("info", p, n)                   # XNC hisobiga ta'sir qilmaydi; mahsulot dasturida «Сообщения» ga tushadi
                continue
            if cmd == "Err":
                self.note("error", p, n)
                if not self.dry:                          # XNC da — avvalgidek ogohlantirish (xatolar hisoblagichiga kiradi)
                    self.warn("xnc.w_user_err", n=n, text=str(p.get("text", "")) or "Err")
                continue
            if self.dry and cmd not in CONTROL_CMDS:      # mahsulot dasturida geometriya yo'q: o'tkazib yuboriladi + ogohlantirish
                self.warn("pp.w_geometry", n=n, cmd=cmd)
                continue
            self.cur_src = sn
            self.command(c, p, n)
            if c.children:                                # oddiy buyruqning bolalari — undan keyin bajariladi
                sig = self.block(c.children, n + ".", sn + ".")
                if sig:
                    return sig
        return None

    def command(self, c: XncCommand, p: dict, n: str) -> None:
        cmd = c.cmd
        env, num = self.env, self.num
        dx, dy, dz = env.get("dx", 0.0), env.get("dy", 0.0), env.get("dz", 0.0)       # quruq rejimda (W12) yo'q
        self.cur_n = n
        p = self.inherit(cmd, p)
        if cmd == "Par":
            name = str(p.get("name", "")).strip()
            if name:
                self.par(c, p, n, name)
        elif cmd in ("Var", "Set"):
            name = str(p.get("name", "")).strip()
            if name and (par_type(p.get("type")) == "string" if cmd == "Var" else isinstance(env.get(name), str)):
                # matn o'zgaruvchisi (W18): Var type=string yoki matn Par / Var ga Set — ifoda natijasi matnga aylantiriladi
                raw = p.get("value")
                try:
                    s = _expr.to_text(_expr.evaluate(raw, env, degrees=XNC_DEGREES, max_len=MAX_EXPR)) if raw not in (None, "") else ""
                except Exception as e:  # noqa: BLE001 — foydalanuvchi ifodasi server xatosiga aylanmasin
                    self.warn("xnc.w_param", n=n, cmd=cmd, param="value", e=_describe(e))
                    s = None
                if s is not None:
                    if len(s) > MAX_PAR_STRING:
                        self.warn("xnc.w_param", n=n, cmd=cmd, param="value", e=_("xnc.e_str_long", n=MAX_PAR_STRING))
                        s = s[:MAX_PAR_STRING]
                    env[name] = s
                    self.defined.add(name)
            elif name:
                v = num(c, p, "value", n, 0.0, True)      # noto'g'ri ifoda — o'zgaruvchi e'lon qilinmaydi (keyin «noma'lum»)
                if v is not None:
                    if str(p.get("type", "")).strip().lower() in ("int", "integer"):
                        v = float(int(v))                 # butun tipli o'zgaruvchi — kasr qismi tashlanadi
                    env[name] = v
                    self.defined.add(name)
        elif cmd == "Tool":
            nm = str(p.get("N", p.get("name", "")))
            lt = self.lib.find(nm) if self.lib and not has_val(p, "D") else None      # D berilmagan — jadvaldagi asbob
            d = float(lt.d) if lt is not None else num(c, p, "D", n)
            self.tools[nm] = d
        elif cmd == "Origin":
            nx, ny = num(c, p, "X", n, self.ox, True), num(c, p, "Y", n, self.oy, True)
            if nx is not None and ny is not None:
                self.ox, self.oy = nx, ny
                env["origin.x"], env["origin.y"] = nx, ny
        elif cmd.startswith("Drill"):
            t = str(p.get("T", ""))
            need_x = cmd in ("DrillFront", "DrillTop", "DrillBottom")
            need_y = cmd in ("DrillFront", "DrillLeft", "DrillRight")
            X = num(c, p, "X", n, 0.0, need_x)
            Y = num(c, p, "Y", n, 0.0, need_y)
            if X is None or Y is None:
                return                                    # noto'g'ri koordinata — teshik bajarilmaydi
            Z = num(c, p, "Z", n, dz / 2)
            # qirra teshigi «Середина по Z» (M): true — qalinlik o'rtasida (Z e'tiborsiz), false — Z aniq koordinata.
            # M yozilmagan eski dasturlarda Z aniq koordinata (standart dz/2) sifatida qoladi.
            mid = cmd != "DrillFront" and p.get("M") not in (None, "") and self.flag(c, p, "M", n, True)
            if mid:
                Z = dz / 2
            plane = _DRILL_PLANE[cmd]
            d = num(c, p, "D", n, self.tool_d(t, plane, 5.0))
            dp = num(c, p, "DP", n, self.tool_dp(t, plane, dz))
            cnt = num(c, p, "count", n, 1.0)
            if need_x:
                X += self.ox
            if need_y:
                Y += self.oy
            # frontal teshik massivi: AC dona, AS qadam, AV — Y bo'ylab (true) yoki X bo'ylab (false)
            holes = [(X, Y)]
            if cmd == "DrillFront":
                ac = num(c, p, "AC", n, 1.0)
                step = num(c, p, "AS", n, 0.0)
                nh = max(1, min(1000, int(ac)))
                if nh > 1:
                    vert = self.flag(c, p, "AV", n)
                    holes = [(X, Y + i * step) if vert else (X + i * step, Y) for i in range(nh)]
            for hx, hy in holes:
                o = dict(kind=cmd, X=hx, Y=hy, Z=Z, D=d, DP=dp, T=t, count=max(1, min(1000, int(cnt))), M=bool(mid))
                # detal tashqarisidagi teshik (masalan, shablon kattaroq detal uchun yozilgan) — bajarilmaydi
                tol = 0.01
                if cmd == "DrillFront":
                    o["inside"] = -tol <= hx <= dx + tol and -tol <= hy <= dy + tol
                elif cmd in ("DrillLeft", "DrillRight"):
                    o["inside"] = -tol <= hy <= dy + tol
                else:
                    o["inside"] = -tol <= hx <= dx + tol
                self.emit(o)
        elif cmd in _MILL:
            t = str(p.get("T", ""))
            X, Y = num(c, p, "X", n, 0.0, True), num(c, p, "Y", n, 0.0, True)
            ok = X is not None and Y is not None
            dpv = num(c, p, "DP", n, _NAN)
            # kirish nuqtasining chuqurlik ifodasi hisoblanmasa (aniqlanmagan o'zgaruvchi) — kontur bajarilmaydi
            if cmd == "MillStart":
                ok = ok and ("DP" not in p or p["DP"] in ("", None) or math.isfinite(dpv))
            cx = num(c, p, "CX", n, _NAN)
            cy = num(c, p, "CY", n, _NAN)
            if cmd == "MillArcCenter" and any(k in p and p[k] not in ("", None) for k in ("CX", "CY")) \
                    and not (math.isfinite(cx) and math.isfinite(cy)):
                ok = False
            x2 = num(c, p, "X2", n, _NAN)
            y2 = num(c, p, "Y2", n, _NAN)
            if cmd == "MillArc3P" and not (math.isfinite(x2) and math.isfinite(y2)):
                x2, y2 = cx, cy                           # oraliq nuqta CX/CY orqali ham berilishi mumkin
            d = num(c, p, "D", n, self.tool_d(t, "front", 0.0))
            o = dict(kind=cmd, X=(X or 0.0) + self.ox, Y=(Y or 0.0) + self.oy,
                     CX=cx + self.ox, CY=cy + self.oy, X2=x2 + self.ox, Y2=y2 + self.oy,
                     R=num(c, p, "R", n, 0.0), DIR=str(p.get("DIR", "")),
                     D=d, DP=dpv if math.isfinite(dpv) else dz, T=t,
                     ok=ok, C=int(num(c, p, "C", n, 0.0)))
            if cmd == "MillStart":
                # chuqurlikka qadam (SDP), tekislikdagi qadam (SXY, standart D/2), kirish (IN) / chiqish (OUT) turi
                sxy = num(c, p, "SXY", n, _NAN)
                if not math.isfinite(sxy) and d and d > 0:
                    sxy = d / 2
                o.update(SDP=num(c, p, "SDP", n, _NAN), SXY=sxy, IN=int(num(c, p, "IN", n, 0.0)),
                         OUT=int(num(c, p, "OUT", n, 1.0)))
            self.emit(o)
        elif cmd == "MillFillet":                         # burchak yumaloqlash: evaluate() oxirida qo'llanadi
            self.emit(dict(kind="MillFillet", R=num(c, p, "R", n, 0.0), n=n))
        elif cmd == "MillRect":
            vals = [num(c, p, k, n, 0.0, k in "XYLW") for k in ("X", "Y", "L", "W")]
            ang = num(c, p, "A", n, 0.0)
            rad = num(c, p, "R", n, 0.0)
            ok = all(v is not None for v in vals)
            X, Y, L, W = (v or 0.0 for v in vals)
            if not RECT_XY_IS_CENTER:
                X, Y = X + L / 2, Y + W / 2
            t = str(p.get("T", ""))
            dpv = num(c, p, "DP", n, _NAN)
            self.emit(dict(kind="MillRect", X=X + self.ox, Y=Y + self.oy, L=L, W=W, A=ang, R=max(0.0, rad),
                           D=num(c, p, "D", n, self.tool_d(t, "front", 0.0)), DP=dpv if math.isfinite(dpv) else dz, T=t,
                           C=int(num(c, p, "C", n, 0.0)), ok=ok))
        elif cmd == "MillEllipse":
            legacy = not has_val(p, "RL") and has_val(p, "B")      # eski dastur: A, B — to'liq o'qlar, burilishsiz
            if legacy:
                vals = [num(c, p, "X", n, 0.0, True), num(c, p, "Y", n, 0.0, True),
                        (num(c, p, "A", n, 0.0, True) or 0.0) / 2, (num(c, p, "B", n, 0.0, True) or 0.0) / 2]
                ang = 0.0
            else:
                vals = [num(c, p, k, n, 0.0, True) for k in ("X", "Y", "RL", "RW")]
                ang = num(c, p, "A", n, 0.0)
            t = str(p.get("T", ""))
            dpv = num(c, p, "DP", n, _NAN)
            self.emit(dict(kind="MillEllipse", X=(vals[0] or 0.0) + self.ox, Y=(vals[1] or 0.0) + self.oy,
                           RL=abs(vals[2] or 0.0), RW=abs(vals[3] or 0.0), A=ang,
                           D=num(c, p, "D", n, self.tool_d(t, "front", 0.0)), DP=dpv if math.isfinite(dpv) else dz, T=t,
                           C=int(num(c, p, "C", n, 0.0)), ok=all(v is not None for v in vals)))
        elif cmd == "Groove":
            def has(k):
                return k in p and p[k] not in ("", None)
            kx = "X1" if has("X1") else ("X" if has("X") else None)       # X1/Y1 yo'q bo'lsa — X/Y
            ky = "Y1" if has("Y1") else ("Y" if has("Y") else None)
            x1 = num(c, p, kx, n, 0.0, True) if kx else 0.0
            y1 = num(c, p, ky, n, 0.0, True) if ky else 0.0
            ok = x1 is not None and y1 is not None
            x1, y1 = x1 or 0.0, y1 or 0.0
            if has("L") and not has("X2"):                                # uzunlik bilan: gorizontal paz
                ln = num(c, p, "L", n, 0.0, True)
                ok = ok and ln is not None
                x2, y2 = x1 + (ln or 0.0), y1
            else:
                x2 = num(c, p, "X2", n, x1, True)
                y2 = num(c, p, "Y2", n, y1, True)
                ok = ok and x2 is not None and y2 is not None
                x2, y2 = (x1 if x2 is None else x2), (y1 if y2 is None else y2)
            t = str(p.get("T", ""))
            dp = num(c, p, "DP", n, _NAN)
            ok = ok and ("DP" not in p or p["DP"] in ("", None) or math.isfinite(dp))
            self.emit(dict(kind="Groove", X1=x1 + self.ox, Y1=y1 + self.oy, X2=x2 + self.ox, Y2=y2 + self.oy,
                           DP=dp if math.isfinite(dp) else dz, W=num(c, p, "W", n, 4.0),
                           D=num(c, p, "D", n, self.tool_d(t, "front", 4.0)), T=t, ok=ok, C=int(num(c, p, "C", n, 0.0))))

    # --- burchak yumaloqlash (MillFillet) ---
    @staticmethod
    def _segment(o: dict, start):
        """Kontur amali (MillLine / MillArc* ) → `xnc_fillet.Seg` (boshi `start`); yoy geometriyasi hisoblanmasa — to'g'ri chiziq
        (chizma ham shunday chizadi)."""
        end = (o["X"], o["Y"])
        if o["kind"] != "MillLine":
            g = mill_arc(o["kind"], start, o)
            if g is not None:
                return _F.Seg(start, end, g[3], g[2])
        return _F.Seg(start, end)

    def apply_fillets(self) -> None:
        """MillFillet R: oldingi (A→P) va keyingi (P→B) kontur segmentlari orasidagi P burchagini R radius bilan yumaloqlaydi.
        Segmentlar to'g'ri chiziq (MillLine) yoki yoy (MillArc / MillArcCenter / MillArc3P) bo'lishi mumkin — geometriya
        `xnc_fillet.py` da (urinma aylana markazi, urinish nuqtalari). Oldingi segment T1 da tugaydi, orasiga markazli yoy qo'shiladi,
        keyingi segment T2 dan boshlanadi. Yoy qisqartirilsa u markazli shaklga (MillArcCenter) o'tadi (aylana o'zgarmaydi).
        Qo'shnilar kontur segmenti bo'lmasa (MillStart, MillRect …) — `w_fillet_geom`; urinma aylana qurib bo'lmasa — `w_fillet_none`;
        radius segmentlar uchun katta bo'lsa — `w_fillet_big`; burchak yo'q (urinma / bir chiziq) — jim; burchak o'zgarishsiz qoladi."""
        ops = self.out
        if not any(o["kind"] == "MillFillet" for o in ops):
            return
        res: list[dict] = []
        pos = before = None
        for i, o in enumerate(ops):
            k = o["kind"]
            if k == "MillStart":
                pos, before = (o["X"], o["Y"]), None
                res.append(o)
            elif k in _SEGMENTS:
                before, pos = pos, (o["X"], o["Y"])
                res.append(o)
            elif k == "MillFillet":
                r = o["R"]
                if not r or r <= 0:
                    continue
                prev = res[-1] if res else None
                nxt = ops[i + 1] if i + 1 < len(ops) else None
                if (prev is None or prev["kind"] not in _SEGMENTS or before is None or nxt is None
                        or nxt["kind"] not in _SEGMENTS):
                    self.warn("xnc.w_fillet_geom", n=o.get("n", ""))
                    continue
                if not (prev.get("ok", True) and nxt.get("ok", True)):
                    continue                                       # hisoblanmaydigan kontur: baribir bajarilmaydi
                s1 = self._segment(prev, before)
                s2 = self._segment(nxt, pos)
                if math.dist(s1.a, s1.b) < 1e-9 or math.dist(s2.a, s2.b) < 1e-9:
                    continue
                f = _F.fillet(s1, s2, r)
                if f == "flat":                                    # burchaksiz (to'g'ri chiziq / urinma) — yumaloqlanmaydi
                    continue
                if isinstance(f, str):
                    self.warn("xnc.w_fillet_none" if f == "none" else "xnc.w_fillet_big", n=o.get("n", ""), r=f"{r:g}")
                    continue
                rd = (lambda v: round(v, 6))                       # stanok uchun toza raqamlar (hisob shovqini yo'q)
                t1 = (rd(f.t1[0]), rd(f.t1[1]))
                t2 = (rd(f.t2[0]), rd(f.t2[1]))
                cen = (rd(f.center[0]), rd(f.center[1]))
                if s1.is_arc:                                      # qisqargan yoy: aylana o'sha, oxiri T1 (markazli shaklda)
                    prev.update(kind="MillArcCenter", CX=s1.c[0], CY=s1.c[1], DIR="true" if s1.ccw else "false",
                                R=0.0, X2=_NAN, Y2=_NAN)
                prev["X"], prev["Y"] = t1                          # oldingi segment qisqaradi
                if s2.is_arc:                                      # keyingi yoy T2 dan boshlanadi: aylana o'sha (markazli shaklda)
                    nxt.update(kind="MillArcCenter", CX=s2.c[0], CY=s2.c[1], DIR="true" if s2.ccw else "false",
                               R=0.0, X2=_NAN, Y2=_NAN)
                res.append(dict(kind="MillArcCenter", X=t2[0], Y=t2[1], CX=cen[0], CY=cen[1], X2=_NAN, Y2=_NAN,
                                R=0.0, DIR="true" if f.ccw else "false", D=prev["D"], DP=prev["DP"], T=prev["T"],
                                ok=prev["ok"], C=prev["C"], fillet=True, cmd_path=o.get("cmd_path", ""),
                                src=o.get("src", [])))
                before, pos = t1, t2
            else:
                res.append(o)
        ops[:] = res


def has_val(p: dict, key: str) -> bool:
    return key in p and p[key] not in ("", None)


def evaluate(cmds: list[XncCommand], dx: float, dy: float, dz: float, variables: dict | None = None,
             pars: dict | None = None, tool_lib=None) -> EvalOps:
    """Dasturni «yoyib» chiqadi: har geometrik amal hisoblangan qiymatlar bilan (chizma va statistika uchun).
    If/Else/While/DoWhile/Sub/Call/Ret/Break/Continue haqiqatan bajariladi. Natija — amallar ro'yxati;
    `.problems` — xatolar soni, `.messages` — xabarlar (foydalanuvchi tilida), `.params` — Par parametrlari holati.
    `pars` — operatsiyada kiritilgan Par qiymatlari (nom → qiymat). `tool_lib` — sozlamadagi asboblar jadvali (zaxira):
    None — ulangan joriy jadval (`set_tool_library_provider`), `{}` / bo'sh — jadvalsiz hisob. Har amalda `cmd_path` —
    buyruq yo'li («2.3», 1 dan boshlab, ichma-ich nuqta bilan); `src` — daraxtdagi manba yo'llari (0 dan, frontend `pathKey`):
    [buyruqning o'zi, Call qatorlari (ichkaridan tashqariga)] — chizmada buyruq bo'yicha belgilash uchun."""
    run = _Run(dx, dy, dz, variables, pars, _default_tool_lib() if tool_lib is None else tool_lib)
    run.collect_subs(cmds)
    run.block(cmds, "")
    run.apply_fillets()
    return run.out


def evaluate_control(cmds: list[XncCommand], variables: dict | None = None, pars: dict | None = None) -> EvalOps:
    """«Quruq» rejim (mahsulot dasturi, W12): faqat boshqaruv / o'zgaruvchi buyruqlari (CONTROL_CMDS) — geometrik buyruq
    bajarilmaydi (ogohlantirish), dx/dy/dz va detal o'zgaruvchilari yo'q. Natija: `.vars` — dastur oxiridagi o'zgaruvchilar
    (Par / Var / Set; `variables` bilan berilgan tashqi nomlarsiz), `.notes` — Msg (info) / Err (error), `.violations` —
    Err soni, `.messages` / `.problems` — ifoda va dastur xatolari, `.params` — Par holati. Tsikl / qadam chegaralari XNC bilan bir xil."""
    run = _Run(0.0, 0.0, 0.0, variables, pars, {}, dry=True)
    run.collect_subs(cmds)
    run.block(cmds, "")
    run.out.vars = {k: v for k, v in run.env.items() if k not in run.seed or k in run.defined}
    return run.out


def program_vars(x: XNCParams) -> dict[str, float]:
    """Ifodalardagi o'zgaruvchilar (J3): detaldan hisoblangan (part_vars) + operatsiyaning o'zi."""
    v = dict(DEFAULT_VARS)
    v.update(x.part_vars or {})
    v["xncSide"] = 1.0 if x.face_side else 0.0
    v["bySizeDetail"] = 1.0 if x.by_part_size else 0.0
    return v


# «Переменные» oynasi: tizim o'zgaruvchilari (tartib bilan) va turlari
SYSTEM_VARS: tuple[tuple[str, str], ...] = (
    ("allowanceB", "double"), ("allowanceL", "double"), ("allowanceR", "double"), ("allowanceT", "double"),
    ("bySizeDetail", "boolean"), ("dx", "double"), ("dy", "double"), ("dz", "double"),
    ("ebj", "double"), ("ebt", "double"), ("elj", "double"), ("elt", "double"), ("erj", "double"), ("ert", "double"),
    ("etj", "double"), ("ett", "double"), ("origin.x", "double"), ("origin.y", "double"), ("xncSide", "boolean"),
)


def variable_table(x: XNCParams) -> list[dict]:
    """«Переменные» jadvali: tizim o'zgaruvchilari (`SYSTEM_VARS` tartibida), so'ng dasturning o'z Par / Var lari (dasturdagi
    tartibda, takrorlarsiz). Qiymat — dastur bajarilgandan keyingi joriy qiymat (hisoblanmagan / bajarilmagan shoxchadagi
    o'zgaruvchi — None). Qator: {name, kind: system | par | var, type: double | integer | boolean | string, value, description}
    (tizim qatorlarining tavsifi — UI tarjimasida; dasturnikilar — Par yorlig'i yoki buyruq izohi)."""
    run = _Run(x.length, x.width, x.thickness, program_vars(x), x.par_values, _default_tool_lib())
    run.collect_subs(x.program)
    run.block(x.program, "")
    env = run.env

    def val(name: str, typ: str):
        v = env.get(name)
        if isinstance(v, str):
            return v
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            return None
        return bool(v) if typ == "boolean" else float(v)

    rows = [dict(name=n, kind="system", type=t, value=val(n, t), description="") for n, t in SYSTEM_VARS]
    seen = {n for n, _t in SYSTEM_VARS}

    def walk(cmds: list[XncCommand]) -> None:
        for c in cmds:
            if not c.enabled:
                continue
            if c.cmd in ("Par", "Var"):
                name = str(c.params.get("name", "")).strip()
                if name and name not in seen:
                    seen.add(name)
                    typ = par_type(c.params.get("type"))
                    desc = str(c.params.get("label", "") or "") if c.cmd == "Par" else ""
                    rows.append(dict(name=name, kind=c.cmd.lower(), type=typ, value=val(name, typ) if name in run.defined else None,
                                     description=desc or c.comment or ""))
            if c.children:
                walk(c.children)

    walk(x.program)
    return rows


# ───────────────────────── Yoylar ─────────────────────────
def arc_sweep(start, end, center, direction) -> tuple[float, float]:
    """Markazli yoy: (radius, burilish burchagi rad). direction «true» — soat millariga teskari (matematik,
    Y yuqoriga), aks holda soat bo'yicha; boshi = oxiri — to'liq aylana. Katta yoylar (> 180°) ham to'g'ri
    (GibLab saqlagan freza uzunliklari bilan tekshirilgan)."""
    r = math.dist(start, center)
    if r <= 1e-9:
        return 0.0, 0.0
    a0 = math.atan2(start[1] - center[1], start[0] - center[0])
    a1 = math.atan2(end[1] - center[1], end[0] - center[0])
    ccw = str(direction).strip().lower() in ("true", "1", "ccw")
    sw = (a1 - a0) if ccw else (a0 - a1)
    sw %= 2 * math.pi
    if sw <= 1e-9:
        sw = 2 * math.pi
    return r, sw


def _is_ccw(direction) -> bool:
    return str(direction).strip().lower() in ("true", "1", "ccw")


def arc_through(a, b, c) -> tuple[float, float, bool, tuple[float, float]] | None:
    """Uch nuqtadan (boshi a, oraliq b, oxiri c) o'tuvchi yoy: (radius, burchak rad, ccw, markaz).
    Nuqtalar bir to'g'ri chiziqda bo'lsa — None."""
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-9:
        return None
    ux = ((a[0] ** 2 + a[1] ** 2) * (b[1] - c[1]) + (b[0] ** 2 + b[1] ** 2) * (c[1] - a[1])
          + (c[0] ** 2 + c[1] ** 2) * (a[1] - b[1])) / d
    uy = ((a[0] ** 2 + a[1] ** 2) * (c[0] - b[0]) + (b[0] ** 2 + b[1] ** 2) * (a[0] - c[0])
          + (c[0] ** 2 + c[1] ** 2) * (b[0] - a[0])) / d
    cen = (ux, uy)
    r = math.dist(a, cen)
    cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
    ccw = cross > 0
    a0 = math.atan2(a[1] - uy, a[0] - ux)
    a1 = math.atan2(c[1] - uy, c[0] - ux)
    sw = ((a1 - a0) if ccw else (a0 - a1)) % (2 * math.pi)
    return r, sw, ccw, cen


def arc_by_radius(a, b, r: float, ccw: bool) -> tuple[float, float, bool, tuple[float, float]] | None:
    """Radius bo'yicha kichik yoy (≤ 180°): (radius, burchak rad, ccw, markaz). Vatar 2R dan uzun — None."""
    r = abs(r)
    chord = math.dist(a, b)
    if r <= 1e-9 or chord <= 1e-9 or chord > 2 * r + 1e-9:
        return None
    h = math.sqrt(max(0.0, r * r - chord * chord / 4))
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    nx, ny = -(b[1] - a[1]) / chord, (b[0] - a[0]) / chord      # yurish yo'nalishining chap normali
    s = 1 if ccw else -1
    cen = (mx + s * h * nx, my + s * h * ny)
    return r, 2 * math.asin(min(1.0, chord / (2 * r))), ccw, cen


def mill_arc(kind: str, start, o: dict):
    """Frezalash yoyi geometriyasi: (radius, burchak, ccw, markaz) yoki None (to'g'ri chiziq / vatar)."""
    end = (o["X"], o["Y"])
    if kind == "MillArcCenter" and not math.isnan(o["CX"]):
        cen = (o["CX"], o["CY"])
        r, sw = arc_sweep(start, end, cen, o.get("DIR", ""))
        return (r, sw, _is_ccw(o.get("DIR", "")), cen) if r > 0 else None
    if kind == "MillArc" and o["R"]:
        ccw = _is_ccw(o.get("DIR", "")) != (o["R"] < 0)
        return arc_by_radius(start, end, o["R"], ccw)
    if kind == "MillArc3P" and not math.isnan(o["X2"]):
        return arc_through(start, (o["X2"], o["Y2"]), end)
    return None


GROOVE_STEP = 0.7          # keyingi o'tish arra qalinligining 70 % iga suriladi (o'tishlar bir-birini yopadi)


def groove_passes(width: float, saw: float) -> int:
    """Paz eni uchun arra o'tishlari soni: arradan tor paz — bajarib bo'lmaydi (0); aks holda
    1 + ⌈(en − arra) / (0.7 × arra)⌉. Korxona GibLab loyihalaridagi saqlangan «длина пропила» qiymatlari bilan
    tekshirilgan (4 mm arra: 4 → 1, 6 → 2, 10 / 10.5 / 11 → 4, 26 → 9 o'tish; 8360 dasturdan 8359 tasi mos)."""
    if saw <= 0 or width <= 0 or not (math.isfinite(width) and math.isfinite(saw)):
        return 0
    if width < saw - 1e-6:
        return 0
    if width <= saw + 1e-6:
        return 1
    return 1 + math.ceil((width - saw) / (GROOVE_STEP * saw) - 1e-9)


# ───────────────────────── To'rtburchak va ellips geometriyasi ─────────────────────────
def _ang(a: float) -> float:
    """Burilish burchagi (rad): ANGLE_DEGREES bo'lsa gradusdan."""
    return math.radians(a) if ANGLE_DEGREES else a


def rect_segments(o: dict) -> list[tuple]:
    """MillRect yopiq konturi, dastur koordinatalarida: [("M", x, y), ("L", x, y), ("A", x, y, cx, cy, ccw), …].
    (X, Y) — markaz, L — X o'qi bo'ylab, W — Y o'qi bo'ylab (burilishgacha), A — markaz atrofida burilish
    (musbat: +X dan +Y tomonga), R — burchak radiusi (≤ min(L, W)/2). Yoylar `arc_sweep` (ccw=True) bilan mos."""
    L, W = abs(o["L"]), abs(o["W"])
    cx, cy = o["X"], o["Y"]
    a = _ang(o.get("A", 0.0) or 0.0)
    ca, sa = math.cos(a), math.sin(a)
    r = max(0.0, min(o.get("R", 0.0) or 0.0, L / 2, W / 2))
    hl, hw = L / 2, W / 2

    def tr(u, v):
        return (cx + u * ca - v * sa, cy + u * sa + v * ca)

    rounded = r > 1e-9
    # aylanish tartibi: yuqori chiziq → o'ng → pastki → chap (matematik yo'nalishda chapga buriladi: yoylar ccw)
    seg: list[tuple] = [("M", *tr(-hl + r, -hw)), ("L", *tr(hl - r, -hw))]
    if rounded:
        seg.append(("A", *tr(hl, -hw + r), *tr(hl - r, -hw + r), True))
    seg.append(("L", *tr(hl, hw - r)))
    if rounded:
        seg.append(("A", *tr(hl - r, hw), *tr(hl - r, hw - r), True))
    seg.append(("L", *tr(-hl + r, hw)))
    if rounded:
        seg.append(("A", *tr(-hl, hw - r), *tr(-hl + r, hw - r), True))
    seg.append(("L", *tr(-hl, -hw + r)))
    if rounded:
        seg.append(("A", *tr(-hl + r, -hw), *tr(-hl + r, -hw + r), True))
    out = [seg[0]]
    for s in seg[1:]:                                   # nol uzunlikli chiziqlar (r = L/2 yoki W/2) tashlanadi
        if s[0] == "L" and math.dist(out[-1][1:3], s[1:3]) < 1e-9:
            continue
        out.append(s)
    return out


def rect_length(o: dict) -> float:
    L, W = abs(o["L"]), abs(o["W"])
    r = max(0.0, min(o.get("R", 0.0) or 0.0, L / 2, W / 2))
    return 2 * (L - 2 * r) + 2 * (W - 2 * r) + 2 * math.pi * r


def ellipse_length(o: dict) -> float:
    """Ellips uzunligi (Ramanujan formulasi; RL, RW — yarim o'qlar)."""
    a, b = abs(o["RL"]), abs(o["RW"])
    if a <= 0 or b <= 0:
        return 4 * max(a, b)
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))


def ellipse_points(o: dict, tol: float = ELLIPSE_TOL) -> list[tuple[float, float]]:
    """Ellips konturi siniq chiziq sifatida (yopiq: oxirgi nuqta = birinchisi), dastur koordinatalarida.
    Burchak qadami chiziqdan chetlanish ≤ tol bo'ladigan qilib tanlanadi."""
    a, b = abs(o["RL"]), abs(o["RW"])
    rmax = max(a, b, 1e-9)
    n = int(min(720, max(36, math.ceil(math.pi / math.acos(max(-1.0, 1 - tol / rmax))))))
    n += n % 4                                          # to'rt o'q uchlari nuqtada bo'lsin
    ang = _ang(o.get("A", 0.0) or 0.0)
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        u, v = a * math.cos(t), b * math.sin(t)
        pts.append((o["X"] + u * ca - v * sa, o["Y"] + u * sa + v * ca))
    pts.append(pts[0])
    return pts


# ───────────────────────── Statistika va narx ─────────────────────────
def program_stats(cmds: list[XncCommand], dx: float, dy: float, dz: float, variables: dict | None = None,
                  pars: dict | None = None, tool_lib=None) -> dict:
    ops = evaluate(cmds, dx, dy, dz, variables, pars, tool_lib)
    drills = sum(o["count"] for o in ops if o["kind"].startswith("Drill") and o.get("inside", True))
    mill = 0.0
    saw = 0.0
    pos = None
    for o in ops:
        k = o["kind"]
        if k == "MillStart":
            pos = (o["X"], o["Y"])
            if not o.get("ok", True) or (o.get("C", 0) == 3 and not POCKET_COUNTS_IN_LENGTH):
                pos = None              # hisoblanmaydigan kontur (yoki 3-tur korreksiya): uzunlikka kirmaydi
        elif k == "MillLine" and pos is not None:
            nxt = (o["X"], o["Y"]); mill += math.dist(pos, nxt); pos = nxt
        elif k in ("MillArc", "MillArcCenter", "MillArc3P") and pos is not None:
            nxt = (o["X"], o["Y"])
            g = mill_arc(k, pos, o)
            mill += g[0] * g[1] if g else math.dist(pos, nxt)
            pos = nxt
        elif k == "MillRect":
            if o.get("C", 0) != 3 or POCKET_COUNTS_IN_LENGTH:
                mill += rect_length(o)
        elif k == "MillEllipse":
            if o.get("C", 0) != 3 or POCKET_COUNTS_IN_LENGTH:
                mill += ellipse_length(o)
        elif k == "Groove":
            if o.get("ok", True):
                saw += math.dist((o["X1"], o["Y1"]), (o["X2"], o["Y2"])) * groove_passes(o["W"], o.get("D", 4.0))
    fin = (lambda v: v if math.isfinite(v) else 0.0)
    bad = sum(1 for o in ops if o["kind"] in _MILL + ("Groove", "MillRect", "MillEllipse") and not o.get("ok", True))
    if bad:
        mill = 0.0      # dasturda hisoblanmaydigan freza konturi bor — dastur stanokda bajarilmaydi (GibLab ham 0)
    return dict(drills=int(drills), mill_m=round(fin(mill) / 1000, 3), saw_m=round(fin(saw) / 1000, 3),
                errors=ops.problems, warnings=list(ops.messages), params=unique_params(ops.params))


def unique_params(params: list[dict]) -> list[dict]:
    """Bajarilgan Par buyruqlari: bir nom — bitta yozuv (birinchisi; siklda takrorlansa ham)."""
    seen: set[str] = set()
    out = []
    for p in params:
        if p["name"] not in seen:
            seen.add(p["name"])
            out.append(p)
    return out


def xnc_stats(x: XNCParams) -> dict:
    """Operatsiya dasturining statistikasi (detaldan hisoblangan o'zgaruvchilar va kiritilgan Par qiymatlari bilan)."""
    return program_stats(x.program, x.length, x.width, x.thickness, program_vars(x), x.par_values)


def xnc_cost(op: Operation) -> dict:
    x = op.xnc
    st = xnc_stats(x)
    unit = st["drills"] * x.drill_price + st["mill_m"] * x.mill_price_m + \
        st["saw_m"] * x.saw_price_m + x.extra_cost
    if not math.isfinite(unit):
        unit = 0.0
    op.cost_material = 0
    op.cost_operation = round(unit * x.qty, 2) if math.isfinite(unit * x.qty) else 0.0
    return {**st, "unit_cost": round(unit, 2), "qty": x.qty, "cost": op.cost_operation}


def xnc_holes_table(op: Operation) -> list[list]:
    x = op.xnc
    rows = []
    for o in evaluate(x.program, x.length, x.width, x.thickness, program_vars(x), x.par_values):
        if o["kind"].startswith("Drill") and o.get("inside", True):
            side = {"DrillFront": "", "DrillLeft": "←", "DrillRight": "→", "DrillTop": "↑", "DrillBottom": "↓"}[o["kind"]]
            rows.append([len(rows) + 1, f"{o['X']:g}{side}", f"{o['Y']:g}", f"{o['D']:g}", f"{o['DP']:g}", o["T"]])
    return rows


# ───────────────────────── Chizma ─────────────────────────
class _View:
    """Chizma ko'rinishi: koordinata boshi (LT/RT/LB/RB) va ko'zgu (mirror_x/y) — dastur koordinatalarini detalning
    chap-yuqori burchagidan o'lchanadigan «fizik» holatga o'tkazadi; burish (rotation 0/90/180/270, soat bo'yicha) —
    butun chizmani aylantiradi."""

    def __init__(self, x: XNCParams):
        self.dx, self.dy = max(x.length, 1.0), max(x.width, 1.0)
        self.fx = (x.origin in ("RT", "RB")) != bool(x.mirror_x)
        self.fy = (x.origin in ("LB", "RB")) != bool(x.mirror_y)
        self.rot = x.rotation
        self.mirror_x, self.mirror_y = bool(x.mirror_x), bool(x.mirror_y)
        self.flip_arc = self.fx != self.fy          # bitta akslantirish — yoy yo'nalishi teskari
        self.W, self.H = (self.dy, self.dx) if self.rot in (90, 270) else (self.dx, self.dy)

    def canon(self, x: float, y: float) -> tuple[float, float]:
        return (self.dx - x if self.fx else x), (self.dy - y if self.fy else y)

    def phys(self, x: float, y: float) -> tuple[float, float]:
        """Fizik (chap-yuqori) koordinata → ekran (burishdan keyin)."""
        if self.rot == 90:
            return self.dy - y, x
        if self.rot == 180:
            return self.dx - x, self.dy - y
        if self.rot == 270:
            return y, self.dx - x
        return x, y

    def pt(self, x: float, y: float) -> tuple[float, float]:
        return self.phys(*self.canon(x, y))

    def sweep(self, ccw: bool) -> int:
        return int(ccw != self.flip_arc)


DRAW_TURN_BADGE = True        # (W18) stanok cheklovi qo'shimcha burish bergan bo'lsa (`extra_turn` ≠ 0) chizmada yozuv chiqadi; False — yo'q
                              # (burishning o'zi chizmani faqat `turned=True` da buradi — «stanokdagi ko'rinish»)


# Chizma ranglari (xodimlarga tanish «yoyilgan» ko'rinish: lits yuzasi + to'rtta yon ko'rinish)
DRAW_FILL = "#FFA500"          # detal (yuza va yon ko'rinishlar) — kroy kartasidagi detal rangi bilan bir xil
DRAW_LINE = "#3a2a00"
DRAW_FACE_LINE = "#2b45c8"     # lits yuzasi konturi
DRAW_HOLE = "#4a3200"
DRAW_MILL = "#7d3cc9"
# Onlayn ko'rinishga moslik (X_1015 §10): umumiy o'lcham yozuvlari standart o'chiq, teshikning minimal ekran o'lchami, tekstura
# belgisi, qirra teshigi — yon polosada ko'ndalang chiziqcha, dastur xatosi — chizma ustida qizil matn
DRAW_DIMS = False             # eni / bo'yi yozuvlari («2000», «347») — standart ko'rsatilmaydi; endpoint `dims=true` yoqadi
DRAW_MIN_HOLE_PX = 2.0        # yuza teshigi aylanasining ekrandagi eng kichik radiusi (px): D=3 teshik 35 mm kosacha yonida ham ko'rinsin
DRAW_HOLE_SECTIONS = True     # yuza teshigining yon ko'rinishlardagi proyeksiyasi (oq to'rtburchak, D kenglikda, DP chuqurlikda) — onlayn chizmadagi kabi
DRAW_TEXTURE = True           # bog'langan detal Ткт (grain) bo'lsa — yuza markazida 3 ta yupqa kulrang gorizontal chiziq (tekstura belgisi)
DRAW_TEXTURE_LEN = 1 / 3      # tekstura chizig'i uzunligi — detal uzunligiga nisbatan
DRAW_ERROR_TEXT = True        # dasturning birinchi xatosi (yoki bo'sh nom) chizma markazida qizil qalin matn bilan
DRAW_GRAIN = "#6a5000"
# Buyruq ↔ chizma bog'lanishi: har geometrik element `data-cmd="0.2 3"` atributini oladi — manba buyruqning daraxtdagi yo'li
# (0 dan, frontend `pathKey`) va (Sub tanasi bo'lsa) Call qatorlari yo'llari. UI tanlangan buyruq elementlarini shu atribut orqali
# qizil bilan belgilaydi (SVG qayta so'ralmaydi), chizmadagi elementni bosish — buyruqni tanlaydi. False — atributlar yozilmaydi.
DRAW_CMD_TAGS = True
DRAW_ERROR = "#d01010"


def xnc_drawing_svg(op: Operation, project: Project | None = None, width_px: int = 560, turn: int = 0,
                    turned: bool = False, height_px: int = 0, dims: bool | None = None) -> str:
    """Detal chizmasi — «yoyilgan» ko'rinish: o'rtada yuza, atrofida to'rtta yon ko'rinish (qalinlik bo'yicha).
    Yuza teshiklari — xoch belgili doira (yon ko'rinishlarda chuqurlik kesimi), qirra teshiklari — yon ko'rinishda doira va
    yuzada kanal (chuqurlik uzunligida); freza (yoylar — haqiqiy yoy), paz; koordinata boshi belgisi (X / Y), lits / orqa
    tomon ko'rsatkichi, kromka belgilari (harf) kromkali tomon yonida. Koordinata boshi / ko'zgu / burish hisobga olinadi.
    `turn` — stanok cheklovlari (W8) bergan qo'shimcha burish (0/90/180/270, `machine_program()["extra_turn"]`): `DRAW_TURN_BADGE`
    bo'lsa chizma tagida yozuv (`<g class="xnc-turn" data-turn=…>`) chiqadi; `turned=True` — chizma shu burish bilan,
    ya'ni stanokdagi holatida chiziladi (kromka belgilari ham aylanadi).
    `height_px` — ko'rsatiladigan maydon balandligi (0 — e'tiborsiz): ekran masshtabi (px/mm) `width_px` va `height_px` ning kichigidan
    olinadi — minimal ko'rinadigan o'lchamlar (teshik radiusi, chiziq eni) shu masshtabda hisoblanadi. `dims` — eni / bo'yi yozuvlari
    (None — `DRAW_DIMS`). Yuza markazidagi 3 ta yupqa chiziq — bog'langan detal teksturali (Ткт) bo'lsa; dastur xatosi — qizil matn."""
    x = op.xnc
    if turn and turned:
        x = x.model_copy(update={"rotation": (x.rotation + turn) % 360})
    v = _View(x)
    W, H = v.W, v.H
    T = max(float(x.thickness or 0), 1.0)
    fs = max(W, H) / 46
    # Masshtab ikki bosqichda: avval taxminiy (detal kengligi bo'yicha), undan yon ko'rinish qalinligi / oraliq / hoshiya
    # piksel birligida hisoblanadi (onlayn chizmadagi kabi: yon ko'rinish — haqiqiy qalinlik, oraliq ≈ 5 px, chiziqlar 1 px)
    k0 = width_px / (W * 1.12)
    if height_px and height_px > 0:
        k0 = min(k0, height_px / (H * 1.3))
    Tv = max(T, 2.0 / k0)                       # yon ko'rinish eni — haqiqiy qalinlik (kamida 2 px)
    gap = 5.0 / k0                              # yuza va yon ko'rinish orasi (≈ 5 px)
    side = gap + Tv
    pad = side + fs * 2.6                       # kromka harfi va koordinata boshi belgisi uchun joy
    k = width_px / (W + 2 * pad)
    if height_px and height_px > 0:
        k = min(k, height_px / (H + 2 * pad))          # maydon balandligi cheklasa — haqiqiy ekran masshtabi shu

    def pxmm(n: float) -> float:
        """Ekran pikseli → chizma birligi (mm): minimal ko'rinadigan o'lchamlar uchun."""
        return n / k

    lw = pxmm(1.0)                              # barcha konturlar — ekranda 1 px (onlayn chizma uslubi)
    if dims is None:
        dims = DRAW_DIMS
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad:g} {-pad:g} {W + 2 * pad:g} {H + 2 * pad:g}" '
           f'width="{width_px}" height="{(H + 2 * pad) * k:.0f}" font-family="Arial">']
    body = f'fill="{DRAW_FILL}" stroke="{DRAW_LINE}" stroke-width="{lw:.2f}"'
    # yon ko'rinishlar: top / bottom / left / right (ekran tomonlari)
    strips = {"top": (0.0, -side, W, Tv), "bottom": (0.0, H + gap, W, Tv),
              "left": (-side, 0.0, Tv, H), "right": (W + gap, 0.0, Tv, H)}
    for (sx, sy, sw, sh) in strips.values():
        out.append(f'<rect x="{sx:g}" y="{sy:g}" width="{sw:g}" height="{sh:g}" {body}/>')
    out.append(f'<rect x="0" y="0" width="{W:g}" height="{H:g}" fill="{DRAW_FILL}" stroke="{DRAW_FACE_LINE}" '
               f'stroke-width="{lw:.2f}"/>')

    def screen_side(px: float, py: float) -> str:
        """Ekrandagi nuqta qaysi chetda (yuza konturida)."""
        d = {"left": abs(px), "right": abs(W - px), "top": abs(py), "bottom": abs(H - py)}
        return min(d, key=d.get)

    # kromkalar (bog'langan detaldan): harf — kromkali tomon yon ko'rinishi tashqarisida; rang — kromka rangi.
    # Orqa yuzadan ishlov (face_side=false): chizma ishlov tomonidan qaraladi — detal tomonlari `xnc_constraints.BACK_FACE_MIRROR`
    # bo'yicha akslanadi (W18: chap ↔ o'ng), dastur koordinatalari o'zgarmaydi.
    linked = None
    if project is not None:
        from .render import part_edges, safe_color
        from .xnc_constraints import machine_side
        linked = next((p for o in project.operations for p in o.parts if op.id in p.xnc_op_ids), None)
        if linked is not None:
            ed = part_edges(linked, project)
            dx, dy = v.dx, v.dy
            mids = {"top": (dx / 2, 0), "bottom": (dx / 2, dy), "left": (0, dy / 2), "right": (dx, dy / 2)}
            off = side + fs * 1.3
            back = not bool(x.face_side)
            for sd, e in ed.items():
                if not e:
                    continue
                mx, my = v.phys(*mids[machine_side(sd, back)])
                ss = screen_side(mx, my)
                tx, ty = {"top": (mx, -off), "bottom": (mx, H + off), "left": (-off, my), "right": (W + off, my)}[ss]
                col = safe_color(e["color"])
                sx, sy, sw, sh = strips[ss]
                out.append(f'<rect x="{sx:g}" y="{sy:g}" width="{sw:g}" height="{sh:g}" fill="none" stroke="{col}" '
                           f'stroke-width="{lw * 1.5:.2f}"/>')
                out.append(f'<text x="{tx:g}" y="{ty:g}" font-size="{fs * 2.2:.1f}" font-family="Times New Roman, serif" '
                           f'text-anchor="middle" dominant-baseline="middle" fill="{col}">{escape(e["symbol"])}</text>')
    # tekstura belgisi: detal Ткт bo'lsa — yuza markazida 3 ta yupqa kulrang chiziq (detal uzunligi bo'ylab, ≈ 1/3 uzunlikda)
    if DRAW_TEXTURE and linked is not None and bool(getattr(linked, "grain", False)):
        half = v.dx * DRAW_TEXTURE_LEN / 2
        out.append('<g class="xnc-grain">')
        for i in (-1, 0, 1):
            yy = v.dy / 2 + i * fs * 0.9
            (ax, ay), (bx, by) = v.phys(v.dx / 2 - half, yy), v.phys(v.dx / 2 + half, yy)
            out.append(f'<line x1="{ax:g}" y1="{ay:g}" x2="{bx:g}" y2="{by:g}" stroke="{DRAW_GRAIN}" stroke-opacity=".75" stroke-width="{lw:.2f}"/>')
        out.append("</g>")
    ops = evaluate(x.program, x.length, x.width, x.thickness, program_vars(x), x.par_values)
    pos = None
    path: list[str] = []
    segs: list[str] = []          # kontur segmentlari (buyruq bo'yicha belgilash uchun ko'rinmas nusxalar)
    start_tag = ""
    pocket = False
    swap_x = {"DrillLeft": "DrillRight", "DrillRight": "DrillLeft"}
    swap_y = {"DrillTop": "DrillBottom", "DrillBottom": "DrillTop"}
    stroke = f'stroke="{DRAW_MILL}" stroke-width="{pxmm(1.5):.2f}"'
    hole = f'stroke="{DRAW_HOLE}" stroke-width="{lw:.2f}"'

    def flush():
        if path:
            # C = 3 (cho'ntak): kontur ichi to'ldiriladi (frezalanadigan maydon)
            fill = f'fill="{DRAW_MILL}" fill-opacity=".18"' if pocket else 'fill="none"'
            out.append(f'<path d="{" ".join(path)}" {fill} {stroke}{start_tag}/>')
            # har segment — alohida ko'rinmas (stroke="none") yo'l: buyruq tanlanganda CSS uni qizil chizadi, bosish ham shu
            out.extend(segs)
        segs.clear()

    def rect_d(o):
        d, cur = [], None
        for s in rect_segments(o):
            px, py = v.pt(s[1], s[2])
            if s[0] == "M":
                d.append(f"M {px:g} {py:g}")
            elif s[0] == "L":
                d.append(f"L {px:g} {py:g}")
            else:
                r = math.dist(cur, (s[3], s[4]))
                d.append(f"A {r:g} {r:g} 0 0 {v.sweep(s[5])} {px:g} {py:g}")
            cur = (s[1], s[2])
        return " ".join(d) + " Z"

    def cross(cx: float, cy: float, r: float) -> str:
        c = r + pxmm(2.0)                                  # xoch chiziqlari aylanadan ≈ 2 px tashqariga chiqadi
        return (f'<line x1="{cx - c:g}" y1="{cy:g}" x2="{cx + c:g}" y2="{cy:g}" {hole}/>'
                f'<line x1="{cx:g}" y1="{cy - c:g}" x2="{cx:g}" y2="{cy + c:g}" {hole}/>')

    def depth_v(dp: float) -> float:
        """Chuqurlik (mm) → yon ko'rinishdagi uzunlik (yon ko'rinish eni Tv, haqiqiy qalinlik T)."""
        return max(0.0, min(dp, T)) / T * Tv

    def tag(o) -> str:
        """` data-cmd="…"` — amal qaysi buyruq(lar)dan (chizmada belgilash uchun); yo'l yo'q bo'lsa — bo'sh."""
        if not DRAW_CMD_TAGS:
            return ""
        src = " ".join(dict.fromkeys(q for q in o.get("src", []) if q))
        return f' data-cmd="{src}"' if src else ""

    for o in ops:
        kd = o["kind"]
        if kd.startswith("Drill") and not o.get("inside", True):
            continue
        if kd == "DrillFront":
            cx, cy = v.pt(o["X"], o["Y"])
            r = max(o["D"] / 2, pxmm(DRAW_MIN_HOLE_PX))     # kichik teshik (D=3) ham ekranda ko'rinadigan aylana + xoch
            thru = o["DP"] >= x.thickness - 1e-6
            # yuza teshigi (aylana + xoch + yon ko'rinishlardagi kesimlar) — bitta guruh: buyruq tanlansa hammasi belgilanadi
            out.append(f'<g class="xnc-hole"{tag(o)}>')
            out.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{"#fff" if thru else "none"}" {hole}/>'
                       + cross(cx, cy, r))
            if not DRAW_HOLE_SECTIONS:
                out.append("</g>")
                continue
            # yon ko'rinishlarda chuqurlik kesimi (yuza tomondan — yuzaga qaragan chetdan)
            dv = depth_v(o["DP"])
            hw = max(o["D"], pxmm(3.0))
            sec = 'fill="#fff" ' + hole
            out.append(f'<rect x="{cx - hw / 2:g}" y="{-gap - dv:g}" width="{hw:g}" height="{dv:g}" {sec}/>')
            out.append(f'<rect x="{cx - hw / 2:g}" y="{H + gap:g}" width="{hw:g}" height="{dv:g}" {sec}/>')
            out.append("</g>")
            # chap / o'ng polosalardagi kesimlar guruhdan tashqarida: tanlanganda faqat yuza + yuqori / pastki polosa belgilanadi
            out.append(f'<rect x="{-gap - dv:g}" y="{cy - hw / 2:g}" width="{dv:g}" height="{hw:g}" {sec}/>')
            out.append(f'<rect x="{W + gap:g}" y="{cy - hw / 2:g}" width="{dv:g}" height="{hw:g}" {sec}/>')
        elif kd in ("DrillLeft", "DrillRight", "DrillTop", "DrillBottom"):
            L = max(o["DP"], fs * 0.5)
            sd = kd
            if v.mirror_x:
                sd = swap_x.get(sd, sd)
            if v.mirror_y:
                sd = swap_y.get(sd, sd)
            if sd in ("DrillLeft", "DrillRight"):
                yy = v.dy - o["Y"] if v.fy else o["Y"]
                seg = (0, yy, L, yy) if sd == "DrillLeft" else (v.dx, yy, v.dx - L, yy)
            else:
                xx = v.dx - o["X"] if v.fx else o["X"]
                seg = (xx, 0, xx, L) if sd == "DrillTop" else (xx, v.dy, xx, v.dy - L)
            (sx1, sy1), (sx2, sy2) = v.phys(seg[0], seg[1]), v.phys(seg[2], seg[3])
            # yuzada: chetdan ichkariga chuqurlik (DP) bo'yicha yupqa chiziq, oxirida teshik diametri (D) kengligida ko'ndalang
            # chiziqcha; yon polosada: teshik o'rnida polosani kesib o'tuvchi yupqa chiziqcha (onlayn ko'rinishdagi kabi)
            hl = f'stroke="{DRAW_HOLE}" stroke-width="{lw:.2f}"'
            ext = pxmm(2.0)
            dh = max(o["D"], pxmm(4.0)) / 2
            ss = screen_side(sx1, sy1)
            if abs(sx1 - sx2) > abs(sy1 - sy2):           # gorizontal chuqurlik chizig'i → oxirida tik chiziqcha
                tip = (sx2, sy2 - dh, sx2, sy2 + dh)
            else:
                tip = (sx2 - dh, sy2, sx2 + dh, sy2)
            mark = {"top": (sx1, -side - ext, sx1, -gap + ext), "bottom": (sx1, H + gap - ext, sx1, H + side + ext),
                    "left": (-side - ext, sy1, -gap + ext, sy1), "right": (W + gap - ext, sy1, W + side + ext, sy1)}[ss]
            # tanlanganda ko'rinadigan (odatda ko'rinmas) qismlar: yuzadagi kanal (DP uzunlikda × D enida) — to'liq qizil,
            # polosadagi belgi markazi — qizil nuqta
            chx, chy = min(sx1, sx2), min(sy1, sy2)
            chw, chh = abs(sx2 - sx1), abs(sy2 - sy1)
            if chw >= chh:
                chy, chh = sy1 - dh, 2 * dh
            else:
                chx, chw = sx1 - dh, 2 * dh
            cr = pxmm(1.5)
            mx0, my0 = (mark[0] + mark[2]) / 2, (mark[1] + mark[3]) / 2
            out.append(f'<g class="xnc-edge-hole" data-side="{ss}"{tag(o)}>'
                       f'<rect class="xnc-ch" x="{chx:g}" y="{chy:g}" width="{chw:g}" height="{chh:g}" fill="none" stroke="none"/>'
                       f'<rect class="xnc-ctr" x="{mx0 - cr:g}" y="{my0 - cr:g}" width="{2 * cr:g}" height="{2 * cr:g}" '
                       f'fill="none" stroke="none"/>'
                       f'<line x1="{sx1:g}" y1="{sy1:g}" x2="{sx2:g}" y2="{sy2:g}" {hl}/>'
                       f'<line x1="{tip[0]:g}" y1="{tip[1]:g}" x2="{tip[2]:g}" y2="{tip[3]:g}" {hl}/>'
                       f'<line x1="{mark[0]:g}" y1="{mark[1]:g}" x2="{mark[2]:g}" y2="{mark[3]:g}" {hl}/></g>')
        elif kd == "MillStart":
            flush()
            px, py = v.pt(o["X"], o["Y"])
            path = [f"M {px:g} {py:g}"]
            start_tag = tag(o)
            pocket = o.get("C", 0) == 3
            pos = (o["X"], o["Y"])
        elif kd in ("MillLine", "MillArc", "MillArcCenter", "MillArc3P") and pos is not None:
            end = (o["X"], o["Y"])
            ex, ey = v.pt(*end)
            sx0, sy0 = v.pt(*pos)
            n0 = len(path)
            geo = mill_arc(kd, pos, o) if kd != "MillLine" else None
            if geo is not None:
                r, sw, ccw, cen = geo
                sweep = v.sweep(ccw)
                if sw >= 2 * math.pi - 1e-9:        # to'liq aylana — ikki yarim yoy
                    mx, my = v.pt(2 * cen[0] - pos[0], 2 * cen[1] - pos[1])
                    path.append(f"A {r:g} {r:g} 0 1 {sweep} {mx:g} {my:g} A {r:g} {r:g} 0 1 {sweep} {ex:g} {ey:g}")
                else:
                    large = 1 if sw > math.pi + 1e-9 else 0
                    path.append(f"A {r:g} {r:g} 0 {large} {sweep} {ex:g} {ey:g}")
            else:
                path.append(f"L {ex:g} {ey:g}")
            if DRAW_CMD_TAGS and tag(o):
                segs.append(f'<path class="xnc-seg" d="M {sx0:g} {sy0:g} {path[n0]}" fill="none" stroke="none" '
                            f'stroke-width="{pxmm(1.5):.2f}"{tag(o)}/>')
            pos = end
        elif kd == "MillRect" and o.get("ok", True):
            fill = f'fill="{DRAW_MILL}" fill-opacity=".18"' if o.get("C", 0) == 3 else 'fill="none"'
            out.append(f'<path d="{rect_d(o)}" {fill} {stroke}{tag(o)}/>')
        elif kd == "MillEllipse" and o.get("ok", True):
            pts = " ".join(("M" if i == 0 else "L") + f" {px:g} {py:g}"
                           for i, (px, py) in enumerate(v.pt(*q) for q in ellipse_points(o)))
            fill = f'fill="{DRAW_MILL}" fill-opacity=".18"' if o.get("C", 0) == 3 else 'fill="none"'
            out.append(f'<path d="{pts} Z" {fill} {stroke}{tag(o)}/>')
        elif kd == "Groove":
            ax, ay = v.pt(o["X1"], o["Y1"])
            bx, by = v.pt(o["X2"], o["Y2"])
            gw = max(o["W"], fs * 0.25)
            out.append(f'<g class="xnc-groove"{tag(o)}>'
                       f'<line class="xnc-gw" x1="{ax:g}" y1="{ay:g}" x2="{bx:g}" y2="{by:g}" stroke="#fff" stroke-opacity=".6" '
                       f'stroke-width="{gw:g}"/>'
                       f'<line x1="{ax:g}" y1="{ay:g}" x2="{bx:g}" y2="{by:g}" stroke="{DRAW_HOLE}" '
                       f'stroke-width="{lw:.2f}" stroke-dasharray="{fs * 0.5:g} {fs * 0.3:g}"/></g>')
    flush()
    # koordinata boshi belgisi: doira + X (qizil) / Y (yashil) strelkalar — dastur o'qlari yo'nalishida
    ox, oy = v.pt(0, 0)
    ux, uy = v.pt(1, 0)
    wx, wy = v.pt(0, 1)
    a = fs * 2.4
    aw = pxmm(1.2)                                         # o'q va strelka chiziqlari (1.2 px)
    mx_ = -side - fs * 1.3 if ox < W / 2 else W + side + fs * 1.3
    my_ = -side - fs * 1.3 if oy < H / 2 else H + side + fs * 1.3
    out.append(f'<g class="xnc-origin"><circle cx="{mx_:g}" cy="{my_:g}" r="{fs * 0.45:g}" fill="none" stroke="#1b2fd0" '
               f'stroke-width="{lw:.2f}"/>'
               f'<line x1="{mx_ - fs * 0.7:g}" y1="{my_:g}" x2="{mx_ + fs * 0.7:g}" y2="{my_:g}" stroke="#1b2fd0" stroke-width="{lw:.2f}"/>'
               f'<line x1="{mx_:g}" y1="{my_ - fs * 0.7:g}" x2="{mx_:g}" y2="{my_ + fs * 0.7:g}" stroke="#1b2fd0" stroke-width="{lw:.2f}"/>')
    for (vx, vy, col, lab) in ((ux - ox, uy - oy, "#e02020", "X"), (wx - ox, wy - oy, "#1a8f2a", "Y")):
        ex, ey = mx_ + vx * a, my_ + vy * a
        hx, hy = -vy, vx                                   # strelka uchi uchun perpendikulyar
        out.append(f'<line x1="{mx_:g}" y1="{my_:g}" x2="{ex:g}" y2="{ey:g}" stroke="{col}" stroke-width="{aw:.2f}"/>'
                   f'<path d="M {ex:g} {ey:g} L {ex - vx * fs * 0.8 + hx * fs * 0.3:g} {ey - vy * fs * 0.8 + hy * fs * 0.3:g} '
                   f'M {ex:g} {ey:g} L {ex - vx * fs * 0.8 - hx * fs * 0.3:g} {ey - vy * fs * 0.8 - hy * fs * 0.3:g}" '
                   f'stroke="{col}" stroke-width="{aw:.2f}" fill="none"/>'
                   f'<text x="{mx_ + vx * a * 0.55 + hx * fs * 1.0:g}" y="{my_ + vy * a * 0.55 + hy * fs * 1.0:g}" font-size="{fs * 1.25:.1f}" '
                   f'font-weight="bold" text-anchor="middle" dominant-baseline="middle" fill="{col}">{lab}</text>')
    out.append("</g>")
    # lits / orqa tomon ko'rsatkichi: plita va unga qaragan strelka (lits — yuqoridan, orqa — pastdan)
    bw = fs * 2.0                                                       # plita belgisi: eni; qalinligi — yon ko'rinishdagidek
    ix = W + side - bw + fs * 0.2 if mx_ < W / 2 else -side - fs * 0.2
    iy = -side - fs * 1.6
    face = bool(x.face_side)
    sgn = -1 if face else 1
    ay2 = iy - pxmm(2) if face else iy + Tv + pxmm(2)
    ay1 = ay2 + sgn * fs * 1.4
    out.append(f'<g class="xnc-face" data-face="{1 if face else 0}">'
               f'<rect x="{ix:g}" y="{iy:g}" width="{bw:g}" height="{Tv:g}" {body}/>'
               f'<line x1="{ix + bw / 2:g}" y1="{ay1:g}" x2="{ix + bw / 2:g}" y2="{ay2:g}" stroke="#000" stroke-width="{aw:.2f}"/>'
               f'<path d="M {ix + bw / 2:g} {ay2:g} l {-fs * 0.28:g} {sgn * fs * 0.45:g} '
               f'M {ix + bw / 2:g} {ay2:g} l {fs * 0.28:g} {sgn * fs * 0.45:g}" stroke="#000" '
               f'stroke-width="{aw:.2f}" fill="none"/></g>')
    # o'lchamlar (ekrandagi eni / bo'yi) — yon ko'rinishlardan tashqarida, kichik; faqat so'ralganda (`dims`)
    if dims:
        dm = side + fs * 3.7
        out.append(f'<g class="xnc-dims"><text x="{W / 2:g}" y="{-dm:g}" font-size="{fs * 1.05:.1f}" text-anchor="middle" fill="#555">{W:g}</text>')
        out.append(f'<text x="{-dm:g}" y="{H / 2:g}" font-size="{fs * 1.05:.1f}" text-anchor="middle" fill="#555" '
                   f'transform="rotate(-90 {-dm:g} {H / 2:g})">{H:g}</text></g>')
    # dastur xatosi (ifoda hisoblanmadi, nom bo'sh …): birinchi xabar chizma markazida qizil qalin matn bilan
    if DRAW_ERROR_TEXT:
        errs = ([_("xnc.err_name_empty")] if not (op.name or "").strip() else []) + [str(m) for m in getattr(ops, "messages", [])]
        if errs:
            out.append(f'<text class="xnc-error" x="{W / 2:g}" y="{H / 2:g}" font-size="{max(fs * 1.5, pxmm(13)):.1f}" font-weight="bold" '
                       f'text-anchor="middle" dominant-baseline="middle" fill="{DRAW_ERROR}">{escape(errs[0])}</text>')
    if turn and DRAW_TURN_BADGE:
        msg = _("xnc.turn_badge_view" if turned else "xnc.turn_badge", t=int(turn))
        out.append(f'<g class="xnc-turn" data-turn="{int(turn)}" data-turned="{1 if turned else 0}">'
                   f'<text x="{W / 2:g}" y="{H + pad * 0.92:g}" font-size="{fs * 1.05:.1f}" text-anchor="middle" fill="#b9770e">'
                   f'↻ {escape(msg)}</text></g>')
    out.append("</svg>")
    return "".join(out)


# ───────────────────────── Ishlov markazi (postprotsessor) uchun toza ma'lumot ─────────────────────────
_ROT_SIDE = {0: {}, 90: {"left": "top", "top": "right", "right": "bottom", "bottom": "left"},
             180: {"left": "right", "right": "left", "top": "bottom", "bottom": "top"},
             270: {"left": "bottom", "bottom": "right", "right": "top", "top": "left"}}
_DRILL_SIDE = {"DrillLeft": "left", "DrillRight": "right", "DrillTop": "top", "DrillBottom": "bottom"}
_MIRROR_X = {"left": "right", "right": "left"}
_MIRROR_Y = {"top": "bottom", "bottom": "top"}


def _num_or_none(v):
    return v if isinstance(v, (int, float)) and math.isfinite(v) else None


def long_side_turn(length: float, width: float, long_side: str) -> int:
    """«Uzun tomon gorizontal / vertikal» cheklovi (ishlov markazi): qo'shimcha burish (0 yoki 90°).
    long_side: horizontal | vertical | any. Detal (burishdan keyingi) uzun tomoni talab qilinganidan boshqacha bo'lsa — 90°."""
    ls = (long_side or "any").lower()
    if ls not in ("horizontal", "vertical") or abs(length - width) < 1e-9:
        return 0
    horizontal_now = length >= width
    return 0 if horizontal_now == (ls == "horizontal") else 90


def edged_sides(op: Operation, project: Project | None) -> list[str]:
    """Operatsiya bog'langan detalning kromkali tomonlari (zagotovka holatida: top | bottom | left | right); bog'lanmagan — []."""
    if project is None:
        return []
    from .render import part_edges
    linked = next((p for o in project.operations for p in o.parts if op.id in p.xnc_op_ids), None)
    return list(part_edges(linked, project)) if linked is not None else []


def machine_program(op: Operation, project: Project | None = None, long_side: str = "any", constraints=None) -> dict:
    """Dastur stanok postprotsessori uchun toza ma'lumot sifatida: ifodalar hisoblangan, burish / ko'zgu / koordinata boshi
    OLDINDAN qo'llangan — koordinatalar detalning (burishdan keyingi) chap-yuqori burchagidan, X o'ngga, Y pastga (mm).
      size   — {length, width}: burishdan keyingi detal o'lchami (dx, dy — zagotovka, burishdan oldin)
      ops    — tartiblangan amallar: drill (face: front|left|right|top|bottom), mill_start / mill_line / mill_arc,
               rect, ellipse (path bilan), groove; har birida tool, d (asbob diametri), depth
      tools  — ishlatilgan asboblar
    Qirra teshigida (x, y) — teshik kiradigan chekkadagi nuqta. Yoylar markaz (cx, cy), radius va yo'nalish bilan:
    `clockwise` — ekran koordinatalarida (Y pastga) soat mili yo'nalishida.
    `long_side` — «uzun tomon» cheklovi (horizontal | vertical | any): kerak bo'lsa qo'shimcha 90° burish qo'llanadi.
    `constraints` — stanok cheklovlari (services.xnc_constraints.XncConstraints; rejim off — e'tiborsiz): `long_side` berilmagan
    ("any") bo'lsa «uzun tomon» talabi undan olinadi, «kromka bilan burchakka burish» yoqilgan bo'lsa detal kromkali tomoni
    burchakka tushadigan qo'shimcha burish (0 / 90 / 180 / 270) qo'llanadi. Natijadagi `extra_turn` — shu qo'shimcha burish,
    `rotation` — {long_side, corner, target, rule, turn} (cheklov ishlatilmasa None); har amalda `cmd_path` — buyruq yo'li."""
    x = op.xnc
    xe = x
    cons = constraints if constraints is not None and getattr(constraints, "active", False) else None
    if long_side not in ("horizontal", "vertical") and cons is not None:
        long_side = cons.long_side()
    extra = long_side_turn(*((x.width, x.length) if x.rotation in (90, 270) else (x.length, x.width)), long_side)
    rot_info = None
    if cons is not None and cons.rotate_corner_on:
        from . import xnc_constraints as XC
        edged = edged_sides(op, project)
        if edged:
            extra, rot_info = XC.pick_turn(x.rotation, extra if long_side in ("horizontal", "vertical") else None, edged,
                                           cons.rotate_corner, back=not x.face_side)       # orqa yuza: stanokda akslangan (W18)
    if long_side in ("horizontal", "vertical") or rot_info is not None:
        rot_info = dict(rot_info or {}, long_side=long_side, turn=extra)
    if extra:
        xe = x.model_copy(update={"rotation": (x.rotation + extra) % 360})
    v = _View(xe)
    raw = evaluate(x.program, x.length, x.width, x.thickness, program_vars(x), x.par_values)
    out: list[dict] = []
    tools: dict[str, dict] = {}
    cmd_at = {"p": ""}

    def tool(o, kind):
        nm = o.get("T", "")
        d = _num_or_none(o.get("D"))
        t = tools.setdefault(nm, dict(name=nm, d=d, uses=[]))
        if d is not None and not t["d"]:
            t["d"] = d
        if kind not in t["uses"]:
            t["uses"].append(kind)

    def add(d):
        d["n"] = len(out) + 1
        d["cmd_path"] = cmd_at["p"]
        out.append(d)

    pos = None
    for o in raw:
        kd = o["kind"]
        cmd_at["p"] = o.get("cmd_path", "")
        if kd.startswith("Drill"):
            if not o.get("inside", True):
                continue
            tool(o, "drill")
            if kd == "DrillFront":
                px, py = v.pt(o["X"], o["Y"])
                add(dict(kind="drill", face="front", x=px, y=py, d=o["D"], depth=o["DP"], tool=o["T"], count=o["count"],
                         through=o["DP"] >= x.thickness - 1e-6))
                continue
            side = _DRILL_SIDE[kd]
            if v.mirror_x:
                side = _MIRROR_X.get(side, side)
            if v.mirror_y:
                side = _MIRROR_Y.get(side, side)
            if side in ("left", "right"):
                yy = v.dy - o["Y"] if v.fy else o["Y"]
                ex, ey = v.phys(0.0 if side == "left" else v.dx, yy)
            else:
                xx = v.dx - o["X"] if v.fx else o["X"]
                ex, ey = v.phys(xx, 0.0 if side == "top" else v.dy)
            add(dict(kind="drill", face=_ROT_SIDE[v.rot].get(side, side), x=ex, y=ey, z=o["Z"], d=o["D"], depth=o["DP"],
                     tool=o["T"], count=o["count"], middle=o.get("M", False)))
        elif kd == "MillStart":
            tool(o, "mill")
            px, py = v.pt(o["X"], o["Y"])
            pos = (o["X"], o["Y"])
            add(dict(kind="mill_start", x=px, y=py, depth=o["DP"], tool=o["T"], d=o["D"], correction=o.get("C", 0),
                     pocket=o.get("C", 0) == 3, step_depth=_num_or_none(o.get("SDP")),
                     step_xy=_num_or_none(o.get("SXY")), entry=o.get("IN", 0), exit=o.get("OUT", 1), ok=o.get("ok", True)))
        elif kd in ("MillLine", "MillArc", "MillArcCenter", "MillArc3P") and pos is not None:
            end = (o["X"], o["Y"])
            ex, ey = v.pt(*end)
            geo = mill_arc(kd, pos, o) if kd != "MillLine" else None
            if geo is not None:
                r, sw, ccw, cen = geo
                cx, cy = v.pt(*cen)
                add(dict(kind="mill_arc", x=ex, y=ey, cx=cx, cy=cy, radius=r, angle=math.degrees(sw),
                         clockwise=bool(v.sweep(ccw)), depth=o["DP"], tool=o["T"], fillet=bool(o.get("fillet"))))
            else:
                add(dict(kind="mill_line", x=ex, y=ey, depth=o["DP"], tool=o["T"]))
            pos = end
        elif kd == "MillRect" and o.get("ok", True):
            tool(o, "mill")
            path, cur = [], None
            for s in rect_segments(o):
                px, py = v.pt(s[1], s[2])
                if s[0] == "A":
                    cx, cy = v.pt(s[3], s[4])
                    path.append(dict(type="arc", x=px, y=py, cx=cx, cy=cy, radius=math.dist(cur, (s[3], s[4])),
                                     clockwise=bool(v.sweep(s[5]))))
                else:
                    path.append(dict(type="move" if s[0] == "M" else "line", x=px, y=py))
                cur = (s[1], s[2])
            px, py = v.pt(o["X"], o["Y"])
            add(dict(kind="rect", x=px, y=py, length=o["L"], width=o["W"], angle=o["A"], radius=o["R"], d=o["D"],
                     depth=o["DP"], tool=o["T"], correction=o["C"], pocket=o["C"] == 3, path=path))
        elif kd == "MillEllipse" and o.get("ok", True):
            tool(o, "mill")
            px, py = v.pt(o["X"], o["Y"])
            add(dict(kind="ellipse", x=px, y=py, rl=o["RL"], rw=o["RW"], angle=o["A"], d=o["D"], depth=o["DP"],
                     tool=o["T"], correction=o["C"], pocket=o["C"] == 3,
                     path=[dict(x=a, y=b) for a, b in (v.pt(*q) for q in ellipse_points(o))]))
        elif kd == "Groove" and o.get("ok", True):
            tool(o, "groove")
            ax, ay = v.pt(o["X1"], o["Y1"])
            bx, by = v.pt(o["X2"], o["Y2"])
            add(dict(kind="groove", x1=ax, y1=ay, x2=bx, y2=by, width=o["W"], depth=o["DP"], tool=o["T"], d=o["D"],
                     passes=groove_passes(o["W"], o.get("D", 4.0)), correction=o.get("C", 0)))
    st = program_stats(x.program, x.length, x.width, x.thickness, program_vars(x), x.par_values)
    return dict(size=dict(length=v.W, width=v.H), blank=dict(length=x.length, width=x.width, thickness=x.thickness),
                ops=out, tools=list(tools.values()), stats={k: st[k] for k in ("drills", "mill_m", "saw_m")},
                errors=st["errors"], warnings=st["warnings"],
                params=[dict(name=p["name"], label=p["label"], type=p["type"], value=p["value"]) for p in st["params"]],
                extra_turn=extra, rotation=rot_info, face_back=not x.face_side)


def xnc_ops_for_part(project: Project, part_id: str) -> list[Operation]:
    return [o for o in project.operations if o.type == OpType.XNC and any(
        part_id == p.id and o.id in p.xnc_op_ids for op in project.operations for p in op.parts)]
