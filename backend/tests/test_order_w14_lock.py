"""W14 — tahrir bloklanishi (standart O'CHIQ — faqat ogohlantirish; `MEBELIX_ORDER_LOCK_FROM` bilan yoqiladi) va
holat o'tishidagi bloklamaydigan ogohlantirishlar («Готов»: kroy bajarilmagan; «Заказан»: detallar yo'q)."""
import pytest

from app.services import mes, order_flow


@pytest.fixture(autouse=True)
def _quiet_hooks(monkeypatch):
    monkeypatch.setattr(mes, "send_webhook", lambda event, payload, attempts=None: dict(sent=True, attempts=1))
    monkeypatch.delenv(order_flow.LOCK_ENV, raising=False)


def mk(client, name="W14 lock"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def order(client, pid, status, **kw):
    return client.post(f"/api/projects/{pid}/order", json={"status": status, **kw})


def add_cs(client, pid):
    return client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "LDSP"})


# ───────────────────────── sozlama ─────────────────────────
@pytest.mark.parametrize("raw,expect", [(None, None), ("", None), ("0", None), ("1", None), ("abc", None), ("4", None),
                                        (" 2 ", 2), ("2", 2), ("3", 3)])
def test_lock_from_parsing(monkeypatch, raw, expect):
    if raw is None:
        monkeypatch.delenv(order_flow.LOCK_ENV, raising=False)
    else:
        monkeypatch.setenv(order_flow.LOCK_ENV, raw)
    got = order_flow.lock_from()
    assert (None if got is None else int(got)) == expect


# ───────────────────────── standart: hech narsa bloklanmaydi, faqat ogohlantirish ─────────────────────────
def test_default_nothing_is_blocked_but_state_warns(client, kravat):
    pid, cs, _el = kravat
    assert order(client, pid, 1).status_code == 200
    assert client.get(f"/api/projects/{pid}/order").json()["edit_warning"] is False
    assert order(client, pid, 2, ready_date="2026-12-01").status_code == 200
    assert order(client, pid, 3).status_code == 200
    st = client.get(f"/api/projects/{pid}/order").json()
    assert st["edit_warning"] is True and st["lock"] == {"from_status": None, "active": False}
    # «Готов» holatida ham hamma tahrir va kroy ishlaydi
    assert add_cs(client, pid).status_code == 200
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    assert client.post(f"/api/projects/{pid}/actions/merge-same").status_code == 200
    assert client.patch(f"/api/projects/{pid}/operations/{cs}", json={"name": "yangi"}).status_code == 200


# ───────────────────────── yoqilgan: «Утвержден» dan boshlab ─────────────────────────
def test_lock_from_approved_blocks_content_edits_only(client, kravat, monkeypatch):
    pid, cs, el = kravat
    monkeypatch.setenv(order_flow.LOCK_ENV, "2")
    assert add_cs(client, pid).status_code == 200                      # «Не заказан» — ochiq
    assert order(client, pid, 1).status_code == 200
    assert add_cs(client, pid).status_code == 200                      # «Заказан» — hali ochiq
    assert order(client, pid, 2, ready_date="2026-12-01").status_code == 200
    st = client.get(f"/api/projects/{pid}/order").json()
    assert st["lock"] == {"from_status": 2, "active": True}
    n_ops = len(client.get(f"/api/projects/{pid}").json()["operations"])

    blocked = [
        ("post", f"/api/projects/{pid}/operations", {"type": "CS"}),
        ("patch", f"/api/projects/{pid}/operations/{cs}", {"name": "x"}),
        ("delete", f"/api/projects/{pid}/operations/{el}", None),
        ("post", f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast", None),
        ("post", f"/api/projects/{pid}/operations/{cs}/parts", [{"name": "Z", "length": 100, "width": 100}]),
        ("post", f"/api/projects/{pid}/products", {"name": "Yangi"}),
        ("post", f"/api/projects/{pid}/actions/merge-same", None),
        ("post", f"/api/projects/{pid}/actions/split-edges", None),
        ("post", f"/api/projects/{pid}/actions/optimize-ops", None),
        ("post", f"/api/projects/{pid}/actions/clear", None),
    ]
    for method, url, body in blocked:
        r = getattr(client, method)(url, **({"json": body} if body is not None else {}))
        assert r.status_code == 409, (method, url, r.text)
        assert "заблокировано" in r.json()["detail"] and "Утвержден" in r.json()["detail"]
    r = client.post(f"/api/projects/{pid}/actions/clear", headers={"Accept-Language": "uz"})
    assert r.status_code == 409 and "bloklangan" in r.json()["detail"] and "Tasdiqlangan" in r.json()["detail"]
    assert len(client.get(f"/api/projects/{pid}").json()["operations"]) == n_ops

    # ochiq qoladi: o'qish, sarlavha, holat, saqlash, undo/redo, nusxa, hisobot, eksport, sex (QR «bajarildi»)
    assert client.get(f"/api/projects/{pid}").status_code == 200
    assert client.patch(f"/api/projects/{pid}", json={"note": "izoh"}).status_code == 200
    assert client.post(f"/api/projects/{pid}/save").status_code == 200
    assert client.post(f"/api/projects/{pid}/report", json={}).status_code == 200
    assert client.get(f"/api/projects/{pid}/export").status_code == 200
    assert client.post(f"/api/projects/{pid}/undo").status_code == 200
    assert client.post(f"/api/projects/{pid}/redo").status_code == 200
    cp = client.post(f"/api/projects/{pid}/copy")
    assert cp.status_code == 200 and cp.json()["status"] == 0
    assert add_cs(client, cp.json()["id"]).status_code == 200            # nusxa «Не заказан» — ochiq
    # orqaga qaytarish — tahrir yana ochiladi
    assert order(client, pid, 1).status_code == 200
    assert add_cs(client, pid).status_code == 200


def test_lock_from_ready_leaves_approved_open(client, kravat, monkeypatch):
    pid, cs, _el = kravat
    monkeypatch.setenv(order_flow.LOCK_ENV, "3")
    order(client, pid, 2, ready_date="2026-12-01")
    assert add_cs(client, pid).status_code == 200                        # «Утвержден» — ochiq
    assert order(client, pid, 3).status_code == 200
    r = add_cs(client, pid)
    assert r.status_code == 409 and "Готов" in r.json()["detail"]


def test_lock_does_not_stop_workshop_scan(client, kravat, monkeypatch):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    monkeypatch.setenv(order_flow.LOCK_ENV, "2")
    order(client, pid, 2, ready_date="2026-12-01")
    p = client.get(f"/api/projects/{pid}").json()
    code = f"MXK:{p['number']}:{cs}:1"
    assert client.post(f"/api/mes/scan/{code}/done").status_code == 200   # sex progressi bloklanmaydi


def test_lock_unknown_project_is_left_to_the_endpoint(client, monkeypatch):
    monkeypatch.setenv(order_flow.LOCK_ENV, "2")
    assert client.post("/api/projects/yoq-loyiha/operations", json={"type": "CS"}).status_code == 404


# ───────────────────────── ogohlantirishlar (bloklamaydi) ─────────────────────────
def _w(client, pid, to):
    t = next(t for t in client.get(f"/api/projects/{pid}/order").json()["transitions"] if t["to"] == to)
    return t["allowed"], {w["code"]: w["n"] for w in t["warnings"]}, t["warnings"]


def test_warning_ordering_empty_project(client):
    pid = mk(client)
    allowed, w, full = _w(client, pid, 1)
    assert allowed and w == {"no_parts": 0} and "нет деталей" in full[0]["text"]
    assert order(client, pid, 1).status_code == 200                      # ogohlantirish — bloklamaydi


def test_no_warning_when_parts_exist(client, kravat):
    pid, _cs, _el = kravat
    assert _w(client, pid, 1)[1] == {}
    assert _w(client, pid, 2)[1] == {}                                   # tasdiqlashda kroy shart emas (hali ishga tushmagan)


def test_warning_ready_follows_cutting_progress(client, kravat):
    pid, cs, _el = kravat
    assert _w(client, pid, 3)[1] == {"no_cut": 1}                        # CS kroysiz
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    w = _w(client, pid, 3)[1]
    assert "no_cut" not in w and w.get("cut_open", 0) >= 1               # kartalar sexda «bajarildi» deb belgilanmagan
    p = client.get(f"/api/projects/{pid}").json()
    res = next(o for o in p["operations"] if o["id"] == cs)["result"]
    for m in res["maps"]:
        r = client.post(f"/api/mes/scan/MXK:{p['number']}:{cs}:{m['index']}/done", params={"count": 1000})
        assert r.status_code == 200 and r.json()["done"] == r.json()["copies"]
    assert _w(client, pid, 3)[1] == {}
    # ogohlantirish bilan ham o'tish mumkin (bloklanmaydi)
    other = client.post("/api/projects", json={"name": "Kroysiz tayyor"}).json()["id"]
    assert order(client, other, 3).status_code == 200


def test_warnings_only_for_allowed_transitions(client):
    pid = mk(client)
    for t in client.get(f"/api/projects/{pid}/order").json()["transitions"]:
        if not t["allowed"]:
            assert t["warnings"] == []
