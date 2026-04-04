"""
Import-related API methods for ListMonk client.

This module provides mixin methods for managing subscriber imports.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ._api_handler import JSONDict


class ImportMixin:
    """Mixin providing import-related API methods."""

    def get_import_status(self) -> JSONDict:
        """
        Retrieve the status of an ongoing import.

        Returns:
            JSON dict with "data" containing import status:
            - name: Import file name
            - total: Total records to import
            - imported: Number of records imported so far
            - status: Import status ("none", "running", "finished", etc.)
        """
        return self._api.send("GET", "/api/import/subscribers")

    def get_import_logs(self) -> JSONDict:
        """
        Retrieve logs from an ongoing import.

        Returns:
            JSON dict with "data" containing the import log text.
        """
        return self._api.send("GET", "/api/import/subscribers/logs")

    def import_subscribers(  # pylint: disable=too-many-arguments
        self,
        file_path: str,
        mode: str,
        delimiter: str,
        *,
        lists: Optional[List[int]] = None,
        overwrite: bool = False,
        subscription_status: Optional[str] = None,
        overwrite_userinfo: Optional[bool] = None,
        overwrite_subscription_status: Optional[bool] = None,
    ) -> JSONDict:
        """
        Upload a CSV file (optionally ZIP compressed)
        for bulk subscriber import.

        Args:
            file_path: Path to the CSV or ZIP file to upload.
            mode: Import mode - "subscribe" or "blocklist".
            delimiter: Single character delimiter used
                    in CSV (e.g., "," or ";").
            lists: Optional list of list IDs to subscribe
                    imported subscribers to.
            overwrite: Whether to overwrite existing
                    subscriber data (default: False).
            subscription_status: Optional subscription
                    status (e.g., "confirmed", "unconfirmed").
            overwrite_userinfo: Optional granular overwrite
                    for subscriber profile data (v6.0.0+).
            overwrite_subscription_status: Optional granular overwrite
                    for subscription status data (v6.0.0+).

        Returns:
            JSON dict with import parameters that were used.

        Examples:
            # Import subscribers from CSV
            client.import_subscribers(
                file_path="/path/to/subscribers.csv",
                mode="subscribe",
                delimiter=",",
                lists=[1, 2],
                overwrite=True,
                subscription_status="confirmed"
            )

            # Blocklist emails from CSV
            client.import_subscribers(
                file_path="/path/to/blocklist.csv",
                mode="blocklist",
                delimiter=",",
            )
        """

        # Build params JSON string
        params_dict: Dict[str, Any] = {
            "mode": mode,
            "delim": delimiter,
        }
        if overwrite_userinfo is not None or overwrite_subscription_status is not None:
            if overwrite_userinfo is not None:
                params_dict["overwrite_userinfo"] = overwrite_userinfo
            if overwrite_subscription_status is not None:
                params_dict["overwrite_subscription_status"] = overwrite_subscription_status
        else:
            params_dict["overwrite"] = overwrite
        if lists is not None:
            params_dict["lists"] = lists
        if subscription_status is not None:
            params_dict["subscription_status"] = subscription_status

        params_json = json.dumps(params_dict)

        # Prepare multipart form data
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Import file not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        content_type = "application/zip" if ext.lower() == ".zip" else "text/csv"

        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, content_type)}
            data = {"params": params_json}

            return self._api.send_multipart(
                "POST", "/api/import/subscribers", files=files, data=data
            )

    def delete_import(self) -> JSONDict:
        """
        Stop and delete an ongoing import.

        Returns:
            JSON dict with "data" containing import status after deletion.
        """
        return self._api.send("DELETE", "/api/import/subscribers")
