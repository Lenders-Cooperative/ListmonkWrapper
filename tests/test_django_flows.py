def test_create_and_delete_subscriber_with_django_user(client, django_user):
    created = client.create_subscriber(
        email=django_user.email,
        name=django_user.username,
    )
    data = created["data"]

    assert data["email"] == django_user.email
    assert data["name"] == django_user.username

    deleted = client.delete_subscriber(data["id"])

    # Deletion in Listmonk v5.1.0+ returns {"data": True}
    assert "data" in deleted
    assert deleted["data"] is True
