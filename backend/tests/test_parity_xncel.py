"""(EL) «Настройка символов и цветов» jadvali (sozlama `el_symbols`) va (XNC) «Переменные» jadvali (`xnc-vars`)."""
import pytest

from app.models import XNCParams, XncCommand
from app.plugins.legacy_project import _EL_COLORS
from app.services import el_symbols as ES
from app.services import xnc as X

URL = "/api/settings/el_symbols/default"


@pytest.fixture()
def reset_symbols(client):
    yield
    client.put(URL, json={})            # standart jadvalga qaytarish
    ES.invalidate()


# ───────────────────────── EL: jadval ─────────────────────────
def test_default_table_letters_and_distinct_colors():
    rows = ES.default_rows()
    assert [r.symbol for r in rows[:4]] == ["A", "B", "C", "D"] and len(rows) == 26
    assert [r.color for r in rows[:len(_EL_COLORS)]] == _EL_COLORS          # importdagi standart ranglar — boshida
    assert len({r.color.lower() for r in rows}) == len(rows)                # har belgiga o'z rangi


def test_settings_scope_listed_and_roundtrip(client, reset_symbols):
    assert "el_symbols" in client.get("/api/settings").json()
    d = client.get(URL).json()
    assert d["rows"][0] == {"symbol": "A", "color": _EL_COLORS[0]}
    new = {"rows": [{"symbol": "X", "color": "#112233"}, {"symbol": "Я", "color": "#AABBCC"}]}
    assert client.put(URL, json=new).status_code == 200
    assert client.get(URL).json() == new


@pytest.mark.parametrize("row", [
    {"symbol": "AB", "color": "#112233"},       # 2 belgi
    {"symbol": "", "color": "#112233"},         # bo'sh
    {"symbol": " ", "color": "#112233"},        # faqat bo'sh joy
    {"symbol": "A", "color": "red"},            # rang formati
    {"symbol": "A", "color": "#12345"},
    {"symbol": "A", "color": "#12345g"},
    {"symbol": "A"},
])
def test_validation_rejects_bad_rows(client, reset_symbols, row):
    before = client.get(URL).json()
    assert 400 <= client.put(URL, json={"rows": [row]}).status_code < 500
    assert client.get(URL).json() == before


def test_new_el_operation_takes_next_unused_row(client, reset_symbols):
    client.put(URL, json={"rows": [{"symbol": "X", "color": "#111111"}, {"symbol": "Y", "color": "#222222"},
                                   {"symbol": "Z", "color": "#333333"}]})
    pid = client.post("/api/projects", json={"name": "EL jadval"}).json()["id"]

    def add():
        p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "K"}).json()
        return p["operations"][-1]

    a, b = add(), add()
    assert (a["el"]["symbol"], a["el"]["color"]) == ("X", "#111111")
    assert (b["el"]["symbol"], b["el"]["color"]) == ("Y", "#222222")
    # birinchi kromka belgisi bo'shatilsa — keyingi yangi kromka yana shu qatorni oladi
    client.patch(f"/api/projects/{pid}/operations/{a['id']}", json={"el": {"symbol": "Q"}})
    c = add()
    assert (c["el"]["symbol"], c["el"]["color"]) == ("X", "#111111")
    d = add()
    assert (d["el"]["symbol"], d["el"]["color"]) == ("Z", "#333333")
    e = add()                                    # hammasi band: aylanib (n-qator)
    assert e["el"]["symbol"] in ("X", "Y", "Z")


def test_empty_table_falls_back_to_builtin(client, reset_symbols):
    assert client.put(URL, json={"rows": []}).status_code == 200
    assert ES.next_style([], 0) == ("A", _EL_COLORS[0])
    assert ES.next_style(["A", "B"], 2)[0] == "C"


def test_importer_edge_style_uses_table(client, reset_symbols):
    from app.models import ELParams, OpType, Operation, Project
    from app.services.importers import assign_edge_style
    client.put(URL, json={"rows": [{"symbol": "M", "color": "#abcdef"}, {"symbol": "N", "color": "#fedcba"}]})
    pr = Project(name="imp")
    pr.operations.append(Operation(type=OpType.EL, name="e1", el=ELParams(symbol="M", color="#000000")))
    el = ELParams()
    assign_edge_style(pr, el)
    assert (el.symbol, el.color) == ("N", "#fedcba")


def test_legacy_fallback_by_order(client, reset_symbols):
    assert ES.style_at(0) == ("A", _EL_COLORS[0]) and ES.style_at(1) == ("B", _EL_COLORS[1])
    client.put(URL, json={"rows": [{"symbol": "P", "color": "#010203"}, {"symbol": "R", "color": "#040506"}]})
    assert ES.style_at(0) == ("P", "#010203") and ES.style_at(3) == ("R", "#040506")


# ───────────────────────── XNC: «Переменные» ─────────────────────────
ORDER = ["allowanceB", "allowanceL", "allowanceR", "allowanceT", "bySizeDetail", "dx", "dy", "dz", "ebj", "ebt", "elj", "elt",
         "erj", "ert", "etj", "ett", "origin.x", "origin.y", "xncSide"]


def _cmd(cmd, comment="", children=(), enabled=True, **params):
    return XncCommand(cmd=cmd, params=params, comment=comment, enabled=enabled, children=list(children))


def test_variable_table_system_rows_in_order():
    x = XNCParams(length=600, width=400, thickness=18, face_side=False, by_part_size=True,
                  part_vars={"allowanceT": 2, "etj": 0.5, "ett": 1})
    rows = X.variable_table(x)
    assert [r["name"] for r in rows] == ORDER
    by = {r["name"]: r for r in rows}
    assert (by["dx"]["value"], by["dy"]["value"], by["dz"]["value"]) == (600, 400, 18)
    assert by["allowanceT"]["value"] == 2 and by["etj"]["value"] == 0.5 and by["ett"]["value"] == 1
    assert by["bySizeDetail"]["type"] == "boolean" and by["bySizeDetail"]["value"] is True
    assert by["xncSide"]["value"] is False and by["dx"]["type"] == "double"
    assert all(r["kind"] == "system" for r in rows)


def test_variable_table_program_entries_and_values():
    prog = [
        _cmd("Par", name="off", value=32, label="Отступ", type="int"),
        _cmd("Par", name="title", value="abc", type="string"),
        _cmd("Var", "половина", name="half", value="dx/2"),
        _cmd("Origin", X=10, Y=20),
        _cmd("If", cond="dx>10000", children=[_cmd("Var", name="never", value=1)]),
        _cmd("Var", name="skipped", value=5, enabled=False),
        _cmd("Set", name="half", value="half+off"),
        _cmd("Var", name="half", value=1),          # takror nom — jadvalda bir marta
    ]
    rows = X.variable_table(XNCParams(length=600, width=400, thickness=16, program=prog, par_values={"off": 40}))
    assert [r["name"] for r in rows[:len(ORDER)]] == ORDER
    own = rows[len(ORDER):]
    assert [(r["name"], r["kind"]) for r in own] == [("off", "par"), ("title", "par"), ("half", "var"), ("never", "var")]
    by = {r["name"]: r for r in rows}
    assert by["off"]["value"] == 40 and by["off"]["type"] == "integer" and by["off"]["description"] == "Отступ"
    assert by["title"]["value"] == "abc" and by["title"]["type"] == "string"
    assert by["half"]["value"] == 1 and by["half"]["description"] == "половина"       # dastur oxiridagi qiymat
    assert by["never"]["value"] is None                                            # bajarilmagan shoxcha
    assert by["origin.x"]["value"] == 10 and by["origin.y"]["value"] == 20


def test_xnc_vars_endpoint(client):
    pid = client.post("/api/projects", json={"name": "XNC vars"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "name": "prog"}).json()
    oid = p["operations"][-1]["id"]
    prog = [dict(cmd="Par", params=dict(name="p1", value="dz*2", label="Двойная толщина")),
            dict(cmd="Var", params=dict(name="v1", value="p1+1"))]
    r = client.patch(f"/api/projects/{pid}/operations/{oid}",
                     json={"xnc": {"program": prog, "length": 500, "width": 300, "thickness": 16}})
    assert r.status_code == 200
    rows = client.get(f"/api/projects/{pid}/operations/{oid}/xnc-vars").json()["rows"]
    assert [r["name"] for r in rows] == ORDER + ["p1", "v1"]
    by = {r["name"]: r for r in rows}
    assert by["dx"]["value"] == 500 and by["p1"]["value"] == 32 and by["v1"]["value"] == 33
    assert by["p1"]["description"] == "Двойная толщина"
    # XNC bo'lmagan operatsiya — 400
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "EL", "name": "k"}).json()
    assert client.get(f"/api/projects/{pid}/operations/{p['operations'][-1]['id']}/xnc-vars").status_code == 400
