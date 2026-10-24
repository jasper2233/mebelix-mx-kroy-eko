"""Altendorf (ELMO) — formatli arra stanogi (qo'lda boshqariladigan, ELMO tirgak displeyi): har karta `<dastur>.<NNNN>.saw`,
zip `<dastur>.zip` (dastur — 4 raqamli nom, standart «0001»). Tavsif: docs/mebelix/postprocessors/altendorf-elmo.md.

Onlayn tizim faylidan o'rganildi (2026-10-24, 10 karta, 236 kesim): sarlavha (VER/ID/CANVAS/LABEL — doimiy), keyin
  ACUT (blok; №; Label-Identifikation-<id>; <id>; * A;B * A * t; detalmi; d1;d2; soni; <soni>x; tirgak; o'lcham;
        S;A;H;<disk balandligi>;U;G; boshqa tirgak; qoldiq+100; U;G;S;0;U;A;M;<t>;U;A)
  BLOCK (№; x1;y1;x2;y2; "en";;;"bo'y";1;1)        — keyin bo'linadigan bo'laklar (0 — butun list)
  LINE  (blok; №; x1;y1;x2;y2;1;1;1;1;<propil>;1)   — har arra yurishi (takrorlangan detal — har biri alohida)
Koordinatalar — list torsovkasi (+ propil) dan keyin (0, 0) chap-yuqori; list o'lchami shu nuqtadan qarama-qarshi chetgacha.
A — bo'lakning qat'iy o'lchami, B — kesishdan oldingi qolgan uzunlik; qoldiq = B − o'lcham. d1;d2 — detal bo'lsa detalning
o'z o'lchamlari (l; w), blok bo'lsa X;Y o'lchami (kesim o'qi bo'ylab + propil). Bloklar stek tartibida ishlanadi (oxirgi
yaratilgan blok birinchi). Ketma-ket bir xil detallar bitta ACUT da (soni, «Nx»), LINE esa har biri uchun.

Tirgak («P» — bo'ylama, «L» — ko'ndalang): bo'lak o'lchami bo'ylama tirgak oralig'ida va bo'lak «balandlik/en» nisbati
chegarasida bo'lsa — P, aks holda L (stanok sozlamalari: «Продольный упор» 2…1600, «Соотношение высота-ширина» 4).
Onlayn fayl bilan 212/236 kesimda bir xil; qolgan 24 tasida (asosan blokdagi oxirgi kesim) onlayn tizim L tanlagan —
qoidasi aniqlanmadi (ochiq savol, operator ikkala tirgak bilan ham kesa oladi).
"""
from __future__ import annotations

from . import SawJob, SawNode, num, register

HEAD = [";MebeliX Kroy postprocessor for Altendorf", "VER (1)", 'ID (" ";1)', "CANVAS (15;35;540;420)", "",
        "LABEL (5;0;3;0h;FFFFFFh;PRG;9)", "LABEL (200;0;3;0h;FFFFFFh;SHT;25)", "LABEL (560;60;4;0h;FFFFFFh;0s;1)",
        "LABEL (640;70;4;0h;FFFFFFh;0;7;1)", "LABEL (560;140;4;0h;FFFFFFh;1s;1)", "LABEL (640;150;4;0h;FFFFFFh;1;7;1)",
        "LABEL (560;200;4;0h;FFFFFFh;2s;1)", "LABEL (640;210;4;0h;FFFFFFh;2;7;1)", "LABEL (560;260;4;0h;FFFFFFh;3s;1)",
        "LABEL (640;270;4;0h;FFFFFFh;3;7;1)", "LABEL (640;110;3;0h;FFFFFFh;STRW;8)", "LABEL (560;25;4;0h;FFFFFFh;NAC;4)",
        "LABEL (5;435;3;0h;FFFFFFh;T2;20)", "LABEL (660;300;2;FFFFFFh;0h;RPM;10)", ""]
EPS = 0.01


def _n(v: float) -> str:
    return num(round(float(v), 3))


def _ext(n: SawNode, ax: str) -> float:
    return n.l if ax == "x" else n.w


def fence(s: float, A: float, P: dict) -> str:
    """«P» (bo'ylama tirgak) yoki «L» (ko'ndalang)."""
    lo, hi = float(P.get("fence_long_min", 2)), float(P.get("fence_long_max", 1600))
    ratio = float(P.get("height_width_ratio", 4) or 4)
    return "P" if lo <= s <= hi and s <= ratio * A else "L"


def map_text(job: SawJob, m) -> str:
    P = job.params or {}
    blade = _n(P.get("saw_blade_height", 49))
    t = _n(job.thickness)
    k = float(job.kerf)
    root = m.tree
    acut: list[str] = []
    blocks: list[str] = []
    lines: list[str] = []
    if root is None:
        return "\n".join(HEAD) + "\n"
    ox, oy = root.x, root.y                       # torsovka + propil
    Ln, Wn = m.sheet_length - ox, m.sheet_width - oy
    blocks.append(f'BLOCK (0;0;0;{_n(Ln)};{_n(Wn)};"{_n(Ln)}";;;"{_n(Wn)}";1;1)')
    nblk = [0]
    ncut = [0]
    # stek: (tugun, blok raqami, bo'lak boshi x0, y0, A — qat'iy o'lcham, B0 — o'z o'qi bo'yicha uzunlik)
    stack: list[tuple[SawNode, int, float, float, float, float]] = []
    root_ax = root.axis or "x"
    stack.append((root, -1, 0.0, 0.0, Wn if root_ax == "x" else Ln, Ln if root_ax == "x" else Wn))
    while stack:
        node, bid, x0, y0, A, B = stack.pop()
        ax = node.axis or "x"
        kids = list(node.children)
        while kids and kids[-1].kind == "W":      # oxirgi chiqindi / qoldiq — kesilmaydi
            kids.pop()
        cur = 0.0                                 # bo'lak boshidan (o'z o'qi bo'ylab)
        i = 0
        new_blocks: list[tuple[SawNode, int, float, float, float, float]] = []
        while i < len(kids):
            c = kids[i]
            s = _ext(c, ax)
            cnt = 1
            if c.kind == "P":                     # ketma-ket bir xil detal — bitta ACUT
                while i + cnt < len(kids) and kids[i + cnt].kind == "P" and kids[i + cnt].uid == c.uid \
                        and abs(_ext(kids[i + cnt], ax) - s) < EPS:
                    cnt += 1
            r = B - s
            f = fence(s, A, P)
            other = "L" if f == "P" else "P"
            if c.kind == "P":
                sp = job.part(c.uid)
                pl, pw = (sp.length, sp.width) if sp else (c.l, c.w)
                lab, pid, isp, d1, d2 = f"Label-Identifikation-{c.uid}", str(c.uid), "1", _n(pl), _n(pw)
            else:
                lab, pid, isp = "", "", "0"
                d1, d2 = (_n(s + k), _n(A)) if ax == "x" else (_n(A), _n(s + k))
            acut.append(f"ACUT ({bid};{ncut[0]};{lab};{pid};* {_n(A)};{_n(B)} * {_n(A)} * {t};{isp};{d1};{d2};{cnt};{cnt}x;"
                        f"{f};{_n(s)};S;A;H;{blade};U;G;{other};{_n(r + 100)};U;G;S;0;U;A;M;{t};U;A)")
            for j in range(cnt):
                pos = cur + s
                if ax == "x":
                    lines.append(f"LINE ({bid};{ncut[0]};{_n(x0 + pos)};{_n(y0)};{_n(x0 + pos)};{_n(y0 + A)};1;1;1;1;{_n(k)};1)")
                else:
                    lines.append(f"LINE ({bid};{ncut[0]};{_n(x0)};{_n(y0 + pos)};{_n(x0 + A)};{_n(y0 + pos)};1;1;1;1;{_n(k)};1)")
                if c.kind == "C" and j == 0:
                    nblk[0] += 1
                    if ax == "x":
                        bx0, by0, bx1, by1 = x0 + cur, y0, x0 + cur + s + k, y0 + A
                        new_blocks.append((c, nblk[0], x0 + cur, y0, s, A))
                    else:
                        bx0, by0, bx1, by1 = x0, y0 + cur, x0 + A, y0 + cur + s + k
                        new_blocks.append((c, nblk[0], x0, y0 + cur, s, A))
                    blocks.append(f'BLOCK ({nblk[0]};{_n(bx0)};{_n(by0)};{_n(bx1)};{_n(by1)};"{_n(bx1 - bx0)}";;;"{_n(by1 - by0)}";1;1)')
                cur += s + k
                B -= s + k
            ncut[0] += 1
            i += cnt
        stack.extend(new_blocks)                  # oxirgi yaratilgan blok — birinchi ishlanadi
    return "\n".join(HEAD + acut + [""] + blocks + [""] + lines) + "\n"


def generate(job: SawJob) -> list[tuple[str, bytes]]:
    prog = str((job.params or {}).get("program_name") or "0001").strip()[:4].rjust(4, "0")
    return [(f"{prog}.{i:04d}.saw", map_text(job, m).encode("cp1251", "replace")) for i, m in enumerate(job.maps, 1)]


NOTE = ("Har karta — `<dastur>.<NNNN>.saw` (zip). Tirgak tanlovi (P/L) stanok sozlamalaridagi tirgak oralig'i va balandlik/en "
        "nisbati bo'yicha; onlayn tizim bilan 90 % kesimda bir xil (qolganida u ko'ndalang tirgakni tanlaydi).")
register("elmo3", "Altendorf (ELMO) — .saw", "saw", "zip", note=NOTE)(generate)
