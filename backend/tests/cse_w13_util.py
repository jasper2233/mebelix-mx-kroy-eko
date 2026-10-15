"""W13 (CSE) testlari uchun umumiy yordamchilar: loyiha yaratish, daraxt qurish, qo'lda tahrir amalini yuborish va
natijani mustaqil tekshirish (validate + zona + hisoblagichlar)."""
from __future__ import annotations

import copy
import json
from collections import Counter

from app import store
from app.models import CuttingResult
from app.services import calc
from app.services.optimizer import _zone
from app.services.validate import map_stock, validate

TOL = 0.011


# ───────────────────────── daraxt qurish (kesish daraxti JSON ko'rinishida) ─────────────────────────
def P(x, y, l, w, u, o=0):
    d = {"x": x, "y": y, "l": l, "w": w, "k": "P", "u": u}
    if o:
        d["o"] = 1
    return d


def W(x, y, l, w):
    return {"x": x, "y": y, "l": l, "w": w, "k": "W"}


def C(x, y, l, w, axis, kids, g=None):
    d = {"x": x, "y": y, "l": l, "w": w, "k": "C", "a": axis, "c": list(kids)}
    if g is not None:
        d["g"] = g
    return d


def nodes(root, pred, path=()):
    """Daraxtdan shartga mos hamma tugunlar: [(manzil, tugun)] (hujjat tartibida)."""
    out = []
    if pred(root):
        out.append((list(path), root))
    for i, c in enumerate(root.get("c", [])):
        out += nodes(c, pred, path + (i,))
    return out


def leaves_p(root):
    return nodes(root, lambda n: n["k"] == "P")


def node_at(root, path):
    n = root
    for i in path:
        n = n["c"][i]
    return n


# ───────────────────────── loyiha ─────────────────────────
def op_of(p, oid):
    return next(o for o in p["operations"] if o["id"] == oid)


def make_project(client, parts, cut=None, group=None):
    """CS loyiha: `parts` — [(L, W, qty[, grain])]; `cut` — cs_cut qismi (standart: torsovka 0, propil 3, burilish 6);
    `group` — {uid: dict(group_by=…, group_max=…)}. Qaytaradi (pid, cs_id, sheet)."""
    p = client.post("/api/projects", json={"name": "CSE W13"}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LDSP16", "name": "LDSP"}).json()
    cs = p["operations"][-1]["id"]
    base = {"kerf": 3, "trim_length": 0, "trim_width": 0, "min_trim_cut": 5, "max_rotations": 6, "quality": "fast"}
    base.update(cut or {})
    r = client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": base})
    assert r.status_code == 200, r.text
    rows = []
    for t in parts:
        L, Wd, q = t[0], t[1], t[2]
        grain = t[3] if len(t) > 3 else False
        rows.append(dict(name=f"D{len(rows) + 1}", length=L, width=Wd, qty=q, grain=grain))
    r = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=rows)
    assert r.status_code == 200, r.text
    p = client.get(f"/api/projects/{pid}").json()
    op = op_of(p, cs)
    if group:
        ups = [{"id": next(x for x in op["parts"] if x["uid"] == uid)["id"], "fields": f} for uid, f in group.items()]
        r = client.post(f"/api/projects/{pid}/operations/{cs}/parts/batch-update", json=ups)
        assert r.status_code == 200, r.text
        op = op_of(client.get(f"/api/projects/{pid}").json(), cs)
    return pid, cs, op["sheets"][0]


def card(sheet, tree, copies=1):
    """Bitta kartali qoralama natija (faqat daraxt — qolganini server qayta quradi)."""
    return {"maps": [{"index": 1, "sheet_id": sheet["id"], "sheet_length": sheet["length"],
                      "sheet_width": sheet["width"], "copies": copies, "strips": [tree]}]}


def blank(client, pid, cs, sheet, axis="y"):
    """Bo'sh karta (bitta katta chiqindi)."""
    return ok(client, pid, cs, {"maps": []}, type="add_map", sheet_id=sheet["id"], axis=axis)


# ───────────────────────── tahrir amali ─────────────────────────
def edit(client, pid, cs, res, **action):
    return client.post(f"/api/projects/{pid}/operations/{cs}/edit", json={"result": res, "action": action})


def ok(client, pid, cs, res, **action):
    r = edit(client, pid, cs, res, **action)
    assert r.status_code == 200, (action, r.status_code, r.text[:300])
    out = r.json()
    check(pid, cs, out)
    return out


def bad(client, pid, cs, res, **action):
    """Amal rad etilishi kerak: 4xx (500 emas); detail matnini qaytaradi."""
    r = edit(client, pid, cs, res, **action)
    assert 400 <= r.status_code < 500, (action, r.status_code, r.text[:300])
    return r.json().get("detail", "")


# ───────────────────────── mustaqil tekshiruv ─────────────────────────
def check(pid, cs, res_json, expect_manual=True):
    """Natijani serverdan mustaqil tekshiradi: validate() = 0 xato; har detal listning foydali zonasida; daraxt barglari
    = joylashuvlar; hisoblagichlar izchil. CuttingResult qaytaradi."""
    p = store.load(pid)
    op = store.op_of(p, cs)
    res = res_json if isinstance(res_json, CuttingResult) else CuttingResult.model_validate(res_json)
    return check_model(p, op, res, expect_manual)


def check_model(p, op, res, expect_manual=True):
    cut = op.cs_cut
    errs = validate(res, calc._items_for(p, op, cut), op.sheets, cut)
    assert not errs, errs
    stock = {s.id: s for s in op.sheets}
    for i, m in enumerate(res.maps, 1):
        assert m.index == i
        z = _zone(map_stock(stock[m.sheet_id], m), cut)
        for pl in m.placements:
            assert pl.x >= z.ox - TOL and pl.y >= z.oy - TOL, (i, pl)
            assert pl.x + pl.length <= z.ox + z.UL + TOL and pl.y + pl.width <= z.oy + z.UW + TOL, (i, pl, z)
        n_leaf = len(leaves_p(m.strips[0])) if m.strips else 0
        assert n_leaf == len(m.placements) == m.parts_count
        assert m.copies >= 1
    assert res.total_sheets == sum(m.copies for m in res.maps)
    assert res.total_parts == sum(m.parts_count * m.copies for m in res.maps)
    placed = Counter()
    for m in res.maps:
        for pl in m.placements:
            placed[pl.part_id] += m.copies
    need = {pt.id: calc.effective_qty(p, pt) for pt in op.parts}
    for pid_, n in placed.items():
        assert n <= need[pid_]
    assert sum(need.values()) - sum(placed.values()) == len(res.unplaced)
    if expect_manual:
        assert res.manual
    return res


def uid_count(res_json, uid):
    return sum(m["copies"] for m in res_json["maps"] for pl in m["placements"] if pl["part_uid"] == uid)


def deep(x):
    return copy.deepcopy(x)


def raw_post(client, url, payload):
    """Qo'lda JSON (NaN/Infinity tokenlari uchun)."""
    return client.post(url, content=payload if isinstance(payload, str) else json.dumps(payload),
                       headers={"Content-Type": "application/json"})
