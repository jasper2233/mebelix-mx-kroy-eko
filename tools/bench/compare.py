"""Korxona loyihalari korpusi bo'yicha kroy sifatini avvalgi dastur (GibLab) saqlagan natijalar bilan solishtirish.

    cd tools/bench && python3 compare.py [fast|normal|max] [teg]

corpus.json — 205 ta real .project fayldagi CS kroylar (398 ta; detallar, kesish parametrlari) va ularning ichida
saqlangan avvalgi dastur natijasi: listlar soni, деловой qoldiq m², kesish uzunligi. Har kroy MebeliX optimizatori
bilan qayta yechiladi, natija `validate()` bilan tekshiriladi (ustma-ust, propil, minimal obrezka, daraja).
Natija: out_<teg>.json va qisqa jadval. Optimizatorni o'zgartirgandan keyin shu skript bilan tekshiring:
listlar soni ko'paymasin, xato 0 bo'lsin.
"""
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))


def job(args):
    k, j, quality = args
    from app.models import CSCutParams, CSMaterialParams, FirstCutDir, StockSheet
    from app.services import optimizer as mod
    from app.services.validate import validate
    items = []
    for p in j["parts"]:
        rot = not (j["texture"] and p["grain"])
        items += [mod.Item(p["id"], k, p["l"], p["w"], rot) for _ in range(p["qty"])]
    s = j["sheet"]
    cut = CSCutParams(kerf=j["kerf"], trim_length=j["trimL"], trim_width=j["trimW"], max_rotations=j["max_turns"],
                      complex_strips=j["complex"], min_trim_cut=j["min_trim"], trim_includes_kerf=j["trim_includes_kerf"],
                      first_cut=FirstCutDir(j["direct"]) if j["direct"] in (0, 1, 2, 3, 4) else FirstCutDir.ANY,
                      quality=quality)
    mat = CSMaterialParams(remnant_min_side1=j["rem1"], remnant_min_side2=j["rem2"], remnant_min_area=j["rem_area"])
    st = [StockSheet(id="s", length=s["l"], width=s["w"])]
    t0 = time.time()
    res = mod.optimize(items, st, cut, mat)
    dt = time.time() - t0
    errs = len(validate(res, items, st, cut))
    biz = sum(o.length * o.width / 1e6 * m.copies for m in res.maps for o in m.offcuts if o.kind == "remnant" and o.business)
    return dict(k=k, sheets=res.total_sheets, gl=j["gl_sheets"], unpl=len(res.unplaced), t=dt, file=j["file"], op=j["op"],
                n=len(items), biz=round(biz, 4), gl_biz=j.get("gl_business_m2"), cut=res.total_cut_length_m,
                gl_cut=j.get("gl_cut_m"), errs=errs, valid=j.get("valid", True))


def main():
    quality = sys.argv[1] if len(sys.argv) > 1 else "normal"
    tag = sys.argv[2] if len(sys.argv) > 2 else quality
    jobs = json.load(open(os.path.join(HERE, "corpus.json")))
    sel = os.environ.get("SEL")
    ks = [int(x) for x in sel.split(",")] if sel else range(len(jobs))
    t = time.time()
    with Pool(os.cpu_count()) as pool:
        out = pool.map(job, [(k, jobs[k], quality) for k in ks], chunksize=1)
    json.dump(out, open(os.path.join(HERE, f"out_{tag}.json"), "w"))
    v = [o for o in out if o["valid"]]          # avvalgi dastur natijasi to'liq bo'lmagan kroylar hisobga olinmaydi
    me = sum(o["sheets"] for o in v)
    gl = sum(o["gl"] for o in v)
    better = sum(o["sheets"] < o["gl"] for o in v)
    worse = sum(o["sheets"] > o["gl"] for o in v)
    eq = [o for o in v if o["sheets"] == o["gl"]]
    bz = sum(o["biz"] for o in eq)
    gbz = sum(o["gl_biz"] or 0 for o in eq)
    cu = sum(o["cut"] for o in eq)
    gcu = sum(o["gl_cut"] or 0 for o in eq)
    print(f"{tag}: {len(v)} kroy | listlar MebeliX {me}, avvalgi {gl} | kam {better}, teng {len(v) - better - worse}, "
          f"ko'p {worse} | tekshiruv xatosi {sum(o['errs'] for o in out)} | joylashmagan {sum(o['unpl'] for o in v)} | "
          f"eng uzoq {max(o['t'] for o in out):.1f} s | jami {time.time() - t:.0f} s")
    print(f"   listlar soni teng {len(eq)} kroyda: деловой qoldiq {bz:.1f} m² (avvalgi {gbz:.1f}) | "
          f"kesish uzunligi {cu:.0f} m (avvalgi {gcu:.0f})")
    for o in v:
        if o["sheets"] > o["gl"]:
            print(f"   ko'p: #{o['k']} {o['file']} op{o['op']} detal {o['n']}: {o['sheets']} > {o['gl']}")


if __name__ == "__main__":
    main()
