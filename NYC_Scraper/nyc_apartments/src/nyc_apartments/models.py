from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class Apartment(BaseModel):
    """Normalized apartment / unit representation across all providers."""

    id: str = Field(..., description="Provider-specific unique identifier for the unit")
    provider: str = Field(..., description="Name of the source/provider")

    title: Optional[str] = Field(None, description="Short human-friendly title, if any")

    address: str = Field(..., description="Full street address")
    neighborhood: Optional[str] = Field(None, description="Neighborhood or NTA name")
    city: str = Field("New York", description="City name")
    state: str = Field("NY", description="State code")
    zipcode: Optional[str] = None

    lat: Optional[float] = Field(None, description="Latitude of the unit/building")
    lon: Optional[float] = Field(None, description="Longitude of the unit/building")

    price: Optional[int] = Field(
        None,
        description="Monthly rent in dollars, if available from the provider.",
    )
    beds: Optional[float] = None
    baths: Optional[float] = None

    url: Optional[HttpUrl] = Field(
        None,
        description="Public listing / info URL, if available.",
    )

    raw: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional raw payload from the provider for debugging.",
    )


class Location(BaseModel):
    lat: float
    lon: float
