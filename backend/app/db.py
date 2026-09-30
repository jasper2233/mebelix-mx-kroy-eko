"""Saqlash qatlami (SQLAlchemy). Standart — SQLite, prod uchun PostgreSQL:
   MEBELIX_DB_URL=postgresql+psycopg://user:pass@host/mebelix

Loyiha to'liq JSON hujjat sifatida saqlanadi (GibLab loyiha fayli kabi) —
bu MES ga moslashni osonlashtiradi. Ro'yxat/qidiruv uchun ustunlar alohida.
"""
from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import (JSON, Column, DateTime, Float, ForeignKey, Integer, String,
                        Text, create_engine)
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = os.getenv("MEBELIX_DB_URL", "sqlite:///./mebelix_kroy.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
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
    """Standart parametrlar va chop profillari (KROYGA, Standart, Uslugiya...)."""
    __tablename__ = "settings_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String(50), index=True)   # cs_defaults | el_defaults | print | part_columns
    name = Column(String(100))
    data = Column(JSON)


class RemnantRow(Base):
    """Ombordagi qoldiqlar (kroydan keyin avtomatik qo'shiladi)."""
    __tablename__ = "remnants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(100), index=True)
    length = Column(Float); width = Column(Float); thickness = Column(Float)
    qty = Column(Integer, default=1)
    source_project = Column(String(32), nullable=True)
    note = Column(Text, default="")


def init_db():
    Base.metadata.create_all(engine)
