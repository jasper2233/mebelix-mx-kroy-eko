"""Saqlash qatlami (SQLAlchemy). Standart — SQLite, prod uchun PostgreSQL:
   MEBELIX_DB_URL=postgresql+psycopg://user:pass@host/mebelix

Loyiha to'liq JSON hujjat sifatida saqlanadi — bu MES ga moslashni osonlashtiradi.
Ro'yxat/qidiruv uchun ustunlar alohida.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, LargeBinary, PrimaryKeyConstraint, String,
                        Text,
                        UniqueConstraint, create_engine, event, false, func, inspect, or_, text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

from . import tenant

log = logging.getLogger("mebelix.db")

DB_URL = os.getenv("MEBELIX_DB_URL", "sqlite:///./mebelix_kroy.db")
IS_SQLITE = DB_URL.startswith("sqlite")
IS_PG = DB_URL.startswith("postgresql")
# PostgreSQL: bir nechta ilova jarayoni (har biri o'z ulanishlar hovuzi) — hovuz o'lchami muhitdan
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if IS_SQLITE else {},
                       pool_pre_ping=True,
                       **({} if IS_SQLITE else dict(pool_size=int(os.getenv("MEBELIX_DB_POOL", "10")),
                                                    max_overflow=int(os.getenv("MEBELIX_DB_OVERFLOW", "20")),
                                                    pool_recycle=1800)))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()
# PostgreSQL da JSONB (siqilgan, tez o'qiladi); SQLite da oddiy JSON
JSONT = JSON().with_variant(JSONB(), "postgresql")


if IS_PG:
    @event.listens_for(engine, "begin")
    def _tenant_guc(conn):
        """Har tranzaksiya boshida joriy korxona (`app.cid`) va tizim rejimi (`app.sys`) — RLS siyosatlari shularni o'qiydi.
        Xom DBAPI kursori — SQLAlchemy tranzaksiyasini qayta boshlatmaslik uchun; `set_config(..., true)` — faqat shu tranzaksiyaga."""
        cur = conn.connection.dbapi_connection.cursor()
        try:
            cur.execute("SELECT set_config('app.cid', %s, true), set_config('app.sys', %s, true)",
                        (str(tenant.current()), "1" if tenant.is_system() else "0"))
        finally:
            cur.close()


def _company_col():
    """Korxona ustuni: ORM yozuvida joriy korxona; eski / SQLite qatorlari — 1 (bizning ishxona)."""
    return Column(Integer, nullable=False, default=tenant.current, server_default=text("1"), index=True)


def _fold(v):
    """SQLite funksiyasi: Unicode casefold (SQLite lower()/LIKE faqat ASCII uchun katta-kichikni farqlamaydi)."""
    return None if v is None else str(v).casefold()


if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _sqlite_functions(dbapi_conn, _record):      # har yangi ulanishda
        dbapi_conn.create_function("mx_fold", 1, _fold, deterministic=True)


def like_escape(s: str) -> str:
    """LIKE namunasida `%`, `_` va `\\` oddiy belgi bo'lib qolsin (ESCAPE '\\')."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def text_search(q: str, *cols):
    """«Ichida» qidiruv: katta-kichik harfga sezgirsiz (kirill ham — SQLite va PostgreSQL), `%`/`_` wildcard emas.
    Bo'sh `q` — shartsiz (None)."""
    q = (q or "").strip()
    if not q:
        return None
    if IS_SQLITE:
        pat = f"%{like_escape(q.casefold())}%"
        return or_(*[func.mx_fold(c).like(pat, escape="\\") for c in cols])
    pat = f"%{like_escape(q.lower())}%"
    return or_(*[func.lower(c).like(pat, escape="\\") for c in cols])


class CompanyRow(Base):
    """Abonent — korxona. Ma'lumot jadvallarining `company_id` si shunga ishora qiladi (RLS bilan ajratiladi)."""
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    plan = Column(String(30), default="")                   # ta'rif (3-bosqich)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserRow(Base):
    """Foydalanuvchi: login butun tizimda noyob (kichik harflarda), parol — PBKDF2-SHA256 xesh (`auth.hash_password`)."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    login = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(300), nullable=False)
    name = Column(String(200), default="")
    roles = Column(JSONT, default=list)
    active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class FolderRow(Base):
    __tablename__ = "folders"
    id = Column(String(32), primary_key=True)
    company_id = _company_col()
    parent_id = Column(String(32), ForeignKey("folders.id"), nullable=True)
    name = Column(String(200), nullable=False)
    owner = Column(String(100), default="")


class ProjectRow(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("company_id", "number", name="uq_projects_company_number"),)
    id = Column(String(32), primary_key=True)
    company_id = _company_col()
    number = Column(Integer, index=True)                    # Заказ ID — korxona ichida noyob
    folder_id = Column(String(32), ForeignKey("folders.id"), nullable=True, index=True)
    name = Column(String(300), index=True)
    owner = Column(String(100), default="")
    status = Column(Integer, default=0)
    order_date = Column(String(10))
    cost = Column(Float, default=0)
    mes_order_ref = Column(String(100), index=True, nullable=True)
    customer = Column(String(200), default="")
    history_cursor = Column(Integer, default=0)             # undo/redo ko'rsatkichi (joriy versiya)
    data = Column(JSONT, nullable=False)                    # to'liq Project JSON
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectHistoryRow(Base):
    """Отменить/Вернуть (undo/redo) uchun versiyalar."""
    __tablename__ = "project_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = _company_col()
    project_id = Column(String(32), ForeignKey("projects.id"), index=True)
    version = Column(Integer)
    data = Column(JSONT)                                    # eski yozuvlar (siqilmagan); yangilari — `zdata`
    zdata = Column(LargeBinary, nullable=True)              # zlib(JSON) — 2-bosqich: tarix ~3 marta kichik (store.history_data)
    created_at = Column(DateTime, default=datetime.utcnow)


class CatalogItemRow(Base):
    """Каталог товаров — MES ombor/tovarlar bilan sinxronlanadi."""
    __tablename__ = "catalog_items"
    # kalit — (korxona, id): MES dan kelgan id lar turli korxonalarda bir xil bo'lishi mumkin (`ckey`)
    __table_args__ = (PrimaryKeyConstraint("company_id", "id", name="pk_catalog_items"),)
    id = Column(String(64))
    company_id = Column(Integer, nullable=False, default=tenant.current, server_default=text("1"), index=True)
    parent_id = Column(String(64), nullable=True, index=True)
    kind = Column(String(20))       # sheet | linear | edge | surface | folder
    code = Column(String(100), index=True)
    name = Column(String(300))
    unit = Column(String(20), default="")
    price = Column(Float, default=0)
    stock = Column(Float, default=0)
    thickness = Column(Float, nullable=True)
    length = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    params = Column(JSONT, default=dict)   # grain, kerf, trim, ...
    has_image = Column(Boolean, default=False)   # rasm `catalog_images` jadvalida (ro'yxatga og'ir matn chiqmasin)


class CatalogImageRow(Base):
    """Material rasmi: tekshirilgan `data:image/…;base64,…` URI yoki `http(s)://` havola (services/catalog.py)."""
    __tablename__ = "catalog_images"
    __table_args__ = (PrimaryKeyConstraint("company_id", "item_id", name="pk_catalog_images"),)
    item_id = Column(String(64))
    company_id = Column(Integer, nullable=False, default=tenant.current, server_default=text("1"), index=True)
    data = Column(Text, nullable=False)


class SettingsProfileRow(Base):
    """Standart parametrlar va profillar: cs_defaults | el_defaults | print | labels | part_columns | postprocessor | app."""
    __tablename__ = "settings_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = _company_col()
    scope = Column(String(50), index=True)
    name = Column(String(100))
    data = Column(JSONT)
    is_default = Column(Boolean, default=False)


class RemnantRow(Base):
    """Ombordagi qoldiqlar (деловые остатки): kroydan keyin tasdiq bilan qo'shiladi, keyingi kroyda ishlatiladi."""
    __tablename__ = "remnants"
    __table_args__ = {"sqlite_autoincrement": True}     # o'chirilgan qoldiq raqami qayta berilmasin
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = _company_col()
    material_code = Column(String(100), index=True)
    material_name = Column(String(300), default="")
    length = Column(Float); width = Column(Float); thickness = Column(Float)
    qty = Column(Integer, default=1)
    source_project = Column(String(32), nullable=True)      # qaysi loyihadan qolgan
    source_number = Column(Integer, nullable=True)
    source_op = Column(String(32), nullable=True)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    reserved_project = Column(String(32), nullable=True, index=True)   # rezerv: qoldiqni tanlagan (band qilgan) loyiha id si
    # (CL, W11) погонажный qoldiq: bir o'lchovli bo'lak — `length` uzunlik, `width` polosa eni; listli (CS) qoldiqlardan ajratiladi
    linear = Column(Boolean, nullable=False, default=False, server_default=false())


class JobRow(Base):
    """Fon ishlari holati (CN nesting va keyingi bosqichda kroy / PDF): bir nechta ilova jarayoni bo'lganda holatni istalgan jarayon
    o'qiydi, to'xtatish (`cancel`) bayrog'ini ishni bajarayotgan jarayon ko'radi. Vaqtlar — UTC (epoch soniya)."""
    __tablename__ = "jobs"
    id = Column(String(32), primary_key=True)
    company_id = _company_col()
    kind = Column(String(20), nullable=False, default="cn")
    project_id = Column(String(32), index=True)
    op_id = Column(String(32))
    quality = Column(String(10), default="")
    state = Column(String(12), nullable=False, default="running", index=True)   # queued | running | done | error | cancelled
    progress = Column(Float, default=0.0)
    message = Column(Text, default="")
    error = Column(Text, default="")
    summary = Column(JSONT, nullable=True)
    cancel = Column(Boolean, nullable=False, default=False, server_default=false())
    started = Column(Float, nullable=False)
    finished = Column(Float, default=0.0)
    heartbeat = Column(Float, nullable=False)                          # oxirgi yangilanish (ishchi tirikligi)
    # 2-bosqich: hisoblar navbati (services/compute.py, app/worker.py) — vazifa kirishi, so'rov tili, bajaruvchi, HTTP xato kodi
    payload = Column(JSONT, nullable=True)
    lang = Column(String(16), nullable=True)
    worker = Column(String(64), nullable=True)
    code = Column(Integer, nullable=True)


# ───────────────────────── OEE va ishlab chiqarish analitikasi (W17) ─────────────────────────
# Barcha vaqtlar — UTC (naive datetime sifatida saqlanadi); smena soatlari esa zavod mahalliy vaqtida (`oee_config.tz_offset_min`).
def _utc_now() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)



class OeeMachineRow(Base):
    """OEE stanogi: `key` — postprotsessor stanoklari (`postprocessors.MACHINES`) kaliti yoki erkin; ideal tezlik parametrlari."""
    __tablename__ = "oee_machines"
    __table_args__ = (UniqueConstraint("company_id", "key", name="uq_oee_machines_company_key"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = _company_col()
    key = Column(String(64), nullable=False)
    name = Column(String(200), nullable=False)
    kind = Column(String(20), default="saw")                # saw | edge | cnc | other
    pp_key = Column(String(64), nullable=True)              # postprotsessor stanogi bilan bog'lanish (ixtiyoriy)
    cut_speed_mm_s = Column(Float, nullable=True)           # ideal kesish tezligi, mm/s
    cut_change_s = Column(Float, nullable=True)             # bitta kesim almashinuvi vaqti, s
    sheet_load_s = Column(Float, nullable=True)             # bitta list yuklash vaqti, s
    ideal_unit_s = Column(Float, nullable=True)             # geometriyasiz hodisalar uchun: bitta birlikning ideal sikli, s
    active = Column(Boolean, default=True)                  # NULL = faol
    note = Column(Text, default="")
    created_at = Column(DateTime, default=_utc_now)


class OeeShiftRow(Base):
    """Smena kalendari: `kind="shift"` — haftalik shablon (hafta kunlari, mahalliy soat, tanaffuslar); `kind="off"` — dam olish/bayram."""
    __tablename__ = "oee_shifts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = _company_col()
    kind = Column(String(10), default="shift")
    machine_key = Column(String(64), nullable=True, index=True)    # NULL — hamma stanoklar uchun
    name = Column(String(100), default="")
    weekdays = Column(JSONT, nullable=True)                 # [0..6], 0 = dushanba
    start_time = Column(String(5), nullable=True)           # «HH:MM» (mahalliy)
    end_time = Column(String(5), nullable=True)             # tugash ≤ boshlanish bo'lsa — yarim tundan o'tadi
    breaks = Column(JSONT, nullable=True)                   # [{start, end, name}] — rejalashtirilgan to'xtash
    valid_from = Column(String(10), nullable=True)          # YYYY-MM-DD (mahalliy sana), ixtiyoriy
    valid_to = Column(String(10), nullable=True)
    active = Column(Boolean, default=True)


class OeeReasonRow(Base):
    """To'xtash / brak sabab kodlari (sozlanadigan ro'yxat). `planned` — rejalashtirilgan to'xtash (rejalashtirilgan vaqtdan chiqariladi)."""
    __tablename__ = "oee_reasons"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_oee_reasons_company_code"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = _company_col()
    code = Column(String(32), nullable=False)
    name_ru = Column(String(120), default="")
    name_uz = Column(String(120), default="")
    kind = Column(String(10), default="downtime")           # downtime | reject
    planned = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    sort = Column(Integer, default=100)
    system = Column(Boolean, default=False)                 # boshlang'ich ro'yxat — o'chirib bo'lmaydi (nofaol qilish mumkin)


class OeeEventRow(Base):
    """OEE hodisasi: `run` (karta/list kesildi), `downtime` (to'xtash), `reject` (brak). Vaqtlar — UTC."""
    __tablename__ = "oee_events"
    __table_args__ = (Index("ix_oee_events_machine_end", "machine_key", "end_ts"),
                      Index("ix_oee_events_machine_start", "machine_key", "start_ts"),
                      UniqueConstraint("company_id", "external_id", name="uq_oee_events_company_ext"))
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = _company_col()
    type = Column(String(10), nullable=False, index=True)
    machine_key = Column(String(64), nullable=False)
    start_ts = Column(DateTime, nullable=True)              # run: ixtiyoriy; downtime: majburiy
    end_ts = Column(DateTime, nullable=True)                # run/reject: majburiy; downtime: bo'sh = hali davom etmoqda
    qty = Column(Integer, nullable=True)                    # run: kesilgan listlar; reject: brak soni
    reject_qty = Column(Integer, nullable=True)             # run: shu hodisadagi brak
    unit = Column(String(10), nullable=True)                # brak birligi: part | sheet
    parts = Column(Integer, nullable=True)                  # run: ishlab chiqarilgan detallar (ma'lum bo'lsa)
    parts_per_sheet = Column(Integer, nullable=True)
    cut_length_m = Column(Float, nullable=True)             # bitta list kesish uzunligi (LT), m
    cuts = Column(Integer, nullable=True)                   # bitta listdagi kesimlar soni (CT)
    sheets_per_pack = Column(Integer, nullable=True)        # paketdagi listlar
    ideal_cycle_s = Column(Float, nullable=True)            # MES bergan ideal sikl (bitta list/birlik), s
    sheet_area_m2 = Column(Float, nullable=True)            # bitta list maydoni, m² (material samaradorligi KPI — OEE dan alohida)
    parts_area_m2 = Column(Float, nullable=True)            # bitta listdagi detallar maydoni, m²
    remnant_area_m2 = Column(Float, nullable=True)          # bitta listdan qolgan деловой qoldiq maydoni, m²
    reason = Column(String(32), nullable=True)
    note = Column(Text, nullable=True)
    project_number = Column(Integer, nullable=True, index=True)
    project_id = Column(String(32), nullable=True)
    op_id = Column(String(32), nullable=True)
    map_index = Column(Integer, nullable=True)
    source = Column(String(20), nullable=True)              # mes | workshop | manual | demo | api
    external_id = Column(String(100), nullable=True)        # idempotentlik kaliti (korxona ichida noyob)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


class OeeConfigRow(Base):
    """OEE sozlamalari (kalit → JSON): `config` (tz_offset_min, idle_gap_s, …), `seeded` (boshlang'ich ma'lumot qo'yilgan)."""
    __tablename__ = "oee_config"
    __table_args__ = (PrimaryKeyConstraint("company_id", "key", name="pk_oee_config"),)
    company_id = Column(Integer, nullable=False, default=tenant.current, server_default=text("1"))
    key = Column(String(50))
    value = Column(JSONT, nullable=True)


# Eski bazalar uchun yetishmagan ustunlar (SQLite/PostgreSQL: ALTER TABLE ... ADD COLUMN)
_CID = "INTEGER NOT NULL DEFAULT 1"
# korxona bilan ajratiladigan jadvallar (PostgreSQL da RLS siyosati shularga qo'yiladi)
TENANT_TABLES = ("folders", "projects", "project_history", "catalog_items", "catalog_images", "settings_profiles", "remnants",
                 "oee_machines", "oee_shifts", "oee_reasons", "oee_events", "oee_config", "jobs")

_MIGRATIONS = {
    **{t: {"company_id": _CID} for t in TENANT_TABLES},
    "projects": {"customer": "VARCHAR(200) DEFAULT ''", "history_cursor": "INTEGER DEFAULT 0", "company_id": _CID},
    "settings_profiles": {"is_default": "BOOLEAN DEFAULT FALSE", "company_id": _CID},
    "catalog_items": {"has_image": "BOOLEAN DEFAULT FALSE", "company_id": _CID},
    "project_history": {"zdata": "BYTEA" if IS_PG else "BLOB", "company_id": _CID},
    "jobs": {"payload": "JSONB" if IS_PG else "JSON", "lang": "VARCHAR(16)", "worker": "VARCHAR(64)", "code": "INTEGER",
             "company_id": _CID},
    "remnants": {"material_name": "VARCHAR(300) DEFAULT ''", "source_number": "INTEGER",
                 "source_op": "VARCHAR(32)", "created_at": "TIMESTAMP", "reserved_project": "VARCHAR(32)",
                 "linear": "BOOLEAN NOT NULL DEFAULT FALSE", "company_id": _CID},
}


def _migrate() -> None:
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in _MIGRATIONS.items():
            if not insp.has_table(table):
                continue
            have = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols.items():
                if name not in have:
                    log.info("migratsiya: %s.%s qo'shildi", table, name)
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def _migrate_declared(prefix: str = "oee_") -> None:
    """Modelda e'lon qilingan, lekin eski jadvalda yo'q ustunlarni qo'shadi (faqat `prefix` jadvallari, faqat NULL bo'lishi
    mumkin ustunlar). Yangi jadvallar `create_all` bilan yaratiladi; bu — keyingi versiyalarda qo'shiladigan ustunlar uchun."""
    insp = inspect(engine)
    tables = [t for t in Base.metadata.sorted_tables if t.name.startswith(prefix) and insp.has_table(t.name)]
    with engine.begin() as conn:
        for t in tables:
            have = {c["name"] for c in insp.get_columns(t.name)}
            for col in t.columns:
                if col.name in have or col.primary_key or not col.nullable:
                    continue
                ddl = col.type.compile(dialect=engine.dialect)
                log.info("migratsiya: %s.%s qo'shildi", t.name, col.name)
                conn.execute(text(f"ALTER TABLE {t.name} ADD COLUMN {col.name} {ddl}"))
    # indekslar va unikal cheklovlar (eski jadvalda bo'lmasligi mumkin): e'lon qilingan indekslar + unique=True ustunlar
    insp = inspect(engine)
    with engine.begin() as conn:
        for t in tables:
            have_idx = {i["name"] for i in insp.get_indexes(t.name)}
            uniq_cols = {tuple(u["column_names"]) for u in insp.get_unique_constraints(t.name)} | \
                {tuple(i["column_names"]) for i in insp.get_indexes(t.name) if i.get("unique")}
            for ix in t.indexes:
                if ix.name not in have_idx:
                    ix.create(conn, checkfirst=True)
            for col in t.columns:
                if col.unique and not col.primary_key and (col.name,) not in uniq_cols:
                    conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS uq_{t.name}_{col.name} ON {t.name} ({col.name})"))
            # jadval darajasidagi noyobliklar (masalan korxona ichida: company_id + external_id)
            for uc in t.constraints:
                if isinstance(uc, UniqueConstraint) and uc.name and tuple(c.name for c in uc.columns) not in uniq_cols:
                    cols = ", ".join(c.name for c in uc.columns)
                    conn.execute(text(f"CREATE UNIQUE INDEX IF NOT EXISTS {uc.name} ON {t.name} ({cols})"))


_RLS_EXPR = ("current_setting('app.sys', true) = '1' "
             "OR company_id = NULLIF(current_setting('app.cid', true), '')::int")


def _rls() -> None:
    """PostgreSQL: har korxona jadvalida Row-Level Security (FORCE — jadval egasi ham bo'ysunadi) va yagona siyosat."""
    with engine.begin() as conn:
        have = {(r[0], r[1]) for r in conn.execute(text("SELECT tablename, policyname FROM pg_policies"))}
        for t in TENANT_TABLES:
            conn.execute(text(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY"))
            conn.execute(text(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY"))
            if (t, "mx_tenant") not in have:
                conn.execute(text(f"CREATE POLICY mx_tenant ON {t} USING ({_RLS_EXPR}) WITH CHECK ({_RLS_EXPR})"))


def ckey(item_id):
    """Katalog qatori kaliti joriy korxonada: `s.get(CatalogItemRow, ckey(id))` (kalit — korxona + id)."""
    return (tenant.current(), item_id)


def _composite_pk() -> None:
    """PostgreSQL: eski bazada katalog kaliti faqat `id` edi → (company_id, id). SQLite (bitta korxona) — o'zgarishsiz
    (model so'rovlari baribir korxona + id bo'yicha)."""
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, col, name in (("catalog_items", "id", "pk_catalog_items"), ("catalog_images", "item_id", "pk_catalog_images")):
            if not insp.has_table(table):
                continue
            pk = insp.get_pk_constraint(table)
            if list(pk.get("constrained_columns") or []) == [col]:
                log.info("migratsiya: %s kaliti → (company_id, %s)", table, col)
                conn.execute(text(f'ALTER TABLE {table} DROP CONSTRAINT "{pk["name"]}"'))
                conn.execute(text(f"ALTER TABLE {table} ADD CONSTRAINT {name} PRIMARY KEY (company_id, {col})"))


def _ensure_company_one() -> None:
    """1-korxona (bizning ishxona) — mavjud ma'lumot shu korxonaniki."""
    with SessionLocal() as s:
        if s.get(CompanyRow, 1) is None:
            s.add(CompanyRow(id=1, name="MebeliX", active=True, plan=""))
            s.commit()
    if IS_PG:
        with engine.begin() as conn:
            conn.execute(text("SELECT setval(pg_get_serial_sequence('companies', 'id'), "
                              "GREATEST((SELECT max(id) FROM companies), 1))"))


def init_db():
    """Sxema: jadvallar, eski bazalar uchun ustunlar, PostgreSQL da RLS. Bir nechta ilova jarayoni bir vaqtda ishga tushsa —
    PostgreSQL advisory lock bilan navbatma-navbat (aks holda ALTER / CREATE bir-biriga to'qnashardi)."""
    with tenant.system():
        lk = engine.connect() if IS_PG else None
        try:
            if lk is not None:
                lk.execute(text("SELECT pg_advisory_lock(727001)"))
                lk.commit()
            Base.metadata.create_all(engine)
            _migrate()
            _migrate_declared()
            _migrate_declared("jobs")
            _ensure_company_one()
            if IS_PG:
                _composite_pk()
                _rls()
        finally:
            if lk is not None:
                lk.execute(text("SELECT pg_advisory_unlock(727001)"))
                lk.commit()
                lk.close()
