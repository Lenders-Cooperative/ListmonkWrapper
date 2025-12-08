"""
Tests for import-related API endpoints.

This module covers import operations:
- Getting import status
- Getting import logs
- Deleting/stopping imports
"""


def test_get_import_status(client):
    """Test retrieving import status."""
    result = client.get_import_status()
    assert "data" in result
    assert "status" in result["data"]


def test_get_import_logs(client):
    """Test retrieving import logs."""
    result = client.get_import_logs()
    assert "data" in result
    # Logs may be empty string if no import has run
    assert isinstance(result["data"], str)


def test_delete_import(client):
    """Test deleting/stopping an import."""
    # This should work even if no import is running
    result = client.delete_import()
    assert "data" in result
    assert "status" in result["data"]
