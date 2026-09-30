"""Excel / CSV dan detallarni import qilish.

Ustunlar xaritasi (col_map) foydalanuvchi sozlaydi, masalan:
  {"name": "A", "length": "B", "width": "C", "qty": "D", "grain": "E",
   "edge_top": "F", "edge_bottom": "G", "edge_left": "H", "edge_right": "I", "code": "J"}
Kromka ustunida EL operatsiyasining kodi yoki nomi yoziladi (bo'sh = kromka yo'q).
"""
from __future__ import annotations

import csv
import io

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

from ..models import EdgeRef, OpType, Part, Project

TRUE = {"1", "да", "ha", "yes", "true", "+", "x"}


def _rows_xlsx(data: bytes, sheet: int, start_row: int):
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.worksheets[sheet]
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if i >= start_row:
            yield list(row)


def _rows_csv(data: bytes, start_row: int):
    text = data.decode("utf-8-sig", errors="replace")
    dialect = csv.Sniffer().sniff(text[:2048], delimiters=";,\t")
    for i, row in enumerate(csv.reader(io.StringIO(text), dialect), 1):
        if i >= start_row:
            yield row


def _cell(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def preview(data: bytes, filename: str, sheet: int = 0, n: int = 30) -> dict:
    """Ustunlar xaritasini tanlash uchun: varaqlar nomi va birinchi n qator (A, B, C ... harflari bilan)."""
    from openpyxl.utils import get_column_letter
    sheets: list[str] = []
    if filename.lower().endswith(".csv"):
        rows = []
        for i, r in enumerate(_rows_csv(data, 1)):
            if i >= n:
                break
            rows.append([_cell(c) for c in r])
    else:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        sheets = [ws.title for ws in wb.worksheets]
        ws = wb.worksheets[min(sheet, len(wb.worksheets) - 1)]
        rows = []
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i >= n:
                break
            rows.append([_cell(c) for c in r])
    width = max((len(r) for r in rows), default=0)
    return dict(sheets=sheets, columns=[get_column_letter(i + 1) for i in range(width)],
                rows=[r + [""] * (width - len(r)) for r in rows])


def import_catalog(data: bytes, filename: str, col_map: dict[str, str], sheet: int = 0, start_row: int = 2,
                   default_kind: str = "sheet") -> list[dict]:
    """Каталог товаров: ustunlar xaritasi bo'yicha qatorlar (id bo'sh bo'lsa — kod yoki qator raqami)."""
    rows = _rows_csv(data, start_row) if filename.lower().endswith(".csv") else _rows_xlsx(data, sheet, start_row)
    idx = {k: column_index_from_string(v) - 1 for k, v in col_map.items() if v}

    def get(row, key, default=None):
        i = idx.get(key)
        if i is None or i >= len(row) or row[i] is None or str(row[i]).strip() == "":
            return default
        return row[i]

    def num(row, key):
        v = get(row, key)
        if v is None:
            return None
        try:
            return float(str(v).replace(",", ".").replace(" ", ""))
        except ValueError:
            return None

    out = []
    for n, row in enumerate(rows, start_row):
        name = get(row, "name")
        if name is None:
            continue
        code = _cell(get(row, "code", ""))
        rid = _cell(get(row, "id", "")) or code or f"row{n}"
        parent = get(row, "parent_id")
        out.append(dict(id=rid, parent_id=_cell(parent) if parent is not None else None,
                        kind=str(get(row, "kind", default_kind)).strip() or default_kind, code=code,
                        name=str(name).strip(), unit=_cell(get(row, "unit", "")), price=num(row, "price") or 0,
                        stock=num(row, "stock") or 0, thickness=num(row, "thickness"), length=num(row, "length"),
                        width=num(row, "width"), params={}))
    return out


def import_parts(project: Project, data: bytes, filename: str, col_map: dict[str, str],
                 sheet: int = 0, start_row: int = 2) -> list[Part]:
    rows = _rows_csv(data, start_row) if filename.lower().endswith(".csv") \
        else _rows_xlsx(data, sheet, start_row)
    idx = {k: column_index_from_string(v) - 1 for k, v in col_map.items() if v}
    el_ops = {}
    for op in project.operations:
        if op.type == OpType.EL:
            el_ops[op.code.strip().lower()] = op.id
            el_ops[op.name.strip().lower()] = op.id

    def get(row, key, default=None):
        i = idx.get(key)
        if i is None or i >= len(row) or row[i] is None or str(row[i]).strip() == "":
            return default
        return row[i]

    uid = max((p.uid for op in project.operations for p in op.parts), default=0)
    parts: list[Part] = []
    for row in rows:
        L, W = get(row, "length"), get(row, "width")
        if L is None or W is None:
            continue
        try:
            L = float(str(L).replace(",", ".")); W = float(str(W).replace(",", "."))
        except ValueError:
            continue
        uid += 1
        p = Part(uid=uid, name=str(get(row, "name", "")), code=str(get(row, "code", "")),
                 length=L, width=W, qty=int(float(get(row, "qty", 1))),
                 grain=str(get(row, "grain", "")).strip().lower() in TRUE)
        for side in ("top", "bottom", "left", "right"):
            v = get(row, f"edge_{side}")
            if v is not None:
                setattr(p, f"edge_{side}", EdgeRef(op_id=el_ops.get(str(v).strip().lower())))
        parts.append(p)
    return parts
