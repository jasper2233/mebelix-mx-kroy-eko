"""W6: ifoda API (`/api/expr/functions`, `/api/expr/check`) va ifoda hujjatlari (`services/expr_docs.py`)."""
import random
import re

import pytest

from app.services import expr as E
from app.services import expr_docs as D

UZ = {"Accept-Language": "uz"}


# ───────────────────────── Hujjatlar (expr_docs) ─────────────────────────
def test_docs_cover_every_function_exactly():
    listed = {n for rows in E.FUNCTION_GROUPS.values() for n, _s in rows}
    assert set(D.DOCS) == listed                               # hujjatsiz funksiya ham, ortiqcha hujjat ham yo'q
    assert listed == set(E.function_names())                   # FUNCTION_GROUPS dvigatel reestri bilan mos
    assert len(listed) == 65                                   # 28 matematik + 25 matn + 7 konvertatsiya + 5 aralash (jumladan if)
    for name, (ru, uz, ex) in D.DOCS.items():
        assert ru.strip() and uz.strip() and ex.strip(), name
        assert ru != uz, name                                  # uz — o'zbekcha (rus matnining nusxasi emas)


def test_every_example_runs_and_pure_results_are_stable():
    for row in D.function_rows():
        if row["name"] in D.DYNAMIC:
            continue
        assert row["example_type"] != "error", row["example"]
        v = E.evaluate(row["example"], {}, rng=random.Random(1))
        assert E.to_text(v) == row["example_result"] and D.type_name(v) == row["example_type"], row["example"]
    # test-vektorlar (yordam misollariga mos, qo'lda tekshirilgan)
    got = {r["name"]: r["example_result"] for r in D.function_rows()}
    assert got["abs"] == "7" and got["ceil"] == "2.0" and got["floor"] == "-2.0" and got["round"] == "2.57"
    assert got["crc16"] == "63534" and got["crc32"] == "-662733300" and got["translit"] == "Shkaf"
    assert got["lspace"] == "ab000" and got["rspace"] == "000ab" and got["roman"] == "MMXXVI"
    assert got["format"] == "3.14" and got["find"] == "3" and got["findr"] == "5" and got["boolean"] == "true"
    assert got["ns"] == "" and got["empty"] == "true" and got["dectohex"] == "ff" and got["calculate"] == "14"
    assert D.type_name(None) == "null" and D.type_name(True) == "boolean" and D.type_name(3) == "integer"
    assert D.type_name(2.0) == "double" and D.type_name("x") == "string"


def test_dynamic_examples_described_not_computed():
    rows = {r["name"]: r for r in D.function_rows()}
    assert rows["random"]["example_result"] == "0.0 … 1.0" and rows["random"]["pure"] is False
    assert rows["uuid"]["pure"] is False and rows["now"]["pure"] is False
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", rows["now"]["example_result"])
    assert rows["abs"]["pure"] is True
    for name in ("random", "uuid", "now"):                     # misollarning o'zi esa ishlaydi
        E.evaluate(rows[name]["example"], {})


def test_constants_and_operators_examples():
    consts = {c["name"]: c for c in D.constant_rows()}
    assert set(consts) == {"pi", "e", "true", "false", "null"}
    assert consts["pi"]["example_result"].startswith("3.14159") and consts["null"]["example_type"] == "null"
    ops = D.operator_rows()
    assert len(ops) >= 6
    for o in ops:
        assert o["example_type"] != "error", o["example"]
        assert o["description_ru"] and o["description_uz"]
    assert next(o for o in ops if o["example"] == "7 / 2")["example_result"] == "3"        # butun ÷ butun


# ───────────────────────── GET /api/expr/functions ─────────────────────────
def test_functions_endpoint_shape(client):
    r = client.get("/api/expr/functions")
    assert r.status_code == 200
    j = r.json()
    assert [g["key"] for g in j["groups"]] == ["math", "text", "convert", "misc"]
    assert sum(g["count"] for g in j["groups"]) == len(j["functions"]) == 65
    f0 = j["functions"][0]
    assert {"group", "name", "signature", "description_ru", "description_uz", "description", "example", "example_result",
            "example_type", "pure"} <= set(f0)
    names = [f["name"] for f in j["functions"]]
    assert len(names) == len(set(names))
    assert "if" in names and "format" in names and "crc32" in names and "round" in names
    by = {f["name"]: f for f in j["functions"]}
    assert by["round"]["signature"] == "round(x[, n])" and by["round"]["group"] == "math"
    assert by["left"]["group"] == "text" and by["dectohex"]["group"] == "convert" and by["now"]["group"] == "misc"
    assert {c["name"] for c in j["constants"]} == {"pi", "e", "true", "false", "null"}
    assert j["operators"] and j["limits"]["max_length"] == E.MAX_SRC and j["limits"]["max_steps"] == E.MAX_STEPS


def test_functions_language_follows_header(client):
    ru = client.get("/api/expr/functions").json()
    uz = client.get("/api/expr/functions", headers=UZ).json()
    r_abs = next(f for f in ru["functions"] if f["name"] == "abs")
    u_abs = next(f for f in uz["functions"] if f["name"] == "abs")
    assert r_abs["description"] == r_abs["description_ru"] and u_abs["description"] == u_abs["description_uz"]
    assert r_abs["description_ru"] == u_abs["description_ru"] and r_abs["description"] != u_abs["description"]


# ───────────────────────── POST /api/expr/check ─────────────────────────
def check(client, expr, context=None, degrees=False, headers=None):
    body = {"expr": expr, "degrees": degrees}
    if context is not None:
        body["context"] = context
    r = client.post("/api/expr/check", json=body, headers=headers or {})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("expr,typ,text,value", [
    ("1+2", "integer", "3", 3), ("7/2", "integer", "3", 3), ("7.0/2", "double", "3.5", 3.5), ("2^10", "double", "1024.0", 1024.0),
    ("'a'+1", "string", "a1", "a1"), ("1<2", "boolean", "true", True), ("1=2", "boolean", "false", False),
    ("null", "null", "", None), ("if(2>1, 'yes', 'no')", "string", "yes", "yes"), ("round(-1.5)", "integer", "-1", -1),
    ("left('abcdef', 2) + right('abcdef', 2)", "string", "abef", "abef"), ("crc32('test')", "integer", "-662733300", -662733300),
    ("format('0.00', 3.14159)", "string", "3.14", "3.14"), ("1 if 2>1 else 3", "integer", "1", 1), ("pi", "double", None, None),
])
def test_check_ok(client, expr, typ, text, value):
    j = check(client, expr)
    assert j["ok"] is True and j["error"] is None and j["stage"] is None and j["type"] == typ, j
    if text is not None:
        assert j["value_text"] == text and j["value"] == value and type(j["value"]) is type(value)


def test_check_context_values(client):
    j = check(client, "dx*2 + dy", {"dx": 480, "dy": 0.5})
    assert j["ok"] and j["type"] == "double" and j["value"] == 960.5
    j = check(client, "part.id + 1", {"part.id": 7})                       # nuqtali nomlar
    assert j["ok"] and j["value"] == 8 and j["type"] == "integer"
    j = check(client, "name + '-' + flag", {"name": "Shkaf", "flag": True})
    assert j["ok"] and j["value"] == "Shkaf-true"
    j = check(client, "empty(x)", {"x": None})
    assert j["ok"] and j["value"] is True
    j = check(client, "boolean(x)", {"x": "T"})
    assert j["ok"] and j["value"] is True


def test_check_error_stages_and_language(client):
    j = check(client, "dx*2")                                              # o'zgaruvchi berilmagan
    assert j["ok"] is False and j["stage"] == "eval" and "dx" in j["error"] and j["value"] is None and j["type"] is None
    j_uz = check(client, "dx*2", headers=UZ)
    assert "noma'lum o'zgaruvchi" in j_uz["error"] and "неизвестная" in j["error"]
    j = check(client, "1+")
    assert j["ok"] is False and j["stage"] == "syntax" and j["error"]
    assert check(client, "")["stage"] == "syntax" and check(client, "   ")["stage"] == "syntax"
    j = check(client, "1/0")
    assert j["ok"] is False and j["stage"] == "eval" and "ноль" in j["error"]
    assert "nolga" in check(client, "1/0", headers=UZ)["error"]
    j = check(client, "nofunc(1)")
    assert j["ok"] is False and "nofunc" in j["error"]
    assert check(client, "sqrt(1,2)")["ok"] is False                       # argumentlar soni
    assert check(client, "sqrt(-1)")["ok"] is False                        # domen xatosi — jim 0 emas


def test_check_degrees_flag(client):
    rad = check(client, "sin(90)")
    deg = check(client, "sin(90)", degrees=True)
    assert rad["ok"] and abs(rad["value"] - 0.8939966636005579) < 1e-12
    assert deg["ok"] and deg["value"] == pytest.approx(1.0)
    assert check(client, "cos(pi)")["value"] == pytest.approx(-1.0)        # standart — radian
    assert check(client, "acos(-1)", degrees=True)["value"] == pytest.approx(180.0)


def test_check_limits(client):
    long_ok = "+".join(["1"] * 400)                                         # 799 belgi — uzunlik chegarasida, lekin chuqur zanjir
    j = check(client, long_ok)
    assert j["ok"] is False and j["stage"] == "eval", j                    # hisoblash daraxti chuqurligi chegarasi
    too_long = "1+" * 600 + "1"                                            # 1201 belgi > 1000
    j = check(client, too_long)
    assert j["ok"] is False and j["stage"] == "syntax" and "1000" in j["error"]
    r = client.post("/api/expr/check", json={"expr": "1" * 6000})          # so'rov chegarasi (422)
    assert r.status_code == 422
    assert check(client, "rept('abcdefghij', 2000)")["ok"] is False        # natija matni > 10 000
    assert check(client, "2^100")["ok"] is False                           # daraja chegarasi
    # calculate() ichma-ich chuqurligi
    s = "1+1"
    for _i in range(6):
        s = "calculate('" + s.replace("\\", "\\\\").replace("'", "\\'") + "')"
    assert check(client, s)["ok"] is False
    shallow = check(client, "calculate('calculate(\\'1+2\\')')")
    assert shallow["ok"] and shallow["value"] == 3


def test_check_context_limits(client):
    r = client.post("/api/expr/check", json={"expr": "1", "context": {f"v{i}": i for i in range(201)}})
    assert r.status_code == 400
    assert client.post("/api/expr/check", json={"expr": "1", "context": {f"v{i}": i for i in range(200)}}).status_code == 200
    assert client.post("/api/expr/check", json={"expr": "1", "context": {"x" * 101: 1}}).status_code == 400
    assert client.post("/api/expr/check", json={"expr": "1", "context": {"x": 10 ** 16}}).status_code == 400
    assert client.post("/api/expr/check", json={"expr": "1", "context": {"x": "z" * 1001}}).status_code == 400
    r = client.post("/api/expr/check", content='{"expr": "x", "context": {"x": 1e999}}', headers={"Content-Type": "application/json"})
    assert r.status_code == 400                                             # cheksiz qiymat
    assert client.post("/api/expr/check", json={"expr": "1", "context": {"x": [1]}}).status_code == 422    # tur noto'g'ri
    assert client.post("/api/expr/check", json={"expr": "1", "context": {"x": 1}}, headers=UZ).status_code == 200
    r = client.post("/api/expr/check", json={"expr": "1", "context": {"x" * 101: 1}}, headers=UZ)
    assert "yaroqsiz" in r.json()["detail"]


@pytest.mark.parametrize("expr", [
    "__import__('os').system('echo')", "().__class__", "open('x')", "exec('1')", "eval('1')", "a.b.c", "x[0]", "lambda: 1",
    "import os", "1; 2", "`1`", "$x", "{1:2}", "[1,2]", "'abc", "\"abc", "'\\u12'", "'\\q'", "1e999", "999999999999*999999999999",
    "format('0.0E', 1e300)", "format('#,##0', 1e30)", "now('qq')", "calculate(calculate('1'))", "mid('abc', 0, 99999999)",
    "rept('a', -1)", "roman(0)", "DecToHex(1e30)", "HexToDec('zz')", "double('x')", "round(1, 99)", "logx(1, 1)",
    "²+1", "1²", "①", "x²", "½", "٣+٤", "１２＋３", "ǅ(1)", "áb", "\u0000", "1​+1",
])
def test_check_hostile_inputs_never_crash(client, expr):
    r = client.post("/api/expr/check", json={"expr": expr})
    assert r.status_code == 200, (expr, r.text)
    j = r.json()
    assert isinstance(j["ok"], bool) and (j["ok"] or j["error"])


@pytest.mark.parametrize("src", ["²", "1²", "1,①", ".①", "①+1", "x ,②"])
def test_engine_rejects_non_decimal_digits_without_crashing(src):
    """`str.isdigit()` rost, lekin `\\d` mos kelmaydigan belgilar (², ①) avval AttributeError berardi."""
    with pytest.raises(ValueError):
        E.evaluate(src, {"x": 1})
    with pytest.raises(ValueError):
        E.compile_check(src)


def test_engine_raises_only_value_error_on_garbage():
    """Dvigatel har qanday kirishda faqat ValueError (foydalanuvchi xabari) beradi — boshqa istisno API'da 500 bo'lardi."""
    rng = random.Random(7)
    alphabet = list("0123456789.,eE+-*/%^<>=!()'\"\\ \tabxyzAB_") + ["²", "①", "٣", "½", "ǅ", "é", "ы", "́", "​", "$", "@", "#",
                                                                    "and", "or", "not", "xor", "if", "else", "true", "null", "pi", "\\u", "\\n"]
    funcs = ["abs", "round", "mid", "format", "now", "left", "find", "replace", "rept", "lspace", "calculate", "DecToHex", "roman", "logx"]
    for _i in range(4000):
        parts = [rng.choice(alphabet) for _ in range(rng.randint(1, 12))]
        if rng.random() < 0.4:
            parts.insert(rng.randint(0, len(parts)), rng.choice(funcs) + "(")
        src = "".join(parts)
        try:
            E.evaluate(src, {"x": 1, "a": "t"})
        except ValueError:
            pass
        try:
            E.compile_check(src)
        except ValueError:
            pass


def test_check_fuzz_no_server_errors(client):
    rng = random.Random(20261002)
    atoms = ["1", "2.5", "x", "'s'", "true", "null", "pi", "(", ")", "+", "-", "*", "/", "%", "^", "<", ">=", "=", "<>", "and", "or",
             "not", "xor", ",", "abs", "if", "len", "mid", "format", "round", "max", ".", "'", "\\"]
    for _i in range(250):
        expr = " ".join(rng.choice(atoms) for _ in range(rng.randint(1, 14)))
        r = client.post("/api/expr/check", json={"expr": expr, "context": {"x": 3}})
        assert r.status_code == 200, (expr, r.text)
        j = r.json()
        assert j["ok"] or j["error"], expr
        if j["ok"]:
            assert j["type"] in ("integer", "double", "boolean", "string", "null"), expr


def test_check_does_not_leak_or_mutate_between_calls(client):
    a = check(client, "x", {"x": 1})
    b = check(client, "x")                                                  # oldingi kontekst esda qolmaydi
    assert a["ok"] and not b["ok"]
    assert check(client, "now('yyyy')")["value_text"].isdigit()


def test_expr_api_requires_auth_when_enabled(client, monkeypatch):
    """Autentifikatsiya yoqilganda (MES SSO) ifoda API ham himoyalangan; viewer roli ham ifodani tekshira oladi (faqat o'qish/hisoblash)."""
    import time

    import jwt
    monkeypatch.setenv("MEBELIX_AUTH_REQUIRED", "1")
    monkeypatch.setenv("MEBELIX_JWT_SECRET", "s3cret-for-tests-only-0123456789")
    assert client.get("/api/expr/functions").status_code == 401
    assert client.post("/api/expr/check", json={"expr": "1+1"}).status_code == 401
    tok = jwt.encode({"sub": "u7", "name": "Ali", "exp": int(time.time()) + 60}, "s3cret-for-tests-only-0123456789", algorithm="HS256")
    h = {"Authorization": f"Bearer {tok}"}
    assert client.get("/api/expr/functions", headers=h).status_code == 200
    assert client.post("/api/expr/check", json={"expr": "1+1"}, headers=h).json()["value"] == 2
