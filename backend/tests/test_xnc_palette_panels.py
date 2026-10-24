"""XNC «Палитра» → tezkor panellar (onlayn kabi «Сверление», 2026-10-23): standart yoqilgan, eski sozlama (panels yo'q) buzilmaydi,
noma'lum kalitlar tashlanadi, saqlangan holat qaytadi."""
from app.services.xnc_tools import XncPalette


def test_panels_default_and_normalize():
    assert [(p.key, p.enabled) for p in XncPalette().panels] == [("drill", True)]
    assert [(p.key, p.enabled) for p in XncPalette.model_validate({"items": ["DrillFront"]}).panels] == [("drill", True)]
    d = XncPalette.model_validate({"items": None, "panels": [{"key": "zz"}, {"key": "drill", "enabled": False}]})
    assert [(p.key, p.enabled) for p in d.panels] == [("drill", False)]


def test_panels_saved_via_api(client):
    r = client.put("/api/settings/xnc_palette/default", json={"items": [], "panels": [{"key": "drill", "enabled": False}]})
    assert r.status_code == 200
    got = client.get("/api/settings/xnc_palette/default").json()
    assert got["panels"] == [{"key": "drill", "enabled": False}] and len(got["items"]) > 20     # buyruqlar — standartdan
