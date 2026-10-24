"""Etiketka o'zgaruvchilari: chop qatorlari (detal nusxasi / qoldiq / mahsulot / foydalanuvchi qatori) va har qator uchun
ifoda muhiti (kontekst provayderi).

Nomlar — nuqtali (`project.name`, `part.id`, `edge.top.symbol` …; ifoda tilida nuqtali nom bitta o'zgaruvchi). Inventar
(03 Ilova B) dagi snake_case nomlari (`part_uid`, `edge_top_symbol`) va eski dasturdagi qisqa nomlar (`ets`, `thick`, `txt`) —
**taxalluslar**: ular bir xil qiymatni beradi. Faqat bizda mavjud ma'lumotlar; qolganlari T_LB_ETIKETKA.md da «keyin».

Qator turiga mos kelmaydigan o'zgaruvchi bo'sh standart qiymatga ega (satr «», son 0, mantiqiy false) — bitta shablon turli
qatorlar bilan xato bermaydi; faqat nomi noma'lum (imlo xatosi) o'zgaruvchi xato beradi.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterator, Optional

from ..models import LB_MAX_LABELS, LBParams, OpType, Operation, Part, Product, Project, SizeMode
from ..i18n import norm_lang, pick_for
from . import expr, product_program
from .calc import edge_map, effective_qty, total_qty
from .label_user import coerce_user_value, sample_row, user_field_specs
from .labels import map_qr_text, qr_text
from .render import fmt, part_edges, part_marks, part_mill_flag
from .sizes import compute_sizes

SIDES = ("top", "bottom", "left", "right")
SIDE_CH = {"top": "t", "bottom": "b", "left": "l", "right": "r"}        # eski qisqa nomlar: etc, ebs, ell, ert …
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,30}$")

# ───────────────────────── Ro'yxat (UI va hujjat uchun) ─────────────────────────
# (nom, tur, guruh, rus, o'zbek)
VARS: list[tuple[str, str, str, str, str]] = [
    ("project.name", "string", "project", "Название проекта", "Loyiha nomi"),
    ("project.number", "integer", "project", "Номер проекта (Заказ ID)", "Loyiha raqami (Buyurtma ID)"),
    ("project.date", "string", "project", "Дата заказа (дд.мм.гггг)", "Buyurtma sanasi (kk.oo.yyyy)"),
    ("project.ready_date", "string", "project", "Дата готовности", "Tayyor bo'lish sanasi"),
    ("project.description", "string", "project", "Примечание проекта", "Loyiha izohi"),
    ("project.currency", "string", "project", "Валюта", "Valyuta"),
    ("project.owner", "string", "project", "Автор", "Muallif"),
    ("project.customer", "string", "project", "Заказчик", "Buyurtmachi"),
    ("project.mes", "string", "project", "Номер заказа в MES", "MES buyurtma raqami"),
    ("project.crc16", "integer", "project", "CRC16 названия проекта", "Loyiha nomining CRC16"),
    ("project.crc32", "integer", "project", "CRC32 названия проекта", "Loyiha nomining CRC32"),
    ("product.index", "integer", "product", "Номер изделия", "Mahsulot tartib raqami"),
    ("product.name", "string", "product", "Название изделия", "Mahsulot nomi"),
    ("product.code", "string", "product", "Код изделия", "Mahsulot kodi"),
    ("product.qty", "integer", "product", "Количество изделий", "Mahsulotlar soni"),
    ("product.count", "integer", "product", "Количество изделий (синоним)", "Mahsulotlar soni (sinonim)"),
    ("product.description", "string", "product", "Описание изделия", "Mahsulot tavsifi"),
    ("product.phone1", "string", "product", "Телефон 1", "Telefon 1"),
    ("product.phone2", "string", "product", "Телефон 2", "Telefon 2"),
    ("product.date", "string", "product", "Дата готовности изделия", "Mahsulot tayyor sanasi"),
    ("product.order", "string", "product", "Данные заказа", "Buyurtma ma'lumoti"),
    ("material.name", "string", "material", "Материал (название операции CS)", "Material (CS operatsiya nomi)"),
    ("material.code", "string", "material", "Код материала", "Material kodi"),
    ("material.thickness", "double", "material", "Толщина материала, мм", "Material qalinligi, mm"),
    ("part.id", "integer", "part", "ID детали в проекте", "Detalning loyihadagi ID si"),
    ("part.uid", "integer", "part", "ID детали (синоним part.id)", "Detal ID (part.id sinonimi)"),
    ("part.code", "string", "part", "Код детали", "Detal kodi"),
    ("part.name", "string", "part", "Наименование детали", "Detal nomi"),
    ("part.title", "string", "part", "Знаки обработки + наименование", "Ishlov belgilari + nom"),
    ("part.description", "string", "part", "Описание детали", "Detal tavsifi"),
    ("part.marks", "string", "part", "Знаки обработки (= * %)", "Ishlov belgilari (= * %)"),
    ("part.index", "integer", "part", "Номер детали в операции", "Detalning operatsiyadagi raqami"),
    ("part.length", "double", "part", "Длина (как введена, режим проекта), мм", "Uzunlik (kiritilgan, loyiha rejimi), mm"),
    ("part.width", "double", "part", "Ширина (как введена), мм", "En (kiritilgan), mm"),
    ("part.blank_length", "double", "part", "Длина заготовки", "Zagotovka uzunligi"),
    ("part.blank_width", "double", "part", "Ширина заготовки", "Zagotovka eni"),
    ("part.detail_length", "double", "part", "Длина готовой детали (с кромкой)", "Tayyor detal uzunligi (kromka bilan)"),
    ("part.detail_width", "double", "part", "Ширина готовой детали (с кромкой)", "Tayyor detal eni (kromka bilan)"),
    ("part.jointed_length", "double", "part", "Длина после прифуговки", "Prifugovkadan keyingi uzunlik"),
    ("part.jointed_width", "double", "part", "Ширина после прифуговки", "Prifugovkadan keyingi en"),
    ("part.saw_length", "double", "part", "Длина для пилы (с припуском)", "Arra uzunligi (pripusk bilan)"),
    ("part.saw_width", "double", "part", "Ширина для пилы (с припуском)", "Arra eni (pripusk bilan)"),
    ("part.thickness", "double", "part", "Толщина, мм", "Qalinlik, mm"),
    ("part.dims", "string", "part", "«Длина × ширина × толщина»", "«Uzunlik × en × qalinlik»"),
    ("part.qty", "integer", "part", "Количество (ОК − МК)", "Soni (ОК − МК)"),
    ("part.total_qty", "integer", "part", "Количество всего (деталь × изделие)", "Jami soni (detal × mahsulot)"),
    ("part.used_qty", "integer", "part", "Вошло в раскрой (ИК)", "Kroyga kirgan (ИК)"),
    ("part.copy", "integer", "part", "Номер экземпляра детали (i)", "Detal nusxasi raqami (i)"),
    ("part.copies", "integer", "part", "Число экземпляров (n)", "Nusxalar soni (n)"),
    ("part.counter", "integer", "part", "Счётчик = номер экземпляра ❓", "Hisoblagich = nusxa raqami ❓"),
    ("part.grain", "boolean", "part", "Текстура (Ткт)", "Tekstura (Ткт)"),
    ("part.groove", "boolean", "part", "Есть паз (=)", "Paz bor (=)"),
    ("part.mill", "boolean", "part", "Есть фрезеровка (*)", "Frezalash bor (*)"),
    ("part.drill", "boolean", "part", "Есть сверление (%)", "Parmalash bor (%)"),
    ("part.qr", "string", "part", "Текст QR (MXK:…) для сканера MES", "MES skaneri uchun QR matni (MXK:…)"),
    ("map.index", "integer", "map", "Номер карты кроя", "Kroy kartasi raqami"),
    ("map.total", "integer", "map", "Карт всего", "Kartalar jami"),
    ("map.copies", "integer", "map", "Листов по карте", "Karta bo'yicha listlar"),
    ("map.sheet_length", "double", "map", "Длина листа карты", "Karta listi uzunligi"),
    ("map.sheet_width", "double", "map", "Ширина листа карты", "Karta listi eni"),
    ("map.fill", "double", "map", "Заполнение карты, %", "Karta to'ldirilishi, %"),
    ("map.qr", "string", "map", "Текст QR карты (MXK:…)", "Karta QR matni (MXK:…)"),
    # (CL) Погонажный раскрой (W18): polosa — kroy kartasi (1D); CS/boshqa operatsiyalarda bu o'zgaruvchilar bo'sh (0 / «»)
    ("strip.index", "integer", "strip", "Номер полосы (карты CL)", "Polosa (karta) raqami (CL)"),
    ("strip.total", "integer", "strip", "Карт (полос-схем) всего", "Kartalar (polosa sxemalari) jami"),
    ("strip.copies", "integer", "strip", "Полос по карте", "Karta bo'yicha polosalar"),
    ("strip.length", "double", "strip", "Длина полосы, мм", "Polosa uzunligi, mm"),
    ("strip.width", "double", "strip", "Ширина полосы (= ширина детали), мм", "Polosa eni (= detal eni), mm"),
    ("strip.parts", "integer", "strip", "Деталей в полосе", "Polosadagi detallar soni"),
    ("strip.fill", "double", "strip", "Заполнение полосы, %", "Polosa to'ldirilishi, %"),
    ("strip.offcut", "double", "strip", "Остаток полосы (отход), мм", "Polosa qoldig'i (otxod), mm"),
    ("strip.business", "boolean", "strip", "Остаток полосы деловой", "Polosa qoldig'i deloviy"),
    ("waste.number", "integer", "waste", "Номер остатка (Д№)", "Qoldiq raqami (Д№)"),
    ("waste.length", "double", "waste", "Длина остатка", "Qoldiq uzunligi"),
    ("waste.width", "double", "waste", "Ширина остатка", "Qoldiq eni"),
    ("waste.area", "double", "waste", "Площадь остатка, м²", "Qoldiq maydoni, m²"),
    ("waste.business", "boolean", "waste", "Деловой остаток", "Deloviy qoldiq"),
    ("label.number", "integer", "label", "Порядковый номер этикетки в печати", "Etiketkaning chopdagi tartib raqami"),
    ("label.total", "integer", "label", "Всего этикеток в печати", "Chopdagi jami etiketkalar"),
    ("label.index", "integer", "label", "Номер этикетки одной детали (1…count)", "Bir detal etiketkasi raqami (1…count)"),
    ("label.count", "integer", "label", "Этикеток на одну деталь", "Bir detalga etiketkalar soni"),
    ("label.kind", "string", "label", "Вид: part | waste | product | user", "Turi: part | waste | product | user"),
    ("label.code", "string", "label", "Код для штрихкода (QR/MXK)", "Shtrixkod uchun kod (QR/MXK)"),
    ("label.lang", "string", "label", "Язык печати: ru | uz", "Chop tili: ru | uz"),
    ("label.width", "double", "label", "Ширина этикетки, мм", "Etiketka eni, mm"),
    ("label.height", "double", "label", "Высота этикетки, мм", "Etiketka balandligi, mm"),
]
for _s in SIDES:
    VARS += [(f"edge.{_s}.has", "boolean", "edge", f"Кромка есть ({_s})", f"Kromka bor ({_s})"),
             (f"edge.{_s}.symbol", "string", "edge", f"Символ кромки ({_s})", f"Kromka belgisi ({_s})"),
             (f"edge.{_s}.name", "string", "edge", f"Название кромки ({_s})", f"Kromka nomi ({_s})"),
             (f"edge.{_s}.code", "string", "edge", f"Код кромки ({_s})", f"Kromka kodi ({_s})"),
             (f"edge.{_s}.thickness", "double", "edge", f"Толщина кромки ({_s})", f"Kromka qalinligi ({_s})"),
             (f"edge.{_s}.jointing", "double", "edge", f"Прифуговка ({_s})", f"Prifugovka ({_s})"),
             (f"edge.{_s}.color", "string", "edge", f"Цвет кромки ({_s})", f"Kromka rangi ({_s})"),
             (f"edge.{_s}.lines", "integer", "edge", f"Линий маркировки ({_s})", f"Belgi chiziqlari soni ({_s})")]
VARS += [("edge.count", "integer", "edge", "Число кромкуемых сторон", "Kromkalanadigan tomonlar soni")]
for _s in SIDES:
    VARS += [(f"groove.{_s}.has", "boolean", "groove", f"Паз есть ({_s})", f"Paz bor ({_s})"),
             (f"groove.{_s}.code", "string", "groove", f"Код паза ({_s})", f"Paz kodi ({_s})"),
             (f"groove.{_s}.name", "string", "groove", f"Название паза ({_s})", f"Paz nomi ({_s})"),
             (f"groove.{_s}.width", "double", "groove", f"Ширина паза ({_s})", f"Paz eni ({_s})"),
             (f"groove.{_s}.depth", "double", "groove", f"Глубина паза ({_s})", f"Paz chuqurligi ({_s})"),
             (f"groove.{_s}.offset", "double", "groove", f"Отступ паза ({_s})", f"Paz otstupi ({_s})"),
             (f"groove.{_s}.back", "boolean", "groove", f"Паз с обратной стороны ({_s})", f"Paz orqa tomonda ({_s})")]
for _s, _ru, _uz in (("front", "лицевая", "old (lits)"), ("back", "обратная", "orqa")):      # (SP) Обработка поверхности (W12)
    VARS += [(f"surface.{_s}.has", "boolean", "surface", f"Обработка поверхности есть ({_ru})", f"Sirt ishlovi bor ({_uz})"),
             (f"surface.{_s}.name", "string", "surface", f"Название обработки поверхности ({_ru})", f"Sirt ishlovi nomi ({_uz})"),
             (f"surface.{_s}.code", "string", "surface", f"Код обработки поверхности ({_ru})", f"Sirt ishlovi kodi ({_uz})")]
for _n in range(1, 6):
    VARS += [(f"xnc{_n}.code", "string", "xnc", f"Код CNC-программы {_n}", f"CNC dastur kodi {_n}"),
             (f"xnc{_n}.side", "boolean", "xnc", f"CNC {_n}: лицевая сторона", f"CNC {_n}: old tomon"),
             (f"xnc{_n}.by_size", "boolean", "xnc", f"CNC {_n}: по размеру детали", f"CNC {_n}: detal o'lchami bo'yicha")]

# Taxalluslar: yangi nom → (eski nom, ...). Qiymat bir xil. 03 Ilova B: snake_case nomlar va eski dasturdagi qisqa nomlar.
ALIASES: dict[str, str] = {
    "project_name": "project.name", "project_number": "project.number", "project_date": "project.date",
    "project_crc32": "project.crc32", "project_crc16": "project.crc16", "project_description": "project.description",
    "project_currency": "project.currency", "product_name": "product.name", "product_code": "product.code",
    "product_qty": "product.qty", "product_phone1": "product.phone1", "product_phone2": "product.phone2",
    "product_index": "product.index", "product_description": "product.description", "product_date": "product.date",
    "material_name": "material.name", "material_code": "material.code", "thickness": "part.thickness",
    "part_uid": "part.uid", "part_code": "part.code", "part_name": "part.name", "part_description": "part.description",
    "part_index": "part.index", "counter": "part.counter", "qty": "part.qty", "total_qty": "part.total_qty",
    "used_qty": "part.used_qty", "grain": "part.grain", "groove": "part.groove", "mill": "part.mill", "drill": "part.drill",
    "detail_length": "part.detail_length", "detail_width": "part.detail_width", "saw_length": "part.saw_length",
    "saw_width": "part.saw_width", "length": "part.blank_length", "width": "part.blank_width",
    "detail.length": "part.detail_length", "detail.width": "part.detail_width", "thick": "part.thickness",
    "txt": "part.grain", "count": "part.qty", "totalCount": "part.total_qty", "usedCount": "part.used_qty",
    "name": "part.name", "description": "part.description", "index": "part.index",
    "business": "waste.business", "map_index": "map.index", "remnant_number": "waste.number",
}
for _s in SIDES:
    for _suffix, _field in (("symbol", "s"), ("code", "c"), ("name", "n"), ("thickness", "t"), ("jointing", "j")):
        ALIASES[f"edge_{_s}_{_suffix}"] = f"edge.{_s}.{_suffix}"
        ALIASES[f"e{SIDE_CH[_s]}{_field}"] = f"edge.{_s}.{_suffix}"
ALIASES["surfFront"] = "surface.front.name"           # (SP) lits / orqa sirt ishlovi nomi (inventar LB-070)
ALIASES["surfBack"] = "surface.back.name"
for _n in range(1, 6):
    ALIASES[f"XNC{_n}"] = f"xnc{_n}.code"
    ALIASES[f"xncSide{_n}"] = f"xnc{_n}.side"
    ALIASES[f"xncBSD{_n}"] = f"xnc{_n}.by_size"
# W9 (tayyor shablon fayllarini import): operatsiyadagi raqam va paz qisqa nomlari (grtc grtn grtw grtd grto — yuqori; b/l/r — boshqalar)
ALIASES["indexInOperation"] = "part.index"
ALIASES["index_in_operation"] = "part.index"
for _s in SIDES:
    for _suffix, _field in (("code", "c"), ("name", "n"), ("width", "w"), ("depth", "d"), ("offset", "o")):
        ALIASES[f"gr{SIDE_CH[_s]}{_field}"] = f"groove.{_s}.{_suffix}"

_ZERO = {"string": "", "integer": 0, "double": 0.0, "boolean": False}
DEFAULTS: dict = {name: _ZERO[tp] for name, tp, *_ in VARS}
for _alias, _src in ALIASES.items():
    DEFAULTS[_alias] = DEFAULTS[_src]
DEFAULTS["waste"] = False              # eski «waste» (qoldiq belgisi): qator turi qoldiq bo'lsa true (EnvBuilder.env)
VAR_NAMES = set(DEFAULTS)
VAR_TYPES: dict[str, str] = {n: tp for n, tp, *_ in VARS}


def variable_catalog(lang: str = "ru") -> list[dict]:
    """UI uchun: guruhlar bo'yicha o'zgaruvchilar (+ taxalluslar soni)."""
    groups: dict[str, list[dict]] = {}
    for name, tp, grp, ru, uz in VARS:
        groups.setdefault(grp, []).append({"name": name, "type": tp, "title": pick_for(lang, ru, uz)})
    return [{"key": k, "vars": v} for k, v in groups.items()]


# ───────────────────────── Qatorlar ─────────────────────────
@dataclass(slots=True)
class Item:
    kind: str                                  # part | waste | product | user
    op: Optional[Operation] = None
    part: Optional[Part] = None
    part_index: int = 0
    copy: int = 1
    copies: int = 1
    map: object = None                         # CutMap | None
    off: object = None                         # Offcut | None
    product: Optional[Product] = None
    product_index: int = 0
    row: Optional[dict] = None                 # source=user qatori
    sub: int = 1                               # label.index
    subs: int = 1                              # label.count


LABEL_SOURCE_TYPES = (OpType.CS, OpType.CL)       # etiketka manbai: listli (CS) va pogonaj (CL, W18) kroy operatsiyalari


def _cs_ops(project: Project, lb: LBParams) -> list[Operation]:
    return [o for o in project.operations if o.type in LABEL_SOURCE_TYPES and (not lb.cs_op_id or o.id == lb.cs_op_id)]


def _part_seq(project: Project, op: Operation, include_zero: bool = False, once: bool = False) -> Iterator[tuple[Part, int, object]]:
    """(detal, operatsiyadagi raqami, karta | None) — kroy kartalari bo'yicha (arradan chiqish tartibi), kroy bo'lmasa ro'yxat bo'yicha.
    `include_zero` — soni 0 bo'lgan detal ham bir marta chiqadi (kroysiz holatda); `once` — kroysiz holatda har detal bir marta
    («Для каждой детали» o'chiq: katta sonli detal 10^N marta aylanmasin)."""
    index = {p.id: i for i, p in enumerate(op.parts, 1)}
    parts = {p.id: p for p in op.parts}
    if op.result and op.result.maps:
        for m in op.result.maps:
            for _ in range(max(1, m.copies)):
                for pl in m.placements:
                    p = parts.get(pl.part_id)
                    if p is not None:
                        yield p, index[p.id], m
    else:
        for p in op.parts:
            reps = effective_qty(project, p)
            if once:
                reps = min(reps, 1)
            for _ in range(reps if reps > 0 or not include_zero else 1):
                yield p, index[p.id], None


def iter_items(project: Project, lb: LBParams) -> Iterator[Item]:
    """Chop qatorlari (kerakli tartibda). Tez oqim: ro'yxat yig'ilmaydi."""
    if lb.source == "products":
        for idx, pr in enumerate(project.products, 1):
            if lb.product_only_nonzero and pr.qty <= 0:
                continue
            n = max(1, pr.qty) if lb.product_each else 1
            for c in range(1, n + 1):
                yield Item("product", product=pr, product_index=idx, copy=c, copies=n)
        return
    if lb.source == "user":
        for row in lb.data:
            try:
                q = int(float(row.get("qty", 1)))
            except (TypeError, ValueError):
                q = 1
            for c in range(1, max(0, min(q, LB_MAX_LABELS + 1)) + 1):
                yield Item("user", row=row, copy=c, copies=q)
        return
    sel = lb.selected_uids()
    if lb.print_parts:
        for op in _cs_ops(project, lb):
            seen: set[str] = set()
            counters: dict[str, int] = {}
            for p, idx, m in _part_seq(project, op, include_zero=not lb.part_each and not lb.part_only_nonzero,
                                      once=not lb.part_each):
                n = effective_qty(project, p)
                if (lb.part_only_nonzero and n <= 0) or (lb.part_each and n <= 0) or (sel is not None and p.uid not in sel):
                    continue
                if not lb.part_each:
                    if p.id in seen:
                        continue
                    seen.add(p.id)
                    i = 1
                else:
                    counters[p.id] = counters.get(p.id, 0) + 1
                    i = counters[p.id]
                for s in range(1, lb.label_count + 1):
                    yield Item("part", op=op, part=p, part_index=idx, copy=i, copies=n, map=m, sub=s, subs=lb.label_count)
    if lb.print_wastes:
        for op in _cs_ops(project, lb):
            if not (op.result and op.result.maps):
                continue
            for m in op.result.maps:
                for off in m.offcuts:
                    if off.kind != "remnant" or (lb.waste_business_only and not off.business):
                        continue
                    n = max(1, m.copies) if lb.waste_each else 1
                    for c in range(1, n + 1):
                        yield Item("waste", op=op, map=m, off=off, copy=c, copies=n)


def count_items(project: Project, lb: LBParams) -> dict:
    """Etiketkalar soni (arifmetika bilan — juda katta sonlarda ham tez): {total, parts, wastes, products, user}."""
    out = dict(total=0, parts=0, wastes=0, products=0, user=0)
    if lb.source == "products":
        for pr in project.products:
            if lb.product_only_nonzero and pr.qty <= 0:
                continue
            out["products"] += max(1, pr.qty) if lb.product_each else 1
    elif lb.source == "user":
        for row in lb.data:
            try:
                out["user"] += max(0, int(float(row.get("qty", 1))))
            except (TypeError, ValueError):
                out["user"] += 1
    else:
        sel = lb.selected_uids()
        if lb.print_parts:
            for op in _cs_ops(project, lb):
                if op.result and op.result.maps:
                    parts = {p.id: p for p in op.parts}
                    per: dict[str, int] = {}
                    for m in op.result.maps:
                        for pl in m.placements:
                            if pl.part_id in parts:
                                per[pl.part_id] = per.get(pl.part_id, 0) + max(1, m.copies)
                    for pid, k in per.items():
                        p = parts[pid]
                        n = effective_qty(project, p)
                        if (lb.part_only_nonzero and n <= 0) or (sel is not None and p.uid not in sel):
                            continue
                        out["parts"] += (k if lb.part_each else 1) * lb.label_count
                else:
                    for p in op.parts:
                        n = effective_qty(project, p)
                        if (lb.part_only_nonzero and n <= 0) or (sel is not None and p.uid not in sel):
                            continue
                        out["parts"] += (n if lb.part_each else (1 if n > 0 or not lb.part_only_nonzero else 0)) * lb.label_count
        if lb.print_wastes:
            for op in _cs_ops(project, lb):
                if op.result and op.result.maps:
                    for m in op.result.maps:
                        for off in m.offcuts:
                            if off.kind == "remnant" and (not lb.waste_business_only or off.business):
                                out["wastes"] += max(1, m.copies) if lb.waste_each else 1
    out["total"] = out["parts"] + out["wastes"] + out["products"] + out["user"]
    return out


# ───────────────────────── Muhit ─────────────────────────
def _date_s(d: Optional[date]) -> str:
    return d.strftime("%d.%m.%Y") if d else ""


def _crc(name: str, fn: str) -> int:
    return int(expr.evaluate(f"{fn}(s)", {"s": name or ""}))


def _op_thickness(op: Operation) -> float:
    """Material qalinligi: CS — `cs_material`, CL — `cl.thickness` (W18)."""
    if op.cs_material:
        return float(op.cs_material.thickness)
    return float(op.cl.thickness) if op.cl is not None else 0.0


class EnvBuilder:
    """Har chop uchun bitta: loyiha/operatsiya/detal qismlari keshlanadi, har etiketkaga yengil lug'at beriladi."""

    def __init__(self, project: Project, lb: LBParams, total: int = 0, lang: str = "ru"):
        self.project = project
        self.lb = lb
        self.total = total
        self.number = 0
        self.sizes = edge_map(project)
        self.el_ops = {o.id: o for o in project.operations if o.type == OpType.EL}
        self.gr_ops = {o.id: o for o in project.operations if o.type == OpType.GR}
        self.xnc_ops = {o.id: o for o in project.operations if o.type == OpType.XNC}
        self.sp_ops = {o.id: o for o in project.operations if o.type == OpType.SP}
        self.product_index = {p.id: i for i, p in enumerate(project.products, 1)}
        self.products = {p.id: p for p in project.products}
        self.user_fields = user_field_specs(lb.fields)           # source=user: {nom: (tur, standart qiymat)}
        self.user_names = list(self.user_fields)
        self.base = dict(DEFAULTS)
        for n, (tp, dv) in self.user_fields.items():
            self.base[f"user.{n}"] = coerce_user_value(None, tp, dv)
        pr = project
        self.base.update({
            "project.name": pr.name, "project.number": pr.number, "project.date": _date_s(pr.order_date),
            "project.ready_date": _date_s(pr.ready_date), "project.description": pr.note, "project.currency": pr.currency,
            "project.owner": pr.owner, "project.customer": pr.customer, "project.mes": pr.mes_order_ref or "",
            "project.crc16": _crc(pr.name, "crc16"), "project.crc32": _crc(pr.name, "crc32"),
            "label.width": lb.label_size()[0], "label.height": lb.label_size()[1], "label.total": total,
            "label.lang": "uz" if norm_lang(lang) != "ru" else "ru",
        })
        for pr_ in project.products:         # mahsulot dasturi o'zgaruvchilari (W12): `product.<nom>` — dasturi yo'q mahsulotda 0
            for k in product_program.ctx_vars(pr_):
                self.base.setdefault(k, 0.0)
        self._op_cache: dict[str, dict] = {}
        self._part_cache: dict[tuple[str, str], dict] = {}

    # — qismlar —
    def _product(self, pr: Optional[Product], idx: int) -> dict:
        if pr is None:
            return {}
        d = {"product.index": idx, "product.name": pr.name, "product.code": pr.code, "product.qty": pr.qty,
             "product.count": pr.qty, "product.description": pr.description, "product.phone1": pr.phone1,
             "product.phone2": pr.phone2, "product.date": pr.ready_date or _date_s(self.project.ready_date),
             "product.order": pr.order_info}
        for k, v in product_program.ctx_vars(pr).items():       # mahsulot «Программа» o'zgaruvchilari; mavjud nom ustun
            d.setdefault(k, v)
        return d

    def _op(self, op: Operation) -> dict:
        d = self._op_cache.get(op.id)
        if d is None:
            d = {"material.name": op.name, "material.code": op.code, "material.thickness": _op_thickness(op)}
            self._op_cache[op.id] = d
        return d

    def _part(self, op: Operation, p: Part) -> dict:
        key = (op.id, p.id)
        d = self._part_cache.get(key)
        if d is not None:
            return d
        project = self.project
        cut = op.cs_cut
        cl = op.cl if op.type == OpType.CL else None
        pw = p.model_copy(update={"width": float(cl.width)}) if cl is not None else p       # (CL) detal eni = polosa eni
        sz = compute_sizes(pw, SizeMode(project.size_mode), self.sizes, cut.machining_allowance if cut else 0)
        th = _op_thickness(op)
        marks = part_marks(p, project)
        prod = self.products.get(p.product_id or "")
        d = self._product(prod, self.product_index.get(p.product_id or "", 0))
        d.update({
            "part.id": p.uid, "part.uid": p.uid, "part.code": p.code, "part.name": p.name, "part.description": p.description,
            "part.title": (marks + " " if marks else "") + p.name, "part.marks": marks,
            "part.length": float(p.length), "part.width": float(pw.width),
            "part.blank_length": float(sz.blank[0]), "part.blank_width": float(sz.blank[1]),
            "part.detail_length": float(sz.detail[0]), "part.detail_width": float(sz.detail[1]),
            "part.jointed_length": float(sz.jointed[0]), "part.jointed_width": float(sz.jointed[1]),
            "part.saw_length": float(sz.saw[0]), "part.saw_width": float(sz.saw[1]),
            "part.thickness": th, "part.dims": f"{fmt(p.length)} × {fmt(pw.width)} × {fmt(th)}",
            "part.qty": effective_qty(project, p), "part.total_qty": total_qty(project, p), "part.used_qty": p.used_qty,
            "part.grain": bool(p.grain), "part.groove": "=" in marks, "part.mill": part_mill_flag(p, project), "part.drill": "%" in marks,
        })
        # kromka
        ed = part_edges(p, project)
        n_edges = 0
        for s in SIDES:
            e = ed.get(s)
            ref = getattr(p, f"edge_{s}")
            el_op = self.el_ops.get(ref.op_id) if ref and ref.op_id else None
            if e is not None:
                n_edges += 1
                el = el_op.el if el_op is not None else None
                d.update({f"edge.{s}.has": True, f"edge.{s}.symbol": e["symbol"], f"edge.{s}.name": e["name"],
                          f"edge.{s}.code": el_op.code if el_op else "", f"edge.{s}.color": e["color"],
                          f"edge.{s}.lines": e["lines"], f"edge.{s}.thickness": float(el.thickness) if el else 0.0,
                          f"edge.{s}.jointing": float(el.jointing_width) if el else 0.0})
        d["edge.count"] = n_edges
        # paz
        for s in SIDES:
            g = getattr(p, f"groove_{s}")
            gop = self.gr_ops.get(g.op_id) if g and g.op_id else None
            if gop is not None and gop.gr is not None:
                d.update({f"groove.{s}.has": True, f"groove.{s}.code": gop.code, f"groove.{s}.name": gop.name,
                          f"groove.{s}.width": float(gop.gr.width), f"groove.{s}.depth": float(gop.gr.depth),
                          f"groove.{s}.offset": float(gop.gr.offset), f"groove.{s}.back": bool(g.back_side)})
        # sirt ishlovi (SP): lits / orqa
        for sd, ref in (("front", p.surface_face_op), ("back", p.surface_back_op)):
            sop = self.sp_ops.get(ref) if ref else None
            if sop is not None:
                d.update({f"surface.{sd}.has": True, f"surface.{sd}.name": sop.name, f"surface.{sd}.code": sop.code})
        # CNC dasturlar (5 tagacha)
        n = 0
        for xid in p.xnc_op_ids:
            xop = self.xnc_ops.get(xid)
            if xop is None or n >= 5:
                continue
            n += 1
            d.update({f"xnc{n}.code": xop.code, f"xnc{n}.side": bool(xop.xnc.face_side) if xop.xnc else False,
                      f"xnc{n}.by_size": bool(xop.xnc.by_part_size) if xop.xnc else False})
        d.update(self._op(op))
        self._part_cache[key] = d
        return d

    def env(self, it: Item) -> dict:
        """Bitta etiketka uchun muhit (xom lug'at: `label.number` har chaqiruvda 1 ga oshadi)."""
        self.number += 1
        e = dict(self.base)
        project = self.project
        e["label.number"] = self.number
        e["label.kind"] = it.kind
        e["label.index"] = it.sub
        e["label.count"] = it.subs
        if it.kind == "part" and it.part is not None and it.op is not None:
            e.update(self._part(it.op, it.part))
            e["part.index"] = it.part_index
            e["part.copy"] = it.copy
            e["part.copies"] = it.copies
            e["part.counter"] = it.copy
            code = qr_text(project, it.part.uid, it.copy, it.copies)
            e["part.qr"] = code
            e["label.code"] = code
            self._map(e, it.op, it.map)
        elif it.kind == "waste" and it.op is not None and it.off is not None:
            off = it.off
            e.update(self._op(it.op))
            self._map(e, it.op, it.map)
            e.update({"waste.number": int(off.number), "waste.length": float(off.length), "waste.width": float(off.width),
                      "waste.area": round(off.length * off.width / 1e6, 4), "waste.business": bool(off.business)})
            e["label.code"] = e["map.qr"]
            e["part.copy"] = it.copy
            e["part.copies"] = it.copies
        elif it.kind == "product" and it.product is not None:
            e.update(self._product(it.product, it.product_index))
            e["part.copy"] = it.copy
            e["part.copies"] = it.copies
            e["label.code"] = f"MXK:{project.number}:P{it.product_index}:{it.copy}/{it.copies}"
        elif it.kind == "user" and it.row is not None:
            for n, (tp, dv) in self.user_fields.items():
                e[f"user.{n}"] = coerce_user_value(it.row.get(n), tp, dv)
            e["part.copy"] = it.copy
            e["part.copies"] = it.copies
        # taxalluslar
        for alias, src in ALIASES.items():
            if src in e:
                e[alias] = e[src]
        e["waste"] = it.kind == "waste"
        if it.kind == "waste":        # W9: tayyor shablonlarda qoldiq qatorida length/width/count/indexInOperation — qoldiq o'lchami, soni, raqami ❓
            e["length"] = e["detail.length"] = e["waste.length"]
            e["width"] = e["detail.width"] = e["waste.width"]
            e["count"] = e["totalCount"] = e["usedCount"] = it.copies
            e["indexInOperation"] = e["index_in_operation"] = e["waste.number"]
        return e

    def _map(self, e: dict, op: Operation, m) -> None:
        if m is None:
            return
        res = op.result
        e.update({"map.index": m.index, "map.total": len(res.maps) if res else 0, "map.copies": m.copies,
                  "map.sheet_length": float(m.sheet_length), "map.sheet_width": float(m.sheet_width),
                  "map.fill": float(m.fill_percent), "map.qr": map_qr_text(self.project, op.id, m.index)})
        if op.type == OpType.CL:                               # (CL) polosa o'zgaruvchilari (W18); otxod — kartadagi oxirgi bo'lak
            off = next((o for o in reversed(m.offcuts) if o.kind in ("remnant", "waste")), None)
            e.update({"strip.index": m.index, "strip.total": len(res.maps) if res else 0, "strip.copies": m.copies,
                      "strip.length": float(m.sheet_length), "strip.width": float(m.sheet_width),
                      "strip.parts": int(m.parts_count), "strip.fill": float(m.fill_percent),
                      "strip.offcut": float(off.length) if off is not None else 0.0,
                      "strip.business": bool(off.business) if off is not None else False})


# ───────────────────────── Namuna (shablon ko'rinishi, loyihasiz) ─────────────────────────
def sample_project(lang: str = "ru") -> tuple[Project, Operation]:
    """Namuna loyiha (saqlanmaydi): kromkali detal, mahsulot, kroy kartasi — shablon jonli ko'rinishi uchun."""
    from ..models import CSCutParams, CSMaterialParams, CutMap, CuttingResult, EdgeRef, ELParams, Offcut, Placement
    uz = norm_lang(lang) != "ru"
    L = lambda ru, u: pick_for(lang, ru, u)          # noqa: E731 — namuna nomlari joriy yozuvda (uz-Cyrl — kirill)
    el = Operation(type=OpType.EL, code="PVC04/19", name="ПВХ 0.4/19", el=ELParams(symbol="A", color="#d33", thickness=0.4))
    el2 = Operation(type=OpType.EL, code="PVC2/19", name="ПВХ 2/19", el=ELParams(symbol="B", color="#36c", thickness=2))
    prod = Product(name=L("Шкаф трёхдверный", "Shkaf 3-eshikli"), code="SH-300", qty=2, phone1="+998 90 123-45-67")
    part = Part(uid=7, name=L("Боковая панель", "Yon panel"), code="01_017", length=748, width=468, qty=2,
                product_id=prod.id, grain=True, edge_top=EdgeRef(op_id=el.id), edge_left=EdgeRef(op_id=el2.id))
    part2 = Part(uid=8, name=L("Полка", "Tokcha"), length=500, width=300, qty=1, product_id=prod.id)
    cs = Operation(type=OpType.CS, code="LDSP16", name=L("ЛДСП 16 Белый", "LDSP 16 Oq"),
                   cs_material=CSMaterialParams(thickness=16), cs_cut=CSCutParams(), parts=[part, part2])
    m = CutMap(index=3, sheet_id="s", sheet_length=2750, sheet_width=1830, copies=1, fill_percent=91.5, parts_count=2,
               placements=[Placement(part_id=part.id, part_uid=7, x=0, y=0, length=748, width=468),
                           Placement(part_id=part.id, part_uid=7, x=750, y=0, length=748, width=468)],
               offcuts=[Offcut(x=0, y=500, length=1200, width=600, kind="remnant", number=2, business=True)])
    cs.result = CuttingResult(maps=[m], total_sheets=1, total_parts=2)
    project = Project(number=1000123, name=L("Шкаф Каримов", "Shkaf Karimov"), currency="UZS",
                      operations=[el, el2, cs], products=[prod], customer="Karimov", owner="MebeliX")
    return project, cs


def sample_env(kind: str = "part", lang: str = "ru", lb: Optional[LBParams] = None, row: Optional[dict] = None) -> dict:
    """Namuna etiketka muhiti (kind: part | waste | product | user). `row` — kind=user uchun bitta qator (berilmasa: `lb.data[0]`
    yoki maydonlar bo'yicha namuna qator)."""
    lb = lb or LBParams()
    project, cs = sample_project(lang)
    part, m = cs.parts[0], cs.result.maps[0]
    eb = EnvBuilder(project, lb, total=1, lang=lang)
    if kind == "waste":
        it = Item("waste", op=cs, map=m, off=m.offcuts[0])
    elif kind == "product":
        it = Item("product", product=project.products[0], product_index=1, copy=1, copies=2)
    elif kind == "user":
        row = row if isinstance(row, dict) else (lb.data[0] if lb.data and isinstance(lb.data[0], dict) else sample_row(lb.fields, lang))
        it = Item("user", row=row, copy=1, copies=1)
    else:
        it = Item("part", op=cs, part=part, part_index=1, copy=1, copies=2, map=m)
    return eb.env(it)
