"""
API Handler for ListMonk HTTP requests.

This module provides the low-level HTTP handling with Basic Authentication.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import requests
from requests import Session

JSONDict = Dict[str, Any]


class APIHandler:  # pylint: disable=too-few-public-methods
    """HTTP handler that manages Basic Authentication and request dispatch.

    This class is responsible for:
    - Setting up HTTP Basic Authentication for all requests.
    - Sending HTTP requests with automatic authentication.
    """

    REQUEST_TIMEOUT = 30

    def __init__(
        self,
        host: str,
        *,
        username: str,
        password: str,
    ) -> None:
        """
        Initialize the API handler.

        Args:
            host: Base Listmonk URL including protocol and port.
            username: API username for Listmonk Basic Auth.
            password: API password/token for Listmonk Basic Auth.
        """
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self.session: Session = requests.Session()
        # Set up Basic Auth for all requests
        self.session.auth = (username, password)

    # ------------------------------------------------------------------
    # Request Dispatch
    # ------------------------------------------------------------------

    def send(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        *,
        payload: Optional[JSONDict] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> JSONDict:
        """
        Send an HTTP request, automatically handling authentication.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.).
            url: API path (e.g. "/api/subscribers").
            payload: Optional JSON body for the request.
            params: Optional query parameters.
            headers: Optional additional headers.

        Returns:
            Parsed JSON response as a dictionary. For responses with no
            body (e.g. some DELETE endpoints), an empty dict is returned.

        Raises:
            requests.HTTPError: If the response signals an HTTP error.
        """
        full_url = f"{self._host}{url}"
        response = self.session.request(
            method=method,
            url=full_url,
            json=payload,
            params=params,
            headers=headers,
            timeout=self.REQUEST_TIMEOUT,
        )

        # For Basic Auth, credentials are sent with each request
        # If we get 401, it means invalid credentials, not expired session
        # So we don't retry - just raise the error

        # Check for errors and include response body in error message if available
        if not response.ok:
            error_msg = f"{response.status_code} {response.reason}"
            try:
                error_body = response.json()
                if "message" in error_body:
                    error_msg += f": {error_body['message']}"
            except (ValueError, KeyError):
                # If response is not JSON or doesn't have message, use text
                if response.text:
                    error_msg += f": {response.text[:200]}"
            raise requests.HTTPError(error_msg, response=response)

        response.raise_for_status()
        if response.content:
            return response.json()

        return {}  # DELETE etc. may return empty body

    def send_multipart(
        self,
        method: str,
        url: str,
        *,
        files: Optional[Union[Dict[str, Any], List[tuple]]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> JSONDict:
        """
        Send a multipart/form-data request (for file uploads).

        Args:
            method: HTTP method (typically POST).
            url: API path (e.g. "/api/import/subscribers").
            files: Optional dictionary of files to upload, or list of tuples
                   for multiple files with the same key.
            data: Optional form data fields.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            requests.HTTPError: If the response signals an HTTP error.
        """
        full_url = f"{self._host}{url}"
        response = self.session.request(
            method=method,
            url=full_url,
            files=files,
            data=data,
            timeout=self.REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        if response.content:
            return response.json()

        return {}
