"""Nanxing SyntecCad — `.scx` (XML `Root/Project/Panels/Panel`; docs/mebelix/postprocessors/nanxing-synteccad.md).

Format — stanok (Nanxing MH2026_Drill 3.1.2.4) qabul qiladigan ko'rinish. Manbalar (2026-10-22):
  • korxona namunasi `uzgarishlar/0004 Test.zip` (lokal tizim 2023-05-17 versiyasi) — 8/8 bayt-ma-bayt;
  • korxona MES dasturidagi generator qoidalari (`MebeliX-Mes-System`, `services/giblab/scx.py`, `docs/10` §7.2 — 87 loyiha,
    5286 eksport fayli korpusidan): orqa tomon, amallar tartibi, chet bo'ylab freza, qo'shqavat detal, ko'zgu.
Avvalgi (2021 onlayn) ko'rinish — kesilgan kontur + ramka va korreksiyali freza — stanokda «Mill path node not on panel
outline» xatosini berdi.

Bitta DETAL = bitta `<old tomon XNC kodi>.scx`: orqa tomon dasturi (`side="false"`) alohida fayl EMAS — uning yuza amallari
`Face="6"` bilan shu faylga qo'shiladi (koordinata old tomon bilan bir xil: x, W − y; qirra teshigi Z = qalinlik − z).
Qatorlar: XML sarlavhasidan keyin `\\n`, qolgan har element alohida qatorda `\\r\\n`. Koordinata: X = x, Y = W − y (boshi
pastki-chap burchakda), qirra teshigi Z — pastki yuzadan. Har dasturda tartib: qirra teshiklari → yuza teshiklari → pazlar →
frezalar (har guruh ichida dastur tartibi); `ID` 1000 dan ketma-ket, `IsGenCode="2"`. Atributlar alifbo tartibida.
  • `Panel@ID` — mahsulot kodi + «_» + detal kodi (`000401_01_004`); bo'lmasa XNC kodi. `Name` — lotin yozuvida: kirill
    harflari transliteratsiya, «–» / «—» → «-».
  • `<Outline>` — doim detal to'rtburchagi: (L,0) (L,W) (0,W) (0,0).
  • `<EdgeGroup>` — kromkali tomonlar (l 4, r 3, t 1, b 2 tartibida), kromka yo'q bo'lsa blok yozilmaydi.
  • Freza — asbob MARKAZI yo'li (`_cnc2.offset_path`: korreksiya tomoniga d/2), `ToolOffset="中"`; korreksiyasiz — xom yo'l
    (中); butun kontur bitta chet bo'ylab va c=2 — xom yo'l, `右`. Yoy `Angle` — burilish burchagi (XNC dir="true" → musbat).
  • Qo'shqavat detal (dz ≈ 2 × list qalinligi yoki 32): qalinlik va qirra Z ikki baravar, yuza teshigi chuqurligi bir qatlamga
    kam, freza chuqurligi eksport qalinligidan oshmaydi.
  • Dastur ko'zgusi (`mirHor` / `mirVert`) geometriyaga qo'llanadi.
"""
from __future__ import annotations

from . import DrillJob, Files, drill_job, num_hu, register, set_batch
from . import _cnc as C
from ._cnc2 import offset_path, sweep, xml_attr

CAD = "MebeliX Kroy"
FACE = {"L": "4", "R": "3", "T": "1", "B": "2"}
BORDER = 0.05                   # mm: kontur chetda yotadi

_TR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяўқғҳ",
               ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
                "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "o'", "q", "g'", "h"]))
_DASH = {"–": "-", "—": "-", "‒": "-", "−": "-"}
_TB = {"T": "B", "B": "T"}


def n(v: float) -> str:
    return num_hu(v, 3)


def latin(s: str) -> str:
    """Nom → lotin yozuvi (kirill transliteratsiya, uzun chiziqlar «-»); boshqa belgilar o'zgarmaydi."""
    out = []
    for ch in s or "":
        lo = ch.lower()
        if lo in _TR:
            t = _TR[lo]
            out.append(t.capitalize() if ch != lo and t else t)
        else:
            out.append(_DASH.get(ch, ch))
    return "".join(out)


def panel_id(job: DrillJob) -> str:
    """Mahsulot kodi + «_» + detal kodi (namunada `000401_01_004`); birortasi bo'lmasa — XNC kodi."""
    p = C.part_of(job)
    if p is not None and p.code and p.product_id:
        pr = next((x for x in job.project.products if x.id == p.product_id), None)
        if pr is not None and pr.code:
            return f"{pr.code}_{p.code}"
    return job.code


def part_jobs(job: DrillJob) -> list[DrillJob]:
    """Detalning barcha XNC dasturlari: avval old tomon, keyin orqa (har guruhda kod bo'yicha). Detalga bog'lanmagan — o'zi."""
    p = C.part_of(job)
    if p is None:
        return [job]
    jobs = [job if o.id == job.op.id else drill_job(job.project, o)
            for o in job.project.operations if o.id in p.xnc_op_ids and o.xnc is not None]
    return sorted(jobs or [job], key=lambda j: (not j.face, j.code))


def _mirror_y(lst: list[dict], dy: float) -> list[dict]:
    res = []
    for o in lst:
        o = dict(o)
        t = o["t"]
        if t == "drill":
            if o["side"] in _TB:
                o["side"] = _TB[o["side"]]
            else:
                o["y"] = dy - o["y"]
        elif t == "groove":
            o["y1"], o["y2"] = dy - o["y1"], dy - o["y2"]
            if o["c"] in (1, 2):
                o["c"] = 3 - o["c"]
        elif t == "ms":
            o["y"] = dy - o["y"]
            if o["c"] in (1, 2):
                o["c"] = 3 - o["c"]
        elif t == "ml":
            o["y"] = dy - o["y"]
        elif t == "mac":
            o["y"], o["cy"] = dy - o["y"], dy - o["cy"]
            o["ccw"] = not o["ccw"]
        res.append(o)
    return res


def job_ops(j: DrillJob) -> list[dict]:
    """Dastur amallari o'z koordinatasida (orqa tomon ag'darilmaydi), ko'zgu qo'llangan."""
    lst = C.ops(j)
    x = j.op.xnc
    if x is not None and x.mirror_x:
        lst = C.mirror(lst, j.dx)
    if x is not None and x.mirror_y:
        lst = _mirror_y(lst, j.dy)
    return lst


def plate_thickness(job: DrillJob) -> float:
    """Detal joylashgan kroy (CS) materialining qalinligi (qo'shqavat detalni aniqlash uchun); topilmasa 0."""
    from ...models import OpType
    for o in job.project.operations:
        if o.type == OpType.CS and o.cs_material is not None and any(job.op.id in p.xnc_op_ids for p in o.parts):
            return float(o.cs_material.thickness or 0)
    return 0.0


def _edges(job: DrillJob) -> list[str]:
    th = {s[0]: v["thickness"] for s, v in C.edges(job)}
    res = []
    for k, face in (("l", "4"), ("r", "3"), ("t", "1"), ("b", "2")):
        if k in th:
            t = float(th[k] or 0.0) or 1.0
            res.append(f'<Edge CentralAngle="0" Face="{face}" Pre_Milling="1.0" Thickness="{t!r}" X="0" Y="0"/>')
    return res


def _on_border(cont: list[dict], L: float, W: float) -> bool:
    pts = [(o["x"], o["y"]) for o in cont]
    return (all(abs(x) < BORDER for x, _ in pts) or all(abs(x - L) < BORDER for x, _ in pts)
            or all(abs(y) < BORDER for _, y in pts) or all(abs(y - W) < BORDER for _, y in pts))


def _pocket_side(cont: list[dict]) -> int:
    """Cho'ntak (c=3) korreksiyasi → ichki tomon (1 / 2); ochiq kontur — markaz (0). XNC koordinatasida (Y pastga) yuzasi
    musbat konturda ichki tomon — harakatga nisbatan `c=1` tomoni."""
    pts = [(o["x"], o["y"]) for o in cont]
    if len(pts) < 3 or abs(pts[0][0] - pts[-1][0]) > BORDER or abs(pts[0][1] - pts[-1][1]) > BORDER:
        return 0
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:]))
    return 1 if a > 0 else 2


def _close(segs: list[list], cont: list[dict]) -> list[list]:
    """Yopiq kontur siljitilganda boshi va oxiri (ikkalasi chiziq bo'lsa) kesishish nuqtasida tutashadi; nol uzunlikli
    segmentlar olib tashlanadi (tor cho'ntakda ichki yo'l chiziqqa aylanadi)."""
    p0, p1 = (cont[0]["x"], cont[0]["y"]), (cont[-1]["x"], cont[-1]["y"])
    if len(segs) > 1 and abs(p0[0] - p1[0]) <= BORDER and abs(p0[1] - p1[1]) <= BORDER \
            and segs[0][0] == "L" and segs[-1][0] == "L":
        (x1, y1), (x2, y2) = segs[-1][1], segs[-1][2]
        (x3, y3), (x4, y4) = segs[0][1], segs[0][2]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) > 1e-12:
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            ip = (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
            segs[-1][2] = ip
            segs[0][1] = ip
    out = [s for s in segs if s[0] != "L" or abs(s[1][0] - s[2][0]) > 1e-3 or abs(s[1][1] - s[2][1]) > 1e-3]
    return out or segs[:1]


def program(job: DrillJob, jobs: list[DrillJob] | None = None) -> str:
    jobs = jobs or [job]
    front = jobs[0]
    L, W, T = front.dx, front.dy, front.dz
    pt = plate_thickness(front)
    layer = 0.0
    if (pt and abs(T - 2 * pt) < 0.1) or abs(T - 32.0) < 0.1:      # qo'shqavat detal: eksport — bitta list qatlami
        layer = T / 2
        T = T / 2
    rows = [f'<Root Cad="{CAD}" version="2.0">', "<Project>", "<Panels>",
            f'<Panel ID="{xml_attr(panel_id(front))}" IsProduce="true" Length="{n(L)}" MachiningPoint="1" '
            f'Name="{xml_attr(latin(front.name))}" Thickness="{n(T)}" Width="{n(W)}">',
            "<Outline>", f'<Point X="{n(L)}" Y="0"/>', f'<Point X="{n(L)}" Y="{n(W)}"/>', f'<Point X="0" Y="{n(W)}"/>',
            '<Point X="0" Y="0"/>', "</Outline>"]
    edges = _edges(front)
    if edges:
        rows += ["<EdgeGroup>", *edges, "</EdgeGroup>"]
    rows.append("<Machines>")
    mid = 1000
    for j in jobs:
        sf = "5" if j.face else "6"
        lst = job_ops(j)
        conts = {id(c[0]): c for c in C.contours(lst)}
        for o in (o for o in lst if o["t"] == "drill" and o["side"] != "F"):
            sd = o["side"]
            if sd in ("L", "R"):
                X, Y = (0.0 if sd == "L" else L), W - o["y"]
            else:
                X, Y = o["x"], (W if sd == "T" else 0.0)
            z = o["z"] * (0.5 if layer else 1.0)
            if not j.face:
                z = T - z                                           # orqa dasturda Z orqa yuzadan
            rows.append(f'<Machining Depth="{n(o["dp"])}" Diameter="{n(o["d"])}" Face="{FACE[sd]}" ID="{mid}" IsGenCode="2" '
                        f'Type="1" X="{n(X)}" Y="{n(Y)}" Z="{n(z)}"/>')
            mid += 1
        for o in (o for o in lst if o["t"] == "drill" and o["side"] == "F"):
            dp = o["dp"] - layer if layer and o["dp"] > layer else o["dp"]
            rows.append(f'<Machining Depth="{n(dp)}" Diameter="{n(o["d"])}" Face="{sf}" ID="{mid}" IsGenCode="2" Type="2" '
                        f'X="{n(o["x"])}" Y="{n(W - o["y"])}"/>')
            mid += 1
        for o in (o for o in lst if o["t"] == "groove"):
            rows.append(f'<Machining Depth="{n(o["dp"])}" EndX="{n(o["x2"])}" EndY="{n(W - o["y2"])}" EndZ="{n(T)}" Face="{sf}" '
                        f'ID="{mid}" IsGenCode="2" ToolOffset="中" Type="4" Width="{n(o["w"])}" '
                        f'X="{n(o["x1"])}" Y="{n(W - o["y1"])}" Z="{n(T)}"/>')
            mid += 1
        for o in (o for o in lst if o["t"] == "ms" and id(o) in conts and len(conts[id(o)]) > 1):
            cont = conts[id(o)]
            off = "中"
            if o["c"] == 2 and _on_border(cont, L, W):              # chet bo'ylab tirim: xom yo'l, tomonni stanok oladi
                cont = [dict(cont[0], c=0)] + cont[1:]
                off = "右"
            elif o["c"] == 3:                                       # cho'ntak: yopiq kontur ichiga d/2 (o'yiq chegarasi aniq)
                cont = [dict(cont[0], c=_pocket_side(cont))] + cont[1:]
            segs = offset_path(cont)
            if o["c"] == 3:
                segs = _close(segs, cont)
            x0, y0 = segs[0][1]
            ls = []
            for i, sg in enumerate(segs):
                q = sg[2]
                if sg[0] == "L":
                    ang = "0"
                else:
                    c = sg[3]
                    ang = n(sweep(sg[1], dict(x=q[0], y=q[1], cx=c[0], cy=c[1], ccw=sg[5])))
                ls.append(f'<Line Angle="{ang}" EndX="{n(q[0])}" EndY="{n(W - q[1])}" LineID="{i}"/>')
            dp = min(o["dp"], T) if layer else o["dp"]
            rows.append(f'<Machining Closed="0" Depth="{n(dp)}" Diameter="{n(o["d"])}" Face="{sf}" ID="{mid}" IsGenCode="2" '
                        f'Pocket="0" ToolOffset="{off}" Type="3" X="{n(x0)}" Y="{n(W - y0)}">')
            rows += ["<Lines>", *ls, "</Lines>", "</Machining>"]
            mid += 1
    rows += ["</Machines>", "</Panel>", "</Panels>", "</Project>", "</Root>"]
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + "".join(r + "\r\n" for r in rows)


@register("nanxing_syntec", "Nanxing SyntecCad (.scx)", "cnc", "scx",
          note="Stanok (Nanxing MH2026_Drill) qabul qiladigan ko'rinish — korxona namunasi va MES korpus qoidalari (2026-10-22): "
               "bitta detal = bitta fayl (orqa tomon Face 6 bilan shu faylda), detal to'rtburchagi, kromkalar EdgeGroup da, "
               "freza asbob MARKAZI yo'li (中), amallar ID bilan, IsGenCode=2. Root@Cad=\"MebeliX Kroy\".")
def nanxing_syntec(job: DrillJob) -> Files:
    jobs = part_jobs(job)
    if jobs[0].op.id != job.op.id:
        return []                                  # detalning boshqa (asosiy) dasturi faylida
    return [(f"{job.code}.scx", program(job, jobs).encode("utf-8"))]


@set_batch("nanxing_syntec")
def nanxing_batch(jobs: list[DrillJob], _project=None) -> Files:
    """Tanlangan dasturlar: har detalga bitta fayl (orqa tomon dasturi tanlansa ham — detalning asosiy fayli)."""
    out: Files = []
    seen: set[str] = set()
    for j in jobs:
        group = part_jobs(j)
        head = group[0]
        if head.op.id in seen:
            continue
        seen.add(head.op.id)
        out.append((f"{head.code}.scx", program(head, group).encode("utf-8")))
    return out
