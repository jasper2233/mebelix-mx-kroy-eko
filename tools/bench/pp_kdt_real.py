"""KDT arra (pilniy markaz, `kdt_presize_xml`) va KDT prisadka fayllari ↔ korxonada stanokda REAL ishlayotgan fayllar.

Papka (repoga kirmaydi): `post/` — `pilniy sentr/<N> <MIJOZ>.zip`, `prisadka/<MIJOZ>.zip`, `project 10 ta.zip` (shu fayllarni bergan
loyihalar). Har loyiha: import + fayldagi tayyor kroy (`data` bloki → `pp_online_cut`, ya'ni AYNAN o'sha kartalar) → MX generatori →
fayllar mantiqan va bayt bo'yicha solishtiriladi. `.emf` (etiketka rasmlari) solishtirilmaydi.

    python pp_kdt_real.py [--src PAPKA] [--saw-key kdt_presize_xml] [--drill-key kdt_panel] [--show 3] [--only 3189]
"""
from __future__ import annotations

import argparse
import difflib
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
from app.services import ppfmt  # noqa: E402
from pp_online_same_cut import load_project_file, unpack  # noqa: E402

SRC = r"D:/cloude giblab jasur/post"


def zip_files(path: str) -> dict[str, bytes]:
    out = {}
    with zipfile.ZipFile(path) as z:
        for i in z.infolist():
            if not i.is_dir():
                out[i.filename] = z.read(i)
    return out


def projects(src: str) -> dict[str, tuple[str, bytes]]:
    """loyiha raqami → (nom, .project baytlari)."""
    out = {}
    for n, d in zip_files(os.path.join(src, "project 10 ta.zip")).items():
        if n.endswith(".project"):
            b = os.path.basename(n)
            out[b.split("_")[0]] = (b, d)
    return out


def pair_sources(src: str, projs: dict) -> list[tuple[str, str | None, str | None]]:
    """Arra zip — tartib raqami bo'yicha («1 JAXONGIR» … «10 ABDULATIF», loyiha raqami o'sishida); prisadka zip — arra zip
    nomidan raqam olib tashlangani («JAXONGIR 2»), «1 JAXONGIR.zip» kabi raqamli nom ham. Arra zip bilan bir xil (nusxa)
    prisadka zip hisobga olinmaydi."""
    nums = sorted(projs)
    sd, dd = os.path.join(src, "pilniy sentr"), os.path.join(src, "prisadka")
    saws = {int(f.split()[0]): f for f in os.listdir(sd) if f.endswith(".zip") and f.split()[0].isdigit()}
    drills = {f: os.path.join(dd, f) for f in os.listdir(dd) if f.endswith(".zip")}
    out = []
    for i, n in enumerate(nums, 1):
        sf = saws.get(i)
        dz = None
        if sf:
            rest = sf.split(" ", 1)[1]
            for cand in (sf, rest):
                if cand in drills and open(drills[cand], "rb").read() != open(os.path.join(sd, sf), "rb").read():
                    dz = drills[cand]
        out.append((n, os.path.join(sd, sf) if sf else None, dz))
    return out


def show_diff(a: bytes, b: bytes, k: int) -> str:
    ta, tb = a.decode("utf-8", "replace"), b.decode("utf-8", "replace")
    if "\n" not in ta.strip():                                  # bir qatorli XML — teg bo'yicha bo'lamiz
        ta, tb = ta.replace("><", ">\n<"), tb.replace("><", ">\n<")
    d = [x for x in difflib.unified_diff(ta.splitlines(), tb.splitlines(), "real", "mx", n=0, lineterm="")
         if not x.startswith(("---", "+++"))]
    return "\n        ".join(x[:200] for x in d[: k * 4])


def gen(key: str, proj, op=None) -> dict[str, bytes]:
    fmt = ppfmt.load_all()[key]
    if op is not None:
        files = fmt.fn(ppfmt.saw_job(proj, op))
    else:
        jobs = [ppfmt.drill_job(proj, o) for o in proj.operations if o.type == OpType.XNC]
        files = fmt.batch(jobs, proj) if fmt.batch else [f for j in jobs for f in fmt.fn(j)]
    out = {}
    for n, d in files:
        out.update(unpack(n, d))
    return out


def lf(d: bytes) -> bytes:
    return d.replace(b"\r\n", b"\n")


def canon_saw(d: bytes) -> list[str]:
    """Arra XML ning MANTIQIY ko'rinishi: kesish daraxti (o'lcham, koordinata, qatlam, torsovka, kesim, tur, detal kodi) va
    detallar ro'yxati. Ichki `id` lar paydo bo'lish tartibidagi raqamga, qoldiq kodi `O*` ga keltiriladi; atribut tartibi,
    qatorlar, `print_code`, list `code` hisobga olinmaydi (ular alohida tekshiriladi)."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(d)
    ids: dict[str, int] = {"0": 0}

    def cid(v: str) -> int:
        return ids.setdefault(v, len(ids))
    # detal kodi — onlayn tizimda eksport paytidagi ichki raqam: o'lcham bilan almashtiriladi
    dims = {c.get("code"): f"{c.get('l')}x{c.get('w')}" for pn in root if pn.tag == "parts" for c in pn}

    def code(c) -> str:
        v = c.get("code", "")
        return "O*" if re.match(r"^O\d+$", v) else dims.get(v, v)
    out = []
    for pn in root:
        if pn.tag == "parts":
            for c in pn:
                a = dict(c.attrib)
                a["code"] = code(c)
                out.append("PART " + " ".join(f"{k}={a[k]}" for k in sorted(a)))
            continue
        a = {k: v for k, v in pn.attrib.items() if k != "code"}
        out.append(f"{pn.tag} " + " ".join(f"{k}={a[k]}" for k in sorted(a)))
        for no in pn:
            for c in no:
                cid(c.get("id"))
        for no in pn:
            a = dict(no.attrib)
            a["id"] = str(cid(a["id"]))
            # print_code: bir xil o'lchamli detallar o'rin almashishi mumkin — panel bo'yicha (o'lcham, raqam) to'plami alohida
            kids = [f"[cut={c.get('cut')} type={c.get('type')} id={cid(c.get('id'))} code={code(c)}]" for c in no]
            out.append("  no " + " ".join(f"{k}={a[k]}" for k in sorted(a) if k != "id") + f" ref={a['id']} " + "".join(kids))
        pcs = sorted(f"{code(c)}#{c.get('print_code', '')}" for no in pn for c in no if c.get("type") in ("1", "3"))
        out.append("  print_code " + " ".join(pcs))
    return out


def panel_parts(d: bytes) -> list[str]:
    """Har karta (panel) dagi detallar to'plami (o'lcham bo'yicha) — kroy bir xilmi, tezkor tekshiruv."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(d)
    dims = {c.get("code"): "x".join(sorted([c.get("l"), c.get("w")])) for pn in root if pn.tag == "parts" for c in pn}
    out = []
    for pn in root:
        if pn.tag != "parts":
            first = next(iter(pn), None)                         # 1-daraja kesimlar (qoldiq o'lchami bilan) — kroy kaliti
            lvl1 = sorted(c.get("cut") for c in first) if first is not None else []
            out.append(pn.get("num") + ":" + ",".join(lvl1) + "|" + ",".join(sorted(
                dims.get(c.get("code"), "?") for no in pn for c in no if c.get("type") == "1")))
    return sorted(out)


def base(n: str) -> str:
    return os.path.basename(n).lower()


def mat_key(n: str, materials: list[str]) -> str:
    """Arra fayli → material nomi (fayl nomidagi buyurtma nomi har xil: «JAXONGIR 31 88 …» / «3188_jahongir_…»)."""
    from app.services.ppfmt._saw_giben import translit
    b = re.sub(r"[\s_]+", " ", translit(os.path.splitext(os.path.basename(n))[0]).lower()).strip()
    for m in sorted(materials, key=len, reverse=True):
        mm = re.sub(r"[\s_]+", " ", translit(m).lower()).strip()
        if b.endswith(mm):
            return mm
    return b


def panel_key(d: bytes) -> str:
    m = re.search(rb"<PanelName>(.*?)</PanelName>", d)
    dims = re.findall(rb"<Panel(?:Length|Width|Thickness)>(.*?)</Panel", d)
    return ((m.group(1) if m else b"?") + b"|" + b"x".join(dims)).decode("utf-8", "replace")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--saw-key", default="kdt_presize_xml")
    ap.add_argument("--drill-key", default="kdt_panel")
    ap.add_argument("--show", type=int, default=2)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    projs = projects(a.src)
    tot = Counter()
    for num, saw_zip, drill_zip in pair_sources(a.src, projs):
        if a.only and num not in a.only.split(","):
            continue
        name, data = projs[num]
        proj = load_project_file(name, data)
        print(f"\n=== {name}")
        # ---- arra: har CS operatsiyasi — bitta XML
        if saw_zip:
            ref = {k: v for k, v in zip_files(saw_zip).items() if k.lower().endswith(".xml")}
            ours = {}
            for op in proj.operations:
                if op.type == OpType.CS and op.result and op.result.maps:
                    ours.update({k: v for k, v in gen(a.saw_key, proj, op).items() if k.lower().endswith(".xml")})
            mats = [o.name for o in proj.operations if o.type == OpType.CS]
            same = 0
            for rn, rv in sorted(ref.items()):
                on = next((k for k in ours if mat_key(k, mats) == mat_key(rn, mats)), None)
                tot["saw_ref"] += 1
                if on and ours[on] == rv:
                    same += 1
                    tot["saw_same"] += 1
                    continue
                if on and canon_saw(ours[on]) == canon_saw(rv):
                    tot["saw_logic"] += 1
                    print(f"  ARRA {mat_key(rn, mats)}: mantiqan BIR XIL (faqat yozilish shakli farq qiladi)")
                    continue
                if on and panel_parts(ours[on]) != panel_parts(rv):
                    tot["saw_othercut"] += 1
                    print(f"  ARRA {mat_key(rn, mats)}: kartalardagi detallar boshqacha — .project dagi kroy arra faylidan keyin "
                          f"o'zgargan (solishtirib bo'lmaydi)")
                    continue
                print(f"  ARRA {base(rn)} ↔ {base(on) if on else '— (MX da yo‘q)'}: MANTIQIY FARQ")
                if on:
                    d = [x for x in difflib.unified_diff(canon_saw(rv), canon_saw(ours[on]), "real", "mx", n=0, lineterm="")
                         if not x.startswith(("---", "+++"))]
                    print("        " + "\n        ".join(x[:220] for x in d[: a.show * 4]))
            extra = [base(k) for k in ours if not any(mat_key(k, mats) == mat_key(r, mats) for r in ref)]
            print(f"  arra: {same}/{len(ref)} bir xil" + (f"; MX ortiqcha: {extra}" if extra else ""))
        # ---- prisadka: har XNC — bitta XML
        if drill_zip:
            ref = {k: v for k, v in zip_files(drill_zip).items() if k.lower().endswith(".xml")}
            ours = gen(a.drill_key, proj)
            same = 0
            shown = 0
            pool = {}
            for k in ours:
                pool.setdefault(panel_key(ours[k]), []).append(k)
            for rn, rv in sorted(ref.items()):
                cand = pool.get(panel_key(rv)) or []
                on = next((k for k in cand if lf(ours[k]) == lf(rv)), cand[0] if cand else None)
                if on:
                    cand.remove(on)
                tot["drill_ref"] += 1
                if on and ours[on].replace(b"\r\n", b"\n") == rv.replace(b"\r\n", b"\n"):
                    same += 1
                    tot["drill_same"] += 1
                    continue
                if shown < a.show:
                    shown += 1
                    print(f"  PRISADKA {base(rn)} ↔ {base(on) if on else '— (MX da yo‘q)'}")
                    if on:
                        print("        " + show_diff(rv, ours[on], a.show))
            extra = [base(k) for v in pool.values() for k in v]
            print(f"  prisadka: {same}/{len(ref)} bir xil (MX fayllari {len(ours)})" + (f"; MX ortiqcha: {extra[:5]}" if extra else ""))
        else:
            print("  prisadka: namuna yo'q")
    print(f"\nJAMI arra {tot['saw_same']}/{tot['saw_ref']} bayt, mantiqan {tot['saw_same'] + tot['saw_logic']}/{tot['saw_ref']}, boshqa kroy {tot['saw_othercut']}; prisadka {tot['drill_same']}/{tot['drill_ref']}")


if __name__ == "__main__":
    main()
