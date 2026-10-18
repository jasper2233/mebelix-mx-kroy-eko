"""XNC muharriri sozlamalari (W8): «Ограничения» — stanok (ishlov markazi) cheklovlari.

Sozlama doirasi `xnc_constraints` (standart profil): pydantic modeli `XncConstraints`. Cheklovlar faqat MA'LUMOT: stanok formati
yo'q (postprotsessorni korxona dasturchilari yozadi) — bu yerda (1) dasturni tekshirish (`check_program`: xabarlar ro'yxati) va
(2) detalni stanok stoliga qanday burish kerakligini hisoblash (`pick_turn`: «uzun tomon», «kromka burchakda») bor.

Rejim (`mode`): `off` — hammasi o'chiq (tekshiruv ham, avtomatik burish ham); `warn` — xabarlar «ogohlantirish» darajasida;
`block` — «xato» darajasida. ❓ Onlayn dasturda «Режим» tanlovining qiymatlari ko'rinmadi (faqat «Выключить») — `warn`/`block` bizning
taxminimiz; `block` hozircha faqat xabar darajasini belgilaydi (eksportni to'smaydi).

Tekshiruvlar stanok orientatsiyasida (burish, ko'zgu va koordinata boshi qo'llangan: `xnc.machine_program`) bajariladi:
X — detal uzunligi (burishdan keyin), Y — eni, Z — qalinlik; «yuqori/past/chap/o'ng» — detalning chap-yuqori burchagidan.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..i18n import MSG, _, pick
from ..models import Base, Operation

MODES = ("off", "warn", "block")
SIDES = ("top", "bottom", "left", "right")
CORNERS = ("LT", "RT", "LB", "RB")
CORNER_SIDES = {"LT": ("left", "top"), "RT": ("right", "top"), "LB": ("left", "bottom"), "RB": ("right", "bottom")}

# ───────── Qarorlar (yordamda aniq emas — bitta konstanta orqasida; hujjat: docs/mebelix/T_W8_XNC_SOZLAMALAR.md) ─────────
# ❓ «Kromka bilan burchakka burish»: bir nechta kromkali tomon bo'lsa qaysi biri burchakka tushishi yordamda yozilmagan.
#    "first" — birinchi kromkali tomon (EDGE_ORDER: yuqori, past, chap, o'ng — loyihadagi tomonlar tartibi) burchak tomonlaridan
#    biriga tushadigan eng kichik burish tanlanadi; "max" — burchakdagi kromkali tomonlar soni eng ko'p bo'lgan burish.
CORNER_EDGE_RULE = "first"
EDGE_ORDER = ("top", "bottom", "left", "right")
# ❓ «Paz chetidan min. masofa»: True — to'rt tomon uchun ham pazning chegaraviy to'rtburchagi (uchlari ham) hisobga olinadi
#    (chetdan chetgacha o'tuvchi paz chap/o'ng chegarani buzadi); False — faqat paz yo'nalishiga ko'ndalang tomonlar.
GROOVE_MARGIN_ALL_SIDES = True
# ❓ (W18, W8 savol 5) ORQA YUZADAN ishlov (`face_side=false`, ifodalarda `xncSide = 0`): detal stanok stoliga orqa yuzi tepada qilib
#    ag'dariladi. Dastur koordinatalari va «yuqori/past/chap/o'ng» tomonlar detalning o'z (lits ko'rinishidagi) holatida beriladi, cheklovlar
#    esa STANOK tomonlari uchun yoziladi → orqa yuzada tomonlar akslanadi. `BACK_FACE_MIRROR`: "x" — detal tik o'q atrofida
#    ag'dariladi (kitob varag'i kabi: chap ↔ o'ng, yuqori/past o'zgarmaydi) — standart; "y" — gorizontal o'q atrofida (yuqori ↔ past);
#    "none" — akslantirish yo'q (orqa yuza lits kabi hisoblanadi). Ta'sir qiladi: «gorizontal teshik markazidan frontal tekislikkacha»
#    (`hole_center_*`), «paz chetidan masofa» (`groove_margin_*`), «pastdan gorizontal teshik» (`avoid_bottom_horizontal`) va
#    «kromka bilan burchakka burish» (`pick_turn(back=True)`). Gabarit, paz yo'nalishi (gorizontal/vertikal), teshiklar orasi va chetidan masofa,
#    freza — tomonga bog'liq emas. Frontal teshik «Z» si har doim ishlov yuzasidan (orqa yuzada — orqa yuzadan) o'lchanadi.
BACK_FACE_MIRROR = "x"
_BACK_FLIP = {"x": {"left": "right", "right": "left"}, "y": {"top": "bottom", "bottom": "top"}, "none": {}}
MAX_ISSUES = 100                  # xabarlar ro'yxati uzunligi (qolgani «yana N» qatori bilan)
MAX_PAIRS = 400                   # teshiklar orasi masofasi: topilgan juftliklar chegarasi (ish hajmi uchun)
EPS = 1e-6


class Limit(Base):
    """Yoqish katakchasi + qiymat (mm)."""
    enabled: bool = False
    value: float = Field(0, ge=0, le=100000)


class Flag(Base):
    """Yoqish katakchasi + ichki belgi (`value`: paz uchun «ruxsat», pastdan burg'ulash uchun «afzallik»)."""
    enabled: bool = False
    value: bool = True


def _lim(v: float):
    return Field(default_factory=lambda: Limit(value=v))


def _flag(v: bool):
    return Field(default_factory=lambda: Flag(value=v))


# standart qiymatlar — onlayn dastur ekran nusxasidan (hammasi o'chiq katakchalar bilan)
LIMIT_DEFAULTS: dict[str, float] = {
    "length_min": 200, "length_max": 3000, "width_min": 70, "width_max": 950, "thickness_min": 12, "thickness_max": 60,
    "hole_center_top": 30, "hole_center_bottom": 30, "hole_center_left": 30, "hole_center_right": 30,
    "groove_margin_top": 30, "groove_margin_bottom": 30, "groove_margin_left": 30, "groove_margin_right": 30,
    "mill_max_distance": 100,
    "blind_depth_margin": 2, "hole_gap_min": 5, "hole_edge_front_min": 4, "hole_edge_horizontal_min": 3,
}
FLAG_DEFAULTS: dict[str, bool] = {"groove_horizontal": True, "groove_vertical": False, "avoid_bottom_horizontal": True}


class XncConstraints(Base):
    mode: Literal["off", "warn", "block"] = "off"
    # 1) detal gabaritlari (stanok orientatsiyasida: X — uzunlik, Y — en, Z — qalinlik), mm
    length_min: Limit = _lim(200)
    length_max: Limit = _lim(3000)
    width_min: Limit = _lim(70)
    width_max: Limit = _lim(950)
    thickness_min: Limit = _lim(12)
    thickness_max: Limit = _lim(60)
    # 2) burish
    rotate_long_side: Literal["off", "horizontal", "vertical"] = "off"      # «Разворачивать деталь длинной стороной»
    rotate_corner_on: bool = False                                           # «Разворачивать деталь кромкой в …»
    rotate_corner: Literal["LT", "RT", "LB", "RB"] = "LT"
    # 3) gorizontal teshik markazidan frontal tekislikkacha eng katta masofa (qaysi tomondan burg'ulanayotganiga qarab)
    hole_center_top: Limit = _lim(30)
    hole_center_bottom: Limit = _lim(30)
    hole_center_left: Limit = _lim(30)
    hole_center_right: Limit = _lim(30)
    # 4) paz: ruxsat (value) va pazning detal chetidan eng kichik masofasi
    groove_horizontal: Flag = _flag(True)
    groove_vertical: Flag = _flag(False)
    groove_margin_top: Limit = _lim(30)
    groove_margin_bottom: Limit = _lim(30)
    groove_margin_left: Limit = _lim(30)
    groove_margin_right: Limit = _lim(30)
    # 5) frezalash (radiuslar): detaldan frezagacha eng katta masofa
    mill_max_distance: Limit = _lim(100)
    # 6) burg'ulash
    avoid_bottom_horizontal: Flag = _flag(True)       # pastdan gorizontal teshiklar nomaqbul; value — «afzallik» (har doim ogohlantirish)
    blind_depth_margin: Limit = _lim(2)               # ko'r vertikal teshik chuqurligi ≤ qalinlik − qiymat
    hole_gap_min: Limit = _lim(5)                     # teshiklar chetlari orasi eng kichik masofa
    hole_edge_front_min: Limit = _lim(4)              # detal chetidan frontal teshik chetigacha
    hole_edge_horizontal_min: Limit = _lim(3)         # detal chetidan gorizontal teshik chetigacha

    @model_validator(mode="before")
    @classmethod
    def _fill_defaults(cls, data):
        """Eski / qisman JSON: ichki obyektda `value` yo'q bo'lsa — shu maydonning standart qiymati (umumiy 0 emas)."""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        for k, dv in LIMIT_DEFAULTS.items():
            v = data.get(k)
            if isinstance(v, dict) and "value" not in v:
                data[k] = {**v, "value": dv}
        for k, dv in FLAG_DEFAULTS.items():
            v = data.get(k)
            if isinstance(v, dict) and "value" not in v:
                data[k] = {**v, "value": dv}
        return data

    @model_validator(mode="after")
    def _ranges(self):
        for lo, hi in (("length_min", "length_max"), ("width_min", "width_max"), ("thickness_min", "thickness_max")):
            a, b = getattr(self, lo), getattr(self, hi)
            if a.enabled and b.enabled and a.value > b.value:
                raise ValueError(_("xnc_cn_range", a=f"{a.value:g}", b=f"{b.value:g}"))
        return self

    @property
    def active(self) -> bool:
        return self.mode != "off"

    def long_side(self) -> str:
        """Cheklovdan kelib chiqadigan «uzun tomon» talabi: horizontal | vertical | any."""
        return self.rotate_long_side if self.active and self.rotate_long_side != "off" else "any"


# ───────────────────────── Burish hisobi ─────────────────────────
_CW = {"left": "top", "top": "right", "right": "bottom", "bottom": "left"}      # 90° soat bo'yicha (xnc._ROT_SIDE[90])


def side_after(side: str, rot: int) -> str:
    """Detal tomoni `rot` (0/90/180/270, soat bo'yicha) burilgandan keyin qaysi tomonda bo'ladi."""
    for _i in range((rot // 90) % 4):
        side = _CW[side]
    return side


def machine_side(side: str, back: bool) -> str:
    """Dastur (detal) tomoni → stanok tomoni: lits yuzada o'zgarmaydi, orqa yuzada `BACK_FACE_MIRROR` bo'yicha akslanadi (modul sarlavhasi)."""
    return _BACK_FLIP.get(BACK_FACE_MIRROR, {}).get(side, side) if back else side


def pick_turn(rotation: int, long_turn: int | None, edged: list[str], corner: str,
              rule: str | None = None, back: bool = False) -> tuple[int, dict]:
    """Kromka bilan burchakka burish: qo'shimcha burish (0/90/180/270) va ma'lumot.
    rotation — operatsiyadagi mavjud burish; long_turn — «uzun tomon» talabi allaqachon beradigan qo'shimcha burish (0 / 90;
    None — talab yo'q): u berilsa faqat shu juftlikdagi (0,180 yoki 90,270) burishlardan tanlanadi; edged — kromkali tomonlar
    (zagotovka holatida). Qoida `rule` (standart CORNER_EDGE_RULE): modul sarlavhasiga qarang. `back` — orqa yuzadan ishlov:
    burishdan keyingi tomon stanokda akslangan holda hisoblanadi (`machine_side`)."""
    rule = rule or CORNER_EDGE_RULE
    base = long_turn or 0
    allowed = [e for e in (0, 90, 180, 270) if long_turn is None or e % 180 == long_turn % 180]
    pref = sorted(allowed, key=lambda e: (e != base, e))            # avval o'zgarishsiz (yoki uzun tomon talabi), keyin kichigi
    ordered = [s for s in EDGE_ORDER if s in edged]
    cs = set(CORNER_SIDES[corner])
    info = dict(rule=rule, corner=corner, target=ordered[0] if ordered else None, turn=base)
    if not ordered:
        return base, info

    def hit(side: str, e: int) -> bool:
        return machine_side(side_after(side, (rotation + e) % 360), back) in cs

    if rule == "max":
        best = max(pref, key=lambda e: (sum(hit(s, e) for s in ordered), hit(ordered[0], e), -pref.index(e)))
    else:
        cand = [e for e in pref if hit(ordered[0], e)]
        best = cand[0] if cand else base
    info["turn"] = best
    return best, info


# ───────────────────────── Xabarlar ─────────────────────────
_SIDE_FROM = {"top": ("сверху", "yuqoridan"), "bottom": ("снизу", "pastdan"), "left": ("слева", "chapdan"),
              "right": ("справа", "o'ngdan")}
_SIDE_EDGE = {"top": ("сверху", "yuqori"), "bottom": ("снизу", "pastki"), "left": ("слева", "chap"), "right": ("справа", "o'ng")}


def _g(v: float) -> str:
    return f"{round(float(v), 2):g}"


def msg2(key: str, **kw) -> tuple[str, str]:
    """(ru, uz) matn: qiymatlar tuple (ru, uz) bo'lishi mumkin."""
    ru, uz = MSG[key]

    def pick(i):
        return {k: (v[i] if isinstance(v, tuple) else v) for k, v in kw.items()}
    return ru.format(**pick(0)), uz.format(**pick(1))


class _Collector:
    """Xabarlarni (kod, buyruq yo'li, qo'shimcha kalit) bo'yicha jamlaydi: massiv teshiklari bitta qator (×N) bo'ladi."""

    def __init__(self):
        self.items: dict[tuple, dict] = {}

    def add(self, level: str, code: str, key: str, path: str, group: str = "", **kw) -> None:
        k = (code, path, group)
        it = self.items.get(k)
        if it is None:
            self.items[k] = dict(level=level, code=code, key=key, path=path, kw=kw, count=1)
        else:
            it["count"] += 1
            if level == "error":
                it["level"] = "error"

    def result(self) -> list[dict]:
        out = []
        for it in self.items.values():
            ru, uz = msg2(it["key"], **it["kw"])
            if it["count"] > 1:
                ru, uz = f"{ru} (×{it['count']})", f"{uz} (×{it['count']})"
            out.append(dict(level=it["level"], code=it["code"], text=pick(ru, uz), text_ru=ru, text_uz=uz,
                            command_path=it["path"], count=it["count"]))
        out.sort(key=lambda d: _path_key(d["command_path"]))
        if len(out) > MAX_ISSUES:
            extra = len(out) - MAX_ISSUES
            ru, uz = msg2("xnc_cn.more", n=extra)
            lvl = "error" if any(d["level"] == "error" for d in out[MAX_ISSUES:]) else "warn"
            out = out[:MAX_ISSUES] + [dict(level=lvl, code="more", text=pick(ru, uz), text_ru=ru, text_uz=uz,
                                           command_path="", count=extra)]
        return out


def _path_key(path: str) -> tuple:
    """«2.3.1» → (2, 3, 1); bo'sh yo'l (detal darajasidagi xabar) — eng boshida."""
    try:
        return tuple(int(p) for p in path.split(".") if p) if path else ()
    except ValueError:
        return (10 ** 9,)


# ───────────────────────── Tekshiruv ─────────────────────────
def _outside(x: float, y: float, L: float, W: float) -> float:
    """(x, y) nuqtaning detal to'rtburchagidan tashqaridagi masofasi (ichkarida — 0)."""
    return math.hypot(max(0.0, -x, x - L), max(0.0, -y, y - W))


def check_program(c: XncConstraints | None, prog, project=None) -> list[dict]:
    """Dastur cheklovlarga mos kelishini tekshiradi. `prog` — `xnc.machine_program` natijasi (dict) yoki XNC operatsiyasi
    (Operation: shu cheklovlar bilan hisoblanadi, `project` — kromka ma'lumoti uchun, ixtiyoriy).
    Qaytaradi: [{level: warn|error, code, text, text_ru, text_uz, command_path, count}]. `mode=off` yoki c=None — []."""
    if c is None or not c.active:
        return []
    if isinstance(prog, Operation):
        from .xnc import machine_program
        prog = machine_program(prog, project, "any", c)
    lvl = "error" if c.mode == "block" else "warn"
    col = _Collector()
    L, W = float(prog["size"]["length"]), float(prog["size"]["width"])
    T = float(prog["blank"]["thickness"])
    back = bool(prog.get("face_back"))                              # orqa yuzadan ishlov: stanok tomonlari akslangan (W18)

    # 1) gabaritlar (detal darajasida — buyruq yo'li yo'q)
    for fld, val, key, mode in (("length_min", L, "len_min", "min"), ("length_max", L, "len_max", "max"),
                                ("width_min", W, "wid_min", "min"), ("width_max", W, "wid_max", "max"),
                                ("thickness_min", T, "thk_min", "min"), ("thickness_max", T, "thk_max", "max")):
        lim: Limit = getattr(c, fld)
        if lim.enabled and ((mode == "min" and val < lim.value - EPS) or (mode == "max" and val > lim.value + EPS)):
            col.add(lvl, key, f"xnc_cn.size_{key}", "", v=_g(val), lim=_g(lim.value))

    fronts: list[tuple] = []                                        # teshiklar orasi: (a, b, r, indeks, yo'l)
    sides: dict[str, list[tuple]] = {s: [] for s in SIDES}
    for idx, o in enumerate(prog.get("ops", [])):
        kind, path = o.get("kind"), o.get("cmd_path", "") or ""
        if kind == "drill":
            r = max(0.0, float(o.get("d") or 0.0)) / 2
            x, y = float(o["x"]), float(o["y"])
            if o.get("face") == "front":
                lim = c.blind_depth_margin
                if lim.enabled and not o.get("through") and float(o.get("depth") or 0) > T - lim.value + EPS:
                    col.add(lvl, "blind_depth", "xnc_cn.blind_depth", path, n=path, v=_g(o["depth"]), t=_g(T), lim=_g(lim.value))
                lim = c.hole_edge_front_min
                if lim.enabled:
                    dist = min(x - r, L - x - r, y - r, W - y - r)
                    if dist < lim.value - EPS:
                        col.add(lvl, "hole_edge_front", "xnc_cn.hole_edge_front", path, n=path, v=_g(dist), lim=_g(lim.value))
                fronts.append((x, y, r, idx, path))
                continue
            face = o["face"]
            mface = machine_side(face, back)                        # stanok tomoni (orqa yuzada akslangan)
            z = float(o.get("z", T / 2))
            lim = getattr(c, f"hole_center_{mface}")
            if lim.enabled and z > lim.value + EPS:
                col.add(lvl, "hole_center_far", "xnc_cn.hole_center_far", path, group=face, n=path, side=_SIDE_FROM[mface],
                        v=_g(z), lim=_g(lim.value))
            flag = c.avoid_bottom_horizontal
            if flag.enabled and mface == "bottom":
                col.add("warn" if flag.value else lvl, "bottom_horizontal", "xnc_cn.bottom_horizontal", path, n=path)
            pos = y if face in ("left", "right") else x                 # chekka bo'ylab o'rin
            along = (W if face in ("left", "right") else L)
            lim = c.hole_edge_horizontal_min
            if lim.enabled:
                dist = min(z - r, T - z - r, pos - r, along - pos - r)
                if dist < lim.value - EPS:
                    col.add(lvl, "hole_edge_horizontal", "xnc_cn.hole_edge_horizontal", path, n=path, v=_g(dist),
                            lim=_g(lim.value))
            sides[face].append((pos, z, r, idx, path))
        elif kind == "groove":
            _check_groove(c, col, lvl, o, path, L, W, back)
        elif kind in ("mill_start", "mill_line", "mill_arc", "rect", "ellipse") and c.mill_max_distance.enabled:
            pts = [(o["x"], o["y"])] if kind in ("mill_start", "mill_line", "mill_arc") else [
                (p["x"], p["y"]) for p in o.get("path", [])]
            far = max((_outside(float(px), float(py), L, W) for px, py in pts), default=0.0)
            if far > c.mill_max_distance.value + EPS:
                col.add(lvl, "mill_far", "xnc_cn.mill_far", path, n=path, v=_g(far), lim=_g(c.mill_max_distance.value))

    # teshiklar chetlari orasi (frontal — bir tekislik; yon teshiklar — chekka bo'ylab o'rin va qalinlikdagi o'rin tekisligida)
    if c.hole_gap_min.enabled:
        gap = c.hole_gap_min.value
        groups = [fronts] + [sides[s] for s in SIDES]
        budget = MAX_PAIRS
        for grp in groups:
            for first, second, g in _close_pairs(grp, gap, budget):
                budget -= 1
                col.add(lvl, "hole_gap", "xnc_cn.hole_gap", second[4] or first[4], n=second[4], m=first[4], v=_g(g), lim=_g(gap))
            if budget <= 0:
                break
    return col.result()


def _check_groove(c: XncConstraints, col: _Collector, lvl: str, o: dict, path: str, L: float, W: float,
                  back: bool = False) -> None:
    x1, y1, x2, y2 = float(o["x1"]), float(o["y1"]), float(o["x2"]), float(o["y2"])
    w = max(0.0, float(o.get("width") or 0.0))
    horizontal = abs(y2 - y1) <= abs(x2 - x1) + EPS                  # asosiy yo'nalish bo'yicha (nuqta — gorizontal)
    flag = c.groove_horizontal if horizontal else c.groove_vertical
    if flag.enabled and not flag.value:
        col.add(lvl, "groove_horizontal" if horizontal else "groove_vertical",
                "xnc_cn.groove_h_forbidden" if horizontal else "xnc_cn.groove_v_forbidden", path, n=path)
    if horizontal:
        ym = (y1 + y2) / 2
        box = (min(x1, x2), ym - w / 2, max(x1, x2), ym + w / 2)
    else:
        xm = (x1 + x2) / 2
        box = (xm - w / 2, min(y1, y2), xm + w / 2, max(y1, y2))
    dist = {"top": box[1], "bottom": W - box[3], "left": box[0], "right": L - box[2]}
    cross = ("top", "bottom") if horizontal else ("left", "right")
    for side in SIDES:
        mside = machine_side(side, back)                            # chegara stanok tomoni bo'yicha (orqa yuzada akslangan)
        lim: Limit = getattr(c, f"groove_margin_{mside}")
        if not lim.enabled or (not GROOVE_MARGIN_ALL_SIDES and side not in cross):
            continue
        if dist[side] < lim.value - EPS:
            col.add(lvl, "groove_margin", "xnc_cn.groove_margin", path, group=side, n=path, side=_SIDE_EDGE[mside],
                    v=_g(max(0.0, dist[side])), lim=_g(lim.value))


def _close_pairs(pts: list[tuple], gap: float, budget: int):
    """Chetlari orasi `gap` dan kichik teshik juftliklari: (a, b, r, indeks, yo'l) ro'yxatidan (birinchi, ikkinchi, masofa),
    `ikkinchi` — dasturda keyin kelgani. Saralab, qo'shni bo'laklarnigina solishtiradi (katta massivda ham tez)."""
    if len(pts) < 2 or budget <= 0:
        return
    pts = sorted(pts, key=lambda p: p[0])
    rmax = max(p[2] for p in pts)
    found = 0
    for i, p in enumerate(pts):
        for j in range(i + 1, len(pts)):
            q = pts[j]
            if q[0] - p[0] - p[2] - rmax >= gap:                    # keyingilari yanada uzoq
                break
            g = math.hypot(q[0] - p[0], q[1] - p[1]) - p[2] - q[2]
            if g < gap - EPS:
                first, second = (p, q) if p[3] < q[3] else (q, p)
                yield first, second, g
                found += 1
                if found >= budget:
                    return


# ───────────────────────── Yuklash va operatsiya bo'yicha tekshiruv ─────────────────────────
def load() -> XncConstraints:
    """Sozlamadagi (standart profil) cheklovlar; baza xatosi / noto'g'ri yozuv — standart (o'chiq)."""
    try:
        from . import settings
        return XncConstraints.model_validate(settings.get_default("xnc_constraints"))
    except Exception:  # noqa: BLE001
        return XncConstraints()


def analyze(op, project=None, c: XncConstraints | None = None, long_side: str = "any") -> dict:
    """Operatsiya (XNC) bo'yicha: {mode, issues, extra_turn, rotation}. c=None — sozlamadan o'qiladi."""
    from .xnc import machine_program
    c = c if c is not None else load()
    if not c.active:
        return dict(mode=c.mode, issues=[], extra_turn=0, rotation=None)
    prog = machine_program(op, project, long_side, c)
    return dict(mode=c.mode, issues=check_program(c, prog), extra_turn=prog["extra_turn"], rotation=prog.get("rotation"))


def stats_fields(op, project=None) -> dict:
    """`xnc-stats` javobiga qo'shiladigan maydonlar: constraint_mode, constraint_issues, constraint_turn (qo'shimcha burish).
    Rejim off — hisob qilinmaydi (issues bo'sh)."""
    r = analyze(op, project)
    return dict(constraint_mode=r["mode"], constraint_issues=r["issues"], constraint_turn=r["extra_turn"])
