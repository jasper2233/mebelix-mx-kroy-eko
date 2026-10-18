"""O'zbek kirill (uz-Cyrl) tili: transliterator (lotin → kirill) va backend xabarlari / hisobotlari kirillda."""
import json
import os
import re

import pytest

from app import i18n
from app.uz_translit import to_cyrillic

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
CASES = json.load(open(os.path.join(FIX, "uz_translit_cases.json"), encoding="utf-8"))
WORDS = json.load(open(os.path.join(FIX, "uz_translit_words.json"), encoding="utf-8"))
CYRL = {"Accept-Language": "uz-Cyrl"}
LATIN_WORD = re.compile(r"(?<![A-Za-z{])[a-z]{4,}(?![A-Za-z}])")


# ───────────────────────── transliterator ─────────────────────────
@pytest.mark.parametrize("src,want", CASES, ids=[c[0][:40] or "empty" for c in CASES])
def test_translit_cases(src, want):
    assert to_cyrillic(src) == want


@pytest.mark.parametrize("src,want", sorted(WORDS.items()))
def test_translit_app_words(src, want):
    """Ilovadagi ~60 tipik so'z — o'zbek kirill imlosi (istisnolar fayli bilan)."""
    assert to_cyrillic(src) == want
    assert to_cyrillic(src.capitalize()) == want[:1].upper() + want[1:]


def test_translit_cases_count():
    assert len(CASES) >= 40 and len(WORDS) >= 50


def test_translit_idempotent_on_cyrillic():
    for _src, want in CASES:
        assert to_cyrillic(want) == want


def test_translit_deep():
    from app.uz_translit import deep
    assert deep({"a": ["Yo'q", ("Ha",)], "n": 5}) == {"a": ["Йўқ", ("Ҳа",)], "n": 5}


@pytest.mark.parametrize("v,want", [
    ("uz-Cyrl", "uz-Cyrl"), ("uz_cyrl", "uz-Cyrl"), ("UZ-CYRL", "uz-Cyrl"), ("uz-Cyrl-UZ", "uz-Cyrl"),
    ("uz-Cyrl,ru;q=0.8", "uz-Cyrl"), ("uz", "uz"), ("uz-Latn", "uz"), ("ru-RU", "ru"), ("", "ru"), (None, "ru"), ("en", "ru"),
])
def test_norm_lang(v, want):
    assert i18n.norm_lang(v) == want


def test_msg_catalog_cyrl_has_no_stray_latin():
    """Backend xabarlari katalogi: kirill ko'rinishida (o'rinbosarlarsiz) uzun lotin so'z deyarli qolmaydi."""
    tok = i18n.SCRIPT.set("cyrl")
    lt = i18n.LANG.set("uz")
    try:
        bad = []
        for key, (_ru, uz) in i18n.MSG.items():
            text = re.sub(r"\{[^{}]*\}|«[a-z_]+»|\([a-z_ |]+\)", "", i18n.cy(uz))
            for w in LATIN_WORD.findall(text):
                if w.lower() not in i18n_keep():
                    bad.append((key, w))
        assert len(bad) <= 40, bad[:40]
    finally:
        i18n.LANG.reset(lt)
        i18n.SCRIPT.reset(tok)


def i18n_keep():
    from app import uz_translit as T
    return T.KEEP | T.KEEP_LOWER | {f for f in T.FUNCS}


# ───────────────────────── API: uz-Cyrl so'rov — kirill javob ─────────────────────────
def test_api_404_message_cyrillic(client):
    r = client.get("/api/projects/nope-xyz", headers=CYRL)
    assert r.status_code == 404
    assert r.json()["detail"] == "Лойиҳа топилмади"
    assert client.get("/api/projects/nope-xyz", headers={"Accept-Language": "uz"}).json()["detail"] == "Loyiha topilmadi"
    assert client.get("/api/projects/nope-xyz", headers={"Accept-Language": "ru"}).json()["detail"] == "Проект не найден"


def test_api_422_field_names_cyrillic(client):
    pid = client.post("/api/projects", json={"name": "cyrl-422"}).json()["id"]
    p = client.post(f"/api/projects/{pid}/operations", json={"type": "CS", "code": "L16", "name": "LDSP"}).json()
    oid = p["operations"][-1]["id"]
    r = client.post(f"/api/projects/{pid}/operations/{oid}/parts", json=[{"name": "x", "length": -5, "width": 100, "qty": 1}],
                    headers=CYRL)
    assert r.status_code == 422
    text = json.dumps(r.json(), ensure_ascii=False)
    assert "Узунлик" in text and "Uzunlik" not in text


def test_report_html_cyrillic(client, kravat):
    pid, cs_id, _el = kravat
    client.post(f"/api/projects/{pid}/operations/{cs_id}/cut", json={})
    cy = client.get(f"/api/projects/{pid}/report", params={"lang": "uz-Cyrl"}).text
    lat = client.get(f"/api/projects/{pid}/report", params={"lang": "uz"}).text
    assert "lang='uz-Cyrl'" in cy and "Loyiha" in lat
    assert "Лойиҳа" in cy and "Loyiha" not in cy
    # foydalanuvchi ma'lumoti (loyiha nomi, detal nomlari) o'girilmaydi
    assert "Detskiy kravat" in cy and "Panel1" in cy


def test_report_lang_param_wins_over_header(client, kravat):
    pid, _cs, _el = kravat
    lat = client.get(f"/api/projects/{pid}/report", params={"lang": "uz"}, headers=CYRL).text
    assert "Loyiha" in lat and "Лойиҳа" not in lat


def test_label_templates_cyrillic(client):
    cy = [t for t in client.get("/api/label-templates", params={"lang": "uz-Cyrl"}).json() if t.get("builtin")]
    lat = [t for t in client.get("/api/label-templates", params={"lang": "uz"}).json() if t.get("builtin")]
    assert len(cy) == len(lat) and cy
    assert [c["name"] for c in cy] == [to_cyrillic(x["name"]) for x in lat]
    assert any(c["name"] != x["name"] for c, x in zip(cy, lat))


def test_label_variables_cyrillic(client):
    g = client.get("/api/label-variables", params={"lang": "uz-Cyrl"}).json()["groups"]
    titles = [v["title"] for grp in g for v in grp["vars"]]
    assert titles and sum(1 for t in titles if re.search(r"[ЎўҚқҒғҲҳ]", t)) > 10


def test_xnc_templates_cyrillic(client):
    lat = client.get("/api/xnc/templates", params={"lang": "uz"}).json()
    cy = client.get("/api/xnc/templates", params={"lang": "uz-Cyrl"}).json()
    lib = [(a, b) for a, b in zip(lat, cy) if a.get("builtin")]
    assert lib and all(b["name"] == to_cyrillic(a["name"]) for a, b in lib)


def test_postprocessor_labels_cyrillic(client):
    cy = {m["key"]: m.get("label", "") for m in client.get("/api/postprocessors", headers=CYRL).json() if m.get("machine")}
    lat = {m["key"]: m.get("label", "") for m in client.get("/api/postprocessors", headers={"Accept-Language": "uz"}).json()
           if m.get("machine")}
    assert cy and any("Arra markazi" in v for v in lat.values())
    assert any("Арра маркази" in v for v in cy.values()) and not any("Arra markazi" in v for v in cy.values())


def test_uz_latin_unchanged(client):
    """uz (lotin) javoblari avvalgidek — kirillga o'tmaydi."""
    r = client.get("/api/projects/nope-xyz", headers={"Accept-Language": "uz"})
    assert not re.search(r"[А-Яа-я]", r.json()["detail"])
