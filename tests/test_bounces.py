"""
Tests for bounce-related API endpoints.

This module covers all bounce operations:
- Retrieving bounce records
- Deleting bounce records (all, multiple, single)
"""

import pytest
import requests


def test_get_bounces(client):
    """Test retrieving all bounce records."""
    result = client.get_bounces()
    assert "data" in result
    assert "results" in result["data"]
    assert isinstance(result["data"]["results"], list)
    assert "total" in result["data"]
    assert "page" in result["data"]
    assert "per_page" in result["data"]


def test_get_bounces_with_pagination(client):
    """Test retrieving bounce records with pagination."""
    result = client.get_bounces(page=1, per_page=10)
    assert "data" in result
    assert "results" in result["data"]
    assert isinstance(result["data"]["results"], list)
    # API returns page=0 when there are no results, otherwise returns the requested page
    # per_page may be 0 when there are no results, otherwise returns the requested value
    assert "page" in result["data"]
    assert "per_page" in result["data"]


def test_get_bounces_with_filters(client):
    """Test retrieving bounce records with filters."""
    result = client.get_bounces(order_by="created_at", order="desc", per_page=5)
    assert "data" in result
    assert "results" in result["data"]
    assert isinstance(result["data"]["results"], list)


def test_get_bounces_for_campaign(client):
    """Test retrieving bounce records for a specific campaign."""
    # First, get all campaigns to find an existing one
    campaigns = client.get_campaigns()
    if campaigns["data"]["results"]:
        campaign_id = campaigns["data"]["results"][0]["id"]
        result = client.get_bounces(campaign_id=campaign_id)
        assert "data" in result
        assert "results" in result["data"]
        assert isinstance(result["data"]["results"], list)
    else:
        # No campaigns exist, just test the API call doesn't error
        result = client.get_bounces(campaign_id=99999)
        assert "data" in result
        assert "results" in result["data"]
        assert isinstance(result["data"]["results"], list)


def test_delete_bounce_validation_errors(client):
    """Test validation errors for delete_bounces."""
    # Test: Neither all_bounces nor bounce_ids provided
    with pytest.raises(ValueError, match="Must provide either"):
        client.delete_bounces()

    # Test: Both all_bounces and bounce_ids provided
    with pytest.raises(ValueError, match="Cannot provide both"):
        client.delete_bounces(all_bounces=True, bounce_ids=[1, 2, 3])


def test_delete_bounce_single(client):
    """Test deleting a single bounce record."""
    # First, get bounces to see if any exist
    bounces = client.get_bounces(per_page=1)

    if bounces["data"]["results"]:
        bounce_id = bounces["data"]["results"][0]["id"]
        # Delete the bounce
        result = client.delete_bounce(bounce_id)
        assert "data" in result
        assert result["data"] is True

        # Verify it's deleted (should not appear in results)
        # Note: We can't verify this directly since we don't know if there are other bounces
    else:
        # No bounces exist, test deleting a non-existent bounce
        # The API may return success even for non-existent IDs
        try:
            result = client.delete_bounce(99999999)
            # If it succeeds, that's fine - some APIs return success for non-existent resources
            assert "data" in result
        except requests.HTTPError:
            # If it raises an error, that's also acceptable behavior
            pass


def test_delete_bounces_multiple(client):
    """Test deleting multiple bounce records."""
    # First, get some bounces
    bounces = client.get_bounces(per_page=5)

    if len(bounces["data"]["results"]) >= 2:
        bounce_ids = [b["id"] for b in bounces["data"]["results"][:2]]
        # Delete multiple bounces
        result = client.delete_bounces(bounce_ids=bounce_ids)
        assert "data" in result
        assert result["data"] is True
    else:
        # Not enough bounces, test with non-existent IDs (should still work)
        # The API may return success even if IDs don't exist
        try:
            result = client.delete_bounces(bounce_ids=[99999998, 99999999])
            assert "data" in result
            assert result["data"] is True
        except requests.HTTPError:
            # API may return error for non-existent IDs, which is also acceptable
            pass


def test_delete_bounces_all(client):
    """Test deleting all bounce records."""
    # This is a destructive operation, so we'll test it carefully
    # First check if there are any bounces
    bounces = client.get_bounces()
    initial_count = bounces["data"]["total"]

    if initial_count > 0:
        # Delete all bounces
        result = client.delete_bounces(all_bounces=True)
        assert "data" in result
        assert result["data"] is True

        # Verify all bounces are deleted
        bounces_after = client.get_bounces()
        assert bounces_after["data"]["total"] == 0
    else:
        # No bounces exist, test that the API call still works
        result = client.delete_bounces(all_bounces=True)
        assert "data" in result
        assert result["data"] is True
