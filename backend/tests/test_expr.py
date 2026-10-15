"""Umumiy ifoda dvigateli (services/expr.py): GibLab yordamidagi misollar (funksional tavsifga mos), xavfsizlik, chegaralar."""
import datetime as dt
import math
import random

import pytest

from app.services import expr as E

ENV = {"dx": 480.0, "dy": 800.0, "project.name": "1234 Shkaf", "part.id": 7, "part.counter": 3, "flag": True}


def ev(src, **kw):
    return E.evaluate(src, ENV, **kw)


@pytest.mark.parametrize("src,val", [
    # taqqoslash va mantiq
    ("1>2", False), ("1!=2", True), ("1<>2", True), ("1-3+2==0", True), ("1=1", True), ("2=1", False),
    ("if(1!=2,1,2)", 1), ("if(true,'Да','Нет')", "Да"), ("if (1>2, 10, 20)", 20),
    ("not 1>2", True), ("true and false", False), ("true or false", True), ("true xor true", False), ("true xor false", True),
    ("false xor false", False), ("1<2 xor 3<2", True), ("not true or true", True),
    # matn bilan +
    ("'abc'+'XXX'", "abcXXX"), ("'abc'+1", "abc1"), ("'abc'+1+2", "abc12"), ("'abc'+(1+2)", "abc3"),
    ("'result:'+(1=2)", "result:false"), ("'a\\tb'", "a\tb"), ("'\\u00A9'", "©"), ('"x"+\'y\'', "xy"),
    # arifmetika: butun / haqiqiy
    ("7/2", 3), ("-7/2", -3), ("7.0/2", 3.5), ("7%3", 1), ("-7%3", -1), ("7%-3", 1), ("2^3", 8.0), ("2^3^2", 512.0), ("-2^2", -4.0),
    ("2^-1", 0.5), ("1+2*3", 7), ("(1+2)*3", 9), ("10-2-3", 5), ("1,5*2", 3.0), ("max(1,5,3)", 5), ("min(1,5)", 1),
    ("1 if dx>500 else 2", 2), ("dx/2", 240.0), ("(dx>100)*10", 10),
    # matematika (radian)
    ("abs(-1.22)", 1.22), ("abs(-777)", 777), ("ceil(1.5)", 2.0), ("floor(-1.5)", -2.0), ("floor(1.5)", 1.0),
    ("round(-1.5)", -1), ("round(2.2)", 2), ("round(2.5)", 3), ("round(2.567,2)", 2.57), ("max(1,-3.0)", 1.0), ("min(9,3)", 3),
    ("sqrt(4)", 2.0), ("cos(pi)", -1.0), ("acos(-1)", math.pi), ("ln(2)", math.log(2)), ("logx(9,3)", 2.0), ("log(100)", 2.0),
    ("log2(8)", 3.0), ("sin(1.5)", math.sin(1.5)), ("cos(1.5)", 0.0707372016677029), ("sec(pi)", -1.0), ("exp(0)", 1.0),
    ("sign(-1.5)", -1.0), ("sign(2)", 1.0), ("atan(-1)", -math.pi / 4), ("acot(1)", math.pi / 4), ("e", math.e),
    ("sinh(0)", 0.0), ("tanh(0)", 0.0), ("cosh(0)", 1.0),
    # matn funksiyalari
    ("len('abc')", 3), ("len('')", 0), ("mid('abc',1,2)", "ab"), ("mid('abc',3,1)", "c"), ("left('abc',2)", "ab"),
    ("right('abc',2)", "bc"), ("lspace('abc',5,'X')", "abcXX"), ("rspace('abc',5,'X')", "XXabc"), ("rept(123,2)", "123123"),
    ("rept('abc',2)", "abcabc"), ("ns(null)", ""), ("ns('abc')", "abc"), ("empty(null)", True), ("empty('')", True),
    ("empty('abc')", False), ("trim(' abc ')", "abc"), ("ltrim(' abc ')", "abc "), ("rtrim(' abc ')", " abc"),
    ("ucase('Abc')", "ABC"), ("lcase('Abc')", "abc"), ("find('abcd','bc',1)", 2), ("find(1234,23,1)", 2), ("find('abc','z')", 0),
    ("findr('abcdbc','bc',6)", 5), ("findr(1234123,2,7)", 6), ("replace('abc','b','xxxx')", "axxxxc"), ("replace('1231','1','9')", "9239"),
    ("startswith('abc','ab')", True), ("startswith('abc','bc')", False), ("startswith(1234123,12)", True),
    ("endswith('abc','ab')", False), ("endswith('abc','bc')", True), ("double('1.0')", 1.0), ("double(1)", 1.0),
    ("integer('1.0')", 1), ("integer(1.7)", 1), ("boolean('true')", True), ("boolean('True')", True), ("boolean('T')", True),
    ("boolean('1')", True), ("boolean('')", False), ("boolean('false')", False), ("boolean('f')", False),
    ("translit('Пример')", "Primer"), ("crc16('test')", 63534), ("crc32('test')", -662733300),
    # sonli o'zgartirishlar
    ("DecToHex(255)", "ff"), ("HexToDec('ff')", 255), ("DecToOct(255)", "377"), ("OctToDec('377')", 255),
    ("DecToBin(255)", "11111111"), ("BinToDec('11111111')", 255), ("roman(111)", "CXI"), ("roman(3999)", "MMMCMXCIX"),
    # format
    ("format('0.000',23.2)", "23.200"), ("format('0000',1)", "0001"), ("format('%',0.32)", "%32"), ("format('#.##',2.5)", "2.5"),
    ("format('#,##0.00',1234567.891)", "1,234,567.89"), ("format('0.0%',0.256)", "25.6%"), ("format('0.00;(0.00)',-3.5)", "(3.50)"),
    ("format('0.#',2)", "2"), ("format('00.0',-1.25)", "-01.2"), ("format('0',2.5)", "2"), ("format('0',3.5)", "4"),
    ("calculate('1+2')", 3), ("calculate('dx*2')", 960.0),
    # o'zgaruvchilar
    ("dx+dy", 1280.0), ("project.name", "1234 Shkaf"), ("flag and dx>100", True),
    # shtrixkod misoli
    ("left(trim(project.name)+' ', find(trim(project.name)+' ',' ',1)-1) + rspace(right(part.id,4),4,'0') + "
     "rspace(right(part.counter,4),4,'0')", "123400070003"),
])
def test_examples(src, val):
    r = ev(src)
    if isinstance(val, float):
        assert isinstance(r, float) and r == pytest.approx(val, abs=1e-12), src
    else:
        assert r == val and type(r) is type(val), (src, r)


def test_type_rules():
    assert isinstance(ev("1+2"), int) and isinstance(ev("1+2.0"), float)
    assert ev("7/2") == 3 and ev("7.0/2") == 3.5 and ev("dx/7") == pytest.approx(480 / 7)
    assert E.to_text(2.0) == "2.0" and E.to_text(2) == "2" and E.to_text(True) == "true" and E.to_text(None) == ""
    assert E.to_text(1.2246467991473532e-16) == "1.2246467991473532E-16"
    assert E.to_text(1e7) == "1.0E7" and E.to_text(0.001) == "0.001" and E.to_text(0.0001) == "1.0E-4"
    assert ev("'x'+1.5") == "x1.5" and ev("'x'+2.0") == "x2.0"
    assert ev("3000000000") == 3000000000.0 and isinstance(ev("3000000000"), float)        # 32 bitdan katta — haqiqiy


def test_degrees_mode():
    assert E.evaluate("sin(90)", {}, degrees=True) == pytest.approx(1.0)
    assert E.evaluate("tan(45)", {}, degrees=True) == pytest.approx(1.0)
    assert E.evaluate("acos(0)", {}, degrees=True) == pytest.approx(90.0)
    assert E.evaluate("sin(90)", {}) == pytest.approx(math.sin(90))


def test_if_is_lazy():
    assert ev("if(true, 1, 1/0)") == 1
    assert ev("if(false, 1/0, 2)") == 2
    with pytest.raises(ValueError):
        ev("if(true, 1/0, 2)")
    assert ev("true or 1/0") is True and ev("false and 1/0") is False


def test_eval_number_wrapper():
    assert E.eval_number("dx>100", ENV) == 1.0 and E.eval_number("not dx", ENV) == 0.0
    assert E.eval_number("7/2", ENV) == 3.0
    for bad in ("'a'", "null", "'1'+'2'"):
        with pytest.raises(ValueError):
            E.eval_number(bad, ENV)


@pytest.mark.parametrize("src", [
    "1/0", "1.0/0", "5%0", "abc", "__import__('os')", "dx.real", "lambda: 1", "[1,2]", "min()", "sqrt(-1)", "9**9**9", "dx +",
    "round(1,2,3)", "log(0)", "ln(-1)", "acos(2)", "roman(0)", "roman(4000)", "mid('abc')", "unknownfn(1)", "if(1,2)", "'abc", "1 2",
    "(1+2", "1+2)", "format('0.0')", "ucase(null, 1)", "1e400+1", "rept('a', 100000)", "now('q')", "HexToDec('zz')", "dx" * 400,
    "'a'-1", "not", "null+1", "2^100", "true+'a'*2",
])
def test_bad_expressions_raise(src):
    with pytest.raises(ValueError):
        ev(src)


def test_limits():
    deep = "(" * 200 + "1" + ")" * 200
    with pytest.raises(ValueError):
        ev(deep)
    with pytest.raises(ValueError):
        ev("-" * 500 + "1")
    long_sum = "+".join(["1"] * 600)                     # 1199 belgi > 1000
    with pytest.raises(ValueError):
        ev(long_sum)
    ok = "+".join(["1"] * 250)                           # chuqurlik va tugunlar soni chegarasi ichida
    assert ev(ok) == 250
    with pytest.raises(ValueError):                      # juda uzun zanjir — «juda murakkab»
        ev("+".join(["1"] * 450))
    with pytest.raises(ValueError):                      # calculate rekursiyasi chegaralangan
        E.evaluate("calculate('calculate(\"calculate(\\'calculate(\\\\\\'1\\\\\\')\\')\")')", {})
    assert len(ev("rept('ab', 5000)")) == 10000
    with pytest.raises(ValueError):
        ev("rept('ab', 5001)")


def test_now_and_random_are_injectable():
    fixed = lambda: dt.datetime(2016, 6, 26, 19, 28, 35, 109000)
    assert E.evaluate("now('yyyy.MM.dd')", {}, clock=fixed) == "2016.06.26"
    assert E.evaluate("now('HH:mm:ss')", {}, clock=fixed) == "19:28:35"
    assert E.evaluate("now('d MMMM yyyy, EEEE')", {}, clock=fixed) == "26 Июнь 2016, воскресенье"
    assert E.evaluate("now('dd.MM.yy HH:mm:ss.SSS')", {}, clock=fixed) == "26.06.16 19:28:35.109"
    assert E.evaluate("now('hh:mm a')", {}, clock=fixed) == "07:28 PM"
    assert E.evaluate("now('d MMM EEE')", {}, clock=fixed, lang="uz") == "26 iyn Ya"
    assert E.evaluate("now(\"'t'yyyy\")", {}, clock=fixed) == "t2016"          # naqshdagi 't' — qo'shtirnoqli matn
    assert E.evaluate("now(\"''yyyy\")", {}, clock=fixed) == "'2016"
    r1 = E.evaluate("random()", {}, rng=random.Random(5))
    assert 0 <= r1 < 1 and r1 == E.evaluate("random()", {}, rng=random.Random(5))
    u = E.evaluate("UUID()", {})
    assert len(u) == 36 and u.count("-") == 4


def test_compile_check_and_names():
    E.compile_check("if(a>1, 'x', 'y')")
    with pytest.raises(ValueError):
        E.compile_check("1 +")
    names = E.function_names()
    for must in ("if", "format", "now", "crc16", "roman", "sin", "mid", "translit", "calculate", "uuid"):
        assert must in names
    listed = {n for grp in E.FUNCTION_GROUPS.values() for n, _sig in grp}
    assert listed == set(names)


def test_no_python_escape_hatches():
    for src in ("().__class__", "dx.__class__", "'a'.upper()", "[x for x in dx]", "(lambda: 1)()", "1 if 1 else", "import os"):
        with pytest.raises(ValueError):
            ev(src)
