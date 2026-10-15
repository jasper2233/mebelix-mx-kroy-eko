"""Import plaginlari («Импорт из других программ»).

Har plagin foydalanuvchining O'Z ma'lumot faylini o'qib, MebeliX loyihasiga aylantiradi (faqat o'qish).
MebeliX ning o'z formati — `.mxk.json`; boshqa formatlar faqat import uchun.
Plagin funksiyasi: (fayl baytlari, fayl nomi) → (Project, ogohlantirishlar ro'yxati).

Ro'yxatga olish (W18): `@register(".fxm", "Imos (fxm)", key="imos")` — `key` `services/import_formats.CATALOG` dagi format kaliti
(dialog formatni shu kalit bilan tanlaydi, shuning uchun bir xil kengaytma — `.xml` — bir necha formatga tegishli bo'lishi mumkin:
`exts=(".xml",), by_ext=False`). Parametrlar (profil) plaginga `services.import_formats.option("kalit", standart)` orqali keladi.
Yangi importer qo'shish yo'li — `docs/mebelix/T_W18_IMPORT_INFRA.md`.
"""
from __future__ import annotations

from typing import Callable

from ..models import Project

Importer = Callable[[bytes, str], tuple[Project, list[str]]]

# kengaytma → (nomi, funksiya) — `find(filename)` shuni ishlatadi (eski yo'l: /projects/import-file)
REGISTRY: dict[str, tuple[str, Importer]] = {}
# format kaliti → (nomi, funksiya, kengaytmalar) — «Импорт из других программ» dialogi shuni ishlatadi
BY_KEY: dict[str, tuple[str, Importer, tuple[str, ...]]] = {}


def register(ext: str, title: str, *, key: str | None = None, exts: tuple[str, ...] | None = None, by_ext: bool = True):
    """`ext` — asosiy kengaytma; `key` — dialogdagi format kaliti; `exts` — format qabul qiladigan hamma kengaytmalar;
    `by_ext=False` — kengaytma bo'yicha avtomatik tanlanmasin (bir xil kengaytma bir necha formatda: faqat dialog orqali)."""
    def deco(fn: Importer) -> Importer:
        all_exts = tuple(e.lower() for e in (exts or ((ext,) if ext else ())))
        if ext and by_ext:
            REGISTRY[ext.lower()] = (title, fn)
        if key:
            BY_KEY[key] = (title, fn, all_exts)
        return fn
    return deco


def find(filename: str) -> tuple[str, Importer] | None:
    low = (filename or "").lower()
    for ext, v in REGISTRY.items():
        if low.endswith(ext):
            return v
    return None


def by_key(key: str) -> tuple[str, Importer, tuple[str, ...]] | None:
    return BY_KEY.get(key)


def formats() -> list[dict]:
    return [dict(ext=ext, title=title) for ext, (title, _fn) in REGISTRY.items()]


from . import legacy_project  # noqa: E402,F401  (ro'yxatga olish)
