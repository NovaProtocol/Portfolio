from __future__ import annotations

import base64
import io
import json
import logging
import re
import tempfile
from pathlib import Path

from flask import Response, render_template

from apps.resume import blueprint

_RESUME_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "resume.json"
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

logger = logging.getLogger(__name__)

# CSS injected to strip screen-only chrome so only the A4 resume
# sheets remain, ready to capture one per page.
_STRIP_CSS = """
    .navbar, .footer, .save-btn,
    .resume-page > .container > .text-center { display: none !important; }
    .resume-page { padding: 0 !important; background: #fff !important; }
    .resume-page > .container { max-width: none !important; padding: 0 !important; margin: 0 !important; }
    .resume-pages { gap: 0 !important; margin: 0 !important; }
    main { padding: 0 !important; }
    #resume-source { display: none !important; }
"""


def _load_resume() -> dict:
    try:
        return json.loads(_RESUME_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        logger.exception("Failed to load resume data from %s", _RESUME_PATH)
        return {}


_RESUME = _load_resume()


def _img_to_data_uri(path: Path) -> str:
    """Convert an image file to a base64 data URI."""
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
    """Replace all /static/... image srcs with base64 data URIs."""
    pattern = re.compile(r'src="(/static/([^"]+))"')

    def replace(match: re.Match) -> str:
        static_path = match.group(2)
        file_path = _STATIC_DIR / static_path
        if file_path.is_file():
            return f'src="{_img_to_data_uri(file_path)}"'
        return match.group(0)

    return pattern.sub(replace, html)


@blueprint.route("/")
def index():
    return render_template("resume/index.html", resume=_RESUME)


@blueprint.route("/pdf")
def pdf():
    """Generate a PDF that is a 1:1 copy of the on-screen resume.

    Each on-screen A4 sheet is captured as an image (pixel-perfect:
    same fonts, same line breaks) and placed on a PDF page. This is
    the only way to guarantee the PDF matches the browser view
    exactly, because browser print re-layouts text differently.

    Uses Playwright (local dev only).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return Response(
            "PDF generation needs Playwright. Install locally: "
            "pip install playwright && playwright install chromium",
            status=503,
            mimetype="text/plain",
        )

    try:
        import pymupdf
    except ImportError:
        return Response(
            "PDF generation needs pymupdf. Install locally: pip install pymupdf",
            status=503,
            mimetype="text/plain",
        )

    html = render_template("resume/index.html", resume=_RESUME)
    html = _inline_images(html)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # A4 size at 96dpi with 2x scale for crisp text.
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
            return Response("Could not render resume sheets.", status=500)

        image_files = []
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(count):
                img_path = f"{tmp}/sheet_{i}.png"
                sheets.nth(i).screenshot(path=img_path)
                image_files.append(img_path)

            pdf_doc = pymupdf.open()
            for img_path in image_files:
                # Compress to JPEG to keep the file small.
                from PIL import Image

                im = Image.open(img_path).convert("RGB")
                jpg_path = img_path.rsplit(".", 1)[0] + ".jpg"
                im.save(jpg_path, quality=90)
                page_rect = pdf_doc.new_page(width=595.28, height=841.89)
                page_rect.insert_image(page_rect.rect, filename=jpg_path)

            pdf_bytes = pdf_doc.tobytes(deflate=True, garbage=4)
            pdf_doc.close()

        browser.close()

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=resume.pdf"},
    )