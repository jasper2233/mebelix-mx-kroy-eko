"""Ko'p abonentli rejim (docs/mebelix/Y_MASSHTAB_ABONENTLAR.md): korxonalar bir-birining ma'lumotini ko'rmaydi va o'zgartira olmaydi.
To'liq ajratish (RLS) — PostgreSQL da (`MEBELIX_TEST_DB_URL`); SQLite da — parol xeshi, token ichidagi korxona va bazadagi foydalanuvchi."""
from __future__ import annotations

import threading

import pytest

from app import auth, tenant
from app.db import IS_PG, CompanyRow, SessionLocal, UserRow


def _mk_company(name: str) -> int:
    with tenant.system(), SessionLocal() as s:
        co = CompanyRow(name=name, active=True, plan="")
        s.add(co); s.commit()
        return co.id


def _mk_user(cid: int, login: str, password: str, roles=("admin",)) -> None:
    with tenant.system(), SessionLocal() as s:
        s.add(UserRow(company_id=cid, login=login, password_hash=auth.hash_password(password), name=login,
                      roles=list(roles), active=True))
        s.commit()


@pytest.fixture()
def jwt_env(monkeypatch):
    monkeypatch.setenv("MEBELIX_JWT_SECRET", "t" * 40)
    monkeypatch.delenv("MEBELIX_USERS", raising=False)


def _login(client, login, password):
    r = client.post("/api/auth/login", json={"username": login, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_password_hash_roundtrip():
    h = auth.hash_password("Maxfiy-123")
    assert h.startswith("pbkdf2_sha256$") and "Maxfiy-123" not in h
    assert auth.verify_password("Maxfiy-123", h) and not auth.verify_password("maxfiy-123", h)
    assert not auth.verify_password("x", "buzilgan")


def test_db_user_login_token_has_company(client, jwt_env):
    import uuid
    cid = _mk_company("Sinov korxona A")
    login = f"u_{uuid.uuid4().hex[:8]}"
    _mk_user(cid, login, "Parol-1")
    r = client.post("/api/auth/login", json={"username": login.upper(), "password": "Parol-1"})
    assert r.status_code == 200, r.text
    assert r.json()["cid"] == cid
    assert client.post("/api/auth/login", json={"username": login, "password": "noto'g'ri"}).status_code in (400, 401)
    # o'chirilgan korxona — kira olmaydi
    with tenant.system(), SessionLocal() as s:
        s.get(CompanyRow, cid).active = False; s.commit()
    assert client.post("/api/auth/login", json={"username": login, "password": "Parol-1"}).status_code in (400, 401, 403)


@pytest.mark.skipif(not IS_PG, reason="RLS ajratish — faqat PostgreSQL da")
def test_companies_are_isolated(client, jwt_env):
    import uuid
    a, b = _mk_company("Korxona A"), _mk_company("Korxona B")
    la, lb = f"a_{uuid.uuid4().hex[:6]}", f"b_{uuid.uuid4().hex[:6]}"
    _mk_user(a, la, "pa"); _mk_user(b, lb, "pb")
    ha, hb = _login(client, la, "pa"), _login(client, lb, "pb")
    pa = client.post("/api/projects", json={"name": "A loyiha"}, headers=ha).json()
    pb = client.post("/api/projects", json={"name": "B loyiha"}, headers=hb).json()
    # har korxona raqamlashni o'zidan boshlaydi
    assert pa["number"] == 1000001 and pb["number"] == 1000001
    # ro'yxat: faqat o'zinikini ko'radi
    la_ids = {p["id"] for p in client.get("/api/projects", headers=ha).json()}
    lb_ids = {p["id"] for p in client.get("/api/projects", headers=hb).json()}
    assert pa["id"] in la_ids and pb["id"] not in la_ids
    assert pb["id"] in lb_ids and pa["id"] not in lb_ids
    # boshqa korxona loyihasini o'qish / o'zgartirish / o'chirish — yo'q
    assert client.get(f"/api/projects/{pb['id']}", headers=ha).status_code == 404
    assert client.patch(f"/api/projects/{pb['id']}", json={"name": "buzish"}, headers=ha).status_code in (404, 405, 422)
    assert client.delete(f"/api/projects/{pb['id']}", headers=ha).status_code == 404
    assert client.get(f"/api/projects/{pb['id']}", headers=hb).json()["name"] == "B loyiha"
    # mahalliy (tokensiz) rejim — 1-korxona: yangi korxonalarning loyihalarini ko'rmaydi
    local = {p["id"] for p in client.get("/api/projects").json()}
    assert pa["id"] not in local and pb["id"] not in local
    # sozlamalar ham ajratilgan
    r = client.post("/api/settings/profiles", json={"scope": "print", "name": "A chop", "data": {}}, headers=ha)
    if r.status_code == 200:
        names_b = [x.get("name") for x in client.get("/api/settings/profiles?scope=print", headers=hb).json()]
        assert "A chop" not in names_b


@pytest.mark.skipif(not IS_PG, reason="RLS — faqat PostgreSQL da")
def test_rls_blocks_raw_cross_company_access():
    """Ilova filtri esdan chiqsa ham baza boshqa korxona qatorini bermaydi va unga yozdirmaydi."""
    from sqlalchemy import text
    from app.db import engine
    a, b = _mk_company("RLS A"), _mk_company("RLS B")
    with tenant.use(a), engine.begin() as c:
        c.execute(text("INSERT INTO folders (id, company_id, name, owner) VALUES (:i, :c, 'A papka', '')"),
                  {"i": f"fa{a}", "c": a})
    with tenant.use(b), engine.begin() as c:
        assert c.execute(text("SELECT count(*) FROM folders WHERE id = :i"), {"i": f"fa{a}"}).scalar() == 0
        with pytest.raises(Exception):     # boshqa korxona nomidan yozish — WITH CHECK rad etadi
            c.execute(text("INSERT INTO folders (id, company_id, name, owner) VALUES ('fx', :c, 'x', '')"), {"c": a})
    with tenant.use(a), engine.begin() as c:
        assert c.execute(text("SELECT count(*) FROM folders WHERE id = :i"), {"i": f"fa{a}"}).scalar() == 1


def test_parallel_edits_not_lost(client):
    """Bir loyihaga parallel 20 ta qo'shish (har biri o'z oqimida) — birortasi ham yo'qolmaydi (qulf)."""
    p = client.post("/api/projects", json={"name": "Parallel"}).json()
    pid = p["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L", "name": "L"}).json()
    oid = p["operations"][0]["id"]
    errs = []

    def add(i):
        r = client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[{"name": f"p{i}", "length": 300, "width": 200}])
        if r.status_code != 200:
            errs.append(r.text)
    th = [threading.Thread(target=tenant.bind(add, i)) for i in range(20)]
    [t.start() for t in th]; [t.join() for t in th]
    assert not errs
    parts = client.get(f"/api/projects/{pid}").json()["operations"][0]["parts"]
    assert len(parts) == 20 and len({x["uid"] for x in parts}) == 20
