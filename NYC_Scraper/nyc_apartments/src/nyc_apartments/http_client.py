from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import requests

from .config import get_base_config

logger = logging.getLogger(__name__)

_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        config = get_base_config()
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": "nyc-apartments-scraper/0.1",
            "Accept": "application/json",
        })
        proxies: Dict[str, str] = {}
        if config.http_proxy:
            proxies["http"] = config.http_proxy
        if config.https_proxy:
            proxies["https"] = config.https_proxy
        if proxies:
            _session.proxies.update(proxies)
    return _session


def fetch_json(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> Any:
    """Fetch JSON with a small retry loop."""

    session = get_session()
    attempt = 0
    last_exc: Optional[Exception] = None

    while attempt < retries:
        try:
            response = session.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # broad but OK for lightweight CLI tool
            last_exc = exc
            attempt += 1
            sleep_for = backoff_factor * (2 ** (attempt - 1))
            logger.warning("HTTP error on %s (attempt %s/%s): %s", url, attempt, retries, exc)
            time.sleep(sleep_for)

    assert last_exc is not None
    raise last_exc
