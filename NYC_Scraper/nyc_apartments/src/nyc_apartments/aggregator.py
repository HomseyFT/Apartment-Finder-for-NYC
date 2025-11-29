from __future__ import annotations

import logging
from typing import Iterable, List, Sequence, Type

from .config import AppConfig
from .filters import apply_filters
from .geo import geocode_address
from .models import Apartment, Location
from .providers.base import BaseProvider, discover_providers

logger = logging.getLogger(__name__)


def resolve_center(config: AppConfig) -> Location:
    if config.center_lat is not None and config.center_lon is not None:
        return Location(lat=config.center_lat, lon=config.center_lon)

    if not config.center_address:
        raise ValueError(
            "Either center_lat/center_lon or center_address must be provided."
        )

    loc = geocode_address(config.center_address, user_agent=config.geocoder_user_agent)
    if loc is None:
        raise RuntimeError(f"Could not geocode center address: {config.center_address!r}")

    return loc


def run_aggregation(config: AppConfig) -> List[Apartment]:
    center = resolve_center(config)

    providers: Sequence[Type[BaseProvider]] = discover_providers(config.providers)
    logger.info("Discovered providers: %s", [p.name for p in providers])

    apartments: List[Apartment] = []

    for provider_cls in providers:
        provider = provider_cls()
        try:
            results = provider.fetch(config)
            apartments.extend(results)
        except Exception as exc:  # noqa: BLE001 - this is CLI tooling, log and continue
            logger.exception("Provider %s failed: %s", provider.name, exc)

    # Deduplicate by (provider, id)
    seen: set[tuple[str, str]] = set()
    deduped: List[Apartment] = []
    for apt in apartments:
        key = (apt.provider, apt.id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(apt)

    filtered = apply_filters(deduped, config, center)

    # Sort: first by distance to center (if available), then by price (if available)
    def sort_key(apt: Apartment):
        if apt.lat is None or apt.lon is None:
            distance = float("inf")
        else:
            # lazy import to avoid circular import
            from .geo import haversine_km

            distance = haversine_km(center.lat, center.lon, apt.lat, apt.lon)
        price = apt.price if apt.price is not None else float("inf")
        return (distance, price)

    filtered.sort(key=sort_key)
    return filtered
