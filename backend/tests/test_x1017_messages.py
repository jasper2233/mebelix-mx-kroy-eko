# -*- coding: utf-8 -*-
"""2026-10-17 · xabarlar auditi: 422 xabari odam o'qiydigan maydon nomi bilan (ru/uz), har xato alohida qator (`messages`),
noma'lum API yo'li — tilga mos 404, model tekshiruvi va stanok formati xabarlari — joriy tilda (bir tilda qotib qolmagan)."""
import pytest

from app.i18n import LANG, error_field_label, format_errors
from app.models import Part

UZ = {"Accept-Language": "uz"}


def test_field_label_paths():
    tok = LANG.set("ru")
    try:
        assert error_field_label(("body", "parts", 0, "length")) == "Детали №1 › Длина"
        assert error_field_label(("query", "unknown_x")) == "unknown_x"
        assert error_field_label(("body", "params", "function-after[_v(), dict]", "x")) == "Параметры › X"
        msg = format_errors([{"type": "greater_than_equal", "loc": ("body", "length"), "ctx": {"ge": 0}}])
        assert msg == "Длина: должно быть не меньше 0"
    finally:
        LANG.reset(tok)
    tok = LANG.set("uz")
    try:
        assert error_field_label(("body", "parts", 2, "width")) == "Detallar №3 › En"
    finally:
        LANG.reset(tok)


def test_422_has_human_message_and_lines(client):
    r = client.post("/api/remnants", json={"material_code": "Z", "length": 100, "width": 100, "qty": 1}).json()
    bad = client.patch(f"/api/remnants/{r['id']}", json={"length": -5, "width": "abc"})
    assert bad.status_code == 422
    j = bad.json()
    assert "Длина:" in j["message"] and "Ширина:" in j["message"]
    assert len(j["messages"]) == 2 and all(": " in m for m in j["messages"])
    assert j["detail"][0]["loc"][-1] in ("length", "width")                    # eski tuzilma saqlangan
    uz = client.patch(f"/api/remnants/{r['id']}", json={"length": -5}, headers=UZ).json()
    assert uz["message"].startswith("Uzunlik: ") and "kam bo'lmasligi" in uz["message"]


def test_unknown_api_path_404_is_localized(client):
    r = client.get("/api/__nope__/x")
    if r.status_code == 404 and r.headers.get("content-type", "").startswith("application/json"):
        d = r.json()["detail"]
        assert d != "Not Found"
        assert "Topilmadi" in client.get("/api/__nope__/x", headers=UZ).json()["detail"]


def test_model_validator_messages_follow_language():
    for lang, word in (("ru", "параметр"), ("uz", "parametr")):
        tok = LANG.set(lang)
        try:
            with pytest.raises(Exception) as e:
                Part(name="p", length=10, width=10, qty=1, user_params={"x": float("nan")})
            assert word in str(e.value)
        finally:
            LANG.reset(tok)


def test_ppfmt_messages_follow_language():
    from app.services.ppfmt import tooling
    tok = LANG.set("uz")
    try:
        with pytest.raises(ValueError, match="stanok asbobi ko'rsatilmagan: freza"):
            tooling.need_tool(type("J", (), {"tools": {}, "machine": ""})(), "mill", "front", 8)
    finally:
        LANG.reset(tok)
    with pytest.raises(ValueError, match="не указан инструмент станка: фреза"):
        tooling.need_tool(type("J", (), {"tools": {}, "machine": ""})(), "mill", "front", 8)
