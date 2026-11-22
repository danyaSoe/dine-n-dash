"""Sample restaurant records used by the Food Service."""

from datetime import time
from typing import Final

from app.schemas import Restaurant

RESTAURANTS: Final[tuple[Restaurant, ...]] = (
    Restaurant(
        id="R001",
        name="Warung A",
        opening_hours={"opens_at": time(8), "closes_at": time(17)},
        supported_meal_modes=("dine_in", "takeaway"),
        waiting_time_estimates=(
            {"start_time": time(8), "end_time": time(12), "minutes": 8},
            {"start_time": time(12), "end_time": time(17), "minutes": 12},
        ),
    ),
    Restaurant(
        id="R002",
        name="Warung B",
        opening_hours={"opens_at": time(8), "closes_at": time(17)},
        supported_meal_modes=("takeaway",),
        waiting_time_estimates=(
            {"start_time": time(8), "end_time": time(11), "minutes": 10},
            {"start_time": time(11), "end_time": time(17), "minutes": 14},
        ),
    ),
    Restaurant(
        id="R003",
        name="Warung C",
        opening_hours={"opens_at": time(10), "closes_at": time(18)},
        supported_meal_modes=("dine_in",),
        waiting_time_estimates=(
            {"start_time": time(10), "end_time": time(13), "minutes": 6},
            {"start_time": time(13), "end_time": time(18), "minutes": 9},
        ),
    ),
    Restaurant(
        id="R004",
        name="Warung D",
        opening_hours={"opens_at": time(9), "closes_at": time(16)},
        supported_meal_modes=("dine_in", "takeaway"),
        waiting_time_estimates=(
            {"start_time": time(9), "end_time": time(12), "minutes": 7},
            {"start_time": time(12), "end_time": time(16), "minutes": 11},
        ),
    ),
    Restaurant(
        id="R005",
        name="Warung E",
        opening_hours={"opens_at": time(8), "closes_at": time(16)},
        supported_meal_modes=("dine_in", "takeaway"),
        waiting_time_estimates=(
            {"start_time": time(8), "end_time": time(12), "minutes": 9},
            {"start_time": time(12), "end_time": time(16), "minutes": 13},
        ),
    ),
)

RESTAURANTS_BY_ID: Final[dict[str, Restaurant]] = {
    restaurant.id: restaurant for restaurant in RESTAURANTS
}
