"""SCM WinCut — zip: `<buyurtma>/<asos>.NNN` (har kesish kartasi uchun INI uslubidagi fayl).

Tavsif: docs/mebelix/postprocessors/scm-wincut.md. Kesish daraxti MaestroCut bilan bir xil (`Y → X → U → V`, trimlar
`RY` / `RX`), lekin `P` / `F` qatorlari yo'q — o'rniga `U*` / `V*` belgi qatorlari: bir ota ichida birinchi bo'lmagan va
bolalari bor birinchi kesim oldidan. `[Riferimenti]` — kesim → etiketkalar (MaestroCut `EtiID` kabi), `AltPacco` =
listlar soni × qalinlik.

`[Dati]` 31 maydon: 13–28-maydonlar (namunada bo'sh) — BIZNING «Дополнительные данные для этикеток» jadvali qiymatlari
(tartib bo'yicha; standart jadval bo'sh → bo'sh maydonlar). 31-maydon (boshqa dasturning etiketka blobi) yozilmaydi (bo'sh).
"""
from __future__ import annotations

from . import SawJob, register
from . import _saw_bsf as B
from .scm_maestrocut import Pattern, patterns, rest_part_id

KEY = "scm_wincut"
ENC = "cp1251"
CRLF = "\r\n"
ZERO = "0.0000"


def _f(v) -> str:
    return B.text(v).replace(",", " ").replace("\r", " ").replace("\n", " ")


def pattern_file(job: SawJob, P: B.Parts, L: B.Labels, pat: Pattern) -> str:
    rows = pat.rows(marks=True)
    out = ["[Intestazione]", f"Descrizione={job.material_name}", f"TipoMateriale={job.material_code}",
           f"Lunghezza={B.ival(pat.lung)}", f"Larghezza={B.ival(pat.larg)}", f"Spessore={B.ival(job.thickness)}",
           f"AltPacco={B.ival(pat.copies * job.thickness)}", f"VelRotaz={job.params.get('vel_rotaz', 3000)}",
           f"VelAvanz={job.params.get('vel_avanz', 30)}", "[Dati]", f"NumeroDati={len(pat.uids) + len(pat.rems)}"]
    cnt = pat.counts()
    thk = B.ival(job.thickness)
    for u in pat.uids:
        sp = P.saw[u]
        cl, cw = P.cut_lw(u)
        extra = [_f(v) for _n, v in L.values(u)][:16]
        f = ["", "", str(cnt.get(u, 0)), "jobName", "jobDesc", str(u), B.ival(cl), B.ival(cw), thk, "", "0", str(sp.qty),
             *extra, *[""] * (16 - len(extra)), "PART", str(P.index.get(u, 0)), ""]
        out.append(f"{pat.part_id[u]}=" + ",".join(f))
    rems = B.remnants(pat.m)
    for n in pat.rems:
        o = rems.get(n) or {}
        f = ["", "", "1", "jobName", "jobDesc", str(rest_part_id(P, n)), B.ival(o.get("length") or 0),
             B.ival(o.get("width") or 0), thk, "", "0", "1", *[""] * 16, "REST", "1", ""]
        out.append(f"{pat.rest_id[n]}=" + ",".join(f))
    out.append("[Righe]")
    for k, (t, dim, rip, _e) in enumerate(rows, 1):
        out.append(f"{k}={t},{ZERO if dim is None else B.ival(dim)},{rip},{ZERO},{ZERO},{ZERO},{ZERO}")
    out.append(f"NumeroRighe={len(rows)}")
    out.append("[Riferimenti]")
    for k, (_t, _d, _r, e) in enumerate(rows, 1):
        out.append(f"{k}={e}")
    return CRLF.join(out) + CRLF


def files(job: SawJob) -> dict[str, bytes]:
    stem = B.file_stem(job)
    folder = B.order_name(job).replace("/", "_").replace("\\", "_")
    P, L = B.Parts(job), B.Labels(job, KEY)
    out = {}
    for i, p in enumerate(patterns(job, P), 1):
        out[f"{folder}/{stem}.{i:03d}"] = pattern_file(job, P, L, p).encode(ENC, "replace")
    return out


@register(KEY, "SCM WinCut", "saw", "zip",
          note="[Dati] ning 31-maydoni (boshqa dasturning etiketka blobi) yozilmaydi; 13–28-maydonlar — «Дополнительные данные "
               "для этикеток» jadvalidan. 5-darajadan chuqur kesim belgilari namunasiz — taxminiy.")
def gen(job: SawJob):
    f = files(job)
    return [(f"{B.file_stem(job)}.zip", B.make_zip(list(f.items())))]
