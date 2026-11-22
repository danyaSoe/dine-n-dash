from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_restaurants_returns_sample_data_with_waiting_estimates() -> None:
    response = client.get("/restaurants")

    assert response.status_code == 200
    body = response.json()
    assert body["data_source"] == "sample"
    assert len(body["restaurants"]) == 5
    restaurant = next(item for item in body["restaurants"] if item["id"] == "R001")
    assert restaurant["name"] == "Warung A"
    assert restaurant["supported_meal_modes"] == ["dine_in", "takeaway"]
    assert restaurant["waiting_time_estimates"][0]["minutes"] == 8


def test_get_restaurant_detail() -> None:
    response = client.get("/restaurants/R001")

    assert response.status_code == 200
    assert response.json()["restaurant"]["id"] == "R001"
    assert response.json()["data_source"] == "sample"


def test_get_unknown_restaurant_returns_clear_not_found_error() -> None:
    response = client.get("/restaurants/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant 'UNKNOWN' was not found."


def test_availability_reports_open_mode_support_and_waiting_minutes() -> None:
    response = client.get(
        "/restaurants/R001/availability",
        params={"arrival_time": "11:40", "meal_mode": "dine_in"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data_source": "sample",
        "restaurant_id": "R001",
        "arrival_time": "11:40:00",
        "is_open": True,
        "meal_mode": "dine_in",
        "supports_meal_mode": True,
        "waiting_minutes": 8,
    }


def test_waiting_estimate_uses_next_time_range_at_boundary() -> None:
    response = client.get(
        "/restaurants/R001/availability",
        params={"arrival_time": "12:00", "meal_mode": "takeaway"},
    )

    assert response.status_code == 200
    assert response.json()["waiting_minutes"] == 12


def test_availability_reports_closed_before_opening_time() -> None:
    response = client.get(
        "/restaurants/R001/availability",
        params={"arrival_time": "07:59", "meal_mode": "dine_in"},
    )

    assert response.status_code == 200
    assert response.json()["is_open"] is False
    assert response.json()["waiting_minutes"] is None


def test_availability_reports_closed_at_closing_time() -> None:
    response = client.get(
        "/restaurants/R001/availability",
        params={"arrival_time": "17:00", "meal_mode": "takeaway"},
    )

    assert response.status_code == 200
    assert response.json()["is_open"] is False
    assert response.json()["waiting_minutes"] is None


def test_availability_reports_unsupported_meal_mode() -> None:
    response = client.get(
        "/restaurants/R002/availability",
        params={"arrival_time": "11:30", "meal_mode": "dine_in"},
    )

    assert response.status_code == 200
    assert response.json()["is_open"] is True
    assert response.json()["supports_meal_mode"] is False
    assert response.json()["waiting_minutes"] == 14


def test_availability_returns_404_for_unknown_restaurant() -> None:
    response = client.get(
        "/restaurants/UNKNOWN/availability",
        params={"arrival_time": "11:30", "meal_mode": "takeaway"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Restaurant 'UNKNOWN' was not found."


def test_availability_rejects_invalid_meal_mode() -> None:
    response = client.get(
        "/restaurants/R001/availability",
        params={"arrival_time": "11:30", "meal_mode": "delivery"},
    )

    assert response.status_code == 422


def test_availability_rejects_invalid_time() -> None:
    response = client.get(
        "/restaurants/R001/availability",
        params={"arrival_time": "not-a-time", "meal_mode": "takeaway"},
    )

    assert response.status_code == 422


def test_availability_rejects_timezone_aware_time() -> None:
    response = client.get(
        "/restaurants/R001/availability",
        params={"arrival_time": "11:30:00+07:00", "meal_mode": "takeaway"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "arrival_time must be a local time without a timezone."
    )


def test_health_check_remains_available() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "food-service"}
