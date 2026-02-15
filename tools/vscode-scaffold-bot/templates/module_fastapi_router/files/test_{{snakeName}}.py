"""Tests for {{PascalName}} router."""

import pytest
from fastapi.testclient import TestClient


def test_list_{{snakeName}}(client: TestClient):
    response = client.get("/{{kebabName}}/")
    assert response.status_code == 200


def test_get_{{snakeName}}(client: TestClient):
    response = client.get("/{{kebabName}}/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_create_{{snakeName}}(client: TestClient):
    response = client.post("/{{kebabName}}/")
    assert response.status_code == 200
    assert response.json()["status"] == "created"
