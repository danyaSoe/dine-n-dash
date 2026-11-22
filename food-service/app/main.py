from datetime import time
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from app.data import (
    RESTAURANTS,
    RESTAURANTS_BY_ID,
)
from app.schemas import (
    MealMode,
    RestaurantAvailabilityResponse,
    RestaurantResponse,
    RestaurantsResponse,
)
from app.services import (
    get_waiting_minutes,
    is_open,
    supports_meal_mode,
)

app = FastAPI(title="Food Service")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "food-service"}


@app.get("/restaurants", response_model=RestaurantsResponse)
def list_restaurants() -> RestaurantsResponse:
    return RestaurantsResponse(restaurants=RESTAURANTS)


@app.get("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(restaurant_id: str) -> RestaurantResponse:
    restaurant = RESTAURANTS_BY_ID.get(restaurant_id)
    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail=f"Restaurant '{restaurant_id}' was not found.",
        )
    return RestaurantResponse(restaurant=restaurant)


@app.get(
    "/restaurants/{restaurant_id}/availability",
    response_model=RestaurantAvailabilityResponse,
)
def check_availability(
    restaurant_id: str,
    arrival_time: Annotated[time, Query()],
    meal_mode: Annotated[MealMode, Query()],
) -> RestaurantAvailabilityResponse:
    if arrival_time.tzinfo is not None:
        raise HTTPException(
            status_code=422,
            detail="arrival_time must be a local time without a timezone.",
        )

    restaurant = RESTAURANTS_BY_ID.get(restaurant_id)
    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail=f"Restaurant '{restaurant_id}' was not found.",
        )

    restaurant_is_open = is_open(restaurant, arrival_time)
    waiting_minutes = (
        get_waiting_minutes(restaurant, arrival_time) if restaurant_is_open else None
    )
    if restaurant_is_open and waiting_minutes is None:
        raise HTTPException(
            status_code=500,
            detail=f"No sample waiting-time estimate is configured for "
            f"restaurant '{restaurant_id}' at {arrival_time.strftime('%H:%M')}.",
        )

    return RestaurantAvailabilityResponse(
        restaurant_id=restaurant.id,
        arrival_time=arrival_time,
        is_open=restaurant_is_open,
        meal_mode=meal_mode,
        supports_meal_mode=supports_meal_mode(restaurant, meal_mode),
        waiting_minutes=waiting_minutes,
    )
