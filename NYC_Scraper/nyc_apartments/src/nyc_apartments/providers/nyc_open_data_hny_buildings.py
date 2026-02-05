from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import AppConfig
from ..http_client import fetch_json
from ..models import Apartment
from .base import BaseProvider


# Housing New York Units by Building dataset on NYC Open Data (Socrata)
# Landing page: https://data.cityofnewyork.us/Housing-Development/Housing-New-York-Units-by-Building/hg8x-zxpr
# API endpoint pattern: https://data.cityofnewyork.us/resource/hg8x-zxpr.json
_DATASET_URL = "https://data.cityofnewyork.us/resource/hg8x-zxpr.json"
_MAX_ROWS = 5000


class NYCHousingNewYorkBuildingsProvider(BaseProvider):
    """Provider backed by HPD's Housing New York Units by Building dataset.

    This is not a live listing feed; it exposes affordable housing
    production/preservation data at the building level, used here as a
    stand-in for apartment inventory so you can exercise the pipeline.
    """

    name = "nyc_open_data_hny_buildings"

    def fetch(self, config: AppConfig) -> List[Apartment]:
        headers: Dict[str, str] = {}
        if config.nyc_open_data_app_token:
            headers["X-App-Token"] = config.nyc_open_data_app_token

        params: Dict[str, Any] = {"$limit": _MAX_ROWS}

        raw = fetch_json(_DATASET_URL, params=params, headers=headers)
        if not isinstance(raw, list):
            return []

        apartments: List[Apartment] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                apartments.append(self._normalize(item))
            except Exception:
                # Be tolerant of occasional bad rows / schema surprises.
                continue

        return apartments

    def _normalize(self, data: Dict[str, Any]) -> Apartment:
        # IDs
        building_id = str(
            data.get("building_id")
            or data.get("buildingid")
            or data.get("building_id_number")
            or ""
        )
        project_id = str(data.get("project_id") or data.get("projectid") or "")

        if building_id:
            apt_id = building_id
        elif project_id:
            apt_id = project_id
        else:
            addr_bits = [
                str(data.get("house_number") or data.get("low_house_number") or "").strip(),
                str(data.get("street_name") or data.get("streetname") or "").strip(),
                str(data.get("borough") or data.get("boro") or "").strip(),
            ]
            apt_id = "|".join(addr_bits) or "unknown-id"

        # Address
        house_num = str(
            data.get("house_number")
            or data.get("low_house_number")
            or data.get("high_house_number")
            or ""
        ).strip()
        street = str(data.get("street_name") or data.get("streetname") or "").strip()
        borough = str(data.get("borough") or data.get("boro") or "").strip()

        parts = [p for p in [house_num, street] if p]
        address = " ".join(parts) if parts else "Unknown address"
        if borough:
            address = f"{address}, {borough}"

        zipcode = data.get("postcode") or data.get("zip") or None

        # Coordinates: dataset may expose latitude/longitude or a location object
        lat: Optional[float] = None
        lon: Optional[float] = None

        if "latitude" in data and "longitude" in data:
            try:
                lat = float(data["latitude"])
                lon = float(data["longitude"])
            except (TypeError, ValueError):
                lat = lon = None
        elif "location" in data and isinstance(data["location"], dict):
            loc = data["location"]
            coords = loc.get("coordinates")
            if isinstance(coords, (list, tuple)) and len(coords) == 2:
                try:
                    lon = float(coords[0])
                    lat = float(coords[1])
                except (TypeError, ValueError):
                    lat = lon = None

        neighborhood = data.get("nta_name") or data.get("neighborhood") or None

        return Apartment(
            id=apt_id,
            provider=self.name,
            title=data.get("project_name") or None,
            address=address,
            neighborhood=neighborhood,
            zipcode=str(zipcode) if zipcode is not None else None,
            lat=lat,
            lon=lon,
            price=None,  # Dataset does not include rents
            beds=None,
            baths=None,
            url=None,
            raw=data,
        )
