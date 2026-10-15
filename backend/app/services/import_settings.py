"""Importning umumiy sozlamalari (W18, `settings` doirasi `import_settings`) — serverda, hamma ish joyi uchun bir xil.

Hozircha bitta narsa: **katalog ildiz kategoriya ID lari** (`catalog_roots` = `{tur: ildiz papka ID}`) — «Товары» importida qator
turi (varaq / pogonaj / kromka / sirt) shu ildiz ostida bo'lishidan aniqlanadi (W3). Ilgari ular faqat import so'rovida va brauzerda
(`localStorage`) turardi; endi serverda saqlanadi: `PUT /api/settings/import_settings/default {catalog_roots: {...}}`.
`POST /catalog/import` da `roots` maydoni berilmasa — shu saqlangan qiymatlar ishlatiladi (berilsa, so'rovdagisi ustun).
"""
from __future__ import annotations

import re

from pydantic import BaseModel, field_validator

from ..i18n import _
from .catalog import KINDS

MAX_ROOT_ID = 40
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


class ImportSettings(BaseModel):
    catalog_roots: dict[str, str] = {}

    @field_validator("catalog_roots", mode="before")
    @classmethod
    def _roots(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(_("val_dict"))
        out: dict[str, str] = {}
        for k, x in v.items():
            if k not in KINDS:
                raise ValueError(_("imp_root_kind", k=str(k)[:30], x=", ".join(KINDS)))
            if x is None or isinstance(x, bool):
                continue
            s = str(x).strip()
            if not s:
                continue                                  # bo'sh = ildiz yo'q (standart tur)
            if len(s) > MAX_ROOT_ID:
                raise ValueError(_("val_str_long", v=MAX_ROOT_ID))
            if _CTRL.search(s):
                raise ValueError(_("pp_ctrl_chars"))
            out[k] = s
        return out


def saved_roots() -> dict[str, str]:
    """Serverda saqlangan ildiz kategoriya ID lari (yo'q bo'lsa — bo'sh)."""
    from . import settings
    try:
        return dict(settings.get_default("import_settings").get("catalog_roots") or {})
    except Exception:  # noqa: BLE001 — sozlama o'qilmasa import to'xtamasin
        return {}
