"""2026-10-16 — XNC «Сохранить текущие параметры для использования по умолчанию»: narxlar xnc_defaults ga saqlanadi va
yangi XNC operatsiyasi ularni oladi."""


def test_xnc_price_defaults(client):
    r = client.put("/api/settings/xnc_defaults/default",
                   json={"drill_price": 150, "mill_price_m": 2000, "saw_price_m": 900, "extra_cost": 50})
    assert r.status_code == 200, r.text
    pid = client.post("/api/projects", json={"name": "XNC narx"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "XNC", "name": "a"}).json()
    x = p["operations"][-1]["xnc"]
    assert (x["drill_price"], x["mill_price_m"], x["saw_price_m"], x["extra_cost"]) == (150, 2000, 900, 50)
    assert client.put("/api/settings/xnc_defaults/default", json={"drill_price": -1}).status_code in (400, 422)
    client.put("/api/settings/xnc_defaults/default", json={})          # standartga qaytarish (boshqa testlarga ta'sir qilmasin)
