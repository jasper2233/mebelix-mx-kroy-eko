"""MX Kroy: papkadagi har loyihada asosiy funksiyalarni sinash (API orqali, faqat o'qish/yuklab olish — loyiha o'zgarmaydi).
Har CS kroy natijasi uchun barcha arra formatlari, loyihadagi XNC lar uchun barcha prisadka formatlari, hisobot (HTML + A4 PDF),
etiketkalar, .project eksporti va MES paketi. Natija: har loyiha bo'yicha xatolar ro'yxati.
    python tools/parity/smoke_all.py <folder_id> [http://127.0.0.1:8000]
"""
import json, sys, time, urllib.request, urllib.error

FOLDER = sys.argv[1]
BASE = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000") + "/api"


def req(path, method="GET", body=None, timeout=300):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode(), {}


def js(path):
    s, b, _ = req(path)
    return json.loads(b) if s == 200 else None


native = js("/postprocessors/native") or []
saw = [n["key"] for n in native if n.get("group") != "cnc"]
cnc = [n["key"] for n in native if n.get("group") == "cnc"]
projects = [p for p in (js("/projects?all_folders=true") or []) if p.get("folder_id") == FOLDER]
summary = []
for p in projects:
    pid = p["id"]
    proj = js(f"/projects/{pid}")
    errs, ok = [], 0
    t0 = time.time()
    for path in (f"/projects/{pid}/report", f"/projects/{pid}/report.pdf", f"/projects/{pid}/labels",
                 f"/projects/{pid}/export/project", f"/projects/{pid}/mes-package?version=1"):
        s, b, h = req(path)
        if s != 200 or len(b) < 50: errs.append(f"{path.split(pid)[1]} → {s} {b[:120]!r}")
        else: ok += 1
    for o in proj["operations"]:
        if o["type"] != "CS" or not o.get("result"):
            continue
        for k in saw:
            s, b, h = req(f"/projects/{pid}/operations/{o['id']}/postprocess?key=machine:{k}")
            if s != 200 or not b: errs.append(f"arra {k} [{o['name'][:20]}] → {s} {b[:160]!r}")
            else: ok += 1
    if any(o["type"] == "XNC" for o in proj["operations"]):
        for k in cnc:
            s, b, h = req(f"/projects/{pid}/postprocess-xnc?key=machine:{k}")
            if s != 200 or not b: errs.append(f"prisadka {k} → {s} {b[:160]!r}")
            else: ok += 1
    summary.append({"name": p["name"], "ok": ok, "errors": errs, "s": round(time.time() - t0)})
    print(f"{p['name']}: {ok} ok, {len(errs)} xato ({round(time.time() - t0)} s)", flush=True)
    for e in errs[:40]:
        print("   ", e, flush=True)
json.dump(summary, open("smoke_all.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
