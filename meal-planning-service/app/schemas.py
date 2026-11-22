from datetime import time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

MealMode = Literal["dine_in", "takeaway"]


class RecommendationRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=100)
    ready_time: time
    class_start: time
    buffer_minutes: int = Field(ge=0)
    meal_mode: MealMode
    meal_duration_minutes: int | None = Field(default=None, ge=0)

    @field_validator("origin", "destination")
    @classmethod
    def validate_location_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Location must not be blank.")
        return value.strip()

    @model_validator(mode="after")
    def validate_same_day_schedule(self) -> "RecommendationRequest":
        if self.ready_time.tzinfo is not None or self.class_start.tzinfo is not None:
            raise ValueError("Times must be local times without a timezone.")
        if self.ready_time.second or self.ready_time.microsecond:
            raise ValueError("Times must use minute precision (HH:MM).")
        if self.class_start.second or self.class_start.microsecond:
            raise ValueError("Times must use minute precision (HH:MM).")
        if self.class_start <= self.ready_time:
            raise ValueError("class_start must be after ready_time on the same day.")
        if self.meal_mode == "dine_in" and self.meal_duration_minutes is None:
            raise ValueError("meal_duration_minutes is required for dine_in.")
        return self


class RestaurantOpeningHours(BaseModel):
    opens_at: time
    closes_at: time


class RestaurantWaitingTimeEstimate(BaseModel):
    start_time: time
    end_time: time
    minutes: int = Field(ge=0)


class Restaurant(BaseModel):
    id: str
    name: str
    opening_hours: RestaurantOpeningHours
    supported_meal_modes: tuple[MealMode, ...]
    waiting_time_estimates: tuple[RestaurantWaitingTimeEstimate, ...]


class RestaurantsResponse(BaseModel):
    data_source: Literal["sample"]
    restaurants: tuple[Restaurant, ...]


class RestaurantAvailabilityResponse(BaseModel):
    data_source: Literal["sample"]
    restaurant_id: str
    arrival_time: time
    is_open: bool
    meal_mode: MealMode
    supports_meal_mode: bool
    waiting_minutes: int | None = Field(ge=0)


class RouteEstimateResponse(BaseModel):
    data_source: Literal["sample"]
    origin: str
    destination: str
    walking_minutes: int = Field(ge=0)


class Recommendation(BaseModel):
    restaurant_id: str
    restaurant_name: str
    travel_to_restaurant_minutes: int
    waiting_minutes: int
    meal_duration_minutes: int
    travel_to_class_minutes: int
    departure_deadline: str
    remaining_minutes: int


class RecommendationsResponse(BaseModel):
    success: bool
    recommendations: list[Recommendation]
    unavailable_reasons: list[str]
