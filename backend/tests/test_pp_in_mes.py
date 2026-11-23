"""Stanok postprotsessorlari MES tizimida (2026-11-23, foydalanuvchi qarori): MX da xira va bosilmaydi (403),
MebeliX'ning o'z formatlari (CSV, TXT, DXF, JSON, XNC JSON, MES) va XNC muharriri ishlaydi, MES paketiga stanok fayllari
ICHKARIDA yasalib boradi. Qayta yoqish — `MEBELIX_PP_ENABLED=1` (testlar standart holda shu rejimda: conftest)."""
import base64

import pytest

from test_mes_package_x1018 import proj, reset_access  # noqa: F401 — fixture'lar


@pytest.fixture()
def pp_off(monkeypatch):
    monkeypatch.setenv("MEBELIX_PP_ENABLED", "0")


def test_machines_greyed_and_refused(client, proj, reset_access, pp_off):  # noqa: F811
    pid, cs, xid = proj
    # ro'yxatlar: barcha stanoklar opened=false (xira), o'z formatlarimiz ochiq
    lst = client.get("/api/postprocessors").json()
    machines = [p for p in lst if p.get("machine")]
    assert machines and all(p["opened"] is False and not p["available"] for p in machines)
    assert all(p["opened"] is not False for p in lst if p.get("builtin"))
    xl = client.get("/api/xnc/postprocessors").json()
    assert all(p["opened"] is False for p in xl if p.get("machine"))
    assert any(p.get("builtin") and p["opened"] is not False for p in xl)
    # stanok fayli — 403 «MES tizimida»
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:holzma_ptx"})
    assert r.status_code == 403 and "MES" in r.json()["detail"]
    r = client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:tpa"})
    assert r.status_code == 403
    r = client.get(f"/api/projects/{pid}/postprocess-xnc", params={"key": "machine:tpa", "ops": xid})
    assert r.status_code == 403
    # o'z formatlarimiz ishlaydi
    for k in ("csv", "commands", "dxf", "json"):
        r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": k})
        assert r.status_code == 200, (k, r.text[:200])
    assert client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "json"}).status_code == 200


def test_templates_closed_and_admin_cannot_open(client, proj, reset_access, pp_off):  # noqa: F811
    pid, cs, _xid = proj
    t = client.post("/api/settings/postprocessor", json={"name": "Shablon", "data": {
        "name": "Shablon", "extension": "txt", "template": "{{ project.name }}"}})
    assert t.status_code in (200, 201), t.text
    tid = t.json()["id"]
    try:
        r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"profile_id": tid})
        assert r.status_code == 403 and "MES" in r.json()["detail"]
        assert all(p["opened"] is False for p in client.get("/api/postprocessors").json() if p.get("profile_id") == tid)
        st = client.get("/api/postprocessors/access").json()
        assert st["in_mes"] is True and st["open"] == []
        r = client.put("/api/postprocessors/access", json={"open": ["holzma_ptx"]})
        assert r.status_code == 403 and "MES" in r.json()["detail"]
    finally:
        client.delete(f"/api/settings/postprocessor/{tid}")


def test_mes_package_still_carries_machine_files(client, proj, reset_access, pp_off):  # noqa: F811
    """MX da xira bo'lsa ham MES ga yuboriladigan paketda stanok fayllari bor (MES o'z generatorini tayyorlaguncha)."""
    pid, _cs, _xid = proj
    client.put("/api/postprocessors/machines", json={"enabled": {"holzma_ptx": True, "tpa": True}, "profile": {},
                                                      "prefix": False})
    d = client.get(f"/api/projects/{pid}/mes-package", params={"version": 1}).json()
    keys = {f["machine"]["key"] for f in d["postprocessor_files"]}
    assert keys == {"holzma_ptx", "tpa"}
    assert d["machining"]["saw_ready"] and d["machining"]["cnc_ready"]
    assert all(base64.b64decode(f["content_base64"]) for f in d["postprocessor_files"])
    d = client.get(f"/api/projects/{pid}/mes-package", params={"version": 1, "pp": "machine:holzma_ptx"}).json()
    assert [f["machine"]["key"] for f in d["postprocessor_files"]] == ["holzma_ptx"]


def test_enabled_switch_restores_old_behaviour(client, proj, reset_access, monkeypatch):  # noqa: F811
    pid, cs, _xid = proj
    monkeypatch.setenv("MEBELIX_PP_ENABLED", "1")
    assert client.get("/api/postprocessors/access").json()["in_mes"] is False
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:holzma_ptx"})
    assert r.status_code == 200
