from datetime import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.errors import DependencyRequestError, RouteUnavailableError
from app.main import app
from app.schemas import (
    MealMode,
    RecommendationRequest,
    Restaurant,
    RestaurantAvailabilityResponse,
    RestaurantOpeningHours,
    RestaurantWaitingTimeEstimate,
    RestaurantsResponse,
    RouteEstimateResponse,
)
from app.services import planner

client = TestClient(app)


def make_restaurant(
    restaurant_id: str = "R001",
    name: str = "Warung A",
    *,
    modes: tuple[MealMode, ...] = ("dine_in", "takeaway"),
) -> Restaurant:
    return Restaurant(
        id=restaurant_id,
        name=name,
        opening_hours=RestaurantOpeningHours(
            opens_at=time(8),
            closes_at=time(17),
        ),
        supported_meal_modes=modes,
        waiting_time_estimates=(
            RestaurantWaitingTimeEstimate(
                start_time=time(8),
                end_time=time(17),
                minutes=8,
            ),
        ),
    )


def request_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "origin": "Labtek V",
        "destination": "Labtek VIII",
        "ready_time": "11:40",
        "class_start": "12:30",
        "buffer_minutes": 5,
        "meal_mode": "dine_in",
        "meal_duration_minutes": 18,
    }
    payload.update(overrides)
    return payload


def configure_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    restaurants: tuple[Restaurant, ...],
    *,
    outbound_minutes: dict[str, int] | None = None,
    return_minutes: dict[str, int] | None = None,
    open_status: dict[str, bool] | None = None,
    supported_modes: dict[str, bool] | None = None,
    waiting_minutes: dict[str, int | None] | None = None,
) -> None:
    monkeypatch.setattr(
        planner,
        "get_restaurants",
        lambda: RestaurantsResponse(data_source="sample", restaurants=restaurants),
    )

    def route_estimate(origin: str, destination: str) -> RouteEstimateResponse:
        if origin == "Labtek V":
            minutes = (outbound_minutes or {}).get(destination, 7)
        else:
            minutes = (return_minutes or {}).get(origin, 8)
        return RouteEstimateResponse(
            data_source="sample",
            origin=origin,
            destination=destination,
            walking_minutes=minutes,
        )

    def availability(
        restaurant_id: str,
        arrival_time: time,
        meal_mode: MealMode,
    ) -> RestaurantAvailabilityResponse:
        del meal_mode
        restaurant = next(item for item in restaurants if item.id == restaurant_id)
        return RestaurantAvailabilityResponse(
            data_source="sample",
            restaurant_id=restaurant_id,
            arrival_time=arrival_time,
            is_open=(open_status or {}).get(restaurant_id, True),
            meal_mode="dine_in",
            supports_meal_mode=(supported_modes or {}).get(restaurant_id, True),
            waiting_minutes=(waiting_minutes or {}).get(restaurant_id, 8),
        )

    monkeypatch.setattr(planner, "get_route_estimate", route_estimate)
    monkeypatch.setattr(planner, "get_availability", availability)


def test_recommendation_matches_brief_calculation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant = make_restaurant()
    configure_dependencies(monkeypatch, (restaurant,))

    response = planner.create_recommendations(
        RecommendationRequest.model_validate(request_payload())
    )

    assert response.success is True
    assert len(response.recommendations) == 1
    recommendation = response.recommendations[0]
    assert recommendation.travel_to_restaurant_minutes == 7
    assert recommendation.waiting_minutes == 8
    assert recommendation.meal_duration_minutes == 18
    assert recommendation.travel_to_class_minutes == 8
    assert recommendation.departure_deadline == "12:17"
    assert recommendation.remaining_minutes == 4


def test_late_candidate_is_not_recommended(monkeypatch: pytest.MonkeyPatch) -> None:
    restaurant = make_restaurant()
    configure_dependencies(monkeypatch, (restaurant,))

    response = client.post(
        "/recommendations",
        json=request_payload(class_start="12:20"),
    )

    assert response.status_code == 200
    assert response.json()["success"] is False
    assert response.json()["recommendations"] == []
    assert "after the arrival deadline" in response.json()["unavailable_reasons"][0]


def test_closed_restaurant_is_not_recommended(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant = make_restaurant()
    configure_dependencies(monkeypatch, (restaurant,), open_status={"R001": False})

    response = planner.create_recommendations(
        RecommendationRequest.model_validate(request_payload())
    )

    assert response.recommendations == []
    assert "closed" in response.unavailable_reasons[0]


def test_service_finishing_after_closing_is_not_recommended(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant = Restaurant(
        id="R001",
        name="Warung A",
        opening_hours=RestaurantOpeningHours(
            opens_at=time(8),
            closes_at=time(12),
        ),
        supported_meal_modes=("dine_in",),
        waiting_time_estimates=(
            RestaurantWaitingTimeEstimate(
                start_time=time(8),
                end_time=time(17),
                minutes=8,
            ),
        ),
    )
    configure_dependencies(monkeypatch, (restaurant,))

    response = planner.create_recommendations(
        RecommendationRequest.model_validate(request_payload())
    )

    assert response.recommendations == []
    assert "finish after closing time" in response.unavailable_reasons[0]


def test_unsupported_meal_mode_is_not_recommended(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant = make_restaurant(modes=("takeaway",))
    configure_dependencies(
        monkeypatch,
        (restaurant,),
        supported_modes={"R001": False},
    )

    response = planner.create_recommendations(
        RecommendationRequest.model_validate(request_payload())
    )

    assert response.recommendations == []
    assert "does not support dine_in" in response.unavailable_reasons[0]


def test_takeaway_does_not_add_dine_in_duration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant = make_restaurant()
    configure_dependencies(monkeypatch, (restaurant,))

    response = planner.create_recommendations(
        RecommendationRequest.model_validate(
            request_payload(meal_mode="takeaway", meal_duration_minutes=None)
        )
    )

    recommendation = response.recommendations[0]
    assert recommendation.meal_duration_minutes == 0
    assert recommendation.remaining_minutes == 22
    assert recommendation.departure_deadline == "12:17"


def test_recommendations_are_sorted_by_remaining_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurants = (
        make_restaurant("R001", "Warung A"),
        make_restaurant("R002", "Warung B"),
    )
    configure_dependencies(
        monkeypatch,
        restaurants,
        outbound_minutes={"Warung A": 7, "Warung B": 4},
        return_minutes={"Warung A": 8, "Warung B": 5},
    )

    response = planner.create_recommendations(
        RecommendationRequest.model_validate(request_payload())
    )

    assert [item.restaurant_id for item in response.recommendations] == [
        "R002",
        "R001",
    ]
    assert [
        item.remaining_minutes for item in response.recommendations
    ] == [10, 4]


def test_dependency_failure_returns_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable() -> RestaurantsResponse:
        raise DependencyRequestError("Food Service", "connection refused")

    monkeypatch.setattr(planner, "get_restaurants", unavailable)

    response = client.post("/recommendations", json=request_payload())

    assert response.status_code == 503
    assert "Food Service dependency error" in response.json()["detail"]


def test_mobility_dependency_failure_returns_service_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant = make_restaurant()
    monkeypatch.setattr(
        planner,
        "get_restaurants",
        lambda: RestaurantsResponse(data_source="sample", restaurants=(restaurant,)),
    )

    def unavailable(origin: str, destination: str) -> RouteEstimateResponse:
        del origin, destination
        raise DependencyRequestError("Campus Mobility Service", "request failed.")

    monkeypatch.setattr(planner, "get_route_estimate", unavailable)

    response = client.post("/recommendations", json=request_payload())

    assert response.status_code == 503
    assert "Campus Mobility Service dependency error" in response.json()["detail"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"meal_mode": "delivery"},
        {"buffer_minutes": -1},
        {"meal_duration_minutes": -1},
        {"meal_duration_minutes": None},
        {"ready_time": "12:31"},
        {"origin": "   "},
        {"ready_time": "11:40:30"},
        {"ready_time": "11:40+07:00"},
    ],
)
def test_invalid_input_is_rejected(overrides: dict[str, object]) -> None:
    response = client.post("/recommendations", json=request_payload(**overrides))

    assert response.status_code == 422


def test_takeaway_does_not_require_meal_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    restaurant = make_restaurant()
    configure_dependencies(monkeypatch, (restaurant,))

    response = client.post(
        "/recommendations",
        json=request_payload(meal_mode="takeaway"),
    )

    assert response.status_code == 200
    assert response.json()["recommendations"][0]["meal_duration_minutes"] == 0


def test_http_clients_call_both_dependency_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.clients import food, mobility

    monkeypatch.setenv("FOOD_SERVICE_URL", "http://food.internal")
    monkeypatch.setenv("MOBILITY_SERVICE_URL", "http://mobility.internal")
    monkeypatch.setenv("SERVICE_TIMEOUT_SECONDS", "1.5")
    calls: list[tuple[str, dict[str, object] | None, float]] = []

    def mock_get(
        url: str,
        *,
        params: dict[str, str] | None = None,
        timeout: float,
    ) -> httpx.Response:
        calls.append((url, params, timeout))
        if url == "http://food.internal/restaurants":
            payload: dict[str, object] = {
                "data_source": "sample",
                "restaurants": [],
            }
        elif url.endswith("/availability"):
            payload = {
                "data_source": "sample",
                "restaurant_id": "R001",
                "arrival_time": "11:47:00",
                "is_open": True,
                "meal_mode": "dine_in",
                "supports_meal_mode": True,
                "waiting_minutes": 8,
            }
        else:
            payload = {
                "data_source": "sample",
                "origin": "Labtek V",
                "destination": "Warung A",
                "walking_minutes": 7,
            }
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", mock_get)

    food.get_restaurants()
    food.get_availability("R001", time(11, 47), "dine_in")
    mobility.get_route_estimate("Labtek V", "Warung A")

    assert [call[0] for call in calls] == [
        "http://food.internal/restaurants",
        "http://food.internal/restaurants/R001/availability",
        "http://mobility.internal/routes/estimate",
    ]
    assert calls[1][1] == {"arrival_time": "11:47", "meal_mode": "dine_in"}
    assert calls[2][1] == {"origin": "Labtek V", "destination": "Warung A"}
    assert all(call[2] == 1.5 for call in calls)


def test_mobility_route_not_found_is_a_candidate_constraint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    restaurant = make_restaurant()
    configure_dependencies(monkeypatch, (restaurant,))

    def no_route(origin: str, destination: str) -> RouteEstimateResponse:
        del origin, destination
        raise RouteUnavailableError("No sample walking route is available.")

    monkeypatch.setattr(planner, "get_route_estimate", no_route)

    response = planner.create_recommendations(
        RecommendationRequest.model_validate(request_payload())
    )

    assert response.success is False
    assert response.recommendations == []
    assert "No sample walking route" in response.unavailable_reasons[0]


def test_health_check_remains_available() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "meal-planning-service"}
