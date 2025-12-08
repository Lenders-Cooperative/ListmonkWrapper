"""
List-related API methods for ListMonk client.

This module provides mixin methods for managing lists.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from ._api_handler import JSONDict


class ListsMixin:
    """Mixin providing list-related API methods."""

    def get_lists(  # pylint: disable=too-many-arguments
        self,
        *,
        query: Optional[str] = None,
        status: Optional[str] = None,
        minimal: bool = False,
        tag: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        per_page: int | str = "all",
    ) -> JSONDict:
        """
        Retrieve all lists with optional filtering and sorting.

        Args:
            query: Optional string for list name search.
            status: Optional status filter - "active" or "archived".
                   Defaults to all lists if not specified.
            minimal: If True, returns lists without subscriber counts (faster).
            tag: Optional list of tags to filter by.
            order_by: Optional sort field - "name", "status", "created_at", "updated_at".
            order: Optional sorting order - "ASC" or "DESC".
            page: Page number for pagination.
            per_page: Results per page or "all".

        Returns:
            JSON dict with "data" containing "results" (list of lists)
            and pagination metadata.

        Examples:
            # Get all lists
            client.get_lists()

            # Get only active lists
            client.get_lists(status="active")

            # Search by name
            client.get_lists(query="newsletter")

            # Get archived lists without subscriber counts
            client.get_lists(status="archived", minimal=True)
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if query:
            params["query"] = query
        if status:
            params["status"] = status
        if minimal:
            params["minimal"] = True
        if tag is not None:
            # API expects multiple tag parameters: ?tag=tag1&tag=tag2
            params["tag"] = tag
        if order_by:
            params["order_by"] = order_by
        if order:
            params["order"] = order

        return self._api.send("GET", "/api/lists", params=params)

    def get_public_lists(self) -> JSONDict:
        """
        Retrieve public lists (unauthenticated endpoint).

        Returns only lists with type="public" and status="active".
        Archived lists are never shown.

        Returns:
            JSON array of lists with uuid and name fields.
        """
        # This endpoint doesn't require authentication
        # Create a temporary session without auth
        full_url = f"{self._api._host}/api/public/lists"  # pylint: disable=protected-access
        temp_session = requests.Session()
        response = temp_session.get(full_url, timeout=self._api.REQUEST_TIMEOUT)
        response.raise_for_status()
        if response.content:
            return response.json()
        return []

    def get_list(self, list_id: int) -> JSONDict:
        """
        Retrieve a specific list by ID.

        Args:
            list_id: ID of the list to retrieve.

        Returns:
            JSON dict with the list under the "data" key.
        """
        return self._api.send("GET", f"/api/lists/{list_id}")

    def create_list(  # pylint: disable=too-many-arguments
        self,
        name: str,
        list_type: str,
        optin: str,
        *,
        status: str = "active",
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> JSONDict:
        """
        Create a new list.

        Args:
            name: Name of the new list.
            list_type: Type of list - "private" or "public".
            optin: Opt-in type - "single" or "double".
            status: Status of the list - "active" or "archived" (default: "active").
            tags: Optional list of associated tags.
            description: Optional description of the list.

        Returns:
            JSON dict with the created list under the "data" key.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "type": list_type,
            "optin": optin,
            "status": status,
            "tags": tags or [],
        }
        if description:
            payload["description"] = description
        return self._api.send("POST", "/api/lists", payload=payload)

    def update_list(  # pylint: disable=too-many-arguments
        self,
        list_id: int,
        name: str,
        list_type: str,
        optin: str,
        *,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> JSONDict:
        """
        Update an existing list.

        Args:
            list_id: ID of the list to update.
            name: Updated name for the list.
            list_type: Updated type - "private" or "public".
            optin: Updated opt-in type - "single" or "double".
            status: Optional updated status - "active" or "archived".
            tags: Optional updated list of associated tags.
            description: Optional updated description of the list.

        Returns:
            JSON dict with the updated list under the "data" key.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "type": list_type,
            "optin": optin,
        }
        if status:
            payload["status"] = status
        if tags is not None:
            payload["tags"] = tags
        if description is not None:
            payload["description"] = description
        return self._api.send("PUT", f"/api/lists/{list_id}", payload=payload)

    def delete_list(self, list_id: int) -> JSONDict:
        """
        Delete a specific list by ID.

        Args:
            list_id: ID of the list to delete.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        return self._api.send("DELETE", f"/api/lists/{list_id}")

    def delete_lists(
        self,
        *,
        list_ids: Optional[List[int]] = None,
        query: Optional[str] = None,
    ) -> JSONDict:
        """
        Delete multiple lists by IDs or by search query.

        Args:
            list_ids: One or more list IDs to delete (required if query not provided).
            query: Search query to filter lists for deletion (required if list_ids not provided).

        Returns:
            JSON dict with `{"data": True}` on success.

        Examples:
            # Delete by IDs
            client.delete_lists(list_ids=[10, 11, 12])

            # Delete by search query
            client.delete_lists(query="test list")
        """
        if not list_ids and not query:
            raise ValueError("Either list_ids or query must be provided")

        params: Dict[str, Any] = {}
        if list_ids:
            # API expects multiple id query parameters: ?id=1&id=2
            params["id"] = list_ids
        if query:
            params["query"] = query

        return self._api.send("DELETE", "/api/lists", params=params)
