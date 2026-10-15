"""Detal etiketkalari (nakleyka): har bir detal nusxasi uchun, QR kod bilan — MES skaneri uchun.

QR matni:  MXK:<loyiha №>:<detal ID>:<nusxa>/<jami>   masalan  MXK:1000123:7:2/4
MES shu kod bo'yicha API dan detalni topadi: GET /api/mes/scan/{kod}.
Tartib — kroy kartalari bo'yicha (arradan chiqish tartibida), kroy bo'lmasa detallar ro'yxati bo'yicha.
"""
from __future__ import annotations

from html import escape
from typing import Optional

from ..models import LabelSettings, OpType, Project
from .calc import effective_qty
from .render import CSP_META, _qr_svg, fmt, part_edges, part_marks


def qr_text(project: Project, uid: int, i: int, n: int) -> str:
    """Detal etiketkasi: MXK:<loyiha №>:<detal ID>:<nusxa>/<jami>."""
    return f"MXK:{project.number}:{uid}:{i}/{n}"


def map_qr_text(project: Project, op_id: str, index: int) -> str:
    """Kroy kartasi (hisobotda): MXK:<loyiha №>:<operatsiya id>:<karta №>."""
    return f"MXK:{project.number}:{op_id}:{index}"


def parse_qr(code: str) -> Optional[dict]:
    """QR matni → ma'lumot. Detal etiketkasida nusxa raqami 1..jami oralig'ida bo'lishi shart (0/0, 3/2, −1/−1 — yaroqsiz);
    karta raqami ≥ 1."""
    try:
        tag, number, a, b = code.strip().split(":")
        if tag != "MXK":
            return None
        if "/" in b:
            i, n = b.split("/")
            copy, total = int(i), int(n)
            if not (1 <= copy <= total):
                return None
            return dict(kind="part", number=int(number), uid=int(a), copy=copy, total=total)
        if int(b) < 1:
            return None
        return dict(kind="map", number=int(number), op_id=a, map=int(b))
    except ValueError:
        return None


def edge_icon_parts(ed: dict, size: float = 34) -> tuple[float, float, str]:
    """Kichik detal sxemasi (kromkali tomonlar qalin chiziq, belgisi bilan): (eni, bo'yi, ichki SVG). Shablon dvigateli ham
    shu funksiyadan foydalanadi (`edges` elementi)."""
    w, h = size * 1.6, size
    s = [f'<rect x="4" y="4" width="{w - 8:.0f}" height="{h - 8}" fill="#fff" stroke="#999" stroke-width="1"/>']
    seg = {"top": (4, 4, w - 4, 4), "bottom": (4, h - 4, w - 4, h - 4), "left": (4, 4, 4, h - 4), "right": (w - 4, 4, w - 4, h - 4)}
    txt = {"top": (w / 2, 12), "bottom": (w / 2, h - 7), "left": (10, h / 2 + 3), "right": (w - 10, h / 2 + 3)}
    for sd, e in ed.items():
        x1, y1, x2, y2 = seg[sd]
        if e.get("lines", 1) > 0:              # «Линии маркировки» 0 — chiziqsiz, faqat belgi
            s.append(f'<line x1="{x1:.0f}" y1="{y1}" x2="{x2:.0f}" y2="{y2}" stroke="#000" stroke-width="3.5"/>')
        tx, ty = txt[sd]
        s.append(f'<text x="{tx:.0f}" y="{ty:.0f}" font-size="8" text-anchor="middle" font-family="Arial">{escape(e["symbol"])}</text>')
    return w, h, "".join(s)


def _edge_icon(ed: dict, size: int = 34) -> str:
    """Kichik detal sxemasi: kromkali tomonlar qalin chiziq, belgisi bilan."""
    w, h, inner = edge_icon_parts(ed, size)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h}" viewBox="0 0 {w:.0f} {h}">'
            f'{inner}</svg>')


def labels_html(project: Project, ls: Optional[LabelSettings] = None, op_id: Optional[str] = None,
                lang: str = "ru") -> str:
    ls = ls or LabelSettings()
    w_map = "карта" if lang == "ru" else "karta"
    title = "Этикетки" if lang == "ru" else "Etiketkalar"
    products = {p.id: p for p in project.products}
    # kichik etiketka (masalan 40×25): shrift, QR va kromka sxemasi o'lchamga qarab kichraytiriladi — pastki qator
    # (nusxa/jami · karta) kesilib ketmasin
    k = max(0.55, min(1.0, ls.height_mm / 40, ls.width_mm / 58))
    cards = []
    for op in project.operations:
        if op.type != OpType.CS or (op_id and op.id != op_id):
            continue
        parts = {p.id: p for p in op.parts}
        seq: list[tuple] = []           # (part, karta №)
        if op.result and op.result.maps:
            for m in op.result.maps:
                for _ in range(m.copies):
                    for pl in m.placements:
                        if pl.part_id in parts:
                            seq.append((parts[pl.part_id], m.index))
        else:
            for p in op.parts:
                seq += [(p, None)] * effective_qty(project, p)
        counters: dict[str, int] = {}
        thick = op.cs_material.thickness if op.cs_material else 0
        for p, map_no in seq:
            n = effective_qty(project, p)
            counters[p.id] = counters.get(p.id, 0) + 1
            i = counters[p.id]
            ed = part_edges(p, project)
            marks = part_marks(p, project)
            prod = products.get(p.product_id)
            qr = _qr_svg(qr_text(project, p.uid, i, n), scale=2) if ls.qr else ""
            cards.append(f"""
<div class="lbl">
  <div class="top"><b>№{project.number}</b> {escape(project.name[:28])}</div>
  <div class="mid">
    <div class="info">
      <div class="nm"><span class="uid">{p.uid}</span> {escape((marks + ' ' if marks else '') + p.name[:40])}</div>
      <div class="dim">{fmt(p.length)} × {fmt(p.width)} × {fmt(thick)}</div>
      <div class="mat">{escape(op.name[:40])}</div>
      {f'<div class="prod">{escape(prod.name[:36])}</div>' if ls.show_product and prod else ''}
      <div class="foot">{i}/{n}{f' · {w_map} {map_no}' if ls.show_map and map_no else ''}</div>
    </div>
    <div class="right">{_edge_icon(ed, max(20, round(34 * k))) if ls.show_edges and ed else ''}<div class="qr">{qr}</div></div>
  </div>
</div>""")
    cols = int(ls.columns)
    if cols <= 0:
        page = f"@page {{ size: {ls.width_mm}mm {ls.height_mm}mm; margin: 0; }} .lbl {{ page-break-after: always; }}"
        grid = "display:block"
    else:
        page = "@page { size: A4; margin: 6mm; }"
        grid = f"display:grid; grid-template-columns: repeat({cols}, {ls.width_mm}mm); gap: 2mm"
    css = f"""{page}
body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; }}
.sheet {{ {grid}; }}
.lbl {{ width: {ls.width_mm}mm; height: {ls.height_mm}mm; box-sizing: border-box; border: 0.2mm solid #555;
        padding: {1.2 * k:.2f}mm {1.6 * k:.2f}mm; overflow: hidden; page-break-inside: avoid; font-size: {2.6 * k:.2f}mm; }}
.top {{ font-size: {2.4 * k:.2f}mm; border-bottom: 0.2mm solid #999; padding-bottom: .4mm; white-space: nowrap; overflow: hidden; }}
.mid {{ display: flex; justify-content: space-between; gap: 1mm; margin-top: .6mm; }}
.info {{ min-width: 0; flex: 1; }}
.nm {{ font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.uid {{ display: inline-block; background: #111; color: #fff; padding: 0 1mm; border-radius: .6mm; }}
.dim {{ font-size: {4.2 * k:.2f}mm; font-weight: bold; margin: .5mm 0; white-space: nowrap; overflow: hidden; }}
.mat, .prod {{ font-size: {2.3 * k:.2f}mm; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.foot {{ font-size: {2.3 * k:.2f}mm; color: #333; margin-top: .4mm; white-space: nowrap; }}
.right {{ display: flex; flex-direction: column; align-items: flex-end; }}
.qr svg {{ width: {max(11.0, 15 * k):.1f}mm; height: {max(11.0, 15 * k):.1f}mm; }}
"""
    return (f"<!DOCTYPE html><html><head><meta charset='utf-8'>{CSP_META}<title>{title} — {escape(project.name)}</title>"
            f"<style>{css}</style></head><body><div class='sheet'>{''.join(cards)}</div></body></html>")
