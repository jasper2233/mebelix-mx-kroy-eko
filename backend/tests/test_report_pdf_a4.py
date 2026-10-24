"""«Печать отчета»: hisobot A4 PDF (sahifalar, kolontitul «Проект: nom» / «Страница N») — WeasyPrint yoki Chrome / Edge bilan."""
import pytest

from app.services import pdf_render


def test_report_pdf_a4(client, kravat):
    pid, _cs, _el = kravat
    if pdf_render.chrome_path() is None:
        r = client.get(f"/api/projects/{pid}/report.pdf")
        assert r.status_code in (200, 501)
        pytest.skip("PDF dvigateli yo'q")
    r = client.get(f"/api/projects/{pid}/report.pdf?inline=true")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-" and r.headers["content-disposition"].startswith("inline")
    ps = client.get("/api/settings/print/default").json()
    r2 = client.post(f"/api/projects/{pid}/report.pdf", json=ps)
    assert r2.status_code == 200 and r2.content[:5] == b"%PDF-"


def test_report_footer_css(client, kravat):
    pid, _cs, _el = kravat
    html = client.get(f"/api/projects/{pid}/report").text
    assert "@bottom-left" in html and "@bottom-right" in html and "Страница" in html
