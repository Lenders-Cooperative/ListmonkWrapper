#
# Created on Tue Dec 22 2021
#
# Copyright (c) 2021 Lenders Cooperative, a division of Summit Technology Group, Inc.
#


def test_create_and_delete_subscriber_with_django_user(client, django_user):
    results = client.create_subscriber(email=django_user.email, name=django_user.username)
    data = results["data"]
    new_user_id = data["id"]
    assert isinstance(data["id"], int)
    assert data["name"] == django_user.username
    assert data["email"] == django_user.email

    results = client.delete_subscriber(new_user_id)
    assert results.get("data")
