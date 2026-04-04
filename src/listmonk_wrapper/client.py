"""
ListMonk API Client (Listmonk v5.1.0+ and v6.0.0+ compatible)
--------------------------------------------------------------

Listmonk v5.1.0+ and v6.0.0+ use HTTP Basic Authentication for API access.
This client implements:

- Basic Auth with username/password (credentials sent with each request)
- A high-level wrapper around the most common Listmonk REST API endpoints
"""

from __future__ import annotations

from ._api_handler import APIHandler
from ._bounces import BouncesMixin
from ._campaigns import CampaignsMixin
from ._import import ImportMixin
from ._lists import ListsMixin
from ._media import MediaMixin
from ._subscribers import SubscriberMixin
from ._templates import TemplatesMixin
from ._transactional import TransactionalMixin


class ListMonkClient(  # pylint: disable=too-many-ancestors
    SubscriberMixin,
    ListsMixin,
    TemplatesMixin,
    ImportMixin,
    CampaignsMixin,
    MediaMixin,
    TransactionalMixin,
    BouncesMixin,
):
    """High-level wrapper exposing Listmonk's REST API endpoints."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        port: int | str,
        *,
        username: str,
        password: str,
    ) -> None:
        """
        Initialize a Listmonk API client.

        Args:
            host: Base host URL without port (e.g. "http://localhost").
            port: Port where Listmonk is listening (e.g. 9000).
            username: Username used for HTTP Basic Authentication on API requests.
            password: Password or API token used for HTTP Basic Authentication on API requests.
        """
        base = f"{host}:{port}"
        self._api = APIHandler(base, username=username, password=password)
