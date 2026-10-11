def create_test_user(client, email="urltest@example.com"):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_create_url(client):
    access_token = create_test_user(client)

    response = client.post(
        "/urls",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "original_url": "https://github.com",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["original_url"] == "https://github.com/"
    assert "id" in response_data
    assert "short_code" in response_data
    assert len(response_data["short_code"]) == 7


def test_list_urls(client):
    access_token = create_test_user(
        client,
        email="list@example.com",
    )

    client.post(
        "/urls",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "original_url": "https://github.com",
        },
    )

    response = client.get(
        "/urls",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) >= 1
    assert response_data[0]["original_url"] == "https://github.com/"


def test_create_url_without_authentication(client):
    response = client.post(
        "/urls",
        json={
            "original_url": "https://github.com",
        },
    )

    assert response.status_code == 401


def test_delete_url(client):
    access_token = create_test_user(
        client,
        email="delete@example.com",
    )

    create_response = client.post(
        "/urls",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "original_url": "https://github.com",
        },
    )

    assert create_response.status_code == 201

    url_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/urls/{url_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert delete_response.status_code == 204


def test_user_cannot_delete_another_users_url(client):
    first_access_token = create_test_user(
        client,
        email="owner@example.com",
    )

    second_access_token = create_test_user(
        client,
        email="other@example.com",
    )

    create_response = client.post(
        "/urls",
        headers={
            "Authorization": f"Bearer {first_access_token}",
        },
        json={
            "original_url": "https://github.com",
        },
    )

    assert create_response.status_code == 201

    url_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/urls/{url_id}",
        headers={
            "Authorization": f"Bearer {second_access_token}",
        },
    )

    assert delete_response.status_code == 404



def test_delete_url_clears_cache_and_click_counter(client):
    from app.cache.redis import redis_client

    access_token = create_test_user(
        client,
        email="delete-cache@example.com",
    )

    create_response = client.post(
        "/urls",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "original_url": "https://github.com",
        },
    )

    assert create_response.status_code == 201

    url_data = create_response.json()
    short_code = url_data["short_code"]

    redis_client.set(
        f"url:{short_code}",
        '{"original_url":"https://github.com/"}',
    )
    redis_client.set(f"clicks:{short_code}", 4)

    delete_response = client.delete(
        f"/urls/{url_data['id']}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert delete_response.status_code == 204
    assert redis_client.get(f"url:{short_code}") is None
    assert redis_client.get(f"clicks:{short_code}") is None
