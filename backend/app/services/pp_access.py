"""Postprotsessorlarga kirish huquqi («mijoz uchun ochilgan» postprotsessorlar) — 2026-10-18 foydalanuvchi qarori.

MODEL (ikki qatlam, ikkalasi ham bajarilishi shart):

  1) **Ochilgan (litsenziya)** — `pp_access`: shu korxona (mijoz) uchun qaysi stanok postprotsessorlari ulangan.
     Faqat **administrator** o'zgartiradi (`PUT /api/postprocessors/access`); boshqalar faqat o'qiydi.
     Saqlanishi: `settings_profiles` jadvalida `scope="pp_access"` qatori ({open: [kalit], updated_by, updated_at}).
     Bu scope ataylab `settings.MODELS` ga kiritilmagan — umumiy `/api/settings/{scope}` yo'llari va sozlamalar
     zaxirasi (backup import) orqali uni o'zgartirib bo'lmaydi; yagona yo'l — admin endpointi.
     Qator YO'Q bo'lsa (standart, hech narsa buzilmasin) — ochilgan = bugun ishlayotganlarning hammasi:
     o'rnatilgan generatori bor stanoklar (`services/ppfmt`) ∪ yoqilgan stanoklar ∪ shablon biriktirilgan stanoklar.

  2) **Yoqilgan / sozlangan** — mavjud `pp_machines` (texnolog): stanokni yoqish, format shablonini biriktirish,
     parametrlar, prefiks («Настройки → Постпроцессоры»). O'zgarmagan.

  Ishlaydi = ochilgan ∧ (o'rnatilgan generator bor ∨ (yoqilgan ∧ shablon biriktirilgan)).
  Yopiq postprotsessor ro'yxatlarda nomi bilan qoladi (xira, bosilmaydi), server esa uni 403 bilan rad etadi
  (UI da yashirish yetarli emas: MCP / API ham shu tekshiruvdan o'tadi).

Qamrov (2026-10-18, 2-qaror): stanok postprotsessorlari (`machine:<kalit>`) VA MebeliX'ning o'z formatlari hamda korxona
shablonlari («qo'shimchalar», `EXTRA`):
  * `mx:csv`, `mx:commands`, `mx:dxf`, `mx:json` — kroy (CS / CL / CN) o'rnatilgan eksportlari (`postprocessors.BUILTIN`);
  * `mx:xnc_json` — XNC JSON (`postprocessors.XNC_BUILTIN`);
  * `mx:mes_export` — MES uchun loyiha natijasi (`/projects/{id}/mes-export`, `GET /mes/orders/{ref}`);
  * `mx:mes_package` — MES paketi v1 (`/projects/{id}/mes-package`; sxema ochiq);
  * `pp:<id>` — korxona shabloni stanoksiz (profile_id bilan) ishga tushirilganda. Stanokka biriktirilgan shablon stanok
    kaliti bilan tekshiriladi (shablon yopiqligi stanokni to'xtatmaydi).
  Qo'shimchalar standart OCHIQ: qatorda faqat yopilganlari saqlanadi (`closed_extra`), yangi shablon ham ochiq tug'iladi.
  Shablon muharriridagi jonli ko'rish (`POST /postprocessors/preview`) va etiketka maydonlari ko'rinishi tekshirilmaydi —
  ular fayl chiqarmaydi (muharrir ishlashi uchun). Qator: {open?: [stanok], closed_extra?: [kalit], updated_by, updated_at};
  `open` kaliti yo'q bo'lsa stanoklar standart holatda (`default_open`).
Har postprotsessor avvalgidek bitta stanokka bog'langan (kalit = stanok kaliti, `postprocessors.MACHINES`).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException

from ..db import SessionLocal, SettingsProfileRow
from ..i18n import _

SCOPE = "pp_access"


def _cfg() -> dict:
    from . import settings
    d = settings.get_default("pp_machines") or {}
    return dict(enabled={k for k, v in (d.get("enabled") or {}).items() if v},
                bound={k for k, v in (d.get("profile") or {}).items() if v is not None})


def _native(group: Optional[str] = None) -> set[str]:
    from . import ppfmt
    return {k for k, f in ppfmt.load_all().items() if group is None or f.group == group}


def default_open() -> set[str]:
    """Saqlangan ro'yxat yo'q bo'lsa — bugun ishlayotgan stanoklar (o'rnatilgan ∪ yoqilgan ∪ shablon biriktirilgan)."""
    from .postprocessors import MACHINE_BY_KEY
    c = _cfg()
    return {k for k in MACHINE_BY_KEY if k in _native() or k in c["enabled"] or k in c["bound"]}


# MebeliX'ning o'z formatlari: kalit → (guruh, i18n kaliti). Guruh — admin oynasidagi bo'lim (saw — kroy, cnc — XNC, mes — MES)
EXTRA_MX: dict[str, tuple[str, str]] = {
    "mx:csv": ("saw", "pp_builtin_csv"),
    "mx:commands": ("saw", "pp_builtin_commands"),
    "mx:dxf": ("saw", "pp_builtin_dxf"),
    "mx:json": ("saw", "pp_builtin_json"),
    "mx:xnc_json": ("cnc", "pp_builtin_xnc_json"),
    "mx:mes_export": ("mes", "pp_extra_mes_export"),
    "mx:mes_package": ("mes", "pp_extra_mes_package"),
}


def _templates() -> dict[str, dict]:
    """Korxona shablonlari: `pp:<id>` → profil."""
    from . import settings
    return {f"pp:{r['id']}": r for r in settings.list_profiles("postprocessor")}


def _row() -> Optional[dict]:
    with SessionLocal() as s:
        r = s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == SCOPE).order_by(SettingsProfileRow.id).first()
        return dict(r.data or {}) if r is not None else None


def is_explicit() -> bool:
    """Stanoklar ro'yxati admin tomonidan saqlanganmi (qo'shimchalarning yopilishi bunga kirmaydi)."""
    row = _row()
    return row is not None and "open" in row


def open_keys() -> set[str]:
    """Ochilgan stanok kalitlari (saqlangan ro'yxat yoki standart)."""
    from .postprocessors import MACHINE_BY_KEY
    row = _row()
    if row is None or "open" not in row:
        return default_open()
    return {k for k in (row.get("open") or []) if k in MACHINE_BY_KEY}


def closed_extras() -> set[str]:
    """Yopilgan qo'shimchalar (MebeliX formatlari va shablonlar); o'chirilgan shablonlar hisobga olinmaydi."""
    row = _row() or {}
    keys = set(row.get("closed_extra") or [])
    tpls = _templates() if any(k.startswith("pp:") for k in keys) else {}
    return {k for k in keys if k in EXTRA_MX or k in tpls}


def is_open(key: str) -> bool:
    return key in open_keys()


def extra_open(key: str) -> bool:
    return key not in closed_extras()


def label(key: str) -> str:
    from ..i18n import LANG
    from .postprocessors import pp_label
    return pp_label(key, LANG.get())


def extra_label(key: str) -> str:
    if key in EXTRA_MX:
        return _(EXTRA_MX[key][1])
    r = _templates().get(key)
    return (r["name"] or (r["data"] or {}).get("name", "")) if r else key


def require_open(key: str) -> None:
    """Yopiq stanok postprotsessori — 403 (ru/uz xabar). Noma'lum kalit tekshiruvi chaqiruvchida (400)."""
    if not is_open(key):
        raise HTTPException(403, _("pp_closed", n=label(key)))


def require_extra(key: str) -> None:
    """Yopiq MebeliX formati yoki shablon (`mx:*`, `pp:<id>`) — 403 (stanoklar bilan bir xil xabar)."""
    if not extra_open(key):
        raise HTTPException(403, _("pp_closed", n=extra_label(key)))


def usable(key: str, opened: Optional[set[str]] = None) -> bool:
    """Ishlaydimi: ochilgan ∧ (o'rnatilgan generator ∨ (yoqilgan ∧ shablon biriktirilgan))."""
    if key not in (opened if opened is not None else open_keys()):
        return False
    c = _cfg()
    if key in c["bound"]:                    # shablon ustun (ishga tushirish qoidasi bilan bir xil): stanok yoqilgan bo'lishi shart
        return key in c["enabled"]
    return key in _native()


def extras_state(closed: Optional[set[str]] = None) -> list[dict]:
    """Admin oynasi uchun qo'shimchalar: avval MebeliX formatlari (kroy, XNC, MES), keyin shablonlar."""
    from .postprocessors import template_kind
    closed = closed_extras() if closed is None else closed
    out = [dict(key=k, kind="mx", group=g, label=_(lk), open=k not in closed) for k, (g, lk) in EXTRA_MX.items()]
    for k, r in _templates().items():
        d = r["data"] or {}
        out.append(dict(key=k, kind="template", group=template_kind(d.get("template", "")), label=r["name"] or d.get("name", ""),
                        extension=d.get("extension", "txt"), open=k not in closed))
    return out


def state() -> dict:
    """GET javobi: {explicit, open: [kalit], machines: [{key, name, group, label, open, native}],
    closed_extra: [kalit], extras: [{key, kind (mx|template), group, label, open}], updated_by, updated_at}."""
    from ..i18n import LANG
    from .postprocessors import MACHINES, pp_label, pp_order
    row = _row()
    opened = open_keys()
    nat = _native()
    ms = [dict(key=k, name=n, group=g, label=pp_label(k, LANG.get()), open=k in opened, native=k in nat)
          for k, n, g in MACHINES]
    ms.sort(key=lambda m: (m["group"] != "saw", pp_order(m["key"])))
    closed = closed_extras()
    return dict(explicit=row is not None and "open" in row, open=sorted(opened), machines=ms,
                closed_extra=sorted(closed), extras=extras_state(closed),
                updated_by=(row or {}).get("updated_by", ""), updated_at=(row or {}).get("updated_at", ""))


_KEEP = object()        # PUT da maydon berilmagan — saqlangani o'zgarmaydi


def set_open(keys=_KEEP, user: str = "", closed_extra=_KEEP) -> dict:
    """Kirish ro'yxatini saqlash.
    `keys` — ochilgan stanoklar: ro'yxat | `None` (standartga qaytarish) | berilmagan (o'zgarmaydi);
    `closed_extra` — yopilgan qo'shimchalar: ro'yxat | `None` (hammasi ochiq) | berilmagan.
    Faqat `keys=None` (closed_extra berilmagan) — eski xulq: hammasi standartga (qator o'chiriladi). Noma'lum kalit — 400."""
    from .postprocessors import MACHINE_BY_KEY
    if keys is not _KEEP and keys is not None:
        bad = [k for k in keys if k not in MACHINE_BY_KEY]
        if bad:
            raise HTTPException(400, _("pp_machine_unknown", k=", ".join(bad)[:200]))
    if closed_extra is not _KEEP and closed_extra is not None:
        tpls = _templates()
        bad = [k for k in closed_extra if k not in EXTRA_MX and k not in tpls]
        if bad:
            raise HTTPException(400, _("pp_extra_unknown", k=", ".join(map(str, bad))[:200]))
    with SessionLocal() as s:
        q = s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == SCOPE)
        r = q.order_by(SettingsProfileRow.id).first()
        if keys is None and closed_extra is _KEEP:
            q.delete()
            s.commit()
            return state()
        data = {k: v for k, v in dict(r.data or {}).items() if k in ("open", "closed_extra")} if r is not None else {}
        if keys is not _KEEP:
            if keys is None:
                data.pop("open", None)
            else:
                data["open"] = sorted(set(keys))
        if closed_extra is not _KEEP:
            if closed_extra:
                data["closed_extra"] = sorted(set(closed_extra))
            else:
                data.pop("closed_extra", None)
        if not data:                          # hech narsa saqlanmagan — standart holat
            q.delete()
            s.commit()
            return state()
        data.update(updated_by=(user or "")[:100], updated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        if r is None:
            s.add(SettingsProfileRow(scope=SCOPE, name="pp_access", data=data, is_default=True))
        else:
            r.data = data
        s.commit()
    return state()


def require_admin(user: dict) -> None:
    """Ochish / yopish — faqat «administrator» roli (tokensiz lokal rejim — admin). Rolsiz token ham admin emas."""
    from ..auth import canonical_roles
    if user.get("read_only") or "admin" not in canonical_roles(user.get("roles") or []):
        raise HTTPException(403, _("pp_access_admin"))
