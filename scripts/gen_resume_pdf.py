#!/usr/bin/env python3
"""Regenerate static/assets/images/resume.pdf from the resume source HTML.

The resume page embeds a pre-generated PDF in an iframe. Run this after
editing data/resume.json or apps/resume/templates/resume/source.html:

    DEPLOYMENT_TYPE=DEBUG python scripts/gen_resume_pdf.py

Captures each on-screen A4 sheet at 2x DPI via Playwright and places
them on full-page PDFs, so the PDF is a pixel-perfect copy of the
on-screen rendering (same fonts, same line breaks).
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DEPLOYMENT_TYPE", "DEBUG")

from PIL import Image  # noqa: E402

import pymupdf  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

STATIC_DIR = ROOT / "static"
OUT = STATIC_DIR / "assets" / "images" / "resume.pdf"

_STRIP_CSS = """
    .navbar, .footer, .save-btn,
    .resume-page > .container > .text-center { display: none !important; }
    .resume-page { padding: 0 !important; background: #fff !important; }
    .resume-page > .container { max-width: none !important; padding: 0 !important; margin: 0 !important; }
    .resume-pages { gap: 0 !important; margin: 0 !important; }
    main { padding: 0 !important; }
    #resume-source { display: none !important; }
"""


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
        page = browser.new_page(
            viewport={"width": 794, "height": 1123},
            device_scale_factor=2,
        )
        page.emulate_media(media="screen")
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(4000)
        page.add_style_tag(content=_STRIP_CSS)
        page.wait_for_timeout(500)

        sheets = page.locator(".resume-sheet")
        count = sheets.count()
        if count == 0:
            browser.close()
            raise SystemExit("ERROR: no resume sheets rendered")

        with tempfile.TemporaryDirectory() as tmp:
            jpg_files = []
            for i in range(count):
                png = f"{tmp}/sheet_{i}.png"
                sheets.nth(i).screenshot(path=png)
                jpg = f"{tmp}/sheet_{i}.jpg"
                Image.open(png).convert("RGB").save(jpg, quality=90)
                jpg_files.append(jpg)

            pdf = pymupdf.open()
            for jpg in jpg_files:
                page_rect = pdf.new_page(width=595.28, height=841.89)
                page_rect.insert_image(page_rect.rect, filename=jpg)
            pdf.save(str(OUT), deflate=True, garbage=4)
            pdf.close()

        browser.close()

    print(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes, {count} pages)")


if __name__ == "__main__":
    main()
