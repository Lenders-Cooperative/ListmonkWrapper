"""
Media-related API methods for ListMonk client.

This module provides mixin methods for managing media files (images, PDFs, etc.).
"""

from __future__ import annotations

import os
from typing import Any, Dict

from ._api_handler import JSONDict


class MediaMixin:
    """Mixin providing media-related API methods."""

    def get_media(self) -> JSONDict:
        """
        Retrieve all uploaded media files.

        Returns:
            JSON dict with "data" containing pagination info and "results" list.
            The "data" dict includes:
            - results: List of media files (each with id, uuid, filename, etc.)
            - page: Current page number
            - per_page: Items per page
            - query: Search query (if any)
            Each media file in results includes:
            - id: Media ID
            - uuid: Media UUID
            - filename: Original filename
            - created_at: Creation timestamp
            - thumb_url: Thumbnail URL (if available)
            - uri: Media file URI
        """
        return self._api.send("GET", "/api/media")

    def get_media_file(self, media_id: int) -> JSONDict:
        """
        Retrieve a specific media file by ID.

        Args:
            media_id: ID of the media file to retrieve.

        Returns:
            JSON dict with "data" containing the media file details:
            - id: Media ID
            - uuid: Media UUID
            - filename: Original filename
            - content_type: MIME type
            - created_at: Creation timestamp
            - thumb_url: Thumbnail URL (if available)
            - provider: Storage provider (e.g., "filesystem")
            - meta: Additional metadata
            - url: Full URL to the media file
        """
        return self._api.send("GET", f"/api/media/{media_id}")

    def upload_media(self, file_path: str) -> JSONDict:
        """
        Upload a media file (image, PDF, etc.).

        Args:
            file_path: Path to the file to upload.

        Returns:
            JSON dict with "data" containing the uploaded media file details:
            - id: Media ID
            - uuid: Media UUID
            - filename: Original filename
            - created_at: Creation timestamp
            - thumb_uri: Thumbnail URI (if available)
            - uri: Media file URI

        Raises:
            FileNotFoundError: If the file doesn't exist.

        Examples:
            # Upload an image
            result = client.upload_media("/path/to/image.jpg")
            media_id = result["data"]["id"]

            # Upload a PDF
            result = client.upload_media("/path/to/document.pdf")
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")

        # Determine content type from file extension
        _, ext = os.path.splitext(file_path)
        content_type_map: Dict[str, str] = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".pdf": "application/pdf",
            ".svg": "image/svg+xml",
        }
        content_type = content_type_map.get(ext.lower(), "application/octet-stream")

        with open(file_path, "rb") as f:
            files: Dict[str, Any] = {"file": (os.path.basename(file_path), f, content_type)}

            return self._api.send_multipart("POST", "/api/media", files=files)

    def delete_media(self, media_id: int) -> JSONDict:
        """
        Delete an uploaded media file.

        Args:
            media_id: ID of the media file to delete.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        return self._api.send("DELETE", f"/api/media/{media_id}")
