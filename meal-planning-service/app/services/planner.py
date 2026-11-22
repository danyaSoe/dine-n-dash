from datetime import time

from app.clients.errors import RouteUnavailableError
from app.clients.food import get_availability, get_restaurants
from app.clients.mobility import get_route_estimate
from app.schemas import (
    Recommendation,
    RecommendationRequest,
    RecommendationsResponse,
    Restaurant,
)


def _minutes_after_midnight(value: time) -> int:
    return value.hour * 60 + value.minute


def _time_after_minutes(start: time, duration_minutes: int) -> time | None:
    total_minutes = _minutes_after_midnight(start) + duration_minutes
    if total_minutes >= 24 * 60:
        return None
    return time(total_minutes // 60, total_minutes % 60)


def _same_day_minute_after(start: time, duration_minutes: int) -> int | None:
    result = _time_after_minutes(start, duration_minutes)
    if result is None:
        return None
    return _minutes_after_midnight(result)


def _unavailable(restaurant: Restaurant, reason: str) -> str:
    return f"{restaurant.name}: {reason}"


def create_recommendations(
    request: RecommendationRequest,
) -> RecommendationsResponse:
    restaurants_response = get_restaurants()
    arrival_deadline = (
        _minutes_after_midnight(request.class_start) - request.buffer_minutes
    )
    recommendations: list[Recommendation] = []
    unavailable_reasons: list[str] = []

    for restaurant in restaurants_response.restaurants:
        try:
            travel_to = get_route_estimate(request.origin, restaurant.name)
            travel_to_class = get_route_estimate(restaurant.name, request.destination)
        except RouteUnavailableError as exc:
            unavailable_reasons.append(_unavailable(restaurant, str(exc)))
            continue

        restaurant_arrival = _time_after_minutes(
            request.ready_time,
            travel_to.walking_minutes,
        )
        if restaurant_arrival is None:
            unavailable_reasons.append(
                _unavailable(restaurant, "arrival would be after midnight.")
            )
            continue

        availability = get_availability(
            restaurant.id,
            restaurant_arrival,
            request.meal_mode,
        )
        if not availability.is_open:
            unavailable_reasons.append(
                _unavailable(restaurant, "closed at the estimated arrival time.")
            )
            continue
        if not availability.supports_meal_mode:
            unavailable_reasons.append(
                _unavailable(
                    restaurant,
                    f"does not support {request.meal_mode}.",
                )
            )
            continue
        if availability.waiting_minutes is None:
            unavailable_reasons.append(
                _unavailable(restaurant, "waiting-time estimate is unavailable.")
            )
            continue

        meal_duration = (
            (request.meal_duration_minutes or 0)
            if request.meal_mode == "dine_in"
            else 0
        )
        service_complete = _time_after_minutes(
            restaurant_arrival,
            availability.waiting_minutes + meal_duration,
        )
        if service_complete is None:
            unavailable_reasons.append(
                _unavailable(restaurant, "service would continue after midnight.")
            )
            continue
        if service_complete > restaurant.opening_hours.closes_at:
            unavailable_reasons.append(
                _unavailable(restaurant, "service would finish after closing time.")
            )
            continue

        estimated_arrival = _same_day_minute_after(
            service_complete,
            travel_to_class.walking_minutes,
        )
        if estimated_arrival is None:
            unavailable_reasons.append(
                _unavailable(restaurant, "arrival at class would be after midnight.")
            )
            continue

        remaining_minutes = arrival_deadline - estimated_arrival
        if remaining_minutes < 0:
            unavailable_reasons.append(
                _unavailable(
                    restaurant,
                    f"would arrive {abs(remaining_minutes)} minute(s) after "
                    "the arrival deadline.",
                )
            )
            continue

        departure_deadline = arrival_deadline - travel_to_class.walking_minutes
        departure_hour, departure_minute = divmod(departure_deadline, 60)
        recommendations.append(
            Recommendation(
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name,
                travel_to_restaurant_minutes=travel_to.walking_minutes,
                waiting_minutes=availability.waiting_minutes,
                meal_duration_minutes=meal_duration,
                travel_to_class_minutes=travel_to_class.walking_minutes,
                departure_deadline=f"{departure_hour:02d}:{departure_minute:02d}",
                remaining_minutes=remaining_minutes,
            )
        )

    recommendations.sort(key=lambda item: item.remaining_minutes, reverse=True)
    return RecommendationsResponse(
        success=bool(recommendations),
        recommendations=recommendations,
        unavailable_reasons=unavailable_reasons,
    )
