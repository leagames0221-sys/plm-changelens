"""R5: traceability-table impact (deterministic, no LLM)."""

from __future__ import annotations

from pathlib import Path

from plm_changelens.packs.plm.bom_loader import load_bom_csv
from plm_changelens.packs.plm.classify import diff_boms
from plm_changelens.packs.plm.traceability import diff_traceability, load_trace_csv

FIX = Path(__file__).parent / "fixtures"


def _impact():
    cs = diff_boms(load_bom_csv(FIX / "bom_old.csv"), load_bom_csv(FIX / "bom_new.csv"))
    links = load_trace_csv(FIX / "trace_table.csv")
    return diff_traceability(cs, links)


def test_affected_links_identified():
    impact = _impact()
    affected_reqs = {a.link.requirement_id for a in impact.affected}
    # REQ-001 covers PART-310 (quantity changed) -> affected
    # REQ-002 covers PART-320 (revision) + PART-110 (removed) -> affected
    # REQ-003 covers SUB-210 (unchanged) -> not affected
    assert affected_reqs == {"REQ-001", "REQ-002"}


def test_affected_link_reports_triggering_parts_and_reasons():
    impact = _impact()
    req002 = next(a for a in impact.affected if a.link.requirement_id == "REQ-002")
    assert set(req002.triggering_parts) == {"PART-320", "PART-110"}
    assert "revision_updated" in req002.reasons
    assert "part_removed" in req002.reasons


def test_new_part_without_link_is_candidate():
    impact = _impact()
    # PART-330 was added and is not in any trace link.
    assert impact.new_link_candidates == ["PART-330"]


def test_deterministic():
    assert _impact().to_dict() == _impact().to_dict()
