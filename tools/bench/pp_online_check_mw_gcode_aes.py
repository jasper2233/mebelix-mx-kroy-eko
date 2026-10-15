"""Masterwood MW310, «G CODE», AES Sirius generatorlari ↔ onlayn parallel sinov namunalari (bayt-ma-bayt).

`<ONLINE>/loyiha.project` BIZNING importer bilan o'qiladi, har XNC operatsiyasi `ppfmt.drill_job` → stanok moduli (fn yoki
batch) → fayl; `<ONLINE>/yangi_formatlar/{mw310,gcode,aes_sirius_one}.zip` dagi fayllar bilan solishtiriladi. Asboblar jadvali
(namunalar olingandagi raqamlar 1…15) `job.params["tools"]` orqali beriladi. Solishtirishdan oldin faqat dastur nomi
tenglashtiriladi (G CODE 1-qatoridagi izoh). ONLINE papkasi: `--online` yoki `MEBELIX_PP_ONLINE`; bo'lmasa — o'tkaziladi.

    cd tools/bench && python pp_online_check_mw_gcode_aes.py [--format mw310,gcode] [--show 3]
"""
from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import tooling  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ONLINE = os.environ.get("MEBELIX_PP_ONLINE") or os.path.join(ROOT, "post prtsessorlar", "ONLINE_2026-10-04")
FORMATS = {                      # kalit → (zip, faqat shu XNC kodlari yoki None — hammasi)
    "mw310": ("mw310.zip", None),
    "gcode": ("gcode.zip", None),
    "aes_sirius": ("aes_sirius_one.zip", {"100602_01_001"}),
}
# Namunalar olingandagi «Инструменты» jadvali (qatorlar tartibida 1…15)
TOOL_ROWS = (("drill", "front", 3), ("through", "front", 8), ("drill", "front", 8), ("drill", "front", 10),
             ("drill", "front", 15), ("drill", "front", 35), ("drill", "left", 4.5), ("drill", "left", 8),
             ("drill", "right", 4.5), ("drill", "right", 8), ("drill", "top", 4.5), ("drill", "top", 8),
             ("drill", "bottom", 4.5), ("drill", "bottom", 8), ("mill", "front", 8))
TOOLS = {tooling.tool_key(k, p, d): str(i) for i, (k, p, d) in enumerate(TOOL_ROWS, 1)}
TITLE = re.compile(rb"\(generated code in [^)]*\)")


def normalize(key: str, real: bytes, gen: bytes) -> bytes:
    """Namunadagi dastur nomini biznikiga tenglashtirish (ma'lumotga bog'liq emas)."""
    if key == "gcode":
        m = TITLE.search(gen)
        if m:
            real = TITLE.sub(lambda _m: m.group(0), real, count=1)
    return real


def generate(key: str, project, only) -> dict[str, bytes]:
    fmt = ppfmt.load_all()[key]
    jobs = []
    for o in project.operations:
        if o.type == OpType.XNC and o.xnc and (only is None or o.code in only):
            j = ppfmt.drill_job(project, o, key)
            j.params = dict(j.params, tools=dict(TOOLS))
            jobs.append(j)
    files = fmt.batch(jobs, project) if fmt.batch else [f for j in jobs for f in fmt.fn(j)]
    return dict(ppfmt._dedupe(files))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", default=",".join(FORMATS))
    ap.add_argument("--online", default=ONLINE)
    ap.add_argument("--show", type=int, default=3)
    a = ap.parse_args()
    pf = os.path.join(a.online, "loyiha.project")
    if not os.path.exists(pf):
        print(f"ONLINE papkasi topilmadi ({a.online}) — o'tkazildi")
        return 0
    with open(pf, "rb") as f:
        project, _w = import_project(f.read(), os.path.basename(pf))
    bad = 0
    for key in [k for k in a.format.split(",") if k]:
        zname, only = FORMATS[key]
        zpath = os.path.join(a.online, "yangi_formatlar", zname)
        if not os.path.exists(zpath):
            print(f"{key:11s} namuna yo'q ({zname}) — o'tkazildi")
            continue
        with zipfile.ZipFile(zpath) as z:
            real = {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}
        try:
            gen = generate(key, project, only)
        except ValueError as e:
            print(f"{key:11s} XATO: {e}")
            bad += 1
            continue
        same = diff = missing = shown = 0
        for name, data in real.items():
            g = gen.get(name)
            if g is None:
                missing += 1
                continue
            data = normalize(key, data, g)
            if g == data:
                same += 1
                continue
            diff += 1
            if shown < a.show:
                shown += 1
                ra, ga = data.decode("latin-1").split("\r\n"), g.decode("latin-1").split("\r\n")
                dl = [x for x in difflib.unified_diff(ra, ga, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
                print(f"  {key} {name}: {len(dl)} qator farq")
                for x in dl[:12]:
                    print("      " + x[:160])
        extra = len([nm for nm in gen if nm not in real])
        bad += diff + missing + extra
        print(f"{key:11s} bir xil {same}/{len(real)} | farqli {diff} | yo'q {missing} | ortiqcha {extra}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
