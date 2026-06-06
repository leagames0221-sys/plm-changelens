"""Human-readable rendering of a ChangeSet (R6.1)."""

from __future__ import annotations

from ..core.change_model import ChangeCategory, ChangeSet

_LABELS = {
    ChangeCategory.PART_ADDED: "Added parts",
    ChangeCategory.PART_REMOVED: "Removed parts",
    ChangeCategory.QUANTITY_CHANGED: "Quantity changes",
    ChangeCategory.REVISION_UPDATED: "Revision updates",
}


def render_human(change_set: ChangeSet) -> str:
    lines: list[str] = []
    counts = change_set.counts()
    total = sum(counts.values())
    lines.append(f"BOM change report — {total} change(s)")
    lines.append("=" * 40)
    for cat in ChangeCategory:
        lines.append(f"  {_LABELS[cat]}: {counts[cat.value]}")
    lines.append("")

    for cat in ChangeCategory:
        items = change_set.by_category(cat)
        if not items:
            continue
        lines.append(f"## {_LABELS[cat]} ({len(items)})")
        for it in items:
            lines.append(f"  - {it.part_number}   [under: {it.path_str}]")
            detail = _detail(cat, it)
            if detail:
                lines.append(f"      {detail}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _detail(cat: ChangeCategory, it) -> str:
    if cat is ChangeCategory.QUANTITY_CHANGED and it.old and it.new:
        return f"quantity: {it.old.get('quantity')} -> {it.new.get('quantity')}"
    if cat is ChangeCategory.REVISION_UPDATED and it.old and it.new:
        return f"revision: {it.old.get('revision')} -> {it.new.get('revision')}"
    if cat is ChangeCategory.PART_ADDED and it.new:
        return f"qty {it.new.get('quantity')}, rev {it.new.get('revision')}"
    if cat is ChangeCategory.PART_REMOVED and it.old:
        return f"was qty {it.old.get('quantity')}, rev {it.old.get('revision')}"
    return ""
