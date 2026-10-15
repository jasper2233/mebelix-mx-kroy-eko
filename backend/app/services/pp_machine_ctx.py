"""Postprotsessor stanoklari: sozlamalarni saqlash, sxema javobi, etiketka maydonlarini hisoblash va shablon konteksti (W7).

Saqlash — `pp_machines` sozlamasi (mavjud `enabled` / `profile` / `prefix` yoniga, ularni buzmasdan):
  params:       {stanok_kaliti: {param: qiymat}}   — faqat standartdan farqlari (siyrak); qolgani sxema standarti
  label_fields: {stanok_kaliti: [{name, expr}]}    — standart jadvaldan farq qilsa; yo'q bo'lsa — standart jadval

Etiketka maydon ifodalari **faqat** `services/expr.py` da hisoblanadi (CLAUDE.md 14-qoida); o'zgaruvchilar — W4 `label_vars`
(nuqtali nomlar va GibLab taxalluslari: `usedCount`, `ets`, `etn`, `XNC1`, `grtn`, `mill` …). Ifoda xatosi jim 0 emas:
qiymat `#ERR` + kontekstdagi `label_warnings`.

Shablon konteksti (`postprocessors.context` / `context_xnc` ga qo'shiladi; stanok tanlanmagan bo'lsa `machine = None`):
  machine        — {key, name, group, params: {param: qiymat}, label_fields: [{name, expr}]}
  maps[].placements[].label / label_text, parts[].label / label_text — {maydon nomi: qiymat} (tipli) va {nom: matn}
  label_warnings — [{field, expr, message, error, count, part_uid}]
Stanok **formati** bu yerda yo'q — faqat toza ma'lumot; format shablonini korxona dasturchilari yozadi.
"""
from __future__ import annotations

import math
from typing import Any, Optional

from ..i18n import _
from ..models import LBParams, Operation, OpType, Part, Project
from . import expr
from . import pp_machine_schema as S
from . import settings
from .calc import effective_qty
from .expr_docs import type_name
from .label_vars import ALIASES, VARS, EnvBuilder, Item, sample_project

LABEL_LANG = "ru"            # fayl mazmuni interfeys tiliga bog'liq bo'lmasin (sana nomlari va h.k.)
ERR_VALUE = "#ERR"

# Ifoda yordamchisi (UI) uchun eng ko'p ishlatiladigan o'zgaruvchilar (GibLab nomlari — taxalluslar; qiymat — tanlangan detaldan)
HELPER_VARS = ("project.name", "project.number", "material.name", "material.code", "product.name", "name", "description",
               "part.id", "indexInOperation", "length", "width", "detail.length", "detail.width", "thick", "usedCount",
               "count", "totalCount", "txt", "waste", "ets", "ebs", "els", "ers", "ett", "ebt", "elt", "ert", "etn", "ebn",
               "eln", "ern", "grtn", "grbn", "grln", "grrn", "XNC1", "XNC2", "mill", "drill", "groove")
_TITLES = {n: (ru, uz) for n, _tp, _g, ru, uz in VARS}
_TITLES["waste"] = ("Признак остатка (у детали — false)", "Qoldiq belgisi (detal uchun — false)")


# ───────────────────────── Saqlash (pp_machines ichida) ─────────────────────────
def _raw() -> dict:
    d = settings.get_default("pp_machines")
    return d if isinstance(d, dict) else {}


def _save(d: dict) -> None:
    settings.set_default("pp_machines", d)


def saved_params(key: str) -> dict[str, Any]:
    v = (_raw().get("params") or {}).get(key)
    return dict(v) if isinstance(v, dict) else {}


def get_params(key: str) -> dict[str, Any]:
    """Stanok parametrlari: sxema standartlari ustiga saqlanganlari (tipli)."""
    return S.resolve_params(key, saved_params(key))


def set_params(key: str, clean: dict[str, Any]) -> None:
    """Tekshirilgan qiymatlar to'plamini saqlaydi (to'liq almashtirish; standartga teng qiymatlar saqlanmaydi)."""
    dflt = S.defaults(key)
    sparse = {k: v for k, v in clean.items() if k in dflt and (type(v) is not type(dflt[k]) or v != dflt[k])}
    d = dict(_raw())
    allp = dict(d.get("params") or {})
    if sparse:
        allp[key] = sparse
    else:
        allp.pop(key, None)
    d["params"] = allp
    _save(d)


def get_tools(key: str) -> dict[str, str]:
    """«Инструменты» jadvali: asbob kaliti (`ppfmt.tooling.tool_key`) → stanokdagi raqam / nom (faqat to'ldirilganlari)."""
    t = (_raw().get("tools") or {}).get(key)
    return {str(k): str(v) for k, v in t.items() if str(v).strip()} if isinstance(t, dict) else {}


def set_tools(key: str, tools: dict[str, str]) -> None:
    clean = {str(k)[:60]: str(v).strip()[:40] for k, v in (tools or {}).items() if str(v).strip()}
    if len(clean) > 200:
        raise ValueError("tools: too many rows")
    d = dict(_raw())
    allt = dict(d.get("tools") or {})
    if clean:
        allt[key] = clean
    else:
        allt.pop(key, None)
    d["tools"] = allt
    _save(d)


def get_label_fields(key: str) -> list[dict]:
    lf = (_raw().get("label_fields") or {}).get(key)
    if S.schema_of(key).label_table is not None and isinstance(lf, list):
        return [dict(name=str(r.get("name", "")), expr=str(r.get("expr", ""))) for r in lf if isinstance(r, dict)]
    return S.default_label_rows(key)


def set_label_fields(key: str, rows: list[dict]) -> None:
    d = dict(_raw())
    allf = dict(d.get("label_fields") or {})
    if rows == S.default_label_rows(key):
        allf.pop(key, None)                     # standartga teng — saqlanmaydi («standartga qaytarish»)
    else:
        allf[key] = rows
    d["label_fields"] = allf
    _save(d)


def machine_ref(key: str) -> tuple[str, str]:
    """(nom, guruh) — ro'yxatda yo'q kalit uchun KeyError."""
    from .postprocessors import MACHINE_BY_KEY
    return MACHINE_BY_KEY[key]


def machine_context(key: str) -> dict:
    """Shablon konteksti uchun `machine`."""
    name, group = machine_ref(key)
    return dict(key=key, name=name, group=group, params=get_params(key), label_fields=get_label_fields(key))


# ───────────────────────── Sxema javobi (UI uchun) ─────────────────────────
def _param_json(p: S.Param, value: Any) -> dict:
    d: dict[str, Any] = dict(key=p.key, type=p.type, ru=p.ru, uz=p.uz, default=p.default, value=value,
                             modified=(type(value) is not type(p.default) or value != p.default))
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
    return d


def schema_payload(key: str) -> dict:
    """`GET /postprocessors/machines/{key}/schema`: sxema + joriy qiymatlar + standartlar."""
    name, group = machine_ref(key)
    sch = S.schema_of(key)
    values = S.resolve_params(key, saved_params(key))
    groups: dict[str, dict] = {}
    for p in sch.params:
        g = groups.get(p.group)
        if g is None:
            ru, uz = S.GROUPS[p.group]
            g = groups[p.group] = dict(key=p.group, ru=ru, uz=uz, params=[])
        g["params"].append(_param_json(p, values[p.key]))
    modified = [p.key for p in sch.params if type(values[p.key]) is not type(p.default) or values[p.key] != p.default]
    table = None
    if sch.label_table is not None:
        rows = get_label_fields(key)
        dflt = S.default_label_rows(key)
        table = dict(title=dict(ru=sch.label_table.title_ru, uz=sch.label_table.title_uz), kind=sch.label_table.kind,
                     max_rows=S.MAX_LABEL_ROWS, rows=rows, defaults=dflt, is_default=rows == dflt)
    return dict(key=key, name=name, group=group,
                info=dict(ru=sch.info_ru, uz=sch.info_uz) if (sch.info_ru or sch.info_uz) else None,
                groups=list(groups.values()), values=values, defaults=S.defaults(key), modified=modified, label_table=table)


# ───────────────────────── Etiketka maydonlarini hisoblash ─────────────────────────
def _clean_value(v: Any) -> Any:
    """JSON / shablon uchun xavfsiz qiymat (cheksiz son — matn)."""
    if isinstance(v, float) and not math.isfinite(v):
        return expr.to_text(v)
    return v


def eval_field(src: str, env: dict, lang: str = LABEL_LANG) -> dict:
    """Bitta ifoda: {ok, type, value, text, error, stage}. Bo'sh ifoda — to'g'ri, qiymat «». Xatoda `value`/`text` = «#ERR»."""
    s = (src or "").strip()
    if not s:
        return dict(ok=True, type="string", value="", text="", error=None, stage=None)
    err_stage: Optional[tuple[str, str]] = None
    try:
        expr.compile_check(s)
    except ValueError as e:
        err_stage = (str(e), "syntax")
    except Exception:  # noqa: BLE001
        err_stage = (_("xnc.e_syntax"), "syntax")
    if err_stage is None:
        try:
            v = expr.evaluate(s, env, lang=lang)
        except ValueError as e:
            err_stage = (str(e), "eval")
        except Exception:  # noqa: BLE001 — dvigatel kutilmagan xato bersa ham jim 0 emas
            err_stage = (_("xnc.e_forbidden"), "eval")
        else:
            return dict(ok=True, type=type_name(v), value=_clean_value(v), text=expr.to_text(v), error=None, stage=None)
    return dict(ok=False, type=None, value=ERR_VALUE, text=ERR_VALUE, error=err_stage[0], stage=err_stage[1])


class LabelCalc:
    """Bitta CS operatsiyasi uchun etiketka maydonlari hisobchisi (`label_vars` muhiti; xatolar yig'iladi)."""

    def __init__(self, project: Project, op: Operation, fields: list[dict], lang: str = LABEL_LANG):
        self.project, self.op, self.fields, self.lang = project, op, fields, lang
        self.eb = EnvBuilder(project, LBParams(), total=0, lang=lang)
        self.index = {p.id: i for i, p in enumerate(op.parts, 1)}
        self._warn: dict[tuple[str, str], dict] = {}

    def env(self, part: Part, m) -> dict:
        it = Item("part", op=self.op, part=part, part_index=self.index.get(part.id, 0), copy=1,
                  copies=effective_qty(self.project, part), map=m)
        return self.eb.env(it)

    def values(self, part: Part, m=None) -> list[dict]:
        env = self.env(part, m)
        out = []
        for f in self.fields:
            r = eval_field(f.get("expr", ""), env, self.lang)
            if not r["ok"]:
                w = self._warn.setdefault((f["name"], r["error"]), dict(
                    field=f["name"], expr=f.get("expr", ""), error=r["error"],
                    message=_("pp_label_value_err", f=f["name"], e=r["error"]), count=0, part_uid=part.uid, _uids=set()))
                if part.uid not in w["_uids"]:
                    w["_uids"].add(part.uid)
                    w["count"] += 1
            out.append(dict(name=f["name"], expr=f.get("expr", ""), **r))
        return out

    def warnings(self) -> list[dict]:
        return [{k: v for k, v in w.items() if not k.startswith("_")} for w in self._warn.values()]


def _fill(target: dict, vals: list[dict]) -> None:
    target["label"] = {r["name"]: r["value"] for r in vals}
    target["label_text"] = {r["name"]: r["text"] for r in vals}


def attach_machine(ctx: dict, project: Project, op: Operation, key: Optional[str]) -> dict:
    """Shablon kontekstiga `machine`, `label_warnings` va (CS uchun) har detalga hisoblangan `label` qo'shadi. Joyida o'zgartiradi."""
    ctx["label_warnings"] = []
    for p in ctx.get("parts", []):
        p.setdefault("label", {}); p.setdefault("label_text", {})
    for m in ctx.get("maps", []):
        for pl in m["placements"]:
            pl.setdefault("label", {}); pl.setdefault("label_text", {})
    if not key:
        ctx["machine"] = None
        return ctx
    mc = machine_context(key)
    ctx["machine"] = mc
    if op.type != OpType.CS or not mc["label_fields"] or S.schema_of(key).label_table is None:
        return ctx
    calc = LabelCalc(project, op, mc["label_fields"])
    by_id = {p.id: p for p in op.parts}
    cache: dict[tuple[str, int], list[dict]] = {}
    for mi, m in enumerate(op.result.maps if op.result else []):
        for pi, pl in enumerate(m.placements):
            part = by_id.get(pl.part_id)
            if part is None:
                continue
            ck = (part.id, m.index)
            if ck not in cache:
                cache[ck] = calc.values(part, m)
            _fill(ctx["maps"][mi]["placements"][pi], cache[ck])
    for i, part in enumerate(op.parts):
        _fill(ctx["parts"][i], calc.values(part, None))
    ctx["label_warnings"] = calc.warnings()
    return ctx


def attach_machine_xnc(ctx: dict, key: Optional[str]) -> dict:
    """Ishlov markazi (XNC) konteksti: faqat `machine` (etiketka maydonlari jadvali yo'q)."""
    ctx["machine"] = machine_context(key) if key else None
    ctx["label_warnings"] = []
    return ctx


# ───────────────────────── Jonli ko'rinish (Настройки → Постпроцессоры) ─────────────────────────
def preview_fields(key: str, fields: list[dict], project: Project, op: Operation, part: Part) -> dict:
    """Berilgan detal kontekstida har maydon ifodasini hisoblaydi. Qaytaradi: {part, map_index, fields: [...]}."""
    calc = LabelCalc(project, op, fields)
    m = None
    for cm in (op.result.maps if op.result else []):
        if any(pl.part_id == part.id for pl in cm.placements):
            m = cm
            break
    vals = calc.values(part, m)
    seen: set[str] = set()
    rows = []
    for i, r in enumerate(vals):
        name = str(r["name"]).strip()
        e = S.check_name(name, seen)
        seen.add(name)
        rows.append(dict(index=i, name=r["name"], expr=r["expr"], ok=r["ok"], type=r["type"], value=r["value"],
                         text=r["text"], error=r["error"], stage=r["stage"], name_error=e))
    env = calc.env(part, m)
    variables = []
    for n in HELPER_VARS:
        ru, uz = _TITLES.get(ALIASES.get(n, n), ("", ""))
        variables.append(dict(name=n, ru=ru, uz=uz, value=_clean_value(env.get(n))))
    return dict(part=dict(uid=part.uid, name=part.name, code=part.code, index=calc.index.get(part.id, 0)),
                map_index=m.index if m is not None else None, fields=rows, variables=variables)


def sample_target() -> tuple[Project, Operation, Part]:
    """Loyiha tanlanmaganda: namuna loyiha (saqlanmaydi) — shablon jonli ko'rinishi uchun."""
    project, cs = sample_project(LABEL_LANG)
    return project, cs, cs.parts[0]
