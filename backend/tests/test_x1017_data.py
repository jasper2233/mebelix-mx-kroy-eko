"""2026-10-17: «5000 kupe» onlayn ↔ MX solishtiruvidagi DATA / FUNC-backend farqlari (sintetik fayllar bilan).

* XNC dastur parametrlari fayldagi yozuvi bilan saqlanadi («34.0» → «34» bo'lib qolmaydi), qiymati o'zgarmaydi, eksport aynan yozadi;
* (CL) «Припуск на обработку заготовки» (cAllowanceWorkpiece) — import / eksport / pilniy uzunlik;
* hisobot: CS sarlavhasi standart yoqiq, detallar jadvali «№» — tartib raqami, O qatori qalin, «Таблица команд» T qatorida «К» bo'sh.
"""
from __future__ import annotations

import html
import xml.etree.ElementTree as ET

from app.models import CLParams, OpType, PrintSettings
from app.plugins.legacy_project import _num_or_expr, import_project
from app.services import render, xnc
from app.services.cl_calc import saw_length
from app.services.project_export import export_project

PROG = html.escape(
    '<program dx="900" dy="500" dz="16"><tool name="B5" d="5"/>'
    '<br ver="2" y="70" dp="34.0" z="8" ac="1" m="true" name="B5"/>'
    '<bf x="100" y="429.99" dp="3.00" ac="1" av="false" name="B5"/></program>', quote=True)


def _xml(allow: str = "2") -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project name="X1017" currency="UZS" version="1" date="1785152837899" orderDate="1785152837899">
 <good typeId="product" id="2" count="1" name="Model-Z" code="77">
  <part id="5" name="yon" dl="900" dw="500" count="1" txt="true"/>
  <part id="3" name="tepa" dl="800" dw="400" count="1" txt="true"/>
  <part id="11" name="Plintus" dl="1200" dw="45" l="1200" w="45" count="2"/>
  <operation id="9"/>
 </good>
 <good typeId="tool.cutting" id="30" swSawthick="4"/>
 <good typeId="sheet" id="33" name="LDSP" l="2750" w="1830" t="16" cost="0"><part id="60" count="10000" l="2750" w="1830"/></good>
 <good typeId="band" id="20" name="Plintus 45" code="PL-45" l="3200" w="45" t="22" cost="0"><part count="10000" id="50" l="3200" w="45"/></good>
 <good typeId="simple" id="15" unit="шт" count="4" cost="0" name="Vint"/>
 <operation typeId="CS" id="8" tool1="30" cSizeMode="1" cTrimL="10" cTrimW="10" printable="true" startNewPage="true">
  <material id="33"/><part id="5"/><part id="3"/><part id="60"/>
 </operation>
 <operation typeId="CL" id="7" tool1="30" cSizeMode="1" l="3200" w="45" t="22" cTrimW="10" cAllowanceWorkpiece="{allow}"
   printable="true" startNewPage="true"><material id="20"/><part id="11"/><part id="50"/></operation>
 <operation typeId="O" typeName="Furnitura" id="9" printable="true" startNewPage="true"><material id="15" count="4"/></operation>
 <operation typeId="XNC" id="12" code="X-5" typeName="yon" program="{PROG}" count="1" side="true" turn="0" bySizeDetail="true"
   printable="true" startNewPage="true"><part id="5"/></operation>
</project>""".encode("utf-8")


def _op(p, t):
    return next(o for o in p.operations if o.type == t)


# ───────────────────────── XNC: asl yozuv saqlanadi ─────────────────────────
def test_num_or_expr_keeps_non_canonical_number_text():
    assert _num_or_expr("34.0") == "34.0" and _num_or_expr("3.00") == "3.00" and _num_or_expr("08") == "08"
    assert _num_or_expr("34") == 34.0 and _num_or_expr("429.99") == 429.99 and _num_or_expr("-5") == -5.0
    assert _num_or_expr("dz+3.00") == "dz+3.00" and _num_or_expr(None) is None


def test_xnc_program_text_roundtrips_and_evaluates_the_same():
    p, _w = import_project(_xml(), "x1017.project")
    x = _op(p, OpType.XNC)
    br = next(c for c in x.xnc.program if c.cmd == "DrillRight")
    assert br.params["DP"] == "34.0" and br.params["Y"] == 70.0 and br.params["M"] == "true"
    bf = next(c for c in x.xnc.program if c.cmd == "DrillFront")
    assert bf.params["DP"] == "3.00" and bf.params["Y"] == 429.99
    st = xnc.xnc_stats(x.xnc)
    assert st["drills"] == 2 and not st.get("errors")
    # eksport — fayldagi yozuv aynan
    res = export_project(p)
    prog = next(o.get("program") for o in ET.fromstring(res.xml).findall("operation") if o.get("typeId") == "XNC")
    assert 'dp="34.0"' in prog and 'dp="3.00"' in prog and 'm="true"' in prog
    p2, _w2 = import_project(res.xml, "rt.project")
    br2 = next(c for c in _op(p2, OpType.XNC).xnc.program if c.cmd == "DrillRight")
    assert br2.params["DP"] == "34.0"


# ───────────────────────── (CL) Припуск на обработку заготовки ─────────────────────────
def test_cl_machining_allowance_import_export_and_saw_length():
    p, _w = import_project(_xml("2"), "x1017.project")
    cl = _op(p, OpType.CL)
    assert cl.cl.machining_allowance == 2
    part = cl.parts[0]
    assert saw_length(p, cl, part) == 1200 + 2 * 2                    # har uchidan qo'shiladi
    cl0 = cl.model_copy(update={"cl": cl.cl.model_copy(update={"machining_allowance": 0})})
    assert saw_length(p, cl0, part) == 1200
    root = ET.fromstring(export_project(p).xml)
    oe = next(o for o in root.findall("operation") if o.get("typeId") == "CL")
    assert oe.get("cAllowanceWorkpiece") == "2"
    p0, _w0 = import_project(_xml("0"), "x1017.project")
    oe0 = next(o for o in ET.fromstring(export_project(p0).xml).findall("operation") if o.get("typeId") == "CL")
    assert oe0.get("cAllowanceWorkpiece") is None                     # standart (0) — eksport o'zgarmaydi
    assert CLParams().machining_allowance == 0
    assert CLParams.model_validate({"machining_allowance": 999}, context={"legacy": True}).machining_allowance <= 500


# ───────────────────────── hisobot ─────────────────────────
def test_report_cs_title_default_sequential_numbers_and_bold_o_row():
    p, _w = import_project(_xml(), "x1017.project")
    assert PrintSettings().cs_title is True
    h = render.project_report_html(p, PrintSettings(), "ru")
    assert "(CS) Листовой раскрой: LDSP" in h
    sec = h.split("(CS) Листовой раскрой")[1]
    import re
    nums = [int(n) for n in re.findall(r"<tr><td>(\d+)</td><td>\d+</td>", sec.split("</table>")[0])]
    assert nums == [1, 2]                                             # detal ID (5, 3) emas — tartib raqami
    assert "<td class='b'>O</td><td class='b'>Model-Z</td>" in h


def test_report_command_table_t_rows_have_blank_count(client):
    import re
    r = client.post("/api/projects/import-file", files={"file": ("x1017.project", _xml(), "application/xml")})
    assert r.status_code == 200, r.text[:300]
    pj = r.json()["project"]
    cs = next(o for o in pj["operations"] if o["type"] == "CS")["id"]
    assert client.post(f"/api/projects/{pj['id']}/operations/{cs}/optimize?quality=fast").status_code == 200
    h = client.post(f"/api/projects/{pj['id']}/report?lang=ru", json={"cs_maps": True, "cs_commands": True}).text
    t_rows = re.findall(r"<tr><td>T\d+</td><td>[^<]*</td><td>([^<]*)</td>", h)
    assert t_rows and all(v == "" for v in t_rows)
    assert re.search(r"<tr><td>P\d+</td><td>[^<]*</td><td>\d+</td>", h)   # detal qatorlarida soni bor
