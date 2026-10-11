def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "pytest@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["email"] == "pytest@example.com"
    assert "id" in response_data


def test_duplicate_user_registration(client):
    user_data = {
        "email": "duplicate@example.com",
        "password": "TestPassword123!",
    }

    first_response = client.post(
        "/auth/register",
        json=user_data,
    )

    second_response = client.post(
        "/auth/register",
        json=user_data,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_login_user(client):
    user_data = {
        "email": "login@example.com",
        "password": "TestPassword123!",
    }

    register_response = client.post(
        "/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert login_response.status_code == 200

    response_data = login_response.json()

    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"


def test_login_with_wrong_password(client):
    user_data = {
        "email": "wrongpassword@example.com",
        "password": "CorrectPassword123!",
    }

    register_response = client.post(
        "/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": user_data["email"],
            "password": "WrongPassword123!",
        },
    )

    assert login_response.status_code == 401
