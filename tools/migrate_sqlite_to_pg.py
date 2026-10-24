"""SQLite (eski ish bazasi) → PostgreSQL ko'chirish (ko'p abonentli rejim, docs/mebelix/Y_MASSHTAB_ABONENTLAR.md).

    python tools/migrate_sqlite_to_pg.py --src backend/mebelix_kroy.db --dst "postgresql+psycopg://..."  [--force]

• Maqsad bazada sxema yaratiladi (`init_db`: jadvallar, RLS, 1-korxona). Ma'lumot — 1-korxona (bizning ishxona).
• Maqsadda allaqachon loyiha bo'lsa — to'xtaydi (ustidan yozilmasin); `--force` — maqsaddagi ma'lumot jadvallari tozalanadi.
• Oxirida har jadval qatorlari soni va loyihalar mazmuni (nazorat yig'indisi) solishtiriladi; farq bo'lsa — xato bilan chiqadi.
Manba bazaga tegilmaydi (faqat o'qish).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="SQLite fayli")
    ap.add_argument("--dst", required=True, help="PostgreSQL URL (postgresql+psycopg://...)")
    ap.add_argument("--force", action="store_true", help="maqsaddagi ma'lumot jadvallarini tozalab qayta ko'chirish")
    a = ap.parse_args()
    src_path = Path(a.src).resolve()
    if not src_path.is_file():
        print("manba topilmadi:", src_path)
        return 2
    os.environ["MEBELIX_DB_URL"] = a.dst
    sys.path.insert(0, str(ROOT / "backend"))
    from sqlalchemy import create_engine, insert, select, text
    from app import tenant
    from app import db as D

    src = create_engine(f"sqlite:///file:{src_path.as_posix()}?mode=ro&uri=true")
    D.init_db()
    # ko'chirish tartibi: ota jadvallar avval
    order = ["folders", "projects", "project_history", "catalog_items", "catalog_images", "settings_profiles", "remnants",
             "oee_machines", "oee_shifts", "oee_reasons", "oee_events", "oee_config"]
    meta = D.Base.metadata
    with tenant.system():
        with D.engine.begin() as c:
            have = c.execute(text("SELECT count(*) FROM projects")).scalar()
            if have and not a.force:
                print(f"maqsadda {have} ta loyiha bor — to'xtadim (--force bilan qayta ko'chirish mumkin)")
                return 3
            if a.force:
                for t in reversed(order):
                    c.execute(text(f"DELETE FROM {t}"))
        src_tables = set(src.dialect.get_table_names(src.connect()))
        report = []
        for name in order:
            if name not in src_tables:
                report.append((name, 0, 0))
                continue
            t = meta.tables[name]
            with src.connect() as sc:
                scols = [r[1] for r in sc.exec_driver_sql(f"PRAGMA table_info({name})")]
                cols = [c for c in t.columns if c.name in scols or c.name == "company_id"]
                rows = [dict(r._mapping) for r in sc.execute(select(*[t.c[c.name] for c in cols if c.name in scols]))]
            for r in rows:
                r["company_id"] = 1
            if name == "folders":                         # o'z-o'ziga havola: avval ota papkalar
                done, pending, ordered = set(), list(rows), []
                while pending:
                    nxt = [r for r in pending if not r.get("parent_id") or r["parent_id"] in done]
                    if not nxt:                           # yetim havola — otasiz qilib qo'yiladi
                        nxt = pending[:1]
                        nxt[0]["parent_id"] = None
                    for r in nxt:
                        done.add(r["id"]); ordered.append(r); pending.remove(r)
                rows = ordered
            with D.engine.begin() as c:
                for i in range(0, len(rows), 500):
                    c.execute(insert(t), rows[i:i + 500])
                # butun sonli kalit ketma-ketligi davom etsin
                pk = [k for k in t.primary_key.columns if k.autoincrement is True or (k.name == "id" and str(k.type) == "INTEGER")]
                for k in pk:
                    c.execute(text(f"SELECT setval(pg_get_serial_sequence('{name}', '{k.name}'), "
                                   f"GREATEST((SELECT max({k.name}) FROM {name}), 1))"))
            with D.engine.connect() as c:
                n_dst = c.execute(text(f"SELECT count(*) FROM {name}")).scalar()
            report.append((name, len(rows), n_dst))

        # mazmun tekshiruvi: har loyiha JSON i (kalitlar tartibidan qat'i nazar) bir xil
        def digest(conn, sql):
            h = hashlib.sha256()
            for pid, data in conn.execute(text(sql)):
                obj = json.loads(data) if isinstance(data, str) else data
                h.update(pid.encode()); h.update(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode())
            return h.hexdigest()
        with src.connect() as sc, D.engine.connect() as c:
            d_src = digest(sc, "SELECT id, data FROM projects ORDER BY id")
            d_dst = digest(c, "SELECT id, data FROM projects ORDER BY id")
    bad = [r for r in report if r[1] != r[2]]
    for name, a_n, b_n in report:
        print(f"{name:20s} manba {a_n:7d}  →  maqsad {b_n:7d}  {'OK' if a_n == b_n else 'FARQ!'}")
    print("loyihalar mazmuni:", "bir xil" if d_src == d_dst else "FARQ!")
    return 1 if bad or d_src != d_dst else 0


if __name__ == "__main__":
    raise SystemExit(main())
