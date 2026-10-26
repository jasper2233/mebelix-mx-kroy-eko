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
from ._saw_giben import GN, patterns, translit

ID_START = 1000


def _attr(s: str) -> str:
    return escape(s or "", {'"': "&quot;"})


def sheet_code(job: SawJob, P) -> str:
    """List kodi: «sheet_id» sozlamasi, import qilingan fayldagi list raqami (onlayn tizimdagidek) yoki tartib raqami (1, 2, …)."""
    forced = str(job.params.get("sheet_id") or "").strip()
    if forced:
        return forced
    for i, s in enumerate(job.stock, 1):
        if s.get("id") == P.map.sheet_id:
            return str(s.get("uid") or i)
    return "1"


def _tag(name: str, attrs: dict, close: bool) -> str:
    """v2: atributlar alifbo tartibida, bo'sh element — `/>` (stanokdagi yangi versiya fayllaridagidek)."""
    body = " ".join(f'{k}="{v}"' for k, v in sorted(attrs.items()))
    return f"<{name} {body}{'/' if close else ''}>"


def xml_text(job: SawJob, v2: bool = False) -> str:
    """KDT XML. v1 — 2021 yilgi onlayn namuna (ko'p qatorli, `print_code` siz). v2 — korxonada stanokda hozir ishlayotgan
    fayllar (2026-10-26, `post/` — 10 buyurtma): bitta qator, atributlar alifbo tartibida, detal va qoldiqda `print_code`
    (operatsiyadagi detal tartib raqami / O1, O2 …), 3-qatlam va chuqurroq konteyner tugunlarida `trim` = 1-daraja
    siljishining yarmi (torsovka 2 + propil 3 → 2.5) va bolalar shuncha suriladi — real fayllarning 481 holatining hammasida.
    Bo'laklar tartibi — karta joylashuvi tartibi (`_saw_giben.pattern` koordinata bo'yicha saralaydi)."""
    kerf = job.kerf
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<project>"]
    pno = {p.uid: i for i, p in enumerate(job.parts, 1)}           # print_code: detal operatsiyadagi tartib raqami
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
        if v2:
            pa = dict(l=num(L), w=num(W), material=_attr(job.material_name), code=_attr(sheet_code(job, P)),
                      thickness=num(job.thickness), saw=num(kerf), num=str(P.copies))
            if job.material_code:
                pa["mcode"] = _attr(job.material_code)
            out.append(_tag(f"panel{pi}", pa, False))
        else:
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
                        if v2 and c.rest is not None:              # polosa oxiridagi деловой qoldiq
                            code = f"O{len(rests) + 1}"
                            nd["ch"].append(dict(cut=c.rest[0], type="3", code=code, id=newid(), ch=[]))
                            rests.append((code, c.rest[1], c.rest[2]))
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
                # 2-qatlam: torsovka + propil; chuqurroq: v1 — bo'lak boshidagi haqiqiy siljish (namunalarda 2.5, bizda 0),
                # v2 — real fayllardagidek har konteynerda 1-daraja siljishining yarmi
                deep = P.off1 / 2 if v2 else c.get("lead", 0.0)
                c["trim"] = (P.off2 if layer + 1 == 2 else deep) if c["ch"] else 0.0
                place(c)
                pos += c["cut"] + kerf

        place(root)
        stack = [root]
        while stack:                                   # stek tartibi: har tugundan keyin uning oxirgi farzandi
            n = stack.pop()
            nodeno += 1
            if v2:
                out.append(_tag(f"no.{nodeno}", dict(l=num(n["l"]), w=num(n["w"]), trim=num(n["trim"]), x=num(n["x"]),
                                                    y=num(n["y"]), layer=str(n["layer"]), id=str(n["id"])), not n["ch"]))
                for c in n["ch"]:
                    pa = dict(cut=num(c["cut"]), type=c["type"], id=str(c["id"]), code=c["code"])
                    if c["type"] == "1":
                        pa["print_code"] = str(pno.get(int(c["code"]), c["code"])) if c["code"].isdigit() else c["code"]
                    elif c["type"] == "3":
                        pa["print_code"] = c["code"]
                    out.append(_tag("part", pa, True))
                if n["ch"]:
                    out.append(f"</no.{nodeno}>")
            else:
                out.append(f'<no.{nodeno} l="{num(n["l"])}" w="{num(n["w"])}" trim="{num(n["trim"])}" x="{num(n["x"])}"'
                           f' y="{num(n["y"])}" layer="{n["layer"]}" id="{n["id"]}">')
                for c in n["ch"]:
                    out.append(f'<part cut="{num(c["cut"])}" type="{c["type"]}" id="{c["id"]}" code="{c["code"]}" />')
                out.append(f"</no.{nodeno}>")
            stack.extend(n["ch"])
        out.append(f"</panel{pi}>")
        if not v2:
            out.append("")
    out.append("<parts>")
    for p in job.parts:
        used = min(p.qty, placed.get(p.uid, 0))
        if v2:
            out.append(_tag("part", dict(code=str(p.uid), l=num(p.length), w=num(p.width), sq=str(p.qty), uc=str(used),
                                         rc=str(p.qty - used)), True))
        else:
            out.append(f'<part code="{p.uid}" l="{num(p.length)}" w="{num(p.width)}" sq="{p.qty}" uc="{used}"'
                       f' rc="{p.qty - used}" />')
    for code, l, w in rests:
        if v2:
            out.append(_tag("part", dict(code=code, l=num(l), w=num(w), sq="1", uc="1", rc="0"), True))
        else:
            out.append(f'<part code="{code}" l="{num(l)}" w="{num(w)}" sq="1" uc="1" rc="0" />')
    out.append("</parts>")
    out.append("</project>")
    if v2:
        return out[0] + "".join(out[1:])
    return "\n".join(out)


def rests_of(job: SawJob, xml: Optional[str] = None) -> list[tuple[str, float, float]]:
    """Qoldiqlar (kod, uzunlik, en) — etiketka rasmlari uchun; XML dagi `<parts>` ro'yxatidan (polosa ichidagi qoldiqlar ham,
    raqamlar XML bilan aynan bir xil)."""
    import re
    xml = xml if xml is not None else xml_text(job, v2=True)
    return [(c, float(l), float(w)) for c, l, w in re.findall(r'<part code="(O\d+)" l="([^"]+)" rc="[^"]*" sq="[^"]*" uc="[^"]*" w="([^"]+)"/>', xml)]


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


# ---- v2 etiketka (640×480, 1 bit PNG — stanokdagi `.emf` fayllaridagidek o'lcham; maket — o'zimizniki) ----
LW, LH = 640, 480


def _fonts():
    from PIL import ImageFont
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return {sz: ImageFont.truetype(name, sz) for sz in (22, 26, 30, 38)}
        except Exception:      # noqa: BLE001
            continue
    f = ImageFont.load_default()
    return {sz: f for sz in (22, 26, 30, 38)}


def _qr(img, text: str, x: int, y: int, size: int) -> None:
    """QR kod (segno) — `text` (prisadka dasturi nomi / qoldiq raqami)."""
    try:
        import segno
        m = segno.make_qr(text, error="m", boost_error=False).matrix     # oddiy QR (Micro QR ni skanerlar o'qimaydi)
    except Exception:      # noqa: BLE001
        return
    q = len(m)
    cell = max(2, size // (q + 8))                      # 4 modul oq hoshiya (skaner uchun shart)
    x, y = x + 4 * cell, y + 4 * cell
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for r, row in enumerate(m):
        for c, v in enumerate(row):
            if v:
                d.rectangle([x + c * cell, y + r * cell, x + (c + 1) * cell - 1, y + (r + 1) * cell - 1], fill=0)


def _stamp() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y.%m.%d %H:%M")


def label_png_v2(job: SawJob, p: SawPart, index: int) -> Optional[bytes]:
    """Detal etiketkasi: soni, prisadka dasturi nomi + QR (XNC bo'lsa — stanok etiketkani skanerlab dasturni ochadi),
    buyurtma, material, o'lcham, har tomondagi kromka (matn va sxema), raqam_nom, mahsulot, sana."""
    try:
        from PIL import Image, ImageDraw
    except Exception:      # noqa: BLE001 — Pillow ixtiyoriy
        return None
    try:
        F = _fonts()
        img = Image.new("1", (LW, LH), 1)
        d = ImageDraw.Draw(img)
        d.text((16, 14), f"Кол-во: {p.qty}", font=F[30], fill=0)
        if p.xnc_file:
            d.text((16, 52), p.xnc_file[:34], font=F[22], fill=0)
            _qr(img, p.xnc_file, LW - 190, 0, 190)
        d.text((16, 98), (job.project_name or "")[:30], font=F[30], fill=0)
        d.text((16, 136), (job.material_name or "")[:34], font=F[26], fill=0)
        # sxema: detal to'rtburchagi, kromkali tomon — qalin chiziq
        x0, y0, w, h = 480, 230, 120, 140
        d.rectangle([x0, y0, x0 + w, y0 + h], outline=0, width=1)
        ed = p.edges or {}
        for side, line in (("top", [x0, y0, x0 + w, y0]), ("bottom", [x0, y0 + h, x0 + w, y0 + h]),
                           ("left", [x0, y0, x0, y0 + h]), ("right", [x0 + w, y0, x0 + w, y0 + h])):
            if ed.get(side):
                d.line(line, fill=0, width=6)
        sym = {k: (v or {}).get("symbol", "") for k, v in ed.items()}
        d.text((x0 + w // 2 - 20, y0 - 30), f"({sym['top']})" if sym.get("top") else "", font=F[22], fill=0)
        d.text((x0 + w // 2 - 20, y0 + h + 4), f"({sym['bottom']})" if sym.get("bottom") else "", font=F[22], fill=0)
        names = [ed[s0]["name"] for s0 in ("top", "bottom", "left", "right") if ed.get(s0) and ed[s0].get("name")]
        if names:
            d.text((16, 176), "Кромка: " + ", ".join(dict.fromkeys(names))[:40], font=F[22], fill=0)
        d.text((16, 214), f"{num(p.length)} x {num(p.width)} x {num(job.thickness)}", font=F[38], fill=0)
        d.text((16, 268), f"{index}_{p.name}"[:36], font=F[30], fill=0)
        if p.product:
            d.text((16, 308), p.product[:40], font=F[26], fill=0)
        d.text((16, LH - 44), _stamp(), font=F[22], fill=0)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:      # noqa: BLE001 — rasm chizilmasa XML baribir chiqadi
        return None


def rest_png_v2(job: SawJob, code: str, k: int, l: float, w: float) -> Optional[bytes]:
    """Qoldiq etiketkasi: buyurtma, material, «Деловой остаток», o'lcham, raqam, soni, sana, QR (qoldiq raqami)."""
    try:
        from PIL import Image, ImageDraw
    except Exception:      # noqa: BLE001
        return None
    try:
        F = _fonts()
        img = Image.new("1", (LW, LH), 1)
        d = ImageDraw.Draw(img)
        d.text((16, 16), f"П: {(job.project_name or '')[:28]}", font=F[30], fill=0)
        d.text((16, 62), f"М: {(job.material_name or '')[:30]}", font=F[30], fill=0)
        d.text((60, 120), "Деловой остаток", font=F[38], fill=0)
        d.text((16, 182), f"Р: {num(l)} x {num(w)} x {num(job.thickness)}", font=F[30], fill=0)
        d.text((16, 232), f"№: {k}", font=F[30], fill=0)
        d.text((220, 232), "К: 1", font=F[30], fill=0)
        d.text((16, 290), _stamp(), font=F[22], fill=0)
        _qr(img, str(k), LW - 230, LH - 230, 220)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:      # noqa: BLE001
        return None


def _folder_name(job: SawJob) -> str:
    """v2: `<buyurtma nomi> <material>` lotinda (probellar saqlanadi — stanokdagi fayllardagidek), taqiqlangan belgilarsiz."""
    import re
    # kirill — lotinga (stanokdagi fayllarda «Акрил MOKKO» → «Akril MOKKO»; XML ichida nom o'zgarmaydi)
    s = translit(f"{(job.project_name or job.order or '').strip()} {job.material_name}".strip())
    s = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", s)
    return re.sub(r"\s+", " ", s).strip()[:120] or "kroy"


@register("kdt_presize_xml", "KDT XML (.xml + etiketka rasmlari)", "saw", "zip",
          note="Stanokda hozir ishlayotgan versiya (2026-10-26, korxonaning 10 buyurtmasi bilan solishtirildi): zip ichida "
               "`<buyurtma> <material>/<buyurtma> <material>.xml` + har detalga `<kod>.emf`, qoldiqqa `O1.emf` (etiketka — "
               "o'zimizning maket, PNG). XML bitta qatorda, atributlar alifbo tartibida, `print_code` — detalning "
               "operatsiyadagi tartib raqami; 3-qatlamdan chuqur konteynerlarda siljish = (torsovka + propil) / 2. "
               "Ichki `id` va list `code` — o'zimizning noyob raqamlar (mantiqqa ta'sir qilmaydi).")
def kdt_presize_xml(job: SawJob) -> Files:
    folder = _folder_name(job)
    xml = xml_text(job, v2=True)
    files: Files = [(f"{folder}/{folder}.xml", xml.encode("utf-8"))]
    for i, p in enumerate(job.parts, 1):
        png = label_png_v2(job, p, i)
        if png:
            files.append((f"{folder}/{p.uid}.emf", png))
    for k, (code, l, w) in enumerate(rests_of(job, xml), 1):
        png = rest_png_v2(job, code, k, l, w)
        if png:
            files.append((f"{folder}/{code}.emf", png))
    return [(job_title(job) + ".zip", zip_files(files))]


@register("kdt_presize_xml_v1", "KDT XML 2021 (.xml + etiketka rasmlari)", "saw", "zip",
          note="Zip: `<loyiha>_<material>.xml` + har detalga `<id>.emf` (PNG). Namunalarda faqat birinchi material "
               "chiqarilgan; bizda har CS operatsiyasi alohida zip. Etiketka rasmi — o'zimizning sodda maket (Pillow "
               "o'rnatilmagan bo'lsa rasmlar qo'shilmaydi). Ichki `id` lar — noyob hisoblagich, qoldiq kodi O1, O2, …; "
               "list kodi (`code`) — «sheet_id» sozlamasi yoki karta raqami; 3-qatlamdan chuqur siljish 2.5 mm "
               "— daraxtdagi haqiqiy qiymat (namunalarda 2.5, bizning kroyda 0).")
def kdt_presize_xml_v1(job: SawJob) -> Files:
    title = job_title(job)
    files: Files = [(title + ".xml", xml_text(job).encode("utf-8"))]
    for i, p in enumerate(job.parts, 1):
        png = label_png(job, p, i)
        if png:
            files.append((f"{p.uid}.emf", png))
    return [(title + ".zip", zip_files(files))]
