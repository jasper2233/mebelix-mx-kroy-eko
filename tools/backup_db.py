"""Ish bazasining zaxira nusxasi (server ishlab turganda ham xavfsiz).

Har yangilash (kod o'zgarishi, server qayta ishga tushishi) oldidan: `python tools/backup_db.py`.
• Xodimlar serveri PostgreSQL da bo'lsa (`../run_server.bat` da `postgresql` URL) — `pg_dump` (siqilgan, -Fc) →
  `<loyiha ildizi>/../backups/mebelix_pg_YYYYmmdd_HHMMSS.dump`, `pg_restore --list` bilan tekshiriladi;
• aks holda — SQLite backup API → `mebelix_kroy_YYYYmmdd_HHMMSS.db` (PRAGMA integrity_check).
Har turdan oxirgi 10 tasi saqlanadi. `--mode pg|sqlite` — majburan tanlash.
"""
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent
SRC = ROOT / "backend" / "mebelix_kroy.db"
DST_DIR = BASE / "backups"
KEEP = 10


def _mode() -> str:
    if "--mode" in sys.argv:
        return sys.argv[sys.argv.index("--mode") + 1]
    bat = BASE / "run_server.bat"
    try:
        if re.search(rb"MEBELIX_DB_URL=postgresql", bat.read_bytes()):
            return "pg"
    except OSError:
        pass
    return "sqlite"


def _pg_env() -> dict:
    env = dict(os.environ)
    for ln in (BASE / "pg_secrets.env").read_text(encoding="ascii").splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    # zaxira — bosh administrator nomidan: RLS (korxonalar ajratilishi) dastur foydalanuvchisiga hammasini bermaydi,
    # zaxirada esa BARCHA korxonalar bo'lishi kerak
    env["PGPASSWORD"] = env["PG_SUPERPASS"]
    return env


def backup_pg() -> int:
    env = _pg_env()
    DST_DIR.mkdir(exist_ok=True)
    dst = DST_DIR / f"mebelix_pg_{datetime.now():%Y%m%d_%H%M%S}.dump"
    bin_ = BASE / "pgsql" / "bin"
    r = subprocess.run([str(bin_ / "pg_dump.exe"), "-h", "localhost", "-p", env.get("PG_PORT", "5432"), "-U", env["PG_SUPERUSER"],
                        "-d", env["PG_DB"], "-Fc", "-Z", "6", "-f", str(dst)], env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print("pg_dump xato:", r.stderr.strip()[:500])
        return 2
    lst = subprocess.run([str(bin_ / "pg_restore.exe"), "--list", str(dst)], env=env, capture_output=True, text=True)
    ok = lst.returncode == 0 and "TABLE DATA public projects" in lst.stdout
    print(f"zaxira: {dst} ({dst.stat().st_size // (1024 * 1024)} MB), tekshiruv: {'ok' if ok else 'XATO'}")
    for old in sorted(DST_DIR.glob("mebelix_pg_*.dump"))[:-KEEP]:
        old.unlink()
    return 0 if ok else 2


def backup_sqlite() -> int:
    if not SRC.exists():
        print(f"baza topilmadi: {SRC}")
        return 1
    DST_DIR.mkdir(exist_ok=True)
    dst = DST_DIR / f"mebelix_kroy_{datetime.now():%Y%m%d_%H%M%S}.db"
    src = sqlite3.connect(f"file:{SRC}?mode=ro", uri=True)
    out = sqlite3.connect(dst)
    with out:
        src.backup(out)
    src.close()
    out.close()
    ok = sqlite3.connect(dst).execute("PRAGMA integrity_check").fetchone()[0]
    print(f"zaxira: {dst} ({dst.stat().st_size // (1024 * 1024)} MB), tekshiruv: {ok}")
    for old in sorted(DST_DIR.glob("mebelix_kroy_*.db"))[:-KEEP]:
        old.unlink()
    return 0 if ok == "ok" else 2


def main() -> int:
    return backup_pg() if _mode() == "pg" else backup_sqlite()


if __name__ == "__main__":
    sys.exit(main())
