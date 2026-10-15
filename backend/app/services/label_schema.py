"""`label_template` sozlama scope i uchun model: LB shablon JSON (kutubxona profili ma'lumoti).

Tuzilma `label_tpl.normalize_template` bilan tekshiriladi (kech import — settings ↔ render aylanishi bo'lmasin);
ifoda sintaksisi saqlashda tekshirilmaydi (muharrir `POST /api/label-templates/check` bilan ko'rsatadi)."""
from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LabelTemplateDoc(BaseModel):
    model_config = ConfigDict(extra="allow")
    v: int = 1
    name: str = ""
    size: dict = Field(default_factory=lambda: {"w": 58, "h": 40})
    params: list = Field(default_factory=list)
    vars: list = Field(default_factory=list)
    elements: list = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any):
        from .label_tpl import normalize_template
        return normalize_template(data if data not in (None, "") else {})


# ───────────────────────── ZPL (W15): printer sozlamalari ─────────────────────────
_ZPL_FONT_RE = re.compile(r"^(?:[0-9A-Z]|[A-Z]:[A-Za-z0-9_-]{1,16}\.(?:TTF|TTE|OTF|FNT))$")
_ZPL_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_ZPL_FORMAT_RE = re.compile(r"\^X[AZ]", re.IGNORECASE)
ZPL_HEADER_MAX = 2000


class ZplSettings(BaseModel):
    """«ZPL» chiqarish sozlamalari (`label_zpl` scope — standart profil; so'rovda ham berilishi mumkin).

    dpi — printer zichligi (203 / 300); header — har etiketkaga qo'shiladigan foydalanuvchi buyruqlari («ZPL Header»: `~SD`, `^PR`,
    `^MD`, `^CW` va h.k.; `~` buyruqlari `^XA` dan oldin, qolganlari `^XA`, `^CI28`, `^PW`, `^LL` dan keyin; `^XA`/`^XZ` olib tashlanadi); utf8 — `^CI28`;
    font — `^A` shrifti: bitta belgi (`0` — o'rnatilgan masshtablanadigan, `A`…`H`, …) yoki printer xotirasidagi fayl
    (`E:ARIAL.TTF` — kirill matn uchun printerga oldindan yuklanadi); emit_size — `^PW`/`^LL` yozilsin."""
    model_config = ConfigDict(extra="ignore")
    dpi: Literal[203, 300] = 203
    header: str = Field("", max_length=ZPL_HEADER_MAX)
    utf8: bool = True
    font: str = "0"
    emit_size: bool = True

    @field_validator("header", mode="before")
    @classmethod
    def _header(cls, v: Any) -> str:
        s = "" if v is None else str(v)
        return _ZPL_FORMAT_RE.sub("", _ZPL_CTRL_RE.sub("", s)).strip()

    @field_validator("font", mode="before")
    @classmethod
    def _font(cls, v: Any) -> str:
        s = ("0" if v in (None, "") else str(v)).strip().upper()
        if not _ZPL_FONT_RE.match(s):
            from ..i18n import _
            raise ValueError(_("lb.zpl_font_bad"))
        return s
