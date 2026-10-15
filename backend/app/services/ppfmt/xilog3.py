"""SCM Xilog v3 — `.pgm` ikkilik konteyner (`Xilog3-7.0`) + Xilog matn qatorlari (docs/mebelix/postprocessors/scm-xilog-v3.md).

Bitta XNC operatsiyasi = bitta `<XNC kodi>.pgm`. Konteyner: 0x109 baytlik doimiy prefiks (1×1 BMP eskiz, versiya, ofsetlar
jadvali, DZ/FLD/DX/DY o'zgaruvchilar jadvali), tokenlangan `H` bloki, keyin har qator alohida yozuv (`02 37 10` + uzunlik +
`S` + matn + NUL), oxirida `02 37 10`. Sonlar 2 xonagacha. Koordinatalar XNC dagidek (yuz tomon); orqa tomon — X ag'darilgan.
"""
from __future__ import annotations

import struct

from . import DrillJob, Files, register
from . import _cnc as C

ENC = "cp1251"
F_OF = {"F": 1, "R": 2, "L": 3, "B": 4, "T": 5}
ARROW_FACE = {"top": "V", "bottom": "^", "left": ">", "right": "<"}
ARROW_BACK = {"top": "V", "bottom": "^", "left": "<", "right": ">"}


from . import tooling as TL          # freza / paz arrasi raqami — «Инструменты» jadvalidan (bo'sh bo'lsa -1)

def fmt(v: float) -> str:
    """2 xonagacha yaxlitlab, oxirgi nollarsiz (298.2989 → 298.3, 568.00 → 568)."""
    v = round(float(v) + 0.0, 2)
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _bmp() -> bytes:
    """1×1 piksel, 1 bit, oq — eskiz o'rni (0x42 bayt)."""
    dib = struct.pack("<IiiHHIIiiII", 40, 1, 1, 1, 1, 0, 4, 3790, 3780, 0, 0)
    pal = b"\x00\x00\x00\x00\xff\xff\xff\x00"
    return b"BM" + struct.pack("<IHHI", 0x42, 0, 0, 0x3E) + dib + pal + b"\x00\x00\x00\x00"


def _var(name: str, typ: int, idx: int) -> bytes:
    nb = name.encode("ascii")
    return b"\x00\x00\x00\x10" + bytes([typ]) + bytes(16) + b"\x07a" + bytes([len(nb)]) + nb + b"V" + bytes([idx]) + b"\x00i\x00\x00"


def _prefix() -> bytes:
    head = (_bmp() + b"Xilog3-7.0 \x00" + struct.pack("<III", 5, 2, 1) + b"\x00\x00"
            + struct.pack("<IIIIIIIIIII", 4, 0, 0x42, 0x42, 0x46, 0x88, 0, 4, 0, 0, 0))
    vt = _var("DZ", 0x20, 0x62) + _var("FLD", 0x21, 0x63) + _var("DX", 0x20, 0x60) + _var("DY", 0x20, 0x61)
    out = head + vt
    assert len(out) == 0x109
    return out


PREFIX = _prefix()


def container(dx: float, dy: float, dz: float, r: int, comment: str, htext: str, recs: list[str]) -> bytes:
    com = comment.encode(ENC, errors="replace")[:255]
    ht = htext.encode(ENC, errors="replace")
    m = 81 + len(com)
    ln = m + 3 + len(ht)
    h = (b"\x01\x03\x01\x00" + struct.pack("<HH", ln, m) + bytes(12) + b"\x7f\xff"
         + b"".join(b"Q" + struct.pack("<f", v) for v in (dx, dy, dz))
         + b"iAB" + b"i\x00\x00" + b"l\x00\x00\x00\x00" + b"i" + struct.pack("<h", max(-32768, min(32767, int(r))))
         + b"i\x02\x00" + b"a\x03def" + b"i\x00\x00" + b"i\x01\x00" + b"i\x00\x00" * 3 + b"Q" + struct.pack("<f", 0.0)
         + b";" + bytes([len(com)]) + com + b"S" + struct.pack("<H", len(ht)) + ht + b"\x00")
    body = b""
    for t in recs:
        tb = t.encode(ENC, errors="replace")
        body += b"\x02\x37\x10" + struct.pack("<HHBH", 11 + len(tb), 8, 0x53, len(tb)) + tb + b"\x00"
    body += b"\x02\x37\x10"
    out = bytearray(PREFIX + h + body)
    sz = len(out)
    out[0x74:0x78] = struct.pack("<I", sz - 0x8A)
    out[0x80:0x84] = struct.pack("<I", sz)
    return bytes(out)


def read_records(data: bytes) -> tuple[str, list[str]]:
    """`.pgm` → (H qatori, buyruq qatorlari) — tekshiruv / testlar uchun."""
    p = 0x109
    ln, m = struct.unpack("<HH", data[p + 4:p + 8])
    tl = struct.unpack("<H", data[p + m + 1:p + m + 3])[0]
    htext = data[p + m + 3:p + m + 3 + tl].decode(ENC, errors="replace")
    q = p + ln + 1
    recs = []
    while q + 3 < len(data) and data[q:q + 3] == b"\x02\x37\x10":
        rl, _a, _s, tl = struct.unpack("<HHBH", data[q + 3:q + 10])
        recs.append(data[q + 10:q + 10 + tl].decode(ENC, errors="replace"))
        q += rl
    return htext, recs


def comment(job: DrillJob) -> str:
    arrows = ARROW_FACE if job.face else ARROW_BACK
    s = ""
    for side, e in C.edges(job):
        s += f"{arrows[side]}:({e['symbol']}) {fmt(e['thickness'])}mm  "
    return s + C.one_line(job.name)


def lines(job: DrillJob) -> list[str]:
    dz = job.dz
    out = []
    for o in C.machine_ops(job):
        t = o["t"]
        if t == "drill":
            f = F_OF[o["side"]]
            if f == 1:
                x, y = o["x"], o["y"]
            elif f in (2, 3):
                x, y = dz - o["z"], o["y"]
            else:
                x, y = o["x"], dz - o["z"]
            nn = "L" if f == 1 and o["dp"] >= dz else "P"
            out.append(f"XBO X={fmt(x)} Y={fmt(y)} Z={fmt(o['dp'])} D={fmt(o['d'])} N={nn} F={f}")
        elif t == "groove":
            out.append(f"XG0 X={fmt(o['x1'])} Y={fmt(o['y1'])} Z={fmt(o['dp'])} T={TL.tool_ref(job, 'saw', 'front', o['w'], '-1')} F=1 C={o['c']}")
            out.append(f"G1 X={fmt(o['x2'])} Y={fmt(o['y2'])}")
        elif t == "ms":
            out.append(f"XGIN Q=0 G=2 C={o['c']}")
            out.append(f"XG0 X={fmt(o['x'])} Y={fmt(o['y'])} Z={fmt(o['dp'])} T={TL.tool_ref(job, 'mill', 'front', o['d'], '-1')} F=1 C={o['c']}")
        elif t == "ml":
            out.append(f"XL2P X={fmt(o['x'])} Y={fmt(o['y'])}")
        elif t == "mac":
            out.append(f"{'G2' if o['ccw'] else 'G3'} X={fmt(o['x'])} Y={fmt(o['y'])} I={fmt(o['cx'])} J={fmt(o['cy'])}")
    out.append(";END")
    return out


def program(job: DrillJob) -> bytes:
    com = comment(job)
    r = getattr(job.op.xnc, "qty", 1) if job.op.xnc else 1
    htext = f'H DX={fmt(job.dx)} DY={fmt(job.dy)} DZ={fmt(job.dz)} -AB C=0 R={r} *MM /"def.tlg" ;{com}'
    return container(job.dx, job.dy, job.dz, r, com, htext, lines(job))


@register("xilog3", "SCM Xilog v3 (.pgm)", "cnc", "pgm",
          note="Ikkilik Xilog3-7.0 konteyner. Paz eni va asbob (T=-1) yozilmaydi; kirish XGIN Q=0 G=2 (namunada yagona). "
               "N=L — o'tuvchi yuz teshigi (DP ≥ qalinlik). Qirra teshigi balandligi dz − z. Orqa tomondagi qirra teshigi "
               "(F2↔F3) va freza (G2↔G3, C 1↔2) — namunada yo'q, faraz. Izohdagi kirill harflari cp1251 (tekshirilmagan).")
def xilog3(job: DrillJob) -> Files:
    return [(f"{job.code}.pgm", program(job))]
