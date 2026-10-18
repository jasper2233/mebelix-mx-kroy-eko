"""Postprotsessor stanoklari ro'yxati va «MES integratsiyasi» bayrog'i (v2.2)."""
import zipfile
import io


def _machines(client):
    return client.get("/api/postprocessors/machines").json()


def _flat(d):
    return {m["key"]: m for g in d["groups"] for m in g["machines"]}


def test_machine_list_has_all_names(client):
    d = _machines(client)
    assert [g["key"] for g in d["groups"]] == ["saw", "cnc"]
    flat = _flat(d)
    for name in ("SCM WinCut", "HOLZMA PTX", "Biesse OSI", "Homag CHF 41/44/44 NPS400", "ELMO 3", "GlassGCODE"):
        assert name in {m["name"] for m in flat.values()}
    assert not any(m["enabled"] or m["bound"] for m in flat.values())       # boshida hammasi o'chiq / ulanmagan
    assert d["prefix"] is False


def test_machine_enable_bind_and_download(client, kravat):
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    # o'rnatilgan formati yo'q stanok (ELMO 3): o'chiq yoki shablon ulanmagan bo'lsa yuklab bo'lmaydi
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:elmo3")
    assert r.status_code == 403         # 2026-10-18: yoqilmagan, generatorsiz stanok standart holatda mijoz uchun ochilmagan (pp_access)
    # o'rnatilgan format (v2.5, namunalardan — masalan SCM WinCut): shablonsiz ham ishlaydi, faylda «GibLab» yo'q
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:scm_wincut")
    assert r.status_code == 200 and b"GibLab" not in r.content
    prof = client.post("/api/settings/postprocessor", json={"name": "SCM test", "data": {
        "name": "SCM test", "extension": "scm", "per_map": False,
        "template": "{% for m in maps %}S;{{ f(m.sheet_length) }}\n{% endfor %}"}}).json()
    d = client.put("/api/postprocessors/machines", json={"enabled": {"elmo3": True}, "profile": {}, "prefix": False}).json()
    assert _flat(d)["elmo3"]["enabled"] and not _flat(d)["elmo3"]["bound"]
    lst = client.get("/api/postprocessors").json()
    row = next(x for x in lst if x["key"] == "machine:elmo3")
    assert row["machine"] and row["available"] is False
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:elmo3")
    assert r.status_code == 400                                              # shablon ulanmagan
    d = client.put("/api/postprocessors/machines", json={"enabled": {"elmo3": True},
                                                          "profile": {"elmo3": prof["id"]}, "prefix": True}).json()
    m = _flat(d)["elmo3"]
    assert m["bound"] and m["profile_name"] == "SCM test" and d["prefix"] is True
    row = next(x for x in client.get("/api/postprocessors").json() if x["key"] == "machine:elmo3")
    assert row["available"] is True and row["extension"] == "scm"
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:elmo3")
    assert r.status_code == 200
    assert "ELMO_3_" in r.headers["content-disposition"]                  # fayl nomi prefiksi
    assert r.content.decode().startswith("S;2750")
    # tozalash
    client.put("/api/postprocessors/machines", json={"enabled": {}, "profile": {}, "prefix": False})
    client.delete(f"/api/settings/postprocessor/{prof['id']}")


def test_machine_validation(client):
    r = client.put("/api/postprocessors/machines", json={"enabled": {"nope": True}, "profile": {}, "prefix": False})
    assert r.status_code == 400
    r = client.put("/api/postprocessors/machines", json={"enabled": {}, "profile": {"scm_wincut": 999999}, "prefix": False})
    assert r.status_code == 404
    r = client.get("/api/projects/x/operations/y/postprocess?key=machine:nope")
    assert r.status_code in (400, 404)


def test_mes_enabled_flag(client):
    d = client.get("/api/settings/app/default").json()
    assert d["mes_enabled"] is False
    d["mes_enabled"] = True
    assert client.put("/api/settings/app/default", json=d).status_code == 200
    assert client.get("/api/settings/app/default").json()["mes_enabled"] is True
    d["mes_enabled"] = False
    client.put("/api/settings/app/default", json=d)
    assert client.get("/api/settings/app/default").json()["mes_enabled"] is False
