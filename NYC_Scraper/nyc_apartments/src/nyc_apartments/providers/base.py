from __future__ import annotations

import abc
import importlib
import inspect
import pkgutil
from typing import ClassVar, List, Sequence, Type

from ..config import AppConfig
from ..models import Apartment


class BaseProvider(abc.ABC):
    """Base class for all listing providers."""

    #: Short string identifier used in config/CLI.
    name: ClassVar[str]

    @abc.abstractmethod
    def fetch(self, config: AppConfig) -> List[Apartment]:
        """Fetch apartments for the given configuration."""


def _iter_provider_classes() -> List[Type[BaseProvider]]:
    """Import all submodules of the providers package and collect subclasses.

    Note: ``__path__`` only exists on packages, not on this module, so we first
    resolve the parent package object and then use its ``__path__`` for
    discovery.
    """

    providers: List[Type[BaseProvider]] = []

    # This module lives in nyc_apartments.providers.base
    package_name = __name__.rsplit(".", 1)[0]
    package = importlib.import_module(package_name)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return providers

    # Walk all modules in this package.
    for module_info in pkgutil.iter_modules(package_path, prefix=package_name + "."):
        module = importlib.import_module(module_info.name)
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseProvider) and obj is not BaseProvider:
                providers.append(obj)

    return providers


_DISCOVERED: Sequence[Type[BaseProvider]] | None = None


def discover_providers(enabled_names: Sequence[str] | None = None) -> Sequence[Type[BaseProvider]]:
    """Discover all provider classes in this package.

    If *enabled_names* is provided and non-empty, only providers whose
    ``.name`` attribute is in that list are returned.
    """

    global _DISCOVERED
    if _DISCOVERED is None:
        _DISCOVERED = _iter_provider_classes()

    if not enabled_names:
        return list(_DISCOVERED)

    enabled = set(enabled_names)
    return [cls for cls in _DISCOVERED if getattr(cls, "name", None) in enabled]
