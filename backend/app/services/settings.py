"""Sozlamalar profillari (settings_profiles jadvali).

scope lar:
  cs_defaults   — yangi CS operatsiya parametrlari  {material: CSMaterialParams, cut: CSCutParams}
  el_defaults   — yangi EL operatsiya parametrlari  (ELParams)
  o_defaults    — yangi O (Комплектация) operatsiya standarti  {work_cost, unit}
  gr_defaults   — yangi GR operatsiya parametrlari  (GRParams; usage/cut_length/passes saqlanmaydi)
  sp_defaults   — yangi SP (sirt ishlovi) operatsiya parametrlari (SPParams; area_m2/material_m2 saqlanmaydi)
  cl_defaults   — yangi CL (погонажный раскрой) operatsiya parametrlari (CLParams; usage_m/multiplicity saqlanmaydi)
  print         — «Печать отчета» profillari         (PrintSettings)
  labels        — etiketka profillari                (LabelSettings; eski qat'iy etiketka — `/projects/{id}/labels`)
  lb_defaults   — yangi LB (Этикетки) operatsiya parametrlari (LBParams; tanlov/shablon nusxasi/qatorlar saqlanmaydi)
  label_template — LB shablon kutubxonasi (JSON shablon; services/label_tpl.py, label_schema.LabelTemplateDoc)
  label_zpl     — LB: ZPL chiqarish sozlamalari (dpi 203/300, «ZPL Header», shrift; label_schema.ZplSettings — standart profil)
  part_columns  — «Настройки колонок» profillari     ({columns: [{key, title?, visible, width}]})
  o_columns / el_columns / cl_columns / cn_columns — boshqa jadvallar «Настройки» (Ctrl+P) profillari va standarti
                  (GridColumns: {columns: [{key, visible, title?, width? (belgilarda), user?}]}; standart — `PUT …/default`;
                  `user` — foydalanuvchi ustuni: {kind: param|expr, vtype: string|int|double|bool, desc, expr}, kalit = parametr nomi)
  excel_import  — «Импорт из Excel» ustun xaritasi profillari ({map: {...}, start: int})
  import_profile — «Импорт из других программ» profillari ({format, params}; services/import_formats.py, W18)
  import_settings — importning umumiy sozlamalari (W18): katalog ildiz kategoriya ID lari (`catalog_roots`)
  postprocessor — foydalanuvchi postprotsessorlari  (PostprocessorProfile)
  xnc_template  — XNC shablonlar kutubxonasi (nom bilan saqlangan dasturlar; XncTemplate)
  xnc_constraints — «Настройки → XNC → Ограничения»: stanok cheklovlari (XncConstraints; standart profil)
  xnc_tools     — «… → Инструменты»: asboblar jadvali (XncToolsDoc; standart profil); hisobda T nomi bo'yicha zaxira
  xnc_palette   — «… → Палитра»: XNC buyruqlar palitrasi tartibi/yoqilganligi (XncPalette; standart profil)
  el_symbols    — (EL) «Настройка символов и цветов»: kromka belgilari va ranglari jadvali (ElSymbolsDoc; standart profil)
  app          — umumiy: standart valyuta, til, detal kiritish rejimi taklifi
"""
from __future__ import annotations

from typing import Any

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from ..db import SessionLocal, SettingsProfileRow
from ..i18n import _, format_errors
from .o_ops import ODefaults
from .xnc_templates import XncTemplate
from .xnc_constraints import XncConstraints
from .xnc_tools import XncPalette, XncToolsDoc, invalidate as _xnc_tools_invalidate
from ..models import USER_PARAM_NAME_RE
from ..models import (CLParams, CNParams, CSCutParams, CSMaterialParams, ELParams, GRParams, LBParams, LabelSettings,
                      PostprocessorProfile, PrintSettings, SPParams)
from .label_schema import LabelTemplateDoc, ZplSettings
from .import_formats import ImportProfile
from .import_settings import ImportSettings
from .el_symbols import ElSymbolsDoc, invalidate as _el_symbols_invalidate


class CSDefaults(BaseModel):
    material: CSMaterialParams = CSMaterialParams()
    cut: CSCutParams = CSCutParams()


class UserColumn(BaseModel):
    """Foydalanuvchi ustuni («Свойства» oynasi): «Настроенный Параметры» (`param` — qiymat har qatorda `user_params[kalit]` da,
    matn sifatida) yoki «Выражение» (`expr` — qator maydonlari va parametrlaridan hisoblanadi, faqat o'qish)."""
    kind: Literal["param", "expr"] = "param"
    vtype: Literal["string", "int", "double", "bool"] = "string"      # «Тип колонки»
    desc: str = Field("", max_length=300)                              # «Описание» (sarlavha maslahati)
    expr: str = Field("", max_length=1000)                             # «Выражение» (services/expr.py tili)

    @field_validator("expr")
    @classmethod
    def _expr_syntax(cls, v: str) -> str:
        if v.strip():
            from . import expr as E
            E.compile_check(v)                                          # sintaksis xatosi — ValueError (foydalanuvchi tilida)
        return v


class GridColumn(BaseModel):
    """Jadval ustuni profilda: kalit (frontend katalogi), yoqilgan, foydalanuvchi nomi, kenglik (belgilarda).
    Foydalanuvchi ustunida (`user`) kalit — parametr nomi («material.name1»): ifoda tilidagi o'zgaruvchi nomi bo'lishi shart."""
    key: str = Field(min_length=1, max_length=40)
    visible: bool = True
    title: str | None = Field(None, max_length=100)
    width: float | None = Field(None, gt=0, le=300, allow_inf_nan=False)
    user: UserColumn | None = None

    @model_validator(mode="after")
    def _user_key(self):
        if self.user is not None and not USER_PARAM_NAME_RE.match(self.key):
            raise ValueError(_("set_user_col_name", name=self.key))
        return self


class GridColumns(BaseModel):
    """`o_columns`, `el_columns`, `cl_columns`, `cn_columns`: «Настройки» oynasi (ustunlar tartibi, ko'rinishi, nomi, kengligi,
    foydalanuvchi ustunlari)."""
    columns: list[GridColumn] = Field(default_factory=list, max_length=200)

    @field_validator("columns")
    @classmethod
    def _unique(cls, v: list[GridColumn]) -> list[GridColumn]:
        seen: set[str] = set()
        for c in v:
            if c.key in seen:
                raise ValueError(_("set_col_dup", col=c.key))
            seen.add(c.key)
        return v


# ustunlar profillari bor jadvallar (CS detallari — eski `part_columns`, tekshiruvsiz)
# cs_sheets_columns — CS «Листы и остатки» jadvali (2026-10-18)
GRID_COLUMN_SCOPES = ("o_columns", "el_columns", "cl_columns", "cn_columns", "cs_sheets_columns",
                      "ops_columns", "catalog_columns",      # «Операции» va «Товары» (Каталог товаров) jadvallari (2026-10-18)
                      "products_columns")                    # «Изделия» jadvali (2-qism, 2026-10-18)


class XncDefaults(BaseModel):
    """`xnc_defaults`: yangi XNC operatsiyasining narxlari (teshik, 1 m freza, 1 m arra, qo'shimcha qiymat)."""
    drill_price: float = Field(0, ge=0, le=1e9, allow_inf_nan=False)
    mill_price_m: float = Field(0, ge=0, le=1e9, allow_inf_nan=False)
    saw_price_m: float = Field(0, ge=0, le=1e9, allow_inf_nan=False)
    extra_cost: float = Field(0, ge=0, le=1e9, allow_inf_nan=False)


class AppSettings(BaseModel):
    currency: str = "UZS"
    language: str = "ru"                    # ru | uz
    input_mode_suggest: str = "none"        # none | blank | detail | jointed («Режимы ввода деталей»)
    remnant_confirm: bool = False           # kroydan keyin qoldiqlarni omborga yozishni so'rash (standart o'chiq — oyna
                                            # ish oqimini to'xtatmasin; asboblar panelidagi «Деловые остатки → склад» tugmasi bor)
    default_sheet_length: float = Field(2750, gt=0, le=20000, allow_inf_nan=False)    # mm; yangi CS listi
    default_sheet_width: float = Field(1830, gt=0, le=20000, allow_inf_nan=False)
    mes_enabled: bool = False               # «MES» bo'limi (chap panel) — integratsiya yoqilgandagina faol

    @field_validator("currency")
    @classmethod
    def _currency(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError(_("val_currency_empty"))
        if len(v) > 10:
            raise ValueError(_("val_str_long", v=10))
        return v


MODELS: dict[str, type[BaseModel] | None] = {
    "cs_defaults": CSDefaults, "el_defaults": ELParams, "gr_defaults": GRParams, "print": PrintSettings, "labels": LabelSettings,
    "sp_defaults": SPParams,     # (SP) Обработка поверхности: yangi operatsiya parametrlari (area_m2 / material_m2 saqlanmaydi)
    "cl_defaults": CLParams,     # (CL) Погонажный раскрой: yangi operatsiya parametrlari (usage_m / multiplicity saqlanmaydi)
    "cn_defaults": CNParams,     # (CN, W16) Нестинговый раскрой: yangi operatsiya parametrlari (usage_m2 / multiplicity saqlanmaydi)
    "o_defaults": ODefaults,    # (O) Комплектация: yangi operatsiyaning ish narxi va yangi qatorlar birligi
    "xnc_defaults": XncDefaults,  # (XNC) yangi operatsiya narxlari («Сохранить текущие параметры для использования по умолчанию»)
    "postprocessor": PostprocessorProfile, "app": AppSettings, "part_columns": None,
    "excel_import": None,        # «Импорт из Excel» profillari: {map: {maydon: ustun}, start: boshlang'ich qator}
    "pp_machines": None,         # postprotsessor stanoklari: {enabled: {kalit: bool}, profile: {kalit: profil id}, prefix: bool}
    "xnc_template": XncTemplate,     # XNC shablonlar kutubxonasi: {description, category, program: [XncCommand], par_values}
    "xnc_constraints": XncConstraints, "xnc_tools": XncToolsDoc, "xnc_palette": XncPalette,     # XNC muharriri sozlamalari (W8)
    "lb_defaults": LBParams,         # (LB) yangi etiketka operatsiyasi parametrlari (tanlov/shablon nusxasi/qatorlar saqlanmaydi)
    "label_template": LabelTemplateDoc,    # LB shablon kutubxonasi (JSON shablon; services/label_tpl.py)
    "label_zpl": ZplSettings,              # LB: ZPL chiqarish sozlamalari (dpi, «ZPL Header», shrift; standart profil — W15)
    "import_profile": ImportProfile,       # «Импорт из других программ» profillari (W18): format + standartdan farqli parametrlar
    "import_settings": ImportSettings,     # importning umumiy sozlamalari (W18): katalog ildiz kategoriya ID lari
    "el_symbols": ElSymbolsDoc,            # (EL) «Настройка символов и цветов»: yangi kromkalar belgisi / rangi jadvali (standart profil)
    **{s: GridColumns for s in GRID_COLUMN_SCOPES},   # O / EL / CL / CN jadvallari «Настройки» (Ctrl+P) profillari va standarti
}
SCOPES = tuple(MODELS)


def _changed(scope: str) -> None:
    """Sozlama yozildi: hisobda keshlanadigan jadvallar yangilansin (asboblar jadvali — services/xnc_tools.py)."""
    if scope == "xnc_tools":
        _xnc_tools_invalidate()
    elif scope == "el_symbols":
        _el_symbols_invalidate()


class SettingsError(ValueError):
    pass


# Har obyektga xos maydonlar umumiy standartga yozilmaydi: yangi kromkaning belgisi (A, B, C …) va rangi har doim avto
AUTO_FIELDS: dict[str, tuple[str, ...]] = {"el_defaults": ("symbol", "color"),
                                           "gr_defaults": ("usage", "cut_length", "passes"),      # GR: hisoblangan qiymatlar standartga yozilmaydi
                                           "sp_defaults": ("area_m2", "material_m2"),             # SP: hisoblangan qiymatlar standartga yozilmaydi
                                           "cl_defaults": ("usage_m", "multiplicity"),            # CL: hisoblangan qiymatlar standartga yozilmaydi
                                           "cn_defaults": ("usage_m2", "multiplicity"),           # CN: hisoblangan qiymatlar standartga yozilmaydi
                                           # LB: loyihaga xos tanlov/ma'lumot/shablon nusxasi standartga yozilmaydi (shablonni — kutubxonaga)
                                           "lb_defaults": ("part_selected", "part_selected_only", "cs_op_id", "fields", "data", "template", "legacy_program")}


def validate_data(scope: str, data: Any) -> dict:
    if scope not in MODELS:
        raise SettingsError(_("set_unknown_scope", s=scope))
    model = MODELS[scope]
    if model is None:
        if not isinstance(data, dict):
            raise SettingsError(_("set_json_object"))
        return data
    try:
        out = model.model_validate(data or {}).model_dump(mode="json")
    except ValidationError as e:
        raise SettingsError(_("set_invalid", e=format_errors(e.errors()))) from e
    for f in AUTO_FIELDS.get(scope, ()):
        out.pop(f, None)
    return out


def builtin(scope: str) -> dict:
    model = MODELS.get(scope)
    if scope in ("postprocessor", "excel_import", "pp_machines"):
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


def find_by_name(scope: str, name: str) -> dict | None:
    """Shu `scope` da shu nomli (bo'sh joylarsiz, katta-kichik harfga sezgirsiz) birinchi profil."""
    key = (name or "").strip().casefold()
    for r in list_profiles(scope):
        if (r["name"] or "").strip().casefold() == key:
            return r
    return None


def create(scope: str, name: str, data: Any, is_default: bool = False) -> dict:
    clean = validate_data(scope, data)
    with SessionLocal() as s:
        if is_default:
            s.query(SettingsProfileRow).filter(SettingsProfileRow.scope == scope).update({"is_default": False})
        r = SettingsProfileRow(scope=scope, name=name, data=clean, is_default=is_default)
        s.add(r); s.commit()
        _changed(scope)
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
        _changed(scope)
        return _row(r)


def delete(scope: str, pid: int) -> None:
    with SessionLocal() as s:
        r = s.get(SettingsProfileRow, pid)
        if not r or r.scope != scope:
            raise KeyError(pid)
        s.delete(r); s.commit()
    _changed(scope)


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
            out = validate_data(scope, merged)
        except SettingsError:
            return base
        for f in AUTO_FIELDS.get(scope, ()):         # eski saqlangan belgi/rang ham e'tiborga olinmaydi
            out[f] = base[f]
        return out
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
        _changed(scope)
        return _row(r)


def resolve(scope: str, profile_id: int | None) -> dict:
    """Berilgan profil (bo'lmasa standart) ma'lumotlari."""
    if profile_id:
        pr = get_profile(scope, profile_id)
        if pr:
            base = builtin(scope)
            if not isinstance(base, dict):
                return pr["data"]
            out = {**base, **pr["data"]}
            for f in AUTO_FIELDS.get(scope, ()):
                out[f] = base[f]
            return out
    return get_default(scope)


def seed() -> None:
    """Birinchi ishga tushishda: namunaviy postprotsessor profili."""
    from .postprocessors import EXAMPLE_TEMPLATE
    if not list_profiles("postprocessor"):
        create("postprocessor", "Пример — станок предприятия", PostprocessorProfile(
            name="Пример — станок предприятия", extension="txt", per_map=True, newline="crlf",
            template=EXAMPLE_TEMPLATE,
            description="Настройте шаблон под формат вашего станка (Настройки → Постпроцессоры) / "
                        "Shablonni stanok formatiga moslang").model_dump())
