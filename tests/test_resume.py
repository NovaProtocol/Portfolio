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


def default_resume() -> dict:
    """The resume everything is built from."""
    return json.loads((REPO / "data" / "default_resume.json").read_text())


def overrides() -> list[dict]:
    """The named resumes, as written in the data file."""
    return json.loads((REPO / "data" / "overwrite_resume.json").read_text())


def served(name: str | None = None) -> dict:
    """A resume as the app resolves it: default, with the override merged in."""
    from apps.routes.resume import load_resume

    return load_resume(name)


def resume_data() -> dict:
    """Back-compat: the generic resume, resolved."""
    return served()


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
    resume = default_resume()

    assert "homelab" not in resume, "the dedicated homelab section is back"

    names = [p.get("name") for p in resume["projects"]]
    assert names.count("Homelab") == 1, f"Homelab appears {names.count('Homelab')} times"

    # And no template renders one either, however the data is shaped.
    for name in ("_page1_body.html", "_page2_body.html", "view.html"):
        text = (TEMPLATES / name).read_text()
        assert "section-homelab" not in text, f"{name} still renders a homelab section"


def test_the_resume_list_is_generic_plus_the_overrides() -> None:
    """Generic first and always present, then each named resume in file order."""
    from apps.routes.resume import resume_names

    names = resume_names()
    written = [entry["resume_name"] for entry in overrides()]

    assert names[0] == "Generic", f"the list starts with {names[0]!r}"
    assert names == ["Generic", *written], f"{names} vs {written}"
    assert "Mechanical Engineering" in names


def test_an_override_changes_only_what_it_names() -> None:
    """Everything the override does not mention is inherited from the default.

    This is the whole point of the split, and a shallow merge would break it: an
    override that sets only `summary` would drop nested keys elsewhere, and the
    resume would quietly lose content.
    """
    base = default_resume()
    mech = served("Mechanical Engineering")

    assert mech["summary"] != base["summary"]
    assert mech["headline"] != base["headline"]

    unchanged = [k for k in base if k not in ("summary", "headline", "projects")]
    for key in unchanged:
        assert mech[key] == base[key], f"{key} should have been inherited unchanged"


def test_the_merge_is_deep() -> None:
    """A nested override must not take its siblings with it."""
    from apps.routes.resume import _deep_merge

    base = {"a": {"keep": 1, "change": 2}, "b": 3}
    out = _deep_merge(base, {"a": {"change": 99}})

    assert out == {"a": {"keep": 1, "change": 99}, "b": 3}
    assert base == {"a": {"keep": 1, "change": 2}, "b": 3}, "the base was mutated"


def test_the_mechanical_resume_drops_only_practiceforge() -> None:
    """One project is left out, and it is the one with no subject to place.

    Every other entry is engineering work a mechanical reader can follow.
    PracticeForge is a Python practice sandbox, recorded elsewhere as halted for
    lack of productive use, so it has nothing to say to that reader.
    """
    base = [p["name"] for p in default_resume()["projects"]]
    mech = [p["name"] for p in served("Mechanical Engineering")["projects"]]

    assert set(mech) == set(base) - {"PracticeForge"}
    assert mech[0] == "MELE Review", "the mechanical resume should lead with its subject"
    assert base[0] == "Water Billing System", "the generic resume leads with the largest build"


def test_a_named_resume_repeats_no_project_text() -> None:
    """Project content lives in the default, once.

    An override names projects; it must not restate them, or the two files drift
    and the site shows one version while the fit tool measures another.
    """
    for entry in overrides():
        projects = (entry.get("overwrites") or {}).get("projects")
        if projects is None:
            continue
        assert all(isinstance(p, str) for p in projects), (
            f"{entry['resume_name']} inlines project content; name them instead"
        )


def test_a_named_resume_only_names_projects_that_exist() -> None:
    """A rename in the default would otherwise silently empty a resume."""
    pool = {p["name"] for p in default_resume()["projects"]}
    for entry in overrides():
        projects = (entry.get("overwrites") or {}).get("projects") or []
        unknown = [p for p in projects if p not in pool]
        assert not unknown, f"{entry['resume_name']} names projects that do not exist: {unknown}"
        assert len(set(projects)) == len(projects), f"{entry['resume_name']} repeats a project"


def test_each_resume_renders_its_own_projects(client) -> None:
    """The order asked for is the order rendered, per resume."""
    from apps.routes.resume import resume_names

    for name in resume_names():
        body = client.get(f"/resume/view?page=2&resume={name}").text
        rendered = re.findall(r'<p class="title"[^>]*>([^<]+)</p>', body)
        expected = [p["name"] for p in served(name)["projects"]]
        assert rendered == expected, f"{name}: {rendered}"


def test_an_unknown_resume_serves_the_generic_one(client) -> None:
    """A stale bookmark or a typo must not 500 a resume."""
    generic = client.get("/resume/view?page=2").text
    for bad in ("nonsense", "", "mechanical", "3"):
        resp = client.get(f"/resume/view?page=2&resume={bad}")
        assert resp.status_code == 200, f"resume={bad!r} returned {resp.status_code}"
        assert resp.text == generic, f"resume={bad!r} did not fall back to Generic"


def test_the_old_parameters_are_ignored_rather_than_rejected(client) -> None:
    """`variant` and `theme` were both real once. Links to them must still work."""
    generic = client.get("/resume/view?page=2").text
    for old in ("variant=mechanical", "variant=software", "theme=1", "theme=3"):
        assert client.get(f"/resume/view?page=2&{old}").text == generic, old

    hub = (TEMPLATES / "index.html").read_text()
    assert "variant-btn" not in hub
    assert "theme-btn" not in hub
    assert "resume-btn" in hub

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
    resume = default_resume()
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
    resume = default_resume()
    gatekeeper = next(
        (p for p in resume["projects"] if "GateKeeper" in p.get("name", "")), None
    )
    assert gatekeeper, "GateKeeper is no longer on the resume"
    assert "SQLite" not in gatekeeper["tech"]
    assert "MySQL" in gatekeeper["tech"]


def test_the_fit_tool_measures_the_document_the_site_serves() -> None:
    """The tool loads through the app, not through a copy of its logic.

    It used to reimplement the resolution, which is how a fill figure ends up
    describing a document nobody is served.
    """
    from resume_fit import load_resume as tool_load

    for name in ("Generic", "Mechanical Engineering", None):
        assert tool_load(name) == served(name), f"the tool disagrees for {name!r}"


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
    resume = default_resume()
    plant = next(
        (j for j in resume["experience"] if "Physical Plant" in j.get("role", "")), None
    )
    assert plant, "the facilities entry is gone"
    joined = " ".join(plant["responsibilities"])
    assert "Coordinated documentation and communication across departments" in joined
