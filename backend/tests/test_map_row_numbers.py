"""Kroy kartasi va hisobot jadvallarida detal raqami — «Детали» jadvalidagi № (tartib raqami), ID emas (xodim videosi
«1281 Usmon», 2026-11-05: ID lar Bazis importida sakraydi, xodim detalni ro'yxatdan tartib raqami bilan topadi — lokal tizimdagidek)."""
import re

from app.models import Project
from app.services import render


def test_map_and_report_use_row_numbers(client):
    pid = client.post("/api/projects", json={"name": "ROWNO"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "LD", "name": "LDSP"}).json()
    cs = p["operations"][0]["id"]
    made = client.post(f"/api/projects/{pid}/operations/{cs}/parts",
                       json=[{"name": n, "length": l, "width": w, "qty": 1} for n, l, w in
                             [("a", 500, 400), ("b", 600, 300), ("c", 700, 200)]]).json()
    a = next(x for x in made["operations"][0]["parts"] if x["name"] == "a")
    client.post(f"/api/projects/{pid}/operations/{cs}/parts/delete", json={"ids": [a["id"]]})
    assert client.post(f"/api/projects/{pid}/operations/{cs}/optimize?quality=fast").status_code == 200
    proj = Project.model_validate(client.get(f"/api/projects/{pid}").json())
    op = proj.operations[0]
    assert [x.uid for x in op.parts] == [2, 3]
    assert render.part_row_numbers(op) == {op.parts[0].id: 1, op.parts[1].id: 2}
    svg = render.map_svg(op.result.maps[0], 800, None, proj, op, "number")
    nums = set(re.findall(r'dominant-baseline="middle">(\d+)</text>', svg))
    assert nums == {"1", "2"}
