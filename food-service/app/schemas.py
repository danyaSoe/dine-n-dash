from datetime import time
from typing import Literal

from pydantic import BaseModel

MealMode = Literal["dine_in", "takeaway"]


class OpeningHours(BaseModel):
    opens_at: time
    closes_at: time


class WaitingTimeEstimate(BaseModel):
    start_time: time
    end_time: time
    minutes: int


class Restaurant(BaseModel):
    id: str
    name: str
    opening_hours: OpeningHours
    supported_meal_modes: tuple[MealMode, ...]
    waiting_time_estimates: tuple[WaitingTimeEstimate, ...]


class RestaurantsResponse(BaseModel):
    data_source: Literal["sample"] = "sample"
    restaurants: tuple[Restaurant, ...]


class RestaurantResponse(BaseModel):
    data_source: Literal["sample"] = "sample"
    restaurant: Restaurant


class RestaurantAvailabilityResponse(BaseModel):
    data_source: Literal["sample"] = "sample"
    restaurant_id: str
    arrival_time: time
    is_open: bool
    meal_mode: MealMode
    supports_meal_mode: bool
    waiting_minutes: int | None
