"""Postprotsessorlar: kroy natijasini stanok / boshqa tizim formatiga o'girish.

O'rnatilgan formatlar (hamma uchun ochiq, mustaqil yozilgan):
  csv       — kesish ro'yxati (Excel/1C/MES uchun)
  commands  — kesish buyruqlari matni (arra operatori uchun, T/C/P/W + daraja)
  dxf       — kroy kartalari DXF (R12, CAD/CAM uchun)
  json      — to'liq natija (MES integratsiyasi)

Foydalanuvchi postprotsessori — «Настройки → Постпроцессоры» da shablon yoziladi (Jinja2, xavfsiz sandbox).
Korxonangiz arra stanogining formatini shu yerda kod o'zgartirmasdan tasvirlaysiz. Shablonga beriladigan
ma'lumotlar (kontekst):
  project  — {name, number, customer, order_date, ready_date, currency, mes_order_ref}
  op       — {name, code, thickness, kerf, trim_length, trim_width, sheets_per_pack}
  maps     — [{index, copies, packs, sheet_length, sheet_width, is_remnant, fill, cut_length_m, cuts,
               placements:[{n, uid, name, code, x, y, length, width, rotated, edges}],
               commands:[{n, code, level, size, count, ref}],
               remnants:[{number, x, y, length, width, business}]}]
  parts    — [{uid, name, code, length, width, qty, used, left, grain, edges, label, label_text}]
  map      — (per_map=True bo'lsa) joriy karta
  f(v, n=1) — sonni formatlash (nuqta bilan), now — sana-vaqt
  machine  — stanok tanlangan bo'lsa (`machine:<kalit>`): {key, name, group, params: {param: qiymat}, label_fields: [{name, expr}]},
             aks holda None. `maps[].placements[]` va `parts[]` da `label` {maydon nomi: qiymat} (tipli) va `label_text`
             {nom: matn} — stanokning «Данные для этикеток» ifodalari shu detal kontekstida hisoblangan; ifoda xatosi —
             «#ERR» (jim 0 emas) va `label_warnings` [{field, expr, message, error, count, part_uid}] (services/pp_machine_ctx.py)
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime

from ..models import Operation, OpType, PostprocessorProfile, Project
from .calc import op_part, total_qty
from ..i18n import _, pick_for
from .render import part_edges, rotate_edges
from .tpl_sandbox import fnum, render as render_limited

BUILTIN = {
    "csv": dict(name="MebeliX CSV — kesish ro'yxati", extension="csv"),
    "commands": dict(name="Kesish buyruqlari (operator uchun, TXT)", extension="txt"),
    "dxf": dict(name="DXF — kroy kartalari (CAD/CAM)", extension="dxf"),
    "json": dict(name="MES JSON — to'liq natija", extension="json"),
}

# Stanok / tizim nomlari (faqat ro'yxat): har birining format shabloni korxona dasturchilari tomonidan biriktiriladi
# («Настройки → Постпроцессоры»). (kalit, nom, guruh): saw — pil markazlari (CS natijasi), cnc — ishlov markazlari (XNC).
MACHINES: list[tuple[str, str, str]] = [
    ("scm_wincut", "SCM WinCut", "saw"), ("scm_maestrocut", "SCM MaestroCut", "saw"),
    ("holzma_ptx", "HOLZMA PTX", "saw"), ("holzma_cadmatic4", "HOLZMA CadMatic4", "saw"),
    ("holzma_cadmatic3", "HOLZMA CadMatic3", "saw"), ("biesse_osi", "Biesse OSI", "saw"),
    ("biesse_nc300", "Biesse NC300", "saw"), ("felder_format4_pc6", "FELDER Format4 PC6", "saw"),
    ("felder_format4_pc7", "FELDER Format4 PC7", "saw"), ("felder_f4classic", "F4Classic", "saw"),
    ("homag_chf", "Homag CHF 41/44/44 NPS400", "saw"), ("kdt_presize_qk", "KDT-PreSize QK", "saw"),
    ("kdt_presize_xml", "KDT-PreSize XML", "saw"), ("scheer", "Scheer", "saw"),
    ("nanxing_cutsawfg", "Nanxing CutSawFG", "saw"), ("nanxing_nxcutsaw", "Nanxing NXCutSaw", "saw"),
    ("shelling_mcs", "Shelling MCS", "saw"), ("elmo3", "Altendorf (ELMO)", "saw"), ("glass_gcode", "GlassGCODE", "saw"),
    ("woodwop", "WoodWop (Homag)", "cnc"), ("biesseworks", "BiesseWorks", "cnc"), ("biesse_osi_plus", "Biesse OSI+", "cnc"),
    ("xilog3", "Xilog 3", "cnc"), ("format4", "Format4 (Felder)", "cnc"), ("gcode", "G-Code", "cnc"),
    ("ilenia", "iLenia", "cnc"), ("kdt_trepan", "KDT Trepan", "cnc"), ("mw310", "MW310", "cnc"), ("tpa", "TPA", "cnc"),
    ("vitap_bridge", "Vitap Bridge", "cnc"), ("xd_woodcam", "XD WoodCam", "cnc"),
    # v2.5: korxona namunalaridan o'rganilgan qo'shimcha stanoklar (o'rnatilgan generatorlar — services/ppfmt)
    ("homag", "HOMAG (pattern)", "saw"), ("shelling", "Shelling", "saw"), ("nanxing_cutsaw", "Nanxing CutSaw", "saw"),
    ("aes_alpha", "AES Alpha", "saw"), ("aess_alpha", "AESS Alpha (SS)", "saw"), ("fastpanel", "FastPanel", "saw"),
    ("giben_g57", "Giben G57", "saw"), ("giben_gdrive", "Giben GDrive", "saw"), ("giben_gvisionxp", "Giben GVisionXP", "saw"),
    ("kdt_ks33x", "KDT KS33X", "saw"), ("kdt_new", "KDT (новая версия)", "saw"),
    ("scm_startech", "SCM Startech CN V", "cnc"), ("daron_foxcnc", "Daron FoxCNC / MicroDraw", "cnc"),
    ("hirzt_magi", "HIRZT MAGI", "cnc"), ("nanxing_syntec", "Nanxing SyntecCad", "cnc"),
]
MACHINES += [("ima_wop", "IMA (ImaWop)", "cnc"), ("holzher_nchops", "Holz-Her (NC-hops)", "cnc"),
             ("aes_sirius", "AES Sirius (GCode)", "cnc")]
# 2026-10-24: onlayn tizim namunalaridan — shisha kesish (Lisec) va (CN) nesting ishlov markazlari (guruh «nest»)
MACHINES += [("lisec_xopt", "Lisec (XOpt)", "saw"),
             ("cn_ncstudio", "CNC (NCStudio)", "nest"), ("cn_kdt_gcode", "KDT (GCode)", "nest"),
             ("cn_woodwop", "Homag (WoodWOP v6.x)", "nest"), ("cn_tpa", "TPA Genesis Evolution 8.9", "nest"),
             ("cn_biesseworks", "Biesse (BiesseWorks v3.x)", "nest")]
# 2026-10-26: korxonada stanokda HOZIR ishlayotgan KDT fayllari (post/ — 10 buyurtma): prisadka `KDTPanelFormat`; arra XML ning
# eski (2021) shakli alohida kalitda qoladi
MACHINES += [("kdt_panel", "KDT (KDTPanelFormat)", "cnc"), ("kdt_presize_xml_v1", "KDT-PreSize XML 2021", "saw")]
MACHINE_BY_KEY = {k: (n, g) for k, n, g in MACHINES}

# Postprotsessor oynasidagi yozuvlar va tartib (xodimlarga tanish ro'yxat): kalit → (ru, uz). Ro'yxatda yo'q stanoklar —
# oxirida, o'z nomi bilan. «Пильный центр …» / «Обрабатывающий центр …» / «Сверлильно-присадочный станок …».
_SAW, _CNC, _DRL = ("Пильный центр", "Arra markazi"), ("Обрабатывающий центр", "Ishlov markazi"),     ("Сверлильно-присадочный станок", "Parmalash-prisadka stanogi")
PP_LABELS: list[tuple[str, tuple[str, str], str]] = [
    ("holzma_ptx", _SAW, "HOLZMA (*.ptx)"), ("holzma_cadmatic4", _SAW, "HOLZMA (CadMatic v4.x)"),
    ("holzma_cadmatic3", _SAW, "HOLZMA (CadMatic v3.x)"), ("giben_gvisionxp", _SAW, "Giben (GVisionXP)"),
    ("giben_g57", _SAW, "Giben (G57)"), ("giben_gdrive", _SAW, "Giben (GDrive)"), ("scm_wincut", _SAW, "SCM (WinCut v5)"),
    ("scm_maestrocut", _SAW, "SCM (MaestroCut)"), ("kdt_ks33x", _SAW, "KDT (KS33X v4.4 / PreSize V4.x)"),
    ("kdt_new", _SAW, "KDT (PreSize V1.4.0P / V6.3.2P *.qk)"),
    ("kdt_presize_qk", _SAW, "KDT (PreSize V3.3.0P *.qk)"), ("kdt_presize_xml", _SAW, "KDT (XML)"),
    ("kdt_presize_xml_v1", _SAW, "KDT (XML 2021)"),
    ("biesse_osi", _SAW, "Biesse Selco (OSI)"), ("biesse_nc300", _SAW, "Biesse Selco (NC300)"),
    ("felder_format4_pc6", _SAW, "Felder (Format4 PC6)"), ("felder_format4_pc7", _SAW, "Felder (Format4 PC7)"),
    ("felder_f4classic", _SAW, "Felder (F4Classic)"), ("homag_chf", _SAW, "Homag CHF 41/44/44 (NPS400)"),
    ("homag", _SAW, "HOMAG (pattern)"), ("fastpanel", _SAW, "(FastPanel)"), ("scheer", _SAW, "Scheer (Pa)"),
    ("nanxing_cutsawfg", _SAW, "Nanxing (CutSawFG)"), ("nanxing_cutsaw", _SAW, "Nanxing (CutSaw)"),
    ("nanxing_nxcutsaw", _SAW, "Nanxing (NXCutSaw)"), ("shelling_mcs", _SAW, "Shelling (MCS)"),
    ("shelling", _SAW, "Shelling"), ("aes_alpha", _SAW, "AES Alpha (SS)"), ("aess_alpha", _SAW, "AESS Alpha (SS)"),
    ("gcode", ("", ""), "G CODE"), ("xilog3", _CNC, "SCM (Xilog v3)"), ("scm_startech", _DRL, "SCM (Startech CN V)"),
    ("woodwop", _CNC, "Homag (WoodWOP v6.x)"), ("biesseworks", _CNC, "Biesse (BiesseWorks v3.x)"),
    ("tpa", _CNC, "TPA Genesis Evolution 8.9"), ("mw310", _CNC, "Masterwood (MW310)"), ("xd_woodcam", _CNC, "(XDWoodCam)"),
    ("kdt_panel", _DRL, "KDT (KDTPanelFormat)"), ("kdt_trepan", _CNC, "KDT/WDX (Trepan, 2021)"),
    ("nanxing_syntec", _CNC, "Nanxing (SyntecCad)"),
    ("ima_wop", _CNC, "IMA (ImaWop)"), ("holzher_nchops", _CNC, "Holz-Her (NC-hops)"), ("aes_sirius", _CNC, "AES Sirius (GCode)"),
    ("vitap_bridge", _DRL, "Vitap Bridge"), ("daron_foxcnc", _DRL, "Daron (FoxCNC, MicroDraw)"),
    ("hirzt_magi", _CNC, "HIRZT и Maggi (iLENIA CAD/4)"),
    ("elmo3", ("Форматно-раскроечный станок", "Formatli arra stanogi"), "Altendorf (ELMO)"),
    ("lisec_xopt", ("Линия резки стекла", "Shisha kesish liniyasi"), "Lisec (XOpt)"),
    ("cn_ncstudio", _CNC, "CNC (NCStudio)"), ("cn_woodwop", _CNC, "Homag (WoodWOP v6.x)"),
    ("cn_tpa", _CNC, "TPA Genesis Evolution 8.9"), ("cn_biesseworks", _CNC, "Biesse (BiesseWorks v3.x)"),
    ("cn_kdt_gcode", _CNC, "KDT (GCode)"),
]
_PP_LABEL = {k: (pre, tail) for k, pre, tail in PP_LABELS}
_PP_ORDER = {k: i for i, (k, _p, _t) in enumerate(PP_LABELS)}


def pp_label(key: str, lang: str = "ru") -> str:
    """Postprotsessor oynasidagi yozuv: «Пильный центр HOLZMA (*.ptx)»; ro'yxatda yo'q stanok — o'z nomi."""
    if key in _PP_LABEL:
        pre, tail = _PP_LABEL[key]
        head = pick_for(lang, pre[0], pre[1]) if pre else ""
        return f"{head} {tail}".strip()
    return MACHINE_BY_KEY.get(key, (key, ""))[0]


def pp_order(key: str) -> int:
    return _PP_ORDER.get(key, 10_000)

EXAMPLE_TEMPLATE ="""{#- Namuna: har karta alohida fayl. O'zingizning stanok formatingizga moslang. -#}
SHEET;{{ f(map.sheet_length) }};{{ f(map.sheet_width) }};{{ f(op.thickness) }};{{ map.copies }}
{% for c in map.commands -%}
CUT;{{ c.n }};{{ c.code }};{{ c.level }};{{ f(c.size) }};{{ c.count }};{{ c.ref }}
{% endfor -%}
{% for p in map.placements -%}
PART;{{ p.uid }};{{ f(p.x) }};{{ f(p.y) }};{{ f(p.length) }};{{ f(p.width) }};{{ 1 if p.rotated else 0 }};{{ p.name }}
{% endfor -%}
END
"""


_f = fnum          # o'rnatilgan formatlar ham shablondagi f() bilan bir xil formatlaydi


def context_cn(project: Project, op: Operation, machine_key: str | None = None) -> dict:
    """(CN, W16) Nesting operatsiyasi uchun postprotsessor konteksti: joylashuvlar, burchaklar, list koordinatalaridagi poligonlar, asbob va
    asbob yo'li (kontur ofseti). Stanok G-code formati bu yerda YO'Q (korxona dasturchilari shablonda yozadi). Tavsif — services/cn_post.py."""
    from .cn_post import context_cn as _ctx
    return _ctx(project, op, machine_key)


def context(project: Project, op: Operation, machine_key: str | None = None) -> dict:
    if op.type == OpType.CN:                       # (CN, W16) nesting: kontur / burchak / asbob konteksti
        return context_cn(project, op, machine_key)
    from .pp_machine_ctx import attach_machine
    parts = {p.id: p for p in op.parts}
    res = op.result
    cut = op.cs_cut
    ctx_parts = []
    for p in op.parts:
        ed = part_edges(p, project)
        ctx_parts.append(dict(uid=p.uid, name=p.name, code=p.code, length=p.length, width=op_part(op, p).width,
                              qty=total_qty(project, p), used=p.used_qty, left=p.left_qty, grain=p.grain,
                              edges={k: v["symbol"] for k, v in ed.items()}))
    maps = []
    for m in (res.maps if res else []):
        pls = []
        for i, pl in enumerate(m.placements, 1):
            p = parts.get(pl.part_id)
            ed = rotate_edges(part_edges(p, project), pl.rotated) if p else {}
            pls.append(dict(n=i, uid=pl.part_uid, name=p.name if p else "", code=p.code if p else "",
                            x=pl.x, y=pl.y, length=pl.length, width=pl.width, rotated=pl.rotated,
                            edges={k: v["symbol"] for k, v in ed.items() if v}))
        cmds = [dict(n=i, code=c.code, level=c.level, size=c.size, count=c.count, ref=c.ref)
                for i, c in enumerate(m.commands, 1)]
        rem = [dict(number=o.number, x=o.x, y=o.y, length=o.length, width=o.width, business=o.business)
               for o in m.offcuts if o.kind == "remnant"]
        maps.append(dict(index=m.index, copies=m.copies, sheet_length=m.sheet_length, sheet_width=m.sheet_width,
                         is_remnant=m.is_remnant, fill=m.fill_percent, cut_length_m=m.cut_length_m,
                         cuts=m.cuts_count, packs=m.packs, placements=pls, commands=cmds, remnants=rem))
    ctx = dict(
        project=dict(name=project.name, number=project.number, customer=project.customer,
                     order_date=str(project.order_date), ready_date=str(project.ready_date),
                     currency=project.currency, mes_order_ref=project.mes_order_ref or ""),
        op=(dict(name=op.name, code=op.code, thickness=op.cl.thickness, kerf=op.cl.kerf, trim_length=op.cl.trim,   # (CL) pogonaj
                 trim_width=op.cl.trim, sheets_per_pack=res.sheets_per_pack if res else 1, kind="linear",
                 strip_width=op.cl.width)
            if op.type == OpType.CL and op.cl else
            dict(name=op.name, code=op.code, thickness=op.cs_material.thickness if op.cs_material else 0,
                 kerf=cut.kerf if cut else 0, trim_length=cut.trim_length if cut else 0,
                 trim_width=cut.trim_width if cut else 0, sheets_per_pack=res.sheets_per_pack if res else 1)),
        maps=maps, parts=ctx_parts, f=fnum, now=datetime.now().strftime("%Y-%m-%d %H:%M"))
    return attach_machine(ctx, project, op, machine_key)          # machine, label, label_text, label_warnings (W7)


def _csv(ctx: dict) -> str:
    rows = [_("pp_csv_head")]
    for m in ctx["maps"]:
        for p in m["placements"]:
            ed = "".join(f"{k[0].upper()}{v}" for k, v in sorted(p["edges"].items()))
            rows.append(";".join(str(v) for v in (m["index"], m["copies"], _f(m["sheet_length"]), _f(m["sheet_width"]),
                                                  p["uid"], p["name"].replace(";", ","), p["code"], _f(p["x"]), _f(p["y"]),
                                                  _f(p["length"]), _f(p["width"]), 1 if p["rotated"] else 0, ed)))
    return "\n".join(rows) + "\n"


def _commands(ctx: dict) -> str:
    out = [f"MebeliX Kroy — {ctx['project']['name']} (№{ctx['project']['number']})",
           _("pp_txt_material", name=ctx['op']['name'], t=_f(ctx['op']['thickness']), k=_f(ctx['op']['kerf'])), ""]
    for m in ctx["maps"]:
        out.append(_("pp_txt_map", i=m['index'], n=len(ctx['maps']), l=_f(m['sheet_length']), w=_f(m['sheet_width']),
                     c=m['copies'], f=m['fill'], lt=m['cut_length_m']))
        out.append(f"{'№':>3}  {'Кд':<4}{'Р':>9}{'К':>4}  Д")
        for c in m["commands"]:
            out.append(f"{c['n']:>3}  {c['code'] + str(c['level']):<4}{_f(c['size']):>9}{c['count']:>4}  {c['ref']}")
        out.append("")
    return "\n".join(out)


def _dxf(ctx: dict) -> str:
    def line(x1, y1, x2, y2, layer):
        return f"0\nLINE\n8\n{layer}\n10\n{x1:.2f}\n20\n{y1:.2f}\n30\n0\n11\n{x2:.2f}\n21\n{y2:.2f}\n31\n0\n"

    def rect(x, y, w, h, layer):
        return line(x, y, x + w, y, layer) + line(x + w, y, x + w, y + h, layer) + \
            line(x + w, y + h, x, y + h, layer) + line(x, y + h, x, y, layer)

    def text(x, y, h, s, layer):
        return f"0\nTEXT\n8\n{layer}\n10\n{x:.2f}\n20\n{y:.2f}\n30\n0\n40\n{h:.2f}\n1\n{s}\n"
    layers = ("SHEET", "PARTS", "REMNANT", "TEXT")
    head = "0\nSECTION\n2\nHEADER\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n4\n" + "".join(
        f"0\nLAYER\n2\n{n}\n70\n0\n62\n{c}\n6\nCONTINUOUS\n" for n, c in zip(layers, (7, 3, 5, 2))) + \
        "0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n"
    body = []
    oy = 0.0
    for m in ctx["maps"]:
        W = m["sheet_width"]
        body.append(text(0, oy + W + 60, 60, f"{ctx['op']['name']} karta {m['index']} x{m['copies']}", "TEXT"))
        body.append(rect(0, oy, m["sheet_length"], W, "SHEET"))
        for p in m["placements"]:
            y = oy + W - p["y"] - p["width"]           # DXF Y yuqoriga
            body.append(rect(p["x"], y, p["length"], p["width"], "PARTS"))
            th = max(10.0, min(60.0, min(p["length"], p["width"]) / 5))
            body.append(text(p["x"] + th / 2, y + p["width"] / 2 - th / 2, th,
                             f"{p['uid']} {_f(p['length'])}x{_f(p['width'])}", "TEXT"))
        for r in m["remnants"]:
            y = oy + W - r["y"] - r["width"]
            body.append(rect(r["x"], y, r["length"], r["width"], "REMNANT"))
        oy += W + 300
    return head + "".join(body) + "0\nENDSEC\n0\nEOF\n"


def run_builtin(key: str, project: Project, op: Operation) -> tuple[str, bytes, str]:
    if op.type == OpType.CN:                       # (CN, W16) o'rnatilgan formatlar: json (to'liq kontekst), csv, dxf (poligonlar), commands
        from .cn_post import run_builtin_cn
        return run_builtin_cn(key, project, op, _safe_name)
    ctx = context(project, op)
    base = f"{project.number}_{_safe_name(op.code or op.name, 'kroy', 30)}"
    if key == "csv":
        return f"{base}.csv", ("﻿" + _csv(ctx)).encode("utf-8"), "text/csv"
    if key == "commands":
        return f"{base}_buyruqlar.txt", _commands(ctx).encode("utf-8"), "text/plain"
    if key == "dxf":
        return f"{base}.dxf", _dxf(ctx).encode("ascii", errors="replace"), "application/dxf"
    if key == "json":
        data = dict(project=ctx["project"], op=ctx["op"], maps=ctx["maps"], parts=ctx["parts"])
        return f"{base}.json", json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"), "application/json"
    raise KeyError(key)


def _safe_name(s: str, dflt: str, n: int = 40) -> str:
    """Fayl nomi bo'lagi: faqat harf/raqam/_-. (zip ichida ../ yoki / bo'lmasin)."""
    out = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in (s or "").strip())[:n].strip("_")
    return out or dflt


def render_template(pp: PostprocessorProfile, project: Project, op: Operation, machine_key: str | None = None,
                    warnings_out: list | None = None) -> tuple[str, bytes, str]:
    """Foydalanuvchi shabloni. per_map=True — har karta alohida fayl (zip). `machine_key` — stanok tanlangan bo'lsa
    kontekstga `machine` va hisoblangan `label` lar qo'shiladi; `warnings_out` ga etiketka ifodalari xatolari
    (`label_warnings`) qo'shiladi."""
    ctx = context(project, op, machine_key)
    if warnings_out is not None:
        warnings_out.extend(ctx["label_warnings"])
    pp = pp.model_copy(update={"extension": _safe_name(pp.extension, "txt", 10)})
    nl = "\r\n" if pp.newline == "crlf" else "\n"
    base = f"{project.number}_{_safe_name(op.code or op.name, 'kroy', 30)}"

    def enc(text: str) -> bytes:
        text = text.replace("\r\n", "\n").replace("\n", nl)
        return text.encode(pp.encoding or "utf-8", errors="replace")
    if pp.per_map:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for m in ctx["maps"]:
                z.writestr(f"{base}_{m['index']:02d}.{pp.extension}", enc(render_limited(pp.template, {**ctx, "map": m})))
        return f"{base}_{_safe_name(pp.name, 'pp')}.zip", buf.getvalue(), "application/zip"
    return f"{base}.{pp.extension}", enc(render_limited(pp.template, ctx)), "text/plain"


def is_cs(op: Operation) -> bool:
    return op.type == OpType.CS


# Shablon qaysi kontekst uchun yozilgan: kroy (CS/CL/CN: `map`, `maps`, `placements`, `offcuts`) yoki ishlov markazi (`xnc`).
_SAW_VARS = re.compile(r"\b(maps?|placements|offcuts)\b")
_XNC_VARS = re.compile(r"\bxnc\b")


def template_kind(template: str) -> str:
    """'saw' — faqat kroy o'zgaruvchilari, 'xnc' — faqat ishlov markazi, 'any' — ikkalasi ham / aniqlanmadi.
    XNC «Постпроцессор» ro'yxatida pil markazi shablonlari ko'rsatilmaydi va teskarisi — «'map' is undefined» o'rniga tushunarli xabar."""
    t = template or ""
    saw, xnc = bool(_SAW_VARS.search(t)), bool(_XNC_VARS.search(t))
    if saw and not xnc:
        return "saw"
    if xnc and not saw:
        return "xnc"
    return "any"


# ───────────────────────── Ishlov markazi (XNC operatsiyasi) ─────────────────────────
XNC_BUILTIN = {"json": dict(name="XNC JSON — hisoblangan amallar", extension="json")}


def _jsonable(v):
    """NaN / cheksiz sonlar → None (JSON ga mos), ichma-ich ro'yxat/lug'at bo'ylab."""
    if isinstance(v, float):
        return v if v == v and v not in (float("inf"), float("-inf")) else None
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return v


def context_xnc(project: Project, op: Operation, long_side: str = "any", machine_key: str | None = None,
                constraints=None) -> dict:
    """XNC (ishlov markazi) operatsiyasi uchun postprotsessor konteksti — faqat toza ma'lumot (stanok formati yo'q):
      project — {name, number, customer, order_date, ready_date, currency, mes_order_ref}
      op      — {name, code, qty}
      xnc     — {code, name, qty, face ('front' | 'back'), turn, mirror_x, mirror_y, origin, size{length,width},
                 blank{length,width,thickness}, part{uid,name,code,length,width,qty} | None,
                 edges{top,bottom,left,right}   — detal tomonlari (zagotovka holatida): {symbol, name, thickness, joint},
                 edges_final{…}                 — shu tomonlar burishdan keyingi holatda,
                 ops [...], tools [...], params [...], stats {drills, mill_m, saw_m}, errors, warnings, extra_turn}
      f(v, n=1) — sonni formatlash, now — sana-vaqt.
      machine   — `machine:<kalit>` tanlangan bo'lsa {key, name, group, params, label_fields}, aks holda None (W7).
    Koordinatalar: burish / ko'zgu / koordinata boshi OLDINDAN qo'llangan (detalning chap-yuqori burchagidan, X o'ngga,
    Y pastga, mm); ifodalar hisoblangan. `ops` tuzilmasi — `services.xnc.machine_program`. `long_side` —
    «uzun tomon gorizontal / vertikal» cheklovi (horizontal | vertical | any).
    `constraints` (W8, services.xnc_constraints.XncConstraints; None yoki rejim off — cheklovsiz): «uzun tomon» (long_side
    berilmagan bo'lsa) va «kromka bilan burchakka burish» qo'shimcha burishni belgilaydi (`extra_turn`, `rotation`), kontekstda
    `constraints` (sozlama) va `constraint_issues` (tekshiruv xabarlari: level, code, text, text_ru, text_uz, command_path)."""
    from .calc import edge_map
    from .xnc import _ROT_SIDE, machine_program
    from .xnc_constraints import check_program
    x = op.xnc
    prog = machine_program(op, project, long_side, constraints)
    linked = next((p for o in project.operations for p in o.parts if op.id in p.xnc_op_ids), None)
    edges: dict = {}
    part = None
    if linked is not None:
        part = dict(uid=linked.uid, name=linked.name, code=linked.code, length=linked.length, width=linked.width,
                    qty=total_qty(project, linked))
        emap = edge_map(project)
        for side, e in part_edges(linked, project).items():
            el = emap.get(getattr(linked, f"edge_{side}").op_id)
            edges[side] = dict(symbol=e["symbol"], name=e["name"], thickness=el.thickness if el else 0.0,
                               joint=el.jointing_width if el else 0.0)
    rot = (x.rotation + prog["extra_turn"]) % 360
    final = {_ROT_SIDE[rot].get(s, s): e for s, e in edges.items()}
    xnc = dict(code=op.code, name=op.name, qty=x.qty, face="front" if x.face_side else "back", turn=rot,
               mirror_x=x.mirror_x, mirror_y=x.mirror_y, origin=x.origin, part=part, edges=edges, edges_final=final,
               constraints=constraints.model_dump(mode="json") if constraints is not None else dict(mode="off"),
               constraint_issues=check_program(constraints, prog), **prog)
    from .pp_machine_ctx import attach_machine_xnc
    ctx = _jsonable(dict(
        project=dict(name=project.name, number=project.number, customer=project.customer,
                     order_date=str(project.order_date), ready_date=str(project.ready_date),
                     currency=project.currency, mes_order_ref=project.mes_order_ref or ""),
        op=dict(name=op.name, code=op.code, qty=x.qty), xnc=xnc)) | dict(f=fnum, now=datetime.now().strftime("%Y-%m-%d %H:%M"))
    return attach_machine_xnc(ctx, machine_key)


def xnc_base_name(project: Project, op: Operation) -> str:
    return f"{project.number}_{_safe_name(op.code or op.name, 'xnc', 30)}"


def run_builtin_xnc(key: str, project: Project, op: Operation, long_side: str = "any",
                    constraints=None) -> tuple[str, bytes, str]:
    ctx = context_xnc(project, op, long_side, constraints=constraints)
    if key == "json":
        data = dict(project=ctx["project"], op=ctx["op"], xnc=ctx["xnc"])
        return f"{xnc_base_name(project, op)}.json", json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"), \
            "application/json"
    raise KeyError(key)


def render_template_xnc(pp: PostprocessorProfile, project: Project, op: Operation,
                        long_side: str = "any", machine_key: str | None = None,
                        constraints=None) -> tuple[str, bytes, str]:
    """Foydalanuvchi shabloni (Jinja2, sandbox) XNC operatsiyasi uchun: kontekstda `xnc` (context_xnc). Bitta fayl."""
    ctx = context_xnc(project, op, long_side, machine_key, constraints)
    pp = pp.model_copy(update={"extension": _safe_name(pp.extension, "txt", 10)})
    nl = "\r\n" if pp.newline == "crlf" else "\n"
    text = render_limited(pp.template, ctx).replace("\r\n", "\n").replace("\n", nl)
    return f"{xnc_base_name(project, op)}.{pp.extension}", text.encode(pp.encoding or "utf-8", errors="replace"), \
        "text/plain"


def is_xnc(op: Operation) -> bool:
    return op.type == OpType.XNC and op.xnc is not None
