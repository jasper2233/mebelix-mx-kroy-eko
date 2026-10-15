"""W7 · Etiketka maydonlari jonli ko'rinishi (preview) va postprotsessor Jinja konteksti: `machine`, hisoblangan
`maps[].placements[].label`, ifoda xatosi — «#ERR» + ogohlantirish (jim 0 emas); CS va XNC konteksti."""
import pytest

from app.models import Operation, OpType, Project, XNCParams, XncCommand as C
from app.services import postprocessors as pp
from app.services import settings

BASE = "/api/postprocessors/machines"


@pytest.fixture(autouse=True)
def clean(client):                       # client — baza jadvallari yaratilgandan keyin
    settings.set_default("pp_machines", {})
    yield
    settings.set_default("pp_machines", {})


@pytest.fixture()
def cut(client, kravat):
    """Kroy qilingan loyiha: (pid, cs_id, el_id, project JSON, CS operatsiya JSON)."""
    pid, cs, el = kravat
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    p = client.get(f"/api/projects/{pid}").json()
    op = next(o for o in p["operations"] if o["id"] == cs)
    return pid, cs, el, p, op


def preview(client, key, body):
    r = client.post(f"{BASE}/{key}/label-fields/preview", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def by_name(j):
    return {f["name"]: f for f in j["fields"]}


def part_with_edges(op):
    return next(p for p in op["parts"] if p["name"] == "Panel6")             # kravat: 6-detalda yuqori va past kromka


# ───────────────────────── preview ─────────────────────────
def test_preview_computes_each_field_in_selected_part_context(client, cut):
    pid, cs, el, p, op = cut
    pt = part_with_edges(op)
    sym = next(o for o in p["operations"] if o["id"] == el)["el"]["symbol"]
    rows = [dict(name="used", expr="usedCount"), dict(name="idx", expr="indexInOperation"),
            dict(name="code", expr="'P' + part.id"), dict(name="top", expr="if(empty(ets),'','('+ets+') '+etn)"),
            dict(name="sides", expr="ets+ebs+els+ers"), dict(name="len", expr="format('0.00',detail.length)"),
            dict(name="proj", expr="project.name"), dict(name="mat", expr="material.code"), dict(name="blank", expr="")]
    j = preview(client, "scm_wincut", dict(project_id=pid, op_id=cs, part_uid=pt["uid"], fields=rows))
    assert j["source"] == "project" and j["part"]["uid"] == pt["uid"] and j["part"]["name"] == "Panel6"
    assert j["part"]["index"] == 6 and j["map_index"] is not None
    f = by_name(j)
    assert all(x["ok"] for x in j["fields"])
    assert f["used"]["value"] == pt["used_qty"] and f["used"]["type"] == "integer"
    assert f["idx"]["value"] == 6
    assert f["code"]["value"] == f"P{pt['uid']}" and f["code"]["type"] == "string"
    assert f["top"]["text"] == f"({sym}) PVC 1-19"
    assert f["sides"]["value"] == sym + sym                                  # yuqori va past kromka
    assert f["len"]["value"] == "%.2f" % pt["length"] and f["proj"]["value"] == "Detskiy kravat" and f["mat"]["value"] == "LDSP16"
    assert f["blank"]["value"] == "" and f["blank"]["ok"] is True
    vs = {v["name"]: v for v in j["variables"]}                                # ifoda yordamchisi uchun tanlangan detal qiymatlari
    assert vs["usedCount"]["value"] == pt["used_qty"] and vs["indexInOperation"]["value"] == 6 and vs["ets"]["value"] == sym
    assert vs["project.name"]["value"] == "Detskiy kravat" and vs["usedCount"]["ru"] and vs["usedCount"]["uz"]
    # boshqa detal — boshqa qiymat; part_uid berilmasa — birinchi detal
    p1 = op["parts"][0]
    j1 = preview(client, "scm_wincut", dict(project_id=pid, op_id=cs, fields=rows))
    assert j1["part"]["uid"] == p1["uid"] and by_name(j1)["idx"]["value"] == 1 and by_name(j1)["sides"]["value"] == ""
    # saqlanmagan qoralama o'rniga saqlangan jadval
    assert client.put(f"{BASE}/scm_wincut/label-fields", json={"label_fields": [dict(name="only", expr="usedCount*10")]}).status_code == 200
    js = preview(client, "scm_wincut", dict(project_id=pid, op_id=cs, part_uid=pt["uid"]))
    assert [x["name"] for x in js["fields"]] == ["only"] and js["fields"][0]["value"] == pt["used_qty"] * 10


def test_preview_errors_are_visible_not_silent_zero(client, cut):
    pid, cs, _el, _p, _op = cut
    rows = [dict(name="ok", expr="usedCount"), dict(name="unk", expr="no_such_var + 1"), dict(name="syn", expr="1+"),
            dict(name="dup", expr="1"), dict(name="dup", expr="2"), dict(name="", expr="3"),
            dict(name="fn", expr="nofunc(1)")]
    j = preview(client, "scm_wincut", dict(project_id=pid, op_id=cs, fields=rows))
    f = j["fields"]
    assert f[0]["ok"] and f[0]["error"] is None
    assert not f[1]["ok"] and f[1]["stage"] == "eval" and f[1]["value"] == "#ERR" and f[1]["error"] and "no_such_var" in f[1]["error"]
    assert not f[2]["ok"] and f[2]["stage"] == "syntax" and f[2]["value"] == "#ERR"
    assert f[3]["name_error"] is None and f[4]["name_error"] and f[5]["name_error"]
    assert not f[6]["ok"] and f[6]["stage"] == "eval"


def test_preview_sample_and_bad_targets(client, cut, kravat):
    pid, cs, el, _p, op = cut
    assert preview(client, "biesse_osi", {})["source"] == "sample"
    base = f"{BASE}/scm_wincut/label-fields/preview"
    assert client.post(base, json=dict(project_id="no-such", op_id=cs)).status_code == 404
    assert client.post(base, json=dict(project_id=pid, op_id="no-such")).status_code == 404
    assert client.post(base, json=dict(project_id=pid)).status_code == 404                  # op_id kerak
    assert client.post(base, json=dict(project_id=pid, op_id=el)).status_code == 400        # CS emas
    assert client.post(base, json=dict(project_id=pid, op_id=cs, part_uid=999999)).status_code == 404
    assert client.post(base, json=dict(project_id=pid, op_id=cs, fields=[dict(name=f"F{i}", expr="1") for i in range(101)])
                       ).status_code == 400


# ───────────────────────── postprotsessor konteksti ─────────────────────────
TPL = ("{{ machine.key }}|{{ machine.name }}|{{ machine.params.trim_uv }}|{{ machine.params.list_dir }}"
       "|{{ machine.label_fields|length }}|W={{ label_warnings|length }}\n"
       "{% for m in maps %}{% for p in m.placements %}{{ p.uid }}:{{ p.label['Campo10'] }}:{{ p.label_text['Campo11'] }}"
       ":{{ p.label['Campo12'] }};{% endfor %}{% endfor %}")


def bind(client, key, template, **kw):
    prof = client.post("/api/settings/postprocessor", json={"name": f"W7 {key}", "data": {
        "name": f"W7 {key}", "extension": "txt", "per_map": False, "newline": "lf", "template": template, **kw}}).json()
    r = client.put("/api/postprocessors/machines", json={"enabled": {key: True}, "profile": {key: prof["id"]}, "prefix": False})
    assert r.status_code == 200
    return prof


def test_machine_context_in_jinja_with_calculated_labels(client, cut):
    pid, cs, _el, p, op = cut
    prof = bind(client, "scm_wincut", TPL)
    try:
        assert client.put(f"{BASE}/scm_wincut/params", json={"params": {"trim_uv": 12, "list_dir": "D:\\lst\\"}}).status_code == 200
        assert client.put(f"{BASE}/scm_wincut/label-fields", json={"label_fields": [
            dict(name="Campo10", expr="usedCount"), dict(name="Campo11", expr="'N'+part.id"),
            dict(name="Campo12", expr="if(empty(ets),'-',ets)")]}).status_code == 200
        r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:scm_wincut")
        assert r.status_code == 200, r.text
        assert "X-Label-Warnings" not in r.headers and "x-label-warnings" not in r.headers
        head, body = r.content.decode().split("\n", 1)
        assert head == "scm_wincut|SCM WinCut|12.0|D:\\lst\\|3|W=0"
        used = {x["uid"]: x["used_qty"] for x in op["parts"]}
        sym = next(o for o in p["operations"] if o["id"] == _el)["el"]["symbol"]
        items = [s.split(":") for s in body.strip().split(";") if s]
        assert items and {int(u) for u, *_ in items} == {x["uid"] for x in op["parts"] if used[x["uid"]] > 0}
        for u, c10, c11, c12 in items:
            assert int(c10) == used[int(u)] and c11 == f"N{u}"
            assert c12 == (sym if int(u) == part_with_edges(op)["uid"] else "-")
    finally:
        client.delete(f"/api/settings/postprocessor/{prof['id']}")


def test_expression_error_gives_err_marker_and_warning_not_zero(client, cut):
    pid, cs, *_ = cut
    prof = bind(client, "scm_wincut", TPL + "\n{% for w in label_warnings %}#{{ w.field }}={{ w.count }}/{{ w.error }}{% endfor %}")
    try:
        assert client.put(f"{BASE}/scm_wincut/label-fields", json={"label_fields": [
            dict(name="Campo10", expr="no_such_var"), dict(name="Campo11", expr="usedCount"), dict(name="Campo12", expr="1/0")]}).status_code == 200
        r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:scm_wincut")
        assert r.status_code == 200
        text = r.content.decode()
        assert ":#ERR;" in text and "#ERR" in text.split("\n")[1]
        assert r.headers["x-label-warnings"] == "2"                       # Campo10 va Campo12 (1/0 ham xato yoki #ERR)
        warn_line = text.strip().split("\n")[-1]
        assert "#Campo10=" in warn_line and "no_such_var" in warn_line
        assert "W=2" in text.split("\n")[0]
    finally:
        client.delete(f"/api/settings/postprocessor/{prof['id']}")


def test_non_machine_downloads_have_no_machine(client, cut):
    pid, cs, *_ = cut
    prof = client.post("/api/settings/postprocessor", json={"name": "W7 plain", "data": {
        "name": "W7 plain", "extension": "txt", "per_map": False, "newline": "lf",
        "template": "{{ 'none' if machine is none else 'has' }}|{{ label_warnings|length }}"
                    "{% for m in maps %}{% for p in m.placements %}|{{ p.label|length }}{% endfor %}{% endfor %}"}}).json()
    try:
        r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?profile_id={prof['id']}")
        assert r.status_code == 200 and r.content.decode().startswith("none|0|0|0")
        assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=json").status_code == 200       # o'rnatilgan — buzilmagan
        assert client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=csv").status_code == 200
    finally:
        client.delete(f"/api/settings/postprocessor/{prof['id']}")


def test_machine_without_labels_gets_empty_label_dicts(client, cut):
    pid, cs, *_ = cut
    prof = bind(client, "homag_chf", "{{ machine.key }}|{{ machine.params.trim_zw }}|{{ machine.params.orientation }}"
                                     "|{{ machine.label_fields|length }}{% for m in maps %}{% for p in m.placements %}|{{ p.label|length }}"
                                     "{% endfor %}{% endfor %}")
    try:
        r = client.get(f"/api/projects/{pid}/operations/{cs}/postprocess?key=machine:homag_chf")
        assert r.status_code == 200
        parts = r.content.decode().split("|")
        assert parts[:4] == ["homag_chf", "0.0", "first_cut_5", "0"] and set(parts[4:]) == {"0"}
    finally:
        client.delete(f"/api/settings/postprocessor/{prof['id']}")


def test_template_preview_endpoint_accepts_machine(client, cut):
    pid, cs, *_ = cut
    client.put(f"{BASE}/biesse_osi/params", json={"params": {"program_version": "5.3"}})
    tpl = "{{ machine.params.program_version }}|{{ maps[0].placements[0].label['Код'] }}"
    body = dict(project_id=pid, op_id=cs, machine="biesse_osi",
                profile={"name": "x", "extension": "txt", "per_map": False, "template": tpl})
    j = client.post("/api/postprocessors/preview", json=body).json()
    assert j["ok"] and j["text"].startswith("5.3|P")
    body["machine"] = "nope"
    assert client.post("/api/postprocessors/preview", json=body).status_code == 400
    body.pop("machine")
    j = client.post("/api/postprocessors/preview", json=body).json()
    assert j["ok"] is False                                              # stanoksiz kontekstda machine yo'q


def test_context_helpers_directly(kravat, client):
    """Servis darajasida: `context(project, op, machine_key)` — machine, label, label_text, label_warnings."""
    from app import store
    pid, cs, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast")
    project = store.load(pid)
    op = store.op_of(project, cs)
    c0 = pp.context(project, op)
    assert c0["machine"] is None and c0["label_warnings"] == []
    assert all(pl["label"] == {} for m in c0["maps"] for pl in m["placements"]) and all(p["label"] == {} for p in c0["parts"])
    c1 = pp.context(project, op, "biesse_osi")
    assert c1["machine"]["key"] == "biesse_osi" and c1["machine"]["group"] == "saw" and c1["machine"]["params"]["orientation"] == "horizontal"
    pl = c1["maps"][0]["placements"][0]
    assert pl["label"]["Код"] == f"P{pl['uid']}" and pl["label_text"]["Код"] == f"P{pl['uid']}" and set(pl["label"]) == set(pl["label_text"])
    assert c1["parts"][0]["label"]["Код подформата / PartNo"] == 1 and c1["label_warnings"] == []
    json_ok = __import__("json").dumps(c1["maps"][0]["placements"][0]["label"])                # JSON-ga mos
    assert json_ok


def test_xnc_context_has_machine(client):
    op = Operation(type=OpType.XNC, code="K1", name="Bok", xnc=XNCParams(
        length=200, width=100, thickness=16, by_part_size=False, program=[XncCommand("Tool", N="B8", D=8)]))
    prj = Project(name="T", operations=[op])
    c0 = pp.context_xnc(prj, op)
    assert c0["machine"] is None and c0["label_warnings"] == []
    c1 = pp.context_xnc(prj, op, machine_key="woodwop")
    assert c1["machine"] == dict(key="woodwop", name="WoodWop (Homag)", group="cnc", params={}, label_fields=[])
    assert c1["xnc"]["code"] == "K1"                                        # eski kontekst saqlangan


def test_xnc_machine_download_gets_machine_context(client, kravat):
    from test_xnc_w1_postprocess import _xnc_op
    pid, _cs, _pt, xid = _xnc_op(client, kravat, [dict(cmd="DrillFront", params=dict(X=30, Y=20, DP=12, D=8), comment="", children=[])])
    prof = bind(client, "woodwop", "{{ machine.key }}|{{ machine.name }}|{{ machine.group }}|{{ machine.params|length }}"
                                   "|{{ machine.label_fields|length }}|{{ xnc.code }}")
    try:
        r = client.get(f"/api/projects/{pid}/operations/{xid}/postprocess", params={"key": "machine:woodwop"})
        assert r.status_code == 200, r.text
        assert r.content.decode().startswith("woodwop|WoodWop (Homag)|cnc|0|0|")
    finally:
        client.delete(f"/api/settings/postprocessor/{prof['id']}")


def XncCommand(kind, /, **p):
    return C(cmd=kind, params=p)
