"""XNC «Параметры» → «Открыть» / «Сохранить»: operatsiya dasturini faylga saqlash va fayldan ochish
(`<program>` XML — .xnc, va bizning shablon JSON fayli)."""
import json

from app.models import XncCommand as C

from test_qa_fix_calc import _op, _set_prog, _xnc_for


def _url(pid, xid):
    return f"/api/projects/{pid}/operations/{xid}/xnc/program-file"


def test_save_xnc_then_open_roundtrip(client, kravat):
    pid, _cs, _pt, xid = _xnc_for(client, kravat)
    prog = [C(cmd="DrillFront", params={"X": 50, "Y": 40, "D": 8, "DP": 12}).model_dump(mode="json")]
    _set_prog(client, pid, xid, prog)
    r = client.get(_url(pid, xid))
    assert r.status_code == 200
    assert ".xnc" in r.headers["content-disposition"] and r.text.lstrip().startswith("<?xml")
    assert "<program" in r.text and 'dx="' in r.text
    # dasturni bo'shatib, fayldan qayta ochamiz
    _set_prog(client, pid, xid, [])
    o = client.post(_url(pid, xid), files={"file": ("a.xnc", r.content)})
    assert o.status_code == 200, o.text
    x = _op(o.json()["project"], xid)["xnc"]
    assert len(x["program"]) == 1 and x["program"][0]["cmd"] == "DrillFront"
    assert float(x["program"][0]["params"]["X"]) == 50


def test_save_json_keeps_parameters_and_open(client, kravat):
    pid, _cs, _pt, xid = _xnc_for(client, kravat)
    prog = [C(cmd="Par", params={"name": "h", "value": 30, "label": "H", "type": "double"}).model_dump(mode="json"),
            C(cmd="DrillFront", params={"X": "h", "Y": 40, "D": 8, "DP": 12}).model_dump(mode="json")]
    _set_prog(client, pid, xid, prog, par_values={"h": 45})
    r = client.get(_url(pid, xid), params={"fmt": "json"})
    assert r.status_code == 200 and ".xnc.json" in r.headers["content-disposition"]
    d = json.loads(r.content)
    assert d["par_values"] == {"h": 45}
    _set_prog(client, pid, xid, [], par_values={})
    o = client.post(_url(pid, xid), files={"file": ("a.xnc.json", r.content)})
    assert o.status_code == 200, o.text
    x = _op(o.json()["project"], xid)["xnc"]
    assert [c["cmd"] for c in x["program"]] == ["Par", "DrillFront"] and x["par_values"] == {"h": 45}


def test_open_rejects_bad_files_and_non_xnc(client, kravat):
    pid, cs, _pt, xid = _xnc_for(client, kravat)
    assert client.post(_url(pid, xid), files={"file": ("a.xnc", b"junk")}).status_code == 400
    assert client.post(_url(pid, xid), files={"file": ("a.xnc", b"<program")}).status_code == 400
    assert client.post(_url(pid, xid), files={"file": ("a.json", b'{"kind": "other"}')}).status_code == 400
    assert client.post(_url(pid, xid), files={"file": ("a.xnc", b"")}).status_code == 400
    assert client.get(_url(pid, cs)).status_code == 400


def test_open_xml_sets_blank_size_only_without_by_part_size(client, kravat):
    pid, _cs, _pt, xid = _xnc_for(client, kravat)
    xml = b'<?xml version="1.0" encoding="UTF-8"?><program dx="700" dy="300" dz="18"><bf x="10" y="20" dp="5" d="5"/></program>'
    p = client.post(_url(pid, xid), files={"file": ("a.xnc", xml)}).json()["project"]
    x = _op(p, xid)["xnc"]
    assert x["by_part_size"] and x["length"] != 700                       # detal o'lchami saqlanadi
    client.patch(f"/api/projects/{pid}/operations/{xid}", json={"xnc": {"by_part_size": False}})
    p = client.post(_url(pid, xid), files={"file": ("a.xnc", xml)}).json()["project"]
    x = _op(p, xid)["xnc"]
    assert (x["length"], x["width"], x["thickness"]) == (700, 300, 18)
