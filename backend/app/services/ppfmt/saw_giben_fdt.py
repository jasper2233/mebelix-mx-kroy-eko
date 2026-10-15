"""Giben G57 va Giben GVisionXP — `.fdt` (Prisma «FDT/FDS» INI-matn): listlar, detallar, kartalar va kesimlar ketma-ketligi.
Tavsif: docs/mebelix/postprocessors/giben-g57.md, giben-gvisionxp.md.

Bitta CS operatsiyasi (material) = bitta fayl `<loyiha>_<material>.fdt` (ASCII/cp1251, LF, o'lchamlar mm×1000).
GVisionXP — shu formatning «soddalashtirilgan» ko'rinishi: detallar ro'yxati va joylashuv yo'q, faqat kartalar va
`Tagli_Ed` kesimlari; bir nechta maydon namunalardagi doimiylar bilan yoziladi."""
from __future__ import annotations

from . import Files, SawJob, register
from ._saw_common import job_title
from ._saw_giben import GN, GPat, business_area, depth, layout, patterns, um

_ZERO_A = ("LUNGHEZZALAMA", "MINIMOX", "MINIMOY", "MASSIMOX", "MASSIMOY", "QTFSTGVER", "MINSTRISCIAX", "MINSTRISCIAY",
           "BATTUTA", "PINZEY1", "PINZEY2", "PRETAGLI", "RIFPRETG", "RIFPRETAGLIOR", "MINIMOPRE", "MASSIMOPRE",
           "PRETAGLIORIZ", "PRETAGLIOZ")
_ZERO_B = ("RIPETIZIONI", "TIPOSFRIDO", "MAGGIORAZIONE", "ECCEDENZAPERC", "POSIZIONI", "RINUMERAPOS", "LIBERAPOS",
           "LUNGMINCOIL", "ECCRIP", "STIRAMENTO", "FORMATOUNICO", "MAXNUMSTRISCIE", "MAXNUMSTRISCIEPRETG",
           "MAXPROFPRETAGLIO", "LIVTGSXPRETG", "COSTOTGX", "COSTOTGY", "COSTOTAGLISUCC", "COSTOPRETAGLIO",
           "COSTOSBANCATA", "COSTOFISSO", "MINIMOSFRIDOX", "MINIMOSFRIDOY", "MINIMOMIGLIORESFRIDOX",
           "MINIMOMIGLIORESFRIDOY", "COL2LIVELLO")
_PANEL_TAIL = ("MINTRONC = 0", "CAV = 0", "TIPOPANNELLO = 0", "RUOT = -1", "SBN = 0", "SBS = 0", "SBE = 0", "SBO = 0",
               "MINIMOSFRIDOX = 0", "MINIMOSFRIDOY = 0", "MINIMOMIGLIORESFRIDOX = 0", "MINIMOMIGLIORESFRIDOY = 0",
               "NUMCAV = 0", "INSERTMAN = -1")
_FDS_HEAD = ("SBN = 0", "SBS = 0", "SBE = 0", "SBO = 0", "RUOT = -1", "PRUOTATO = 0", "TAGLIABILE = -1", "RIFIUTATO = 0",
             "AFFETTATO = 0", "VERTOR = 0", "ALTOBASSO = 0", "DXSX = 0", "TIPOTAGLIO = 0", "AREAELEM = 0",
             "AREAELEMRECUPER = 0", "LUNGTAGLI = 0", "NUMTAGLI = 0")


def _rnd(x: float) -> int:
    return int(x + 0.5)


def _cuts(nodes: list[GN], lvl: int = 3) -> list[tuple[int, float, int]]:
    """Daraxtning to'g'ri (pre-order) o'tishi: (TIPOTG, QUOTATG, QTARIP)."""
    out: list[tuple[int, float, int]] = []
    for c in nodes:
        out.append((lvl, c.size, c.rep))
        out += _cuts(c.kids, lvl + 1)
    return out


def _sheets(job: SawJob, pats: list[GPat]) -> tuple[list[tuple[str, float, float, int]], dict[int, str]]:
    """Ishlatilgan list formatlari: [(IDL, uzunlik, en, soni)] va karta → IDL."""
    ids: dict[tuple, int] = {}
    rows: list[list] = []
    of: dict[int, str] = {}
    forced = str(job.params.get("sheet_id") or "").strip()
    for p in pats:
        m = p.map
        k = (m.sheet_id, round(m.sheet_length, 3), round(m.sheet_width, 3))
        if k not in ids:
            ids[k] = len(rows)
            rows.append([str(len(rows) + 1), m.sheet_length, m.sheet_width, 0])
        rows[ids[k]][3] += p.copies
        of[id(p)] = rows[ids[k]][0]
    if forced and len(rows) == 1:                  # stanokdagi list raqami sozlamadan (bitta format bo'lsa)
        rows[0][0] = forced
        of = {k: forced for k in of}
    return [tuple(r) for r in rows], of


def _fdt(job: SawJob, gvision: bool) -> str:
    pats = patterns(job)
    name = job.material_name
    kerf = job.kerf
    thick = "18000" if gvision else str(um(job.thickness))
    cs = getattr(job.op, "cs_material", None)
    min_part = um(getattr(cs, "min_part_size", 30.0) or 0)
    L: list[str] = []
    a = L.append
    a("[StartGenerale]"); a("VERSIONE = 6"); a("[EndGenerale]")
    a("[StartProduzione]"); a("NUMOTTIMIZZAZIONI = 1"); a("[StartOtt1]")
    a("MATERIALE = " + ("" if gvision else name)); a("SPESSORE = " + thick)
    for x in ("SCARICATA = 0", "RIGA = 23", "APPLICAZIONE = ", "VERSIONEOTT = ", "COLORE = Colore", "CODTIPO = ",
              "DESCR = "):
        a(x)
    a("CODMAT = " + name); a("CODCOL = COL"); a("PEZZINONPOS = 0"); a("TAGLIABILE = -1"); a("[EndOtt1]")
    a("[EndProduzione]")
    a("[StartOttimizzazioni]"); a("[StartOttimizzazione1]"); a("[StartParametri]")
    a("[StartParametriPriorita]")
    for x in ("ABILITAPRIORITA", "GREZZO", "SFRIDO", "COIL", "SEMILAVORATO", "PRODOTTOFINITO"):
        a(x + " = 0")
    a("[EndParametriPriorita]"); a("[StartParametriPannelli]"); a("CODGRUPPO = "); a("PARTENZA = LASTRE")
    a("SPESSORE = " + thick); a("PROFSCAN = 10000"); a("CODMATERIALE = " + name)
    a("MATERIALE = " + ("" if gvision else " " + name)); a("VELMATERIALE = " + ("20000" if gvision else "150000"))
    a("CODCOLORE = COL"); a("COLORE = Colore"); a("CODTIPO = "); a("PESOSPECIFICO = 0")
    a("DESCRPRODUZIONE = " + ("" if gvision else "MATERIALE|COLORE|1")); a("RIFVALORIZ = -1")
    a("[EndParametriPannelli]")
    a("[StartParametriMacchina]")
    for x in ("CODMACCHINA = 0", "NOMEMACCHINA = ", "OTTSEMPLIFICATA = 0", "GESTAUTOSBORDI = 0", "ORDPZSTR = 0",
              "TEMPIMEDIOCICLO = 0", "ACCORPAPEZZISUMISURE = 0", "ACCORPAPEZZISUMISURECODICE = 0"):
        a(x)
    a("[EndParametriMacchina]"); a("[StartParametriGenerali]")
    a("TIPOSTRISCE = " + ("0" if gvision else "1")); a("LIVELLITAGLIO = " + ("0" if gvision else str(max([4] + [depth(P.kids) for P in pats]))))
    a("ORIGINEASSI = 0"); a("POSIZIONESFRIDI = 0"); a("XORDINAPER = 0"); a("XORDINADIR = " + ("0" if gvision else "1"))
    a("YORDINAPER = 0"); a("YORDINADIR = 0"); a("MANTIENILOGICO = 0")
    if not gvision:
        a(f"SPESSORELAMA = {um(kerf)}")
    a("DIAMETROLAMA = 390000")
    for x in _ZERO_A:
        a(x + " = 0")
    a("NOMEPOSTP = "); a("ALTEZZAPACCO = 90000")
    for x in _ZERO_B:
        a(x + " = 0")
    a("OTTIMIZZA = -1"); a("RIFILOMIN = 0"); a("[EndParametriGenerali]"); a("[EndParametri]")

    # ── listlar (FDT)
    sheets, sheet_of = _sheets(job, pats)
    if gvision:
        # namunalarda doim ikkita «standart» format (1: 2750×1830, 3: 2750×2100); birinchisi — bizning list o'lchami
        l0, w0 = (sheets[0][1], sheets[0][2]) if sheets else (2750.0, 1830.0)
        panels = [("1", l0, w0, 1), ("3", 2750.0, 2100.0, 1)]
    else:
        panels = sheets
    a("[StartPannelliFDT]")
    for i, (idl, pl, pw, q) in enumerate(panels, 1):
        a(f"[StartDatiPannelloFDT{i}]"); a(f"NUMEROPANNINIZ = {len(panels)}"); a(f"NUMEROPANN = {len(panels)}")
        a(f"[StartDatiPannelloFDT{i}]")            # teg ikki marta — namunalardagi kabi
        a("NUOVO = -1"); a("SFRIDO = 0"); a("FAMIGLIA = "); a("RIGA = -1"); a(f"IDL = {idl}"); a("DES = ")
        a("BARCODE = "); a(f"XBA = {um(pl)}"); a(f"YAL = {um(pw)}"); a(f"QTAINIZ = {q}"); a(f"QTA = {q}")
        a("COS = 0"); a("PRT = 0"); a(f"COD = {idl}")
        for x in _PANEL_TAIL:
            a(x)
        a(f"[EndDatiPannelloFDT{i}]"); a(f"[EndPannelloFDT{i}]")
    a("[EndPannelliFDT]")

    # ── detallar (FDT)
    a("[StartElementiFDT]")
    if not gvision:
        for i, p in enumerate(job.parts, 1):
            a(f"[StartDatiElementoFDT{i}]"); a("NUOVO = -1"); a("RIGA = 0"); a(f"IDP = {p.uid}")
            for x in ("FAMIGLIA", "BARCODE", "DISEGNO", "PRODUZIONE", "COMMESSA", "CLIENTE"):
                a(x + " = ")
            a(f"XBA = {um(p.length)}"); a(f"YAL = {um(p.width)}")
            for x in ("QTAINIZ", "QTA", "RUOT", "URG", "CAV", "SBN", "SBS", "SBE", "SBO"):
                a(x + " = 0")
            a("IN = 5132488"); a("BN = "); a("IS = 1242984"); a("BS = "); a(f"IE = {i}"); a("BE = "); a("IO = 0")
            a("BO = "); a("COD = ")
            for x in ("ORD", "ECCPOS", "ECCNEG", "MAGGPOSX", "MAGGNEGX", "MAGGPOSY", "MAGGNEGY", "NUMLAV"):
                a(x + " = 0")
            for x in ("DATA = ", "IDL = 0", "LCOD = ", "LXBA = 0", "LYAL = 0", "ELSFRIDO = 0", "INSERTMAN = -1",
                      "DESCRIZIONE = ", "TIPORECORD = 0", "NUMPEZZIBASEPALLET = 0", "NUMPEZZIALTEZZAPALLET = 4203419",
                      "ALTEZZAPALLET = 0", "DESCRORDINE = ", "DATAORDINE = ", "SORDINE = "):
                a(x)
            a(f"[EndDatiElementoFDT{i}]")
    a("[EndElementiFDT]"); a("[StartMacro]"); a("[EndMacro]")

    # ── natija yig'indisi
    a("[StartParametriFDS]"); a("TEMPODICALCOLO = "); a(f"TOTALESCHEMI = {len(pats)}")
    if gvision:
        a(f"AREATOTALEPANN = {um(panels[0][1] * panels[0][2] + panels[1][1] * panels[1][2])}")
        a("AREATOTALEELEM = 0"); a("AREATOTALEELEMREC = 0")
    else:
        area = 0.0
        for _, pl, pw, q in sheets:
            area += pl * pw / 1e6 * q              # m² (namunadagi yaxlitlash shu tartibda mos keladi)
        a(f"AREATOTALEPANN = {_rnd(area * 1000)}")
        a(f"AREATOTALEELEM = {_rnd(sum(p.length * p.width * p.qty for p in job.parts) / 1000)}")
        a(f"AREATOTALEELEMREC = {_rnd(business_area(job) * 1000)}")
    a("[EndParametriFDS]")

    # ── kartalar (FDS)
    a("[StartPannelliFDS]")
    for i, P in enumerate(pats, 1):
        a(f"[StartPannelloFDS{i}]"); a(f"[StartDatiPannelloFDS{i}]"); a("NUMELEMENTI = 0")
        a(f"RIPETIZIONI = {P.copies}"); a("IDL = " + ("1" if gvision else sheet_of[id(P)]))
        a(f"DIMX = {um(P.dimx)}"); a(f"DIMY = {um(P.dimy)}")
        for x in _FDS_HEAD:
            a(x)
        a(f"MINIMOSFRIDOX = {min_part}"); a(f"MINIMOSFRIDOY = {min_part}")
        a("MINIMOMIGLIORESFRIDOX = 0"); a("MINIMOMIGLIORESFRIDOY = 0"); a("MAGAZZINO = 0")
        a(f"FOGLIPACCO = {P.copies}"); a("RIFILOCODA = 0"); a("RIFILO1 = 0"); a("RIFILO2 = 0")
        a(f"RIFILO3 = {um(P.map.trim_length)}"); a(f"RIFILO4 = {um(P.map.trim_width)}"); a("RIFILO5 = 0")
        a("NUMCAV = 0"); a("AREAELEMMAX = 0"); a("TOTALEBORDI = 0")
        a(f"[EndDatiPannelloFDS{i}]"); a("[StartElementiFDS]")
        if not gvision:
            for j, (uid, x0, y0, x1, y1) in enumerate(layout(P, kerf), 1):
                a(f"[StartDatiElementoFDS{j}]"); a(f"IDP = {uid}"); a("RUOTATO = 0"); a("RUOTABILE = -1")
                a(f"XANGINF = {um(x0)}"); a(f"YANGINF = {um(y0)}"); a(f"XANGSUP = {um(x1)}"); a(f"YANGSUP = {um(y1)}")
                for x in ("ELSFRIDO", "RIFIUTATO", "SELEZIONATO", "MAGELEMENTO"):
                    a(x + " = 0")
                a("TIPOSELEZIONE = 5161934"); a(f"[EndDatiElementoFDS{j}]")
        a("[EndElementiFDS]"); a("[StartTagli]")
        if not gvision:
            xx = um(P.dimx + kerf / 2)
            a("[StartTaglio1]"); a(f"XANGINF = {xx}"); a("YANGINF = 0"); a(f"XANGSUP = {xx}")
            a(f"YANGSUP = {um(P.dimy)}")
            for x in ("TIPOTG = 0", "TGUTENTE = -1", "PADRE = 0", "FIGLIO = 0", "FRATELLO = 0", "PEZZOSTACCATO = 0"):
                a(x)
            a("[EndTaglio1]")
        a("[EndTagli]"); a("[StartTagli_Ed]")
        for j, (lvl, q, n) in enumerate(_cuts(P.kids), 1):
            a(f"[StartTg_Ed{j}]")
            for x in ("XSTARTTG", "YSTARTTG", "XENDTG", "YENDTG"):
                a(x + " = 0")
            a(f"QUOTATG = {um(q)}"); a(f"TIPOTG = {lvl}"); a("LINEATG = 0"); a("TGUTENTE = -1")
            a("PEZZISTACCATI = 1"); a(f"QTARIP = {n}"); a("PADRE = 0"); a("FIGLIO = 0"); a("FRATELLO = 0")
            a(f"[EndTg_Ed{j}]")
        a("[EndTagli_Ed]"); a("[StartSIDP_PezziProd]"); a("[EndSIDP_PezziProd]"); a(f"[EndPannelloFDS{i}]")
    if gvision:
        a("[StartTagli_Ed]")                       # namunalardagi yopilmagan teg
    a("[EndPannelliFDS]"); a("[EndOttimizzazione1]"); a("[EndOttimizzazioni]")
    return "\n".join(L) + "\n"


_NOTE = ("Namunalarda buyurtmaning faqat birinchi materiali eksport qilingan; bizda har CS operatsiyasi (material) — "
         "alohida fayl. Namunalarda kesim darajalari 3…6 (4 daraja; kroy chuqurroq bo'lsa 7 ham yoziladi); o'rtadagi chiqindi yozilmaydi (bo'laklar oldinga suriladi). ")


@register("giben_g57", "Giben G57 (.fdt)", "saw", "fdt",
          note=_NOTE + "List raqami (IDL) — «sheet_id» sozlamasi yoki 1,2,…; «axlat» doimiylar (IN, IS, TIPOSELEZIONE) "
                       "va ALTEZZAPACCO=90000 namunadagidek; kromka/nom yozilmaydi; RUOTATO doim 0.")
def giben_g57(job: SawJob) -> Files:
    return [(job_title(job) + ".fdt", _fdt(job, False).encode("cp1251", "replace"))]


@register("giben_gvisionxp", "Giben GVisionXP (.fdt)", "saw", "fdt",
          note=_NOTE + "Detallar va joylashuv yozilmaydi (faqat kesimlar). SPESSORE=18000, ikkinchi «standart» list "
                       "2750×2100 va propil yozilmasligi — namunadagi doimiylar (stanok sozlamasi bilan tekshirilsin).")
def giben_gvisionxp(job: SawJob) -> Files:
    return [(job_title(job) + ".fdt", _fdt(job, True).encode("cp1251", "replace"))]
