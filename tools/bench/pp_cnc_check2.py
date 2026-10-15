"""Ishlov markazi postprotsessorlari (2-guruh: Daron, HIRZT, KDT, Nanxing SyntecCad, XDWoodCam) ↔ korxona namunalari.

`pp_cnc_check.py` dagi kabi: har namuna buyurtma uchun korxona loyihasi BIZNING importer bilan o'qiladi, har XNC
operatsiyasi `ppfmt.drill_job` → stanok moduli → fayl, zipdagi fayl bilan bayt-ma-bayt solishtiriladi (3173 — loyiha
eksportdan keyin o'zgargan, alohida). Solishtirishdan oldin faqat ma'lumotga bog'liq bo'lmagan maydonlar tenglashtiriladi:
Daron `Time` (eksport vaqti), Nanxing `Root@Cad` (dastur nomi). Daron da faqat `Grain` farq qiladigan fayllar alohida sanaladi. Frezalashli detallar fayllari alohida sanaladi va
ular uchun «Outline siz» va «Outline + freza qatorlarisiz» solishtiruv ham ko'rsatiladi.

    cd tools/bench && python pp_cnc_check2.py [--machine daron_foxcnc,kdt_trepan] [--order 3166] [--show 3]
"""
from __future__ import annotations

import argparse
import collections
import difflib
import os
import re
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pp_cnc_check import CHANGED, PROJECTS, SAMPLES, find_project  # noqa: E402
from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import _cnc as C  # noqa: E402

MACHINES = {
    "daron_foxcnc": "Daron FoxCNC, MicroDraw",
    "hirzt_magi": "HIRZT MAGI",
    "kdt_trepan": "KDT WDX trepan",
    "nanxing_syntec": "Nanxing SyntecCad",
    "xd_woodcam": "XDWoodCam",
}
OUTLINE = re.compile(rb"<Outline>.*?</Outline>", re.S)
GRAIN = re.compile(rb'Grain="[^"]*"')


def normalize(key: str, real: bytes, gen: bytes) -> bytes:
    """Namunadagi ma'lumotga bog'liq bo'lmagan maydonlarni biznikiga tenglashtirish."""
    if key == "daron_foxcnc":
        m = re.search(rb'Time="[^"]*"', gen)
        if m:
            real = re.sub(rb'Time="[^"]*"', m.group(0), real, count=1)
    elif key == "nanxing_syntec":
        m = re.search(rb'<Root Cad="[^"]*"', gen)
        if m:
            real = re.sub(rb'<Root Cad="[^"]*"', m.group(0), real, count=1)
    return real


def lines_of(data: bytes) -> list[str]:
    s = data.decode("utf-8", errors="replace")
    if "\r\n" not in s:
        s = s.replace("><", ">\r\n<")
    return s.split("\r\n")


def strip_mill(key: str, data: bytes, mill_widths: set[bytes]) -> bytes:
    data = OUTLINE.sub(b"", data)
    if key == "daron_foxcnc":
        data = re.sub(rb'<Slot[LA] [^>]*Width="([^"]*)"[^>]*/>\r\n',
                      lambda m: b"" if (m.group(0).startswith(b"<SlotA") or m.group(1) in mill_widths) else m.group(0), data)
    return data


def mill_parts(project) -> set[int]:
    """Detallar (uid), ularning biror XNC dasturida frezalash bor."""
    res = set()
    xmill = set()
    for o in project.operations:
        if o.type == OpType.XNC and o.xnc:
            stack = list(o.xnc.program)
            while stack:
                c = stack.pop()
                if c.enabled and str(getattr(c.cmd, "value", c.cmd)).startswith("Mill"):
                    xmill.add(o.id)
                    break
                stack.extend(c.children)
    for o in project.operations:
        for p in o.parts:
            if set(p.xnc_op_ids) & xmill:
                res.add(id(p))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--machine", default=",".join(MACHINES))
    ap.add_argument("--order", default="")
    ap.add_argument("--show", type=int, default=3)
    ap.add_argument("--showmill", type=int, default=0, help="frezali farqli fayllardan ko'rsatiladigani")
    ap.add_argument("--samples", default=SAMPLES)
    ap.add_argument("--projects", default=PROJECTS)
    a = ap.parse_args()
    keys = [k for k in a.machine.split(",") if k]
    fmts = ppfmt.load_all()
    import glob
    orders = sorted({os.path.splitext(os.path.basename(z))[0]
                     for k in keys for z in glob.glob(os.path.join(a.samples, MACHINES[k], "*.zip"))})
    if a.order:
        orders = [o for o in orders if o.startswith(a.order)]
    res = {k: collections.Counter() for k in keys}
    shown = collections.Counter()
    t0 = time.time()
    for order in orders:
        num = order.split("_")[0]
        pf = find_project(order, a.projects)
        if not pf:
            print(f"[{order}] loyiha topilmadi — o'tkazildi")
            continue
        with open(pf, "rb") as f:
            project, _w = import_project(f.read(), os.path.basename(pf))
        xops = [o for o in project.operations if o.type == OpType.XNC and o.xnc]
        jobs = [ppfmt.drill_job(project, o) for o in xops]
        mp = mill_parts(project)
        tag = "changed" if num in CHANGED else "main"
        for k in keys:
            zpath = os.path.join(a.samples, MACHINES[k], order + ".zip")
            if not os.path.exists(zpath):
                continue
            with zipfile.ZipFile(zpath) as z:
                real = {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}
            fmt = fmts[k]
            names, gens, mills, widths = [], [], [], []
            for j in jobs:
                p = C.part_of(j)
                for nm, data in fmt.fn(j):
                    names.append(nm)
                    gens.append(data)
                    mills.append(p is not None and id(p) in mp)
                    widths.append({ppfmt.num(o["d"]).encode() for o in C.ops(j) if o["t"] == "ms"})
            dd = ppfmt._dedupe(list(zip(names, gens)))
            gen = {nm: (data, mills[i], widths[i]) for i, (nm, data) in enumerate(dd)}
            r = res[k]
            for name, data in real.items():
                g = gen.get(name)
                grp = tag + ("_mill" if g and g[1] else "")
                r[grp + "_total"] += 1
                if g is None:
                    r[grp + "_missing"] += 1
                    continue
                data = normalize(k, data, g[0])
                if g[0] == data:
                    r[grp + "_same"] += 1
                    continue
                if k == "daron_foxcnc" and GRAIN.sub(b"", g[0]) == GRAIN.sub(b"", data):
                    r[tag + "_grain_only"] += 1         # faqat Grain (3183: loyiha eksportdan keyin saqlangan)
                    r[grp + "_diff"] += 1
                elif g[1] and OUTLINE.sub(b"", g[0]) == OUTLINE.sub(b"", data):
                    r[grp + "_same_but_outline"] += 1
                elif g[1] and strip_mill(k, g[0], g[2]) == strip_mill(k, data, g[2]):
                    r[grp + "_same_but_outline_millpath"] += 1
                else:
                    r[grp + "_diff"] += 1
                lim = a.showmill if g[1] else a.show
                if tag == "main" and shown[(k, g[1])] < lim:
                    shown[(k, g[1])] += 1
                    ra, ga = lines_of(data), lines_of(g[0])
                    dl = [x for x in difflib.unified_diff(ra, ga, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
                    print(f"  {k} [{order}] {name}{' (freza)' if g[1] else ''}: {len(dl)} qator farq")
                    for x in dl[:12]:
                        print("      " + x[:200])
            r[tag + "_extra"] += len([nm for nm in gen if nm not in real])
    print(f"\nVaqt: {time.time() - t0:.1f} s")
    for k in keys:
        r = res[k]
        tot = r["main_total"] + r["main_mill_total"]
        same = r["main_same"] + r["main_mill_same"]
        print(f"{k:15s} bir xil {same}/{tot} | frezasiz {r['main_same']}/{r['main_total']} "
              f"(farqli {r['main_diff']}, yo'q {r['main_missing']}) | frezali {r['main_mill_same']}/{r['main_mill_total']} "
              f"(Outline dan tashqari {r['main_mill_same_but_outline']}, Outline+freza yo'lidan tashqari "
              f"{r['main_mill_same_but_outline_millpath']}, farqli {r['main_mill_diff']}) | ortiqcha {r['main_extra']} | "
              f"3173: {r['changed_same'] + r['changed_mill_same']}/{r['changed_total'] + r['changed_mill_total']}"
              + (f" | faqat Grain farqi: {r['main_grain_only']}" if r["main_grain_only"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
