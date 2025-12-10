"""
Transactional message API methods for ListMonk client.

This module provides mixin methods for sending transactional messages.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ._api_handler import JSONDict


class TransactionalMixin:  # pylint: disable=too-few-public-methods
    """Mixin providing transactional message API methods."""

    # ------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------
    def _validate_mode(self, subscriber_mode: str, allow_external: bool) -> None:
        """Validate subscriber mode constraints."""
        if subscriber_mode == "external" and not allow_external:
            raise ValueError(
                "subscriber_mode 'external' requires Listmonk v6.0.0+; "
                "set allow_external=True or use 'fallback' with existing subscribers."
            )

    def _validate_fallback(  # pylint: disable=too-many-arguments
        self,
        subscriber_mode: str,
        subscriber_email: Optional[str],
        subscriber_id: Optional[int],
        subscriber_emails: Optional[List[str]],
        subscriber_ids: Optional[List[int]],
    ) -> None:
        """Validate fallback mode rules."""
        if subscriber_mode != "fallback":
            return

        if subscriber_email or subscriber_id or subscriber_ids:
            raise ValueError("subscriber_mode 'fallback' only accepts subscriber_emails")

        if not subscriber_emails:
            raise ValueError("subscriber_mode 'fallback' requires subscriber_emails")

    def _validate_external(  # pylint: disable=too-many-arguments
        self,
        subscriber_mode: str,
        subscriber_email: Optional[str],
        subscriber_id: Optional[int],
        subscriber_emails: Optional[List[str]],
        subscriber_ids: Optional[List[int]],
    ) -> None:
        """Validate external mode rules."""
        if subscriber_mode != "external":
            return

        if subscriber_id or subscriber_ids:
            raise ValueError("subscriber_mode 'external' only accepts subscriber_email(s)")

        if not (subscriber_email or subscriber_emails):
            raise ValueError("subscriber_mode 'external' requires subscriber_email(s)")

    def _validate_subscriber_sets(
        self,
        subscriber_email: Optional[str],
        subscriber_id: Optional[int],
        subscriber_emails: Optional[List[str]],
        subscriber_ids: Optional[List[int]],
    ) -> None:
        """Ensure subscriber parameters are mutually valid."""
        single = subscriber_email is not None or subscriber_id is not None
        multiple = subscriber_emails is not None or subscriber_ids is not None

        if not single and not multiple:
            raise ValueError(
                "Provide either (subscriber_email|subscriber_id) or "
                "(subscriber_emails|subscriber_ids)"
            )

        if single and multiple:
            raise ValueError("Cannot provide both single and multiple subscriber parameters")

    # ------------------------------------------------------------
    # Subscriber payload builder
    # ------------------------------------------------------------
    @staticmethod
    def _build_subscriber_payload(
        subscriber_email: Optional[str],
        subscriber_id: Optional[int],
        subscriber_emails: Optional[List[str]],
        subscriber_ids: Optional[List[int]],
    ) -> Dict[str, Any]:
        """Return only the subscriber-specific payload keys."""
        if subscriber_email:
            return {"subscriber_email": subscriber_email}
        if subscriber_id:
            return {"subscriber_id": subscriber_id}
        if subscriber_emails:
            return {"subscriber_emails": subscriber_emails}
        if subscriber_ids:
            return {"subscriber_ids": subscriber_ids}
        return {}

    # ------------------------------------------------------------
    # Attachment handling
    # ------------------------------------------------------------
    def _prepare_attachments(self, attachments: List[str], payload: Dict[str, Any]) -> JSONDict:
        """Send multipart transactional request with attachments."""
        for path in attachments:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Attachment file not found: {path}")

        files_list: List[tuple] = []
        file_handles: List[Any] = []

        try:
            for path in attachments:
                filename = os.path.basename(path)
                fh = open(path, "rb")  # pylint: disable=consider-using-with
                file_handles.append(fh)
                files_list.append(("file", (filename, fh, None)))

            # Listmonk expects form data, so embed JSON payload into the form field.
            form_data = {"data": json.dumps(payload)}
            return self._api.send_multipart("POST", "/api/tx", files=files_list, data=form_data)
        finally:
            for fh in file_handles:
                fh.close()

    # ------------------------------------------------------------
    # Main API method
    # ------------------------------------------------------------
    def send_transactional(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        template_id: int,
        *,
        subscriber_email: Optional[str] = None,
        subscriber_id: Optional[int] = None,
        subscriber_emails: Optional[List[str]] = None,
        subscriber_ids: Optional[List[int]] = None,
        subscriber_mode: str = "default",
        from_email: Optional[str] = None,
        subject: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[List[Dict[str, str]]] = None,
        messenger: str = "email",
        content_type: str = "html",
        attachments: Optional[List[str]] = None,
        allow_external: bool = False,
    ) -> JSONDict:
        """Send a transactional message to one or more subscribers.

        Example:
            client.send_transactional(
                template_id=123,
                subscriber_email="user@example.com",
                subject="Welcome",
                data={"plan": "starter"},
            )
        """
        # ---- Validation ----
        self._validate_mode(subscriber_mode, allow_external)
        self._validate_fallback(
            subscriber_mode,
            subscriber_email,
            subscriber_id,
            subscriber_emails,
            subscriber_ids,
        )
        self._validate_external(
            subscriber_mode,
            subscriber_email,
            subscriber_id,
            subscriber_emails,
            subscriber_ids,
        )
        self._validate_subscriber_sets(
            subscriber_email,
            subscriber_id,
            subscriber_emails,
            subscriber_ids,
        )

        # ---- Build payload ----
        payload: Dict[str, Any] = {
            "template_id": template_id,
            "subscriber_mode": subscriber_mode,
            "messenger": messenger,
            "content_type": content_type,
        }

        payload.update(
            self._build_subscriber_payload(
                subscriber_email,
                subscriber_id,
                subscriber_emails,
                subscriber_ids,
            )
        )

        if from_email:
            payload["from_email"] = from_email
        if subject:
            payload["subject"] = subject
        if data:
            payload["data"] = data
        if headers:
            payload["headers"] = headers

        # ---- Handle attachments ----
        if attachments:
            return self._prepare_attachments(attachments, payload)

        # ---- Send JSON ----
        return self._api.send("POST", "/api/tx", payload=payload)
