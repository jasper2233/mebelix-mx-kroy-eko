"""Postprotsessorlar ↔ onlayn tizim: AYNAN BIR XIL kroy va loyihada bayt-ma-bayt solishtiruv.

Onlayn tizimda loyiha kesilib, har stanok uchun fayl yuklab olinadi (`<papka>/arra/<kalit>__*`, `<papka>/xnc/<kalit>__*`) va
loyiha `.project` sifatida eksport qilinadi. MX: loyiha importi + onlayn kroy natijasi (`data` bloki → `pp_online_cut`) →
o'rnatilgan generator → fayllar onlayn fayllar bilan solishtiriladi. Shu bilan optimizator farqi chiqarib tashlanadi —
faqat stanok formati tekshiriladi.

    python pp_online_same_cut.py [--dir PAPKA] [--op 1] [--only kalit1,kalit2] [--show 3] [--xnc]
"""
from __future__ import annotations

import argparse
import difflib
import glob
import io
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "backend"))
sys.path.insert(0, HERE)
from app.models import OpType  # noqa: E402
from app.plugins.legacy_project import import_project  # noqa: E402
from app.services import calc, ppfmt  # noqa: E402
import pp_online_cut  # noqa: E402

DEFAULT_DIR = r"D:/cloude giblab jasur/post prtsessorlar/ONLINE_2026-10-24"
FORBIDDEN = b"giblab"


def unpack(name: str, data: bytes) -> dict[str, bytes]:
    if data[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(data))
        out: dict[str, bytes] = {}
        for i in z.infolist():
            if i.is_dir():
                continue
            out.update({f"{i.filename}/{k}" if k != i.filename else k: v for k, v in unpack(i.filename, z.read(i)).items()})
        return out
    return {name: data}


def load_project(folder: str):
    path = glob.glob(os.path.join(folder, "*.project"))[0]
    return load_project_file(os.path.basename(path), open(path, "rb").read())


def load_project_file(name: str, data: bytes):
    """`.project` baytlari → loyiha + fayldagi tayyor kroy (`data` bloki)."""
    proj, _w = import_project(data, name)
    root = ET.fromstring(data)
    if not root.get("name"):                      # nomsiz loyiha — onlayn tizim «Без имени» deb yozadi (MX fayl nomini oladi)
        proj.name = "Без имени"
    xops = list(root.iter("operation"))
    for i, op in enumerate(proj.operations):
        if op.type == OpType.CS and xops[i].get("data"):
            op.result = pp_online_cut.to_result(proj, op, xops[i].get("data"))
            calc._account(proj, op)                # ИК / Ост (usedCount) — oddiy kroydan keyingidek
    return proj


def pair(ref: dict[str, bytes], ours: dict[str, bytes]) -> list[tuple[str, str | None]]:
    """Fayllarni moslash: avval bir xil nom, keyin bir xil kengaytma + tartib."""
    left = dict(ours)
    out = []
    for name in sorted(ref):
        base = name.rsplit("/", 1)[-1]
        hit = next((k for k in left if k.rsplit("/", 1)[-1] == base), None)
        if hit is None:
            ext = os.path.splitext(base)[1].lower()
            hit = next((k for k in sorted(left) if os.path.splitext(k)[1].lower() == ext), None)
        out.append((name, hit))
        if hit:
            left.pop(hit)
    out += [("", k) for k in sorted(left)]
    return out


# --norm: tizimga bog'liq, stanok o'qishiga ta'sirsiz qiymatlar niqoblanadi (sana / vaqt, dastur nomi, vaqtdan olingan
# raqamlar, GUID). Qolgan har farq — format farqi.
NORM = [
    (rb"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?", b"<DT>"), (rb"\d{2}\.\d{2}\.\d{4}( \d{2}:\d{2}(:\d{2})?)?", b"<D>"),
    (rb"\d{4}-\d{2}-\d{2}", b"<D>"), (rb"\d{2}:\d{2}:\d{2}", b"<T>"),
    (rb"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", b"<GUID>"),
    (rb"\b[0-9a-f]{4}0000[0-9a-f]{12}\b", b"<XID>"),           # Shelling eksport ID (tasodifiy + vaqt)
    (rb"(?<=,)\d{2}:\d{2}(?=,)", b"<HM>"),                     # AES BSL2 soat
    (rb"\d{14,}", b"<NUM>"), (rb"(?i)giblab|mebelix kroy|mebelix", b"<PROG>"),
]


def norm(d: bytes) -> bytes:
    for pat, rep in NORM:
        d = re.sub(pat, rep, d)
    return d


def text(d: bytes) -> list[str] | None:
    for enc in ("utf-8", "cp1251"):
        try:
            t = d.decode(enc)
        except UnicodeDecodeError:
            continue
        if sum(ch < " " and ch not in "\r\n\t" for ch in t[:4000]) < 5:
            return t.splitlines()
    return None


def first_diff(a: bytes, b: bytes, show: int) -> str:
    la, lb = text(a), text(b)
    if la is not None and lb is not None:
        d = [x for x in difflib.unified_diff(la, lb, "onlayn", "mx", n=0, lineterm="") if not x.startswith(("---", "+++"))]
        return "\n      ".join(x[:240] for x in d[: show * 3])
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    return f"bayt {i}: onlayn {a[i:i + 16].hex()} | mx {b[i:i + 16].hex()} (uzunlik {len(a)} / {len(b)})"


# Ataylab yozilmaydigan fayllar (onlayn tizimning etiketka rasmlari / ichki ma'lumoti — CLAUDE.md 14-qoida)
SKIP = re.compile(r"(?i)(\.zpl|\.emf|etikett\.bin|giblabdata[^/]*\.xml)$")


def generate(kind: str, key: str, proj, op) -> dict[str, bytes]:
    reg = ppfmt.load_all()
    fmt = reg[key]
    files: list = []
    if kind.startswith("arra"):
        files = fmt.fn(ppfmt.saw_job(proj, op))
    else:
        jobs = [ppfmt.drill_job(proj, o) for o in proj.operations if o.type == OpType.XNC]
        files = fmt.batch(jobs, proj) if fmt.batch else [f for j in jobs for f in fmt.fn(j)]
    ours: dict[str, bytes] = {}
    for n, data in files:
        ours.update(unpack(n, data))
    return ours


def run(kind: str, folder: str, proj, op_no: int, only: set[str], show: int, nm: bool = False) -> dict:
    op = [o for o in proj.operations][op_no - 1]
    reg = ppfmt.load_all()
    res = {}
    for f in sorted(glob.glob(os.path.join(folder, kind, "*__*"))):
        key = os.path.basename(f).split("__")[0]
        if only and key not in only:
            continue
        if key not in reg:
            res[key] = ("generator yo'q", 0, 0)
            print(f"[{key}] MX da generator yo'q")
            continue
        ref = unpack(os.path.basename(f), open(f, "rb").read())
        skipped = [k for k in ref if SKIP.search(k)]
        ref = {k: v for k, v in ref.items() if k not in skipped}
        try:
            ours = generate(kind, key, proj, op)
        except Exception as e:  # noqa: BLE001 — format xatosi hisobotga
            print(f"[{key}] MX XATO: {e}")
            res[key] = ("xato", 0, len(ref))
            continue
        bad = [n for n, d in ours.items() if FORBIDDEN in d.lower() or FORBIDDEN in n.lower().encode()]
        if nm:
            ref = {k: norm(v) for k, v in ref.items()}
            ours = {k: norm(v) for k, v in ours.items()}
        same = 0
        lines = []
        for rn, on in pair(ref, ours):
            a, b = ref.get(rn, b""), ours.get(on, b"") if on else b""
            if rn and on and a == b:
                same += 1
            else:
                lines.append(f"   {rn or '—'} ↔ {on or '—'}: {first_diff(a, b, show) if rn and on else 'juft yo‘q'}")
        print(f"[{key}] {same}/{len(ref)} bir xil" + (f"  (MX fayllari: {len(ours)})" if len(ours) != len(ref) else "")
              + (f"  (yozilmaydigan: {len(skipped)})" if skipped else "")
              + (f"  ⚠ 'giblab' so'zi: {bad}" if bad else ""))
        for ln in lines[:show]:
            print(ln)
        res[key] = (same, len(ref), len(ours))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--op", type=int, default=1)
    ap.add_argument("--only", default="")
    ap.add_argument("--show", type=int, default=3)
    ap.add_argument("--norm", action="store_true")
    ap.add_argument("--kind", default="arra")             # arra / arra_op3 / xnc — namuna papkasidagi kichik papka
    a = ap.parse_args()
    if not os.path.isdir(a.dir):
        print("namuna papkasi yo'q — o'tkazib yuborildi")
        return
    proj = load_project(a.dir)
    only = {x for x in a.only.split(",") if x}
    run(a.kind, a.dir, proj, a.op, only, a.show, a.norm)


if __name__ == "__main__":
    main()
