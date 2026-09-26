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


def test_each_variant_leads_with_what_it_is_for() -> None:
    """The two variants open with different projects, on purpose.

    Mechanical leads with the licensure reviewer, whose subject is mechanical.
    Software leads with the largest complete build. If these ever come out the
    same, one of the variants has stopped doing its job.
    """
    variants = resume_data()["variants"]
    assert list(variants) == ["mechanical", "software"], "variant set changed"
    assert variants["mechanical"]["order"][0] == "MELE Review"
    assert variants["software"]["order"][0] == "Water Billing System"


def test_the_mechanical_variant_drops_only_practiceforge() -> None:
    """One exclusion, and it is the one with no subject to place.

    Every other project is engineering work that a mechanical recruiter can read
    as process. PracticeForge is the one entry with neither an engineering
    subject nor a product purpose, and the owner's own notes record it as halted
    for lack of productive use.
    """
    resume = resume_data()
    mechanical = resume["variants"]["mechanical"]["order"]
    software = resume["variants"]["software"]["order"]

    pool = {p["name"] for p in resume["projects"]}
    assert set(mechanical) == pool - {"PracticeForge"}
    assert set(software) == pool
    # Nothing is invented by a variant, and nothing else is dropped.
    assert set(mechanical) < set(software)


def test_every_variant_names_projects_that_exist() -> None:
    """A rename in the pool would otherwise silently empty a variant."""
    resume = resume_data()
    pool = {p["name"] for p in resume["projects"]}
    for name, spec in resume["variants"].items():
        unknown = [x for x in spec["order"] if x not in pool]
        assert not unknown, f"variant {name!r} names projects that do not exist: {unknown}"
        assert len(set(spec["order"])) == len(spec["order"]), f"variant {name!r} repeats a project"


def test_the_variant_orders_the_page_the_route_serves(client) -> None:
    """The order asked for is the order rendered, for both variants."""
    for variant, expected in resume_data()["variants"].items():
        body = client.get(f"/resume/view?page=2&variant={variant}").text
        rendered = re.findall(r'<p class="title"[^>]*>([^<]+)</p>', body)
        assert rendered == expected["order"], f"{variant}: {rendered}"


def test_an_unknown_variant_serves_the_default_rather_than_failing(client) -> None:
    """A stale bookmark or a typo must not 500 a resume."""
    default = client.get("/resume/view?page=2").text
    for bad in ("nonsense", "", "MECHANICAL", "3"):
        resp = client.get(f"/resume/view?page=2&variant={bad}")
        assert resp.status_code == 200, f"variant={bad!r} returned {resp.status_code}"
        assert resp.text == default, f"variant={bad!r} did not fall back to the default"


def test_the_theme_parameter_is_gone_and_changes_nothing(client) -> None:
    """One theme is published, so `theme` must not still select another.

    The other two were deleted. Leaving the argument working would keep dead CSS
    alive behind a query string that nothing links to.
    """
    plain = client.get("/resume/view?page=2").text
    for theme in (1, 2, 3):
        assert client.get(f"/resume/view?page=2&theme={theme}").text == plain

    theme_css = (TEMPLATES / "_theme.html").read_text()
    assert "{% if theme" not in theme_css, "_theme.html still branches on a theme"
    assert "theme-btn" not in (TEMPLATES / "index.html").read_text()


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


def test_the_fit_tool_orders_projects_the_way_the_route_does() -> None:
    """Two functions resolve the variant order; they must agree.

    `tools/resume_fit.py` keeps its own copy so it can measure a page without the
    app. A fill figure measured against a different project list than the one
    served is worse than no figure, so the two are compared here.
    """
    from resume_fit import order_projects

    data = resume_data()
    for variant in data["variants"]:
        tool = [p["name"] for p in order_projects(data, variant)["projects"]]
        spec = data["variants"][variant]["order"]
        assert tool == spec, f"{variant}: fit tool {tool} vs data {spec}"


def test_the_resume_renders_the_homelab_once(client) -> None:
    """One Homelab entry across the two sheets, and it is a project."""
    body = client.get("/resume/view").text
    assert body.count("<h2>Homelab</h2>") == 0, "Homelab should not be its own section"
    assert "Homelab" in body, "the Homelab project disappeared"
    assert "Selected Personal Projects" in body
    assert "Host Dashboard" not in body, "still shows the old name"

    for url in ("/resume/view?page=1", "/resume/view?page=2"):
        assert "section-homelab" not in client.get(url).text


def test_the_facilities_coordination_line_stays() -> None:
    """Flagged missing twice; pinned so a future trim has to argue with a test.

    The owner asked for this line back after it was dropped in two successive
    revisions and called it non-negotiable.
    """
    resume = resume_data()
    plant = next(
        (j for j in resume["experience"] if "Physical Plant" in j.get("role", "")), None
    )
    assert plant, "the facilities entry is gone"
    joined = " ".join(plant["responsibilities"])
    assert "Coordinated documentation and communication across departments" in joined
