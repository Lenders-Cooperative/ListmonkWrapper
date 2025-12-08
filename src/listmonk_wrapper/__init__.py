"""
ListmonkWrapper
===============

A lightweight Python client for interacting with the ListMonk REST API.

This package provides:
- A typed, PEP-friendly `ListMonkClient` for managing subscribers, lists,
  templates, and campaigns.
- Compatibility with both BasicAuth (for bootstrap or legacy setups)
  and modern token-based authentication.
- A clean public API surface (`ListMonkClient`) re-exported at the package root.

Usage example:

    from listmonk_wrapper import ListMonkClient

    client = ListMonkClient(
        host="http://localhost",
        port=9000,
        username="admin",  # pragma: allowlist secret
        password="admin",  # pragma: allowlist secret
    )

    subscribers = client.query_subscribers()
    print(subscribers)

This module re-exports the primary client class for convenience:

    from listmonk_wrapper import ListMonkClient
"""

from .client import ListMonkClient

__all__ = ["ListMonkClient"]
