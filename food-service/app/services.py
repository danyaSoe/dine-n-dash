from datetime import time

from app.schemas import MealMode, Restaurant


def is_open(restaurant: Restaurant, arrival_time: time) -> bool:
    opening_hours = restaurant.opening_hours
    return opening_hours.opens_at <= arrival_time < opening_hours.closes_at


def get_waiting_minutes(restaurant: Restaurant, arrival_time: time) -> int | None:
    for estimate in restaurant.waiting_time_estimates:
        if estimate.start_time <= arrival_time < estimate.end_time:
            return estimate.minutes
    return None


def supports_meal_mode(restaurant: Restaurant, meal_mode: MealMode) -> bool:
    return meal_mode in restaurant.supported_meal_modes
