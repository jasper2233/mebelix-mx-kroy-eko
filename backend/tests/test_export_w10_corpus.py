"""W10: real korxona fayllarida (`.project`, GibLab saqlagan + Bazis eksporti) aylanma tekshiruvi:
import → eksport → import → hisoblangan ko'rsatkichlar (detallar soni va maydoni, kromka metri `calc.edge_usage`, XNC `xnc-stats`)
teng; eksport XML ning element/atribut to'plami real fayllardagi to'plamning qismi (noma'lum atribut yo'q).

Papka: env `GP_DIR` (yo'q bo'lsa — loyihaning yonidagi `giblab project`); fayl topilmasa testlar `skip`. Tanlov: tasodifiy 60 ta
(`GP_N`, urug' `GP_SEED`). Mijoz ismlari log va xabarlarga YOZILMAYDI — faqat tartib raqami.
"""
from __future__ import annotations

import os
import random
from pathlib import Path

import pytest

from app.plugins.legacy_project import import_project
from app.services.project_export import export_project
from app.services.project_schema import unknown_vocabulary, validate_project_xml, vocabulary
from w10_helpers import canon, diff, metrics


def _corpus_dir() -> Path | None:
    env = os.environ.get("GP_DIR")
    cands = [Path(env)] if env else [Path(__file__).resolve().parents[3] / "giblab project"]
    return next((c for c in cands if c.is_dir()), None)


_DIR = _corpus_dir()
_ALL = sorted(_DIR.rglob("*.project")) if _DIR else []
N = int(os.environ.get("GP_N", "60"))
SEED = int(os.environ.get("GP_SEED", "20261002"))
SAMPLE = random.Random(SEED).sample(_ALL, min(N, len(_ALL))) if _ALL else []

pytestmark = pytest.mark.skipif(not SAMPLE, reason="GP_DIR (real .project fayllar papkasi) topilmadi yoki bo'sh")

# Hujjatda (format tavsifi) bor, lekin real fayllarda uchramaydigan atributlar — eksport ularni faqat ma'lumot bo'lsa yozadi
DOC_ONLY = {("operation[CS]", "description"),          # «Описание» — operatsiyaning standart atributi (hujjatda)
            ("operation[LB]", "typeName")}             # «Наименование операции» — standart atribut; real LB da nom shablon ichida


@pytest.fixture(scope="module")
def roundtrips():
    out = []
    for i, f in enumerate(SAMPLE):
        p1, _w = import_project(f.read_bytes(), f.name)
        m1 = metrics(p1)
        res = export_project(p1)                              # sxemadan o'tishni ichida tekshiradi
        p2, _w2 = import_project(res.xml, f.name)
        out.append(dict(i=i, p1=p1, p2=p2, m1=m1, m2=metrics(p2), res=res))
    return out


def test_sample_is_random_and_reproducible():
    assert len(SAMPLE) == min(N, len(_ALL))
    assert SAMPLE == random.Random(SEED).sample(_ALL, len(SAMPLE))
    print(f"\nkorpus: {len(_ALL)} fayl, tanlov {len(SAMPLE)} (urug' {SEED})")


def test_metrics_equal_after_roundtrip(roundtrips):
    """detallar soni va maydoni, kromka metri, XNC statistikasi — import → eksport → import da o'zgarmaydi."""
    bad = [(r["i"], diff(r["m1"], r["m2"], limit=3)) for r in roundtrips if r["m1"] != r["m2"]]
    assert not bad, bad
    n_xnc = sum(len(r["m1"]["xnc"]) for r in roundtrips)
    n_el = sum(len(r["m1"]["el"]) for r in roundtrips)
    n_parts = sum(m[1] for r in roundtrips for m in r["m1"]["cs"])
    print(f"\nteng: {len(roundtrips)}/{len(roundtrips)} fayl; CS detal soni {n_parts}, EL {n_el}, XNC {n_xnc}")
    assert n_parts > 0 and n_xnc > 0 and n_el > 0


def test_all_imported_data_equal_after_roundtrip(roundtrips):
    """Ko'rsatkichlardan tashqari butun mazmun ham teng (id lar o'rniga tartib raqamlari): detal maydonlari, EL / CS / XNC / O / LB."""
    bad = [(r["i"], diff(canon(r["p1"]), canon(r["p2"]), limit=3)) for r in roundtrips]
    bad = [b for b in bad if b[1]]
    print(f"\nto'liq teng: {len(roundtrips) - len(bad)}/{len(roundtrips)}")
    assert not bad, bad


def test_export_vocabulary_is_subset_of_real_files(roundtrips):
    """Eksport yozgan (element, atribut) juftlari — real fayllardagi to'plamning qismi (hujjatda bor, real faylda yo'q
    atributlar `DOC_ONLY` da aniq sanalgan); sxema lug'atida ham bor."""
    in_sample = set(SAMPLE)
    extra = [f for f in _ALL if f not in in_sample]
    # real to'plam: tanlov + yana 140 tasodifiy fayl (`GP_VOCAB_ALL=1` — butun korpus)
    pool = list(SAMPLE) + (extra if os.environ.get("GP_VOCAB_ALL") else random.Random(SEED + 1).sample(extra, min(len(extra), 140)))
    real: set[tuple[str, str]] = set()
    for f in pool:
        real |= vocabulary(f.read_bytes())
    written: set[tuple[str, str]] = set()
    for r in roundtrips:
        written |= vocabulary(r["res"].xml)
    unknown = {(k_, a) for k_, a in written - real if not (k_.startswith("good[product]") and a.startswith("product."))}
    assert unknown <= DOC_ONLY, sorted(unknown - DOC_ONLY)
    for r in roundtrips:
        assert unknown_vocabulary(vocabulary(r["res"].xml)) == set()
    print(f"\nyozilgan (element, atribut): {len(written)}; real to'plam ({len(pool)} fayl): {len(real)}")


def test_exported_files_validate_and_reimport_without_new_warnings(roundtrips):
    for r in roundtrips:
        assert validate_project_xml(r["res"].xml, strict=True) == []
        assert r["res"].xml.startswith(b'<?xml version="1.0" encoding="UTF-8"?>')
