"""IMA ImaWop (.FMC) va Holz-Her NC-HOPS (.hop) generatorlari ↔ onlayn namunalar: bayt-ma-bayt solishtirish.

`<ONLINE>/loyiha.project` BIZNING importer bilan o'qiladi, har XNC operatsiyasi `ppfmt.drill_job` → format moduli → fayl,
`<ONLINE>/yangi_formatlar/<kalit>.zip` dagi fayl bilan solishtiriladi. Asboblar jadvali namuna olingan paytdagidek
(TOOLS). Ikki rejim: «standart» (generator qanday yozsa) va «namunadagidek» (namunadagi ikki xato takrorlanadi:
ImaWop `MPY = MPX`, NC-HOPS DrillTop/Bottom Y teskari emas) — qolgan hamma narsa bayt-ma-bayt mosligini ko'rsatadi.
Dastur nomi namunada bo'lsa «MebeliX Kroy» ga tenglashtiriladi (bu ikki formatda uchramaydi). Papka yo'q bo'lsa — o'tkaziladi.

    cd tools/bench && python pp_online_check_ima_hops.py [--online DIR] [--show 3]
    (yoki muhit o'zgaruvchisi MEBELIX_PP_ONLINE)
"""
from __future__ import annotations

import argparse
import difflib
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ONLINE = os.environ.get("MEBELIX_PP_ONLINE") or os.path.join(ROOT, "post prtsessorlar", "ONLINE_2026-10-04")
# Namuna olingan paytdagi «Инструменты» jadvali (kalit — ppfmt.tooling.tool_key)
DRILLS = [("front", d) for d in (3, 8, 10, 15, 35)] + [(p, d) for p in ("left", "right", "top", "bottom") for d in (4.5, 8)]
TOOLS = {
    "ima_wop": {"mill:front:8": "MILL8"},                                    # parmalar: diametr bo'yicha (nomsiz)
    "holzher_nchops": {"mill:front:8": "8", **{f"drill:{p}:{d}": "-1" for p, d in DRILLS}},
}
SAMPLE_FLAG = {"ima_wop": ("ima_wop", "MPY_AS_SAMPLE"), "holzher_nchops": ("holzher_nchops", "TB_AS_SAMPLE")}
APP_NAMES = (b"Built in GibLab", b"GibLab")


def normalize(data: bytes) -> bytes:
    for a in APP_NAMES:
        data = data.replace(a, b"MebeliX Kroy")
    return data


def generate(key: str, project, sample_mode: bool) -> dict[str, bytes]:
    import importlib

    from app.models import OpType
    from app.services import ppfmt
    fmt = ppfmt.load_all()[key]
    mod_name, flag = SAMPLE_FLAG[key]
    mod = importlib.import_module(f"app.services.ppfmt.{mod_name}")
    old = getattr(mod, flag)
    setattr(mod, flag, sample_mode)
    try:
        files = []
        for o in project.operations:
            if o.type == OpType.XNC and o.xnc:
                job = ppfmt.drill_job(project, o)
                job.params = {"tools": dict(TOOLS[key])}
                job.machine = key
                files += fmt.fn(job)
        return dict(ppfmt._dedupe(files))
    finally:
        setattr(mod, flag, old)


def compare(real: dict[str, bytes], gen: dict[str, bytes]) -> tuple[list[str], list[str], list[str], list[str]]:
    same, diff = [], []
    for name, data in sorted(real.items()):
        if name in gen:
            (same if normalize(data) == gen[name] else diff).append(name)
    return same, diff, sorted(set(real) - set(gen)), sorted(set(gen) - set(real))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--online", default=ONLINE)
    ap.add_argument("--show", type=int, default=3, help="har format uchun ko'rsatiladigan farqli fayllar soni")
    a = ap.parse_args()
    pf = os.path.join(a.online, "loyiha.project")
    if not os.path.exists(pf):
        print(f"namuna papkasi topilmadi: {a.online} — o'tkazildi")
        return 0
    from app.plugins.legacy_project import import_project
    with open(pf, "rb") as f:
        project, _w = import_project(f.read(), os.path.basename(pf))
    bad = 0
    for key in TOOLS:
        zpath = os.path.join(a.online, "yangi_formatlar", key + ".zip")
        if not os.path.exists(zpath):
            print(f"{key}: namuna zip yo'q — o'tkazildi")
            continue
        with zipfile.ZipFile(zpath) as z:
            real = {os.path.basename(i.filename): z.read(i) for i in z.infolist() if not i.is_dir()}
        for mode, label in ((False, "standart"), (True, "namunadagidek")):
            gen = generate(key, project, mode)
            same, diff, missing, extra = compare(real, gen)
            print(f"{key:15s} [{label:13s}] bir xil {len(same)}/{len(real)} | farqli {len(diff)} | yo'q {len(missing)} | "
                  f"ortiqcha {len(extra)}")
            if mode:
                bad += len(diff) + len(missing) + len(extra)
            for name in diff[:a.show]:
                ra = normalize(real[name]).decode("cp1251", "replace").split("\r\n")
                ga = gen[name].decode("cp1251", "replace").split("\r\n")
                dl = [x for x in difflib.unified_diff(ra, ga, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
                print(f"    {name}: {len(dl)} qator farq")
                for x in dl[:10]:
                    print("        " + x[:160])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
