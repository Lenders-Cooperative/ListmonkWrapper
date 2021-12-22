#
# Created on Tue Dec 22 2021
#
# Copyright (c) 2021 Lenders Cooperative, a division of Summit Technology Group, Inc.
#

import pytest


def test_get_all_campaigns(client):
    results = client.get_campaigns()
    assert results.get("data")


def test_get_subscriber_info(client):
    results = client.get_subscriber_info(1)
    assert results.get("data")


def test_query_subscribers(client):
    results = client.query_subscribers(attributes={})
    assert results.get("data")


def test_delete_subscriber(client, subscriber_id):
    results = client.delete_subscriber(subscriber_id)
    assert results.get("data")


def test_create_and_delete_subscriber(client):
    results = client.create_subscriber(email="test3457@gmail.com", name="Jeff")
    new_user_id = results.get("data", {}).get("id")
    assert isinstance(new_user_id, int)

    results = client.delete_subscriber(new_user_id)
    assert results.get("data")


def test_create_list(client):
    results = client.create_list(name="Test List", list_type="private", optin="double")
    assert results.get("data")


@pytest.mark.parametrize(
    "user_id, email, name",
    [
        ("1", "test@gmail.com", "test12345"),
        ("1", "john12345@hotmail.com", "John Doe"),
        ("1", "jane-doe555@yahoo.com", "Jane Doe"),
    ],
)
def test_update_subscriber(user_id, email, name, client):
    results = client.update_subscriber(user_id=user_id, email=email, name=name)
    assert results.get("data")
    results = client.get_subscriber_info(user_id)
    assert results["data"]["email"] == email
    assert results["data"]["name"] == name
