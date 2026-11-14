# «Печать отчета» → «Скачать PDF» va «Страницы» (2026-11-14, foydalanuvchi talabi): chop etishda keraksiz varaqlar chiqmasin —
# tayyor hisobot PDF dan faqat tanlangan sahifalar (`POST /api/pdf/select-pages`).
import io

import pytest
from pypdf import PdfReader, PdfWriter

from app.services.pdf_render import parse_pages, select_pages


def _pdf(n: int) -> bytes:
    w = PdfWriter()
    for i in range(n):
        w.add_blank_page(width=100 + i, height=100)      # sahifani eniga qarab taniymiz
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()


def _widths(pdf: bytes) -> list[int]:
    return [int(float(p.mediabox.width)) - 100 for p in PdfReader(io.BytesIO(pdf)).pages]


def test_parse_pages():
    assert parse_pages("", 4) == [0, 1, 2, 3]
    assert parse_pages("1-2, 4", 5) == [0, 1, 3]
    assert parse_pages("3-", 5) == [2, 3, 4]
    assert parse_pages("2;2,1", 3) == [1, 0]
    for bad in ("0", "6", "3-2", "a", "1-x"):
        with pytest.raises(ValueError):
            parse_pages(bad, 5)


def test_select_pages_keeps_only_chosen():
    assert _widths(select_pages(_pdf(6), "1, 3-4")) == [0, 2, 3]


def test_endpoint(client):
    r = client.post("/api/pdf/select-pages?pages=2-3&name=1000187 Muzaffar", content=_pdf(5),
                    headers={"Content-Type": "application/pdf"})
    assert r.status_code == 200, r.text
    assert r.headers["x-pages"] == "2" and r.headers["x-pages-total"] == "5"
    assert "attachment" in r.headers["content-disposition"]
    assert _widths(r.content) == [1, 2]
    bad = client.post("/api/pdf/select-pages?pages=9", content=_pdf(3), headers={"Content-Type": "application/pdf"})
    assert bad.status_code == 400
    assert client.post("/api/pdf/select-pages", content=b"hello").status_code == 400
