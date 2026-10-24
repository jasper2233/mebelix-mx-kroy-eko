"""OEE (W17): eski bazada migratsiya — yangi jadvallar yaratiladi (CREATE), eski ma'lumot saqlanadi, kam ustunli eski OEE jadvali
ALTER bilan to'ldiriladi (+ indekslar, unikal `external_id`). Alohida jarayonda (`MEBELIX_DB_URL` import paytida o'qiladi)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

SCRIPT = textwrap.dedent('''
    import json
    from sqlalchemy import inspect, text
    import app.db as d

    out = {}
    # 1) ESKI baza: OEE jadvallarisiz, ma'lumot bilan
    legacy = [t for t in d.Base.metadata.sorted_tables if not t.name.startswith("oee_")]
    d.Base.metadata.create_all(d.engine, tables=legacy)
    with d.engine.begin() as c:
        c.execute(text("INSERT INTO folders (id, name, owner) VALUES ('f1', 'Papka', 'u')"))
        c.execute(text("INSERT INTO remnants (material_code, length, width, thickness, qty, linear) VALUES ('LDSP', 800, 600, 16, 2, 0)"))
    out["oee_before"] = sorted(t for t in inspect(d.engine).get_table_names() if t.startswith("oee_"))

    d.init_db()                                   # CREATE
    d.init_db()                                   # takroriy chaqiruv xato bermaydi
    insp = inspect(d.engine)
    out["oee_after"] = sorted(t for t in insp.get_table_names() if t.startswith("oee_"))
    out["event_cols"] = sorted(c["name"] for c in insp.get_columns("oee_events"))
    out["event_idx"] = sorted(i["name"] for i in insp.get_indexes("oee_events") if i["name"])
    with d.engine.begin() as c:
        out["kept_remnants"] = c.execute(text("SELECT COUNT(*) FROM remnants")).scalar()
        out["kept_folders"] = c.execute(text("SELECT COUNT(*) FROM folders")).scalar()

    # 2) kam ustunli ESKI oee_events (+ bitta qator) → ALTER
    with d.engine.begin() as c:
        c.execute(text("DROP TABLE oee_events"))
        c.execute(text("CREATE TABLE oee_events (id INTEGER PRIMARY KEY AUTOINCREMENT, type VARCHAR(10) NOT NULL, "
                       "machine_key VARCHAR(64) NOT NULL, start_ts DATETIME, end_ts DATETIME, qty INTEGER)"))
        c.execute(text("INSERT INTO oee_events (type, machine_key, end_ts, qty) VALUES ('run', 'm1', '2026-01-01 10:00:00', 3)"))
    insp = inspect(d.engine)
    out["stale_cols_before"] = sorted(c["name"] for c in insp.get_columns("oee_events"))
    d.init_db()
    insp = inspect(d.engine)
    out["stale_cols_after"] = sorted(c["name"] for c in insp.get_columns("oee_events"))
    out["stale_idx_after"] = sorted(i["name"] for i in insp.get_indexes("oee_events") if i["name"])
    # korxona ichida noyob (ko'p abonentli rejim, 2026-10-22): (company_id, external_id)
    want = ["company_id", "external_id"]
    out["stale_unique_after"] = any(i.get("unique") and i["column_names"] == want for i in insp.get_indexes("oee_events")) or \\
        any(u["column_names"] == want for u in insp.get_unique_constraints("oee_events"))
    with d.SessionLocal() as s:
        row = s.query(d.OeeEventRow).first()
        out["old_row"] = [row.type, row.machine_key, row.qty, row.external_id, row.reject_qty]

    # 3) migratsiyadan keyin tizim ishlaydi: boshlang'ich ma'lumot, stanok, idempotent qabul, hisob
    from app.services import oee
    oee.ensure_defaults()
    oee.create_machine(oee.MachineIn(key="m1"))
    ev = dict(type="run", machine="m1", end="2026-01-02T10:00:00Z", qty=1, external_id="e1")
    a = oee.ingest([ev])[0]["status"]
    b = oee.ingest([ev])[0]["status"]
    out["ingest"] = [a, b]
    # unikal indeks haqiqatan ishlaydi: ikkinchi bir xil external_id to'g'ridan-to'g'ri qo'shilmaydi
    from sqlalchemy.exc import IntegrityError
    try:
        with d.SessionLocal() as s:
            s.add(d.OeeEventRow(type="run", machine_key="m1", end_ts=None, external_id="e1"))
            s.commit()
        out["unique_enforced"] = False
    except IntegrityError:
        out["unique_enforced"] = True
    out["reasons"] = len(oee.list_reasons())
    print("RESULT:" + json.dumps(out))
''')


def run_script(tmp_path):
    db = tmp_path / "old.db"
    env = dict(os.environ, MEBELIX_DB_URL=f"sqlite:///{db.as_posix()}", PYTHONIOENCODING="utf-8")
    env.pop("MEBELIX_TEST_DB_URL", None)
    p = subprocess.run([sys.executable, "-c", SCRIPT], cwd=str(BACKEND), env=env, capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert p.returncode == 0, p.stderr[-3000:]
    line = next(x for x in p.stdout.splitlines() if x.startswith("RESULT:"))
    return json.loads(line[len("RESULT:"):])


def test_old_database_gets_oee_tables_and_keeps_data(tmp_path):
    r = run_script(tmp_path)
    assert r["oee_before"] == []
    assert r["oee_after"] == ["oee_config", "oee_events", "oee_machines", "oee_reasons", "oee_shifts"]
    assert r["kept_remnants"] == 1 and r["kept_folders"] == 1               # eski ma'lumot buzilmagan
    for col in ("type", "machine_key", "start_ts", "end_ts", "qty", "reject_qty", "unit", "parts", "cut_length_m", "cuts",
                "ideal_cycle_s", "reason", "external_id", "source", "created_at", "updated_at"):
        assert col in r["event_cols"], col
    # indekslar (vaqt/stanok bo'yicha so'rovlar uchun)
    assert {"ix_oee_events_machine_end", "ix_oee_events_machine_start", "ix_oee_events_type"} <= set(r["event_idx"])


def test_stale_oee_table_is_altered_and_old_rows_survive(tmp_path):
    r = run_script(tmp_path)
    assert "external_id" not in r["stale_cols_before"] and "reject_qty" not in r["stale_cols_before"]
    assert {"external_id", "reject_qty", "unit", "cut_length_m", "reason", "source", "created_at"} <= set(r["stale_cols_after"])
    assert {"ix_oee_events_machine_end", "ix_oee_events_machine_start"} <= set(r["stale_idx_after"])
    assert r["stale_unique_after"] is True and r["unique_enforced"] is True
    assert r["old_row"] == ["run", "m1", 3, None, None]                    # eski qator o'qiladi, yangi ustunlar — NULL
    assert r["ingest"] == ["created", "unchanged"] and r["reasons"] == 15
