"""W14 — loyihalar ro'yxati: ustunlar (ID, Владелец, Состояние, Дата, Стоимость, Изменено, Наименование), holat bo'yicha
filtr, «Изменено» (UTC, belgi bilan), «Владелец» to'g'riligi (yaratish, nusxa, MES, import, JWT nomi)."""
import json
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.db import ProjectRow, SessionLocal
from app.services import mes

SECRET = "w14-list-secret-0123456789-abcdefghijklmnop"
COLS = {"id", "number", "owner", "status", "order_date", "cost", "name", "folder_id", "customer", "mes_order_ref",
        "updated_at"}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("MEBELIX_JWT_SECRET", SECRET)
    monkeypatch.setattr(mes, "send_webhook", lambda event, payload, attempts=None: dict(sent=True, attempts=1))


def tok(name, roles=None):
    claims = {"sub": name.lower(), "name": name, "exp": int(time.time()) + 300}
    if roles is not None:
        claims["roles"] = roles
    return {"Authorization": "Bearer " + jwt.encode(claims, SECRET, algorithm="HS256")}


def folder(client, name):
    return client.post("/api/folders", json={"name": name}).json()["id"]


def row(client, pid, **params):
    rows = client.get("/api/projects", params=params).json()
    return next((r for r in rows if r["id"] == pid), None)


# ───────────────────────── ustunlar ─────────────────────────
def test_list_row_has_all_columns(client):
    f = folder(client, "ustunlar")
    p = client.post("/api/projects", json={"name": "Ustun", "folder_id": f, "customer": "Mijoz"}).json()
    rows = client.get("/api/projects", params={"folder_id": f}).json()
    assert len(rows) == 1 and set(rows[0]) == COLS
    r = rows[0]
    assert (r["id"], r["number"], r["owner"], r["status"], r["name"], r["customer"]) == \
        (p["id"], p["number"], "admin", 0, "Ustun", "Mijoz")
    assert r["order_date"] == p["order_date"] and r["cost"] == 0 and r["folder_id"] == f


def test_list_cost_follows_calculation(client, kravat):
    pid, cs, _el = kravat
    assert row(client, pid)["cost"] == 0
    client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_material": {"price": 100000}})
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    full = client.get(f"/api/projects/{pid}").json()
    expect = round(sum(o["cost_material"] + o["cost_operation"] for o in full["operations"]), 2)
    assert expect > 0 and row(client, pid)["cost"] == expect


# ───────────────────────── Изменено (OL-007) ─────────────────────────
def _utc(s):
    assert s.endswith("Z"), s                                   # vaqt zonasi belgisi bor — brauzer to'g'ri o'qiydi
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_changed_column_is_utc_and_moves_on_edit_only(client):
    f = folder(client, "izmenen")
    pid = client.post("/api/projects", json={"name": "Izm", "folder_id": f}).json()["id"]
    t0 = _utc(row(client, pid, folder_id=f)["updated_at"])
    assert abs((datetime.now(timezone.utc) - t0).total_seconds()) < 120          # UTC (mahalliy vaqt emas)
    time.sleep(1.1)
    client.get(f"/api/projects/{pid}")
    client.post(f"/api/projects/{pid}/save")                                       # o'zgarishsiz saqlash
    assert _utc(row(client, pid, folder_id=f)["updated_at"]) == t0                 # ochish/saqlash «Изменено» ni siljitmaydi
    client.patch(f"/api/projects/{pid}", json={"note": "o'zgardi"})
    t1 = _utc(row(client, pid, folder_id=f)["updated_at"])
    assert t1 > t0 and (t1 - t0) < timedelta(minutes=2)


def test_order_status_change_updates_changed_column(client):
    f = folder(client, "izm2")
    pid = client.post("/api/projects", json={"name": "Izm2", "folder_id": f}).json()["id"]
    t0 = _utc(row(client, pid, folder_id=f)["updated_at"])
    time.sleep(1.1)
    client.post(f"/api/projects/{pid}/order", json={"status": 1})
    assert _utc(row(client, pid, folder_id=f)["updated_at"]) > t0


def test_old_row_without_updated_at_lists_as_null(client):
    pid = client.post("/api/projects", json={"name": "Eski"}).json()["id"]
    with SessionLocal() as s:
        r = s.get(ProjectRow, pid)
        r.updated_at = None
        s.commit()
    assert row(client, pid)["updated_at"] is None
    assert client.get(f"/api/projects/{pid}").status_code == 200


# ───────────────────────── Состояние: filtr va ro'yxatda aks etishi ─────────────────────────
def test_status_filter_and_live_status_in_list(client):
    f = folder(client, "holatlar")
    ids = [client.post("/api/projects", json={"name": f"HOLAT-W14-{i}", "folder_id": f}).json()["id"] for i in range(4)]
    client.post(f"/api/projects/{ids[1]}/order", json={"status": 1})
    client.post(f"/api/projects/{ids[2]}/order", json={"status": 2, "ready_date": "2026-12-01"})
    client.post(f"/api/projects/{ids[3]}/order", json={"status": 3})
    allr = client.get("/api/projects", params={"folder_id": f}).json()
    assert [r["status"] for r in allr] == [0, 1, 2, 3]                              # nomer bo'yicha tartib
    for s in range(4):
        got = client.get("/api/projects", params={"folder_id": f, "status": s}).json()
        assert [r["id"] for r in got] == [ids[s]]
    assert client.get("/api/projects", params={"folder_id": f, "status": 9}).json() == []
    # qidiruv + filtr birga (barcha papkalar bo'yicha)
    got = client.get("/api/projects", params={"q": "holat-w14-2", "status": 2}).json()
    assert [r["id"] for r in got] == [ids[2]]
    assert client.get("/api/projects", params={"q": "holat-w14-2", "status": 1}).json() == []
    # orqaga qaytarish ro'yxatda darhol ko'rinadi
    client.post(f"/api/projects/{ids[3]}/order", json={"status": 1})
    assert row(client, ids[3], folder_id=f)["status"] == 1


# ───────────────────────── Владелец ─────────────────────────
def test_owner_create_copy_patch_and_mes(client):
    f = folder(client, "egalar")
    a = client.post("/api/projects", json={"name": "A-loyiha", "folder_id": f}, headers=tok("Aziz")).json()
    assert a["owner"] == "Aziz" and row(client, a["id"], folder_id=f)["owner"] == "Aziz"
    # nusxa — nusxa olgan foydalanuvchi egasi
    c = client.post(f"/api/projects/{a['id']}/copy", params={"folder_id": f}, headers=tok("Bobur")).json()
    assert c["owner"] == "Bobur" and row(client, c["id"], folder_id=f)["owner"] == "Bobur"
    assert row(client, a["id"], folder_id=f)["owner"] == "Aziz"                    # asl loyiha o'zgarmagan
    # tokensiz (lokal) — «admin»; qo'lda berilgan ega — shu
    d = client.post("/api/projects", json={"name": "D", "folder_id": f}).json()
    e = client.post("/api/projects", json={"name": "E", "folder_id": f, "owner": "Sex-2"}).json()
    assert (d["owner"], e["owner"]) == ("admin", "Sex-2")
    client.patch(f"/api/projects/{d['id']}", json={"owner": "Yangi ega"})
    assert row(client, d["id"], folder_id=f)["owner"] == "Yangi ega"
    # egani tarix yozuvi (kim o'zgartirdi) bilan aralashtirmaymiz: holat o'zgartirgan ega bo'lib qolmaydi
    client.post(f"/api/projects/{a['id']}/order", json={"status": 1}, headers=tok("Dilshod", ["texnolog"]))
    assert row(client, a["id"], folder_id=f)["owner"] == "Aziz"
    assert client.get(f"/api/projects/{a['id']}").json()["order_log"][0]["user"] == "Dilshod"
    # MES buyurtmasi — «MES»
    order = {"mes_order_ref": "W14-OWN-1", "name": "MES zakaz", "materials": [{"code": "L16", "name": "L", "thickness": 16}],
             "products": [{"name": "P", "qty": 1, "parts": [{"name": "x", "material_code": "L16", "length": 500, "width": 300}]}]}
    m = client.post("/api/mes/orders", json=order, params={"folder_id": f}).json()
    assert m["owner"] == "MES" and row(client, m["id"], folder_id=f)["owner"] == "MES"


def test_owner_on_import(client):
    """Import: fayldagi ega saqlanadi; bo'sh bo'lsa — import qilgan foydalanuvchi."""
    f = folder(client, "import-egalar")
    pid = client.post("/api/projects", json={"name": "Imp", "folder_id": f}, headers=tok("Aziz")).json()["id"]
    raw = client.get(f"/api/projects/{pid}").json()
    up = lambda body, who: client.post("/api/projects/import", data={"folder_id": f}, headers=tok(who),     # noqa: E731
                                       files={"file": ("p.mxk.json", json.dumps(body).encode(), "application/json")}).json()
    assert up(raw, "Bobur")["owner"] == "Aziz"
    assert up({**raw, "owner": ""}, "Bobur")["owner"] == "Bobur"
