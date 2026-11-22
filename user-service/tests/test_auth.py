from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
VALID_CREDENTIALS = {"email": "student@example.com", "password": "LongEnoughPassword123"}


def test_register_rejects_valid_input_without_claiming_success() -> None:
    response = client.post("/auth/register", json=VALID_CREDENTIALS)

    assert response.status_code == 501
    assert response.json() == {
        "detail": (
            "Registration is unavailable because user storage is not configured."
        )
    }


def test_login_rejects_valid_input_without_claiming_success() -> None:
    response = client.post("/auth/login", json=VALID_CREDENTIALS)

    assert response.status_code == 501
    assert response.json() == {
        "detail": (
            "Authentication is unavailable because credentials are not stored "
            "or verified."
        )
    }


def test_register_rejects_invalid_email() -> None:
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "LongEnoughPassword123"},
    )

    assert response.status_code == 422


def test_login_rejects_invalid_email() -> None:
    response = client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "LongEnoughPassword123"},
    )

    assert response.status_code == 422


def test_register_rejects_short_password_without_echoing_it() -> None:
    password = "tiny-secret"
    response = client.post(
        "/auth/register",
        json={"email": "student@example.com", "password": password},
    )

    assert response.status_code == 422
    assert password not in response.text


def test_login_rejects_short_password_without_echoing_it() -> None:
    password = "tiny-secret"
    response = client.post(
        "/auth/login",
        json={"email": "student@example.com", "password": password},
    )

    assert response.status_code == 422
    assert password not in response.text


def test_missing_credentials_are_rejected_without_echoing_password() -> None:
    password = "LongEnoughPassword123"
    response = client.post(
        "/auth/register",
        json={"password": password},
    )

    assert response.status_code == 422
    assert password not in response.text


def test_authentication_operations_are_marked_unimplemented_in_openapi() -> None:
    schema = client.get("/openapi.json").json()

    for path in ("/auth/register", "/auth/login"):
        assert "501" in schema["paths"][path]["post"]["responses"]
        assert "200" not in schema["paths"][path]["post"]["responses"]


def test_health_check_remains_available() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "user-service"}
