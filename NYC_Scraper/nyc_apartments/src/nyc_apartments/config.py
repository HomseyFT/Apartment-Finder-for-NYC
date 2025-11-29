from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application configuration loaded from env and CLI overrides."""

    # Center location
    center_address: Optional[str] = Field(
        None,
        description="Human-readable address used for geocoding center point.",
    )
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None

    # Search constraints
    radius_km: float = 3.0
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_beds: Optional[float] = None
    max_beds: Optional[float] = None

    # Providers
    providers: List[str] = Field(
        default_factory=list,
        description="List of provider names to enable; empty means all discovered.",
    )

    # Output
    output_format: str = Field("table", description="table | json | csv")
    limit: Optional[int] = Field(
        None,
        description="Max number of apartments to return after filtering.",
    )

    # NYC Open Data / HTTP
    nyc_open_data_app_token: Optional[str] = Field(
        default=None,
        env="NYC_OPEN_DATA_APP_TOKEN",
    )

    http_proxy: Optional[str] = Field(default=None, env="HTTP_PROXY")
    https_proxy: Optional[str] = Field(default=None, env="HTTPS_PROXY")

    geocoder_user_agent: str = Field(
        default="nyc-apartments-scraper",
        env="GEOCODER_USER_AGENT",
    )

    class Config:
        env_prefix = "NYC_APTS_"
        case_sensitive = False


def _load_base_config() -> AppConfig:
    load_dotenv()  # Load from .env if present
    return AppConfig()  # type: ignore[arg-type]


@lru_cache(maxsize=1)
def get_base_config() -> AppConfig:
    """Load config (from env/.env) once and cache it."""

    return _load_base_config()


def merge_cli_overrides(base: AppConfig, **overrides: object) -> AppConfig:
    """Return a new AppConfig with CLI overrides applied if not None.

    Typer will pass None for options that were not explicitly set, so we only
    update the underlying settings for keys that have non-None values.
    """

    data = base.dict()
    for key, value in overrides.items():
        if value is not None and key in data:
            data[key] = value
    return AppConfig(**data)
