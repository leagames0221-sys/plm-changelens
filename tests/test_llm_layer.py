"""R3/R4: impact summary + draft generation (deterministic via mock provider)."""

from __future__ import annotations

from pathlib import Path

from plm_changelens.core.change_model import ChangeCategory
from plm_changelens.llm.doc_gen import DRAFT_LABEL, generate_drafts
from plm_changelens.llm.impact_summary import generate_impact_summary
from plm_changelens.llm.providers.mock import MockProvider
from plm_changelens.packs.plm.bom_loader import load_bom_csv
from plm_changelens.packs.plm.classify import diff_boms

FIX = Path(__file__).parent / "fixtures"


def _changeset():
    return diff_boms(load_bom_csv(FIX / "bom_old.csv"), load_bom_csv(FIX / "bom_new.csv"))


def test_impact_summary_one_finding_per_change_with_evidence():
    cs = _changeset()
    report = generate_impact_summary(cs, MockProvider())
    assert len(report.findings) == len(cs.changes)
    # R3.3: each finding is bound to its source change (evidence is structural).
    for finding in report.findings:
        ev = finding.to_dict()["evidence"]
        assert ev["part_number"] == finding.change.part_number
        assert ev["category"] == finding.change.category.value


def test_drafts_are_labelled_and_ears_mapped():
    cs = _changeset()
    bundle = generate_drafts(cs, MockProvider())
    assert bundle.to_dict()["label"] == DRAFT_LABEL
    assert len(bundle.artifacts) == len(cs.changes)
    for art in bundle.artifacts:
        assert art.label == DRAFT_LABEL  # R4.3 every artifact flagged draft
        assert art.ears_pattern  # R4.2 an EARS pattern is assigned
        assert art.test_type

    # Spot-check the category->EARS mapping is applied.
    added = next(a for a in bundle.artifacts
                 if a.change.category is ChangeCategory.PART_ADDED)
    assert added.ears_pattern.value == "event_driven"


def test_impact_is_deterministic_with_mock():
    cs = _changeset()
    a = generate_impact_summary(cs, MockProvider()).to_dict()
    b = generate_impact_summary(cs, MockProvider()).to_dict()
    assert a == b
