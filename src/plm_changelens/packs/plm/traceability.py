"""Traceability-table impact (R5): which requirement<->design<->test links a BOM
change touches, and which added parts still need a link. Deterministic, no LLM.

Trace-table CSV contract (columns, case-insensitive):
    requirement_id, design_id, test_id, part_numbers
``part_numbers`` is a ``;``-separated list of the parts a link covers. The model
borrows Doorstop's idea of typed, validatable links (ADR-0004) but stays a light
internal structure; export is JSON for now.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...core.change_model import ChangeCategory, ChangeSet

REQUIRED_COLUMNS = ("requirement_id", "design_id", "test_id", "part_numbers")


class TraceFormatError(ValueError):
    """Raised when a trace-table CSV is structurally invalid."""


@dataclass(frozen=True)
class TraceLink:
    requirement_id: str
    design_id: str
    test_id: str
    part_numbers: frozenset[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "design_id": self.design_id,
            "test_id": self.test_id,
            "part_numbers": sorted(self.part_numbers),
        }


@dataclass(frozen=True)
class AffectedLink:
    link: TraceLink
    triggering_parts: list[str]
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "link": self.link.to_dict(),
            "triggering_parts": self.triggering_parts,
            "reasons": self.reasons,
        }


@dataclass(frozen=True)
class TraceImpact:
    affected: list[AffectedLink] = field(default_factory=list)
    new_link_candidates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "affected": [a.to_dict() for a in self.affected],
            "new_link_candidates": list(self.new_link_candidates),
        }


def load_trace_csv(path: str | Path) -> list[TraceLink]:
    p = Path(path)
    if not p.exists():
        raise TraceFormatError(f"file not found: {p}")
    with p.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise TraceFormatError("file is empty (no header row)")
        colmap = {name.strip().lower(): name for name in reader.fieldnames}
        missing = [c for c in REQUIRED_COLUMNS if c not in colmap]
        if missing:
            raise TraceFormatError(f"missing required column(s): {', '.join(missing)}")
        links: list[TraceLink] = []
        for row in reader:
            parts = {
                tok.strip()
                for tok in (row.get(colmap["part_numbers"]) or "").split(";")
                if tok.strip()
            }
            links.append(
                TraceLink(
                    requirement_id=(row.get(colmap["requirement_id"]) or "").strip(),
                    design_id=(row.get(colmap["design_id"]) or "").strip(),
                    test_id=(row.get(colmap["test_id"]) or "").strip(),
                    part_numbers=frozenset(parts),
                )
            )
    return links


def diff_traceability(change_set: ChangeSet, links: list[TraceLink]) -> TraceImpact:
    """Identify links touched by the change set and added parts lacking a link."""
    # Map each changed part -> the change categories that touched it.
    touched: dict[str, set[str]] = {}
    for c in change_set.changes:
        touched.setdefault(c.part_number, set()).add(c.category.value)

    linked_parts = {p for link in links for p in link.part_numbers}

    affected: list[AffectedLink] = []
    for link in links:
        triggering = sorted(link.part_numbers & touched.keys())
        if not triggering:
            continue
        reasons = sorted({cat for p in triggering for cat in touched[p]})
        affected.append(
            AffectedLink(link=link, triggering_parts=triggering, reasons=reasons)
        )

    added_parts = {
        c.part_number
        for c in change_set.by_category(ChangeCategory.PART_ADDED)
    }
    new_link_candidates = sorted(added_parts - linked_parts)

    return TraceImpact(affected=affected, new_link_candidates=new_link_candidates)
