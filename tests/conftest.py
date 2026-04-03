"""
Global fixtures for ListMonk integration tests.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import pytest
import requests
from dotenv import load_dotenv

from listmonk_wrapper import ListMonkClient

# Load .env from project root so LISTMONK_* vars are visible to tests
load_dotenv()


LISTMONK_HOST = os.getenv("LISTMONK_HOST", "http://localhost")
LISTMONK_PORT = os.getenv("LISTMONK_PORT", "9000")


def _load_api_creds_from_file() -> None:
    creds_file = os.path.join(os.path.dirname(__file__), "..", "tmp", "listmonk_api_creds.sh")
    if not os.path.exists(creds_file):
        return

    with open(creds_file, "r") as f:
        for line in f:
            if line.startswith("export "):
                parts = line.replace("export ", "").strip().split("=", 1)
                if len(parts) == 2:
                    key = parts[0]
                    value = parts[1].strip("'\"")
                    os.environ[key] = value


def _get_api_credentials() -> tuple[str, str]:
    username = os.getenv("LISTMONK_API_USER") or os.getenv("LISTMONK_ADMIN_API_USER", "api_admin")
    password = os.getenv("LISTMONK_API_TOKEN") or os.getenv("LISTMONK_ADMIN_PASSWORD", "admin123")
    return username, password


def _parse_version(version: str) -> tuple[int, ...]:
    cleaned = version.strip().lstrip("v").split("-", 1)[0]
    parts = []
    for part in cleaned.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            break
    return tuple(parts) if parts else (0, 0, 0)


@pytest.fixture(scope="session", autouse=True)
def ensure_listmonk_ready():
    """
    Ensure Listmonk is ready before tests run.

    Note: Containers are started by 'make test' via 'make listmonk-up',
    which already waits for health checks. This fixture just verifies
    the API is responding as a final check.
    """
    url = f"{LISTMONK_HOST}:{LISTMONK_PORT}/api/campaigns"

    # Wait up to 60 seconds for API to be ready (listmonk may take time to start)
    for _ in range(120):  # 60 seconds max wait
        try:
            r = requests.get(url, timeout=2)
            if r.status_code in (200, 401, 403):
                return  # API is ready
        except Exception:
            pass
        time.sleep(0.5)
    else:
        raise RuntimeError(
            f"Listmonk API not ready at {LISTMONK_HOST}:{LISTMONK_PORT}. "
            "Make sure containers are running (run 'make listmonk-up')."
        )


@dataclass
class User:
    listmonk_id: int
    username: str
    email: str
    is_superuser: bool = False
    is_staff: bool = False
    is_active: bool = True


# -------------------------------------------------------------------------
# ListMonk Client Fixture (session-based auth — v5.x)
# -------------------------------------------------------------------------


@pytest.fixture(scope="session")
def client() -> ListMonkClient:
    """
    Provide an authenticated ListMonk client for all tests.
    Listmonk v5.1.0+ uses Basic Auth with API credentials (username:token).
    """
    # Try to load API credentials from the credentials
    # file created by start-listmonk
    _load_api_creds_from_file()

    # Use API credentials if available, otherwise
    # fall back to admin credentials
    username, password = _get_api_credentials()
    host = os.getenv("LISTMONK_HOST", "http://localhost")
    port = os.getenv("LISTMONK_PORT", "9000")

    return ListMonkClient(
        host=host,
        port=port,
        username=username,
        password=password,
    )


@pytest.fixture(scope="session")
def listmonk_version() -> str:
    _load_api_creds_from_file()
    username, password = _get_api_credentials()
    host = os.getenv("LISTMONK_HOST", "http://localhost")
    port = os.getenv("LISTMONK_PORT", "9000")
    url = f"{host}:{port}/api/config"

    try:
        response = requests.get(url, auth=(username, password), timeout=5)
        response.raise_for_status()
        return response.json()["data"]["version"]
    except Exception:
        return "0.0.0"


@pytest.fixture(scope="session")
def listmonk_version_tuple(listmonk_version: str) -> tuple[int, ...]:
    return _parse_version(listmonk_version)


# -------------------------------------------------------------------------
# Subscriber Fixture
# -------------------------------------------------------------------------


@pytest.fixture
def subscriber_id(client: ListMonkClient):
    """
    Create a temporary subscriber with a unique email and clean up after use.
    """
    email = f"fixture_{int(time.time())}_{os.getpid()}@test.com"
    result = client.create_subscriber(email=email, name="FixtureSubscriber")
    sid = result["data"]["id"]
    yield sid
    try:
        client.delete_subscriber(sid)
    except Exception:
        pass


# -------------------------------------------------------------------------
# Mock Django User Fixture (unchanged)
# -------------------------------------------------------------------------


@pytest.fixture
def django_user() -> User:
    return User(
        listmonk_id=1,
        username="Test-User",
        email="test-email@gmail.com",
    )
