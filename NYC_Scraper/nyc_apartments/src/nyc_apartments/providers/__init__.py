"""Pluggable data providers for nyc_apartments."""

from .base import BaseProvider, discover_providers

__all__ = ["BaseProvider", "discover_providers"]
