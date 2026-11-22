from app.clients.errors import (
    DependencyNotFoundError,
    DependencyRequestError,
    RouteUnavailableError,
)
from app.clients.http import request_model, service_url
from app.schemas import RouteEstimateResponse


def get_route_estimate(origin: str, destination: str) -> RouteEstimateResponse:
    base_url = service_url("MOBILITY_SERVICE_URL", "http://127.0.0.1:8001")
    try:
        return request_model(
            service_name="Campus Mobility Service",
            url=f"{base_url}/routes/estimate",
            params={"origin": origin, "destination": destination},
            response_model=RouteEstimateResponse,
        )
    except DependencyNotFoundError as exc:
        raise RouteUnavailableError(str(exc)) from exc
    except DependencyRequestError:
        raise
