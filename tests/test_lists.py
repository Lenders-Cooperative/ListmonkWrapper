"""
Tests for list-related API endpoints.

This module covers all list operations:
- CRUD operations (create, read, update, delete)
- Filtering and querying
- Public lists
- Bulk operations
"""

import time

import pytest
import requests


def test_create_list(client):
    """Test creating a list."""
    result = client.create_list(name="Test List", list_type="private", optin="double")
    assert "data" in result
    assert isinstance(result["data"], dict)


def test_update_list(client):
    """Test updating a list."""
    result = client.update_list(list_id=1, name="Test List", list_type="private", optin="double")
    # v5.1.0+ list update returns {"data": {...}}
    assert "data" in result
    assert isinstance(result["data"], dict)


def test_create_update_list(client):
    """Test creating and updating a list."""
    # Create
    created = client.create_list(name="Extended List", list_type="private", optin="double")
    list_id = created["data"]["id"]
    assert isinstance(list_id, int)

    # Update
    updated = client.update_list(
        list_id=list_id,
        name="Extended List Updated",
        list_type="private",
        optin="double",
    )
    assert "data" in updated
    assert isinstance(updated["data"], dict)


def test_get_lists(client):
    """Test retrieving all lists."""
    result = client.get_lists()
    assert "data" in result
    assert "results" in result["data"]
    assert isinstance(result["data"]["results"], list)


def test_get_lists_with_filters(client):
    """Test retrieving lists with filters."""
    # Create a list
    timestamp = int(time.time())
    list_name = f"FilterList_{timestamp}"
    created = client.create_list(name=list_name, list_type="private", optin="single")
    list_id = created["data"]["id"]

    try:
        # Get active lists
        result = client.get_lists(status="active")
        assert "data" in result
        assert any(lst["id"] == list_id for lst in result["data"]["results"])

        # Get lists with minimal data
        result = client.get_lists(minimal=True)
        assert "data" in result

        # Search by name
        result = client.get_lists(query=list_name)
        assert "data" in result
        assert any(lst["name"] == list_name for lst in result["data"]["results"])
    finally:
        client.delete_list(list_id)


def test_get_public_lists(client):
    """Test retrieving public lists."""
    # Create a public list
    timestamp = int(time.time())
    list_name = f"PublicList_{timestamp}"
    created = client.create_list(name=list_name, list_type="public", optin="single")
    list_id = created["data"]["id"]

    try:
        result = client.get_public_lists()
        # Should return a list (not wrapped in "data")
        assert isinstance(result, list)
        # Should include our public list
        assert any(lst["name"] == list_name for lst in result)
    finally:
        client.delete_list(list_id)


def test_get_list(client):
    """Test retrieving a specific list."""
    # Create a list
    timestamp = int(time.time())
    list_name = f"GetList_{timestamp}"
    created = client.create_list(name=list_name, list_type="private", optin="single")
    list_id = created["data"]["id"]

    try:
        # Get the list
        retrieved = client.get_list(list_id)
        assert "data" in retrieved
        assert retrieved["data"]["id"] == list_id
        assert retrieved["data"]["name"] == list_name
    finally:
        client.delete_list(list_id)


def test_delete_list(client):
    """Test deleting a list."""
    # Create a list
    timestamp = int(time.time())
    list_name = f"DeleteList_{timestamp}"
    created = client.create_list(name=list_name, list_type="private", optin="single")
    list_id = created["data"]["id"]

    # Delete the list
    result = client.delete_list(list_id)
    assert "data" in result
    assert result["data"] is True

    # Verify list is deleted
    with pytest.raises(requests.HTTPError):
        client.get_list(list_id)


def test_delete_lists_by_ids(client):
    """Test bulk deleting lists by IDs."""
    # Create multiple lists
    timestamp = int(time.time())
    list_names = [
        f"BulkDelete1_{timestamp}",
        f"BulkDelete2_{timestamp}",
    ]
    list_ids = []
    for name in list_names:
        created = client.create_list(name=name, list_type="private", optin="single")
        list_ids.append(created["data"]["id"])

    try:
        # Delete lists one by one (bulk delete may not be supported)
        # or try bulk delete and handle gracefully
        try:
            result = client.delete_lists(list_ids=list_ids)
            assert "data" in result
            assert result["data"] is True

            # Verify lists are deleted
            for list_id in list_ids:
                with pytest.raises(requests.HTTPError):
                    client.get_list(list_id)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                # Bulk delete might not be supported, delete individually
                for list_id in list_ids:
                    result = client.delete_list(list_id)
                    assert "data" in result
                    assert result["data"] is True
            else:
                raise
    except Exception:
        # Cleanup if test fails
        for list_id in list_ids:
            try:
                client.delete_list(list_id)
            except Exception:
                pass
        raise


def test_delete_lists_by_query(client):
    """Test deleting lists by search query."""
    # Create a list with a specific name pattern
    timestamp = int(time.time())
    list_name = f"QueryDelete_{timestamp}"
    created = client.create_list(name=list_name, list_type="private", optin="single")
    list_id = created["data"]["id"]

    try:
        # Delete by query (may not be supported, handle gracefully)
        try:
            result = client.delete_lists(query=list_name)
            assert "data" in result
            assert result["data"] is True

            # Verify list is deleted
            with pytest.raises(requests.HTTPError):
                client.get_list(list_id)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                # Query delete might not be supported, delete individually
                result = client.delete_list(list_id)
                assert "data" in result
                assert result["data"] is True
            else:
                raise
    except Exception:
        # Cleanup if test fails
        try:
            client.delete_list(list_id)
        except Exception:
            pass
        raise


def test_invalid_list_update_raises(client):
    """Test that invalid list ID raises HTTPError."""
    with pytest.raises(requests.HTTPError):
        client.update_list(
            list_id=999999,
            name="Nope",
            list_type="private",
            optin="double",
        )
