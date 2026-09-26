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


def test_the_homelab_is_a_project_and_not_a_section_of_its_own() -> None:
    """It is one thing, so it gets one entry.

    The homelab was briefly both a dedicated section at the foot of page 1 and a
    project on page 2, saying the same three facts under two headings, so a
    reader counting projects saw six entries for five projects.
    """
    resume = resume_data()

    assert "homelab" not in resume, "the dedicated homelab section is back"

    names = [p.get("name") for p in resume["projects"]]
    assert names.count("Homelab") == 1, f"Homelab appears {names.count('Homelab')} times"

    # And no template renders one either, however the data is shaped.
    for name in ("_page1_body.html", "_page2_body.html", "view.html"):
        text = (TEMPLATES / name).read_text()
        assert "section-homelab" not in text, f"{name} still renders a homelab section"


def test_the_homelab_leads_the_projects() -> None:
    """It hosts every other project, so it is listed first."""
    projects = resume_data()["projects"]
    assert projects[0]["name"] == "Homelab", (
        f"the projects lead with {projects[0]['name']!r}; the homelab hosts the rest"
    )


def test_the_two_pages_do_not_repeat_each_other() -> None:
    """Page 1 is the background, page 2 is the work.

    Sections have been placed on the wrong page more than once while this was
    being rearranged, which is exactly the kind of duplication a shared partial
    makes easy to reintroduce by including the wrong file.
    """
    body1 = (TEMPLATES / "_page1_body.html").read_text()
    body2 = (TEMPLATES / "_page2_body.html").read_text()

    assert "section-projects" in body2
    assert "section-projects" not in body1
    assert "section-experience" in body1
    assert "section-experience" not in body2


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


def test_the_resume_renders_the_homelab_once(client) -> None:
    """One Homelab entry across the two sheets, and it is a project."""
    body = client.get("/resume/view").text
    assert body.count("<h2>Homelab</h2>") == 0, "Homelab should not be its own section"
    assert "Homelab" in body, "the Homelab project disappeared"
    assert "Selected Personal Projects" in body
    assert "Host Dashboard" not in body, "still shows the old name"

    for url in ("/resume/view?page=1", "/resume/view?page=2"):
        assert "section-homelab" not in client.get(url).text
