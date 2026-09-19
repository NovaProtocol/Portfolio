import os

os.environ.setdefault("DEPLOYMENT_TYPE", "debug")

import pytest
from fastapi.testclient import TestClient

from apps import create_app


@pytest.fixture()
def client():
    with TestClient(create_app()) as client:
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_index_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_unknown_project_is_404(client):
    resp = client.get("/projects/info/no-such-project/")
    assert resp.status_code == 404
