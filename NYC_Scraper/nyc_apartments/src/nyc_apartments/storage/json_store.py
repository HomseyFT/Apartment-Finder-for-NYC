from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from ..models import Apartment


def save_to_json(path: str, apartments: Iterable[Apartment]) -> None:
    """Serialize apartments to a JSON file on disk."""

    data = [apt.dict() for apt in apartments]
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_from_json(path: str) -> List[Apartment]:
    """Load apartments from a JSON file; return an empty list if missing."""

    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    return [Apartment(**item) for item in raw]
