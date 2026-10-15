"""W4 · LB: Code128 (noldan yozilgan) va QR SVG — jadval to'g'riligi, kodlash, nazorat yig'indisi, teskari dekodlash."""
import random
import re

import pytest

from app.services import barcode


def test_code128_table_is_valid():
    """Jadval qo'lda yozilgan — tuzilish qoidalari bilan tekshiriladi: 107 ta noyob belgi, har biri 11 modul (to'xtash — 13),
    3 bar + 3 bo'shliq, barlar jami eni juft (Code128 «parity» qoidasi)."""
    pats = barcode.PATTERNS
    assert len(pats) == 107 and len(set(pats)) == 107
    for i, p in enumerate(pats):
        assert sum(p) == (13 if i == barcode.STOP else 11), (i, p)
        assert len(p) == (7 if i == barcode.STOP else 6)
        assert sum(p[0::2]) % 2 == 0, (i, p)
    # ma'lum belgilar: bo'sh joy (0) — 11011001100, B boshlanishi — 11010010000, C boshlanishi — 11010011100, to'xtash — 1100011101011
    def bits(p):
        s, bar = "", True
        for w in p:
            s += ("1" if bar else "0") * w
            bar = not bar
        return s
    assert bits(pats[0]) == "11011001100"
    assert bits(pats[barcode.START_B]) == "11010010000"
    assert bits(pats[barcode.START_C]) == "11010011100"
    assert bits(pats[barcode.STOP]) == "1100011101011"


def test_code128_known_vectors():
    assert barcode.code128_codes("A") == [104, 33, 34]                       # (104 + 33) % 103
    assert barcode.code128_codes("Hello") == [104, 40, 69, 76, 76, 79, 76]   # nazorat 1209 % 103 = 76
    assert barcode.code128_codes("1234") == [105, 12, 34, 82]                # C to'plami: (105 + 12 + 2·34) % 103
    # toq raqamlar: birinchi raqam B da, so'ng C ga o'tish
    assert barcode.code128_codes("12345") == [104, 17, 99, 23, 45, (104 + 17 + 99 * 2 + 23 * 3 + 45 * 4) % 103]


def test_code128_roundtrip_many():
    rnd = random.Random(7)
    samples = ["0", "00", "123", "1234", "12345", "123456", "AB1234", "AB1234CD", "AB123456CD", "x" * 80, " ", "~", "a b-c_d/e",
               "MXK:1000123:7:2/4", "1000123000700001", "98765432109876543210"]
    for _ in range(300):
        n = rnd.randint(1, 40)
        alphabet = rnd.choice(["0123456789", "0123456789ab", "ABC xyz-:/.", "0123456789" * 3 + "Q"])
        samples.append("".join(rnd.choice(alphabet) for _ in range(n)))
    for s in samples:
        assert barcode.decode_widths(barcode.code128_widths(s)) == s, s


def test_code128_numeric_is_compact():
    """Faqat raqam — C to'plami (juft raqamlar 1 belgi): 16 raqam = 11 + 8·11 + 11 + 13 modul."""
    assert barcode.code128_total_modules("1000123000700001") == 11 + 8 * 11 + 11 + 13
    assert barcode.code128_total_modules("ABCDEFGH") == 11 + 8 * 11 + 11 + 13      # B: bir xil uzunlikdagi matn


@pytest.mark.parametrize("bad", ["", "kirill: яблоко", "tab\tx", "x" * 201, "é"])
def test_code128_rejects_unsupported(bad):
    with pytest.raises(ValueError):
        barcode.code128_codes(bad)


def test_code128_svg_group_is_pure_svg():
    g, mw = barcode.code128_group("1000123000700001", 2, 3, 50, 10, caption=True)
    assert g.startswith("<g ") and g.endswith("</g>")
    assert "<script" not in g and "href" not in g and "on" + "load" not in g
    assert 0.3 < mw < 0.45                                                   # 50 mm / (123 + 20) modul
    assert ">1000123000700001</text>" in g                                   # matn takrori (caption)
    g2, _ = barcode.code128_group("<b>&", 0, 0, 30, 8, caption=True)         # matn escape qilinadi
    assert "&lt;b&gt;&amp;" in g2 and "<b>" not in g2
    # chiziqlar yig'indisi: path dagi bar kengliklari jadvaldagi bar kengliklariga teng
    widths = barcode.code128_widths("1000123000700001")
    d = re.search(r' d="([^"]+)"', g).group(1)
    got = [int(m) for m in re.findall(r"h(\d+)v", d)]
    assert got == widths[0::2]


def test_qr_path_matches_segno_matrix():
    import segno
    data = "MXK:1000123:7:2/4"
    n, d = barcode.qr_cells(data, "m", False)
    q = segno.make(data, error="m", micro=False)
    rows = [list(r) for r in q.matrix]
    assert n == len(rows)
    grid = [[0] * n for _ in range(n)]
    for x, y, w in re.findall(r"M(\d+) (\d+)h(\d+)v1h-\d+z", d):
        for i in range(int(x), int(x) + int(w)):
            grid[int(y)][i] = 1
    assert grid == [[1 if c else 0 for c in r] for r in rows]


def test_qr_fast_mask_is_valid_and_much_faster():
    import time
    data = [f"MXK:1000123:{i}:1/2" for i in range(300)]
    t = time.perf_counter()
    for s in data:
        barcode.qr_cells(s + "x", "m", True)
    fast = time.perf_counter() - t
    t = time.perf_counter()
    for s in data:
        barcode.qr_cells(s + "y", "m", False)
    slow = time.perf_counter() - t
    assert fast < slow
    n1, _ = barcode.qr_cells("MXK:1:2:3/4", "m", True)
    n2, _ = barcode.qr_cells("MXK:1:2:3/4", "m", False)
    assert n1 == n2 == 21


def test_qr_group_and_limits():
    g = barcode.qr_group("MXK:1:2:3/4", 1, 2, 15)
    assert g.startswith("<g ") and "scale(" in g and "<script" not in g
    with pytest.raises(ValueError):
        barcode.qr_cells("")
    with pytest.raises(ValueError):
        barcode.qr_cells("x" * 1001)
