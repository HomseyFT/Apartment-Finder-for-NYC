from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from ..config import AppConfig
from ..http_client import fetch_json
from ..models import Apartment
from .base import BaseProvider


_RENTCAST_LISTINGS_URL = "https://api.rentcast.io/v1/listings/rental/long-term"
_MAX_RENTCAST_LIMIT = 500  # per RentCast docs


class RentcastLongTermRentalProvider(BaseProvider):
    """Provider backed by RentCast long-term rental listings.

    This uses the configured center address/coords and radius to query the
    RentCast listings API and normalize the results into Apartment objects.
    """

    name = "rentcast_rental_listings"

    def fetch(self, config: AppConfig) -> List[Apartment]:
        # Prefer the config value, but also fall back to the raw env var in case
        # settings/env-prefix wiring changes.
        api_key = config.rentcast_api_key or os.getenv("RENTCAST_API_KEY")
        if not api_key:
            # No key configured; silently return no results so other providers can run.
            return []
        # Resolve center; this may geocode center_address if lat/lon were not set.
        from ..aggregator import resolve_center  # lazy import to avoid cycles

        center = resolve_center(config)

        # RentCast expects radius in miles.
        radius_miles = max(config.radius_km, 0.1) * 0.621371

        # Respect the global limit when choosing how many listings to request.
        if config.limit is not None and config.limit > 0:
            requested = min(config.limit, _MAX_RENTCAST_LIMIT)
        else:
            requested = 100

        headers: Dict[str, str] = {"X-Api-Key": api_key}

        params: Dict[str, Any] = {
            "latitude": center.lat,
            "longitude": center.lon,
            "radius": radius_miles,
            "status": "Active",
            "limit": requested,
        }

        # Map price and bedroom filters to RentCast's numeric range syntax when available.
        if config.min_price is not None or config.max_price is not None:
            min_val = str(config.min_price) if config.min_price is not None else "*"
            max_val = str(config.max_price) if config.max_price is not None else "*"
            params["price"] = f"{min_val}:{max_val}"

        if config.min_beds is not None or config.max_beds is not None:
            min_val = str(config.min_beds) if config.min_beds is not None else "*"
            max_val = str(config.max_beds) if config.max_beds is not None else "*"
            params["bedrooms"] = f"{min_val}:{max_val}"

        raw = fetch_json(_RENTCAST_LISTINGS_URL, params=params, headers=headers)
        if not isinstance(raw, list):
            return []

        apartments: List[Apartment] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                apartments.append(self._normalize(item))
            except Exception:
                # Be tolerant of schema surprises and bad rows.
                continue

        return apartments

    def _normalize(self, data: Dict[str, Any]) -> Apartment:
        # Basic identifiers
        listing_id = str(
            data.get("id")
            or data.get("listingId")
            or data.get("zillowId")
            or data.get("mlsId")
            or ""
        )
        if not listing_id:
            # Fallback to address-based ID if absolutely necessary.
            addr_bits = [
                str(data.get("addressLine1") or "").strip(),
                str(data.get("city") or "").strip(),
                str(data.get("state") or "").strip(),
                str(data.get("zipCode") or "").strip(),
            ]
            listing_id = "|".join([b for b in addr_bits if b]) or "unknown-id"

        # Address components
        formatted_address = (data.get("formattedAddress") or "").strip()
        address_line1 = (data.get("addressLine1") or "").strip()
        city = (data.get("city") or "New York").strip() or "New York"
        state = (data.get("state") or "NY").strip() or "NY"
        zipcode_val: Optional[str] = None
        if data.get("zipCode") is not None:
            zipcode_val = str(data.get("zipCode")).strip() or None

        if formatted_address:
            address = formatted_address
        elif address_line1:
            parts = [address_line1, city, state]
            if zipcode_val:
                parts.append(zipcode_val)
            address = ", ".join(parts)
        else:
            address = "Unknown address"

        lat: Optional[float] = None
        lon: Optional[float] = None
        if data.get("latitude") is not None and data.get("longitude") is not None:
            try:
                lat = float(data["latitude"])  # type: ignore[arg-type]
                lon = float(data["longitude"])  # type: ignore[arg-type]
            except (TypeError, ValueError):
                lat = lon = None

        # Core unit attributes
        price_val: Optional[int] = None
        if data.get("price") is not None:
            try:
                price_val = int(float(data["price"]))  # guard against strings/floats
            except (TypeError, ValueError):
                price_val = None

        beds_val: Optional[float] = None
        if data.get("bedrooms") is not None:
            try:
                beds_val = float(data["bedrooms"])  # type: ignore[arg-type]
            except (TypeError, ValueError):
                beds_val = None

        baths_val: Optional[float] = None
        if data.get("bathrooms") is not None:
            try:
                baths_val = float(data["bathrooms"])  # type: ignore[arg-type]
            except (TypeError, ValueError):
                baths_val = None

        # Optional title from property type and status
        property_type = (data.get("propertyType") or "").strip()
        status = (data.get("status") or "").strip()
        title_parts = []
        if beds_val is not None:
            title_parts.append(f"{beds_val:g} BR")
        if property_type:
            title_parts.append(property_type)
        if status:
            title_parts.append(f"({status})")
        title = " ".join(title_parts) or None

        # Construct a stable RentCast property report URL, if address is known.
        url: Optional[str] = None
        if formatted_address:
            from urllib.parse import quote_plus

            encoded_addr = quote_plus(formatted_address)
            url = f"https://app.rentcast.io/property-reports?address={encoded_addr}"

        return Apartment(
            id=listing_id,
            provider=self.name,
            title=title,
            address=address,
            neighborhood=None,
            city=city,
            state=state,
            zipcode=zipcode_val,
            lat=lat,
            lon=lon,
            price=price_val,
            beds=beds_val,
            baths=baths_val,
            url=url,
            raw=data,
        )
