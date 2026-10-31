"""W14 — «Заказать» oqimi: loyiha holatlari, o'tish qoidalari, rollar, tarix, tahrir bloklanishi, «Очистить проект».

Holatlar (OrderStatus): 0 Не заказан → 1 Заказан → 2 Утвержден → 3 Готов  (GibLab buyurtma yordami, ORD-004…006):
  * «Заказать» — holatni «Заказан» ga o'tkazadi (buyurtma tekshiruv va baho uchun ijrochiga ketadi);
  * «Утвержден» — buyurtma qabul qilindi, ishga tushdi, **tayyorlik sanasi** qo'yiladi (ORD-006);
  * «Готов» — tayyor mahsulot ombordan olinadi.
Yordam faqat shularni aytadi. Qolgan hamma narsa (o'tkazib yuborish, orqaga qaytarish, kim nima qila oladi, bloklash) yordamda
**yo'q** — quyidagi konstantalar orqasida standart tanlangan va `docs/mebelix/T_W14_BUYURTMA.md` da savol sifatida yozilgan.

Qoidalar jadvali (`TRANSITIONS` hujjat uchun, kod `check_transition` da):
  oldinga (0→1, 1→2, 2→3)               — yozish huquqi bor hamma rol;
  oldinga, o'tkazib (0→2, 0→3, 1→3)     — `ALLOW_SKIP_FORWARD` (standart ruxsat: avvalgi PATCH xulqi, ichki buyurtmalar);
  orqaga (har qanday kamayish)          — faqat `BACK_ROLES` (admin, texnolog) yoki rolsiz (eski/lokal) foydalanuvchi;
  «ko'ruvchi» (read_only)               — hech qanday o'zgartirish yo'q;
  «Утвержден» ga o'tishda tayyorlik sanasi belgilanadi (POST .../order: majburiy, agar sana hali qo'yilmagan bo'lsa).

MES: holat o'zgarsa mavjud `mes.send_webhook("project.status", …)` (fon vazifasi) — yuklama avvalgidek (project_id, number,
mes_order_ref, status, old_status). Ijrochi/izoh — faqat ichki tarixda, webhookka va MES eksportiga kirmaydi.
Tahrir bloklanishi: standart O'CHIQ (yordamda bloklash haqida gap yo'q) — faqat ogohlantirish; `MEBELIX_ORDER_LOCK_FROM=2|3`
bilan «Утвержден» / «Готов» dan boshlab loyiha tarkibini o'zgartiruvchi so'rovlar 409 bo'ladi (sarlavha, holat, undo — ochiq).
"""
from __future__ import annotations

import os
import re
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, Request
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from ..auth import SAFE_METHODS, _READONLY_POST, canonical_roles
from ..db import ProjectHistoryRow, ProjectRow, SessionLocal
from ..i18n import _
from ..models import OpType, OrderLogEntry, OrderStatus, Project
from . import warehouse

# ───────────────────────── Parametrlar (bitta joyda — o'zgartirish oson) ─────────────────────────
ALLOW_SKIP_FORWARD = True                              # 0→2, 0→3, 1→3 (avvalgi PATCH xulqi; ichki buyurtma uchun)
BACK_ROLES = frozenset({"admin", "technologist"})      # orqaga qaytara oladigan rollar (auth.canonical_roles nomlari)
ORDER_LOG_LIMIT = 100                                  # loyihada saqlanadigan tarix yozuvlari
LOCK_ENV = "MEBELIX_ORDER_LOCK_FROM"                   # «» / 0 = bloklanmaydi (standart); 2 yoki 3 — shu holatdan boshlab
YEAR_MIN, YEAR_MAX = 1990, 2100                        # tayyorlik sanasi oralig'i (main._check_date bilan bir xil)

# Hujjat uchun: (qayerdan, qayerga) → qoida. Kod shu jadvalga emas, check_transition ga tayanadi (testlar ikkalasini tekshiradi).
TRANSITIONS = {
    (0, 1): "forward", (1, 2): "forward", (2, 3): "forward",
    (0, 2): "skip", (0, 3): "skip", (1, 3): "skip",
    (1, 0): "back", (2, 0): "back", (2, 1): "back", (3, 0): "back", (3, 1): "back", (3, 2): "back",
}

_LOCK_PATH = re.compile(r"^/api/projects/([^/]+)/(operations|products|actions|import)(/|$)")
# MES ga yuborilgan loyiha: undo/redo ham yopiq; arradan kelgan «karta bajarildi» (`/maps/n`) va tekshiruv — ochiq
_SENT_PATH = re.compile(r"^/api/projects/([^/]+)/(operations|products|actions|import|undo|redo)(/|$)")
_SENT_OPEN = re.compile(r"/maps/\d+$|/edit/check$")


def status_name(s: int | OrderStatus) -> str:
    return _(f"order_st_{int(s)}")


def kind_of(old: int, new: int) -> str:
    """forward | skip | back | same."""
    if new == old:
        return "same"
    if new < old:
        return "back"
    return "forward" if new == old + 1 else "skip"


# ───────────────────────── Rollar ─────────────────────────
def user_caps(user: dict) -> dict:
    """Foydalanuvchi huquqlari: can_change (holat o'zgartirish), can_back (orqaga qaytarish). Rolsiz token / lokal rejim —
    to'liq huquq (auth.py dagi «rollari yo'q token avvalgidek» qoidasi); «ko'ruvchi» — hech narsa."""
    if user.get("read_only"):
        return dict(can_change=False, can_back=False)
    roles = canonical_roles(user.get("roles") or [])
    return dict(can_change=True, can_back=(not roles) or bool(roles & BACK_ROLES))


# ───────────────────────── Tekshiruvlar ─────────────────────────
def check_date(v: str) -> str:
    """Tayyorlik sanasi matni → ISO (YYYY-MM-DD); noto'g'ri yoki oraliqdan tashqari — 400."""
    try:
        d = TypeAdapter(date).validate_python(v.strip() if isinstance(v, str) else v)
    except ValidationError as e:
        raise HTTPException(400, _("val_date_bad", f="ready_date", v=str(v)[:30])) from e
    if not (YEAR_MIN <= d.year <= YEAR_MAX):
        raise HTTPException(400, _("val_date_range", f="ready_date", a=YEAR_MIN, b=YEAR_MAX))
    return d.isoformat()


def ready_is_set(p: Project) -> bool:
    """Tayyorlik sanasi qo'yilganmi? Yangi loyihada u buyurtma sanasiga teng (standart) — «qo'yilmagan» hisoblanadi."""
    return p.ready_date > p.order_date


def check_transition(p: Project, new: OrderStatus, user: dict, *, ready_given: bool = False,
                     strict_ready: bool = True) -> None:
    """Qoidalarni tekshiradi; buzilsa HTTPException (403 / 409 / 422). `ready_given` — so'rovda sana berilgan;
    `strict_ready=False` — «Утвержден» uchun sana talab qilinmaydi (PATCH sarlavha yo'li: eski mijozlar bilan moslik)."""
    old = p.status
    caps = user_caps(user)
    if not caps["can_change"]:
        raise HTTPException(403, _("forbidden_readonly"))
    k = kind_of(int(old), int(new))
    if k == "same":
        raise HTTPException(409, _("order_same", s=status_name(new)))
    if k == "back" and not caps["can_back"]:
        raise HTTPException(403, _("order_back_forbidden"))
    if k == "skip" and not ALLOW_SKIP_FORWARD:
        raise HTTPException(409, _("order_skip_forbidden", a=status_name(old), b=status_name(new)))
    if strict_ready and new == OrderStatus.APPROVED and not ready_given and not ready_is_set(p):
        raise HTTPException(422, _("order_ready_required"))


def warnings_for(p: Project, new: OrderStatus) -> list[dict]:
    """Bloklamaydigan ogohlantirishlar: [{code, n, text}] — matn so'rov tilida (UI to'g'ridan-to'g'ri ko'rsatadi)."""
    out: list[dict] = []
    cs = [o for o in p.operations if o.type in (OpType.CS, OpType.CL, OpType.CN)]
    if new == OrderStatus.ORDERED and not any(o.parts for o in cs):
        out.append(dict(code="no_parts", n=0, text=_("order_w_no_parts")))
    if new == OrderStatus.READY:
        no_cut = [o for o in cs if o.parts and o.result is None]
        if no_cut:
            out.append(dict(code="no_cut", n=len(no_cut), text=_("order_w_no_cut", n=len(no_cut))))
        open_maps = sum(1 for o in cs if o.result for m in o.result.maps if m.done_count < max(1, m.copies))
        if open_maps:
            out.append(dict(code="cut_open", n=open_maps, text=_("order_w_cut_open", n=open_maps)))
    return out


# ───────────────────────── O'tishni bajarish ─────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def apply_transition(p: Project, new: OrderStatus, user: dict, *, ready_date: Optional[str] = None, executor: str = "",
                     comment: str = "", via: str = "order") -> OrderLogEntry:
    """Holatni o'zgartiradi (qoidalar tekshirilgan deb hisoblanadi), tayyorlik sanasini qo'yadi va tarixga yozadi.
    `ready_date` — allaqachon tekshirilgan ISO sana yoki None."""
    old = p.status
    p.status = new
    if ready_date:
        p.ready_date = date.fromisoformat(ready_date)
    entry = OrderLogEntry(at=now_iso(), user=str(user.get("name") or "")[:100], from_status=old, to_status=new,
                          executor=executor.strip()[:200], comment=comment.strip()[:1000], ready_date=ready_date or "",
                          via=via)
    p.order_log = (list(p.order_log) + [entry])[-ORDER_LOG_LIMIT:]
    return entry


def webhook_payload(p: Project, old: OrderStatus) -> dict:
    """`project.status` yuklamasi — main.update_project_header dagi bilan aynan bir xil (MES tomoni o'zgarmaydi)."""
    return dict(project_id=p.id, number=p.number, mes_order_ref=p.mes_order_ref, status=int(p.status),
                old_status=int(old))


# ───────────────────────── Holat (UI uchun) ─────────────────────────
def lock_from() -> Optional[OrderStatus]:
    raw = (os.getenv(LOCK_ENV) or "").strip()
    return OrderStatus(int(raw)) if raw in ("2", "3") else None


def order_state(p: Project, user: dict) -> dict:
    """«Заказать» oynasi uchun: joriy holat, har maqsad holati bo'yicha ruxsat/sabab/ogohlantirishlar, tarix (yangisi birinchi)."""
    transitions = []
    for to in OrderStatus:
        if to == p.status:
            continue
        try:
            check_transition(p, to, user, ready_given=True)
            allowed, reason = True, None
        except HTTPException as e:
            allowed, reason = False, str(e.detail)
        transitions.append(dict(to=int(to), kind=kind_of(int(p.status), int(to)), allowed=allowed, reason=reason,
                                needs_ready_date=to == OrderStatus.APPROVED and not ready_is_set(p),
                                warnings=warnings_for(p, to) if allowed else []))
    last = p.order_log[-1] if p.order_log else None
    lock = lock_from()
    return dict(status=int(p.status), order_date=p.order_date.isoformat(), ready_date=p.ready_date.isoformat(),
                ready_set=ready_is_set(p), executor=last.executor if last else "", comment="",
                transitions=transitions, can_change=user_caps(user)["can_change"], can_back=user_caps(user)["can_back"],
                edit_warning=int(p.status) >= int(OrderStatus.APPROVED),
                lock=dict(from_status=int(lock) if lock is not None else None,
                          active=lock is not None and int(p.status) >= int(lock)),
                log=[e.model_dump(mode="json") for e in reversed(p.order_log)])


# ───────────────────────── Tahrir bloklanishi (ixtiyoriy) ─────────────────────────
def _guard_check(path: str, lock: OrderStatus) -> None:
    m = _LOCK_PATH.match(path)
    if not m or _READONLY_POST.match(path):
        return
    with SessionLocal() as s:
        st = s.scalar(select(ProjectRow.status).where(ProjectRow.id == m.group(1)))
    if st is not None and int(st) >= int(lock):
        raise HTTPException(409, _("order_locked", s=status_name(st)))


def _sent_check(path: str) -> None:
    """MES buyurtmasiga bog'lanmagan loyihada `data` o'qilmaydi (katta JSON) — oddiy loyihalarga yuklama yo'q."""
    m = _SENT_PATH.match(path)
    if not m or _READONLY_POST.match(path) or _SENT_OPEN.search(path):
        return
    with SessionLocal() as s:
        if not s.scalar(select(ProjectRow.mes_order_ref).where(ProjectRow.id == m.group(1))):
            return
        data = s.scalar(select(ProjectRow.data).where(ProjectRow.id == m.group(1)))
    sent = (data or {}).get("mes_sent")
    if sent:
        raise HTTPException(409, _("mes_send_locked", v=sent.get("version", 1)))


async def edit_guard(request: Request) -> None:
    """`api` routeri bog'liqligi: `MEBELIX_ORDER_LOCK_FROM` o'rnatilgan bo'lsa, shu holatdan boshlab loyiha tarkibini
    o'zgartiruvchi so'rovlar (operatsiyalar, mahsulotlar, `actions/*`, Excel import) 409 beradi. Sarlavha (PATCH), holat
    (`/order`), undo/redo, saqlash, nusxa, hisobot, oldindan ko'rish — ochiq. Standart: o'chiq — hech qanday so'rov
    to'xtamaydi va oqim (thread) almashtirilmaydi (async: o'qish/o'chiq holatda deyarli bepul)."""
    if request.method.upper() in SAFE_METHODS:
        return
    await run_in_threadpool(_sent_check, request.url.path)
    lock = lock_from()
    if lock is None:
        return
    await run_in_threadpool(_guard_check, request.url.path, lock)


# ───────────────────────── Undo / redo: orqaga qaytarish qoidasidan chetlab o'tilmasin ─────────────────────────
def check_step(pid: str, d: int, user: dict) -> None:
    """Undo (d=-1) / redo (d=+1) holatni pasaytirsa — orqaga qaytarish qoidasi (BACK_ROLES) tekshiriladi.
    Holat o'zgarmasa yoki ko'tarilsa — tekshiruv yo'q. «Ko'ruvchi» undo qila olmaydi."""
    from .. import store
    caps = user_caps(user)
    with SessionLocal() as s:
        row = s.get(ProjectRow, pid)
        if row is None:
            return                                           # 404 ni store.step beradi
        cur = (row.history_cursor or 0) + d
        h = s.scalar(select(ProjectHistoryRow).where(ProjectHistoryRow.project_id == pid,
                                                     ProjectHistoryRow.version == cur))
        old = int(row.status or 0)
        new = int((store.history_data(h) or {}).get("status", 0)) if h is not None else old
    if new == old:
        return
    if not caps["can_change"]:
        raise HTTPException(403, _("forbidden_readonly"))
    if new < old and not caps["can_back"]:
        raise HTTPException(403, _("order_back_forbidden"))


# ───────────────────────── «Очистить проект» ─────────────────────────
def clear_project(p: Project) -> dict[str, Any]:
    """«Очистить проект» (GibLab yordamida ma'nosi yo'q — TAXMINIY, xavfsiz talqin): loyihadagi **kroy natijalari va ulardan
    hisoblangan sanoqlar** tozalanadi: operatsiya natijalari (`result`: kartalar, qoldiqlar, sex «bajarildi» belgilari),
    detalning «Раскроено / Осталось», listning «Использовано». Omborga yozilgan qoldiqlar bekor qilinadi (xuddi qayta
    kroydagidek). Detallar, mahsulotlar, operatsiya parametrlari, listlar ro'yxati, kromka/XNC/etiketka ma'lumotlari — SAQLANADI.
    Qaytaradi: tozalangan operatsiyalar / kartalar soni va bekor qilingan ombor yozuvlari."""
    ops = maps = rolled = 0
    for op in p.operations:
        if op.result is not None:
            ops += 1
            maps += len(op.result.maps)
            if op.result.remnants_saved:
                warehouse.rollback(op)
                rolled += 1
        op.result = None
        for pt in op.parts:                   # saqlashda calc.recalc_project qayta hisoblaydi (kroysiz: Осталось = hammasi)
            pt.used_qty = pt.left_qty = 0
        for sh in op.sheets:
            sh.used_qty = 0
    return dict(operations=ops, maps=maps, warehouse_rolled_back=rolled)
