from datetime import time

from app.clients.http import request_model, service_url
from app.schemas import (
    MealMode,
    RestaurantAvailabilityResponse,
    RestaurantsResponse,
)


def get_restaurants() -> RestaurantsResponse:
    base_url = service_url("FOOD_SERVICE_URL", "http://127.0.0.1:8002")
    return request_model(
        service_name="Food Service",
        url=f"{base_url}/restaurants",
        params=None,
        response_model=RestaurantsResponse,
    )


def get_availability(
    restaurant_id: str,
    arrival_time: time,
    meal_mode: MealMode,
) -> RestaurantAvailabilityResponse:
    base_url = service_url("FOOD_SERVICE_URL", "http://127.0.0.1:8002")
    return request_model(
        service_name="Food Service",
        url=f"{base_url}/restaurants/{restaurant_id}/availability",
        params={
            "arrival_time": arrival_time.strftime("%H:%M"),
            "meal_mode": meal_mode,
        },
        response_model=RestaurantAvailabilityResponse,
    )
