"""«Отправить в MES» (services/mes_send.py): yuborishdan oldingi tekshiruv, MES javobi, qulf (undo ham), qayta ochish.
Ma'lumotlar sintetik; MES o'rniga `httpx.post` almashtiriladi."""
import json

import pytest


class _Resp:
    def __init__(self, status, body):
        self.status_code, self._body = status, body

    def json(self):
        return self._body


@pytest.fixture()
def mes_env(monkeypatch):
    monkeypatch.setenv("MES_WEBHOOK_URL", "http://mes.test/api/v1/integ/kroy/webhook")
    monkeypatch.setenv("MES_WEBHOOK_TOKEN", "srv")
    monkeypatch.setenv("MES_PUBLIC_URL", "http://mes.test")
    calls = {"resp": _Resp(201, {"order_id": 7, "order_number": "B-2026-901", "redirect_url": "/orders/7", "version": 1}), "sent": []}

    def post(url, **kw):
        calls["sent"].append((url, kw))
        return calls["resp"]

    monkeypatch.setattr("httpx.post", post)
    return calls


@pytest.fixture()
def proj(client):
    pid = client.post("/api/projects", json={"name": "MES yuborish"}).json()["id"]
    client.patch(f"/api/projects/{pid}", json={"mes_order_ref": "B-2026-901"})
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "LDSP 16"}).json()
    oid = p["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[{"name": "bok", "length": 700, "width": 300, "qty": 2}])
    return pid, oid


def _cut(client, pid, oid):
    assert client.post(f"/api/projects/{pid}/operations/{oid}/optimize?quality=fast").status_code == 200


def test_not_cut_is_rejected_before_sending(client, proj, mes_env):
    pid, oid = proj
    r = client.post(f"/api/projects/{pid}/mes-send")
    assert r.status_code == 422 and not mes_env["sent"]


def test_not_linked_is_rejected(client, mes_env):
    pid = client.post("/api/projects", json={"name": "Bog'lanmagan"}).json()["id"]
    assert client.post(f"/api/projects/{pid}/mes-send").status_code == 422 and not mes_env["sent"]


def test_send_locks_and_reopen_unlocks(client, proj, mes_env):
    pid, oid = proj
    _cut(client, pid, oid)
    r = client.post(f"/api/projects/{pid}/mes-send")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["mes_url"] == "http://mes.test/orders/7" and d["project"]["mes_sent"]["version"] == 1
    # kroy o'zi ham webhook yuboradi — paket so'rovi manzili bo'yicha olinadi
    kw = next(k for u, k in mes_env["sent"] if u == f"http://mes.test/api/v1/integ/kroy/loyiha/{pid}/paket")
    assert kw["headers"]["Authorization"] == "Bearer srv"
    assert json.loads(kw["content"])["source"]["mes_order_number"] == "B-2026-901"

    add = [{"name": "yangi", "length": 100, "width": 100, "qty": 1}]
    assert client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=add).status_code == 409
    assert client.post(f"/api/projects/{pid}/undo").status_code == 409
    assert client.post(f"/api/projects/{pid}/mes-send").status_code == 409
    assert client.get(f"/api/projects/{pid}").status_code == 200

    r = client.post(f"/api/projects/{pid}/mes-reopen")
    assert r.status_code == 200 and r.json()["mes_sent"] is None
    assert any(k.get("json", {}).get("event") == "project.reopened" for _, k in mes_env["sent"])
    assert client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=add).status_code != 409


def test_mes_refusal_keeps_project_open_and_shows_reason(client, proj, mes_env):
    pid, oid = proj
    _cut(client, pid, oid)
    mes_env["resp"] = _Resp(409, {"detail": "Postda skan bor"})
    r = client.post(f"/api/projects/{pid}/mes-send")
    assert r.status_code == 409 and "Postda skan bor" in r.text
    assert client.get(f"/api/projects/{pid}").json().get("mes_sent") is None


def test_fittings_keep_own_name_and_unit(client, proj, mes_env):
    pid, oid = proj
    _cut(client, pid, oid)
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "O", "code": "F", "name": "Furnitura"}).json()
    mats = [dict(code="P1", name="Petlya", unit="шт", qty=8), dict(code="P2", name="Profil", unit="м", qty=2.5)]
    assert client.patch(f"/api/projects/{pid}/operations/{p['operations'][-1]['id']}", json={"o": {"materials": mats}}).status_code == 200
    d = client.get(f"/api/projects/{pid}/mes-package", params={"version": 1, "pp": "none", "mes_order_number": "B-2026-901"}).json()
    assert [(c["name"], c["unit"], c["qty"]) for c in d["consumption"] if c["type"] == "O"] == [("Petlya", "шт", 8), ("Profil", "м", 2.5)]
