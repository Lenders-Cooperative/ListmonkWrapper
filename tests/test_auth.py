"""
Tests for authentication and general API functionality.

This module covers:
- Basic authentication verification
- General API connectivity
"""


def test_basic_auth_works(client):
    """
    Verify that Basic Auth credentials are sent with each request.
    Basic Auth doesn't require session management like cookie-based auth.
    """
    # Make a request - Basic Auth credentials are sent automatically
    result = client.query_subscribers()

    assert "data" in result
    assert "results" in result["data"]
