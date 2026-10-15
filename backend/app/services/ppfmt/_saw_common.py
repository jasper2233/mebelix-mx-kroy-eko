"""Arra (pil markazi) formatlari uchun umumiy yordamchilar: fayl nomi, sana, daraxt bo'ylab yurish, sinov uchun
sun'iy SawJob. Modul nomi «_» bilan boshlanadi — `load_all()` uni format sifatida yuklamaydi."""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterator, Optional

from . import SawJob, SawMap, SawNode, SawPart, safe_name

PROGRAM = "MebeliX Kroy"          # yaratuvchi / dastur maydonlari uchun (boshqa dastur nomi yozilmaydi)


def job_title(job: SawJob, n: int = 80) -> str:
    """Fayl nomi (kengaytmasiz): `<loyiha>_<material>`; loyiha nomi buyurtma raqami bilan boshlanmasa — oldiga raqam.
    Namunalarda loyiha nomi allaqachon `3161_mijoz` ko'rinishida, shuning uchun raqam takrorlanmaydi."""
    order = (job.order or "").strip()
    pn = (job.project_name or "").strip()
    if order and order != "0" and not pn.startswith(order):
        pn = f"{order}_{pn}" if pn else order
    return safe_name(f"{pn}_{job.material_name}" if pn else job.material_name, "kroy", n)


def parse_date(s: str) -> Optional[date]:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19] if "T" in s else s[:10], fmt).date()
        except ValueError:
            continue
    return None


def fmt_date(s: str, fmt: str = "%d.%m.%Y") -> str:
    d = parse_date(s) or date.today()
    return d.strftime(fmt)


def ival(v: float) -> str:
    """Butun mm bo'lsa butun, aks holda 1 xonagacha kasr (nuqta bilan)."""
    r = round(float(v), 1)
    return str(int(r)) if r == int(r) else f"{r:.1f}"


def walk(n: Optional[SawNode]) -> Iterator[SawNode]:
    if n is None:
        return
    yield n
    for c in n.children:
        yield from walk(c)


def leaves(n: Optional[SawNode]) -> Iterator[SawNode]:
    for x in walk(n):
        if not x.children and x.kind != "C":
            yield x


def part_totals(job: SawJob) -> dict[int, int]:
    """Kartalar bo'yicha har detal uid → jami dona (karta nusxalari bilan)."""
    out: dict[int, int] = {}
    for m in job.maps:
        for lf in leaves(m.tree):
            if lf.kind == "P" and lf.uid:
                out[lf.uid] = out.get(lf.uid, 0) + max(1, m.copies)
    return out


def tree_errors(n: Optional[SawNode], kerf: float, eps: float = 0.51) -> list[str]:
    """Daraxt tekshiruvi: bolalar ota ichida, o'q bo'ylab ketma-ket (orada ≥ propil), boshqa o'qda ota bilan teng."""
    errs: list[str] = []
    for c in walk(n):
        if c.kind != "C" or not c.children:
            continue
        ax = c.axis or "x"
        pos = c.x if ax == "x" else c.y
        end = (c.x + c.l) if ax == "x" else (c.y + c.w)
        for i, ch in enumerate(c.children):
            a = ch.x if ax == "x" else ch.y
            s = ch.l if ax == "x" else ch.w
            o = ch.w if ax == "x" else ch.l
            if i and a + eps < pos + kerf:
                errs.append(f"propil yetmaydi ({a} < {pos}+{kerf})")
            if a + s > end + eps:
                errs.append(f"bola ota chegarasidan chiqdi ({a}+{s} > {end})")
            if abs(o - (c.w if ax == "x" else c.l)) > eps:
                errs.append(f"bola eni ota bilan teng emas ({o})")
            pos = a + s
    return errs


# ───────────────────────── sinov (pytest) uchun sun'iy ish ─────────────────────────
def demo_job(parts: list[SawPart], maps: list[SawMap], *, kerf: float = 4.0, trim: float = 10.0, thickness: float = 16.0,
             material: str = "LDSP OQ", project_name: str = "9001_test", order: str = "9001",
             params: Optional[dict] = None) -> SawJob:
    from ...models import Operation, OpType, Project
    pr = Project(name=project_name, number=int(order) if order.isdigit() else 0)
    op = Operation(type=OpType.CS, name=material, code="M1")
    return SawJob(project=pr, op=op, order=order, project_name=project_name, customer="", material_name=material,
                  material_code="M1", thickness=thickness, kerf=kerf, trim_length=trim, trim_width=trim, pack_height=40,
                  max_rotations=4, parts=parts, maps=maps, stock=[dict(id="s1", length=2800, width=2070, qty=10000,
                                                                      is_remnant=False)],
                  params=params or {}, order_date="2026-10-01", ready_date="2026-10-01")
