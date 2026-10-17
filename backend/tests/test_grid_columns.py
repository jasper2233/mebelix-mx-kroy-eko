"""Jadvallar «Настройки» (Ctrl+P) profillari: o_columns / el_columns / cl_columns / cn_columns — tekshiruv, standart."""
import pytest

from app.services import settings

SCOPES = settings.GRID_COLUMN_SCOPES


@pytest.mark.parametrize("scope", SCOPES)
def test_grid_columns_profile_crud_and_default(client, scope):
    # o'rnatilgan standart — bo'sh ro'yxat (frontend katalogi ishlatiladi)
    assert client.get(f"/api/settings/{scope}/default").json() == {"columns": []}
    cols = [{"key": "code", "visible": True, "width": 20}, {"key": "used", "visible": False, "title": "IK"}]
    pr = client.post(f"/api/settings/{scope}", json={"name": "Mening", "data": {"columns": cols}})
    assert pr.status_code == 200, pr.text
    data = pr.json()["data"]["columns"]
    assert [c["key"] for c in data] == ["code", "used"]
    assert data[0]["width"] == 20 and data[1]["visible"] is False and data[1]["title"] == "IK"
    # «Настройка значений по умолчанию» — standart profil
    r = client.put(f"/api/settings/{scope}/default", json={"columns": cols[:1]})
    assert r.status_code == 200 and r.json()["is_default"]
    assert client.get(f"/api/settings/{scope}/default").json()["columns"][0]["key"] == "code"
    # ikkinchi saqlash yangi qator yaratmaydi
    client.put(f"/api/settings/{scope}/default", json={"columns": cols})
    rows = client.get(f"/api/settings/{scope}").json()
    assert sum(1 for p in rows if p["is_default"]) == 1
    assert len(client.get(f"/api/settings/{scope}/default").json()["columns"]) == 2


@pytest.mark.parametrize("bad", [
    {"columns": [{"key": "", "visible": True}]},                     # bo'sh kalit
    {"columns": [{"key": "x" * 41}]},                                 # juda uzun kalit
    {"columns": [{"key": "code", "width": 0}]},                       # kenglik > 0
    {"columns": [{"key": "code", "width": 1000}]},                    # kenglik ≤ 300 belgi
    {"columns": [{"key": "code", "title": "n" * 101}]},               # nom ≤ 100
    {"columns": "abc"},
    {"columns": [{"key": "c"}] * 201},                                # ≤ 200 ustun
])
def test_grid_columns_validation(client, bad):
    assert client.post("/api/settings/o_columns", json={"name": "X", "data": bad}).status_code == 400
    assert client.put("/api/settings/el_columns/default", json=bad).status_code in (400, 422)


def test_part_columns_unchanged(client):
    # CS detallari profillari avvalgidek (tekshiruvsiz JSON obyekt)
    r = client.post("/api/settings/part_columns", json={"name": "Eski", "data": {"columns": [{"key": "name", "visible": True, "extra": 1}]}})
    assert r.status_code == 200 and r.json()["data"]["columns"][0]["extra"] == 1
