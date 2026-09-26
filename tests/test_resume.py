"""The resume templates, and the one fact that has to agree between them.

The resume is two fixed A4 sheets with `overflow: hidden`, so content that grows
past the box is silently invisible rather than spilling onto a third page. Two of
the templates say how tall the content area is, and they must agree:

* `_resume_css.html` sets the page padding that the browser renders.
* `tools/resume_fit.py` assumes that padding to estimate how full a page is.

When those drifted there was nothing to notice it. The fit tool reported that
both pages fit while the page it measured was using a different padding, and the
template's own copy of the rules had quietly fallen behind the other two.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TEMPLATES = REPO / "apps" / "resume" / "templates" / "resume"

sys.path.insert(0, str(REPO / "tools"))


def resume_data() -> dict:
    return json.loads((REPO / "data" / "resume.json").read_text())


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from apps import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


def test_the_page_padding_matches_what_the_fit_tool_assumes() -> None:
    """The one number that has to agree, checked rather than remembered."""
    from resume_fit import PAD_V_PX

    css = (TEMPLATES / "_resume_css.html").read_text()
    match = re.search(r"padding:\s*([\d.]+)mm\s+[\d.]+mm", css)
    assert match, "no `.page` padding found in _resume_css.html"

    top_mm = float(match.group(1))
    assumed_mm = PAD_V_PX / 2 / (96 / 25.4)
    assert abs(top_mm - assumed_mm) < 0.01, (
        f"the template pads {top_mm}mm vertically and resume_fit.py assumes "
        f"{assumed_mm:.2f}mm; the fit figure is wrong until these agree"
    )


def test_the_shared_rules_are_included_once() -> None:
    """Every template gets the shared sheet, and none keeps a private copy.

    The three templates each carried their own version of these rules and they
    drifted, which is what caused the view to overflow while the iframe beside it
    did not.
    """
    for name in ("page1.html", "page2.html", "view.html"):
        text = (TEMPLATES / name).read_text()
        assert '_resume_css.html' in text, f"{name} does not include the shared rules"

    css = (TEMPLATES / "_resume_css.html").read_text()
    for rule in ("section:last-child", ".resume-header", "section h2", ".skill-row"):
        assert rule in css, f"the shared sheet lost `{rule}`"


def test_the_two_pages_do_not_repeat_each_other() -> None:
    """Page 1 carries the homelab; page 2 carries the projects.

    The homelab section went on both pages at different points while it was being
    placed, which is exactly the kind of duplication a shared partial makes easy
    to reintroduce by including the wrong file.
    """
    body1 = (TEMPLATES / "_page1_body.html").read_text()
    body2 = (TEMPLATES / "_page2_body.html").read_text()

    assert "section-homelab" in body1
    assert "section-homelab" not in body2
    assert "section-projects" in body2
    assert "section-projects" not in body1


def test_every_project_names_its_technology(client) -> None:
    """A project entry with no tech stack is a heading and a claim."""
    resume = resume_data()
    assert resume["projects"], "no projects to check"
    for project in resume["projects"]:
        assert project.get("tech"), f"{project.get('name')} has no tech line"
        assert project.get("highlights"), f"{project.get('name')} has no highlights"


def test_gatekeeper_does_not_claim_sqlite(client) -> None:
    """GateKeeper runs MySQL in production; SQLite is only the fallback default.

    Its module docstring and `shared/config.py` both say so, and the resume said
    SQLite for two revisions. Pinned because "SQLite" reads as a smaller build
    than the one that actually runs.
    """
    resume = resume_data()
    gatekeeper = next(
        (p for p in resume["projects"] if "GateKeeper" in p.get("name", "")), None
    )
    assert gatekeeper, "GateKeeper is no longer on the resume"
    assert "SQLite" not in gatekeeper["tech"]
    assert "MySQL" in gatekeeper["tech"]


def test_the_resume_renders_with_the_homelab_section(client) -> None:
    """The section is data-driven, so a rename of the key would empty it."""
    for url, expected in (
        ("/resume/view?page=1", "Homelab"),
        ("/resume/view?page=2", "Technical Skills"),
    ):
        body = client.get(url).text
        assert expected in body, f"{url} lost its {expected} section"
        assert "Host Dashboard" not in body, f"{url} still shows the old name"
