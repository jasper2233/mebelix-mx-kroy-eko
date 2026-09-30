"""Detal o'lchamlari: 4 xil o'lcham va ular orasidagi o'tish.

  detal (kromka bilan)       — tayyor detal
  prifugovkadan keyin        — detal − kromka qalinligi (har kromkali tomonda)
  zagotovka                  — prifugovkadan keyin + prifugovka eni (har kromkali tomonda)
  pilniy (arra o'lchami)     — zagotovka + ishlov pripuski (▽ △ ▷ ◁)

Uzunlik (length) — top/bottom tomonlar bo'ylab; kromka top/bottom uzunlik
bo'ylab yopishtiriladi, shuning uchun u ENi (width) ni kamaytiradi.
left/right kromkalar esa UZUNLIKni kamaytiradi.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models import ELParams, Part, SizeMode


@dataclass
class Sizes:
    detail: tuple[float, float]
    jointed: tuple[float, float]
    blank: tuple[float, float]
    saw: tuple[float, float]


def _edge(part: Part, side: str, edges: dict[str, ELParams]) -> ELParams | None:
    ref = getattr(part, f"edge_{side}")
    return edges.get(ref.op_id) if ref and ref.op_id else None


def compute_sizes(part: Part, mode: SizeMode, edges: dict[str, ELParams],
                  machining_allowance: float = 0) -> Sizes:
    def thick(side):
        e = _edge(part, side, edges); return e.thickness if e else 0

    def joint(side):
        e = _edge(part, side, edges); return e.jointing_width if e else 0

    # Uzunlikka ta'sir: left/right; enga ta'sir: top/bottom
    t_l = thick("left") + thick("right"); t_w = thick("top") + thick("bottom")
    j_l = joint("left") + joint("right"); j_w = joint("top") + joint("bottom")
    L, W = part.length, part.width

    if mode == SizeMode.DETAIL:
        detail = (L, W)
        jointed = (L - t_l, W - t_w)
        blank = (jointed[0] + j_l, jointed[1] + j_w)
    elif mode == SizeMode.JOINTED:
        jointed = (L, W)
        detail = (L + t_l, W + t_w)
        blank = (L + j_l, W + j_w)
    else:  # BLANK
        blank = (L, W)
        jointed = (L - j_l, W - j_w)
        detail = (jointed[0] + t_l, jointed[1] + t_w)

    # Pilniy o'lcham: detal pripusklari + umumiy "Припуск на обработку заготовки" (har tomonda)
    saw = (blank[0] + part.allow_left + part.allow_right + 2 * machining_allowance,
           blank[1] + part.allow_top + part.allow_bottom + 2 * machining_allowance)
    return Sizes(detail=detail, jointed=jointed, blank=blank, saw=saw)
