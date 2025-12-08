"""
Template-related API methods for ListMonk client.

This module provides mixin methods for managing templates.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ._api_handler import JSONDict


class TemplatesMixin:
    """Mixin providing template-related API methods."""

    def create_template(  # pylint: disable=too-many-arguments
        self,
        name: str,
        body: str,
        *,
        template_type: str = "campaign",
        subject: Optional[str] = None,
        body_source: Optional[str] = None,
    ) -> JSONDict:
        """
        Create a new template.

        Args:
            name: Template name.
            body: HTML body of the template.
            Should include {{ template "content" . }}
                  placeholder for campaign templates.
            template_type: Template type - "campaign",
            "campaign_visual", or "tx"
                          (default: "campaign").
            subject: Optional subject line for the template (only for tx type).
            body_source: Optional JSON source for email-builder template
                        (only for campaign_visual type).

        Returns:
            JSON dict with the created template under the "data" key.

        Examples:
            # Campaign template
            client.create_template(
                "Newsletter",
                "<html><body>{{ template \"content\" . }}</body></html>"
            )

            # Transactional template with subject
            client.create_template(
                "Welcome Email",
                "<html><body>Welcome!</body></html>",
                template_type="tx",
                subject="Welcome to our service"
            )

            # Visual editor template
            client.create_template(
                "Visual Template",
                "<html><body>Content</body></html>",
                template_type="campaign_visual",
                body_source='{"blocks": [...]}'
            )
        """
        payload: Dict[str, Any] = {
            "name": name,
            "body": body,
            "type": template_type,
        }
        if subject is not None:
            payload["subject"] = subject
        if body_source is not None:
            payload["body_source"] = body_source
        return self._api.send("POST", "/api/templates", payload=payload)

    def update_template(  # pylint: disable=too-many-arguments
        self,
        template_id: int,
        name: str,
        body: str,
        *,
        template_type: Optional[str] = None,
        subject: Optional[str] = None,
        body_source: Optional[str] = None,
    ) -> JSONDict:
        """
        Update an existing template.

        Args:
            template_id: Internal Listmonk template ID.
            name: Updated template name.
            body: Updated HTML body of the template.
            template_type: Optional updated template type - "campaign",
                    "campaign_visual", or "tx".
            subject: Optional updated subject line (only for tx type).
            body_source: Optional updated JSON source for
            email-builder template
                        (only for campaign_visual type).

        Returns:
            JSON dict with the updated template under the "data" key.
        """
        payload: Dict[str, Any] = {"name": name, "body": body}
        if template_type is not None:
            payload["type"] = template_type
        if subject is not None:
            payload["subject"] = subject
        if body_source is not None:
            payload["body_source"] = body_source
        return self._api.send("PUT", f"/api/templates/{template_id}", payload=payload)

    def get_templates(self) -> JSONDict:
        """
        Retrieve all templates.

        Returns:
            JSON dict with "data" containing a list of templates.
        """
        return self._api.send("GET", "/api/templates")

    def get_template(self, template_id: int) -> JSONDict:
        """
        Retrieve a specific template.

        Args:
            template_id: ID of the template to retrieve.

        Returns:
            JSON dict with the template under the "data" key.
        """
        return self._api.send("GET", f"/api/templates/{template_id}")

    def delete_template(self, template_id: int) -> JSONDict:
        """
        Delete a template by ID.

        Args:
            template_id: ID of the template to delete.

        Returns:
            JSON dict with `{"data": True}` for successful deletion.
        """
        return self._api.send("DELETE", f"/api/templates/{template_id}")

    def set_default_template(self, template_id: int) -> JSONDict:
        """
        Set a template as the default template.

        Args:
            template_id: ID of the template to set as default.

        Returns:
            JSON dict with the updated template under the "data" key.
        """
        return self._api.send("PUT", f"/api/templates/{template_id}/default")
