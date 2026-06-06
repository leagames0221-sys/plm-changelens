"""Run the deterministic core diff over two BOM trees and classify the result.

Maps each tree-edit ``Operation`` onto one or more :class:`ChangeItem` in the
four BOM categories (R2.2) and attaches the hierarchical path (R2.3). An UPDATE
that changes both quantity and revision yields two change items (one per
attribute) so each emitted item is exactly one category.
"""

from __future__ import annotations

from ...core.change_model import ChangeCategory, ChangeItem, ChangeSet
from ...core.tree import Node
from ...core.tree_diff import Operation, OpType, diff
from .bom_node import BomAttrs, insert_cost, remove_cost, update_cost


def diff_boms(old_root: Node, new_root: Node) -> ChangeSet:
    """Compute the deterministic, classified change set between two BOMs."""
    _distance, operations = diff(
        old_root,
        new_root,
        insert_cost=insert_cost,
        remove_cost=remove_cost,
        update_cost=update_cost,
    )
    items: list[ChangeItem] = []
    for op in operations:
        items.extend(_classify_op(op))
    items.sort(key=_sort_key)
    return ChangeSet(changes=items)


def _classify_op(op: Operation) -> list[ChangeItem]:
    if op.op is OpType.MATCH:
        return []
    if op.op is OpType.INSERT:
        attrs: BomAttrs = op.b.payload
        return [
            ChangeItem(
                category=ChangeCategory.PART_ADDED,
                part_number=attrs.part_number,
                path=list(attrs.path),
                old=None,
                new=attrs.snapshot(),
            )
        ]
    if op.op is OpType.REMOVE:
        attrs = op.a.payload
        return [
            ChangeItem(
                category=ChangeCategory.PART_REMOVED,
                part_number=attrs.part_number,
                path=list(attrs.path),
                old=attrs.snapshot(),
                new=None,
            )
        ]
    # UPDATE: same part number, attribute(s) changed.
    old: BomAttrs = op.a.payload
    new: BomAttrs = op.b.payload
    out: list[ChangeItem] = []
    if old.quantity != new.quantity:
        out.append(
            ChangeItem(
                category=ChangeCategory.QUANTITY_CHANGED,
                part_number=new.part_number,
                path=list(new.path),
                old=old.snapshot(),
                new=new.snapshot(),
            )
        )
    if old.revision != new.revision:
        out.append(
            ChangeItem(
                category=ChangeCategory.REVISION_UPDATED,
                part_number=new.part_number,
                path=list(new.path),
                old=old.snapshot(),
                new=new.snapshot(),
            )
        )
    return out


_CATEGORY_ORDER = {
    ChangeCategory.PART_ADDED: 0,
    ChangeCategory.PART_REMOVED: 1,
    ChangeCategory.QUANTITY_CHANGED: 2,
    ChangeCategory.REVISION_UPDATED: 3,
}


def _sort_key(item: ChangeItem):
    return (_CATEGORY_ORDER[item.category], tuple(item.path), item.part_number)
