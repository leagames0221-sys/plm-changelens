"""Load an indented (level-based) BOM CSV into a ``core.Node`` tree.

CSV contract (R1.2). Required columns (case-insensitive, order-free):
    level         integer hierarchy level; the single level-0 row is the top
                  assembly. A child has level = parent.level + 1.
    part_number   part identity.
    quantity      numeric quantity.
    revision      revision string (e.g. "A", "01", "R2").
Any other columns are preserved in ``BomAttrs.extra``.

Validation (R1.3): missing required columns, non-monotonic / skipped levels,
non-numeric quantity, more than one root, or an empty file raise
:class:`BomFormatError` with the offending row number. The loader never guesses
or fills in missing data.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ...core.tree import Node
from .bom_node import BomAttrs

REQUIRED_COLUMNS = ("level", "part_number", "quantity", "revision")


class BomFormatError(ValueError):
    """Raised when a BOM CSV is structurally invalid. Carries a row number."""

    def __init__(self, message: str, row: int | None = None):
        self.row = row
        prefix = f"row {row}: " if row is not None else ""
        super().__init__(f"{prefix}{message}")


def load_bom_csv(path: str | Path) -> Node:
    """Parse ``path`` and return the BOM as a labelled tree (root = top assembly)."""
    p = Path(path)
    if not p.exists():
        raise BomFormatError(f"file not found: {p}")
    with p.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise BomFormatError("file is empty (no header row)")
        normalized = {name.strip().lower(): name for name in reader.fieldnames}
        missing = [c for c in REQUIRED_COLUMNS if c not in normalized]
        if missing:
            raise BomFormatError(f"missing required column(s): {', '.join(missing)}")
        rows = list(reader)
    return _build_tree(rows, normalized)


def _build_tree(rows: list[dict[str, str]], colmap: dict[str, str]) -> Node:
    if not rows:
        raise BomFormatError("file has a header but no data rows")

    def field(row: dict[str, str], key: str) -> str:
        return (row.get(colmap[key]) or "").strip()

    extra_keys = [
        lower for lower, _orig in colmap.items() if lower not in REQUIRED_COLUMNS
    ]

    root: Node | None = None
    # Stack of (level, node) representing the current ancestry path.
    stack: list[tuple[int, Node]] = []

    for idx, row in enumerate(rows, start=2):  # row 1 is the header
        level = _parse_level(field(row, "level"), idx)
        part_number = field(row, "part_number")
        if not part_number:
            raise BomFormatError("empty part_number", idx)
        quantity = _parse_quantity(field(row, "quantity"), idx)
        revision = field(row, "revision")
        extra = {k: field(row, k) for k in extra_keys}

        if level == 0:
            if root is not None:
                raise BomFormatError("multiple level-0 (root) rows found", idx)
            attrs = BomAttrs(part_number, quantity, revision, path=[], extra=extra)
            root = Node(label=part_number, payload=attrs)
            stack = [(0, root)]
            continue

        if root is None:
            raise BomFormatError("first data row must be level 0 (top assembly)", idx)

        # Pop ancestors until we find this row's parent (level-1).
        while stack and stack[-1][0] >= level:
            stack.pop()
        if not stack or stack[-1][0] != level - 1:
            raise BomFormatError(
                f"level {level} row has no level-{level - 1} parent (skipped level?)",
                idx,
            )
        parent_level, parent_node = stack[-1]
        parent_attrs: BomAttrs = parent_node.payload
        path = [*parent_attrs.path, parent_attrs.part_number]
        attrs = BomAttrs(part_number, quantity, revision, path=path, extra=extra)
        node = Node(label=part_number, payload=attrs)
        parent_node.add(node)
        stack.append((level, node))

    if root is None:
        raise BomFormatError("no level-0 (root) row found")
    return root


def _parse_level(value: str, row: int) -> int:
    try:
        level = int(value)
    except ValueError:
        raise BomFormatError(f"level must be an integer, got {value!r}", row) from None
    if level < 0:
        raise BomFormatError(f"level must be >= 0, got {level}", row)
    return level


def _parse_quantity(value: str, row: int) -> float:
    try:
        return float(value)
    except ValueError:
        raise BomFormatError(
            f"quantity must be numeric, got {value!r}", row
        ) from None
