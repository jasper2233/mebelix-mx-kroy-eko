"""Nanxing NXCutSaw — `.CUT` (AutoCUT XML `ver=500`). Tavsif: docs/mebelix/postprocessors/nanxing-nxcutsaw.md
(+ nanxing-nxcutsaw-flat.md — xuddi shu format, tekis papka).

Bitta CS operatsiyasi (material) → bitta fayl: UTF-8 (BOM'siz), butun XML bitta qatorda, atributlar alfavit tartibida.
Tarkibi: kirish listlari (`Condition`), delovoy qoldiqlar (`Spares`), kesish kartalari (`Layout` → `Part` daraxti),
detallar ro'yxati (`Objective`, etiketka maydonlari F1…F13).
"""
from __future__ import annotations

from typing import Optional

from . import SawJob, num, register
from . import _saw_strips as S

KEY = "nanxing_nxcutsaw"
NOTE = ("Torsovka (Sx/Sy, birinchi bo'lak boshi) = kroy zonasining boshi (torsovka + propil, namunalarda 2 + 3 = 5). "
        "Paket balandligi faylga yozilmaydi (stanokda). Kasr o'lchamlar nuqta bilan (namunalarda uchramagan).")


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _el(tag: str, attrs: dict, inner: Optional[str] = None) -> str:
    a = "".join(f' {k}="{_esc(v)}"' for k, v in sorted(attrs.items()))
    return f"<{tag}{a}/>" if inner is None else f"<{tag}{a}>{inner}</{tag}>"


def _part_xml(p: S.Piece, grouped: int, uid_idx: dict[int, int]) -> str:
    x, y, l, w = p.cr
    at = {"Px": num(x), "Py": num(y), "X": num(l), "Y": num(w)}
    if p.kind == "P":
        at["UID"] = str(uid_idx.get(p.uid, 0))
        if p.rotated:
            at["Angle"] = "90"
    elif p.kind == "R":
        at["UID"] = str(p.k - 1)
        at["Spare"] = "True"
    if grouped > 1:
        at["Grouped"] = str(grouped)
    if p.kind != "C" or not p.children:
        return _el("Part", at)
    return _el("Part", at, _children_xml(p, uid_idx))


def _children_xml(p: S.Piece, uid_idx: dict[int, int]) -> str:
    out = []
    for run in S.runs(p.children):
        for i, c in enumerate(run):
            out.append(_part_xml(c, len(run) if i == len(run) - 1 else 0, uid_idx))
    return "".join(out)


def cut_xml(job: SawJob) -> bytes:
    infos = S.map_infos(job)
    uid_idx = {p.uid: i for i, p in enumerate(job.parts)}
    mat = job.material_name
    kerf = num(job.kerf)
    # kirish listlari: har list uchun torsovka — shu listdagi birinchi karta zonasidan
    trims: dict[str, tuple[float, float]] = {}
    for mi in infos:
        trims.setdefault(mi.m.sheet_id, (mi.tx, mi.ty))
    dflt = S.default_trim(job)
    cond = []
    sid_idx: dict[str, int] = {}
    for i, s in enumerate(job.stock):
        sid_idx[s["id"]] = i
        tx, ty = trims.get(s["id"], dflt)
        cond.append(_el("Shape", {"Count": str(int(s["qty"])), "Flag": "True", "Name": mat, "Sx": num(tx), "Sy": num(ty),
                                  "X": num(s["length"]), "Y": num(s["width"])}))
    spares = "".join(_el("Shape", {"Count": str(c), "Name": f"О{k}", "Turn": "False", "X": num(x), "Y": num(y)})
                     for k, (x, y, c) in enumerate(S.spares(infos), 1))
    lays = []
    for i, mi in enumerate(infos):
        inner = _children_xml(mi.root, uid_idx) if mi.root is not None else ""
        lays.append(_el("Layout", {"Count": str(mi.m.copies), "Cut": "true" if mi.axis == "x" else "false", "CutCount": "0",
                                   "ID": str(i), "SheetID": str(sid_idx.get(mi.m.sheet_id, 0)), "SheetName": mat,
                                   "X": num(mi.L), "Y": num(mi.W)}, inner))
    shapes = []
    for i, p in enumerate(job.parts):
        at = {"Count": str(p.qty), "F1": p.name, "F3": str(p.qty), "F4": f"{p.length:.2f}", "F5": f"{p.width:.2f}",
              "F12": "true" if p.has_mill else "false", "F13": "true" if p.has_drill else "false",
              "Name": f"Д{i + 1}", "NestGap": kerf, "Order": p.product, "Turn": "true" if S.can_turn(job, p) else "false",
              "X": num(p.length), "Y": num(p.width)}
        if p.description:
            at["F2"] = p.description
        if p.xnc_face:
            at["F6"] = p.xnc_face
        if p.xnc_back:
            at["F7"] = p.xnc_back
        for f, side in (("F8", "top"), ("F9", "bottom"), ("F10", "left"), ("F11", "right")):
            t = S.edge_text(p.edges.get(side))
            if t:
                at[f] = t
        shapes.append(_el("Shape", at))
    data_at = {"Ply": num(job.thickness), "TypeName": mat}
    if job.material_code:
        data_at["Type"] = job.material_code
    data = _el("Data", data_at,
               _el("Spares", {"Type": "Shape"}, spares or None)
               + _el("Condition", {"Count": str(len(cond)), "Type": "Shape"}, "".join(cond))
               + _el("Solutions", {"SolveGap": kerf}, "<Solution><Layouts>" + "".join(lays) + "</Layouts></Solution>")
               + _el("Objective", {"Count": str(len(shapes)), "Type": "Shape"}, "".join(shapes)))
    proj = _el("Project", {"Memo": "", "Name": S.project_title(job), "Update": S.now().strftime("%d.%m.%Y %H:%M:%S")}, data)
    xml = '<?xml version="1.0" encoding="UTF-8"?>' + _el("AutoCUT", {"ver": "500"}, proj)
    return xml.encode("utf-8")


@register(KEY, "Nanxing NXCutSaw (.CUT)", "saw", ".CUT", note=NOTE)
def generate(job: SawJob):
    return [(S.file_stem(job) + ".CUT", cut_xml(job))]
