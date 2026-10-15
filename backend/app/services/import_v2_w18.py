"""Excel import v2 kengaytmalari (W18; `import_v2.py` dan kechiktirib chaqiriladi) — W3 «Qilinmadi» bandlari:

  * «Простые операции» tabi (XLS-013): Excel varag'i qatorlari (Код, Наименование, Ед.И, Кол, Цена) → (O) Комплектация
    operatsiyasi; `o_ops.parse_rows` (buferdan qo'yish bilan bir xil qoidalar, `PasteResult`). Ixtiyoriy ustunlar: «Операция»
    (qiymat bo'yicha alohida O operatsiya), «Изделие» (egasi — mahsulot).
  * «Материалы» tabi (XLS-012): katalogdan (kod / nom bo'yicha aniq) topib CS / EL / SP / CL operatsiya yaratish; katalogda
    yo'q material — qatorning o'z ustunlari bilan (`create_missing`).
  * «Детали» tabidagi qo'shimcha ustun guruhlari (XLS-009): (SP) Обработка поверхности (lits / orqa), (GR) Пазование (4 tomon),
    (XNC) Обработка 1 / 2 — XNC **shablon** kodi bo'yicha detalga yangi XNC operatsiyasi bog'lanadi; shablon topilmasa — ogohlantirish.
  * погонаж: «Ширина» bo'sh qator — CL operatsiyasiga (XLS-005; `PartsTab.linear_no_width`).
Mavjud operatsiya (nom / kod bo'yicha) qayta ishlatiladi, yangisi `ImportReport.created_ops` ga yoziladi.
Hujjat: `docs/mebelix/T_W18_IMPORT_INFRA.md` §3.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

from ..i18n import LANG, _
from ..models import (CLParams, ELParams, GRParams, GrooveSide, OpType, Operation, Part, Product, Project, SPParams,
                      StockSheet, XNCParams)
from . import catalog as catalog_svc
from . import importers as imp
from . import o_ops, settings, sp_ops
from . import import_v2 as V

MAX_NEW_XNC = 5000                 # bitta importda ko'pi bilan shuncha yangi XNC operatsiyasi (noto'g'ri ustun tanlansa)
MAX_NEW_EXTRA_OPS = 100            # shu ustun guruhlaridan yaratiladigan SP / GR operatsiyalari

MATERIAL_FIELDS = ("code", "name", "kind", "thickness", "length", "width", "price")
SIMPLE_FIELDS = ("code", "name", "unit", "qty", "price", "operation", "product")
EXTRA_FIELDS = ("sp_front", "sp_back", "gr_top", "gr_bottom", "gr_left", "gr_right", "xnc1", "xnc2")

TYPE_OF_KIND = {"sheet": "CS", "linear": "CL", "edge": "EL", "surface": "SP"}
_KIND_RE = (("sheet", re.compile(r"лист|sheet|list|varaq", re.I)), ("edge", re.compile(r"кром|edge|kromka", re.I)),
            ("surface", re.compile(r"поверх|surface|sirt", re.I)), ("linear", re.compile(r"погон|linear|pogon", re.I)))
_CATALOG_ORDER = ("sheet", "edge", "surface", "linear")

MakeOp = Callable[[str, str, str, Optional[str]], Operation]       # (tur, nom, kod, katalog id) → yangi operatsiya


def kind_of(text: str) -> Optional[str]:
    """«Тип» katagi (лист / кромка / поверхность / погонаж, sheet / edge / …) → katalog turi."""
    for k, rx in _KIND_RE:
        if rx.search(text or ""):
            return k
    return None


def default_make_op(typ: str, name: str, code: str, item_id: Optional[str]) -> Operation:
    """API qatlamisiz (to'g'ridan-to'g'ri `run_import`) yaratish: standart parametrlar (katalog ma'lumotisiz)."""
    if typ == "CS":
        return V.default_cs(name, code)
    op = Operation(type=OpType(typ), code=code, name=name)
    if typ == "EL":
        op.el = ELParams()
    elif typ == "SP":
        op.sp = sp_ops.new_params(settings.get_default("sp_defaults"))
    elif typ == "CL":
        op.cl = CLParams()
        op.sheets = [StockSheet(length=6000, width=op.cl.width)]
    return op


def _insert_op(project: Project, op: Operation, rep: V.ImportReport) -> None:
    """Yangi operatsiya — shu importda yaratilgan birinchi kromkadan oldin (CS lar kromkadan oldin turadi), aks holda oxiriga."""
    first_edge = rep.created_edges[0] if rep.created_edges else None
    at = next((i for i, o in enumerate(project.operations) if o is first_edge), len(project.operations))
    project.operations.insert(at, op)
    rep.created_ops.append(op)


def _new_op_guard(rep: V.ImportReport) -> None:
    if len(rep.created_ops) >= V.MAX_NEW_OPS:
        raise V.ImportConfigError(_("imp_too_many_materials", n=V.MAX_NEW_OPS))


# ───────────────────────── «Материалы» tabi ─────────────────────────
def _num(raw, label: str, lo_zero: bool = False) -> tuple[Optional[float], Optional[str]]:
    """Ixtiyoriy son ustuni: bo'sh — (None, None); noto'g'ri — (None, sabab)."""
    if raw is None:
        return None, None
    f = imp.parse_number(raw)
    if f is None:
        return None, _("imp_skip_nan", f=label, v=imp.cell_text(raw).strip()[:30])
    if f < 0 or (f == 0 and not lo_zero) or f > 1e9:
        return None, _("imp_skip_nonpos", f=label, v=f"{f:g}") if f <= 0 else _("imp_skip_big", f=label, v=f"{f:g}")
    return f, None


def _existing_op(project: Project, typ: str, code: str, name: str) -> Optional[Operation]:
    keys = {k for k in (V._fold(code), V._fold(name)) if k}
    for o in project.operations:
        if o.type.value == typ and (V._fold(o.code) in keys or V._fold(o.name) in keys):
            return o
    return None


def _apply_row_values(op: Operation, typ: str, th: Optional[float], L: Optional[float], W: Optional[float],
                      price: Optional[float]) -> None:
    """Katalogda topilmagan material: qatorning o'z qiymatlari (berilganlari) standart parametrlar ustiga."""
    if typ == "CS" and op.cs_material is not None:
        if th:
            op.cs_material.thickness = th
        if price is not None:
            op.cs_material.price = price
        if (L or W) and op.sheets:
            op.sheets[0].length = min(L or op.sheets[0].length, 20000.0)
            op.sheets[0].width = min(W or op.sheets[0].width, 20000.0)
    elif typ == "EL" and op.el is not None:
        if th is not None:
            op.el.thickness = th
        if W:
            op.el.width = W
        if price is not None:
            op.el.price = price
    elif typ == "SP" and op.sp is not None and price is not None:
        op.sp.price = price
    elif typ == "CL" and op.cl is not None:
        if W:
            op.cl.width = min(W, 20000.0)
        if th:
            op.cl.thickness = min(th, 1000.0)
        if price is not None:
            op.cl.price = price
        if op.sheets:
            if L:
                op.sheets[0].length = min(L, 20000.0)
            op.sheets[0].width = op.cl.width


def import_materials(project: Project, bk: imp.Book, tab: "V.MaterialsTab", rep: V.ImportReport, make_op: MakeOp) -> None:
    cols = V._cols(tab.map, MATERIAL_FIELDS)
    if "code" not in cols and "name" not in cols:
        raise V.ImportConfigError(_("imp_need_material_col"))
    seen: set[tuple[str, str]] = set()
    for rno, row in bk.rows(V._sheet_ref(tab), tab.start_row, tab.end_row):
        if all(V._get(row, i) is None for i in cols.values()):
            continue
        code, name = V._text(row, cols.get("code"), 100), V._text(row, cols.get("name"))
        title = name or code
        if not title:
            rep.skipped.append(dict(row=rno, tab="materials", reason=_("imp_skip_empty", f=_("imp_f_name"))))
            continue
        hint_txt = V._text(row, cols.get("kind"), 40)
        hint = kind_of(hint_txt) if hint_txt else None
        if hint_txt and hint is None:
            rep.skipped.append(dict(row=rno, tab="materials", reason=_("imp_mat_bad_kind", v=hint_txt[:30])))
            continue
        # katalogdan (kod, so'ng nom bo'yicha aniq): tur ko'rsatilgan bo'lsa — faqat shu tur
        item = None
        for kind in ((hint,) if hint else _CATALOG_ORDER):
            item = (catalog_svc.find_item(kind, code) if code else None) or (catalog_svc.find_item(kind, name) if name else None)
            if item is not None:
                break
        th, e1 = _num(V._get(row, cols.get("thickness")), _("imp_f_thickness"))
        L, e2 = _num(V._get(row, cols.get("length")), _("imp_f_length"))
        W, e3 = _num(V._get(row, cols.get("width")), _("imp_f_width"))
        price, e4 = _num(V._get(row, cols.get("price")), _("imp_f_price"), lo_zero=True)
        if item is None:
            if not tab.create_missing:
                rep.skipped.append(dict(row=rno, tab="materials", reason=_("imp_mat_not_found", v=title[:60])))
                continue
            errs = [e for e in (e1, e2, e3, e4) if e]
            if errs:
                rep.skipped.append(dict(row=rno, tab="materials", reason="; ".join(errs)))
                continue
            kind = hint or tab.default_kind
        else:
            kind = item.kind
        typ = TYPE_OF_KIND.get(kind)
        if typ is None:                                        # katalog papkasi va h.k.
            rep.skipped.append(dict(row=rno, tab="materials", reason=_("imp_mat_bad_kind", v=str(kind)[:30])))
            continue
        key = (typ, V._fold(item.code if item and item.code else code) or V._fold(item.name if item else name))
        if key in seen:
            continue
        seen.add(key)
        ex = _existing_op(project, typ, item.code if item else code, item.name if item else name)
        if ex is not None:
            rep.materials_existing += 1
            continue
        _new_op_guard(rep)
        op = make_op(typ, (item.name if item else name) or title, (item.code if item else code) or "", item.id if item else None)
        if item is None:
            _apply_row_values(op, typ, th, L, W, price)
            rep.warnings.append(_("imp_mat_not_in_catalog", row=rno, name=title[:60]))
        if typ == "EL" and op.el is not None:
            imp.assign_edge_style(project, op.el)
            rep.created_edges.append(op)
            project.operations.append(op)
        else:
            _insert_op(project, op, rep)
        rep.materials_added += 1


# ───────────────────────── «Простые операции» tabi ─────────────────────────
def import_simple(project: Project, bk: imp.Book, tab: "V.SimpleTab", rep: V.ImportReport) -> None:
    cols = V._cols(tab.map, SIMPLE_FIELDS)
    if "code" not in cols and "name" not in cols:
        raise V.ImportConfigError(_("imp_need_simple_col"))
    defaults = settings.get_default("o_defaults")
    unit = o_ops.default_unit(defaults)
    target: Optional[Operation] = None
    if tab.target_op:
        target = next((o for o in project.operations if o.id == tab.target_op), None)
        if target is None or target.type != OpType.O:
            raise V.ImportConfigError(_("imp_target_not_o", id=tab.target_op[:20]))
    prod_by_text: dict[str, Product] = {}
    for pr in reversed(project.products):
        for k in (pr.name, pr.code):
            if V._fold(k):
                prod_by_text[V._fold(k)] = pr
    groups: dict[str, list[tuple[int, list[str]]]] = {}       # «Операция» ustuni qiymati (katta-kichik harfsiz) → qatorlar
    group_prod: dict[str, Optional[Product]] = {}
    seen_names: dict[str, str] = {}                           # kalit → operatsiya nomi (fayldagi yozuvi)
    order: list[str] = []
    warned_prod: set[str] = set()
    for rno, row in bk.rows(V._sheet_ref(tab), tab.start_row, tab.end_row):
        if all(V._get(row, i) is None for i in cols.values()):
            continue
        gname = V._text(row, cols.get("operation"), 300) if "operation" in cols else ""
        key = V._fold(gname)
        if key not in groups:
            groups[key] = []
            order.append(key)
            group_prod[key] = None
            seen_names[key] = gname
        ptxt = V._text(row, cols.get("product"), 300) if "product" in cols else ""
        if ptxt and group_prod[key] is None:
            pr = prod_by_text.get(V._fold(ptxt))
            if pr is None:
                if V._fold(ptxt) not in warned_prod:
                    warned_prod.add(V._fold(ptxt))
                    rep.warnings.append(_("imp_simple_no_product", row=rno, name=ptxt[:60]))
            else:
                group_prod[key] = pr
        cells = [V._text(row, cols.get(f), 300) if f in cols else "" for f in ("code", "name", "unit", "qty", "price")]
        groups[key].append((rno, cells))
    for key in order:
        rows = groups[key]
        if not rows:
            continue
        op = target
        if op is None:
            _new_op_guard(rep)
            title = seen_names.get(key, "") or tab.op_name.strip() or _("imp_simple_default_name")
            op = Operation(type=OpType.O, name=title[:300], o=o_ops.new_params(defaults))
            if group_prod.get(key) is not None:
                op.o.owner_product_id = group_prod[key].id           # type: ignore[union-attr]
            project.operations.append(op)
            rep.created_ops.append(op)
            rep.created_o.append(op)
        elif group_prod.get(key) is not None and not op.o.owner_product_id:       # type: ignore[union-attr]
            op.o.owner_product_id = group_prod[key].id               # type: ignore[union-attr]
        room = o_ops.O_MAX_ROWS - len(op.o.materials)                 # type: ignore[union-attr]
        res = o_ops.parse_rows(rows, max(room, 0), unit)
        op.o.materials.extend(res.rows)                                # type: ignore[union-attr]
        rep.simple_rows += len(res.rows)
        for s in res.skipped:
            rep.skipped.append(dict(s, tab="simple"))
        rep.warnings.extend(res.warnings)


# ───────────────────────── «Детали»: (SP) / (GR) / (XNC) ustun guruhlari ─────────────────────────
def resolve_template(text: str) -> Optional[tuple[str, "object"]]:
    """XNC shablon kodi (`lib:<kalit>`, `u:<id>`, foydalanuvchi shablon nomi, o'rnatilgan shablon kaliti yoki nomi — katta-kichik
    harfga sezgirsiz) → (nom, XncTemplate) yoki None."""
    from . import xnc_templates as T
    t = (text or "").strip()
    if not t:
        return None
    low = t.casefold()
    lang = LANG.get()
    try:
        if low.startswith("lib:") and t[4:] in T.LIBRARY:
            ru, uz, dru, duz, cat, _b = T.LIBRARY[t[4:]]
            return (uz if lang == "uz" else ru), T.XncTemplate(description=duz if lang == "uz" else dru, category=cat,
                                                              program=T.library_program(t[4:], lang))
        if low.startswith("u:") and t[2:].isdigit():
            r = settings.get_profile("xnc_template", int(t[2:]))
            return (r["name"], T.XncTemplate.model_validate(r["data"])) if r else None
        r = settings.find_by_name("xnc_template", t)
        if r is not None:
            return r["name"], T.XncTemplate.model_validate(r["data"])
        for key, (ru, uz, dru, duz, cat, _b) in T.LIBRARY.items():
            if low in (key.casefold(), ru.casefold(), uz.casefold()):
                return (uz if lang == "uz" else ru), T.XncTemplate(description=duz if lang == "uz" else dru, category=cat,
                                                                  program=T.library_program(key, lang))
    except Exception:  # noqa: BLE001 — buzuq saqlangan shablon: «topilmadi» sifatida ogohlantiriladi
        return None
    return None


class Extras:
    """Qo'shimcha ustun guruhlarini detallarga bog'lash (detallar loyihaga qo'shilib, `uid` berilgandan keyin)."""

    def __init__(self, project: Project, rep: V.ImportReport):
        self.project, self.rep = project, rep
        self.gr_cache: dict[str, Operation] = {}
        self.tpl_cache: dict[str, Optional[tuple[str, object]]] = {}
        self.new_extra = 0
        self.xnc_codes = {V._fold(o.code) for o in project.operations if o.type == OpType.XNC and o.code}
        self.host: dict[str, Operation] = {}

    def _gr(self, text: str) -> Operation:
        key = V._fold(text)
        op = self.gr_cache.get(key)
        if op is not None:
            return op
        for o in self.project.operations:
            if o.type == OpType.GR and key in (V._fold(o.name), V._fold(o.code)):
                op = o
                break
        if op is None:
            if self.new_extra >= MAX_NEW_EXTRA_OPS:
                raise V.ImportConfigError(_("imp_too_many_materials", n=MAX_NEW_EXTRA_OPS))
            self.new_extra += 1
            try:
                gp = GRParams.model_validate({k: v for k, v in settings.get_default("gr_defaults").items()
                                              if k not in ("usage", "cut_length", "passes")})
            except Exception:  # noqa: BLE001
                gp = GRParams()
            op = Operation(type=OpType.GR, name=text.strip()[:300], gr=gp)
            self.project.operations.append(op)
            self.rep.created_ops.append(op)
            self.rep.warnings.append(_("imp_gr_created", name=text.strip()[:60]))
        self.gr_cache[key] = op
        return op

    def _unique_xnc_code(self, base: str) -> str:
        code, n = base, 1
        while V._fold(code) in self.xnc_codes:
            n += 1
            code = f"{base}-{n}"
        self.xnc_codes.add(V._fold(code))
        return code

    def link(self, staged: list["V._Staged"]) -> None:
        sp_before = {o.id for o in self.project.operations if o.type == OpType.SP}
        for s in staged:
            ex = s.extras
            if not ex:
                continue
            part = s.part
            for col, side in (("sp_front", "front"), ("sp_back", "back")):
                txt = ex.get(col, "")
                if txt and txt.casefold() not in imp.NO_EDGE:
                    new_before = len(self.project.operations)
                    sp = sp_ops.find_or_create(self.project, txt)
                    if len(self.project.operations) > new_before:
                        if sp.id not in sp_before:
                            sp_before.add(sp.id)
                            self.new_extra += 1
                            self.rep.created_ops.append(sp)
                            self.rep.warnings.append(_("imp_sp_created", name=txt[:60]))
                        if self.new_extra > MAX_NEW_EXTRA_OPS:
                            raise V.ImportConfigError(_("imp_too_many_materials", n=MAX_NEW_EXTRA_OPS))
                    sp_ops.attach(part, side, sp)
                    self.rep.linked["sp"] += 1
            for col, side in (("gr_top", "top"), ("gr_bottom", "bottom"), ("gr_left", "left"), ("gr_right", "right")):
                txt = ex.get(col, "")
                if txt and txt.casefold() not in imp.NO_EDGE:
                    setattr(part, f"groove_{side}", GrooveSide(op_id=self._gr(txt).id, back_side=False))
                    self.rep.linked["gr"] += 1
            for n, col in enumerate(("xnc1", "xnc2"), 1):
                txt = ex.get(col, "")
                if not txt or txt.casefold() in imp.NO_EDGE:
                    continue
                key = txt.casefold()
                if key not in self.tpl_cache:
                    self.tpl_cache[key] = resolve_template(txt)
                    if self.tpl_cache[key] is None:
                        self.rep.warnings.append(_("imp_xnc_tpl_missing", row=s.rno, code=txt[:60]))
                found = self.tpl_cache[key]
                if found is None:
                    continue
                if self.rep.linked["xnc_new"] >= MAX_NEW_XNC:
                    raise V.ImportConfigError(_("imp_too_many_xnc", n=MAX_NEW_XNC))
                self._xnc_for_part(s, found, n)

    def _xnc_for_part(self, s: "V._Staged", found: tuple[str, object], n: int) -> None:
        name, tpl = found
        prod = next((x for x in self.project.products if x.id == s.part.product_id), None)
        base = "_".join(x for x in ((prod.code if prod else ""), s.part.code or str(s.part.uid)) if x)
        code = self._unique_xnc_code(base if n == 1 else f"{base}-{n}")
        th = s.op.cs_material.thickness if s.op.cs_material else 16
        x = XNCParams(thickness=th, program=[c.model_copy(deep=True) for c in tpl.program],         # type: ignore[attr-defined]
                      par_values=dict(tpl.par_values))                                                # type: ignore[attr-defined]
        xop = Operation(type=OpType.XNC, code=code, name=s.part.name or name, xnc=x, xnc_part_id=s.part.id)
        s.part.xnc_op_ids.append(xop.id)
        self.project.operations.append(xop)
        self.rep.linked["xnc"] += 1
        self.rep.linked["xnc_new"] += 1


def link_extras(project: Project, staged: list["V._Staged"], rep: V.ImportReport) -> None:
    if any(s.extras for s in staged):
        Extras(project, rep).link(staged)
