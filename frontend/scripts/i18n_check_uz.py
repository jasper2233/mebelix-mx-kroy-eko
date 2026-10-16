# -*- coding: utf-8 -*-
"""uz tarjimasini tekshirish: `python scripts/i18n_check_uz.py` → ru bilan bir xil yoki kirill so'zli uz kalitlar ro'yxati.

Xodimlarning o'z atamalari (kirill, ikkala tilda bir xil: «Сони», «Ишлатилди», «ОВ/ОН/ОЛ/ОП», «Ткт», «Д-на/Ш-на» va h.k.)
ruxsat ro'yxatida — ular topilma hisoblanmaydi. Natija 0 bo'lsa chiqish kodi 0, aks holda 1.
Ishlatish: `--json` — topilmalarni JSON ro'yxat sifatida chiqaradi (tarjima skriptini tayyorlash uchun)."""
import json, os, re, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # Windows konsoli cp1251 bo'lsa ham kirill/lotin chiqsin

HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(HERE, "..", "src", "i18n")

# Xodimlar atamalari — kirill yozuvi ikkala tilda saqlanadi (A_GLOSSARY.md). Ro'yxat so'z darajasida: uz matndagi har bir
# kirill so'zi shu to'plamda bo'lsa — matn toza hisoblanadi.
STAFF_WORDS = {
    "сони", "ишлатилди", "колдик", "ов", "он", "ол", "оп", "ткт", "д-на", "ш-на", "изох", "мк", "ок", "д№",
}
# Kalit darajasidagi ruxsat: qiymat to'liq xodim atamasi yoki ma'lumot nomi (material/kromka nomlari, misollar).
ALLOW_KEYS = set()
# Kalit prefikslari — ma'lumotdan keladigan nomlar (material, kromka va h.k.), tarjima qilinmaydi.
ALLOW_PREFIX = ()

CYR = re.compile(r"[А-Яа-яЁёЎўҚқҒғҲҳ]")
WORD = re.compile(r"[А-Яа-яЁёЎўҚқҒғҲҳ][А-Яа-яЁёЎўҚқҒғҲҳ\-№]*\.?")


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "."))
        else:
            out[key] = v
    return out


def cyr_words(s):
    s = re.sub(r"Д(?=\d)", "", s)          # «Д5», «Д5⊂3» — qoldiq raqami (Д№), xodim belgisi
    return [w.lower().strip(".") for w in WORD.findall(s)]


def check():
    ru = flatten(json.load(open(os.path.join(I18N, "ru.json"), encoding="utf-8")))
    uz = flatten(json.load(open(os.path.join(I18N, "uz.json"), encoding="utf-8")))
    findings = []
    for k in sorted(uz):
        if k in ALLOW_KEYS or k.startswith(ALLOW_PREFIX):
            continue
        v = uz[k]
        if not isinstance(v, str):
            continue
        r = ru.get(k)
        ws = cyr_words(v)
        if not ws:
            continue          # lotin — bir xil bo'lsa ham (ID, Excel, mm…) muammo emas; «Д5» qoldiq raqami ham
        if all(w in STAFF_WORDS for w in ws):
            continue          # xodim atamasi («Сони», «ОВ»…)
        same = v == r
        findings.append({"key": k, "ru": r, "uz": v, "same": same})
    return findings


# `i18n_src.py` barcha `i18n_*.py` ni exec qiladi — u holda tekshiruv ishlamasin (faqat to'g'ridan-to'g'ri ishga tushganda).
if __name__ == "__main__" and os.path.basename(globals().get("__file__", "")) == "i18n_check_uz.py":
    f = check()
    if "--json" in sys.argv:
        print(json.dumps(f, ensure_ascii=False, indent=1))
    else:
        for x in f:
            tag = "=" if x["same"] else "~"
            print(f"{tag} {x['key']}: {x['uz']!r}")
        print(f"topilmalar: {len(f)}")
    sys.exit(1 if f else 0)
