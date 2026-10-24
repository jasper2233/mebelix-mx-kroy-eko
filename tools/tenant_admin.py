"""Abonentlar (korxonalar) va foydalanuvchilarni boshqarish (ko'p abonentli rejim, docs/mebelix/Y_MASSHTAB_ABONENTLAR.md).

    python tools/tenant_admin.py list
    python tools/tenant_admin.py create-company "Mebel sexi"                       → yangi korxona raqami
    python tools/tenant_admin.py add-user --company 2 --login ali --password ... [--roles admin|cutter|technologist|viewer] [--name "Ali"]
    python tools/tenant_admin.py set-password --login ali --password ...
    python tools/tenant_admin.py import-env-users --bat ../run_server.bat         → MEBELIX_USERS dagi loginlar 1-korxonaga (xesh bilan)
    python tools/tenant_admin.py deactivate-company 2 | activate-company 2

Baza — `MEBELIX_DB_URL` (yoki `--db`). Parollar ekranga chiqarilmaydi, bazada faqat PBKDF2 xeshi saqlanadi.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _boot(db: str | None):
    if db:
        os.environ["MEBELIX_DB_URL"] = db
    sys.path.insert(0, str(ROOT / "backend"))
    from app import db as D
    D.init_db()
    return D


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", help="baza URL (berilmasa — MEBELIX_DB_URL)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    c = sub.add_parser("create-company"); c.add_argument("name")
    u = sub.add_parser("add-user")
    u.add_argument("--company", type=int, required=True); u.add_argument("--login", required=True)
    u.add_argument("--password", required=True); u.add_argument("--roles", default="admin"); u.add_argument("--name", default="")
    sp = sub.add_parser("set-password"); sp.add_argument("--login", required=True); sp.add_argument("--password", required=True)
    ie = sub.add_parser("import-env-users"); ie.add_argument("--bat", required=True)
    for cmd in ("deactivate-company", "activate-company"):
        x = sub.add_parser(cmd); x.add_argument("id", type=int)
    a = ap.parse_args()
    D = _boot(a.db)
    from app.auth import hash_password
    from app import tenant

    with tenant.system(), D.SessionLocal() as s:
        if a.cmd == "list":
            for co in s.query(D.CompanyRow).order_by(D.CompanyRow.id):
                users = s.query(D.UserRow).filter(D.UserRow.company_id == co.id).order_by(D.UserRow.login).all()
                print(f"[{co.id}] {co.name} {'' if co.active else '(o`chirilgan)'} — foydalanuvchilar: "
                      + (", ".join(f"{x.login}({'|'.join(x.roles or [])})" for x in users) or "yo'q"))
            return 0
        if a.cmd == "create-company":
            co = D.CompanyRow(name=a.name.strip(), active=True, plan="")
            s.add(co); s.commit()
            print("yangi korxona:", co.id)
            return 0
        if a.cmd == "add-user":
            if s.get(D.CompanyRow, a.company) is None:
                print("korxona yo'q:", a.company); return 2
            login = a.login.strip().lower()
            if s.query(D.UserRow).filter(D.UserRow.login == login).first():
                print("bunday login bor:", login); return 2
            s.add(D.UserRow(company_id=a.company, login=login, password_hash=hash_password(a.password),
                            name=a.name or login, roles=[r for r in a.roles.split("|") if r] or ["admin"], active=True))
            s.commit(); print("qo'shildi:", login)
            return 0
        if a.cmd == "set-password":
            usr = s.query(D.UserRow).filter(D.UserRow.login == a.login.strip().lower()).first()
            if usr is None:
                print("login yo'q"); return 2
            usr.password_hash = hash_password(a.password); s.commit(); print("parol yangilandi:", usr.login)
            return 0
        if a.cmd == "import-env-users":
            raw = Path(a.bat).read_bytes()
            m = re.search(rb'MEBELIX_USERS=([^"\r\n]*)', raw)
            if not m:
                print("MEBELIX_USERS topilmadi"); return 2
            n = 0
            for item in m.group(1).decode().split(","):
                bits = item.strip().split(":")
                if len(bits) < 2 or not bits[0]:
                    continue
                login = bits[0].strip().lower()
                roles = [r for r in (bits[2] if len(bits) > 2 else "admin").split("|") if r] or ["admin"]
                usr = s.query(D.UserRow).filter(D.UserRow.login == login).first()
                if usr is None:
                    s.add(D.UserRow(company_id=tenant.DEFAULT_CID, login=login, password_hash=hash_password(bits[1]),
                                    name=login, roles=roles, active=True))
                    n += 1
            s.commit(); print("import qilindi:", n)
            return 0
        if a.cmd in ("deactivate-company", "activate-company"):
            co = s.get(D.CompanyRow, a.id)
            if co is None:
                print("korxona yo'q"); return 2
            co.active = a.cmd == "activate-company"; s.commit(); print("ok")
            return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
