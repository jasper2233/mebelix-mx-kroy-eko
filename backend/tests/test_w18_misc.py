"""W18 / mayda bandlar: stanok sozlamalarida etiketka shabloni havolasi (`template` turi: F4Classic / KDT XML), «Что нового» v2.3
(i18n manbasi), frontend i18n ru/uz tengligi."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.services import pp_machine_schema as S
from app.services import settings

BASE = "/api/postprocessors/machines"
ROOT = Path(__file__).resolve().parents[2]
TPL_MACHINES = ("felder_f4classic", "kdt_presize_xml")


@pytest.fixture(autouse=True)
def clean(client):
    settings.set_default("pp_machines", {})
    yield
    settings.set_default("pp_machines", {})


def _flat(sch):
    return {p["key"]: p for g in sch["groups"] for p in g["params"]}


def test_only_f4classic_and_kdt_xml_have_template_param():
    have = {k for k, sch in S.SCHEMAS.items() if any(p.type == "template" for p in sch.params)}
    assert have == set(TPL_MACHINES)
    for k in TPL_MACHINES:
        p = next(p for p in S.SCHEMAS[k].params if p.type == "template")
        assert (p.key, p.group, p.default) == ("label_template", "label_files", "")
        assert p.ru.strip() and p.uz.strip()


def test_schema_endpoint_exposes_template_param_and_saves_references(client):
    for key in TPL_MACHINES:
        s = client.get(f"{BASE}/{key}/schema").json()
        p = _flat(s)["label_template"]
        assert p["type"] == "template" and p["default"] == "" and p["value"] == "" and p["modified"] is False
        r = client.put(f"{BASE}/{key}/params", json={"params": {"label_template": "builtin:detail"}})
        assert r.status_code == 200, r.text
        p = _flat(r.json())["label_template"]
        assert p["value"] == "builtin:detail" and p["modified"] is True and "label_template" in r.json()["modified"]
        # foydalanuvchi shabloni (kutubxona) va qaytarish (bo'sh = standart; siyrak saqlanadi)
        assert client.put(f"{BASE}/{key}/params", json={"params": {"label_template": "profile:12"}}).status_code == 200
        r = client.put(f"{BASE}/{key}/params", json={"params": {"label_template": ""}})
        assert r.status_code == 200 and _flat(r.json())["label_template"]["modified"] is False


@pytest.mark.parametrize("bad", ["x", "builtin:", "profile:", "profile:abc", "profile:-1", "builtin:a b", "builtin:" + "a" * 61,
                                 "http://evil", "../../etc/passwd", 5, True, None, ["builtin:detail"]])
def test_template_reference_rejects_anything_but_library_ids(client, bad):
    r = client.put(f"{BASE}/felder_f4classic/params", json={"params": {"label_template": bad}})
    assert r.status_code == 400, (bad, r.text)
    assert _flat(client.get(f"{BASE}/felder_f4classic/schema").json())["label_template"]["value"] == ""    # hech narsa saqlanmadi


def test_template_param_not_accepted_by_other_machines_and_error_is_localized(client):
    r = client.put(f"{BASE}/scm_wincut/params", json={"params": {"label_template": "builtin:detail"}})
    assert r.status_code == 400
    r = client.put(f"{BASE}/kdt_presize_xml/params", json={"params": {"label_template": "zzz"}}, headers={"Accept-Language": "uz"})
    assert r.status_code == 400 and "shabloni havolasi" in json.dumps(r.json(), ensure_ascii=False)
    r = client.put(f"{BASE}/kdt_presize_xml/params", json={"params": {"label_template": "zzz"}}, headers={"Accept-Language": "ru"})
    assert "Ссылка на шаблон" in json.dumps(r.json(), ensure_ascii=False)


def test_template_reference_reaches_machine_context(client):
    from app.services import pp_machine_ctx as C
    client.put(f"{BASE}/kdt_presize_xml/params", json={"params": {"label_template": "builtin:detail", "label_dx": 70.0}})
    assert S.resolve_params("kdt_presize_xml", C.saved_params("kdt_presize_xml"))["label_template"] == "builtin:detail"
    ref = client.get("/api/label-templates").json()                                   # havola kutubxona identifikatorlariga mos
    assert any(m["id"] == "builtin:detail" for m in ref)


# ───────────────────────── «Что нового» v2.3 va i18n ─────────────────────────
def _src():
    return (ROOT / "frontend" / "scripts" / "i18n_w6.py").read_text(encoding="utf-8")


def test_whatsnew_v23_is_first_version_and_covers_w7_to_w14():
    src = _src()
    keys = re.findall(r'^    \("(v\d+)"', src, flags=re.M)
    assert keys[0] == "v23" and keys[:3] == ["v23", "v22", "v21"]
    block = src.split('("v23"', 1)[1].split('("v22"', 1)[0]
    for must in ("Станки", "XNC", "этикет", "Экспорт проекта", "Погонаж", "SP", "CSE", "Заказ", "Импорт из других программ"):
        assert must in block, must
    assert "GibLab" not in block and "Giblab" not in block


def _load_json(name: str) -> dict:
    p = ROOT / "frontend" / "src" / "i18n" / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _flatten(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _flatten(v, f"{pre}{k}.")
        else:
            yield f"{pre}{k}", v


def test_built_i18n_has_v23_items_in_both_languages_and_same_keys():
    ru, uz = dict(_flatten(_load_json("ru"))), dict(_flatten(_load_json("uz")))
    assert set(ru) == set(uz)                                                          # har kalit ikkala tilda
    for lang in (ru, uz):
        items = [k for k in lang if re.fullmatch(r"whatsnew\.v23\.i\d+\.t", k)]
        assert len(items) >= 10
        assert lang["whatsnew.v23.date"] == "2026-10-02" and lang["whatsnew.v23.title"]
        assert all(lang[k.replace(".t", ".d")].strip() for k in items)
    assert ru["whatsnew.v23.title"] != uz["whatsnew.v23.title"]
    for k in ("importx.no_module", "importx.reset_all", "projects.col.no", "ppm.tpl_open", "import.tabs.simple", "import.tabs.materials"):
        assert ru[k] and uz[k], k
    assert "образец файла" in ru["importx.no_module"] and "namuna" in uz["importx.no_module"]
    assert not [k for k, v in {**ru, **uz}.items() if isinstance(v, str) and re.search(r"giblab", v, re.I)]    # «GibLab» so'zi yo'q
