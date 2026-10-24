"""«Кодирование» (XNC Параметры, 2026-10-23 onlayn tizimda jonli ko'rildi): kod = now('yyMMddHHmmss') + crc16(loyiha nomi) 5 xona
+ detal ID 4 xona + XNC tartib raqami; «5000 kupe» loyihasidagi «tom» (ID 2, 2-XNC) uchun onlayn ko'rinish: 261023095835 25652 0002 2."""
import datetime as dt

from app.models import Operation, OpType, Part, Project, XNCParams
from app.services import xnc_coding as XC

CFG = {"add_op_number": True, "add_side_number": False,
       "expr": "now('yyMMddHHmmss')+rspace(crc16(project.name),5,'0')+rspace(part.id,4,'0')"}


def _project():
    x1 = Operation(type=OpType.XNC, name="Fasad", code="old1", xnc=XNCParams())
    x2 = Operation(type=OpType.XNC, name="tom", code="old2", xnc=XNCParams(face_side=False))
    x3 = Operation(type=OpType.XNC, name="chap sokol", code="", xnc=XNCParams())          # detalga bog'lanmagan
    cs = Operation(type=OpType.CS, name="LMDF", parts=[Part(uid=1, name="Fasad", length=700, width=400, xnc_op_ids=[x1.id]),
                                                     Part(uid=2, name="tom", length=1950, width=600, xnc_op_ids=[x2.id])])
    return Project(name="5000 kupe", operations=[cs, x1, x2, x3]), (x1, x2, x3)


def test_codes_like_online_sample():
    p, (x1, x2, x3) = _project()
    t = dt.datetime(2026, 10, 23, 9, 58, 35)
    got = {oid: c for oid, c, _e in XC.codes(p, CFG, clock=lambda: t)}
    assert got[x2.id] == "2610230958352565200022"           # onlayn «Кодирование Настройки» namunasi bilan bir xil
    assert got[x1.id] == "2610230958352565200011"
    assert got[x3.id] is None                                # bog'lanmagan — o'zgarmaydi
    side = {oid: c for oid, c, _e in XC.codes(p, {**CFG, "add_op_number": False, "add_side_number": True}, clock=lambda: t)}
    assert side[x1.id].endswith("00011") and side[x2.id].endswith("00022")       # 1 — lits, 2 — orqa tomon


def test_apply_unique_and_api(client):
    p, (x1, x2, x3) = _project()
    st = XC.apply(p, {**CFG, "expr": "'K'", "add_op_number": False})        # hammasi bir xil — noyob qilinadi
    assert (x1.code, x2.code, x3.code) == ("K", "K-2", "")
    assert st == {"changed": 2, "skipped": 1, "errors": []}
    bad = XC.apply(p, {**CFG, "expr": "1+"})
    assert bad["errors"] and x1.code == "K"                  # xato ifoda — kod o'zgarmaydi

    pid = client.post("/api/projects", json={"name": "5000 kupe"}).json()["id"]
    pr = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L", "name": "LMDF"}).json()
    cs = pr["operations"][-1]["id"]
    pr = client.post(f"/api/projects/{pid}/operations/{cs}/parts", json=[{"name": "tom", "length": 1950, "width": 600, "qty": 1}]).json()
    part = next(o for o in pr["operations"] if o["id"] == cs)["parts"][0]
    pr = client.post(f"/api/projects/{pid}/operations/{cs}/parts/{part['id']}/xnc").json()
    xop = pr["operations"][-1]["id"]
    r = client.post(f"/api/projects/{pid}/actions/xnc-coding?preview=1", json={"expr": "'A'+rspace(part.id,4,'0')"}).json()
    assert r == {"sample": f"A{part['uid']:04d}1", "error": ""}
    assert next(o for o in client.get(f"/api/projects/{pid}").json()["operations"] if o["id"] == xop)["code"] != r["sample"]
    r = client.post(f"/api/projects/{pid}/actions/xnc-coding", json={}).json()
    code = next(o for o in r["project"]["operations"] if o["id"] == xop)["code"]
    assert len(code) == 12 + 5 + 4 + 1 and code.endswith(f"{part['uid']:04d}1") and r["changed"] == 1
