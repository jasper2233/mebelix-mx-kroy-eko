"""KDT XML (arra) yozuvchisi qoidalarini `.project` ga bog'lanmasdan tekshirish: stanokda ishlayotgan real XML dagi kroy
(daraxt, koordinatalar) qayta MX kroy daraxtiga aylantiriladi → `kdt_presize_xml` (v2) yozuvchisi → natija real fayl bilan
MANTIQAN solishtiriladi (`pp_kdt_real.canon_saw`: ichki id, qoldiq kodi, list kodi hisobga olinmaydi).

Real XML koordinatalari: `y` — list uzunligi bo'ylab, `x` — eni bo'ylab; toq qatlam tuguni `x..x+w`, `y..y+l`, juft qatlam —
`x..x+l`, `y..y+w`. MX daraxtida `x` — uzunlik bo'ylab, shuning uchun x ↔ y almashtiriladi.

    python pp_kdt_xml_roundtrip.py [--src PAPKA] [--show 2]
"""
from __future__ import annotations

import argparse
import difflib
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
sys.path.insert(0, HERE)
from app.services.ppfmt import SawMap, SawNode, SawPart  # noqa: E402
from app.services.ppfmt._saw_common import demo_job  # noqa: E402
from app.services.ppfmt.saw_kdt_xml import xml_text  # noqa: E402
from pp_kdt_real import SRC, canon_saw  # noqa: E402


SWAP = [True]          # panel `l` — list uzunligi (odatiy) bo'lsa XML y → MX x; aks holda (1-kesimlar eni bo'ylab) almashmaydi


def rect(no) -> tuple[float, float, float, float]:
    """XML tuguni → MX to'rtburchagi (x — list uzunligi bo'ylab, y — eni bo'ylab, uzunlik, en)."""
    x, y, l, w = (float(no.get(k)) for k in ("x", "y", "l", "w"))
    lay = int(no.get("layer"))
    ax, ay, ex, ey = (x, y, w, l) if lay % 2 == 1 else (x, y, l, w)     # XML: x..x+ex, y..y+ey
    return (ay, ax, ey, ex) if SWAP[0] else (ax, ay, ex, ey)


def parse(data: bytes, sheet_len: float | None = None):
    """sheet_len — haqiqiy list uzunligi (ma'lum bo'lsa; aks holda uzun tomoni deb olinadi)."""
    root = ET.fromstring(data)
    parts_xml = next(pn for pn in root if pn.tag == "parts")
    dims = {c.get("code"): (float(c.get("l")), float(c.get("w")), int(c.get("sq"))) for c in parts_xml}
    panels = [pn for pn in root if pn.tag != "parts"]
    kerf = float(panels[0].get("saw"))
    trim = float(next(iter(panels[0])).get("trim")) - kerf
    maps = []
    for i, pn in enumerate(panels, 1):
        nodes = list(pn)
        by_id = {no.get("id"): no for no in nodes}
        L, W = float(pn.get("l")), float(pn.get("w"))
        real_len = sheet_len if sheet_len else max(L, W)
        SWAP[0] = abs(L - real_len) < 0.01
        L, W = (L, W) if SWAP[0] else (W, L)            # L — haqiqiy list uzunligi

        def build(no, axis_hint: str, rem_no=[0]) -> SawNode:
            x, y, l, w = rect(no)
            # kesim o'qi geometriyadan: bolalar x bo'yicha har xil boshlansa — o'q x
            kids = [by_id.get(c.get("id")) for c in no]
            xs = {round(rect(k)[0], 3) for k in kids if k is not None}
            axis = "x" if len(xs) > 1 else ("y" if len(kids) > 1 else axis_hint)
            if len(kids) == 1 and kids[0] is not None:
                kx, ky, kl, kw = rect(kids[0])
                axis = "y" if abs(kl - l) < 0.01 else "x"
            n = SawNode(x=x, y=y, l=l, w=w, kind="C", axis=axis, children=[])
            for c in no:
                t = c.get("type")
                ch = by_id.get(c.get("id"))
                if t == "1":
                    cx, cy, cl, cw = rect(ch) if ch is not None else (x, y, 0, 0)
                    n.children.append(SawNode(x=cx, y=cy, l=cl, w=cw, kind="P", uid=int(c.get("code"))))
                elif t == "2" and ch is not None:
                    n.children.append(build(ch, "y" if axis == "x" else "x"))
                elif t == "3" and ch is not None:
                    rem_no[0] += 1
                    cx, cy, cl, cw = rect(ch)
                    n.children.append(SawNode(x=cx, y=cy, l=cl, w=cw, kind="W", rem=rem_no[0]))
            return n
        first = nodes[0]
        top = build(first, "x")
        off = float(first.get("trim"))
        # daraxt ildizi — foydali zona (torsovka + propil dan keyin)
        top.x, top.y, top.l, top.w = off, off, L - 2 * off, W - 2 * off
        maps.append(SawMap(index=i, copies=int(pn.get("num")), sheet_length=L, sheet_width=W, is_remnant=False,
                           sheet_id="s1", tree=top, placements=[], offcuts=[], commands=[], trim_length=trim, trim_width=trim))
    parts = [SawPart(uid=int(k), name=f"d{k}", code=k, length=v[0], width=v[1], qty=v[2], grain=False)
             for k, v in dims.items() if k.isdigit()]
    job = demo_job(parts, maps, kerf=kerf, trim=trim)
    job.material_name = panels[0].get("material")
    job.material_code = panels[0].get("mcode") or ""
    job.thickness = float(panels[0].get("thickness"))
    return job


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--show", type=int, default=2)
    a = ap.parse_args()
    tot = Counter()
    shown = 0
    sd = os.path.join(a.src, "pilniy sentr")
    for z in sorted(os.listdir(sd)):
        with zipfile.ZipFile(os.path.join(sd, z)) as zf:
            for n in zf.namelist():
                if not n.lower().endswith(".xml"):
                    continue
                real = zf.read(n)
                tot["jami"] += 1
                try:
                    ours = xml_text(parse(real), v2=True).encode("utf-8")
                except Exception as e:  # noqa: BLE001
                    tot["xato"] += 1
                    print(f"  {z} / {n.split('/')[-1]}: tiklashda xato: {e}")
                    continue
                if canon_saw(ours) == canon_saw(real):
                    tot["mantiqan bir xil"] += 1
                    continue
                tot["farq"] += 1
                if shown < a.show:
                    shown += 1
                    d = [x for x in difflib.unified_diff(canon_saw(real), canon_saw(ours), "real", "mx", n=0, lineterm="")
                         if not x.startswith(("---", "+++"))]
                    print(f"  {z} / {n.split('/')[-1]}:\n      " + "\n      ".join(x[:200] for x in d[:8]))
    print(dict(tot))


if __name__ == "__main__":
    main()
