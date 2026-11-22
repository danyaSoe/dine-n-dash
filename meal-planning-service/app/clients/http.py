import math
import os
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.clients.errors import DependencyNotFoundError, DependencyRequestError

ModelT = TypeVar("ModelT", bound=BaseModel)


def request_model(
    *,
    service_name: str,
    url: str,
    params: dict[str, str] | None,
    response_model: type[ModelT],
) -> ModelT:
    try:
        timeout = float(os.getenv("SERVICE_TIMEOUT_SECONDS", "3"))
    except ValueError as exc:
        raise DependencyRequestError(
            service_name,
            "SERVICE_TIMEOUT_SECONDS must be a positive number.",
        ) from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise DependencyRequestError(
            service_name,
            "SERVICE_TIMEOUT_SECONDS must be a positive number.",
        )

    try:
        response = httpx.get(url, params=params, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_type = (
            DependencyNotFoundError
            if exc.response.status_code == 404
            else DependencyRequestError
        )
        raise error_type(
            service_name,
            f"HTTP {exc.response.status_code} from the configured endpoint.",
        ) from exc
    except httpx.RequestError as exc:
        raise DependencyRequestError(
            service_name,
            f"request failed ({type(exc).__name__}).",
        ) from exc
    except httpx.InvalidURL as exc:
        raise DependencyRequestError(
            service_name,
            "the configured endpoint URL is invalid.",
        ) from exc

    try:
        return response_model.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise DependencyRequestError(
            service_name,
            "the response did not match the expected API contract.",
        ) from exc


def service_url(environment_variable: str, default: str) -> str:
    return os.getenv(environment_variable, default).rstrip("/")
