"""Stanok formati kesim darajasini cheklasa — kroy avtomatik qayta bajariladi (X-PP-Refit); Felder F4Classic generatori."""
import io
import zipfile


def _cut(client, kravat, rot: int):
    pid, cs, _el = kravat
    assert client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"max_rotations": rot}}).status_code == 200
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize").status_code == 200
    return pid, cs


def _op(client, pid, oid):
    return next(x for x in client.get(f"/api/projects/{pid}").json()["operations"] if x["id"] == oid)


def test_fastpanel_refits_rotations_to_three(client, kravat):
    pid, cs = _cut(client, kravat, 5)
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:fastpanel"})
    assert r.status_code == 200, r.text
    assert r.headers.get("X-PP-Refit") == "3"
    o = _op(client, pid, cs)
    assert o["cs_cut"]["max_rotations"] == 3 and o["result"]["maps"]
    r2 = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:fastpanel"})
    assert r2.status_code == 200 and "X-PP-Refit" not in r2.headers       # endi mos — qayta kroy yo'q


def test_no_refit_when_within_limit(client, kravat):
    pid, cs = _cut(client, kravat, 4)
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:holzma_ptx"})
    assert r.status_code == 200 and "X-PP-Refit" not in r.headers
    assert _op(client, pid, cs)["cs_cut"]["max_rotations"] == 4


def test_f4classic_txt_per_map(client, kravat):
    pid, cs = _cut(client, kravat, 3)
    r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess", params={"key": "machine:felder_f4classic"})
    assert r.status_code == 200, r.text
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert names and all(n.endswith(".txt") for n in names)
    lines = z.read(names[0]).decode("cp1251").split("\r\n")
    assert lines[0] == "PR_VERSIONE = 12" and lines[15] == "PR_TAGLI = "
    assert lines[16].startswith("0, ") and any(",  , " in x for x in lines[16:])
    assert all("GibLab" not in x for x in lines)


def test_xnc_project_zip_only_selected_ops(client, kravat):
    """«Операции» oynasida belgilangan XNC dasturlari — faqat ular zip ga tushadi (`ops`)."""
    pid, cs, _el = kravat
    ids = []
    for nm in ("x1", "x2", "x3"):
        p = client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "code": f"C_{nm}", "name": nm}).json()
        xid = p["operations"][-1]["id"]
        ids.append(xid)
        prog = [dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, D=8), comment="", children=[])]
        assert client.patch(f"/api/projects/{pid}/operations/{xid}",
                            json={"xnc": {"length": 400, "width": 300, "thickness": 16, "program": prog}}).status_code == 200
    r = client.get(f"/api/projects/{pid}/postprocess-xnc", params={"key": "machine:tpa", "ops": ",".join(ids[:2])})
    assert r.status_code == 200, r.text
    names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert len(names) == 2 and any("C_x1" in n for n in names) and not any("C_x3" in n for n in names)
    r = client.get(f"/api/projects/{pid}/postprocess-xnc", params={"key": "machine:tpa"})
    assert len(zipfile.ZipFile(io.BytesIO(r.content)).namelist()) == 3


def test_machine_tools_table_roundtrip(client):
    """«Инструменты» jadvali: standart qatorlar, saqlash, nostandart diametr, noto'g'ri kalit."""
    base = "/api/postprocessors/machines/woodwop/tools"
    r = client.get(base)
    assert r.status_code == 200 and any(x["key"] == "mill:front:8" for x in r.json()["rows"])
    r = client.put(base, json={"tools": {"mill:front:8": "101", "drill:front:12": " 7 ", "saw:front:4": ""}})
    assert r.status_code == 200
    got = {x["key"]: x["ref"] for x in r.json()["rows"]}
    assert got["mill:front:8"] == "101" and got["drill:front:12"] == "7" and got["saw:front:4"] == ""
    assert client.put(base, json={"tools": {"laser:front:8": "1"}}).status_code == 400
    assert client.put(base, json={"tools": {}}).status_code == 200
    assert client.get("/api/postprocessors/machines/nope/tools").status_code == 400


def test_order_text_prefers_current_project_name():
    from app.models import Project
    from app.services.ppfmt import order_text
    assert order_text(Project(name="Yangi nom"), "9001 eski") == "Yangi nom"
    assert order_text(Project(name="9001_mijoz"), "9001 mijoz") == "9001 mijoz"      # faqat «_» farqi — yozuv shakli saqlanadi
    assert order_text(Project(name=""), "9001 eski") == "9001 eski"


def test_rot_limit_by_version():
    from app.services import ppfmt
    assert ppfmt.rot_limit("fastpanel", {"version": "2.1.5"}) == 3 and ppfmt.rot_limit("fastpanel", {"version": "2.1.4"}) == 2
    assert ppfmt.rot_limit("scheer") == 3 and ppfmt.rot_limit("holzma_ptx") is None
