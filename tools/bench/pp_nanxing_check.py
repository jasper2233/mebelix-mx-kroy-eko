"""Nanxing SyntecCad (.scx): korxona loyihasi BIZNING importer bilan o'qiladi, har XNC operatsiyasi → .scx, stanok qabul qilgan
namuna zip'dagi fayl bilan bayt-ma-bayt solishtiriladi (`Root@Cad` dan tashqari).

    python pp_nanxing_check.py "<loyiha>.project" "<namuna>.zip"

Fayllar korxonaniki — repoga qo'shilmaydi (2026-10-22 namunasi: 8 / 8 bir xil)."""
from __future__ import annotations

import difflib
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402


def main() -> int:
    proj, sample = sys.argv[1], sys.argv[2]
    with open(proj, "rb") as f:
        project, _w = import_project(f.read(), os.path.basename(proj))
    with zipfile.ZipFile(sample) as z:
        ref = {os.path.basename(n): z.read(n) for n in z.namelist() if n.lower().endswith(".scx")}
    fn = ppfmt.load_all()["nanxing_syntec"].fn
    ok = total = 0
    for op in project.operations:
        if op.type != OpType.XNC:
            continue
        (name, gen), = fn(ppfmt.drill_job(project, op))
        total += 1
        real = ref.get(name)
        if real is None:
            print("namunada yo'q:", name)
            continue
        real = re.sub(rb'<Root Cad="[^"]*"', b'<Root Cad="MebeliX Kroy"', real, count=1)
        if real == gen:
            ok += 1
            continue
        print("FARQ:", name)
        sys.stdout.writelines(list(difflib.unified_diff(real.decode("utf-8", "replace").splitlines(True),
                                                        gen.decode("utf-8", "replace").splitlines(True), n=0))[:20])
    print(f"{ok} / {total} bayt-ma-bayt")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
