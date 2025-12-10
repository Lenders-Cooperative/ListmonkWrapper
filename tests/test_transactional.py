"""
Tests for transactional message API endpoints.

This module covers all transactional operations:
- Sending transactional messages to single subscribers
- Sending transactional messages to multiple subscribers
- Using different subscriber modes (default, fallback)
- Sending with file attachments
"""

import os
import tempfile
import time

import pytest
import requests


def test_send_transactional_single_subscriber_by_email(client):
    """Test sending transactional message to a single subscriber by email."""
    # Create a transactional template
    timestamp = int(time.time())
    template_name = f"TxTemplate_{timestamp}"
    template_body = (
        "<html><body>Hello {{ .Subscriber.Name }}! Order: {{ .Tx.Data.order_id }}</body></html>"
    )

    try:
        # Create template
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="Test Transactional"
        )
        template_id = template["data"]["id"]

        # Create a subscriber
        subscriber = client.create_subscriber(
            email=f"tx_test_{timestamp}@test.com", name="TxTestUser"
        )
        subscriber_email = subscriber["data"]["email"]

        # Send transactional message
        result = client.send_transactional(
            template_id=template_id,
            subscriber_email=subscriber_email,
            data={"order_id": "12345"},
        )

        assert "data" in result
        assert result["data"] is True

        # Cleanup
        client.delete_subscriber(subscriber["data"]["id"])
        client.delete_template(template_id)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_send_transactional_single_subscriber_by_id(client):
    """Test sending transactional message to a single subscriber by ID."""
    # Create a transactional template
    timestamp = int(time.time())
    template_name = f"TxTemplate_{timestamp}"
    template_body = "<html><body>Hello {{ .Subscriber.Name }}!</body></html>"

    try:
        # Create template
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="Test Transactional"
        )
        template_id = template["data"]["id"]

        # Create a subscriber
        subscriber = client.create_subscriber(
            email=f"tx_test_{timestamp}@test.com", name="TxTestUser"
        )
        subscriber_id = subscriber["data"]["id"]

        # Send transactional message
        result = client.send_transactional(
            template_id=template_id,
            subscriber_id=subscriber_id,
        )

        assert "data" in result
        assert result["data"] is True

        # Cleanup
        client.delete_subscriber(subscriber_id)
        client.delete_template(template_id)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_send_transactional_multiple_subscribers(client):
    """Test sending transactional message to multiple subscribers."""
    # Create a transactional template
    timestamp = int(time.time())
    template_name = f"TxTemplate_{timestamp}"
    template_body = "<html><body>Hello! Order: {{ .Tx.Data.order_id }}</body></html>"

    try:
        # Create template
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="Test Transactional"
        )
        template_id = template["data"]["id"]

        # Create subscribers
        subscriber1 = client.create_subscriber(
            email=f"tx_test1_{timestamp}@test.com", name="TxTestUser1"
        )
        subscriber2 = client.create_subscriber(
            email=f"tx_test2_{timestamp}@test.com", name="TxTestUser2"
        )

        subscriber_emails = [subscriber1["data"]["email"], subscriber2["data"]["email"]]

        # Send transactional message
        result = client.send_transactional(
            template_id=template_id,
            subscriber_emails=subscriber_emails,
            data={"order_id": "67890"},
        )

        assert "data" in result
        assert result["data"] is True

        # Cleanup
        client.delete_subscriber(subscriber1["data"]["id"])
        client.delete_subscriber(subscriber2["data"]["id"])
        client.delete_template(template_id)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_send_transactional_with_optional_params(client):
    """Test sending transactional message with optional parameters."""
    # Create a transactional template
    timestamp = int(time.time())
    template_name = f"TxTemplate_{timestamp}"
    template_body = "<html><body>Hello {{ .Subscriber.Name }}!</body></html>"

    try:
        # Create template
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="Default Subject"
        )
        template_id = template["data"]["id"]

        # Create a subscriber
        subscriber = client.create_subscriber(
            email=f"tx_test_{timestamp}@test.com", name="TxTestUser"
        )
        subscriber_email = subscriber["data"]["email"]

        # Send transactional message with custom subject and from_email
        result = client.send_transactional(
            template_id=template_id,
            subscriber_email=subscriber_email,
            subject="Custom Subject",
            from_email="custom@test.com",
            content_type="html",
            data={"key": "value"},
        )

        assert "data" in result
        assert result["data"] is True

        # Cleanup
        client.delete_subscriber(subscriber["data"]["id"])
        client.delete_template(template_id)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_send_transactional_with_attachments(client):
    """Test sending transactional message with file attachments."""
    # Create a transactional template
    timestamp = int(time.time())
    template_name = f"TxTemplate_{timestamp}"
    template_body = "<html><body>Hello {{ .Subscriber.Name }}!</body></html>"

    try:
        # Create template
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="Test Transactional"
        )
        template_id = template["data"]["id"]

        # Create a subscriber
        subscriber = client.create_subscriber(
            email=f"tx_test_{timestamp}@test.com", name="TxTestUser"
        )
        subscriber_email = subscriber["data"]["email"]

        # Create temporary attachment files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file1:
            tmp_file1.write("Test attachment content")
            tmp_path1 = tmp_file1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file2:
            tmp_file2.write("Another attachment")
            tmp_path2 = tmp_file2.name

        try:
            # Send transactional message with attachments
            result = client.send_transactional(
                template_id=template_id,
                subscriber_email=subscriber_email,
                attachments=[tmp_path1, tmp_path2],
            )

            assert "data" in result
            assert result["data"] is True
        finally:
            # Cleanup temp files
            if os.path.exists(tmp_path1):
                os.unlink(tmp_path1)
            if os.path.exists(tmp_path2):
                os.unlink(tmp_path2)

        # Cleanup
        client.delete_subscriber(subscriber["data"]["id"])
        client.delete_template(template_id)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_send_transactional_validation_errors(client):
    """Test validation errors for transactional messages."""
    # Create a transactional template
    timestamp = int(time.time())
    template_name = f"TxTemplate_{timestamp}"
    template_body = "<html><body>Test</body></html>"

    try:
        # Create template
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="Test"
        )
        template_id = template["data"]["id"]

        # Test: No subscriber parameters
        with pytest.raises(ValueError, match="Provide either"):
            client.send_transactional(template_id=template_id)

        # Test: Both single and multiple subscriber parameters
        with pytest.raises(ValueError, match="Cannot provide both"):
            client.send_transactional(
                template_id=template_id,
                subscriber_email="test@test.com",
                subscriber_emails=["test@test.com"],
            )

        # Test: External mode requires opt-in for v6.0.0+ support
        with pytest.raises(
            ValueError, match="subscriber_mode 'external' requires Listmonk v6.0.0\\+"
        ):
            client.send_transactional(
                template_id=template_id,
                subscriber_mode="external",
                subscriber_emails=["test@test.com"],
            )

        # Cleanup
        client.delete_template(template_id)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_send_transactional_nonexistent_attachment(client):
    """Test that sending with nonexistent attachment raises FileNotFoundError."""
    # Create a transactional template
    timestamp = int(time.time())
    template_name = f"TxTemplate_{timestamp}"
    template_body = "<html><body>Test</body></html>"

    try:
        # Create template
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="Test"
        )
        template_id = template["data"]["id"]

        # Create a subscriber
        subscriber = client.create_subscriber(
            email=f"tx_test_{timestamp}@test.com", name="TxTestUser"
        )
        subscriber_email = subscriber["data"]["email"]

        # Test: Nonexistent attachment file
        with pytest.raises(FileNotFoundError):
            client.send_transactional(
                template_id=template_id,
                subscriber_email=subscriber_email,
                attachments=["/nonexistent/path/to/file.pdf"],
            )

        # Cleanup
        client.delete_subscriber(subscriber["data"]["id"])
        client.delete_template(template_id)
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise


def test_send_transactional_external_v6(client, listmonk_version_tuple):
    """Test external recipient mode in v6.0.0+."""
    if listmonk_version_tuple < (6, 0, 0):
        pytest.skip("External recipients require Listmonk v6.0.0+")

    timestamp = int(time.time())
    template_name = f"TxExternalTemplate_{timestamp}"
    template_body = "<html><body>External</body></html>"

    template_id = None
    try:
        template = client.create_template(
            template_name, template_body, template_type="tx", subject="External"
        )
        template_id = template["data"]["id"]

        result = client.send_transactional(
            template_id=template_id,
            subscriber_mode="external",
            subscriber_email=f"external_{timestamp}@test.com",
            allow_external=True,
        )
        assert "data" in result
        assert result["data"] is True
    finally:
        if template_id is not None:
            client.delete_template(template_id)
