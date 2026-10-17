"""Loyihani `.project` (XML) fayliga eksport — `plugins/legacy_project.py` importerining TESKARISI.

Foydalanuvchi ruxsati (2026-10-02): `.project` GibLabning OCHIQ va tavsiflangan fayl formati; tayyor faylni import va eksport
qilish — mijoz ixtiyori (tizim ommabop bo'lishi kerak). Eksport faqat shu ochiq tavsifga va foydalanuvchining o'z fayllaridagi
tuzilishga (teg/atribut nomlari) asoslanadi; GibLab dasturi, kaliti va litsenziyasiga tegilmaydi.

Nima yoziladi (importer o'qiydigan hamma narsa):
  * `<project>`: name, currency, version, date (tayyorlik), orderDate, description, project.uuid (yangi UUID);
  * mahsulotlar `good typeId="product"` (+ ichida detallar: o'lchamlar — l/w, dl/dw, jl/jw va pilniy cl/cw; count, minusCount,
    txt, name, code, part.designation, pripusk, guruhlash, kromka `elt/elb/ell/elr`, paz `grt…`), phone1/2, description,
    product.order va `product.*` qo'shimcha parametrlar;
  * har CS: `tool.cutting` (arra), `sheet` (material + listlar/qoldiq qatorlari `part`) va `operation CS` (parametrlar);
  * har EL: `tool.edgeline`, `band` (kromka materiali) va `operation EL`; GR; XNC (`program` XML — `project_export_xnc`);
    O (komplektatsiya: `simple` good + `material` havolalari, egasi — mahsulot ichida `<operation id="N"/>` + `owner`);
    LB (sahifa parametrlari, `fields`, eski `program`).
  * detal id lari = `Part.uid` (onlayn tizimdagi «ID»; qayta import o'sha raqamlarni qaytaradi), qolgan id lar — eng katta
    uid dan keyingi raqamlar (hammasi loyiha bo'ylab noyob).
Nima yozilmaydi: kroy NATIJASI (kartalar `data/draw`, statistika `cFilling…`, narx jami `cost*`, ishlatilgan soni) — qabul
qiluvchi dastur kroyni qayta hisoblaydi; formatda joyi yo'q maydonlar (buyurtmachi, holat, MES havolasi, XNC koordinata boshi
burchagi …) — ular ogohlantirishlarda sanab o'tiladi.

`version`: formatning o'z versiyasi — tavsifda «По умолчанию: 1», namunada `version="1"`; real fayllardagi 21052101 / 23051701 —
GibLab build sanalari, biz ularni o'ylab topmaymiz: `version="1"` yoziladi.
"""
from __future__ import annotations

import base64
import re
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Optional

from ..i18n import _
from ..models import ELParams, LBParams, Operation, OpType, Part, Product, Project, SizeMode
from ..plugins.legacy_project import COST_TYPE, SIZE_MODE, _TZ, _UID_MAX
from .project_export_xnc import PROLOG, boolean, clean, num, program_xml
from .project_schema import GOOD_ATTRS, PART_PATTERN_ATTR, PRODUCT_PART_ATTRS, GOOD_PATTERN_ATTRS, validate_project_xml
from .sizes import compute_sizes

FORMAT_VERSION = "1"                                   # tavsifdagi standart (Example1: version="1")
COST_ID = {v: k for k, v in COST_TYPE.items()}         # OpCostBase → GibLab «cCostType»
MODE_ID = {v: k for k, v in SIZE_MODE.items()}         # SizeMode → cSizeMode
SUPPORTED = (OpType.CS, OpType.CL, OpType.EL, OpType.GR, OpType.XNC, OpType.O, OpType.LB, OpType.SP)
_ATTR_KEY = re.compile(r"^product\.[A-Za-z0-9_][A-Za-z0-9_.\-]{0,89}$")     # mahsulot «Дополнительные параметры»: product.<nom>

# W9 (etiketka shablonini eksport qilish) shu ro'yxatga funksiya qo'shadi: (LBParams) → `program` matni yoki None.
LB_PROGRAM_EXPORTERS: list[Callable[[LBParams], Optional[str]]] = []


def user_attrs(params: dict[str, str], prefix: str, reserved) -> dict[str, str]:
    """Foydalanuvchi parametrlari («Настроенный Параметры» ustunlari) → XML atributlari: faqat format nomlash qoidasiga mos
    («part.<nom>» — detalda, «material.<nom>» — oddiy materialda) va formatning o'z atributlari bilan to'qnashmaydigan nomlar.
    Boshqa nomli parametrlar `.project` ga yozilmaydi (`.mxk.json` da saqlanadi)."""
    pat = PART_PATTERN_ATTR if prefix == "part." else GOOD_PATTERN_ATTRS["simple"]
    return {k: _s(v) for k, v in (params or {}).items() if k.startswith(prefix) and k not in reserved and pat.match(k) and v != ""}


class ExportError(Exception):
    """Eksport qilingan XML o'z sxemamizdan o'tmadi (dastur xatosi) — fayl berilmaydi."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors[:5]))
        self.errors = errors


@dataclass
class ExportResult:
    xml: bytes
    filename: str
    warnings: list[dict] = field(default_factory=list)        # [{level: "warn" | "info", code, text}]
    counts: dict = field(default_factory=dict)


def _s(v) -> str:
    return clean(v if v is not None else "")


def _ms(d: date) -> str:
    """Sana → epoch millisekund (mahalliy 12:00: istalgan vaqt mintaqasida ham o'sha kun)."""
    return str(int(datetime(d.year, d.month, d.day, 12, tzinfo=_TZ).timestamp() * 1000))


def _r4(v: float) -> str:
    return num(round(v, 4))


def safe_filename(project: Project) -> str:
    base = re.sub(r'\s+', " ", re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " ", project.name or "")).strip(" .")[:80].strip()
    return f"{base or project.number or 'project'}.project"


class _Exporter:
    def __init__(self, project: Project):
        self.p = project
        self.warns: list[dict] = []
        self.dropped: set[str] = set()
        self._seq = 0
        self.edges: dict[str, ELParams] = {o.id: o.el for o in project.operations if o.type == OpType.EL and o.el}
        self.op_eid: dict[str, str] = {}
        self.part_eid: dict[int, str] = {}                  # id(Part) → eksportdagi id
        self.first_eid: dict[str, str] = {}                 # Part.id → birinchi nusxasining id si
        self.edge_users: dict[str, list[str]] = {}          # EL op id → detal eid lari
        self.groove_users: dict[str, list[str]] = {}
        self.sp_users: dict[str, list[str]] = {}
        self.sp_back_only: set[str] = set()                 # faqat orqa tomoni SP ga bog'langan detali bor SP operatsiyalar
        self.op_by_id: dict[str, Operation] = {}
        self.part_by_pid: dict[str, Part] = {}
        self.xnc_links: dict[str, list[Part]] = {}          # XNC op id → unga havola qilgan detallar
        self.counts: dict = {}

    # ── yordamchilar ──
    def nid(self) -> str:
        self._seq += 1
        return str(self._seq)

    def warn(self, key: str, /, level: str = "warn", **kw) -> None:
        self.warns.append(dict(level=level, code=key, text=_("exp_" + key, **kw)))

    @staticmethod
    def _opname(op: Operation) -> str:
        return op.name or op.code or op.type.value

    # ── asosiy ──
    def build(self) -> ET.Element:
        p = self.p
        ops = [o for o in p.operations if o.type in SUPPORTED]
        for o in p.operations:
            if o.type not in SUPPORTED:
                self.warn("op_skipped", t=o.type.value, name=self._opname(o))
        cs_ops = [o for o in ops if o.type in (OpType.CS, OpType.CL)]      # detalli kroy operatsiyalari (CL — W11, cl_export.py)
        self.op_by_id = {o.id: o for o in ops}
        for o in cs_ops:                                    # XNC → bog'langan detallar (bir marta, O(N))
            for pt in o.parts:
                self.part_by_pid.setdefault(pt.id, pt)
                for xid in pt.xnc_op_ids:
                    self.xnc_links.setdefault(xid, []).append(pt)
        mode = p.size_mode
        dims = {SizeMode.BLANK: ("l", "w"), SizeMode.DETAIL: ("dl", "dw"), SizeMode.JOINTED: ("jl", "jw")}[mode]

        # id lar: detallar — `Part.uid` (onlayn tizimdagi «ID»; qayta import o'sha raqamlarni qaytaradi); qolganlari (mahsulot,
        # operatsiya, asbob, list qatorlari, uid siz yoki takror uid li detallar) — eng katta uid dan keyingi raqamlar;
        # hammasi butun loyiha bo'ylab noyob (sxema shuni talab qiladi)
        self._seq = max((pt.uid for o in cs_ops for pt in o.parts if 0 < pt.uid <= _UID_MAX), default=0)
        prod_eid = {pr.id: self.nid() for pr in p.products}
        for o in ops:
            self.op_eid[o.id] = self.nid()
        by_prod: dict[str, list[tuple[Operation, Part]]] = {pr.id: [] for pr in p.products}
        orphans: list[tuple[Operation, Part]] = []
        for o in cs_ops:
            for pt in o.parts:
                (by_prod[pt.product_id] if pt.product_id in by_prod else orphans).append((o, pt))
        orphan_eid = None
        if orphans:
            orphan_eid = self.nid()
            self.warn("noproduct", n=len(orphans), name=_("exp_orphan_name"))
        # detal qatorlari: bir xil detal (mahsulot, uid, atributlar) bir nechta kroy operatsiyasida (importerdagi nusxalar) —
        # BITTA qator, operatsiyalar o'sha id ga havola qiladi (real fayllardagidek; qayta import nusxalarni o'sha uid bilan beradi)
        taken: set[str] = set()
        shared: dict[tuple, str] = {}
        part_rows: list[tuple[str, dict[str, str]]] = []        # (mahsulot kaliti, atributlar id bilan) — yoziladigan qatorlar
        for pid, lst in list(by_prod.items()) + [("", orphans)]:
            for op, pt in lst:
                attrs, dangling = self._part_attrs(op, pt, dims)
                key = (pid, pt.uid, tuple(sorted(attrs.items())))
                eid = shared.get(key) if 0 < pt.uid <= _UID_MAX else None
                if eid is None:
                    eid = str(pt.uid) if 0 < pt.uid <= _UID_MAX and str(pt.uid) not in taken else self.nid()
                    taken.add(eid)
                    shared[key] = eid
                    part_rows.append((pid, {"id": eid, **attrs}))
                    if dangling:
                        self.warn("dangling_ref", uid=pt.uid, n=dangling)
                self.part_eid[id(pt)] = eid
                self.first_eid.setdefault(pt.id, eid)
                self._register_part(pt, eid)

        root = ET.Element("project")
        if p.name:
            root.set("name", _s(p.name))
        if p.currency:
            root.set("currency", _s(p.currency))
        root.set("version", FORMAT_VERSION)
        root.set("date", _ms(p.ready_date))
        root.set("orderDate", _ms(p.order_date))
        if p.note:
            root.set("description", _s(p.note))
        root.set("project.uuid", str(uuid.uuid4()))
        if p.customer or p.mes_order_ref or p.status:
            self.dropped.add(_("exp_drop_order"))

        # 1) mahsulotlar va detallar
        prod_el: dict[str, ET.Element] = {}
        for pr in p.products:
            g = ET.SubElement(root, "good", id=prod_eid[pr.id], typeId="product")
            self._product_attrs(g, pr)
            prod_el[pr.id] = g
        if orphans and orphan_eid:
            g = ET.SubElement(root, "good", id=orphan_eid, typeId="product", name=_("exp_orphan_name"), count="1")
            prod_el[""] = g
        for pid, a in part_rows:
            ET.SubElement(prod_el[pid], "part", a)
        for op in ops:                                  # O egasi: mahsulot ichida `<operation id="N"/>` (real fayllardagidek)
            if op.type == OpType.O and op.o and op.o.owner_product_id in prod_el:
                ET.SubElement(prod_el[op.o.owner_product_id], "operation", id=self.op_eid[op.id])

        # 2) goods (asbob + material) — har operatsiya uchun, keyin operatsiyalar o'zi (real fayllardagi tartib)
        op_els: list[ET.Element] = []
        for op in ops:
            if op.type == OpType.CS:
                op_els.append(self._cs(root, op, mode))
            elif op.type == OpType.CL:
                from .cl_export import cl_operation
                op_els.append(cl_operation(self, root, op, mode))
            elif op.type == OpType.EL:
                op_els.append(self._el(root, op))
            elif op.type == OpType.GR:
                op_els.append(self._gr(op))
            elif op.type == OpType.XNC:
                op_els.append(self._xnc(op))
            elif op.type == OpType.O:
                op_els.append(self._o(root, op, prod_eid))
            elif op.type == OpType.LB:
                op_els.append(self._lb(op))
            elif op.type == OpType.SP:
                op_els.append(self._sp(op))
        root.extend(op_els)
        if any(o.result and o.result.maps for o in cs_ops):
            self.warn("results_note", level="info")
        if self.dropped:
            self.warn("dropped", level="info", what=", ".join(sorted(self.dropped)))
        self.counts = dict(products=len(p.products) + (1 if orphans else 0), part_rows=len(part_rows),
                           operations={t.value: sum(1 for o in ops if o.type == t) for t in SUPPORTED
                                       if any(o.type == t for o in ops)},
                           skipped_operations=len(p.operations) - len(ops))
        return root

    # ── mahsulot / detal ──
    def _product_attrs(self, g: ET.Element, pr: Product) -> None:
        if pr.code:
            g.set("code", _s(pr.code))
        g.set("name", _s(pr.name))
        g.set("count", str(pr.qty))
        if pr.phone1:
            g.set("phone1", _s(pr.phone1))
        if pr.phone2:
            g.set("phone2", _s(pr.phone2))
        if pr.description:
            g.set("description", _s(pr.description))
        if pr.order_info:
            g.set("product.order", _s(pr.order_info))
        legacy = getattr(pr, "legacy_program", "")           # W12: importdagi mahsulot dasturi matni — yo'qolmasin
        if legacy:
            g.set("program", _s(legacy))
        elif getattr(pr, "program", None):                   # MebeliX da yozilgan dastur: formatda teg nomlari tavsiflanmagan
            self.warn("prog_skipped", name=pr.name)
        for k, v in pr.extra.items():
            key = k.strip()
            if not _ATTR_KEY.match(key) or key == "product.order":
                self.warn("extra_key", name=pr.name, k=key[:40])
                continue
            g.set(key, _s(v))
        if pr.ready_date:
            self.dropped.add(_("exp_drop_product_date"))

    def _part_attrs(self, op: Operation, pt: Part, dims: tuple[str, str]) -> tuple[dict[str, str], int]:
        """Detal qatori atributlari (id siz) va «osilib qolgan» (EL/GR bo'lmagan) havolalar soni. Ro'yxatga olish va yozish alohida
        (`_register_part`, `build`): bir xil detal ikki kroy operatsiyasida bitta qator bo'lishi uchun atributlar solishtiriladi."""
        cut = op.cs_cut
        a: dict[str, str] = {}
        if pt.name:
            a["name"] = _s(pt.name)
        if pt.code:
            a["code"] = _s(pt.code)
        if pt.description:
            a["part.designation"] = _s(pt.description)
        a["count"] = str(pt.qty)
        a["minusCount"] = str(pt.minus_qty)
        a["txt"] = boolean(pt.grain)
        if op.type == OpType.CL:                            # (CL) eni = polosa eni; hisoblanmagan detal — xom manfiy uzunlik (W11)
            from .cl_export import part_size_attrs
            a.update(part_size_attrs(self.p, op, pt, dims, self.edges))
        else:
            a[dims[0]] = num(pt.length)
            a[dims[1]] = num(pt.width)
            if pt.length > 0 and pt.width > 0:              # qolgan o'lchamlar (nol qatorda — faqat rejim atributi)
                s = compute_sizes(pt, self.p.size_mode, self.edges, cut.machining_allowance if cut else 0)
                for kl, kw_, vals in (("l", "w", s.blank), ("dl", "dw", s.detail), ("jl", "jw", s.jointed), ("cl", "cw", s.saw)):
                    if kl not in a and vals[0] >= 0 and vals[1] >= 0:
                        a[kl], a[kw_] = _r4(vals[0]), _r4(vals[1])
        for attr, v in (("allowanceT", pt.allow_top), ("allowanceB", pt.allow_bottom), ("allowanceL", pt.allow_left),
                        ("allowanceR", pt.allow_right)):
            if v > 0:
                a[attr] = num(v)
        if pt.group_by != "none":
            a["groupInBlock"] = "1" if pt.group_by == "length" else "2"
            a["groupInBlockMC"] = str(pt.group_min)
            a["groupInBlockMaxC"] = str(pt.group_max)
        ua = user_attrs(pt.user_params, "part.", PRODUCT_PART_ATTRS)
        if len(ua) < len(pt.user_params):
            self.dropped.add(_("exp_drop_user_params"))
        a.update(ua)
        dangling = 0
        for side, attr in (("top", "elt"), ("bottom", "elb"), ("left", "ell"), ("right", "elr")):
            ref = getattr(pt, f"edge_{side}").op_id
            if not ref:
                continue
            tgt = self.op_by_id.get(ref)
            if tgt is None or tgt.type != OpType.EL:
                dangling += 1
                continue
            a[attr] = f"@operation#{self.op_eid[ref]}"
        for side, attr in (("top", "grt"), ("bottom", "grb"), ("left", "grl"), ("right", "grr")):
            gs = getattr(pt, f"groove_{side}")
            if not gs.op_id:
                continue
            tgt = self.op_by_id.get(gs.op_id)
            if tgt is None or tgt.type != OpType.GR:
                dangling += 1
                continue
            a[attr] = f"@operation#{self.op_eid[gs.op_id]}"
            if gs.back_side:
                a[attr + "s"] = "false"
        return a, dangling

    def _register_part(self, pt: Part, eid: str) -> None:
        """Detal id sini EL / GR / SP operatsiyalarining `<part>` ro'yxatiga qo'shadi (takrorlanmaydi)."""
        for side in ("top", "bottom", "left", "right"):
            ref = getattr(pt, f"edge_{side}").op_id
            tgt = self.op_by_id.get(ref) if ref else None
            if tgt is not None and tgt.type == OpType.EL:
                users = self.edge_users.setdefault(ref, [])
                if eid not in users:
                    users.append(eid)
            gs = getattr(pt, f"groove_{side}")
            tgt = self.op_by_id.get(gs.op_id) if gs.op_id else None
            if tgt is not None and tgt.type == OpType.GR:
                users = self.groove_users.setdefault(gs.op_id, [])
                if eid not in users:
                    users.append(eid)
        for sid, back in ((getattr(pt, "surface_face_op", None), False), (getattr(pt, "surface_back_op", None), True)):
            tgt = self.op_by_id.get(sid) if sid else None
            if tgt is not None and tgt.type == OpType.SP:        # SP: formatda tomon yo'q — faqat «detal shu operatsiyada»
                users = self.sp_users.setdefault(sid, [])
                if eid not in users:
                    users.append(eid)
                if back and not getattr(pt, "surface_face_op", None):
                    self.sp_back_only.add(sid)

    # ── CS ──
    def _cs(self, root: ET.Element, op: Operation, mode: SizeMode) -> ET.Element:
        from ..models import CSCutParams, CSMaterialParams
        cut = op.cs_cut or CSCutParams()
        mat = op.cs_material or CSMaterialParams()
        tool_id, sheet_id = self.nid(), self.nid()
        ET.SubElement(root, "good", id=tool_id, typeId="tool.cutting",
                      swSawthick=num(cut.kerf), swSawthickDiv=num(cut.kerf_group if cut.kerf_group is not None else -1),
                      swPackageHeight=num(cut.pack_height), swMaxturns=str(cut.max_rotations),
                      swComplexBand=boolean(cut.complex_strips), swTrimIncludeSaw=boolean(cut.trim_includes_kerf),
                      swSort=str(int(cut.strip_sort)), swSortInBand=str(int(cut.in_strip_sort)),
                      swMinSizeBand=num(cut.min_strip_width), swMaxSizeBand=num(cut.max_strip_width),
                      swMaxLengthBand=num(cut.max_strip_length), swMinPruning=num(cut.min_trim_cut))
        sg = ET.SubElement(root, "good", id=sheet_id, typeId="sheet", name=_s(op.name), t=num(mat.thickness),
                           cost=num(mat.price))
        if op.code:
            sg.set("code", _s(op.code))
        first = next((s for s in op.sheets if not s.is_remnant and not s.source_remnant_id), op.sheets[0] if op.sheets else None)
        if first is not None:
            sg.set("l", num(first.length))
            sg.set("w", num(first.width))
        sheet_part_ids: list[str] = []
        remn = 0
        for sh in op.sheets:
            sid = self.nid()
            sheet_part_ids.append(sid)
            a = {"id": sid, "count": str(sh.qty), "l": num(sh.length), "w": num(sh.width)}
            for k, v in (("cTrimL", sh.trim_length), ("cTrimW", sh.trim_width), ("cTrimEL", sh.end_offset_bottom),
                         ("cTrimEW", sh.end_offset_right)):
                if v is not None:
                    a[k] = num(v)
            if sh.description:
                a["description"] = _s(sh.description)
            ET.SubElement(sg, "part", a)
            if sh.is_remnant or sh.source_remnant_id:
                remn += 1
        if remn:
            self.warn("remnant_sheet", name=self._opname(op), n=remn)
        if mat.est_fill_percent < 50 or cut.fill_packet < 50:
            self.warn("fill_ambig", name=self._opname(op))
        if cut.max_rotations < 2:                               # onlayn GibLabda ro'yxat 2…6 — boshqa dastur 1 ni qabul qilmasligi mumkin
            self.warn("rot_one", name=self._opname(op))
        a = {"id": self.op_eid[op.id], "typeId": "CS", "tool1": tool_id, "cSizeMode": str(MODE_ID[mode]),
             "cTrimL": num(cut.trim_length), "cTrimW": num(cut.trim_width)}
        if cut.end_offset_bottom is not None:
            a["cTrimEL"] = num(cut.end_offset_bottom)
        if cut.end_offset_right is not None:
            a["cTrimEW"] = num(cut.end_offset_right)
        a.update(csDirectCut=str(int(cut.first_cut)), csTexture=boolean(cut.use_grain),
                 cFillRep=num(cut.fill_packet / 100), cCPF=num(mat.est_fill_percent / 100),
                 cAllowanceWorkpiece=num(cut.machining_allowance), cCostType=str(COST_ID[mat.op_cost_base]),
                 cCostCut=num(mat.op_price), cCostByItem=boolean(mat.cost_by_sheets),
                 cCostByItemRound=str(int(mat.sheet_rounding.value)), cMinDimRegWaste1=num(mat.remnant_min_side1),
                 cMinDimRegWaste2=num(mat.remnant_min_side2), cBusinessWaste=num(mat.remnant_min_area),
                 cTrimWaste=boolean(mat.remnant_size_incl_trim), cMinDimDetail=num(mat.min_part_size),
                 cSaveDrawCut=boolean(cut.save_drawings), cCombiningParts=boolean(cut.merge_parts),
                 cMaxPartsOnPattern=str(cut.max_part_types_per_map), cPrefLargePacket=boolean(cut.prefer_big_pack),
                 t=num(mat.thickness))
        if first is not None:
            a["l"], a["w"] = num(first.length), num(first.width)
        a.update(printable=boolean(op.print), startNewPage=boolean(op.new_page))
        if op.description:
            a["description"] = _s(op.description)
        oe = ET.Element("operation", a)
        ET.SubElement(oe, "material", id=sheet_id)
        for pt in op.parts:
            ET.SubElement(oe, "part", id=self.part_eid[id(pt)])
        for sid in sheet_part_ids:
            ET.SubElement(oe, "part", id=sid)
        return oe

    # ── EL ──
    def _el(self, root: ET.Element, op: Operation) -> ET.Element:
        el = op.el or ELParams()
        tool_id, band_id = self.nid(), self.nid()
        ET.SubElement(root, "good", id=tool_id, typeId="tool.edgeline", elCost=num(el.op_price),
                      elRestSide=num(el.overhang), elMinSize=num(el.min_glue_length),
                      elWidthPreJoint=num(el.jointing_width))
        bg = ET.SubElement(root, "good", id=band_id, typeId="band", name=_s(op.name), w=num(el.width),
                           t=num(el.thickness), cost=num(el.price))
        if op.code:
            bg.set("code", _s(op.code))
        a = {"id": self.op_eid[op.id], "typeId": "EL", "tool1": tool_id, "elCalcMat": boolean(el.count_material),
             "w": num(el.width), "t": num(el.thickness), "elRoundMat": str(el.material_round),
             "elRoundLength": str(el.work_round), "elWastePRC": num(el.waste_percent), "elSymbol": _s(el.symbol),
             "elColor": _s(el.color), "elLineMark": str(el.marker_lines), "elMinDimDetail": num(el.min_perp_side),
             "printable": boolean(op.print), "startNewPage": boolean(op.new_page)}
        if op.description:
            a["description"] = _s(op.description)
        oe = ET.Element("operation", a)
        ET.SubElement(oe, "material", id=band_id)
        for eid in self.edge_users.get(op.id, []):
            ET.SubElement(oe, "part", id=eid)
        return oe

    # ── GR ──
    def _gr(self, op: Operation) -> ET.Element:
        from ..models import GRParams
        g = op.gr or GRParams()
        a = {"id": self.op_eid[op.id], "typeId": "GR", "typeName": _s(op.name), "grWidth": num(g.width),
             "grDepth": num(g.depth), "grOffset": num(g.offset), "grOffsetIncl": boolean(g.offset_inclusive),
             "grSawthick": num(g.saw_thickness), "grCost": num(g.price), "printable": boolean(op.print),
             "startNewPage": boolean(op.new_page)}
        if op.description:
            a["description"] = _s(op.description)
        if op.code:
            self.dropped.add(_("exp_drop_code"))
        oe = ET.Element("operation", a)
        for eid in self.groove_users.get(op.id, []):
            ET.SubElement(oe, "part", id=eid)
        return oe

    # ── XNC ──
    def _xnc(self, op: Operation) -> ET.Element:
        from ..models import XNCParams
        x = op.xnc or XNCParams()
        code = op.code or op.name or self.op_eid[op.id]

        def note(kind: str, kw: dict) -> None:
            self.warn("xnc_" + kind, **kw)
        a = {"id": self.op_eid[op.id], "typeId": "XNC", "typeName": _s(op.name)}
        if op.code:
            a["code"] = _s(op.code)
        a.update(program=program_xml(x, _s(code), note), count=str(x.qty), side=boolean(x.face_side),
                 turn=str(x.rotation // 90), mirHor=boolean(x.mirror_x), mirVert=boolean(x.mirror_y),
                 bySizeDetail=boolean(x.by_part_size), priceBore=num(x.drill_price), priceMill=num(x.mill_price_m),
                 priceCut=num(x.saw_price_m), price=num(x.extra_cost), printable=boolean(op.print),
                 startNewPage=boolean(op.new_page))
        if op.description:
            a["description"] = _s(op.description)
        if x.origin != "LT":
            self.warn("xnc_origin", code=_s(code), o=x.origin)
        oe = ET.Element("operation", a)
        linked = self.xnc_links.get(op.id, [])
        ref = self.first_eid.get(op.xnc_part_id or "") if op.xnc_part_id else None
        if ref is None and linked:
            ref = self.part_eid.get(id(linked[0]))
        if len({pt.id for pt in linked} | ({op.xnc_part_id} if ref and op.xnc_part_id else set())) > 1:
            self.warn("xnc_shared", code=_s(code))
        if ref:
            ET.SubElement(oe, "part", id=ref)
        return oe

    # ── O ──
    def _o(self, root: ET.Element, op: Operation, prod_eid: dict[str, str]) -> ET.Element:
        from ..models import OParams
        o = op.o or OParams()
        a = {"id": self.op_eid[op.id], "typeId": "O", "typeName": _s(op.name), "costOperation": num(o.work_cost),
             "printable": boolean(op.print), "startNewPage": boolean(op.new_page)}
        if o.owner_product_id and o.owner_product_id in prod_eid:
            a["owner"] = prod_eid[o.owner_product_id]
        if op.description:
            a["description"] = _s(op.description)
        if op.code:
            self.dropped.add(_("exp_drop_code"))
        oe = ET.Element("operation", a)
        for m in o.materials:
            gid = self.nid()
            if len(user_attrs(m.user_params, "material.", GOOD_ATTRS["simple"])) < len(m.user_params):
                self.dropped.add(_("exp_drop_user_params"))
            ET.SubElement(root, "good", {"id": gid, "typeId": "simple", "code": _s(m.code), "name": _s(m.name), "unit": _s(m.unit),
                                         "count": num(m.qty), "cost": num(m.price),
                                         **user_attrs(m.user_params, "material.", GOOD_ATTRS["simple"])})
            ET.SubElement(oe, "material", id=gid, count=num(m.qty))
        return oe

    # ── SP (W12) ──
    def _sp(self, op: Operation) -> ET.Element:
        sp = getattr(op, "sp", None)
        a = {"id": self.op_eid[op.id], "typeId": "SP", "typeName": _s(op.name)}
        if sp is not None:
            a.update(spCalcMat=boolean(sp.count_material), spWastePRC=num(sp.waste_percent), spRestSide=num(sp.rest_side),
                     spSizeMode=str(sp.size_mode), spCost=num(sp.op_price))
            if sp.price:
                self.dropped.add(_("exp_drop_sp_price"))
        a.update(printable=boolean(op.print), startNewPage=boolean(op.new_page))
        if op.description:
            a["description"] = _s(op.description)
        if op.code:
            self.dropped.add(_("exp_drop_code"))
        if op.id in self.sp_back_only:
            self.warn("sp_side", name=self._opname(op))
        oe = ET.Element("operation", a)
        for eid in self.sp_users.get(op.id, []):
            ET.SubElement(oe, "part", id=eid)
        return oe

    # ── LB ──
    def _lb(self, op: Operation) -> ET.Element:
        lb = op.lb or LBParams()
        name = self._opname(op)
        a = {"id": self.op_eid[op.id], "typeId": "LB", "typeName": _s(op.name),
             "printMode": "0" if lb.mode == "sheet" else "1", "columns": str(lb.columns), "rows": str(lb.rows),
             "gap": num(lb.gap_mm), "margin": boolean(lb.margin_mm is not None),
             "source": str({"user": 0, "products": 1, "parts": 2}[lb.source]),
             "printParts": boolean(lb.print_parts), "partEach": boolean(lb.part_each),
             "partONZ": boolean(lb.part_only_nonzero), "partSelected": boolean(lb.selected_uids() is not None),
             "printWastes": boolean(lb.print_wastes), "wasteEach": boolean(lb.waste_each),
             "productEach": boolean(lb.product_each), "productONZ": boolean(lb.product_only_nonzero),
             "printable": boolean(op.print), "startNewPage": boolean(op.new_page)}
        if lb.fields:
            f = ET.Element("fields")
            for i, fd in enumerate(lb.fields, 1):
                fe = ET.SubElement(f, "field", id=str(i), name=_s(fd.get("name", "")), type=_s(fd.get("type", "string")),
                                   width=num(fd.get("width", 10)), default=_s(fd.get("default", "")))
                if fd.get("title") and fd.get("title") != fd.get("name"):
                    fe.set("description", _s(fd["title"]))
            a["fields"] = "BASE64:" + base64.b64encode(ET.tostring(f, encoding="unicode").encode("utf-8")).decode("ascii")
        program = lb.legacy_program or ""
        if not program:
            for fn in LB_PROGRAM_EXPORTERS:
                program = fn(lb) or ""
                if program:
                    break
        if program:
            a["program"] = _s(program)
        else:
            self.warn("lb_no_program", name=name)
        if lb.source == "user" and lb.data:
            self.warn("lb_user_data", name=name)
        if op.description:
            a["description"] = _s(op.description)
        if op.code:
            self.dropped.add(_("exp_drop_code"))
        return ET.Element("operation", a)


def _serialize(root: ET.Element) -> bytes:
    ET.indent(root, space="\t")
    text = ET.tostring(root, encoding="unicode").replace(" />", "/>")
    return (PROLOG + "\n" + text + "\n").encode("utf-8")


def export_project(project: Project, *, validate: bool = True) -> ExportResult:
    """Loyiha → `.project` (UTF-8 XML). `validate=True` — natija o'z sxemamiz bo'yicha tekshiriladi (xato — `ExportError`)."""
    ex = _Exporter(project)
    root = ex.build()
    data = _serialize(root)
    if validate:
        errs = validate_project_xml(data, strict=True)
        if errs:
            raise ExportError(errs)
    return ExportResult(xml=data, filename=safe_filename(project), warnings=ex.warns, counts=ex.counts)
