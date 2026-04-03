"""
Subscriber-related API methods for ListMonk client.

This module provides mixin methods for managing subscribers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._api_handler import JSONDict


class SubscriberMixin:
    """Mixin providing subscriber-related API methods."""

    def get_subscriber(self, subscriber_id: int) -> JSONDict:
        """
        Retrieve a single subscriber by ID.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.

        Returns:
            A JSON dict containing the subscriber under the "data" key.
        """
        return self._api.send("GET", f"/api/subscribers/{subscriber_id}")

    def create_subscriber(  # pylint: disable=too-many-arguments
        self,
        email: str,
        name: str,
        *,
        status: str = "enabled",
        attribs: Optional[JSONDict] = None,
        lists: Optional[List[int]] = None,
        preconfirm_subscriptions: bool = False,
    ) -> JSONDict:
        """
        Create a new subscriber.

        Args:
            email: Subscriber email address.
            name: Subscriber display name.
            status: Subscriber status - "enabled" or "blocklisted"
                    (default: "enabled").
            attribs: Optional metadata stored in `attribs` JSON.
            lists: Optional list of list IDs to subscribe the user to.
            preconfirm_subscriptions:
                If True, subscriptions are marked as confirmed (default: False)
                and no opt-in emails are sent for double opt-in lists.

        Returns:
            JSON dict with the created subscriber under the "data" key.
        """
        payload = {
            "email": email,
            "name": name,
            "status": status,
            "attribs": attribs or {},
            "lists": lists or [],
            "preconfirm_subscriptions": preconfirm_subscriptions,
        }
        return self._api.send("POST", "/api/subscribers", payload=payload)

    def update_subscriber(  # pylint: disable=too-many-arguments
        self,
        subscriber_id: int,
        email: str,
        name: str,
        *,
        attribs: Optional[JSONDict] = None,
        lists: Optional[List[int]] = None,
    ) -> JSONDict:
        """
        Update an existing subscriber.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.
            email: Updated email address.
            name: Updated display name.
            attribs: Optional updated metadata.
            lists: Optional updated list of list IDs.

        Returns:
            JSON dict, typically with a "message": "ok" payload.
        """
        payload = {
            "email": email,
            "name": name,
            "attribs": attribs or {},
            "lists": lists or [],
        }
        return self._api.send("PUT", f"/api/subscribers/{subscriber_id}", payload=payload)

    def delete_subscriber(self, subscriber_id: int) -> JSONDict:
        """
        Delete a subscriber by ID.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.

        Returns:
            A JSON dict containing ``{"data": True}`` for successful deletion.
        """
        return self._api.send("DELETE", f"/api/subscribers/{subscriber_id}")

    def query_subscribers(  # pylint: disable=too-many-arguments
        self,
        *,
        query: Optional[str] = None,
        list_id: Optional[List[int]] = None,
        subscription_status: Optional[str] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        per_page: int | str = "all",
        **kwargs: Any,
    ) -> JSONDict:
        """
        Query subscribers with optional SQL-like query filters.

        Args:
            query: Optional SQL-like query string for filtering.
                  Examples:
                  - "email LIKE '%example%'" - Search by email pattern
                  - "name='John Doe'" - Exact name match
                  - "status='enabled'" - Filter by status
                  See Listmonk query documentation for full syntax.
            list_id: Optional list of list IDs to filter by.
            subscription_status: Optional subscription status to filter by
                               (requires list_id to be set).
            order_by: Optional sorting field - "name", "status",
            "created_at", "updated_at".
            order: Optional sorting order - "ASC" or "DESC".
            page: Page number for paginated results.
            per_page: Results per page or "all".
            **kwargs: Additional query parameters passed as-is.

        Returns:
            JSON dict with "data" containing "results" (list of subscribers)
            and pagination metadata ("total", "page", "per_page").

        Examples:
            # Search by email
            client.query_subscribers(query="email LIKE '%example%'")

            # Filter by list ID
            client.query_subscribers(list_id=[1, 2])

            # Filter by list and subscription status
            client.query_subscribers(
                list_id=[1], subscription_status="confirmed"
            )

            # Sort by name descending
            client.query_subscribers(order_by="name", order="DESC")

            # Combine with pagination
            client.query_subscribers(
                query="email LIKE '%test%'", page=1, per_page=20
            )
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page, **kwargs}

        if query:
            params["query"] = query
        if list_id is not None:
            # API expects multiple list_id
            # query parameters: ?list_id=1&list_id=2
            # requests handles this when we pass a list
            params["list_id"] = list_id
        if subscription_status:
            params["subscription_status"] = subscription_status
        if order_by:
            params["order_by"] = order_by
        if order:
            params["order"] = order

        return self._api.send("GET", "/api/subscribers", params=params)

    def export_subscriber(self, subscriber_id: int) -> JSONDict:
        """
        Export a specific subscriber.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.

        Returns:
            JSON dict with exported subscriber data.
        """
        return self._api.send("GET", f"/api/subscribers/{subscriber_id}/export")

    def get_subscriber_bounces(self, subscriber_id: int) -> JSONDict:
        """
        Retrieve bounce records for a specific subscriber.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.

        Returns:
            JSON dict with bounce records under the "data" key.
        """
        return self._api.send("GET", f"/api/subscribers/{subscriber_id}/bounces")

    def send_optin_email(self, subscriber_id: int) -> JSONDict:
        """
        Send opt-in confirmation email to a subscriber.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        return self._api.send("POST", f"/api/subscribers/{subscriber_id}/optin", payload={})

    def create_public_subscription(
        self,
        email: str,
        list_uuids: List[str],
        *,
        name: Optional[str] = None,
    ) -> JSONDict:
        """
        Create a public subscription (no authentication required).

        Args:
            email: Subscriber email address.
            list_uuids: List of list UUIDs to subscribe to.
            name: Optional subscriber name.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        payload: Dict[str, Any] = {
            "email": email,
            "list_uuids": list_uuids,
        }
        if name:
            payload["name"] = name
        return self._api.send("POST", "/api/public/subscription", payload=payload)

    def modify_subscriber_lists(
        self,
        subscriber_ids: List[int],
        action: str,
        target_list_ids: List[int],
        *,
        status: Optional[str] = None,
    ) -> JSONDict:
        """
        Modify subscriber list memberships in bulk.

        Args:
            subscriber_ids: Array of subscriber IDs to modify.
            action: Action to apply - "add", "remove", or "unsubscribe".
            target_list_ids: Array of list IDs to modify.
            status: Required for "add" action - "confirmed", "unconfirmed",
            or "unsubscribed".

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        payload: Dict[str, Any] = {
            "ids": subscriber_ids,
            "action": action,
            "target_list_ids": target_list_ids,
        }
        if status:
            payload["status"] = status
        return self._api.send("PUT", "/api/subscribers/lists", payload=payload)

    def blocklist_subscriber(self, subscriber_id: int) -> JSONDict:
        """
        Blocklist a specific subscriber.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        return self._api.send("PUT", f"/api/subscribers/{subscriber_id}/blocklist")

    def blocklist_subscribers(self, subscriber_ids: List[int]) -> JSONDict:
        """
        Blocklist multiple subscribers.

        Args:
            subscriber_ids: List of subscriber IDs to blocklist.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        payload = {"ids": subscriber_ids}
        return self._api.send("PUT", "/api/subscribers/blocklist", payload=payload)

    def blocklist_subscribers_by_query(
        self,
        query: str,
        *,
        list_ids: Optional[List[int]] = None,
    ) -> JSONDict:
        """
        Blocklist subscribers based on SQL expression.

        Args:
            query: SQL expression to filter subscribers
                    (e.g., "name LIKE 'John%'")
            list_ids: Optional list IDs to limit the filtering to.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        payload: Dict[str, Any] = {"query": query}
        if list_ids is not None:
            payload["list_ids"] = list_ids
        return self._api.send("PUT", "/api/subscribers/query/blocklist", payload=payload)

    def delete_subscribers(self, subscriber_ids: List[int]) -> JSONDict:
        """
        Delete one or more subscribers by ID.

        Args:
            subscriber_ids: List of subscriber IDs to delete.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        # API expects multiple id query parameters: ?id=1&id=2
        # requests handles this when we pass a list
        params = {"id": subscriber_ids}
        return self._api.send("DELETE", "/api/subscribers", params=params)

    def delete_subscribers_by_query(
        self,
        *,
        query: Optional[str] = None,
        list_ids: Optional[List[int]] = None,
        all_subscribers: bool = False,
    ) -> JSONDict:
        """
        Delete subscribers based on SQL expression.

        Args:
            query: Optional SQL expression to filter subscribers.
            list_ids: Optional list IDs to limit the filtering to.
            all_subscribers: If True, ignores query and deletes
            all subscribers.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        payload: Dict[str, Any] = {}
        if query:
            payload["query"] = query
        if list_ids is not None:
            payload["list_ids"] = list_ids
        if all_subscribers:
            payload["all"] = True
        return self._api.send("POST", "/api/subscribers/query/delete", payload=payload)

    def delete_subscriber_bounces(self, subscriber_id: int) -> JSONDict:
        """
        Delete bounce records for a specific subscriber.

        Args:
            subscriber_id: Internal Listmonk subscriber ID.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        return self._api.send("DELETE", f"/api/subscribers/{subscriber_id}/bounces")
