"""
Campaign-related API methods for ListMonk client.

This module provides mixin methods for managing campaigns.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._api_handler import JSONDict


class CampaignsMixin:
    """Mixin providing campaign-related API methods."""

    def get_campaigns(self) -> JSONDict:
        """
        Retrieve all campaigns.

        Returns:
            JSON dict containing a "result" list of campaigns along with
            pagination metadata.
        """
        return self._api.send("GET", "/api/campaigns")

    def create_campaign(  # pylint: disable=too-many-arguments
        self,
        name: str,
        subject: str,
        body: str,
        from_email: str,
        *,
        content_type: str = "html",
        lists: Optional[List[int]] = None,
        template_id: int = 1,
        tags: Optional[List[str]] = None,
        attribs: Optional[Dict[str, Any]] = None,
    ) -> JSONDict:
        """
        Create a new campaign.

        Args:
            name: Campaign name.
            subject: Email subject line.
            body: Campaign body content.
            from_email: From address to use.
            content_type: Content type, usually "html" or "plain".
            lists: List of list IDs to target; defaults to [1] if omitted.
            template_id: Template ID to use for the campaign.
            tags: Optional list of tags.
            attribs: Optional JSON attributes for the campaign (v6.0.0+).

        Returns:
            JSON dict with the created campaign under the "data" key.
        """
        payload = {
            "name": name,
            "subject": subject,
            "body": body,
            "from_email": from_email,
            "content_type": content_type,
            "lists": lists or [1],
            "template_id": template_id,
            "tags": tags or [],
        }
        if attribs is not None:
            payload["attribs"] = attribs
        return self._api.send("POST", "/api/campaigns", payload=payload)

    def update_campaign(  # pylint: disable=too-many-arguments
        self,
        campaign_id: int,
        *,
        name: str,
        subject: str,
        body: str,
        from_email: str,
        content_type: str = "html",
        lists: Optional[List[int]] = None,
        template_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        attribs: Optional[Dict[str, Any]] = None,
    ) -> JSONDict:
        """
        Update an existing campaign.

        Args:
            campaign_id: Internal Listmonk campaign ID.
            name: Updated campaign name.
            subject: Updated subject line.
            body: Updated campaign body.
            from_email: Updated from address.
            content_type: Updated content type.
            lists: Optional updated list of list IDs.
            template_id: Optional updated template ID.
            tags: Optional updated list of tags.
            attribs: Optional JSON attributes for the campaign (v6.0.0+).

        Returns:
            JSON dict, typically with a "message": "ok" payload.
        """
        payload = {
            "name": name,
            "subject": subject,
            "body": body,
            "from_email": from_email,
            "content_type": content_type,
            "lists": lists or [1],
            "template_id": template_id,
            "tags": tags or [],
        }
        if attribs is not None:
            payload["attribs"] = attribs
        return self._api.send("PUT", f"/api/campaigns/{campaign_id}", payload=payload)

    def run_campaign(self, campaign_id: int) -> JSONDict:
        """
        Set a campaign's status to ``running``.

        Args:
            campaign_id: Internal Listmonk campaign ID.

        Returns:
            JSON dict, typically with a "message": "ok" payload.
        """
        return self._api.send(
            "PUT",
            f"/api/campaigns/{campaign_id}/status",
            payload={"status": "running"},
        )

    def delete_campaign(self, campaign_id: int) -> JSONDict:
        """
        Delete a single campaign by ID.

        Args:
            campaign_id: Internal Listmonk campaign ID.

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        return self._api.send("DELETE", f"/api/campaigns/{campaign_id}")

    def delete_campaigns(
        self,
        *,
        campaign_ids: Optional[List[int]] = None,
        query: Optional[str] = None,
        delete_all: bool = False,
    ) -> JSONDict:
        """
        Delete multiple campaigns by IDs or by search query (v6.0.0+).

        Args:
            campaign_ids: One or more campaign IDs to delete (required if query/all not provided).
            query: Search query to filter campaigns for deletion.
            delete_all: When True, delete all campaigns (requires v6.0.0+).

        Returns:
            JSON dict with `{"data": True}` on success.
        """
        if not campaign_ids and not query and not delete_all:
            raise ValueError("Either campaign_ids, query, or delete_all=True must be provided")

        params: Dict[str, Any] = {}
        if campaign_ids:
            params["id"] = campaign_ids
        if query:
            params["query"] = query
        if delete_all:
            params["all"] = True

        return self._api.send("DELETE", "/api/campaigns", params=params)
