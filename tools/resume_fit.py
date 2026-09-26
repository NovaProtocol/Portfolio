#!/usr/bin/env python3
"""Render the resume pages and measure how much of each A4 page they fill.

The resume is two fixed-size A4 pages with `overflow: hidden`, so content that
grows past the box is silently invisible rather than spilling. That makes "does
it still fit" a question worth being able to answer, and it is the kind of
question a template change can get wrong without any test noticing.

Measurement is approximate by design: it computes the height of the rendered
blocks from the same CSS the template uses, rather than launching a browser. It
is accurate enough to say "this grew by a third of a page", which is the signal
that matters. `dashboard/check-pages.mjs` in ServerDashboard is where a real
browser is used.

Usage:
    .venv/bin/python tools/resume_fit.py            # both pages
    .venv/bin/python tools/resume_fit.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402

# A4 at 96 dpi, minus the 13mm/18mm padding the template applies. Must match
# `page1.html`/`page2.html`: when the template was 15mm this said 15mm, and the
# figure is only worth having if the two agree.
PAGE_H_PX = 297 * 96 / 25.4          # 1122.5
PAD_V_PX = 2 * 13 * 96 / 25.4        # 98.3
USABLE_H = PAGE_H_PX - PAD_V_PX      # ~1024 px

# Base font is 11px with a 1.42 line height.
LINE = 11 * 1.42                     # ~15.6 px


def make_env() -> Environment:
    """The same search path the app builds, so a template that renders here
    renders there. `apps/templating.py` lists four directories and the resume
    pages include `resume/_theme.html` from the third.

    `url_for` comes from the app's own mapping rather than a stub, so the
    template's `{{ url_for('static', ...) }}` calls behave as they do in
    production instead of being papered over.
    """
    from apps.templating import _url_for

    env = Environment(
        loader=FileSystemLoader([
            str(ROOT / "apps" / "templates"),
            str(ROOT / "apps" / "home" / "templates"),
            str(ROOT / "apps" / "projects" / "templates"),
            str(ROOT / "apps" / "resume" / "templates"),
        ]),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["url_for"] = _url_for
    return env


def fold(text: str, chars: int = 118) -> int:
    """How many rendered lines a string occupies, wrapped at `chars`."""
    import textwrap

    if not text:
        return 0
    return len(textwrap.wrap(text, chars)) or 1


# Which blocks each page template renders, so a page is measured against its own
# content rather than against every block in the data. Getting this wrong is not
# a small error: summing page 1's blocks into page 2 made both pages report the
# same 168%, and "both pages are equally overflowing" is worse than no figure.
PAGE_BLOCKS = {
    1: ("header", "summary", "education", "coursework", "certifications", "experience"),
    2: ("projects", "skills"),
}


def _header(resume: dict) -> float:
    """The name block and the photo, whichever is taller.

    The photo is a fixed 90px and sits beside the text rather than above it, so a
    resume with a long contact block is measured by the text and one with a short
    block by the photo. Counting the text alone overstates the second case, and
    the first draft of this also counted a line the photo covers.
    """
    contact = resume.get("contact") or {}
    lines = 1                                   # the address, always present
    lines += sum(
        1 for key in ("phone", "email", "linkedin", "github", "portfolio")
        if contact.get(key)
    )
    who = 26 + (14 if resume.get("headline") else 0) + lines * 13.5
    photo = 90 if resume.get("photo") else 0
    return max(who, photo) + 24                 # bottom padding and the rule


def measure(page: int, resume: dict) -> dict:
    """Approximate the height of one page's blocks.

    Counted per element type from the data rather than parsed out of the HTML,
    because the numbers that matter are the list lengths and string lengths, and
    they are already in hand.
    """
    detail: dict[str, float] = {}

    if page == 1:
        detail["header"] = _header(resume)

        detail["summary"] = 14 + fold(resume.get("summary", "")) * LINE + 12

        e = 14
        for edu in resume.get("education", []):
            e += 16 + 15.6 + (15.6 if edu.get("status") else 0)
            e += len(edu.get("awards", [])) * 15.6
            e += 10
        detail["education"] = e + 10

        cw = resume.get("coursework") or []
        if cw:
            detail["coursework"] = 14 + fold(" · ".join(cw)) * LINE + 12

        c = 14
        for cert in resume.get("certifications", []):
            c += 16 + 15.6 + (15.6 if cert.get("detail") else 0) + 10
        detail["certifications"] = c + 8

        x = 14
        for job in resume.get("experience", []):
            x += 16 + 15.6 + (15.6 if job.get("role") else 0)
            for item in job.get("responsibilities", []):
                x += fold("• " + item, 112) * 15.6
            x += 10
        detail["experience"] = x + 8

    elif page == 2:
        if resume.get("projects"):
            p = 14 + 2 * LINE            # the heading and the intro paragraph
            for proj in resume.get("projects", []):
                p += 16
                if proj.get("tech"):
                    p += 13.5
                if proj.get("status_line"):
                    p += 13.5
                if proj.get("url"):
                    p += 13.5
                for item in proj.get("highlights", []):
                    p += fold("• " + item, 112) * 15.6
                p += 10
            detail["projects"] = p + 8

        detail["skills"] = 14 + len(resume.get("skills", [])) * (LINE + 6.4) + 8

    else:
        raise ValueError(f"no page {page}")

    stray = set(detail) - set(PAGE_BLOCKS[page])
    if stray:
        raise AssertionError(f"page {page} measured unknown blocks: {sorted(stray)}")

    px = sum(detail.values())
    return {"height_px": round(px, 1), "usable_px": round(USABLE_H, 1),
            "fill": round(px / USABLE_H * 100, 1), "blocks": detail}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--page", type=int, choices=[1, 2])
    args = ap.parse_args()

    resume = json.loads((ROOT / "data" / "resume.json").read_text())
    env = make_env()

    pages = [1, 2] if not args.page else [args.page]
    out = {}
    for n in pages:
        # Rendered as a smoke test rather than as the thing measured: a template
        # that fails to render should fail here, loudly, and an empty one should
        # not be reported as a page that fits comfortably.
        html = env.get_template(f"resume/page{n}.html").render(resume=resume)
        if not html.strip():
            raise SystemExit(f"page{n}.html rendered nothing")
        out[f"page{n}"] = measure(n, resume)

    if not args.json:
        for n in pages:
            r = out[f"page{n}"]
            print(f"  page {n}  {r['height_px']:.0f} / {r['usable_px']:.0f} px"
                  f"  = {r['fill']:.0f}% full")
            for name, h in r["blocks"].items():
                print(f"            {name:<16} {h:>7.0f} px")
        print()
        for n in pages:
            fill = out[f"page{n}"]["fill"]
            verdict = "overflowing" if fill > 100 else ("tight" if fill > 94 else "fits")
            print(f"  page {n}: {verdict}")
    else:
        print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
