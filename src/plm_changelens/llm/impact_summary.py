"""Change-impact summary (R3): LLM prose, deterministic evidence linkage.

Each finding is structurally bound to the concrete ChangeItem that produced it
(R3.3) — the traceability does NOT rely on the model being honest. The model
only supplies the natural-language explanation; the evidence (part number, path,
old/new) is attached by code. If no provider is available the deterministic
change set alone is still usable (R3.2, handled by the caller).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.change_model import ChangeItem, ChangeSet
from .provider import LLMProvider

_SYSTEM = (
    "You are assisting medical-device PLM change control. Given one bill-of-"
    "materials change, explain its likely impact on higher-level assemblies and "
    "on verification, in 1-2 plain sentences. Do not invent part numbers."
)


@dataclass(frozen=True)
class ImpactFinding:
    change: ChangeItem
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "change": self.change.to_dict(),
            "explanation": self.explanation,
            "evidence": {
                "part_number": self.change.part_number,
                "path": list(self.change.path),
                "category": self.change.category.value,
            },
        }


@dataclass(frozen=True)
class ImpactReport:
    findings: list[ImpactFinding]

    def to_dict(self) -> dict[str, Any]:
        return {"findings": [f.to_dict() for f in self.findings]}


def _prompt_for(change: ChangeItem) -> str:
    return (
        f"Change: {change.category.value} of part {change.part_number} "
        f"under assembly path [{change.path_str}]. "
        f"old={change.old} new={change.new}"
    )


def generate_impact_summary(
    change_set: ChangeSet, provider: LLMProvider
) -> ImpactReport:
    """Produce one explanation per change, each bound to its source change."""
    findings: list[ImpactFinding] = []
    for change in change_set.changes:
        explanation = provider.complete(_prompt_for(change), system=_SYSTEM)
        findings.append(ImpactFinding(change=change, explanation=explanation))
    return ImpactReport(findings=findings)
