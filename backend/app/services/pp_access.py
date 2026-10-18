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

Qamrov: faqat stanokka bog'langan postprotsessorlar (`machine:<kalit>`). MebeliX'ning o'z umumiy eksportlari
(CSV / buyruqlar TXT / DXF / MES JSON, XNC JSON) va korxonaning o'z shablonlari (`pp:<id>`, stanoksiz) — stanok
formati emas, ular doim ochiq (ochiq savol sifatida hujjatda qayd etilgan). Har postprotsessor avvalgidek bitta
stanokka bog'langan (kalit = stanok kaliti, `postprocessors.MACHINES`).
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


def _row() -> Optional[dict]:
    with SessionLocal() as s:
        r = s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == SCOPE).order_by(SettingsProfileRow.id).first()
        return dict(r.data or {}) if r is not None else None


def is_explicit() -> bool:
    return _row() is not None


def open_keys() -> set[str]:
    """Ochilgan stanok kalitlari (saqlangan ro'yxat yoki standart)."""
    from .postprocessors import MACHINE_BY_KEY
    row = _row()
    if row is None:
        return default_open()
    return {k for k in (row.get("open") or []) if k in MACHINE_BY_KEY}


def is_open(key: str) -> bool:
    return key in open_keys()


def label(key: str) -> str:
    from ..i18n import LANG
    from .postprocessors import pp_label
    return pp_label(key, LANG.get())


def require_open(key: str) -> None:
    """Yopiq stanok postprotsessori — 403 (ru/uz xabar). Noma'lum kalit tekshiruvi chaqiruvchida (400)."""
    if not is_open(key):
        raise HTTPException(403, _("pp_closed", n=label(key)))


def usable(key: str, opened: Optional[set[str]] = None) -> bool:
    """Ishlaydimi: ochilgan ∧ (o'rnatilgan generator ∨ (yoqilgan ∧ shablon biriktirilgan))."""
    if key not in (opened if opened is not None else open_keys()):
        return False
    c = _cfg()
    if key in c["bound"]:                    # shablon ustun (ishga tushirish qoidasi bilan bir xil): stanok yoqilgan bo'lishi shart
        return key in c["enabled"]
    return key in _native()


def state() -> dict:
    """GET javobi: {explicit, open: [kalit], machines: [{key, name, group, label, open, native}], updated_by, updated_at}."""
    from ..i18n import LANG
    from .postprocessors import MACHINES, pp_label, pp_order
    row = _row()
    opened = open_keys()
    nat = _native()
    ms = [dict(key=k, name=n, group=g, label=pp_label(k, LANG.get()), open=k in opened, native=k in nat)
          for k, n, g in MACHINES]
    ms.sort(key=lambda m: (m["group"] != "saw", pp_order(m["key"])))
    return dict(explicit=row is not None, open=sorted(opened), machines=ms,
                updated_by=(row or {}).get("updated_by", ""), updated_at=(row or {}).get("updated_at", ""))


def set_open(keys: Optional[list[str]], user: str = "") -> dict:
    """Ochilgan ro'yxatni saqlash (`None` — saqlanganini o'chirib standartga qaytarish). Noma'lum kalit — 400."""
    from .postprocessors import MACHINE_BY_KEY
    with SessionLocal() as s:
        q = s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == SCOPE)
        if keys is None:
            q.delete()
            s.commit()
            return state()
        bad = [k for k in keys if k not in MACHINE_BY_KEY]
        if bad:
            raise HTTPException(400, _("pp_machine_unknown", k=", ".join(bad)[:200]))
        data = dict(open=sorted(set(keys)), updated_by=(user or "")[:100],
                    updated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        r = q.order_by(SettingsProfileRow.id).first()
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
