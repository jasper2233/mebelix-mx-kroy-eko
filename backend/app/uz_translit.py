# -*- coding: utf-8 -*-
"""O'zbek lotin yozuvi (1995 alifbosi) → o'zbek kirill yozuvi transliteratori.

Bitta manba: frontend generatsiyasi (`frontend/scripts/i18n_src.py` → `src/i18n/uz-Cyrl.json`) va backend ish vaqtida
(`app/i18n.py`, `uz-Cyrl` tili) shu modulni ishlatadi; brauzerdagi ma'lumot matnlari uchun aynan shu qoidalar
`frontend/src/i18n/translit.ts` da (moslik `frontend/scripts/check_translit_parity.mjs` bilan tekshiriladi).

Tarjima qilinmaydi: o'rinbosarlar ({{x}}, {x}, %s), teglar (<b>), `kod`, URL / e-mail, fayl kengaytmalari, tugma
birikmalari ([CTRL]+[P], Ctrl+W, F1), birliklar (mm, m²), katta harfli qisqartmalar (XNC, PDF, DXF), raqamli/«_» li
identifikatorlar (A4, part.name1), mahsulot/format nomlari (Excel, Holzma …), kirill matn («Раскрой» — o'zgarmaydi).
Istisnolar — `uz_cyrl_overrides.json` (words / stems / keep / keep_lower / phrases / abbr).
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

APOS = "'ʻ’`‘ʼ"
_HERE = os.path.dirname(os.path.abspath(__file__))
OVERRIDES_PATH = os.path.join(_HERE, "uz_cyrl_overrides.json")


def _load():
    with open(OVERRIDES_PATH, encoding="utf-8") as f:
        d = json.load(f)
    words = {k.lower(): v for k, v in d.get("words", {}).items()}
    stems = {k.lower(): v for k, v in d.get("stems", {}).items()}
    keep = {k.lower() for k in d.get("keep", [])}
    keep_lower = set(d.get("keep_lower", []))
    phrases = list(d.get("phrases", []))
    abbr = dict(d.get("abbr", {}))
    funcs = list(d.get("funcs", []))
    tags = list(d.get("tags", []))
    return words, stems, keep, keep_lower, phrases, abbr, funcs, tags


WORDS, STEMS, KEEP, KEEP_LOWER, PHRASES, ABBR, FUNCS, TAGS = _load()
_STEM_KEYS = sorted(STEMS, key=len, reverse=True)

# o'zbekcha qo'shimchalar zanjiri (o'zak istisnosidan keyin) — «sex» + «lar» + «da» …
SUFFIX_RE = re.compile(
    r"(?:lar|ning|ni|ga|ka|qa|dagi|da|ta|dan|tan|gacha|cha|imiz|ingiz|miz|ngiz|im|ing|si|i|m|ng|lik|li|siz|chi|day|dek"
    r"|mi|ku|yu|u|ham|lashtir|lash|lan|langan|la|dir|gi)*")

_A = "[" + re.escape(APOS) + "]"
_B = r"(?<![A-Za-z0-9_])"          # \b o'rniga: JS bilan bir xil (kirill harfi chegara hisoblanadi)
_E = r"(?![A-Za-z0-9_])"
# tugma nomlari (Ctrl+… dan keyin): bitta belgi, F1…F12, maxsus tugmalar
_KEYS = (r"F[0-9]{1,2}|PgUp|PgDn|PageUp|PageDown|Home|End|Del|Delete|Insert|Ins|Enter|Esc|Tab|Space|Backspace|Up|Down|Left"
         r"|Right|Ctrl|CTRL|Alt|ALT|Shift|SHIFT|Cmd|Win|Meta|[A-Za-z0-9](?:/[A-Za-z0-9])*|[^\sA-Za-z0-9]")
_PROTECT = re.compile(
    "|".join([
        r"\{\{.*?\}\}",                                  # i18next {{x}}
        r"\{[^{}\s]*\}",                                 # python {x}, {n:.1f}
        r"%\([A-Za-z_]+\)[sdif]|%[sdif]",                # %s, %(name)s
        r"\$t\([^)]*\)",                                 # i18next $t(kalit)
        r"</?(?:" + "|".join(TAGS) + r")(?:\s[^<>\n]*)?/?>",   # HTML/XML teglar (<b>, <program>); <nom> — o'giriladi
        r"`[^`\n]*`",                                    # `kod`
        r"\[[A-Za-z0-9 ]+\](?:\s*\+\s*\[[A-Za-z0-9 ]+\])*",   # [CTRL]+[P]
        r"(?:https?|ftp|file)://[^\s«»\"')]+",           # URL
        _B + r"www\.[^\s«»\"')]+",
        _B + r"data:[A-Za-z]+/[A-Za-z0-9.+-]+(?:;base64)?",
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+",     # e-mail
        _B + r"(?:Ctrl|CTRL|Alt|ALT|Shift|SHIFT|Cmd|Win|Meta)(?:\s*\+\s*(?:" + _KEYS + r"))+(?![A-Za-z0-9_" + APOS + "])",  # Ctrl+W, Shift+F1
        _B + r"(?:" + "|".join(FUNCS) + r")\(",                     # ifoda funksiyalari: trim(, max(
        r"(?<![A-Za-z0-9])/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.{}<>-]+)+",   # /api/mes/orders
        r"#/[A-Za-z0-9_/-]*",                                        # #/sex (manzil)
        _B + r"[A-Za-z_][A-Za-z0-9_]+(?:\.[A-Za-z_][A-Za-z0-9_]+)+" + _E,   # part.name1, label.lang
        r"(?<![A-Za-z0-9])\.[A-Za-z][A-Za-z0-9]{0,5}" + _E,          # .xlsx, .mxk
        _B + r"[A-Za-z_]+[0-9_][A-Za-z0-9_]*",                       # A4, F1, Code128, external_id
        _B + r"[A-Za-z]+(?:[ \t]*\|[ \t]*[A-Za-z_]+)+" + _E,         # kod qiymatlari: replace | rename | skip
    ] + [r"(?<![A-Za-z])" + re.escape(p) + r"(?![A-Za-z])" for p in sorted(PHRASES, key=len, reverse=True)]))
# qisqartmalar: «h.k.» → «ҳ.к.»
_ABBR = [(re.compile(r"(?<![A-Za-z])" + re.escape(k) + r"(?![A-Za-z])"), v)
         for k, v in sorted(ABBR.items(), key=lambda x: -len(x[0]))]

_WORD = re.compile(r"[A-Za-z]+(?:" + _A + r"[A-Za-z]+)*(?:(?<=[oOgG])" + _A + ")?")

_SIMPLE = {"a": "а", "b": "б", "d": "д", "f": "ф", "g": "г", "h": "ҳ", "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м",
           "n": "н", "o": "о", "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "x": "х", "z": "з",
           "w": "в", "c": "ц"}
_CYR_V = set("аеёиоуэюяўАЕЁИОУЭЮЯЎ")
_LAT_V = set("aeiou")
_YV = {"o": "ё", "u": "ю", "a": "я"}


def _rules(w: str, prev: str = "") -> str:
    """Bitta so'z (faqat lotin harflari va «'») → kirill. `prev` — oldingi kirill matn (o'zak istisnosidan keyin)."""
    lw = w.lower()
    n = len(w)
    out: list[str] = []
    i = 0

    def last() -> str:
        return out[-1][-1].lower() if out and out[-1] else (prev[-1:].lower() if prev else "")

    def at(j: int) -> str:
        return lw[j] if j < n else ""

    while i < n:
        c, nx, nx2, nx3 = lw[i], at(i + 1), at(i + 2), at(i + 3)
        up = w[i].isupper()
        step = 1
        if c in "og" and nx == "'":
            r, step = ("ў" if c == "o" else "ғ"), 2          # o' → ў, g' → ғ
        elif c == "s" and nx == "h":
            r, step = "ш", 2
        elif c == "c" and nx == "h":
            r, step = "ч", 2
        elif c == "y" and nx in ("o", "u", "a", "e") and nx and not (nx == "o" and nx2 == "'"):
            if nx == "e":                                    # ye: so'z boshi / unlidan keyin — е; undoshdan keyin — ъе (obyekt)
                lc = last()
                r = "е" if (not lc or lc in _CYR_V or lc in "ъь") else "ъе"
            else:
                r = _YV[nx]                                  # yo → ё, yu → ю, ya → я
            step = 2
        elif c == "e":                                       # so'z boshi / unlidan keyin — э
            lc = last()
            r = "э" if (not lc or lc in _CYR_V) else "е"
        elif c == "t" and nx == "s" and (nx2 == "e" or (nx2 == "i" and nx3 in _LAT_V and nx3)):
            r, step = "ц", 2                                 # operatsiya → операция, tsex → цех
        elif (c == "s" and last() in ("к", "н") and nx == "i"
              and (lw.startswith("ya", i + 2) or (last() == "к" and lw.startswith("on", i + 2)))):
            r = "ц"                                          # funksiya → функция, stansiya → станция
        elif c == "'":
            r = "" if (last() == "с" and nx == "h") else "ъ"   # Is'hoq → Исҳоқ; ma'lumot → маълумот
        elif c == "y":
            r = "й"
        else:
            r = _SIMPLE.get(c, w[i])
        out.append(r.upper() if up else r)
        i += step
    return "".join(out)


def _case(src: str, cyr: str) -> str:
    letters = [ch for ch in src if ch.isalpha()]
    if letters and letters[0].isupper():
        if len(letters) > 1 and all(ch.isupper() for ch in letters):
            return cyr.upper()
        return cyr[:1].upper() + cyr[1:]
    return cyr


def _word(w: str) -> str:
    norm = re.sub(_A, "'", w)
    lw = norm.lower()
    letters = re.sub(r"[^A-Za-z]", "", norm)
    if lw in WORDS:
        return _case(norm, WORDS[lw])
    if len(letters) == 1 and lw != "u" and not (len(norm) == 2 and norm[1] == "'"):
        return w                                           # bitta harf: X, Y, W, m (birlik)
    if len(letters) >= 2 and letters.isupper():
        return w                                           # qisqartma: XNC, PDF, ID, CTRL
    if re.search(r"[a-z][A-Z]", letters):
        return w                                           # MebeliX, PgUp, GibLab
    if lw in KEEP or norm in KEEP_LOWER:
        return w
    for st in _STEM_KEYS:
        if lw.startswith(st) and SUFFIX_RE.fullmatch(lw, len(st)):
            cyr = STEMS[st]
            return _case(norm, cyr + _rules(lw[len(st):], cyr))
    return _rules(norm)


def _words(s: str) -> str:
    return _WORD.sub(lambda m: _word(m.group(0)), s)


def _plain(s: str) -> str:
    out: list[str] = []
    pos = 0
    hits = sorted(((m.start(), m.end(), v) for rx, v in _ABBR for m in rx.finditer(s)), key=lambda x: x[0])
    for a, b, v in hits:
        if a < pos:
            continue
        out.append(_words(s[pos:a]))
        out.append(v)
        pos = b
    out.append(_words(s[pos:]))
    return "".join(out)


@lru_cache(maxsize=20000)
def to_cyrillic(s: str) -> str:
    """O'zbek lotin matni → kirill (himoyalangan bo'laklar o'zgarmaydi)."""
    if not s or not re.search(r"[A-Za-z]", s):
        return s
    out: list[str] = []
    pos = 0
    for m in _PROTECT.finditer(s):
        if m.start() > pos:
            out.append(_plain(s[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_plain(s[pos:]))
    return "".join(out)


def deep(v):
    """JSON tuzilmasidagi barcha satrlarni o'giradi (dict/list rekursiv; kalitlar o'zgarmaydi)."""
    if isinstance(v, str):
        return to_cyrillic(v)
    if isinstance(v, dict):
        return {k: deep(x) for k, x in v.items()}
    if isinstance(v, list):
        return [deep(x) for x in v]
    if isinstance(v, tuple):
        return tuple(deep(x) for x in v)
    return v
