from __future__ import annotations

import math
from typing import Optional, Tuple

from geopy.geocoders import Nominatim

from .models import Location


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth in kilometers."""

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def within_radius(
    center: Location, point: Location, radius_km: float
) -> bool:
    return haversine_km(center.lat, center.lon, point.lat, point.lon) <= radius_km


_geocoder: Optional[Nominatim] = None


def get_geocoder(user_agent: str = "nyc-apartments-scraper") -> Nominatim:
    global _geocoder
    if _geocoder is None:
        _geocoder = Nominatim(user_agent=user_agent)
    return _geocoder


def geocode_address(address: str, user_agent: Optional[str] = None) -> Optional[Location]:
    """Geocode an address into a Location (lat/lon) or return None on failure."""

    geocoder = get_geocoder(user_agent or "nyc-apartments-scraper")
    result = geocoder.geocode(address)
    if not result:
        return None
    return Location(lat=result.latitude, lon=result.longitude)
