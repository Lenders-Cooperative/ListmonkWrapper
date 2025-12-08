"""
Tests for media-related API endpoints.

This module covers all media operations:
- Retrieving media files
- Uploading media files
- Deleting media files
"""

import base64
import os
import tempfile

import pytest
import requests


def test_get_media(client):
    """Test retrieving all media files."""
    result = client.get_media()
    # Response should have "data" key with pagination info and "results" list
    assert "data" in result
    assert "results" in result["data"]
    assert isinstance(result["data"]["results"], list)


def test_get_media_file(client):
    """Test retrieving a specific media file."""
    # First, upload a media file to test with (use PNG - txt files are not supported)
    # Base64-encoded valid minimal PNG: 1x1 transparent pixel
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    png_data = base64.b64decode(png_base64)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(png_data)
        tmp_path = tmp_file.name

    try:
        # Upload a file first
        upload_result = client.upload_media(tmp_path)
        media_id = upload_result["data"]["id"]

        # Now retrieve it
        result = client.get_media_file(media_id)
        assert "data" in result
        assert result["data"]["id"] == media_id
        assert "filename" in result["data"]
        assert "uuid" in result["data"]

        # Clean up
        client.delete_media(media_id)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_upload_and_delete_media(client):
    """Test uploading and deleting a media file."""
    # Create a temporary test file (use PNG - txt files are not supported)
    # Base64-encoded valid minimal PNG: 1x1 transparent pixel
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    png_data = base64.b64decode(png_base64)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(png_data)
        tmp_path = tmp_file.name

    try:
        # Upload the file
        result = client.upload_media(tmp_path)
        assert "data" in result
        assert "id" in result["data"]
        media_id = result["data"]["id"]
        assert isinstance(media_id, int)

        # Verify we can retrieve it
        retrieved = client.get_media_file(media_id)
        assert retrieved["data"]["id"] == media_id

        # Delete the media file
        delete_result = client.delete_media(media_id)
        assert "data" in delete_result
        assert delete_result["data"] is True

        # Verify it's deleted (should raise HTTPError)
        with pytest.raises(requests.HTTPError):
            client.get_media_file(media_id)
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_upload_media_nonexistent_file(client):
    """Test that uploading a nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        client.upload_media("/nonexistent/path/to/file.jpg")


def test_upload_media_image(client):
    """Test uploading an image file."""
    # Create a temporary image file (minimal valid 1x1 transparent PNG)
    # Base64-encoded valid minimal PNG: 1x1 transparent pixel
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    png_data = base64.b64decode(png_base64)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(png_data)
        tmp_path = tmp_file.name

    try:
        result = client.upload_media(tmp_path)
        assert "data" in result
        assert "id" in result["data"]
        media_id = result["data"]["id"]

        # Clean up
        client.delete_media(media_id)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_delete_nonexistent_media(client):
    """Test that deleting a nonexistent media file raises HTTPError."""
    with pytest.raises(requests.HTTPError):
        client.delete_media(99999999)
