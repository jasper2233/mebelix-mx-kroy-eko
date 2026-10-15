"""Saqlash qatlami (SQLAlchemy). Standart — SQLite, prod uchun PostgreSQL:
   MEBELIX_DB_URL=postgresql+psycopg://user:pass@host/mebelix

Loyiha to'liq JSON hujjat sifatida saqlanadi — bu MES ga moslashni osonlashtiradi.
Ro'yxat/qidiruv uchun ustunlar alohida.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text,
                        create_engine, event, false, func, inspect, or_, text)
from sqlalchemy.orm import declarative_base, sessionmaker

log = logging.getLogger("mebelix.db")

DB_URL = os.getenv("MEBELIX_DB_URL", "sqlite:///./mebelix_kroy.db")
IS_SQLITE = DB_URL.startswith("sqlite")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if IS_SQLITE else {},
                       pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


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


class FolderRow(Base):
    __tablename__ = "folders"
    id = Column(String(32), primary_key=True)
    parent_id = Column(String(32), ForeignKey("folders.id"), nullable=True)
    name = Column(String(200), nullable=False)
    owner = Column(String(100), default="")


class ProjectRow(Base):
    __tablename__ = "projects"
    id = Column(String(32), primary_key=True)
    number = Column(Integer, unique=True, index=True)       # Заказ ID
    folder_id = Column(String(32), ForeignKey("folders.id"), nullable=True, index=True)
    name = Column(String(300), index=True)
    owner = Column(String(100), default="")
    status = Column(Integer, default=0)
    order_date = Column(String(10))
    cost = Column(Float, default=0)
    mes_order_ref = Column(String(100), index=True, nullable=True)
    customer = Column(String(200), default="")
    history_cursor = Column(Integer, default=0)             # undo/redo ko'rsatkichi (joriy versiya)
    data = Column(JSON, nullable=False)                     # to'liq Project JSON
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectHistoryRow(Base):
    """Отменить/Вернуть (undo/redo) uchun versiyalar."""
    __tablename__ = "project_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(32), ForeignKey("projects.id"), index=True)
    version = Column(Integer)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class CatalogItemRow(Base):
    """Каталог товаров — MES ombor/tovarlar bilan sinxronlanadi."""
    __tablename__ = "catalog_items"
    id = Column(String(64), primary_key=True)
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
    params = Column(JSON, default=dict)   # grain, kerf, trim, ...
    has_image = Column(Boolean, default=False)   # rasm `catalog_images` jadvalida (ro'yxatga og'ir matn chiqmasin)


class CatalogImageRow(Base):
    """Material rasmi: tekshirilgan `data:image/…;base64,…` URI yoki `http(s)://` havola (services/catalog.py)."""
    __tablename__ = "catalog_images"
    item_id = Column(String(64), primary_key=True)
    data = Column(Text, nullable=False)


class SettingsProfileRow(Base):
    """Standart parametrlar va profillar: cs_defaults | el_defaults | print | labels | part_columns | postprocessor | app."""
    __tablename__ = "settings_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String(50), index=True)
    name = Column(String(100))
    data = Column(JSON)
    is_default = Column(Boolean, default=False)


class RemnantRow(Base):
    """Ombordagi qoldiqlar (деловые остатки): kroydan keyin tasdiq bilan qo'shiladi, keyingi kroyda ishlatiladi."""
    __tablename__ = "remnants"
    __table_args__ = {"sqlite_autoincrement": True}     # o'chirilgan qoldiq raqami qayta berilmasin
    id = Column(Integer, primary_key=True, autoincrement=True)
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


# ───────────────────────── OEE va ishlab chiqarish analitikasi (W17) ─────────────────────────
# Barcha vaqtlar — UTC (naive datetime sifatida saqlanadi); smena soatlari esa zavod mahalliy vaqtida (`oee_config.tz_offset_min`).
def _utc_now() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)



class OeeMachineRow(Base):
    """OEE stanogi: `key` — postprotsessor stanoklari (`postprocessors.MACHINES`) kaliti yoki erkin; ideal tezlik parametrlari."""
    __tablename__ = "oee_machines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False)
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
    kind = Column(String(10), default="shift")
    machine_key = Column(String(64), nullable=True, index=True)    # NULL — hamma stanoklar uchun
    name = Column(String(100), default="")
    weekdays = Column(JSON, nullable=True)                  # [0..6], 0 = dushanba
    start_time = Column(String(5), nullable=True)           # «HH:MM» (mahalliy)
    end_time = Column(String(5), nullable=True)             # tugash ≤ boshlanish bo'lsa — yarim tundan o'tadi
    breaks = Column(JSON, nullable=True)                    # [{start, end, name}] — rejalashtirilgan to'xtash
    valid_from = Column(String(10), nullable=True)          # YYYY-MM-DD (mahalliy sana), ixtiyoriy
    valid_to = Column(String(10), nullable=True)
    active = Column(Boolean, default=True)


class OeeReasonRow(Base):
    """To'xtash / brak sabab kodlari (sozlanadigan ro'yxat). `planned` — rejalashtirilgan to'xtash (rejalashtirilgan vaqtdan chiqariladi)."""
    __tablename__ = "oee_reasons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False)
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
                      Index("ix_oee_events_machine_start", "machine_key", "start_ts"))
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    external_id = Column(String(100), unique=True, nullable=True)   # idempotentlik kaliti
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


class OeeConfigRow(Base):
    """OEE sozlamalari (kalit → JSON): `config` (tz_offset_min, idle_gap_s, …), `seeded` (boshlang'ich ma'lumot qo'yilgan)."""
    __tablename__ = "oee_config"
    key = Column(String(50), primary_key=True)
    value = Column(JSON, nullable=True)


# Eski bazalar uchun yetishmagan ustunlar (SQLite/PostgreSQL: ALTER TABLE ... ADD COLUMN)
_MIGRATIONS = {
    "projects": {"customer": "VARCHAR(200) DEFAULT ''", "history_cursor": "INTEGER DEFAULT 0"},
    "settings_profiles": {"is_default": "BOOLEAN DEFAULT FALSE"},
    "catalog_items": {"has_image": "BOOLEAN DEFAULT FALSE"},
    "remnants": {"material_name": "VARCHAR(300) DEFAULT ''", "source_number": "INTEGER",
                 "source_op": "VARCHAR(32)", "created_at": "TIMESTAMP", "reserved_project": "VARCHAR(32)",
                 "linear": "BOOLEAN NOT NULL DEFAULT FALSE"},
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


def init_db():
    Base.metadata.create_all(engine)
    _migrate()
    _migrate_declared()
