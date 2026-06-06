"""Canonical change-item data model (the diff output schema).

Naming convention borrows from DeepDiff's named change categories (values_changed
/ iterable_item_added / dictionary_item_removed) but is specialised to BOM change
semantics. This is the single canonical shape every downstream layer (report,
LLM impact summary, traceability) consumes. (ADR-0002 / ADR-0004)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ChangeCategory(StrEnum):
    PART_ADDED = "part_added"
    PART_REMOVED = "part_removed"
    QUANTITY_CHANGED = "quantity_changed"
    REVISION_UPDATED = "revision_updated"


@dataclass(frozen=True)
class ChangeItem:
    """One classified BOM change.

    Attributes:
        category: which of the four BOM change categories this is.
        part_number: the affected part number.
        path: hierarchical path of parent part numbers from the top assembly
            down to (and excluding) this part, e.g. ["ASSY-100", "SUB-210"].
        old: previous value snapshot (None for additions).
        new: new value snapshot (None for removals).
    """

    category: ChangeCategory
    part_number: str
    path: list[str] = field(default_factory=list)
    old: dict[str, Any] | None = None
    new: dict[str, Any] | None = None

    @property
    def path_str(self) -> str:
        return " / ".join(self.path) if self.path else "(top)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "part_number": self.part_number,
            "path": list(self.path),
            "path_str": self.path_str,
            "old": self.old,
            "new": self.new,
        }


@dataclass(frozen=True)
class ChangeSet:
    """Deterministic, ordered collection of changes between two BOM versions."""

    changes: list[ChangeItem] = field(default_factory=list)

    def by_category(self, category: ChangeCategory) -> list[ChangeItem]:
        return [c for c in self.changes if c.category == category]

    def counts(self) -> dict[str, int]:
        out = {cat.value: 0 for cat in ChangeCategory}
        for c in self.changes:
            out[c.category.value] += 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": self.counts(),
            "changes": [c.to_dict() for c in self.changes],
        }
