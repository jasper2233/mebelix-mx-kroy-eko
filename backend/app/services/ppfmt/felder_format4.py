"""FELDER Format4 — `.may` fayli: PC6 (qat'iy kenglikdagi maydonlar, «/» ajratkich, ASCII) va PC7 («§§» ajratkich, UTF-8).

Tavsif: docs/mebelix/postprocessors/felder-pc6.md, felder-pc7.md. Bitta material (CS operatsiyasi) = bitta fayl:
  MA000 sarlavha · (PC6: MA005 material) · MA010 (+ PC6: MA015) har detal · (PC6: MA050 list) · har karta: MA200, polosalar
  MA300 (polosalar Y bo'ylab) yoki MA400 (X bo'ylab), ichida faqat barglar MA3k0 / MA4k0 · MA999.
  k — bargni ozod qiluvchi oxirgi kesim darajasi L bo'yicha: k = 2L−3; ota bo'lakdagi birinchi kesim va L ≥ 3 bo'lsa k = 2L−4.
  PC7 qo'shimcha: qoldiq polosasi (`MA300§§o'lcham§§` + `R<n>` bargi) va `REST` qatorlari (ishlatilgan listlar, qoldiqlar).

Matn maydonlari BIZNING «Данные для этикеток» jadvalidan (qator tartibi bo'yicha, services/expr.py):
  PC6: 0 detal nomi(16) · 1 MA000 matni · 2–4 MA005 sarlavhalari · 5 MA010 kromka bayroqlari(12) · 6–9 kromkalar ·
       10–14 MA015 matnlari · 15 XNC kodi · 16 havola.
  PC7: 0 detal nomi · 1 MA000 matni · 2–5 kromkalar · 6–16 MA010 ning 17–27-maydonlari.
Yozilmaydi: PC6 fayl oxiridagi boshqa dasturning etiketka ma'lumotlari bloki; dastur nomi maydonlarida — «MebeliX Kroy».
"""
from __future__ import annotations

import binascii

from . import SawJob, register
from . import _saw_bsf as B
from ._saw_giben import translit

KEY6 = "felder_format4_pc6"
KEY7 = "felder_format4_pc7"
CRLF = "\r\n"
SEP7 = "§§"
INNER = (("jl", "part.jointed_length"), ("jw", "part.jointed_width"), ("groove", "groove"), ("drill", "drill"),
         ("mill", "mill"))
SIDES = ("top", "bottom", "left", "right")


def edge_text(e: dict) -> str:
    return f"({e.get('symbol', '')}) {e.get('name', '')}" if e else ""


def op_no(job: SawJob) -> int:
    """CS operatsiyasining loyihadagi tartib raqami (1 dan)."""
    for i, o in enumerate(job.project.operations, 1):
        if o.id == job.op.id:
            return i
    return 1


def mat_code(job: SawJob) -> str:
    """Material kodi; bo'sh bo'lsa — materialning fayldagi raqami (onlayn tizimdagidek), u ham yo'q bo'lsa operatsiya raqami."""
    return job.material_code or str(job.material_uid or op_no(job))


def trims(job: SawJob, m=None) -> tuple[float, float]:
    inc = bool(getattr(job.op.cs_cut, "trim_includes_kerf", False)) if job.op.cs_cut else False
    k = 0.0 if inc else float(job.kerf or 0)
    tl = float(m.trim_length if m is not None else job.trim_length or 0)
    tw = float(m.trim_width if m is not None else job.trim_width or 0)
    return tl + k, tw + k


def batch_id(job: SawJob, when) -> str:
    crc = binascii.crc_hqx(f"{job.project_name}{job.material_name}".encode("utf-8"), 0)
    return f"#N({when.strftime('%y%m%d%H%M%S')}{crc % 100000:05d})"


def leaf_rows(cuts: list[B.Cut], with_rem: bool):
    """Karta barglari DFS tartibida: ("strip", o'lcham, qoldiq polosasi?) va ("leaf", k, barg). 1-darajadagi barg —
    polosa + 2-darajali barg sifatida (polosa o'lchami = barg o'lchami)."""
    cuts = cuts if with_rem else B.drop_rem(cuts)
    for s in cuts:
        if s.leaf:
            yield "strip", s, bool(s.rem)
            yield "leaf", 1, s
            continue
        yield "strip", s, False
        yield from _rec(_order_strip(s.children))


def _hidden(c: B.Cut) -> bool:
    """2-daraja bo'lagi, ichida tayyor (3-daraja) detal yo'q — formatda uning ochilishi yozilmaydi (yashirin)."""
    return bool(c.children) and not any(k.leaf for k in c.children)


def _order_strip(kids: list[B.Cut], front_ok: bool = True) -> list[B.Cut]:
    """Polosa ichidagi 2-daraja bo'laklar tartibi. «Yashirin» bo'lak faqat polosa boshida yoki 2-daraja tayyor detaldan
    (k=1) keyin turganda to'g'ri o'qiladi (aks holda uning barglari oldingi bo'lakka tegishli deb o'qilardi), shuning
    uchun bunday bo'laklar polosa boshiga yoki tayyor detaldan keyinga ko'chiriladi (bo'laklar o'rnini almashtirish
    kesish sxemasini o'zgartirmaydi). Boshqa bo'laklar tartibi saqlanadi."""
    bad = [c for i, c in enumerate(kids) if _hidden(c) and i > 0 and not kids[i - 1].leaf]
    if not bad:
        return kids
    out = [c for c in kids if not any(c is x for x in bad)]
    if front_ok and not (out and _hidden(out[0])):
        out.insert(0, bad.pop(0))
    i = 0
    while bad and i < len(out):
        if out[i].leaf and not (i + 1 < len(out) and _hidden(out[i + 1])):
            out.insert(i + 1, bad.pop(0))
            i += 1
        i += 1
    return out + bad                                   # joy topilmaganlari (kamdan-kam) — oxirida, o'z holicha


def _rec(children: list[B.Cut]):
    kids = list(children)
    if kids and not kids[0].leaf:                    # bo'lak tayyor detal bilan boshlansin (yangi ota bo'lak aniq ochiladi)
        j = next((i for i, c in enumerate(kids) if c.leaf), None)
        if j is not None:
            kids.insert(0, kids.pop(j))
    kids = _order_strip(kids, front_ok=not any(c.leaf for c in kids))
    for i, c in enumerate(kids):
        if c.leaf:
            L = c.level
            yield "leaf", (2 * L - 4 if (i == 0 and L >= 3) else 2 * L - 3), c
        else:
            yield from _rec(c.children)


class Ctx:
    def __init__(self, job: SawJob, key: str):
        self.job = job
        self.P = B.Parts(job)
        self.L = B.Labels(job, key)
        self.I = B.Labels(job, key, rows=[dict(name=n, expr=e) for n, e in INNER])
        self.uids = [p.uid for p in job.op.parts if p.uid in self.P.saw]
        self.first = self.uids[0] if self.uids else 0

    def lab(self, u: int, i: int, dflt) -> str:
        """Jadvalning i-qatori qiymati (jadval qisqa yoki yo'q bo'lsa — format qoidasi bo'yicha `dflt`)."""
        v = self.L.values(u)
        return B.text(v[i][1]) if i < len(v) else B.text(dflt)

    def inner(self, u: int) -> dict:
        return {n: v for n, v in self.I.values(u)}

    def trees(self):
        return [(m, *B.cut_tree(m)) for m in self.job.maps]


# ───────────────────────── PC6 ─────────────────────────
def _fit6(v, w: int) -> str:
    """PC6 — ASCII matn: kirill harflar maydon kengligi hisoblanishidan OLDIN lotinga o'giriladi (onlayn tizim fayli bilan
    tekshirilgan: «Без имени» → «Bez imeni»; PC7 esa UTF-8 da o'zgarishsiz)."""
    return B.fit(translit("" if v is None else str(v)), w)


def pc6(job: SawJob, *, when=None) -> str:
    c = Ctx(job, KEY6)
    P = c.P
    when = when or B.now()
    code, opid, thk = _fit6(mat_code(job), 10), f"{op_no(job):06d}", B.zero(job.thickness, 5)
    head = f"{code}/{opid}/{thk}"
    prog = B.PROGRAM
    out = [f"MA000/{when.strftime('%d%m%y')}/A//{_fit6(prog, 8)}/M/{_fit6(job.project.currency or '', 3)}/"
           f"{_fit6(c.lab(c.first, 1, B.order_name(job)), 30)}/",
           f"MA005/{head}/{_fit6(c.lab(c.first, 2, job.material_name), 30)}/{_fit6(c.lab(c.first, 3, job.material_code), 30)}/"
           f"{_fit6(c.lab(c.first, 4, batch_id(job, when)), 30)}/"]
    for u in c.uids:
        sp = P.saw[u]
        l, w = P.lw(u)
        cl, cw = P.cut_lw(u)
        inn = c.inner(u)
        e = [P.edge(u, s) for s in SIDES]
        flags = "".join(("1 " if x else "  ") for x in e)
        try:
            jl, jw = float(inn.get("jl", l)), float(inn.get("jw", w))
        except (TypeError, ValueError):
            jl, jw = l, w
        name = _fit6(c.lab(u, 0, sp.name), 16)
        q = f"{max(0, sp.qty):05d}"
        base = f"{head}/{name}/{B.zero(l, 8)}/{B.zero(w, 8)}/{q}"
        out.append(f"MA010/{base}/{'N' if sp.grain else 'J'}/  /{_fit6(c.lab(u, 5, flags), 12)}/{B.zero(cl, 8)}/{B.zero(cw, 8)}/"
                   f"{B.zero(jl, 8)}/{B.zero(jw, 8)}/"
                   + "".join(_fit6(c.lab(u, 6 + i, edge_text(x)), 30) + "/" for i, x in enumerate(e)) + f"{q}/{q}/")
        out.append(f"MA015/{base}/" + "".join(_fit6(c.lab(u, 10 + i, ""), 30) + "/" for i in range(5))
                   + f"{_fit6(c.lab(u, 15, sp.xnc_face), 30)}/{_fit6(c.lab(u, 16, f'#P({u})'), 30)}/")
    tl, tw = trims(job)
    kerf = B.zero(job.kerf, 4)
    sl = job.stock[0]["length"] if job.stock else (job.maps[0].sheet_length if job.maps else 0)
    sw = job.stock[0]["width"] if job.stock else (job.maps[0].sheet_width if job.maps else 0)
    out.append(f"MA050/{head}/{_fit6(prog, 6)}/{B.zero(sl, 8)}/{B.zero(sw, 8)}/0015/J   /0000.00/{B.zero(100 + tl, 8)}/"
               f"{B.zero(tl, 4)}/{B.zero(tl, 4)}/{B.zero(tw, 4)}/{kerf}/"
               f"{_fit6(c.lab(c.first, 2, job.material_name), 30)}/{_fit6(c.lab(c.first, 3, job.material_code), 30)}/ /")
    order = {u: i for i, u in enumerate(c.uids, 1)}
    for m, ax, cuts in c.trees():
        tl, tw = trims(job, m)
        n = f"{max(1, m.copies):04d}"
        out.append(f"MA200/{head}/{_fit6(prog, 6)}/{B.zero(m.sheet_length, 8)}/{B.zero(m.sheet_width, 8)}/{n}/{n}/{n}/"
                   f"{B.zero(tl, 4)}/{B.zero(tl, 4)}/{B.zero(tw, 4)}/{B.zero(tw, 4)}/{kerf}/")
        fam = "MA3" if ax == "y" else "MA4"
        for kind, a, b in leaf_rows(cuts, with_rem=False):
            if kind == "strip":
                out.append(f"{fam}00/{B.zero(a.dim, 8)}/     /")
            else:
                out.append(f"{fam}{a}0/{_fit6(order.get(b.uid, 0), 16)}/{B.zero(b.sx, 8)}/{B.zero(b.sy, 8)}/01/     /")
    out.append("MA999/")
    return CRLF.join(out) + CRLF


# ───────────────────────── PC7 ─────────────────────────
def pc7(job: SawJob, *, when=None) -> str:
    c = Ctx(job, KEY7)
    P = c.P
    when = when or B.now()
    fname = f"{B.file_stem(job)}.may"
    code = job.material_code or job.material_name
    thk = B.ival(job.thickness)
    out = [SEP7.join(["MA000", when.strftime("%d.%m.%Y"), B.PROGRAM, "I", fname, "MM", job.project.currency or "",
                      c.lab(c.first, 1, B.order_name(job))])]
    for u in c.uids:
        sp = P.saw[u]
        l, w = P.lw(u)
        cl, cw = P.cut_lw(u)
        inn = c.inner(u)
        e = [P.edge(u, s) for s in SIDES]
        pr = P.product(u)
        dfl = [P.index.get(u, 0), job.material_name, job.material_code, pr.name if pr else "", "", sp.xnc_face, sp.xnc_back,
               inn.get("mill", sp.has_mill), inn.get("drill", sp.has_drill), inn.get("groove", False), f"#P({u})"]
        out.append(SEP7.join(["MA010", str(u), code, thk, c.lab(u, 0, sp.name), B.ival(l), B.ival(w), str(sp.qty),
                              "True" if sp.grain else "False", *[c.lab(u, 2 + i, edge_text(x)) for i, x in enumerate(e)],
                              B.ival(cl), B.ival(cw), B.ival(l), B.ival(w), *[c.lab(u, 6 + i, d) for i, d in enumerate(dfl)]]))
    nid = max(P.model, default=0)

    def rest(i: int, ln: float, wd: float, qty: int) -> str:
        s = [B.ival(ln), B.ival(wd)]
        return SEP7.join(["MA010", str(i), code, thk, "REST", *s, str(qty), "True", *s, *s, *s, "1", job.material_name,
                          job.material_code, "", "", "", "", "false", "false", "false", f"#P({i})"])
    sheets: dict[tuple[float, float], int] = {}
    suid: dict[tuple[float, float], int] = {}
    for m in job.maps:
        k = (m.sheet_length, m.sheet_width)
        sheets[k] = sheets.get(k, 0) + max(1, m.copies)
        suid.setdefault(k, job.sheet_uid(m.sheet_id))
    for (ln, wd), q in sheets.items():
        nid += 1                                   # list qatori raqami: fayldagi id (import qilingan), bo'lmasa keyingi raqam
        out.append(rest(suid[(ln, wd)] or nid, ln, wd, q))
    trees = c.trees()
    rem_id: dict[tuple[int, int], tuple[int, int]] = {}       # (karta, qoldiq raqami) → (REST ID, R raqami)
    rn = 0
    for mi, (m, ax, cuts) in enumerate(trees):
        rems = B.remnants(m)
        for lf, _mult in B.leaves_mult(cuts):
            if lf.rem and (mi, lf.rem) not in rem_id:
                nid += 1
                rn += 1
                rem_id[(mi, lf.rem)] = (nid, rn)
                o = rems.get(lf.rem) or {}
                out.append(rest(nid, o.get("length") or lf.sx, o.get("width") or lf.sy, 0))
    bid = batch_id(job, when)
    kerf = B.ival(job.kerf)
    for mi, (m, ax, cuts) in enumerate(trees):
        tl, tw = trims(job, m)
        n = str(max(1, m.copies))
        out.append(SEP7.join(["MA200", code, thk, job.material_name, bid, B.ival(m.sheet_length), B.ival(m.sheet_width), n, n, n,
                              B.ival(tl), B.ival(tl), B.ival(tw), B.ival(tw), kerf]))
        fam = "MA3" if ax == "y" else "MA4"
        rems = B.remnants(m)
        for kind, a, b in leaf_rows(cuts, with_rem=True):
            if kind == "strip":
                if b:                                   # qoldiq polosasi: xom o'lcham (list chetigacha), oxirida bo'sh maydon
                    o = rems.get(a.rem) or {}
                    raw = o.get("raw_width" if ax == "y" else "raw_length") or a.dim
                    out.append(SEP7.join([f"{fam}00", B.ival(raw), ""]))
                else:
                    out.append(SEP7.join([f"{fam}00", B.ival(a.dim)]))
            elif b.rem:
                i, r = rem_id[(mi, b.rem)]
                o = rems.get(b.rem) or {}
                top = b.level == 1
                x = (o.get("raw_length") if top else o.get("length")) or b.sx
                y = (o.get("raw_width") if top else o.get("width")) or b.sy
                out.append(SEP7.join([f"{fam}{a}0", f"R{r}", B.ival(x), B.ival(y), str(i), "1"]))
            else:
                out.append(SEP7.join([f"{fam}{a}0", f"D{b.uid}", B.ival(b.sx), B.ival(b.sy), str(b.uid), n]))
    out.append("MA999")
    return CRLF.join(out) + CRLF


@register(KEY6, "FELDER Format4 PC6 (.may)", "saw", "may",
          note="Fayl oxiridagi boshqa dasturning etiketka ma'lumotlari bloki yozilmaydi (fayl MA999 bilan tugaydi); matn "
               "maydonlari — «Данные для этикеток» jadvalidan. Material kodi bo'sh bo'lsa — operatsiya tartib raqami. "
               "Qoldiqlar PC6 ga yozilmaydi. Kirill — cp1251 (tasdiqlanmagan).")
def gen_pc6(job: SawJob):
    return [(f"{B.file_stem(job)}.may", pc6(job).encode("cp1251", "replace"))]


@register(KEY7, "FELDER Format4 PC7 (.may, UTF-8)", "saw", "may",
          note="Matn maydonlari — «Данные для этикеток» jadvalidan. Qoldiq va list REST qatorlari uchun yangi ID lar beriladi.")
def gen_pc7(job: SawJob):
    return [(f"{B.file_stem(job)}.may", pc7(job).encode("utf-8"))]
