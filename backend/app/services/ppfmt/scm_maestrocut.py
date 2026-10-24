"""SCM MaestroCut — zip: har kesish kartasi uchun `<asos>.NNN.XPrg` + partiya fayli `<asos>.XMix`.

Tavsif: docs/mebelix/postprocessors/scm-maestrocut.md. Kesish daraxti `Y → X → U → V` (toq darajalar `Larghezza` o'qida,
juftlari `Lunghezza` o'qida), preorder; trimlar `RY` (bir marta) va `RX` (har polosada) = torsovka + propil; `Rip` —
ketma-ket bir xil kesimlar (bir xil detal bo'lsa); `EtiID` — kesimdan chiqadigan bo'laklar etiketkalari, paket
qatlamlari vergul bilan. `F` — tayyor bo'lakdan keyingi belgi (Y/X/U da har biridan keyin, V da oxirgisidan keyin).

`Etichetta` maydonlari: nomi BIZNING «Дополнительные данные для этикеток» jadvalidagi qator nomiga teng atributlar
(Codice, Lunghezza, Richiesti, CodiceBordo1…4, Job, CampoN …) — jadval ifodasidan (services/expr.py); qolganlari — format
qoidasi. Yozilmaydi: boshqa dasturning etiketka bloblari bo'limi va uning nomi bilan atalgan `Header` ID atributi
(Campo64 dagi fayl ID si saqlanadi).
"""
from __future__ import annotations

import math
import uuid

from . import SawJob, register
from . import _saw_bsf as B

KEY = "scm_maestrocut"
ENC = "utf-8"                    # onlayn tizim fayli — UTF-8 (deklaratsiyasiz), 2026-10-24 tekshirildi
CRLF = "\r\n"
LEVEL = {1: "Y", 2: "X", 3: "U", 4: "V", 5: "W", 6: "Z"}     # 5–6-darajalar namunalarda yo'q (taxminiy belgi)
XMIX_DIR = "C:\\MaestroCut\\Client\\xMix\\"
INNER = (("index", "index"), ("groove", "groove"), ("drill", "drill"), ("mill", "mill"))
ETI_KEYS = (["Id", "Resto", "Codice", "Lunghezza", "Larghezza", "Richiesti", "CodiceBordo1", "CodiceBordo2", "CodiceBordo3",
             "CodiceBordo4", "Job"] + [f"Campo{n}" for n in range(1, 65)])


def lv(level: int) -> str:
    return LEVEL.get(level, f"L{level}")


class Pattern:
    """Bitta karta: kesimlar (qoldiqlar biriktirilgan), etiketkalar (detallar operatsiya tartibida, so'ng qoldiqlar)."""

    def __init__(self, job: SawJob, m, P: B.Parts):
        self.m = m
        self.copies = max(1, m.copies)
        self.axis, cuts = B.cut_tree(m)
        self.cuts = B.attach_rests(B.merge_runs(cuts, by_part=True))
        uids = sorted({c.uid for c in B.walk_cuts(self.cuts) if c.leaf and c.uid}, key=lambda u: P.index.get(u, 0))
        self.part_id = {u: i for i, u in enumerate(uids, 1)}
        rems = [n for c in B.walk_cuts(self.cuts) for n in c.rest]
        self.rest_id = {n: len(uids) + i for i, n in enumerate(rems, 1)}
        self.uids, self.rems = uids, rems
        inc = bool(getattr(job.op.cs_cut, "trim_includes_kerf", False)) if job.op.cs_cut else False
        k = 0.0 if inc else float(job.kerf or 0)
        tl, tw = float(m.trim_length or 0) + k, float(m.trim_width or 0) + k
        if self.axis == "y":                       # polosalar Y bo'ylab: Y-kesim chizig'i list uzunligi bo'ylab
            self.lung, self.larg, self.ry, self.rx = m.sheet_length, m.sheet_width, tw, tl
        else:
            self.lung, self.larg, self.ry, self.rx = m.sheet_width, m.sheet_length, tl, tw

    def eti(self, c: B.Cut, mult: int) -> str:
        s = ""
        if c.leaf and c.uid:
            s = ("(" + ",".join([str(self.part_id[c.uid])] * self.copies) + ")") * mult
        for n in c.rest:
            s += f"({self.rest_id[n]})"
        return s

    def rows(self, marks: bool = False):
        """(tur, o'lcham | None, Rip, EtiID). MaestroCut: `F` belgilari bilan (`marks=False`); WinCut: `F` o'rniga
        `U*` / `V*` qatorlari (`marks=True`). Trimlar (`RY`, `RX`) ikkalasida ham."""
        out = [("RY", self.ry, 1, "")]

        def rec(cuts, mult):
            marked = False
            for i, c in enumerate(cuts):
                m2 = mult * c.rep
                if marks and c.level >= 2 and i > 0 and c.children and not marked:
                    out.append((lv(c.level + 1) + "*", None, 0, ""))     # birinchi bo'lmagan, bolali birinchi kesim oldidan
                    marked = True
                out.append((lv(c.level), c.dim, c.rep, self.eti(c, m2)))
                if c.level == 1:
                    out.append(("RX", self.rx, 1, ""))
                if c.leaf:
                    if not marks and (c.level <= 3 or i == len(cuts) - 1):
                        out.append(("F", None, 0, ""))
                else:
                    rec(c.children, m2)
        rec(self.cuts, 1)
        return out

    def counts(self) -> dict[int, int]:
        """uid → shu kartadagi bo'laklar soni (paket qatlamlari bilan)."""
        out: dict[int, int] = {}
        for lf, mult in B.leaves_mult(self.cuts):
            if lf.uid:
                out[lf.uid] = out.get(lf.uid, 0) + mult * self.copies
        return out


def used_counts(pats: list[Pattern]) -> dict[int, int]:
    out: dict[int, int] = {}
    for p in pats:
        for u, n in p.counts().items():
            out[u] = out.get(u, 0) + n
    return out


def rest_part_id(P: B.Parts, n: int) -> int:
    """Qoldiq uchun yangi noyob ID (detal uid laridan keyin)."""
    return max(P.model, default=0) + n


def etichetta(job: SawJob, P: B.Parts, L: B.Labels, I: B.Labels, pat: Pattern, used: dict, fid: str) -> list[str]:
    order = B.order_name(job)
    d = B.project_date(job).strftime("%d.%m.%Y")
    thk = job.thickness
    out = []

    def line(a: dict) -> str:
        return "<Etichetta " + " ".join(f'{k}="{B.esc_xml(a.get(k, ""))}"' for k in ETI_KEYS) + "/>"

    for u in pat.uids:
        i = pat.part_id[u]
        sp = P.saw[u]
        l, w = P.lw(u)
        cl, cw = P.cut_lw(u)
        e = [P.edge(u, s) for s in ("top", "bottom", "left", "right")]
        pr = P.product(u)
        inner = {n: v for n, v in I.values(u)}
        a = {"Codice": order, "Lunghezza": B.n2(cl), "Larghezza": B.n2(cw), "Richiesti": str(sp.qty),
             "Job": order, "Campo1": order, "Campo3": str(u), "Campo4": B.n2(cl), "Campo5": B.n2(cw), "Campo6": B.n2(thk),
             "Campo7": job.material_code, "Campo8": "1" if sp.grain else "0", "Campo9": str(sp.qty), "Campo10": sp.name,
             "Campo19": "0", "Campo20": "sheet", "Campo26": d, "Campo28": job.material_name, "Campo29": job.material_code,
             "Campo30": str(P.prod_index.get(pr.id, "")) if pr else "", "Campo31": pr.name if pr else "",
             "Campo32": pr.code if pr else "", "Campo33": str(pr.qty) if pr else "", "Campo36": sp.code, "Campo37": sp.name,
             "Campo39": B.text(inner.get("index", "")), "Campo40": str(P.index.get(u, 0)),
             "Campo41": B.n1(l), "Campo42": B.n1(w), "Campo43": B.n1(cl), "Campo44": B.n1(cw), "Campo45": B.n1(thk),
             "Campo46": "false", "Campo47": str(sp.qty), "Campo48": str(sp.qty), "Campo49": str(used.get(u, 0)),
             "Campo58": B.text(inner.get("groove", False)) or "false",
             "Campo59": B.text(inner.get("drill", sp.has_drill)) or "false",
             "Campo60": B.text(inner.get("mill", sp.has_mill)) or "false", "Campo61": sp.xnc_face, "Campo62": sp.xnc_back}
        for k, x in enumerate(e):
            a[f"CodiceBordo{k + 1}"] = x.get("symbol", "")
            a[f"Campo{11 + k}"] = x.get("name", "")
            a[f"Campo{15 + k}"] = x.get("code", "")
            a[f"Campo{50 + 2 * k}"] = x.get("name", "")
            a[f"Campo{51 + 2 * k}"] = B.n1(x.get("thickness") or 0)
        for n, v in L.values(u):                     # bizning jadval: atribut nomi bo'yicha
            if n in ETI_KEYS:
                # qiymat qirqiladi: standart ifoda bo'sh kromkaga ' ' beradi, onlayn tizim fayli va korxona namunalarida
                # CodiceBordo="" (2026-10-24 tekshirildi; avval «" "» yozilardi)
                a[n] = B.text(v).strip()
        a.update({"Id": str(i), "Resto": "0", "Campo64": f"{fid}#{i}"})
        out.append(line(a))
    rems = B.remnants(pat.m)
    for n in pat.rems:
        i = pat.rest_id[n]
        o = rems.get(n) or {}
        ln, wd = float(o.get("length") or 0), float(o.get("width") or 0)
        a = {"Id": str(i), "Resto": "1", "Codice": order, "Lunghezza": B.n2(ln), "Larghezza": B.n2(wd), "Richiesti": "1",
             "Job": order, "Campo1": order, "Campo3": str(rest_part_id(P, n)), "Campo4": B.n2(ln), "Campo5": B.n2(wd),
             "Campo6": B.n2(thk), "Campo7": job.material_code, "Campo8": "0", "Campo9": "0", "Campo19": "1",
             "Campo20": "sheet", "Campo26": d, "Campo28": job.material_name, "Campo29": job.material_code, "Campo39": "1",
             "Campo40": "1", "Campo41": B.n1(ln), "Campo42": B.n1(wd), "Campo43": B.n1(ln), "Campo44": B.n1(wd),
             "Campo45": B.n1(thk), "Campo46": "true", "Campo47": "1", "Campo48": "1", "Campo49": "0", "Campo51": "0.0",
             "Campo53": "0.0", "Campo55": "0.0", "Campo57": "0.0", "Campo58": "false", "Campo59": "false",
             "Campo60": "false", "Campo64": f"{fid}#{i}"}
        out.append(line(a))
    return out


def pack(job: SawJob) -> int:
    t = float(job.thickness or 0)
    return max(1, int(math.floor((float(job.pack_height or 0) + 1e-6) / t))) if t > 0 else 1


def xprg(job: SawJob, P: B.Parts, L: B.Labels, I: B.Labels, pat: Pattern, used: dict, fid: str, today) -> str:
    out = [f'<SchemaDoc><Header TipoCave="1" NumFogliPacco="{pack(job)}" Descrizione="{B.esc_xml(job.material_name)}" '
           f'Spessore="{B.ival(job.thickness)}" Date="{today.strftime("%d/%m/%Y")}" Lunghezza="{B.ival(pat.lung)}" '
           f'Larghezza="{B.ival(pat.larg)}" SpessoreLama="{B.ival(job.kerf)}" Swap="0" Inforesto="1"/>',
           f'<Material Tipologia="{pat.copies}" Codice="{B.esc_xml(job.material_code)}"/>', "<Pattern>",
           f'<Cut ID="1" T="P" Dim="{B.ival(pat.lung)}" Rip="1" EtiID=""/>']
    for n, (t, dim, rip, eti) in enumerate(pat.rows(), 2):
        out.append(f'<Cut ID="{n}" T="{t}" Dim="{"0.00" if dim is None else B.ival(dim)}" Rip="{rip}" EtiID="{eti}"/>')
    out += ["</Pattern>", "<DatiEtichetta>"] + etichetta(job, P, L, I, pat, used, fid) + ["</DatiEtichetta>", "</SchemaDoc>"]
    return CRLF.join(out)


def xmix(job: SawJob, stem: str, pats: list[Pattern], today) -> str:
    def el(tag, a):
        return f"<{tag}" + "".join(f' {k}="{B.esc_xml(v)}"' for k, v in sorted(a.items())) + "/>"
    d = str(job.params.get("list_dir") or XMIX_DIR)
    if d and not d.endswith(("\\", "/")):
        d += "\\"
    mats, rows = [], []
    for i, p in enumerate(pats, 1):
        a = {"Larghezza": B.ival(p.m.sheet_width), "Lunghezza": B.ival(p.m.sheet_length), "Quantita": str(p.copies),
             "Spessore": B.ival(job.thickness), "Tipologia": ""}
        if job.material_code:
            a["Codice"] = job.material_code
        mats.append(el("Material", a))
        rows.append(el("RigaMix", {"CambioMateriale": "0", "File": f"{d}{stem}.{i:03d}.XPrg", "Pacco": str(pack(job)),
                                   "Rep": str(p.copies)}))
    hdr = el("Header", {"Date": today.strftime("%d.%m.%Y"), "Descrizione": stem, "Import": f"From {B.PROGRAM}"})
    return f"<xMix>{hdr}<Materials>{''.join(mats)}</Materials><RigheMix>{''.join(rows)}</RigheMix></xMix>"


def patterns(job: SawJob, P: B.Parts) -> list[Pattern]:
    return [Pattern(job, m, P) for m in job.maps]


def files(job: SawJob, *, when=None, ids=None) -> dict[str, bytes]:
    """Zip ichidagi fayllar. `ids` — har karta uchun fayl ID si (tekshiruvda namunadagi qiymat; odatda tasodifiy)."""
    stem = B.file_stem(job)
    today = when or B.now()
    P, L = B.Parts(job), B.Labels(job, KEY)
    I = B.Labels(job, KEY, rows=[dict(name=n, expr=e) for n, e in INNER])
    pats = patterns(job, P)
    used = used_counts(pats)
    out = {}
    for i, p in enumerate(pats, 1):
        fid = (ids[i - 1] if ids else None) or uuid.uuid4().hex
        out[f"{stem}.{i:03d}.XPrg"] = xprg(job, P, L, I, p, used, fid, today).encode(ENC, "replace")
    out[f"{stem}.XMix"] = xmix(job, stem, pats, today).encode(ENC, "replace")
    return out


@register(KEY, "SCM MaestroCut", "saw", "zip",
          note="Boshqa dasturning etiketka bloblari bo'limi va uning ID atributi yozilmaydi; etiketka maydonlari — "
               "«Дополнительные данные для этикеток» jadvalidan. 5–6-daraja kesim belgilari (W, Z) namunasiz — taxminiy.")
def gen(job: SawJob):
    f = files(job)
    return [(f"{B.file_stem(job)}.zip", B.make_zip(list(f.items())))]
