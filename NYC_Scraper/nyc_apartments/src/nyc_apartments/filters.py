from __future__ import annotations

from typing import Iterable, List

from .config import AppConfig
from .geo import within_radius
from .models import Apartment, Location


def filter_by_price(
    apartments: Iterable[Apartment], min_price: int | None, max_price: int | None
) -> List[Apartment]:
    result: List[Apartment] = []
    for apt in apartments:
        price = apt.price
        if price is None:
            # Keep entries without price; they can still be useful for non-price queries.
            result.append(apt)
            continue
        if min_price is not None and price < min_price:
            continue
        if max_price is not None and price > max_price:
            continue
        result.append(apt)
    return result


def filter_by_beds(
    apartments: Iterable[Apartment], min_beds: float | None, max_beds: float | None
) -> List[Apartment]:
    result: List[Apartment] = []
    for apt in apartments:
        beds = apt.beds
        if beds is None:
            result.append(apt)
            continue
        if min_beds is not None and beds < min_beds:
            continue
        if max_beds is not None and beds > max_beds:
            continue
        result.append(apt)
    return result


def filter_by_radius(
    apartments: Iterable[Apartment], center: Location, radius_km: float
) -> List[Apartment]:
    result: List[Apartment] = []
    for apt in apartments:
        if apt.lat is None or apt.lon is None:
            # Drop entries without coordinates when filtering by radius.
            continue
        if within_radius(center, Location(lat=apt.lat, lon=apt.lon), radius_km):
            result.append(apt)
    return result


def apply_filters(
    apartments: Iterable[Apartment],
    config: AppConfig,
    center: Location,
) -> List[Apartment]:
    """Apply all configured filters and return a new list."""

    result: List[Apartment] = list(apartments)
    result = filter_by_radius(result, center, config.radius_km)
    result = filter_by_price(result, config.min_price, config.max_price)
    result = filter_by_beds(result, config.min_beds, config.max_beds)

    if config.limit is not None and config.limit > 0:
        result = result[: config.limit]

    return result
