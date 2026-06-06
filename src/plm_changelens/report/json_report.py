"""Structured JSON rendering of a ChangeSet (R6.1)."""

from __future__ import annotations

import json

from ..core.change_model import ChangeSet


def render_json(change_set: ChangeSet, *, indent: int = 2) -> str:
    """Deterministic JSON (stable key order) for machine consumption."""
    return json.dumps(
        change_set.to_dict(), indent=indent, ensure_ascii=False, sort_keys=False
    )
