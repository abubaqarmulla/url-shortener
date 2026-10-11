def test_login_rate_limit(client):
    email = "ratelimit@example.com"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert register_response.status_code == 201

    responses = []

    for _ in range(6):
        response = client.post(
            "/auth/login",
            data={
                "username": email,
                "password": "TestPassword123!",
            },
        )

        responses.append(response)

    successful_logins = [
        response
        for response in responses
        if response.status_code == 200
    ]

    rate_limited_responses = [
        response
        for response in responses
        if response.status_code == 429
    ]

    assert len(successful_logins) == 5
    assert len(rate_limited_responses) == 1


def test_create_url_rate_limit(client):
    email = "url-ratelimit@example.com"

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

    access_token = login_response.json()["access_token"]

    responses = []

    for index in range(21):
        response = client.post(
            "/urls",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "original_url": f"https://example.com/{index}",
            },
        )

        responses.append(response)

    successful_requests = [
        response
        for response in responses
        if response.status_code == 201
    ]

    rate_limited_responses = [
        response
        for response in responses
        if response.status_code == 429
    ]

    assert len(successful_requests) == 20
    assert len(rate_limited_responses) == 1


def test_rate_limit_rejects_excess_requests_and_sets_expiry():
    from uuid import uuid4

    from app.cache.redis import check_rate_limit, redis_client

    identifier = f"test:{uuid4().hex}"
    key = f"rate_limit:{identifier}"

    try:
        assert check_rate_limit(identifier, 2, 60) is True
        assert check_rate_limit(identifier, 2, 60) is True
        assert check_rate_limit(identifier, 2, 60) is False

        ttl = redis_client.ttl(key)

        assert 0 < ttl <= 60
        assert int(redis_client.get(key)) == 3
    finally:
        redis_client.delete(key)
