"""Ifoda tili API (muharrir yordamchisi): funksiyalar ro'yxati va ifodani serverda tekshirish.

  GET  /api/expr/functions  — guruhlar, funksiyalar (nom, imzo, ru/uz tavsif, misol va uning natijasi), konstantalar, operatorlar, chegaralar
  POST /api/expr/check      — {expr, context?, degrees?} → {ok, type, value, value_text, error, stage}
  POST /api/expr/eval-rows  — {exprs, rows} → {results: [{error, values, errors}]}: jadval «Выражение» ustunlari (har qator — kontekst)

Ifoda **faqat serverda** hisoblanadi (frontendda ikkinchi dvigatel yo'q — natija farqi xavfi). Chegaralar `services/expr.py` da:
uzunlik ≤ 1000, hisoblash qadamlari ≤ 10 000, matn ≤ 10 000, `calculate` ≤ 4 daraja; `eval`/`ast` ishlatilmaydi.
"""
from __future__ import annotations

import logging
import math
from typing import Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt, StrictStr

from .i18n import LANG, _
from .services import expr as E
from .services import expr_docs as D

log = logging.getLogger(__name__)
router = APIRouter(prefix="/expr", tags=["ifodalar"])

MAX_CONTEXT = 200            # kontekstdagi o'zgaruvchilar soni
MAX_NAME = 100               # o'zgaruvchi nomi uzunligi
MAX_CTX_TEXT = 1000          # kontekstdagi matn qiymati uzunligi
MAX_CTX_INT = 10 ** 15       # kontekstdagi butun qiymat moduli
MAX_BODY_EXPR = 5000         # so'rovdagi ifoda (undan uzunlari 422); dvigatel chegarasi — E.MAX_SRC
MAX_ROWS = 5000              # eval-rows: qatorlar (O «Материалы» chegarasi bilan bir xil)
MAX_EXPRS = 20               # eval-rows: bitta so'rovdagi ifodalar
MAX_CELLS = 50_000           # eval-rows: qatorlar × ifodalar

CtxValue = Union[StrictBool, StrictInt, StrictFloat, StrictStr, None]


class CheckIn(BaseModel):
    expr: str = Field(max_length=MAX_BODY_EXPR)
    context: dict[str, CtxValue] = Field(default_factory=dict)    # o'zgaruvchi nomi → namuna qiymat
    degrees: bool = False                                          # burchaklar gradusda (XNC eski rejimi); standart — radian


def _lang() -> str:
    return "uz" if LANG.get() == "uz" else "ru"


@router.get("/functions")
def functions():
    lang = _lang()
    return dict(
        groups=D.group_rows(),
        functions=D.function_rows(lang),
        constants=D.constant_rows(lang),
        operators=D.operator_rows(lang),
        limits=dict(max_length=E.MAX_SRC, max_steps=E.MAX_STEPS, max_text=E.MAX_TEXT, max_calc_depth=E.MAX_CALC_DEPTH,
                    max_context=MAX_CONTEXT),
    )


def _clean_context(ctx: dict) -> dict:
    if len(ctx) > MAX_CONTEXT:
        raise HTTPException(400, _("expr_ctx_too_many", n=MAX_CONTEXT))
    env: dict = {}
    for name, v in ctx.items():
        bad = len(name) > MAX_NAME or not name.strip()
        if isinstance(v, bool) or v is None:
            pass
        elif isinstance(v, int):
            bad = bad or abs(v) > MAX_CTX_INT
        elif isinstance(v, float):
            bad = bad or not math.isfinite(v)
        elif isinstance(v, str):
            bad = bad or len(v) > MAX_CTX_TEXT
        if bad:
            raise HTTPException(400, _("expr_ctx_bad", name=name[:MAX_NAME]))
        env[name] = v
    return env


@router.post("/check")
def check(inp: CheckIn):
    env = _clean_context(inp.context)
    src = inp.expr.strip()
    out: dict = dict(ok=False, type=None, value=None, value_text="", error=None, stage=None)
    try:
        E.compile_check(src)                                    # avval sintaksis (o'zgaruvchi qiymatlarisiz); bo'sh ifoda ham xato
    except ValueError as e:
        out.update(error=str(e), stage="syntax")
        return out
    except Exception:  # noqa: BLE001
        log.exception("expr.check: kutilmagan xato (sintaksis)")
        out.update(error=_("xnc.e_syntax"), stage="syntax")
        return out
    try:
        v = E.evaluate(src, env, degrees=inp.degrees, lang=_lang())
    except ValueError as e:
        out.update(error=str(e), stage="eval")
        return out
    except Exception:  # noqa: BLE001  — dvigatel kutilmagan xato bersa ham API 500 qaytarmaydi (xabar umumiy, jurnalga yoziladi)
        log.exception("expr.check: kutilmagan xato")
        out.update(error=_("xnc.e_forbidden"), stage="eval")
        return out
    value: Optional[Union[bool, int, float, str]] = v
    if isinstance(v, float) and not math.isfinite(v):
        value = None
    out.update(ok=True, type=D.type_name(v), value=value, value_text=E.to_text(v))
    return out


class RowsIn(BaseModel):
    exprs: list[str] = Field(max_length=MAX_EXPRS)
    rows: list[dict[str, CtxValue]] = Field(max_length=MAX_ROWS)


@router.post("/eval-rows")
def eval_rows(inp: RowsIn):
    """Jadvaldagi «Выражение» ustunlari: har ifoda har qator kontekstida hisoblanadi (qator maydonlari + «Настроенный Параметры»).
    Javob: `results[i]` — i-ifoda: `error` (sintaksis xatosi — butun ustun uchun), `values[j]` (j-qator qiymati; xatoda null)
    va `errors[j]` (qator xatosi matni yoki null). Bo'sh ifoda — hamma qiymat null, xatosiz."""
    if any(len(x) > MAX_BODY_EXPR for x in inp.exprs) or len(inp.exprs) * len(inp.rows) > MAX_CELLS:
        raise HTTPException(400, _("expr_rows_limit", rows=MAX_ROWS, exprs=MAX_EXPRS))
    envs = [_clean_context(r) for r in inp.rows]
    n = len(envs)
    lang = _lang()
    results = []
    for raw in inp.exprs:
        src = raw.strip()
        res: dict = dict(error=None, values=[None] * n, errors=[None] * n)
        results.append(res)
        if not src:
            continue
        try:
            E.compile_check(src)
        except ValueError as e:
            res["error"] = str(e)
            continue
        except Exception:  # noqa: BLE001
            log.exception("expr.eval_rows: kutilmagan xato (sintaksis)")
            res["error"] = _("xnc.e_syntax")
            continue
        for j, env in enumerate(envs):
            try:
                v = E.evaluate(src, env, lang=lang)
            except ValueError as e:
                res["errors"][j] = str(e)
                continue
            except Exception:  # noqa: BLE001
                log.exception("expr.eval_rows: kutilmagan xato")
                res["errors"][j] = _("xnc.e_forbidden")
                continue
            res["values"][j] = None if isinstance(v, float) and not math.isfinite(v) else v
    return dict(results=results)
