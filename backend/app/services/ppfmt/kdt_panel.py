"""KDT prisadka — `.xml` (`KDTPanelFormat`): korxonada stanokda HOZIR ishlayotgan versiya (2026-10-26, `post/prisadka` —
9 buyurtma, 680 fayl bilan solishtirildi). Eski `AndersonXMLdata` — `kdt_trepan.py`.

Qoidalar (real fayllardan):
  * bitta DETAL = bitta fayl: yuz tomon dasturi + orqa tomon dasturining ko'r teshiklari («Back Vertical Hole», TypeNo 8;
    teshib o'tuvchilari — asosiy tomonda, 1). Orqa dasturda freza / paz bo'lsa (yuzda yo'q) — detal AG'DARILADI: orqa
    dastur asosiy (1, 3, 7), yuz tomon ko'r teshiklari — 8, hamma X — uzunlik − x;
    nomi — XNC kodi, kod bo'sh bo'lsa `<ishlov nomi>_null_1`; takror nom — `nom (1)`, `nom (2)` (arra etiketkasidagi QR ham
    shu nom — stanok etiketkani skanerlab dasturni ochadi);
  * koordinatalar: X — dasturdagidek, Y — pastdan (en − y; dastur boshi chap-yuqorida). Orqa teshiklar — orqa dasturning
    X i o'zgarishsiz, Y pastdan;
  * `PanelOutline` — to'rt tomon (past, o'ng, yuqori, chap): kromka bo'lsa `Banding` 1.5, «(belgi) qalinlikmm», kromka rangi;
    bo'lmasa 0.3 va «-»;
  * yuza amallari (teshik, orqa teshik, freza yo'li «Path», paz «Groove») — koordinata boshidan har safar eng yaqin keyingisi
    (asbob yo'li qisqa); oxirida qirra teshiklari: chap (Y↑), o'ng (Y↓), past (X↑), yuqori (X↓) (Quadrant: chap 1, o'ng 2, yuqori 3, past 4);
  * freza: `Path` — Point / Line / Arc (Radius, Direction: soat strelkasiga qarshi → 0), Correction 1 ↔ 2 (Y teskari), Close.
Har element alohida qatorda, CRLF; sonlar 4 kasrgacha (yoy radiusi 5)."""
from __future__ import annotations

import math

from . import DrillJob, Files, drill_job, register, set_batch
from . import _cnc as C
from ._cnc2 import num, xml_text

HOLE_TAIL = ["<HoleNo>1</HoleNo>", "<IntervalX>0</IntervalX>", "<IntervalY>0</IntervalY>", "<IntervalZ>0</IntervalZ>",
             "<Mirror>0</Mirror>", "</CAD>"]
CORR = {0: "0", 1: "2", 2: "1"}         # Y teskari — korreksiya tomoni almashadi
QUAD = {"L": "1", "R": "2", "T": "3", "B": "4"}   # dastur T (y=0) — pastdan o'lchanganda yuqori qirra


def n(v: float) -> str:
    return num(v, 4)


def file_name(job: DrillJob) -> str:
    """Fayl va etiketka QR nomi: XNC kodi; kod bo'sh bo'lsa `<ishlov nomi>_null_1`."""
    code = (job.op.code or "").strip()
    return code or f"{job.op.name or 'xnc'}_null_1"


def _rgb(hex_color: str) -> str:
    h = (hex_color or "#000000").lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        r = g = b = 0
    return f"rgb({r},{g},{b})"


def _outline(job: DrillJob) -> list[str]:
    from ...models import OpType
    L, W = job.dx, job.dy
    part = C.part_of(job)
    els = {o.id: o for o in job.project.operations if o.type == OpType.EL and o.el is not None}
    out = ["<PanelOutline>"]
    # (x, y) — tomon boshi; tomonlar: past (dasturdagi y=W), o'ng (x=L), yuqori (y=0), chap (x=0)
    for (x, y), side in (((0, 0), "bottom"), ((L, 0), "right"), ((L, W), "top"), ((0, W), "left")):
        ref = getattr(part, f"edge_{side}", None) if part is not None else None
        el = els.get(ref.op_id) if ref is not None and ref.op_id else None
        out += ["<Vertex>", f"<X1>{n(x)}</X1>", f"<Y1>{n(y)}</Y1>", "<Bulge>0</Bulge>"]
        if el is not None:
            col = _rgb(el.el.color)
            out += ["<Banding>1.5</Banding>", f"<Description>({xml_text(el.el.symbol or '?')}) {num(el.el.thickness, 4)}mm</Description>",
                    f"<BandingColor>{col}</BandingColor>", f"<DescriptionColor>{col}</DescriptionColor>"]
        else:
            out += ["<Banding>0.3</Banding>", "<Description>-</Description>",
                    "<DescriptionColor>rgb(200, 200, 200)</DescriptionColor>"]
        out.append("</Vertex>")
    out.append("</PanelOutline>")
    return out


def _hole(tn: str, name: str, p, o) -> tuple:
    return (p, p, ["<CAD>", f"<TypeNo>{tn}</TypeNo>", f"<TypeName>{name}</TypeName>", "<PlaneID>0</PlaneID>",
                   "<Quadrant>1</Quadrant>", f"<X1>{n(p[0])}</X1>", f"<Y1>{n(p[1])}</Y1>",
                   f"<Depth>{n(o['dp'])}</Depth>", f"<Diameter>{n(o['d'])}</Diameter>", *HOLE_TAIL])


def _machining(job: DrillJob) -> bool:
    """Dasturda freza yoki paz bormi (ular faqat yuqoridan bajariladi)."""
    return any(o["t"] in ("groove", "ms") for o in C.ops(job))


def _items(main: DrillJob, others: list[DrillJob], flip: bool) -> tuple[list[tuple], list[tuple]]:
    """Yuza elementlari va qirra teshiklari [(boshlanish, tugash, qatorlar)].

    `main` — yuqoridan ishlanadigan dastur (1, 3, 7 va qirra teshiklari), `others` — teskari tomon dasturi: ko'r teshiklari
    «Back Vertical Hole» (8), teshib o'tuvchilari (chuqurlik ≥ qalinlik) — asosiy tomonda (1). `flip` — detal ag'darilgan
    (orqa tomon dasturida freza / paz bor): hamma X — `uzunlik − x` (real fayllardagidek)."""
    L, W, T = main.dx, main.dy, main.dz

    def fx(x):
        return L - x if flip else x

    def fy(y):
        return W - y
    items: list[tuple] = []
    edge: list[tuple] = []
    path: list[str] | None = None
    start = cur = None
    width = corr = dp = None

    def close_path():
        nonlocal path, start, cur
        if path is not None:
            closed = "1" if start is not None and cur is not None and math.dist(start, cur) < 1e-6 else "0"
            body = ["<CAD>", "<TypeNo>7</TypeNo>", "<TypeName>Path</TypeName>", f"<Width>{n(width)}</Width>",
                    f"<Correction>{corr}</Correction>", f"<Depth>{n(dp)}</Depth>", f"<Close>{closed}</Close>",
                    "<Vertexes>"] + path + ["</Vertexes>", "</CAD>"]
            items.append((start, cur, body))
        path = None

    def ccorr(c):
        v = CORR.get(c, "0")
        return {"1": "2", "2": "1"}.get(v, v) if flip else v
    for o in C.ops(main):
        t = o["t"]
        if t == "drill":
            close_path()
            if o["side"] == "F":
                items.append(_hole("1", "Vertical Hole", (fx(o["x"]), fy(o["y"])), o))
            else:
                s0 = o["side"]
                rows = ["<CAD>", "<TypeNo>2</TypeNo>", "<TypeName>Horizontal Hole</TypeName>", "<PlaneID>2</PlaneID>"]
                if s0 in ("L", "R"):
                    x = fx(0 if s0 == "L" else L)
                    p = (x, fy(o["y"]))
                    rows += [f"<X1>{n(p[0])}</X1>", f"<Quadrant>{'1' if x == 0 else '2'}</Quadrant>", f"<Y1>{n(p[1])}</Y1>"]
                else:
                    p = (fx(o["x"]), W if s0 == "T" else 0)
                    rows += [f"<Quadrant>{QUAD[s0]}</Quadrant>", f"<X1>{n(p[0])}</X1>", f"<Y1>{n(p[1])}</Y1>"]
                rows += [f"<Z1>{n(T - o['z'])}</Z1>", f"<Depth>{n(o['dp'])}</Depth>", f"<Diameter>{n(o['d'])}</Diameter>", *HOLE_TAIL]
                edge.append((p, p, rows))
        elif t == "groove":
            close_path()
            a, b = (fx(o["x1"]), fy(o["y1"])), (fx(o["x2"]), fy(o["y2"]))
            items.append((a, b, ["<CAD>", "<TypeNo>3</TypeNo>", "<TypeName>Groove</TypeName>", f"<BeginX>{n(a[0])}</BeginX>",
                                 f"<BeginY>{n(a[1])}</BeginY>", f"<EndX>{n(b[0])}</EndX>", f"<EndY>{n(b[1])}</EndY>",
                                 f"<Width>{n(o['w'])}</Width>", f"<Correction>{ccorr(o['c'])}</Correction>",
                                 "<UseSaw>1</UseSaw>", f"<Depth>{n(o['dp'])}</Depth>", "</CAD>"]))
        elif t == "ms":
            close_path()
            start = cur = (fx(o["x"]), fy(o["y"]))
            width, corr, dp = o["d"], ccorr(o["c"]), o["dp"]
            path = ["<Point>", f"<X1>{n(cur[0])}</X1>", f"<Y1>{n(cur[1])}</Y1>", "</Point>"]
        elif t == "ml" and path is not None:
            cur = (fx(o["x"]), fy(o["y"]))
            path += ["<Line>", f"<X1>{n(cur[0])}</X1>", f"<Y1>{n(cur[1])}</Y1>", "</Line>"]
        elif t == "mac" and path is not None:
            r = math.hypot(o["x"] - o["cx"], o["y"] - o["cy"])
            cur = (fx(o["x"]), fy(o["y"]))
            ccw = o["ccw"] != flip                          # X ko'zgusi yoy yo'nalishini almashtiradi
            path += ["<Arc>", f"<X1>{n(cur[0])}</X1>", f"<Y1>{n(cur[1])}</Y1>", f"<Radius>{num(r, 5)}</Radius>",
                     f"<Direction>{'0' if ccw else '1'}</Direction>", "</Arc>"]
    close_path()
    # teskari tomon: ko'r teshiklar — 8, teshib o'tuvchilar — asosiy tomonda (1); X — shu dasturning o'z X i (ag'darilganda ko'zgu)
    for oj in others:
        for o in C.ops(oj):
            if o["t"] == "drill" and o["side"] == "F":
                through = o["dp"] >= oj.dz - 1e-6
                items.append(_hole("1", "Vertical Hole", (fx(o["x"]), fy(o["y"])), o) if through else
                             _hole("8", "Back Vertical Hole", (fx(o["x"]), fy(o["y"])), o))
    return items, edge


ROUTE_FIRST = "origin"       # birinchi element: "program" — dasturdagi birinchisi, "origin" — boshga eng yaqini


def _route(items: list[tuple], groove_keep: bool = True) -> list[tuple]:
    """Asbob yo'li: birinchi — dasturdagi birinchi element, keyin har safar joriy nuqtaga eng yaqini (teng masofada —
    dastur tartibi). Paz bajarilgach joriy nuqta — paz boshi (real fayllardagidek)."""
    left = list(items)
    pos = (0.0, 0.0)
    out = []
    first = True
    while left:
        if first and ROUTE_FIRST == "program":
            i = 0
        else:
            i = min(range(len(left)), key=lambda k: (math.dist(pos, left[k][0]), k))
        first = False
        it = left.pop(i)
        out.append(it)
        pos = it[0] if (groove_keep and it[2][1] == "<TypeNo>3</TypeNo>") else it[1]
    return out


def _edge_order(edge: list[tuple]) -> list[tuple]:
    """Qirra teshiklari: chap qirra (Y o'sishi), o'ng (Y kamayishi), past (X o'sishi), yuqori (X kamayishi) — real fayllardagi
    tartib (barqaror: teng koordinatada dastur tartibi)."""
    def key(it):
        (x, y), rows = it[0], it[2]
        q = next(r for r in rows if r.startswith("<Quadrant>"))[10:11]
        return {"1": (0, y), "2": (1, -y), "4": (2, x), "3": (3, -x)}[q]
    return sorted(edge, key=key)


def program(job: DrillJob, back: list[DrillJob] | None = None) -> str:
    L, W, T = job.dx, job.dy, job.dz
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<KDTPanelFormat>", "<PANEL>", f"<PanelLength>{n(L)}</PanelLength>",
           f"<PanelWidth>{n(W)}</PanelWidth>", f"<PanelThickness>{n(T)}</PanelThickness>",
           f"<PanelName>{xml_text(job.name)}</PanelName>", *_outline(job), "</PANEL>"]
    back = back or []
    # orqa tomon dasturida freza / paz bo'lsa (yuz tomonda yo'q) — detal ag'dariladi: orqa dastur yuqoridan ishlanadi
    flip = bool(back) and any(_machining(b) for b in back) and not _machining(job)
    items, edge = (_items(back[0], [job] + back[1:], True) if flip else _items(job, back, False))
    for _s, _e, rows in _route(items):
        out += rows
    for _s, _e, rows in _edge_order(edge):
        out += rows
    out.append("</KDTPanelFormat>")
    return "\r\n".join(out) + "\r\n"


def _part_jobs(job: DrillJob) -> list[DrillJob]:
    p = C.part_of(job)
    if p is None:
        return [job]
    jobs = [job if o.id == job.op.id else drill_job(job.project, o)
            for o in job.project.operations if o.id in p.xnc_op_ids and o.xnc is not None]
    return jobs or [job]


@register("kdt_panel", "KDT (.xml KDTPanelFormat — joriy versiya)", "cnc", "xml",
          note="Stanokda hozir ishlayotgan format (korxonaning 9 buyurtmasi, 680 fayl bilan solishtirildi). Bitta detal — bitta "
               "fayl (orqa tomon teshiklari TypeNo 8 bilan shu faylda), nomi — XNC kodi yoki `<nom>_null_1` (arra etiketkasidagi QR "
               "bilan bir xil). Y pastdan, kromkali kontur, asbob yo'li eng yaqin nuqta tartibida, qirra teshiklari oxirida. "
               "Orqa tomondagi freza / paz — namunada yo'q (yozilmaydi).")
def kdt_panel(job: DrillJob) -> Files:
    group = _part_jobs(job)
    faces = [j for j in group if j.face]
    head = faces[0] if faces else job
    back = [j for j in group if not j.face] if faces else []
    return [(f"{file_name(head)}.xml", program(head, back).encode("utf-8"))]


@set_batch("kdt_panel")
def kdt_panel_batch(jobs: list[DrillJob], project=None) -> Files:
    """Har detalga bitta fayl (orqa dastur yuz tomon fayliga qo'shiladi); bir xil nomlar — `nom (1)`, `nom (2)`."""
    files: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for j in jobs:
        group = _part_jobs(j)
        faces = [g for g in group if g.face]
        head = faces[0] if faces else j
        if head.op.id in seen or (not j.face and faces and any(f.op.id in {x.op.id for x in jobs} for f in faces)
                                   and head.op.id != j.op.id and head.op.id in seen):
            continue
        if not j.face and faces:
            if any(f.op.id == x.op.id for f in faces for x in jobs):
                continue                                   # yuz tomon dasturi ham tanlangan — u bilan birga yoziladi
        seen.add(head.op.id)
        back = [g for g in group if not g.face] if faces else []
        files.append((file_name(head), program(head, back).encode("utf-8")))
    names = C.dup_names([nm for nm, _ in files])
    return [(f"{nm}.xml", d) for nm, (_o, d) in zip(names, files)]
