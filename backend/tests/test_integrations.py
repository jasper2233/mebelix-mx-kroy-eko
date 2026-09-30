""".project import plagini, MES integratsiyasi (buyurtma, eksport, QR skaner, webhook) va JWT avtorizatsiya."""
import time

import jwt

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<project name="1099 Test shkaf" currency="сум" version="23051701">
  <good typeId="product" id="1" code="109901" name="01 shkaf" count="2">
    <part id="11" code="01_001" name="01_001 bok" count="2" txt="true" l="720" w="560" dl="720" dw="560"
          jl="719" jw="558" cl="720" cw="560" elt="@operation#1" elb="@operation#1" ell="@operation#1"/>
    <part id="12" code="01_002" name="01_002 polka" count="3" txt="false" dl="764" dw="540" elt="@operation#1"/>
    <part id="13" code="01_003" name="01_003 orqa" count="1" txt="false" dl="1200" dw="700"/>
  </good>
  <good typeId="tool.cutting" id="2" swSawthick="4.4" swSawthickDiv="-1" swPackageHeight="40" swMaxturns="4"
        swComplexBand="true" swTrimIncludeSaw="false" swSort="0" swSortInBand="3" swMinSizeBand="0"
        swMaxSizeBand="0" swMinPruning="6" swMaxLengthBand="10000"/>
  <good typeId="tool.edgeline" id="3" elRestSide="30" elMinSize="0" elWidthPreJoint="1" elCost="0"/>
  <good typeId="sheet" id="4" code="LDSP-16" name="LDSP 16 Oq" t="16" l="2750" w="1830" count="2" cost="420000">
    <part id="20" l="2750" w="1830" count="10000" usedCount="2"/>
    <part id="21" l="2000" w="1830" rl="2005" rw="1830" count="1" waste="true" business="true"/>
  </good>
  <good typeId="band" id="5" code="KP-1/19" name="PVC 1/19 Oq" t="1" w="19" count="10" cost="2500"/>
  <operation typeId="EL" id="1" tool1="3" w="19" t="1" elCalcMat="true" elWastePRC="0" elSymbol="A"
             elColor="#D2691E" elLineMark="0" elMinDimDetail="0" printable="true" startNewPage="true">
    <material id="5" count="10"/>
    <part id="11"/><part id="12"/>
  </operation>
  <operation typeId="CS" id="2" tool1="2" cTrimL="10" cTrimW="10" cMinDimRegWaste1="1000" cMinDimRegWaste2="500"
             cBusinessWaste="0.5" csTexture="true" csDirectCut="1" cMaterialCount="2" cFilling="0.81"
             cCPF="0.9" cFillRep="0.9" t="16" l="2750" w="1830" data="QUJD">
    <material id="4" count="2"/>
    <part id="11"/><part id="12"/><part id="13"/>
  </operation>
  <operation typeId="XNC" id="3" code="109901_01_001" typeName="01_001 bok" side="true" turn="0" count="4"
             bySizeDetail="true" mirHor="false" mirVert="false"
             program="&lt;?xml version=&quot;1.0&quot;?&gt;&lt;program dx=&quot;720&quot; dy=&quot;560&quot; dz=&quot;16&quot;&gt;&lt;tool name=&quot;Bore8&quot; d=&quot;8&quot;/&gt;&lt;var name=&quot;th&quot; type=&quot;double&quot; expr=&quot;dz+3&quot;/&gt;&lt;bf x=&quot;37&quot; y=&quot;32&quot; dp=&quot;th&quot; name=&quot;Bore8&quot;/&gt;&lt;bf x=&quot;37&quot; y=&quot;9999&quot; dp=&quot;12&quot; name=&quot;Bore8&quot;/&gt;&lt;bl y=&quot;50&quot; z=&quot;8&quot; dp=&quot;30&quot; name=&quot;Bore8&quot;/&gt;&lt;ms x=&quot;0&quot; y=&quot;100&quot; dp=&quot;10&quot; c=&quot;1&quot; name=&quot;Mill8&quot;/&gt;&lt;ml x=&quot;100&quot; y=&quot;100&quot;/&gt;&lt;gr x1=&quot;0&quot; y1=&quot;540&quot; x2=&quot;720&quot; y2=&quot;540&quot; dp=&quot;8&quot; t=&quot;4&quot; name=&quot;Cut4&quot;/&gt;&lt;/program&gt;">
    <part id="11"/>
  </operation>
</project>
"""


def _op(p, t):
    return [o for o in p["operations"] if o["type"] == t]


def test_import_project_file(client):
    r = client.post("/api/projects/import-file", files={"file": ("1099 Test shkaf.project", SAMPLE.encode("utf-8"))})
    assert r.status_code == 200, r.text
    d = r.json()
    p = d["project"]
    assert p["name"] == "1099 Test shkaf" and p["currency"] == "UZS" and p["size_mode"] == "detail"
    assert p["products"][0]["qty"] == 2 and p["products"][0]["code"] == "109901"
    cs, el, xnc = _op(p, "CS")[0], _op(p, "EL")[0], _op(p, "XNC")[0]
    assert cs["name"] == "LDSP 16 Oq" and cs["code"] == "LDSP-16" and cs["cs_material"]["price"] == 420000
    assert cs["cs_cut"]["kerf"] == 4.4 and cs["cs_cut"]["trim_length"] == 10 and cs["cs_cut"]["max_rotations"] == 4
    assert cs["cs_cut"]["min_trim_cut"] == 6 and cs["cs_cut"]["first_cut"] == 1
    assert [s["length"] for s in cs["sheets"]] == [2750]            # oldingi kroy qoldig'i list emas
    assert "2 list" in cs["description"]
    assert el["el"]["overhang"] == 30 and el["el"]["thickness"] == 1 and el["el"]["jointing_width"] == 1
    assert el["el"]["color"] == "#D2691E" and el["el"]["price"] == 2500
    parts = {pt["code"]: pt for pt in cs["parts"]}
    bok = parts["01_001"]
    assert bok["grain"] and bok["qty"] == 2 and bok["edge_top"]["op_id"] == el["id"]
    assert bok["edge_right"]["op_id"] is None and bok["xnc_op_ids"] == [xnc["id"]]
    assert [pt["uid"] for pt in cs["parts"]] == [1, 2, 3]
    # XNC: dastur o'girilgan, detal tashqarisidagi teshik hisoblanmaydi
    st = client.get(f"/api/projects/{p['id']}/operations/{xnc['id']}/xnc-stats").json()
    assert st["drills"] == 2 and st["mill_m"] == 0.1 and st["saw_m"] == 0.72
    cmds = [c["cmd"] for c in xnc["xnc"]["program"]]
    assert cmds == ["Tool", "Var", "DrillFront", "DrillFront", "DrillLeft", "MillStart", "MillLine", "Groove"]
    # kromka sarfi: ish = Σ tomon, material = Σ(tomon + 2×30)
    eu = client.get(f"/api/projects/{p['id']}/operations/{el['id']}/edge-usage").json()
    work = (720 * 2 + 560) * 4 + 764 * 6
    assert abs(eu["work_m"] - work / 1000) < 1e-6
    assert abs(eu["material_m"] - (work + 60 * (3 * 4 + 6)) / 1000) < 1e-6
    res = client.post(f"/api/projects/{p['id']}/operations/{cs['id']}/optimize?quality=fast").json()
    assert not res["unplaced"] and res["total_parts"] == 4 + 6 + 2
    assert client.post("/api/projects/import-file", files={"file": ("x.project", b"<nope")}).status_code == 400


ORDER = {
    "mes_order_ref": "MES-2026-0042", "name": "Oshxona Karimov", "customer": "Karimov A.",
    "materials": [{"code": "LDSP-16-W", "name": "LDSP 16 Oq", "thickness": 16, "length": 2750, "width": 1830,
                   "price": 420000}],
    "edges": [{"code": "PVC-2-19", "name": "PVC 2/19 Oq", "thickness": 2, "price": 3000}],
    "products": [{"code": "K-01", "name": "Pastki shkaf 600", "qty": 2, "parts": [
        {"name": "Yon devor", "code": "YD", "material_code": "LDSP-16-W", "length": 720, "width": 560, "qty": 2,
         "grain": True, "edges": {"top": "PVC-2-19", "left": "PVC-2-19"}},
        {"name": "Tub", "code": "TB", "material_code": "LDSP-16-W", "length": 568, "width": 560, "qty": 1,
         "edges": {"top": "PVC-2-19"}}]}],
}


def test_mes_order_export_scan_done(client):
    p = client.post("/api/mes/orders", json=ORDER).json()
    assert p["mes_order_ref"] == "MES-2026-0042" and p["owner"] == "MES" and p["customer"] == "Karimov A."
    cs, el = _op(p, "CS")[0], _op(p, "EL")[0]
    assert len(cs["parts"]) == 2 and cs["cs_material"]["price"] == 420000 and el["el"]["thickness"] == 2
    assert cs["parts"][0]["edge_top"]["op_id"] == el["id"] and cs["parts"][0]["grain"]
    # qayta yuborish (hali tasdiqlanmagan) — o'sha loyiha yangilanadi
    p2 = client.post("/api/mes/orders", json=ORDER).json()
    assert p2["id"] == p["id"] and p2["number"] == p["number"]
    res = client.post(f"/api/projects/{p['id']}/operations/{cs['id']}/optimize?quality=fast").json()
    assert res["total_parts"] == 6
    ex = client.get("/api/mes/orders/MES-2026-0042").json()
    cse = next(o for o in ex["operations"] if o["type"] == "CS")
    assert cse["sheets"] == 1 and cse["parts"][0]["qty"] == 4 and ex["warehouse"]
    # detal etiketkasi QR → ma'lumot
    code = f"MXK:{p['number']}:1:1/4"
    info = client.get(f"/api/mes/scan/{code}").json()
    assert info["kind"] == "part" and info["part"]["name"] == "Yon devor" and info["maps"] == [1]
    assert info["product"]["name"] == "Pastki shkaf 600"
    # karta QR → kesildi deb belgilash
    mcode = f"MXK:{p['number']}:{cs['id']}:1"
    assert client.get(f"/api/mes/scan/{mcode}").json()["map"]["done"] == 0
    assert client.post(f"/api/mes/scan/{mcode}/done").json()["done"] == 1
    assert client.post(f"/api/mes/scan/{code}/done").status_code == 400
    assert client.get("/api/mes/scan/XYZ").status_code == 400
    # tasdiqlangan buyurtmani qayta yuborish — 409
    client.patch(f"/api/projects/{p['id']}", json={"status": 2})
    assert client.post("/api/mes/orders", json=ORDER).status_code == 409


def test_webhook_on_status_change(client, monkeypatch):
    import httpx
    calls = []
    monkeypatch.setenv("MES_WEBHOOK_URL", "http://mes.local/hook")
    monkeypatch.setenv("MES_WEBHOOK_TOKEN", "t0k")
    monkeypatch.setattr(httpx, "post", lambda url, json=None, headers=None, timeout=None: calls.append((url, json, headers)))
    p = client.post("/api/projects", json={"name": "Hook", "mes_order_ref": "M-1"}).json()
    client.patch(f"/api/projects/{p['id']}", json={"status": 1})
    ev = [c for c in calls if c[1]["event"] == "project.status"]
    assert ev and ev[0][0] == "http://mes.local/hook" and ev[0][1]["status"] == 1 and ev[0][1]["old_status"] == 0
    assert ev[0][2]["Authorization"] == "Bearer t0k"
    assert client.post("/api/mes/webhook-test").json()["sent"]


def test_jwt_auth(client, monkeypatch):
    monkeypatch.setenv("MEBELIX_AUTH_REQUIRED", "1")
    monkeypatch.setenv("MEBELIX_JWT_SECRET", "s3cret-for-tests-only-0123456789")
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/health").status_code == 200                 # ochiq
    tok = jwt.encode({"sub": "u42", "name": "Dilshod", "exp": int(time.time()) + 60},
                     "s3cret-for-tests-only-0123456789", algorithm="HS256")
    h = {"Authorization": f"Bearer {tok}"}
    assert client.get("/api/me", headers=h).json()["name"] == "Dilshod"
    p = client.post("/api/projects", json={"name": "JWT"}, headers=h).json()
    assert p["owner"] == "Dilshod"
    bad = jwt.encode({"sub": "x"}, "wrong-secret-wrong-secret-wrong-00", algorithm="HS256")
    assert client.get("/api/me", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
