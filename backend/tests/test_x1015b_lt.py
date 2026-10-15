"""X-1015b — LT (kesish uzunligi) va CT (kesimlar soni) qoidasi onlayn tizim bilan bir xil
(docs/mebelix/X_1015_ONLAYN_AUDIT_MCP.md §12).

Onlayn «Таблица команд» (5000 kupe, CS1: list 2750×1830, propil 3, torsovka 2/2) dan 5 karta geometriyasi mustaqil qayta
quriladi (faqat jadval qatorlari: T/C/P, daraja, o'lcham, soni, detal ID) va `_build_map` bergan LT onlayn qiymatlar bilan
solishtiriladi: 26.85 / 22.79 / 24.1 / 20.42 / 19.13 m (jami 113.3 m).

Qoida: jadvalning har qatori (T, C, P; K marta) — bitta arra yurishi, uzunligi — kesilayotgan bo'lakning ko'ndalang o'lchami:
1-daraja (T1, C1) — list tomoni to'liq (list burilgan «R» bo'lsa 2750, aks holda 1830); 2-daraja (T2, C2, P2) — polosa eni
(C1 o'lchami); 3-daraja — bo'lak o'lchami (C2 o'lchami) va h.k. Propil qo'shilmaydi, K marta sanaladi, har darajada oxirgi
kesim ham sanaladi (onlayn geometriyada har stack oxirida ≥ «отступ в конце» qoldiq bor). Eski qoidamiz chuqur (≥ 3-daraja)
tugunda chegaraga tegib turgan oxirgi bo'lakni sanamas edi — shu tuzatildi (bizning 5000 kupe 5-kartasi: 15.67 → 17.618 m).
"""
from app.models import CSCutParams, CSMaterialParams, StockSheet
from app.services.optimizer import EPS, Item, _N, _Sheet, _build_map, _other, _zone, optimize

SHEET = StockSheet(id="s", length=2750, width=1830)
CUT = CSCutParams(kerf=3, trim_length=2, trim_width=2)
MAT = CSMaterialParams()

# Onlayn jadvallar: (LT onlayn, R — list burilgan [1-daraja kesimlar 2750 tomoni bo'ylab], qatorlar «Кд|Р|K|Д»)
ONLINE = [
    (26.85, True, "T1|2|| ; C1|1711|1| ; T2|2|| ; C2|1950|1| ; P3|600|1|2 ; P3|600|1|4 ; C3|500|1| ; P4|951|1|1 ; P4|951|1|31 ; "
                  "C2|668|1| ; P3|450|3|17 ; P3|100|2|10 ; C3|101|1| ; P4|410|1|27 ; C2|101|1| ; P3|1430|1|22 ; C1|100|1| ; T2|2|| ; "
                  "P2|409|1|24 ; P2|2000|1|32 ; C2|101|1| ; P3|84|1|34 ; C2|100|1| ; P3|84|1|30"),
    (22.79, False, "T1|2|| ; C1|1270|1| ; T2|2|| ; C2|584|1| ; P3|884|1|8 ; P3|378|1|6 ; C2|584|1| ; P3|884|1|9 ; P3|378|1|6 ; "
                   "C2|584|1| ; P3|883|1|5 ; P3|378|1|6 ; C1|883|1| ; T2|2|| ; P2|584|1|5 ; P2|584|2|7 ; C1|409|1| ; T2|2|| ; "
                   "P2|882|1|21 ; P2|881|1|20 ; C1|100|1| ; T2|2|| ; P2|974|1|25 ; P2|800|1|29"),
    (24.10, True, "T1|2|| ; C1|1108|1| ; T2|2|| ; C2|1984|1| ; P3|500|1|11 ; C3|600|1| ; P4|1968|1|3 ; C2|700|1| ; P3|500|1|13 ; "
                  "C3|450|1| ; P4|668|1|17 ; C1|600|1| ; T2|2|| ; P2|1968|1|16 ; C2|378|2| ; P3|584|1|6 ; C1|102|1| ; T2|2|| ; "
                  "P2|2000|1|28"),
    (20.42, True, "T1|2|| ; C1|1303|1| ; T2|2|| ; C2|2000|1| ; P3|347|1|18 ; C3|948|1| ; P4|1948|1|33 ; C2|409|1| ; P3|881|1|20 ; "
                  "C2|100|1| ; P3|1076|1|26 ; C1|500|1| ; T2|2|| ; P2|1984|1|12 ; P2|334|1|15"),
    (19.13, False, "T1|2|| ; C1|2000|1| ; T2|2|| ; P2|347|1|19 ; C2|948|1| ; P3|1948|1|33 ; C2|500|1| ; P3|1968|1|14 ; C1|487|1| ; "
                   "T2|2|| ; C2|1420|1| ; P3|101|1|23 ; C3|378|1| ; P4|584|1|6"),
]


def _nest(text):
    """Jadval qatorlari → ichma-ich tuzilma [code, level, size, k, det, children]; C qatorining bolalari — keyingi
    chuqurroq qatorlar (daraja ≤ C darajasi bo'lgan qatorgacha)."""
    root = ["S", 0, None, 1, "", []]
    stack = [root]
    for cell in text.split(";"):
        cmd, size, k, det = [c.strip() for c in cell.strip().split("|")]
        node = [cmd[0], int(cmd[1:]), float(size), int(k) if k else 1, det, []]
        while stack[-1][1] >= node[1]:
            stack.pop()
        assert stack[-1][1] == node[1] - 1, cell
        stack[-1][5].append(node)
        if node[0] == "C":
            stack.append(node)
    return root


def _flat(node):
    """Kutilgan buyruqlar (K ochilgan): [(code, level, size, det)]; C qatori K>1 — bir xil bo'laklar, har biriga ichki daraxt."""
    out = []
    for code, lvl, size, k, det, kids in node[5]:
        for _ in range(k if code == "C" else 1):
            out += [(code, lvl, size, det)] * (k if code == "P" else 1)
            out += _flat([code, lvl, size, k, det, kids])
    return out


def _tree(nested, rotated, z, kerf):
    """Onlayn jadval → bizning kesish daraxti (zona koordinatalarida). Burilgan list: polosalar Y bo'ylab (ildiz o'qi y,
    1-daraja kesimlar 2750 tomoni bo'ylab), aks holda X bo'ylab. Har stack oxirida qolgan joy — W (chiqindi)."""
    def build(parent, node, axis, depth):
        pos = 0.0
        avail = parent.l if axis == "x" else parent.w
        for code, lvl, size, k, det, kids in node[5]:
            if code == "T":
                continue                                   # torsovka — zonada (ox/oy) hisobga olingan
            for _ in range(k if code == "C" else 1):
                for _r in range(k if code == "P" else 1):
                    if axis == "x":
                        x, y, l, w = parent.x + pos, parent.y, size, parent.w
                    else:
                        x, y, l, w = parent.x, parent.y + pos, parent.l, size
                    if code == "P":
                        leaf = _N(x, y, l, w, depth + 1, "P")
                        leaf.pid = (f"d{det}", int(det))
                        parent.children.append(leaf)
                    else:
                        c = _N(x, y, l, w, depth + 1, "C", axis=_other(axis))
                        parent.children.append(c)
                        build(c, [code, lvl, size, k, det, kids], _other(axis), depth + 1)
                    pos += size + kerf
        rest = avail - pos
        assert rest > -EPS, (node[:5], rest)              # qayta qurilgan geometriya sig'adi (oxirgi kesimdan keyin ham)
        if rest > EPS:
            parent.children.append(_N(parent.x + pos, parent.y, rest, parent.w, depth + 1, "W") if axis == "x"
                                   else _N(parent.x, parent.y + pos, parent.l, rest, depth + 1, "W"))

    axis1 = "y" if rotated else "x"
    root = _N(0.0, 0.0, z.UL, z.UW, 0, "C", axis=axis1)
    build(root, nested, axis1, 0)
    return root


def _rows(m):
    """Bizning jadval, K ochilgan (W qatorlari — qoldiq raqamlari — solishtirilmaydi)."""
    return [(c.code, c.level, c.size, c.ref) for c in m.commands if c.code != "W" for _ in range(c.count)]


def _lt_from_rows(m):
    """Qoida jadval orqali: LT = Σ K × cross(daraja); cross[1] — list tomoni (ildiz o'qi bo'yicha), har C qatori keyingi
    darajaga o'z o'lchamini beradi. LT jadvalning sof funksiyasi bo'lishi kerak."""
    cross = {1: m.sheet_width if m.strips[0]["a"] == "x" else m.sheet_length}
    total = 0.0
    for c in m.commands:
        if c.code == "W":
            continue
        total += cross[c.level] * c.count
        if c.code == "C":
            cross[c.level + 1] = c.size
    return round(total / 1000, 3)


def _map(root, idx=1):
    z = _zone(SHEET, CUT)
    return _build_map(_Sheet(z, root, 0.0, []), idx, CUT, MAT, [0], {})


def test_online_five_maps_lt_reproduced_exactly():
    z = _zone(SHEET, CUT)
    total = 0.0
    for i, (lt, rotated, text) in enumerate(ONLINE, 1):
        nested = _nest(text)
        m = _map(_tree(nested, rotated, z, CUT.kerf), i)
        assert abs(m.cut_length_m - lt) <= 0.0051, (i, m.cut_length_m, lt)       # 26.855 → onlayn 26.85
        expect = _flat(nested)
        assert _rows(m) == expect, i                                           # jadval ham qatorma-qator bir xil
        assert m.cuts_count == len(expect)                                     # CT = qatorlar soni (K bilan)
        assert m.cut_length_m == _lt_from_rows(m)
        assert m.parts_count == sum(1 for r in expect if r[0] == "P")
        total += m.cut_length_m
    assert abs(total - 113.3) <= 0.01                                          # 26.855+22.793+24.102+20.419+19.130


def test_level1_cut_length_is_full_sheet_side_and_t2_is_strip_width():
    # 2-karta (R yo'q): T1 + 4×C1 = 5 × 1830; har polosada T2 = polosa eni (1270, 883, 409, 100)
    z = _zone(SHEET, CUT)
    lt, rotated, text = ONLINE[1]
    m = _map(_tree(_nest(text), rotated, z, CUT.kerf))
    t1 = [c for c in m.commands if c.code == "T" and c.level == 1]
    t2 = [c for c in m.commands if c.code == "T" and c.level == 2]
    assert len(t1) == 1 and len(t2) == 4
    by_level = {}
    cross = {1: 1830.0}
    for c in m.commands:
        if c.code != "W":
            by_level[c.level] = by_level.get(c.level, 0.0) + cross[c.level] * c.count
            if c.code == "C":
                cross[c.level + 1] = c.size
    assert by_level[1] == 5 * 1830 and by_level[2] == 4 * 1270 + 4 * 883 + 3 * 409 + 3 * 100
    assert by_level[3] == 6 * 584 and round(sum(by_level.values()) / 1000, 3) == 22.793


# Bizning 5000 kupe 5-kartasi (list koordinatalarida): 1948×1451 bo'lak ichida oxirgi C3 500 bo'lagi chegaraga tegib turibdi
# (W yo'q) — eski qoida uni sanamas edi (15.67 m), onlayn qoida bo'yicha 17.618 m.
MX_MAP5 = ("C", 5, 5, 2740, 1820, "y", [
    ("C", 5, 5, 2740, 1451, "x", [
        ("C", 5, 5, 1948, 1451, "y", [
            ("P", 5, 5, 1948, 948, 33),
            ("C", 5, 956, 1948, 500, "x", [("P", 5, 956, 951, 500, 1), ("P", 959, 956, 951, 500, 31), ("W", 1913, 956, 40, 500)]),
        ]),
        ("C", 1956, 5, 409, 1451, "y", [
            ("P", 1956, 5, 409, 881, 20),
            ("C", 1956, 889, 409, 500, "x", [("P", 1956, 889, 334, 500, 15), ("W", 2293, 889, 72, 500)]),
            ("W", 1956, 1392, 409, 64)]),
        ("C", 2368, 5, 100, 1451, "y", [("P", 2368, 5, 100, 1076, 26), ("W", 2368, 1084, 100, 372)]),
        ("W", 2471, 5, 274, 1451)]),
    ("W", 5, 1459, 2740, 366)])


def _from_dsl(d, ox, oy, depth=0):
    kind, x, y, l, w = d[0], d[1] - ox, d[2] - oy, d[3], d[4]
    if kind == "C":
        n = _N(x, y, l, w, depth, "C", axis=d[5], children=[_from_dsl(c, ox, oy, depth + 1) for c in d[6]])
    elif kind == "P":
        n = _N(x, y, l, w, depth, "P")
        n.pid = (f"d{d[5]}", d[5])
    else:
        n = _N(x, y, l, w, depth, "W")
    return n


def test_flush_last_piece_in_deep_node_is_counted():
    z = _zone(SHEET, CUT)
    m = _map(_from_dsl(MX_MAP5, z.ox, z.oy))
    # T1 2750 + C1 2750 | polosa 1451: T2 + C2×3 = 4×1451 | 1948-bo'lak: P3 948 + C3 500 = 2×1948 (ikkalasi ham!) | 500-bo'lak: 2×500
    # | 409-bo'lak: P3 881 + C3 500 = 2×409; 334: 500 | 100-bo'lak: 100
    assert m.cut_length_m == 17.618 and m.cuts_count == 14
    assert m.cut_length_m == _lt_from_rows(m)
    assert [(c.code, c.level, c.size) for c in m.commands if c.level >= 3][:2] == [("P", 3, 948.0), ("C", 3, 500.0)]


def test_waste_between_parts_needs_its_own_cut():
    # polosa (400 eni) ichida P 300 | W 100 | P 500: chiqindini keyingi detaldan ajratadigan kesim sanaladi (onlayn «W — рез отхода»)
    z = _zone(SHEET, CUT)
    strip = _N(0, 0, 400, z.UW, 1, "C", axis="y")
    a = _N(0, 0, 400, 300, 2, "P"); a.pid = ("a", 1)
    b = _N(0, 406, 400, 500, 2, "P"); b.pid = ("b", 2)
    strip.children = [a, _N(0, 303, 400, 100, 2, "W"), b, _N(0, 909, 400, z.UW - 909, 2, "W")]
    root = _N(0, 0, z.UL, z.UW, 0, "C", axis="x", children=[strip, _N(403, 0, z.UL - 403, z.UW, 1, "W")])
    m = _map(root)
    # T1 1830 + C1 1830 + T2 400 + P 400 + W 400 + P 400
    assert m.cuts_count == 6 and m.cut_length_m == 5.26


def test_optimizer_output_lt_is_pure_function_of_command_table():
    items = [Item("a", 1, 1968, 600, True), Item("b", 2, 1968, 600, True), Item("c", 3, 1968, 500, True),
             Item("d", 4, 951, 500, True), Item("e", 5, 951, 500, True), Item("f", 6, 1948, 948, True),
             Item("g", 7, 409, 881, True), Item("h", 8, 334, 500, True), Item("i", 9, 100, 1076, True),
             Item("j", 10, 668, 450, True), Item("k", 11, 668, 450, True), Item("l", 12, 2000, 102, True)]
    cut = CSCutParams(kerf=3, trim_length=2, trim_width=2, quality="fast")
    res = optimize(items, [SHEET], cut, MAT)
    assert res.maps and not res.unplaced
    for m in res.maps:
        assert m.cut_length_m == _lt_from_rows(m)
        assert m.cuts_count == sum(c.count for c in m.commands if c.code != "W")
    assert res.total_cut_length_m == round(sum(m.cut_length_m * m.copies for m in res.maps), 3)
