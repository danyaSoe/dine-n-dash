from typing import Literal

from pydantic import BaseModel


class Location(BaseModel):
    id: str
    name: str


class LocationsResponse(BaseModel):
    data_source: Literal["sample"] = "sample"
    locations: list[Location]


class RouteEstimateResponse(BaseModel):
    data_source: Literal["sample"] = "sample"
    origin: str
    destination: str
    walking_minutes: int
