"""Sample campus locations and undirected walking-time estimates."""

from typing import Final

LOCATIONS: Final[tuple[dict[str, str], ...]] = (
    {"id": "LABTEK_V", "name": "Labtek V"},
    {"id": "LABTEK_VIII", "name": "Labtek VIII"},
    {"id": "R001", "name": "Warung A"},
    {"id": "R002", "name": "Warung B"},
    {"id": "R003", "name": "Warung C"},
    {"id": "R004", "name": "Warung D"},
    {"id": "R005", "name": "Warung E"},
)

_WALKING_TIMES: Final[dict[tuple[str, str], int]] = {
    ("Labtek V", "Labtek VIII"): 15,
    ("Labtek V", "Warung A"): 7,
    ("Labtek VIII", "Warung A"): 8,
    ("Labtek V", "Warung B"): 9,
    ("Labtek VIII", "Warung B"): 6,
    ("Labtek V", "Warung C"): 11,
    ("Labtek VIII", "Warung C"): 5,
    ("Labtek V", "Warung D"): 6,
    ("Labtek VIII", "Warung D"): 10,
    ("Labtek V", "Warung E"): 8,
    ("Labtek VIII", "Warung E"): 7,
}

WALKING_TIMES_MINUTES: Final[dict[tuple[str, str], int]] = {
    tuple(sorted((origin, destination))): minutes
    for (origin, destination), minutes in _WALKING_TIMES.items()
}

LOCATION_NAMES: Final[frozenset[str]] = frozenset(
    location["name"] for location in LOCATIONS
)
