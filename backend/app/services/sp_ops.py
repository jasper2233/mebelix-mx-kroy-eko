"""(SP) Обработка поверхности (W12) — yaratish, `.project` importi, Excel importi uchun bog'lanish nuqtalari.

Operatsiya detalning lits (`Part.surface_face_op`) va/yoki orqa (`Part.surface_back_op`) tomoniga EL kromka kabi bog'lanadi.
Hisob — `calc.surface_usage` (aylanma import bo'lmasligi uchun u yerda); bu modul `calc` ni import qilmaydi.

    ishlov maydoni  = Σ (L × W) × tomonlar soni × (ОК − МК)                     [m²]   — L×W: «Режим размеров» (spSizeMode)
    material sarfi  = Σ (L + 2·r) × (W + 2·r) × tomonlar × (ОК − МК) × (1 + chiqit %)   [m²]   — r = «Длина остатка по краям»
    material narxi  = material sarfi × material narxi (1 m²)            (faqat «Учитывать материал» ✓)
    operatsiya narxi = ishlov maydoni × spCost (1 m²)

Qaysi qismi hujjatda yo'q (SP yordami GibLabda yo'q) — `docs/mebelix/T_W12_SP_PROGRAMMA.md` dagi «savollar».
"""
from __future__ import annotations

import math
from typing import Optional

from ..i18n import _
from ..models import SP_DEFAULT_SIZE_MODE, OpType, Operation, Part, Project, SPParams

# spRestSide ma'nosi ❓: True — har chetda (uzunlik va enga 2·r qo'shiladi), False — faqat bir chetda (r). Bitta konstanta.
REST_BOTH_EDGES = True


def new_params(defaults: Optional[dict] = None) -> SPParams:
    """Yangi SP operatsiyasi parametrlari (`sp_defaults` sozlamasi bo'yicha; hisoblangan maydonlarsiz)."""
    d = {k: v for k, v in (defaults or {}).items() if k not in ("area_m2", "material_m2")}
    try:
        return SPParams.model_validate(d)
    except Exception:  # noqa: BLE001 — buzuq sozlama: o'rnatilgan standart
        return SPParams()


def surface_side(part: Part, side: str) -> Optional[str]:
    """Detal tomoni (`front` | `back`) → SP operatsiya id si."""
    return part.surface_face_op if side == "front" else part.surface_back_op


def attach(part: Part, side: str, sp_op: Optional[Operation]) -> None:
    """Detalning tomoniga SP operatsiyasini biriktirish (None — olib tashlash). Excel importi (W3, «(SP) Обработка поверхности»
    ustun guruhi, XLS-009) shu funksiyadan foydalanadi."""
    oid = sp_op.id if sp_op is not None else None
    if side == "front":
        part.surface_face_op = oid
    else:
        part.surface_back_op = oid


def find_or_create(project: Project, text: str) -> Operation:
    """Matn (kod yoki nom, katta-kichik harfga sezgirsiz) bo'yicha mavjud SP operatsiyasi; yo'q bo'lsa — yangisi (standart
    parametrlar bilan) loyihaga qo'shiladi. Excel importi (W3) uchun bog'lanish nuqtasi (EL uchun `importers.EdgeResolver` kabi)."""
    key = (text or "").strip().lower()
    for op in project.operations:
        if op.type == OpType.SP and key and key in ((op.name or "").strip().lower(), (op.code or "").strip().lower()):
            return op
    from . import settings
    try:
        defaults = settings.get_default("sp_defaults")
    except Exception:  # noqa: BLE001 — baza yo'q / sozlama buzuq
        defaults = None
    op = Operation(type=OpType.SP, name=(text or "").strip(), sp=new_params(defaults))
    project.operations.append(op)
    return op


def prune_surface_refs(project: Project) -> None:
    """O'chirilgan (yoki SP bo'lmay qolgan) operatsiyaga havolalar detallardan tozalanadi."""
    ids = {o.id for o in project.operations if o.type == OpType.SP}
    for op in project.operations:
        for pt in op.parts:
            if pt.surface_face_op and pt.surface_face_op not in ids:
                pt.surface_face_op = None
            if pt.surface_back_op and pt.surface_back_op not in ids:
                pt.surface_back_op = None


def part_sides(part: Part, sp_id: str) -> int:
    """Detalning nechta tomoni shu SP operatsiyasiga bog'langan (0..2)."""
    return int(part.surface_face_op == sp_id) + int(part.surface_back_op == sp_id)


def material_dims(L: float, W: float, rest: float) -> tuple[float, float]:
    """Material o'lchami: chetlardagi qoldiq bilan (`REST_BOTH_EDGES`)."""
    k = 2 if REST_BOTH_EDGES else 1
    return L + k * rest, W + k * rest


# ───────────────────────── `.project` importi ─────────────────────────
def _f(v, d: float = 0.0) -> float:
    try:
        x = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return d
    return x if math.isfinite(x) else d


def _b(v, d: bool = False) -> bool:
    if v is None:
        return d
    return str(v).strip().lower() in ("true", "1", "yes", "да")


def from_project_xml(oe, goods: dict) -> Operation:
    """`<operation typeId="SP">` → `Operation(type=SP)`. Format (yordam «Формат файлов проектов»): `spCalcMat`, `spWastePRC`,
    `spRestSide`, `spSizeMode` (-1 pilniy, 0 zagotovka), `spCost` (1 m² narxi) + standart atributlar; `<material id>` — material
    (`good`): kod, nom va narx (`cost` — material 1 m²) shundan olinadi, bo'lmasa `typeName`. Detallarga havolalar
    (`<part id>`) importer tomonidan o'rnatiladi. `printable` / `startNewPage` ni chaqiruvchi o'rnatadi."""
    me = oe.find("material")
    good = goods.get(me.get("id")) if me is not None else None
    name = ((good.get("name") if good is not None else None) or oe.get("typeName") or oe.get("name") or "").strip() \
        or "Обработка поверхности"
    code = ((good.get("code") if good is not None else None) or oe.get("code") or "").strip()
    mode = int(_f(oe.get("spSizeMode"), SP_DEFAULT_SIZE_MODE))
    sp = SPParams(count_material=_b(oe.get("spCalcMat"), True),
                  waste_percent=min(max(_f(oe.get("spWastePRC")), 0.0), 100.0),
                  rest_side=min(max(_f(oe.get("spRestSide")), 0.0), 10000.0),
                  size_mode=mode if mode in (-1, 0) else SP_DEFAULT_SIZE_MODE,
                  op_price=min(max(_f(oe.get("spCost")), 0.0), 1e9),
                  price=min(max(_f(good.get("cost")) if good is not None else 0.0, 0.0), 1e9))
    return Operation(type=OpType.SP, code=code[:100], name=name[:300], description=oe.get("description") or "", sp=sp)


def link_parts(links: list[tuple[str, Operation]], copies: dict[str, list[Part]], warnings: list[str]) -> None:
    """`<part id>` havolalari → detallar. Fayl SP tomonini ko'rsatmaydi ❓: birinchi SP — lits (old) tomon; detalda lits band
    bo'lsa (ikkinchi SP) — orqa tomon. Har SP uchun bitta ogohlantirish (tomon taxmin qilingani)."""
    warned: set[str] = set()
    for src_id, op in links:
        targets = copies.get(src_id, [])
        if not targets:
            warnings.append(_("imp_sp_part", name=op.name, ref=src_id))
            continue
        if op.id not in warned:
            warned.add(op.id)
            warnings.append(_("imp_sp_side", name=op.name))
        for pt in targets:
            if pt.surface_face_op in (None, op.id):
                pt.surface_face_op = op.id
            elif pt.surface_back_op in (None, op.id):
                pt.surface_back_op = op.id
