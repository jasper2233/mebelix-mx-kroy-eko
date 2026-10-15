"""W13 / CSE: tasodifiy tahrir ketma-ketliklari (200 ta) — har muvaffaqiyatli amaldan keyin `validate()` 0 xato va
mustaqil invariantlar; rad etilgan amal holatni o'zgartirmaydi. Seed = ketma-ketlik raqami (xato — qayta ishlab chiqariladi).

Tahrir amallari to'g'ridan-to'g'ri `editor.apply` orqali (HTTP'siz, tez); API qatlami boshqa testlarda."""
import random
from collections import Counter

import pytest

from app import store
from app.models import CuttingResult
from app.services import calc, editor
from cse_w13_util import check_model, make_project, node_at, nodes

CONFIGS = {
    "plain": dict(parts=[(400, 300, 12), (250, 600, 8), (1200, 350, 4), (700, 700, 3), (150, 150, 20)], cut={}),
    "rot3_trims": dict(parts=[(400, 300, 12), (250, 600, 8), (1200, 350, 4), (700, 700, 3), (150, 150, 20)],
                       cut={"max_rotations": 3, "trim_length": 5, "trim_width": 5, "min_trim_cut": 10, "kerf": 4}),
    "group": dict(parts=[(300, 500, 9), (600, 400, 4), (900, 250, 3), (120, 120, 15)],
                  cut={"kerf_group": 5}, group={1: dict(group_by="length", group_max=4)}),
    "strips_only": dict(parts=[(500, 400, 10), (300, 300, 12), (800, 200, 5)], cut={"max_rotations": 1, "kerf": 2}),
}
PER_CONFIG = 50                     # 4 × 50 = 200 ketma-ketlik
STEPS = 12

KINDS = [("remove", 10), ("move", 6), ("clone", 5), ("expand", 5), ("rotate", 1), ("place", 12), ("place_auto", 6),
         ("place_multi", 10), ("expand_block", 6), ("flip", 7), ("replace", 6), ("swap", 6), ("move_map", 3),
         ("map_trim", 6), ("copies", 3), ("add_map", 2), ("delete_map", 2), ("comment", 1)]
STATS: Counter = Counter()
FAILS: Counter = Counter()


def _left(op, p, res):
    """uid → hali joylashmagan nusxalar soni."""
    placed = Counter()
    for m in res.maps:
        for pl in m.placements:
            placed[pl.part_uid] += m.copies
    return {pt.uid: calc.effective_qty(p, pt) - placed[pt.uid] for pt in op.parts}


def _gen(rng, res, uids, sheet_ids, left, pinfo, forced=None):
    """Joriy natijaga mos tasodifiy amal (hali joylashmagan detallar va sig'adigan joylar tomon yo'naltirilgan)."""
    if not res.maps:
        return {"type": "add_map", "sheet_id": rng.choice(sheet_ids)}
    mi = rng.randrange(len(res.maps))
    root = res.maps[mi].strips[0]
    allnodes = nodes(root, lambda n: True)
    ps = [x for x in allnodes if x[1]["k"] == "P"]
    ws = [x for x in allnodes if x[1]["k"] == "W"]
    cs_ = [x for x in allnodes if x[1]["k"] == "C" and x[0]]
    body = ps + cs_
    kind = forced or rng.choices([k for k, _w in KINDS], [w for _k, w in KINDS])[0]
    a = {"type": kind, "map": mi + 1}
    free_uids = [u for u in uids if left.get(u, 0) >= res.maps[mi].copies] or uids

    def fitting(uid_pool):
        """Sig'adigan (bo'sh joy, detal) juftliklari."""
        out = []
        for p_, n_ in ws:
            for u in uid_pool:
                pi = pinfo[u]
                if (pi.l <= n_["l"] + 0.01 and pi.w <= n_["w"] + 0.01) or (pi.w <= n_["l"] + 0.01 and pi.l <= n_["w"] + 0.01):
                    out.append((p_, u))
        return out

    def some(lst, hi=3):
        return [p for p, _n in rng.sample(lst, min(len(lst), rng.randint(1, hi)))] if lst else []

    def sel(lst, hi=3):
        got = some(lst, hi)
        if not got:
            return {"path": []}
        return {"paths": got} if (len(got) > 1 or rng.random() < 0.3) else {"path": got[0]}

    if kind in ("remove", "move", "clone"):
        a.update(sel(body, 4))
        if kind == "move":
            a["to"] = rng.choice(["start", "end", "prev", "next"])
    elif kind == "expand":
        a["path"] = rng.choice([p for p, _n in cs_] or [[]])
    elif kind == "rotate":
        small = [x for x in cs_ if len([1 for q in nodes(x[1], lambda n: n["k"] == "P")]) <= 6]
        a.update(sel(small, 2))
    elif kind in ("place", "place_auto", "place_multi"):
        pairs = fitting(free_uids) if rng.random() < 0.85 else []
        if pairs:
            wp, uid = rng.choice(pairs)
        else:
            wp, uid = rng.choice([p for p, _n in ws] or [[]]), rng.choice(uids)
        a["uid"] = uid
        if kind != "place_auto":
            a["path"] = wp
        if rng.random() < 0.3:
            a["rotated"] = rng.random() < 0.5
        if kind == "place_multi" and rng.random() < 0.4:
            a["count"] = rng.randint(1, 8)
    elif kind == "expand_block":
        grouped = [x for x in ps if x[1]["u"] == 1] if any(left) else []
        a["path"] = rng.choice(grouped or ps or [([], None)])[0]
    elif kind == "flip":
        feasible = []                                  # burilganda joyiga (keyingi bo'sh joy bilan) sig'adigan detallar
        for p_, n_ in ps:
            par = node_at(root, p_[:-1])
            sibs, i_ = par["c"], p_[-1]
            pi = pinfo[n_["u"]]
            if not pi.can_rotate or abs(pi.l - pi.w) < 0.01:
                continue
            ax = par["a"]
            extra = (sibs[i_ + 1]["l"] if ax == "x" else sibs[i_ + 1]["w"]) + 5 if i_ + 1 < len(sibs) and sibs[i_ + 1]["k"] == "W" else 0
            a_old, b_old = (n_["l"], n_["w"]) if ax == "x" else (n_["w"], n_["l"])
            a_new, b_new = (n_["w"], n_["l"]) if ax == "x" else (n_["l"], n_["w"])
            if a_new <= a_old + extra + 0.01 and b_new <= b_old + 0.01:
                feasible.append((p_, n_))
        a.update(sel(feasible if feasible and rng.random() < 0.8 else ps, 2))
    elif kind == "replace":
        a["path"] = rng.choice([p for p, _n in ps] or [[]])
        a["uid"] = rng.choice(free_uids)
        if rng.random() < 0.2:
            a["rotated"] = rng.random() < 0.5
    elif kind == "swap":
        if len(body) >= 2:
            x = rng.choice(body)
            sib = [y for y in body if len(y[0]) == len(x[0]) and y[0][:-1] == x[0][:-1] and y[0] != x[0]]
            y = rng.choice(sib) if sib else rng.choice(body)
            a["paths"] = [x[0], y[0]]
        else:
            a["paths"] = [[0], [1]]
    elif kind == "move_map":
        a["to"] = rng.choice(["up", "down", "first", "last"])
    elif kind == "map_trim":
        for k in rng.sample(["trim_length", "trim_width", "end_offset_bottom", "end_offset_right"], rng.randint(1, 3)):
            a[k] = rng.choice([None, 0, 1, 2, 5, 10, 25, 60, 100])
    elif kind == "copies":
        a["copies"] = rng.randint(1, 3)
    elif kind == "add_map":
        a = {"type": "add_map", "sheet_id": rng.choice(sheet_ids), "axis": rng.choice(["x", "y"])}
    elif kind == "comment":
        a["comment"] = rng.choice(["", "a", "izoh " * 50])
    return a


@pytest.fixture(scope="module")
def projects(client):
    out = {}
    for name, cfg in CONFIGS.items():
        pid, cs, sh = make_project(client, cfg["parts"], cut=cfg["cut"], group=cfg.get("group"))
        r = client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
        assert r.status_code == 200, r.text
        p = store.load(pid)
        op = store.op_of(p, cs)
        out[name] = (p, op, CuttingResult.model_validate(r.json()))
    return out


@pytest.mark.parametrize("name", list(CONFIGS))
def test_fuzz_edit_sequences_always_validate(projects, name):
    p, op, res0 = projects[name]
    uids = [pt.uid for pt in op.parts]
    sheet_ids = [s.id for s in op.sheets]
    pinfo = editor.part_info(p, op)
    check_model(p, op, res0, expect_manual=False)
    for seq in range(PER_CONFIG):
        rng = random.Random(f"{name}:{seq}")
        res = res0.model_copy(deep=True)
        log = []
        n_pre = rng.randint(1, 3)
        for step in range(STEPS):
            # boshida 1–3 ta o'chirish (xodim avval joy bo'shatadi), keyin tasodifiy amallar
            forced = "remove" if step < n_pre else None
            action = _gen(rng, res, uids, sheet_ids, _left(op, p, res), pinfo, forced)
            before = res.model_dump_json()
            try:
                new = editor.apply(p, op, res, action)
            except editor.EditError:
                FAILS[action["type"]] += 1
                assert res.model_dump_json() == before, ("rad etilgan amal qoralamani o'zgartirdi", name, seq, action)
                log.append((action, "rad"))
                continue
            log.append((action, "ok"))
            STATS[action["type"]] += 1
            try:
                check_model(p, op, new)
            except AssertionError as e:                                # noqa: PERF203 — xato tarixi bilan
                raise AssertionError(f"{name}:{seq} qadam {step}: {action}\n{e}\nketma-ketlik: {log}") from e
            assert res.model_dump_json() == before                   # kirish nusxasi o'zgarmaydi
            res = new
        # qayta qurish barqaror (idempotent): natijani yana qursak — o'sha daraxtlar
        if res.maps:
            again = editor.rebuild(p, op, res)
            assert [m.strips for m in again.maps] == [m.strips for m in res.maps], (name, seq)
            assert [m.placements for m in again.maps] == [m.placements for m in res.maps]


def test_fuzz_covers_every_new_action():
    """Fuzz bo'sh o'tmasin: har bir amal turi kamida bir marta muvaffaqiyatli qo'llangan (parametrlangan testlardan keyin)."""
    if not STATS:
        pytest.skip("fuzz alohida yurgizilgan")
    print("fuzz ok:", dict(STATS), "rad:", dict(FAILS))
    must_often = ["remove", "move", "place", "place_multi", "swap", "map_trim", "comment", "copies", "add_map"]
    for k in must_often:
        assert STATS[k] >= 5, (k, dict(STATS), dict(FAILS))
    for k in ("clone", "expand", "place_auto", "move_map", "delete_map", "flip", "replace", "expand_block"):
        assert STATS[k] >= 1, (k, dict(STATS), dict(FAILS))
    assert sum(STATS.values()) >= 400, dict(STATS)
