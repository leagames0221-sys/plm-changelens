"""R2.2/R2.3: BOM diff classification into the four categories + path."""

from __future__ import annotations

from pathlib import Path

from plm_changelens.core.change_model import ChangeCategory
from plm_changelens.packs.plm.bom_loader import load_bom_csv
from plm_changelens.packs.plm.classify import diff_boms

FIX = Path(__file__).parent / "fixtures"


def _run():
    old = load_bom_csv(FIX / "bom_old.csv")
    new = load_bom_csv(FIX / "bom_new.csv")
    return diff_boms(old, new)


def test_counts_match_expected():
    cs = _run()
    counts = cs.counts()
    assert counts["part_added"] == 1
    assert counts["part_removed"] == 1
    assert counts["quantity_changed"] == 1
    assert counts["revision_updated"] == 1


def test_added_part_is_washer_with_path():
    cs = _run()
    added = cs.by_category(ChangeCategory.PART_ADDED)
    assert [a.part_number for a in added] == ["PART-330"]
    assert added[0].path == ["ASSY-100", "SUB-210"]


def test_removed_part_is_cover():
    cs = _run()
    removed = cs.by_category(ChangeCategory.PART_REMOVED)
    assert [r.part_number for r in removed] == ["PART-110"]


def test_quantity_change_screw_4_to_6():
    cs = _run()
    q = cs.by_category(ChangeCategory.QUANTITY_CHANGED)
    assert len(q) == 1
    assert q[0].part_number == "PART-310"
    assert q[0].old["quantity"] == 4.0
    assert q[0].new["quantity"] == 6.0


def test_revision_update_bracket_b_to_c():
    cs = _run()
    r = cs.by_category(ChangeCategory.REVISION_UPDATED)
    assert len(r) == 1
    assert r[0].part_number == "PART-320"
    assert r[0].old["revision"] == "B"
    assert r[0].new["revision"] == "C"


def test_determinism_same_changeset_each_run():
    a = _run().to_dict()
    b = _run().to_dict()
    assert a == b
