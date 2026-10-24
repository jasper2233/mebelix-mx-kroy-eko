"""W10: `.project` eksporti — REST: fayl yuklab olish, hisobot (ogohlantirishlar), ko'p loyiha ZIP, import bilan aylanma."""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from urllib.parse import unquote

from app.services.project_schema import validate_project_xml


def _export(client, pid, **kw):
    return client.get(f"/api/projects/{pid}/export/project", **kw)


def test_download_is_attachment_with_utf8_xml(client, kravat):
    pid, cs, el = kravat
    r = _export(client, pid)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml") and "utf-8" in r.headers["content-type"].lower()
    cd = r.headers["content-disposition"]
    assert cd.startswith("attachment;") and "filename*=UTF-8''" in cd and cd.split("filename*=UTF-8''")[1].endswith(".project")
    assert r.content.startswith(b'<?xml version="1.0" encoding="UTF-8"?>')
    assert validate_project_xml(r.content) == []
    root = ET.fromstring(r.content)
    assert root.get("name") == "Detskiy kravat" and root.get("version") == "21052101"
    parts = root.findall("good[@typeId='product']/part")
    assert len(parts) == 14 and sum(int(p.get("count")) for p in parts) == 19
    assert {o.get("typeId") for o in root.findall("operation")} == {"CS", "EL"}


def test_filename_non_ascii_name_is_percent_encoded_with_ascii_fallback(client):
    p = client.post("/api/projects", json={"name": "Шкаф №1 / тест"}).json()
    r = _export(client, p["id"])
    cd = r.headers["content-disposition"]
    assert re.search(r'filename="[\x20-\x7e]+\.project"', cd)
    assert unquote(cd.split("filename*=UTF-8''")[1]) == "Шкаф_№1_тест.project"      # bo'shliq → «_» (onlayn eksportdagidek)


def test_unknown_project_is_404(client):
    assert _export(client, "yo'q-loyiha").status_code == 404
    assert client.get("/api/projects/yo'q-loyiha/export/project/report").status_code == 404


def test_report_lists_counts_and_warnings_in_ui_language(client, kravat):
    pid, cs, el = kravat
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize", json={"quality": "fast"}).status_code == 200
    r = client.get(f"/api/projects/{pid}/export/project/report", headers={"Accept-Language": "uz"})
    assert r.status_code == 200
    d = r.json()
    assert d["filename"].endswith(".project") and d["bytes"] > 1000 and d["format_version"] == "21052101"
    assert d["counts"]["part_rows"] == 14 and d["counts"]["operations"] == {"CS": 1, "EL": 1}
    # CS kartalari (MES uchun) faylga yoziladi: «natija yozilmaydi» eslatmasi yo'q; `draw` (chizma) — yo'q
    assert not any(w["code"] == "results_note" for w in d["warnings"])
    body = _export(client, pid).content
    assert b"cMaterialCount" in body and b' data="' in body and b"draw=" not in body


def test_export_then_import_roundtrip_through_api(client, kravat):
    pid, cs, el = kravat
    src = client.get(f"/api/projects/{pid}").json()
    blob = _export(client, pid).content
    r = client.post("/api/projects/import-file", files={"file": ("kravat.project", blob)})
    assert r.status_code == 200, r.text
    new = r.json()["project"]
    assert new["id"] != pid
    s_cs = next(o for o in src["operations"] if o["type"] == "CS")
    n_cs = next(o for o in new["operations"] if o["type"] == "CS")
    key = lambda pt: (pt["name"], pt["length"], pt["width"], pt["qty"], pt["grain"])      # noqa: E731
    assert [key(p) for p in s_cs["parts"]] == [key(p) for p in n_cs["parts"]]
    assert n_cs["cs_cut"]["kerf"] == s_cs["cs_cut"]["kerf"] and n_cs["cs_cut"]["max_rotations"] == s_cs["cs_cut"]["max_rotations"]
    n_el = next(o for o in new["operations"] if o["type"] == "EL")
    edged = [p for p in n_cs["parts"] if p["edge_top"]["op_id"] == n_el["id"] and p["edge_bottom"]["op_id"] == n_el["id"]]
    assert len(edged) == 1 and edged[0]["name"] == "Panel6"
    assert n_el["code"] == "KP-1/19" and n_el["name"] == "PVC 1-19"


def test_one_rotation_survives_export_import_through_api(client, kravat):
    pid, cs, el = kravat
    assert client.patch(f"/api/projects/{pid}/operations/{cs}", json={"cs_cut": {"max_rotations": 1}}).status_code == 200
    blob = _export(client, pid).content
    assert b'swMaxturns="1"' in blob
    new = client.post("/api/projects/import-file", files={"file": ("a.project", blob)}).json()["project"]
    assert next(o for o in new["operations"] if o["type"] == "CS")["cs_cut"]["max_rotations"] == 1


def test_zip_of_several_projects_dedupes_names(client, kravat):
    pid, cs, el = kravat
    other = client.post("/api/projects", json={"name": "Detskiy kravat"}).json()["id"]
    r = client.post("/api/projects/export/project-zip", json={"ids": [pid, other, pid]})
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert names == ["Detskiy_kravat.project", "Detskiy_kravat_(2).project"]            # takroriy id e'tiborga olinmaydi
    for n in names:
        assert validate_project_xml(z.read(n)) == []
    assert client.post("/api/projects/export/project-zip", json={"ids": [pid, "yo'q"]}).status_code == 404
    assert client.post("/api/projects/export/project-zip", json={"ids": []}).status_code == 422


def test_mxk_json_export_still_works(client, kravat):
    pid, cs, el = kravat
    r = client.get(f"/api/projects/{pid}/export")
    assert r.status_code == 200 and r.json()["name"] == "Detskiy kravat"
    assert r.headers["content-disposition"].endswith('.mxk.json"')
