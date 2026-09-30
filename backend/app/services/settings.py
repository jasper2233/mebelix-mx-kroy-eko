"""Sozlamalar profillari (settings_profiles jadvali).

scope lar:
  cs_defaults   — yangi CS operatsiya parametrlari  {material: CSMaterialParams, cut: CSCutParams}
  el_defaults   — yangi EL operatsiya parametrlari  (ELParams)
  print         — «Печать отчета» profillari         (PrintSettings)
  labels        — etiketka profillari                (LabelSettings)
  part_columns  — «Настройки колонок» profillari     ({columns: [{key, title?, visible, width}]})
  postprocessor — foydalanuvchi postprotsessorlari  (PostprocessorProfile)
  app           — umumiy: standart valyuta, til, detal kiritish rejimi taklifi
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from ..db import SessionLocal, SettingsProfileRow
from ..i18n import _
from ..models import CSCutParams, CSMaterialParams, ELParams, LabelSettings, PostprocessorProfile, PrintSettings


class CSDefaults(BaseModel):
    material: CSMaterialParams = CSMaterialParams()
    cut: CSCutParams = CSCutParams()


class AppSettings(BaseModel):
    currency: str = "UZS"
    language: str = "ru"                    # ru | uz
    input_mode_suggest: str = "none"        # none | blank | detail | jointed («Режимы ввода деталей»)
    remnant_confirm: bool = True            # kroydan keyin qoldiqlarni omborga yozishni so'rash
    default_sheet_length: float = 2750
    default_sheet_width: float = 1830


MODELS: dict[str, type[BaseModel] | None] = {
    "cs_defaults": CSDefaults, "el_defaults": ELParams, "print": PrintSettings, "labels": LabelSettings,
    "postprocessor": PostprocessorProfile, "app": AppSettings, "part_columns": None,
}
SCOPES = tuple(MODELS)


class SettingsError(ValueError):
    pass


def validate_data(scope: str, data: Any) -> dict:
    if scope not in MODELS:
        raise SettingsError(_("set_unknown_scope", s=scope))
    model = MODELS[scope]
    if model is None:
        if not isinstance(data, dict):
            raise SettingsError(_("set_json_object"))
        return data
    try:
        return model.model_validate(data or {}).model_dump(mode="json")
    except ValidationError as e:
        raise SettingsError(_("set_invalid", e=e)) from e


def builtin(scope: str) -> dict:
    model = MODELS.get(scope)
    if scope == "postprocessor":
        return {}
    return model().model_dump(mode="json") if model else {"columns": []}


def _row(r: SettingsProfileRow) -> dict:
    return dict(id=r.id, scope=r.scope, name=r.name, data=r.data or {}, is_default=bool(r.is_default))


def list_profiles(scope: str) -> list[dict]:
    with SessionLocal() as s:
        rows = s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == scope).order_by(SettingsProfileRow.id).all()
        return [_row(r) for r in rows]


def get_profile(scope: str, pid: int) -> dict | None:
    with SessionLocal() as s:
        r = s.get(SettingsProfileRow, pid)
        return _row(r) if r and r.scope == scope else None


def create(scope: str, name: str, data: Any, is_default: bool = False) -> dict:
    clean = validate_data(scope, data)
    with SessionLocal() as s:
        if is_default:
            s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == scope).update({"is_default": False})
        r = SettingsProfileRow(scope=scope, name=name, data=clean, is_default=is_default)
        s.add(r); s.commit()
        return _row(r)


def update(scope: str, pid: int, name: str | None = None, data: Any = None, is_default: bool | None = None) -> dict:
    with SessionLocal() as s:
        r = s.get(SettingsProfileRow, pid)
        if not r or r.scope != scope:
            raise KeyError(pid)
        if name is not None:
            r.name = name
        if data is not None:
            r.data = validate_data(scope, data)
        if is_default:
            s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == scope).update({"is_default": False})
            r.is_default = True
        elif is_default is False:
            r.is_default = False
        s.commit()
        return _row(r)


def delete(scope: str, pid: int) -> None:
    with SessionLocal() as s:
        r = s.get(SettingsProfileRow, pid)
        if not r or r.scope != scope:
            raise KeyError(pid)
        s.delete(r); s.commit()


def get_default(scope: str) -> dict:
    """Standart profil ma'lumotlari (o'rnatilgan qiymatlar ustiga)."""
    with SessionLocal() as s:
        r = s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == scope,
                                               SettingsProfileRow.is_default.is_(True)).first()
        data = r.data if r else None
    base = builtin(scope)
    if not data:
        return base
    if isinstance(base, dict) and isinstance(data, dict):
        merged = {**base, **data}
        try:
            return validate_data(scope, merged)
        except SettingsError:
            return base
    return data


def set_default(scope: str, data: Any, name: str = "Standart") -> dict:
    clean = validate_data(scope, data)
    with SessionLocal() as s:
        r = s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == scope,
                                               SettingsProfileRow.is_default.is_(True)).first()
        if r is None:
            r = SettingsProfileRow(scope=scope, name=name, data=clean, is_default=True)
            s.add(r)
        else:
            r.data = clean
        s.commit()
        return _row(r)


def resolve(scope: str, profile_id: int | None) -> dict:
    """Berilgan profil (bo'lmasa standart) ma'lumotlari."""
    if profile_id:
        pr = get_profile(scope, profile_id)
        if pr:
            base = builtin(scope)
            return {**base, **pr["data"]} if isinstance(base, dict) else pr["data"]
    return get_default(scope)


def seed() -> None:
    """Birinchi ishga tushishda: namunaviy postprotsessor profili."""
    from .postprocessors import EXAMPLE_TEMPLATE
    if not list_profiles("postprocessor"):
        create("postprocessor", "Namuna — bizning arra stanogi", PostprocessorProfile(
            name="Namuna — bizning arra stanogi", extension="txt", per_map=True, newline="crlf",
            template=EXAMPLE_TEMPLATE,
            description="Shablonni stanok formatiga moslang (Настройки → Постпроцессоры)").model_dump())
