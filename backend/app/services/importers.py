"""Excel / CSV dan detallarni import qilish.

Ustunlar xaritasi (col_map) foydalanuvchi sozlaydi, masalan:
  {"name": "A", "length": "B", "width": "C", "qty": "D", "grain": "E",
   "edge_top": "F", "edge_bottom": "G", "edge_left": "H", "edge_right": "I", "code": "J"}
Kromka ustunida EL operatsiyasining kodi, nomi yoki belgisi (A, B ...) yoziladi (bo'sh / «-» / «нет» = kromka yo'q);
topilmasa — Ctrl+V dagidek yangi EL operatsiyasi yaratiladi (keyingi bo'sh belgi va rang bilan).

Raqamlar: «1 200,5», «1 200», «1.200,5», «1200 мм», «2 шт» o'qiladi (probel / qattiq probel — ming ajratgich,
vergul — o'nli). Hech qaysi qator jim tashlanmaydi: o'tkazib yuborilganlar `skipped: [{row, reason}]` da, qo'shimcha
xabarlar (yangi kromka va h.k.) `warnings` da qaytariladi.
"""
from __future__ import annotations

import csv
import io
import math
import re
import string
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

from ..i18n import _
from ..models import EdgeRef, ELParams, OpType, Operation, Part, Project

TRUE = {"1", "да", "ha", "yes", "true", "+", "x"}
NO_EDGE = {"-", "—", "–", "0", "нет", "yo'q", "yoq", "no", "none", "n/a"}
MAX_DIM = 100_000         # mm
MAX_QTY = 100_000
SIDES = ("top", "bottom", "left", "right")

# Xavfsizlik chegaralari (mijoz fayli serverda saqlanmaydi — faqat xotirada o'qiladi, formula/makros bajarilmaydi)
MAX_FILE_BYTES = 10 * 1024 * 1024        # yuklangan fayl
MAX_UNZIPPED_BYTES = 150 * 1024 * 1024   # .xlsx ichidagi barcha qismlar yig'indisi (zip-bomba)
MAX_ZIP_ENTRIES = 2000
MAX_ROW_NO = 50_000                      # varaqning shu qatoridan keyingisi o'qilmaydi
MAX_COLS = 256                           # keng qatorlar shu ustunda kesiladi
_OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


# ───────────────────────── Fayl o'qish ─────────────────────────
def check_size(data: bytes) -> None:
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(_("imp_file_big", n=MAX_FILE_BYTES // (1024 * 1024)))


def sniff_format(data: bytes, filename: str) -> str:
    """Fayl turi mazmundan aniqlanadi (kengaytma emas): xlsx (zip) | xls (OLE2) | csv. Kengaytmasi Excel bo'lib,
    mazmuni boshqa (masalan, HTML-«xls») bo'lsa — tushunarli xato."""
    if data[:4] == b"PK\x03\x04":
        return "xlsx"
    if data[:8] == _OLE2:
        return "xls"
    ext = (filename or "").lower().rsplit(".", 1)[-1] if "." in (filename or "") else ""
    if ext in ("xlsx", "xlsm", "xlsb", "xls"):
        raise ValueError(_("imp_not_excel"))
    return "csv"


def cell_text(v) -> str:
    """Katak → matn (butun float — butun son; sana — YYYY-MM-DD)."""
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d") if (v.hour, v.minute, v.second) == (0, 0, 0) else v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _xls_value(c, datemode: int):
    import xlrd
    t = c.ctype
    if t in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK, xlrd.XL_CELL_ERROR):
        return None
    if t == xlrd.XL_CELL_DATE:
        try:
            return xlrd.xldate_as_datetime(c.value, datemode)
        except Exception:  # noqa: BLE001 — noto'g'ri sana raqami: son sifatida
            return c.value
    if t == xlrd.XL_CELL_BOOLEAN:
        return bool(c.value)
    return c.value


class Book:
    """Excel (.xlsx / .xls) yoki CSV fayl: varaqlar nomi va qatorlar oqimi. `with Book(data, filename) as b: ...`.
    Formulalar hisoblanmaydi (saqlangan qiymat o'qiladi), makrolar bajarilmaydi, hech narsa diskka yozilmaydi."""

    def __init__(self, data: bytes, filename: str = ""):
        check_size(data)
        self.data = data
        self.kind = sniff_format(data, filename)
        self.names: list[str] = []
        self._wb = None
        if self.kind == "xlsx":
            try:
                zf = zipfile.ZipFile(io.BytesIO(data))
            except zipfile.BadZipFile as e:
                raise ValueError(_("imp_not_excel")) from e
            infos = zf.infolist()
            if len(infos) > MAX_ZIP_ENTRIES or sum(i.file_size for i in infos) > MAX_UNZIPPED_BYTES:
                raise ValueError(_("imp_zip_big"))
            self._wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True, keep_links=False)
            self.names = [ws.title for ws in self._wb.worksheets]
        elif self.kind == "xls":
            try:
                import xlrd
            except ImportError as e:             # xlrd o'rnatilmagan — aniq xabar (.xlsx / .csv talab qilinadi)
                raise ValueError(_("imp_xls_missing")) from e
            try:
                self._wb = xlrd.open_workbook(file_contents=data, on_demand=True, formatting_info=False)
            except Exception as e:  # noqa: BLE001 — shifrlangan / buzilgan .xls
                raise ValueError(_("imp_xls_bad", e=str(e)[:120])) from e
            self.names = list(self._wb.sheet_names())

    def __enter__(self) -> "Book":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        wb, self._wb = self._wb, None
        if wb is not None:
            try:
                wb.close() if self.kind == "xlsx" else wb.release_resources()
            except Exception:  # noqa: BLE001
                pass

    def index(self, sheet=0, clamp: bool = False) -> int:
        """Varaq: nomi (matn) yoki tartib raqami (0 dan). clamp — chegaradan chiqsa oxirgisi (ko'rish uchun)."""
        if not self.names:
            return 0
        if isinstance(sheet, str) and sheet.strip():
            key = sheet.strip().casefold()
            for i, n in enumerate(self.names):
                if n == sheet or n.strip().casefold() == key:
                    return i
            raise ValueError(_("imp_sheet_missing", s=sheet.strip()[:60]))
        try:
            i = int(sheet or 0)
        except (TypeError, ValueError):
            i = 0
        if 0 <= i < len(self.names):
            return i
        if clamp:
            return max(0, min(i, len(self.names) - 1))
        raise ValueError(_("imp_sheet_missing", s=str(i + 1)))

    def sheet_name(self, sheet=0, clamp: bool = False) -> str:
        return self.names[self.index(sheet, clamp)] if self.names else ""

    def rows(self, sheet=0, start_row: int = 1, end_row: int = 0, clamp: bool = False):
        """(qator raqami — fayldagi, 1 dan; qator qiymatlari). `end_row` 0 — oxirigacha (MAX_ROW_NO bilan cheklangan)."""
        start_row = max(1, int(start_row or 1))
        last = MAX_ROW_NO if not end_row or end_row <= 0 else min(int(end_row), MAX_ROW_NO)
        if start_row > last:
            return
        if self.kind == "csv":
            for n, row in enumerate(_csv_reader(self.data), 1):
                if n > last:
                    break
                if n >= start_row:
                    yield n, list(row[:MAX_COLS])
        elif self.kind == "xlsx":
            ws = self._wb.worksheets[self.index(sheet, clamp)]
            for n, row in enumerate(ws.iter_rows(min_row=start_row, max_row=last, values_only=True), start_row):
                yield n, list(row[:MAX_COLS])
        else:
            sh = self._wb.sheet_by_index(self.index(sheet, clamp))
            dm = self._wb.datemode
            for r in range(start_row - 1, min(sh.nrows, last)):
                yield r + 1, [_xls_value(c, dm) for c in sh.row(r)[:MAX_COLS]]


def _csv_reader(data: bytes):
    text = decode_csv(data)
    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=";,\t")
    except csv.Error:                  # bitta ustun yoki ajratgich topilmadi — «;» (Excel, ru/uz)
        head = text[:2048]
        dialect = type("_Dialect", (csv.excel,), {"delimiter": "," if "," in head and ";" not in head else ";"})
    return csv.reader(io.StringIO(text), dialect)


def decode_csv(data: bytes) -> str:
    """CSV matni: UTF-8 (BOM bilan/siz); bo'lmasa — UTF-16 (BOM) yoki cp1251 (rus Excel «CSV; ;»)."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1251", errors="replace")


def _numbered(data: bytes, filename: str, sheet=0, start_row: int = 1, end_row: int = 0):
    """(fayldagi qator raqami, qator) — qator raqami foydalanuvchi ko'rgan raqam (1 dan). .xlsx / .xls / .csv."""
    with Book(data, filename) as bk:
        yield from bk.rows(sheet, start_row, end_row)


_cell = cell_text


# ───────────────────────── Raqamlar ─────────────────────────
_WS = re.compile(r"[\s    ]+")
_NUM = re.compile(r"([+-]?[\d.,]*\d)(?:[^\W\d_]+\.?)?")        # son + ixtiyoriy birlik (мм, mm, шт, pcs)


def parse_number(v) -> float | None:
    """Katak qiymati → son yoki None. Matn: «1 200,5», «1 200», «1.200,5», «1,200.5», «1200 мм»."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    s = _WS.sub("", str(v).replace("−", "-"))
    m = _NUM.fullmatch(s)
    if not m:
        return None
    tok = m.group(1)
    sign = ""
    if tok[0] in "+-":
        sign, tok = tok[0], tok[1:]
    has_dot, has_comma = "." in tok, "," in tok
    if has_dot and has_comma:                      # oxirgi uchragani — o'nli ajratgich
        dec = "." if tok.rfind(".") > tok.rfind(",") else ","
        thou = "," if dec == "." else "."
        tok = tok.replace(thou, "").replace(dec, ".")
    elif has_comma:
        tok = tok.replace(",", "") if tok.count(",") > 1 else tok.replace(",", ".")
    elif has_dot and tok.count(".") > 1:
        tok = tok.replace(".", "")
    try:
        f = float(sign + tok)
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def parse_qty(v) -> int | None:
    """Soni: butun son 0..MAX_QTY (matn: «2 шт», «x2»); aks holda None."""
    f = parse_number(v)
    if f is None:
        m = re.fullmatch(r"\D*?(\d+)\D*", str(v).strip()) if v is not None else None
        if not m:
            return None
        f = float(m.group(1))
    if abs(f - round(f)) > 1e-9 or not (0 <= f <= MAX_QTY):
        return None
    return int(round(f))


def _fmt(f: float) -> str:
    return f"{f:g}"


# ───────────────────────── Ko'rish / katalog ─────────────────────────
def preview(data: bytes, filename: str, sheet: int = 0, n: int = 30) -> dict:
    """Ustunlar xaritasini tanlash uchun: varaqlar nomi va birinchi n qator (A, B, C ... harflari bilan)."""
    from openpyxl.utils import get_column_letter
    with Book(data, filename) as bk:
        rows = [[cell_text(c)[:200] for c in r] for _no, r in bk.rows(sheet, 1, n, clamp=True)]
        sheets, shown, fmt = list(bk.names), bk.sheet_name(sheet, clamp=True), bk.kind
    width = max((len(r) for r in rows), default=0)
    return dict(sheets=sheets, columns=[get_column_letter(i + 1) for i in range(width)],
                rows=[r + [""] * (width - len(r)) for r in rows], sheet=shown, format=fmt)


def import_catalog(data: bytes, filename: str, col_map: dict[str, str], sheet: int = 0, start_row: int = 2,
                   default_kind: str = "sheet") -> list[dict]:
    """Каталог товаров: ustunlar xaritasi bo'yicha qatorlar (id bo'sh bo'lsa — kod yoki qator raqami).
    Daraxt (papka belgisi, ildiz kategoriyalar), rasm va parametrlar ustunlari — `services/catalog.import_catalog_ex`."""
    from .catalog import import_catalog_ex
    return import_catalog_ex(data, filename, col_map, sheet, start_row, default_kind).rows


# ───────────────────────── Detallar ─────────────────────────
@dataclass
class ImportResult:
    parts: list[Part] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)          # [{row, reason}]
    warnings: list[str] = field(default_factory=list)
    created_edges: list[Operation] = field(default_factory=list)   # yangi yaratilgan EL operatsiyalari


def assign_edge_style(project: Project, el: ELParams) -> None:
    """Yangi kromkaga keyingi bo'sh belgi (A, B …) va rang (W18: «Материалы» tabi ham foydalanadi)."""
    from . import el_symbols                   # jadval: «Настройка символов и цветов» (sozlama `el_symbols`)
    els = [o for o in project.operations if o.type == OpType.EL]
    el.symbol, el.color = el_symbols.next_style(((o.el.symbol or "") for o in els if o.el), len(els))


def _new_edge(project: Project, text: str) -> Operation:
    """Noma'lum kromka nomi → yangi EL operatsiyasi (standart parametrlar, keyingi bo'sh belgi va rang)."""
    from . import settings
    try:
        el = ELParams.model_validate(settings.get_default("el_defaults"))
    except Exception:  # noqa: BLE001 — baza yo'q / sozlama buzuq: o'rnatilgan qiymatlar
        el = ELParams()
    assign_edge_style(project, el)
    op = Operation(type=OpType.EL, code="", name=text.strip(), el=el)
    project.operations.append(op)
    return op


class EdgeResolver:
    """Kromka katagi → EL operatsiya id si: kod / nom / belgi (A, B …) bo'yicha mavjudi; «-» — kromka yo'q; topilmasa —
    yangi EL yaratiladi (`created` ga qo'shiladi, `warnings` ga xabar)."""

    def __init__(self, project: Project, created: list[Operation], warnings: list[str]):
        self.project, self.created, self.warnings = project, created, warnings
        self.by_text: dict[str, str] = {}
        self.by_symbol: dict[str, str] = {}
        for op in project.operations:
            if op.type != OpType.EL:
                continue
            for k in (op.code, op.name):
                if k and k.strip():
                    self.by_text.setdefault(k.strip().lower(), op.id)
            if op.el and (op.el.symbol or "").strip():
                self.by_symbol.setdefault(op.el.symbol.strip().lower(), op.id)

    def resolve(self, text: str, rno: int) -> str | None:
        key = text.strip().lower()
        if key in self.by_text:
            return self.by_text[key]
        if key in self.by_symbol:                             # kromka belgisi (A, B ...)
            return self.by_symbol[key]
        if key in NO_EDGE:
            return None
        op = _new_edge(self.project, text)
        self.created.append(op)
        self.by_text[key] = op.id
        self.by_symbol.setdefault((op.el.symbol or "").lower(), op.id)
        self.warnings.append(_("imp_edge_created", row=rno, name=text.strip()))
        return op.id


def check_dim(raw, label: str) -> tuple[float | None, str | None]:
    """O'lcham katagi → (qiymat, None) yoki (None, o'tkazib yuborish sababi)."""
    if raw is None:
        return None, _("imp_skip_empty", f=label)
    f = parse_number(raw)
    if f is None:
        return None, _("imp_skip_nan", f=label, v=str(raw).strip()[:30])
    if f <= 0:
        return None, _("imp_skip_nonpos", f=label, v=_fmt(f))
    if f > MAX_DIM:
        return None, _("imp_skip_big", f=label, v=_fmt(f))
    return f, None


def import_parts_ex(project: Project, data: bytes, filename: str, col_map: dict[str, str],
                    sheet: int = 0, start_row: int = 2) -> ImportResult:
    """Excel/CSV qatorlari → detallar. Yaroqsiz qatorlar `skipped` ga (qator raqami + sabab), yangi kromkalar
    loyihaga EL operatsiya sifatida qo'shiladi (`created_edges`, `warnings`)."""
    if not isinstance(col_map, dict):
        raise ValueError(_("set_json_object"))
    idx = {k: column_index_from_string(str(v).strip().upper()) - 1 for k, v in col_map.items() if v}
    if "length" not in idx or "width" not in idx:
        raise ValueError(_("imp_need_columns"))
    res = ImportResult()
    edge_id = EdgeResolver(project, res.created_edges, res.warnings).resolve
    dim = check_dim

    def get(row, key, default=None):
        i = idx.get(key)
        if i is None or i >= len(row) or row[i] is None or str(row[i]).strip() == "":
            return default
        return row[i]

    uid = max((p.uid for op in project.operations for p in op.parts), default=0)
    for rno, row in _numbered(data, filename, sheet, start_row):
        if all(get(row, k) is None for k in idx):             # to'liq bo'sh qator — jim o'tkaziladi
            continue
        L, el_ = dim(get(row, "length"), _("imp_f_length"))
        W, ew_ = dim(get(row, "width"), _("imp_f_width"))
        qty, eq_ = 1, None
        if get(row, "qty") is not None:
            q = parse_qty(get(row, "qty"))
            if q is None:
                eq_ = _("imp_skip_qty", f=_("imp_f_qty"), v=str(get(row, "qty")).strip()[:30], n=MAX_QTY)
            else:
                qty = q
        reasons = [r for r in (el_, ew_, eq_) if r]
        if reasons:
            res.skipped.append(dict(row=rno, reason="; ".join(reasons)))
            continue
        uid += 1
        pt = Part(uid=uid, name=_cell(get(row, "name", "")), code=_cell(get(row, "code", "")),
                  length=L, width=W, qty=qty, grain=_cell(get(row, "grain", "")).strip().lower() in TRUE)
        for side in SIDES:
            v = get(row, f"edge_{side}")
            if v is not None:
                setattr(pt, f"edge_{side}", EdgeRef(op_id=edge_id(_cell(v), rno)))
        res.parts.append(pt)
    if res.skipped:
        res.warnings.append(_("imp_rows_skipped", n=len(res.skipped)))
    return res


def import_parts(project: Project, data: bytes, filename: str, col_map: dict[str, str],
                 sheet: int = 0, start_row: int = 2) -> list[Part]:
    """Eski interfeys: faqat detallar ro'yxati (o'tkazib yuborilgan qatorlar haqida — `import_parts_ex`)."""
    return import_parts_ex(project, data, filename, col_map, sheet, start_row).parts
