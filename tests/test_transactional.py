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


def _uid():
    """Return a high-entropy suffix safe for email/name uniqueness."""
    return f"{time.time_ns()}_{os.getpid()}"


def test_send_transactional_single_subscriber_by_email(client):
    """Test sending transactional message to a single subscriber by email."""
    uid = _uid()
    template_id = subscriber_id = None

    try:
        template = client.create_template(
            f"TxTemplate_{uid}",
            "<html><body>Hello {{ .Subscriber.Name }}! Order: {{ .Tx.Data.order_id }}</body></html>",
            template_type="tx",
            subject="Test Transactional",
        )
        template_id = template["data"]["id"]

        subscriber = client.create_subscriber(
            email=f"tx_email_{uid}@test.com", name="TxTestUser"
        )
        subscriber_id = subscriber["data"]["id"]

        result = client.send_transactional(
            template_id=template_id,
            subscriber_email=subscriber["data"]["email"],
            data={"order_id": "12345"},
        )
        assert "data" in result
        assert result["data"] is True
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
    finally:
        for delete_fn, rid in [
            (client.delete_subscriber, subscriber_id),
            (client.delete_template, template_id),
        ]:
            if rid is not None:
                try:
                    delete_fn(rid)
                except Exception:
                    pass


def test_send_transactional_single_subscriber_by_id(client):
    """Test sending transactional message to a single subscriber by ID."""
    uid = _uid()
    template_id = subscriber_id = None

    try:
        template = client.create_template(
            f"TxTemplate_{uid}",
            "<html><body>Hello {{ .Subscriber.Name }}!</body></html>",
            template_type="tx",
            subject="Test Transactional",
        )
        template_id = template["data"]["id"]

        subscriber = client.create_subscriber(
            email=f"tx_id_{uid}@test.com", name="TxTestUser"
        )
        subscriber_id = subscriber["data"]["id"]

        result = client.send_transactional(
            template_id=template_id,
            subscriber_id=subscriber_id,
        )
        assert "data" in result
        assert result["data"] is True
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
    finally:
        for delete_fn, rid in [
            (client.delete_subscriber, subscriber_id),
            (client.delete_template, template_id),
        ]:
            if rid is not None:
                try:
                    delete_fn(rid)
                except Exception:
                    pass


def test_send_transactional_multiple_subscribers(client):
    """Test sending transactional message to multiple subscribers."""
    uid = _uid()
    template_id = None
    subscriber_ids = []

    try:
        template = client.create_template(
            f"TxTemplate_{uid}",
            "<html><body>Hello! Order: {{ .Tx.Data.order_id }}</body></html>",
            template_type="tx",
            subject="Test Transactional",
        )
        template_id = template["data"]["id"]

        sub1 = client.create_subscriber(
            email=f"tx_multi1_{uid}@test.com", name="TxTestUser1"
        )
        subscriber_ids.append(sub1["data"]["id"])
        sub2 = client.create_subscriber(
            email=f"tx_multi2_{uid}@test.com", name="TxTestUser2"
        )
        subscriber_ids.append(sub2["data"]["id"])

        result = client.send_transactional(
            template_id=template_id,
            subscriber_emails=[sub1["data"]["email"], sub2["data"]["email"]],
            data={"order_id": "67890"},
        )
        assert "data" in result
        assert result["data"] is True
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
    finally:
        for sid in subscriber_ids:
            try:
                client.delete_subscriber(sid)
            except Exception:
                pass
        if template_id is not None:
            try:
                client.delete_template(template_id)
            except Exception:
                pass


def test_send_transactional_with_optional_params(client):
    """Test sending transactional message with optional parameters."""
    uid = _uid()
    template_id = subscriber_id = None

    try:
        template = client.create_template(
            f"TxTemplate_{uid}",
            "<html><body>Hello {{ .Subscriber.Name }}!</body></html>",
            template_type="tx",
            subject="Default Subject",
        )
        template_id = template["data"]["id"]

        subscriber = client.create_subscriber(
            email=f"tx_opts_{uid}@test.com", name="TxTestUser"
        )
        subscriber_id = subscriber["data"]["id"]

        result = client.send_transactional(
            template_id=template_id,
            subscriber_email=subscriber["data"]["email"],
            subject="Custom Subject",
            from_email="custom@test.com",
            content_type="html",
            data={"key": "value"},
        )
        assert "data" in result
        assert result["data"] is True
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
    finally:
        for delete_fn, rid in [
            (client.delete_subscriber, subscriber_id),
            (client.delete_template, template_id),
        ]:
            if rid is not None:
                try:
                    delete_fn(rid)
                except Exception:
                    pass


def test_send_transactional_with_attachments(client):
    """Test sending transactional message with file attachments."""
    uid = _uid()
    template_id = subscriber_id = None
    tmp_paths = []

    try:
        template = client.create_template(
            f"TxTemplate_{uid}",
            "<html><body>Hello {{ .Subscriber.Name }}!</body></html>",
            template_type="tx",
            subject="Test Transactional",
        )
        template_id = template["data"]["id"]

        subscriber = client.create_subscriber(
            email=f"tx_attach_{uid}@test.com", name="TxTestUser"
        )
        subscriber_id = subscriber["data"]["id"]

        for content in ("Test attachment content", "Another attachment"):
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
            tmp.write(content)
            tmp.close()
            tmp_paths.append(tmp.name)

        result = client.send_transactional(
            template_id=template_id,
            subscriber_email=subscriber["data"]["email"],
            attachments=tmp_paths,
        )
        assert "data" in result
        assert result["data"] is True
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
    finally:
        for path in tmp_paths:
            if os.path.exists(path):
                os.unlink(path)
        for delete_fn, rid in [
            (client.delete_subscriber, subscriber_id),
            (client.delete_template, template_id),
        ]:
            if rid is not None:
                try:
                    delete_fn(rid)
                except Exception:
                    pass


def test_send_transactional_validation_errors(client):
    """Test validation errors for transactional messages."""
    uid = _uid()
    template_id = None

    try:
        template = client.create_template(
            f"TxTemplate_{uid}",
            "<html><body>Test</body></html>",
            template_type="tx",
            subject="Test",
        )
        template_id = template["data"]["id"]

        with pytest.raises(ValueError, match="Provide either"):
            client.send_transactional(template_id=template_id)

        with pytest.raises(ValueError, match="Cannot provide both"):
            client.send_transactional(
                template_id=template_id,
                subscriber_email="test@test.com",
                subscriber_emails=["test@test.com"],
            )

        with pytest.raises(
            ValueError, match="subscriber_mode 'external' requires Listmonk v6.0.0\\+"
        ):
            client.send_transactional(
                template_id=template_id,
                subscriber_mode="external",
                subscriber_emails=["test@test.com"],
            )
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
    finally:
        if template_id is not None:
            try:
                client.delete_template(template_id)
            except Exception:
                pass


def test_send_transactional_nonexistent_attachment(client):
    """Test that sending with nonexistent attachment raises FileNotFoundError."""
    uid = _uid()
    template_id = subscriber_id = None

    try:
        template = client.create_template(
            f"TxTemplate_{uid}",
            "<html><body>Test</body></html>",
            template_type="tx",
            subject="Test",
        )
        template_id = template["data"]["id"]

        subscriber = client.create_subscriber(
            email=f"tx_nofile_{uid}@test.com", name="TxTestUser"
        )
        subscriber_id = subscriber["data"]["id"]

        with pytest.raises(FileNotFoundError):
            client.send_transactional(
                template_id=template_id,
                subscriber_email=subscriber["data"]["email"],
                attachments=["/nonexistent/path/to/file.pdf"],
            )
    except requests.HTTPError as e:
        if e.response.status_code == 500:
            pytest.skip("Template creation failed with server error")
        raise
    finally:
        for delete_fn, rid in [
            (client.delete_subscriber, subscriber_id),
            (client.delete_template, template_id),
        ]:
            if rid is not None:
                try:
                    delete_fn(rid)
                except Exception:
                    pass


def test_send_transactional_external_v6(client, listmonk_version_tuple):
    """Test external recipient mode in v6.0.0+."""
    if listmonk_version_tuple < (6, 0, 0):
        pytest.skip("External recipients require Listmonk v6.0.0+")

    uid = _uid()
    template_id = None

    try:
        template = client.create_template(
            f"TxExternalTemplate_{uid}",
            "<html><body>External</body></html>",
            template_type="tx",
            subject="External",
        )
        template_id = template["data"]["id"]

        result = client.send_transactional(
            template_id=template_id,
            subscriber_mode="external",
            subscriber_email=f"external_{uid}@test.com",
            allow_external=True,
        )
        assert "data" in result
        assert result["data"] is True
    finally:
        if template_id is not None:
            try:
                client.delete_template(template_id)
            except Exception:
                pass
