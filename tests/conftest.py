#
# Created on Wed Dec 22 2021
#
# Copyright (c) 2021 Lenders Cooperative, a division of Summit Technology Group, Inc.
#

from dataclasses import dataclass

import pytest

from listmonk_wrapper import ListMonkClient


@dataclass
class User:
    listmonk_id: int
    username: str
    email: str
    is_superuser: bool = False
    is_staff: bool = False
    is_active: bool = True


@pytest.fixture
def client():
    return ListMonkClient(host="http://localhost", port=9000, username="listmonk", password="listmonk")


@pytest.fixture
def subscriber_id(client):
    results = client.create_subscriber(email="test3457@gmail.com", name="Jeff")
    return results["data"]["id"]


@pytest.fixture
def django_user():
    return User(listmonk_id=1, username="Test-User", email="test-email@gmail.com")
