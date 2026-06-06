"""Requirement / test-spec update drafts (R4).

For each BOM change, emit a DRAFT requirement (in an EARS template) and a DRAFT
test outline. The EARS skeleton is chosen deterministically by change category;
the LLM only fills the natural-language body. Every artifact is explicitly
labelled as a review-required draft (R4.3) — the tool never produces an
authoritative requirement or test.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..core.change_model import ChangeCategory, ChangeItem, ChangeSet
from .provider import LLMProvider

DRAFT_LABEL = "DRAFT — requires human review (not an approved requirement)"


class EarsPattern(StrEnum):
    UBIQUITOUS = "ubiquitous"  # The <system> shall <action>
    EVENT_DRIVEN = "event_driven"  # When <trigger>, the <system> shall <action>
    STATE_DRIVEN = "state_driven"  # While <state>, the <system> shall <action>
    UNWANTED = "unwanted"  # If <condition>, then the <system> shall <action>
    OPTIONAL = "optional"  # Where <feature>, the <system> shall <action>


# Which EARS pattern best frames each BOM change category, and the matching test
# type (cc-sdd / spec-kit mapping: event->integration, unwanted->error/edge).
_CATEGORY_TO_EARS = {
    ChangeCategory.PART_ADDED: (EarsPattern.EVENT_DRIVEN, "integration test"),
    ChangeCategory.PART_REMOVED: (EarsPattern.UNWANTED, "regression / error-path test"),
    ChangeCategory.QUANTITY_CHANGED: (EarsPattern.STATE_DRIVEN, "parametric / state test"),
    ChangeCategory.REVISION_UPDATED: (EarsPattern.EVENT_DRIVEN, "integration test"),
}

_SYSTEM = (
    "You draft medical-device software requirements. Given a BOM change and an "
    "EARS pattern, write ONE concise requirement sentence following that pattern. "
    "Output only the sentence. Do not invent identifiers."
)


@dataclass(frozen=True)
class DraftArtifact:
    change: ChangeItem
    ears_pattern: EarsPattern
    requirement_draft: str
    test_type: str
    test_draft: str
    label: str = DRAFT_LABEL

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "change": self.change.to_dict(),
            "ears_pattern": self.ears_pattern.value,
            "requirement_draft": self.requirement_draft,
            "test_type": self.test_type,
            "test_draft": self.test_draft,
        }


@dataclass(frozen=True)
class DraftBundle:
    artifacts: list[DraftArtifact]

    def to_dict(self) -> dict[str, Any]:
        return {"label": DRAFT_LABEL, "artifacts": [a.to_dict() for a in self.artifacts]}


def _req_prompt(change: ChangeItem, pattern: EarsPattern) -> str:
    return (
        f"EARS pattern: {pattern.value}. "
        f"BOM change: {change.category.value} of {change.part_number} "
        f"under [{change.path_str}]. old={change.old} new={change.new}"
    )


def _test_outline(change: ChangeItem, test_type: str) -> str:
    return (
        f"{test_type}: verify the system behaviour affected by "
        f"{change.category.value} of {change.part_number} "
        f"under [{change.path_str}]."
    )


def generate_drafts(change_set: ChangeSet, provider: LLMProvider) -> DraftBundle:
    artifacts: list[DraftArtifact] = []
    for change in change_set.changes:
        pattern, test_type = _CATEGORY_TO_EARS[change.category]
        requirement = provider.complete(_req_prompt(change, pattern), system=_SYSTEM)
        artifacts.append(
            DraftArtifact(
                change=change,
                ears_pattern=pattern,
                requirement_draft=requirement,
                test_type=test_type,
                test_draft=_test_outline(change, test_type),
            )
        )
    return DraftBundle(artifacts=artifacts)
