"""KDT fayllari MX ning O'Z kroyi bilan: har loyiha MX optimizatorida kesiladi → `kdt_presize_xml` (arra) va `kdt_panel`
(prisadka). Tekshiruvlar:
  * arra XML qayta o'qilib (`pp_kdt_xml_roundtrip.parse`) yana yoziladi — mantiqan o'zi bilan bir xil (yozuvchi izchil);
  * XML dagi detallar soni = kroy natijasidagi joylashgan detallar (nusxalar bilan);
  * har XNC li detal etiketkasining QR i (`xnc_file`) — prisadka fayllari nomlaridan biri;
  * prisadka fayllari soni = XNC li detallar soni (orqa tomon alohida fayl emas).

    python pp_kdt_own_cut.py [--src PAPKA] [--quality fast]
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
import zipfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
sys.path.insert(0, HERE)
from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import calc, ppfmt  # noqa: E402
from pp_kdt_real import SRC, canon_saw, projects  # noqa: E402
from pp_kdt_xml_roundtrip import parse  # noqa: E402
from app.services.ppfmt.saw_kdt_xml import xml_text  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--quality", default="fast")
    ap.add_argument("--dir", default="", help="`.project` fayllari papkasi (zip o'rniga)")
    a = ap.parse_args()
    reg = ppfmt.load_all()
    tot = Counter()
    projs = ({f.split("_")[0]: (f, open(os.path.join(a.dir, f), "rb").read()) for f in os.listdir(a.dir) if f.endswith(".project")}
             if a.dir else projects(a.src))
    for num, (name, data) in sorted(projs.items()):
        proj, _w = import_project(data, name)
        bad = []
        for op in proj.operations:
            if op.type != OpType.CS or not op.parts:
                continue
            op.cs_cut.quality = a.quality
            op.result = None
            try:
                calc.run_cutting(proj, op, quality=a.quality)
            except Exception as e:  # noqa: BLE001
                bad.append(f"{op.name}: kroy xatosi {e}")
                continue
            if not op.result or not op.result.maps:
                continue
            job = ppfmt.saw_job(proj, op)
            (zn, zdata), = reg["kdt_presize_xml"].fn(job)
            zf = zipfile.ZipFile(io.BytesIO(zdata))
            xml = next(zf.read(n) for n in zf.namelist() if n.endswith(".xml"))
            tot["arra"] += 1
            if canon_saw(xml_text(parse(xml, op.result.maps[0].sheet_length), v2=True).encode()) != canon_saw(xml):
                bad.append(f"{op.name}: XML o'zi bilan mos emas")
            placed = sum(m.copies * len(m.placements) for m in op.result.maps)
            parts_xml = sum(int(x) for x in re.findall(r'<part code="\d+" l="[^"]+" rc="\d+" sq="\d+" uc="(\d+)"', xml.decode()))
            if parts_xml != placed:
                bad.append(f"{op.name}: XML dagi detallar {parts_xml} ≠ kroyda {placed}")
            for p in job.parts:
                if p.xnc_file:
                    tot["qr"] += 1
        jobs = [ppfmt.drill_job(proj, o) for o in proj.operations if o.type == OpType.XNC]
        files = reg["kdt_panel"].batch(jobs, proj)
        names = {n[:-4] for n, _ in files}
        tot["prisadka"] += len(files)
        parts_xnc = {p.id for o in proj.operations if o.type == OpType.CS for p in o.parts if p.xnc_op_ids}
        if len(files) != len(parts_xnc):
            bad.append(f"prisadka fayllari {len(files)} ≠ XNC li detallar {len(parts_xnc)}")
        for o in proj.operations:
            if o.type != OpType.CS or not o.result:
                continue
            for p in ppfmt.saw_job(proj, o).parts:
                if p.xnc_file and p.xnc_file not in {re.sub(r" \(\d+\)$", "", x) for x in names}:
                    bad.append(f"QR «{p.xnc_file}» prisadka fayllari orasida yo'q")
        tot["xato"] += len(bad)
        print(f"{name}: arra/prisadka tayyor" + ("" if not bad else "  XATO: " + "; ".join(bad[:4])))
    print(dict(tot))


if __name__ == "__main__":
    main()
