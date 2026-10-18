# -*- coding: utf-8 -*-
"""uz-Cyrl (o'zbek kirill) tekshiruvi: `python scripts/i18n_check_uz_cyrl.py` → kirill matnda qolgan lotin so'zlar.

Ruxsat etilganlar (hisoblanadi, lekin topilma emas): o'rinbosarlar ({{x}}, {x}), katta harfli qisqartmalar (XNC, PDF),
bitta harf (X, Y, m), raqamli identifikatorlar (A4, F1), mahsulot/kod nomlari (`uz_cyrl_overrides.json` keep / keep_lower /
funcs / phrases), fayl kengaytmalari, tugma nomlari. Qolgani — «shubhali» (ko'pincha kod namunalari ichidagi so'zlar):
ro'yxat chiqariladi. `--strict` — shubhali bo'lsa chiqish kodi 1. `uz.json` dagi kirill bo'lmagan matnda o'zgarish
bo'lmagan qiymatlar ham sanaladi (o'girilmagan satr)."""
import collections, json, os, re, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(HERE, "..", "src", "i18n")
OV = json.load(open(os.path.join(I18N, "uz_cyrl_overrides.json"), encoding="utf-8"))
KEEP = {w.lower() for w in OV.get("keep", [])} | {w.lower() for w in OV.get("funcs", [])}
KEEP_LOWER = set(OV.get("keep_lower", [])) | set(OV.get("tags", []))
PHRASE_WORDS = {w.lower() for p in OV.get("phrases", []) for w in re.findall(r"[A-Za-z]+", p)}

PLACE = re.compile(r"\{\{.*?\}\}|\{[^{}\n]*\}|https?://\S+|`[^`\n]*`|\$t\([^)]*\)")
TOKEN = re.compile(r"(?<![A-Za-z0-9_.])[A-Za-z][A-Za-z'ʻ’]*(?![A-Za-z0-9_])")


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flatten(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def allowed(tok: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", tok)
    if len(letters) <= 1:
        return True
    if letters.isupper() or re.search(r"[a-z][A-Z]", letters):
        return True
    lw = letters.lower()
    return lw in KEEP or letters in KEEP_LOWER or lw in PHRASE_WORDS


def check():
    uz = flatten(json.load(open(os.path.join(I18N, "uz.json"), encoding="utf-8")))
    cy = flatten(json.load(open(os.path.join(I18N, "uz-Cyrl.json"), encoding="utf-8")))
    total = collections.Counter()
    suspicious = collections.defaultdict(list)
    unchanged = []
    for k, v in cy.items():
        if not isinstance(v, str):
            continue
        src = uz.get(k, "")
        if v == src and re.search(r"[a-z]{3,}", PLACE.sub("", src)):
            unchanged.append(k)
        for t in TOKEN.findall(PLACE.sub(" ", v)):
            total[t] += 1
            if not allowed(t):
                suspicious[t].append(k)
    return total, suspicious, unchanged


if __name__ == "__main__" and os.path.basename(globals().get("__file__", "")) == "i18n_check_uz_cyrl.py":
    total, sus, unchanged = check()
    print(f"qolgan lotin so'zlar (o'rinbosarlarsiz): {sum(total.values())} ta, {len(total)} xil")
    print("eng ko'p:", ", ".join(f"{w}×{n}" for w, n in total.most_common(40)))
    print(f"shubhali: {sum(len(v) for v in sus.values())} ta, {len(sus)} xil")
    for w, ks in sorted(sus.items(), key=lambda x: -len(x[1])):
        print(f"  {w}: {len(ks)} — {', '.join(ks[:4])}")
    print(f"o'zgarmagan qiymatlar (lotin matn): {len(unchanged)}", ", ".join(unchanged[:20]))
    sys.exit(1 if ("--strict" in sys.argv and sus) else 0)
