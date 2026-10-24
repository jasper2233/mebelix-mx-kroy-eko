"""XNC standart shablonlari — onlayn «Открыть шаблоны обработки» oynasidagi papkalar mazmuniga mos (2026-10-23 ko'rildi):
«Типовые фрезеровки» (detal chetini shakllantirish: yoy, o'yiq, burchak) va «Фасады МДФ» (yuzadagi dekor frezalar).
Dasturlar BIZNIKI — onlayn shablonlarning matni nusxalanmagan: faqat nomlar va umumiy mebel geometriyasi (parametrli).

Koordinatalar: X — o'ngga (dx), Y — pastga (dy), boshi chap-yuqori. Chetni shakllantiruvchi konturlar detaldan TASHQARIDAN
boshlanib tashqarida tugaydi (`e` — chiqish masofasi = freza diametri); korreksiya (C) chiqindi tomonga — chizma sinovida
tekshirilgan (`tests/test_xnc_templates_std.py`). Dekor (fasad) konturlari yopiq, C=0 (frezaning o'qi chiziq ustida).
"""
from __future__ import annotations

from typing import Callable

from ..models import XncCommand

L_ = Callable[[str, str], str]


def C(cmd: str, comment: str = "", children: list[XncCommand] | None = None, **params) -> XncCommand:
    return XncCommand(cmd=cmd, params=params, comment=comment, children=children or [])


def Par(name: str, value, label: str, typ: str = "double", suffix: str = "") -> XncCommand:
    p: dict = dict(name=name, value=value, label=label, type=typ)
    if suffix:
        p["suffix"] = suffix
    return XncCommand(cmd="Par", params=p)


def _edge_tool(L: L_) -> list[XncCommand]:
    """Chet frezasi umumiy parametrlari: freza diametri, chuqurlik (dz — o'tkazib kesish)."""
    mm = L("мм", "mm")
    return [Par("td", 12, L("Диаметр фрезы", "Freza diametri"), suffix=mm),
            Par("depth", "dz", L("Глубина (dz — сквозная резка)", "Chuqurlik (dz — o'tkazib kesish)"), suffix=mm),
            C("Var", L("выход фрезы за деталь", "frezaning detaldan chiqishi"), name="e", value="td"),
            C("Tool", N="Mill", D="td")]


def _start(x, y, corr: int, comment: str = "") -> XncCommand:
    return C("MillStart", comment, X=x, Y=y, DP="depth", T="Mill", C=corr)


def _line(x, y) -> XncCommand:
    return C("MillLine", X=x, Y=y)


def _arc3(x, y, x2, y2) -> XncCommand:
    return C("MillArc3P", X=x, Y=y, X2=x2, Y2=y2)


def _arcc(x, y, cx, cy, cw: bool) -> XncCommand:
    return C("MillArcCenter", X=x, Y=y, CX=cx, CY=cy, DIR="true" if cw else "false")


# ───────────────────────── Типовые фрезеровки (detal chetini shakllantirish) ─────────────────────────
# Chiqindi tomoni: harakat yo'nalishiga nisbatan chap (C=2) yoki o'ng (C=1) — ekran koordinatalarida (Y pastga).

def radius_one(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("h", 50, L("Высота дуги (стрела)", "Yoy balandligi (o'q)"), suffix=mm), *_edge_tool(L),
            _start("-e", "h", 2, L("верхняя сторона — дуга", "yuqori tomon — yoy")),
            _line(0, "h"), _arc3("dx", "h", "dx/2", 0), _line("dx+e", "h")]


def radius_two(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("h", 50, L("Высота дуги (стрела)", "Yoy balandligi (o'q)"), suffix=mm), *_edge_tool(L),
            _start("-e", "h", 2, L("верхняя дуга", "yuqori yoy")), _line(0, "h"), _arc3("dx", "h", "dx/2", 0), _line("dx+e", "h"),
            _start("-e", "dy-h", 1, L("нижняя дуга", "pastki yoy")), _line(0, "dy-h"), _arc3("dx", "dy-h", "dx/2", "dy"),
            _line("dx+e", "dy-h")]


def cut_circle(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("cx", "dx/2", L("Центр X", "Markaz X"), suffix=mm), Par("cy", "dy/2", L("Центр Y", "Markaz Y"), suffix=mm),
            Par("D", 100, L("Диаметр выреза", "Kesik diametri"), suffix=mm), *_edge_tool(L),
            _start("cx+D/2", "cy", 2, L("окружность: начало = конец", "aylana: boshi = oxiri")),
            _arcc("cx+D/2", "cy", "cx", "cy", True)]


def _notch(L: L_, r: bool) -> list[XncCommand]:
    mm = L("мм", "mm")
    out = [Par("cx", "dx/2", L("Центр выреза по X", "O'yiq markazi X"), suffix=mm),
           Par("w", 150, L("Ширина выреза", "O'yiq eni"), suffix=mm),
           Par("hd", 30, L("Глубина выреза от края", "O'yiq chuqurligi (chetdan)"), suffix=mm)]
    if r:
        out.append(Par("r", 10, L("Радиус углов выреза", "O'yiq burchak radiusi"), suffix=mm))
    out += [*_edge_tool(L), _start("cx-w/2", "-e", 2, L("вырез под ручку на верхнем крае", "yuqori chetda tutqich o'yig'i")),
            _line("cx-w/2", "hd")]
    if r:
        out.append(C("MillFillet", R="r"))
    out.append(_line("cx+w/2", "hd"))
    if r:
        out.append(C("MillFillet", R="r"))
    out.append(_line("cx+w/2", "-e"))
    return out


def notch(L: L_) -> list[XncCommand]:
    return _notch(L, False)


def notch_r(L: L_) -> list[XncCommand]:
    return _notch(L, True)


def outer_two_r(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("R", 100, L("Радиус нижних углов", "Pastki burchaklar radiusi"), suffix=mm), *_edge_tool(L),
            C("Var", name="rr", value="max(1, min(R, min(dx/2, dy)))"),
            _start("-e", "dy-rr", 1, L("два внешних радиуса снизу", "pastda ikki tashqi radius")), _line(0, "dy-rr"),
            _arcc("rr", "dy", "rr", "dy-rr", False), _line("dx-rr", "dy"),
            _arcc("dx", "dy-rr", "dx-rr", "dy-rr", False), _line("dx+e", "dy-rr")]


def inner_two_r(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("R", 60, L("Радиус нижних углов", "Pastki burchaklar radiusi"), suffix=mm), *_edge_tool(L),
            C("Var", name="rr", value="max(1, min(R, min(dx/2, dy)))"),
            _start("-e", "dy-rr", 1, L("левый внутренний радиус", "chap ichki radius")), _line(0, "dy-rr"),
            _arcc("rr", "dy", 0, "dy", True), _line("rr", "dy+e"),
            _start("dx-rr", "dy+e", 1, L("правый внутренний радиус", "o'ng ichki radius")), _line("dx-rr", "dy"),
            _arcc("dx", "dy-rr", "dx", "dy", True), _line("dx+e", "dy-rr")]


def _step(L: L_, fillet: bool, radii: bool) -> list[XncCommand]:
    mm = L("мм", "mm")
    out = [Par("a", 150, L("Длина выреза (по X)", "Kesik uzunligi (X)"), suffix=mm),
           Par("b", 100, L("Высота выреза (по Y)", "Kesik balandligi (Y)"), suffix=mm)]
    if fillet:
        out.append(Par("r", 20, L("Радиус внутреннего угла", "Ichki burchak radiusi"), suffix=mm))
    if radii:
        out.append(Par("r2", 10, L("Радиус внешних углов", "Tashqi burchaklar radiusi"), suffix=mm))
    if radii:       # tashqi radiuslar: yo'l detal cheti bo'ylab keladi va ketadi (chet bilan kesik orasidagi burchak yumaloqlanadi)
        out += [*_edge_tool(L), _start("dx-a-r2", "dy+e", 1, L("прямой вырез с радиусами", "radiusli to'g'ri kesik")),
                _line("dx-a-r2", "dy"), _arcc("dx-a", "dy-r2", "dx-a-r2", "dy-r2", False), _line("dx-a", "dy-b"),
                C("MillFillet", R="r"), _line("dx-r2", "dy-b"), _arcc("dx", "dy-b-r2", "dx-r2", "dy-b-r2", False),
                _line("dx+e", "dy-b-r2")]
        return out
    out += [*_edge_tool(L), _start("dx-a", "dy+e", 1, L("прямой вырез в правом нижнем углу", "o'ng pastki burchakda to'g'ri kesik")),
            _line("dx-a", "dy-b")]
    if fillet:
        out.append(C("MillFillet", R="r"))
    out += [_line("dx", "dy-b"), _line("dx+e", "dy-b")]
    return out


def step(L: L_) -> list[XncCommand]:
    return _step(L, False, False)


def step_fillet(L: L_) -> list[XncCommand]:
    return _step(L, True, False)


def step_radii(L: L_) -> list[XncCommand]:
    return _step(L, True, True)


def corner45(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("c", 80, L("Срез угла (катет)", "Burchak kesigi (katet)"), suffix=mm), *_edge_tool(L),
            _start("dx-c-e", "-e", 2, L("срез правого верхнего угла 45°", "o'ng yuqori burchak 45° kesigi")),
            _line("dx+e", "c+e")]


def corner_deg(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("c", 100, L("Срез по верхнему краю", "Yuqori chet bo'ylab kesik"), suffix=mm),
            Par("ang", 30, L("Угол среза, градусы", "Kesik burchagi, gradus"), suffix="°"), *_edge_tool(L),
            C("Var", L("высота среза по правому краю", "o'ng chet bo'ylab kesik balandligi"), name="hc",
              value="c*tan(ang*pi/180)"),
            C("Var", name="k", value="e/max(1, c)"),
            _start("dx-c-e", "-k*hc", 2, L("срез правого верхнего угла под углом", "o'ng yuqori burchak burchak ostida")),
            _line("dx+e", "hc+k*hc")]


def corner_outer_r(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("R", 80, L("Радиус угла", "Burchak radiusi"), suffix=mm), *_edge_tool(L),
            C("Var", name="rr", value="max(1, min(R, min(dx, dy)))"),
            _start("dx-rr", "-e", 2, L("скругление правого верхнего угла", "o'ng yuqori burchakni yumaloqlash")),
            _line("dx-rr", 0), _arcc("dx", "rr", "dx-rr", "rr", True), _line("dx+e", "rr")]


def corner_inner_r(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("R", 80, L("Радиус угла", "Burchak radiusi"), suffix=mm), *_edge_tool(L),
            C("Var", name="rr", value="max(1, min(R, min(dx, dy)))"),
            _start("dx-rr", "-e", 2, L("внутренний радиус правого верхнего угла", "o'ng yuqori burchakda ichki radius")),
            _line("dx-rr", 0), _arcc("dx", "rr", "dx", 0, False), _line("dx+e", "rr")]


# ───────────────────────── Фасады МДФ (yuzadagi dekor frezalar, yopiq konturlar) ─────────────────────────

def _decor_tool(L: L_, m: int = 70) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [Par("m", m, L("Отступ рисунка от края", "Naqshning chetdan masofasi"), suffix=mm),
            Par("dp", 4, L("Глубина фрезеровки", "Frezalash chuqurligi"), suffix=mm),
            Par("td", 6, L("Диаметр фрезы", "Freza diametri"), suffix=mm),
            C("Tool", N="Decor", D="td")]


def _ds(x, y, comment: str = "") -> XncCommand:
    return C("MillStart", comment, X=x, Y=y, DP="dp", T="Decor", C=0)


def f_arch(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("ha", 100, L("Высота арки", "Arka balandligi"), suffix=mm),
            Par("r", 15, L("Радиус нижних углов", "Pastki burchaklar radiusi"), suffix=mm),
            _ds("dx/2", "dy-m", L("рамка с аркой сверху (вход — середина низа)", "tepasi arkali ramka (kirish — past o'rtasi)")),
            _line("dx-m", "dy-m"), C("MillFillet", R="r"), _line("dx-m", "m+ha"),
            _arc3("m", "m+ha", "dx/2", "m"), _line("m", "dy-m"), C("MillFillet", R="r"), _line("dx/2", "dy-m")]


def f_outer_r(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("r", 40, L("Радиус углов", "Burchaklar radiusi"), suffix=mm),
            C("MillRect", L("рамка со скруглёнными углами (X, Y — центр)", "yumaloq burchakli ramka (X, Y — markaz)"),
              X="dx/2", Y="dy/2", L="dx-2*m", W="dy-2*m", R="r", DP="dp", T="Decor")]


def f_inner_r(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("r", 40, L("Радиус вогнутых углов", "Botiq burchaklar radiusi"), suffix=mm),
            _ds("m+r", "m", L("рамка с вогнутыми углами", "botiq burchakli ramka")),
            _line("dx-m-r", "m"), _arcc("dx-m", "m+r", "dx-m", "m", False),
            _line("dx-m", "dy-m-r"), _arcc("dx-m-r", "dy-m", "dx-m", "dy-m", False),
            _line("m+r", "dy-m"), _arcc("m", "dy-m-r", "m", "dy-m", False),
            _line("m", "m+r"), _arcc("m+r", "m", "m", "m", False)]


def f_kiev(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("r", 35, L("Радиус вогнутых углов", "Botiq burchaklar radiusi"), suffix=mm),
            Par("h", 25, L("Подъём верхней и нижней дуги", "Yuqori va pastki yoy ko'tarilishi"), suffix=mm),
            _ds("m+r", "m+h", L("«Киевский»: вогнутые углы и дуги сверху/снизу", "botiq burchaklar, tepa/past yoylar")),
            _arc3("dx-m-r", "m+h", "dx/2", "m"), _arcc("dx-m", "m+h+r", "dx-m", "m+h", False),
            _line("dx-m", "dy-m-h-r"), _arcc("dx-m-r", "dy-m-h", "dx-m", "dy-m-h", False),
            _arc3("m+r", "dy-m-h", "dx/2", "dy-m"), _arcc("m", "dy-m-h-r", "m", "dy-m-h", False),
            _line("m", "m+h+r"), _arcc("m+r", "m+h", "m", "m+h", False)]


def f_rays(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L, 60), Par("n", 3, L("Количество линий", "Chiziqlar soni"), typ="integer"),
            Par("g", 12, L("Шаг между линиями", "Chiziqlar orasidagi qadam"), suffix=mm),
            C("Var", name="i", value=0, type="integer"),
            C("While", L("Г-образные лучи от левого нижнего угла", "chap pastki burchakdan L-shaklli nurlar"), cond="i<n",
              children=[_ds("m+i*g", "m"), _line("m+i*g", "dy-m-i*g"), _line("dx-m", "dy-m-i*g"),
                        C("Set", name="i", value="i+1")])]


def f_frame(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("b", 120, L("Отступ поперечин от верха/низа рамки", "Ko'ndalanglarning ramka tepa/pastidan masofasi"),
                                 suffix=mm),
            C("MillRect", L("рамка", "ramka"), X="dx/2", Y="dy/2", L="dx-2*m", W="dy-2*m", R=0, DP="dp", T="Decor"),
            _ds("m", "m+b", L("верхняя поперечина", "yuqori ko'ndalang")), _line("dx-m", "m+b"),
            _ds("m", "dy-m-b", L("нижняя поперечина", "pastki ko'ndalang")), _line("dx-m", "dy-m-b")]


def f_raport(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("s", 40, L("Размер угловых квадратов", "Burchak kvadratlari o'lchami"), suffix=mm),
            C("MillRect", L("рамка", "ramka"), X="dx/2", Y="dy/2", L="dx-2*m", W="dy-2*m", R=0, DP="dp", T="Decor"),
            C("MillRect", L("угловые квадраты", "burchak kvadratlari"), X="m+s/2", Y="m+s/2", L="s", W="s", R=0, DP="dp", T="Decor"),
            C("MillRect", X="dx-m-s/2", Y="m+s/2", L="s", W="s", R=0, DP="dp", T="Decor"),
            C("MillRect", X="m+s/2", Y="dy-m-s/2", L="s", W="s", R=0, DP="dp", T="Decor"),
            C("MillRect", X="dx-m-s/2", Y="dy-m-s/2", L="s", W="s", R=0, DP="dp", T="Decor")]


def f_waist(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("w", 25, L("Прогиб боковых сторон («талия»)", "Yon tomonlar egilishi («bel»)"), suffix=mm),
            Par("r", 15, L("Радиус углов", "Burchaklar radiusi"), suffix=mm),
            _ds("dx/2", "m", L("рамка с вогнутыми боковыми сторонами (вход — середина верха)", "yon tomonlari botiq ramka")),
            _line("dx-m", "m"), C("MillFillet", R="r"), _arc3("dx-m", "dy-m", "dx-m-w", "dy/2"), C("MillFillet", R="r"),
            _line("m", "dy-m"), C("MillFillet", R="r"), _arc3("m", "m", "m+w", "dy/2"), C("MillFillet", R="r"),
            _line("dx/2", "m")]


def f_corner(L: L_) -> list[XncCommand]:
    mm = L("мм", "mm")
    return [*_decor_tool(L), Par("c", 35, L("Срез углов рамки", "Ramka burchaklari kesigi"), suffix=mm),
            _ds("m+c", "m", L("рамка со срезанными углами", "burchaklari kesilgan ramka")),
            _line("dx-m-c", "m"), _line("dx-m", "m+c"), _line("dx-m", "dy-m-c"), _line("dx-m-c", "dy-m"),
            _line("m+c", "dy-m"), _line("m", "dy-m-c"), _line("m", "m+c"), _line("m+c", "m")]


MILL_FOLDER = ("Типовые фрезеровки", "Tipik frezalar")
FACADE_FOLDER = ("Фасады МДФ", "MDF fasadlar")

# kalit → (ru nom, uz nom, papka (ru, uz), namuna detal (dx, dy), quruvchi)
STD: dict[str, tuple[str, str, tuple[str, str], tuple[int, int], Callable[[L_], list[XncCommand]]]] = {
    "m_radius1": ("1 сторона с радиусом", "1 tomoni radiusli", MILL_FOLDER, (600, 400), radius_one),
    "m_radius2": ("2 стороны с радиусом", "2 tomoni radiusli", MILL_FOLDER, (600, 400), radius_two),
    "m_circle": ("Вырез круг", "Doira kesik", MILL_FOLDER, (600, 400), cut_circle),
    "m_notch": ("Вырез под ручку", "Tutqich o'yig'i", MILL_FOLDER, (600, 400), notch),
    "m_notch_r": ("Вырез под ручку с радиусом", "Radiusli tutqich o'yig'i", MILL_FOLDER, (600, 400), notch_r),
    "m_outer2": ("Два внешних радиуса", "Ikki tashqi radius", MILL_FOLDER, (600, 400), outer_two_r),
    "m_inner2": ("Два внутренних радиуса", "Ikki ichki radius", MILL_FOLDER, (600, 400), inner_two_r),
    "m_step": ("Прямой вырез", "To'g'ri kesik", MILL_FOLDER, (600, 400), step),
    "m_step_f": ("Прямой вырез со скруглением", "Yumaloqlangan to'g'ri kesik", MILL_FOLDER, (600, 400), step_fillet),
    "m_step_r": ("Прямой вырез с радиусами", "Radiusli to'g'ri kesik", MILL_FOLDER, (600, 400), step_radii),
    "m_corner": ("Угол", "Burchak", MILL_FOLDER, (600, 400), corner45),
    "m_corner_deg": ("Угол в градусах", "Gradusli burchak", MILL_FOLDER, (600, 400), corner_deg),
    "m_corner_or": ("Угол с внешним радиусом", "Tashqi radiusli burchak", MILL_FOLDER, (600, 400), corner_outer_r),
    "m_corner_ir": ("Угол с внутренним радиусом", "Ichki radiusli burchak", MILL_FOLDER, (600, 400), corner_inner_r),
    "f_arch": ("Арка", "Arka", FACADE_FOLDER, (400, 700), f_arch),
    "f_outer_r": ("Внешний радиус", "Tashqi radius", FACADE_FOLDER, (400, 700), f_outer_r),
    "f_inner_r": ("Внутренний радиус", "Ichki radius", FACADE_FOLDER, (400, 700), f_inner_r),
    "f_kiev": ("Киевский", "Kiev", FACADE_FOLDER, (400, 700), f_kiev),
    "f_rays": ("Лучи", "Nurlar", FACADE_FOLDER, (400, 700), f_rays),
    "f_frame": ("Рамка", "Ramka", FACADE_FOLDER, (400, 700), f_frame),
    "f_raport": ("Рапорт", "Raport", FACADE_FOLDER, (400, 700), f_raport),
    "f_waist": ("Талия", "Bel", FACADE_FOLDER, (400, 700), f_waist),
    "f_corner": ("Угол", "Burchak", FACADE_FOLDER, (400, 700), f_corner),
}
