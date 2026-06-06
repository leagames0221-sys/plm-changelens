"""BOM attribute schema and BOM-aware tree-edit cost callbacks.

A BOM part is stored as a ``core.Node`` whose ``label`` is the part number
(identity) and whose ``payload`` is a :class:`BomAttrs`. The cost callbacks
encode BOM semantics on top of the agnostic tree diff: parts with different
part numbers are never aligned (they are a remove + insert), while parts with
the same number but differing quantity/revision are an UPDATE. (ADR-0002)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.tree import Node

# A part-number mismatch must never be treated as an in-place update; make its
# cost strictly larger than remove(1) + insert(1) so the algorithm prefers a
# remove + insert (= PART_REMOVED + PART_ADDED), which is the correct semantics.
MISMATCH_COST = 1_000_000.0


@dataclass
class BomAttrs:
    part_number: str
    quantity: float
    revision: str
    path: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        snap = {
            "part_number": self.part_number,
            "quantity": self.quantity,
            "revision": self.revision,
        }
        snap.update(self.extra)
        return snap


def insert_cost(_node: Node) -> float:
    return 1.0


def remove_cost(_node: Node) -> float:
    return 1.0


def update_cost(a: Node, b: Node) -> float:
    """0 == identical, small == same part w/ attr change, huge == different part."""
    aa: BomAttrs = a.payload
    bb: BomAttrs = b.payload
    if aa.part_number != bb.part_number:
        return MISMATCH_COST
    if aa.quantity == bb.quantity and aa.revision == bb.revision:
        return 0.0
    return 1.0
