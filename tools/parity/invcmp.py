# GibLab ↔ MX Kroy ekran yozuvlari solishtiruvi: har ekranda GibLab'dagi yozuv / maslahat (title) / ro'yxat varianti bizda bormi
import json, os, re, sys, glob
IGN = re.compile(r"^(29367|behzod.*|.*@gmail.*|0 грн|GibLab|\d[\d .,:/%-]*|чт .*|UZS|.|\d{2}_\d{3}.*|\d{6}_.*|01_0\d\dx.*|Пазование1|№1 02 shkaf.*|[A-Za-z]{1,3}: [\d./% ]+|KP-.*|XDF.*|LDSP.*|1-\d+ .*|oval .*|02 shkaf|KROYGA|ldsp kashmir.*|19\*1 kashmir|.*Изделие1.*|Я 20.*|\d \w+|Yorqin.*|test uchun|Мой|Без имени|ср .*|Dropbox|<a href.*|\(CS\) ldsp.*)$")
def norm(t):
    t = t.lower().replace("ё", "е")
    t = re.sub(r"\[[^\]]*\]", "", t)            # [F1], [CTRL]+[A]
    t = re.sub(r"\([^)]*(ctrl|alt|shift|enter|f\d)[^)]*\)", "", t)
    t = re.sub(r"[^a-zа-я0-9]+", " ", t).strip()
    return t
def load(p):
    return json.load(open(p, encoding="utf-8"))
RU = set()        # ilovadagi barcha ruscha yozuvlar (jadval sarlavhasi maslahatlari DOM da `title` emas — shu yerdan tekshiriladi)
def _walk(d):
    for v in d.values():
        if isinstance(v, dict): _walk(v)
        else: RU.add(norm(str(v)))
_walk(json.load(open(r"D:/cloude giblab jasur/MebeliX_Kroy/frontend/src/i18n/ru.json", encoding="utf-8")))
TYPO = {"експортировать": "экспортировать", "коментарий": "комментарий", "окруление листы": "округление листы", "окруление полосы": "округление полосы", "сменить еmail": "сменить email", "длине реза c торцовкой": "длине реза с торцовкой", "для открытия проекта двойной клик по соответсвующей строке или нажмите": "для открытия проекта двойной клик по соответствующей строке или нажмите"}   # manbadagi imlo xatolari
allmx = set()
for f in glob.glob("inv/mx/*.json"):
    for k, t in load(f): allmx.add(norm(t))
tot = [0, 0]; rep = []
for f in sorted(glob.glob("inv/gl/*.json")):
    name = os.path.basename(f)[:-5]
    mxf = f"inv/mx/{name}.json"
    if not os.path.exists(mxf): continue
    mx = {norm(t) for k, t in load(mxf)}
    data = {norm(t) for k, t in load(mxf) if k == "text"}
    miss = []; n = 0
    for k, t in load(f):
        if k == "input" or IGN.match(t): continue
        nt = norm(t)
        if not nt or len(nt) < 2: continue
        n += 1
        nt = TYPO.get(nt, nt)
        if nt in mx or (k == "title" and nt in RU): continue
        if any(nt in m or (len(m) > 5 and m in nt) for m in mx): continue      # qisman mos (uzunroq / qisqaroq yozuv)
        miss.append((k, t, nt in allmx))
    tot[0] += n; tot[1] += n - len(miss)
    rep.append((name, n, len(miss), miss))
for name, n, m, miss in rep:
    print(f"{name:14s} {n-m:4d}/{n:<4d} = {100*(n-m)/max(n,1):5.1f}%")
    if "-v" in sys.argv:
        for k, t, elsewhere in miss: print(f"      - [{k}] {t}" + ("   (boshqa ekranda bor)" if elsewhere else ""))
print(f"JAMI {tot[1]}/{tot[0]} = {100*tot[1]/max(tot[0],1):.1f}%")
