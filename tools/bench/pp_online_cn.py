"""(CN) nesting postprotsessorlari ↔ onlayn tizim fayllari: bayt-ma-bayt (yo'llar namunadan olinadi).

Onlayn tizim o'z nesting yo'lini (qo'shni detallar orasidagi umumiy kesimlar) chiqaradi, MX esa har detal konturini —
shuning uchun yo'llar NCStudio namunasidan o'qiladi va har format generatori shu yo'llardan yozgan fayl onlayn fayl bilan
solishtiriladi (fayl sintaksisi). NCStudio 1-qatori (dastur nomi) solishtirilmaydi.

    python pp_online_cn.py [--dir PAPKA]
Namunalar: `<PAPKA>/cn_<format>__*.zip` (1-variant: «Выступ снизу» 0, 1 list) va `cn2_*` (0.5, 2 list).
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
from app.services import ppfmt  # noqa: E402
from app.services.ppfmt import cn_nest as C  # noqa: E402

DEFAULT_DIR = r"D:/cloude giblab jasur/post prtsessorlar/ONLINE_2026-10-24"
FORMATS = {"ncstudio": "cn_ncstudio", "kdt_gcode": "cn_kdt_gcode", "woodwop": "cn_woodwop", "tpa": "cn_tpa",
           "biesseworks": "cn_biesseworks"}


def unzip(path: str) -> dict[str, bytes]:
    z = zipfile.ZipFile(path)
    return {n: z.read(n) for n in z.namelist()}


def paths_from_ncstudio(text: str) -> list[list[tuple[float, float]]]:
    out, cur, x, y = [], None, 0.0, 0.0
    for ln in text.splitlines():
        m = re.match(r"G0 X([-\d.]+) Y([-\d.]+)", ln)
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            cur = [(x, y)]
            out.append(cur)
            continue
        if ln.startswith("G1") and cur is not None:
            mx, my = re.search(r"X([-\d.]+)", ln), re.search(r"Y([-\d.]+)", ln)
            x = float(mx.group(1)) if mx else x
            y = float(my.group(1)) if my else y
            cur.append((x, y))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=DEFAULT_DIR)
    a = ap.parse_args()
    if not glob.glob(os.path.join(a.dir, "cn_ncstudio__*.zip")):
        print("namuna yo'q — o'tkazib yuborildi")
        return
    reg = ppfmt.load_all()
    total = same = 0
    for var, overhang in (("cn", 0.0), ("cn2", 0.5)):
        nc = unzip(glob.glob(os.path.join(a.dir, f"{var}_ncstudio__*.zip"))[0])
        maps = [C.NestMap(index=int(re.search(r"F(\d+)", n).group(1)), length=2750, width=1830,
                          paths=paths_from_ncstudio(d.decode("cp1251"))) for n, d in sorted(nc.items())]
        for short, key in FORMATS.items():
            ref = unzip(glob.glob(os.path.join(a.dir, f"{var}_{short}__*.zip"))[0])
            tool = C.NestTool(rpm=3000 if short == "ncstudio" else 18000, feed_z=100 if short == "ncstudio" else 3000,
                              feed_xy=5000)
            job = C.NestJob(thickness=18, overhang=overhang, tool=tool, maps=maps)
            ours = dict(reg[key].fn(job))
            for n, d in sorted(ref.items()):
                o = ours.get(n, b"")
                if short == "ncstudio":                   # 1-qator — dastur nomi
                    d, o = d.split(b"\r\n", 1)[1], o.split(b"\r\n", 1)[1] if o else b""
                ok = d == o
                total += 1
                same += ok
                if not ok:
                    la, lb = d.decode("cp1251").splitlines(), o.decode("cp1251").splitlines()
                    i = next((i for i, (u, v) in enumerate(zip(la, lb)) if u != v), min(len(la), len(lb)))
                    print(f"  [{var} {short}] {n}: qator {i + 1}: onlayn {la[i] if i < len(la) else '—'!r} / mx {lb[i] if i < len(lb) else '—'!r}")
            print(f"[{var} {short}] {sum(1 for n in ref if True)} fayl")
    print(f"BIR XIL: {same}/{total}")


if __name__ == "__main__":
    main()
