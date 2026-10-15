"""W14 — «Заказать» oqimi: o'tish matritsasi, rollar, tayyorlik sanasi, tarix, MES webhook (mock), undo qoidasi,
PATCH moslik, eski JSON, nusxa."""
import json
import time

import jwt
import pytest

from app.models import Project
from app.services import mes, order_flow

SECRET = "w14-test-secret-0123456789-abcdefghijklmnop"
UZ = {"Accept-Language": "uz"}


@pytest.fixture(autouse=True)
def _jwt_env(monkeypatch):
    """Token dekodlanishi uchun kalit (AUTH_REQUIRED yo'q: tokensiz so'rov — lokal «admin»)."""
    monkeypatch.setenv("MEBELIX_JWT_SECRET", SECRET)


@pytest.fixture()
def hooks(monkeypatch):
    """MES webhook chaqiruvlari (mock): [(event, payload)]."""
    calls = []

    def fake(event, payload, attempts=None):
        calls.append((event, payload))
        return dict(sent=True, status=200, error=None, elapsed_ms=0, attempts=1)
    monkeypatch.setattr(mes, "send_webhook", fake)
    return calls


def tok(roles=None, name="Tester"):
    claims = {"sub": "u1", "name": name, "exp": int(time.time()) + 300}
    if roles is not None:
        claims["roles"] = roles
    return {"Authorization": "Bearer " + jwt.encode(claims, SECRET, algorithm="HS256")}


ROLES = {"cutter": ["kroychi"], "tech": ["texnolog"], "admin": ["admin"], "none": None, "unknown": ["boshqa-rol"],
         "viewer": ["viewer"]}
BACK_OK = {"tech", "admin", "none", "unknown"}          # rolsiz / tanilmagan rol — eski qoida: to'liq huquq (auth.py)


def mk(client, name="W14 oqim"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def get(client, pid):
    return client.get(f"/api/projects/{pid}").json()


def order(client, pid, status=None, headers=None, **kw):
    body = dict(kw)
    if status is not None:
        body["status"] = status
    return client.post(f"/api/projects/{pid}/order", json=body, headers=headers)


def to_status(client, pid, s):
    """Lokal admin sifatida holatga olib borish (0 — hech narsa)."""
    if s == 1:
        assert order(client, pid, 1).status_code == 200
    elif s == 2:
        assert order(client, pid, 2, ready_date="2026-11-20").status_code == 200
    elif s == 3:
        assert order(client, pid, 3).status_code == 200
    assert get(client, pid)["status"] == s


def expected(old, new, role):
    if role == "viewer":
        return 403
    if new == old:
        return 409
    if new < old:
        return 200 if role in BACK_OK else 403
    return 200


# ───────────────────────── jadval va matritsa ─────────────────────────
def test_transitions_table_matches_kind_of():
    pairs = {(a, b) for a in range(4) for b in range(4) if a != b}
    assert set(order_flow.TRANSITIONS) == pairs
    for (a, b), k in order_flow.TRANSITIONS.items():
        assert order_flow.kind_of(a, b) == k
    assert order_flow.kind_of(2, 2) == "same"


@pytest.mark.parametrize("old", [0, 1, 2, 3])
@pytest.mark.parametrize("new", [0, 1, 2, 3])
def test_transition_matrix_by_role(client, hooks, old, new):
    for role, roles in ROLES.items():
        pid = mk(client, f"matritsa {old}-{new} {role}")
        to_status(client, pid, old)
        hooks.clear()
        r = order(client, pid, new, headers=tok(roles), ready_date="2026-12-01" if new == 2 else None)
        assert r.status_code == expected(old, new, role), (old, new, role, r.text)
        if r.status_code == 200:
            assert r.json()["status"] == new
            assert [(e, p["old_status"], p["status"]) for e, p in hooks] == [("project.status", old, new)]
        else:
            assert get(client, pid)["status"] == old              # rad etildi — holat o'zgarmadi
            assert hooks == []                                    # webhook yo'q


@pytest.mark.parametrize("old", [0, 1, 2, 3])
def test_state_endpoint_agrees_with_rules(client, old):
    for role, roles in ROLES.items():
        pid = mk(client, f"holat {old} {role}")
        to_status(client, pid, old)
        s = client.get(f"/api/projects/{pid}/order", headers=tok(roles)).json()
        assert s["status"] == old and {t["to"] for t in s["transitions"]} == {0, 1, 2, 3} - {old}
        for t in s["transitions"]:
            assert t["allowed"] == (expected(old, t["to"], role) == 200), (old, t, role)
            assert t["kind"] == order_flow.kind_of(old, t["to"])
            assert (t["reason"] is None) == t["allowed"]
        assert s["can_change"] == (role != "viewer") and s["can_back"] == (role in BACK_OK)


def test_skip_forward_is_a_switch(client, hooks, monkeypatch):
    pid = mk(client)
    monkeypatch.setattr(order_flow, "ALLOW_SKIP_FORWARD", False)
    r = order(client, pid, 2, ready_date="2026-12-01")
    assert r.status_code == 409 and "пропускать" in r.json()["detail"]
    r = order(client, pid, 2, ready_date="2026-12-01", headers=UZ)
    assert r.status_code == 409 and "o'tkazib" in r.json()["detail"]
    assert order(client, pid, 1).status_code == 200                # bir qadam — ruxsat
    assert order(client, pid, 2, ready_date="2026-12-01").status_code == 200
    assert order(client, pid, 3).status_code == 200
    st = client.get(f"/api/projects/{pid}/order").json()
    assert all(t["kind"] == "back" for t in st["transitions"])      # oldinga o'tish qolmadi (Готов oxirgi)


def test_default_status_is_ordered_and_bad_status_is_422(client, hooks):
    pid = mk(client)
    p = order(client, pid).json()                                   # status berilmagan — «Заказать»
    assert p["status"] == 1
    assert order(client, pid, 7).status_code == 422
    assert order(client, pid, "x").status_code == 422
    assert get(client, pid)["status"] == 1


def test_viewer_cannot_change_status_even_without_required_auth(client, hooks):
    pid = mk(client)
    r = order(client, pid, 1, headers=tok(["viewer"]))
    assert r.status_code == 403 and r.json()["detail"].startswith("Недостаточно прав")
    r = client.patch(f"/api/projects/{pid}", json={"status": 1}, headers=tok(["viewer"]))
    assert r.status_code == 403
    # holatsiz PATCH (nom) — ko'ruvchi uchun avvalgidek (auth.py faqat AUTH_REQUIRED da to'sadi)
    assert client.patch(f"/api/projects/{pid}", json={"note": "x"}, headers=tok(["viewer"])).status_code == 200
    assert get(client, pid)["status"] == 0 and hooks == []


# ───────────────────────── tayyorlik sanasi (ORD-006) ─────────────────────────
def test_approve_requires_ready_date_until_it_is_set(client, hooks):
    pid = mk(client)
    s = client.get(f"/api/projects/{pid}/order").json()
    assert s["ready_set"] is False
    assert next(t for t in s["transitions"] if t["to"] == 2)["needs_ready_date"] is True
    assert next(t for t in s["transitions"] if t["to"] == 1)["needs_ready_date"] is False
    r = order(client, pid, 2)
    assert r.status_code == 422 and "дату готовности" in r.json()["detail"]
    r = order(client, pid, 2, headers=UZ)
    assert r.status_code == 422 and "tayyorlik sanasi" in r.json()["detail"]
    assert get(client, pid)["status"] == 0 and hooks == []
    assert order(client, pid, 2, ready_date="not-a-date").status_code == 400
    assert order(client, pid, 2, ready_date="2200-01-01").status_code == 400
    assert order(client, pid, 2, ready_date="0001-01-01").status_code == 400
    assert get(client, pid)["status"] == 0
    p = order(client, pid, 2, ready_date="2026-12-05", executor="Sex 2", comment="tezkor").json()
    assert p["status"] == 2 and p["ready_date"] == "2026-12-05"
    assert p["order_log"][-1]["ready_date"] == "2026-12-05"
    s = client.get(f"/api/projects/{pid}/order").json()
    assert s["ready_set"] is True and s["ready_date"] == "2026-12-05"


def test_approve_without_date_is_fine_when_date_already_set(client, hooks):
    pid = mk(client)
    client.patch(f"/api/projects/{pid}", json={"ready_date": "2099-01-01"})          # sarlavhadan qo'lda
    assert client.get(f"/api/projects/{pid}/order").json()["ready_set"] is True
    assert order(client, pid, 2).status_code == 200


def test_ready_date_can_be_changed_when_going_back_and_forth(client, hooks):
    pid = mk(client)
    to_status(client, pid, 2)
    p = order(client, pid, 1, ready_date="2027-01-15").json()          # orqaga + yangi sana
    assert p["status"] == 1 and p["ready_date"] == "2027-01-15"
    p = order(client, pid, 2).json()                                   # sana saqlangan — qayta so'ralmaydi
    assert p["status"] == 2 and p["ready_date"] == "2027-01-15"


def test_patch_status_stays_compatible_without_ready_date(client, hooks):
    """Eski mijozlar (PATCH sarlavha): 0→2 sanasiz ham ishlaydi; qoidalar (rol, orqaga) va tarix esa amal qiladi."""
    pid = mk(client)
    p = client.patch(f"/api/projects/{pid}", json={"status": 2}).json()
    assert p["status"] == 2 and p["order_log"][-1]["via"] == "patch"
    assert [(e, x["old_status"], x["status"]) for e, x in hooks] == [("project.status", 0, 2)]
    hooks.clear()
    assert client.patch(f"/api/projects/{pid}", json={"status": 2, "note": "o'sha"}).status_code == 200   # o'zgarish yo'q
    assert hooks == [] and len(get(client, pid)["order_log"]) == 1
    r = client.patch(f"/api/projects/{pid}", json={"status": 1}, headers=tok(["kroychi"]))
    assert r.status_code == 403 and get(client, pid)["status"] == 2 and hooks == []
    assert client.patch(f"/api/projects/{pid}", json={"status": 1}, headers=tok(["texnolog"])).status_code == 200
    assert client.patch(f"/api/projects/{pid}", json={"status": 9}).status_code == 422


# ───────────────────────── tarix yozuvi ─────────────────────────
def test_log_records_who_when_and_internal_text_only(client, hooks, monkeypatch):
    pid = mk(client)
    assert get(client, pid)["order_log"] == []
    order(client, pid, 1, headers=tok(["kroychi"], name="Jasur"), executor="  Sex №2  ", comment=" tezroq ")
    order(client, pid, 2, headers=tok(["texnolog"], name="Dilshod"), ready_date="2026-12-10")
    order(client, pid, 1, headers=tok(["admin"], name="Admin"), comment="qaytarildi")
    log = get(client, pid)["order_log"]
    assert [(e["user"], e["from_status"], e["to_status"], e["via"]) for e in log] == [
        ("Jasur", 0, 1, "order"), ("Dilshod", 1, 2, "order"), ("Admin", 2, 1, "order")]
    assert log[0]["executor"] == "Sex №2" and log[0]["comment"] == "tezroq" and log[1]["ready_date"] == "2026-12-10"
    assert all(e["at"].endswith("Z") and len(e["at"]) == 20 for e in log)
    st = client.get(f"/api/projects/{pid}/order").json()
    assert [e["to_status"] for e in st["log"]] == [1, 2, 1]               # yangisi birinchi: 2→1, 1→2, 0→1
    assert [e["from_status"] for e in st["log"]] == [2, 1, 0]
    assert st["executor"] == ""                                            # oxirgi yozuvda ijrochi yo'q
    # ichki matn webhookka kirmaydi
    for _ev, payload in hooks:
        assert set(payload) == {"project_id", "number", "mes_order_ref", "status", "old_status"}
        assert "Sex" not in json.dumps(payload) and "tezroq" not in json.dumps(payload)


def test_log_is_capped(client, hooks, monkeypatch):
    monkeypatch.setattr(order_flow, "ORDER_LOG_LIMIT", 5)
    pid = mk(client)
    for _ in range(4):
        order(client, pid, 1)
        order(client, pid, 0)
    log = get(client, pid)["order_log"]
    assert len(log) == 5 and log[-1]["to_status"] == 0


def test_log_length_limits_are_422(client):
    pid = mk(client)
    assert order(client, pid, 1, executor="x" * 201).status_code == 422
    assert order(client, pid, 1, comment="x" * 1001).status_code == 422
    assert order(client, pid, 1, executor="x" * 200, comment="y" * 1000).status_code == 200


def test_copy_resets_status_and_log(client, hooks):
    pid = mk(client)
    to_status(client, pid, 2)
    cp = client.post(f"/api/projects/{pid}/copy").json()
    assert cp["status"] == 0 and cp["order_log"] == [] and get(client, pid)["order_log"]


def test_old_json_without_log_opens_with_defaults(client, hooks):
    pid = mk(client)
    raw = get(client, pid)
    raw.pop("order_log")
    files = {"file": ("eski.mxk.json", json.dumps(raw).encode(), "application/json")}
    r = client.post("/api/projects/import", files=files)
    assert r.status_code == 200 and r.json()["order_log"] == []
    # eksport → import: tarix saqlanadi
    to_status(client, pid, 1)
    exp = client.get(f"/api/projects/{pid}/export").content
    r = client.post("/api/projects/import", files={"file": ("x.mxk.json", exp, "application/json")}).json()
    assert [e["to_status"] for e in r["order_log"]] == [1]


# ───────────────────────── MES webhook ─────────────────────────
def test_webhook_goes_through_existing_mechanism_with_same_payload(client, monkeypatch):
    import httpx
    sent = []
    monkeypatch.setenv("MES_WEBHOOK_URL", "http://mes.local/hook")
    monkeypatch.setenv("MES_WEBHOOK_TOKEN", "t0k")
    monkeypatch.setattr(httpx, "post", lambda url, json=None, headers=None, timeout=None: sent.append((url, json, headers)))
    p = client.post("/api/projects", json={"name": "Hook W14", "mes_order_ref": "W14-1"}).json()
    r = order(client, p["id"], 1, executor="Sex", comment="ichki")
    assert r.status_code == 200
    ev = [s for s in sent if s[1]["event"] == "project.status"]
    assert len(ev) == 1 and ev[0][0] == "http://mes.local/hook" and ev[0][2]["Authorization"] == "Bearer t0k"
    body = ev[0][1]
    assert body == {"event": "project.status", "project_id": p["id"], "number": p["number"], "mes_order_ref": "W14-1",
                    "status": 1, "old_status": 0}
    # PATCH yo'li bilan bir xil yuklama
    sent.clear()
    client.patch(f"/api/projects/{p['id']}", json={"status": 0})
    assert sent[0][1] == {**body, "status": 0, "old_status": 1}


def test_no_webhook_when_url_missing_or_status_unchanged(client, monkeypatch):
    monkeypatch.delenv("MES_WEBHOOK_URL", raising=False)
    pid = mk(client)
    assert order(client, pid, 1).status_code == 200                # URL yo'q — xatosiz, jim
    assert mes.send_webhook("project.status", {})["attempts"] == 0


# ───────────────────────── undo / redo — orqaga qaytarish qoidasidan chetlab o'tilmaydi ─────────────────────────
def test_undo_of_status_follows_back_rule(client, hooks):
    pid = mk(client)
    to_status(client, pid, 1)
    to_status(client, pid, 2)
    hooks.clear()
    r = client.post(f"/api/projects/{pid}/undo", headers=tok(["kroychi"]))
    assert r.status_code == 403 and "технолог" in r.json()["detail"]
    assert get(client, pid)["status"] == 2 and hooks == []
    r = client.post(f"/api/projects/{pid}/undo", headers=tok(["texnolog"]))
    assert r.status_code == 200 and r.json()["status"] == 1 and len(r.json()["order_log"]) == 1   # tarix ham orqaga
    assert [(x["old_status"], x["status"]) for _e, x in hooks] == [(2, 1)]
    # redo — oldinga: kroychi ham qila oladi
    r = client.post(f"/api/projects/{pid}/redo", headers=tok(["kroychi"]))
    assert r.status_code == 200 and r.json()["status"] == 2
    # holatga tegmaydigan undo — kroychi uchun ochiq
    client.patch(f"/api/projects/{pid}", json={"note": "izoh"})
    assert client.post(f"/api/projects/{pid}/undo", headers=tok(["kroychi"])).status_code == 200
    # ko'ruvchi holatni qaytara olmaydi
    assert client.post(f"/api/projects/{pid}/undo", headers=tok(["viewer"])).status_code == 403
    assert get(client, pid)["status"] == 2


def test_undo_without_history_is_still_400(client):
    pid = mk(client)
    assert client.post(f"/api/projects/{pid}/undo").status_code == 400      # tarixda faqat yaratilish versiyasi


# ───────────────────────── hamma narsa eski loyihalar bilan mos ─────────────────────────
def test_new_project_defaults(client):
    p = client.post("/api/projects", json={"name": "Standart"}).json()
    assert p["status"] == 0 and p["order_log"] == [] and p["order_date"] == p["ready_date"]
    s = client.get(f"/api/projects/{p['id']}/order").json()
    assert s["edit_warning"] is False and s["lock"] == {"from_status": None, "active": False}
    assert order_flow.ready_is_set(Project.model_validate(p)) is False
