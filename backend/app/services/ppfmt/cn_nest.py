"""(CN) Нестинговый раскрой — ishlov markazlari uchun frezalash dasturi (har karta = bitta fayl `F<n>.<ext>`, zip).

Formatlar onlayn tizimda «test uchun» loyihasida chiqarilgan fayllardan o'rganildi (2026-10-24; tavsif —
`docs/mebelix/postprocessors/cn-nesting.md`): CNC (NCStudio) `.NC`, KDT (GCode) `.NC`, Homag WoodWOP `.mpr`, TPA `.TCN`,
Biesse BiesseWorks `.bpp`. Hammasi bir xil ma'lumotdan yoziladi: har karta uchun asbob markazi yo'llari (siniq chiziqlar,
list koordinatalarida: X o'ngga, Y pastga, chap-yuqori burchakdan), asbob va chuqurlik.

Yo'llar MX nesting natijasidan: har detalning asbob yo'li (`cn_post` — kontur ofseti, yoylar siniq chiziq). Onlayn tizim
qo'shni detallar orasidagi umumiy chiziqni bir marta kesadi — MX har detal konturini alohida aylanib o'tadi (xavfsiz, lekin
uzunroq). Fayl sintaksisi namunalar bilan bayt-ma-bayt tekshirilgan (`tools/bench/pp_online_same_cut.py --kind cn`).

Chuqurlik: freza list qalinligi + «Выступ снизу» ga tushadi (onlayn: 18 + 0 → Z-18, 18 + 0.5 → Z-18.5); KDT da Z hisobi
stol (list osti) dan: kirish Z = −выступ, chiqish Z = qalinlik + 20; Y = y − list eni.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import num, register

CRLF = "\r\n"


@dataclass
class NestTool:
    name: str = "MillBaseCut"
    number: int = 1
    diameter: float = 12.0
    rpm: int = 18000
    feed_z: float = 3000.0
    feed_xy: float = 5000.0
    ccw: bool = True                 # «Против часовой стрелки (D-)» — M04; aks holda M03


@dataclass
class NestMap:
    index: int
    length: float
    width: float
    paths: list[list[tuple[float, float]]] = field(default_factory=list)


@dataclass
class NestJob:
    thickness: float
    overhang: float                  # «Выступ снизу» (freza list ostidan chiqishi), mm
    tool: NestTool
    maps: list[NestMap]
    params: dict = field(default_factory=dict)

    @property
    def depth(self) -> float:
        return self.thickness + self.overhang


def _p(job: NestJob, key: str, dflt):
    v = job.params.get(key)
    return dflt if v in (None, "") else v


def _f1(v: float) -> str:
    return f"{float(v):.1f}"


def _files(job: NestJob, ext: str, text) -> list[tuple[str, bytes]]:
    return [(f"F{m.index}.{ext}", text(job, m).encode("cp1251", "replace")) for m in job.maps]


# ───────────────────────── CNC (NCStudio) ─────────────────────────
def ncstudio(job: NestJob, m: NestMap, state: Optional[dict] = None) -> str:
    t = job.tool
    rz = float(_p(job, "retract_z", 30))
    z = _f1(-job.depth)
    out = ["(NCStudio, generated code in MebeliX Kroy)", "G90", f"({num(t.diameter)}MM {t.name})", f"T{t.number} M06",
           f"G0 Z{_f1(rz)}", f" M0{4 if t.ccw else 3} S{t.rpm}", f"G43 H{t.number}"]
    state = {} if state is None else state
    first_g1 = state.get("first_g1", True)   # butun ishdagi (1-fayl) birinchi G1 qatorida Z ham yoziladi (namunadagi kabi)
    for path in m.paths:
        if len(path) < 2:
            continue
        (px, py) = path[0]
        out += [f"G0 X{_f1(px)} Y{_f1(py)}", f"Z{z} F{_f1(t.feed_z)}"]
        first = True
        for x, y in path[1:]:
            w = ["G1"]
            if _f1(x) != _f1(px):
                w.append(f"X{_f1(x)}")
            if _f1(y) != _f1(py):
                w.append(f"Y{_f1(y)}")
            if len(w) == 1:
                continue
            if first_g1:
                w.append(f"Z{z}")
            if first:
                w.append(f"F{_f1(t.feed_xy)}")
            out.append(" ".join(w))
            first = first_g1 = False
            px, py = x, y
        out.append(f"G0 Z{_f1(rz)}")
    state["first_g1"] = first_g1
    out += ["M05", "M30"]
    return CRLF.join(out) + CRLF


# ───────────────────────── KDT (GCode) ─────────────────────────
KDT_START = "G53 Z-15.000 \\n M129 \\n M123 \\n M125 \\n G53 Z-15.000 \\n G54 G90"
KDT_END = "M30"


def _block(s: str) -> list[str]:
    return [x.strip() for x in str(s).replace("\\n", "\n").split("\n") if x.strip()]


def kdt(job: NestJob, m: NestMap) -> str:
    t = job.tool
    W = m.width
    up = _f1(float(_p(job, "retract_z_kdt", job.thickness + 20)))
    z = _f1(-job.overhang) if job.overhang else "0.0"
    out = _block(_p(job, "start_block", KDT_START)) + [f"M6 T{t.number}", f"M0{4 if t.ccw else 3} S{t.rpm}", f"G43 H{t.number}"]
    for path in m.paths:
        if len(path) < 2:
            continue
        x0, y0 = path[0]
        out += [f"G0 X{_f1(x0)} Y{_f1(y0 - W)}", f"G1 Z{z} F{num(t.feed_z)}"]
        first = True
        for x, y in path[1:]:
            out.append(f"G1 X{_f1(x)} Y{_f1(y - W)}" + (f" F{num(t.feed_xy)}" if first else ""))
            first = False
        out.append(f"G0 Z{up}")
    out += ["M5"] + _block(_p(job, "end_block", KDT_END))
    return CRLF.join(out) + CRLF


# ───────────────────────── Homag WoodWOP (.mpr) ─────────────────────────
def woodwop(job: NestJob, m: NestMap) -> str:
    L, W, T = num(m.length), num(m.width), num(job.thickness)
    za = num(-job.overhang) if job.overhang else "0"
    out = ["[H", 'VERSION="4.0 Alpha"', 'MAT="HOMAG"', 'FM="1"', 'INCH="0"', 'VIEW="NOMIRROR"', 'ANZ="1"', 'BES="0"', 'ENT="0"',
           f"_BSX={L}", f"_BSY={W}", f"_BSZ={T}", "_FNX=0.000000", "_FNY=0.000000", "_RNX=0.000000", "_RNY=0.000000",
           "_RNZ=0.000000", f"_RX={L}", f"_RY={W}", "",
           "[001", f'l="{L}"', 'KM="length"', f'w="{W}"', 'KM="width"', f't="{T}"', 'KM="thickness"', "",
           "<100 \\WerkStck\\", 'LA="l"', 'BR="w"', 'DI="t"', 'FNX="0"', 'FNY="0"', 'AX="0"', 'AY="0"', ""]
    k = 0
    for path in m.paths:
        if len(path) < 2:
            continue
        k += 1
        x0, y0 = path[0]
        out += [f"]{k}", "$E0", "KP ", f"X={num(x0)}", f"Y={num(y0)}", f"Z={za}", "KO=00", ""]
        for i, (x, y) in enumerate(path[1:], 1):
            out += [f"$E{i}", "KL ", f"X={num(x)}", f"Y={num(y)}", ""]
        out += ["<105 \\Konturfraesen\\", f'EA="{k}:0"', f'EE="{k}:{len(path) - 1}"', 'RK="NoWRK"', 'MDA="SEN"',
                'MDE="SEN_AB"', 'EM="0"', f'TNO="{job.tool.number}"', f'ZA="{za}"', 'F_="STANDARD"', ""]
    if out[-1] == "" and k:
        out.pop()                     # oxirgi blokdan keyin bo'sh qator yo'q
    out.append("!")
    return CRLF.join(out) + CRLF


# ───────────────────────── TPA (TCN tpaCAD) ─────────────────────────
TPA_LABEL = ("W#1100{ ::WT2 WB=1 #8098=truetype.tmcr #6=1 #8015=0 #8020=l/2 #8021=h/2 #8132=1 #8103=0 #8104=0 #8100=0 "
             "#8500=FRONT #8501=Arial #8502=20.0 #8503=2.00 #8504=0 #8505=0 #8507=20 #8508=0 #8512=0 #8520=1 #8521=1 "
             "#8523=1 #8524=0 }W")


def tpa(job: NestJob, m: NestMap) -> str:
    out = ["TPA\\ALBATROS\\EDICAD\\02.00:921:r0w0h0s1", "$=null", "::SIDE=1",
           f"::UNm DL={num(m.length)} DH={num(m.width)} DS={num(job.thickness)}",
           "OFFS{", "#0=0|0", "#1=0|0", "#2=0|0", "#3=0.0|0", "#4=0.0|0", "#5=0.0|0", "#6=0.0|0", "#7=0.0|0", "}OFFS",
           "VARV{", "}VARV", "VAR{", "}VAR", "SPEC{", "}SPEC", "OPTI{", "}OPTI", "LINK{", "}LINK", "PREV{", "}PREV", "SIDE#1{"]
    for path in m.paths:
        if len(path) < 2:
            continue
        x0, y0 = path[0]
        out.append(f"W#89{{ ::WTs #1={num(x0)} #2={num(y0)} #3={num(-job.depth)} #40=0 #205=1 }}W")
        out += [f"W#2201{{ ::WTl  #1={num(x)}  #2={num(y)} }}W" for x, y in path[1:]]
    out += [TPA_LABEL, "}SIDE"] + [s for n in range(2, 7) for s in (f"SIDE#{n}{{", "}SIDE")]
    return CRLF.join(out) + CRLF


# ───────────────────────── Biesse (BiesseWorks v3.x) ─────────────────────────
_BPP_VARS = ['ORLST|"1"', "SIMMETRY|1", "TLCHK|0", 'TOOLING|""', 'CUSTSTR|""', "FCN|1.000000", "XCUT|0", "YCUT|0", "JIGTH|0",
             "CKOP|0", "UNIQUE|0", 'MATERIAL|"ashwhite"', 'PUTLST|""', "OPPWKRS|0", "UNICLAMP|0", "CHKCOLL|0", "WTPIANI|0",
             "COLLTOOL|0", "CALCEDTH|0", "ENABLELABEL|0", "RUNPAV|1"]
_ROUT_TAIL = ("-1, 0, 0, 0, 0, 50, 0, 45, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, "
              '0, 0,"", 103, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, 0, 0, 0, 0, "", 5, 0, '
              '20, 80, 60, 0, "", "", "ROUT", 0, 0, 0, 0, 0, 0, 0, 0, 0')


def biesse(job: NestJob, m: NestMap, start_no: int) -> tuple[str, int]:
    """→ (matn, keyingi P raqami): `P<n>` hisoblagichi kartalar (fayllar) bo'ylab davom etadi."""
    out = ["[HEADER]", "TYPE=BPP", "VER=130", "", "[DESCRIPTION]", "|", "", "[VARIABLES]",
           f"PAN=LPX|{num(m.length)}||0|", f"PAN=LPY|{num(m.width)}||0|", f"PAN=LPZ|{num(job.thickness)}||0|"]
    out += [f"PAN={v}||0|" for v in _BPP_VARS] + ["", "[PROGRAM]"]
    nid = 15                          # qator raqamlari: ROUT 15, START +11, birinchi LINE +11, keyingilari +10, ENDPATH +12, keyingi ROUT +6
    no = start_no
    tl = num(job.tool.diameter)
    for path in m.paths:
        if len(path) < 2:
            continue
        out.append(f'@ ROUT, "", "", {nid}, "", 0 : "P{no:05d}", 0, "{job.tool.number}", 0, {num(job.depth)}, "", 1, {tl}, '
                   + _ROUT_TAIL)
        no += 1
        nid += 11
        x0, y0 = path[0]
        out.append(f'  @ START_POINT, "", "", {nid}, "", 0 : {num(x0)}, {num(y0)}, 0')
        nid += 11
        for i, (x, y) in enumerate(path[1:]):
            if i:
                nid += 10
            out.append(f'  @ LINE_EP, "", "", {nid}, "", 0 : {num(x)}, {num(y)}, 0, 0, 0, 0, 0, 0, 0')
        nid += 12
        out.append(f'  @ ENDPATH, "", "", {nid}, "", 0 :')
        nid += 6
    out += ["", "[VBSCRIPT]", "", "[MACRODATA]", "", "[TDCODES]", "", "[PCF]", "", "[TOOLING]", ""]
    return CRLF.join(out) + CRLF, no


def _biesse_files(job: NestJob) -> list[tuple[str, bytes]]:
    out = []
    no = 1
    for m in job.maps:
        txt, no = biesse(job, m, no)
        out.append((f"F{m.index}.bpp", txt.encode("cp1251", "replace")))
    return out


_NOTE = ("Har karta — bitta fayl (F1, F2 …). Yo'llar — MX nesting natijasidagi detal konturlari (asbob markazi). «Выступ снизу», "
         "asbob raqami, aylanish, tezliklar — «Настройки → Постпроцессоры» da.")
def _ncstudio_files(job: NestJob) -> list[tuple[str, bytes]]:
    st: dict = {}
    return [(f"F{m.index}.NC", ncstudio(job, m, st).encode("cp1251", "replace")) for m in job.maps]


register("cn_ncstudio", "CNC (NCStudio) — nesting", "nest", "zip", note=_NOTE)(_ncstudio_files)
register("cn_kdt_gcode", "KDT (GCode) — nesting", "nest", "zip", note=_NOTE)(lambda job: _files(job, "NC", kdt))
register("cn_woodwop", "Homag (WoodWOP v6.x) — nesting", "nest", "zip", note=_NOTE)(lambda job: _files(job, "mpr", woodwop))
register("cn_tpa", "TPA Genesis Evolution 8.9 — nesting", "nest", "zip", note=_NOTE)(lambda job: _files(job, "TCN", tpa))
register("cn_biesseworks", "Biesse (BiesseWorks v3.x) — nesting", "nest", "zip", note=_NOTE)(_biesse_files)

# stanok sozlamasidagi standart asbob (onlayn tizimdagi standartlar)
DEFAULT_TOOL = {
    "cn_ncstudio": NestTool(rpm=3000, feed_z=100.0, feed_xy=5000.0),
    "cn_kdt_gcode": NestTool(rpm=18000, feed_z=3000.0, feed_xy=8000.0),
}


def nest_job(project, op, machine_key: Optional[str] = None) -> NestJob:
    """MX nesting natijasi → NestJob: har karta uchun detallar asbob yo'llari (tashqi va ichki konturlar)."""
    from ..cn_post import context_cn
    params: dict = {}
    if machine_key:
        try:
            from ..pp_machine_ctx import get_params
            params = get_params(machine_key)
        except Exception:      # noqa: BLE001 — sozlama sxemasi bo'lmasa standartlar
            params = {}
    ctx = context_cn(project, op, machine_key)
    d = DEFAULT_TOOL.get(machine_key or "", NestTool())
    tool = NestTool(name=str(params.get("tool_name") or d.name), number=int(params.get("tool_number") or d.number),
                    diameter=float(ctx["tool"]["diameter"]), rpm=int(params.get("rpm") or d.rpm),
                    feed_z=float(params.get("feed_z") or d.feed_z), feed_xy=float(params.get("feed_xy") or d.feed_xy),
                    ccw=str(params.get("direction", "ccw")) != "cw")
    maps = []
    for mm in ctx["maps"]:
        paths = []
        for pl in mm["placements"]:
            for ring in pl["tool_path"]["holes"] + pl["tool_path"]["outer"]:     # avval ichki konturlar, keyin tashqi
                pts = [(round(float(x), 3), round(float(y), 3)) for x, y in ring]
                if pts and pts[0] != pts[-1]:
                    pts.append(pts[0])
                if len(pts) >= 3:
                    paths.append(pts)
        maps.append(NestMap(index=mm["index"], length=mm["sheet_length"], width=mm["sheet_width"], paths=paths))
    return NestJob(thickness=float(ctx["op"]["thickness"]), overhang=float(params.get("overhang") or 0), tool=tool,
                   maps=maps, params=params)
