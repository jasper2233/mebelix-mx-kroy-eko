"""LB chop: shablon tanlash, sahifa maketi (A4 to'r / rulon), HTML yig'ish; kroy kartalari miniatyurasi (A4 da 4 / 6 karta).

Chiqish — faqat HTML + inline SVG (skript yo'q, CSP `render.CSP_META`): brauzer «Chop etish» yoki PDF. Eski `labels.labels_html`
(qat'iy QR etiketka) o'zgarishsiz qoladi (`GET/POST /projects/{pid}/labels`); yangi tizim — LBParams + shablon.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from html import escape
from typing import Optional

from ..i18n import LANG, _
from ..models import LB_MAX_LABELS, LBParams, OpType, PrintSettings, Project
from . import settings
from .label_builtin import DEFAULT_KEY, builtin_template
from .label_tpl import Renderer, TemplateError, normalize_template
from .label_vars import EnvBuilder, count_items, iter_items
from .labels import map_qr_text
from .render import CSP_META, _qr_svg, map_header, map_svg

PREVIEW_SHOWN = 6          # jonli ko'rinishda ko'rsatiladigan etiketkalar
PREVIEW_SCAN = 300         # xato qidirish uchun hisoblanadigan etiketkalar (ko'rsatilmaydi)
FAST_QR_FROM = 400         # shundan ko'p etiketkada QR niqobi qidirilmaydi (tezlik)


class LabelsLimit(ValueError):
    """Etiketkalar soni chegaradan oshdi."""

    def __init__(self, total: int):
        super().__init__(_("lb.e_too_many", n=total, max=LB_MAX_LABELS))
        self.total = total


@dataclass
class LabelsResult:
    html: str = ""
    total: int = 0                 # chop etiketkalari jami (cheklovsiz)
    rendered: int = 0              # HTML da bor
    pages: int = 0
    counts: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    template: str = ""             # shablon manbasi: embedded | builtin:<kalit> | profile:<id>
    template_name: str = ""
    truncated: bool = False
    banner: bool = True            # HTML ichida xatolar bannerini ko'rsatish (muharrir ko'rishida o'chiriladi — xatolar alohida ro'yxatda)


def resolve_template(lb: LBParams, lang: str = "ru") -> tuple[dict, str, list[str]]:
    """LBParams → (normallashgan shablon, manba, ogohlantirishlar). Xato — TemplateError."""
    warnings: list[str] = []
    if lb.template:
        return normalize_template(lb.template), "embedded", warnings
    tid = lb.template_id or ""
    if tid.startswith("builtin:"):
        t = builtin_template(tid[8:], lang)
        if t is not None:
            return t, tid, warnings
        warnings.append(_("lb.w_tpl_missing", id=tid))
    elif tid.startswith("profile:") or tid.isdigit():
        try:
            pr = settings.get_profile("label_template", int(tid.split(":")[-1]))
        except ValueError:
            pr = None
        if pr is not None:
            return normalize_template(pr["data"]), tid, warnings
        warnings.append(_("lb.w_tpl_missing", id=tid))
    return builtin_template(DEFAULT_KEY, lang) or {}, f"builtin:{DEFAULT_KEY}", warnings


def sheet_geometry(lb: LBParams) -> dict:
    """A4 sahifa geometriyasi: nechta ustun/qator sig'adi (ogohlantirish uchun) va bir sahifadagi etiketkalar."""
    pw, ph = (297.0, 210.0) if lb.rotate_page == 90 else (210.0, 297.0)
    m = float(lb.margin_mm or 0.0)
    W, H, gap = float(lb.width_mm), float(lb.height_mm), float(lb.gap_mm)
    fit_cols = int((pw - 2 * m + gap) // (W + gap + 1e-9))
    fit_rows = int((ph - 2 * m + gap) // (H + gap + 1e-9))
    rows = lb.rows or max(1, fit_rows)
    return dict(pw=pw, ph=ph, margin=m, fit_cols=fit_cols, fit_rows=fit_rows, cols=lb.columns, rows=rows,
                per_page=max(1, lb.columns * rows))


def _banner(errors: list, warnings: list) -> str:
    if not errors and not warnings:
        return ""
    li = []
    for e in errors:
        loc = f"#{escape(str(e.get('path', '')))}" if e.get("path") else ""
        cnt = f" ×{e['count']}" if e.get("count", 1) > 1 else ""
        li.append(f"<li class='e'><b>{loc} {escape(str(e.get('field', '')))}</b> {escape(str(e.get('message', '')))}{cnt}</li>")
    for w in warnings:
        msg = w if isinstance(w, str) else w.get("message", "")
        li.append(f"<li class='w'>{escape(str(msg))}</li>")
    return f"<div class='errs'><ul>{''.join(li)}</ul></div>"


def _css(lb: LBParams, geo: dict) -> str:
    W, H = lb.width_mm, lb.height_mm
    border = ".2mm solid #555" if lb.border_kind == "perimeter" else "none"      # «Границы»: Нет границы / Границы по периметру
    base = (f"body{{margin:0;font-family:Arial,Helvetica,sans-serif}}"
            f".lbl{{box-sizing:border-box;border:{border};overflow:hidden;page-break-inside:avoid;break-inside:avoid;background:#fff}}"
            f".lbl svg{{display:block;width:100%;height:100%}}"
            f".errs{{font:12px Arial;background:#fff4e5;border:1px solid #f0b36b;margin:6px;padding:4px 10px}}"
            f".errs ul{{margin:0;padding-left:16px}}.errs .e{{color:#b00020}}.errs .w{{color:#8a5a00}}"
            f".empty{{font:14px Arial;color:#666;padding:20px}}"
            f"@media print{{.errs{{display:none}}}}")
    if lb.mode == "roll":
        w, h = (H, W) if lb.rotate_page == 90 else (W, H)
        return (f"@page{{size:{w:g}mm {h:g}mm;margin:0}}{base}"
                f".pg{{width:{w:g}mm;height:{h:g}mm;overflow:hidden;position:relative;page-break-after:always;break-after:page}}"
                f".pg:last-child{{page-break-after:auto;break-after:auto}}"
                f".pg .lbl{{width:{W:g}mm;height:{H:g}mm}}"
                f".rot{{position:absolute;left:{H:g}mm;top:0;width:{W:g}mm;height:{H:g}mm;transform-origin:0 0;transform:rotate(90deg)}}"
                f"@media screen{{body{{background:#e5e7eb}}.pg{{margin:4mm auto;box-shadow:0 0 4px #0004;background:#fff}}}}")
    pw, ph, m = geo["pw"], geo["ph"], geo["margin"]
    return (f"@page{{size:{pw:g}mm {ph:g}mm;margin:{m:g}mm}}{base}"
            f".grid{{display:grid;grid-template-columns:repeat({lb.columns},{W:g}mm);grid-auto-rows:{H:g}mm;gap:{lb.gap_mm:g}mm}}"
            f".lbl{{width:{W:g}mm;height:{H:g}mm}}"
            f".pg{{page-break-after:always;break-after:page}}.pg:last-child{{page-break-after:auto;break-after:auto}}"
            f"@media screen{{body{{background:#e5e7eb{';zoom:.7' if pw > ph else ''}}}.pg{{width:{pw:g}mm;min-height:{ph:g}mm;padding:{m:g}mm;box-sizing:border-box;"
            f"background:#fff;margin:4mm auto;box-shadow:0 0 4px #0004}}}}")


def render_labels(project: Project, lb: LBParams, *, lang: str = "ru", limit: Optional[int] = None,
                  scan: Optional[int] = None, banner: bool = True) -> LabelsResult:
    """Etiketkalar HTML i. `limit` — ko'rsatiladigan etiketkalar (None = hammasi, ≤ LB_MAX_LABELS; oshsa — LabelsLimit),
    `scan` — xato qidirish uchun qo'shimcha hisoblanadigan (ko'rsatilmaydigan) etiketkalar."""
    lang = lang if lang in ("ru", "uz") else "ru"
    token = LANG.set(lang)
    try:
        return _render(project, lb, lang, limit, scan, banner)
    finally:
        LANG.reset(token)


def _render(project: Project, lb: LBParams, lang: str, limit: Optional[int], scan: Optional[int],
            banner: bool = True) -> LabelsResult:
    counts = count_items(project, lb)
    total = counts["total"]
    if limit is None and total > LB_MAX_LABELS:
        raise LabelsLimit(total)
    res = LabelsResult(total=total, counts=counts, banner=banner)
    try:
        tpl, src, warns = resolve_template(lb, lang)
    except TemplateError as e:
        res.errors.append({"path": "", "field": "", "expr": "", "message": str(e), "count": 1})
        res.html = _page(lb, [], res, lang)
        return res
    res.template, res.template_name, res.warnings = src, str(tpl.get("name", "")), list(warns)
    geo = sheet_geometry(lb)
    if lb.mode == "sheet":
        if geo["fit_cols"] < lb.columns:
            res.warnings.append(_("lb.w_cols", cols=lb.columns, fit=max(0, geo["fit_cols"])))
        if geo["fit_rows"] < 1 or (lb.rows and lb.rows > geo["fit_rows"]):
            res.warnings.append(_("lb.w_rows", rows=lb.rows or 1, fit=max(0, geo["fit_rows"])))
    n_show = LB_MAX_LABELS if limit is None else limit
    n_run = n_show if limit is None else max(n_show, scan or 0)
    renderer = Renderer(tpl, width_mm=lb.width_mm, height_mm=lb.height_mm, params=lb.params, lang=lang,
                        fast_qr=total > FAST_QR_FROM)
    eb = EnvBuilder(project, lb, total, lang)
    cells: list[str] = []
    ran = 0
    for it in iter_items(project, lb):
        if ran >= n_run:
            break
        svg = renderer.render(eb.env(it))
        if ran < n_show:
            cells.append(svg)
        ran += 1
    res.rendered = len(cells)
    res.truncated = total > len(cells)
    res.errors = list(renderer.errors.values())
    res.warnings += [w["message"] for w in renderer.warnings.values()]
    res.html = _page(lb, cells, res, lang)
    res.pages = (math.ceil(total / geo["per_page"]) if lb.mode == "sheet" else total) if total else 0
    return res


def _page(lb: LBParams, svgs: list[str], res: LabelsResult, lang: str) -> str:
    geo = sheet_geometry(lb)
    title = "Этикетки" if lang == "ru" else "Etiketkalar"
    if not svgs:
        body = f"<div class='empty'>{escape(_('lb.empty'))}</div>"
    elif lb.mode == "roll":
        if lb.rotate_page == 90:
            body = "".join(f"<div class='pg'><div class='rot'><div class='lbl'>{s}</div></div></div>" for s in svgs)
        else:
            body = "".join(f"<div class='pg'><div class='lbl'>{s}</div></div>" for s in svgs)
    else:
        per = geo["per_page"]
        pages = []
        for i in range(0, len(svgs), per):
            pages.append("<div class='pg'><div class='grid'>"
                         + "".join(f"<div class='lbl'>{s}</div>" for s in svgs[i:i + per]) + "</div></div>")
        body = "".join(pages)
    return (f"<!DOCTYPE html><html lang='{lang}'><head><meta charset='utf-8'>{CSP_META}<title>{title}</title>"
            f"<style>{_css(lb, geo)}</style></head><body>{_banner(res.errors, res.warnings) if res.banner else ''}{body}</body></html>")


# ───────────────────────── Kroy kartalari miniatyurasi: A4 da 4 / 6 ─────────────────────────
MAP_SHEET_COUNTS = (4, 6)


def map_sheets_html(project: Project, *, per_page: int = 4, op_id: Optional[str] = None, lang: str = "ru",
                    ps: Optional[PrintSettings] = None) -> tuple[str, int]:
    """Kroy kartalarining miniatyurasi: A4 (bosma) da 2 ustun × (per_page / 2) qator. Qaytaradi: (HTML, kartalar soni).
    Karta chizmasi — hisobotdagi `render.map_svg` (kromka chiziqlari, detal raqami); sarlavha — `map_header`; kichik QR — karta kodi."""
    if per_page not in MAP_SHEET_COUNTS:
        raise ValueError(_("lb.e_per_page"))
    ps = ps or PrintSettings()
    token = LANG.set(lang if lang in ("ru", "uz") else "ru")
    try:
        cells: list[str] = []
        for op in project.operations:
            if op.type != OpType.CS or (op_id and op.id != op_id) or not (op.result and op.result.maps):
                continue
            res = op.result
            for m in res.maps:
                svg = map_svg(m, 420, None, project, op, "number", ps.map_edges, False, ps.map_mirror)
                qr = _qr_svg(map_qr_text(project, op.id, m.index), scale=2) if ps.map_qr else ""
                head = f"{escape(op.name)} &nbsp; {escape(map_header(m, res, ps.map_header_fields))}"
                cells.append(f"<div class='mc'><div class='mh'>{head}</div>"
                             f"<div class='mq'>{qr}</div><div class='ms'>{svg}</div></div>")
        rows = per_page // 2
        gap = 4.0
        landscape = per_page == 4                       # 2×2 — albom A4 (karta nisbati 1.5 — vertikal sahifada joy bo'sh qoladi); 2×3 — kitob
        cw, ch = (281.0, 194.0) if landscape else (194.0, 281.0)      # A4 − 2·8 mm maydon
        cell_h = (ch - gap * (rows - 1)) / rows
        css = (f"@page{{size:{'A4 landscape' if landscape else 'A4'};margin:8mm}}body{{margin:0;font-family:Arial,Helvetica,sans-serif}}"
               f".mp{{display:grid;grid-template-columns:repeat(2,1fr);grid-auto-rows:{cell_h:.1f}mm;gap:{gap:g}mm;"
               f"page-break-after:always;break-after:page}}.mp:last-child{{page-break-after:auto;break-after:auto}}"
               f".mc{{position:relative;border:.2mm solid #999;padding:1.5mm;box-sizing:border-box;overflow:hidden}}"
               f".mh{{font-size:2.9mm;font-weight:bold;padding-right:11mm;margin-bottom:1.5mm;line-height:1.25}}"
               f".mq{{position:absolute;top:1.5mm;right:1.5mm}}.mq svg{{width:10mm;height:10mm}}"
               f".ms svg{{display:block;width:100%;height:auto}}.empty{{font:14px Arial;color:#666;padding:20px}}"
               f"@media screen{{body{{background:#e5e7eb{';zoom:.7' if landscape else ''}}}.mp{{width:{cw:g}mm;height:{ch:g}mm;padding:8mm;background:#fff;"
               f"margin:4mm auto;box-shadow:0 0 4px #0004;box-sizing:content-box}}}}")
        if not cells:
            body = f"<div class='empty'>{escape(_('cut_first'))}</div>"
        else:
            body = "".join("<div class='mp'>" + "".join(cells[i:i + per_page]) + "</div>" for i in range(0, len(cells), per_page))
        title = "Карты кроя" if lang == "ru" else "Kroy kartalari"
        html = (f"<!DOCTYPE html><html lang='{lang}'><head><meta charset='utf-8'>{CSP_META}<title>{title}</title>"
                f"<style>{css}</style></head><body>{body}</body></html>")
        return html, len(cells)
    finally:
        LANG.reset(token)
