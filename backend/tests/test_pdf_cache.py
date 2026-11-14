# -*- coding: utf-8 -*-
"""PDF keshi (2026-11-14): bir xil hisobot HTML i uchun PDF qayta yasalmaydi; Chrome teglarsiz (kichik PDF) chaqiriladi;
xeshli frontend fayllari brauzerda uzoq keshlanadi."""
from app.services import pdf_render


def test_same_html_built_once(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_render, "PDF_CACHE_DIR", tmp_path)
    calls = []
    monkeypatch.setattr(pdf_render, "_html_to_pdf", lambda h, t: calls.append(h) or b"%PDF-1.4 " + h.encode())
    a = pdf_render.html_to_pdf("<p>1</p>")
    b = pdf_render.html_to_pdf("<p>1</p>")
    c = pdf_render.html_to_pdf("<p>2</p>")
    assert a == b and a != c and calls == ["<p>1</p>", "<p>2</p>"]


def test_cache_trimmed(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_render, "PDF_CACHE_DIR", tmp_path)
    monkeypatch.setattr(pdf_render, "PDF_CACHE_MAX_FILES", 3)
    monkeypatch.setattr(pdf_render, "_html_to_pdf", lambda h, t: b"%PDF " + h.encode())
    for i in range(6):
        pdf_render.html_to_pdf(f"<p>{i}</p>")
    assert len(list(tmp_path.glob("*.pdf"))) == 3


def test_failed_pdf_not_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_render, "PDF_CACHE_DIR", tmp_path)
    monkeypatch.setattr(pdf_render, "_html_to_pdf", lambda h, t: None)
    assert pdf_render.html_to_pdf("<p>x</p>") is None and not list(tmp_path.glob("*.pdf"))


def test_chrome_without_tagging(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(pdf_render, "chrome_path", lambda: "chrome")
    monkeypatch.setitem(__import__("sys").modules, "weasyprint", None)

    def run(cmd, **kw):
        seen["cmd"] = cmd
        raise OSError
    monkeypatch.setattr(pdf_render.subprocess, "run", run)
    assert pdf_render._html_to_pdf("<p/>", 5) is None
    assert "--disable-pdf-tagging" in seen["cmd"] and any(c.startswith("--user-data-dir=") for c in seen["cmd"])


def test_hashed_assets_long_cache(client):
    import re
    html = client.get("/").text
    m = re.search(r'/assets/[^"]+\.js', html)
    if not m:
        return                                  # frontend yig'ilmagan muhit
    r = client.get(m.group(0))
    assert r.status_code == 200 and "immutable" in r.headers.get("cache-control", "")
