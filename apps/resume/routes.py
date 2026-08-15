from __future__ import annotations

import base64
import json
import logging
import re
from pathlib import Path

from flask import Response, render_template

from apps.resume import blueprint

_RESUME_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "resume.json"
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

logger = logging.getLogger(__name__)

# CSS injected into the page before PDF generation to strip the
# screen-only chrome so the A4 sheets fill the entire PDF page.
_PRINT_STRIP_CSS = """
    .navbar, .footer, .save-btn,
    .resume-page > .container > .text-center { display: none !important; }
    .resume-page { padding: 0 !important; background: #fff !important; }
    .resume-page > .container { padding: 0 !important; max-width: none !important; margin: 0 !important; }
    .resume-pages { gap: 0 !important; margin: 0 !important; }
    main { padding: 0 !important; }
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

    Uses Playwright (local dev only). In production without Chromium
    installed, returns a 503 so the button degrades gracefully.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return Response(
            "PDF generation requires Playwright. Install it locally: pip install playwright && playwright install chromium",
            status=503,
            mimetype="text/plain",
        )

    html = render_template("resume/index.html", resume=_RESUME)
    html = _inline_images(html)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.emulate_media(media="screen")
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(4000)
        page.add_style_tag(content=_PRINT_STRIP_CSS)
        page.wait_for_timeout(500)
        pdf_bytes = page.pdf(
            width="210mm",
            height="297mm",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        browser.close()

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=resume.pdf"},
    )