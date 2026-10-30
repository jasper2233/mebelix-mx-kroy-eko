"""«Раскроечные станки» (2026-10-30, xodim loyihasi «1275»): operator loyihada pilani o'zgartirsa — faqat o'sha loyihada;
yangi CS / import stanok standartidan; standart faqat /saw-machines orqali (login paroli bilan; tokensiz rejimda parolsiz)."""


def _cs(p, cs):
    return next(o for o in p["operations"] if o["id"] == cs)


def _new_cs(client):
    p = client.post("/api/projects", json={"name": "pila"}).json()
    p = client.post(f"/api/projects/{p['id']}/operations", json={"type": "CS", "name": "LDSP"}).json()
    return p["id"], p["operations"][-1]


def test_operator_kerf_change_stays_in_project(client):
    pid, op = _new_cs(client)
    base = op["cs_cut"]["kerf"]
    assert op["cs_cut"]["machine_id"]
    client.patch(f"/api/projects/{pid}/operations/{op['id']}", json={"cs_cut": {"kerf": base + 3, "max_rotations": 2}})
    # keyingi loyiha — stanok standarti (operator o'zgarishi o'tmaydi)
    _pid2, op2 = _new_cs(client)
    assert op2["cs_cut"]["kerf"] == base and op2["cs_cut"]["max_rotations"] != 2
    # birinchi loyihada o'zgarish saqlangan
    assert _cs(client.get(f"/api/projects/{pid}").json(), op["id"])["cs_cut"]["kerf"] == base + 3


def test_standard_changes_only_via_machines_api(client):
    r = client.put("/api/settings/saw_machines/default", json={"machines": []})
    assert r.status_code == 403
    sm = client.get("/api/saw-machines").json()
    main = next(m for m in sm["machines"] if m["id"] == sm["default_id"])
    r = client.post("/api/saw-machines/save", json={"password": "", "machine": {"id": main["id"], "name": "KS832", "cut": {**main["cut"], "kerf": 4.4}}})
    assert r.status_code == 200, r.text
    m = next(x for x in r.json()["machines"] if x["id"] == main["id"])
    assert m["cut"]["kerf"] == 4.4 and m["name"] == "KS832" and m["updated_at"]
    _pid, op = _new_cs(client)
    assert op["cs_cut"]["kerf"] == 4.4
    # ikkinchi stanok + loginning o'z tanlovi
    r = client.post("/api/saw-machines/save", json={"machine": {"name": "Altendorf", "cut": {**main["cut"], "kerf": 3.2}}}).json()
    alt = next(x for x in r["machines"] if x["name"] == "Altendorf")
    client.put("/api/saw-machines/me", json={"machine_id": alt["id"]})
    _pid, op = _new_cs(client)
    assert op["cs_cut"]["kerf"] == 3.2 and op["cs_cut"]["machine_id"] == alt["id"]
    client.put("/api/saw-machines/me", json={"machine_id": None})
    r = client.post(f"/api/saw-machines/{alt['id']}/delete", json={})
    assert r.status_code == 200
    # standartni qaytarish (boshqa testlarga ta'sir qilmasin)
    client.post("/api/saw-machines/save", json={"machine": {"id": main["id"], "name": main["name"], "cut": main["cut"]}})


def test_password_checked_when_auth_enabled(monkeypatch):
    import pytest
    from fastapi import HTTPException
    from app import auth
    monkeypatch.setattr(auth, "password_required", lambda: True)
    monkeypatch.setattr(auth, "db_user", lambda login: None)
    monkeypatch.setattr(auth, "login_users", lambda: {"oper": ("sir123", ["admin"])})
    user = {"sub": "oper", "roles": ["admin"], "read_only": False}
    auth.confirm_password(user, "sir123")
    with pytest.raises(HTTPException) as e:
        auth.confirm_password(user, "xato")
    assert e.value.status_code == 403
    with pytest.raises(HTTPException):
        auth.confirm_password({"sub": "v", "roles": ["viewer"], "read_only": True}, "sir123")


def test_password_checked_by_mes_in_sso_mode(monkeypatch):
    """MES SSO (ochiq kalit): MX da parol yo'q — login + parolni MES `/integ/kroy/parol-tekshir` tekshiradi;
    MES javob bermasa yoki sozlanmagan bo'lsa standart parolsiz o'zgarmaydi."""
    import httpx
    import pytest
    from fastapi import HTTPException
    from app import auth
    monkeypatch.delenv("MEBELIX_JWT_SECRET", raising=False)
    monkeypatch.setenv("MEBELIX_JWT_PUBLIC_KEY", "-----BEGIN PUBLIC KEY-----x")
    monkeypatch.setenv("MES_WEBHOOK_URL", "http://mes/api/v1/integ/kroy/webhook")
    monkeypatch.setenv("MES_API_TOKEN", "tok")
    assert auth.password_required() and auth.mes_password_url() == "http://mes/api/v1/integ/kroy/parol-tekshir"
    calls = []

    def post(url, json, headers, timeout):
        calls.append((url, json, headers.get("Authorization")))
        return httpx.Response(200, json={"ok": json["password"] == "mes-parol"})

    monkeypatch.setattr(httpx, "post", post)
    user = {"sub": "texnolog1", "roles": ["texnolog"], "read_only": False}
    auth.confirm_password(user, "mes-parol")
    assert calls[-1] == ("http://mes/api/v1/integ/kroy/parol-tekshir", {"login": "texnolog1", "password": "mes-parol"},
                         "Bearer tok")
    for pw in ("xato", None, ""):
        with pytest.raises(HTTPException) as e:
            auth.confirm_password(user, pw)
        assert e.value.status_code == 403
    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(429, json={}))
    with pytest.raises(HTTPException) as e:
        auth.confirm_password(user, "mes-parol")
    assert e.value.status_code == 429

    def down(*a, **k):
        raise httpx.ConnectError("yo'q")

    monkeypatch.setattr(httpx, "post", down)
    with pytest.raises(HTTPException) as e:
        auth.confirm_password(user, "mes-parol")
    assert e.value.status_code == 503
    monkeypatch.delenv("MES_WEBHOOK_URL")
    with pytest.raises(HTTPException) as e:
        auth.confirm_password(user, "mes-parol")
    assert e.value.status_code == 503
