#!/usr/bin/env python3
"""Render the resume pages and measure how much of each A4 page they fill.

The resume is two fixed-size A4 pages with `overflow: hidden`, so content that
grows past the box is silently invisible rather than spilling. That makes "does
it still fit" a question worth being able to answer, and it is the kind of
question a template change can get wrong without any test noticing.

Measurement is approximate, but calibrated rather than guessed. It computes the
height of the rendered blocks from the same CSS the template uses instead of
launching a browser, and every constant in the geometry block below is written
as the declaration it comes from. It was checked against a real browser across
all three resumes and both pages and agrees to within 3px of a 1024px page.

That agreement is the whole value, and it is not self-maintaining: a change to
`_resume_css.html` that this file does not mirror makes the figure quietly
optimistic, which is worse than not having it, the version before this one
reported 105% where the browser measured 110%, and called a page with no slack
at all "94% full". Re-measure a real browser after touching the stylesheet.
`dashboard/check-pages.mjs` in ServerDashboard is where that is already done.

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

# --- geometry, taken from `_resume_css.html` and `_theme.html` --------------
#
# Every figure below is the CSS declaration it comes from, written as arithmetic
# so a change to the stylesheet is a change to one of these lines rather than a
# silent drift. Three of them were wrong before this was rewritten, and each was
# wrong in the optimistic direction, the tool reported 105% where the browser
# said 110%, and "94% full" for a page that was exactly 100% with no slack at
# all. A fill figure that reads low is worse than no figure, because it is the
# one that gets trusted.
#
# `rem` resolves against the *root* font size, which the sheet never sets and so
# is the browser default 16px, not the 11px the page itself inherits. Treating
# them as the same is how `0.68rem` and `0.65rem` collapse into one number.
REM = 16.0
FS = 11.0                            # body { font-size }
LH = 1.38                            # body { line-height }
LINE = FS * LH                       # 15.18

H2_H = 0.95 * FS * LH + 0.15 * REM + 0.2 * REM + 1   # 21.0: type, padding, rule
H2_MB = 0.4 * REM                    # section h2 { margin-bottom }
SECTION_MB = 0.68 * REM              # section { margin-bottom }
ENTRY_MB = 0.65 * REM                # .entry { margin-bottom }
HEAD_MB = 0.1 * REM                  # .entry .head { margin-bottom }
TITLE_MB = 0.15 * REM                # inline margin-bottom on the project title
META_H = 0.85 * FS * LH              # .tech-stack / .demo-line
META_MB = 0.2 * REM                  # .tech-stack / .demo-line { margin-bottom }
LI_H = 0.95 * FS * LH                # .entry ul li
LI_MB = 0.15 * REM                   # .entry ul li { margin-bottom }
SKILL_MB = 0.4 * REM                 # .skill-row { margin-bottom }
UL_MT = 0.1 * REM                    # .entry ul { margin-top }
AWARD_UL_MT = 0.2 * REM              # inline margin-top on the education awards list

ORG_H = 0.95 * FS * LH               # .entry .org
ORG_MT = 0.95 * FS                   # user-agent 1em, at .org's own size
ORG_MB = 0.3 * REM                   # inline margin-bottom on the experience role

H1_H = 1.6 * FS * LH                 # .resume-header h1
H1_MB = 0.3 * REM                    # .resume-header h1 { margin-bottom }
CONTACT_H = 0.9 * FS * LH            # .contact-line
HEADER_MB = 0.9 * REM                # .resume-header { margin-bottom }
HEADER_PB = 0.8 * REM                # .resume-header { padding-bottom }
HEADER_BORDER = 3                    # the 3px double rule
PHOTO_H = 90                         # .resume-photo

#: The user-agent `p { margin: 1em 0 }`, which the sheet never resets on the
#: paragraphs it does not give a class to. It is real space and it is most of a
#: page-1 block, so it has to be counted rather than assumed away.
P_MB = FS

#: Characters to a wrapped line, per font size. These are the only fitted values
#: here, everything above is arithmetic, so they are the ones to revisit if the
#: fill starts drifting. Calibrated against the real browser by reading back the
#: rendered height of every `<li>` and every summary: at these widths the tool
#: reproduces the line count the browser chose for each one, which is what the
#: totals depend on. A single number does not work for both, because the list
#: items are 0.95em inside a 1.2rem indent and so wrap at a different width than
#: the paragraphs they sit under.
#:
#: The bands these were fitted to, as a check on the next change: a paragraph is
#: 3 lines at 385 characters and 4 at 442; a list item is one line at 143 and two
#: at 156.
BODY_CHARS = 143                      # 11px paragraphs, full page width
LI_CHARS = 150                        # .entry ul li, 0.95em inside the indent
META_CHARS = int(BODY_CHARS / 0.85)   # .tech-stack / .demo-line, 0.85em


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


def fold(text: str, chars: int = BODY_CHARS) -> int:
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

#: The one sentence `_page2_body.html` prints above the projects. It is the only
#: fixed prose the measurement depends on; everything else comes from the data.
PROJECTS_INTRO = (
    "Live demos of selected projects are hosted on my portfolio. "
    "Source code for these projects is public on GitHub."
)


def _ul(items: list) -> float:
    """A `<ul>`'s content height: the wrapped items and the gaps between them.

    The list's own `margin-top` is not counted. It collapses with the margin of
    whatever precedes it, and that margin is always the larger of the two, so
    the gap is already paid for by the paragraph above.
    """
    if not items:
        return 0.0
    return (sum(fold("• " + item, LI_CHARS) * LI_H for item in items)
            + (len(items) - 1) * LI_MB)


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
    if resume.get("headline"):
        lines += 1
    who = H1_H + H1_MB + lines * CONTACT_H
    photo = PHOTO_H if resume.get("photo") else 0.0
    return max(who, photo) + HEADER_PB + HEADER_BORDER


def _section(entries: list) -> float:
    """A section box: its heading, then its entries and the gaps between them."""
    if not entries:
        return 0.0
    return H2_H + H2_MB + sum(entries) + (len(entries) - 1) * ENTRY_MB


def _project(proj: dict) -> float:
    """One project entry on page 2.

    The title is followed by up to three meta lines that all share one style and
    one designed margin, then the highlight list. The list's `margin-top` loses
    the collapse to the last meta line's `margin-bottom`, so it adds nothing.
    """
    h = fold(proj.get("name", "")) * LINE + TITLE_MB
    if proj.get("tech"):
        h += fold(f"Tech Stack: {proj['tech']}", META_CHARS) * META_H + META_MB
    if proj.get("status_line"):
        h += fold(proj["status_line"], META_CHARS) * META_H + META_MB
    if proj.get("url"):
        h += fold(f"Live demo: {proj['url']}", META_CHARS) * META_H + META_MB
    return h + _ul(proj.get("highlights") or [])


def _page1(resume: dict) -> dict:
    detail: dict[str, float] = {}

    detail["header"] = _header(resume)

    summary = resume.get("summary", "")
    detail["summary"] = H2_H + max(H2_MB, P_MB) + fold(summary) * LINE

    edu = []
    for entry in resume.get("education", []):
        h = LINE + max(HEAD_MB, ORG_MT) + ORG_H      # head, gap, the degree line
        if entry.get("status"):
            h += ORG_MT + ORG_H                      # a second p.org
        if entry.get("awards"):
            h += AWARD_UL_MT + _ul(entry["awards"])
        edu.append(h)
    if edu:
        detail["education"] = _section(edu)

    cw = resume.get("coursework") or []
    if cw:
        detail["coursework"] = H2_H + max(H2_MB, P_MB) + fold(" · ".join(cw)) * LINE

    certs = []
    for entry in resume.get("certifications", []):
        h = LINE + max(HEAD_MB, P_MB) + LINE         # head, gap, the issuer
        if entry.get("detail"):
            h += P_MB + LINE                         # a bare <p>, one em above
        certs.append(h)
    if certs:
        detail["certifications"] = _section(certs)

    jobs = []
    for entry in resume.get("experience", []):
        h = LINE + max(HEAD_MB, ORG_MT) + ORG_H
        h += max(ORG_MB, UL_MT) + _ul(entry.get("responsibilities") or [])
        jobs.append(h)
    if jobs:
        detail["experience"] = _section(jobs)

    return detail


def _page2(resume: dict) -> dict:
    detail: dict[str, float] = {}

    projects = resume.get("projects") or []
    if projects:
        wrap = sum(_project(p) for p in projects) + (len(projects) - 1) * ENTRY_MB
        # Heading, the intro sentence (a bare `p`, so one em above and below),
        # then the entries.
        detail["projects"] = (
            H2_H + max(H2_MB, P_MB) + fold(PROJECTS_INTRO) * LINE + P_MB + wrap
        )

    skills = resume.get("skills") or []
    if skills:
        # `.skill-row:last-child` carries no margin, so the last row adds no
        # trailing gap, the row itself and the gaps between are all there is.
        detail["skills"] = (
            H2_H + H2_MB + len(skills) * LINE + (len(skills) - 1) * SKILL_MB
        )

    return detail


def measure(page: int, resume: dict) -> dict:
    """The height of one page's blocks, and their total in a 1024px page.

    Counted per element type from the data rather than parsed out of the HTML,
    because the numbers that matter are the list lengths and string lengths, and
    they are already in hand.

    `height_px` is the whole page: the blocks plus the margins between them (and
    the header's own), which is why it is larger than the sum of `blocks`. The
    blocks are reported separately because "which section grew" is the question
    the figure is usually asked.
    """
    if page == 1:
        detail = _page1(resume)
        sections = [
            detail["summary"],
            *[detail[k] for k in ("education", "coursework",
                                  "certifications", "experience") if k in detail],
        ]
        px = (detail["header"] + HEADER_MB
              + sum(sections) + (len(sections) - 1) * SECTION_MB)
    elif page == 2:
        detail = _page2(resume)
        sections = [detail[k] for k in ("projects", "skills") if k in detail]
        px = sum(sections) + max(0, len(sections) - 1) * SECTION_MB
    else:
        raise ValueError(f"no page {page}")

    stray = set(detail) - set(PAGE_BLOCKS[page])
    if stray:
        raise AssertionError(f"page {page} measured unknown blocks: {sorted(stray)}")

    return {"height_px": round(px, 1), "usable_px": round(USABLE_H, 1),
            "fill": round(px / USABLE_H * 100, 1), "blocks": detail}


def load_resume(name: str | None = None) -> dict:
    """One resolved resume, by name, through the app's own loader.

    Deliberately not reimplemented here. The merge and the project expansion live
    in `apps/routes/resume.py`, and a second copy of that logic is how this tool
    ends up reporting the fill of a document nobody is served. `make_env()`
    already imports from `apps.templating`, so there is nothing to avoid.
    """
    from apps.routes.resume import resume_names as names
    from apps.routes.resume import load_resume as load

    chosen = name if name in names() else None
    return load(chosen)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--page", type=int, choices=[1, 2])
    ap.add_argument("--resume", default=None,
                    help="a resume name, or 'all' to measure every one")
    args = ap.parse_args()

    from apps.routes.resume import resume_names

    env = make_env()

    if args.resume == "all":
        names: list[str | None] = list(resume_names())
    else:
        names = [args.resume]

    pages = [1, 2] if not args.page else [args.page]
    everything: dict[str, dict] = {}
    for name in names:
        resume = load_resume(name)
        out = {}
        for n in pages:
            # Rendered as a smoke test rather than as the thing measured: a
            # template that fails to render should fail here, loudly, and an
            # empty one should not be reported as a page that fits comfortably.
            html = env.get_template(f"resume/page{n}.html").render(resume=resume)
            if not html.strip():
                raise SystemExit(f"page{n}.html rendered nothing")
            out[f"page{n}"] = measure(n, resume)
        everything[name or "Generic"] = out

    if args.json:
        print(json.dumps(everything, indent=2))
        return 0

    for name, out in everything.items():
        if len(everything) > 1:
            print(f"  [{name}] {len(load_resume(name)['projects'])} projects")
        for n in pages:
            r = out[f"page{n}"]
            print(f"  page {n}  {r['height_px']:.0f} / {r['usable_px']:.0f} px"
                  f"  = {r['fill']:.0f}% full")
            if n == 2:
                for block, h in r["blocks"].items():
                    print(f"            {block:<16} {h:>7.0f} px")
        for n in pages:
            fill = out[f"page{n}"]["fill"]
            verdict = "overflowing" if fill > 100 else ("tight" if fill > 94 else "fits")
            print(f"  page {n}: {verdict}")
        if len(everything) > 1:
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
