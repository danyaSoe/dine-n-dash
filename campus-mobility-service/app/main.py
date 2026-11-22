from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

from app.data import LOCATIONS, LOCATION_NAMES, WALKING_TIMES_MINUTES
from app.schemas import LocationsResponse, RouteEstimateResponse

app = FastAPI(title="Campus Mobility Service")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "campus-mobility-service"}


@app.get("/locations", response_model=LocationsResponse)
def list_locations() -> LocationsResponse:
    return LocationsResponse(locations=LOCATIONS)


@app.get("/routes/estimate", response_model=RouteEstimateResponse)
def estimate_route(
    origin: Annotated[str, Query(min_length=1, max_length=100)],
    destination: Annotated[str, Query(min_length=1, max_length=100)],
) -> RouteEstimateResponse:
    origin = origin.strip()
    destination = destination.strip()

    if not origin or not destination:
        raise HTTPException(
            status_code=422,
            detail="Origin and destination must not be blank.",
        )

    unknown_locations = [
        name for name in (origin, destination) if name not in LOCATION_NAMES
    ]
    if unknown_locations:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown location(s): {', '.join(unknown_locations)}.",
        )

    if origin == destination:
        walking_minutes = 0
    else:
        route_key = tuple(sorted((origin, destination)))
        walking_minutes = WALKING_TIMES_MINUTES.get(route_key)
        if walking_minutes is None:
            raise HTTPException(
                status_code=404,
                detail=f"No sample walking route is available between "
                f"'{origin}' and '{destination}'.",
            )

    return RouteEstimateResponse(
        origin=origin,
        destination=destination,
        walking_minutes=walking_minutes,
    )
