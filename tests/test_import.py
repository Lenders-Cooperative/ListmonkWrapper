"""
Tests for import-related API endpoints.

This module covers import operations:
- Getting import status
- Getting import logs
- Deleting/stopping imports
"""

import os
import tempfile
import time

import pytest


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


def test_import_overwrite_flags_v6(client, listmonk_version_tuple):
    """Test import overwrite flags in v6.0.0+."""
    if listmonk_version_tuple < (6, 0, 0):
        pytest.skip("Granular overwrite flags require Listmonk v6.0.0+")

    timestamp = int(time.time())
    list_id = None
    created_list = client.create_list(
        name=f"Import List {timestamp}", list_type="private", optin="single"
    )
    list_id = created_list["data"]["id"]

    email = f"import_{timestamp}@test.com"
    csv_content = f"email,name\n{email},Import User\n"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp_file:
            tmp_file.write(csv_content)
            tmp_path = tmp_file.name

        result = client.import_subscribers(
            file_path=tmp_path,
            mode="subscribe",
            delimiter=",",
            lists=[list_id],
            overwrite_userinfo=True,
            overwrite_subscription_status=False,
        )
        assert "data" in result

        for _ in range(20):
            status = client.get_import_status()
            if status["data"]["status"] in {"finished", "done", "complete", "completed"}:
                break
            time.sleep(0.5)

        results = client.query_subscribers(query=f"email = '{email}'")
        if results["data"]["results"]:
            subscriber_id = results["data"]["results"][0]["id"]
            client.delete_subscriber(subscriber_id)
    finally:
        client.delete_import()
        if list_id is not None:
            client.delete_list(list_id)
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
