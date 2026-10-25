"""Qoldiqlar ombori (деловые остатки): kroy natijasini omborga «yozish» va bekor qilish.

commit  — (tasdiqdan keyin) 1) kroyda ishlatilgan ombor qoldiqlari hisobdan chiqariladi,
          2) yangi деловой qoldiqlar omborga qo'shiladi (xom o'lcham — list chetigacha);
          mijoz olib ketadigan («Исп. кол-во») bo'laklar omborga yozilmaydi.
rollback — natija o'zgarsa/o'chirilsa: qo'shilgan qoldiqlar o'chiriladi (hali ishlatilmagan bo'lsa),
          ishlatilganlari qaytariladi.

Rezerv (REM-009): qoldiq «Листы и остатки» ga qo'shilganda `RemnantRow.reserved_project` loyiha id si bilan band qilinadi;
boshqa loyiha uni qo'sha olmaydi va omborga chiqim (commit) qila olmaydi. Rezerv loyihada shu qoldiq listi turguncha
amal qiladi: loyiha saqlanganda `sync_reservations` ro'yxatda qolmagan qoldiqlarni bo'shatadi; loyiha o'chsa — hammasi.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Optional

from sqlalchemy import select

from ..db import ProjectRow, RemnantMoveRow, RemnantRow, SessionLocal
from ..i18n import _
from ..models import Operation, OpType, Project
from . import remnant_rules


def _fin(v) -> float:
    try:
        f = float(v or 0)
    except (TypeError, ValueError):
        return 0.0
    return f if math.isfinite(f) else 0.0


def status_of(r: RemnantRow) -> str:
    """available — ishlatsa bo'ladi · reserved — loyihaga band · pending — arradan chiqishi kutilmoqda · empty — tugagan."""
    if (r.qty or 0) > 0:
        return "reserved" if r.reserved_project else "available"
    if (getattr(r, "qty_pending", 0) or 0) > 0:
        return "pending"
    return "empty"


def row_dict(r: RemnantRow) -> dict:
    L, W = _fin(r.length), _fin(r.width)
    sheet = _fin(getattr(r, "sheet_area_m2", None))
    return dict(id=r.id, material_code=r.material_code or "", material_name=r.material_name or "",
                length=L, width=W, thickness=_fin(r.thickness), qty=r.qty,
                area_m2=round(L * W / 1e6, 3),
                source_project=r.source_project, source_number=r.source_number, source_op=r.source_op,
                note=r.note or "", created_at=r.created_at.isoformat() if r.created_at else None,
                reserved_project=r.reserved_project or None, linear=bool(getattr(r, "linear", False)),
                qty_pending=int(getattr(r, "qty_pending", 0) or 0), source_map=getattr(r, "source_map", None),
                sheet_area_m2=sheet or None, percent=round(L * W / 1e6 / sheet * 100, 1) if sheet > 0 else None,
                mat_type=remnant_rules.material_type(r.material_code, r.material_name), status=status_of(r),
                clean_edges=bool(getattr(r, "clean_edges", False)))


# ───────────────────────── Kirim-chiqim jurnali (MES voqealari navbati) ─────────────────────────
def log_move(s, kind: str, *, row: Optional[RemnantRow] = None, qty: int = 0, material_code: str = "", material_name: str = "",
             length: float = 0, width: float = 0, thickness: float = 0, sheet_m2: Optional[float] = None,
             project: Optional[Project] = None, op_id: Optional[str] = None, map_index: Optional[int] = None,
             note: str = "", project_id: Optional[str] = None, project_number: Optional[int] = None) -> None:
    """Jurnalga yozuv (shu sessiya bilan birga commit bo'ladi). `qty` — bo'laklar soni (ishorasiz; yo'nalishni `kind` beradi)."""
    if row is not None:
        material_code, material_name = row.material_code or "", row.material_name or ""
        length, width, thickness = _fin(row.length), _fin(row.width), _fin(row.thickness)
        sheet_m2 = sheet_m2 or _fin(getattr(row, "sheet_area_m2", None)) or None
        if map_index is None:
            map_index = getattr(row, "source_map", None)
    area = round(_fin(length) * _fin(width) / 1e6, 4)
    s.add(RemnantMoveRow(remnant_id=row.id if row is not None else None, kind=kind, qty=int(qty),
                         material_code=(material_code or "")[:100], material_name=(material_name or "")[:300],
                         length=length, width=width, thickness=thickness, area_m2=area,
                         percent=round(area / sheet_m2 * 100, 1) if sheet_m2 else None,
                         project_id=project.id if project is not None else project_id,
                         project_number=project.number if project is not None else project_number, op_id=op_id, map_index=map_index,
                         note=(note or "")[:500]))


def _number(s, project_id: Optional[str]) -> Optional[int]:
    """Loyiha raqami (jurnalda ichki id emas, xodimlar biladigan № ko'rinsin)."""
    if not project_id:
        return None
    return s.scalar(select(ProjectRow.number).where(ProjectRow.id == project_id))


def move_dict(m: RemnantMoveRow) -> dict:
    return dict(id=m.id, remnant_id=m.remnant_id, kind=m.kind, qty=m.qty, material_code=m.material_code or "",
                material_name=m.material_name or "", length=_fin(m.length), width=_fin(m.width), thickness=_fin(m.thickness),
                area_m2=_fin(m.area_m2), percent=m.percent, project_id=m.project_id, project_number=m.project_number,
                op_id=m.op_id, map=m.map_index, note=m.note or "",
                created_at=m.created_at.isoformat() if m.created_at else None,
                sent_at=m.sent_at.isoformat() if m.sent_at else None)


def kick() -> None:
    """Jurnal o'zgardi — MES ga yuborish (fonda, MES manzili sozlangan bo'lsa)."""
    try:
        from . import remnant_outbox
        remnant_outbox.kick()
    except Exception:  # noqa: BLE001 — yuborish xatosi ombor amalini buzmasin
        pass


def _mes_wait(rules) -> bool:
    """Olib qolingan qoldiq MES signaligacha kutadimi: qoida yoqilgan va MES integratsiyasi yoqilgan."""
    if not rules.wait_mes:
        return False
    try:
        from . import settings
        return bool(settings.get_default("app").get("mes_enabled"))
    except Exception:  # noqa: BLE001
        return False


def material_key(op: Operation) -> str:
    return (op.code or op.name or "").strip()


# ───────────────────────── «Исп. кол-во» (mijoz olib ketadigan qoldiqlar) ─────────────────────────
def rem_key(business: bool, length: float, width: float) -> str:
    """Natijadagi qoldiq guruhi kaliti: «b:UxE» (деловой) / «r:UxE» (oddiy), U×E — foydali o'lcham, yuzdan birlarda
    butun son (frontend `CsSheets.tsx` bilan bir xil: Math.round(v * 100))."""
    return f"{'b' if business else 'r'}:{math.floor(_fin(length) * 100 + 0.5)}x{math.floor(_fin(width) * 100 + 0.5)}"


def result_remnant_groups(op: Operation) -> list[dict]:
    """Natijadagi qoldiqlar (nusxalar bilan), foydali o'lcham va turi bo'yicha guruhlangan:
    [{key, business, length, width, qty, taken}] — taken = mijoz olib ketadigani (qty dan oshmaydi)."""
    res = op.result
    if not res:
        return []
    agg: dict[str, dict] = {}
    for m in res.maps:
        for o in m.offcuts:
            if o.kind != "remnant":
                continue
            k = rem_key(o.business, o.length, o.width)
            g = agg.setdefault(k, dict(key=k, business=bool(o.business), length=o.length, width=o.width, qty=0))
            g["qty"] += m.copies
    taken = res.taken_remnants or {}
    for k, g in agg.items():
        g["taken"] = max(0, min(g["qty"], int(taken.get(k, 0) or 0)))
    return sorted(agg.values(), key=lambda g: (not g["business"], -g["length"] * g["width"]))


def kept_pieces(op: Operation, rules=None) -> list[dict]:
    """Omborga olinadigan bo'laklar har karta bo'yicha: [{map, length, width, qty (nusxalar bilan), copies}] — xom o'lcham.
    Material uchun foiz qoidasi bo'lsa — foiz hal qiladi (bo'lak / butun list ≥ foiz), aks holda деловой qoldiqlar (avvalgi
    xulq). Mijoz olib ketadigan («Исп. кол-во») bo'laklar ayriladi."""
    res = op.result
    if not res:
        return []
    taken = res.taken_remnants or {}
    linear = op.type == OpType.CL                    # (CL) погонажный: uzunlik × eni tartibi saqlanadi (almashtirilmaydi)
    cls = remnant_rules.classify(op, rules, require_rule=False) if op.type == OpType.CS else None
    by_key: dict[str, list] = {}                     # rem_key → [[map, (L, W), n, copies]]
    if cls is not None:
        for pc in cls["pieces"]:
            if pc["keep"]:
                k = rem_key(pc["business"], pc["ul"], pc["uw"]) if pc["kind"] == "remnant" else "w"
                by_key.setdefault(k, []).append([pc["map"], (pc["length"], pc["width"]), pc["copies"], pc["copies"]])
    else:
        for m in res.maps:
            for o in m.offcuts:
                if o.kind == "remnant" and o.business:
                    L = o.raw_length or o.length
                    W = o.raw_width or o.width
                    dims = (round(L, 1), round(W, 1)) if linear else (round(max(L, W), 1), round(min(L, W), 1))
                    by_key.setdefault(rem_key(True, o.length, o.width), []).append([m.index, dims, m.copies, m.copies])
    out: dict[tuple, dict] = {}
    for k, lst in by_key.items():
        skip = max(0, int(taken.get(k, 0) or 0)) if k != "w" else 0
        for e in sorted(lst, key=lambda e: (-e[1][0] * e[1][1], e[0])):
            use = min(e[2], skip)
            skip -= use
            n = e[2] - use
            if n > 0:
                g = out.setdefault((e[0], e[1]), dict(map=e[0], length=e[1][0], width=e[1][1], qty=0, copies=e[3]))
                g["qty"] += n
    return sorted(out.values(), key=lambda g: (-g["length"] * g["width"], g["map"]))


def client_pieces(op: Operation, rules=None) -> list[dict]:
    """Foiz qoidasi bo'yicha mijozga beriladigan (foizdan kichik) qoldiq bo'laklari: [{length, width, qty, percent}]."""
    cls = remnant_rules.classify(op, rules, require_rule=False) if op.type == OpType.CS else None
    if cls is None:
        return []
    cnt: Counter = Counter()
    pct: dict = {}
    for pc in cls["pieces"]:
        # qoida bo'lsa — foizdan kichik qoldiqlar; qoida yo'q — faqat texnolog «mijozga» deb belgilagani
        if not pc["keep"] and pc["kind"] == "remnant" and (cls["percent"] is not None or pc["manual"]):
            cnt[(pc["length"], pc["width"])] += pc["copies"]
            pct[(pc["length"], pc["width"])] = pc["percent"]
    return [dict(length=L, width=W, qty=n, percent=pct[(L, W)])
            for (L, W), n in sorted(cnt.items(), key=lambda kv: -kv[0][0] * kv[0][1])]


def business_remnants(op: Operation) -> list[dict]:
    """Omborga yoziladigan qoldiqlar (nusxalar bilan), xom o'lcham bo'yicha guruhlangan (`kept_pieces` yig'indisi)."""
    cnt: Counter = Counter()
    for g in kept_pieces(op):
        cnt[(g["length"], g["width"])] += g["qty"]
    return [dict(length=L, width=W, qty=n) for (L, W), n in sorted(cnt.items(), key=lambda kv: -kv[0][0] * kv[0][1])]


def consumed(op: Operation) -> dict[int, int]:
    """Kroyda ishlatilgan ombor qoldiqlari: remnant id → soni."""
    out: dict[int, int] = {}
    for sh in op.sheets:
        if sh.source_remnant_id and sh.used_qty:
            out[sh.source_remnant_id] = out.get(sh.source_remnant_id, 0) + sh.used_qty
    return out


class WarehouseConflict(ValueError):
    """Omborda kroy ishlatgan qoldiq yetarli emas (boshqa loyiha ishlatib bo'lgan yoki o'chirilgan) yoki rezerv boshqada."""


WH_FIELDS = ("remnants_saved", "saved_remnant_ids", "saved_remnant_qty", "consumed_remnants")


def detach_result(res) -> None:
    """Natijaning omborga bog'lanishini uzish (import/nusxa/eski versiya — ombor qatorlari boshqa natijaniki)."""
    if res is not None:
        res.remnants_saved = False
        res.saved_remnant_ids = []
        res.saved_remnant_qty = {}
        res.consumed_remnants = {}
        res.remnant_intake_id = None


def detach(op: Operation) -> None:
    detach_result(op.result)


def _same_remnant(r: RemnantRow, sh, key: str) -> bool:
    """Ombor qatori kroydagi qoldiq listi bilan bir xilmi (o'lcham bo'yicha). Material kodi solishtirilmaydi: qator raqamlari
    qayta berilmaydi (`sqlite_autoincrement`), «Показать все материалы» bilan boshqa kodli qoldiq ataylab qo'shilgan bo'lishi
    mumkin — avval bu holda chiqimda yolg'on «не хватает остатков» (409) chiqardi."""
    a = sorted((_fin(r.length), _fin(r.width)))
    b = sorted((float(sh.length), float(sh.width)))
    return abs(a[0] - b[0]) <= 0.5 and abs(a[1] - b[1]) <= 0.5


# ───────────────────────── Rezerv (REM-009) ─────────────────────────
def _reserver_number(holder: str, rid: int) -> Optional[int]:
    """Rezervchi loyiha hali ham shu qoldiqni listlarida saqlaydimi? Ha — loyiha raqami; yo'q (loyiha o'chgan yoki qoldiq
    ro'yxatdan olib tashlangan — eskirgan rezerv) — None."""
    from .. import store
    try:
        p = store.load(holder)
    except Exception:  # noqa: BLE001 — loyiha yo'q (404) yoki o'qib bo'lmaydi: rezerv eskirgan
        return None
    for o in p.operations:
        if any(sh.source_remnant_id == rid for sh in o.sheets):
            return p.number
    return None


def reserve(project_id: str, ids: list[int], atomic: bool = False) -> tuple[list[int], list[tuple[int, int]]]:
    """Qoldiqlarni loyiha uchun band qilish. Qaytaradi: (band qilingan/allaqachon shu loyihada id lar,
    [(id, band qilgan loyiha raqami)] — boshqa loyiha band qilganlari). Soni 0 yoki yo'q qoldiq o'tkazib yuboriladi.
    atomic=True — birortasi boshqa loyihada band bo'lsa hech narsa band qilinmaydi va WarehouseConflict ko'tariladi."""
    from . import remnant_store
    if remnant_store.is_mes():                     # MES rejimi: band qilishni MES yuritadi
        from .. import store
        remnant_store.mes_reservations(store.load(project_id), ids, "add")
        return list(dict.fromkeys(ids)), []
    ok: list[int] = []
    blocked: list[tuple[int, int]] = []
    with SessionLocal() as s:
        for rid in dict.fromkeys(ids):
            r = s.get(RemnantRow, rid, with_for_update=True)
            if r is None or (r.qty or 0) <= 0:
                continue
            holder = r.reserved_project
            if holder and holder != project_id:
                num = _reserver_number(holder, rid)
                if num is not None:
                    blocked.append((rid, num))
                    continue
            if r.reserved_project != project_id:
                log_move(s, "rezerv", row=r, qty=r.qty or 0, project_id=project_id, project_number=_number(s, project_id))
            r.reserved_project = project_id
            ok.append(rid)
        if atomic and blocked:
            s.rollback()
            raise WarehouseConflict("; ".join(_("remnant_reserved_other", id=rid, n=n) for rid, n in blocked))
        s.commit()
    if ok:
        kick()
    return ok, blocked


def check_sheets(project_id: str, rids: list[int]) -> None:
    """Loyiha listlaridagi qoldiqlar boshqa loyiha tomonidan band qilinmaganini tekshiradi (WarehouseConflict)."""
    from . import remnant_store
    if remnant_store.is_mes():
        return
    rids = [r for r in dict.fromkeys(rids) if r]
    if not rids:
        return
    with SessionLocal() as s:
        rows = s.scalars(select(RemnantRow).where(RemnantRow.id.in_(rids))).all()
        held = [(r.id, r.reserved_project) for r in rows if r.reserved_project and r.reserved_project != project_id]
    for rid, holder in held:
        num = _reserver_number(holder, rid)
        if num is not None:
            raise WarehouseConflict(_("remnant_reserved_other", id=rid, n=num))


def release(ids: list[int], project_id: Optional[str] = None) -> int:
    """Rezervni bo'shatish (project_id berilsa — faqat shu loyiha band qilganlari). Bo'shatilganlar soni."""
    from . import remnant_store
    if remnant_store.is_mes():
        if project_id:
            from .. import store
            remnant_store.mes_reservations(store.load(project_id), ids, "remove")
        return len(ids)
    n = 0
    with SessionLocal() as s:
        for rid in dict.fromkeys(ids):
            r = s.get(RemnantRow, rid, with_for_update=True)
            if r is not None and r.reserved_project and (project_id is None or r.reserved_project == project_id):
                log_move(s, "rezerv_bekor", row=r, qty=r.qty or 0, project_id=r.reserved_project,
                         project_number=_number(s, r.reserved_project))
                r.reserved_project = None
                n += 1
        s.commit()
    if n:
        kick()
    return n


def sync_reservations(project: Project) -> None:
    """Loyiha saqlanganda rezerv listlarga moslanadi: 1) u band qilgan, lekin endi listlarida yo'q qoldiqlarning rezervi
    bo'shatiladi; 2) listlarida turgan, hech kim band qilmagan qoldiq (eski loyiha, undo/redo) shu loyiha uchun band qilinadi.
    Boshqa loyiha band qilgan qoldiqqa tegilmaydi (to'qnashuv `commit` da 409 bo'lib ko'rinadi)."""
    from . import remnant_store
    if remnant_store.is_mes():
        refs = sorted({sh.source_remnant_id for o in project.operations for sh in o.sheets if sh.source_remnant_id})
        try:
            remnant_store.mes_reservations(project, refs, "set")
        except Exception:  # noqa: BLE001 — MES vaqtincha javob bermasa loyiha saqlanishi to'xtamasin
            pass
        return
    refs = {sh.source_remnant_id for o in project.operations for sh in o.sheets if sh.source_remnant_id}
    with SessionLocal() as s:
        mine = set(s.scalars(select(RemnantRow.id).where(RemnantRow.reserved_project == project.id)).all())
        stale = [rid for rid in mine if rid not in refs]
        changed = False
        if stale:
            s.query(RemnantRow).filter(RemnantRow.id.in_(stale)).update({"reserved_project": None},
                                                                      synchronize_session=False)
            changed = True
        free = [rid for rid in refs if rid not in mine]
        if free:
            n = s.query(RemnantRow).filter(RemnantRow.id.in_(free), RemnantRow.reserved_project.is_(None)) \
                .update({"reserved_project": project.id}, synchronize_session=False)
            changed = changed or bool(n)
        if changed:
            s.commit()


def release_project(project_id: str) -> None:
    """Loyiha o'chirilganda uning barcha rezervlari bo'shatiladi."""
    from . import remnant_store
    if remnant_store.is_mes():
        return
    with SessionLocal() as s:
        s.query(RemnantRow).filter(RemnantRow.reserved_project == project_id).update({"reserved_project": None},
                                                                                      synchronize_session=False)
        s.commit()


def annotate_reservations(rows: list[dict]) -> list[dict]:
    """Ro'yxat qatorlariga `reserved_number` (band qilgan loyiha raqami) qo'shadi; loyihasi yo'q (o'chgan) rezerv —
    bo'sh deb ko'rsatiladi."""
    ids = {d["reserved_project"] for d in rows if d.get("reserved_project")}
    if not ids:
        return rows
    with SessionLocal() as s:
        nums = {pid: n for pid, n in s.execute(select(ProjectRow.id, ProjectRow.number).where(ProjectRow.id.in_(ids))).all()}
    for d in rows:
        pid = d.get("reserved_project")
        if pid:
            d["reserved_number"] = nums.get(pid)
            if d["reserved_number"] is None:
                d["reserved_project"] = None
    return rows


def commit(project: Project, op: Operation) -> dict:
    assert op.type in (OpType.CS, OpType.CL, OpType.CN)
    from . import remnant_store
    if remnant_store.is_mes():
        if not op.result or not op.result.maps:
            raise ValueError(_("no_result"))
        if op.result.remnants_saved:
            raise ValueError(_("remnants_already"))
        return remnant_store.mes_commit(project, op)
    linear = op.type == OpType.CL
    res = op.result
    if not res or not res.maps:
        raise ValueError(_("no_result"))
    if res.remnants_saved:
        raise ValueError(_("remnants_already"))
    if op.type == OpType.CN:                                          # (CN, W16) nesting: qalinlik CNParams da
        thick = op.cn.thickness if op.cn else 0
    else:
        thick = (op.cl.thickness if op.cl else 0) if linear else (op.cs_material.thickness if op.cs_material else 0)
    added, used = [], {}
    with SessionLocal() as s:
        need = consumed(op)
        rows = {rid: s.get(RemnantRow, rid, with_for_update=True) for rid in need}
        sheets = {sh.source_remnant_id: sh for sh in op.sheets if sh.source_remnant_id}
        key = material_key(op)
        for rid in need:              # qator boshqa qoldiq bo'lib qolgan (o'chirilib, raqam qayta berilgan)
            r, sh = rows[rid], sheets.get(rid)
            if r is not None and sh is not None and not _same_remnant(r, sh, key):
                rows[rid] = None
        short = [(rid, n, (rows[rid].qty or 0) if rows[rid] is not None else 0)
                 for rid, n in need.items() if rows[rid] is None or (rows[rid].qty or 0) < n]
        if short:
            raise WarehouseConflict(_("remnant_short", items=", ".join(
                _("remnant_short_item", id=rid, need=n, have=h) for rid, n, h in short)))
        for rid in need:              # boshqa loyiha band qilgan qoldiqdan chiqim qilib bo'lmaydi
            holder = rows[rid].reserved_project
            if holder and holder != project.id:
                num = _reserver_number(holder, rid)
                if num is not None:
                    raise WarehouseConflict(_("remnant_reserved_other", id=rid, n=num))
        for rid, n in need.items():
            r = rows[rid]
            r.qty = (r.qty or 0) - n
            used[str(rid)] = n
            log_move(s, "chiqim", row=r, qty=n, project=project, op_id=op.id, note=_("rm_sold", n=project.number))
        rules = remnant_rules.load()
        sheet_m2 = round(remnant_rules.sheet_area_mm2(op) / 1e6, 4) if op.type == OpType.CS else None
        note = f"№{project.number} {project.name}"[:500]
        if op.type == OpType.CS and _mes_wait(rules):
            # har karta alohida qator: MES «list arradan chiqdi» signali (karta bo'yicha) qoldiqni «mavjud» qiladi
            done = {m.index: max(0, min(m.copies, int(m.done_count or 0))) for m in res.maps}
            pieces = [dict(g, avail=g["qty"] * done.get(g["map"], 0) // max(1, g["copies"])) for g in kept_pieces(op, rules)]
        else:
            pieces = [dict(g, map=None, avail=g["qty"]) for g in business_remnants(op)]
        for g in pieces:
            r = RemnantRow(material_code=material_key(op), material_name=op.name, length=g["length"],
                           width=g["width"], thickness=thick, qty=g["avail"], qty_pending=g["qty"] - g["avail"],
                           qty_released=g["avail"], source_map=g["map"], sheet_area_m2=sheet_m2, clean_edges=op.type == OpType.CS,
                           source_project=project.id, source_number=project.number, source_op=op.id, linear=linear,
                           note=note)
            s.add(r)
            s.flush()
            added.append(r)
            if r.qty_pending:
                log_move(s, "kutish", row=r, qty=r.qty_pending, project=project, op_id=op.id)
            if r.qty:
                log_move(s, "kirim", row=r, qty=r.qty, project=project, op_id=op.id)
        for g in client_pieces(op, rules):
            log_move(s, "mijozga", qty=g["qty"], material_code=material_key(op), material_name=op.name, length=g["length"],
                     width=g["width"], thickness=thick, sheet_m2=sheet_m2, project=project, op_id=op.id)
        s.commit()
        out_added = [row_dict(r) for r in added]
    kick()
    res.remnants_saved = True
    res.saved_remnant_ids = [r["id"] for r in out_added]
    res.saved_remnant_qty = {str(r["id"]): int(r["qty"] or 0) + int(r["qty_pending"] or 0) for r in out_added}
    res.consumed_remnants = used
    return dict(added=out_added, consumed=used)


def on_map_done(project: Project, op: Operation, map_index: int, done: int) -> int:
    """MES / sex: karta (list) arradan chiqdi — shu kartaning «kutilmoqda» qoldiqlari tayyor nusxalar ulushida «mavjud» bo'ladi
    (`done` kamaysa — hali ishlatilmagan qismi «kutilmoqda» ga qaytadi). O'zgargan bo'laklar soni."""
    res = op.result
    if not res or not res.remnants_saved or not res.saved_remnant_ids or res.remnant_intake_id:
        return 0                                   # MES rejimi: holatni MES o'zi yuritadi
    m = next((x for x in res.maps if x.index == map_index), None)
    if m is None:
        return 0
    c = max(1, m.copies)
    d = max(0, min(c, int(done or 0)))
    changed = 0
    with SessionLocal() as s:
        rows = s.scalars(select(RemnantRow).where(RemnantRow.id.in_(res.saved_remnant_ids),
                                                  RemnantRow.source_map == map_index).with_for_update()).all()
        for r in rows:
            pend, rel = int(r.qty_pending or 0), int(r.qty_released or 0)
            target = (pend + rel) * d // c
            if target > rel:
                k = min(target - rel, pend)
                if k > 0:
                    r.qty = (r.qty or 0) + k
                    r.qty_pending = pend - k
                    r.qty_released = rel + k
                    log_move(s, "kirim", row=r, qty=k, project=project, op_id=op.id, note=_("rm_saw_done"))
                    changed += k
            elif target < rel:
                k = min(rel - target, int(r.qty or 0))       # ishlatilgan qismi qaytarilmaydi
                if k > 0:
                    r.qty = (r.qty or 0) - k
                    r.qty_pending = pend + k
                    r.qty_released = rel - k
                    log_move(s, "kutish", row=r, qty=k, project=project, op_id=op.id, note=_("rm_saw_undo"))
                    changed += k
        if changed:
            s.commit()
    if changed:
        kick()
    return changed


def rollback(op: Operation) -> dict:
    """Omborga yozuvni bekor qilish. Qo'shilgan qoldiq boshqa loyihada ishlatilmagan bo'lsa — o'chiriladi;
    ortiqcha qoldig'i bo'lsa — faqat shu loyiha qo'shgan qismi hisobdan chiqariladi. Agar qoldiqning bir qismini
    boshqa loyiha allaqachon ishlatgan bo'lsa (soni yozilganidan kam) — bizning hissamiz bekor bo'ladi va qator
    o'chiriladi: shundan keyin ishlatgan loyiha o'z yozuvini bekor qilsa, qaytariladigan qoldiq yo'q (egasiz
    «arvoh» qoldiq paydo bo'lmaydi — bekor qilish tartibi natijaga ta'sir qilmaydi; `orphaned` ro'yxatida).
    Ishlatilgan ombor qoldiqlari (agar qator hali o'sha qoldiq bo'lsa) qaytariladi."""
    res = op.result
    if not res or not res.remnants_saved:
        return dict(removed=[], restored={}, kept=[], orphaned=[])
    if res.remnant_intake_id:                      # MES rejimida yozilgan — MES da bekor qilinadi
        from . import remnant_store
        return remnant_store.mes_rollback(op)
    removed, restored, kept, orphaned = [], {}, [], []
    key = material_key(op)
    sheets = {sh.source_remnant_id: sh for sh in op.sheets if sh.source_remnant_id}
    with SessionLocal() as s:
        for rid in res.saved_remnant_ids:
            r = s.get(RemnantRow, rid, with_for_update=True)
            if r is None:
                continue
            have = (r.qty or 0) + (r.qty_pending or 0)
            added = int(res.saved_remnant_qty.get(str(rid), have))
            log_move(s, "bekor", row=r, qty=min(have, added), op_id=op.id, note=_("rm_cancel"),
                     project_id=r.source_project, project_number=r.source_number)
            if have == added:
                s.delete(r)
                removed.append(rid)
            elif have > added:
                r.qty = (r.qty or 0) - added
                removed.append(rid)
            else:                       # bir qismi boshqa kroyda ishlatilgan — egasi qolmaydi, qator o'chiriladi
                s.delete(r)
                removed.append(rid)
                orphaned.append(rid)
        for rid, n in res.consumed_remnants.items():
            r = s.get(RemnantRow, int(rid), with_for_update=True)
            if r is None:               # qator o'chirilgan (egasi bekor qilgan) — qaytariladigan narsa yo'q
                continue
            sh = sheets.get(int(rid))
            if sh is not None and not _same_remnant(r, sh, key):     # qator boshqa qoldiqqa aylangan
                continue
            r.qty = (r.qty or 0) + n
            restored[rid] = n
            log_move(s, "qaytish", row=r, qty=n, op_id=op.id, note=_("rm_return"), project_id=r.reserved_project)
        s.commit()
    kick()
    detach(op)
    return dict(removed=removed, restored=restored, kept=kept, orphaned=orphaned)
