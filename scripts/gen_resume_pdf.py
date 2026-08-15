#!/usr/bin/env python3
"""Regenerate static/assets/images/resume.pdf from the resume source HTML.

The resume page shows the PDF natively in an iframe, so the PDF must
contain real, selectable text. Run after editing data/resume.json or
source.html:

    DEPLOYMENT_TYPE=DEBUG python scripts/gen_resume_pdf.py

Uses Playwright's page.pdf() with the source's @media print CSS, which
flows content naturally across A4 pages (page-break-inside: avoid) and
keeps text as selectable vector text.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DEPLOYMENT_TYPE", "DEBUG")

from playwright.sync_api import sync_playwright  # noqa: E402

STATIC_DIR = ROOT / "static"
OUT = STATIC_DIR / "assets" / "images" / "resume.pdf"


def _img_to_data_uri(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
    }.get(suffix, "application/octet-stream")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _inline_images(html: str) -> str:
    pattern = re.compile(r'src="(/static/([^"]+))"')

    def replace(match: re.Match) -> str:
        static_path = match.group(2)
        file_path = STATIC_DIR / static_path
        if file_path.is_file():
            return f'src="{_img_to_data_uri(file_path)}"'
        return match.group(0)

    return pattern.sub(replace, html)


def render_source() -> str:
    from apps import create_app
    from apps.config import DebugConfig

    app = create_app(DebugConfig)
    with app.test_request_context("/"):
        from flask import render_template

        resume = json.loads((ROOT / "data" / "resume.json").read_text())
        return render_template("resume/source.html", resume=resume)


def main() -> None:
    html = _inline_images(render_source())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(2000)
        # page.pdf() applies @media print and emits real selectable text.
        pdf_bytes = page.pdf(format="A4", print_background=True)
        browser.close()

    OUT.write_bytes(pdf_bytes)
    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
