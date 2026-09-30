"""Saqlash qatlami (SQLAlchemy). Standart — SQLite, prod uchun PostgreSQL:
   MEBELIX_DB_URL=postgresql+psycopg://user:pass@host/mebelix

Loyiha to'liq JSON hujjat sifatida saqlanadi — bu MES ga moslashni osonlashtiradi.
Ro'yxat/qidiruv uchun ustunlar alohida.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
                        create_engine, inspect, text)
from sqlalchemy.orm import declarative_base, sessionmaker

log = logging.getLogger("mebelix.db")

DB_URL = os.getenv("MEBELIX_DB_URL", "sqlite:///./mebelix_kroy.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
                       pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


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


# Eski bazalar uchun yetishmagan ustunlar (SQLite/PostgreSQL: ALTER TABLE ... ADD COLUMN)
_MIGRATIONS = {
    "projects": {"customer": "VARCHAR(200) DEFAULT ''", "history_cursor": "INTEGER DEFAULT 0"},
    "settings_profiles": {"is_default": "BOOLEAN DEFAULT FALSE"},
    "remnants": {"material_name": "VARCHAR(300) DEFAULT ''", "source_number": "INTEGER",
                 "source_op": "VARCHAR(32)", "created_at": "TIMESTAMP"},
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


def init_db():
    Base.metadata.create_all(engine)
    _migrate()
