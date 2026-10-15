"""Ishlov markazi (prisadka) postprotsessorlari ↔ korxona namunalari: bayt-ma-bayt solishtirish.

Har namuna buyurtma (`post prtsessorlar/PRISADKA APPARAT/<stanok>/<NNNN>_<mijoz>.zip`) uchun korxona loyihasi
(`giblab project/**/NNNN_<mijoz>.project`, bo'lmasa `NNNN <mijoz>.project`) BIZNING importer bilan o'qiladi, har XNC
operatsiyasi `ppfmt.drill_job` → stanok moduli (fn yoki batch) bilan fayl(lar)ga aylantiriladi va zipdagi fayllar bilan
solishtiriladi. 3173 — loyiha eksportdan keyin o'zgargan: alohida ko'rsatiladi, umumiy hisobga kirmaydi.

    cd tools/bench && python pp_cnc_check.py [--machine tpa,woodwop] [--order 3166] [--show 5] [--samples DIR] [--projects DIR]
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import os
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SAMPLES = os.path.join(ROOT, "post prtsessorlar", "PRISADKA APPARAT")
PROJECTS = os.path.join(ROOT, "giblab project")
MACHINES = {                     # kalit → (namuna papkasi, kengaytma, matnmi)
    "tpa": ("TPA Genesis Evolution 8.9", ".CNC", True),
    "woodwop": ("Homag Wood WOP v6.x", ".mpr", True),
    "biesseworks": ("Biesse Works v3.x", ".bpp", True),
    "xilog3": ("SCM Xilog v3", ".pgm", False),
    "scm_startech": ("SCM Startech CN V", ".ISO", True),
}
CHANGED = {"3173"}               # loyiha eksportdan keyin o'zgargan buyurtmalar


def find_project(order: str, projects: str) -> str | None:
    num, _, client = order.partition("_")
    for pat in (f"{num}_{client}.project", f"{num} {client}.project"):
        c = sorted(glob.glob(os.path.join(projects, "**", pat), recursive=True))
        if c:
            return c[0]
    return None


def lines_of(key: str, data: bytes) -> list[str]:
    if key == "xilog3":
        from app.services.ppfmt.xilog3 import read_records
        h, recs = read_records(data)
        return [h, *recs]
    return data.decode("cp1251", errors="replace").split("\r\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--machine", default=",".join(MACHINES))
    ap.add_argument("--order", default="")
    ap.add_argument("--show", type=int, default=3, help="har stanok uchun ko'rsatiladigan farqli fayllar soni")
    ap.add_argument("--samples", default=SAMPLES)
    ap.add_argument("--projects", default=PROJECTS)
    a = ap.parse_args()
    keys = [k for k in a.machine.split(",") if k]
    fmts = ppfmt.load_all()
    orders = sorted({os.path.splitext(os.path.basename(z))[0]
                     for k in keys for z in glob.glob(os.path.join(a.samples, MACHINES[k][0], "*.zip"))})
    if a.order:
        orders = [o for o in orders if o.startswith(a.order)]
    res = {k: collections.Counter() for k in keys}
    shown = collections.Counter()
    reasons = {k: collections.Counter() for k in keys}
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
        for k in keys:
            zpath = os.path.join(a.samples, MACHINES[k][0], order + ".zip")
            if not os.path.exists(zpath):
                continue
            with zipfile.ZipFile(zpath) as z:
                real = {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}
            fmt = fmts[k]
            try:
                files = fmt.batch(jobs, project) if fmt.batch else [f for j in jobs for f in fmt.fn(j)]
            except Exception as e:  # noqa: BLE001
                print(f"[{order}] {k}: generator xatosi: {e!r}")
                raise
            gen = dict(ppfmt._dedupe(files))
            tag = "changed" if num in CHANGED else "main"
            r = res[k]
            for name, data in real.items():
                r[tag + "_total"] += 1
                g = gen.get(name)
                if g is None:
                    r[tag + "_missing"] += 1
                    if tag == "main" and shown[k] < a.show:
                        shown[k] += 1
                        print(f"  {k} [{order}] {name}: bizda yo'q")
                    continue
                if g == data:
                    r[tag + "_same"] += 1
                    continue
                r[tag + "_diff"] += 1
                ra, ga = lines_of(k, data), lines_of(k, g)
                dl = [x for x in difflib.unified_diff(ra, ga, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
                first = next((x for x in dl), "")
                if tag == "main":
                    reasons[k][(first[:1] + first[1:].split(" ")[0][:12]) if first else "bayt"] += 1
                if tag == "main" and shown[k] < a.show:
                    shown[k] += 1
                    print(f"  {k} [{order}] {name}: {len(dl)} qator farq")
                    for x in dl[:8]:
                        print("      " + x[:160])
            extra = [n for n in gen if n not in real]
            r[tag + "_extra"] += len(extra)
            if extra and tag == "main" and shown[k] < a.show:
                shown[k] += 1
                print(f"  {k} [{order}] ortiqcha fayllar: {extra[:5]}")
    print(f"\nVaqt: {time.time() - t0:.1f} s")
    for k in keys:
        r = res[k]
        print(f"{k:13s} bir xil {r['main_same']}/{r['main_total']}"
              f" (farqli {r['main_diff']}, bizda yo'q {r['main_missing']}, ortiqcha {r['main_extra']})"
              f" | 3173 (o'zgargan loyiha): {r['changed_same']}/{r['changed_total']}")
        if reasons[k]:
            print("   farq turlari:", dict(reasons[k].most_common(8)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
