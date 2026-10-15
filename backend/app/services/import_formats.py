"""«Импорт из других программ» infratuzilmasi (W18 / WP-C: IMP-001, 004, 005, 006).

Bu modul — **formatlar katalogi** va **importer parametrlari** (ParamGrid sxemasi: guruhlar, tur, standart, «Справка»),
import **profillari** (nomlangan sozlamalar to'plami, `settings` doirasi `import_profile`) va profillarni JSON / XML ga eksport,
fayldan import. Importerning o'zi (fayl → loyiha) bu yerda emas — u `plugins/<nom>.py` da `@register(..., key=<format kaliti>)`
bilan ro'yxatga olinadi (`plugins/__init__.py`).

Qoidalar:
  * Format katalogda bor-u, importeri (plagin) yo'q bo'lsa — holati `no_module` («Нет модуля импорта — предоставьте образец
    файла»): dialogda xira, parametrsiz, import 400. **Importerlar o'ylab topilmaydi** — ular faqat foydalanuvchi bergan
    namuna fayl bo'yicha yoziladi (CLAUDE.md 4–5, S_ISH_QOIDALARI.md).
  * Plagin parametrlarni `option("kalit", standart)` bilan oladi (ContextVar — plagin imzosi `(bytes, str)` o'zgarmagan).
  * Profil — siyrak: faqat standartdan farq qiladigan parametrlar saqlanadi (IMP-004: «belgi qo'yilgan parametr standartni
    bekor qiladi»). Fayl eksportida esa hamma qiymat aniq yoziladi (boshqa korxonada ham aynan shu sozlama chiqsin).
Batafsil: `docs/mebelix/T_W18_IMPORT_INFRA.md`.
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Iterator

from pydantic import BaseModel, Field, model_validator

from ..i18n import _
from .pp_machine_schema import Opt, Param, coerce

try:  # xavfsiz XML o'qish (XXE / «billion laughs»)
    from defusedxml import ElementTree as _SafeET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as _SafeET  # noqa: N817
import xml.etree.ElementTree as ET

APP = "MebeliX Kroy"
FILE_KIND = "import_profiles"
FILE_VERSION = 1
MAX_PROFILE_FILE = 1_000_000          # bayt — profillar fayli
MAX_PROFILES_IN_FILE = 200
MAX_PROFILE_NAME = 100
STATUS_READY = "ready"
STATUS_NO_MODULE = "no_module"


# ───────────────────────── Sxema ─────────────────────────
@dataclass(frozen=True)
class IParam(Param):
    """Importer parametri: `Param` (kalit, guruh, tur, standart, ru/uz, diapazon, variantlar) + «Справка» matni."""
    help_ru: str = ""
    help_uz: str = ""


@dataclass(frozen=True)
class ImportFormat:
    key: str                                  # barqaror kalit: plagin `register(..., key=)` va profil `format` maydoni
    name_ru: str                              # ro'yxatdagi nom (dastur nomlari ikkala tilda bir xil)
    name_uz: str
    exts: tuple[str, ...]                     # fayl kengaytmalari (kichik harf, nuqta bilan)
    icon: str                                 # ikonka kaliti (frontend `importIcons`) — o'zimizning umumiy belgilarimiz
    groups: tuple[tuple[str, str, str], ...] = ()      # (guruh kaliti, ru, uz) — chiqish tartibi
    params: tuple[IParam, ...] = ()
    help_ru: str = ""
    help_uz: str = ""


_NO_SAMPLE_RU = ("Модуль импорта этого формата ещё не написан: для него нужен образец файла (без данных клиентов) и описание того, "
                 "что из него должно получиться в проекте. Параметры появятся вместе с модулем.")
_NO_SAMPLE_UZ = ("Bu format uchun import moduli hali yozilmagan: unga namuna fayl (mijoz ma'lumotlarisiz) va fayldan loyihada nima "
                 "chiqishi kerakligi tavsifi kerak. Parametrlar modul bilan birga paydo bo'ladi.")


def _flag(key: str, ru: str, uz: str, help_ru: str, help_uz: str, group: str = "ops", default: bool = True) -> IParam:
    return IParam(key, group, "bool", default, ru, uz, help_ru=help_ru, help_uz=help_uz)


CATALOG: dict[str, ImportFormat] = {}


def declare(fmt: ImportFormat) -> ImportFormat:
    """Katalogga format qo'shish (yangi plagin o'z formatini shu bilan e'lon qila oladi)."""
    CATALOG[fmt.key] = fmt
    return fmt


declare(ImportFormat(
    "project", "Файл проекта (XML)", "Loyiha fayli (XML)", (".project",), "file-code",
    groups=(("ops", "Операции", "Operatsiyalar"), ("cl", "Погонаж (CL)", "Pogonaj (CL)")),
    params=(
        _flag("import_xnc", "Обработки XNC (сверление, фрезеровка, пазы)", "XNC ishlovlari (teshik, freza, paz)",
              "Программы обработки, привязанные к деталям. Выключено — операции XNC пропускаются (с предупреждением), "
              "детали импортируются без обработок.",
              "Detallarga bog'langan ishlov dasturlari. O'chirilsa — XNC operatsiyalari o'tkazib yuboriladi (ogohlantirish bilan), "
              "detallar ishlovsiz import qilinadi."),
        _flag("import_o", "Комплектация (O)", "Komplektatsiya (O)",
              "Операции «Комплектация»: фурнитура, упаковка, работы. Выключено — пропускаются.",
              "«Komplektatsiya» operatsiyalari: furnitura, qadoq, ishlar. O'chirilsa — o'tkazib yuboriladi."),
        _flag("import_sp", "Обработка поверхности (SP)", "Sirt ishlovi (SP)",
              "Операции обработки поверхности и привязка деталей к ним.",
              "Sirt ishlovi operatsiyalari va detallarni ularga bog'lash."),
        _flag("import_cl", "Погонажный раскрой (CL)", "Pogonaj kroy (CL)",
              "Операции раскроя погонажа: полосы и детали. Выключено — пропускаются.",
              "Pogonaj kroy operatsiyalari: polosalar va detallar. O'chirilsa — o'tkazib yuboriladi."),
        _flag("import_lb", "Этикетки (LB)", "Etiketkalar (LB)",
              "Операции этикеток с их параметрами (шаблон из старого формата только сохраняется).",
              "Etiketka operatsiyalari va ularning parametrlari (eski format shabloni faqat saqlanadi)."),
        IParam("cl_negative_length", "cl", "choice", "uncomputed",
               "Отрицательная длина детали погонажа", "Pogonaj detalining manfiy uzunligi",
               options=(Opt("uncomputed", "Не рассчитана: длина 0 + предупреждение", "Hisoblanmagan: uzunlik 0 + ogohlantirish"),
                        Opt("abs", "Модуль числа |l|", "Son moduli |l|")),
               help_ru="Отрицательная длина — признак детали, которую не рассчитала исходная программа. Стандарт: длина 0 (деталь не "
                       "попадает в раскрой, об этом сообщается). «Модуль» берёт |l| — это допущение, включайте осознанно.",
               help_uz="Manfiy uzunlik — manba dastur hisoblab bo'lmagan detal belgisi. Standart: uzunlik 0 (detal kroyga kirmaydi, "
                       "bu haqda xabar beriladi). «Son moduli» |l| ni oladi — bu taxmin, ongli yoqing."),
    ),
    help_ru="Файл проекта в формате XML (.project): его создают скрипты экспорта Базис-Мебельщик и 3D-Конструктор. Читаются изделия, детали, "
            "кромка, материалы, параметры раскроя и операции XNC / GR / SP / CL / O / LB. Двоичный результат раскроя из файла не читается — "
            "проект раскраивается заново. Профиль хранит только отличия от стандарта.",
    help_uz="XML ko'rinishidagi loyiha fayli (.project): uni Bazis-Mebelshik va 3D-Konstruktor eksport skriptlari yaratadi. Mahsulotlar, "
            "detallar, kromka, materiallar, kroy parametrlari va XNC / GR / SP / CL / O / LB operatsiyalari o'qiladi. Fayldagi ikkilik "
            "kroy natijasi o'qilmaydi — loyiha qayta kroy qilinadi. Profil faqat standartdan farqlarni saqlaydi."))

# Onlayn dialogdagi 7 format (kengaytmalar — ro'yxatdan): importeri yo'q, namuna fayl kerak.
for _k, _ru, _uz, _ex, _ic in (
        ("pro100", "PRO100", "PRO100", (".sto",), "box"),
        ("imos", "Imos (fxm)", "Imos (fxm)", (".fxm",), "boxes"),
        ("bazis", "Базис-Мебельщик (xml, obl)", "Bazis-Mebelshik (xml, obl)", (".xml", ".obl"), "ruler"),
        ("bcad", "BCAD (xml)", "BCAD (xml)", (".xml",), "drafting-compass"),
        ("woody2", "Woody2 (xml, wes)", "Woody2 (xml, wes)", (".xml", ".wes"), "tree-pine"),
        ("woodwop", "WoodWop (mpr)", "WoodWop (mpr)", (".mpr",), "drill"),
        ("ilenia", "iLENIA (pd4)", "iLENIA (pd4)", (".pd4",), "layers")):
    declare(ImportFormat(_k, _ru, _uz, _ex, _ic, help_ru=_NO_SAMPLE_RU, help_uz=_NO_SAMPLE_UZ))


# ───────────────────────── Holat (plagin reestridan) ─────────────────────────
def get(key: str) -> ImportFormat | None:
    return CATALOG.get(key)


def _registered() -> dict[str, tuple[str, Any, tuple[str, ...]]]:
    from .. import plugins
    return plugins.BY_KEY


def status(key: str) -> str:
    return STATUS_READY if key in _registered() else STATUS_NO_MODULE


def all_formats() -> list[ImportFormat]:
    """Katalog + katalogda yo'q, lekin plagin ro'yxatdan o'tgan formatlar (umumiy yozuv sifatida: parametrsiz)."""
    out = list(CATALOG.values())
    for key, (title, _fn, exts) in _registered().items():
        if key not in CATALOG:
            out.append(ImportFormat(key, title, title, exts, "file-code"))
    return out


def format_of(key: str) -> ImportFormat | None:
    f = CATALOG.get(key)
    if f is not None:
        return f
    reg = _registered().get(key)
    return ImportFormat(key, reg[0], reg[0], reg[2], "file-code") if reg else None


def catalog_payload() -> list[dict]:
    out = []
    for f in all_formats():
        st = status(f.key)
        out.append(dict(key=f.key, name=dict(ru=f.name_ru, uz=f.name_uz), exts=list(f.exts), icon=f.icon, status=st,
                        reason=_("imp_no_module") if st == STATUS_NO_MODULE else "", n_params=len(f.params)))
    return out


# ───────────────────────── Parametrlar ─────────────────────────
def defaults(key: str) -> dict[str, Any]:
    f = format_of(key)
    return {p.key: p.default for p in f.params} if f else {}


def validate_params(key: str, raw: Any) -> tuple[dict[str, Any], list[dict]]:
    """`{param: qiymat}` → (tozalangan qiymatlar, xatolar [{key, message}]). Noma'lum kalit — xato; qiymatlar qat'iy turda."""
    f = format_of(key)
    out: dict[str, Any] = {}
    errors: list[dict] = []
    if f is None:
        return out, [dict(key="", message=_("imp_fmt_unknown", k=str(key)[:40]))]
    if raw is None:
        return out, errors
    if not isinstance(raw, dict):
        return out, [dict(key="", message=_("val_dict"))]
    by_key = {p.key: p for p in f.params}
    for k, v in raw.items():
        p = by_key.get(k)
        if p is None:
            errors.append(dict(key=str(k)[:80], message=_("pp_param_unknown", k=str(k)[:80])))
            continue
        try:
            out[k] = coerce(p, v)
        except ValueError as e:
            errors.append(dict(key=k, message=str(e)))
    return out, errors


def _is_default(p: IParam, v: Any) -> bool:
    return type(v) is type(p.default) and v == p.default


def sparse(key: str, values: dict[str, Any]) -> dict[str, Any]:
    """Faqat standartdan farq qiladigan qiymatlar (profilda saqlanadi)."""
    f = format_of(key)
    by_key = {p.key: p for p in f.params} if f else {}
    return {k: v for k, v in values.items() if k in by_key and not _is_default(by_key[k], v)}


def resolve_values(key: str, saved: dict[str, Any] | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Standart ← saqlangan profil (yaroqsiz/eski kalit jim e'tiborsiz) ← so'rov qiymatlari (qat'iy: xato — ValueError)."""
    f = format_of(key)
    out = defaults(key)
    if f is None:
        return out
    by_key = {p.key: p for p in f.params}
    for k, v in (saved or {}).items():
        p = by_key.get(k)
        if p is not None:
            try:
                out[k] = coerce(p, v)
            except ValueError:
                pass
    if overrides:
        clean, errors = validate_params(key, overrides)
        if errors:
            raise ValueError("; ".join(f"{e['key']}: {e['message']}" if e["key"] else e["message"] for e in errors[:3]))
        out.update(clean)
    return out


def _param_json(p: IParam, value: Any) -> dict:
    d: dict[str, Any] = dict(key=p.key, type=p.type, ru=p.ru, uz=p.uz, default=p.default, value=value,
                             modified=not _is_default(p, value))
    if p.min is not None:
        d["min"] = p.min
    if p.max is not None:
        d["max"] = p.max
    if p.type == "choice":
        d["options"] = [dict(value=o.value, ru=o.ru, uz=o.uz) for o in p.options]
        d["custom"] = p.custom
    if p.enabled_if:
        d["enabled_if"] = p.enabled_if
    if p.note_ru or p.note_uz:
        d["note"] = dict(ru=p.note_ru, uz=p.note_uz)
    if p.help_ru or p.help_uz:
        d["help"] = dict(ru=p.help_ru, uz=p.help_uz)
    return d


def schema_payload(key: str, saved: dict[str, Any] | None = None) -> dict | None:
    """`GET /import/formats/{key}/schema`: ParamGrid sxemasi (W7 bilan bir xil shakl) + holat + «Справка»."""
    f = format_of(key)
    if f is None:
        return None
    values = resolve_values(key, saved)
    labels = {g[0]: (g[1], g[2]) for g in f.groups}
    groups: dict[str, dict] = {}
    for gk, (ru, uz) in labels.items():
        groups[gk] = dict(key=gk, ru=ru, uz=uz, params=[])
    for p in f.params:
        g = groups.setdefault(p.group, dict(key=p.group, ru=p.group, uz=p.group, params=[]))
        g["params"].append(_param_json(p, values[p.key]))
    st = status(key)
    return dict(key=f.key, name=dict(ru=f.name_ru, uz=f.name_uz), exts=list(f.exts), icon=f.icon, status=st,
                reason=_("imp_no_module") if st == STATUS_NO_MODULE else "",
                groups=[g for g in groups.values() if g["params"]], values=values, defaults=defaults(key),
                modified=[p.key for p in f.params if not _is_default(p, values[p.key])],
                help=dict(ru=f.help_ru, uz=f.help_uz))


# ───────────────────────── Importerga parametr uzatish ─────────────────────────
_OPTS: ContextVar[dict[str, Any] | None] = ContextVar("mebelix_import_options", default=None)


@contextmanager
def use_options(values: dict[str, Any]) -> Iterator[None]:
    """Importer ishlayotgan vaqtda parametrlar (`option()` orqali o'qiladi). Dialogdan tashqari chaqiruvlarda — bo'sh."""
    tok = _OPTS.set(dict(values))
    try:
        yield
    finally:
        _OPTS.reset(tok)


def option(key: str, default: Any = None) -> Any:
    """Plagin uchun: joriy import parametri; dialogdan tashqarida (yoki parametr berilmagan bo'lsa) — `default`."""
    cur = _OPTS.get()
    return default if cur is None or key not in cur else cur[key]


# ───────────────────────── Profil modeli (settings doirasi `import_profile`) ─────────────────────────
class ImportProfile(BaseModel):
    """Nomlangan import sozlamasi: format + standartdan farqli parametrlar (siyrak). Nomi — `settings_profiles.name`."""
    format: str = Field("project", max_length=40)
    params: dict[str, Any] = {}

    @model_validator(mode="after")
    def _check(self) -> "ImportProfile":
        if format_of(self.format) is None:
            raise ValueError(_("imp_fmt_unknown", k=self.format[:40]))
        clean, errors = validate_params(self.format, self.params)
        if errors:
            raise ValueError("; ".join(f"{e['key']}: {e['message']}" if e["key"] else e["message"] for e in errors[:3]))
        self.params = sparse(self.format, clean)
        return self


# ───────────────────────── Profillar fayli: JSON / XML ─────────────────────────
class ProfileFileError(ValueError):
    pass


def _full(key: str, saved: dict[str, Any]) -> dict[str, Any]:
    return resolve_values(key, saved)


def export_json(profiles: list[dict]) -> dict:
    """`profiles`: [{name, data: {format, params}}] (settings qatorlari) → fayl hujjati (hamma qiymat aniq)."""
    out = []
    for pr in profiles:
        d = pr.get("data") or {}
        key = d.get("format", "project")
        out.append(dict(name=pr.get("name", ""), format=key, params=_full(key, d.get("params") or {})))
    return dict(app=APP, kind=FILE_KIND, version=FILE_VERSION, profiles=out)


def _xml_text(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def export_xml(profiles: list[dict]) -> bytes:
    doc = export_json(profiles)
    root = ET.Element("importProfiles", app=doc["app"], kind=doc["kind"], version=str(doc["version"]))
    for pr in doc["profiles"]:
        pe = ET.SubElement(root, "profile", name=pr["name"], format=pr["format"])
        f = format_of(pr["format"])
        types = {p.key: p.type for p in f.params} if f else {}
        for k, v in pr["params"].items():
            ET.SubElement(pe, "param", key=k, type=types.get(k, "string"), value=_xml_text(v))
    ET.indent(root)
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")


def _from_text(ptype: str, s: str) -> Any:
    """XML qiymati (matn) → tur (keyin `coerce` qat'iy tekshiradi)."""
    s = s.strip() if ptype != "string" else s
    if ptype == "bool":
        if s.lower() in ("true", "1"):
            return True
        if s.lower() in ("false", "0"):
            return False
        raise ValueError(_("val_bool"))
    if ptype == "int":
        try:
            return int(s)
        except ValueError as e:
            raise ValueError(_("val_int")) from e
    if ptype in ("mm", "float"):
        try:
            x = float(s.replace(",", "."))
        except ValueError as e:
            raise ValueError(_("val_number")) from e
        if not math.isfinite(x):
            raise ValueError(_("val_finite"))
        return x
    return s


def parse_file(data: bytes) -> list[dict]:
    """Profillar fayli (JSON yoki XML — mazmundan aniqlanadi) → [{name, format, params}]; tuzilma buzuq — ProfileFileError.
    Har bir profilning ichki xatosi bu yerda tekshirilmaydi (saqlashda `ImportProfile` tekshiradi, hisobotda `invalid`)."""
    if len(data) > MAX_PROFILE_FILE:
        raise ProfileFileError(_("imp_profiles_big", n=MAX_PROFILE_FILE // 1000))
    head = data.lstrip(b"\xef\xbb\xbf \t\r\n")[:1]
    out: list[dict] = []
    if head == b"<":
        try:
            root = _SafeET.fromstring(data)
        except Exception as e:  # noqa: BLE001
            raise ProfileFileError(_("import_not_xml", e=str(e)[:100])) from e
        if root.tag != "importProfiles":
            raise ProfileFileError(_("imp_profiles_bad"))
        for pe in root.findall("profile"):
            key = (pe.get("format") or "").strip()
            f = format_of(key)
            types = {p.key: p.type for p in f.params} if f else {}
            params: dict[str, Any] = {}
            bad = ""
            for qe in pe.findall("param"):
                k = (qe.get("key") or "").strip()
                try:
                    params[k] = _from_text(types.get(k, "string"), qe.get("value") or "")
                except ValueError as e:
                    bad = f"{k}: {e}"
            out.append(dict(name=(pe.get("name") or "").strip(), format=key, params=params, error=bad))
    else:
        import json
        try:
            doc = json.loads(data.decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError) as e:
            raise ProfileFileError(_("imp_profiles_bad")) from e
        items = doc.get("profiles") if isinstance(doc, dict) else None
        if not isinstance(items, list):
            raise ProfileFileError(_("imp_profiles_bad"))
        for it in items:
            if not isinstance(it, dict):
                out.append(dict(name="", format="", params={}, error=_("val_dict")))
                continue
            out.append(dict(name=str(it.get("name") or "").strip(), format=str(it.get("format") or "").strip(),
                            params=it.get("params") if it.get("params") is not None else {}, error=""))
    if len(out) > MAX_PROFILES_IN_FILE:
        raise ProfileFileError(_("imp_profiles_many", n=MAX_PROFILES_IN_FILE))
    return out
