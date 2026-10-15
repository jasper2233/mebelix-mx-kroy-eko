"""XNC shablonlar kutubxonasi (W1): foydalanuvchi shablonlari (sozlama profillari, scope `xnc_template`) + o'rnatilgan
tayyor namunalar (noldan yozilgan, parametrik).

Shablon — nom bilan saqlangan dastur (`XncCommand` daraxti). Parametrik shablon: dastur boshida `Par` buyruqlari
(nom, yorliq, tur, standart qiymat, ko'rinish sharti) — detalga qo'yilganda operatsiyaning «Параметры» yorlig'ida
kiritiladi; geometriya `dx / dy / dz` (zagotovka) va Par larga ifodalar orqali bog'lanadi.

Identifikatorlar: `lib:<kalit>` — o'rnatilgan (o'zgarmas), `u:<id>` — foydalanuvchi shabloni.
Fayl formati (eksport / import, JSON): {"app": "MebeliX Kroy", "kind": "xnc_template", "version": 1, "name", "description",
"category", "program": [XncCommand…], "par_values": {…}}.
"""
from __future__ import annotations

from typing import Any, Callable

from pydantic import Field, field_validator

from ..i18n import LANG, _
from ..models import Base, XncCommand

FORMAT_KIND = "xnc_template"
FORMAT_VERSION = 1
MAX_NODES = 3000            # shablondagi jami buyruqlar
MAX_DEPTH = 24              # buyruqlar ichma-ich chuqurligi


class TemplateError(ValueError):
    pass


class XncTemplate(Base):
    """Saqlanadigan shablon (settings_profiles.data)."""
    description: str = Field("", max_length=2000)
    category: str = Field("", max_length=40)
    program: list[XncCommand] = []
    par_values: dict[str, float | str] = {}

    @field_validator("program")
    @classmethod
    def _limits(cls, v):
        n, depth = count_nodes(v)
        if n > MAX_NODES:
            raise ValueError(_("xnc_tpl_too_big", n=MAX_NODES))
        if depth > MAX_DEPTH:
            raise ValueError(_("xnc_tpl_too_deep", n=MAX_DEPTH))
        return v


def count_nodes(cmds, depth: int = 1) -> tuple[int, int]:
    """(buyruqlar soni, eng katta chuqurlik) — iterativ (chuqur daraxtda rekursiya xatosi bo'lmasin)."""
    n, deep = 0, 0
    stack = [(c, 1) for c in cmds]
    while stack:
        c, d = stack.pop()
        n += 1
        deep = max(deep, d)
        ch = c.get("children") if isinstance(c, dict) else c.children
        for x in ch or []:
            stack.append((x, d + 1))
    return n, deep


def precheck_raw(program) -> None:
    """Xom JSON (import) — pydantic ga berishdan oldin: ro'yxat, hajm va chuqurlik (iterativ)."""
    if not isinstance(program, list):
        raise TemplateError(_("xnc_tpl_bad"))
    n = 0
    stack = [(c, 1) for c in program]
    while stack:
        c, d = stack.pop()
        if not isinstance(c, dict):
            raise TemplateError(_("xnc_tpl_bad"))
        n += 1
        if n > MAX_NODES:
            raise TemplateError(_("xnc_tpl_too_big", n=MAX_NODES))
        if d > MAX_DEPTH:
            raise TemplateError(_("xnc_tpl_too_deep", n=MAX_DEPTH))
        ch = c.get("children") or []
        if not isinstance(ch, list):
            raise TemplateError(_("xnc_tpl_bad"))
        stack.extend((x, d + 1) for x in ch)


# ───────────────────────── Fayl (eksport / import) ─────────────────────────
def to_file(name: str, tpl: XncTemplate) -> dict:
    return {"app": "MebeliX Kroy", "kind": FORMAT_KIND, "version": FORMAT_VERSION, "name": name,
            **tpl.model_dump(mode="json")}


def from_file(data: Any) -> tuple[str, XncTemplate]:
    """Import fayli → (nom, shablon). Format noto'g'ri — TemplateError."""
    if not isinstance(data, dict) or data.get("kind") != FORMAT_KIND:
        raise TemplateError(_("xnc_tpl_bad"))
    name = str(data.get("name") or "").strip()
    if not name:
        raise TemplateError(_("profile_name_empty"))
    if len(name) > 100:
        raise TemplateError(_("val_text_long", f="name", n=100))
    precheck_raw(data.get("program", []))
    try:
        tpl = XncTemplate.model_validate({k: data[k] for k in ("description", "category", "program", "par_values")
                                          if k in data})
    except ValueError as e:
        raise TemplateError(_("xnc_tpl_invalid", e=str(e)[:300])) from e
    return name, tpl


# ───────────────────────── Dastur qo'shish (replace / append) ─────────────────────────
def par_names(cmds: list[XncCommand]) -> set[str]:
    out: set[str] = set()
    stack = list(cmds)
    while stack:
        c = stack.pop()
        if c.cmd == "Par":
            out.add(str(c.params.get("name", "")).strip())
        stack.extend(c.children)
    return out


def merge_program(existing: list[XncCommand], tpl: list[XncCommand], mode: str) -> tuple[list[XncCommand], list[str]]:
    """mode=replace — shablon dasturi butunlay; append — mavjud dastur oxiriga. Qo'shishda mavjud dasturdagi bilan bir
    nomli `Par` (eng yuqori darajadagi) qayta e'lon qilinmaydi — ikkala qism bitta qiymatni ishlatadi.
    Qaytaradi: (yangi dastur, qo'shilmagan Par nomlari)."""
    fresh = [c.model_copy(deep=True) for c in tpl]
    if mode != "append":
        return fresh, []
    have = par_names(existing)
    skipped: list[str] = []
    keep = []
    for c in fresh:
        nm = str(c.params.get("name", "")).strip()
        if c.cmd == "Par" and nm in have:
            skipped.append(nm)
            continue
        keep.append(c)
    return [*(x.model_copy(deep=True) for x in existing), *keep], skipped


# ───────────────────────── O'rnatilgan kutubxona ─────────────────────────
def C(cmd: str, comment: str = "", children: list[XncCommand] | None = None, **params) -> XncCommand:
    return XncCommand(cmd=cmd, params=params, comment=comment, children=children or [])


def Par(name: str, value, label: str, typ: str = "double", suffix: str = "", visible: str | None = None) -> XncCommand:
    p: dict = dict(name=name, value=value, label=label, type=typ)
    if suffix:
        p["suffix"] = suffix
    if visible:
        p["visible"] = visible
    return XncCommand(cmd="Par", params=p)


Builder = Callable[[Callable[[str, str], str]], list[XncCommand]]


def _pocket_rect(L) -> list[XncCommand]:
    mm = L("мм", "mm")
    side = lambda x, y: C("MillLine", X=x, Y=y)       # noqa: E731
    return [
        Par("cx", "dx/2", L("Центр X", "Markaz X"), suffix=mm),
        Par("cy", "dy/2", L("Центр Y", "Markaz Y"), suffix=mm),
        Par("L", 200, L("Длина кармана (по X)", "Cho'ntak uzunligi (X bo'yicha)"), suffix=mm),
        Par("W", 100, L("Ширина кармана (по Y)", "Cho'ntak eni (Y bo'yicha)"), suffix=mm),
        Par("R", 10, L("Радиус углов", "Burchak radiusi"), suffix=mm),
        Par("depth", "dz/2", L("Глубина", "Chuqurlik"), suffix=mm),
        Par("td", 8, L("Диаметр фрезы", "Freza diametri"), suffix=mm),
        C("Var", L("радиус не больше половины стороны", "radius tomonning yarmidan oshmasin"),
          name="rr", value="max(0, min(R, min(L, W)/2))"),
        C("Tool", N="Mill", D="td"),
        C("MillStart", L("кармана (C=3): точка входа на середине стороны", "cho'ntak (C=3): kirish nuqtasi tomon o'rtasida"),
          X="cx", Y="cy-W/2", DP="depth", T="Mill", C=3),
        side("cx+L/2", "cy-W/2"), C("MillFillet", R="rr"),
        side("cx+L/2", "cy+W/2"), C("MillFillet", R="rr"),
        side("cx-L/2", "cy+W/2"), C("MillFillet", R="rr"),
        side("cx-L/2", "cy-W/2"), C("MillFillet", R="rr"),
        side("cx", "cy-W/2"),
    ]


def _hole_circle(L) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [
        Par("cx", "dx/2", L("Центр X", "Markaz X"), suffix=mm),
        Par("cy", "dy/2", L("Центр Y", "Markaz Y"), suffix=mm),
        Par("D", 40, L("Диаметр отверстия", "Teshik diametri"), suffix=mm),
        Par("depth", "dz", L("Глубина (dz — сквозное)", "Chuqurlik (dz — o'tuvchi)"), suffix=mm),
        Par("td", 8, L("Диаметр фрезы", "Freza diametri"), suffix=mm),
        Par("corr", 2, L("Коррекция (0 центр, 1 справа, 2 слева)", "Korreksiya (0 markaz, 1 o'ng, 2 chap)"), typ="integer"),
        C("Tool", N="Mill", D="td"),
        C("MillStart", L("полная окружность: начало = конец", "to'liq aylana: boshi = oxiri"),
          X="cx-D/2", Y="cy", DP="depth", T="Mill", C="corr"),
        C("MillArcCenter", X="cx-D/2", Y="cy", CX="cx", CY="cy", DIR="true"),
    ]


def _outline_rounded(L) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [
        Par("r", 30, L("Радиус углов", "Burchak radiusi"), suffix=mm),
        Par("depth", "dz", L("Глубина (dz — сквозная резка)", "Chuqurlik (dz — o'tkazib kesish)"), suffix=mm),
        Par("td", 8, L("Диаметр фрезы", "Freza diametri"), suffix=mm),
        Par("corr", 2, L("Коррекция (0 центр, 1 справа, 2 слева)", "Korreksiya (0 markaz, 1 o'ng, 2 chap)"), typ="integer"),
        C("Var", name="rr", value="max(0, min(r, min(dx, dy)/2))"),
        C("Tool", N="Mill", D="td"),
        C("MillStart", L("контур детали, вход на середине верхней стороны", "detal konturi, kirish yuqori tomon o'rtasida"),
          X="dx/2", Y=0, DP="depth", T="Mill", C="corr"),
        C("MillLine", X="dx", Y=0), C("MillFillet", R="rr"),
        C("MillLine", X="dx", Y="dy"), C("MillFillet", R="rr"),
        C("MillLine", X=0, Y="dy"), C("MillFillet", R="rr"),
        C("MillLine", X=0, Y=0), C("MillFillet", R="rr"),
        C("MillLine", X="dx/2", Y=0),
    ]


def _facade_frame(L) -> list[XncCommand]:
    mm = L("мм", "mm")
    inner = C("MillRect", L("внутренняя рамка", "ichki ramka"), X="dx/2", Y="dy/2", L="L1-2*gap", W="W1-2*gap",
              R="max(0, r-gap)", DP="depth", T="Mill")
    return [
        Par("m", 70, L("Отступ рамки от края", "Ramkaning chetdan masofasi"), suffix=mm),
        Par("r", 15, L("Радиус углов", "Burchak radiusi"), suffix=mm),
        Par("depth", 4, L("Глубина", "Chuqurlik"), suffix=mm),
        Par("td", 6, L("Диаметр фрезы", "Freza diametri"), suffix=mm),
        Par("dbl", 0, L("Вторая (внутренняя) рамка", "Ikkinchi (ichki) ramka"), typ="boolean"),
        Par("gap", 10, L("Расстояние между рамками", "Ramkalar orasidagi masofa"), suffix=mm, visible="dbl"),
        C("Var", name="L1", value="dx-2*m"), C("Var", name="W1", value="dy-2*m"),
        C("Tool", N="Mill", D="td"),
        C("MillRect", L("внешняя рамка (X, Y — центр)", "tashqi ramka (X, Y — markaz)"), X="dx/2", Y="dy/2", L="L1", W="W1",
          R="r", DP="depth", T="Mill"),
        C("If", cond="dbl", children=[inner]),
    ]


def _row32(L) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [
        Par("y1", 37, L("Отступ ряда от края (по Y)", "Qatorning chetdan masofasi (Y bo'yicha)"), suffix=mm),
        Par("margin", 64, L("Минимальный отступ от торцов (по X)", "Uchlaridan eng kam masofa (X bo'yicha)"), suffix=mm),
        Par("pitch", 32, L("Шаг", "Qadam"), suffix=mm),
        Par("d", 5, L("Диаметр", "Diametr"), suffix=mm),
        Par("depth", 13, L("Глубина", "Chuqurlik"), suffix=mm),
        Par("both", 1, L("Второй ряд с противоположной стороны", "Qarama-qarshi tomondagi ikkinchi qator"), typ="boolean"),
        C("Var", L("число отверстий в ряду", "qatordagi teshiklar soni"), name="n",
          value="max(1, floor((dx-2*margin)/pitch)+1)", type="integer"),
        C("Var", L("ряд по центру детали", "qator detal markazida"), name="xs", value="(dx-(n-1)*pitch)/2"),
        C("Tool", N="Bore", D="d"),
        C("DrillFront", L("массив: AC штук с шагом AS вдоль X", "massiv: AC dona, AS qadam, X bo'ylab"),
          X="xs", Y="y1", DP="depth", T="Bore", AC="n", AS="pitch", AV="false"),
        C("If", cond="both", children=[C("DrillFront", X="xs", Y="dy-y1")]),
    ]


def _side_panel(L) -> list[XncCommand]:
    mm = L("мм", "mm")
    shelf = [C("Tool", N="Pin", D="pd"),
             C("DrillFront", X="xs", Y=37, DP="pdp", T="Pin", AC="n", AS=32, AV="false"),
             C("DrillFront", X="xs", Y="dy-37")]
    mid = [C("DrillFront", X="tp/2", Y="dy/2"), C("DrillFront", X="dx-tp/2", Y="dy/2")]
    return [
        Par("tp", 16, L("Толщина горизонтальных панелей (крыша/дно)", "Gorizontal panellar qalinligi (tom/tub)"), suffix=mm),
        Par("ce", 50, L("Отступ конфирматов от переднего/заднего края", "Konfirmatlarning old/orqa chetdan masofasi"), suffix=mm),
        Par("cd", 5, L("Диаметр под конфирмат", "Konfirmat ostidagi diametr"), suffix=mm),
        Par("shelf", 1, L("Отверстия под полкодержатели (ряд 32 мм)", "Polka tayanchlari teshiklari (32 mm qator)"), typ="boolean"),
        Par("pd", 5, L("Диаметр под полкодержатель", "Polka tayanchi diametri"), suffix=mm, visible="shelf"),
        Par("pdp", 13, L("Глубина под полкодержатель", "Polka tayanchi chuqurligi"), suffix=mm, visible="shelf"),
        Par("back", 1, L("Паз под заднюю стенку", "Orqa devor uchun paz"), typ="boolean"),
        Par("bo", 20, L("Отступ паза от заднего края", "Pazning orqa chetdan masofasi"), suffix=mm, visible="back"),
        Par("bw", 4, L("Ширина паза", "Paz eni"), suffix=mm, visible="back"),
        Par("bd", 8, L("Глубина паза", "Paz chuqurligi"), suffix=mm, visible="back"),
        C("Tool", N="Conf", D="cd"),
        C("Com", L("торцевые отверстия: x = tp/2 от краёв, y — от переднего/заднего края",
                   "uchlardagi teshiklar: x = tp/2, y — old/orqa chetdan")),
        C("DrillFront", X="tp/2", Y="ce", DP="dz", T="Conf"),
        C("DrillFront", X="tp/2", Y="dy-ce"),
        C("DrillFront", X="dx-tp/2", Y="ce"),
        C("DrillFront", X="dx-tp/2", Y="dy-ce"),
        C("If", L("длинная панель — добавить средний конфират", "chuqur panel — o'rtadagi konfirat qo'shiladi"),
          cond="dy>=500", children=mid),
        C("Var", name="n", value="max(1, floor((dx-2*(tp+64))/32)+1)", type="integer"),
        C("Var", name="xs", value="(dx-(n-1)*32)/2"),
        C("If", cond="shelf", children=shelf),
        C("If", cond="back", children=[C("Groove", X1=0, Y1="dy-bo", X2="dx", Y2="dy-bo", DP="bd", W="bw")]),
    ]


def _back_groove(L) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [
        Par("off", 20, L("Отступ паза от края", "Pazning chetdan masofasi"), suffix=mm),
        Par("w", 4, L("Ширина паза", "Paz eni"), suffix=mm),
        Par("dp", 8, L("Глубина паза", "Paz chuqurligi"), suffix=mm),
        Par("side", 0, L("Вдоль длинной стороны (0) или короткой (1)", "Uzun tomon bo'ylab (0) yoki qisqa (1)"),
            typ="integer"),
        C("If", cond="side=0", children=[C("Groove", X1=0, Y1="dy-off", X2="dx", Y2="dy-off", DP="dp", W="w")]),
        C("Else", children=[C("Groove", X1="dx-off", Y1=0, X2="dx-off", Y2="dy", DP="dp", W="w")]),
    ]


# kalit → (ru nom, uz nom, ru tavsif, uz tavsif, toifa, quruvchi)
LIBRARY: dict[str, tuple[str, str, str, str, str, Builder]] = {
    "pocket_rect": ("Карман прямоугольный", "To'rtburchak cho'ntak",
                    "Прямоугольный карман со скруглёнными углами (C=3, точка входа на середине стороны)",
                    "Yumaloq burchakli to'rtburchak cho'ntak (C=3, kirish tomon o'rtasida)", "mill", _pocket_rect),
    "hole_circle": ("Круглое отверстие (фрезой)", "Aylana teshik (freza bilan)",
                    "Круг по окружности: центр, диаметр, глубина, коррекция",
                    "Aylana bo'ylab frezalash: markaz, diametr, chuqurlik, korreksiya", "mill", _hole_circle),
    "outline_rounded": ("Контур со скруглёнными углами", "Yumaloq burchakli kontur",
                        "Контур всей детали со скруглением углов радиусом r",
                        "Butun detal konturi, burchaklar r radius bilan yumaloqlangan", "mill", _outline_rounded),
    "facade_frame": ("Фасад МДФ: рамка", "MDF fasad: ramka",
                     "Рамочная фрезеровка фасада / накладки двери, вторая внутренняя рамка по выбору",
                     "Fasad / eshik nakladkasi ramka frezasi, ixtiyoriy ikkinchi ichki ramka", "facade", _facade_frame),
    "row32": ("Ряд отверстий 32 мм", "32 mm qatorli teshiklar",
              "Ряд(ы) отверстий с шагом 32 мм: массив AC/AS по центру детали",
              "32 mm qadamli teshiklar qatori: AC/AS massivi detal markazida", "drill", _row32),
    "side_panel": ("Боковина шкафа: присадка", "Shkaf yon devori: presadka",
                   "Конфирматы в торцы крыши/дна, полкодержатели (ряд 32 мм), паз под заднюю стенку",
                   "Tom/tubga konfirmatlar, polka tayanchlari (32 mm qator), orqa devor pazi", "drill", _side_panel),
    "back_groove": ("Паз под заднюю стенку", "Orqa devor uchun paz",
                    "Паз по длинной или короткой стороне: отступ, ширина, глубина",
                    "Uzun yoki qisqa tomon bo'ylab paz: masofa, eni, chuqurligi", "groove", _back_groove),
}


def _lang_pick(lang: str | None):
    lg = (lang or LANG.get() or "ru").lower()[:2]
    return (lambda ru, uz: uz if lg == "uz" else ru), lg


def library_program(key: str, lang: str | None = None) -> list[XncCommand]:
    if key not in LIBRARY:
        raise KeyError(key)
    pick, _lg = _lang_pick(lang)
    return LIBRARY[key][5](pick)


def library_list(lang: str | None = None) -> list[dict]:
    pick, lg = _lang_pick(lang)
    out = []
    for key, (ru, uz, dru, duz, cat, build) in LIBRARY.items():
        prog = build(pick)
        out.append(dict(id=f"lib:{key}", name=uz if lg == "uz" else ru, description=duz if lg == "uz" else dru,
                        category=cat, builtin=True, par_count=sum(1 for c in prog if c.cmd == "Par"),
                        commands=count_nodes(prog)[0]))
    return out
