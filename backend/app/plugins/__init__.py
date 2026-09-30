"""Import plaginlari («Импорт из других программ»).

Har plagin foydalanuvchining O'Z ma'lumot faylini o'qib, MebeliX loyihasiga aylantiradi (faqat o'qish).
MebeliX ning o'z formati — `.mxk.json`; boshqa formatlar faqat import uchun.
Plagin funksiyasi: (fayl baytlari, fayl nomi) → (Project, ogohlantirishlar ro'yxati).
"""
from __future__ import annotations

from typing import Callable

from ..models import Project

Importer = Callable[[bytes, str], tuple[Project, list[str]]]

# kengaytma → (nomi, funksiya)
REGISTRY: dict[str, tuple[str, Importer]] = {}


def register(ext: str, title: str):
    def deco(fn: Importer) -> Importer:
        REGISTRY[ext.lower()] = (title, fn)
        return fn
    return deco


def find(filename: str) -> tuple[str, Importer] | None:
    low = (filename or "").lower()
    for ext, v in REGISTRY.items():
        if low.endswith(ext):
            return v
    return None


def formats() -> list[dict]:
    return [dict(ext=ext, title=title) for ext, (title, _fn) in REGISTRY.items()]


from . import legacy_project  # noqa: E402,F401  (ro'yxatga olish)
