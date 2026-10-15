"""W18 / WP-C: «Импорт из других программ» infratuzilmasi — format katalogi (holat `ready` / `no_module`), parametrlar sxemasi,
import profillari (settings `import_profile`), profillarni JSON/XML ga eksport va import (IMP-006), `/import/run`,
plagin reestri (dinamik), umumiy sozlama `import_settings` (katalog ildiz kategoriya ID lari serverda)."""
from __future__ import annotations

import io
import json
import xml.etree.ElementTree as ET

import pytest
from openpyxl import Workbook

from app import plugins
from app.models import Project
from app.services import import_formats as F
from app.services import import_settings

UZ = {"Accept-Language": "uz"}
SEVEN = ["pro100", "imos", "bazis", "bcad", "woody2", "woodwop", "ilenia"]


# ───────────────────────── yordamchilar ─────────────────────────
@pytest.fixture()
def clean_profiles(client):
    """Har test oldidan/keyin import profillari bo'sh (bazasi sessiya bo'yicha umumiy)."""
    def wipe():
        for r in client.get("/api/settings/import_profile").json():
            client.delete(f"/api/settings/import_profile/{r['id']}")
    wipe()
    yield
    wipe()


def _prof(client, name, params=None, fmt="project"):
    return client.post("/api/settings/import_profile", json={"name": name, "data": {"format": fmt, "params": params or {}}})


def _sample_project(client) -> bytes:
    """CS + EL + XNC + O + CL ($API orqali) → `.project` baytlari (W10 eksporti); CL da hisoblanmagan (manfiy) detal bor."""
    p = client.post("/api/projects", json={"name": "W18 namuna"}).json()
    pid = p["id"]
    client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "code": "K1", "name": "PVC 1"})
    cs = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "LDSP"}).json()["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[dict(name="A", length=700, width=500, qty=2)])
    client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "code": "X1", "name": "Teshik"})
    client.post(f"/api/projects/{pid}/operations", json={"type": "O", "name": "Furnitura"})
    cl = client.post(f"/api/projects/{pid}/operations", json={"type": "CL", "name": "Plintus"}).json()["operations"][-1]["id"]
    client.post(f"/api/projects/{pid}/operations/{cl}/parts", json=[dict(name="P1", length=1200, width=0, qty=3)])
    r = client.get(f"/api/projects/{pid}/export/project")
    assert r.status_code == 200, r.text[:300]
    return r.content


def _types(project: dict) -> list[str]:
    return [o["type"] for o in project["operations"]]


def _run(client, data, name="n.project", **form):
    return client.post("/api/import/run", files={"file": (name, data)}, data={k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in form.items()})


# ───────────────────────── katalog ─────────────────────────
def test_catalog_lists_project_plus_seven_formats_with_status_and_icons(client):
    cat = client.get("/api/import/catalog").json()
    by = {x["key"]: x for x in cat}
    assert list(by)[:8] == ["project", *SEVEN]
    assert by["project"]["status"] == "ready" and by["project"]["exts"] == [".project"] and by["project"]["n_params"] == 6
    assert by["project"]["reason"] == ""
    for k in SEVEN:
        assert by[k]["status"] == "no_module" and by[k]["n_params"] == 0 and by[k]["icon"]
        assert "образец файла" in by[k]["reason"]
    assert by["bazis"]["exts"] == [".xml", ".obl"] and by["woody2"]["exts"] == [".xml", ".wes"] and by["pro100"]["exts"] == [".sto"]
    assert {x["icon"] for x in cat} >= {"file-code", "box", "ruler"}
    assert len({x["icon"] for x in cat}) == len(cat)                      # har formatga o'z ikonkasi
    uz = {x["key"]: x for x in client.get("/api/import/catalog", headers=UZ).json()}
    assert "namuna fayl" in uz["imos"]["reason"] and "образец" not in uz["imos"]["reason"]
    # interfeysda «GibLab» so'zi yo'q
    assert "giblab" not in json.dumps(cat, ensure_ascii=False).lower()


def test_schema_project_groups_types_defaults_and_help(client):
    s = client.get("/api/import/formats/project/schema").json()
    assert s["status"] == "ready" and s["values"] == s["defaults"] and s["modified"] == []
    assert [g["key"] for g in s["groups"]] == ["ops", "cl"]
    ops = {p["key"]: p for p in s["groups"][0]["params"]}
    assert set(ops) == {"import_xnc", "import_o", "import_sp", "import_cl", "import_lb"}
    assert all(p["type"] == "bool" and p["default"] is True and p["help"]["ru"] and p["help"]["uz"] for p in ops.values())
    neg = s["groups"][1]["params"][0]
    assert neg["key"] == "cl_negative_length" and neg["type"] == "choice" and neg["default"] == "uncomputed"
    assert [o["value"] for o in neg["options"]] == ["uncomputed", "abs"]
    assert s["help"]["ru"] and s["help"]["uz"]


def test_schema_of_unavailable_format_is_dimmed_and_empty_and_unknown_is_404(client):
    s = client.get("/api/import/formats/imos/schema").json()
    assert s["status"] == "no_module" and s["groups"] == [] and s["values"] == {} and ".fxm" in s["exts"]
    assert "образец файла" in s["reason"] and "образец" in s["help"]["ru"]
    assert client.get("/api/import/formats/nope/schema").status_code == 404


# ───────────────────────── parametrlarni tekshirish ─────────────────────────
def test_validate_params_strict_types_unknown_keys_and_choices():
    clean, errs = F.validate_params("project", {"import_xnc": False, "cl_negative_length": "abs"})
    assert clean == {"import_xnc": False, "cl_negative_length": "abs"} and errs == []
    _c, errs = F.validate_params("project", {"import_xnc": "false", "zzz": 1, "cl_negative_length": "sqrt", "import_o": 0})
    assert {e["key"] for e in errs} == {"import_xnc", "zzz", "cl_negative_length", "import_o"}      # matn/son bool emas, noma'lum kalit, variant
    _c, errs = F.validate_params("project", [1, 2])
    assert errs and errs[0]["key"] == ""
    _c, errs = F.validate_params("ghost", {})
    assert errs and "ghost" in errs[0]["message"]
    assert F.validate_params("imos", {"x": 1})[1]                                      # modulsiz formatda parametr yo'q


def test_resolve_values_layers_defaults_profile_overrides_and_ignores_stale_saved():
    v = F.resolve_values("project", {"import_xnc": False, "legacy_key": 1, "import_o": "bad"}, {"import_lb": False})
    assert v["import_xnc"] is False and v["import_lb"] is False and v["import_o"] is True and "legacy_key" not in v
    with pytest.raises(ValueError):
        F.resolve_values("project", None, {"import_xnc": "no"})
    assert F.sparse("project", {"import_xnc": True, "import_o": False}) == {"import_o": False}


# ───────────────────────── profillar: CRUD ─────────────────────────
def test_profile_crud_through_settings_scope_is_sparse_and_validated(client, clean_profiles):
    r = _prof(client, "Faqat detallar", {"import_xnc": False, "import_o": True, "import_cl": False})
    assert r.status_code == 200, r.text
    row = r.json()
    assert row["scope"] == "import_profile" and row["data"] == {"format": "project", "params": {"import_xnc": False, "import_cl": False}}
    # o'zgartirish (yo'q qiymatlar standartga qaytadi)
    up = client.put(f"/api/settings/import_profile/{row['id']}", json={"name": "Detal", "data": {"format": "project", "params": {"import_sp": False}}})
    assert up.status_code == 200 and up.json()["name"] == "Detal" and up.json()["data"]["params"] == {"import_sp": False}
    listed = client.get("/api/import/profiles").json()
    assert [(x["name"], x["format"], x["params"]) for x in listed] == [("Detal", "project", {"import_sp": False})]
    assert client.get("/api/import/profiles", params={"format": "imos"}).json() == []
    # yaroqsiz: noma'lum parametr / tur / noma'lum format — 400, hech narsa saqlanmaydi
    assert _prof(client, "Bad1", {"import_xnc": "yo'q"}).status_code == 400
    assert _prof(client, "Bad2", {"zzz": True}).status_code == 400
    assert _prof(client, "Bad3", {}, fmt="ghost").status_code == 400
    assert _prof(client, "Bad4", {"x": 1}, fmt="imos").status_code == 400
    bad = _prof(client, "Bad5", {"import_xnc": 5})
    assert bad.status_code == 400 and bad.json()["detail"]
    assert len(client.get("/api/import/profiles").json()) == 1
    assert client.delete(f"/api/settings/import_profile/{row['id']}").status_code == 200
    assert client.get("/api/import/profiles").json() == []


def test_schema_with_profile_applies_saved_values(client, clean_profiles):
    pid = _prof(client, "P", {"import_lb": False, "cl_negative_length": "abs"}).json()["id"]
    s = client.get("/api/import/formats/project/schema", params={"profile_id": pid}).json()
    assert s["values"]["import_lb"] is False and s["values"]["cl_negative_length"] == "abs" and s["values"]["import_xnc"] is True
    assert sorted(s["modified"]) == ["cl_negative_length", "import_lb"]
    flat = {p["key"]: p for g in s["groups"] for p in g["params"]}
    assert flat["import_lb"]["modified"] is True and flat["import_lb"]["default"] is True
    assert client.get("/api/import/formats/project/schema", params={"profile_id": 99999}).status_code == 404


# ───────────────────────── profillarni eksport / import (IMP-006) ─────────────────────────
def test_export_json_has_all_values_and_roundtrips_with_replace(client, clean_profiles):
    _prof(client, "A", {"import_xnc": False})
    _prof(client, "B", {"cl_negative_length": "abs"})
    r = client.get("/api/import/profiles/export")
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/json")
    assert 'filename="import_profiles.json"' in r.headers["content-disposition"]
    doc = r.json()
    assert doc["app"] == "MebeliX Kroy" and doc["kind"] == "import_profiles" and doc["version"] == 1
    pa = next(p for p in doc["profiles"] if p["name"] == "A")
    assert pa["params"]["import_xnc"] is False and pa["params"]["import_o"] is True and len(pa["params"]) == 6      # hammasi aniq
    # bo'shatamiz va yuklaymiz → created
    for x in client.get("/api/import/profiles").json():
        client.delete(f"/api/settings/import_profile/{x['id']}")
    rep = client.post("/api/import/profiles/import", files={"file": ("p.json", r.content)}).json()
    assert (rep["created"], rep["replaced"], rep["invalid"], rep["total"]) == (2, 0, [], 2)
    got = {x["name"]: x["params"] for x in client.get("/api/import/profiles").json()}
    assert got == {"A": {"import_xnc": False}, "B": {"cl_negative_length": "abs"}}               # saqlashda siyrak
    # qayta yuklash: replace (standart) / skip / rename
    assert client.post("/api/import/profiles/import", files={"file": ("p.json", r.content)}).json()["replaced"] == 2
    assert client.post("/api/import/profiles/import", files={"file": ("p.json", r.content)}, data={"on_conflict": "skip"}).json()["skipped"] == 2
    rn = client.post("/api/import/profiles/import", files={"file": ("p.json", r.content)}, data={"on_conflict": "rename"}).json()
    assert rn["renamed"] == 2 and len(client.get("/api/import/profiles").json()) == 4
    assert {x["name"] for x in client.get("/api/import/profiles").json()} == {"A", "B", "A (2)", "B (2)"}
    assert client.post("/api/import/profiles/import", files={"file": ("p.json", r.content)}, data={"on_conflict": "zzz"}).status_code == 400


def test_export_xml_roundtrip_and_filters(client, clean_profiles):
    ia = _prof(client, "Mijoz 1", {"import_o": False, "import_sp": False}).json()["id"]
    _prof(client, "Mijoz 2", {"cl_negative_length": "abs"})
    r = client.get("/api/import/profiles/export", params={"as": "xml", "ids": str(ia)})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    assert r.headers["content-disposition"].endswith('.xml"')
    root = ET.fromstring(r.content)
    assert root.tag == "importProfiles" and root.get("app") == "MebeliX Kroy" and root.get("version") == "1"
    profs = root.findall("profile")
    assert [p.get("name") for p in profs] == ["Mijoz 1"] and profs[0].get("format") == "project"
    vals = {q.get("key"): (q.get("type"), q.get("value")) for q in profs[0].findall("param")}
    assert vals["import_o"] == ("bool", "false") and vals["cl_negative_length"] == ("choice", "uncomputed") and len(vals) == 6
    # eksport formati/format filtri
    assert client.get("/api/import/profiles/export", params={"as": "csv"}).status_code == 400
    assert client.get("/api/import/profiles/export", params={"format": "imos"}).json()["profiles"] == []
    # XML ni qayta yuklash
    client.delete(f"/api/settings/import_profile/{ia}")
    rep = client.post("/api/import/profiles/import", files={"file": ("p.xml", r.content)}).json()
    assert rep["created"] == 1 and rep["invalid"] == []
    back = next(x for x in client.get("/api/import/profiles").json() if x["name"] == "Mijoz 1")
    assert back["params"] == {"import_o": False, "import_sp": False}


def test_import_profiles_reports_invalid_items_and_rejects_garbage(client, clean_profiles):
    doc = {"app": "x", "profiles": [
        {"name": "OK", "format": "project", "params": {"import_lb": False}},
        {"name": "", "format": "project", "params": {}},
        {"name": "Noma'lum format", "format": "ghost", "params": {}},
        {"name": "Yomon tur", "format": "project", "params": {"import_xnc": "ha"}},
        {"name": "Yomon kalit", "format": "project", "params": {"bor_emas": True}},
        "matn"]}
    rep = client.post("/api/import/profiles/import", files={"file": ("p.json", json.dumps(doc).encode())}).json()
    assert rep["created"] == 1 and rep["total"] == 6 and len(rep["invalid"]) == 5
    assert {x["name"] for x in rep["invalid"]} >= {"", "Noma'lum format", "Yomon tur", "Yomon kalit"}
    assert [x["name"] for x in client.get("/api/import/profiles").json()] == ["OK"]
    for blob in (b"\x00\x01garbage", b"[1,2]", b'{"profiles": 5}', b"<project/>", b"<importProfiles><profile"):
        assert client.post("/api/import/profiles/import", files={"file": ("p", blob)}).status_code == 400, blob
    # XML da tashqi/ichki «entity» (XXE, billion laughs) — rad etiladi
    xxe = b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY e SYSTEM "file:///etc/passwd">]><importProfiles><profile name="&e;" format="project"/></importProfiles>'
    assert client.post("/api/import/profiles/import", files={"file": ("p.xml", xxe)}).status_code == 400
    # XML da noto'g'ri qiymat turi — shu profil invalid, qolganlari yuklanadi
    xml = (b'<importProfiles><profile name="X1" format="project"><param key="import_xnc" type="bool" value="maybe"/></profile>'
           b'<profile name="X2" format="project"><param key="import_xnc" type="bool" value="false"/></profile></importProfiles>')
    rep = client.post("/api/import/profiles/import", files={"file": ("p.xml", xml)}).json()
    assert rep["created"] == 1 and [x["name"] for x in rep["invalid"]] == ["X1"]


def test_import_profiles_file_size_and_count_limits(client, clean_profiles):
    big = json.dumps({"profiles": [{"name": f"p{i}", "format": "project", "params": {}} for i in range(F.MAX_PROFILES_IN_FILE + 1)]}).encode()
    assert client.post("/api/import/profiles/import", files={"file": ("p.json", big)}).status_code == 400
    huge = b" " * (F.MAX_PROFILE_FILE + 10)
    assert client.post("/api/import/profiles/import", files={"file": ("p.json", huge)}).status_code == 400
    assert client.get("/api/import/profiles").json() == []


# ───────────────────────── import (run) ─────────────────────────
def test_run_default_imports_everything_and_reports_options(client):
    blob = _sample_project(client)
    r = _run(client, blob, "w18.project", format="project")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["format"] == "project" and d["options"]["import_xnc"] is True
    assert set(_types(d["project"])) == {"CS", "EL", "XNC", "O", "CL"}
    assert d["project"]["id"] and d["project"]["name"] == "W18 namuna"


def test_run_params_skip_operation_types_with_one_warning_per_type(client):
    blob = _sample_project(client)
    r = _run(client, blob, format="project", params={"import_xnc": False, "import_o": False, "import_cl": False})
    assert r.status_code == 200, r.text
    d = r.json()
    assert set(_types(d["project"])) == {"CS", "EL"}
    texts = " | ".join(d["warnings"])
    assert "XNC" in texts and "O" in texts and "CL" in texts
    assert sum("по параметрам импорта" in w for w in d["warnings"]) == 3
    # LB / SP kalitlari ham ishlaydi (namunada ular yo'q — xatosiz o'tadi)
    assert _run(client, blob, format="project", params={"import_lb": False, "import_sp": False}).status_code == 200


def test_run_profile_then_overrides_win(client, clean_profiles):
    blob = _sample_project(client)
    pid = _prof(client, "Faqat CS", {"import_xnc": False, "import_o": False}).json()["id"]
    d = _run(client, blob, format="project", profile_id=str(pid)).json()
    assert "XNC" not in _types(d["project"]) and "O" not in _types(d["project"]) and "CL" in _types(d["project"])
    d = _run(client, blob, format="project", profile_id=str(pid), params={"import_xnc": True}).json()
    assert "XNC" in _types(d["project"]) and "O" not in _types(d["project"])
    assert d["options"]["import_xnc"] is True and d["options"]["import_o"] is False
    assert _run(client, blob, format="project", profile_id="99999").status_code == 404
    imos = _prof(client, "Boshqa", {}, fmt="woody2").status_code
    assert imos == 200                                                    # modulsiz format uchun bo'sh profil mumkin
    other = client.get("/api/import/profiles", params={"format": "woody2"}).json()[0]["id"]
    assert _run(client, blob, format="project", profile_id=str(other)).status_code == 404       # profil boshqa formatniki


def test_run_cl_negative_length_option_switches_rule(client):
    xml = ("""<?xml version="1.0" encoding="UTF-8"?>
<project name="neg" currency="сум" version="23051701">
 <good typeId="product" id="1" name="Shkaf" count="1">
  <part id="10" code="c1" name="Plintus" l="-350" w="7" dl="-350" dw="7" jl="-350" jw="7" count="1"/>
  <part id="11" code="c2" name="Yaxshi" l="1200" w="45" dl="1200" dw="45" count="1"/>
 </good>
 <good typeId="band" id="20" name="Pl" code="PL" l="3200" w="45" t="22" cost="1"><part count="10000" id="50" l="3200" w="45"/></good>
 <operation typeId="CL" id="7" cSizeMode="1" l="3200" w="45" t="22"><material id="20"/><part id="10"/><part id="11"/></operation>
</project>""").encode("utf-8")
    def lens(resp):
        op = next(o for o in resp.json()["project"]["operations"] if o["type"] == "CL")
        return sorted(p["length"] for p in op["parts"])
    base = _run(client, xml, format="project")
    assert base.status_code == 200 and lens(base) == [0, 1200]
    assert any("CL" in w for w in base.json()["warnings"])
    ab = _run(client, xml, format="project", params={"cl_negative_length": "abs"})
    assert lens(ab) == [350, 1200]
    # parametr faqat shu import uchun (keyingi chaqiruv — yana standart); eski yo'l (/projects/import-file) o'zgarmagan
    assert lens(_run(client, xml, format="project")) == [0, 1200]
    old = client.post("/api/projects/import-file", files={"file": ("a.project", xml)})
    assert old.status_code == 200 and sorted(p["length"] for p in next(
        o for o in old.json()["project"]["operations"] if o["type"] == "CL")["parts"]) == [0, 1200]


def test_run_rejections_no_module_extension_params_size(client):
    blob = _sample_project(client)
    r = _run(client, blob, "a.fxm", format="imos")
    assert r.status_code == 400 and "образец файла" in r.json()["detail"]
    r = client.post("/api/import/run", files={"file": ("a.fxm", b"x")}, data={"format": "imos"}, headers=UZ)
    assert r.status_code == 400 and "namuna faylni bering" in r.json()["detail"]
    assert _run(client, blob, "a.json", format="project").status_code == 400                          # kengaytma mos emas
    r = _run(client, blob, "a.xml", format="project")
    assert r.status_code == 400 and ".project" in r.json()["detail"] and "a.xml" in r.json()["detail"]
    assert _run(client, blob, format="ghost").status_code == 404
    for bad in ('{"import_xnc": "no"}', '{"zzz": 1}', '[1]', 'not json'):
        r = client.post("/api/import/run", files={"file": ("a.project", blob)}, data={"format": "project", "params": bad})
        assert r.status_code == 400, bad
    assert _run(client, b"<not-xml", "a.project", format="project").status_code == 400                # buzuq fayl — 400, 500 emas
    assert _run(client, b'<root/>', "a.project", format="project").status_code == 400


# ───────────────────────── plagin reestri (dinamik) ─────────────────────────
def _fake_importer(data: bytes, filename: str):
    return Project(name=f"fake:{F.option('flag', 'dflt')}"), ["w1"]


@pytest.fixture()
def fake_plugin():
    plugins.register(".fxm", "Imos (fxm)", key="imos")(_fake_importer)
    yield
    plugins.BY_KEY.pop("imos", None)
    plugins.REGISTRY.pop(".fxm", None)


def test_registered_plugin_turns_catalog_entry_ready_and_runs(client, fake_plugin):
    by = {x["key"]: x for x in client.get("/api/import/catalog").json()}
    assert by["imos"]["status"] == "ready" and by["imos"]["reason"] == "" and by["pro100"]["status"] == "no_module"
    r = client.post("/api/import/run", files={"file": ("x.fxm", b"data")}, data={"format": "imos"})
    assert r.status_code == 200, r.text
    assert r.json()["project"]["name"] == "fake:dflt" and r.json()["warnings"] == ["w1"]
    # kengaytma «.FXM» (katta harf) ham qabul qilinadi; boshqa kengaytma — yo'q
    assert client.post("/api/import/run", files={"file": ("X.FXM", b"d")}, data={"format": "imos"}).status_code == 200
    assert client.post("/api/import/run", files={"file": ("x.mpr", b"d")}, data={"format": "imos"}).status_code == 400
    # eski yo'l (kengaytma bo'yicha) ham shu plaginni topadi
    assert plugins.find("a.fxm") is not None and plugins.by_key("imos")[2] == (".fxm",)


def test_unknown_plugin_key_appears_as_extra_entry_and_ambiguous_ext_is_dialog_only(client):
    plugins.register("", "Boshqa format", key="demo_x", exts=(".xml",), by_ext=False)(_fake_importer)
    try:
        by = {x["key"]: x for x in client.get("/api/import/catalog").json()}
        assert by["demo_x"]["status"] == "ready" and by["demo_x"]["exts"] == [".xml"] and by["demo_x"]["name"]["ru"] == "Boshqa format"
        assert plugins.find("a.xml") is None                              # `.xml` kengaytma bo'yicha avtomatik tanlanmaydi
        assert client.post("/api/import/run", files={"file": ("a.xml", b"d")}, data={"format": "demo_x"}).status_code == 200
        assert client.get("/api/import/formats/demo_x/schema").json()["status"] == "ready"
    finally:
        plugins.BY_KEY.pop("demo_x", None)


def test_options_context_is_scoped_and_defaults_outside_import():
    assert F.option("flag", "dflt") == "dflt"
    with F.use_options({"flag": "on"}):
        assert F.option("flag", "dflt") == "on" and F.option("other", 7) == 7
        with F.use_options({"flag": "inner"}):
            assert F.option("flag") == "inner"
        assert F.option("flag") == "on"
    assert F.option("flag", "dflt") == "dflt"


# ───────────────────────── katalog ildiz kategoriyalari serverda ─────────────────────────
@pytest.fixture()
def clean_import_settings(client):
    client.put("/api/settings/import_settings/default", json={"catalog_roots": {}})
    yield
    client.put("/api/settings/import_settings/default", json={"catalog_roots": {}})


def test_import_settings_roots_validated_and_stored(client, clean_import_settings):
    assert client.get("/api/settings/import_settings/default").json() == {"catalog_roots": {}}
    r = client.put("/api/settings/import_settings/default", json={"catalog_roots": {"sheet": " 0 ", "edge": "10", "linear": "", "surface": None}})
    assert r.status_code == 200 and r.json()["data"] == {"catalog_roots": {"sheet": "0", "edge": "10"}}
    assert client.get("/api/settings/import_settings/default").json()["catalog_roots"] == {"sheet": "0", "edge": "10"}
    assert import_settings.saved_roots() == {"sheet": "0", "edge": "10"}
    assert client.put("/api/settings/import_settings/default", json={"catalog_roots": {"kuchuk": "1"}}).status_code == 400
    assert client.put("/api/settings/import_settings/default", json={"catalog_roots": {"sheet": "x" * 41}}).status_code == 400
    assert client.put("/api/settings/import_settings/default", json={"catalog_roots": [1]}).status_code == 400
    assert import_settings.saved_roots() == {"sheet": "0", "edge": "10"}              # xato saqlanmadi


def _goods_csv(prefix: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    for r in [["id", "parent_id", "isfolder", "code", "name"],
              [0, None, 1, "", "Листовой"], [1, 0, 0, f"{prefix}S1", "ЛДСП 16"],
              [10, None, 1, "", "Кромка"], [11, 10, 0, f"{prefix}E1", "ПВХ 2"]]:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_catalog_import_uses_saved_roots_when_request_has_none(client, clean_import_settings):
    cmap = json.dumps({"id": "A", "parent_id": "B", "isfolder": "C", "code": "D", "name": "E"})
    client.put("/api/settings/import_settings/default", json={"catalog_roots": {"sheet": "0", "edge": "10"}})
    r = client.post("/api/catalog/import", files={"file": ("g.xlsx", _goods_csv("w18a"))},
                    data={"col_map": cmap, "start_row": 2, "id_prefix": "w18a-"})
    assert r.status_code == 200, r.text
    items = {x["id"]: x for x in client.get("/api/catalog", params={"limit": 5000}).json()}
    assert items["w18a-1"]["kind"] == "sheet" and items["w18a-11"]["kind"] == "edge"            # serverdagi ildizlar ishladi
    # so'rovdagi `roots` serverdagidan ustun; bo'sh obyekt — ildizsiz (standart tur)
    r = client.post("/api/catalog/import", files={"file": ("g.xlsx", _goods_csv("w18b"))},
                    data={"col_map": cmap, "start_row": 2, "id_prefix": "w18b-", "roots": "{}", "kind": "linear"})
    items = {x["id"]: x for x in client.get("/api/catalog", params={"limit": 5000}).json()}
    assert items["w18b-1"]["kind"] == "linear" and items["w18b-11"]["kind"] == "linear"
