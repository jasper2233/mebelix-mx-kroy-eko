"""W7 · Postprotsessor stanoklari sozlamalari sxemasi (ParamGrid) va «etiketka maydonlari» jadvali: sxema to'liqligi (19 stanok),
tur/standart tekshiruvi, noto'g'ri qiymat 400, ifoda tekshiruvi, saqlash (pp_machines) va mavjud API buzilmasligi."""
import os

import pytest

from app.services import expr, settings
from app.services import pp_machine_schema as S
from app.services import postprocessors as pp

# sozlama sxemasi bor 19 ta pil markazi (v2.5 da qo'shilgan stanoklar — o'rnatilgan generatorlar, sxemasiz: bo'sh sxema)
SAW = [k for k, _n, g in pp.MACHINES if g == "saw" and k in S.SCHEMAS]
SAW_NEW = [k for k, _n, g in pp.MACHINES if g == "saw" and k not in S.SCHEMAS]
CNC = [k for k, _n, g in pp.MACHINES if g == "cnc"]
BASE = "/api/postprocessors/machines"


@pytest.fixture(autouse=True)
def clean(client):                       # client — baza jadvallari yaratilgandan keyin
    settings.set_default("pp_machines", {})
    yield
    settings.set_default("pp_machines", {})


def schema(client, key):
    r = client.get(f"{BASE}/{key}/schema")
    assert r.status_code == 200, r.text
    return r.json()


def put_params(client, key, params):
    return client.put(f"{BASE}/{key}/params", json={"params": params})


def put_labels(client, key, rows):
    return client.put(f"{BASE}/{key}/label-fields", json={"label_fields": rows})


def flat(sch):
    return {p["key"]: p for g in sch["groups"] for p in g["params"]}


# ───────────────────────── sxema to'liqligi ─────────────────────────
def test_schema_covers_all_19_saw_machines():
    assert len(SAW) == 20 and set(S.SCHEMAS) == set(SAW)        # 19 + FastPanel (versiya)
    assert {"scm_wincut", "scm_maestrocut", "holzma_ptx", "holzma_cadmatic4", "holzma_cadmatic3", "biesse_osi", "biesse_nc300",
            "felder_format4_pc6", "felder_format4_pc7", "felder_f4classic", "homag_chf", "kdt_presize_qk", "kdt_presize_xml",
            "scheer", "nanxing_cutsawfg", "nanxing_nxcutsaw", "shelling_mcs", "elmo3", "glass_gcode", "fastpanel"} == set(SAW)


def test_new_machines_have_empty_schema(client):
    """v2.5 da qo'shilgan stanoklar (sxemasiz) — schema endpoint bo'sh sxema qaytaradi, xato emas."""
    assert SAW_NEW and "aes_alpha" in SAW_NEW
    for key in SAW_NEW:
        j = schema(client, key)
        assert j["key"] == key and j["group"] == "saw" and j["groups"] == []


def test_every_param_is_well_formed():
    seen_texts = []
    for key, sch in S.SCHEMAS.items():
        keys = [p.key for p in sch.params]
        assert len(keys) == len(set(keys)), key                              # kalitlar noyob
        bools = {p.key for p in sch.params if p.type == "bool"}
        for p in sch.params:
            assert p.type in S.TYPES and p.group in S.GROUPS, (key, p.key)
            assert p.ru.strip() and p.uz.strip(), (key, p.key)                # ru va uz yorliq to'liq
            assert S.coerce(p, p.default) == p.default, (key, p.key)          # standart o'z turiga mos
            assert type(S.coerce(p, p.default)) is type(p.default)
            if p.type == "choice":
                assert p.options and any(o.value == p.default for o in p.options), (key, p.key)
                assert len({o.value for o in p.options}) == len(p.options)
            if p.type in ("mm", "float"):
                assert isinstance(p.default, float) and p.min is not None and p.max is not None
            if p.type == "int":
                assert isinstance(p.default, int) and not isinstance(p.default, bool)
            if p.enabled_if:
                assert p.enabled_if in bools, (key, p.key)                    # bog'liq bo'lgan parametr — bool
            seen_texts += [p.ru, p.uz]
            seen_texts += [t for o in p.options for t in (o.ru, o.uz)]
    assert not [t for t in seen_texts if "giblab" in t.lower()]                # interfeysda «GibLab» so'zi yo'q


def test_schema_endpoint_all_machines(client):
    for key in SAW:
        j = schema(client, key)
        assert j["key"] == key and j["group"] == "saw" and j["name"]
        assert j["values"] == j["defaults"] and j["modified"] == []
        assert set(j["values"]) == {p.key for p in S.SCHEMAS[key].params}
        assert (j["label_table"] is None) == (S.SCHEMAS[key].label_table is None)
        for g in j["groups"]:
            assert g["ru"] and g["uz"] and g["params"]
    # ishlov markazlari — hozircha bo'sh sxema
    for key in CNC:
        j = schema(client, key)
        assert j["group"] == "cnc" and j["groups"] == [] and j["values"] == {} and j["label_table"] is None


def test_unknown_machine_is_400_everywhere(client):
    assert client.get(f"{BASE}/nope/schema").status_code == 400
    assert put_params(client, "nope", {}).status_code == 400
    assert put_labels(client, "nope", []).status_code == 400
    assert client.post(f"{BASE}/nope/label-fields/preview", json={}).status_code == 400


def test_defaults_match_online_inventory(client):
    """06_online_korik.md §2 dagi standart qiymatlar."""
    w = flat(schema(client, "scm_wincut"))
    assert (w["translit_filenames"]["value"], w["print_labels"]["value"], w["label_mode"]["value"]) == (False, True, "normal")
    assert (w["create_list_file"]["value"], w["list_maps_in_lst"]["value"], w["mirror_cuts"]["value"]) == (False, True, True)
    assert w["list_dir"]["value"] == "C:\\wincut\\lst\\" and w["maps_dir"]["value"] == "C:\\wincut\\prg\\"
    assert (w["spread_by_multiplicity"]["value"], w["trim_uv"]["value"], w["trim_with_kerf"]["value"],
            w["use_p_cuts"]["value"]) == (False, 0, True, False)
    assert (w["vel_rotaz"]["value"], w["vel_avanz"]["value"]) == (3000, 30)
    assert w["list_dir"]["enabled_if"] == "create_list_file" and w["trim_uv"]["type"] == "mm" and w["list_dir"]["type"] == "path"
    m = flat(schema(client, "scm_maestrocut"))
    assert m["label_field_no"]["value"] == 64 and m["create_list_file"]["value"] is True
    assert m["list_dir"]["value"] == "C:\\MaestroCut\\Client\\xMix\\"
    e = flat(schema(client, "elmo3"))
    assert [e[k]["value"] for k in ("trim", "saw_blade_height", "height_width_ratio", "fence_long_min", "fence_long_max",
                                    "fence_cross_min", "fence_cross_max")] == [False, 49, 4, 2, 1600, 146, 3200]
    assert schema(client, "elmo3")["info"]["uz"]
    for k, dx, dy in (("felder_f4classic", 58, 60.5), ("kdt_presize_xml", 58, 60.5), ("scheer", 58, 40)):
        f = flat(schema(client, k))
        assert (f["label_dx"]["value"], f["label_dy"]["value"]) == (dx, dy), k
    assert flat(schema(client, "scheer"))["barcode"]["value"] is False
    assert flat(schema(client, "felder_f4classic"))["generate_label_files"]["value"] is True
    assert flat(schema(client, "biesse_osi"))["orientation"]["value"] == "horizontal"
    assert flat(schema(client, "biesse_nc300"))["rdiv"]["value"] == ""
    assert flat(schema(client, "glass_gcode"))["version"]["options"][0]["ru"] == "NCStudio v7"
    assert flat(schema(client, "holzma_cadmatic4"))["cut_order"]["value"] == "as_cadmatic"
    assert flat(schema(client, "homag_chf"))["latin_letters"]["value"] is False
    k = flat(schema(client, "kdt_presize_qk"))
    assert (k["trim_with_kerf"]["value"], k["trim_from_third_rotation"]["value"], k["generate_label_files"]["value"],
            k["distribute_maps_to_packs"]["value"]) == (True, 0, True, True)
    assert flat(schema(client, "shelling_mcs"))["trim_from_third_rotation"]["value"] == 0
    p = flat(schema(client, "felder_format4_pc6"))
    assert (p["remnants_on_maps"]["value"], p["label_by_part_number"]["value"]) == (False, False)
    ptx = flat(schema(client, "holzma_ptx"))
    assert [ptx[k]["value"] for k in ("pre_cut_head", "pre_cut_front", "pre_cut_rear", "label_data_at")] == [0, 0, 0, False]


def test_default_label_tables(client):
    def names(k):
        return [r["name"] for r in schema(client, k)["label_table"]["rows"]]
    assert names("scm_wincut") == [f"Campo{i}" for i in range(10, 15)]
    assert schema(client, "scm_wincut")["label_table"]["rows"][0]["expr"] == ""
    assert names("scm_maestrocut")[:4] == ["Codice", "Lunghezza", "Larghezza", "Richiesti"]
    assert names("nanxing_cutsawfg") == [f"Field{i}" for i in range(1, 21)]
    assert names("nanxing_nxcutsaw") == [f"F{i}" for i in range(1, 21)]
    assert len(names("felder_format4_pc6")) == 17 and len(names("felder_format4_pc7")) == 17
    assert names("felder_format4_pc6")[:2] == ["Part description (16)", "Headdata.text(30)"]
    assert names("biesse_osi")[0] == "Код" and len(names("biesse_osi")) >= 15
    for k in ("holzma_ptx", "shelling_mcs"):
        t = schema(client, k)["label_table"]
        assert t["kind"] == "udi" and t["rows"] == [] and "PARTS_UDI" in t["title"]["ru"]
    for k in ("holzma_cadmatic3", "biesse_nc300", "felder_f4classic", "homag_chf", "kdt_presize_qk", "kdt_presize_xml", "scheer",
              "elmo3", "glass_gcode"):
        assert schema(client, k)["label_table"] is None, k
    # 06 §2 dagi ifodalar (ko'rinadigan qatorlar)
    mx = {r["name"]: r["expr"] for r in schema(client, "scm_maestrocut")["label_table"]["rows"]}
    assert mx["Lunghezza"] == "format('0.00',length)" and mx["Richiesti"] == "if(waste,count,usedCount)"
    assert mx["CodiceBordo1"] == "if(empty(ets),' ',ets)"
    osi = {r["name"]: r["expr"] for r in schema(client, "biesse_osi")["label_table"]["rows"]}
    assert osi["Код"] == "'P' + part.id" and osi["Текстура"] == "if(txt,1,0)" and osi["Данные отхода"] == "now('yyyy-MM-dd')"
    pc7 = {r["name"]: r["expr"] for r in schema(client, "felder_format4_pc7")["label_table"]["rows"]}
    assert pc7["Edge top"] == "if(empty(ets),'','('+ets+') '+etn)" and pc7["Part.text11"] == "'#P('+part.id+')'"


def test_all_default_expressions_compile_and_evaluate_on_sample(client):
    """Standart ifodalar `expr.compile_check` dan o'tadi va namuna detalda xatosiz hisoblanadi (GibLab o'zgaruvchi nomlari —
    `usedCount`, `indexInOperation`, `ets/ebs/els/ers`, `ett…`, `etn…`, `XNC1`, `grtn…`, `mill/drill/groove` — taxallus sifatida ishlaydi)."""
    n = 0
    for key, sch in S.SCHEMAS.items():
        if sch.label_table is None:
            continue
        for name, src in sch.label_table.rows:
            if src:
                expr.compile_check(src)
                n += 1
        r = client.post(f"{BASE}/{key}/label-fields/preview", json={})
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["source"] == "sample" and len(j["fields"]) == len(sch.label_table.rows)
        for f in j["fields"]:
            assert f["ok"] is True and f["error"] is None, (key, f["name"], f["error"])
    assert n >= 90


def test_gib_variable_aliases_work_in_label_context(client):
    rows = [dict(name=n, expr=e) for n, e in (
        ("a", "usedCount"), ("b", "indexInOperation"), ("c", "ets+ebs+els+ers"), ("d", "ett+ebt+elt+ert"),
        ("e", "etn+ebn+eln+ern"), ("f", "grtn+grbn+grln+grrn"), ("g", "XNC1+XNC2"), ("h", "if(mill or drill or groove,1,0)"),
        ("i", "detail.length"), ("j", "format('0.00',length)"), ("k", "if(empty(ets),' ',ets)"), ("l", "crc16(project.name)"))]
    j = client.post(f"{BASE}/scm_wincut/label-fields/preview", json={"fields": rows}).json()
    assert all(f["ok"] for f in j["fields"]), [f for f in j["fields"] if not f["ok"]]
    got = {f["name"]: f["value"] for f in j["fields"]}
    assert got["b"] == 1 and got["c"] == "AB" and got["d"] == pytest.approx(2.4) and got["e"] == "ПВХ 0.4/19ПВХ 2/19" and got["f"] == ""
    assert got["i"] == 748.0 and got["j"] == "746.00" and got["k"] == "A" and isinstance(got["l"], int)


# ───────────────────────── parametrlar: saqlash va tekshirish ─────────────────────────
def test_params_roundtrip_sparse_and_reset(client):
    r = put_params(client, "scm_wincut", {"trim_uv": 5, "list_dir": "D:\\lst\\", "use_p_cuts": True, "vel_avanz": 30})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["values"]["trim_uv"] == 5.0 and j["values"]["list_dir"] == "D:\\lst\\" and j["values"]["use_p_cuts"] is True
    assert set(j["modified"]) == {"trim_uv", "list_dir", "use_p_cuts"}                 # vel_avanz = standart — farq emas
    assert flat(j)["trim_uv"]["modified"] is True and flat(j)["vel_avanz"]["modified"] is False
    raw = settings.get_default("pp_machines")
    assert raw["params"]["scm_wincut"] == {"trim_uv": 5.0, "list_dir": "D:\\lst\\", "use_p_cuts": True}   # siyrak saqlash
    assert schema(client, "scm_wincut")["values"]["trim_uv"] == 5.0                    # qayta o'qish
    assert schema(client, "scm_maestrocut")["modified"] == []                          # boshqa stanokka tegmaydi
    # to'liq almashtirish: yuborilmagan parametr — standart
    r = put_params(client, "scm_wincut", {"vel_rotaz": 4000})
    assert r.json()["modified"] == ["vel_rotaz"] and r.json()["values"]["trim_uv"] == 0.0
    # standartga qaytarish
    r = put_params(client, "scm_wincut", {})
    assert r.json()["modified"] == [] and "params" in settings.get_default("pp_machines")
    assert "scm_wincut" not in settings.get_default("pp_machines")["params"]


def test_params_type_and_range_validation_400(client):
    bad = [
        ("scm_wincut", {"print_labels": "true"}),            # bool qat'iy
        ("scm_wincut", {"print_labels": 1}),
        ("scm_wincut", {"vel_rotaz": 1.5}),                  # int — kasr emas
        ("scm_wincut", {"vel_rotaz": True}),                 # bool — son emas
        ("scm_wincut", {"vel_rotaz": "3000"}),
        ("scm_wincut", {"vel_rotaz": -1}),                   # diapazon
        ("scm_wincut", {"trim_uv": -0.5}),
        ("scm_wincut", {"trim_uv": 10 ** 9}),
        ("scm_wincut", {"trim_uv": None}),
        ("scm_wincut", {"list_dir": 5}),                     # path — satr
        ("scm_wincut", {"list_dir": "C:\\a\nb"}),            # boshqaruv belgisi
        ("scm_wincut", {"list_dir": "C:\\a<b>"}),            # yo'lda taqiqlangan belgilar
        ("scm_wincut", {"list_dir": "x" * 400}),
        ("biesse_osi", {"orientation": "diagonal"}),         # choice — ro'yxatdan
        ("biesse_osi", {"orientation": 1}),
        ("holzma_cadmatic4", {"cut_order": "whatever"}),
        ("biesse_osi", {"program_version": "a" * 400}),
        ("biesse_osi", {"program_version": "a\x00b"}),
        ("elmo3", {"height_width_ratio": "4"}),
        ("elmo3", {"fence_long_max": 10 ** 9}),
        ("felder_f4classic", {"label_dx": 0}),               # min 1
    ]
    for key, params in bad:
        before = schema(client, key)["values"]
        r = put_params(client, key, params)
        assert r.status_code == 400, (key, params, r.text)
        j = r.json()
        assert isinstance(j["detail"], str) and j["errors"] and j["errors"][0]["key"] in params, j
        assert schema(client, key)["values"] == before                              # xatoda hech narsa saqlanmaydi
    # notekis tarkib
    assert client.put(f"{BASE}/scm_wincut/params", json={"params": [1, 2]}).status_code == 422
    assert client.put(f"{BASE}/scm_wincut/params", json={}).status_code == 422


def test_params_unknown_key_is_400_and_lists_all_errors(client):
    r = put_params(client, "scm_wincut", {"nope": 1, "vel_rotaz": "x", "trim_uv": 3})
    assert r.status_code == 400
    errs = {e["key"]: e["message"] for e in r.json()["errors"]}
    assert set(errs) == {"nope", "vel_rotaz"}                                      # to'g'ri `trim_uv` xato emas
    assert schema(client, "scm_wincut")["modified"] == []                          # atomik
    assert put_params(client, "scm_wincut", {"vel_rotaz": 1}).status_code == 200
    # ishlov markazi — bo'sh sxema: har qanday kalit noma'lum, bo'sh to'plam mumkin
    assert put_params(client, "woodwop", {"x": 1}).status_code == 400
    assert put_params(client, "woodwop", {}).status_code == 200


def test_choice_custom_and_valid_values(client):
    assert put_params(client, "biesse_osi", {"orientation": "vertical", "program_version": "5.3"}).status_code == 200
    j = schema(client, "biesse_osi")
    assert flat(j)["orientation"]["value"] == "vertical" and flat(j)["orientation"].get("custom") is not True
    # ro'yxati to'liq bo'lmagan variantlar (custom) — boshqa matn ham mumkin
    assert flat(schema(client, "holzma_cadmatic4"))["orientation"]["custom"] is True
    assert put_params(client, "holzma_cadmatic4", {"orientation": "boshqa", "cut_order": "from_trim"}).status_code == 200
    assert put_params(client, "holzma_cadmatic4", {"orientation": ""}).status_code == 400
    assert put_params(client, "scm_wincut", {"trim_uv": 2, "vel_rotaz": 100}).json()["values"]["vel_rotaz"] == 100


def test_path_params_are_plain_strings_no_filesystem(client, tmp_path):
    """Yo'l — faqat satr: server diskka yozmaydi/o'qimaydi (mavjud bo'lmagan yo'l ham saqlanadi, papka yaratilmaydi)."""
    ghost = str(tmp_path / "no_such" / "dir") + os.sep
    assert put_params(client, "scm_wincut", {"list_dir": ghost, "maps_dir": "\\\\server\\share\\prg\\"}).status_code == 200
    assert schema(client, "scm_wincut")["values"]["list_dir"] == ghost
    assert schema(client, "scm_wincut")["values"]["maps_dir"] == "\\\\server\\share\\prg\\"
    assert not os.path.exists(ghost) and not (tmp_path / "no_such").exists()
    assert put_params(client, "holzma_ptx", {"opt_params_file": "C:\\x\\a.prm", "saw_params_file": ""}).status_code == 200


def test_machines_put_keeps_params_and_labels_and_old_api_unchanged(client):
    put_params(client, "scm_wincut", {"trim_uv": 7})
    put_labels(client, "scm_wincut", [dict(name="Campo10", expr="project.name")])
    d = client.put("/api/postprocessors/machines", json={"enabled": {"scm_wincut": True}, "profile": {}, "prefix": True}).json()
    m = next(m for g in d["groups"] for m in g["machines"] if m["key"] == "scm_wincut")
    assert m["enabled"] is True and d["prefix"] is True
    old = {"key", "name", "group", "enabled", "profile_id", "profile_name", "bound"}    # eski javob maydonlari o'zgarmagan
    assert old <= set(m) and set(m) - old <= {"native", "native_ext", "native_note"}     # v2.5 qo'shimchalari
    j = schema(client, "scm_wincut")
    assert j["values"]["trim_uv"] == 7.0 and j["label_table"]["rows"] == [dict(name="Campo10", expr="project.name")]
    d = client.put("/api/postprocessors/machines", json={"enabled": {}, "profile": {}, "prefix": False}).json()
    assert not any(m["enabled"] for g in d["groups"] for m in g["machines"])
    assert schema(client, "scm_wincut")["values"]["trim_uv"] == 7.0


# ───────────────────────── etiketka maydonlari: saqlash va tekshirish ─────────────────────────
def test_label_fields_save_reset_and_is_default(client):
    j = schema(client, "scm_maestrocut")["label_table"]
    assert j["is_default"] is True and j["rows"] == j["defaults"]
    rows = j["rows"] + [dict(name="Extra", expr="usedCount * 2")]
    r = put_labels(client, "scm_maestrocut", rows)
    assert r.status_code == 200, r.text
    t = r.json()["label_table"]
    assert t["is_default"] is False and t["rows"][-1] == dict(name="Extra", expr="usedCount * 2") and len(t["defaults"]) == 9
    assert settings.get_default("pp_machines")["label_fields"]["scm_maestrocut"] == rows
    # tartibni o'zgartirish ham farq
    assert put_labels(client, "scm_maestrocut", list(reversed(j["rows"]))).json()["label_table"]["is_default"] is False
    # standartga qaytarish: standart jadval yuboriladi → saqlanmaydi
    r = put_labels(client, "scm_maestrocut", j["defaults"])
    assert r.json()["label_table"]["is_default"] is True
    assert "scm_maestrocut" not in (settings.get_default("pp_machines").get("label_fields") or {})
    # bo'sh jadval — to'g'ri (PARTS_UDI kabi); standartdan farq
    assert put_labels(client, "scm_maestrocut", []).json()["label_table"]["rows"] == []
    assert put_labels(client, "holzma_ptx", [dict(name="UDI1", expr="part.code")]).status_code == 200
    assert schema(client, "holzma_ptx")["label_table"]["rows"] == [dict(name="UDI1", expr="part.code")]
    assert put_labels(client, "holzma_ptx", []).json()["label_table"]["is_default"] is True


def test_label_fields_expression_and_name_validation(client):
    r = put_labels(client, "scm_wincut", [dict(name="A", expr="1+"), dict(name="B", expr="usedCount"),
                                          dict(name="C", expr="if(1,2")])
    assert r.status_code == 400
    j = r.json()
    assert [(e["index"], e["field"], e["name"]) for e in j["errors"]] == [(0, "expr", "A"), (2, "expr", "C")]
    assert all(e["message"] for e in j["errors"]) and isinstance(j["detail"], str)
    assert schema(client, "scm_wincut")["label_table"]["is_default"] is True               # xatoda saqlanmaydi
    # nom: bo'sh / takror / juda uzun / matn emas
    for rows, idx in (([dict(name="  ", expr="1")], 0), ([dict(name="X", expr="1"), dict(name="X", expr="2")], 1),
                      ([dict(name="n" * 100, expr="1")], 0), ([dict(name=5, expr="1")], 0)):
        r = put_labels(client, "scm_wincut", rows)
        assert r.status_code == 400 and r.json()["errors"][0]["index"] == idx and r.json()["errors"][0]["field"] == "name", rows
    # ifoda matn emas / qator lug'at emas / ro'yxat emas / juda ko'p qator
    assert put_labels(client, "scm_wincut", [dict(name="A", expr=5)]).status_code == 400
    assert put_labels(client, "scm_wincut", ["A"]).status_code == 400
    assert client.put(f"{BASE}/scm_wincut/label-fields", json={"label_fields": {"A": 1}}).status_code == 422
    assert put_labels(client, "scm_wincut", [dict(name=f"F{i}", expr="1") for i in range(S.MAX_LABEL_ROWS + 1)]).status_code == 400
    assert put_labels(client, "scm_wincut", [dict(name=f"F{i}", expr="1") for i in range(S.MAX_LABEL_ROWS)]).status_code == 200
    # bo'sh ifoda — to'g'ri; noma'lum o'zgaruvchi nomi saqlashda emas, ko'rishda topiladi (compile_check faqat sintaksis)
    assert put_labels(client, "scm_wincut", [dict(name="A", expr=""), dict(name="B", expr="no_such_var + 1")]).status_code == 200
    # jadvali yo'q stanoklar va ishlov markazlari
    assert put_labels(client, "homag_chf", []).status_code == 400
    assert put_labels(client, "woodwop", [dict(name="A", expr="1")]).status_code == 400
    assert client.post(f"{BASE}/homag_chf/label-fields/preview", json={}).status_code == 400


def test_error_messages_follow_language(client):
    r = client.put(f"{BASE}/scm_wincut/params", json={"params": {"vel_rotaz": "x", "zzz": 1}}, headers={"Accept-Language": "uz"})
    assert r.status_code == 400 and "saqlanmadi" in r.json()["detail"]
    assert any("noma'lum" in e["message"] for e in r.json()["errors"])
    r = client.put(f"{BASE}/scm_wincut/params", json={"params": {"vel_rotaz": "x"}}, headers={"Accept-Language": "ru"})
    assert "не сохранены" in r.json()["detail"]
