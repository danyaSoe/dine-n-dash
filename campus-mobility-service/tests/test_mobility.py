from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_locations_returns_sample_locations() -> None:
    response = client.get("/locations")

    assert response.status_code == 200
    body = response.json()
    assert body["data_source"] == "sample"
    assert {"id": "LABTEK_V", "name": "Labtek V"} in body["locations"]
    assert {"id": "R001", "name": "Warung A"} in body["locations"]


def test_estimate_known_route_returns_minutes() -> None:
    response = client.get(
        "/routes/estimate",
        params={"origin": "Labtek V", "destination": "Warung A"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data_source": "sample",
        "origin": "Labtek V",
        "destination": "Warung A",
        "walking_minutes": 7,
    }


def test_estimate_route_is_available_in_both_directions() -> None:
    response = client.get(
        "/routes/estimate",
        params={"origin": "Warung A", "destination": "Labtek V"},
    )

    assert response.status_code == 200
    assert response.json()["walking_minutes"] == 7


def test_same_known_location_has_zero_walking_minutes() -> None:
    response = client.get(
        "/routes/estimate",
        params={"origin": "Labtek V", "destination": "Labtek V"},
    )

    assert response.status_code == 200
    assert response.json()["walking_minutes"] == 0


def test_unknown_location_returns_clear_not_found_error() -> None:
    response = client.get(
        "/routes/estimate",
        params={"origin": "Unknown Building", "destination": "Labtek V"},
    )

    assert response.status_code == 404
    assert "Unknown location(s): Unknown Building." in response.json()["detail"]


def test_known_locations_without_sample_route_return_clear_error() -> None:
    response = client.get(
        "/routes/estimate",
        params={"origin": "Warung A", "destination": "Warung B"},
    )

    assert response.status_code == 404
    assert "No sample walking route is available" in response.json()["detail"]


def test_blank_location_is_rejected() -> None:
    response = client.get(
        "/routes/estimate",
        params={"origin": "   ", "destination": "Labtek V"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Origin and destination must not be blank."


def test_health_check_remains_available() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "campus-mobility-service",
    }
