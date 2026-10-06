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
import fnmatch
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


def test_the_page_reset_lives_in_the_shared_sheet() -> None:
    """The body margin reset must be shared, not restated per template.

    It used to be a separate rule in `page1.html` and `page2.html`. Extracting the
    shared sheet left it behind, and the pages silently gained the browser's
    default 8px body margin: each document became 1139px tall inside its 1123px
    iframe, so every embedded sheet grew a vertical and a horizontal scrollbar.
    `view.html` sets its own `body { margin: 0 }` and looked fine, which is why
    nothing caught it.
    """
    css = (TEMPLATES / "_resume_css.html").read_text()
    assert re.search(r"html,\s*body\s*\{[^}]*margin:\s*0", css), (
        "the shared sheet no longer zeroes the body margin; the embedded pages "
        "will scroll"
    )
    assert re.search(r"padding:\s*0", css.split("html, body")[1].split("}")[0]), (
        "the reset should zero padding as well as margin"
    )

    for name in ("page1.html", "page2.html"):
        text = (TEMPLATES / name).read_text()
        assert "html, body" not in text, (
            f"{name} restates the reset; it belongs in the shared sheet so the "
            f"three cannot drift again"
        )

    # `view.html` is allowed an `html, body` rule of its own, but only to undo the
    # clipping in print. If it ever restates the reset instead, the shared sheet
    # has stopped being the single source and the drift can start again.
    view = (TEMPLATES / "view.html").read_text()
    for rule in re.findall(r"html,\s*body\s*\{([^}]*)\}", view):
        assert "margin" not in rule, (
            "view.html restates the body margin reset instead of inheriting it"
        )


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
    assert base[0] == "Automated Lawn Mower", (
        "the generic resume leads with the undergraduate thesis build"
    )


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


def test_the_software_resume_reads_for_software() -> None:
    """It must not lead with the mechanical degree.

    The generic headline does, which is right for a job fair and wrong for a
    software application: a reader who sees "Mechanical Engineering graduate"
    first has already filed it before reaching the deployed applications.
    """
    soft = served("Software")

    assert not soft["headline"].startswith("Mechanical"), (
        f"the software headline leads with the degree: {soft['headline']!r}"
    )
    assert "Software" in soft["headline"] or "developer" in soft["headline"]

    # And it leads with the largest software build, not the mechanical-subject
    # project.
    assert [p["name"] for p in soft["projects"]][0] == "Water Billing System"
    assert [p["name"] for p in soft["projects"]][-1] == "MELE Review"

    # It drops the thesis build, the way the mechanical resume drops PracticeForge,
    # and keeps every other project. Pinned as an exclusion rather than a count, so
    # a project added to the default has to be placed here deliberately instead of
    # appearing by arithmetic.
    pool = {p["name"] for p in default_resume()["projects"]}
    assert {p["name"] for p in soft["projects"]} == pool - {
        "Automated Lawn Mower"
    }


def test_no_resume_claims_a_degree_it_does_not_have() -> None:
    """The degree is mechanical, and every resume says so or says nothing.

    A software resume still cannot imply a Computer Science degree, because the
    education entry is inherited unchanged from the default and printed in full.
    Checked here because it is the one claim a reader would verify first.
    """
    for name in ("Generic", "Mechanical Engineering", "Software"):
        resume = served(name)
        degrees = " ".join(e.get("degree", "") for e in resume["education"])
        assert "Mechanical" in degrees, f"{name} lost the degree"
        assert "Computer Science" not in degrees
        assert "Computer Science" not in resume["headline"]
        assert "Computer Science" not in resume["summary"]


def test_the_software_summary_does_not_overclaim_experience() -> None:
    """"Self-taught" and the degree, not a title or years that were not earned.

    The honest framing is what was built and where it runs. Anything that reads
    as a job title or a length of employment is a claim the record does not
    support.
    """
    soft = served("Software")
    text = f"{soft['headline']} {soft['summary']}".lower()

    assert "self-taught" in text
    for overclaim in ("senior", "years of experience", "degree in computer",
                      "computer science graduate", "expert"):
        assert overclaim not in text, f"the software resume overclaims: {overclaim!r}"


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


def test_every_resume_in_the_list_has_a_label_and_a_hint() -> None:
    """The selector shows both, so an empty one is a visible gap.

    The blurb is the button's tooltip: it is how a reader knows which resume to
    send without opening both.
    """
    from apps.routes.resume import _RESUME_LIST

    for item in _RESUME_LIST:
        assert item["label"].strip(), f"{item['name']} has no label"
        assert item["blurb"].strip(), f"{item['name']} has no hint for the selector"


def test_the_embedded_sheets_cannot_scroll() -> None:
    """The sheet is exactly as wide as the iframe, so it must never overrun.

    On screen the sheet is 794px inside a 794px frame. A classic scrollbar, as on
    Windows and on macOS set to always show one, takes ~15px of that frame, which
    pushed the sheet over and produced a horizontal bar; the horizontal bar then
    took height and produced a vertical one too. Headless Chromium uses overlay
    scrollbars and shows nothing wrong, which is why this went unnoticed and why
    the fix is asserted here rather than left to the eye.

    Two things have to hold: the screen rules clip, so a narrower frame cannot
    grow a bar, and the print rules do not, so a page that overruns is flowed onto
    the next sheet instead of being silently cut.
    """
    css = (TEMPLATES / "_resume_css.html").read_text()
    assert re.search(r"html,\s*body\s*\{[^}]*overflow:\s*hidden", css), (
        "the shared sheet no longer clips overflow; the embedded sheets will "
        "scroll whenever the frame loses width to a scrollbar"
    )
    assert re.search(r"\.page\s*\{[^}]*overflow:\s*hidden", css), (
        "a fixed-size sheet should not scroll internally"
    )

    view = (TEMPLATES / "view.html").read_text()
    print_block = view[view.index("@media print"):]
    # Both selectors the screen rules clip have to be undone. Asserting only that
    # the phrase "overflow: visible" appears passes while one of the two is still
    # hidden, which is exactly the half-fix this test exists to catch.
    assert re.search(r"html,\s*body\s*\{[^}]*overflow:\s*visible", print_block), (
        "print leaves `html, body` clipped, so an overrunning page is silently "
        "cut instead of flowing onto the next sheet"
    )
    assert re.search(r"\.page\s*\{[^}]*overflow:\s*visible", print_block), (
        "print leaves the sheet clipped"
    )


def test_the_print_rules_come_after_the_shared_sheet() -> None:
    """Source order, because specificity alone does not settle it.

    `view.html` re-sets `overflow` inside `@media print` to override the shared
    sheet. With the include at the end of the style block those rules came first
    and lost, so the print stylesheet kept clipping while every on-screen check
    still passed.
    """
    view = (TEMPLATES / "view.html").read_text()
    # Look at the code, not the prose: the doc comment above the include names
    # the file too, and matching that would find the wrong position.
    code = re.sub(r"\{#.*?#\}", "", view, flags=re.S)
    include_at = code.index('{% include "resume/_resume_css.html" %}')
    print_at = code.index("@media print")
    assert include_at < print_at, (
        "the shared sheet is included after the print block, so its `overflow: "
        "hidden` wins and the print rules do nothing"
    )


def test_a_skill_order_reorders_without_losing_a_category() -> None:
    """An order selects, it does not replace.

    The software resume leads with its own categories. If an order dropped
    everything it did not name, that resume would silently lose the mechanical
    skills, and a category added to the default later would vanish from every
    resume that named an order before it existed.
    """
    default = default_resume()
    soft = served("Software")

    default_names = [s["category"] for s in default["skills"]]
    soft_names = [s["category"] for s in soft["skills"]]

    assert soft_names[0] == "Programming Languages", soft_names
    assert sorted(soft_names) == sorted(default_names), "a category was lost or invented"

    # The values are untouched, only the sequence moved.
    default_values = {s["category"]: s["value"] for s in default["skills"]}
    for skill in soft["skills"]:
        assert skill["value"] == default_values[skill["category"]]

    # And Generic is unaffected, because it names no order.
    assert [s["category"] for s in default["skills"]] == default_names


def test_a_partial_skill_order_still_keeps_every_category() -> None:
    """The case the software resume does not exercise, because it names all eight.

    A resume that names only the categories it cares about must still carry the
    rest. Without this, an order could stop selecting and start replacing and the
    suite would not notice: every order in the data today happens to be
    exhaustive.
    """
    from apps.routes.resume import _order_skills

    base = {
        "skills": [
            {"category": "A", "value": "a"},
            {"category": "B", "value": "b"},
            {"category": "C", "value": "c"},
        ],
        "skill_order": ["C"],
    }
    out = _order_skills(base)

    assert [s["category"] for s in out["skills"]] == ["C", "A", "B"], out["skills"]
    assert base["skills"][0]["category"] == "A", "the input was mutated"
    # No order at all leaves the list alone.
    assert _order_skills({"skills": base["skills"]})["skills"] == base["skills"]


def test_every_named_skill_category_exists() -> None:
    """A rename in the default would otherwise silently drop a row."""
    pool = {s["category"] for s in default_resume()["skills"]}
    for entry in overrides():
        order = (entry.get("overwrites") or {}).get("skill_order") or []
        unknown = [c for c in order if c not in pool]
        assert not unknown, f"{entry['resume_name']} names unknown skill categories: {unknown}"
        assert len(set(order)) == len(order), f"{entry['resume_name']} repeats a category"


def test_the_mechanical_resume_excludes_practiceforge_on_purpose() -> None:
    """The exclusion is deliberate, not a dropped row.

    Every other project is engineering work a mechanical reader can follow.
    PracticeForge is a Python practice sandbox, recorded elsewhere as halted for
    lack of productive use, so it has nothing to say to that reader. Pinned so a
    future edit has to argue with a test rather than quietly re-add it or drop
    something else.
    """
    pool = {p["name"] for p in default_resume()["projects"]}
    mech = {p["name"] for p in served("Mechanical Engineering")["projects"]}

    assert "PracticeForge" not in mech
    assert mech == pool - {"PracticeForge"}


def test_the_mechanical_resume_leads_with_the_hardware_project() -> None:
    """The lead project has to evidence the headline's claim.

    This resume sells embedded systems as the differentiator, so it leads with the
    mower: the undergraduate thesis, and the only entry that is a machine — two
    LiFePO4 packs, a 400 W array, and a panel that commands the drives.

    Water Billing System follows, and is the second piece of hardware evidence: a
    reader taps a phone against an NFC tag on the meter and the reading is
    recorded, with a dedicated NFC route and on-device key derivation. MELE Review
    is stronger on mechanical subject matter, being a licensure reviewer, but it is
    pure software underneath and evidences nothing about hardware, so it stays
    behind both. Pinned with the reason because this order was argued over once
    already, on the argument that MELE is the more mechanical subject; that
    argument is about subject matter, and the page is making a claim about
    hardware.
    """
    mech = [p["name"] for p in served("Mechanical Engineering")["projects"]]

    assert mech[0] == "Automated Lawn Mower", (
        f"the mechanical resume leads with {mech[0]!r}, which does not evidence the "
        f"embedded-systems claim in its headline"
    )
    assert mech[1] == "Water Billing System", (
        "Water Billing is still the second piece of hardware evidence, not dropped"
    )
    assert mech[2] == "MELE Review", "MELE should still be third, not dropped"


def test_the_headline_claim_is_what_the_page_leads_with() -> None:
    """Checked across resumes, not only the one that prompted the fix."""
    expectations = {
        "Mechanical Engineering": ("Automated Lawn Mower", "Embedded"),
        "Software": ("Water Billing System", "developer"),
    }
    for name, (first, headline_word) in expectations.items():
        resume = served(name)
        assert headline_word in resume["headline"], (
            f"{name}: the headline no longer claims {headline_word!r}, so this "
            f"expectation is stale"
        )
        assert resume["projects"][0]["name"] == first, (
            f"{name}: leads with {resume['projects'][0]['name']!r}, not {first!r}"
        )


def test_the_mechanical_resume_leads_with_the_electronics_differentiator() -> None:
    """The headline claims the embedded work, which is what sets it apart.

    Content edit requested by the owner: the mechanical variant sells the
    electronics experience rather than resting on the degree.
    """
    mech = served("Mechanical Engineering")

    assert "Embedded" in mech["headline"], mech["headline"]
    assert "embedded" in mech["summary"].lower()
    # No machine words, and no claim that the degree is electronic.
    assert "Computer" not in mech["headline"]


def test_no_resume_uses_an_em_dash() -> None:
    """Standing house rule for published Portfolio copy.

    The resume is the surface most likely to accumulate one, because a summary is
    where a writer reaches for a dash. En dashes are allowed; em dashes are not.

    Both forms are checked. The files are written with `ensure_ascii`, so a real
    em dash arrives as the six characters `\\u2014` and never as U+2014, and a
    check for the character alone passes while the file is full of them. The same
    file carries an en dash as `\\u2013`, which is what makes this easy to get
    wrong.
    """
    for path in ("default_resume.json", "overwrite_resume.json"):
        text = (REPO / "data" / path).read_text(encoding="utf-8")
        assert "\u2014" not in text, f"{path} contains a literal em dash"
        assert "\\u2014" not in text.lower(), f"{path} contains an escaped em dash"

    # The en dash stays allowed, and it is written as an escape too, so the check
    # above has to name U+2014 rather than reject escapes generally.
    assert "\\u2013" in (REPO / "data" / "default_resume.json").read_text(), (
        "the en dash escape has gone from the data, so this test no longer proves "
        "the em dash check is specific"
    )


def test_the_resume_files_reach_the_image() -> None:
    """The data must not be excluded by `.dockerignore`.

    `data/` holds runtime state a local run writes, so it is ignored, with an
    exception for the JSON content. That exception used to name one file, and
    renaming the file silently dropped the resume from the image: the app still
    started, the build still reported success, and every page rendered empty. The
    tests all passed because they read the working tree, not the image.
    """
    ignore = (REPO / ".dockerignore").read_text()
    patterns = [
        line.strip() for line in ignore.splitlines()
        if line.strip() and not line.startswith("#")
    ]

    for name in ("default_resume.json", "overwrite_resume.json"):
        path = f"data/{name}"
        assert (REPO / path).is_file(), f"{path} is missing from the repo"

        # Docker evaluates patterns in order and the last match wins, so the file
        # has to be re-included after the `data/` exclusion. Matching is done with
        # `fnmatch` against the real path: an earlier version of this test checked
        # whether the filename appeared in the pattern text, which is true of any
        # pattern and therefore proved nothing.
        def matches(pattern: str, target: str) -> bool:
            return fnmatch.fnmatch(target, pattern) or target.startswith(
                pattern.rstrip("/") + "/"
            )

        re_included = [
            i for i, p in enumerate(patterns)
            if p.startswith("!") and matches(p[1:], path)
        ]
        excluded = [i for i, p in enumerate(patterns) if matches(p, path)]

        assert re_included, (
            f"nothing in .dockerignore re-includes {path}; the image will not "
            f"carry the resume"
        )
        last_exclude = max(
            (i for i in excluded if not patterns[i].startswith("!")), default=-1
        )
        assert max(re_included) > last_exclude, (
            f"{path} is re-included before the `data/` exclusion; last match wins, "
            f"so the exclusion stands and the resume never reaches the image"
        )


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
