"""KDT (presize) XML — zip ichida `<loyiha>_<material>.xml` (kesish rejasi) + har detal uchun `<detal id>.emf`
(aslida PNG etiketka rasmi). Tavsif: docs/mebelix/postprocessors/kdt-xml.md.

XML: har karta `<panelK>`, har bo'lak `<no.N>` (ichida kesimlar `<part cut type id code>`), oxirida `<parts>` ro'yxati.
Etiketka rasmi — o'zimizning sodda maket (nom, o'lcham, kod, kromkalar); Pillow o'rnatilmagan bo'lsa rasmlar
qo'shilmaydi (faqat XML)."""
from __future__ import annotations

import io
from typing import Optional
from xml.sax.saxutils import escape

from . import Files, SawJob, SawPart, num, register, zip_files
from ._saw_common import job_title
from ._saw_giben import GN, patterns

ID_START = 1000


def _attr(s: str) -> str:
    return escape(s or "", {'"': "&quot;"})


def sheet_code(job: SawJob, P) -> str:
    """List kodi: «sheet_id» sozlamasi yoki list formatining tartib raqami (1, 2, …)."""
    forced = str(job.params.get("sheet_id") or "").strip()
    if forced:
        return forced
    for i, s in enumerate(job.stock, 1):
        if s.get("id") == P.map.sheet_id:
            return str(i)
    return "1"


def xml_text(job: SawJob) -> str:
    kerf = job.kerf
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<project>"]
    nid = [ID_START]
    nodeno = 0
    rests: list[tuple[str, float, float]] = []
    placed: dict[int, int] = {}

    def newid() -> int:
        v = nid[0]
        nid[0] += 2
        return v

    for pi, P in enumerate(patterns(job), 1):
        L, W = P.dimy, P.dimx
        attrs = f'l="{num(L)}" w="{num(W)}" material="{_attr(job.material_name)}"'
        if job.material_code:
            attrs += f' mcode="{_attr(job.material_code)}"'
        attrs += (f' code="{_attr(sheet_code(job, P))}" thickness="{num(job.thickness)}"'
                  f' saw="{num(kerf)}" num="{P.copies}"')
        out.append(f"<panel{pi} {attrs}>")
        if pi > 1:
            newid()

        def build(nodes: list[GN], lvl: int) -> list[dict]:
            res = []
            for c in nodes:
                for _ in range(c.rep):                 # takrorlar yoyiladi
                    nd = dict(cut=c.size, type="2" if c.kids else "1", code="", id=newid(), ch=[], lead=c.lead)
                    if lvl == 1:
                        newid()
                    if c.kids:
                        nd["ch"] = build(c.kids, lvl + 1)
                    else:
                        nd["code"] = str(c.uid)
                        placed[c.uid] = placed.get(c.uid, 0) + P.copies
                    res.append(nd)
            return res

        strips = build(P.kids, 1)
        if P.rest is not None:
            raw = P.rest_raw(kerf)
            code = f"O{len(rests) + 1}"
            strips.append(dict(cut=raw, type="3", code=code, id=newid(), ch=[]))
            # qoldiq o'lchami list koordinatasida, torsovkasiz: 1-daraja o'qi bo'ylab `raw`, ko'ndalang — butun list
            rests.append((code, raw, W) if P.axis == "x" else (code, W, raw))
        root = dict(l=L, w=W, x=0.0, y=0.0, layer=1, id=0, ch=strips, trim=P.off1)

        def place(node: dict):
            layer = node["layer"]
            pos = node["trim"]
            for c in node["ch"]:
                if layer % 2 == 1:
                    cx, cy = node["x"], node["y"] + pos
                else:
                    cx, cy = node["x"] + pos, node["y"]
                c.update(l=node["w"], w=c["cut"], x=cx, y=cy, layer=layer + 1)
                # 2-qatlam: torsovka + propil; chuqurroq: bo'lak boshidagi haqiqiy siljish (namunalarda 2.5, bizda 0)
                c["trim"] = (P.off2 if layer + 1 == 2 else c.get("lead", 0.0)) if c["ch"] else 0.0
                place(c)
                pos += c["cut"] + kerf

        place(root)
        stack = [root]
        while stack:                                   # stek tartibi: har tugundan keyin uning oxirgi farzandi
            n = stack.pop()
            nodeno += 1
            out.append(f'<no.{nodeno} l="{num(n["l"])}" w="{num(n["w"])}" trim="{num(n["trim"])}" x="{num(n["x"])}"'
                       f' y="{num(n["y"])}" layer="{n["layer"]}" id="{n["id"]}">')
            for c in n["ch"]:
                out.append(f'<part cut="{num(c["cut"])}" type="{c["type"]}" id="{c["id"]}" code="{c["code"]}" />')
            out.append(f"</no.{nodeno}>")
            stack.extend(n["ch"])
        out.append(f"</panel{pi}>")
        out.append("")
    out.append("<parts>")
    for p in job.parts:
        used = min(p.qty, placed.get(p.uid, 0))
        out.append(f'<part code="{p.uid}" l="{num(p.length)}" w="{num(p.width)}" sq="{p.qty}" uc="{used}"'
                   f' rc="{p.qty - used}" />')
    for code, l, w in rests:
        out.append(f'<part code="{code}" l="{num(l)}" w="{num(w)}" sq="1" uc="1" rc="0" />')
    out.append("</parts>")
    out.append("</project>")
    return "\n".join(out)


def label_png(job: SawJob, p: SawPart, index: int) -> Optional[bytes]:
    """O'zimizning sodda etiketka (464×484, 1 bit): nom, o'lcham, kod, kromkalar. Pillow bo'lmasa — None."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:      # noqa: BLE001 — Pillow ixtiyoriy
        return None
    try:
        W, H = 464, 484
        img = Image.new("1", (W, H), 1)
        d = ImageDraw.Draw(img)
        try:
            big = ImageFont.truetype("arial.ttf", 26)
            small = ImageFont.truetype("arial.ttf", 20)
        except Exception:      # noqa: BLE001
            big = small = ImageFont.load_default()
        d.rectangle([4, 4, W - 5, H - 5], outline=0)
        sym = {s: (p.edges.get(s) or {}).get("symbol", "") or ("+" if p.edges.get(s) else "") for s in
               ("top", "bottom", "left", "right")}
        lines = [(big, p.name), (big, f"{num(p.length)} x {num(p.width)} x {num(job.thickness)}"),
                 (small, f"Kod: {p.code or p.uid}"), (small, f"No: {index}   Soni: {p.qty}"),
                 (small, f"Material: {job.material_name}"), (small, f"Buyurtma: {job.project_name}"),
                 (small, f"Mahsulot: {p.product}"),
                 (small, f"Kromka: T[{sym['top']}] B[{sym['bottom']}] L[{sym['left']}] R[{sym['right']}]")]
        if p.xnc_face or p.xnc_back:
            lines.append((small, f"NC: {p.xnc_face or p.xnc_back}"))
        y = 16
        for font, text in lines:
            d.text((16, y), str(text)[:40], font=font, fill=0)
            y += 48 if font is big else 40
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:      # noqa: BLE001 — rasm chizilmasa XML baribir chiqadi
        return None


@register("kdt_presize_xml", "KDT XML (.xml + etiketka rasmlari)", "saw", "zip",
          note="Zip: `<loyiha>_<material>.xml` + har detalga `<id>.emf` (PNG). Namunalarda faqat birinchi material "
               "chiqarilgan; bizda har CS operatsiyasi alohida zip. Etiketka rasmi — o'zimizning sodda maket (Pillow "
               "o'rnatilmagan bo'lsa rasmlar qo'shilmaydi). Ichki `id` lar — noyob hisoblagich, qoldiq kodi O1, O2, …; "
               "list kodi (`code`) — «sheet_id» sozlamasi yoki karta raqami; 3-qatlamdan chuqur siljish 2.5 mm "
               "— daraxtdagi haqiqiy qiymat (namunalarda 2.5, bizning kroyda 0).")
def kdt_presize_xml(job: SawJob) -> Files:
    title = job_title(job)
    files: Files = [(title + ".xml", xml_text(job).encode("utf-8"))]
    for i, p in enumerate(job.parts, 1):
        png = label_png(job, p, i)
        if png:
            files.append((f"{p.uid}.emf", png))
    return [(title + ".zip", zip_files(files))]
