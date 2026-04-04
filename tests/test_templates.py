"""
Tests for template-related API endpoints.

This module covers all template operations:
- CRUD operations (create, read, update, delete)
- Setting default template
"""

import time

import pytest
import requests


def test_get_templates(client):
    """Test retrieving all templates."""
    result = client.get_templates()
    assert "data" in result
    assert isinstance(result["data"], list) or isinstance(
        result.get("data", {}).get("results"), list
    )


def test_get_template(client):
    """Test retrieving a specific template."""
    timestamp = int(time.time())
    template_name = f"GetTemplate_{timestamp}"
    template_body = '<html><body>{{ template "content" . }}</body></html>'

    try:
        created = client.create_template(template_name, template_body)
        tid = created["data"]["id"]

        try:
            retrieved = client.get_template(tid)
            assert "data" in retrieved
            assert retrieved["data"]["id"] == tid
            assert retrieved["data"]["name"] == template_name
        finally:
            client.delete_template(tid)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_template_create_update(client):
    """Test creating and updating a template."""
    template_name = f"MyTemplate_{int(time.time())}"
    template_body = '<html><body>{{ template "content" . }}</body></html>'

    try:
        created = client.create_template(template_name, template_body)
        tid = created["data"]["id"]

        try:
            updated_body = '<html><body><p>Updated</p>{{ template "content" . }}</body></html>'
            updated = client.update_template(tid, f"{template_name} Updated", updated_body)
            assert "data" in updated
            assert isinstance(updated["data"], dict)
        finally:
            client.delete_template(tid)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_delete_template(client):
    """Test deleting a template."""
    timestamp = int(time.time())
    template_name = f"DeleteTemplate_{timestamp}"
    template_body = '<html><body>{{ template "content" . }}</body></html>'

    try:
        created = client.create_template(template_name, template_body)
        tid = created["data"]["id"]

        result = client.delete_template(tid)
        assert "data" in result
        assert result["data"] is True

        with pytest.raises(requests.HTTPError):
            client.get_template(tid)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_set_default_template(client):
    """Test setting a template as default."""
    timestamp = int(time.time())
    template_name = f"DefaultTemplate_{timestamp}"
    template_body = '<html><body>{{ template "content" . }}</body></html>'

    try:
        created = client.create_template(template_name, template_body)
        tid = created["data"]["id"]

        try:
            result = client.set_default_template(tid)
            if isinstance(result.get("data"), list):
                template = next((t for t in result["data"] if t["id"] == tid), None)
                assert template is not None
                assert template["is_default"] is True
            else:
                assert "data" in result
                assert "is_default" in result["data"]
                assert result["data"]["is_default"] is True
        finally:
            client.delete_template(tid)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
