"""W4 · LB: operatsiya parametrlari, qator manbalari (detal / qoldiq / mahsulot), sahifa maketi, shablon kutubxonasi, tekshiruv,
chegaralar (DoS), A4 da kroy kartalari miniatyurasi. Eski `/projects/{pid}/labels` (qat'iy QR etiketka) — test_api.py da."""
import json
import re
import time

import pytest

from app import store
from app.models import LBParams, Operation, OpType, Part, Product, Project
from app.services import barcode, label_builtin, label_print, label_vars, labels
from tests.conftest import KRAVAT


def _new_lb(client, pid, **lb):
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()
    oid = p["operations"][-1]["id"]
    if lb:
        r = client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": lb})
        assert r.status_code == 200, r.text
    return oid


def _html(client, pid, oid, **q):
    r = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels", params=q)
    assert r.status_code == 200, r.text
    return r.text


def _cut(client, kravat):
    pid, cs, el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    return pid, cs, el


def _count(html: str) -> int:
    return html.count("class='lbl'")


# ───────────────────────── operatsiya va parametrlar ─────────────────────────
def test_lb_operation_defaults_patch_and_validation(client, kravat):
    pid = kravat[0]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "LB"}).json()
    op = p["operations"][-1]
    assert op["type"] == "LB" and op["name"] == "Этикетки" and op["cost_material"] == 0 and op["cost_operation"] == 0
    lb = op["lb"]
    assert (lb["source"], lb["mode"], lb["width_mm"], lb["height_mm"], lb["columns"]) == ("parts", "sheet", 58, 40, 3)
    assert lb["print_parts"] and lb["part_each"] and lb["label_count"] == 1 and not lb["print_wastes"] and lb["template_id"] is None
    r = client.patch(f"/api/projects/{pid}/operations/{op['id']}", json={"lb": {"columns": 2, "gap_mm": 5, "margin_mm": None}}).json()
    got = r["operations"][-1]["lb"]
    assert got["columns"] == 2 and got["gap_mm"] == 5 and got["margin_mm"] is None and got["width_mm"] == 58     # qismiy yangilash
    for bad in ({"columns": 0}, {"columns": 21}, {"width_mm": 0}, {"width_mm": 501}, {"label_count": 0}, {"label_count": 21},
                {"rows": -1}, {"mode": "x"}, {"source": "x"}, {"template": {"elements": [{"t": "nope"}]}},
                {"template": {"size": {"w": 1, "h": 1}}}, {"template_id": "x" * 61}):
        assert client.patch(f"/api/projects/{pid}/operations/{op['id']}", json={"lb": bad}).status_code == 422, bad
    # klon va o'chirish ishlaydi
    assert client.post(f"/api/projects/{pid}/operations/{op['id']}/clone").status_code == 200
    assert client.delete(f"/api/projects/{pid}/operations/{op['id']}").status_code == 200


def test_lb_defaults_scope_saves_params_but_not_selection(client, kravat):
    pid = kravat[0]
    saved = client.put("/api/settings/lb_defaults/default", json={
        "width_mm": 70, "height_mm": 50, "columns": 2, "part_selected": [1, 2], "cs_op_id": "zz",
        "template": {"elements": []}, "template_id": "builtin:detail_c128", "data": [{"a": 1}]})
    assert saved.status_code == 200
    d = client.get("/api/settings/lb_defaults/default").json()
    assert d["width_mm"] == 70 and d["template_id"] == "builtin:detail_c128"
    assert d["part_selected"] == [] and d["cs_op_id"] is None and d["template"] is None and d["data"] == []
    oid = _new_lb(client, pid)
    lb = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == oid)["lb"]
    assert (lb["width_mm"], lb["columns"], lb["template_id"]) == (70, 2, "builtin:detail_c128")
    pr = client.get("/api/settings/lb_defaults").json()
    for x in pr:
        client.delete(f"/api/settings/lb_defaults/{x['id']}")
    assert client.get("/api/settings/lb_defaults/default").json()["width_mm"] == 58


# ───────────────────────── qatorlar manbalari ─────────────────────────
def test_default_lb_labels_cover_every_piece_with_mes_codes(client, kravat):
    pid, cs, el = _cut(client, kravat)
    oid = _new_lb(client, pid)
    html = _html(client, pid, oid)
    assert _count(html) == 19 and "MXK:" not in html                    # 19 dona; QR — rasm (yo'l), matn emas
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows").json()
    assert rows["total"] == 19 and len(rows["rows"]) == 19
    num = client.get(f"/api/projects/{pid}").json()["number"]
    qty = {u: q for u, _l, _w, q in KRAVAT}
    want = {f"MXK:{num}:{u}:{i}/{q}" for u, q in qty.items() for i in range(1, q + 1)}
    codes = [r["code"] for r in rows["rows"]]
    assert set(codes) == want and len(codes) == len(set(codes))         # har etiketka noyob; MES skaneri o'qiydigan format
    assert [r["number"] for r in rows["rows"]] == list(range(1, 20))
    assert all(labels.parse_qr(c) for c in codes)
    # birinchi etiketkaning QR i HTML da (yo'l sifatida) bor
    _n, d = barcode.qr_cells(codes[0], "m", False)
    assert d in html
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 19


def test_part_flags_selection_and_label_count(client, kravat):
    pid, cs, el = _cut(client, kravat)
    oid = _new_lb(client, pid)

    def total(**lb):
        client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": lb})
        n = client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"]
        assert _count(_html(client, pid, oid)) == n                       # sanash va chop bir xil
        return n
    assert total(part_each=False) == 14                                   # har detalga bitta
    assert total(part_each=True) == 19
    assert total(part_selected=[2, 5]) == 4                               # uid 2 va 5: 2 + 2 dona
    assert total(part_selected=[]) == 19
    assert total(label_count=3) == 57                                     # bir nusxaga 3 etiketka
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows").json()["rows"]
    assert [r["label_index"] for r in rows[:6]] == [1, 2, 3, 1, 2, 3] and all(r["label_count"] == 3 for r in rows)
    assert len({r["code"] for r in rows}) == 19                           # bir nusxaning 3 etiketkasi — bir xil QR (bitta jism)
    assert total(label_count=1, print_parts=False) == 0
    assert "Нет этикеток" in _html(client, pid, oid)
    assert total(print_parts=True, cs_op_id="yo'q") == 0                  # noma'lum CS — bo'sh, xato emas
    assert total(cs_op_id=cs) == 19


def test_without_cut_result_parts_follow_list_order(client, kravat):
    pid, cs, el = kravat
    oid = _new_lb(client, pid)
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows").json()["rows"]
    assert len(rows) == 19 and [r["part_uid"] for r in rows][:4] == [1, 2, 2, 3]


def test_zero_quantity_parts(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    first = next(o for o in p["operations"] if o["id"] == cs)["parts"][0]
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{first['id']}", json={"qty": 0})
    oid = _new_lb(client, pid)
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 18         # soni 0 — chiqmaydi
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"part_only_nonzero": False, "part_each": False}})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 14         # «bitta qatorga» rejimida qoladi
    assert len(client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows").json()["rows"]) == 14


def test_waste_labels_follow_cut_result(client, kravat):
    pid, cs, el = _cut(client, kravat)
    p = client.get(f"/api/projects/{pid}").json()
    res = next(o for o in p["operations"] if o["id"] == cs)["result"]
    rem = [(m["copies"], o) for m in res["maps"] for o in m["offcuts"] if o["kind"] == "remnant"]
    assert rem, "kroyda qoldiq bo'lishi kerak"
    oid = _new_lb(client, pid, source="parts", print_parts=False, print_wastes=True)
    want_each = sum(c for c, _o in rem)
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json() == dict(
        total=want_each, parts=0, wastes=want_each, products=0, user=0)
    html = _html(client, pid, oid, lang="uz")
    assert _count(html) == want_each and "#ERR" not in html and ">Д2<" in html          # standart shablon qoldiq qatorini ham chiqaradi
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows").json()["rows"]
    assert {r["kind"] for r in rows} == {"waste"} and all(labels.parse_qr(r["code"])["kind"] == "map" for r in rows)
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"waste_each": False}})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["wastes"] == len(rem)
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"waste_each": True, "waste_business_only": True}})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["wastes"] == sum(c for c, o in rem if o["business"])
    # qoldiq + detal bir chopda
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"print_parts": True, "waste_business_only": False}})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 19 + want_each


def test_product_labels(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    prid = p["products"][0]["id"]
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 3, "name": "Shkaf <b>1</b>", "code": "SH-1"})
    client.post(f"/api/projects/{pid}/products", json={"name": "Nol", "qty": 0})
    oid = _new_lb(client, pid, source="products", template_id="builtin:product", width_mm=100, height_mm=60)
    cnt = client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()
    assert cnt["products"] == 1 + 0 and cnt["total"] == 1                  # product_each=False: har mahsulotga bitta; soni 0 — o'tkazilmaydi
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"product_each": True}})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 3
    html = _html(client, pid, oid)
    assert _count(html) == 3 and "Shkaf &lt;b&gt;1&lt;/b&gt;" in html and "<b>1</b>" not in html and "Кол-во: 1 / 3" in html
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"product_only_nonzero": False}})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 3 + 1


def test_user_rows_source(client, kravat):
    pid = kravat[0]
    oid = _new_lb(client, pid, source="user", fields=[{"name": "title", "type": "string"}, {"name": "qty", "type": "integer"}],
                  data=[{"title": "A", "qty": 2}, {"title": "B", "qty": 1}, {"title": "C", "qty": 0}],
                  template={"v": 1, "size": {"w": 58, "h": 40}, "elements": [{"t": "text", "x": 2, "y": 2, "text": "user.title"}]})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["user"] == 3
    html = _html(client, pid, oid)
    assert _count(html) == 3 and html.count(">A<") == 2 and ">B<" in html and ">C<" not in html


# ───────────────────────── sahifa maketi ─────────────────────────
def test_sheet_and_roll_layout(client, kravat):
    pid, cs, el = _cut(client, kravat)
    oid = _new_lb(client, pid)
    h = _html(client, pid, oid)
    assert "repeat(3,58mm)" in h and "@page{size:210mm 297mm;margin:6mm}" in h and "grid-auto-rows:40mm;gap:2mm" in h
    assert h.count("class='pg'") == 2                                       # 3 ustun × 6 qator = 18 / sahifa → 19 etiketka = 2 sahifa
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"rows": 2, "columns": 2, "gap_mm": 10, "margin_mm": 10}})
    h = _html(client, pid, oid)
    assert h.count("class='pg'") == 5 and "margin:10mm" in h and "repeat(2,58mm)" in h      # 19 / 4 = 5 sahifa
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"rotate_page": 90, "rows": 0, "columns": 4, "margin_mm": None}})
    h = _html(client, pid, oid)
    assert "size:297mm 210mm;margin:0mm" in h and "repeat(4,58mm)" in h
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"mode": "roll", "rotate_page": 0}})
    h = _html(client, pid, oid)
    assert "@page{size:58mm 40mm;margin:0}" in h and h.count("class='pg'") == 19 and _count(h) == 19
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"rotate_page": 90}})
    h = _html(client, pid, oid)
    assert "@page{size:40mm 58mm;margin:0}" in h and h.count("class='rot'") == 19
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"border": False}})
    assert "border:none" in _html(client, pid, oid)


def test_overflow_warnings(client, kravat):
    pid, cs, el = _cut(client, kravat)
    oid = _new_lb(client, pid, width_mm=100, columns=3)
    r = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"width_mm": 100, "columns": 3}}).json()
    assert any("3" in w and "1" in w for w in r["warnings"])                # 3 ustun, sahifaga (210 − 12 mm) faqat 1 ta sig'adi
    r = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"height_mm": 300, "columns": 1}}).json()
    assert r["warnings"]                                                    # A4 balandligidan katta etiketka
    r = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"columns": 3}}).json()
    assert r["warnings"] == []


# ───────────────────────── ko'rish va xatolar ─────────────────────────
def test_preview_reports_errors_before_printing(client, kravat):
    pid, cs, el = _cut(client, kravat)
    bad = {"v": 1, "size": {"w": 58, "h": 40}, "elements": [
        {"t": "text", "x": 1, "y": 1, "text": "part.name"}, {"t": "text", "x": 1, "y": "1/0", "text": "'q'"},
        {"t": "text", "x": "ghost", "y": 3, "text": "'w'"}]}
    lb = {"template": bad, "columns": 3}
    r = client.post(f"/api/projects/{pid}/lb/preview?lang=uz", json={"lb": lb}).json()
    assert r["total"] == 19 and r["rendered"] == 6 and r["truncated"] and r["template"] == "embedded"
    assert {(e["path"], e["field"]) for e in r["errors"]} == {("2", "y"), ("3", "x")}
    assert all(e["count"] >= 6 for e in r["errors"]) and "o'zgaruvchi" in next(e for e in r["errors"] if e["path"] == "3")["message"]
    assert "#ERR 2" in r["html"] and "class='errs'" not in r["html"] and r["html"].count("class='lbl'") == 6    # ko'rishda xatolar alohida ro'yxatda
    # xato faqat birinchi 6 tada emas, undan keyingilarida ham topiladi (scan)
    bad2 = {"v": 1, "elements": [{"t": "text", "x": 1, "y": 1, "text": "if(part.id > 13, 1/0, 'x')"}]}
    r = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"template": bad2}}).json()
    assert [e["path"] for e in r["errors"]] == ["1"]
    # chop sahifasi xatoga qaramay chiqadi (qizil belgi bilan), ekranda banner
    oid = _new_lb(client, pid, template=bad)
    h = _html(client, pid, oid)
    assert _count(h) == 19 and "#ERR" in h and "@media print{.errs{display:none}}" in h
    assert "class='errs'" in h and "деление на ноль" in h                  # chop sahifasida ekran uchun banner (chopda yashirin)


def test_template_resolution_and_missing_template_warning(client, kravat):
    pid, cs, el = _cut(client, kravat)
    r = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"template_id": "builtin:detail_c128"}}).json()
    assert r["template"] == "builtin:detail_c128" and "Code128" in r["template_name"] and not r["errors"]
    r = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"template_id": "profile:99999"}}).json()
    assert r["template"] == "builtin:detail" and r["warnings"] and not r["errors"]       # standartga qaytadi, ogohlantirish bilan
    r = client.post(f"/api/projects/{pid}/lb/preview?lang=uz", json={"lb": {"template_id": "builtin:nope"}}).json()
    assert r["template"] == "builtin:detail" and "topilmadi" in r["warnings"][0]


def test_code128_template_prints_1d_barcode(client, kravat):
    pid, cs, el = _cut(client, kravat)
    oid = _new_lb(client, pid, template_id="builtin:detail_c128")
    h = _html(client, pid, oid)
    num = client.get(f"/api/projects/{pid}").json()["number"]
    assert _count(h) == 19 and "MXK:" not in h
    # har etiketkada: loyiha № + detal ID (oxirgi 4) + hisoblagich (4) — matn sifatida va chiziqlar sifatida
    assert f">{num}00010001<" in h
    w = barcode.code128_widths(f"{num}00010001")
    d = barcode.code128_group(f"{num}00010001", 0, 0, 54.8, 10.5, caption=True)[0]          # shablon: eni 58 − 2·1.6, balandligi 10.5
    assert re.search(r' d="([^"]+)"', d).group(1)[:30] in h                  # bir xil chiziqlar yo'li (shablon ham shu kodlashdan foydalanadi)
    assert len(w) > 20


def test_security_headers_and_injection(client):
    p = client.post("/api/projects", json={"name": "<script>alert(1)</script>"}).json()
    pid = p["id"]
    cs = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "X", "name": "\"><img src=x onerror=alert(1)>"}).json()["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{"name": "<svg onload=alert(2)>", "length": 500, "width": 300, "qty": 1}])
    oid = _new_lb(client, pid)
    r = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels")
    assert "default-src 'none'" in r.headers["content-security-policy"] and r.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in r.text                                      # meta CSP ham bor
    body = r.text
    assert "<script" not in body and "<img" not in body and "<svg onload" not in body
    assert "&lt;script&gt;" in body and "&lt;svg onload=alert(2)&gt;" in body
    # ko'rish API si ham (HTML JSON ichida) shunday
    j = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {}}).json()
    assert "<script" not in j["html"] and "<img" not in j["html"]


# ───────────────────────── chegaralar (DoS) ─────────────────────────
def test_label_limit_and_cheap_counting(client, kravat):
    pid, cs, el = kravat
    p = client.get(f"/api/projects/{pid}").json()
    big = next(o for o in p["operations"] if o["id"] == cs)["parts"][0]
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{big['id']}", json={"qty": 100000})
    prid = p["products"][0]["id"]
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 100000})        # 10^10 dona
    oid = _new_lb(client, pid)
    t = time.perf_counter()
    cnt = client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()
    assert cnt["total"] >= 10 ** 10 and time.perf_counter() - t < 2                   # sanash arifmetika bilan
    r = client.get(f"/api/projects/{pid}/operations/{oid}/lb/labels")
    assert r.status_code == 422 and "10000" in r.json()["detail"]
    t = time.perf_counter()
    j = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {}}).json()       # ko'rish — faqat birinchi etiketkalar
    assert j["rendered"] == 6 and j["total"] >= 10 ** 10 and j["truncated"] and time.perf_counter() - t < 5
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows", params={"limit": 50}).json()
    assert len(rows["rows"]) == 50
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/rows", params={"limit": 5000}).status_code == 422
    # 10 000 ning o'zida — chiqadi (chegara — oshganda)
    client.patch(f"/api/projects/{pid}/products/{prid}", json={"qty": 1})
    client.patch(f"/api/projects/{pid}/operations/{cs}/parts/{big['id']}", json={"qty": 10000 - 18})
    assert client.get(f"/api/projects/{pid}/operations/{oid}/lb/count").json()["total"] == 10000


def _synthetic(n_parts: int, qty: int) -> Project:
    from app.models import CSCutParams, CSMaterialParams
    prod = Product(name="Shkaf", code="SH", qty=1)
    op = Operation(type=OpType.CS, code="LDSP", name="LDSP 16", cs_material=CSMaterialParams(), cs_cut=CSCutParams(),
                   parts=[Part(uid=i + 1, name=f"Panel {i + 1}", length=500 + i, width=300 + i, qty=qty, product_id=prod.id)
                          for i in range(n_parts)])
    return Project(number=1000123, name="Bench", operations=[op], products=[prod])


def test_performance_10000_labels_30_expressions():
    """DoS maqsadi: 10 000 etiketka × 30 ifoda ≈ 3 s (bu yerda yuklama o'zgarishiga yo'l qo'yib 3× zaxira bilan tekshiriladi)."""
    tpl = {"v": 1, "name": "bench", "size": {"w": 58, "h": 40}, "elements": [
        {"t": "text", "x": 2, "y": f"{i}*1.2", "size": 2, "text": "left(part.name,10)+' '+part.id"} for i in range(30)]}
    pr = _synthetic(100, 100)
    t0 = time.perf_counter()
    res = label_print.render_labels(pr, LBParams(template=tpl), lang="ru")
    dt = time.perf_counter() - t0
    assert res.total == 10000 and res.rendered == 10000 and not res.errors and res.html.count("class='lbl'") == 10000
    assert dt < 9, f"{dt:.1f}s"
    # ichma-ich: Code128 + QR bilan standart shablonlar ham 10 000 ta uchun bir necha soniyada
    for key in ("detail", "detail_c128"):
        t0 = time.perf_counter()
        res = label_print.render_labels(pr, LBParams(template_id=f"builtin:{key}"), lang="ru")
        assert res.total == 10000 and not res.errors
        assert time.perf_counter() - t0 < 20


# ───────────────────────── o'zgaruvchilar provayderi ─────────────────────────
def test_env_keys_are_declared_and_aliases_agree():
    for kind in ("part", "waste", "product", "user"):
        env = label_vars.sample_env(kind)
        extra = {k for k in env if k not in label_vars.VAR_NAMES and not k.startswith("user.")}
        assert not extra, (kind, extra)
        assert label_vars.VAR_NAMES <= set(env)                                  # standart qiymatlar: hamma nom bor
    e = label_vars.sample_env("part")
    for alias, src in label_vars.ALIASES.items():
        if alias != "waste":
            assert e[alias] == e[src], (alias, src)
    assert e["ets"] == e["edge.top.symbol"] == "A" and e["els"] == "B" and e["edge.count"] == 2
    assert e["edge.top.thickness"] == 0.4 and e["edge.top.code"] == "PVC04/19" and e["edge.bottom.has"] is False
    assert e["part.dims"] == "748 × 468 × 16" and e["part.copy"] == 1 and e["part.copies"] == 2 and e["map.index"] == 3
    assert e["project.crc32"] == label_vars._crc(e["project.name"], "crc32") and isinstance(e["project.crc32"], int)
    w = label_vars.sample_env("waste")
    assert w["waste.number"] == 2 and w["waste.business"] and w["waste"] is True and w["part.name"] == "" and w["map.index"] == 3
    assert w["waste.area"] == 0.72 and w["label.code"] == "MXK:1000123:" + w["map.qr"].split(":")[2] + ":3"
    assert label_vars.sample_env("product")["label.code"].startswith("MXK:1000123:P1:")


def test_variable_catalog_and_functions_endpoint(client):
    j = client.get("/api/label-variables").json()
    names = {v["name"] for g in j["groups"] for v in g["vars"]}
    assert {"project.name", "part.qr", "edge.top.symbol", "map.index", "waste.number", "label.number", "part.counter"} <= names
    assert {g["key"] for g in j["groups"]} >= {"project", "product", "material", "part", "map", "waste", "label", "edge"}
    assert any(f["name"] == "rspace" for f in j["functions"]) and j["max_labels"] == 10000
    uz = client.get("/api/label-variables?lang=uz").json()
    assert next(v for g in uz["groups"] for v in g["vars"] if v["name"] == "project.name")["title"] == "Loyiha nomi"


# ───────────────────────── shablon kutubxonasi ─────────────────────────
def test_template_library_crud_check_preview_export_import(client, kravat):
    pid, cs, el = _cut(client, kravat)
    lst = client.get("/api/label-templates").json()
    ids = [x["id"] for x in lst]
    assert ids[:4] == ["builtin:detail", "builtin:detail_c128", "builtin:waste", "builtin:product"]
    assert all(x["builtin"] for x in lst[:4]) and lst[0]["params"][0]["name"] == "qr"
    uz = client.get("/api/label-templates?lang=uz").json()
    assert uz[0]["name"] != lst[0]["name"]
    # shablon olish
    t = client.get("/api/label-templates/builtin:detail_c128").json()
    assert t["builtin"] and t["template"]["elements"]
    assert client.get("/api/label-templates/builtin:zzz").status_code == 404
    assert client.get("/api/label-templates/profile:999999").status_code == 404
    # kutubxonaga yozish (sozlama profili)
    mine = json.loads(json.dumps(t["template"]))
    mine["name"] = "Mening shablonim"
    mine["elements"].append({"t": "text", "x": 1, "y": 36, "size": 2, "text": "'MARKER-X'"})
    r = client.post("/api/settings/label_template", json={"name": "Mening shablonim", "data": mine})
    assert r.status_code == 200, r.text
    prid = r.json()["id"]
    assert client.post("/api/settings/label_template", json={"name": "bad", "data": {"elements": [{"t": "zz"}]}}).status_code == 400
    lst = client.get("/api/label-templates").json()
    me = next(x for x in lst if x["id"] == f"profile:{prid}")
    assert me["name"] == "Mening shablonim" and not me["builtin"]
    got = client.get(f"/api/label-templates/profile:{prid}").json()
    assert got["template"]["elements"][-1]["text"] == "'MARKER-X'" and got["template"]["name"] == "Mening shablonim"
    # LB operatsiyasi kutubxonadan foydalanadi; loyiha ichidagi nusxa (template) undan ustun
    oid = _new_lb(client, pid, template_id=f"profile:{prid}")
    h = _html(client, pid, oid)
    assert h.count(">MARKER-X<") == 19
    client.patch(f"/api/projects/{pid}/operations/{oid}", json={"lb": {"template": {"elements": [{"t": "text", "x": 1, "y": 1, "text": "'LOCAL'"}]}}})
    h = _html(client, pid, oid)
    assert h.count(">LOCAL<") == 19 and "MARKER-X" not in h
    # eksport / import — aynan o'sha shablon
    ex = client.get(f"/api/label-templates/profile:{prid}/export")
    assert "attachment" in ex.headers["content-disposition"] and ex.headers["content-type"].startswith("application/json")
    imp = client.post("/api/label-templates/import?name=Import", content=ex.content, headers={"Content-Type": "application/json"})
    assert imp.status_code == 200 and imp.json()["errors"] == []
    kir = client.post("/api/settings/label_template", json={"name": "Деталь «Тест» 58×40", "data": mine}).json()["id"]    # kirill nom
    ex2 = client.get(f"/api/label-templates/profile:{kir}/export")
    assert ex2.status_code == 200 and "%D0%94%D0%B5%D1%82%D0%B0%D0%BB%D1%8C" in ex2.headers["content-disposition"]
    back = client.get(f"/api/label-templates/{imp.json()['id']}").json()["template"]
    assert back["elements"] == mine["elements"] and back["vars"] == mine["vars"] and back["params"] == mine["params"]
    assert client.post("/api/label-templates/import", json={"elements": [{"t": "bad"}]}).status_code == 422
    assert client.post("/api/label-templates/import", json=[1, 2]).status_code == 422
    # kutubxonadan boshqa loyihada ishlatish
    p2 = client.post("/api/projects", json={"name": "Boshqa"}).json()["id"]
    cs2 = client.post(f"/api/projects/{p2}/operations", json={"type": "CS", "name": "M"}).json()["operations"][-1]["id"]
    client.post(f"/api/projects/{p2}/operations/{cs2}/parts", json=[{"name": "q", "length": 100, "width": 50, "qty": 2}])
    o2 = _new_lb(client, p2, template_id=f"profile:{prid}")
    assert _html(client, p2, o2).count(">MARKER-X<") == 2
    # o'chirilsa — standartga qaytadi (ogohlantirish bilan), chop buzilmaydi
    assert client.delete(f"/api/settings/label_template/{prid}").json()["ok"]
    j = client.post(f"/api/projects/{pid}/lb/preview", json={"lb": {"template_id": f"profile:{prid}"}}).json()
    assert j["template"] == "builtin:detail" and j["warnings"]
    for x in client.get("/api/settings/label_template").json():
        client.delete(f"/api/settings/label_template/{x['id']}")


def test_template_check_and_preview_endpoints(client):
    t = {"v": 1, "size": {"w": 40, "h": 25}, "params": [{"name": "big", "type": "boolean", "default": False}],
         "elements": [{"t": "text", "x": 1, "y": 1, "size": "if(big, 6, 3)", "text": "part.name"}]}
    ok = client.post("/api/label-templates/check", json={"template": t}).json()
    assert ok == {"ok": True, "errors": [], "warnings": []}
    bad = client.post("/api/label-templates/check?lang=uz", json={"template": {"elements": [{"t": "text", "x": "(", "y": 1, "text": "x1"}]}}).json()
    assert not bad["ok"] and {e["field"] for e in bad["errors"]} >= {"x", "text"}
    assert not client.post("/api/label-templates/check", json={"template": {"size": {"w": 1, "h": 1}}}).json()["ok"]
    assert client.post("/api/label-templates/check", json={"template": t, "width_mm": -1}).status_code == 422
    pv = client.post("/api/label-templates/preview", json={"template": t, "params": {"big": True}, "width_mm": 40, "height_mm": 25}).json()
    assert pv["errors"] == [] and "@page{size:40mm 25mm;margin:0}" in pv["html"] and 'font-size="6"' in pv["html"]
    pv = client.post("/api/label-templates/preview", json={"template": {"elements": [{"t": "x"}]}}).json()
    assert pv["html"] == "" and pv["errors"]
    wp = client.post("/api/label-templates/preview", json={"template": label_builtin.builtin_template("waste"), "kind": "waste"}).json()
    assert wp["errors"] == [] and "Д2" in wp["html"]


# ───────────────────────── A4 da kroy kartalari miniatyurasi ─────────────────────────
def test_map_sheets_four_and_six_per_a4(client):
    p = client.post("/api/projects", json={"name": "Kartalar"}).json()
    pid = p["id"]
    cs = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L", "name": "LDSP"}).json()["operations"][-1]["id"]
    parts = [dict(name=f"P{i}", length=2700 - 10 * i, width=1800 - 10 * i, qty=1) for i in range(10)]       # har biri alohida list
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=parts)
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    maps = next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == cs)["result"]["maps"]
    n = len(maps)
    assert n >= 7
    r4 = client.get(f"/api/projects/{pid}/map-sheets", params={"per_page": 4})
    assert r4.status_code == 200 and "default-src 'none'" in r4.headers["content-security-policy"]
    assert r4.text.count("class='mc'") == n and r4.text.count("class='mp'") == -(-n // 4)
    assert "grid-auto-rows:95.0mm" in r4.text and "size:A4 landscape" in r4.text           # 4 — albom 2×2
    r6 = client.get(f"/api/projects/{pid}/map-sheets", params={"per_page": 6, "lang": "uz"})
    assert r6.text.count("class='mc'") == n and r6.text.count("class='mp'") == -(-n // 6) and "grid-auto-rows:91.0mm" in r6.text
    assert "Kroy kartalari" in r6.text and r6.text.count("<svg") >= n and "size:A4;" in r6.text      # 6 — kitob 2×3
    assert client.get(f"/api/projects/{pid}/map-sheets", params={"per_page": 5}).status_code == 422
    assert client.get(f"/api/projects/{pid}/map-sheets", params={"per_page": 4, "op_id": "yo'q"}).text.count("class='mc'") == 0
    # profil bilan: QR o'chirilgan
    prof = client.post("/api/settings/print", json={"name": "noqr", "data": {"map_qr": False}}).json()
    nq = client.get(f"/api/projects/{pid}/map-sheets", params={"per_page": 4, "profile_id": prof["id"]}).text
    assert len(nq) < len(r4.text) and nq.count("class='mc'") == n
    client.delete(f"/api/settings/print/{prof['id']}")


def test_map_sheets_empty_without_cut(client, kravat):
    pid = kravat[0]
    h = client.get(f"/api/projects/{pid}/map-sheets", params={"per_page": 4}).text
    assert "class='mc'" not in h and "Раскроить" in h


# ───────────────────────── eski etiketka tizimi buzilmagan ─────────────────────────
def test_legacy_labels_endpoint_unchanged(client, kravat):
    pid, cs, el = _cut(client, kravat)
    lb = client.get(f"/api/projects/{pid}/labels").text
    assert lb.count('class="lbl"') == 19 and "MXK:" not in lb
    assert "labels" in client.get("/api/settings").json()
    assert client.get("/api/settings/labels/default").json()["columns"] == 3
