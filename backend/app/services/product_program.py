"""Mahsulot «Программа» (parametrik mahsulot, W12): faqat boshqaruv buyruqlari (Com Par Var Set If Else While DoWhile Break
Continue Sub Call Ret Msg Err) — XNC redaktorining boshqaruv qismi, geometriyasiz.

Hisob — `xnc.evaluate_control` (XNC evaluator'ining «quruq» rejimi: ifodalar `expr.py`, Par qiymati `Product.par_values` dan,
tsikl / qadam chegaralari XNC bilan bir xil). Natija (har saqlashda `apply` yangilaydi, `Product` ga yoziladi):
  prog_vars      — dastur oxiridagi o'zgaruvchilar (Par / Var / Set), faqat sonlar
  prog_messages  — Msg (info), ifoda / dastur xatolari (warning), Err (error — «cheklov buzildi»)
Mahsulot o'zgaruvchilari XNC va etiketka ifodalarida **`product.<nom>`** sifatida ko'rinadi (`ctx_vars`): detalning mahsuloti
dasturidagi o'zgaruvchilar shu detalga bog'langan XNC operatsiyasi (`calc.sync_xnc` → `part_vars`) va detal etiketkasi
(`label_vars.EnvBuilder`) kontekstiga qo'shiladi. Bu qaror GibLab hujjatida yo'q ❓ — `RESERVED_NAMES` / `CTX_PREFIX` konstantalari
(T_W12_SP_PROGRAMMA.md). Mavjud `product.name` kabi standart nomlar bilan to'qnashsa — mavjud ustun (dastur o'zgaruvchisi uzatilmaydi
va ogohlantirish beriladi).

Dastur ichida mahsulotning o'zi `product.qty` (soni) va `product.index` (tartib raqami, 1 dan) o'zgaruvchilari orqali ko'rinadi.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

try:  # xavfsiz XML o'qish (XXE / «billion laughs» dan himoya)
    from defusedxml import ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET  # noqa: N817

from ..i18n import _
from ..models import PROG_MAX_MESSAGES, PROG_MAX_NODES, Product, ProgMessage, Project, XncCommand
from . import xnc

CTX_PREFIX = "product."
# Etiketkada allaqachon mavjud `product.*` nomlari (label_vars.VARS): ularni dastur o'zgaruvchisi bosib ketmaydi
RESERVED_NAMES = frozenset({"index", "name", "code", "qty", "count", "description", "phone1", "phone2", "date", "order"})
MAX_VARS = 200                                           # kontekstga uzatiladigan o'zgaruvchilar (Par/Var soni)
_NAME_OK = re.compile(r"^[^\W\d]\w{0,63}$", re.UNICODE)   # `product.<nom>` — ifoda tilidagi oddiy (nuqtasiz) identifikator


@dataclass
class ProgramResult:
    vars: dict[str, float] = field(default_factory=dict)
    messages: list[dict] = field(default_factory=list)   # {level, text, path}
    params: list[dict] = field(default_factory=list)     # Par holati (UI «Параметры» formasi uchun)
    errors: int = 0                                      # bajarilgan Err soni (cheklov buzilishi)
    problems: int = 0                                    # ifoda / dastur xatolari soni

    @property
    def warnings(self) -> int:
        return sum(1 for m in self.messages if m["level"] == "warning")


# ───────────────────────── `.project` importi: mahsulot `program` atributi (xml) ─────────────────────────
# Formatning ochiq tavsifi (yordam «Формат файлов проектов») mahsulot `program` atributini «Программа с параметрами, переменными
# и ограничениями» (xml) deb ataydi, lekin teg / atribut nomlarini BERMAYDI (hujjatlangan faqat XNC dasturidagi `var`:
# name, type, expr, comment, enable ❓). Korxona fayllarida mahsulot `program` atributi yo'q (0 ta) — shuning uchun quyidagi nomlar
# XNC buyruqlari nomlaridan olingan taxmin: teg = buyruq nomining kichik harfi (`par var set if else while dowhile break
# continue sub call ret msg err com`; qisqa palitra nomlari `wd dw brk con` ham), atributlar: nom `name`, qiymat `value` | `expr`,
# shart `cond` | `expr` | `condition`, matn `text` | `msg`, `comment`, `enable`; Par uchun `label type visible suffix readonly`.
# Tanilmagan teg (yoki geometrik teg) jim o'tkazib yuborilmaydi: ogohlantirish + asl matn `Product.legacy_program` da saqlanadi.
_TAG_CMD = {"com": "Com", "par": "Par", "var": "Var", "set": "Set", "if": "If", "else": "Else", "while": "While", "wd": "While",
            "dowhile": "DoWhile", "dw": "DoWhile", "do": "DoWhile", "break": "Break", "brk": "Break", "continue": "Continue",
            "con": "Continue", "sub": "Sub", "call": "Call", "ret": "Ret", "return": "Ret", "msg": "Msg", "message": "Msg",
            "err": "Err", "error": "Err"}


def _first(a: dict, *keys: str):
    return next((a[k] for k in keys if k in a), None)


def _value(v):
    """Atribut qiymati: son bo'lsa float, aks holda ifoda matni."""
    if v is None:
        return None
    try:
        f = float(v)
    except ValueError:
        return str(v)
    return f if math.isfinite(f) else str(v)


def _xml_params(cmd: str, a: dict) -> dict:
    p: dict = {}
    if cmd in ("Par", "Var", "Set", "Sub", "Call") and a.get("name") is not None:
        p["name"] = a["name"]
    if cmd in ("Par", "Var", "Set"):
        v = _value(_first(a, "value", "expr", "default"))
        if v is not None:
            p["value"] = v
    if cmd in ("Par", "Var") and a.get("type"):
        p["type"] = a["type"]
    if cmd == "Par":
        for k in ("label", "visible", "suffix", "readonly"):
            if a.get(k) is not None:
                p[k] = a[k]
    if cmd in ("If", "Else", "While", "DoWhile"):
        v = _first(a, "cond", "expr", "condition")
        if v is not None:
            p["cond"] = v
    if cmd in ("Msg", "Err"):
        p["text"] = _first(a, "text", "msg", "message") or ""
    return p


def from_xml(text: str, name: str, warnings: list[str]) -> tuple[list[XncCommand], str]:
    """Mahsulot `program` (xml) → (buyruqlar, legacy_program). Hamma teg tanilgan bo'lsa legacy_program bo'sh; aks holda (tanilmagan
    teg, o'qilmagan xml, juda katta dastur) — ogohlantirish qo'shiladi va asl matn qaytadi (yo'qolmaydi, bajarilmaydi)."""
    text = (text or "").strip()
    if not text:
        return [], ""
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except Exception:  # noqa: BLE001 — buzilgan xml
        warnings.append(_("imp_prog_bad", name=name))
        return [], text[:300_000]
    unknown: set[str] = set()
    count = [0]

    def walk(el, depth: int) -> list[XncCommand]:
        out: list[XncCommand] = []
        for ch in el:
            tag = str(ch.tag).lower()
            cmd = _TAG_CMD.get(tag)
            if cmd is None or depth > 32 or count[0] > PROG_MAX_NODES:
                unknown.add(str(ch.tag)[:40])
                continue
            count[0] += 1
            a = ch.attrib
            comment = a.get("comment", "") or (a.get("text", "") if cmd == "Com" else "")
            out.append(XncCommand(cmd=cmd, params=_xml_params(cmd, a), comment=comment,
                                  enabled=str(a.get("enable", "true")).strip().lower() not in ("false", "0"),
                                  children=walk(ch, depth + 1)))
        return out

    cmds = walk(root, 0)
    if count[0] > PROG_MAX_NODES:
        warnings.append(_("imp_prog_bad", name=name))
        return [], text[:300_000]
    for tag in sorted(unknown):
        warnings.append(_("imp_prog_tag", name=name, tag=tag))
    return cmds, (text[:300_000] if unknown else "")


def node_count(cmds) -> int:
    n, stack = 0, list(cmds)
    while stack:
        c = stack.pop()
        n += 1
        stack.extend(c.children)
    return n


def run(product: Product, index: int = 0) -> ProgramResult:
    """Mahsulot dasturini hisoblaydi (mahsulotga yozmaydi). `index` — mahsulotning loyihadagi tartib raqami (1 dan)."""
    res = ProgramResult()
    if product.legacy_program:                               # fayldagi dastur (to'liq / qisman) tushunilmagan — bajarilmaydi
        res.messages.append(dict(level="warning", text=_("pp.w_legacy"), path=""))
    if not product.program:
        return res
    if node_count(product.program) > PROG_MAX_NODES:       # model chegarasidan oshgan eski ma'lumot (API rad etadi)
        res.messages.append(dict(level="error", text=_("pp.w_nodes", n=PROG_MAX_NODES), path=""))
        res.problems = 1
        return res
    seeds = {"product.qty": float(product.qty), "product.index": float(index)}
    ops = xnc.evaluate_control(product.program, seeds, product.par_values)
    for n in ops.notes:
        res.messages.append(dict(level="error" if n["level"] == "error" else "info", text=n["text"][:500], path=n["n"][:60]))
    for m in ops.messages:
        res.messages.append(dict(level="warning", text=str(m)[:500], path=""))
    res.params = xnc.unique_params(ops.params)
    res.errors = ops.violations
    res.problems = ops.problems
    for name, v in ops.vars.items():
        if len(res.vars) >= MAX_VARS:
            break
        if not _NAME_OK.match(name):
            res.messages.append(dict(level="warning", text=_("pp.w_badname", name=name[:60]), path=""))
        elif name in RESERVED_NAMES:
            res.messages.append(dict(level="warning", text=_("pp.w_reserved", name=name), path=""))
        elif isinstance(v, (int, float)) and math.isfinite(v):
            res.vars[name] = float(v)
    del res.messages[PROG_MAX_MESSAGES:]
    return res


def apply(project: Project) -> None:
    """Hamma mahsulot dasturlarini hisoblab natijani (`prog_vars`, `prog_messages`) mahsulotga yozadi (har saqlashda — calc.recalc_project)."""
    for i, pr in enumerate(project.products, 1):
        if not pr.program and not pr.legacy_program and not pr.prog_vars and not pr.prog_messages:
            continue                                         # dasturi yo'q mahsulot (aksariyat) — hech narsa qilinmaydi
        res = run(pr, i)
        pr.prog_vars = res.vars
        pr.prog_messages = [ProgMessage(**m) for m in res.messages]


def ctx_vars(product: Product | None) -> dict[str, float]:
    """XNC va etiketka konteksti uchun: `{"product.<nom>": qiymat}` (mahsulotning hisoblangan o'zgaruvchilari)."""
    if product is None or not product.prog_vars:
        return {}
    return {CTX_PREFIX + k: v for k, v in product.prog_vars.items()}


def severity(project: Project) -> dict:
    """Loyiha sarlavhasidagi ogohlantirish belgisi uchun: {errors, warnings, products} (Err / xato soni, mahsulotlar soni)."""
    err = warn = prods = 0
    for pr in project.products:
        e = sum(1 for m in pr.prog_messages if m.level == "error")
        w = sum(1 for m in pr.prog_messages if m.level == "warning")
        err += e
        warn += w
        prods += 1 if (e or w) else 0
    return dict(errors=err, warnings=warn, products=prods)


def state(project: Project, product: Product) -> dict:
    """UI uchun (`GET .../products/{prid}/program-state`): Par parametrlari holati, o'zgaruvchilar, xabarlar (foydalanuvchi tilida)."""
    idx = next((i for i, p in enumerate(project.products, 1) if p.id == product.id), 0)
    r = run(product, idx)
    return dict(params=r.params, vars=r.vars, messages=r.messages, errors=r.errors, warnings=r.warnings, problems=r.problems)


def recalc_parametric(project: Project) -> dict:
    """«Пересчитать параметричность» (taxminiy ma'no ❓): hamma mahsulot dasturlari va XNC operatsiyalari ifodalari qayta
    hisoblanadi (`calc.recalc_project`: mahsulot o'zgaruvchilari → XNC `part_vars`), natijalar yig'ma hisobot sifatida qaytadi:
    {products: [{id, name, vars, errors, warnings, info}], xnc: [{id, code, name, errors, messages}], totals}."""
    from . import calc
    calc.recalc_project(project)
    prods, programs, err, warn = [], 0, 0, 0
    for i, pr in enumerate(project.products, 1):
        if not (pr.program or pr.legacy_program):
            continue
        programs += 1
        res = run(pr, i)
        err += res.errors
        warn += res.warnings
        prods.append(dict(id=pr.id, name=pr.name, vars=len(res.vars), errors=res.errors, warnings=res.warnings,
                          info=sum(1 for m in res.messages if m["level"] == "info"),
                          messages=[m for m in res.messages if m["level"] != "info"][:20]))
    xs, xerr = [], 0
    for op in project.operations:
        if op.type.value != "XNC" or op.xnc is None or not op.xnc.program:
            continue
        x = op.xnc
        ops = xnc.evaluate(x.program, x.length, x.width, x.thickness, xnc.program_vars(x), x.par_values)
        xerr += ops.problems
        xs.append(dict(id=op.id, code=op.code, name=op.name, errors=ops.problems, messages=list(ops.messages)[:10]))
    return dict(products=prods, xnc=xs,
                totals=dict(products=len(project.products), programs=programs, xnc=len(xs), errors=err,
                            warnings=warn, xnc_errors=xerr))
