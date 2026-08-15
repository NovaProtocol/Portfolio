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
    """Generate the resume PDF on the spot and return it.

    Renders the resume source HTML, inlines images as data URIs, then
    converts to PDF with WeasyPrint (pure Python, no browser). Output
    is a real vector PDF with selectable text — ATS-friendly. Nothing
    is written to disk and no state is kept between requests.
    """
    try:
        import weasyprint
    except ImportError:
        return Response(
            "PDF generation needs WeasyPrint. Install locally: pip install weasyprint",
            status=503,
            mimetype="text/plain",
        )

    html = _inline_images(render_template("resume/source.html", resume=_RESUME))

    pdf_bytes = weasyprint.HTML(string=html).write_pdf()

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=resume.pdf"},
    )