"""`.project` (XML) fayllaridan import — korxonaning mavjud loyihalari (Bazis eksporti) uchun.

Faqat foydalanuvchining o'z ma'lumotlari o'qiladi: mahsulotlar, detallar (o'lchamlar, soni, tekstura,
kromkalar), material/kromka parametrlari, kesish parametrlari va detallarga bog'langan CNC dasturlari
(teshik, freza, paz). Fayldagi ikkilik kroy natijasi (`data`) O'QILMAYDI — import qilingan loyiha
MebeliX optimizatori bilan qayta «Раскроить» qilinadi. Oldingi natijaning ochiq ko'rsatkichlari
(listlar soni, to'ldirish %) faqat solishtirish uchun operatsiya izohiga yoziladi.

Loyiha o'lcham rejimi fayldagi «cSizeMode» dan olinadi (0 — заготовка, 1 — деталь, 2 — после прифуговки) va
detal o'lchami shu rejimdagi atributdan (l/w, dl/dw, jl/jw); kromka qalinligi va prifugovka EL parametrlaridan.
Detal «ID» (`Part.uid`) — fayldagi `<part id="N">` raqami (onlayn tizim ham shuni ko'rsatadi; detal bir nechta
operatsiyada bo'lsa ham o'sha raqam); yaroqsiz id — eng kattasidan keyingi bo'sh raqam. O operatsiyasining egasi —
mahsulot ichidagi `<operation id="N"/>` havolasi (yoki `owner` atributi).
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

try:  # xavfsiz XML o'qish (XXE / «billion laughs» dan himoya)
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET  # noqa: N817

from ..models import (GR_DEFAULTS, CSCutParams, CSMaterialParams, EdgeRef, ELParams, FirstCutDir, GRParams, GrooveSide,
                      OpCostBase, OpType, Operation, Part, Product, Project, SheetRounding, SizeMode, StockSheet,
                      StripSort, XncCommand, XNCParams)
from ..i18n import _
from ..models import user_params_of
from ..services import el_symbols, import_formats, o_ops, product_program, sp_ops
from . import register

CURRENCY = {"сум": "UZS", "сўм": "UZS", "so'm": "UZS", "uzs": "UZS", "руб": "RUB", "руб.": "RUB", "$": "USD",
            "usd": "USD", "eur": "EUR", "€": "EUR", "тенге": "KZT"}



# eski fayllarda kromka rangi berilmasa — tartib bo'yicha standart ranglar
_EL_COLORS = ["#000000", "#D2691E", "#6495ED", "#FF7F50", "#5F9EA0"]

def _f(v, d: float = 0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d


def _i(v, d: int = 0) -> int:
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return d


def _b(v, d: bool = False) -> bool:
    if v is None:
        return d
    return str(v).strip().lower() in ("true", "1", "yes", "да")


_UID_MAX = 10 ** 9


def _part_uid(v) -> int:
    """Fayldagi detal id → ko'rinadigan «ID» (uid): faqat musbat butun son (≤ 1e9) yaroqli, aks holda 0
    (keyin eng katta id dan keyingi raqam beriladi)."""
    s = str(v).strip() if v is not None else ""
    return int(s) if re.fullmatch(r"[0-9]+", s) and 0 < int(s) <= _UID_MAX else 0


def _opt_len(v) -> float | None:
    """Torsovka / otstup: manfiy yoki yo'q — None (umumiy qiymat ishlatiladi), aks holda son."""
    if v is None:
        return None
    x = _f(v, -1.0)
    return x if x >= 0 else None


def _round_code(v) -> int:
    """Yaxlitlash kodi (o'nlik×10 + rejim 0..2); noto'g'ri bo'lsa — [0.00] yaqiniga (20)."""
    c = _i(v, 20)
    return c if 0 <= c <= 62 and c % 10 <= 2 else 20


# GibLab «Расчет стоимости операции по»: 0 kesish uzunligi, 1 detal perimetri, 2 material maydoni, 3 detal maydoni
COST_TYPE = {0: OpCostBase.CUT_LENGTH, 1: OpCostBase.PART_PERIMETER, 2: OpCostBase.MATERIAL_AREA,
             3: OpCostBase.PART_AREA}
SHEET_ROUND = {r.value: r for r in SheetRounding}
SIZE_MODE = {0: SizeMode.BLANK, 1: SizeMode.DETAIL, 2: SizeMode.JOINTED}


def _fill_pct(v, d: float = 90.0) -> float:
    """Расчетный процент заполнения: fayllarda ulush (0.9 = 90 %); ba'zi versiyalarda chiqindi ulushi (0.1)."""
    if v is None:
        return d
    x = _f(v, -1.0)
    if x < 0:
        return d
    x = x * 100 if x <= 1 else x
    return round(x if x >= 50 else 100 - x, 2)


def _num_or_expr(v):
    """Son bo'lsa float, aks holda ifoda matni (masalan 'dz+3' yoki o'zgaruvchi nomi). Son fayldagi yozuvi bizning
    standart yozuvdan farq qilsa («34.0», «3.00», «08») — matn sifatida saqlanadi (o'zgarmas ifoda, qiymati bir xil):
    dastur matni va eksport faylda yozilganidek qoladi."""
    if v is None:
        return None
    try:
        f = float(v)
    except ValueError:
        return str(v)
    t = str(v).strip()
    if math.isfinite(f) and t != _canon_num(f):
        return t
    return f


def _canon_num(f: float) -> str:
    """Eksport yozuvi (`project_export_xnc.num` bilan bir xil): butun — nuqtasiz, aks holda eng qisqa aniq yozuv."""
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(f)


_TZ = timezone(timedelta(hours=5))        # korxona (O'zbekiston, UTC+5) — epoch sanani mahalliy kunga o'giradi


def _date(v) -> date | None:
    """Sana: epoch millisekund (`1775278504994`; 10 xonali — soniya), ISO (`2026-04-04`) yoki `04.04.2026`.
    Mantiqsiz yil (1990..2100 dan tashqari) — None (loyiha sanasi bugungi kun bo'lib qoladi)."""
    if not v:
        return None
    v = str(v).strip()
    d: date | None = None
    if re.fullmatch(r"\d{10,14}", v):
        n = int(v)
        try:
            d = datetime.fromtimestamp(n / 1000 if n >= 10 ** 11 else n, _TZ).date()
        except (OverflowError, OSError, ValueError):
            return None
    else:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", v) or re.match(r"(\d{2})\.(\d{2})\.(\d{4})", v)
        if not m:
            return None
        g = m.groups()
        try:
            d = date(int(g[0]), int(g[1]), int(g[2])) if len(g[0]) == 4 else date(int(g[2]), int(g[1]), int(g[0]))
        except ValueError:
            return None
    return d if 1990 <= d.year <= 2100 else None


# ───────────────────────── CNC dasturi (XML) → XncCommand ─────────────────────────
DRILL = {"bf": "DrillFront", "bl": "DrillLeft", "br": "DrillRight", "bt": "DrillTop", "bb": "DrillBottom"}


KNOWN_TAGS = {"tool", "var", "ms", "ml", "mac", "ma", "gr", "xy", *DRILL}


def program_to_commands(xml_text: str, unknown: set[str] | None = None
                        ) -> tuple[list[XncCommand], tuple[float, float, float] | None]:
    """Detal CNC dasturini MebeliX buyruqlar daraxtiga o'giradi. Qaytaradi: (buyruqlar, (dx, dy, dz)).
    Teglar: tool, var, bf/bl/br/bt/bb (teshik; `ac`/`as`/`av` — massiv: soni/qadam/vertikal → AC/AS/AV), ms/ml/mac/ma
    (freza: `ma` — radiusli yoy → MillArc X,Y,DP,R,DIR), gr (paz), xy (koordinata boshi → Origin X,Y).
    `unknown` berilsa — tanilmagan teglar nomi shunga yig'iladi (import ogohlantirishi uchun)."""
    if not xml_text:
        return [], None
    try:
        root = ET.fromstring(xml_text.encode("utf-8"))
    except Exception:  # noqa: BLE001 — buzilgan dastur: tashlab ketiladi
        return [], None
    size = (_f(root.get("dx")), _f(root.get("dy")), _f(root.get("dz")))
    out: list[XncCommand] = []
    for el in root:
        a = el.attrib
        tag = el.tag
        p: dict = {}
        cmd = None
        comment = a.get("comment", "")
        if tag == "tool":
            cmd, p = "Tool", {"N": a.get("name", ""), "D": _f(a.get("d"))}
        elif tag == "var":
            cmd, p = "Var", {"name": a.get("name", ""), "value": _num_or_expr(a.get("expr", "0")),
                             "type": a.get("type", "double")}
        elif tag in DRILL:
            cmd = DRILL[tag]
            for k_src, k_dst in (("x", "X"), ("y", "Y"), ("z", "Z"), ("dp", "DP"), ("ac", "AC"), ("as", "AS")):
                if a.get(k_src) is not None:
                    p[k_dst] = _num_or_expr(a.get(k_src))
            if a.get("av") is not None:                # vertikal massiv: bayroq (true/false) yoki ifoda
                p["AV"] = _num_or_expr(a.get("av"))
            if a.get("name"):
                p["T"] = a["name"]
            if tag != "bf":
                if a.get("m") is not None:             # «Середина по Z»: true — qalinlik o'rtasida, false — z aniq (standart true)
                    p["M"] = "true" if _b(a.get("m"), True) else "false"
                if a.get("ver") is not None:           # yordamda yo'q (format versiyasi bo'lishi mumkin) — saqlanadi, ishlatilmaydi
                    p["VER"] = _num_or_expr(a.get("ver"))
        elif tag == "ms":
            cmd = "MillStart"
            # yozilmagan atribut — «oldingi qiymat» qoidasi (evaluator): importer 0 qo'ymaydi
            p = {"X": _num_or_expr(a.get("x")), "Y": _num_or_expr(a.get("y")),
                 "DP": _num_or_expr(a.get("dp")), "T": a.get("name", ""), "C": _i(a.get("c"), 0)}
            for k_src, k_dst in (("sdp", "SDP"), ("sxy", "SXY")):   # chuqurlikka / tekislikdagi qadam (ifoda)
                if a.get(k_src) is not None:
                    p[k_dst] = _num_or_expr(a.get(k_src))
            for k_src, k_dst in (("in", "IN"), ("out", "OUT")):     # kirish / chiqish turi (butun)
                if a.get(k_src) is not None:
                    p[k_dst] = _i(a.get(k_src), 0)
        elif tag == "ml":
            cmd, p = "MillLine", {"X": _num_or_expr(a.get("x")), "Y": _num_or_expr(a.get("y"))}
            if a.get("dp") is not None:
                p["DP"] = _num_or_expr(a.get("dp"))
        elif tag == "mac":
            cmd, p = "MillArcCenter", {"X": _num_or_expr(a.get("x")), "Y": _num_or_expr(a.get("y")),
                                       "CX": _num_or_expr(a.get("cx")), "CY": _num_or_expr(a.get("cy")),
                                       "DIR": a.get("dir", "false")}
            if a.get("dp") is not None:
                p["DP"] = _num_or_expr(a.get("dp"))
        elif tag == "ma":                              # radiusli yoy (R manfiy — teskari yo'nalish)
            cmd = "MillArc"
            p = {"X": _num_or_expr(a.get("x")), "Y": _num_or_expr(a.get("y")),
                 "R": _num_or_expr(a.get("r")), "DIR": a.get("dir", "false")}
            if a.get("dp") is not None:
                p["DP"] = _num_or_expr(a.get("dp"))
        elif tag == "xy":                              # koordinata boshi
            cmd, p = "Origin", {"X": _num_or_expr(a.get("x", "0")), "Y": _num_or_expr(a.get("y", "0"))}
        elif tag == "gr":
            cmd = "Groove"
            p = {"X1": _num_or_expr(a.get("x1")), "Y1": _num_or_expr(a.get("y1")),
                 "X2": _num_or_expr(a.get("x2")), "Y2": _num_or_expr(a.get("y2")),
                 "DP": _num_or_expr(a.get("dp")), "W": _num_or_expr(a.get("t", "4")), "T": a.get("name", "")}
            if a.get("c") is not None:                 # korreksiya: 0 markaz, 1 o'ng, 2 chap
                p["C"] = _i(a.get("c"), 0)
            if a.get("p") is not None:                 # yordamda yo'q (korpusda 441 ta, hammasi 0) — saqlanadi, ishlatilmaydi
                p["P"] = _num_or_expr(a.get("p"))
        if cmd:
            p = {k: v for k, v in p.items() if v is not None}
            out.append(XncCommand(cmd=cmd, params=p, comment=comment, enabled=_b(a.get("enable"), True)))
        elif unknown is not None and tag not in KNOWN_TAGS:
            unknown.add(str(tag))
    return out, size


# ───────────────────────── Asosiy import ─────────────────────────
# Import parametrlari (W18, `import_formats` katalogi, format kaliti «project»): operatsiya turi → parametr kaliti.
# Dialogdan tashqarida (`/projects/import-file`) parametr berilmaydi — hammasi yoqiq (avvalgi xulq).
_OPT_BY_TYPE = {"XNC": "import_xnc", "O": "import_o", "SP": "import_sp", "CL": "import_cl", "LB": "import_lb"}


@register(".project", "Loyiha fayli (.project, XML)", key="project")
def import_project(data: bytes, filename: str = "") -> tuple[Project, list[str]]:
    warnings: list[str] = []
    try:
        root = ET.fromstring(data)
    except Exception as e:  # noqa: BLE001
        raise ValueError(_("import_not_xml", e=e)) from e
    if root.tag != "project":
        raise ValueError(_("import_not_project"))

    goods = {g.get("id"): g for g in root.findall("good")}
    first_cs = next((o for o in root.findall("operation") if o.get("typeId") == "CS"), None)
    if first_cs is None:                      # (CL) faqat погонаж bo'lsa — birinchi CL ning cSizeMode i
        first_cs = next((o for o in root.findall("operation") if o.get("typeId") == "CL"), None)
    size_mode = SIZE_MODE.get(_i(first_cs.get("cSizeMode"), 1) if first_cs is not None else 1, SizeMode.DETAIL)
    name = root.get("name") or re.sub(r"\.project$", "", filename.rsplit("/", 1)[-1], flags=re.I) or "Import"
    cur = (root.get("currency") or "UZS").strip()
    p = Project(name=name, currency=CURRENCY.get(cur.lower(), cur.upper()[:3] if cur.isascii() else "UZS"),
                size_mode=size_mode, note=root.get("description", "") or "")
    dims = {SizeMode.BLANK: ("l", "w"), SizeMode.DETAIL: ("dl", "dw"), SizeMode.JOINTED: ("jl", "jw")}[size_mode]
    d_order, d_ready = _date(root.get("orderDate")), _date(root.get("date"))     # buyurtma sanasi / tayyorlik sanasi
    if d_order or d_ready:
        p.order_date = d_order or d_ready
    if d_ready:
        p.ready_date = d_ready

    # Mahsulotlar va detallar (fayldagi detal id → Part)
    src_parts: dict[str, Part] = {}
    src_part_el: dict[str, object] = {}
    prod_by_src: dict[str, Product] = {}     # fayldagi mahsulot good id → Product (O operatsiyasi egasi uchun)
    prod_ops: dict[str, Product] = {}        # mahsulot ichidagi `<operation id="N"/>` → egasi mahsulot (F25)
    max_file_id = 0                          # fayldagi eng katta yaroqli detal id (uid siz detallar shundan davom etadi)
    neg_src: dict[str, tuple[Part, object]] = {}     # manfiy o'lchamli (Bazis'dan hisoblanmagan) detallar: faqat CL operatsiyasi oladi
    for g in root.findall("good"):
        if g.get("typeId") != "product":
            continue
        prod = Product(code=g.get("code", "") or "", name=g.get("name") or "Mahsulot", qty=max(0, _i(g.get("count"), 1)),
                       phone1=g.get("phone1") or "", phone2=g.get("phone2") or "", description=g.get("description") or "")
        # «Свойства»: product.order → Данные заказа; qolgan «x.y» atributlar — Дополнительные параметры
        prod.order_info = g.get("product.order") or ""
        prod.extra = {k: v for k, v in g.attrib.items() if "." in k and k != "product.order" and v != ""}
        if g.get("program"):      # «Программа» (W12): parametrik mahsulot dasturi (xml; teg nomlari — taxmin, product_program.from_xml)
            prod.program, prod.legacy_program = product_program.from_xml(g.get("program"), prod.name, warnings)
        p.products.append(prod)
        if g.get("id") is not None:
            prod_by_src[g.get("id")] = prod
        for oref in g.findall("operation"):     # real fayllarda O operatsiyasi egasi shunday yoziladi
            if oref.get("id") is not None:
                prod_ops[oref.get("id")] = prod
        for pe in g.iter("part"):
            pid = pe.get("id")
            max_file_id = max(max_file_id, _part_uid(pid))
            # loyiha o'lcham rejimidagi o'lcham (yo'q bo'lsa — boshqasi)
            L = _f(pe.get(dims[0])) or _f(pe.get("dl")) or _f(pe.get("l"))
            W = _f(pe.get(dims[1])) or _f(pe.get("dw")) or _f(pe.get("w"))
            neg = L < 0 or W < 0             # manfiy o'lcham — погонажный (CL) detali, Bazis hisoblab bo'lmagan (T_W11_CL.md §4)
            if neg:
                from ..services.cl_import import negative_length
                L, raw_l = negative_length(L) if L < 0 else (L, None)
                W = 0.0
            desig = pe.get("part.designation") or ""
            code = pe.get("code") or pe.get("part.code") or ""
            # pripusk (allowanceT/B/L/R, mm) va «Группировка деталей в блок» (groupInBlock: 0 yo'q, 1 uzunlik, 2 en;
            # groupInBlockMC / groupInBlockMaxC — blokdagi min / maks detal soni)
            grp = {1: "length", 2: "width"}.get(_i(pe.get("groupInBlock"), 0), "none")
            part = Part(uid=_part_uid(pid), product_id=prod.id, name=pe.get("name", "") or "", code=code,
                        description=desig if desig and desig != code else "",
                        length=L, width=W, qty=max(0, _i(pe.get("count"), 1)), grain=_b(pe.get("txt")),
                        minus_qty=max(0, _i(pe.get("minusCount"), 0)),
                        allow_top=max(0.0, _f(pe.get("allowanceT"))), allow_bottom=max(0.0, _f(pe.get("allowanceB"))),
                        allow_left=max(0.0, _f(pe.get("allowanceL"))), allow_right=max(0.0, _f(pe.get("allowanceR"))),
                        group_by=grp, group_min=max(0, _i(pe.get("groupInBlockMC"), 0)) if grp != "none" else 0,
                        group_max=max(0, _i(pe.get("groupInBlockMaxC"), 0)) if grp != "none" else 0,
                        user_params=user_params_of(pe.attrib, "part.", ("part.code", "part.designation", "part.position")))
            if neg:
                part.src_length = raw_l                      # None — faqat eni manfiy bo'lgan (bu holda uzunlik odatdagidek o'qiladi)
                neg_src[pid] = (part, pe)
                continue
            src_parts[pid] = part
            src_part_el[pid] = pe

    ops_by_src: dict[str, Operation] = {}
    edge_ops: dict[str, Operation] = {}      # '@operation#N' → EL operatsiya
    groove_ops: dict[str, Operation] = {}    # '@operation#N' → GR operatsiya
    used_parts: set[str] = set()
    copies: dict[str, list[Part]] = {}       # fayldagi detal id → CS dagi Part(lar)
    ordered: list[Operation] = []
    xnc_links: list[tuple[str, Operation]] = []
    xnc_no_count: set[str] = set()
    sp_links: list[tuple[str, Operation]] = []      # (SP) <part id> havolalari: (fayldagi detal id, SP operatsiya)
    stats = {"CS": 0, "EL": 0, "XNC": 0, "GR": 0, "SP": 0, "CL": 0}
    cl_uncomputed = 0                        # (CL) hisoblanmagan (manfiy uzunlikli) detallar soni
    skipped_ops: list[tuple[str, str]] = []  # (tur, nom) — import qilinmagan operatsiyalar
    unknown_tags: dict[str, set[str]] = {}   # XNC kodi → tanilmagan dastur teglari

    opt_skipped: dict[str, int] = {}         # import parametrlari bo'yicha o'tkazib yuborilgan operatsiyalar: tur → soni
    for oe in root.findall("operation"):
        t = oe.get("typeId")
        oid = oe.get("id")
        if t in _OPT_BY_TYPE and not import_formats.option(_OPT_BY_TYPE[t], True):
            opt_skipped[t] = opt_skipped.get(t, 0) + 1
            continue
        if t == "GR":
            gd = GR_DEFAULTS            # atribut yo'q bo'lsa — formatdagi «по умолчанию» qiymatlar (4 / 8 / 10 / true / 4)
            gp = GRParams(width=_f(oe.get("grWidth"), gd["width"]) or gd["width"],
                          depth=_f(oe.get("grDepth"), gd["depth"]), offset=_f(oe.get("grOffset"), gd["offset"]),
                          offset_inclusive=_b(oe.get("grOffsetIncl"), gd["offset_inclusive"]),
                          saw_thickness=_f(oe.get("grSawthick"), gd["saw_thickness"]) or gd["saw_thickness"],
                          price=_f(oe.get("grCost"), 0))
            op = Operation(type=OpType.GR, code=oe.get("code") or "", name=oe.get("typeName") or "Пазование", gr=gp,
                           description=oe.get("description") or "",
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            groove_ops[f"@operation#{oid}"] = op
            ops_by_src[oid] = op
            ordered.append(op)
            stats["GR"] += 1
        elif t == "EL":
            band = goods.get((oe.find("material").get("id") if oe.find("material") is not None else None) or "")
            tool = goods.get(oe.get("tool1") or "")
            el = ELParams(
                count_material=_b(oe.get("elCalcMat"), True),
                width=_f(oe.get("w"), _f(band.get("w") if band is not None else None, 19)),
                thickness=_f(oe.get("t"), _f(band.get("t") if band is not None else None, 0)),
                jointing_width=_f(tool.get("elWidthPreJoint") if tool is not None else None, 0),
                waste_percent=_f(oe.get("elWastePRC"), 0),
                overhang=_f(tool.get("elRestSide") if tool is not None else None, 20),
                min_glue_length=_f(tool.get("elMinSize") if tool is not None else None, 0),
                # eski fayllarda belgi / rang yo'q: kromka operatsiyalari tartibi bo'yicha (A, B, C …; standart ranglar)
                # — «Настройка символов и цветов» jadvalidan (services/el_symbols.py; standarti A, B, C … + `_EL_COLORS`)
                symbol=(oe.get("elSymbol") or el_symbols.style_at(stats["EL"])[0])[:1],
                color=oe.get("elColor") or el_symbols.style_at(stats["EL"])[1],
                marker_lines=max(0, min(3, _i(oe.get("elLineMark"), 1))),      # 0 — chiziqsiz (faylda shunday bo'lsa)
                min_perp_side=_f(oe.get("elMinDimDetail"), 0),
                price=_f(band.get("cost") if band is not None else None, 0),
                op_price=_f(tool.get("elCost") if tool is not None else None, 0),
                material_round=_round_code(oe.get("elRoundMat")),
                work_round=_round_code(oe.get("elRoundLength")),
            )
            op = Operation(type=OpType.EL, code=(band.get("code") or "") if band is not None else "",
                           name=(band.get("name") or "Kromka") if band is not None else "Kromka", el=el,
                           description=oe.get("description") or "",
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            edge_ops[f"@operation#{oid}"] = op
            ops_by_src[oid] = op
            ordered.append(op)
            stats["EL"] += 1
        elif t == "CS":
            me = oe.find("material")
            sheet = goods.get(me.get("id")) if me is not None else None
            tool = goods.get(oe.get("tool1") or "")
            tg = (lambda k, dflt=None: tool.get(k) if tool is not None else dflt)
            kerf_div = _f(tg("swSawthickDiv"), -1)
            thick = _f(oe.get("t"), _f(sheet.get("t") if sheet is not None else None, 16))
            if thick > 1000:                 # real fayllarda «qalinlik» 3000 mm ham uchraydi (list emas, boshqa material) — qisqartiriladi
                warnings.append(_("imp_thickness_clamped", v=f"{thick:g}"))
                thick = 1000.0
            mat = CSMaterialParams(
                thickness=thick,
                price=_f(sheet.get("cost") if sheet is not None else None, 0),
                est_fill_percent=_fill_pct(oe.get("cCPF") if oe.get("cCPF") is not None else oe.get("cFillRep")),
                cost_by_sheets=_b(oe.get("cCostByItem"), True),
                sheet_rounding=SHEET_ROUND.get(str(_i(oe.get("cCostByItemRound"), 11)), SheetRounding.WHOLE),
                op_cost_base=COST_TYPE.get(_i(oe.get("cCostType"), 0), OpCostBase.CUT_LENGTH),
                op_price=_f(oe.get("cCostCut"), 0),
                remnant_min_side1=_f(oe.get("cMinDimRegWaste1"), 1000),
                remnant_min_side2=_f(oe.get("cMinDimRegWaste2"), 500),
                remnant_min_area=_f(oe.get("cBusinessWaste"), 0.5),
                remnant_size_incl_trim=_b(oe.get("cTrimWaste"), True),
                min_part_size=_f(oe.get("cMinDimDetail"), 30),
            )
            cut = CSCutParams(
                kerf=_f(tg("swSawthick"), 3),
                kerf_group=kerf_div if kerf_div >= 0 else None,
                trim_length=max(0.0, _f(oe.get("cTrimL"), 2)),
                trim_width=max(0.0, _f(oe.get("cTrimW"), 2)),
                end_offset_bottom=_opt_len(oe.get("cTrimEL")),
                end_offset_right=_opt_len(oe.get("cTrimEW")),
                trim_includes_kerf=_b(tg("swTrimIncludeSaw"), False),
                first_cut=FirstCutDir(min(4, max(0, _i(oe.get("csDirectCut"), 0)))),
                use_grain=_b(oe.get("csTexture"), True),
                complex_strips=_b(tg("swComplexBand"), True),
                max_rotations=max(1, min(6, _i(tg("swMaxturns"), 6))),
                pack_height=_f(tg("swPackageHeight"), 40),
                fill_packet=_fill_pct(oe.get("cFillRep")),
                max_part_types_per_map=_i(oe.get("cMaxPartsOnPattern"), 0),
                prefer_big_pack=_b(oe.get("cPrefLargePacket"), True),
                strip_sort=StripSort(min(3, max(0, _i(tg("swSort"), 0)))),
                in_strip_sort=StripSort(min(3, max(0, _i(tg("swSortInBand"), 3)))),
                min_strip_width=_f(tg("swMinSizeBand"), 0),
                max_strip_width=_f(tg("swMaxSizeBand"), 0),
                max_strip_length=_f(tg("swMaxLengthBand"), 10000) or 10000,
                min_trim_cut=_f(tg("swMinPruning"), 5),
                merge_parts=_b(oe.get("cCombiningParts"), False),
                save_drawings=_b(oe.get("cSaveDrawCut"), False),
                machining_allowance=_f(oe.get("cAllowanceWorkpiece"), 0),
            )
            sheets: list[StockSheet] = []
            if sheet is not None:
                for sp in sheet.findall("part"):
                    if _b(sp.get("waste")):
                        continue            # oldingi kroydan qolgan qoldiq — natija emas, o'tkazib yuboriladi
                    qty = _i(sp.get("count"), 0)
                    if qty <= 0 or _f(sp.get("l")) <= 0 or _f(sp.get("w")) <= 0:
                        continue
                    qty = min(qty, 10000)       # real fayllarda «cheksiz» list soni 100000 ham uchraydi — 10000 (= cheksiz)
                    sheets.append(StockSheet(length=min(_f(sp.get("l")), 20000), width=min(_f(sp.get("w")), 20000), qty=qty,
                                             trim_length=_opt_len(sp.get("cTrimL")),
                                             trim_width=_opt_len(sp.get("cTrimW")),
                                             end_offset_bottom=_opt_len(sp.get("cTrimEL")),
                                             end_offset_right=_opt_len(sp.get("cTrimEW")),
                                             description=(sp.get("description") or "")[:500]))
            # Listlar ustuvorligi: avval soni cheklangan (qoldiq/qirqim) listlar, «cheksiz» (10000) listlar oxirida.
            # Korxonaning 44 ta ko'p-listli kroyi bilan tekshirilgan (42/44 mos, 2 ta istisno — detal sig'maydigan mayda list).
            sheets.sort(key=lambda s: s.qty)
            if not sheets:
                L, W = _f(oe.get("l"), 2750), _f(oe.get("w"), 1830)
                if sheet is not None and not oe.get("l"):
                    L, W = _f(sheet.get("l"), 2750), _f(sheet.get("w"), 1830)
                sheets = [StockSheet(length=L, width=W)]
            desc = oe.get("description") or ""          # operatsiya izohi (eksport yozadi); natija statistikasi bo'lsa — u ustun
            if oe.get("cMaterialCount"):
                fill = _f(oe.get("cFilling"), 0) * 100
                desc = _("imp_desc", n=_i(oe.get("cMaterialCount"))) + (f", F {fill:.2f}%" if fill else "")
            op = Operation(type=OpType.CS, code=(sheet.get("code") or "") if sheet is not None else "",
                           name=(sheet.get("name") or "Material") if sheet is not None else "Material",
                           cs_material=mat, cs_cut=cut, sheets=sheets, description=desc,
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            for pr in oe.findall("part"):
                sp = pr.get("id")
                part = src_parts.get(sp)
                if part is None:
                    continue
                if sp in used_parts:
                    part = part.model_copy(deep=True, update={"id": uuid4().hex[:12]})
                    warnings.append(_("imp_part_dup", id=sp))
                used_parts.add(sp)
                copies.setdefault(sp, []).append(part)
                op.parts.append(part)
            ops_by_src[oid] = op
            ordered.append(op)
            stats["CS"] += 1
        elif t == "CL":                       # (CL) Погонажный раскрой (W11): CLParams, polosalar, detallar (cl_import.py)
            from ..services import cl_import
            op = cl_import.from_project_xml(oe, goods, warnings)
            for pr in oe.findall("part"):
                sp = pr.get("id")
                part = src_parts.get(sp)
                if part is None and sp in neg_src:          # hisoblanmagan (manfiy) detal: CL ga tegishli
                    part, pe_neg = neg_src.pop(sp)
                    src_parts[sp], src_part_el[sp] = part, pe_neg
                    if part.length <= 0:
                        cl_uncomputed += 1
                if part is None:
                    continue                                # polosa (stock) qatori havolasi va h.k.
                if sp in used_parts:
                    part = part.model_copy(deep=True, update={"id": uuid4().hex[:12]})
                    warnings.append(_("imp_part_dup", id=sp))
                part.width = 0                              # CL: detal eni — polosa eni (cl.width)
                used_parts.add(sp)
                copies.setdefault(sp, []).append(part)
                op.parts.append(part)
            ops_by_src[oid] = op
            ordered.append(op)
            stats["CL"] += 1
        elif t == "XNC":
            unk: set[str] = set()
            cmds, size = program_to_commands(oe.get("program") or "", unk)
            if unk:
                unknown_tags[oe.get("code") or oe.get("typeName") or f"#{oid}"] = unk
            side = (oe.get("side") or "true").strip().lower()
            turn = _i(oe.get("turn"), 0)
            rot = turn if turn in (0, 90, 180, 270) else {1: 90, 2: 180, 3: 270}.get(turn, 0)
            x = XNCParams(by_part_size=_b(oe.get("bySizeDetail"), True),
                          length=size[0] if size else 0, width=size[1] if size else 0,
                          thickness=size[2] if size else 16, qty=max(1, _i(oe.get("count"), 1)),
                          face_side=side in ("true", "1"), rotation=rot,
                          mirror_x=_b(oe.get("mirHor")), mirror_y=_b(oe.get("mirVert")),
                          program=cmds, drill_price=_f(oe.get("priceBore")), mill_price_m=_f(oe.get("priceMill")),
                          saw_price_m=_f(oe.get("priceCut")), extra_cost=_f(oe.get("price")))
            op = Operation(type=OpType.XNC, code=oe.get("code") or "", name=oe.get("typeName") or "", xnc=x,
                           description=oe.get("description") or "",
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            ref = oe.find("part")
            if ref is not None:
                xnc_links.append((ref.get("id"), op))
            if oe.get("count") is None:            # soni yozilmagan (eski fayl) — bog'langan detal sonidan olinadi
                xnc_no_count.add(op.id)
            ops_by_src[oid] = op
            ordered.append(op)
            stats["XNC"] += 1
        elif t == "SP":                       # (SP) Обработка поверхности (W12): spCalcMat / spWastePRC / spRestSide / spSizeMode / spCost
            op = sp_ops.from_project_xml(oe, goods)
            op.print = _b(oe.get("printable"), True)
            op.new_page = _b(oe.get("startNewPage"), True)
            sp_links += [(r.get("id"), op) for r in oe.findall("part") if r.get("id") is not None]
            ops_by_src[oid] = op
            ordered.append(op)
            stats["SP"] += 1
        elif t == "O":                        # (O) Комплектация: <material> havolalari → OMaterial, owner → mahsulot
            op = o_ops.from_project_xml(oe, goods, prod_by_src, warnings, product_owner=prod_ops.get(oid))
            op.print = _b(oe.get("printable"), True)
            op.new_page = _b(oe.get("startNewPage"), True)
            ops_by_src[oid] = op
            ordered.append(op)
        elif t == "LB":                       # (LB) Этикетки (W4): parametrlar o'qiladi, eski shablon matni faqat saqlanadi
            from ..services import label_import
            lbp, lb_name = label_import.from_project_xml(oe, warnings)
            op = Operation(type=OpType.LB, code=oe.get("code") or "", name=lb_name, lb=lbp,
                           description=oe.get("description") or "",
                           print=_b(oe.get("printable"), True), new_page=_b(oe.get("startNewPage"), True))
            ops_by_src[oid] = op
            ordered.append(op)
        else:                                 # CN ... — import qilinmaydi (qaysi ekani ogohlantiriladi)
            skipped_ops.append((t or "?", oe.get("typeName") or oe.get("name") or oe.get("code") or f"#{oid}"))

    # kromka / paz havolalari va CNC bog'lanishlari
    for sp, part in src_parts.items():
        pe = src_part_el[sp]
        for side, attr in (("top", "elt"), ("bottom", "elb"), ("left", "ell"), ("right", "elr")):
            ref = pe.get(attr)
            if ref and ref in edge_ops:
                for target in copies.get(sp, [part]):
                    setattr(target, f"edge_{side}", EdgeRef(op_id=edge_ops[ref].id))
            elif ref:
                warnings.append(_("imp_edge_missing", id=sp, ref=ref))
        for side, attr in (("top", "grt"), ("bottom", "grb"), ("left", "grl"), ("right", "grr")):
            ref = pe.get(attr)
            if ref and ref in groove_ops:
                face = pe.get(attr + "s")                  # tomon: true = lits (old), false = orqa
                for target in copies.get(sp, [part]):
                    setattr(target, f"groove_{side}",
                            GrooveSide(op_id=groove_ops[ref].id, back_side=face is not None and not _b(face)))
            elif ref:
                warnings.append(_("imp_groove_missing", id=sp, ref=ref))
    for sp, op in xnc_links:
        targets = copies.get(sp, [])
        if targets:
            op.xnc_part_id = targets[0].id
            if op.id in xnc_no_count and op.xnc is not None:
                op.xnc.qty = max(1, targets[0].qty)
            for pt in targets:            # detal bir nechta CS da bo'lsa — har nusxasiga
                if op.id not in pt.xnc_op_ids:
                    pt.xnc_op_ids.append(op.id)

    sp_ops.link_parts(sp_links, copies, warnings)         # (SP) lits / orqa tomon (fayl ko'rsatmaydi ❓ — lits, ikkinchisi orqa)

    # detal ID (uid): fayldagi `<part id="N">` raqami (onlayn tizimdagi «ID» ustuni; detal qaysi operatsiyada bo'lsa ham
    # o'sha raqam, nusxalari ham). Yaroqsiz id li detallar va bitta operatsiya ichida takrorlangan raqamlar — fayldagi eng
    # katta id dan keyingi bo'sh raqamlar (operatsiyalar tartibida). Operatsiya ichida uid noyob (muharrir shunga tayanadi).
    next_free = max_file_id
    for o in ordered:
        seen: set[int] = set()
        for pt in o.parts:
            if pt.uid <= 0 or pt.uid in seen:
                next_free += 1
                pt.uid = next_free
            seen.add(pt.uid)
    missing = [sp for sp in src_parts if sp not in used_parts]
    if missing:
        warnings.append(_("imp_parts_skipped", n=len(missing)))
    if neg_src:                           # CL operatsiyasiga ulanmagan manfiy o'lchamli detallar — import qilinmaydi
        warnings.append(_("imp_neg_parts", n=len(neg_src)))
    if cl_uncomputed:                     # CL: hisoblanmagan detallar uzunlik 0 bilan import qilindi (kroyga kirmaydi)
        warnings.append(_("imp_cl_uncomputed", n=cl_uncomputed))
    for t, n in opt_skipped.items():      # import parametrlari bo'yicha o'tkazib yuborilganlar — turi bo'yicha bitta qator
        warnings.append(_("imp_op_opt_skipped", t=t, n=n))
    for t, nm in skipped_ops[:10]:        # qaysi operatsiyalar o'tkazib yuborilgani (tur + nom) aytiladi
        warnings.append(_("imp_op_skipped", t=t, name=nm))
    if len(skipped_ops) > 10:
        warnings.append(_("imp_ops_skipped", n=len(skipped_ops) - 10))
    for code, tags in unknown_tags.items():
        for tg in sorted(tags):
            warnings.append(_("imp_xnc_tag", code=code, tag=tg))
    p.operations = ordered
    return p, warnings
