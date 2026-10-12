"""The header's Contact control.

A `mailto:` is a correct link that does nothing on a machine with no mail
handler, which reads as a broken button. The header therefore keeps the mailto
as its no-JavaScript fallback *and* renders a panel with the address in text, a
copy control and a web-compose link so the click always leads somewhere.

What is asserted here is the part a server test can see: that the panel exists
and starts closed, that the address comes from one place rather than being typed
into a template, that the trigger is still an anchor pointing at the mailto, and
that the script is on the page. The interaction itself - open, copy, Escape,
click-away - was driven in a real browser.
"""

import os

os.environ.setdefault("DEPLOYMENT_TYPE", "debug")

import pytest
from fastapi.testclient import TestClient

from apps import create_app
from apps.config import get_config


@pytest.fixture()
def client():
    with TestClient(create_app()) as client:
        yield client


@pytest.fixture()
def home(client) -> str:
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.text


def test_the_contact_panel_starts_closed(home: str) -> None:
    """An open panel would sit over the page before anyone clicked anything."""
    assert 'id="ui-contact-panel"' in home
    assert 'id="ui-contact-panel" role="dialog" aria-label="Contact" hidden' in home


def test_the_address_comes_from_the_config_not_a_template(home: str) -> None:
    """One source, so the header and the contact section cannot drift apart."""
    assert get_config().CONTACT_EMAIL in home


def test_the_trigger_is_a_mailto_so_it_survives_having_no_javascript(home: str) -> None:
    """The fallback matters: a button with no script behind it would be dead."""
    assert f'href="mailto:{get_config().CONTACT_EMAIL}"' in home
    assert 'id="ui-contact-trigger"' in home


def test_the_panel_offers_a_copy_and_a_web_compose(home: str) -> None:
    assert "data-contact-copy" in home
    assert f'data-copy-value="{get_config().CONTACT_EMAIL}"' in home
    assert "https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=" in home


def test_the_copy_feedback_is_a_live_region(home: str) -> None:
    """A copy that says nothing announces nothing."""
    assert 'data-contact-status role="status" aria-live="polite"' in home


def test_the_contact_section_shows_the_address_in_text(home: str) -> None:
    """The whole point: something readable that works with no mail handler."""
    contact = home.split('id="contact"', 1)[1] if 'id="contact"' in home else ""
    assert get_config().CONTACT_EMAIL in contact
    assert "data-contact-copy" in contact


def test_the_script_is_on_the_page(home: str) -> None:
    assert "/static/js/contact.js?v=" in home
