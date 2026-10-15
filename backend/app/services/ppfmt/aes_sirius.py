"""AES Sirius (G-kod) — kengaytmasiz matn fayl (docs/mebelix/postprocessors/aes-sirius.md).

YAGONA namunadan (bitta detal: chap va o'ng qirrada bittadan teshik) o'rganilgan — faqat x=0 / x=dx qirra teshiklari
chiqadi. Tuzilishi: izoh-rasm (`{ … }`: uzunlik, en — ustun bo'ylab raqamlar), `R170` uzunlik, `R169` en, `R173` itargich
o'rni (uzunlik / 2), `L M7`, `M12`; har teshik: `M85`, `M87`, `M06T<n>`, `M16`, `G0 Z30.0`, `G0 X<tashqarida 20 mm> Y<y>`,
`M<n>`, `G0 Z-<z>`, `G1 X<chuqurlik> F2000`, qaytish; oxiri `M85`, `M88`, `L GFINPRO.ISC`, `M02`.
X o'ng qirradan (`dx − x`): avval o'ng qirra (XNC) teshiklari (stanokda X = 0 tomoni), keyin chap. Asbob raqami majburiy
(«Инструменты» jadvali). Yuz teshigi, y=0 / y=dy qirra teshigi, paz va freza — namunada yo'q: xato beriladi.
"""
from __future__ import annotations

from . import DrillJob, Files, register
from . import _cnc as C
from . import tooling as TL
from ._cnc2 import num

W = 28                                   # izoh-rasm ichki eni
OUT = 20.0                               # qirradan tashqaridagi yaqinlashish masofasi
SAFE_Z = 30.0
FEED = 2000
MIRROR_X = True                          # X = dx − x (namuna: simmetrik detal — bu yoki «asbob tekisligi almashgan», ochiq savol)
WHAT = {"F": "отверстие в пласть", "T": "отверстие в торец y=0", "B": "отверстие в торец y=dy"}


def n(v: float) -> str:
    return num(v, 3)


def f1(v: float) -> str:
    """Koordinata: kamida bitta kasr raqam (`30.0`, `120.5`)."""
    s = n(v)
    return s if "." in s else s + ".0"


def picture(dx: float, dy: float) -> list[str]:
    rows = ["{" + (" " * 11 + n(dx)).ljust(W) + "}"]
    for i, ch in enumerate(n(dy)):
        rows.append("{" + (" " * 5 + ("+" if i == 0 else "#") * 16 + "   " + ch).ljust(W) + "}")
    return rows + ["{" + "   O".ljust(W) + "}", "{" + " " * W + "}"]


def holes(job: DrillJob) -> list[tuple[bool, dict]]:
    """(stanokda X = 0 tomonimi, teshik) — avval X = 0 tomoni; bir tomonda dastur tartibida."""
    near, far = [], []
    for o in C.machine_ops(job):
        t = o["t"]
        if t == "drill" and o["side"] in ("L", "R"):
            at0 = (o["side"] == "R") if MIRROR_X else (o["side"] == "L")
            (near if at0 else far).append(o)
        elif t == "drill":
            raise ValueError(f"{WHAT[o['side']]} в формат AES Sirius не выводится — в образце только торцы x=0 / x=dx")
        elif t == "groove":
            raise ValueError("паз (Groove) в формат AES Sirius не выводится — нет образца")
        elif t == "ms":
            raise ValueError("фрезерование в формат AES Sirius не выводится — нет образца")
    return [(True, o) for o in near] + [(False, o) for o in far]


def program(job: DrillJob) -> str:
    dx, dy = job.dx, job.dy
    out = picture(dx, dy) + [f"(R170={n(dx)}) {{ LENGTH", f"(R169={n(dy)}) {{ WIDTH", f"(R173={n(dx / 2)}) {{ PUSHER POSITION",
                             "L M7", "M12"]
    for at0, o in holes(job):
        t = TL.need_tool(job, "drill", "left" if o["side"] == "L" else "right", o["d"])
        x0, x1 = (-OUT, o["dp"]) if at0 else (dx + OUT, dx - o["dp"])
        out += ["M85", "M87", f"M06T{t}", "M16", f"G0 Z{f1(SAFE_Z)}", f"G0 X{f1(x0)} Y{f1(o['y'])}", f"M{t}",
                f"G0 Z{f1(-o['z'])}", f"G1 X{f1(x1)} F{FEED}", f"G0 X{f1(x0)}", f"G0 Z{f1(SAFE_Z)}"]
    out += ["M85", "M88", "L GFINPRO.ISC", "M02"]
    return "\r\n".join(out) + "\r\n"


@register("aes_sirius", "AES Sirius (G-kod)", "cnc", "",
          note="Bitta namunadan o'rganilgan: faqat x=0 / x=dx qirra teshiklari; yuz teshigi, y=0 / y=dy qirra teshigi, paz va "
               "freza — xato beriladi. Asbob raqami majburiy («Инструменты»); `M<n>` — asbob raqami bilan bir xil deb olingan. "
               "X = uzunlik − x, Z = −z, `L M7` sarlavhasi — faraz (namuna simmetrik). Qisqichlarga tegish tekshiruvi "
               "(«Обработка задевает прижимы») yo'q — stanokda sinash shart.")
def aes_sirius(job: DrillJob) -> Files:
    return [(job.code, program(job).encode("ascii", errors="replace"))]
