# EL parametrlari eslab qolinadi (2026-10-25, foydalanuvchi talabi): xodim qo'ygan «Длина остатка по краям», «Мин. оклеиваемая
# длина», «Мин. размер стороны», «Ширина прифуговки» … korxona standarti bo'lib qoladi — keyingi import qilingan kromka (Bazis
# fayllarida bu qiymatlar yo'q) shu qiymatlar bilan keladi, foydalanuvchi o'zi o'zgartirmaguncha. Sintetik fayl.
BAZIS = """<?xml version="1.0" encoding="UTF-8"?>
<project name="EL mem" currency="UZS" version="1">
 <good typeId="product" id="2" count="1" name="Shkaf"><part id="18" name="polka" dl="951" dw="500" count="1" elt="@operation#1"/></good>
 <good typeId="sheet" id="4" t="16" name="LDSP" l="2750" w="1830" count="10000" cost="0"/>
 <good typeId="band" id="5" t="1" w="19" name="1-19 test" code="KP-1/19"/>
 <operation typeId="CS" id="3" l="2750" w="1830" t="16"><material id="4"/><part id="18"/></operation>
 <operation typeId="EL" id="1" tool1="4"><material id="5"/><part id="18"/></operation>
</project>"""


def _imp(client):
    r = client.post("/api/projects/import", files={"file": ("el_mem.project", BAZIS.encode(), "application/xml")})
    assert r.status_code == 200, r.text
    p = r.json()
    return p, next(o for o in p["operations"] if o["type"] == "EL")


def test_el_params_remembered_for_next_import(client):
    base = client.get("/api/settings/el_defaults/default").json()
    try:
        p, el = _imp(client)
        want = {"overhang": 30, "min_glue_length": 100, "min_perp_side": 40, "jointing_width": 1}
        for k, v in want.items():                                # Enter bilan bittadan (UI kabi)
            r = client.patch(f"/api/projects/{p['id']}/operations/{el['id']}", json={"el": {k: v}})
            assert r.status_code == 200
        d = client.get("/api/settings/el_defaults/default").json()
        assert {k: d[k] for k in want} == want
        assert d["width"] == base["width"]                       # materialga xos maydon eslab qolinmaydi
        # keyingi import — fayldа qiymat yo'q: oxirgi qo'yilganlar
        _, el2 = _imp(client)
        assert {k: el2["el"][k] for k in want} == want
        assert el2["el"]["thickness"] == 1 and el2["el"]["width"] == 19          # kromka o'lchami — fayldan
        # faylda bor qiymat — fayldagisi
        r = client.post("/api/projects/import", files={"file": ("el_mem2.project", BAZIS.replace(
            '<operation typeId="EL" id="1" tool1="4">', '<good typeId="tool.edgeline" id="4" elRestSide="12" elMinSize="0"/>'
            '<operation typeId="EL" id="1" tool1="4" elMinDimDetail="0">').encode(), "application/xml")})
        el3 = next(o for o in r.json()["operations"] if o["type"] == "EL")["el"]
        assert (el3["overhang"], el3["min_glue_length"], el3["min_perp_side"]) == (12, 0, 0)
        # qo'lda qo'shilgan yangi EL ham
        p4 = client.post(f"/api/projects/{p['id']}/operations", json={"type": "EL", "name": "yangi"}).json()
        el4 = [o for o in p4["operations"] if o["type"] == "EL"][-1]["el"]
        assert el4["overhang"] == 30 and el4["min_perp_side"] == 40
    finally:
        client.put("/api/settings/el_defaults/default", json=base)


BAZIS_CS = """<?xml version="1.0" encoding="UTF-8"?>
<project name="CS mem" currency="UZS" version="1">
 <good typeId="product" id="2" count="1" name="Shkaf"><part id="18" name="polka" dl="951" dw="500" count="1"/></good>
 <good typeId="sheet" id="4" t="16" name="LDSP" l="2750" w="1830" count="10000" cost="0"/>
 <good typeId="tool.cutting" id="6"/>
 <operation typeId="CS" id="3" tool1="6" l="2750" w="1830" t="16"><material id="4"/><part id="18"/></operation>
</project>"""


def test_cs_params_remembered_for_next_import(client):
    """CS: qoldiq chegaralari, min. detal keyingi importga o'tadi; qalinlik, narx, tekstura — yo'q. Pila / торцовка / обрезка /
    вращения / paket — stanok parametrlari (2026-10-30): operator o'zgartirsa faqat o'sha loyihada, keyingisi stanok standartidan."""
    imp = lambda: next(o for o in client.post("/api/projects/import", files={"file": ("cs.project", BAZIS_CS.encode(), "application/xml")}).json()["operations"] if o["type"] == "CS")
    base = client.get("/api/settings/cs_defaults/default").json()
    try:
        r = client.post("/api/projects/import", files={"file": ("cs.project", BAZIS_CS.encode(), "application/xml")}).json()
        op = next(o for o in r["operations"] if o["type"] == "CS")
        cut = {"kerf": 4.4, "trim_length": 10, "trim_width": 8, "min_trim_cut": 12, "max_rotations": 4, "pack_height": 48}
        mat = {"remnant_min_side1": 800, "remnant_min_area": 0.3, "min_part_size": 25, "thickness": 18, "price": 777}
        assert client.patch(f"/api/projects/{r['id']}/operations/{op['id']}", json={"cs_cut": cut}).status_code == 200
        assert client.patch(f"/api/projects/{r['id']}/operations/{op['id']}", json={"cs_material": mat}).status_code == 200
        before = {k: op["cs_cut"][k] for k in cut}
        op2 = imp()
        assert {k: op2["cs_cut"][k] for k in cut} == before                                    # stanok standarti
        assert op2["cs_material"]["remnant_min_side1"] == 800 and op2["cs_material"]["min_part_size"] == 25
        assert op2["cs_material"]["thickness"] == 16 and op2["cs_material"]["price"] == 0     # fayldan / eslab qolinmaydi
        # yangi qo'lda qo'shilgan CS ham
        p3 = client.post(f"/api/projects/{r['id']}/operations", json={"type": "CS", "name": "yangi"}).json()
        assert p3["operations"][-1]["cs_cut"]["trim_length"] == before["trim_length"]
        assert p3["operations"][-1]["cs_material"]["remnant_min_side1"] == 800
    finally:
        client.put("/api/settings/cs_defaults/default", json=base)
