"""Biesse Selco OSI — bitta XML (UTF-8, bitta qatorda, atributlar ASCII tartibida).

Tavsif: docs/mebelix/postprocessors/biesse-selco-osi.md. Tuzilma: Order → WorkList → Part × P, Job × J (TechnoParam × 16,
Board, Program/Cut), Piece × Q (Pid, Sid). Kesish dasturi NC300 bilan bir xil (kodlar 1/4, 2/5, Z1…), lekin `Rep`
faqat bir xil detal(lar) bo'lsa yig'iladi.

`Part` atributlarining bir qismi BIZNING «Данные для этикеток» jadvalidan (pp_machine_schema `_OSI_ROWS`, tartib bo'yicha):
  0 id, 1 qMin, 2 QMax, 3 Prio, 4 L, 5 W, 6 Grain, 7 Finish, 8 EvDate, 9 PartNo (= Code), 10 Comment, 11 Job, 12 Name,
  13 IDesc, 14 IIDesc. Bo'sh qiymat — atribut yozilmaydi. Qolganlari (material, kromka, XNC kodlari) — format qoidasi.

Yozilmaydi: boshqa dasturning har detal uchun etiketka blobi (namunadagi alohida element) va qoldiq etiketkalari.
**Ochiq:** oxirgi `Cut` dagi nazorat summasi (`Chk`) algoritmi noma'lum — atribut yozilmaydi; stanok faylni rad etishi mumkin.
"""
from __future__ import annotations

import uuid
from typing import Optional

from . import SawJob, register
from . import _saw_bsf as B
from .biesse_nc300 import code, trims

KEY = "biesse_osi"
PART_ATTRS = ("id", "qMin", "QMax", "Prio", "L", "W", "Grain", "Finish", "EvDate", "PartNo", "Comment", "Job", "Name",
              "IDesc", "IIDesc")
SIDES = (("Up", "top"), ("Lo", "bottom"), ("L", "left"), ("R", "right"))


def el(tag: str, attrs: dict, children: Optional[list[str]] = None) -> str:
    a = "".join(f' {k}="{B.esc_xml(v)}"' for k, v in sorted(attrs.items()))
    if not children:
        return f"<{tag}{a}/>"
    return f"<{tag}{a}>" + "".join(children) + f"</{tag}>"


def chk(cuts: list[B.Cut]) -> Optional[int]:
    """Oxirgi kesimning nazorat summasi. Algoritm aniqlanmagan (14 namunadagi 80 ta qiymat bo'yicha CRC/Adler/Fletcher,
    bayt yig'indilari, kesim qiymatlari yig'indilari sinaldi — mos kelmadi) → None (atribut yozilmaydi)."""
    return None


def part_attrs(job: SawJob, P: B.Parts, L: B.Labels, u: int) -> dict:
    sp = P.saw[u]
    a: dict[str, str] = {}
    for i, k in enumerate(PART_ATTRS):
        v = B.text(L.by_index(u, i, ""))
        if v != "":
            a[k] = v
    if "PartNo" in a:
        a["Code"] = a["PartNo"]
    pr = P.product(u)
    if pr is not None and pr.name:
        a["Desc1"] = pr.name
    a["Material"] = job.material_name
    for s, side in SIDES:
        e = P.edge(u, side)
        a[f"ThkEdge{s}"] = B.n1(e.get("thickness") or 0) if e else "0.0"
        if e:
            if e.get("symbol"):
                a[f"TypEdge{s}"] = e["symbol"]
            if e.get("name"):
                a[f"MatEdge{s}"] = e["name"]
    if sp.xnc_face:
        a["DrillBarCode2"] = sp.xnc_face
    if sp.xnc_back:
        a["DrillBarCode3"] = sp.xnc_back
    for n in range(2, 7):
        a[f"DrillCode{n}"] = "true"
        a[f"DrillInfo{n}"] = "true"
    a["DrillCode3"] = "false" if sp.xnc_back else "true"
    return a


def build(job: SawJob, *, when=None, guid: Optional[str] = None) -> str:
    stem = B.file_stem(job)
    P, L = B.Parts(job), B.Labels(job, KEY)
    now = when or B.now()
    guid = guid or str(uuid.uuid4())
    d = B.project_date(job)
    parts_xml: list[str] = []
    pid: dict[int, str] = {}
    for p in job.op.parts:
        if p.uid not in P.saw:
            continue
        a = part_attrs(job, P, L, p.uid)
        pid[p.uid] = a.get("id") or f"P{p.uid}"
        parts_xml.append(el("Part", a))
    jobs_xml: list[str] = []
    per_job: list[tuple[str, dict[int, int]]] = []           # (Job@Code, uid → dona)
    first_xy: dict[int, tuple[float, float]] = {}            # uid → listdagi birinchi joylashuv o'lchami (X, Y)
    for i, m in enumerate(job.maps, 1):
        jc = f"{stem}.{i:03d}"
        ax, cuts = B.cut_tree(m)
        prog = B.merge_runs(B.drop_rem(cuts), by_part=True)
        tl, tw = trims(job, m)
        cp = max(1, m.copies)
        tp = []
        for g, t in enumerate((tl, tw, tl, tw)):
            for j, v in enumerate((0, B.cents(t), B.cents(t), B.cents(t))):
                tp.append(el("TechnoParam", {"ID": str(320 + g * 4 + j), "Value": str(v)}))
        board = el("Board", {"Code": f"B1{i}", "Grain": "1", "L": B.ival(m.sheet_length), "MatCode": job.material_name,
                             "MatNo": "1", "Thickness": B.ival(job.thickness), "W": B.ival(m.sheet_width), "id": str(i)})
        flat = list(B.walk_cuts(prog))
        cx = []
        for n, c in enumerate(flat, 1):
            a = {"Code": code(c.level, ax), "L": B.n2(c.dim), "Rep": str(c.rep), "id": str(n)}
            if n == len(flat):
                k = chk(prog)
                if k is not None:
                    a["Chk"] = str(k)
            cx.append(el("Cut", a))
        jobs_xml.append(el("Job", {"Code": jc, "Comment": guid, "ExeOrder": str(i), "QBoards": str(cp), "ToWork": str(cp),
                                   "Type": "PROGRAM", "Worked": "0"}, tp + [board, el("Program", {}, cx) if cx else "<Program/>"]))
        cnt: dict[int, int] = {}
        for lf, mult in B.leaves_mult(cuts):
            if lf.uid:
                cnt[lf.uid] = cnt.get(lf.uid, 0) + mult * cp
                first_xy.setdefault(lf.uid, (round(lf.sx, 2), round(lf.sy, 2)))
        per_job.append((jc, cnt))
    # Piece: bir xil kesish o'lchamli (va tolalikli) detallar bitta bo'lakka
    pieces: dict[tuple, list[int]] = {}                      # (L, W, tola) — listdagi yo'nalishda; tolasiz detal burilishi mumkin
    for p in job.op.parts:
        sp = P.saw.get(p.uid)
        if sp is None:
            continue
        cl, cw = round(sp.length, 2), round(sp.width, 2)
        key = (cl, cw, True) if sp.grain else None
        if key is None:
            key = next((k for k in pieces if not k[2] and (k[0], k[1]) in ((cl, cw), (cw, cl))), None)
        if key is None:
            x, y = first_xy.get(p.uid, (cl, cw))
            key = (x, y, False) if (x, y) in ((cl, cw), (cw, cl)) else (cl, cw, False)
        pieces.setdefault(key, []).append(p.uid)
    pc_xml: list[str] = []
    n = 0
    for (cl, cw, g), uids in pieces.items():
        kids: list[str] = []
        done: set[str] = set()
        for u in uids:                                   # Pid, so'ng shu detal uchragan (hali yozilmagan) kartalar
            kids.append(el("Pid", {"id": pid[u]}))
            for jc, cnt in per_job:
                if jc in done or not cnt.get(u):
                    continue
                done.add(jc)
                kids.append(el("Sid", {"id": jc, **{f"q{pid[v]}": str(cnt[v]) for v in uids if cnt.get(v)}}))
        if not done:
            continue
        n += 1
        q = sum(P.saw[u].qty for u in uids)
        a = {"L": B.n2(cl), "N": str(n), "Q": str(q), "W": B.n2(cw), "qMin": str(q)}
        if g:
            a["G"] = "1"
        pc_xml.append(el("Piece", a, kids))
    wl = el("WorkList", {"Code": stem, "Comment": "", "Due": f"{d.isoformat()} 00:00:00", "MaterialID": "1",
                         "Released": now.strftime("%Y-%m-%d %H:%M:%S")}, parts_xml + jobs_xml + pc_xml)
    return '<?xml version="1.0" encoding="UTF-8"?>' + el("Order", {"Code": d.strftime("%d.%m.%Y"), "Comment": guid}, [wl])


@register(KEY, "Biesse Selco OSI", "saw", "xml",
          note="Diqqat: oxirgi kesimdagi nazorat summasi (Chk) algoritmi noma'lum — u yozilmaydi, stanok faylni rad etishi mumkin "
               "(stanokda sinash kerak). Boshqa dasturning detal etiketka bloklari yozilmaydi. Part maydonlari — "
               "«Данные для этикеток» jadvalidan.")
def gen(job: SawJob):
    return [(f"{B.file_stem(job)}.xml", build(job).encode("utf-8"))]
