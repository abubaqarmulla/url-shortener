import json
from datetime import datetime, timedelta

from app.cache.redis import redis_client


def create_test_user(client, email):
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


def create_test_url(client, access_token, expires_at=None):
    url_data = {
        "original_url": "https://github.com",
    }

    if expires_at is not None:
        url_data["expires_at"] = expires_at

    response = client.post(
        "/urls",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json=url_data,
    )

    assert response.status_code == 201

    return response.json()


def test_analytics_returns_click_count(client):
    access_token = create_test_user(
        client,
        "analytics@example.com",
    )

    url_data = create_test_url(
        client,
        access_token,
    )

    short_code = url_data["short_code"]

    client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    response = client.get(
        f"/urls/{url_data['id']}/analytics",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["url_id"] == url_data["id"]
    assert response_data["short_code"] == short_code
    assert response_data["click_count"] == 2


def test_user_cannot_view_another_users_analytics(client):
    first_access_token = create_test_user(
        client,
        "analytics-owner@example.com",
    )

    second_access_token = create_test_user(
        client,
        "analytics-other@example.com",
    )

    url_data = create_test_url(
        client,
        first_access_token,
    )

    response = client.get(
        f"/urls/{url_data['id']}/analytics",
        headers={
            "Authorization": f"Bearer {second_access_token}",
        },
    )

    assert response.status_code == 404


def test_expired_url_does_not_redirect(client):
    access_token = create_test_user(
        client,
        "expired@example.com",
    )

    expired_time = (
        datetime.utcnow() - timedelta(minutes=5)
    ).isoformat()

    url_data = create_test_url(
        client,
        access_token,
        expires_at=expired_time,
    )

    short_code = url_data["short_code"]

    response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert response.status_code == 410


def test_expired_url_is_not_cached(client):
    access_token = create_test_user(
        client,
        "expired-cache@example.com",
    )

    expired_time = (
        datetime.utcnow() - timedelta(minutes=5)
    ).isoformat()

    url_data = create_test_url(
        client,
        access_token,
        expires_at=expired_time,
    )

    short_code = url_data["short_code"]

    client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    cached_url = redis_client.get(
        f"url:{short_code}"
    )

    assert cached_url is None


def test_expired_cached_url_returns_gone(client):
    from datetime import datetime, timedelta, timezone

    from app.cache.redis import redis_client

    access_token = create_test_user(
        client,
        "expired-redis-hit@example.com",
    )

    future_expiry = (
        datetime.now(timezone.utc) + timedelta(hours=1)
    ).replace(tzinfo=None).isoformat()

    url_data = create_test_url(
        client,
        access_token,
        expires_at=future_expiry,
    )

    short_code = url_data["short_code"]

    # The database URL is still valid, but simulate a stale
    # cached expiration timestamp to exercise the cache-hit guard.
    expired_cached_data = {
        "id": url_data["id"],
        "original_url": "https://github.com/",
        "expires_at": (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat(),
    }

    redis_client.set(
        f"url:{short_code}",
        json.dumps(expired_cached_data),
    )

    response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert response.status_code == 410
    assert redis_client.get(f"url:{short_code}") is None


def test_analytics_sync_preserves_database_count(client, monkeypatch):
    from tests.conftest import TestingSessionLocal

    from app.cache.redis import redis_client
    from app.database.models import URL
    from app.services import analytics_sync

    access_token = create_test_user(
        client,
        "analytics-sync-regression@example.com",
    )

    url_data = create_test_url(client, access_token)
    short_code = url_data["short_code"]

    monkeypatch.setattr(
        analytics_sync,
        "SessionLocal",
        TestingSessionLocal,
    )

    counter_key = f"clicks:{short_code}"

    try:
        redis_client.set(counter_key, 3)

        analytics_sync.synchronize_click_counts()

        database = TestingSessionLocal()
        try:
            url = database.query(URL).filter(
                URL.id == url_data["id"]
            ).one()

            assert url.click_count == 3

            # A lower Redis count must never reduce the DB total.
            url.click_count = 5
            database.commit()
        finally:
            database.close()

        redis_client.set(counter_key, 2)
        analytics_sync.synchronize_click_counts()

        database = TestingSessionLocal()
        try:
            url = database.query(URL).filter(
                URL.id == url_data["id"]
            ).one()

            assert url.click_count == 5
        finally:
            database.close()
    finally:
        redis_client.delete(counter_key)
