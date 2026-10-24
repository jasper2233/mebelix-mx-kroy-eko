"""Loyiha fayli(lar)ini **ochiq loyihaga qo'shish** («Проект → Импортировать», bir nechta fayl birdan — onlayn tizimdagidek).

Har fayl alohida loyiha sifatida o'qiladi (`main._import_bytes`), so'ng joriy loyihaga qo'shiladi:
* mahsulotlar va operatsiyalar **oxiriga qo'shiladi** (birlashtirilmaydi — bir xil materiallarni birlashtirish uchun
  «Общие действия → Объединить»);
* joriy loyihada bor id lar bilan to'qnashgan id lar (mahsulot / operatsiya / detal / list) yangilanadi va ular ko'rsatilgan
  hamma joy (detal → mahsulot, kromka, XNC bog'lanishi va h.k.) bir xil almashtiriladi;
* detal raqamlari (`uid`) saqlanadi; joriy loyihada band bo'lganlari eng kattasidan keyin davom etadi (etiketka tanlovi ham o'giriladi);
* o'lcham kiritish rejimi joriy loyihanikiga o'giriladi (detalning jismoniy o'lchami saqlanadi);
* fayldagi kroy natijasi olinmaydi (joriy loyihada qaytadan «Раскроить»), ombor / sex holati bu bazaga tegishli emas.
Joriy loyihaning sarlavhasi (nomi, sanalar, holat, valyuta) o'zgarmaydi.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from ..models import OpType, Project


def _ids(p: Project) -> set[str]:
    out = {p.id}
    for pr in p.products:
        out.add(pr.id)
    for o in p.operations:
        out.add(o.id)
        for pt in o.parts:
            out.add(pt.id)
        for sh in o.sheets:
            if getattr(sh, "id", None):
                out.add(sh.id)
    return out


def _replace(v: Any, m: dict[str, str]) -> Any:
    """Faqat butun qiymati to'qnashgan id ga teng satrlar almashtiriladi (id — 12 belgili tasodifiy hex)."""
    if isinstance(v, str):
        return m.get(v, v)
    if isinstance(v, list):
        return [_replace(x, m) for x in v]
    if isinstance(v, dict):
        return {k: _replace(x, m) for k, x in v.items()}
    return v


def _to_size_mode(new: Project, mode) -> None:
    if new.size_mode == mode:
        return
    from . import calc
    from .sizes import compute_sizes
    edges = calc.edge_map(new)
    for o in new.operations:
        for pt in o.parts:
            s = compute_sizes(calc.op_part(o, pt), new.size_mode, edges)
            L, W = {"blank": s.blank, "detail": s.detail, "jointed": s.jointed}[mode.value]
            pt.length = round(L, 3)
            if o.type != OpType.CL:
                pt.width = round(W, 3)
    new.size_mode = mode


def append_project(cur: Project, new: Project) -> dict:
    """`new` ni `cur` ga qo'shadi (joyida). Qaytaradi: qo'shilgan mahsulot / operatsiya / detal soni."""
    _to_size_mode(new, cur.size_mode)
    taken = _ids(cur)
    clash = {i: uuid4().hex[:12] for i in _ids(new) - {new.id} if i in taken}
    data = new.model_dump(mode="json")
    if clash:
        data = _replace(data, clash)
    new = Project.model_validate(data)
    # detal raqamlari (ID): fayldagi ID band bo'lmasa — o'zi saqlanadi (onlayn tizimdagidek; etiketka, XNC kodi, MES shu ID bilan),
    # band yoki takror bo'lsa — eng kattasidan keyingi bo'sh raqam (2026-10-23; avval hammasi joriy maksimumdan qayta raqamlanardi)
    taken_uids = {pt.uid for o in cur.operations for pt in o.parts}
    keep: set[int] = set()
    for o in new.operations:
        for pt in o.parts:
            if pt.uid > 0 and pt.uid not in taken_uids and pt.uid not in keep:
                keep.add(pt.uid)
    uid_map: dict[int, int] = {}
    nxt = max(taken_uids | keep, default=0)
    seen: set[int] = set()
    n_parts = 0
    for o in new.operations:
        for pt in o.parts:
            n_parts += 1
            if pt.uid in keep and pt.uid not in seen:
                seen.add(pt.uid)
                uid_map.setdefault(pt.uid, pt.uid)
                continue
            nxt += 1
            uid_map.setdefault(pt.uid, nxt)
            pt.uid = nxt
    for o in new.operations:
        o.result = None                                  # natija qaytadan hisoblanadi
        lb = getattr(o, "lb", None)
        if lb is not None and getattr(lb, "part_selected", None):
            lb.part_selected = [uid_map.get(u, u) for u in lb.part_selected]
    cur.products.extend(new.products)
    cur.operations.extend(new.operations)
    return dict(products=len(new.products), operations=len(new.operations), parts=n_parts)
