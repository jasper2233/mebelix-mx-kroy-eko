"""Postprotsessor stanoklari: sozlamalar sxemasi (ParamGrid) va «etiketka maydonlari» (nom → ifoda) API si (W7).

  GET  /api/postprocessors/machines/{key}/schema               sxema + joriy qiymatlar + standartlar (+ etiketka jadvali)
  PUT  /api/postprocessors/machines/{key}/params               {params: {param: qiymat}} — to'liq almashtirish; tur/diapazon tekshiriladi
  PUT  /api/postprocessors/machines/{key}/label-fields         {label_fields: [{name, expr}]} — ifoda `expr.compile_check` bilan
  POST /api/postprocessors/machines/{key}/label-fields/preview {project_id?, op_id?, part_uid?, fields?} — har ifoda detal kontekstida

Noma'lum stanok yoki parametr kaliti — 400; qiymat/ifoda xatosi — 400 va `{detail, errors: [...]}` (hech narsa saqlanmaydi).
Mavjud `GET/PUT /api/postprocessors/machines` (yoqish, shablon, prefiks) o'zgarmagan. Yo'l parametrlari faqat satr — server
fayl tizimiga yozmaydi va o'qimaydi. Stanok formati yo'q: faqat sozlama va toza ma'lumot (CLAUDE.md 14-qoida).
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import store
from .i18n import _
from .models import OpType
from .services import pp_machine_ctx as C
from .services import pp_machine_schema as S

router = APIRouter(prefix="/postprocessors/machines", tags=["postprotsessor"])


def _key(key: str) -> str:
    from .services.postprocessors import MACHINE_BY_KEY
    if key not in MACHINE_BY_KEY:
        raise HTTPException(400, _("pp_machine_unknown", k=key[:60]))
    return key


def _need_table(key: str) -> None:
    if S.schema_of(key).label_table is None:
        raise HTTPException(400, _("pp_no_label_table"))


def _bad(msg_key: str, errors: list[dict], text: str) -> JSONResponse:
    """400: qisqa xabar (`detail`) + to'liq xatolar ro'yxati (`errors`)."""
    return JSONResponse(status_code=400, content=dict(detail=_(msg_key, e=text), errors=errors))


@router.get("/{key}/schema")
def machine_schema(key: str):
    return C.schema_payload(_key(key))


class ParamsIn(BaseModel):
    params: dict[str, Any]


@router.put("/{key}/params")
def machine_params_put(key: str, inp: ParamsIn):
    """Stanok parametrlarini saqlash (to'liq almashtirish: yuborilmagan parametr — standart). Xato bo'lsa hech narsa saqlanmaydi."""
    key = _key(key)
    clean, errors = S.validate_params(key, inp.params)
    if errors:
        return _bad("pp_params_invalid", errors, "; ".join(f"{e['key']}: {e['message']}" for e in errors[:3]))
    C.set_params(key, clean)
    return C.schema_payload(key)


class ToolsIn(BaseModel):
    tools: dict[str, str]


def _tools_payload(key: str) -> dict:
    """«Инструменты» jadvali: standart qatorlar + foydalanuvchi qo'shgan qatorlar; `ref` — stanokdagi raqam / nom."""
    from .services.ppfmt import tooling as T
    saved = C.get_tools(key)
    rows = T.std_rows(key)
    seen = {r["key"] for r in rows}
    for r in rows:
        if r["key"] in saved:
            r["ref"] = saved[r["key"]]
    for k, v in saved.items():                       # nostandart diametrlar (foydalanuvchi qo'shgan)
        parts = k.split(":")
        if k not in seen and len(parts) == 3 and parts[0] in T.KINDS and parts[1] in T.PLANES:
            try:
                rows.append(dict(key=k, kind=parts[0], plane=parts[1], d=float(parts[2]), ref=v))
            except ValueError:
                continue
    return dict(key=key, rows=rows, kinds=list(T.KINDS), planes=list(T.PLANES))


@router.get("/{key}/tools")
def machine_tools(key: str):
    return _tools_payload(_key(key))


@router.put("/{key}/tools")
def machine_tools_put(key: str, inp: ToolsIn):
    """Asboblar jadvalini saqlash: {asbob kaliti `tur:tekislik:diametr`: raqam / nom}; bo'sh qiymat — o'chiriladi."""
    from .services.ppfmt import tooling as T
    key = _key(key)
    clean: dict[str, str] = {}
    for k, v in inp.tools.items():
        parts = str(k).split(":")
        if len(parts) != 3 or parts[0] not in T.KINDS or parts[1] not in T.PLANES:
            raise HTTPException(400, _("pp_tools_bad_key", k=str(k)[:40]))
        try:
            d = float(parts[2])
        except ValueError:
            raise HTTPException(400, _("pp_tools_bad_key", k=str(k)[:40])) from None
        if not (0 < d <= 400) or len(str(v)) > 40:
            raise HTTPException(400, _("pp_tools_bad_key", k=str(k)[:40]))
        if str(v).strip():
            clean[T.tool_key(parts[0], parts[1], d)] = str(v).strip()
    C.set_tools(key, clean)
    return _tools_payload(key)


class LabelFieldsIn(BaseModel):
    label_fields: list[Any]


@router.put("/{key}/label-fields")
def machine_label_fields_put(key: str, inp: LabelFieldsIn):
    """«Данные для этикеток» jadvalini saqlash. Nom bo'sh/takror bo'lmasin; ifoda sintaksisi `expr.compile_check` bilan
    tekshiriladi (bo'sh ifoda — qiymat «»). Noma'lum o'zgaruvchi nomi bu yerda emas, ko'rish (`preview`) da topiladi."""
    key = _key(key)
    _need_table(key)
    rows, errors = S.validate_label_fields(key, inp.label_fields)
    if errors:
        return _bad("pp_label_invalid", errors, "; ".join(
            f"{e['name'] or ('#' + str(e['index'] + 1))}: {e['message']}" for e in errors[:3]))
    C.set_label_fields(key, rows)
    return C.schema_payload(key)


class PreviewIn(BaseModel):
    project_id: Optional[str] = None
    op_id: Optional[str] = None
    part_uid: Optional[int] = None
    fields: Optional[list[Any]] = None          # saqlanmagan qoralama; yo'q bo'lsa — saqlangan jadval


@router.post("/{key}/label-fields/preview")
def machine_label_fields_preview(key: str, inp: PreviewIn):
    """Har maydon ifodasini tanlangan detal kontekstida hisoblaydi (`label_vars` muhiti: `usedCount`, `ets`, `XNC1`, `grtn` …).
    Loyiha berilmasa — namuna loyiha. Javob: {source, part, map_index, fields: [{name, expr, ok, type, value, text, error, stage,
    name_error}], variables: [{name, ru, uz, value}]}; xato — `value = «#ERR»`; `variables` — ifoda yordamchisi uchun shu
    detalning eng ko'p ishlatiladigan o'zgaruvchilari."""
    key = _key(key)
    _need_table(key)
    if inp.fields is None:
        fields = C.get_label_fields(key)
    else:
        if len(inp.fields) > S.MAX_LABEL_ROWS:
            raise HTTPException(400, _("pp_label_rows_limit", n=S.MAX_LABEL_ROWS))
        fields = [dict(name=str(r.get("name", "")), expr=str(r.get("expr", ""))) for r in inp.fields if isinstance(r, dict)]
    if inp.project_id:
        project = store.load(inp.project_id)
        op = store.op_of(project, inp.op_id or "")
        if op.type != OpType.CS or not op.parts:
            raise HTTPException(400, _("pp_label_op_cs"))
        part = next((p for p in op.parts if p.uid == inp.part_uid), None) if inp.part_uid is not None else op.parts[0]
        if part is None:
            raise HTTPException(404, _("part_not_found"))
        source = "project"
    else:
        project, op, part = C.sample_target()
        source = "sample"
    return dict(source=source, **C.preview_fields(key, fields, project, op, part))
