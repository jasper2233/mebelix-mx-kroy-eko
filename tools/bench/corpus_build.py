"""projects/ papkadagi korxona .project fayllaridan CS kroylar korpusini (corpus.json) qayta qurish.

    cd tools/bench && python3 corpus_build.py

Har CS operatsiya uchun: detallar (kroy o'lchami, soni × mahsulot soni, tekstura), list, kesish parametrlari,
qoldiq qoidalari va fayl ichida saqlangan avvalgi dastur natijasi (gl_*): listlar soni, joylangan detallar soni va
maydoni, kesish uzunligi va soni, деловой qoldiq m², to'ldirish, paketlar. valid — avvalgi natijada barcha detallar
joylangan bo'lsa (aks holda solishtirishda hisobga olinmaydi).
"""
import glob
import json
import os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.environ.get("BENCH_PROJECTS") or os.path.join(HERE, "projects")     # boshqa papka: BENCH_PROJECTS=...
OUT = os.environ.get("BENCH_OUT") or os.path.join(HERE, "corpus.json")        # BENCH_OUT=corpus_big.json


def fnum(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def parse(path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []
    goods = {g.get("id"): g for g in root.findall("good")}
    part_by_id, part_mult = {}, {}
    for g in root.findall("good"):
        if g.get("typeId") == "product":
            mult = int(fnum(g.get("count"), 1)) or 0
            for p in g.iter("part"):
                part_by_id[p.get("id")] = p
                part_mult[p.get("id")] = mult
    jobs = []
    for op in root.findall("operation"):
        if op.get("typeId") != "CS":
            continue
        mat = op.find("material")
        if mat is None:
            continue
        gl_sheets = int(fnum(mat.get("count"), 0))
        sheet_good = goods.get(mat.get("id"))
        tool = goods.get(op.get("tool1"))
        if sheet_good is None or gl_sheets <= 0:
            continue
        stock, remnants = None, []
        for sp in sheet_good.findall("part"):
            if sp.get("waste") == "true":
                remnants.append(dict(l=fnum(sp.get("l")), w=fnum(sp.get("w")), rl=fnum(sp.get("rl")), rw=fnum(sp.get("rw")),
                                     count=int(fnum(sp.get("count"), 1)), business=sp.get("business") == "true"))
            elif stock is None and fnum(sp.get("count")) >= 1:
                stock = dict(l=fnum(sp.get("l")), w=fnum(sp.get("w")), qty=int(fnum(sp.get("count"))),
                             used=int(fnum(sp.get("usedCount"))))
        if stock is None or stock["l"] <= 0:
            continue
        parts = []
        for ref in op.findall("part"):
            p = part_by_id.get(ref.get("id"))
            if p is None:
                continue
            q = int(fnum(p.get("count"), 1)) * part_mult.get(ref.get("id"), 1)
            L = fnum(p.get("cl")) or fnum(p.get("l"))
            W = fnum(p.get("cw")) or fnum(p.get("w"))
            if q > 0 and L > 0 and W > 0:
                parts.append(dict(id=ref.get("id"), l=L, w=W, qty=q, grain=p.get("txt") == "true"))
        if not parts:
            continue
        t = tool if tool is not None else ET.Element("x")
        rel = os.path.relpath(path, PROJ).replace(os.sep, "/")
        job = dict(file=rel, op=op.get("id"), name=sheet_good.get("name"),
                   sheet=stock, gl_sheets=gl_sheets, gl_remnants=remnants, parts=parts,
                   kerf=fnum(t.get("swSawthick"), 3), max_turns=int(fnum(t.get("swMaxturns"), 4)),
                   complex=t.get("swComplexBand", "true") == "true", min_trim=fnum(t.get("swMinPruning"), 5),
                   trim_includes_kerf=t.get("swTrimIncludeSaw") == "true",
                   trimL=fnum(op.get("cTrimL")), trimW=fnum(op.get("cTrimW")),
                   texture=op.get("csTexture", "true") == "true", direct=int(fnum(op.get("csDirectCut"), 0)),
                   rem1=fnum(op.get("cMinDimRegWaste1"), 1000), rem2=fnum(op.get("cMinDimRegWaste2"), 500),
                   rem_area=fnum(op.get("cBusinessWaste"), 0.5))
        job.update(gl_part_count=int(fnum(op.get("cPartCount"))), gl_part_area=fnum(op.get("cPartAmount")),
                   gl_cut_m=fnum(op.get("cTrimLength")), gl_cuts=int(fnum(op.get("cTrimCount"))),
                   gl_business_m2=fnum(op.get("cBusinessWasteAmount")), gl_fill=fnum(op.get("cFilling")),
                   gl_packets=int(fnum(op.get("cCountPackets"))))
        job["valid"] = job["gl_part_count"] == sum(p["qty"] for p in parts)
        jobs.append(job)
    return jobs


def main():
    files = sorted(glob.glob(os.path.join(PROJ, "**", "*.project"), recursive=True))
    if not files:
        raise SystemExit(f"{PROJ} da .project fayllar yo'q")
    jobs = [j for f in files for j in parse(f)]
    if os.environ.get("BENCH_DEDUP"):          # bir xil kroy (detallar, list, parametrlar) qayta sanalmasin
        seen, uniq = set(), []
        for j in jobs:
            key = json.dumps([j["sheet"], sorted((p["l"], p["w"], p["qty"], p["grain"]) for p in j["parts"]), j["kerf"],
                              j["max_turns"], j["trimL"], j["trimW"], j["min_trim"], j["direct"]], sort_keys=True)
            if key not in seen:
                seen.add(key)
                uniq.append(j)
        print("takroriy kroylar olib tashlandi:", len(jobs) - len(uniq))
        jobs = uniq
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(jobs, fh, ensure_ascii=False)
    n_parts = sum(sum(p["qty"] for p in j["parts"]) for j in jobs)
    print(len(files), "fayl ->", len(jobs), "CS kroy,", n_parts, "detal; avvalgi dastur listlari:",
          sum(j["gl_sheets"] for j in jobs), "; to'liq bo'lmagan natija:", sum(not j["valid"] for j in jobs))


if __name__ == "__main__":
    main()
