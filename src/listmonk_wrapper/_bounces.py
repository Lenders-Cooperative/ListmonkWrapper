"""
Bounce-related API methods for ListMonk client.

This module provides mixin methods for managing bounce records.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from ._api_handler import JSONDict


class BouncesMixin:
    """Mixin providing bounce-related API methods."""

    def get_bounces(  # pylint: disable=too-many-arguments
        self,
        *,
        campaign_id: Optional[int] = None,
        page: Optional[int] = None,
        per_page: Optional[Union[int, str]] = None,
        source: Optional[str] = None,
        order_by: Optional[str] = None,
        order: Optional[str] = None,
    ) -> JSONDict:
        """
        Retrieve bounce records.

        Args:
            campaign_id: Optional campaign ID to filter bounces for a specific campaign.
            page: Page number for pagination.
            per_page: Results per page. Set to 'all' to return all results.
            source: Optional source filter.
            order_by: Field to order by. Options: "email", "campaign_name", "source", "created_at".
            order: Sort order - "asc" or "desc".

        Returns:
            JSON dict with "data" containing pagination info and "results" list.
            The "data" dict includes:
            - results: List of bounce records (each with id, type, source, email, etc.)
            - total: Total number of bounce records
            - page: Current page number
            - per_page: Items per page
            - query: Search query (if any)
            Each bounce record includes:
            - id: Bounce ID
            - type: Bounce type ("hard" or "soft")
            - source: Bounce source
            - email: Email address that bounced
            - subscriber_id: Subscriber ID (if applicable)
            - subscriber_uuid: Subscriber UUID (if applicable)
            - campaign: Campaign info (id, name)
            - created_at: Creation timestamp
            - meta: Additional metadata

        Examples:
            # Get all bounces
            result = client.get_bounces()

            # Get bounces for a specific campaign
            result = client.get_bounces(campaign_id=1)

            # Get bounces with pagination
            result = client.get_bounces(page=1, per_page=10, order_by="created_at", order="desc")
        """
        params: Dict[str, Any] = {}
        if campaign_id is not None:
            params["campaign_id"] = campaign_id
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if source is not None:
            params["source"] = source
        if order_by is not None:
            params["order_by"] = order_by
        if order is not None:
            params["order"] = order

        return self._api.send("GET", "/api/bounces", params=params)

    def delete_bounces(
        self,
        *,
        all_bounces: bool = False,
        bounce_ids: Optional[List[int]] = None,
    ) -> JSONDict:
        """
        Delete bounce records.

        Args:
            all_bounces: If True, delete all bounce records. Requires explicit True.
            bounce_ids: Optional list of bounce IDs to delete. Can be used to delete
                       multiple specific bounces.

        Returns:
            JSON dict with `{"data": True}` on success.

        Raises:
            ValueError: If neither all_bounces nor bounce_ids is provided, or if both are provided.

        Examples:
            # Delete all bounces
            client.delete_bounces(all_bounces=True)

            # Delete specific bounces
            client.delete_bounces(bounce_ids=[1, 2, 3])
        """
        if not all_bounces and not bounce_ids:
            raise ValueError("Must provide either all_bounces=True or bounce_ids list")
        if all_bounces and bounce_ids:
            raise ValueError(
                "Cannot provide both all_bounces=True and bounce_ids. "
                "Choose one deletion method."
            )

        params: Dict[str, Any] = {}
        if all_bounces:
            params["all"] = True
        elif bounce_ids:
            # Multiple IDs are passed as repeated query parameters: ?id=1&id=2&id=3
            # requests library handles lists by creating multiple query params
            params["id"] = bounce_ids

        return self._api.send("DELETE", "/api/bounces", params=params)

    def delete_bounce(self, bounce_id: int) -> JSONDict:
        """
        Delete a specific bounce record by ID.

        Args:
            bounce_id: ID of the bounce record to delete.

        Returns:
            JSON dict with `{"data": True}` on success.

        Examples:
            # Delete a single bounce
            client.delete_bounce(bounce_id=123)
        """
        return self._api.send("DELETE", f"/api/bounces/{bounce_id}")
