from app.cache.redis import redis_client


def create_test_user(
    client,
    email,
):
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_test_url(
    client,
    access_token,
):
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

    return response.json()


def test_redirect_url(client):
    access_token = create_test_user(
        client,
        "redirect1@example.com",
    )

    url_data = create_test_url(
        client,
        access_token,
    )

    short_code = url_data["short_code"]

    response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert response.status_code == 307

    assert response.headers["location"] == "https://github.com/"


def test_redirect_increments_click_count(client):
    access_token = create_test_user(
        client,
        "redirect2@example.com",
    )

    url_data = create_test_url(
        client,
        access_token,
    )

    short_code = url_data["short_code"]

    # Clear any previous click counter for this short code
    redis_client.delete(
        f"clicks:{short_code}"
    )

    first_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert first_response.status_code == 307

    second_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert second_response.status_code == 307

    click_count = redis_client.get(
        f"clicks:{short_code}"
    )

    assert click_count is not None
    assert int(click_count) == 2


def test_redirect_uses_redis_cache(client):
    access_token = create_test_user(
        client,
        "redirect3@example.com",
    )

    url_data = create_test_url(
        client,
        access_token,
    )

    short_code = url_data["short_code"]

    # Make sure the first request is a Redis cache MISS
    redis_client.delete(
        f"url:{short_code}"
    )

    first_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert first_response.status_code == 307

    assert (
        first_response.headers["location"]
        == "https://github.com/"
    )

    # The first request should have populated Redis
    cached_url = redis_client.get(
        f"url:{short_code}"
    )

    assert cached_url is not None

    # Second request should use Redis cache
    second_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert second_response.status_code == 307

    assert (
        second_response.headers["location"]
        == "https://github.com/"
    )


def test_invalid_short_code(client):
    response = client.get(
        "/doesnotexist",
        follow_redirects=False,
    )

    assert response.status_code == 404
