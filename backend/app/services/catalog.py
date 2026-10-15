"""«Товары» (material katalogi): kategoriyalar daraxti, rasm xavfsizligi va Excel/CSV importi.

Daraxt modeli (goods.xls ustunlariga mos): `id` / `parent_id` / papka belgisi (`kind = "folder"`). Papka — kategoriya
(ishlab chiqaruvchi → qalinlik → o'lcham …), qolgani — material qatori (`sheet | linear | edge | surface`). Material turi
«ildiz kategoriya»dan olinadi: import sozlamasida har tur uchun ildiz papka ID si beriladi, qator shu ildiz ostida bo'lsa —
o'sha tur (ildiz berilmasa — «standart tur»).

Rasm: faqat `data:image/(png|jpeg|gif|webp);base64,…` (≤ 256 KB) yoki `http(s)://` havola. Tur mazmundan (sehrli baytlar)
aniqlanadi, mijoz aytgan MIME ga ishonilmaydi; SVG va boshqa turlar rad etiladi; o'lcham tomonlari ≤ 8192 px.
Faylning serverdagi yo'li yoki ixtiyoriy URL serverda o'qilmaydi (SSRF / yo'l bosib o'tish yo'q).
"""
from __future__ import annotations

import base64
import binascii
import json
import re
import struct
from dataclasses import dataclass, field
from urllib.parse import urlparse

from openpyxl.utils import column_index_from_string
from sqlalchemy import func, or_, select

from ..db import IS_SQLITE, CatalogImageRow, CatalogItemRow, SessionLocal, text_search
from ..i18n import _
from . import importers as imp

KINDS = ("sheet", "linear", "edge", "surface")
FOLDER = "folder"
CAT_FIELDS = ("id", "parent_id", "isfolder", "code", "name", "unit", "price", "stock", "image", "params",
              "size", "thickness", "length", "width", "kind")
MAX_CATALOG_ROWS = 50_000
MAX_IMAGE_BYTES = 256 * 1024
MAX_IMAGE_SIDE = 8192
MAX_URL_LEN = 500
MAX_PARAMS = 50
MAX_TREE_DEPTH = 64          # daraxt chuqurligi (undan chuqur zanjir shu joydan «ildiz»ga bo'linadi)
_KEY = re.compile(r"^[A-Za-z][\w.\-]{0,39}$")


# ───────────────────────── Rasm ─────────────────────────
def sniff_image(data: bytes) -> str | None:
    """Rasm turi (MIME) — faqat mazmundan: png | jpeg | gif | webp; boshqasi (SVG, HTML, …) — None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def image_size(mime: str, d: bytes) -> tuple[int, int] | None:
    """Rasm eni/bo'yi (piksel) sarlavhadan; o'qib bo'lmasa — None (rasm buzuq deb hisoblanadi)."""
    if len(d) < {"image/png": 24, "image/gif": 10, "image/jpeg": 12, "image/webp": 30}.get(mime, 1 << 30):
        return None                                  # sarlavha kesilgan: qisqa bo'lak noto'g'ri o'lcham bermasin
    try:
        if mime == "image/png":
            return struct.unpack(">II", d[16:24]) if d[12:16] == b"IHDR" else None
        if mime == "image/gif":
            return struct.unpack("<HH", d[6:10])
        if mime == "image/jpeg":
            i, n = 2, len(d)
            for _guard in range(4096):
                while i < n and d[i] != 0xFF:
                    i += 1
                while i < n and d[i] == 0xFF:
                    i += 1
                if i >= n:
                    return None
                m = d[i]
                i += 1
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                    continue
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", d[i + 3:i + 7])
                    return w, h
                i += struct.unpack(">H", d[i:i + 2])[0]
            return None
        if mime == "image/webp":
            kind = d[12:16]
            if kind == b"VP8 ":
                w, h = struct.unpack("<HH", d[26:30])
                return w & 0x3FFF, h & 0x3FFF
            if kind == b"VP8L":
                b = d[21:25]
                return 1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            if kind == b"VP8X":
                return 1 + int.from_bytes(d[24:27], "little"), 1 + int.from_bytes(d[27:30], "little")
    except (struct.error, IndexError):
        return None
    return None


def image_from_bytes(data: bytes) -> str:
    """Rasm baytlari → saqlanadigan `data:` URI (turi/hajmi/o'lchami tekshiriladi). Xato — ValueError (tilga mos)."""
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(_("cat_image_big", n=MAX_IMAGE_BYTES // 1024))
    mime = sniff_image(data)
    if mime is None:
        raise ValueError(_("cat_image_type"))
    size = image_size(mime, data)
    if size is None or not (0 < size[0] <= MAX_IMAGE_SIDE and 0 < size[1] <= MAX_IMAGE_SIDE):
        raise ValueError(_("cat_image_dims", n=MAX_IMAGE_SIDE))
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def normalize_image(value: str) -> str:
    """Rasm qiymati → saqlanadigan matn: `data:image/…;base64,…` (qayta kodlangan) yoki `http(s)://…` havola.
    Boshqa har qanday qiymat (fayl yo'li, `javascript:`, `file:`, SVG …) — ValueError."""
    v = (value or "").strip()
    low = v[:12].lower()
    if low.startswith("data:"):
        head, _sep, payload = v.partition(",")
        if ";base64" not in head.lower() or not payload:
            raise ValueError(_("cat_image_type"))
        # taxminiy hajm: base64 → bayt (4:3) — katta matnni dekodlamasdan rad etish
        if len(payload) > MAX_IMAGE_BYTES * 4 // 3 + 8:
            raise ValueError(_("cat_image_big", n=MAX_IMAGE_BYTES // 1024))
        try:
            raw = base64.b64decode(re.sub(r"\s+", "", payload), validate=True)
        except (binascii.Error, ValueError) as e:
            raise ValueError(_("cat_image_type")) from e
        return image_from_bytes(raw)
    if low.startswith(("http://", "https://")):
        if len(v) > MAX_URL_LEN or re.search(r"[\s\x00-\x1f\x7f<>\"'\\]", v):
            raise ValueError(_("cat_image_url"))
        u = urlparse(v)
        if not u.hostname or u.username or u.password:
            raise ValueError(_("cat_image_url"))
        return v
    raise ValueError(_("cat_image_type"))


def set_image(item_id: str, value: str | None) -> None:
    """Material rasmini saqlash/o'chirish (None). Qiymat `normalize_image` dan o'tgan bo'lishi kerak."""
    with SessionLocal() as s:
        row = s.get(CatalogItemRow, item_id)
        if row is None:
            raise KeyError(item_id)
        img = s.get(CatalogImageRow, item_id)
        if value is None:
            if img is not None:
                s.delete(img)
            row.has_image = False
        else:
            if img is None:
                s.add(CatalogImageRow(item_id=item_id, data=value))
            else:
                img.data = value
            row.has_image = True
        s.commit()


def get_image(item_id: str) -> str | None:
    with SessionLocal() as s:
        img = s.get(CatalogImageRow, item_id)
        return img.data if img is not None else None


def store_images(images: dict[str, str]) -> None:
    """Import vaqtida: {item_id: normalizatsiyalangan rasm} (mavjud qatorlarga)."""
    if not images:
        return
    with SessionLocal() as s:
        for iid, val in images.items():
            img = s.get(CatalogImageRow, iid)
            if img is None:
                s.add(CatalogImageRow(item_id=iid, data=val))
            else:
                img.data = val
            row = s.get(CatalogItemRow, iid)
            if row is not None:
                row.has_image = True
        s.commit()


# ───────────────────────── Parametrlar ustuni ─────────────────────────
def parse_params(v) -> tuple[dict, int]:
    """«Параметры» katagi → ({kalit: qiymat}, tashlab yuborilgan juftliklar soni). Format: JSON obyekt yoki
    `kalit=qiymat; kalit2=qiymat2` (ajratgich `;` yoki yangi qator). Qiymatlar: son, true/false, matn (≤ 200).
    Kalit: lotin harf bilan boshlanadi, ≤ 40 belgi. Ko'pi bilan 50 ta."""
    s = imp.cell_text(v).strip()
    if not s:
        return {}, 0
    pairs: list[tuple[str, object]] = []
    if s.startswith("{"):
        try:
            obj = json.loads(s)
        except ValueError:
            obj = None
        if isinstance(obj, dict):
            pairs = [(str(k), x) for k, x in obj.items()]
    if not pairs:
        for chunk in re.split(r"[;\n]+", s):
            chunk = chunk.strip()
            if not chunk:
                continue
            m = re.match(r"^([^=:]+?)\s*[=:]\s*(.*)$", chunk)
            pairs.append((m.group(1).strip(), m.group(2).strip()) if m else (chunk, True))   # qiymatsiz kalit — true
    out: dict = {}
    dropped = 0
    for k, x in pairs:
        if not _KEY.match(k) or len(out) >= MAX_PARAMS or isinstance(x, (dict, list)):
            dropped += 1
            continue
        if isinstance(x, bool) or x is None:
            out[k] = bool(x)
        elif isinstance(x, (int, float)):
            out[k] = x
        else:
            t = str(x).strip()
            low = t.lower()
            if low in ("true", "yes", "да", "ha"):
                out[k] = True
            elif low in ("false", "no", "нет", "yo'q", "yoq"):
                out[k] = False
            else:
                n = imp.parse_number(t)
                out[k] = (int(n) if n is not None and float(n).is_integer() else n) if n is not None else t[:200]
    return out, dropped


def parse_size(v) -> tuple[float | None, float | None, float | None]:
    """«Размер» katagi → (uzunlik, en, qalinlik): «2750x1830», «2800 × 2070 × 16», «2750*1830», bitta son — faqat uzunlik.
    Ajratgich: x / х (kirill) / × / *. O'qib bo'lmagan bo'lak — None."""
    s = imp.cell_text(v).strip()
    if not s:
        return None, None, None
    nums = [imp.parse_number(t.strip()) for t in re.split(r"\s*[xXхХ×*]\s*", s) if t.strip()][:3]
    nums = [n if n is not None and n > 0 else None for n in nums] + [None, None, None]
    return nums[0], nums[1], nums[2]


# ───────────────────────── Excel/CSV importi ─────────────────────────
@dataclass
class CatalogImport:
    rows: list[dict] = field(default_factory=list)
    images: dict[str, str] = field(default_factory=dict)       # {id: rasm} (normalizatsiyalangan)
    warnings: list[str] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)          # [{row, reason}]
    folders: int = 0
    items: int = 0


def _col(v: str) -> int:
    s = str(v).strip().upper()
    if not re.fullmatch(r"[A-Z]{1,3}", s):
        raise ValueError(_("imp_bad_column", v=str(v)[:20]))
    i = column_index_from_string(s) - 1
    if i >= imp.MAX_COLS:
        raise ValueError(_("imp_bad_column", v=str(v)[:20]))
    return i


def import_catalog_ex(data: bytes, filename: str, col_map: dict, sheet=0, start_row: int = 2,
                      default_kind: str = "sheet", *, end_row: int = 0, roots: dict | None = None,
                      id_prefix: str = "") -> CatalogImport:
    """Katalog qatorlari. col_map kalitlari: `CAT_FIELDS` (id, parent_id, isfolder, code, name, unit, price, stock, image,
    params, size, thickness, length, width, kind); `size` — «Размер» («2750x1830[x16]»): alohida «Длина» / «Ширина» / «Толщина»
    katagi bo'sh bo'lsa shundan olinadi. `roots` — {tur: ildiz kategoriya ID} (qator turi shu ildiz ostida bo'lishidan),
    `id_prefix` — barcha ID larga old qo'shimcha (boshqa fayl/MES ID lari bilan to'qnashmasligi uchun).
    Papka belgisi (`isfolder`) ko'rsatilmasa — boshqa qatorga ota bo'lgan qator papka hisoblanadi."""
    if not isinstance(col_map, dict):
        raise ValueError(_("set_json_object"))
    bad = [k for k in col_map if k not in CAT_FIELDS]
    if bad:
        raise ValueError(_("imp_bad_field", f=str(bad[0])[:30]))
    idx = {k: _col(v) for k, v in col_map.items() if v}
    if "name" not in idx:
        raise ValueError(_("cat_need_name"))
    if default_kind not in KINDS:
        default_kind = "sheet"
    pfx = (id_prefix or "").strip()[:20]
    res = CatalogImport()

    def get(row, key, default=None):
        i = idx.get(key)
        if i is None or i >= len(row) or row[i] is None or str(row[i]).strip() == "":
            return default
        return row[i]

    def num(row, key):
        v = get(row, key)
        return None if v is None else imp.parse_number(v)

    recs: dict[str, dict] = {}
    img_skipped = img_bad = params_dropped = dups = 0
    folder_flag: dict[str, bool] = {}
    with imp.Book(data, filename) as bk:
        for rno, row in bk.rows(sheet, start_row, end_row):
            if all(get(row, k) is None for k in idx):
                continue
            name = get(row, "name")
            if name is None:
                res.skipped.append(dict(row=rno, reason=_("imp_skip_empty", f=_("cat_f_name"))))
                continue
            if len(recs) >= MAX_CATALOG_ROWS:
                raise ValueError(_("imp_too_many_rows", n=MAX_CATALOG_ROWS))
            code = imp.cell_text(get(row, "code", "")).strip()[:100]
            base_id = imp.cell_text(get(row, "id", "")).strip() or code or f"row{rno}"
            rid = (pfx + base_id)[:64]
            parent = imp.cell_text(get(row, "parent_id", "")).strip()
            parent_id = (pfx + parent)[:64] if parent else None
            kind = imp.cell_text(get(row, "kind", "")).strip().lower()
            rec = dict(id=rid, parent_id=parent_id, kind=kind if kind in KINDS else "", code=code,
                       name=imp.cell_text(name).strip()[:300], unit=imp.cell_text(get(row, "unit", "")).strip()[:20],
                       price=num(row, "price") or 0, stock=num(row, "stock") or 0, thickness=num(row, "thickness"),
                       length=num(row, "length"), width=num(row, "width"))
            if "size" in idx:                      # «Размер»: alohida ustun qiymati ustun, bo'sh bo'lsa — shu katakdan
                sl, sw, st = parse_size(get(row, "size"))
                for key, val in (("length", sl), ("width", sw), ("thickness", st)):
                    if rec[key] is None and val is not None:
                        rec[key] = val
            if "params" in idx:                    # ustun ko'rsatilmasa — mavjud qatorning parametrlariga tegilmaydi
                rec["params"], dr = parse_params(get(row, "params"))
                params_dropped += dr
            if "image" in idx and get(row, "image") is not None:
                try:
                    res.images[rid] = normalize_image(imp.cell_text(get(row, "image")))
                except ValueError:
                    img_bad += 1
            if "isfolder" in idx:
                folder_flag[rid] = imp.cell_text(get(row, "isfolder", "")).strip().lower() in imp.TRUE
            if rid in recs:
                dups += 1
            recs[rid] = rec
    if img_bad:
        res.warnings.append(_("cat_image_skipped", n=img_bad))
    if params_dropped:
        res.warnings.append(_("cat_params_dropped", n=params_dropped))
    if dups:
        res.warnings.append(_("cat_dup_ids", n=dups))
    res.images = {k: v for k, v in res.images.items() if k in recs}

    # Papka belgisi: ustun bo'lsa — shu; bo'lmasa — ota bo'lgan qator papka
    has_children = {r["parent_id"] for r in recs.values() if r["parent_id"]}
    for rid, r in recs.items():
        is_folder = folder_flag.get(rid, False) if "isfolder" in idx else rid in has_children
        if is_folder:
            r["kind"] = FOLDER
    # Siklni (o'z-o'ziga ota, A→B→A) uzish
    cyc = 0
    for rid, r in recs.items():
        seen, cur = {rid}, r["parent_id"]
        while cur is not None:
            if cur in seen:
                r["parent_id"] = None
                cyc += 1
                break
            seen.add(cur)
            cur = recs[cur]["parent_id"] if cur in recs else None
    if cyc:
        res.warnings.append(_("cat_cycle", n=cyc))
    # Tur: aniq `kind` ustuni > ildiz kategoriya > standart
    root_kind = {pfx + str(v).strip(): k for k, v in (roots or {}).items() if k in KINDS and str(v).strip() != ""}
    for r in recs.values():
        if r["kind"] == FOLDER:
            continue
        if not r["kind"]:
            cur, depth, found = r["parent_id"], 0, None
            while cur is not None and depth < 64:
                if cur in root_kind:
                    found = root_kind[cur]
                    break
                cur = recs[cur]["parent_id"] if cur in recs else None
                depth += 1
            r["kind"] = found or default_kind
    res.rows = list(recs.values())
    res.folders = sum(1 for r in res.rows if r["kind"] == FOLDER)
    res.items = len(res.rows) - res.folders
    return res


# ───────────────────────── Qidiruv / daraxt ─────────────────────────
_NAT = re.compile(r"(\d+)")


def natural_key(s: str):
    """Tabiiy tartib: «ДСП 10 мм» < «ДСП 16 мм» < «ДСП 100 мм»."""
    return [(0, int(t)) if t.isdigit() else (1, t) for t in _NAT.split((s or "").casefold()) if t != ""]


def exact_fold(col, text: str):
    """Ustun == matn (katta-kichik harf va chekka bo'sh joylarga sezgirsiz)."""
    key = (text or "").strip().casefold()
    return (func.mx_fold(col) if IS_SQLITE else func.lower(col)) == key


def find_item(kind: str, text: str) -> CatalogItemRow | None:
    """Material nomi yoki kodi bo'yicha aniq mos katalog qatori (avto CS yaratishda)."""
    if not (text or "").strip():
        return None
    with SessionLocal() as s:
        st = select(CatalogItemRow).where(CatalogItemRow.kind == kind,
                                          or_(exact_fold(CatalogItemRow.code, text), exact_fold(CatalogItemRow.name, text)))
        return s.scalars(st.order_by(CatalogItemRow.name).limit(1)).first()


def item_dict(r: CatalogItemRow) -> dict:
    return dict(id=r.id, parent_id=r.parent_id, kind=r.kind, code=r.code, name=r.name, unit=r.unit, price=r.price,
                stock=r.stock, thickness=r.thickness, length=r.length, width=r.width, params=r.params or {},
                has_image=bool(r.has_image))


def _folders(s) -> dict[str, dict]:
    rows = s.execute(select(CatalogItemRow.id, CatalogItemRow.parent_id, CatalogItemRow.name, CatalogItemRow.code)
                     .where(CatalogItemRow.kind == FOLDER)).all()
    return {r.id: dict(id=r.id, parent_id=r.parent_id, name=r.name, code=r.code or "") for r in rows}


def descendant_folders(s, root_id: str, folders: dict[str, dict] | None = None) -> list[str]:
    """Papka va uning ichki papkalari (siklga chidamli)."""
    folders = _folders(s) if folders is None else folders
    kids: dict[str, list[str]] = {}
    for f in folders.values():
        if f["parent_id"]:
            kids.setdefault(f["parent_id"], []).append(f["id"])
    out, stack = [], [root_id]
    seen = set()
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        out.append(cur)
        stack.extend(kids.get(cur, []))
    return out


def query_items(kind: str | None = None, parent_id: str | None = None, q: str = "", limit: int = 500, *,
                recursive: bool = False, unfiled: bool = False, folders: bool = True) -> list[dict]:
    """Tekis ro'yxat. `parent_id=""` — ildiz (ota yo'q); `recursive` — ichki papkalar ostidagilar ham; `unfiled` —
    papkasiz materiallar; `folders=False` — papkalar kiritilmaydi."""
    limit = max(1, min(int(limit), 5000))
    with SessionLocal() as s:
        st = select(CatalogItemRow)
        if kind:
            st = st.where(CatalogItemRow.kind == kind)
        if not folders:
            st = st.where(CatalogItemRow.kind != FOLDER)
        if unfiled:
            fids = select(CatalogItemRow.id).where(CatalogItemRow.kind == FOLDER)
            st = st.where(CatalogItemRow.kind != FOLDER,
                          or_(CatalogItemRow.parent_id.is_(None), CatalogItemRow.parent_id.not_in(fids)))
        post: set[str] | None = None
        if parent_id is not None and not unfiled:
            if recursive and parent_id:
                ids = descendant_folders(s, parent_id)
                if len(ids) <= 500:
                    st = st.where(CatalogItemRow.parent_id.in_(ids))
                else:
                    post = set(ids)
            else:
                st = st.where(CatalogItemRow.parent_id == (parent_id or None))
        cond = text_search(q, CatalogItemRow.name, CatalogItemRow.code)
        if cond is not None:
            st = st.where(cond)
        st = st.order_by(CatalogItemRow.name)
        if post is None:
            return [item_dict(r) for r in s.scalars(st.limit(limit)).all()]
        out = []
        for r in s.scalars(st.execution_options(yield_per=500)):
            if r.parent_id in post:
                out.append(item_dict(r))
                if len(out) >= limit:
                    break
        return out


def folder_tree(kind: str | None = None, q: str = "", with_items: bool = False, item_limit: int = 2000,
                root: str | None = None) -> dict:
    """Kategoriyalar daraxti: `{nodes: [{id, parent_id, name, code, kind: "folder", count, children}], total, unfiled}`.
    `count` — papka ostidagi (ichki papkalar bilan) mos materiallar soni; `kind` (tur) yoki `q` (qidiruv) berilsa mos
    material bo'lmagan papkalar tushirib qoldiriladi. `with_items` — materiallar ham barg sifatida (≤ item_limit).
    `root` — faqat shu papka (ichki daraxti bilan). Sikl va juda chuqur zanjirlarga chidamli (rekursiyasiz)."""
    q = (q or "").strip()
    with SessionLocal() as s:
        fmap = _folders(s)
        st = select(CatalogItemRow.id, CatalogItemRow.parent_id).where(CatalogItemRow.kind != FOLDER)
        if kind:
            st = st.where(CatalogItemRow.kind == kind)
        cond = text_search(q, CatalogItemRow.name, CatalogItemRow.code)
        if cond is not None:
            st = st.where(cond)
        direct: dict[str, int] = {}
        total = unfiled = 0
        for r in s.execute(st):
            total += 1
            if r.parent_id in fmap:
                direct[r.parent_id] = direct.get(r.parent_id, 0) + 1
            else:
                unfiled += 1
        # ota xaritasi: mavjud bo'lmagan / o'zi / sikl hosil qiluvchi ota — ildiz
        parent = {fid: (f["parent_id"] if f["parent_id"] in fmap and f["parent_id"] != fid else None)
                  for fid, f in fmap.items()}
        for fid in fmap:
            seen, cur = {fid}, parent[fid]
            while cur is not None:
                if cur in seen or len(seen) > MAX_TREE_DEPTH:      # sikl yoki g'ayritabiiy chuqur zanjir (JSON ichma-ichligi)
                    parent[fid] = None
                    break
                seen.add(cur)
                cur = parent[cur]
        nodes = {fid: dict(f, kind=FOLDER, count=direct.get(fid, 0), children=[]) for fid, f in fmap.items()}
        roots: list[dict] = []
        for fid, n in nodes.items():
            (nodes[parent[fid]]["children"] if parent[fid] else roots).append(n)
        # oldindan tartib (ota bolalardan oldin) → teskari yurib hisoblash: bola ota'dan oldin tugaydi
        order: list[dict] = []
        stack = list(roots)
        while stack:
            n = stack.pop()
            order.append(n)
            stack.extend(n["children"])
        prune = bool(kind or q)
        for n in reversed(order):
            n["count"] += sum(c["count"] for c in n["children"])
            if prune:
                n["children"] = [c for c in n["children"] if c["count"] > 0]
        if prune:
            roots = [r for r in roots if r["count"] > 0]
        key = lambda n: natural_key(n["name"])  # noqa: E731
        roots.sort(key=key)
        for n in order:
            n["children"].sort(key=key)
        if root:
            sub = nodes.get(root)
            roots = [sub] if sub is not None and (not prune or sub["count"] > 0) else []
        if with_items:
            keep = {n["id"]: n for n in _walk(roots)}
            ist = select(CatalogItemRow).where(CatalogItemRow.kind != FOLDER)
            ist = ist.where(CatalogItemRow.parent_id.in_(list(keep))) if len(keep) <= 500 \
                else ist.where(CatalogItemRow.parent_id.is_not(None))
            if kind:
                ist = ist.where(CatalogItemRow.kind == kind)
            if cond is not None:
                ist = ist.where(cond)
            n_items = 0
            for r in s.scalars(ist.order_by(CatalogItemRow.name)):
                if r.parent_id in keep:
                    keep[r.parent_id]["children"].append(dict(item_dict(r), children=[]))
                    n_items += 1
                    if n_items >= max(1, item_limit):
                        break
    return dict(nodes=roots, total=total, unfiled=unfiled)


def _walk(nodes: list[dict]):
    """Daraxtdagi papka tugunlari (rekursiyasiz)."""
    stack = list(nodes)
    while stack:
        n = stack.pop()
        if n.get("kind") == FOLDER:
            yield n
            stack.extend(n["children"])