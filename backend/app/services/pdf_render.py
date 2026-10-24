"""Hisobot HTML → A4 PDF (sahifalarga bo'lingan, kolontitulli) — «Печать отчета» ko'rinishi to'g'ridan-to'g'ri chop uchun.

Dvigatel tartibi: WeasyPrint (o'rnatilgan bo'lsa) → shu kompyuterdagi Chrome / Edge (headless `--print-to-pdf`; `@page`
o'lchami, chegaralari va kolontitul bloklari hurmat qilinadi). Brauzer yo'li: `MEBELIX_CHROME` yoki odatiy o'rnatish joylari.
Hech biri bo'lmasa — `None` (chaqiruvchi HTML ko'rinishga qaytadi).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
)


def chrome_path() -> Optional[str]:
    env = os.getenv("MEBELIX_CHROME", "").strip()
    if env and Path(env).exists():
        return env
    for c in _CANDIDATES:
        if Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    return None


def html_to_pdf(html: str, timeout: float = 90.0) -> Optional[bytes]:
    try:
        from weasyprint import HTML  # type: ignore
        return HTML(string=html).write_pdf()
    except Exception:  # noqa: BLE001 — o'rnatilmagan / ishlamadi — Chrome bilan urinamiz
        pass
    exe = chrome_path()
    if not exe:
        return None
    with tempfile.TemporaryDirectory(prefix="mxpdf_") as tmp:
        src, out = Path(tmp) / "report.html", Path(tmp) / "report.pdf"
        src.write_text(html, encoding="utf-8")
        cmd = [exe, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", "--no-pdf-header-footer", f"--user-data-dir={Path(tmp) / 'profile'}",
               f"--print-to-pdf={out}", src.as_uri()]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        if out.exists() and out.stat().st_size > 0:
            return out.read_bytes()
    return None
