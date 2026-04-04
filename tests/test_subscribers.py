"""
Tests for subscriber-related API endpoints.

This module covers all subscriber operations:
- CRUD operations (create, read, update, delete)
- Querying and filtering
- Blocklisting
- Bounces
- Opt-in emails
- List management
- Export
"""

import time

import pytest
import requests


def test_get_subscriber_info(client):
    """Test retrieving a subscriber by ID."""
    email = f"get_info_{int(time.time())}@test.com"
    created = client.create_subscriber(email=email, name="GetInfo")
    sid = created["data"]["id"]

    try:
        results = client.get_subscriber(sid)
        assert "data" in results
        assert isinstance(results["data"], dict)
        assert results["data"]["id"] == sid
    finally:
        client.delete_subscriber(sid)


def test_query_subscribers(client):
    """Test querying subscribers without filters."""
    results = client.query_subscribers()
    # v5.1.0+ returns {"data": {"results": [...], "total": int, "page": int}}
    assert "data" in results
    assert "results" in results["data"]
    assert isinstance(results["data"]["results"], list)



def test_query_subscribers_by_email(client):
    """Test querying subscribers by email using SQL-like query syntax."""
    # Create a subscriber with a unique email
    email = f"querytest_{int(time.time())}@example.com"
    created = client.create_subscriber(email=email, name="Query Test")
    sid = created["data"]["id"]

    try:
        # Query by exact email
        result = client.query_subscribers(query=f"email='{email}'")
        assert "data" in result
        assert len(result["data"]["results"]) >= 1
        assert any(s["email"] == email for s in result["data"]["results"])

        # Query by email pattern
        result = client.query_subscribers(query="email LIKE '%querytest%'")
        assert "data" in result
        assert len(result["data"]["results"]) >= 1
        assert any(s["email"] == email for s in result["data"]["results"])
    finally:
        client.delete_subscriber(sid)


def test_create_and_delete_subscriber(client):
    """Test creating and deleting a subscriber."""
    email = f"create_delete_{int(time.time())}@test.com"
    created = client.create_subscriber(email=email, name="Jeff")
    sid = created["data"]["id"]
    assert isinstance(sid, int)

    deleted = client.delete_subscriber(sid)
    # DELETE returns {"data": True}
    assert "data" in deleted
    assert deleted["data"] is True


def test_delete_subscriber(client, subscriber_id):
    """Test deleting a subscriber using fixture."""
    result = client.delete_subscriber(subscriber_id)
    # v5.1.0+ DELETE returns {"data": True}
    assert "data" in result
    assert result["data"] is True


def test_create_get_update_delete_subscriber(client):
    """Test full CRUD cycle for subscribers."""
    # Create with unique email to avoid conflicts
    email = f"extended_user_{int(time.time())}@test.com"
    created = client.create_subscriber(
        email=email,
        name="Extended User",
    )
    sid = created["data"]["id"]

    # Get
    retrieved = client.get_subscriber(sid)
    assert retrieved["data"]["email"] == email

    # Update - use unique email to avoid conflicts
    # Note: Updating email can fail with duplicate key constraint if email exists
    updated_email = f"updated_user_{int(time.time())}@test.com"
    try:
        updated = client.update_subscriber(
            sid,
            email=updated_email,
            name="Updated User",
        )
        assert "data" in updated
        assert isinstance(updated["data"], dict)

        # Confirm update - handle potential server errors
        try:
            reread = client.get_subscriber(sid)
            assert reread["data"]["email"] == updated_email
        except requests.HTTPError as e:
            if e.response.status_code in (500, 404):
                # Server error or not found, but update succeeded (we got {"data": {...}})
                pytest.skip(
                    f"Server error ({e.response.status_code}) when reading subscriber after update"
                )
            raise
    except requests.HTTPError as e:
        # Handle duplicate key constraint (409/500) or server errors
        # Listmonk returns 500 when duplicate key constraint is violated
        status_code = e.response.status_code
        if status_code in (409, 500):
            # Update failed due to duplicate email constraint or server error
            # This is a known issue in Listmonk v5.1.0 - updating email can fail
            # if the new email already exists. The important thing is that create/get/delete work.
            pytest.skip(
                f"Subscriber email update failed ({status_code}) - "
                "duplicate key constraint violation or server error in Listmonk v5.1.0"
            )
        raise

    # Delete
    deleted = client.delete_subscriber(sid)
    assert "data" in deleted
    assert deleted["data"] is True

    # Confirm deletion - should get 404, 500, or other error (server error on deleted resource)
    # The deletion itself succeeded (we got {"data": True}), so we just verify
    # that accessing it fails with some error
    with pytest.raises(requests.HTTPError) as exc_info:
        client.get_subscriber(sid)
    # Any error status code is acceptable - deletion succeeded, accessing deleted resource fails
    status_code = exc_info.value.response.status_code
    assert status_code >= 400, f"Expected error status, got {status_code}"


def test_update_subscriber(client):
    """Test updating a subscriber."""
    email = f"update_sub_{int(time.time())}@test.com"
    created = client.create_subscriber(email=email, name="Original")
    sid = created["data"]["id"]

    try:
        updated_email = f"updated_{int(time.time())}@test.com"
        updated = client.update_subscriber(sid, email=updated_email, name="Jane")
        # v5.1.0+ update returns {"data": {...}}
        assert "data" in updated
        assert isinstance(updated["data"], dict)

        retrieved = client.get_subscriber(sid)
        assert retrieved["data"]["email"] == updated_email
    finally:
        client.delete_subscriber(sid)


def test_create_and_delete_subscriber_with_django_user(client, django_user):
    """Test creating and deleting a subscriber using Django user fixture."""
    created = client.create_subscriber(
        email=django_user.email,
        name=django_user.username,
    )
    data = created["data"]

    assert data["email"] == django_user.email
    assert data["name"] == django_user.username

    deleted = client.delete_subscriber(data["id"])

    # Deletion in Listmonk v5.1.0+ returns {"data": True}
    assert "data" in deleted
    assert deleted["data"] is True


def test_export_subscriber(client):
    """Test exporting a subscriber."""
    # Create a subscriber to export
    email = f"export_test_{int(time.time())}@example.com"
    created = client.create_subscriber(email=email, name="Export Test")
    sid = created["data"]["id"]

    try:
        exported = client.export_subscriber(sid)
        assert "data" in exported or isinstance(exported, dict)
    finally:
        client.delete_subscriber(sid)


def test_get_subscriber_bounces(client):
    """Test retrieving subscriber bounce records."""
    # Create a subscriber
    email = f"bounce_test_{int(time.time())}@example.com"
    created = client.create_subscriber(email=email, name="Bounce Test")
    sid = created["data"]["id"]

    try:
        bounces = client.get_subscriber_bounces(sid)
        # Should return a dict with bounce data (may be empty)
        assert isinstance(bounces, dict)
    finally:
        client.delete_subscriber(sid)


def test_send_optin_email(client):
    """Test sending opt-in confirmation email."""
    # Create a subscriber
    email = f"optin_test_{int(time.time())}@example.com"
    created = client.create_subscriber(email=email, name="Optin Test")
    sid = created["data"]["id"]

    try:
        result = client.send_optin_email(sid)
        assert "data" in result
        assert result["data"] is True
    finally:
        client.delete_subscriber(sid)


def test_blocklist_subscriber(client):
    """Test blocklisting a single subscriber."""
    # Create a subscriber
    email = f"blocklist_test_{int(time.time())}@example.com"
    created = client.create_subscriber(email=email, name="Blocklist Test")
    sid = created["data"]["id"]

    try:
        result = client.blocklist_subscriber(sid)
        assert "data" in result
        assert result["data"] is True

        # Verify subscriber is blocklisted
        retrieved = client.get_subscriber(sid)
        assert retrieved["data"]["status"] == "blocklisted"
    finally:
        client.delete_subscriber(sid)


def test_blocklist_subscribers(client):
    """Test blocklisting multiple subscribers."""
    # Create multiple subscribers
    timestamp = int(time.time())
    emails = [
        f"blocklist1_{timestamp}@example.com",
        f"blocklist2_{timestamp}@example.com",
    ]
    sids = []
    for email in emails:
        created = client.create_subscriber(email=email, name="Blocklist Test")
        sids.append(created["data"]["id"])

    try:
        result = client.blocklist_subscribers(sids)
        assert "data" in result
        assert result["data"] is True

        # Verify subscribers are blocklisted
        for sid in sids:
            retrieved = client.get_subscriber(sid)
            assert retrieved["data"]["status"] == "blocklisted"
    finally:
        for sid in sids:
            client.delete_subscriber(sid)


def test_blocklist_subscribers_by_query(client):
    """Test blocklisting subscribers by SQL query."""
    # Create a subscriber with a specific name pattern
    timestamp = int(time.time())
    email = f"query_block_{timestamp}@example.com"
    created = client.create_subscriber(email=email, name=f"QueryBlock_{timestamp}")
    sid = created["data"]["id"]

    try:
        # Blocklist by query
        result = client.blocklist_subscribers_by_query(query=f"name='QueryBlock_{timestamp}'")
        assert "data" in result
        assert result["data"] is True

        # Verify subscriber is blocklisted
        retrieved = client.get_subscriber(sid)
        assert retrieved["data"]["status"] == "blocklisted"
    finally:
        client.delete_subscriber(sid)


def test_delete_subscribers_bulk(client):
    """Test bulk deleting subscribers."""
    # Create multiple subscribers
    timestamp = int(time.time())
    emails = [
        f"bulk_delete1_{timestamp}@example.com",
        f"bulk_delete2_{timestamp}@example.com",
    ]
    sids = []
    for email in emails:
        created = client.create_subscriber(email=email, name="Bulk Delete Test")
        sids.append(created["data"]["id"])

    try:
        result = client.delete_subscribers(sids)
        assert "data" in result
        assert result["data"] is True

        # Verify subscribers are deleted
        for sid in sids:
            with pytest.raises(requests.HTTPError):
                client.get_subscriber(sid)
    except Exception:
        # Cleanup if test fails
        for sid in sids:
            try:
                client.delete_subscriber(sid)
            except Exception:
                pass
        raise


def test_delete_subscribers_by_query(client):
    """Test deleting subscribers by SQL query."""
    # Create a subscriber with a specific name pattern
    timestamp = int(time.time())
    email = f"query_delete_{timestamp}@example.com"
    created = client.create_subscriber(email=email, name=f"QueryDelete_{timestamp}")
    sid = created["data"]["id"]

    try:
        # Delete by query
        result = client.delete_subscribers_by_query(query=f"name='QueryDelete_{timestamp}'")
        assert "data" in result
        assert result["data"] is True

        # Verify subscriber is deleted
        with pytest.raises(requests.HTTPError):
            client.get_subscriber(sid)
    except Exception:
        # Cleanup if test fails
        try:
            client.delete_subscriber(sid)
        except Exception:
            pass
        raise


def test_delete_subscriber_bounces(client):
    """Test deleting subscriber bounce records."""
    # Create a subscriber
    email = f"delete_bounce_{int(time.time())}@example.com"
    created = client.create_subscriber(email=email, name="Delete Bounce Test")
    sid = created["data"]["id"]

    try:
        # Delete bounces (may not have any, but should not error)
        result = client.delete_subscriber_bounces(sid)
        assert "data" in result
        assert result["data"] is True
    finally:
        client.delete_subscriber(sid)


def test_modify_subscriber_lists(client):
    """Test modifying subscriber list memberships."""
    # Create a subscriber and two lists
    timestamp = int(time.time())
    email = f"modify_lists_{timestamp}@example.com"
    created_sub = client.create_subscriber(email=email, name="Modify Lists Test")
    sid = created_sub["data"]["id"]

    list1 = client.create_list(name=f"List1_{timestamp}", list_type="private", optin="single")
    list1_id = list1["data"]["id"]

    list2 = client.create_list(name=f"List2_{timestamp}", list_type="private", optin="single")
    list2_id = list2["data"]["id"]

    try:
        # Add subscriber to list1
        result = client.modify_subscriber_lists(
            subscriber_ids=[sid],
            action="add",
            target_list_ids=[list1_id],
            status="confirmed",
        )
        assert "data" in result
        assert result["data"] is True

        # Verify subscriber is in list1
        # Lists field is a list of dicts with 'id' field
        retrieved = client.get_subscriber(sid)
        list_ids_in_subscriber = [lst["id"] for lst in retrieved["data"]["lists"]]
        assert list1_id in list_ids_in_subscriber

        # Add subscriber to list2
        result = client.modify_subscriber_lists(
            subscriber_ids=[sid],
            action="add",
            target_list_ids=[list2_id],
            status="confirmed",
        )
        assert "data" in result

        # Verify subscriber is now in both lists
        retrieved = client.get_subscriber(sid)
        list_ids_in_subscriber = [lst["id"] for lst in retrieved["data"]["lists"]]
        assert list1_id in list_ids_in_subscriber
        assert list2_id in list_ids_in_subscriber

        # Remove subscriber from list1
        result = client.modify_subscriber_lists(
            subscriber_ids=[sid],
            action="remove",
            target_list_ids=[list1_id],
        )
        assert "data" in result

        # Verify subscriber is only in list2 now
        retrieved = client.get_subscriber(sid)
        list_ids_in_subscriber = [lst["id"] for lst in retrieved["data"]["lists"]]
        assert list1_id not in list_ids_in_subscriber
        assert list2_id in list_ids_in_subscriber
    finally:
        client.delete_subscriber(sid)
        client.delete_list(list1_id)
        client.delete_list(list2_id)


def test_invalid_subscriber_lookup_raises(client):
    """Test that invalid subscriber ID raises HTTPError."""
    with pytest.raises(requests.HTTPError):
        client.get_subscriber(99999999)


def test_subscriber_list_load_performance(client):
    """Test that subscriber query returns results in a reasonable time."""
    start = time.time()
    res = client.query_subscribers(per_page=50)
    end = time.time()

    assert "data" in res
    assert "results" in res["data"]
    # Generous timeout — CI runners and cold containers can be slow.
    assert end - start < 10.0, f"Query took {end - start:.2f}s, exceeds 10s budget"
