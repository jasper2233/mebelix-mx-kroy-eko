"""Kirish oynasi (2026-10-18): MEBELIX_USERS login/parol → JWT; MEBELIX_AUTH_REQUIRED=1 da tokensiz 401;
MEBELIX_AUTH_LOCAL=1 — shu kompyuterdan (tunnel sarlavhasisiz) tokensiz."""
import pytest

SECRET = "login-secret-for-tests-0123456789"


@pytest.fixture()
def auth_on(monkeypatch):
    monkeypatch.setenv("MEBELIX_AUTH_REQUIRED", "1")
    monkeypatch.setenv("MEBELIX_JWT_SECRET", SECRET)
    monkeypatch.setenv("MEBELIX_USERS", "mebelix:mebelix,ali:1234:viewer")


def test_login_off_by_default(client):
    assert client.get("/api/auth/config").json() == {"login": False}
    assert client.post("/api/auth/login", json={"username": "a", "password": "b"}).status_code == 404


def test_login_flow(client, auth_on):
    assert client.get("/api/auth/config").json() == {"login": True}
    assert client.get("/api/me").status_code == 401
    assert client.post("/api/auth/login", json={"username": "mebelix", "password": "wrong"}).status_code == 401
    r = client.post("/api/auth/login", json={"username": "mebelix", "password": "mebelix"})
    assert r.status_code == 200
    me = client.get("/api/me", headers={"Authorization": "Bearer " + r.json()["token"]}).json()
    assert me["name"] == "mebelix" and me["roles"] == ["admin"] and not me["read_only"]


def test_login_viewer_is_read_only(client, auth_on):
    tok = client.post("/api/auth/login", json={"username": "ali", "password": "1234"}).json()["token"]
    h = {"Authorization": "Bearer " + tok}
    assert client.get("/api/me", headers=h).json()["read_only"] is True
    assert client.post("/api/projects", json={"name": "x"}, headers=h).status_code == 403


def test_local_bypass_not_through_tunnel(client, auth_on, monkeypatch):
    monkeypatch.setenv("MEBELIX_AUTH_LOCAL", "1")
    # TestClient mijozi «testclient» — mahalliy emas
    assert client.get("/api/me").status_code == 401
    from app import auth
    monkeypatch.setattr(auth, "_local_ok", lambda req: "cf-connecting-ip" not in req.headers)
    assert client.get("/api/me").status_code == 200
    assert client.get("/api/me", headers={"Cf-Connecting-IP": "1.2.3.4"}).status_code == 401
